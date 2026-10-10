-- ServerScriptService.CC_CharacterAnimations
-- Cage Champions Prototyp v05: Steh-Moveset + schlagabhaengige Trefferreaktionen, Taumeln, K.o. vorne/hinten, Hitstop.
--   Bewegung: Idle, Walk vor/zurueck, Strafe links/rechts (Richtung relativ zur Blickrichtung)
--   Angriffe: Jab, Cross, Hook, Uppercut, LowKick   Verteidigung: Block (halten), BlockHit
--   Treffer: Jab/Cross -> HitStraight, Haken -> HitHook, Aufwaertshaken -> HitUpper, Low Kick -> HitLeg,
--            schwerer Treffer bei wenig Leben -> Stagger; K.o. nach Haken nach vorne, sonst nach hinten (3 s liegen)
--   Wer getroffen wird, verliert seinen laufenden Angriff (Unterbrechung).
-- Animationen ueber temporaere Studio-IDs (RegisterKeyframeSequence); fuer das veroeffentlichte Spiel
-- muessen sie in die Gruppe ANIMEXGANG (7160158) hochgeladen und die IDs hier eingetragen werden.
local KSP = game:GetService("KeyframeSequenceProvider")
local RunService = game:GetService("RunService")
local RS = game.ReplicatedStorage
local A = game.ServerStorage.CC_Animations
local function anim(name) local a = Instance.new("Animation"); a.AnimationId = KSP:RegisterKeyframeSequence(A[name]); return a end
local ANIMS = {
	idle = "Fighter_Idle_v08", walk = "Fighter_Walk_v01", back = "Fighter_WalkBack_v01",
	left = "Fighter_StrafeL_v01", right = "Fighter_StrafeR_v01",
	jab = "Fighter_Jab_v01", cross = "Fighter_Cross_v01", hook = "Fighter_Hook_v01",
	uppercut = "Fighter_Uppercut_v01", lowkick = "Fighter_LowKick_v01",
	block = "Fighter_Block_v01", blockhit = "Fighter_BlockHit_v01",
	hit = "Fighter_HitReact_v01", ko = "Fighter_KO_v01",
	hitStraight = "Fighter_HitStraight_v01", hitHook = "Fighter_HitHook_v01", hitUpper = "Fighter_HitUpper_v01",
	hitLeg = "Fighter_HitLeg_v01", stagger = "Fighter_Stagger_v01", koFwd = "Fighter_KOForward_v01",
}
for k, n in pairs(ANIMS) do ANIMS[k] = anim(n) end

-- Angriffswerte: Trefferzeitpunkt (s), Reichweite (Studs), Schaden, Sperrzeit bis zur naechsten Aktion (s)
local MOVES = {
	jab      = { hit = 0.21, range = 4.5, damage = 6,  lock = 0.55, react = "hitStraight", ko = "ko",    heavy = false },
	cross    = { hit = 0.25, range = 4.7, damage = 10, lock = 0.75, react = "hitStraight", ko = "ko",    heavy = true },
	hook     = { hit = 0.33, range = 4.3, damage = 12, lock = 0.85, react = "hitHook",     ko = "koFwd", heavy = true },
	uppercut = { hit = 0.38, range = 4.1, damage = 14, lock = 0.85, react = "hitUpper",    ko = "ko",    heavy = true },
	lowkick  = { hit = 0.42, range = 4.6, damage = 9,  lock = 1.00, react = "hitLeg",      ko = "ko",    heavy = false },
}
local WALK_REF = 6        -- Laufzyklen sind fuer WalkSpeed 6 gebaut
local BLOCK_FACTOR = 0.2  -- Schaden im Block
local BLOCK_SPEED = 3     -- Laufgeschwindigkeit im Block
local KO_TIME = 3
local STAGGER_HEALTH = 35  -- unter diesem Leben koennen schwere Treffer taumeln lassen
local HITSTOP = 0.07       -- kurzes Einfrieren des Angriffs beim Treffer
local REACTIONS = { "hit", "hitStraight", "hitHook", "hitUpper", "hitLeg", "stagger" }

local fighters = {}
local LOCO = { "walk", "back", "left", "right" }

local function setup(char)
	local hum = char:WaitForChild("Humanoid"); local animator = hum:WaitForChild("Animator")
	hum.BreakJointsOnDeath = false
	hum:SetStateEnabled(Enum.HumanoidStateType.Dead, false)
	local t = {}
	for k, a in pairs(ANIMS) do t[k] = animator:LoadAnimation(a) end
	for _, k in ipairs({ "idle", "walk", "back", "left", "right" }) do t[k].Looped = true end
	t.idle:Play(0.2)
	local f = { char = char, hum = hum, tracks = t, busyUntil = 0, ko = false, blocking = false, speed = hum.WalkSpeed, loco = nil }
	fighters[char] = f
	char.AncestryChanged:Connect(function() if not char.Parent then fighters[char] = nil end end)
	return f
