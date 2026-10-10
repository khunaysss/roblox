-- ServerScriptService.CC_CharacterAnimations
-- Cage Champions Prototyp v06 (+ Ringen: E Takedown, F Sprawl, am Boden LMB Schlag, Leertaste Befreien/Aufstehen): Steh-Moveset + schlagabhaengige Trefferreaktionen, Taumeln, K.o. vorne/hinten, Hitstop.
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
local setBlock -- vorab deklariert (wird im Heartbeat benutzt, Definition weiter unten)
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
		if root and not f.ko and not f.wr then
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

setBlock = function(f, on)
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
		local ms = RS:FindFirstChild("CC_MatchState")
		if ms and ms:GetAttribute("State") == "over" then return end -- liegen bleiben; das Runden-System setzt beim Neustart zurueck
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
local function addDamage(char, amount)  -- fuer die Punktwertung (CC_Match)
	char:SetAttribute("CC_DamageDealt", (char:GetAttribute("CC_DamageDealt") or 0) + amount)
end
local function frozen(f) return f.char:GetAttribute("CC_Frozen") == true end

-- Sounds (SoundService.CC_Sounds): am HumanoidRootPart des Getroffenen abspielen (3D)
local SFX = game:GetService("SoundService"):WaitForChild("CC_Sounds")
local function sfx(char, name, pitch)
	local src = SFX:FindFirstChild(name); local root = char and char:FindFirstChild("HumanoidRootPart")
	if not (src and root) then return end
	local snd = src:Clone(); snd.PlaybackSpeed = (pitch or 1) * (0.94 + math.random() * 0.12); snd.RollOffMaxDistance = 120; snd.Parent = root
	snd:Play(); game:GetService("Debris"):AddItem(snd, snd.TimeLength + 0.5)
end
local function hitFX(char, strength, kind)
	if kind == "hit" then sfx(char, strength > 0.4 and "HitHeavy" or "HitLight")
	elseif kind == "stagger" then sfx(char, "HitHeavy", 0.9)
	elseif kind == "block" and strength > 0.12 then sfx(char, "Block", 1.25)
	elseif kind == "ko" then sfx(char, "HitHeavy", 0.85); task.delay(0.7, function() sfx(char, "BodyFall") end); game.ReplicatedStorage.CC_MatchState:SetAttribute("CrowdBoost", os.clock()) end
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
	if not m or attacker.ko or attacker.blocking or frozen(attacker) or os.clock() < attacker.busyUntil then return end
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
				addDamage(attacker.char, dmg)
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

-- ================= Ringen (Takedown, Sprawl, Guard, Befreiung, Aufstehen) =================
-- Paar-Animationen aus Wrestling_Prototype_v02 (A = Angreifer, B = Verteidiger). Beide HumanoidRootParts werden
-- verankert und exakt wie in Blender aufgestellt: B steht 1,5 m (5,357 Studs) vor A und schaut ihn an.
-- Die Bewegung durch den Raum steckt im Root-Bone; am Ende eines Austauschs werden die HumanoidRootParts auf die
-- End-Positionen versetzt (rootEnd aus den Daten), dann laufen normale Animationen weiter.
local WR_GAP = 1.5 / 0.28
local WR = {}
for _, pair in ipairs({ "TD_DoubleLeg_Success", "TD_DoubleLeg_Defended", "Ground_Guard_Idle", "Ground_Guard_Punch", "Ground_Guard_Escape", "Ground_GetUp" }) do
	for _, s in ipairs({ "A", "B" }) do
		local name = "WR_" .. pair .. "_" .. s
		WR[pair .. "_" .. s] = { anim = anim(name), rootEnd = require(A[name .. "_Data"]).rootEnd }
	end
end
local TD_RANGE = 6          -- Studs
local TD_DAMAGE = 5
local GROUND_PUNCH_DAMAGE = 7
local SPRAWL_WINDOW = 0.45  -- F innerhalb dieser Zeit vor/nach dem Schuss = Sprawl

local function wrTrack(f, key)
	f.wrTracks = f.wrTracks or {}
	if not f.wrTracks[key] then f.wrTracks[key] = f.hum.Animator:LoadAnimation(WR[key].anim) end
	return f.wrTracks[key]
end
local function wrStopAll(f, fade)
	for _, tr in pairs(f.wrTracks or {}) do if tr.IsPlaying then tr:Stop(fade or 0) end end
