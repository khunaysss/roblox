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
	mF = "Fighter_MoveF_v01", mB = "Fighter_MoveB_v01", mL = "Fighter_MoveL_v01", mR = "Fighter_MoveR_v01", -- Fussarbeit v10 (gemischt)
	jab = "Fighter_Jab_v03", cross = "Fighter_Cross_v03", hook = "Fighter_Hook_v03",
	jabBody = "Fighter_JabBody_v01", crossBody = "Fighter_CrossBody_v01", hitBody = "Fighter_HitBody_v01",
	bodykick = "Fighter_BodyKick_v01", highkick = "Fighter_HighKick_v01", frontkick = "Fighter_FrontKick_v01",
	uppercut = "Fighter_Uppercut_v02", lowkick = "Fighter_LowKick_v03",
	block = "Fighter_Block_v01", blockhit = "Fighter_BlockHit_v01",
	hit = "Fighter_HitReact_v01", ko = "Fighter_KO_v01",
	hitStraight = "Fighter_HitStraight_v01", hitHook = "Fighter_HitHook_v01", hitUpper = "Fighter_HitUpper_v01",
	hitLeg = "Fighter_HitLeg_v01", stagger = "Fighter_Stagger_v01", koFwd = "Fighter_KOForward_v01",
}
for k, n in pairs(ANIMS) do ANIMS[k] = anim(n) end

-- Angriffswerte (B): Treffer wird ueber die SICHTBARE Faust bzw. den Fuss geprueft (Bone-Position im Trefferfenster),
-- nicht ueber eine Reichweitenzahl. win = Trefferfenster (s ab Start), limb = Bone der Faust/des Fusses,
-- zone = Ziel (head/body/leg), damage, cost = Ausdauer, lock = Sperre bis zur naechsten Aktion (Kombos: Eingabe wird gepuffert).
local MOVES = {
	jab       = { win = { 0.10, 0.30 }, limb = "LeftHand",  zone = "head", damage = 6,  cost = 5,  lock = 0.42, react = "hitStraight", ko = "ko",    heavy = false },
	cross     = { win = { 0.10, 0.31 }, limb = "RightHand", zone = "head", damage = 10, cost = 8,  lock = 0.58, react = "hitStraight", ko = "ko",    heavy = true },
	hook      = { win = { 0.27, 0.40 }, limb = "LeftHand",  zone = "head", damage = 12, cost = 10, lock = 0.70, react = "hitHook",     ko = "koFwd", heavy = true },
	uppercut  = { win = { 0.32, 0.46 }, limb = "RightHand", zone = "head", damage = 14, cost = 11, lock = 0.72, react = "hitUpper",    ko = "ko",    heavy = true },
	jabBody   = { win = { 0.10, 0.30 }, limb = "LeftHand",  zone = "body", damage = 5,  cost = 5,  lock = 0.45, react = "hitBody",     ko = "koFwd", heavy = false, bodyShot = true },
	crossBody = { win = { 0.10, 0.31 }, limb = "RightHand", zone = "body", damage = 9,  cost = 8,  lock = 0.60, react = "hitBody",     ko = "koFwd", heavy = true,  bodyShot = true },
	lowkick   = { win = { 0.36, 0.50 }, limb = "RightFoot", zone = "leg",  damage = 9,  cost = 12, lock = 0.85, react = "hitLeg",      ko = "ko",    heavy = false },
	bodykick  = { win = { 0.33, 0.52 }, limb = "RightLowerLeg", zone = "body", damage = 11, cost = 14, lock = 0.95, react = "hitBody",     ko = "koFwd", heavy = true,  bodyShot = true },
	highkick  = { win = { 0.42, 0.62 }, limb = "RightLowerLeg", zone = "head", damage = 18, cost = 18, lock = 1.15, react = "hitHook",     ko = "ko",    heavy = true },
	frontkick = { win = { 0.28, 0.45 }, limb = "LeftFoot",  zone = "body", damage = 7,  cost = 9,  lock = 0.80, react = "hitBody",     ko = "ko",    heavy = false, bodyShot = true },
}
-- Trefferkugeln: Mittelpunkt entlang der Bone-Achse (Studs) und Radius (Studs). Faust = Handschuh-Mitte.
local LIMB_OFFSET = { LeftHand = 0.45, RightHand = 0.45, RightFoot = 0.25, LeftFoot = 0.25, RightLowerLeg = 0.9 }  -- Roundhouse trifft mit dem Schienbein
-- Kopfmitte am Oberkoerper verankert: Trefferreaktionen weichen Folgeschlaegen nicht aus
local ZONES = { head = { bone = "UpperTorso", along = 1.6, radius = 0.95 }, body = { bone = "UpperTorso", along = 0.55, radius = 1.25 },
	leg = { bone = "LeftUpperLeg", along = 0.9, radius = 1.1 } }   -- Radius = halbe Koerperteil-Dicke + Handschuh bzw. Schienbein