end

-- Laufanimation nach Bewegungsrichtung relativ zur Blickrichtung
RunService.Heartbeat:Connect(function()
	for _, f in pairs(fighters) do
		local root = f.char:FindFirstChild("HumanoidRootPart")
		if root and not f.ko then
			if f.wantBlock and not f.blocking and os.clock() >= f.busyUntil then setBlock(f, true) end
			local v = root.AssemblyLinearVelocity; v = Vector3.new(v.X, 0, v.Z)
			local want = nil
			if v.Magnitude > 0.8 then
				local fwd = root.CFrame.LookVector:Dot(v.Unit); local side = root.CFrame.RightVector:Dot(v.Unit)
				if math.abs(fwd) >= math.abs(side) then want = fwd > 0 and "walk" or "back" else want = side > 0 and "right" or "left" end
			end
			if want ~= f.loco then
				if f.loco then f.tracks[f.loco]:Stop(0.15) end
				if want then f.tracks[want]:Play(0.15) end
				f.loco = want
				f.char:SetAttribute("CC_Loco", want or "idle")
			end
			if want then f.tracks[want]:AdjustSpeed(v.Magnitude / WALK_REF) end
		end
	end
end)

local function setBlock(f, on)
	f.wantBlock = on
	if f.ko or f.blocking == on then return end
	if on and os.clock() < f.busyUntil then return end -- wird im Heartbeat nachgeholt
	f.blocking = on
	f.char:SetAttribute("CC_Block", on)
	if on then
		f.tracks.block:Play(0.08)
		task.delay(f.tracks.block.Length - 0.02, function() if f.blocking then f.tracks.block:AdjustSpeed(0) end end)
		f.hum.WalkSpeed = BLOCK_SPEED
	else
		f.tracks.block:Stop(0.12); f.tracks.blockhit:Stop(0.1)
		f.hum.WalkSpeed = f.speed
	end
end

local function knockout(f, kind)
	setBlock(f, false)
	f.ko = true
	f.hum.WalkSpeed = 0
	for k, tr in pairs(f.tracks) do if k ~= "idle" and k ~= (kind or "ko") then tr:Stop(0.1) end end
	f.loco = nil
	local ko = f.tracks[kind or "ko"]
	ko:Play(0.1)
	f.char:SetAttribute("CC_LastReact", kind or "ko")
	task.delay(ko.Length - 0.05, function() if f.ko then ko:AdjustSpeed(0) end end)
	f.char:SetAttribute("CC_KO", true)
	task.delay(KO_TIME, function()
		if not f.char.Parent then return end
		ko:Stop(0.4)
		f.hum.Health = f.hum.MaxHealth
		f.hum.WalkSpeed = f.speed
		f.ko = false
		f.char:SetAttribute("CC_KO", false)
	end)
end

local function inFront(attacker, target, range)
	local a, b = attacker.char.HumanoidRootPart, target.char.HumanoidRootPart
	local d = b.Position - a.Position; local flat = Vector3.new(d.X, 0, d.Z)
	return flat.Magnitude <= range and flat.Magnitude > 0 and a.CFrame.LookVector:Dot(flat.Unit) > 0.5
end

-- Treffer-Effekt an die beteiligten Spieler (Kamera-Ruck, Aufblitzen); Staerke 0..1
local function hitFX(char, strength, kind)
	local p = game.Players:GetPlayerFromCharacter(char)
	if p then RS.CC_HitFX:FireClient(p, strength, kind) end
end

-- laufenden Angriff abbrechen (wer getroffen wird, schlaegt nicht weiter)
local function interrupt(f)
	f.attackToken = (f.attackToken or 0) + 1
	for move in pairs(MOVES) do
		if f.tracks[move].IsPlaying then f.tracks[move]:Stop(0.08) end
	end
end

local function react(target, kind, lock)
	for _, k in ipairs(REACTIONS) do if k ~= kind and target.tracks[k].IsPlaying then target.tracks[k]:Stop(0.05) end end
	target.tracks[kind]:Play(0.03)
	target.char:SetAttribute("CC_LastReact", kind)
	target.busyUntil = math.max(target.busyUntil, os.clock() + lock)
end