end
local function stopStanding(f)
	setBlock(f, false); interrupt(f)
	for _, k in ipairs(REACTIONS) do f.tracks[k]:Stop(0.05) end
	for _, k in ipairs({ "walk", "back", "left", "right", "block", "blockhit" }) do f.tracks[k]:Stop(0.05) end
	f.loco = nil
end
-- Root-Bone-Versatz (Blender-Daten) in einen HumanoidRootPart-Versatz umrechnen (nur Position + Drehung um Y)
local function rootOffset(f, v)
	local rootBone = f.char.HumanoidRootPart:FindFirstChild("Root")
	local t = CFrame.new(-v[1], v[2], -v[3], -v[5], v[6], -v[7], v[4])
	local o = rootBone.CFrame * t * rootBone.CFrame:Inverse()
	local _, yaw = o:ToEulerAnglesYXZ()
	return CFrame.new(o.Position.X, 0, o.Position.Z) * CFrame.Angles(0, yaw, 0)
end
local function playPair(a, b, pair, looped)
	local ta, tb = wrTrack(a, pair .. "_A"), wrTrack(b, pair .. "_B")
	wrStopAll(a, 0); wrStopAll(b, 0)
	ta.Looped = looped or false; tb.Looped = looped or false
	ta:Play(0, 1, 1); tb:Play(0, 1, 1)
	return ta, tb
end
local function setWrestle(f, partner, role)
	f.wr = role and { role = role, partner = partner } or nil
	f.char:SetAttribute("CC_Wrestle", role or false)
	f.char.HumanoidRootPart.Anchored = role ~= nil or f.char == workspace:FindFirstChild("CC_TrainingDummy")
end

-- Austausch beenden: beide stehen wieder; HumanoidRootParts auf die End-Positionen des letzten Paars versetzen
local function endExchange(a, b, pair)
	for _, x in ipairs({ { a, "A" }, { b, "B" } }) do
		local f, s = x[1], x[2]
		local start = f.wrStart
		if start then f.char.HumanoidRootPart.CFrame = start * rootOffset(f, WR[pair .. "_" .. s].rootEnd) end
		wrStopAll(f, 0)
		setWrestle(f, nil, nil)
		f.busyUntil = os.clock() + 0.3
	end
end

local function groundLoop(top, bottom)
	playPair(top, bottom, "Ground_Guard_Idle", true)
	top.wr.state = "guard"
end

function tryTakedown(a)
	if a.ko or a.wr or frozen(a) or os.clock() < a.busyUntil then return end
	-- Ziel: naechster Gegner vor A in Reichweite
	local b, bd
	for _, f in pairs(fighters) do
		if f ~= a and not f.ko and not f.wr then
			local d = (f.char.HumanoidRootPart.Position - a.char.HumanoidRootPart.Position) * Vector3.new(1, 0, 1)
			if d.Magnitude <= TD_RANGE and a.char.HumanoidRootPart.CFrame.LookVector:Dot(d.Unit) > 0.4 and (not bd or d.Magnitude < bd) then b, bd = f, d.Magnitude end
		end
	end
	if not b then return end
	stopStanding(a); stopStanding(b)
	-- Aufstellung wie in Blender
	local ra, rb = a.char.HumanoidRootPart, b.char.HumanoidRootPart
	local dir = ((rb.Position - ra.Position) * Vector3.new(1, 0, 1)).Unit
	local Ca = CFrame.lookAt(ra.Position, ra.Position + dir)
	local Cb = Ca * CFrame.new(0, 0, -WR_GAP) * CFrame.Angles(0, math.pi, 0)
	Cb = Cb + Vector3.new(0, rb.Position.Y - Cb.Position.Y, 0)
	setWrestle(a, b, "shoot"); setWrestle(b, a, "defend")
	ra.CFrame = Ca; rb.CFrame = Cb
	a.wrStart, b.wrStart = Ca, Cb
	a.busyUntil, b.busyUntil = math.huge, math.huge
	-- Sprawl: Verteidiger drueckt F kurz vor/nach dem Schuss (Spieler) oder 30 % (Trainingsgegner)
	local shotAt = os.clock()
	local isDummy = b.char == workspace:FindFirstChild("CC_TrainingDummy")
	task.wait(SPRAWL_WINDOW)
	local defended
	if isDummy then defended = math.random() < 0.3 else defended = b.sprawlAt ~= nil and math.abs(b.sprawlAt - shotAt) <= SPRAWL_WINDOW end
	if a.ko or b.ko then return end
	local pair = defended and "TD_DoubleLeg_Defended" or "TD_DoubleLeg_Success"
	print(("[CC] %s Takedown -> %s: %s"):format(a.char.Name, b.char.Name, defended and "Sprawl (abgewehrt)" or "erfolgreich"))
	local ta = playPair(a, b, pair, false)
	hitFX(a.char, 0.25, "land"); hitFX(b.char, defended and 0.2 or 0.6, defended and "block" or "hit")
	ta.Stopped:Wait()
	if defended then
		endExchange(a, b, pair)
		return
	end
	b.hum.Health = math.max(1, b.hum.Health - TD_DAMAGE)
	addDamage(a.char, TD_DAMAGE + 5) -- Takedown zaehlt zusaetzlich
	a.wr.role, b.wr.role = "top", "bottom"
	a.char:SetAttribute("CC_Wrestle", "top"); b.char:SetAttribute("CC_Wrestle", "bottom")
	a.busyUntil, b.busyUntil = 0, 0
	groundLoop(a, b)