local STAMINA_MAX, STAMINA_REGEN, STAMINA_DELAY = 100, 16, 0.6
local LOW_STAMINA = 25          -- darunter: weniger Schaden, langsamere Schlaege
local BUFFER = 0.30             -- Eingabe so viele Sekunden vor Ende der Sperre wird gepuffert (Kombination)
local WALK_REF = 6        -- Laufzyklen sind fuer WalkSpeed 6 gebaut
local BLOCK_FACTOR = 0.2  -- Schaden im Block
local BLOCK_SPEED = 3     -- Laufgeschwindigkeit im Block
local KO_TIME = 3
local HP_FLOOR = 0.01       -- Leben faellt nie ganz auf 0: bei 0 verliert der Humanoid dauerhaft seine Standhoehe (Spieler sank nach K.o. 2 Studs in den Boden)
local STAGGER_HEALTH = 35  -- unter diesem Leben koennen schwere Treffer taumeln lassen
local HITSTOP = 0.07       -- kurzes Einfrieren des Angriffs beim Treffer
local REACTIONS = { "hit", "hitStraight", "hitHook", "hitUpper", "hitLeg", "stagger", "hitBody" }

local fighters = {}
local setBlock -- vorab deklariert (wird im Heartbeat benutzt, Definition weiter unten)
local LOCO = { "walk", "back", "left", "right" }

local function setup(char)
	local hum = char:WaitForChild("Humanoid"); local animator = hum:WaitForChild("Animator")
	hum.BreakJointsOnDeath = false
	hum:SetStateEnabled(Enum.HumanoidStateType.Dead, false)
	local t = {}
	for k, a in pairs(ANIMS) do t[k] = animator:LoadAnimation(a) end
	for _, k in ipairs({ "idle", "walk", "back", "left", "right", "mF", "mB", "mL", "mR" }) do t[k].Looped = true end
	t.idle:Play(0.2)
	-- die vier Fussarbeit-Loops laufen immer synchron mit; nur ihre Gewichte aendern sich (Diagonalen, weiche Wechsel)
	for _, k in ipairs({ "mF", "mB", "mL", "mR" }) do t[k]:Play(0, 0.001, 1) end
	local f = { char = char, hum = hum, tracks = t, busyUntil = 0, ko = false, blocking = false, speed = hum.WalkSpeed, loco = nil,
		stamina = STAMINA_MAX, lastSpend = 0 }
	char:SetAttribute("CC_Stamina", STAMINA_MAX)
	fighters[char] = f
	char.AncestryChanged:Connect(function() if not char.Parent then fighters[char] = nil end end)
	return f
end