local function attack(attacker, move)
	local m = MOVES[move]
	if not m or attacker.ko or attacker.blocking or os.clock() < attacker.busyUntil then return end
	attacker.busyUntil = os.clock() + m.lock
	attacker.attackToken = (attacker.attackToken or 0) + 1
	local token = attacker.attackToken
	local track = attacker.tracks[move]
	track:Play(0.05)
	task.delay(m.hit, function()
		if attacker.ko or not attacker.char.Parent or attacker.attackToken ~= token then return end
		for _, target in pairs(fighters) do
			if target ~= attacker and not target.ko and inFront(attacker, target, m.range) then
				local blocked = target.blocking
				local dmg = blocked and m.damage * BLOCK_FACTOR or m.damage
				target.hum.Health = math.max(0, target.hum.Health - dmg)
				print(("[CC] %s %s -> %s %.0f%s"):format(attacker.char.Name, move, target.char.Name, target.hum.Health, blocked and " (geblockt)" or ""))
				-- Hitstop: der Schlag haelt im Treffermoment kurz an
				track:AdjustSpeed(0.05)
				task.delay(blocked and HITSTOP * 0.5 or HITSTOP, function() if track.IsPlaying then track:AdjustSpeed(1) end end)
				if target.hum.Health <= 0 then
					print("[CC] K.o.!", target.char.Name, m.ko)
					interrupt(target)
					knockout(target, m.ko)
					hitFX(target.char, 1.0, "ko"); hitFX(attacker.char, 0.6, "land")
				elseif blocked then
					target.tracks.blockhit:Play(0.03)
					hitFX(target.char, 0.15, "block"); hitFX(attacker.char, 0.1, "block")
				else
					interrupt(target)
					if m.heavy and target.hum.Health < STAGGER_HEALTH and math.random() < 0.6 then
						react(target, "stagger", 1.1)
						target.hum.WalkSpeed = 2
						task.delay(1.1, function() if not target.ko and not target.blocking then target.hum.WalkSpeed = target.speed end end)
						hitFX(target.char, 0.8, "stagger")
					else
						react(target, m.react, m.heavy and 0.4 or 0.3)
						hitFX(target.char, m.heavy and 0.5 or 0.3, "hit")
					end
					hitFX(attacker.char, m.heavy and 0.3 or 0.15, "land")
				end
			end
		end
	end)
end

local function hook(p) p.CharacterAdded:Connect(setup); if p.Character then task.spawn(setup, p.Character) end end
game.Players.PlayerAdded:Connect(hook); for _, p in ipairs(game.Players:GetPlayers()) do hook(p) end

RS.CC_Action.OnServerEvent:Connect(function(player, move)
	local f = player.Character and fighters[player.Character]
	if f and type(move) == "string" then attack(f, move) end
end)
RS.CC_Block.OnServerEvent:Connect(function(player, on)
	local f = player.Character and fighters[player.Character]
	if f then setBlock(f, on == true) end
end)

-- Trainingsgegner: dreht sich zum Spieler, greift in Reichweite an, blockt manchmal
local dummy = workspace:WaitForChild("CC_TrainingDummy")
local D = setup(dummy)
local fill = dummy.HumanoidRootPart.HealthBar.Frame.Fill
D.hum.HealthChanged:Connect(function(h) fill.Size = UDim2.fromScale(math.max(h, 0) / D.hum.MaxHealth, 1) end)
local nextThink = 0
local DUMMY_MOVES = { "jab", "jab", "cross", "lowkick", "hook" }
RunService.Heartbeat:Connect(function()
	if D.ko then return end
	local root = dummy.HumanoidRootPart
	local best, bestDist
	for char, f in pairs(fighters) do
		if f ~= D and not f.ko then
			local dist = (char.HumanoidRootPart.Position - root.Position).Magnitude
			if not bestDist or dist < bestDist then best, bestDist = f, dist end
		end
	end
	if not best then setBlock(D, false) return end
	local tp = best.char.HumanoidRootPart.Position
	local look = Vector3.new(tp.X, root.Position.Y, tp.Z)
	if (look - root.Position).Magnitude > 0.1 then root.CFrame = root.CFrame:Lerp(CFrame.lookAt(root.Position, look), 0.15) end
	if dummy:GetAttribute("CC_Passive") then setBlock(D, false) return end -- Trainingsmodus: steht nur und dreht sich
	if os.clock() < nextThink then return end
	nextThink = os.clock() + 0.9 + math.random() * 1.1
	if bestDist <= 5 then
		if math.random() < 0.25 then
			setBlock(D, true)
			task.delay(0.8 + math.random() * 0.6, function() setBlock(D, false) end)
		else
			setBlock(D, false)
			attack(D, DUMMY_MOVES[math.random(#DUMMY_MOVES)])
		end
	else
		setBlock(D, false)
	end
end)