end

function groundPunch(top)
	local w = top.wr
	if not w or w.role ~= "top" or w.state ~= "guard" or top.ko then return end
	local bottom = w.partner
	w.state = "punch"
	local ta = playPair(top, bottom, "Ground_Guard_Punch", false)
	task.delay(11 / 24, function()          -- Schlagkontakt Frame 11
		if not (top.wr and bottom.wr) then return end
		bottom.hum.Health = math.max(0, bottom.hum.Health - GROUND_PUNCH_DAMAGE)
		addDamage(top.char, GROUND_PUNCH_DAMAGE)
		print(("[CC] %s Bodenschlag -> %s %.0f"):format(top.char.Name, bottom.char.Name, bottom.hum.Health))
		hitFX(bottom.char, 0.5, "hit"); hitFX(top.char, 0.25, "land")
		ta:AdjustSpeed(0.05); task.delay(HITSTOP, function() if ta.IsPlaying then ta:AdjustSpeed(1) end end)
	end)
	ta.Stopped:Wait()
	if not (top.wr and bottom.wr) then return end
	if bottom.hum.Health <= 0 then
		-- K.o. am Boden: unten bleibt liegen, oben steht auf
		print("[CC] K.o. am Boden!", bottom.char.Name)
		local tb = wrTrack(bottom, "Ground_Guard_Idle_B"); tb:Play(0); tb:AdjustSpeed(0)
		local te = wrTrack(top, "Ground_Guard_Escape_A"); te:Play(0.1); te.Stopped:Wait()
		local tg = wrTrack(top, "Ground_GetUp_A"); tg:Play(0); tg.Stopped:Wait()
		top.char.HumanoidRootPart.CFrame = top.wrStart * rootOffset(top, WR.Ground_GetUp_A.rootEnd)
		wrStopAll(top, 0); setWrestle(top, nil, nil)
		bottom.ko = true; bottom.char:SetAttribute("CC_KO", true); bottom.char:SetAttribute("CC_LastReact", "koGround")
		task.delay(KO_TIME, function()
			bottom.char.HumanoidRootPart.CFrame = bottom.wrStart * rootOffset(bottom, WR.Ground_Guard_Idle_B.rootEnd)
			wrStopAll(bottom, 0.3); setWrestle(bottom, nil, nil)
			bottom.hum.Health = bottom.hum.MaxHealth; bottom.ko = false; bottom.char:SetAttribute("CC_KO", false)
		end)
		return
	end
	groundLoop(top, bottom)
	for _, x in ipairs({ bottom, top }) do
		if x.wantEscape then task.spawn(groundEscape, x) break end
	end
end

-- Befreien/Aufstehen: von unten (Escape) oder oben (aufstehen) - beide nutzen Escape + GetUp
function groundEscape(f)
	local w = f.wr
	if not w or (w.role ~= "top" and w.role ~= "bottom") or w.state == "escape" then return end
	local top = w.role == "top" and f or w.partner
	local bottom = w.role == "bottom" and f or w.partner
	if top.wr.state == "punch" then f.wantEscape = true return end -- nach dem laufenden Schlag ausfuehren
	f.wantEscape = nil
	top.wr.state = "escape"
	local ta = playPair(top, bottom, "Ground_Guard_Escape", false)
	ta.Stopped:Wait()
	local tg = playPair(top, bottom, "Ground_GetUp", false)
	tg.Stopped:Wait()
	endExchange(top, bottom, "Ground_GetUp")
	print(("[CC] %s und %s stehen wieder"):format(top.char.Name, bottom.char.Name))
end