-- Fussarbeit: vier synchrone Loops (vor/zurueck/links/rechts) nach Bewegungsrichtung relativ zur Blickrichtung gewichtet.
-- Abspieltempo = tatsaechliche Geschwindigkeit / 6 (Loops sind fuer WalkSpeed 6 gebaut) -> Standfuss bleibt stehen.
local MOVE_KEYS = { "mF", "mB", "mL", "mR" }
RunService.Heartbeat:Connect(function()
	for _, f in pairs(fighters) do
		local root = f.char:FindFirstChild("HumanoidRootPart")
		local t = f.tracks
		if root and not f.ko and not f.wr then
			if f.wantBlock and not f.blocking and os.clock() >= f.busyUntil then setBlock(f, true) end
			if not t.mF.IsPlaying then for _, k in ipairs(MOVE_KEYS) do t[k]:Play(0, 0.001, 1) end end -- nach K.o./Reset wieder anwerfen (synchron)
			local v = root.AssemblyLinearVelocity; v = Vector3.new(v.X, 0, v.Z)
			local speed = v.Magnitude
			local fwd, side = 0, 0
			if speed > 0.05 then fwd = root.CFrame.LookVector:Dot(v) / speed; side = root.CFrame.RightVector:Dot(v) / speed end
			local amount = math.clamp((speed - 0.4) / 2.0, 0, 1)            -- weicher Einstieg aus dem Stand
			local w = { mF = math.max(fwd, 0), mB = math.max(-fwd, 0), mR = math.max(side, 0), mL = math.max(-side, 0) }
			local sum = w.mF + w.mB + w.mL + w.mR
			for _, k in ipairs(MOVE_KEYS) do
				local wk = sum > 0 and (w[k] / sum) * amount or 0
				t[k]:AdjustWeight(math.max(wk, 0.001), 0.12)
				t[k]:AdjustSpeed(math.max(speed, 0.5) / WALK_REF)
			end
			local dom = amount < 0.05 and "idle" or (math.abs(fwd) >= math.abs(side) and (fwd > 0 and "walk" or "back") or (side > 0 and "right" or "left"))
			if dom ~= f.loco then f.loco = dom; f.char:SetAttribute("CC_Loco", dom) end
		elseif t then
			for _, k in ipairs(MOVE_KEYS) do if t[k] then t[k]:AdjustWeight(0.001, 0.1) end end
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

local function bonePos(char, name, along)
	local hrp = char:FindFirstChild("HumanoidRootPart")
	local b = hrp and hrp:FindFirstChild(name, true)
	if not b then return nil end
	local cf = b.TransformedWorldCFrame
	return cf.Position + cf.UpVector * (along or 0)
end
local function spend(f, amount)
	f.stamina = math.max(0, f.stamina - amount); f.lastSpend = os.clock()
	f.char:SetAttribute("CC_Stamina", math.floor(f.stamina + 0.5))
end
-- Ausdauer-Erholung (nicht waehrend Block und kurz nach einer Aktion)
RunService.Heartbeat:Connect(function(dt)
	for _, f in pairs(fighters) do
		if f.stamina < STAMINA_MAX and os.clock() - f.lastSpend > STAMINA_DELAY and not f.blocking then
			f.stamina = math.min(STAMINA_MAX, f.stamina + STAMINA_REGEN * dt)
			f.char:SetAttribute("CC_Stamina", math.floor(f.stamina + 0.5))
		end
	end
end)

local function land(attacker, target, move, m, track)
	local blocked = target.blocking
	local blockFactor = blocked and (m.bodyShot and 0.5 or BLOCK_FACTOR) or 1   -- hohe Deckung schuetzt den Koerper nur halb
	local tired = attacker.stamina < LOW_STAMINA and 0.7 or 1
	local dmg = m.damage * blockFactor * tired
	target.hum.Health = math.max(HP_FLOOR, target.hum.Health - dmg)
	addDamage(attacker.char, dmg)
	if blocked then spend(target, 4) end
	print(("[CC] %s %s -> %s %.0f%s"):format(attacker.char.Name, move, target.char.Name, target.hum.Health, blocked and " (geblockt)" or ""))
	-- Treffer-Stopp: Glied bleibt an der Oberflaeche stehen (Hitstop) und springt dann in die Rueckzugsphase,
	-- statt durch den Koerper des Gegners weiterzulaufen
	track:AdjustSpeed(0.02)
	task.delay(blocked and HITSTOP * 0.5 or HITSTOP, function()
		if not track.IsPlaying then return end
		local back = m.win[2] + 0.04
		if track.TimePosition < back then track.TimePosition = back end
		track:AdjustSpeed(attacker.animSpeed or 1)
	end)
	if target.hum.Health <= HP_FLOOR then
		print("[CC] K.o.!", target.char.Name, m.ko)
		interrupt(target); knockout(target, m.ko)
		hitFX(target.char, 1.0, "ko"); hitFX(attacker.char, 0.6, "land")
	elseif blocked and blockFactor < 0.4 then
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
		spend(target, m.heavy and 4 or 2)
		hitFX(attacker.char, m.heavy and 0.3 or 0.15, "land")
	end
end

local function attack(attacker, move)
	local m = MOVES[move]
	if not m or attacker.ko or attacker.blocking or attacker.wr or frozen(attacker) then return end
	local now = os.clock()
	if now < attacker.busyUntil then
		-- Kombination: kurz vor Ende der Sperre gedrueckt -> genau EINE Eingabe merken (kein Dauerfeuer)
		if attacker.busyUntil - now <= BUFFER and not attacker.queued then
			attacker.queued = move
			task.delay(attacker.busyUntil - now + 0.01, function() local q = attacker.queued; attacker.queued = nil; if q then attack(attacker, q) end end)
		end
		return
	end
	if attacker.stamina < m.cost then attacker.char:SetAttribute("CC_Tired", workspace:GetServerTimeNow()); return end
	spend(attacker, m.cost)
	local speed = attacker.stamina < LOW_STAMINA and 0.85 or 1
	attacker.animSpeed = speed
	attacker.busyUntil = now + m.lock / speed
	attacker.attackToken = (attacker.attackToken or 0) + 1
	local token = attacker.attackToken
	local track = attacker.tracks[move]
	-- vorherigen Schlag ausblenden: sonst mischen sich zwei Schlaege gleicher Prioritaet und der Arm streckt sich nicht ganz
	for k in pairs(MOVES) do local tr = attacker.tracks[k]; if k ~= move and tr.IsPlaying then tr:Stop(0.06) end end
	track:Play(0.05, 1, speed)
	-- Trefferfenster: Faust-/Fuss-Position gegen die Trefferkugel des Gegners (sichtbare Bewegung = Treffer)
	local t0 = os.clock()
	local done = false
	local dmin = math.huge
	local conn
	conn = RunService.Heartbeat:Connect(function()
		local t = (os.clock() - t0) * speed
		if done or attacker.ko or not attacker.char.Parent or attacker.attackToken ~= token or t > m.win[2] then
			conn:Disconnect()
			if not done and workspace:GetAttribute("CC_DebugHits") then print(("[CC] %s %s verfehlt, kleinster Abstand zur Zone %.2f"):format(attacker.char.Name, move, dmin)) end
			return
		end
		if t < m.win[1] then return end
		local fist = bonePos(attacker.char, m.limb, LIMB_OFFSET[m.limb])
		if not fist then return end
		for _, target in pairs(fighters) do
			if target ~= attacker and not target.ko and not target.wr then
				local z = ZONES[m.zone]
				local zp = bonePos(target.char, z.bone, z.along)
				if zp then dmin = math.min(dmin, (fist - zp).Magnitude - z.radius) end
				if zp and (fist - zp).Magnitude <= z.radius then
					done = true; conn:Disconnect()
					land(attacker, target, move, m, track)
					return
				end
			end
		end
	end)
end

-- ================= Ringen (Takedown, Sprawl, Guard, Befreiung, Aufstehen) =================
-- Paar-Animationen aus Wrestling_Prototype_v03 (Takedown, Guard) und Ground_Positions_v01 (A = Angreifer, B = Verteidiger). Beide HumanoidRootParts werden
-- verankert und exakt wie in Blender aufgestellt: B steht 1,5 m (5,357 Studs) vor A und schaut ihn an.
-- Die Bewegung durch den Raum steckt im Root-Bone; am Ende eines Austauschs werden die HumanoidRootParts auf die
-- End-Positionen versetzt (rootEnd aus den Daten), dann laufen normale Animationen weiter.
local WR_GAP = 1.5 / 0.28
local WR = {}
for _, pair in ipairs({ "TD_DoubleLeg_Success", "TD_DoubleLeg_Defended", "Ground_Guard_Idle", "Ground_Guard_Punch", "Ground_Guard_Escape", "Ground_GetUp",
	"Ground_Pass_Half", "Ground_HalfGuard_Idle", "Ground_Pass_Side", "Ground_Side_Idle", "Ground_Side_To_Mount", "Ground_Mount_Idle",
	"Ground_Mount_Punch", "Ground_Mount_To_Back", "Ground_Back_Idle", "Sub_RNC", "Sub_Armbar" }) do  -- zweite/dritte Zeile: Ground_Positions_v01 (E)
	for _, s in ipairs({ "A", "B" }) do
		local name = "WR_" .. pair .. "_" .. s
		local data = require(A[name .. "_Data"])
		WR[pair .. "_" .. s] = { anim = anim(name), rootEnd = data.rootEnd, len = (#data.frames - 1) / 24 }
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
	if not role then for _, k in ipairs({ "CC_GroundPos", "CC_SubProgress", "CC_SubName", "CC_SubRole" }) do f.char:SetAttribute(k, nil) end end
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

-- ================= Bodenpositionen (E) =================
-- Positionen: guard -> half -> side -> mount -> back. Oben: E = Position verbessern, Linksklick = Schlag (Guard, Mount),
-- Q = Submission (Mount: Armbar, Ruecken: Rear Naked Choke). Unten: Leertaste = befreien (eine Position zurueck,
-- aus der Guard aufstehen). Konter: F kurz nach Beginn des gegnerischen Versuchs -> Animation laeuft rueckwaerts zurueck.
-- Submission-Duell: Animation haelt an; oben Q haemmern, unten Leertaste haemmern; Fortschritt CC_SubProgress (0..1).
local POS_IDLE = { guard = "Ground_Guard_Idle", half = "Ground_HalfGuard_Idle", side = "Ground_Side_Idle", mount = "Ground_Mount_Idle", back = "Ground_Back_Idle" }
local ADVANCE = { guard = { "Ground_Pass_Half", "half" }, half = { "Ground_Pass_Side", "side" }, side = { "Ground_Side_To_Mount", "mount" }, mount = { "Ground_Mount_To_Back", "back" } }
local RETREAT = { half = { "Ground_Pass_Half", "guard" }, side = { "Ground_Pass_Side", "half" }, mount = { "Ground_Side_To_Mount", "side" }, back = { "Ground_Mount_To_Back", "mount" } }
local SUBS = { mount = { pair = "Sub_Armbar", hold = 40 / 24, name = "ARMBAR" }, back = { pair = "Sub_RNC", hold = 30 / 24, name = "REAR NAKED CHOKE" } }
local PUNCH = { guard = { pair = "Ground_Guard_Punch", hit = 11 / 24, dmg = 7 }, mount = { pair = "Ground_Mount_Punch", hit = 10 / 24, dmg = 9 } }
local ADVANCE_COST, ESCAPE_COST, SUB_COST = 10, 14, 16
local COUNTER_WINDOW = 0.4      -- s nach Beginn eines Versuchs, in denen F (Spieler) kontert
local SUB_TIME = 4.0            -- Duell-Dauer; danach befreit sich der Verteidiger
local SUB_TOP, SUB_BOTTOM = 0.075, 0.085   -- Fortschritt pro Tastendruck

local function isDummy(f) return f.char == workspace:FindFirstChild("CC_TrainingDummy") end
local function passive(f) return isDummy(f) and f.char:GetAttribute("CC_Passive") end
local function setPos(top, bottom, pos)
	top.wr.pos, bottom.wr.pos = pos, pos
	top.char:SetAttribute("CC_GroundPos", pos); bottom.char:SetAttribute("CC_GroundPos", pos)
end
local function groundLoop(top, bottom, pos)
	pos = pos or "guard"
	playPair(top, bottom, POS_IDLE[pos], true)
	top.wr.state = "guard"         -- "guard" = ruhig in der aktuellen Position (Name aus v01)
	setPos(top, bottom, pos)
end
-- Paar-Animation rueckwaerts (Konter / Befreien = Uebergang zurueck); Dauer aus den Blender-Daten
local function pairLen(pair) return WR[pair .. "_A"].len end
local function reversePair(top, bottom, pair, from)
	local ta, tb = wrTrack(top, pair .. "_A"), wrTrack(bottom, pair .. "_B")
	if not ta.IsPlaying then wrStopAll(top, 0); wrStopAll(bottom, 0); ta:Play(0, 1, 0); tb:Play(0, 1, 0) end
	local t = from or (pairLen(pair) - 0.02)
	ta.TimePosition, tb.TimePosition = t, t
	ta:AdjustSpeed(-1); tb:AdjustSpeed(-1)
	task.wait(t)
end
-- hat der Gegner gekontert? Spieler: F seit Beginn des Versuchs; Trainingsgegner: Zufall
local function countered(f, t0, chance)
	if isDummy(f) then return not passive(f) and math.random() < chance end
	return f.sprawlAt ~= nil and f.sprawlAt >= t0 - 0.15
end

function groundAdvance(top)
	local w = top.wr
	if not w or w.role ~= "top" or w.state ~= "guard" or top.ko then return end
	local step = ADVANCE[w.pos]; if not step then return end
	if top.stamina < ADVANCE_COST then top.char:SetAttribute("CC_Tired", os.clock()); return end
	local bottom = w.partner
	spend(top, ADVANCE_COST)
	w.state = "advance"
	local t0 = os.clock()
	local ta = playPair(top, bottom, step[1], false)
	task.wait(COUNTER_WINDOW)
	if not (top.wr and bottom.wr) then return end
	if countered(bottom, t0, 0.3) then
		print(("[CC] %s Position %s -> %s: gekontert"):format(top.char.Name, w.pos, step[2]))
		hitFX(top.char, 0.15, "block")
		reversePair(top, bottom, step[1], ta.TimePosition)
		if top.wr and bottom.wr then groundLoop(top, bottom, w.pos) end
		return
	end
	task.wait(math.max(0, pairLen(step[1]) - ta.TimePosition - 0.03))
	if not (top.wr and bottom.wr) then return end
	print(("[CC] %s Position %s -> %s"):format(top.char.Name, w.pos, step[2]))
	addDamage(top.char, 4)      -- Positionsgewinn zaehlt fuer die Punktwertung
	groundLoop(top, bottom, step[2])
end

function groundPunch(top)
	local w = top.wr
	if not w or w.role ~= "top" or w.state ~= "guard" or top.ko then return end
	local p = PUNCH[w.pos]; if not p then return end
	local bottom = w.partner
	w.state = "punch"
	local ta = playPair(top, bottom, p.pair, false)
	task.delay(p.hit, function()
		if not (top.wr and bottom.wr) then return end
		bottom.hum.Health = math.max(HP_FLOOR, bottom.hum.Health - p.dmg)
		addDamage(top.char, p.dmg)
		print(("[CC] %s Bodenschlag (%s) -> %s %.0f"):format(top.char.Name, w.pos, bottom.char.Name, bottom.hum.Health))
		hitFX(bottom.char, 0.5, "hit"); hitFX(top.char, 0.25, "land")
		ta:AdjustSpeed(0.05); task.delay(HITSTOP, function() if ta.IsPlaying then ta:AdjustSpeed(1) end end)
	end)
	ta.Stopped:Wait()
	if not (top.wr and bottom.wr) then return end
	if bottom.hum.Health <= HP_FLOOR then
		-- K.o. am Boden: unten bleibt liegen; aus der Guard steht oben auf, sonst bleibt oben in Position
		print("[CC] K.o. am Boden!", bottom.char.Name)
		local tb = wrTrack(bottom, POS_IDLE[w.pos] .. "_B"); tb:Play(0); tb:AdjustSpeed(0)
		if w.pos == "guard" then
			local te = wrTrack(top, "Ground_Guard_Escape_A"); te:Play(0.1); te.Stopped:Wait()
			local tg = wrTrack(top, "Ground_GetUp_A"); tg:Play(0); tg.Stopped:Wait()
			top.char.HumanoidRootPart.CFrame = top.wrStart * rootOffset(top, WR.Ground_GetUp_A.rootEnd)
			wrStopAll(top, 0); setWrestle(top, nil, nil)
		else
			local ti = wrTrack(top, POS_IDLE[w.pos] .. "_A"); ti:Play(0); ti:AdjustSpeed(0); w.state = "over"
		end
		bottom.ko = true; bottom.char:SetAttribute("CC_KO", true); bottom.char:SetAttribute("CC_LastReact", "koGround")
		task.delay(KO_TIME, function()
			if not bottom.wr then return end
			bottom.char.HumanoidRootPart.CFrame = bottom.wrStart * rootOffset(bottom, WR.Ground_Guard_Idle_B.rootEnd)
			wrStopAll(bottom, 0.3); setWrestle(bottom, nil, nil)
			if top.wr then wrStopAll(top, 0.3); setWrestle(top, nil, nil) end
			bottom.hum.Health = bottom.hum.MaxHealth; bottom.ko = false; bottom.char:SetAttribute("CC_KO", false)
		end)
		return
	end
	groundLoop(top, bottom, w.pos)
	for _, x in ipairs({ bottom, top }) do
		if x.wantEscape then task.spawn(groundEscape, x) break end
	end
end

function groundSubmit(top)
	local w = top.wr
	if not w or w.role ~= "top" or w.state ~= "guard" or top.ko then return end
	local sub = SUBS[w.pos]; if not sub then return end
	if top.stamina < SUB_COST then top.char:SetAttribute("CC_Tired", os.clock()); return end
	local bottom = w.partner
	spend(top, SUB_COST)
	w.state = "sub"; top.mash, bottom.mash = 0, 0
	print(("[CC] %s Submission-Versuch: %s"):format(top.char.Name, sub.name))
	local ta, tb = playPair(top, bottom, sub.pair, false)
	for _, x in ipairs({ top, bottom }) do x.char:SetAttribute("CC_SubName", sub.name); x.char:SetAttribute("CC_SubRole", x == top and "attack" or "defend") end
	task.wait(sub.hold)
	if not (top.wr and bottom.wr) then return end
	ta:AdjustSpeed(0); tb:AdjustSpeed(0)
	-- Duell: Start 0,35; weniger Leben unten -> Griff zieht von selbst zu
	local p, t0, last = 0.35, os.clock(), os.clock()
	local dummyNext = 0
	while top.wr and bottom.wr and p > 0 and p < 1 and os.clock() - t0 < SUB_TIME do
		local dt = task.wait(); local now = os.clock()
		for _, x in ipairs({ top, bottom }) do                 -- Trainingsgegner haemmert ca. 4-5 mal pro Sekunde
			if isDummy(x) and not passive(x) and now >= dummyNext then x.mash += 1; dummyNext = now + 0.18 + math.random() * 0.12 end
		end
		p += top.mash * SUB_TOP - bottom.mash * SUB_BOTTOM + dt * 0.10 * (1 - bottom.hum.Health / bottom.hum.MaxHealth)
		top.mash, bottom.mash = 0, 0
		p = math.clamp(p, 0, 1)
		top.char:SetAttribute("CC_SubProgress", p); bottom.char:SetAttribute("CC_SubProgress", p)
		last = now
	end
	for _, x in ipairs({ top, bottom }) do x.char:SetAttribute("CC_SubProgress", nil); x.char:SetAttribute("CC_SubName", nil); x.char:SetAttribute("CC_SubRole", nil) end
	if not (top.wr and bottom.wr) then return end
	if p >= 1 then
		print(("[CC] %s gewinnt per %s gegen %s"):format(top.char.Name, sub.name, bottom.char.Name))
		ta:AdjustSpeed(1); tb:AdjustSpeed(1)
		task.wait(pairLen(sub.pair) - sub.hold - 0.05)
		ta:AdjustSpeed(0); tb:AdjustSpeed(0)
		w.state = "over"
		addDamage(top.char, 20)
		bottom.hum.Health = HP_FLOOR
		bottom.ko = true; bottom.char:SetAttribute("CC_LastReact", "submission"); bottom.char:SetAttribute("CC_KO", true)
		hitFX(bottom.char, 0.6, "ko")
		return
	end
	print(("[CC] %s befreit sich aus %s"):format(bottom.char.Name, sub.name))
	hitFX(top.char, 0.2, "block")
	reversePair(top, bottom, sub.pair, ta.TimePosition)
	if top.wr and bottom.wr then groundLoop(top, bottom, w.pos) end
end

-- Befreien/Aufstehen: aus der Guard wie bisher (Escape + GetUp), sonst eine Position zurueck (Uebergang rueckwaerts)
function groundEscape(f)
	local w = f.wr
	if not w or (w.role ~= "top" and w.role ~= "bottom") then return end
	local top = w.role == "top" and f or w.partner
	local bottom = w.role == "bottom" and f or w.partner
	local st = top.wr.state
	if st == "sub" then if f == bottom then f.mash = (f.mash or 0) + 1 end return end   -- im Duell: Leertaste haemmern
	if st == "punch" then f.wantEscape = true return end -- nach dem laufenden Schlag ausfuehren
	if st ~= "guard" then return end
	f.wantEscape = nil
	if top.wr.pos ~= "guard" then
		if f ~= bottom then return end
		if bottom.stamina < ESCAPE_COST then bottom.char:SetAttribute("CC_Tired", os.clock()); return end
		spend(bottom, ESCAPE_COST)
		local back = RETREAT[top.wr.pos]
		top.wr.state = "escape"
		local t0 = os.clock()
		local ta = wrTrack(top, back[1] .. "_A")
		wrStopAll(top, 0); wrStopAll(bottom, 0)
		local tb = wrTrack(bottom, back[1] .. "_B")
		ta:Play(0, 1, 0); tb:Play(0, 1, 0)
		local L = pairLen(back[1]) - 0.02
		ta.TimePosition, tb.TimePosition = L, L; ta:AdjustSpeed(-1); tb:AdjustSpeed(-1)
		task.wait(COUNTER_WINDOW)
		if not (top.wr and bottom.wr) then return end
		if countered(top, t0, 0.3) then
			print(("[CC] %s Befreiungsversuch gekontert"):format(bottom.char.Name))
			hitFX(bottom.char, 0.15, "block")
			local tp = ta.TimePosition
			ta:AdjustSpeed(1); tb:AdjustSpeed(1)
			task.wait(math.max(0, L - tp))
			if top.wr and bottom.wr then groundLoop(top, bottom, top.wr.pos) end
			return
		end
		task.wait(math.max(0, ta.TimePosition))
		if not (top.wr and bottom.wr) then return end
		print(("[CC] %s befreit sich: %s -> %s"):format(bottom.char.Name, top.wr.pos, back[2]))
		groundLoop(top, bottom, back[2])
		return
	end
	top.wr.state = "escape"
	local ta = playPair(top, bottom, "Ground_Guard_Escape", false)
	ta.Stopped:Wait()
	local tg = playPair(top, bottom, "Ground_GetUp", false)
	tg.Stopped:Wait()
	endExchange(top, bottom, "Ground_GetUp")
	print(("[CC] %s und %s stehen wieder"):format(top.char.Name, bottom.char.Name))
end

-- Trainingsgegner am Boden: oben Schlaege, Position verbessern, Submission; unten befreien
RunService.Heartbeat:Connect(function()
	local d = workspace:FindFirstChild("CC_TrainingDummy")
	local D_ = d and fighters[d]
	if not (D_ and D_.wr) or D_.ko then return end
	local w = D_.wr
	if os.clock() < (D_.groundThink or 0) then return end
	D_.groundThink = os.clock() + 1.4 + math.random() * 1.2
	if d:GetAttribute("CC_Passive") then return end
	if w.role == "top" and w.state == "guard" then
		local r = math.random()
		if SUBS[w.pos] and r < 0.3 then task.spawn(groundSubmit, D_)
		elseif PUNCH[w.pos] and r < 0.75 then task.spawn(groundPunch, D_)
		elseif ADVANCE[w.pos] and r < 0.95 then task.spawn(groundAdvance, D_)
		elseif w.pos == "guard" then task.spawn(groundEscape, D_) end
	elseif w.role == "bottom" and w.partner.wr and w.partner.wr.state == "guard" and math.random() < 0.35 then
		task.spawn(groundEscape, D_)
	end
end)

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
	if move == "escape" then groundEscape(f)
	elseif f.wr then
		if f.wr.role == "top" and f.wr.state == "sub" then if move == "hook" then f.mash = (f.mash or 0) + 1 end
		elseif f.wr.role == "top" then
			if move == "jab" then task.spawn(groundPunch, f) elseif move == "takedown" then task.spawn(groundAdvance, f) elseif move == "hook" then task.spawn(groundSubmit, f) end
		end
	elseif move == "takedown" then tryTakedown(f)
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
		if r < 0.12 and best.hum.Health > HP_FLOOR and not best.wr then
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