-- Trainingsgegner am Boden: oben schlaegt er, unten befreit er sich nach einer Weile
RunService.Heartbeat:Connect(function()
	local d = workspace:FindFirstChild("CC_TrainingDummy")
	local D_ = d and fighters[d]
	if not (D_ and D_.wr) or D_.ko then return end
	local w = D_.wr
	if os.clock() < (D_.groundThink or 0) then return end
	D_.groundThink = os.clock() + 1.4 + math.random() * 1.2
	if d:GetAttribute("CC_Passive") then return end
	if w.role == "top" and w.state == "guard" then
		if math.random() < 0.8 then task.spawn(groundPunch, D_) else task.spawn(groundEscape, D_) end
	elseif w.role == "bottom" and w.partner.wr and w.partner.wr.state == "guard" and math.random() < 0.35 then
		task.spawn(groundEscape, D_)
	end
end)

local function hook(p) p.CharacterAdded:Connect(setup); if p.Character then task.spawn(setup, p.Character) end end
game.Players.PlayerAdded:Connect(hook); for _, p in ipairs(game.Players:GetPlayers()) do hook(p) end

-- Reset (vom Runden-System ueber ServerStorage.CC_ResetFighter): Ringkampf, Block, K.o., Animationen beenden,
-- volle oder angegebene Leben, an Position setzen
local resetEvent = game.ServerStorage:FindFirstChild("CC_ResetFighter") or Instance.new("BindableFunction")
resetEvent.Name = "CC_ResetFighter"; resetEvent.Parent = game.ServerStorage
resetEvent.OnInvoke = function(char, cf, health)
	local f = fighters[char]
	if not f then return false end
	f.attackToken = (f.attackToken or 0) + 1
	if f.wr then local p = f.wr.partner; wrStopAll(f, 0); setWrestle(f, nil, nil); if p and p.wr then wrStopAll(p, 0); setWrestle(p, nil, nil) end end
	setBlock(f, false); f.wantBlock = false; f.wantEscape = nil
	for k, tr in pairs(f.tracks) do if k ~= "idle" then tr:Stop(0.1) end end
	if not f.tracks.idle.IsPlaying then f.tracks.idle:Play(0.2) end
	f.loco = nil; f.ko = false; f.busyUntil = 0
	f.char:SetAttribute("CC_KO", false); f.char:SetAttribute("CC_Wrestle", false)
	f.hum.Health = health or f.hum.MaxHealth
	if cf then f.char.HumanoidRootPart.CFrame = cf end
	return true
end

RS.CC_Action.OnServerEvent:Connect(function(player, move)
	local f = player.Character and fighters[player.Character]
	if not (f and type(move) == "string") then return end
	if move == "takedown" then tryTakedown(f)
	elseif move == "escape" then groundEscape(f)
	elseif f.wr then if f.wr.role == "top" and move == "jab" then groundPunch(f) end
	else attack(f, move) end
end)
RS.CC_Block.OnServerEvent:Connect(function(player, on)
	local f = player.Character and fighters[player.Character]
	if f and not f.wr then setBlock(f, on == true) end
	if f and on then f.sprawlAt = os.clock() end -- F gedrueckt = Sprawl-Versuch gegen Takedowns
end)

-- Trainingsgegner: dreht sich zum Spieler, greift in Reichweite an, blockt manchmal
local dummy = workspace:WaitForChild("CC_TrainingDummy")
local D = setup(dummy)
local fill = dummy.HumanoidRootPart.HealthBar.Frame.Fill
D.hum.HealthChanged:Connect(function(h) fill.Size = UDim2.fromScale(math.max(h, 0) / D.hum.MaxHealth, 1) end)
local nextThink = 0
local DUMMY_MOVES = { "jab", "jab", "cross", "lowkick", "hook" }
RunService.Heartbeat:Connect(function()
	if D.ko or D.wr then return end
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
	if dummy:GetAttribute("CC_ForceTD") then dummy:SetAttribute("CC_ForceTD", nil); task.spawn(tryTakedown, D) return end -- Test: Takedown sofort
	if dummy:GetAttribute("CC_Passive") then setBlock(D, false) return end -- Trainingsmodus: steht nur und dreht sich
	if os.clock() < nextThink then return end
	nextThink = os.clock() + 0.9 + math.random() * 1.1
	if bestDist <= 5 then
		local r = math.random()
		if r < 0.12 and best.hum.Health > 0 and not best.wr then
			setBlock(D, false)
			task.spawn(tryTakedown, D)
		elseif r < 0.37 then
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
