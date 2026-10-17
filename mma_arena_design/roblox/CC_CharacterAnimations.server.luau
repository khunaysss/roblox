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
-- Kampf-Ereignisse fuer andere Server-Skripte (CC_Tutorial): Fire("hit", angreifer, ziel, schlag, geblockt) | Fire("td", angreifer, ziel, abgewehrt)
local fightEvent = game.ServerStorage:FindFirstChild("CC_FightEvent") or Instance.new("BindableEvent")
fightEvent.Name = "CC_FightEvent"; fightEvent.Parent = game.ServerStorage
local A = game.ServerStorage.CC_Animations
-- Hochgeladene Animationen (Gruppe ANIMEXGANG): ServerStorage.CC_Animations.CC_AnimIds = ModuleScript { [Name] = Asset-ID }.
-- Fehlt eine ID, wird die temporaere Studio-ID benutzt (funktioniert nur in Studio).
local ANIM_IDS = A:FindFirstChild("CC_AnimIds") and require(A.CC_AnimIds) or {}

-- Jeder benutzte Clip wird auch zum Client repliziert. So kann der Client alle
-- Kampfanimationen laden, bevor der erste Takedown abgespielt wird (keine Bind-/T-Pose beim Erstladen).
local animationManifest = RS:FindFirstChild("CC_AnimationManifest") or Instance.new("Folder")
animationManifest.Name = "CC_AnimationManifest"
animationManifest.Parent = RS
local animationsReadyEvent = RS:FindFirstChild("CC_AnimationsReadyEvent") or Instance.new("RemoteEvent")
animationsReadyEvent.Name = "CC_AnimationsReadyEvent"
animationsReadyEvent.Parent = RS
animationsReadyEvent.OnServerEvent:Connect(function(player, loadedCount, failedCount)
	player:SetAttribute("CC_AnimationsLoaded", tonumber(loadedCount) or 0)
	player:SetAttribute("CC_AnimationsFailed", tonumber(failedCount) or 0)
	player:SetAttribute("CC_AnimationsReady", true)
end)

-- Fuer Client-UI (Hauptmenue-Buehne): ausgewaehlte IDs als Attribute an ReplicatedStorage
for _, n in ipairs({ "Fighter_Idle_v08", "Fighter_CasualIdle_v01" }) do
	if ANIM_IDS[n] then game.ReplicatedStorage:SetAttribute("CC_AnimId_" .. n, ANIM_IDS[n]) end
end
local function anim(name)
	local a = Instance.new("Animation")
	a.AnimationId = ANIM_IDS[name] and ("rbxassetid://" .. tostring(ANIM_IDS[name])) or KSP:RegisterKeyframeSequence(A[name])
	local shared = animationManifest:FindFirstChild(name)
	if not shared then
		shared = Instance.new("Animation")
		shared.Name = name
		shared.Parent = animationManifest
	end
	shared.AnimationId = a.AnimationId
	return a
end
local ANIMS = {
	idle = "Fighter_Idle_v08", walk = "Fighter_Walk_v01", back = "Fighter_WalkBack_v01",
	cIdle = "Fighter_CasualIdle_v01", cWalk = "Fighter_CasualWalk_v2", cRun = "Fighter_CasualRun_v3",   -- locker (ausserhalb des Kampfs; Gehen/Laufen v17)
	left = "Fighter_StrafeL_v01", right = "Fighter_StrafeR_v01",
	mF = "Fighter_StepF", mB = "Fighter_StepB", mL = "Fighter_StepL", mR = "Fighter_StepR", -- Fussarbeit v17: Schritt-Nachziehen (gemischt)
	jab = "Fighter_Jab_v03", cross = "Fighter_Cross_v03", hook = "Fighter_Hook_v03",
	jabBody = "Fighter_JabBody_v01", crossBody = "Fighter_CrossBody_v01", hitBody = "Fighter_HitBody_v01",
	bodykick = "Fighter_BodyKick_v3", highkick = "Fighter_HighKick_v3", frontkick = "Fighter_FrontKick_v3",   -- Tritte v17 (= v16 mit flachem Standfuss)
	uppercut = "Fighter_Uppercut_v02", lowkick = "Fighter_LowKick_v5",
	block = "Fighter_Block_v01", blockhit = "Fighter_BlockHit_v01",
	hit = "Fighter_HitReact_v01", ko = "Fighter_KO_v01",
	hitStraight = "Fighter_HitStraight_v01", hitHook = "Fighter_HitHook_v01", hitUpper = "Fighter_HitUpper_v01",
	hitLeg = "Fighter_HitLeg_v01", stagger = "Fighter_Stagger_v01", koFwd = "Fighter_KOForward_v01",
	legCheck = "Fighter_LegCheck_v01", limpL = "Fighter_LimpLeft_v01", limpR = "Fighter_LimpRight_v01",
}
for k, n in pairs(ANIMS) do ANIMS[k] = anim(n) end

-- Angriffswerte (B): Treffer wird ueber die SICHTBARE Faust bzw. den Fuss geprueft (Bone-Position im Trefferfenster),
-- nicht ueber eine Reichweitenzahl. win = Trefferfenster (s ab Start), limb = Bone der Faust/des Fusses,
-- zone = Ziel (head/body/leg), damage, cost = Ausdauer, lock = Sperre bis zur naechsten Aktion (Kombos: Eingabe wird gepuffert).
local MOVES = {
	jab       = { win = { 0.10, 0.30 }, limb = "LeftHand",  zone = "head", injuryRegion = "Nose", injury = 4, hitRadius = 0.36, maxRange = 5.0, facing = 0.35, damage = 6,  cost = 5,  lock = 0.42, react = "hitStraight", ko = "ko",    heavy = false },
	cross     = { win = { 0.10, 0.31 }, limb = "RightHand", zone = "head", injuryRegion = "Nose", injury = 7, hitRadius = 0.38, maxRange = 5.2, facing = 0.30, damage = 10, cost = 8,  lock = 0.58, react = "hitStraight", ko = "ko",    heavy = true },
	hook      = { win = { 0.27, 0.40 }, limb = "LeftHand",  zone = "head", injuryRegion = "Head", injury = 9, hitRadius = 0.42, maxRange = 4.6, facing = 0.05, damage = 12, cost = 10, lock = 0.70, react = "hitHook",     ko = "koFwd", heavy = true },
	uppercut  = { win = { 0.32, 0.46 }, limb = "RightHand", zone = "head", injuryRegion = "Nose", injury = 10, hitRadius = 0.40, maxRange = 4.3, facing = 0.15, damage = 14, cost = 11, lock = 0.72, react = "hitUpper",    ko = "ko",    heavy = true },
	jabBody   = { win = { 0.10, 0.30 }, limb = "LeftHand",  zone = "body", injuryRegion = "Ribs", injury = 4, hitRadius = 0.36, maxRange = 5.0, facing = 0.30, damage = 5,  cost = 5,  lock = 0.45, react = "hitBody",     ko = "koFwd", heavy = false, bodyShot = true },
	crossBody = { win = { 0.10, 0.31 }, limb = "RightHand", zone = "body", injuryRegion = "Ribs", injury = 8, hitRadius = 0.38, maxRange = 5.2, facing = 0.25, damage = 9,  cost = 8,  lock = 0.60, react = "hitBody",     ko = "koFwd", heavy = true,  bodyShot = true },
	lowkick   = { win = { 0.30, 0.45 }, limb = "RightFoot", zone = "leg", injury = 14, hitRadius = 0.44, maxRange = 5.2, facing = 0.05, damage = 9,  cost = 12, lock = 0.82, react = "hitLeg",      ko = "ko",    heavy = false },
	bodykick  = { win = { 0.34, 0.50 }, limb = "RightLowerLeg", zone = "body", injuryRegion = "Ribs", injury = 11, hitRadius = 0.48, maxRange = 5.6, facing = 0.10, damage = 11, cost = 14, lock = 0.98, react = "hitBody",     ko = "koFwd", heavy = true,  bodyShot = true },
	highkick  = { win = { 0.40, 0.64 }, limb = "RightLowerLeg", zone = "head", injuryRegion = "Head", injury = 15, hitRadius = 0.48, maxRange = 5.7, facing = 0.05, damage = 18, cost = 18, lock = 1.15, react = "hitHook",     ko = "ko",    heavy = true },
	frontkick = { win = { 0.30, 0.40 }, limb = "LeftFoot",  zone = "body", injuryRegion = "Ribs", injury = 6, hitRadius = 0.42, maxRange = 5.8, facing = 0.20, damage = 7,  cost = 9,  lock = 0.80, react = "hitBody",     ko = "ko",    heavy = false, bodyShot = true },
}
-- Kleine anatomische Zielkugeln statt einer grossen, magnetischen Trefferzone.
-- Die Gliedmasse besitzt pro Technik einen eigenen Radius; zusammen ergibt das die sichtbare Kontaktflaeche.
local LIMB_OFFSET = { LeftHand = 0.45, RightHand = 0.45, RightFoot = 0.25, LeftFoot = 0.25, RightLowerLeg = 0.9 }
local ZONES = {
	head = { { bone = "UpperTorso", along = 1.55, radius = 0.54 } },
	body = { { bone = "UpperTorso", along = 0.45, radius = 0.72 }, { bone = "LowerTorso", along = 0.25, radius = 0.62 } },
	leg = { { bone = "LeftUpperLeg", along = 0.75, radius = 0.50, region = "LeftLeg" }, { bone = "RightUpperLeg", along = 0.75, radius = 0.50, region = "RightLeg" } },
}
local STAMINA_MAX, STAMINA_REGEN, STAMINA_DELAY = 100, 16, 0.6
-- Kaempfer-Werte (0..20) setzt CC_Profile als Attribute am Spieler (CC_Power, CC_Cardio, CC_Wrestling, CC_Grappling);
-- der Trainingsgegner hat 0. Wirkung: Schlagkraft +1,5 % Schaden je Punkt, Kondition +2 Ausdauer und +2 % Erholung,
-- Ringen: laengeres Sprawl-Fenster bzw. seltener abgewehrt, Bodenkampf: +2,5 % Wirkung je Tastendruck im Submission-Duell.
local function stat(f, name)
	local p = f and game.Players:GetPlayerFromCharacter(f.char)
	local v = p and p:GetAttribute("CC_" .. name) or (f and f.char:GetAttribute("CC_" .. name))
	return math.clamp(tonumber(v) or 0, 0, 20)
end
-- Fortschritt melden (CC_Profile): Trainingspunkte/XP fuer den Spieler hinter einem Kaempfer
local function reward(f, kind, a, b)
	local p = f and game.Players:GetPlayerFromCharacter(f.char)
	local ev = p and game.ServerStorage:FindFirstChild("CC_ProfileEvent")
	if ev then ev:Fire(p, kind, a, b) end
end
local function staminaMax(f) return STAMINA_MAX + 2 * stat(f, "Cardio") end
-- ---- Signaturtechniken (Konfiguration in ReplicatedStorage.CC_Signatures, alle Werte vorlaeufig) ----
local SIG = require(RS:WaitForChild("CC_Signatures"))
local sigFX = RS:FindFirstChild("CC_SigFX") or Instance.new("RemoteEvent"); sigFX.Name = "CC_SigFX"; sigFX.Parent = RS
local function focusGain(f, kind)
	-- nur im echten Kampf mit Gegner (nicht im Tutorial); Fokus als Attribut CC_Focus am Charakter fuer das HUD
	if not f or f.ko or not f.char:GetAttribute("CC_Opponent") then return end
	local ms = RS:FindFirstChild("CC_MatchState")
	if not ms or ms:GetAttribute("Mode") == "tutorial" or ms:GetAttribute("State") ~= "fight" then return end
	local n = SIG.FOCUS[kind] or 0
	if n <= 0 then return end
	f.focus = math.min(SIG.FOCUS_MAX, (f.focus or 0) + n)
	f.char:SetAttribute("CC_Focus", f.focus)
end
local LOW_STAMINA = 25          -- darunter: weniger Schaden, langsamere Schlaege
local BUFFER = 0.30             -- Eingabe so viele Sekunden vor Ende der Sperre wird gepuffert (Kombination)
local WALK_REF = 6        -- Laufzyklen sind fuer WalkSpeed 6 gebaut
local BLOCK_FACTOR = 0.2  -- Schaden im Block
local BLOCK_SPEED = 3     -- Laufgeschwindigkeit im Block
local KO_TIME = 3
local HP_FLOOR = 0.01       -- Leben faellt nie ganz auf 0: bei 0 verliert der Humanoid dauerhaft seine Standhoehe (Spieler sank nach K.o. 2 Studs in den Boden)
local STAGGER_HEALTH = 35  -- Fallback fuer alte Reaktionslogik; Knockdowns werden zusaetzlich ueber Treffertrauma entschieden
-- Unabhaengig von der Punktwertung: saubere harte Treffer bauen Trauma auf.
-- Dadurch koennen Konter/Signaturen frueh K.o. schlagen, waehrend Block und Schlag-Spam deutlich weniger Wirkung haben.
local TRAUMA = {
	HEAD_ROCK = 55, HEAD_KD = 84, HEAD_KO = 108,
	BODY_ROCK = 62, BODY_KD = 92,
	ROCK_TIME = 4.2, DECAY_DELAY = 3.0,
	GROUND_TKO = { guard = 7, half = 6, side = 6, mount = 5, back = 6 },
}
local HITSTOP = 0.07       -- kurzes Einfrieren des Angriffs beim Treffer
local REACTIONS = { "hit", "hitStraight", "hitHook", "hitUpper", "hitLeg", "stagger", "hitBody" }

local fighters = {}
local setBlock -- vorab deklariert (wird im Heartbeat benutzt, Definition weiter unten)
local LOCO = { "walk", "back", "left", "right" }
local INJURY_REGIONS = { "LeftLeg", "RightLeg", "LeftArm", "RightArm", "Ribs", "Nose", "Head" }
local function injury(f, region)
	return math.clamp(tonumber(f and f.char:GetAttribute("CC_Injury_" .. region)) or 0, 0, 100)
end
local function worstLeg(f)
	local l, r = injury(f, "LeftLeg"), injury(f, "RightLeg")
	return math.max(l, r), (l >= r and "Left" or "Right")
end
local function mobilityFactor(f)
	local d = worstLeg(f)
	if d < 30 then return 1
	elseif d < 60 then return 0.88
	elseif d < 85 then return 0.65
	else return 0.38 end
end
local function injuryWalkSpeed(f)
	return math.max(2.2, f.speed * mobilityFactor(f))
end
local function limbRegionForMove(m)
	if m.limb == "LeftHand" then return "LeftArm" end
	if m.limb == "RightHand" then return "RightArm" end
	if m.limb == "LeftFoot" then return "LeftLeg" end
	if m.limb == "RightFoot" or m.limb == "RightLowerLeg" then return "RightLeg" end
end
local function limbPower(f, m)
	local region = limbRegionForMove(m)
	local d = region and injury(f, region) or 0
	if d < 30 then return 1
	elseif d < 60 then return 0.90
	elseif d < 85 then return 0.72
	else return 0.48 end
end

local function setup(char)
	local hum = char:WaitForChild("Humanoid"); local animator = hum:WaitForChild("Animator")
	hum.BreakJointsOnDeath = false
	hum:SetStateEnabled(Enum.HumanoidStateType.Dead, false)
	local t = {}
	for k, a in pairs(ANIMS) do t[k] = animator:LoadAnimation(a) end
	for _, k in ipairs({ "idle", "walk", "back", "left", "right", "mF", "mB", "mL", "mR", "limpL", "limpR", "cIdle", "cWalk", "cRun" }) do t[k].Looped = true end
	t.idle:Play(0.2)
	-- die vier Fussarbeit-Loops laufen immer synchron mit; nur ihre Gewichte aendern sich (Diagonalen, weiche Wechsel)
	for _, k in ipairs({ "mF", "mB", "mL", "mR" }) do t[k]:Play(0, 0.001, 1) end
	local f = { char = char, hum = hum, tracks = t, busyUntil = 0, ko = false, blocking = false, speed = hum.WalkSpeed, loco = nil,
		stamina = STAMINA_MAX, lastSpend = 0, headTrauma = 0, bodyTrauma = 0, groundTrauma = 0,
		rockedUntil = 0, lastTraumaAt = 0, gnpHits = 0, gnpLast = 0 }
	char:SetAttribute("CC_Stamina", STAMINA_MAX)
	char:SetAttribute("CC_HeadTrauma", 0); char:SetAttribute("CC_BodyTrauma", 0); char:SetAttribute("CC_GroundTrauma", 0)
	char:SetAttribute("CC_Rocked", false); char:SetAttribute("CC_RockLevel", 0)
	for _, region in ipairs(INJURY_REGIONS) do
		if char:GetAttribute("CC_Injury_" .. region) == nil then char:SetAttribute("CC_Injury_" .. region, 0) end
	end
	char:SetAttribute("CC_Mobility", 100); char:SetAttribute("CC_MobilitySpeed", f.speed)
	fighters[char] = f
	-- Fokus: neues Match (CC_Match setzt CC_FocusReset) = 0; Test-Modus (CC_TestSignature) = voll
	char:GetAttributeChangedSignal("CC_FocusReset"):Connect(function()
		local test = workspace:GetAttribute("CC_TestSignature") and game.Players:GetPlayerFromCharacter(char)
		f.focus = test and 100 or 0; char:SetAttribute("CC_Focus", f.focus)
	end)
	char.AncestryChanged:Connect(function() if not char.Parent then fighters[char] = nil end end)
	return f
end

-- Fussarbeit: vier synchrone Loops (vor/zurueck/links/rechts) nach Bewegungsrichtung relativ zur Blickrichtung gewichtet.
-- Abspieltempo = tatsaechliche Geschwindigkeit / 6 (Loops sind fuer WalkSpeed 6 gebaut) -> Standfuss bleibt stehen.
local MOVE_KEYS = { "mF", "mB", "mL", "mR" }
-- Locker-Modus: ausserhalb eines Kampfs (kein CC_Opponent) aufrecht stehen, normal gehen (1,80 m/s = 6,4 Studs/s) und laufen
-- (4,2 m/s = 15 Studs/s); Abspieltempo = Geschwindigkeit / gebaute Geschwindigkeit. Im Kampf: Kampfstellung + Fussarbeit.
local CASUAL_WALK_REF, CASUAL_RUN_REF = 1.80 / 0.28, 4.20 / 0.28
local function isCasual(f) return not f.char:GetAttribute("CC_Opponent") and not f.char:GetAttribute("CC_BagPractice") and not f.wr and not f.down and not f.ko end
local function ensure(tr, w) if not tr.IsPlaying then tr:Play(0.10, w or 1, 1) end end
-- Training hands ownership back to locomotion before its high-priority clips fade.
local resumeLoco = Instance.new("BindableFunction")
resumeLoco.Name = "CC_ResumeLocomotion"; resumeLoco.Parent = game.ServerStorage
resumeLoco.OnInvoke = function(char)
 local f = fighters[char]
 if not f or f.ko or f.down or f.wr then return false end
 if game.Players:GetPlayerFromCharacter(char) and isCasual(f) then return true end
 local idle = isCasual(f) and f.tracks.cIdle or f.tracks.idle
 if not idle.IsPlaying then idle:Play(0, 1, 1) end
 idle:AdjustWeight(1, 0); idle:AdjustSpeed(1)
 f.idleOff = false
 return idle.Length > 0
end
RunService.Heartbeat:Connect(function()
	for _, f in pairs(fighters) do
		local root = f.char:FindFirstChild("HumanoidRootPart")
		local t = f.tracks
		if root and isCasual(f) then
			if f.mode ~= "casual" then
				f.mode = "casual"
				t.idle:Stop(0.3)
				for _, k in ipairs(MOVE_KEYS) do t[k]:Stop(0.2) end
				for _, k in ipairs({ "limpL", "limpR" }) do t[k]:Stop(0.2) end
				for _, k in ipairs({ "block", "blockhit", "legCheck" }) do t[k]:Stop(0.2) end
			end
			-- Player locomotion is owned locally; NPCs retain the server controller.
			if not game.Players:GetPlayerFromCharacter(f.char) then
			ensure(t.cIdle); ensure(t.cWalk, 0.001); ensure(t.cRun, 0.001)
			local v = root.AssemblyLinearVelocity; local speed = Vector3.new(v.X, 0, v.Z).Magnitude
			local amount = math.clamp((speed - 0.4) / 2.0, 0, 1)
			local runK = math.clamp((speed - 9) / 4, 0, 1)
			t.cWalk:AdjustWeight(math.max(amount * (1 - runK), 0.001), 0.15); t.cWalk:AdjustSpeed(math.max(speed, 0.5) / CASUAL_WALK_REF)
			t.cRun:AdjustWeight(math.max(amount * runK, 0.001), 0.15); t.cRun:AdjustSpeed(math.max(speed, 0.5) / CASUAL_RUN_REF)
			local dom = amount < 0.05 and "idle" or (runK > 0.5 and "run" or "walk")
			if dom ~= f.loco then f.loco = dom; f.char:SetAttribute("CC_Loco", dom) end
			end
		elseif root and not f.ko and not f.wr and not f.down then
			if f.mode ~= "fight" then
				f.mode = "fight"
				for _, k in ipairs({ "cIdle", "cWalk", "cRun" }) do t[k]:Stop(0.25) end
				ensure(t.idle)
			end
			if f.idleOff then f.idleOff = false; t.idle:AdjustWeight(1, 0.15) end
			if f.wantBlock and not f.blocking and os.clock() >= f.busyUntil then setBlock(f, true) end
			if not t.mF.IsPlaying then for _, k in ipairs(MOVE_KEYS) do t[k]:Play(0, 0.001, 1) end end -- nach K.o./Reset wieder anwerfen (synchron)
			ensure(t.limpL, 0.001); ensure(t.limpR, 0.001)
			local v = root.AssemblyLinearVelocity; v = Vector3.new(v.X, 0, v.Z)
			local speed = v.Magnitude
			local fwd, side = 0, 0
			if speed > 0.05 then fwd = root.CFrame.LookVector:Dot(v) / speed; side = root.CFrame.RightVector:Dot(v) / speed end
			local amount = math.clamp((speed - 0.4) / 2.0, 0, 1)            -- weicher Einstieg aus dem Stand
			local w = { mF = math.max(fwd, 0), mB = math.max(-fwd, 0), mR = math.max(side, 0), mL = math.max(-side, 0) }
			local sum = w.mF + w.mB + w.mL + w.mR
			local legDamage, legSide = worstLeg(f)
			local limpBlend = amount * math.clamp((legDamage - 25) / 60, 0, 0.98)
			for _, k in ipairs(MOVE_KEYS) do
				local wk = (sum > 0 and (w[k] / sum) * amount or 0) * (1 - limpBlend)
				t[k]:AdjustWeight(math.max(wk, 0.001), 0.18)       -- weiche Starts, Stopps und Richtungswechsel
				t[k]:AdjustSpeed(math.max(speed, 0.5) / WALK_REF)
			end
			t.limpL:AdjustWeight(math.max(legSide == "Left" and limpBlend or 0, 0.001), 0.18)
			t.limpR:AdjustWeight(math.max(legSide == "Right" and limpBlend or 0, 0.001), 0.18)
			t.limpL:AdjustSpeed(math.max(speed, 0.5) / WALK_REF * 0.78)
			t.limpR:AdjustSpeed(math.max(speed, 0.5) / WALK_REF * 0.78)
			local dom = amount < 0.05 and "idle" or (math.abs(fwd) >= math.abs(side) and (fwd > 0 and "walk" or "back") or (side > 0 and "right" or "left"))
			if dom ~= f.loco then f.loco = dom; f.char:SetAttribute("CC_Loco", dom) end
		elseif t then
			for _, k in ipairs(MOVE_KEYS) do if t[k] then t[k]:AdjustWeight(0.001, 0.1) end end
			for _, k in ipairs({ "limpL", "limpR" }) do if t[k] then t[k]:AdjustWeight(0.001, 0.1) end end
			-- Bodenkampf/Liegen: Stand-Idle ausblenden, damit in keiner Luecke zwischen zwei Bodenanimationen die Standhaltung durchscheint
			local grounded = f.down or (f.wr and f.wr.role ~= "shoot" and f.wr.role ~= "defend")   -- beim Takedown-Ansatz stehen beide noch
			if not grounded and f.idleOff then f.idleOff = false; t.idle:AdjustWeight(1, 0.1) end
			if grounded and t.idle and not f.idleOff then f.idleOff = true; t.idle:AdjustWeight(0.001, 0.1) end
			if f.mode == "casual" then f.mode = nil; for _, k in ipairs({ "cIdle", "cWalk", "cRun" }) do t[k]:Stop(0.2) end end
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
		f.blockStart = os.clock()
		f.tracks.block:Play(0.08)
		task.delay(f.tracks.block.Length - 0.02, function() if f.blocking then f.tracks.block:AdjustSpeed(0) end end)
		f.hum.WalkSpeed = math.min(BLOCK_SPEED, injuryWalkSpeed(f))
	else
		f.blockStart = nil
		f.tracks.block:AdjustSpeed(1); f.tracks.block:Stop(0.12); f.tracks.blockhit:Stop(0.1); f.tracks.legCheck:Stop(0.1)
		f.hum.WalkSpeed = injuryWalkSpeed(f)
	end
end

local function knockout(f, kind)
	setBlock(f, false)
	f.rockedUntil = 0
	f.char:SetAttribute("CC_Rocked", false); f.char:SetAttribute("CC_RockLevel", 0)
	f.knockToken = (f.knockToken or 0) + 1
	f.knocked = false
	f.char:SetAttribute("CC_Knockdown", nil)
	f.char:SetAttribute("CC_Count", nil)
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
		if ms and (ms:GetAttribute("State") == "over" or ms:GetAttribute("State") == "finisher") then return end -- liegen bleiben; das Runden-System setzt beim Neustart zurueck
		ko:Stop(0.4)
		f.hum.Health = f.hum.MaxHealth
		f.hum.WalkSpeed = f.speed
		f.ko = false
		f.char:SetAttribute("CC_KO", false)
	end)
end

local function knockdown(f, kind)
	setBlock(f, false)
	f.rockedUntil = 0
	f.headTrauma = (f.headTrauma or 0) * 0.48
	f.bodyTrauma = (f.bodyTrauma or 0) * 0.62
	f.char:SetAttribute("CC_Rocked", false); f.char:SetAttribute("CC_RockLevel", 0)
	f.char:SetAttribute("CC_HeadTrauma", math.floor(f.headTrauma + 0.5))
	f.char:SetAttribute("CC_BodyTrauma", math.floor(f.bodyTrauma + 0.5))
	f.knockdowns = (f.knockdowns or 0) + 1
	f.char:SetAttribute("CC_Knockdowns", f.knockdowns)
	if f.knockdowns >= 3 then
		f.char:SetAttribute("CC_Stoppage", "TKO")
		knockout(f, kind)
		return false
	end
	f.knockToken = (f.knockToken or 0) + 1
	local token = f.knockToken
	f.knocked = true
	f.hum.WalkSpeed = 0
	f.hum.Health = HP_FLOOR
	for k, tr in pairs(f.tracks) do if k ~= "idle" and k ~= (kind or "ko") then tr:Stop(0.08) end end
	local fall = f.tracks[kind or "ko"]
	fall:Play(0.08)
	f.char:SetAttribute("CC_LastReact", "knockdown")
	f.char:SetAttribute("CC_Knockdown", true)
	if f.knockdowns >= 2 then f.char:SetAttribute("CC_DoctorRisk", true) end
	task.spawn(function()
		for count = 1, 8 do
			if not f.char.Parent or f.knockToken ~= token or not f.knocked then return end
			local ms = RS:FindFirstChild("CC_MatchState")
			if ms and ms:GetAttribute("State") ~= "fight" then return end
			f.char:SetAttribute("CC_Count", count)
			task.wait(0.65)
		end
		if not f.char.Parent or f.knockToken ~= token or not f.knocked then return end
		fall:Stop(0.3)
		if not f.tracks.idle.IsPlaying then f.tracks.idle:Play(0.2) end
		f.hum.Health = math.max(22, f.hum.MaxHealth * 0.22)
		f.hum.WalkSpeed = injuryWalkSpeed(f)
		f.knocked = false
		f.char:SetAttribute("CC_Knockdown", nil)
		f.char:SetAttribute("CC_Count", nil)
		f.char:SetAttribute("CC_LastReact", "recovered")
		f.busyUntil = os.clock() + 0.8
	end)
	return true
end

-- Lokaler, trefferzonenabhaengiger Schaden. Er heilt waehrend eines Kampfes nicht.
-- Beine steuern Humpeln/Mobilitaet; schwere Arm-/Rippenverletzungen und ein voll zerstoertes Bein beenden den Kampf.
local function updateMobility(f)
	local legDamage = worstLeg(f)
	local factor = mobilityFactor(f)
	f.char:SetAttribute("CC_LegDamage", legDamage)
	f.char:SetAttribute("CC_Mobility", math.floor(factor * 100 + 0.5))
	f.char:SetAttribute("CC_MobilitySpeed", injuryWalkSpeed(f))
	if not f.ko and not f.knocked and not f.blocking and not f.wr and not f.down and f.char:GetAttribute("CC_Frozen") ~= true then
		f.hum.WalkSpeed = injuryWalkSpeed(f)
	end
end
local function applyInjury(f, region, amount, source)
	if not (f and region and amount and amount > 0) or f.ko then return nil end
	local key = "CC_Injury_" .. region
	local old = injury(f, region)
	local new = math.clamp(old + amount, 0, 100)
	f.char:SetAttribute(key, new)
	if region == "LeftLeg" or region == "RightLeg" then updateMobility(f) end
	local stage = new >= 100 and 4 or new >= 85 and 3 or new >= 60 and 2 or new >= 30 and 1 or 0
	local oldStage = old >= 100 and 4 or old >= 85 and 3 or old >= 60 and 2 or old >= 30 and 1 or 0
	if stage > oldStage then
		f.char:SetAttribute("CC_InjuryEvent", region .. "|" .. stage .. "|" .. tostring(workspace:GetServerTimeNow()))
	end
	if (region == "Nose" or region == "Head") and new >= 85 or region == "Ribs" and new >= 90 then
		f.char:SetAttribute("CC_DoctorRisk", true)
	end
	if new >= 100 then
		f.char:SetAttribute("CC_Broken_" .. region, true)
		if region == "LeftLeg" or region == "RightLeg" or region == "LeftArm" or region == "RightArm" or region == "Ribs" then
			f.char:SetAttribute("CC_Stoppage", region == "Ribs" and "BODY_TKO" or (region:find("Leg") and "LEG_TKO" or "ARM_TKO"))
			knockout(f, region == "Ribs" and "koFwd" or "ko")
			return "stopped"
		end
	end
	if (region == "LeftLeg" or region == "RightLeg") and new >= 85 and source == "strike" and (old < 85 or math.random() < 0.35) then
		return "fall"
	end
	if stage > oldStage then return "event" end
	return nil
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
local function hitFX(char, strength, kind, detail)
	local zone = type(detail) == "table" and detail.zone or nil
	local move = type(detail) == "table" and detail.move or nil
	local kick = type(move) == "string" and move:find("kick") ~= nil
	if kind == "hit" or kind == "stagger" then
		if detail == "ground" then sfx(char, "CanvasImpact")
		elseif kick then sfx(char, "KickHit")
		elseif zone == "body" or zone == "leg" then sfx(char, "BodyHit")
		elseif zone == "head" then sfx(char, kind == "stagger" and "HitHeavy" or "HeadHit")
		else sfx(char, strength > 0.4 and "HitHeavy" or "HitLight") end
	elseif kind == "block" and strength > 0.12 then sfx(char, "Block", kick and 0.92 or 1.15)
	elseif kind == "legcheck" then sfx(char, "LegCheck", 0.82)
	elseif kind == "knockdown" then
		sfx(char, "HitHeavy", 0.84); task.delay(0.45, function() sfx(char, "CanvasImpact") end)
		game.ReplicatedStorage.CC_MatchState:SetAttribute("CrowdBoost", os.clock())
	elseif kind == "ko" then
		sfx(char, detail == "submission" and "Submission" or "HitHeavy", detail == "submission" and 0.82 or 0.85)
		task.delay(0.7, function() sfx(char, "CanvasImpact") end)
		game.ReplicatedStorage.CC_MatchState:SetAttribute("CrowdBoost", os.clock())
	end
	local p = game.Players:GetPlayerFromCharacter(char)
	if p then RS.CC_HitFX:FireClient(p, strength, kind) end
end

-- laufenden Angriff abbrechen (wer getroffen wird, schlaegt nicht weiter)
local function interrupt(f)
	f.attackToken = (f.attackToken or 0) + 1
	for move in pairs(MOVES) do
		if f.tracks[move].IsPlaying then f.tracks[move]:Stop(0.08) end
	end
	if f.sigTrack and f.sigTrack.IsPlaying then            -- laufende Signatur: keine Rest-Treffer, keine spaeten Effekte
		f.sigTrack:Stop(0.1)
		if RS:FindFirstChild("CC_SigFX") then RS.CC_SigFX:FireAllClients("cancel", f.char) end
	end
	f.sigActive = false
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
local function pointSegmentDistance(point, a, b)
	local ab = b - a
	local denom = ab:Dot(ab)
	if denom < 0.0001 then return (point - b).Magnitude end
	local t = math.clamp((point - a):Dot(ab) / denom, 0, 1)
	return (point - (a + ab * t)).Magnitude
end
local function spend(f, amount)
	f.stamina = math.max(0, f.stamina - amount); f.lastSpend = os.clock()
	f.char:SetAttribute("CC_Stamina", math.floor(f.stamina + 0.5))
end
-- Ausdauer-Erholung (nicht waehrend Block und kurz nach einer Aktion)
RunService.Heartbeat:Connect(function(dt)
	for _, f in pairs(fighters) do
		local smax = staminaMax(f)
		if f.char:GetAttribute("CC_StaminaMax") ~= smax then f.char:SetAttribute("CC_StaminaMax", smax) end
		if f.stamina < smax and os.clock() - f.lastSpend > STAMINA_DELAY and not f.blocking then
			f.stamina = math.min(smax, f.stamina + STAMINA_REGEN * (1 + 0.02 * stat(f, "Cardio")) * dt)
			f.char:SetAttribute("CC_Stamina", math.floor(f.stamina + 0.5))
		end
	end
end)

local function resolveAttack(f, move, landed)
	if f.lastResolvedMove == move and f.lastResolvedAt and os.clock() - f.lastResolvedAt < 2.2 then f.repeatCount = (f.repeatCount or 1) + 1
	else f.repeatCount = 1 end
	f.lastResolvedMove = move
	f.lastResolvedAt = os.clock()
	if landed then f.lastLandedAt = os.clock() else f.lastMissAt = os.clock() end
end

local function isAttacking(f)
	if f.sigActive then return true end
	for move in pairs(MOVES) do
		local tr = f.tracks[move]
		if tr and tr.IsPlaying then return true end
	end
	return false
end

local function syncTrauma(f)
	f.char:SetAttribute("CC_HeadTrauma", math.floor((f.headTrauma or 0) + 0.5))
	f.char:SetAttribute("CC_BodyTrauma", math.floor((f.bodyTrauma or 0) + 0.5))
	f.char:SetAttribute("CC_GroundTrauma", math.floor((f.groundTrauma or 0) + 0.5))
end

local function setRocked(f, trauma)
	f.rockedUntil = math.max(f.rockedUntil or 0, os.clock() + TRAUMA.ROCK_TIME)
	f.char:SetAttribute("CC_Rocked", true)
	f.char:SetAttribute("CC_RockLevel", math.clamp(math.floor(trauma + 0.5), 0, 100))
end

-- Ergebnis ist absichtlich NICHT an die Punkte/Schadenssumme gekoppelt.
-- Ein sauberer Konter bei wenig Ausdauer ist gefaehrlicher; Block und wiederholtes Spammen derselben Technik sind sicherer.
local function evaluateImpact(attacker, target, m, dmg, blocked)
	local now = os.clock()
	local counter = not blocked and isAttacking(target)
	local staminaRatio = math.clamp((target.stamina or 0) / math.max(1, staminaMax(target)), 0, 1)
	local vulnerable = 1 + (1 - staminaRatio) * 0.38
	local repeatPenalty = 1 / (1 + math.max(0, (attacker.repeatCount or 1) - 2) * 0.16)
	local heavy = m.heavy and 1.34 or 0.78
	local counterBonus = counter and 1.28 or 1
	local sigBonus = attacker.sigActive and 1.16 or 1
	local impact = dmg * heavy * vulnerable * repeatPenalty * counterBonus * sigBonus
	if blocked then impact *= 0.08 end

	target.lastTraumaAt = now
	if m.zone == "head" then target.headTrauma = math.min(130, (target.headTrauma or 0) + impact)
	elseif m.zone == "body" then target.bodyTrauma = math.min(115, (target.bodyTrauma or 0) + impact) end
	syncTrauma(target)
	if blocked then return nil, counter end

	local rocked = now < (target.rockedUntil or 0)
	if m.zone == "head" then
		local trauma = target.headTrauma or 0
		local accumulatedKO = trauma >= TRAUMA.HEAD_KO and impact >= 29 and (counter or attacker.sigActive or (target.knockdowns or 0) >= 1)
		-- Seltener echter One-shot: nur ein harter Kopftreffer als sauberer Konter gegen einen erschoepften/verwundbaren Gegner
		-- oder eine geladene Signatur. Normale Treffer bleiben Knockdowns statt Zufalls-K.o.
		local oneShotKO = m.heavy and impact >= 34 and (counter or attacker.sigActive) and ((m.damage or 0) >= 16 or attacker.sigActive)
		if accumulatedKO or oneShotKO then return "ko", counter end
		if target.hum.Health <= HP_FLOOR or trauma >= TRAUMA.HEAD_KD or (rocked and m.heavy and impact >= 13) then return "knockdown", counter end
		if trauma >= TRAUMA.HEAD_ROCK and not rocked then setRocked(target, trauma); return "rocked", counter end
	elseif m.zone == "body" then
		local trauma = target.bodyTrauma or 0
		if target.hum.Health <= HP_FLOOR or trauma >= TRAUMA.BODY_KD or (rocked and m.heavy and impact >= 15) then return "knockdown", counter end
		if trauma >= TRAUMA.BODY_ROCK and not rocked then setRocked(target, trauma); return "rocked", counter end
	end
	return nil, counter
end

local function registerGroundImpact(bottom, dmg, pos)
	local now = os.clock()
	if now - (bottom.gnpLast or 0) > 2.6 then
		bottom.gnpHits = 0
		bottom.groundTrauma = math.max(0, (bottom.groundTrauma or 0) - 18)
	end
	bottom.gnpLast = now
	bottom.gnpHits = (bottom.gnpHits or 0) + 1
	local tired = 1 + (1 - math.clamp((bottom.stamina or 0) / math.max(1, staminaMax(bottom)), 0, 1)) * 0.3
	bottom.groundTrauma = math.min(100, (bottom.groundTrauma or 0) + dmg * 1.22 * tired)
	bottom.lastTraumaAt = now
	syncTrauma(bottom)
	bottom.char:SetAttribute("CC_UnansweredGroundHits", bottom.gnpHits)
	local limit = TRAUMA.GROUND_TKO[pos] or 6
	return bottom.gnpHits >= limit or bottom.groundTrauma >= 82
end

-- Trauma erholt sich langsam, Punkte und normaler Lebensschaden bleiben davon unberuehrt.
RunService.Heartbeat:Connect(function(dt)
	local now = os.clock()
	for _, f in pairs(fighters) do
		if not f.ko and not f.knocked then
			if now >= (f.rockedUntil or 0) and f.char:GetAttribute("CC_Rocked") then
				f.char:SetAttribute("CC_Rocked", false); f.char:SetAttribute("CC_RockLevel", 0)
				if not f.blocking and not f.wr and not f.down then f.hum.WalkSpeed = injuryWalkSpeed(f) end
			end
			if now - (f.lastTraumaAt or 0) > TRAUMA.DECAY_DELAY then
				local oldH, oldB, oldG = f.headTrauma or 0, f.bodyTrauma or 0, f.groundTrauma or 0
				f.headTrauma = math.max(0, oldH - 1.15 * dt)
				f.bodyTrauma = math.max(0, oldB - 0.85 * dt)
				f.groundTrauma = math.max(0, oldG - 1.4 * dt)
				if math.floor(oldH) ~= math.floor(f.headTrauma) or math.floor(oldB) ~= math.floor(f.bodyTrauma) or math.floor(oldG) ~= math.floor(f.groundTrauma) then syncTrauma(f) end
			end
		end
	end
end)

local function land(attacker, target, move, m, track, hitRegion)
	if frozen(attacker) or frozen(target) then return end
	-- Ali-Signatur "Instinkt": Treffer gegen den Instinkt-Kaempfer werden automatisch ausgewichen (begrenzte Anzahl)
	local tInst = target.instinct
	if tInst and os.clock() < tInst.untilT and (tInst.dodges or 0) > 0 and not target.ko and not target.down and not target.wr then
		tInst.dodges -= 1
		target.char:SetAttribute("CC_InstinctDodges", tInst.dodges)
		local side = (math.random() < 0.5) and "left" or "right"
		local tr = target.tracks[side]
		if tr then tr:Play(0.04, 1, 1.8); task.delay(0.32, function() if tr.IsPlaying then tr:Stop(0.1) end end) end
		fightEvent:Fire("dodge", target.char, attacker.char, move, false)
		sigFX:FireAllClients("dodge", target.char, attacker.char, side)
		print(("[CC] %s weicht %s von %s aus (Instinkt, noch %d)"):format(target.char.Name, move, attacker.char.Name, tInst.dodges))
		return
	end
	local aInst = attacker.instinct
	local calf = aInst and os.clock() < aInst.untilT and move == "lowkick" and not target.blocking
	if calf then
		m = table.clone(m); m.damage = m.damage * (SIG.list.ali.calfMult or 2.5); m.heavy = true
	end
	resolveAttack(attacker, move, true)
	local blocked = target.blocking
	local goodCheck = move == "lowkick" and blocked and target.blockStart and os.clock() - target.blockStart <= 0.55
	if goodCheck then
		target.checkToken = (target.checkToken or 0) + 1
		local checkToken = target.checkToken
		target.tracks.block:Stop(0.04); target.tracks.legCheck:Play(0.04, 1, 0.65)
		target.busyUntil = math.max(target.busyUntil, os.clock() + 0.38)
		target.char:SetAttribute("CC_LegCheck", workspace:GetServerTimeNow())
		target.char:SetAttribute("CC_Checks", (target.char:GetAttribute("CC_Checks") or 0) + 1)
		attacker.hum.Health = math.max(HP_FLOOR, attacker.hum.Health - 4)
		addDamage(target.char, 4)
		local result = applyInjury(attacker, limbRegionForMove(m) or "RightLeg", 18, "check")
		spend(attacker, 4)
		fightEvent:Fire("check", target.char, attacker.char, move, true)
		hitFX(target.char, 0.35, "legcheck", { zone = "leg", move = move })
		hitFX(attacker.char, 0.55, "hit", { zone = "leg", move = move })
		if result ~= "stopped" then interrupt(attacker); react(attacker, "hitLeg", 0.55) end
		task.delay(0.38, function()
			if target.checkToken ~= checkToken then return end
			target.tracks.legCheck:Stop(0.1)
			if target.blocking and not target.ko then target.tracks.block:Play(0.08) end
		end)
		print(("[CC] %s checkt den Low Kick von %s"):format(target.char.Name, attacker.char.Name))
		return
	end
	local blockFactor = blocked and (m.zone == "leg" and 0.55 or (m.bodyShot and 0.5 or BLOCK_FACTOR)) or 1   -- hohe Deckung schuetzt den Koerper nur halb; ein zu frueher Leg-Block ist kein perfekter Check
	local tired = attacker.stamina < LOW_STAMINA and 0.7 or 1
	local lvDmg = (attacker.char == workspace:FindFirstChild("CC_TrainingDummy") and DummyLevel) and DummyLevel().dmg or 1   -- Trainingsgegner-Stufe
	local dmg = m.damage * blockFactor * tired * lvDmg * limbPower(attacker, m) * (1 + 0.015 * stat(attacker, "Power"))
	target.hum.Health = math.max(HP_FLOOR, target.hum.Health - dmg)
	addDamage(attacker.char, dmg)
	if calf then
		-- Instinkt-Calf-Kick: schwere Bein-Verletzung, Effekt, Modus endet
		applyInjury(target, "LeftLeg", SIG.list.ali.calfInjury or 35, "calf")
		aInst.untilT = 0; attacker.char:SetAttribute("CC_Instinct", nil)
		sigFX:FireAllClients("calf", attacker.char, target.char, dmg)
		local pl = game.Players:GetPlayerFromCharacter(attacker.char)
		if pl and pl:GetAttribute("CC_SigTrial") == "ali" then
			pl:SetAttribute("CC_SigTrial", nil)
			local pe = game.ServerStorage:FindFirstChild("CC_ProfileEvent"); if pe then pe:Fire(pl, "sig_unlock", "ali") end
			pl:SetAttribute("CC_SigLearned", "ali|" .. workspace:GetServerTimeNow())
		end
		print(("[CC] %s Instinkt-Calf-Kick -> %s (%.0f Schaden)"):format(attacker.char.Name, target.char.Name, dmg))
	end
	local impactOutcome, wasCounter = evaluateImpact(attacker, target, m, dmg, blocked)
	if wasCounter then
		attacker.char:SetAttribute("CC_CounterHits", (attacker.char:GetAttribute("CC_CounterHits") or 0) + 1)
		target.char:SetAttribute("CC_CounteredAt", workspace:GetServerTimeNow())
	end
	if blocked then
		spend(target, 4)
		attacker.char:SetAttribute("CC_BlockedHits", (attacker.char:GetAttribute("CC_BlockedHits") or 0) + 1)
		target.char:SetAttribute("CC_Blocks", (target.char:GetAttribute("CC_Blocks") or 0) + 1)
	else
		attacker.char:SetAttribute("CC_StrikesLanded", (attacker.char:GetAttribute("CC_StrikesLanded") or 0) + 1)
		attacker.char:SetAttribute("CC_LastHitMove", move)
		if move == "jab" then attacker.char:SetAttribute("CC_JabHits", (attacker.char:GetAttribute("CC_JabHits") or 0) + 1) end
		if move == "lowkick" or move == "bodykick" or move == "highkick" or move == "frontkick" then attacker.char:SetAttribute("CC_KickHits", (attacker.char:GetAttribute("CC_KickHits") or 0) + 1) end
		local zoneKey = m.zone == "head" and "CC_HeadHits" or "CC_BodyHits"
		attacker.char:SetAttribute(zoneKey, (attacker.char:GetAttribute(zoneKey) or 0) + 1)
		if m.zone == "head" then target.char:SetAttribute("CC_HeadDamage", (target.char:GetAttribute("CC_HeadDamage") or 0) + dmg) end
		-- Das Publikum reagiert auch auf klare schwere Treffer, mit Cooldown gegen Audio-Spam.
		if m.heavy and (m.zone == "head" or dmg >= 10) and os.clock() >= (attacker.crowdAt or 0) then
			attacker.crowdAt = os.clock() + 2.5
			game.ReplicatedStorage.CC_MatchState:SetAttribute("CrowdBoost", os.clock())
		end
	end
	local injuryResult
	local region = hitRegion or m.injuryRegion or (m.zone == "head" and "Head" or (m.zone == "body" and "Ribs" or nil))
	if blocked and m.zone == "leg" then
		injuryResult = applyInjury(target, region, (m.injury or 10) * 0.45, "strike")
	elseif blocked then
		local armRegion = (m.limb == "RightHand" or m.limb == "RightFoot" or m.limb == "RightLowerLeg") and "LeftArm" or "RightArm"
		injuryResult = applyInjury(target, armRegion, m.heavy and 6 or 2, "block")
	elseif region then
		injuryResult = applyInjury(target, region, m.injury or math.max(3, dmg * 0.7), "strike")
	end
	fightEvent:Fire("hit", attacker.char, target.char, move, blocked)
	if not attacker.sigActive then                                     -- Signatur-Treffer laden keinen neuen Fokus
		if blocked then focusGain(attacker, "blockedHit"); focusGain(target, "block")
		else focusGain(attacker, m.heavy and "heavy" or "hit") end
	end
	print(("[CC] %s %s -> %s %.0f%s"):format(attacker.char.Name, move, target.char.Name, target.hum.Health, blocked and " (geblockt)" or ""))
	-- Treffer-Stopp: Glied bleibt an der Oberflaeche stehen (Hitstop) und springt dann in die Rueckzugsphase,
	-- statt durch den Koerper des Gegners weiterzulaufen
	track:AdjustSpeed(0.02)
	task.delay(blocked and HITSTOP * 0.5 or HITSTOP, function()
		if not track.IsPlaying then return end
		local back = m.win[2] + 0.04
		if not m.noRewind and track.TimePosition < back then track.TimePosition = back end   -- Signatur: kein Vorspringen (zweiter Schlag folgt)
		track:AdjustSpeed(attacker.animSpeed or 1)
	end)
	if target.ko and injuryResult == "stopped" then
		print("[CC] Verletzungs-T.K.O.!", target.char.Name, target.char:GetAttribute("CC_Stoppage"))
		hitFX(target.char, 1.0, "ko", { zone = m.zone, move = move })
		hitFX(attacker.char, 0.6, "land")
	elseif injuryResult == "fall" then
		interrupt(target)
		local counting = knockdown(target, "ko")
		print("[CC] Leg Health Event!", target.char.Name)
		hitFX(target.char, 1.0, counting and "knockdown" or "ko", { zone = "leg", move = move })
		hitFX(attacker.char, 0.6, "land")
	elseif impactOutcome == "ko" then
		interrupt(target)
		target.char:SetAttribute("CC_Stoppage", "KO")
		knockout(target, m.ko)
		print("[CC] Flash K.O.!", target.char.Name, move)
		hitFX(target.char, 1.0, "ko", { zone = m.zone, move = move, counter = wasCounter })
		hitFX(attacker.char, 0.7, "land")
	elseif impactOutcome == "knockdown" or target.hum.Health <= HP_FLOOR then
		interrupt(target)
		local counting = knockdown(target, m.ko)
		print(counting and "[CC] Knockdown!" or "[CC] T.K.O.!", target.char.Name, m.ko)
		hitFX(target.char, 1.0, counting and "knockdown" or "ko", { zone = m.zone, move = move, counter = wasCounter })
		hitFX(attacker.char, 0.6, "land")
	elseif impactOutcome == "rocked" then
		interrupt(target)
		react(target, "stagger", 1.05)
		target.hum.WalkSpeed = math.min(2, injuryWalkSpeed(target))
		spend(target, m.heavy and 5 or 3)
		hitFX(target.char, 0.85, "stagger", { zone = m.zone, move = move, counter = wasCounter })
		hitFX(attacker.char, 0.35, "land")
	elseif blocked and blockFactor < 0.4 then
		target.tracks.blockhit:Play(0.03)
		hitFX(target.char, 0.15, "block"); hitFX(attacker.char, 0.1, "block")
	else
		interrupt(target)
		react(target, m.react, m.heavy and 0.4 or 0.3)
		hitFX(target.char, m.heavy and 0.5 or 0.3, "hit", { zone = m.zone, move = move })
		spend(target, m.heavy and 4 or 2)
		hitFX(attacker.char, m.heavy and 0.3 or 0.15, "land")
	end
end

local function attack(attacker, move)
	local m = MOVES[move]
	if not m or attacker.ko or attacker.knocked or attacker.blocking or attacker.wr or attacker.down or frozen(attacker) then return end
	local now = os.clock()
	if now < attacker.busyUntil then
		-- Kombination: kurz vor Ende der Sperre gedrueckt -> genau EINE Eingabe merken (kein Dauerfeuer)
		if attacker.busyUntil - now <= BUFFER and not attacker.queued then
			attacker.queued = move
			task.delay(attacker.busyUntil - now + 0.01, function() local q = attacker.queued; attacker.queued = nil; if q then attack(attacker, q) end end)
		end
		return
	end
	local ribs = injury(attacker, "Ribs")
	local cost = m.cost * (1 + math.max(0, ribs - 30) / 140)
	if attacker.stamina < cost then attacker.char:SetAttribute("CC_Tired", workspace:GetServerTimeNow()); return end
	spend(attacker, cost)
	-- Continuous exhaustion affects the whole clip, including the hand returning.
 local staminaRatio = attacker.stamina / staminaMax(attacker)
 local fatigue = math.clamp((0.45 - staminaRatio) / 0.35, 0, 1)
 local speed = (1 - 0.30 * fatigue) * limbPower(attacker, m)
 attacker.char:SetAttribute("CC_AttackSpeed", speed)
	attacker.animSpeed = speed
	attacker.busyUntil = now + m.lock / math.max(speed, 0.45)
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
	local previousLimb = nil
	local opponentName = attacker.char:GetAttribute("CC_Opponent")
	local conn
	conn = RunService.Heartbeat:Connect(function()
		if frozen(attacker) then conn:Disconnect(); if track.IsPlaying then track:Stop(0.08) end; return end
		local t = (os.clock() - t0) * speed
		if done or attacker.ko or not attacker.char.Parent or attacker.attackToken ~= token or t > m.win[2] then
			conn:Disconnect()
			-- Hinweis nur dann, wenn die sichtbare Gliedmasse die Zielzone klar verfehlt hat.
			if not done and attacker.attackToken == token and not attacker.ko and dmin > 0.35 and dmin < math.huge then
				attacker.char:SetAttribute("CC_OutOfRange", workspace:GetServerTimeNow())
			end
			if not done and attacker.attackToken == token then resolveAttack(attacker, move, false) end
			if not done and workspace:GetAttribute("CC_DebugHits") then print(("[CC] %s %s verfehlt, Oberflaechenabstand %.2f"):format(attacker.char.Name, move, dmin)) end
			return
		end
		if t < m.win[1] then return end
		local limb = bonePos(attacker.char, m.limb, LIMB_OFFSET[m.limb])
		if not limb then return end
		local sweepFrom = previousLimb or limb
		local attackerRoot = attacker.char:FindFirstChild("HumanoidRootPart")
		for _, target in pairs(fighters) do
			local targetRoot = target.char:FindFirstChild("HumanoidRootPart")
			local isOpponent = not opponentName or opponentName == "" or target.char.Name == opponentName
			if target ~= attacker and isOpponent and targetRoot and attackerRoot and not target.ko and not target.knocked and not target.wr and not target.down then
				local flat = Vector3.new(targetRoot.Position.X - attackerRoot.Position.X, 0, targetRoot.Position.Z - attackerRoot.Position.Z)
				local facing = flat.Magnitude < 0.05 or Vector3.new(attackerRoot.CFrame.LookVector.X, 0, attackerRoot.CFrame.LookVector.Z).Unit:Dot(flat.Unit) >= m.facing
				for _, z in ipairs(ZONES[m.zone]) do
					local zp = bonePos(target.char, z.bone, z.along)
					if zp then
						local surfaceDistance = pointSegmentDistance(zp, sweepFrom, limb) - z.radius - m.hitRadius
						dmin = math.min(dmin, surfaceDistance)
						if flat.Magnitude <= m.maxRange and facing and surfaceDistance <= 0 then
							done = true; conn:Disconnect()
							land(attacker, target, move, m, track, z.region or m.injuryRegion)
							return
						end
					end
				end
			end
		end
		previousLimb = limb
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
	"Ground_Mount_Punch", "Ground_Mount_To_Back", "Ground_Back_Idle", "Sub_RNC", "Sub_Armbar", "TD_LiftSlam" }) do  -- TD_LiftSlam: Khabib-Signatur (Wrestling_Prototype_v04)  -- zweite/dritte Zeile: Ground_Positions_v01 (E)
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
-- Paar-/Bodenwechsel muessen ohne einen einzigen ungewichteten Frame erfolgen. Sonst zeigt R15 kurz
-- die Bindepose (T-Pose) oder die Standhaltung zwischen Takedown und Bodenkampf.
local WR_FADE = 0.10
-- Die neue Spur zuerst mit Minimalgewicht starten, auf das Laden warten und erst dann die alte Spur ausblenden.
-- Dadurch bleibt die letzte gueltige Pose sichtbar, selbst wenn ein Asset beim ersten Einsatz noch nachlaedt.
local function stopOthersWhenLoaded(f, keep, others, fade)
	f.animToken = (f.animToken or 0) + 1
	local token = f.animToken
	task.spawn(function()
		local t0 = os.clock()
		while keep.IsPlaying and keep.Length == 0 and os.clock() - t0 < 1.5 do RunService.Heartbeat:Wait() end
		if f.animToken ~= token or not keep.IsPlaying or keep.Length == 0 then return end
		-- Length kann bereits bekannt sein, bevor Roblox die erste Pose wirklich ausgewertet hat.
		-- Zwei volle Animationsframes lang bleibt deshalb die alte Pose unangetastet.
		RunService.Heartbeat:Wait()
		RunService.Heartbeat:Wait()
		if f.animToken ~= token or not keep.IsPlaying then return end
		keep:AdjustWeight(1, fade)
		for _, tr in ipairs(others) do if tr ~= keep and tr.IsPlaying then tr:Stop(fade) end end
	end)
end
local function playPair(a, b, pair, looped)
	local ta, tb = wrTrack(a, pair .. "_A"), wrTrack(b, pair .. "_B")
	local oldA, oldB = {}, {}
	for _, tr in pairs(a.wrTracks or {}) do if tr ~= ta and tr.IsPlaying then table.insert(oldA, tr) end end
	for _, tr in pairs(a.dnTracks or {}) do if tr.IsPlaying then table.insert(oldA, tr) end end
	for _, tr in pairs(b.wrTracks or {}) do if tr ~= tb and tr.IsPlaying then table.insert(oldB, tr) end end
	for _, tr in pairs(b.dnTracks or {}) do if tr.IsPlaying then table.insert(oldB, tr) end end
	ta.Looped = looped or false; tb.Looped = looped or false
	ta.Priority = Enum.AnimationPriority.Action4; tb.Priority = Enum.AnimationPriority.Action4
	if ta.IsPlaying then ta:AdjustSpeed(1); ta:AdjustWeight(math.max(ta.WeightCurrent, 0.05), 0)
	else ta:Play(0, 0.05, 1) end
	if tb.IsPlaying then tb:AdjustSpeed(1); tb:AdjustWeight(math.max(tb.WeightCurrent, 0.05), 0)
	else tb:Play(0, 0.05, 1) end
	stopOthersWhenLoaded(a, ta, oldA, WR_FADE)
	stopOthersWhenLoaded(b, tb, oldB, WR_FADE)
	return ta, tb
end
-- Einzelne Ringkampfspur ohne Bindeposen-Luecke wechseln: neue Spur zuerst starten/laden,
-- erst danach alte Ring-/Bodenspuren ausblenden.
local function playWrSolo(f, key, fade, speed, looped, timePosition)
	local tr = wrTrack(f, key)
	local old = {}
	for _, t in pairs(f.wrTracks or {}) do if t ~= tr and t.IsPlaying then table.insert(old, t) end end
	for _, t in pairs(f.dnTracks or {}) do if t ~= tr and t.IsPlaying then table.insert(old, t) end end
	tr.Looped = looped or false
	tr.Priority = Enum.AnimationPriority.Action4
	local requestedSpeed = speed or 1
	if tr.IsPlaying then
		tr:AdjustWeight(math.max(tr.WeightCurrent, 0.05), 0)
		tr:AdjustSpeed(requestedSpeed < 0 and 0 or requestedSpeed)
	else
		tr:Play(0, 0.05, requestedSpeed < 0 and 0 or requestedSpeed)
	end
	if timePosition then tr.TimePosition = timePosition end
	if requestedSpeed < 0 then tr:AdjustSpeed(requestedSpeed) end
	stopOthersWhenLoaded(f, tr, old, fade or WR_FADE)
	return tr
end
local function setWrestle(f, partner, role)
	f.wr = role and { role = role, partner = partner } or nil
	f.char:SetAttribute("CC_Wrestle", role or false)
	if not role then for _, k in ipairs({ "CC_GroundPos", "CC_SubProgress", "CC_SubName", "CC_SubRole", "CC_GroundAction", "CC_GroundActionStart", "CC_GroundActionDuration", "CC_GroundActionFrom", "CC_GroundActionTo", "CC_CounterUntil", "CC_CounterLabel" }) do f.char:SetAttribute(k, nil) end end
	f.char.HumanoidRootPart.Anchored = role ~= nil
end
local function blendToStanding(f, fade)
	local idle = f.tracks.idle
	if not idle.IsPlaying then idle:Play(0, 1, 1)
	else idle:AdjustSpeed(1); idle:AdjustWeight(1, fade or WR_FADE) end
	f.idleOff = false
end

-- Austausch beenden: beide stehen wieder; HumanoidRootParts auf die End-Positionen des letzten Paars versetzen
local function endExchange(a, b, pair)
	if not (a.wr and b.wr) then return end   -- schon zurueckgesetzt (Rundenende, Abbruch, Spieler weg)
	for _, x in ipairs({ { a, "A" }, { b, "B" } }) do
		local f, s = x[1], x[2]
		local start = f.wrStart
		if start then f.char.HumanoidRootPart.CFrame = start * rootOffset(f, WR[pair .. "_" .. s].rootEnd) end
		blendToStanding(f, WR_FADE)
		wrStopAll(f, WR_FADE)
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
local function pairAlive(a, b)
	return a and b and a.char.Parent and b.char.Parent and a.wr and b.wr
		and a.wr.partner == b and b.wr.partner == a
end
local function holdPairPose(a, b)
	for _, f in ipairs({ a, b }) do
		for _, group in ipairs({ f.wrTracks or {}, f.dnTracks or {} }) do
			for _, tr in pairs(group) do if tr.IsPlaying then tr:AdjustSpeed(0) end end
		end
		if f.wr then f.wr.state = "over" end
		f.wantEscape = nil
	end
end
local function pairCancelled(a, b)
	if not pairAlive(a, b) then return true end
	if frozen(a) or frozen(b) then holdPairPose(a, b); return true end
	return false
end
-- Paar-Animation rueckwaerts (Konter / Befreien = Uebergang zurueck); Dauer aus den Blender-Daten
local function pairLen(pair) return WR[pair .. "_A"].len end
-- Nicht bis zum Stopped-Ereignis warten: dann ist die Pose bereits auf Null gefallen. Kurz vor dem Ende
-- halten wir den letzten Frame, bis die Anschlussanimation gestartet ist.
local function holdTrackEnd(tr, len, lead, cancelled)
	if not tr then return false end
	local target = math.max(0, len - (lead or WR_FADE))
	local deadline = os.clock() + math.max(2, len + 1)
	while tr.IsPlaying and tr.TimePosition < target and os.clock() < deadline do
		if cancelled and cancelled() then return false end
		RunService.Heartbeat:Wait()
	end
	if cancelled and cancelled() then return false end
	if tr.IsPlaying and tr.TimePosition >= target then tr:AdjustSpeed(0) end
	return true
end
local function reversePair(top, bottom, pair, from)
	local ta, tb = wrTrack(top, pair .. "_A"), wrTrack(bottom, pair .. "_B")
	if not ta.IsPlaying then
		ta, tb = playPair(top, bottom, pair, false)
		ta:AdjustSpeed(0); tb:AdjustSpeed(0)
	end
	local t = from or (pairLen(pair) - 0.02)
	ta.TimePosition, tb.TimePosition = t, t
	ta:AdjustSpeed(-1); tb:AdjustSpeed(-1)
	local deadline = os.clock() + t
	while os.clock() < deadline do
		if pairCancelled(top, bottom) then return false end
		RunService.Heartbeat:Wait()
	end
	return not pairCancelled(top, bottom)
end
-- hat der Gegner gekontert? Spieler: F seit Beginn des Versuchs; Trainingsgegner: Zufall
local function countered(f, t0, chance)
	if isDummy(f) then return not passive(f) and math.random() < chance * (DummyLevel and DummyLevel().ground or 1) end
	return f.sprawlAt ~= nil and f.sprawlAt >= t0 - 0.15
end
local function clearGroundFeedback(f)
	if not f or not f.char then return end
	for _, key in ipairs({ "CC_GroundAction", "CC_GroundActionStart", "CC_GroundActionDuration", "CC_GroundActionFrom", "CC_GroundActionTo", "CC_CounterUntil", "CC_CounterLabel" }) do
		f.char:SetAttribute(key, nil)
	end
end
local function startGroundAction(f, label, duration, fromPos, toPos)
	if not f or not f.char then return end
	f.char:SetAttribute("CC_GroundAction", label)
	f.char:SetAttribute("CC_GroundActionStart", workspace:GetServerTimeNow())
	f.char:SetAttribute("CC_GroundActionDuration", math.max(duration or 0.1, 0.1))
	f.char:SetAttribute("CC_GroundActionFrom", fromPos)
	f.char:SetAttribute("CC_GroundActionTo", toPos)
end
local function openCounterWindow(f, duration, label)
	if not f or not f.char then return end
	local untilTime = workspace:GetServerTimeNow() + duration
	f.char:SetAttribute("CC_CounterUntil", untilTime)
	f.char:SetAttribute("CC_CounterLabel", label or "KONTER")
	task.delay(duration + 0.05, function()
		if f.char and f.char.Parent and f.char:GetAttribute("CC_CounterUntil") == untilTime then
			f.char:SetAttribute("CC_CounterUntil", nil)
			f.char:SetAttribute("CC_CounterLabel", nil)
		end
	end)
end

function groundAdvance(top)
	local w = top.wr
	if not w or w.role ~= "top" or w.state ~= "guard" or top.ko then return end
	local step = ADVANCE[w.pos]; if not step then return end
	if top.stamina < ADVANCE_COST then top.char:SetAttribute("CC_Tired", workspace:GetServerTimeNow()); return end
	local bottom = w.partner
	spend(top, ADVANCE_COST)
	w.state = "advance"
	local t0 = os.clock()
	local ta = playPair(top, bottom, step[1], false)
	startGroundAction(top, "POSITION", pairLen(step[1]), w.pos, step[2])
	openCounterWindow(bottom, COUNTER_WINDOW, "POSITIONSWECHSEL KONTERN")
	task.wait(COUNTER_WINDOW)
	if not (top.wr and bottom.wr) then return end
	if countered(bottom, t0, 0.3) then
		print(("[CC] %s Position %s -> %s: gekontert"):format(top.char.Name, w.pos, step[2]))
		hitFX(top.char, 0.15, "block")
		clearGroundFeedback(top); clearGroundFeedback(bottom)
		if not reversePair(top, bottom, step[1], ta.TimePosition) then return end
		if not pairCancelled(top, bottom) then groundLoop(top, bottom, w.pos) end
		return
	end
	task.wait(math.max(0, pairLen(step[1]) - ta.TimePosition - 0.03))
	if pairCancelled(top, bottom) then return end
	print(("[CC] %s Position %s -> %s"):format(top.char.Name, w.pos, step[2]))
	reward(top, "train", "Grappling", 1)
	addDamage(top.char, 4)      -- Positionsgewinn zaehlt fuer die Punktwertung
	clearGroundFeedback(top); clearGroundFeedback(bottom)
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
		if pairCancelled(top, bottom) then return end
		local dmg = p.dmg * (1 + 0.015 * stat(top, "Power"))
		bottom.hum.Health = math.max(HP_FLOOR, bottom.hum.Health - dmg)
		addDamage(top.char, dmg)
		top.char:SetAttribute("CC_GroundHits", (top.char:GetAttribute("CC_GroundHits") or 0) + 1)
		if registerGroundImpact(bottom, dmg, w.pos) then
			bottom.char:SetAttribute("CC_Stoppage", "GROUND_TKO")
			bottom.hum.Health = HP_FLOOR
			print("[CC] Ringrichter-Abbruch: Ground-and-Pound T.K.O.!", bottom.char.Name)
		end
		print(("[CC] %s Bodenschlag (%s) -> %s %.0f"):format(top.char.Name, w.pos, bottom.char.Name, bottom.hum.Health))
		focusGain(top, "groundHit")
		hitFX(bottom.char, 0.5, "hit", "ground"); hitFX(top.char, 0.25, "land")
		ta:AdjustSpeed(0.05); task.delay(HITSTOP, function() if ta.IsPlaying then ta:AdjustSpeed(1) end end)
	end)
	if not holdTrackEnd(ta, pairLen(p.pair), nil, function() return pairCancelled(top, bottom) end) then return end
	if pairCancelled(top, bottom) then return end
	if bottom.hum.Health <= HP_FLOOR then
		-- K.o. am Boden: unten bleibt liegen; aus der Guard steht oben auf, sonst bleibt oben in Position
		print("[CC] K.o. am Boden!", bottom.char.Name)
		local tb = wrTrack(bottom, POS_IDLE[w.pos] .. "_B"); tb:Play(0); tb:AdjustSpeed(0)
		if w.pos == "guard" then
			local te = playWrSolo(top, "Ground_Guard_Escape_A", 0.1, 1, false)
			if not holdTrackEnd(te, WR.Ground_Guard_Escape_A.len, nil, function() return frozen(top) end) then return end
			local tg = playWrSolo(top, "Ground_GetUp_A", 0.1, 1, false)
			if not holdTrackEnd(tg, WR.Ground_GetUp_A.len, nil, function() return frozen(top) end) then return end
			top.char.HumanoidRootPart.CFrame = top.wrStart * rootOffset(top, WR.Ground_GetUp_A.rootEnd)
			blendToStanding(top, WR_FADE); wrStopAll(top, WR_FADE); setWrestle(top, nil, nil)
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
	if top.stamina < SUB_COST then top.char:SetAttribute("CC_Tired", workspace:GetServerTimeNow()); return end
	local bottom = w.partner
	spend(top, SUB_COST)
	w.state = "sub"; top.mash, bottom.mash = 0, 0
	print(("[CC] %s Submission-Versuch: %s"):format(top.char.Name, sub.name))
	local ta, tb = playPair(top, bottom, sub.pair, false)
	for _, x in ipairs({ top, bottom }) do x.char:SetAttribute("CC_SubName", sub.name); x.char:SetAttribute("CC_SubRole", x == top and "attack" or "defend") end
	task.wait(sub.hold)
	if pairCancelled(top, bottom) then return end
	ta:AdjustSpeed(0); tb:AdjustSpeed(0)
	-- Duell: Start 0,35; weniger Leben unten -> Griff zieht von selbst zu
	local p, t0, last = 0.35, os.clock(), os.clock()
	local dummyNext = 0
	while pairAlive(top, bottom) and not frozen(top) and not frozen(bottom) and p > 0 and p < 1 and os.clock() - t0 < SUB_TIME do
		local dt = task.wait(); local now = os.clock()
		for _, x in ipairs({ top, bottom }) do                 -- Trainingsgegner haemmert ca. 4-5 mal pro Sekunde
			if isDummy(x) and not passive(x) and now >= dummyNext then x.mash += 1; dummyNext = now + 0.18 + math.random() * 0.12 end
		end
		p += top.mash * SUB_TOP * (1 + 0.025 * stat(top, "Grappling")) - bottom.mash * SUB_BOTTOM * (1 + 0.025 * stat(bottom, "Grappling")) + dt * 0.10 * (1 - bottom.hum.Health / bottom.hum.MaxHealth)
		top.mash, bottom.mash = 0, 0
		p = math.clamp(p, 0, 1)
		top.char:SetAttribute("CC_SubProgress", p); bottom.char:SetAttribute("CC_SubProgress", p)
		last = now
	end
	for _, x in ipairs({ top, bottom }) do x.char:SetAttribute("CC_SubProgress", nil); x.char:SetAttribute("CC_SubName", nil); x.char:SetAttribute("CC_SubRole", nil) end
	if pairCancelled(top, bottom) then return end
	if p >= 1 then
		print(("[CC] %s gewinnt per %s gegen %s"):format(top.char.Name, sub.name, bottom.char.Name))
		reward(top, "train", "Grappling", 3)
		ta:AdjustSpeed(1); tb:AdjustSpeed(1)
		task.wait(pairLen(sub.pair) - sub.hold - 0.05)
		if pairCancelled(top, bottom) then return end
		ta:AdjustSpeed(0); tb:AdjustSpeed(0)
		w.state = "over"
		addDamage(top.char, 20)
		top.char:SetAttribute("CC_SubmissionWins", (top.char:GetAttribute("CC_SubmissionWins") or 0) + 1)
		bottom.hum.Health = HP_FLOOR
		bottom.ko = true; bottom.char:SetAttribute("CC_LastReact", "submission"); bottom.char:SetAttribute("CC_KO", true)
		hitFX(bottom.char, 0.6, "ko", "submission")
		return
	end
	print(("[CC] %s befreit sich aus %s"):format(bottom.char.Name, sub.name))
	reward(bottom, "train", "Grappling", 2)
	hitFX(top.char, 0.2, "block")
	if not reversePair(top, bottom, sub.pair, ta.TimePosition) then return end
	if not pairCancelled(top, bottom) then groundLoop(top, bottom, w.pos) end
end

-- Befreien/Aufstehen aus jeder Bodenposition:
-- Leertaste fuehrt die vorhandenen Positionsanimationen rueckwaerts bis zur Guard und danach sauber in den Stand.
-- Der erste Versuch kostet Ausdauer; ein Konter kann die Kette an der aktuellen Position stoppen.
function groundEscape(f, chaining)
	local w = f.wr
	if not w or (w.role ~= "top" and w.role ~= "bottom") or frozen(f) then return end
	local requesterRole = w.role
	local top = requesterRole == "top" and f or w.partner
	local bottom = requesterRole == "bottom" and f or w.partner
	if pairCancelled(top, bottom) then return end
	local st = top.wr.state
	if st == "sub" then if f == bottom then f.mash = (f.mash or 0) + 1 end return end   -- im Duell: Leertaste haemmern
	if st == "punch" then f.wantEscape = true return end -- nach dem laufenden Schlag ausfuehren
	if st ~= "guard" then return end
	f.wantEscape = nil

	local pos = top.wr.pos
	if pos ~= "guard" then
		local back = RETREAT[pos]
		if not back then return end
		local bottomEscape = f == bottom
		if bottomEscape and not chaining then
			if bottom.stamina < ESCAPE_COST then bottom.char:SetAttribute("CC_Tired", workspace:GetServerTimeNow()); return end
			spend(bottom, ESCAPE_COST)
		end

		top.wr.state = "escape"
		local t0 = os.clock()
		local ta, tb = playPair(top, bottom, back[1], false)
		ta:AdjustSpeed(0); tb:AdjustSpeed(0)
		local L = pairLen(back[1]) - 0.02
		ta.TimePosition, tb.TimePosition = L, L
		ta:AdjustSpeed(-1); tb:AdjustSpeed(-1)
		startGroundAction(f, bottomEscape and "BEFREIUNG" or "AUFSTEHEN", L, pos, back[2])
		if bottomEscape then openCounterWindow(top, COUNTER_WINDOW, "BEFREIUNG KONTERN") end

		if bottomEscape then
			task.wait(COUNTER_WINDOW)
			if pairCancelled(top, bottom) then return end
			if countered(top, t0, 0.3) then
				print(("[CC] %s Befreiungsversuch gekontert"):format(bottom.char.Name))
				hitFX(bottom.char, 0.15, "block")
				clearGroundFeedback(top); clearGroundFeedback(bottom)
				local tp = ta.TimePosition
				ta:AdjustSpeed(1); tb:AdjustSpeed(1)
				task.wait(math.max(0, L - tp))
				if not pairCancelled(top, bottom) then groundLoop(top, bottom, pos) end
				return
			end
		end

		task.wait(math.max(0, ta.TimePosition))
		if pairCancelled(top, bottom) then return end
		if bottomEscape then
			print(("[CC] %s befreit sich: %s -> %s"):format(bottom.char.Name, pos, back[2]))
			reward(bottom, "train", "Grappling", 1)
		else
			print(("[CC] %s loest die Position: %s -> %s"):format(top.char.Name, pos, back[2]))
		end
		clearGroundFeedback(top); clearGroundFeedback(bottom)
		groundLoop(top, bottom, back[2])

		-- Ohne weitere Eingabe bis zur Guard und anschliessend bis zum Stand fortsetzen.
		task.wait(0.08)
		if pairAlive(top, bottom) and f.wr and f.wr.role == requesterRole and not frozen(f) then
			groundEscape(f, true)
		end
		return
	end

	if f == top and DOWN_OK then
		startGroundAction(f, "AUFSTEHEN", 1.2, "guard", "stand")
		topDisengage(top)
		return
	end
	top.wr.state = "escape"
	startGroundAction(f, "AUFSTEHEN", pairLen("Ground_Guard_Escape") + 1.5, "guard", "stand")
	local ta = playPair(top, bottom, "Ground_Guard_Escape", false)
	if not holdTrackEnd(ta, pairLen("Ground_Guard_Escape"), nil, function() return pairCancelled(top, bottom) end) then return end
	if pairCancelled(top, bottom) then return end
	if DOWN_OK then
		enterDown(bottom, "seated", 0.15)
		local tg = playWrSolo(top, "Ground_GetUp_A", 0.1, 1.1, false)
		task.wait(36 / 24 / 1.1)
		if not top.wr or not top.char.Parent then return end
		if frozen(top) then holdPairPose(top, bottom); return end
		top.char.HumanoidRootPart.CFrame = top.wrStart * rootOffset(top, WR.Ground_GetUp_A.rootEnd)
		blendToStanding(top, WR_FADE)
		wrStopAll(top, WR_FADE); setWrestle(top, nil, nil); top.busyUntil = os.clock() + 0.2
		if bottom.down and not bottom.ko and bottom.char.Parent then
			downGetUp(bottom, true)
		end
		print(("[CC] %s befreit sich aus der Guard und steht auf"):format(bottom.char.Name))
		return
	end
	local tg = playPair(top, bottom, "Ground_GetUp", false)
	if not holdTrackEnd(tg, pairLen("Ground_GetUp"), nil, function() return pairCancelled(top, bottom) end) then return end
	endExchange(top, bottom, "Ground_GetUp")
	print(("[CC] %s und %s stehen wieder"):format(top.char.Name, bottom.char.Name))
end

-- ================= Bodenlagen: einer liegt/sitzt/kniet, der andere steht (Gameplay-Ueberarbeitung Abschnitt 2) =================
-- Einzel-Animationen aus Down_Positions_v01.blend (DN_*): Rueckenlage (defensive Guard), seitliche Lage, sitzende Abwehr,
-- kniende Position; Uebergaenge nach oben (E), technisches Aufstehen (Leertaste): Ruecken -> Seite -> Sitzen -> Stand
-- (Ground_GetUp_B), aus dem Sitzen (Ground_GetUp_B) und aus dem Knien. Aufstehen dauert und wird durch Treffer unterbrochen;
-- steht der Gegner direkt am Koerper, geht es nicht ("Abstand schaffen"). Unten: Block (F), Stosstritt nach oben (Linksklick),
-- Fersentritt gegen das Knie (C). Oben stehend: Low Kick gegen die Beine (C), E = in die Guard des Liegenden einsteigen.
-- Keine Kopftritte/Stomps: Schlaege und andere Tritte treffen einen Liegenden nicht.
-- Der Liegende ist verankert (HumanoidRootPart = seine Ringkampf-Position); am Ende des Aufstehens wird er auf die
-- End-Position der Animation versetzt (rootEnd), wie beim Ringkampf.
local DN = {}
for _, n in ipairs({ "Down_Back_Idle", "Down_Back_Block", "Down_Side_Idle", "Down_Seated_Idle", "Down_Kneel_Idle", "Down_Back_To_Side",
	"Down_Side_To_Seated", "Down_Seated_To_Kneel", "Down_GetUp_Kneel", "Down_UpKick", "Down_LegKick", "Down_Hit", "Stand_LegKickDown" }) do
	local key = "DN_" .. n
	local mod = A:FindFirstChild(key .. "_Data")
	if mod and (A:FindFirstChild(key) or ANIM_IDS[key]) then
		local data = require(mod)
		DN[n] = { anim = anim(key), rootEnd = data.rootEnd, len = (#data.frames - 1) / 24 }
	end
end
DOWN_OK = DN.Down_Back_Idle ~= nil      -- global: wird schon in groundEscape (weiter oben) gebraucht
local DOWN_IDLE = { back = "Down_Back_Idle", side = "Down_Side_Idle", seated = "Down_Seated_Idle", kneel = "Down_Kneel_Idle" }
local UP_NEXT = { back = { "Down_Back_To_Side", "side" }, side = { "Down_Side_To_Seated", "seated" }, seated = { "Down_Seated_To_Kneel", "kneel" } }
local GETUP_COST = { back = 14, side = 12, seated = 10, kneel = 6 }
local POSTURE_COST, UPKICK_COST, LEGKICK_COST, LEGKICK_DOWN_COST = 4, 8, 6, 8
local GETUP_SPEED = 1.25          -- Aufstehen etwas zuegiger als in Blender gebaut (Ruecken bis Stand ca. 2,6 s)
local PRESSURE_DIST = 4.2         -- Studs (1,2 m) vom Becken: steht der Gegner so nah, ist Aufstehen nicht moeglich
local DOWN_TURN = 1.6             -- rad/s: Liegender dreht sich zum Gegner
local UPKICK = { win = { 6 / 24, 10 / 24 }, limb = "RightFoot", dmg = 6, push = 4.5, targets = { "LowerTorso", "LeftUpperLeg", "RightUpperLeg" }, radius = 1.35 }
local LEGKICK = { win = { 5 / 24, 9 / 24 }, limb = "LeftFoot", dmg = 5, targets = { "LeftLowerLeg", "RightLowerLeg", "LeftUpperLeg", "RightUpperLeg" }, radius = 1.5 }
local LEGKICK_DOWN = { win = { 11 / 24, 15 / 24 }, limbs = { { "RightLowerLeg", 0.9 }, { "RightFoot", 0.1 } }, dmg = 5,
	targets = { "LeftLowerLeg", "RightLowerLeg", "LeftFoot", "RightFoot", "LeftUpperLeg", "RightUpperLeg" }, radius = 1.4 }

-- Ring-/Bodenanimationen beim Start vorladen (hochgeladene Animationen sonst erst beim ersten Abspielen)
task.spawn(function()
	local list = {}
	for _, e in pairs(WR) do if e.anim then table.insert(list, e.anim) end end
	for _, e in pairs(DN) do if e.anim then table.insert(list, e.anim) end end
	local ok, err = pcall(function() game:GetService("ContentProvider"):PreloadAsync(list) end)
	if not ok then warn("[CC] Vorladen der Bodenanimationen: " .. tostring(err)) end
end)
local function dnTrack(f, n)
	f.dnTracks = f.dnTracks or {}
	if not f.dnTracks[n] then
		local d = DN[n]; if not d then return nil end
		f.dnTracks[n] = f.hum.Animator:LoadAnimation(d.anim)
	end
	return f.dnTracks[n]
end
local function dnStopAll(f, fade, except)
	for _, tr in pairs(f.dnTracks or {}) do if tr ~= except and tr.IsPlaying then tr:Stop(fade or 0.1) end end
end
local function dnPlay(f, n, fade, speed, looped)
	local tr = dnTrack(f, n); if not tr then return nil end
	local others = {}
	for _, t in pairs(f.dnTracks or {}) do if t ~= tr and t.IsPlaying then table.insert(others, t) end end
	for _, t in pairs(f.wrTracks or {}) do if t ~= tr and t.IsPlaying then table.insert(others, t) end end
	tr.Looped = looped or false
	tr.Priority = Enum.AnimationPriority.Action4
	if tr.IsPlaying then tr:AdjustSpeed(speed or 1); tr:AdjustWeight(math.max(tr.WeightCurrent, 0.05), 0)
	else tr:Play(0, 0.05, speed or 1) end
	stopOthersWhenLoaded(f, tr, others, fade or WR_FADE)
	return tr
end
local function opponentOf(f)
	local n = f.char:GetAttribute("CC_Opponent")
	local c = n and workspace:FindFirstChild(n)
	return c and fighters[c]
end
local function setDownAttr(f)
	f.char:SetAttribute("CC_Down", f.down and f.down.state or nil)
	f.char:SetAttribute("CC_DownBusy", f.down and f.down.busy or nil)
end
local function downIdle(f, fade)
	local d = f.down; if not d then return end
	local n = DOWN_IDLE[d.state]
	if d.state == "back" and f.downBlock then n = "Down_Back_Block" end
	dnPlay(f, n, fade or 0.15, 1, true)
end
-- in eine Bodenlage wechseln (aus dem Ringkampf: HumanoidRootPart bleibt auf der Ringkampf-Position)
function enterDown(f, state, fade)
	if not DOWN_OK then return false end
	stopStanding(f)
	if f.wr then f.wr = nil; f.char:SetAttribute("CC_Wrestle", false) end
	for _, k in ipairs({ "CC_GroundPos", "CC_SubProgress", "CC_SubName", "CC_SubRole" }) do f.char:SetAttribute(k, nil) end
	f.char.HumanoidRootPart.Anchored = true
	f.down = { state = state, token = (f.downToken or 0) + 1, enteredAt = os.clock() }
	f.downToken = f.down.token
	f.downHitAt = 0
	f.busyUntil = 0
	setDownAttr(f)
	downIdle(f, fade or 0.3)
	return true
end
-- Bodenlage verlassen (stehend): HumanoidRootPart auf die End-Position der Aufsteh-Animation
local function leaveDown(f, rootEnd)
	local root = f.char.HumanoidRootPart
	if rootEnd then root.CFrame = root.CFrame * rootOffset(f, rootEnd) end
	blendToStanding(f, WR_FADE)
	dnStopAll(f, WR_FADE); wrStopAll(f, WR_FADE)
	f.down = nil; f.downBlock = false
	setDownAttr(f)
	root.Anchored = false
	f.busyUntil = os.clock() + 0.2
end
function clearDown(f, keepAnchored)            -- Reset/Wechsel: ohne Positionsversatz
	f.downToken = (f.downToken or 0) + 1
	f.animToken = (f.animToken or 0) + 1
	dnStopAll(f, 0.1)
	f.down = nil; f.downBlock = false; f.downHitAt = 0
	setDownAttr(f)
	f.char:SetAttribute("CC_DownBlocked", nil)
	if not keepAnchored then
		local root = f.char:FindFirstChild("HumanoidRootPart")
		if root then
			root.AssemblyLinearVelocity = Vector3.zero; root.AssemblyAngularVelocity = Vector3.zero
			root.Anchored = false
		end
		blendToStanding(f, 0.15)
	end
end
local function downBodyPos(f) return bonePos(f.char, "LowerTorso") or f.char.HumanoidRootPart.Position end
-- steht der Gegner direkt am Koerper?
local function underPressure(f)
	local o = opponentOf(f)
	if not o or o.ko or o.down or o.wr then return false end
	local d = (o.char.HumanoidRootPart.Position - downBodyPos(f)) * Vector3.new(1, 0, 1)
	return d.Magnitude < PRESSURE_DIST
end
-- warten; bricht ab bei Treffer oder Reset. Rueckgabe: "ok" | "hit" | "reset"
local function downWait(f, token, seconds, since)
	local t0 = os.clock()
	while os.clock() - t0 < seconds do
		task.wait(0.03)
		if not f.down or f.down.token ~= token or f.ko or not f.char.Parent or frozen(f) then
			if frozen(f) then
				for _, group in ipairs({ f.wrTracks or {}, f.dnTracks or {} }) do
					for _, tr in pairs(group) do if tr.IsPlaying then tr:AdjustSpeed(0) end end
				end
			end
			return "reset"
		end
		if f.downHitAt > since then return "hit" end
	end
	return "ok"
end

-- Aufstehen (Leertaste): Stufen bis zum Stand; Treffer unterbricht -> zurueck in die Lage der aktuellen Stufe
function downGetUp(f, force)
	local d = f.down
	if not d or d.busy or f.ko or frozen(f) then return end
	if not force and underPressure(f) then f.char:SetAttribute("CC_DownBlocked", workspace:GetServerTimeNow()); return end
	local cost = GETUP_COST[d.state]
	if f.stamina < cost then f.char:SetAttribute("CC_Tired", workspace:GetServerTimeNow()); return end
	spend(f, cost)
	d.busy = "getup"; setDownAttr(f)
	local token, since = d.token, os.clock()
	local stages = {}
	local st = d.state
	while st == "back" or st == "side" do table.insert(stages, UP_NEXT[st]); st = UP_NEXT[st][2] end
	for _, s in ipairs(stages) do
		local tr = dnPlay(f, s[1], 0.1, GETUP_SPEED)
		local r = downWait(f, token, DN[s[1]].len / GETUP_SPEED, since)
		if r == "reset" then return end
		if r == "hit" then d.busy = nil; downIdle(f, 0.2); setDownAttr(f); return end
		d.state = s[2]; setDownAttr(f)
		if tr then tr:AdjustSpeed(0) end
	end
	-- letzte Stufe: aus dem Sitzen = Ground_GetUp_B (technisches Aufstehen), aus dem Knien = Down_GetUp_Kneel
	local tr, len, rootEnd
	if d.state == "kneel" then
		tr = dnPlay(f, "Down_GetUp_Kneel", 0.1, GETUP_SPEED); len = DN.Down_GetUp_Kneel.len; rootEnd = DN.Down_GetUp_Kneel.rootEnd
	else
		tr = playWrSolo(f, "Ground_GetUp_B", 0.12, GETUP_SPEED, false)
		len = WR.Ground_GetUp_B.len; rootEnd = WR.Ground_GetUp_B.rootEnd
	end
	-- unterbrechbar, solange noch nicht aufrecht (erste 70 %)
	local r = downWait(f, token, len * 0.7 / GETUP_SPEED, since)
	if r == "reset" then return end
	if r == "hit" then
		if tr then tr:Stop(0.2) end
		d.busy = nil; downIdle(f, 0.25); setDownAttr(f)
		print(("[CC] %s Aufstehen unterbrochen (%s)"):format(f.char.Name, d.state))
		return
	end
	r = downWait(f, token, len * 0.3 / GETUP_SPEED - 0.02, math.huge)
	if r == "reset" then return end
	leaveDown(f, rootEnd)
	reward(f, "train", "Grappling", 1)
	print(("[CC] %s steht wieder auf"):format(f.char.Name))
end
-- Haltung nach oben (E): Ruecken -> Seite -> Sitzen -> Knien
function downPosture(f)
	local d = f.down
	if not d or d.busy or f.ko or frozen(f) then return end
	local nx = UP_NEXT[d.state]; if not nx then return end
	if f.stamina < POSTURE_COST then f.char:SetAttribute("CC_Tired", workspace:GetServerTimeNow()); return end
	spend(f, POSTURE_COST)
	d.busy = "trans"; setDownAttr(f)
	local token, since = d.token, os.clock()
	local tr = dnPlay(f, nx[1], 0.1, 1.1)
	local r = downWait(f, token, DN[nx[1]].len / 1.1, since)
	if r == "reset" then return end
	if r == "ok" then d.state = nx[2]; if tr then tr:AdjustSpeed(0) end end
	print(("[CC] %s am Boden: %s"):format(f.char.Name, d.state))
	d.busy = nil; setDownAttr(f); downIdle(f, 0.1)
end
-- Treffer-Pruefung ueber Bones (Glied des Angreifers gegen Ziel-Bones des Gegners)
local function limbHits(att, limbs, target, targets, radius)
	for _, l in ipairs(limbs) do
		local p = bonePos(att.char, l[1], l[2])
		if p then
			for _, b in ipairs(targets) do
				local q = bonePos(target.char, b, 0.3)
				if q and (p - q).Magnitude <= radius then return true end
			end
		end
	end
	return false
end
local function pushBack(target, from, studs)
	local root = target.char.HumanoidRootPart
	if root.Anchored then return end
	local dir = (root.Position - from) * Vector3.new(1, 0, 1)
	if dir.Magnitude < 0.1 then return end
	dir = dir.Unit
	task.spawn(function()
		for _ = 1, 8 do
			if not root.Parent or root.Anchored then return end
			root.CFrame = root.CFrame + dir * (studs / 8)
			task.wait()
		end
	end)
end
-- Tritt vom Boden (Rueckenlage): "up" = Stosstritt (Abstand), "leg" = Fersentritt gegen das Knie
function downKick(f, kind)
	local d = f.down
	if not d or d.busy or d.state ~= "back" or f.ko or frozen(f) then return end
	local k = kind == "up" and UPKICK or LEGKICK
	local cost = kind == "up" and UPKICK_COST or LEGKICK_COST
	if f.stamina < cost then f.char:SetAttribute("CC_Tired", workspace:GetServerTimeNow()); return end
	spend(f, cost)
	d.busy = "kick"; setDownAttr(f)
	local token, since = d.token, os.clock()
	local name = kind == "up" and "Down_UpKick" or "Down_LegKick"
	local tr = dnPlay(f, name, 0.06, 1)
	local o = opponentOf(f)
	local t0 = os.clock(); local hit = false
	while os.clock() - t0 < DN[name].len do
		task.wait()
		if not f.down or f.down.token ~= token then return end
		local t = os.clock() - t0
		if not hit and o and not o.ko and not o.down and not o.wr and t >= k.win[1] and t <= k.win[2] and limbHits(f, { { k.limb, 0.1 } }, o, k.targets, k.radius) then
			hit = true
			local dmg = k.dmg * (o.blocking and 0.5 or 1) * (1 + 0.015 * stat(f, "Power"))
			o.hum.Health = math.max(HP_FLOOR, o.hum.Health - dmg)
			addDamage(f.char, dmg)
			interrupt(o); react(o, kind == "up" and "hitBody" or "hitLeg", 0.35)
			hitFX(o.char, 0.35, "hit"); hitFX(f.char, 0.2, "land")
			if kind == "up" then pushBack(o, downBodyPos(f), k.push) end
			if tr then tr:AdjustSpeed(0.05); task.delay(HITSTOP, function() if tr.IsPlaying then tr:AdjustSpeed(1) end end) end
			print(("[CC] %s %s vom Boden -> %s %.0f"):format(f.char.Name, kind == "up" and "Stosstritt" or "Beintritt", o.char.Name, o.hum.Health))
		end
		if f.downHitAt > since then break end
	end
	if f.down and f.down.token == token then d.busy = nil; setDownAttr(f); downIdle(f, 0.12) end
end
-- Liegender wird getroffen (Beintritt des Stehenden)
local function downTakeHit(f, dmg, attacker)
	local blocked = f.downBlock
	dmg = dmg * (blocked and 0.4 or 1)
	f.hum.Health = math.max(HP_FLOOR, f.hum.Health - dmg)
	addDamage(attacker.char, dmg)
	f.downHitAt = os.clock()
	hitFX(f.char, blocked and 0.15 or 0.4, blocked and "block" or "hit"); hitFX(attacker.char, 0.25, "land")
	spend(f, blocked and 3 or 5)
	if f.down and not f.down.busy and f.down.state == "back" and not blocked then
		local token = f.down.token
		dnPlay(f, "Down_Hit", 0.04, 1)
		task.delay(DN.Down_Hit.len, function() if f.down and f.down.token == token and not f.down.busy then downIdle(f, 0.12) end end)
	end
	if f.hum.Health <= HP_FLOOR and f.down then
		print("[CC] K.o. am Boden (Beintritte)", f.char.Name)
		f.ko = true; f.char:SetAttribute("CC_KO", true); f.char:SetAttribute("CC_LastReact", "koGround")
		local tr = f.dnTracks and f.dnTracks[DOWN_IDLE[f.down.state]]; if tr then tr:AdjustSpeed(0) end
		hitFX(f.char, 1.0, "ko")
	end
end
-- Stehender tritt die Beine des Liegenden (Low Kick nach unten)
function legKickDown(att, target)
	if att.ko or att.wr or att.down or frozen(att) or os.clock() < att.busyUntil then return end
	if att.stamina < LEGKICK_DOWN_COST then att.char:SetAttribute("CC_Tired", workspace:GetServerTimeNow()); return end
	spend(att, LEGKICK_DOWN_COST)
	setBlock(att, false)
	local d = DN.Stand_LegKickDown
	att.busyUntil = os.clock() + d.len * 0.92
	att.attackToken = (att.attackToken or 0) + 1
	local token = att.attackToken
	for k in pairs(MOVES) do local tr = att.tracks[k]; if tr.IsPlaying then tr:Stop(0.06) end end
	local tr = dnTrack(att, "Stand_LegKickDown"); tr.Looped = false; tr.Priority = Enum.AnimationPriority.Action2; tr:Play(0.06)
	local t0 = os.clock(); local hit = false
	while os.clock() - t0 < LEGKICK_DOWN.win[2] + 0.02 do
		task.wait()
		if att.attackToken ~= token or att.ko then return end
		local t = os.clock() - t0
		if not hit and t >= LEGKICK_DOWN.win[1] and target.down and not target.ko and limbHits(att, LEGKICK_DOWN.limbs, target, LEGKICK_DOWN.targets, LEGKICK_DOWN.radius) then
			hit = true
			downTakeHit(target, LEGKICK_DOWN.dmg * (1 + 0.015 * stat(att, "Power")), att)
			tr:AdjustSpeed(0.05); task.delay(HITSTOP, function() if tr.IsPlaying then tr:AdjustSpeed(1) end end)
			print(("[CC] %s Low Kick am Boden -> %s %.0f"):format(att.char.Name, target.char.Name, target.hum.Health))
		end
	end
end
-- Stehender steigt in die Guard des Liegenden ein (E): nur gegen Rueckenlage, nahe an den Beinen
function enterGuardFromStand(a, b)
	if a.ko or a.wr or a.down or frozen(a) or frozen(b) or os.clock() < a.busyUntil then return end
	local d = b.down
	if not d or d.state ~= "back" or d.busy or b.ko then return end
	local Cb = b.char.HumanoidRootPart.CFrame
	local Ca = Cb * CFrame.Angles(0, math.pi, 0) * CFrame.new(0, 0, WR_GAP)
	local standCF = Ca * rootOffset(a, WR.Ground_GetUp_A.rootEnd)       -- dort steht A am Ende von Ground_GetUp_A
	if ((a.char.HumanoidRootPart.Position - standCF.Position) * Vector3.new(1, 0, 1)).Magnitude > 4.5 then return end
	if a.stamina < ADVANCE_COST then a.char:SetAttribute("CC_Tired", workspace:GetServerTimeNow()); return end
	spend(a, ADVANCE_COST)
	stopStanding(a)
	a.busyUntil = math.huge
	d.busy = "guard"; setDownAttr(b)
	local root = a.char.HumanoidRootPart
	root.Anchored = true
	local from = root.CFrame
	for i = 1, 8 do
		if frozen(a) or frozen(b) or not a.char.Parent or not b.char.Parent then root.Anchored = false; a.busyUntil = 0; return end
		root.CFrame = from:Lerp(standCF, i / 8); task.wait()
	end
	-- Ground_GetUp_A rueckwaerts ab dem Stand (Frame 36): A geht zwischen den Beinen auf die Knie
	local tg = playWrSolo(a, "Ground_GetUp_A", 0.15, -1.3, false, 35 / 24)
	task.wait(35 / 24 / 1.3)
	if frozen(a) or frozen(b) or not (b.down and b.down.busy == "guard") or a.ko or b.ko or not a.char.Parent or not b.char.Parent then
		tg:Stop(0.2); root.CFrame = standCF; root.Anchored = false; a.busyUntil = 0
		if b.down then b.down.busy = nil; setDownAttr(b) end
		return
	end
	clearDown(b, true)
	setWrestle(a, b, "top"); setWrestle(b, a, "bottom")
	a.wrStart, b.wrStart = Ca, Cb
	root.CFrame = Ca
	a.busyUntil, b.busyUntil = 0, 0
	playPair(a, b, POS_IDLE.guard, true)
	a.wr.state = "guard"; setPos(a, b, "guard")
	print(("[CC] %s steigt in die Guard von %s ein"):format(a.char.Name, b.char.Name))
end
-- Oben in der Guard: aufstehen. NPC-Gegner stehen danach automatisch sauber auf.
function topDisengage(top)
	local w = top.wr
	if not w or w.role ~= "top" or w.state ~= "guard" or w.pos ~= "guard" or top.ko or frozen(top) or not DOWN_OK then return end
	local bottom = w.partner
	if top.stamina < ESCAPE_COST * 0.5 then top.char:SetAttribute("CC_Tired", workspace:GetServerTimeNow()); return end
	spend(top, ESCAPE_COST * 0.5)
	w.state = "escape"
	enterDown(bottom, "back", 0.35)
	local tg = playWrSolo(top, "Ground_GetUp_A", 0.15, 1.2, false, 4 / 24)
	task.wait((36 - 4) / 24 / 1.2)
	if not top.wr or not top.char.Parent then return end
	if frozen(top) then holdPairPose(top, bottom); return end
	top.char.HumanoidRootPart.CFrame = top.wrStart * rootOffset(top, WR.Ground_GetUp_A.rootEnd)
	blendToStanding(top, WR_FADE)
	wrStopAll(top, WR_FADE); setWrestle(top, nil, nil); top.busyUntil = os.clock() + 0.2
	local bottomPlayer = game.Players:GetPlayerFromCharacter(bottom.char)
	if not bottomPlayer then
		task.delay(0.35, function()
			if bottom.down and not bottom.ko and bottom.char.Parent then
				downGetUp(bottom, true)
			end
		end)
	end
	print(("[CC] %s steht auf%s"):format(top.char.Name, bottomPlayer and "" or (", " .. bottom.char.Name .. " folgt")))
end
-- Liegender dreht sich langsam zum stehenden Gegner (nur in Ruhe)
RunService.Heartbeat:Connect(function(dt)
	for _, f in pairs(fighters) do
		local d = f.down
		if d and not d.busy and not f.ko then
			local o = opponentOf(f)
			if o and not o.down and not o.wr then
				local root = f.char.HumanoidRootPart
				local to = (o.char.HumanoidRootPart.Position - root.Position) * Vector3.new(1, 0, 1)
				if to.Magnitude > 0.5 then
					local look = root.CFrame.LookVector * Vector3.new(1, 0, 1)
					local ang = math.atan2(look.Unit:Cross(to.Unit).Y, look.Unit:Dot(to.Unit))
					if math.abs(ang) > math.rad(15) then
						root.CFrame = root.CFrame * CFrame.Angles(0, math.clamp(ang, -DOWN_TURN * dt, DOWN_TURN * dt), 0)
					end
				end
			end
		end
	end
end)

-- ================= Trainingsgegner-Stufen (zentral) =================
-- Attribut CC_Difficulty am Trainingsgegner (setzt CC_Match aus der Menue-Auswahl): "passiv" | "anfaenger" | "fortgeschritten".
--   reaction = Denkpause im Stand (min, zusaetzlich zufaellig, s); aggr = Anteil Angriffe je Entscheidung; combo = max. Kombolaenge;
--   block = Blockchance je Entscheidung; td = Takedownchance je Entscheidung; ground = Bodenkampfstaerke (1 = volles Verhalten:
--   Tempo der Bodenentscheidungen, Submission-, Konter-, Befreiungs- und Sprawl-Chance werden damit skaliert); regen = Leben/s;
--   dmg = Schadensfaktor seiner Schlaege und Tritte.
-- "fortgeschritten" = das bisherige vollstaendige Verhalten (Reaktion >= 0,45 s).
local DUMMY_LEVELS = {
	passiv = { reaction = { 1.0, 0.5 }, aggr = 0, combo = 0, block = 0, td = 0, ground = 0, regen = 4, dmg = 0 },
	anfaenger = { reaction = { 1.3, 1.0 }, aggr = 0.26, combo = 2, block = 0.12, td = 0.015, ground = 0.35, regen = 0, dmg = 0.55 },
	fortgeschritten = { reaction = { 0.45, 0.6 }, aggr = 0.48, combo = 3, block = 0.20, td = 0.07, ground = 1.0, regen = 0, dmg = 1 },
	contender = { reaction = { 0.32, 0.35 }, aggr = 0.58, combo = 3, block = 0.26, td = 0.09, ground = 1.15, regen = 0, dmg = 1.08 },
	champion = { reaction = { 0.24, 0.26 }, aggr = 0.66, combo = 4, block = 0.32, td = 0.12, ground = 1.30, regen = 0, dmg = 1.15 },
}
function DummyLevel()
	local d = workspace:FindFirstChild("CC_TrainingDummy")
	return DUMMY_LEVELS[d and d:GetAttribute("CC_Difficulty") or "fortgeschritten"] or DUMMY_LEVELS.fortgeschritten
end

-- Vier klar getrennte Kampfstile. Sie veraendern Distanz, Technikauswahl, Takedowns und Bodenentscheidungen,
-- ohne jemals Client-Eingaben zu lesen. Reaktionen entstehen nur aus bereits sichtbaren/abgeschlossenen Aktionen.
local AI_STYLES = {
	Boxer = {
		want = 3.9, td = 0.25, block = 1.20, aggr = 1.15, ground = 0.75,
		submit = 0.06, punch = 0.78, advance = 0.92, escape = 0.28,
		combos = { { "jab" }, { "jab", "cross" }, { "jab", "jab", "cross" }, { "cross", "hook" }, { "jabBody", "cross" }, { "uppercut", "hook" } },
	},
	Wrestler = {
		want = 4.3, td = 2.35, block = 0.90, aggr = 0.82, ground = 1.25,
		submit = 0.14, punch = 0.48, advance = 0.93, escape = 0.48,
		combos = { { "jab" }, { "jab", "cross" }, { "cross", "hook" }, { "jab", "lowkick" } },
	},
	Kickboxer = {
		want = 5.1, td = 0.18, block = 1.00, aggr = 1.05, ground = 0.70,
		submit = 0.05, punch = 0.52, advance = 0.82, escape = 0.30,
		combos = { { "lowkick" }, { "bodykick" }, { "frontkick" }, { "jab", "lowkick" }, { "jab", "cross", "highkick" }, { "crossBody", "bodykick" } },
	},
	Grappler = {
		want = 4.5, td = 1.75, block = 0.95, aggr = 0.75, ground = 1.50,
		submit = 0.50, punch = 0.66, advance = 0.96, escape = 0.58,
		combos = { { "jab" }, { "jabBody", "cross" }, { "frontkick" }, { "cross", "hook" } },
	},
}
local function DummyStyle()
	local d = workspace:FindFirstChild("CC_TrainingDummy")
	local name = d and d:GetAttribute("CC_AIStyle") or "Boxer"
	return AI_STYLES[name] or AI_STYLES.Boxer, AI_STYLES[name] and name or "Boxer"
end

-- Trainingsgegner am Boden: oben Schlaege, Position verbessern, Submission; unten befreien
RunService.Heartbeat:Connect(function()
	local d = workspace:FindFirstChild("CC_TrainingDummy")
	local D_ = d and fighters[d]
	if not (D_ and D_.wr) or D_.ko or frozen(D_) then return end
	local w = D_.wr
	if os.clock() < (D_.groundThink or 0) then return end
	local style = DummyStyle()
	local G = DummyLevel().ground * style.ground
	D_.groundThink = os.clock() + (1.4 + math.random() * 1.2) / math.max(G, 0.35)   -- schwaecher = langsamere Bodenentscheidungen
	if d:GetAttribute("CC_Passive") or d:GetAttribute("CC_InMatch") == false or G <= 0 then return end
	if w.role == "top" and w.state == "guard" then
		local r = math.random()
		if SUBS[w.pos] and r < style.submit * math.min(G, 1.4) then task.spawn(groundSubmit, D_)
		elseif PUNCH[w.pos] and r < style.punch then task.spawn(groundPunch, D_)
		elseif ADVANCE[w.pos] and r < style.advance then task.spawn(groundAdvance, D_)
		elseif w.pos == "guard" then task.spawn(groundEscape, D_) end
	elseif w.role == "bottom" and w.partner.wr and w.partner.wr.state == "guard" and math.random() < style.escape * math.min(G, 1.4) then
		task.spawn(groundEscape, D_)
	end
end)

function tryTakedown(a, forceSuccess, slam)   -- slam = Signatur-Definition mit slam=true (Khabib): Hochheben, Tragen, Slam
	if a.ko or a.knocked or a.wr or a.down or frozen(a) or os.clock() < a.busyUntil then return end
	local legDamage = worstLeg(a)
	if legDamage >= 85 then
		a.char:SetAttribute("CC_InjuryDenied", "takedown|" .. tostring(workspace:GetServerTimeNow()))
		return
	end
	local injuryWindow = legDamage >= 60 and 0.18 * math.clamp((legDamage - 60) / 25, 0, 1) or 0
	-- Ziel: naechster Gegner vor A in Reichweite
	local b, bd
	for _, f in pairs(fighters) do
		if f ~= a and not f.ko and not f.knocked and not f.wr and not f.down then
			local d = (f.char.HumanoidRootPart.Position - a.char.HumanoidRootPart.Position) * Vector3.new(1, 0, 1)
			if d.Magnitude <= TD_RANGE and a.char.HumanoidRootPart.CFrame.LookVector:Dot(d.Unit) > 0.4 and (not bd or d.Magnitude < bd) then b, bd = f, d.Magnitude end
		end
	end
	if not b then return end
	-- Ali-Instinkt: Takedown gegen den Instinkt-Kaempfer -> Knie-Konter zum Kopf. Angreifer faellt, steht wieder auf (kein Knockdown-Zaehler).
	local bInst = b.instinct
	if bInst and os.clock() < bInst.untilT and (bInst.dodges or 0) > 0 and not b.ko and not b.knocked then
		bInst.dodges -= 1
		b.char:SetAttribute("CC_InstinctDodges", bInst.dodges)
		local def = SIG.list.ali
		local dmg = def.kneeDamage or 18
		interrupt(a); setBlock(a, false)
		if b.tracks.frontkick then b.tracks.frontkick:Play(0.04, 1, 1.5) end
		b.busyUntil = math.max(b.busyUntil, os.clock() + 0.45)
		a.hum.Health = math.max(HP_FLOOR, a.hum.Health - dmg)
		addDamage(b.char, dmg)
		applyInjury(a, "Head", def.kneeInjury or 15, "knee")
		a.char:SetAttribute("CC_HeadHits", (a.char:GetAttribute("CC_HeadHits") or 0) + 1)
		b.char:SetAttribute("CC_StrikesLanded", (b.char:GetAttribute("CC_StrikesLanded") or 0) + 1)
		fightEvent:Fire("hit", b.char, a.char, "knee", false)
		sigFX:FireAllClients("knee", b.char, a.char, dmg)
		print(("[CC] %s Knie-Konter (Instinkt) gegen den Takedown von %s (%.0f Schaden)"):format(b.char.Name, a.char.Name, dmg))
		-- Angreifer faellt nach vorn und steht nach kurzer Zeit wieder auf
		local fall = a.tracks.koFwd or a.tracks.ko
		a.knockToken = (a.knockToken or 0) + 1
		local token = a.knockToken
		a.knocked = true; a.hum.WalkSpeed = 0; a.busyUntil = os.clock() + (def.kneeDownTime or 1.6) + 0.5
		if fall then fall:Play(0.06) end
		a.char:SetAttribute("CC_LastReact", "kneeCounter")
		task.delay(def.kneeDownTime or 1.6, function()
			if not a.char.Parent or a.knockToken ~= token or a.ko then return end
			if fall then fall:Stop(0.3) end
			if not a.tracks.idle.IsPlaying then a.tracks.idle:Play(0.2) end
			a.knocked = false
			a.hum.WalkSpeed = injuryWalkSpeed(a)
			a.char:SetAttribute("CC_LastReact", "recovered")
		end)
		return
	end
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
	-- Sprawl: Verteidiger drueckt F kurz vor/nach dem Schuss. Ein verletztes Bein macht den Schuss langsamer und leichter abzuwehren.
	local shotAt = os.clock()
	local isDummy = b.char == workspace:FindFirstChild("CC_TrainingDummy")
	local shotWindow = SPRAWL_WINDOW + injuryWindow
	task.wait(shotWindow)
	if pairCancelled(a, b) then return end
	local defended
	local tutor = workspace:FindFirstChild("CC_TrainingDummy") and workspace.CC_TrainingDummy:GetAttribute("CC_Tutor")
	if forceSuccess then defended = false
	elseif isDummy then defended = not tutor and math.random() < math.min(0.92, math.max(0.1, 0.3 - 0.01 * stat(a, "Wrestling")) * math.max(DummyLevel().ground, 0.3) + injuryWindow)   -- Tutorial: Takedown gelingt
	elseif tutor == "ground" then defended = false                                                                     -- Tutorial Lektion 6: Spieler soll unten landen
	else defended = b.sprawlAt ~= nil and math.abs(b.sprawlAt - shotAt) <= shotWindow + 0.01 * stat(b, "Wrestling") - 0.005 * stat(a, "Wrestling") end
	fightEvent:Fire("td", a.char, b.char, defended)
	if a.ko or b.ko or not (a.wr and b.wr) then
		for _, f in ipairs({ a, b }) do if f.wr then setWrestle(f, nil, nil) end; f.busyUntil = 0 end
		return
	end
	local pair = defended and "TD_DoubleLeg_Defended" or (slam and "TD_LiftSlam" or "TD_DoubleLeg_Success")
	print(("[CC] %s Takedown -> %s: %s"):format(a.char.Name, b.char.Name, defended and "Sprawl (abgewehrt)" or "erfolgreich"))
	if defended then reward(b, "train", "Wrestling", 2); focusGain(b, "sprawl") else reward(a, "train", "Wrestling", 2); focusGain(a, "takedown") end
	local ta = playPair(a, b, pair, false)
	hitFX(a.char, 0.25, "land"); hitFX(b.char, defended and 0.2 or 0.6, defended and "block" or "hit")
	if pair == "TD_LiftSlam" then   -- Aufprall in Frame 45 (24 fps): Zusatzschaden, Effekt (roter Bildschirm beim Opfer)
		local tok = a.wr
		task.delay((slam.impactFrame or 45) / 24, function()
			if pairCancelled(a, b) or a.wr ~= tok then return end
			b.hum.Health = math.max(1, b.hum.Health - (slam.slamDamage or 14))
			addDamage(a.char, slam.slamDamage or 14)
			applyInjury(b, "Ribs", slam.slamInjury or 10, "slam")
			hitFX(b.char, 1, "hit")
			sigFX:FireAllClients("slam", a.char, b.char, workspace:GetServerTimeNow())
		end)
	end
	if not holdTrackEnd(ta, pairLen(pair), nil, function() return pairCancelled(a, b) end) then return end
	if pairCancelled(a, b) then      -- waehrenddessen zurueckgesetzt, Kampfende oder Spieler weg
		for _, f in ipairs({ a, b }) do if f.wr then wrStopAll(f, 0.1); setWrestle(f, nil, nil); f.busyUntil = 0 end end
		return
	end
	if defended then
		endExchange(a, b, pair)
		return
	end
	b.hum.Health = math.max(1, b.hum.Health - TD_DAMAGE)
	a.char:SetAttribute("CC_Takedowns", (a.char:GetAttribute("CC_Takedowns") or 0) + 1)
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
	local root = f.char:FindFirstChild("HumanoidRootPart")
	if root then root.Anchored = true end                         -- Reset atomar: kein Physik-Frame zwischen Pose und Zielposition
	f.attackToken = (f.attackToken or 0) + 1
	f.animToken = (f.animToken or 0) + 1
	if f.wr then
		local partner = f.wr.partner
		wrStopAll(f, 0.08); setWrestle(f, nil, nil)
		if partner and partner.wr then
			partner.animToken = (partner.animToken or 0) + 1
			wrStopAll(partner, 0.08); setWrestle(partner, nil, nil)
			partner.busyUntil = 0; partner.wantEscape = nil
			if partner.tracks.idle and not partner.tracks.idle.IsPlaying then partner.tracks.idle:Play(0.12) end
		end
	end
	clearDown(f, true)
	setBlock(f, false); f.wantBlock = false; f.wantEscape = nil
	for k, tr in pairs(f.tracks) do if k ~= "idle" then tr:Stop(0.08) end end
	for _, tr in pairs(f.sigTracks or {}) do if tr and tr.IsPlaying then tr:Stop(0.08) end end
	f.sigActive = false; f.sigTrack = nil
	if f.instinct then f.instinct = nil; f.char:SetAttribute("CC_Instinct", nil); f.char:SetAttribute("CC_InstinctDodges", nil) end
	if not f.tracks.idle.IsPlaying then f.tracks.idle:Play(0.12) end
	f.idleOff = false; f.tracks.idle:AdjustWeight(1, 0.08)
	f.knockToken = (f.knockToken or 0) + 1
	local newFight = f.char:GetAttribute("CC_ResetKnockdowns")
	if newFight then
		f.knockdowns = 0
		f.char:SetAttribute("CC_Knockdowns", 0)
		f.char:SetAttribute("CC_ResetKnockdowns", nil)
		f.char:SetAttribute("CC_DoctorRisk", nil)
		f.char:SetAttribute("CC_HeadDamage", 0)
		f.char:SetAttribute("CC_Stoppage", nil)
		f.char:SetAttribute("CC_Checks", 0)
		f.char:SetAttribute("CC_LegCheck", nil)
		f.char:SetAttribute("CC_InjuryEvent", nil)
		for _, region in ipairs(INJURY_REGIONS) do
			f.char:SetAttribute("CC_Injury_" .. region, 0)
			f.char:SetAttribute("CC_Broken_" .. region, nil)
		end
		f.char:SetAttribute("CC_LegDamage", 0)
		f.char:SetAttribute("CC_Mobility", 100)
		f.char:SetAttribute("CC_MobilitySpeed", f.speed)
		f.headTrauma, f.bodyTrauma, f.groundTrauma = 0, 0, 0
	else
		-- Zwischen Runden bleibt ein Teil des Schadens bestehen, aber der Kaempfer bekommt Erholung.
		f.headTrauma = (f.headTrauma or 0) * 0.72
		f.bodyTrauma = (f.bodyTrauma or 0) * 0.76
		f.groundTrauma = 0
	end
	f.rockedUntil, f.gnpHits, f.gnpLast = 0, 0, 0
	f.char:SetAttribute("CC_Rocked", false); f.char:SetAttribute("CC_RockLevel", 0)
	f.char:SetAttribute("CC_UnansweredGroundHits", 0)
	syncTrauma(f)
	f.loco = nil; f.ko = false; f.knocked = false; f.busyUntil = 0; f.mode = nil
	f.hum.Sit = false; f.hum.PlatformStand = false
	f.hum.WalkSpeed = injuryWalkSpeed(f)      -- Kampftempo mit eventueller Beinverletzung; in der Lobby setzt der Client das Locker-Tempo
	for _, k in ipairs({ "CC_GroundPos", "CC_SubProgress", "CC_SubName", "CC_SubRole", "CC_DownBlocked", "CC_Knockdown", "CC_Count" }) do f.char:SetAttribute(k, nil) end
	f.char:SetAttribute("CC_KO", false); f.char:SetAttribute("CC_Wrestle", false)
	f.hum.Health = health or f.hum.MaxHealth
	if root then
		if cf then root.CFrame = cf end
		root.AssemblyLinearVelocity = Vector3.zero; root.AssemblyAngularVelocity = Vector3.zero
		root.Anchored = false
	end
	pcall(function() f.hum:ChangeState(Enum.HumanoidStateType.Running) end)
	return true
end

-- Ausgeruestete Signatur: Attribut CC_Signature am Spieler (CC_Profile) oder Test-Attribut am Workspace (nur Studio-Tests)
local function equippedSig(f)
	local p = game.Players:GetPlayerFromCharacter(f.char)
	if not p then return nil end
	local trial = p:GetAttribute("CC_SigTrial")
	local id = workspace:GetAttribute(SIG.TEST_ATTR) or trial or p:GetAttribute("CC_Signature")
	if trial and id == trial then                                   -- Uebung beim Trainer: nur im Trainingskampf
		local ms = RS:FindFirstChild("CC_MatchState")
		if not ms or ms:GetAttribute("Mode") ~= "training" then return nil end
	end
	return id and SIG.list[id] and id or nil
end
local signatureMotion = require(RS:WaitForChild("CC_SignatureMotion"))
local function sigTrackFor(f, def)
	f.sigTracks = f.sigTracks or {}
	if signatureMotion.Has(def.anim) then
		if not f.sigTracks[def.anim] then f.sigTracks[def.anim] = signatureMotion.Create(f.char, def.anim) end
		return f.sigTracks[def.anim]
	end
	if f.sigTracks[def.anim] == nil then
		local ok, tr = pcall(function()
			local a = Instance.new("Animation")
			a.AnimationId = ANIM_IDS[def.anim] and ("rbxassetid://" .. tostring(ANIM_IDS[def.anim])) or KSP:RegisterKeyframeSequence(A[def.anim])
			return f.hum.Animator:LoadAnimation(a)
		end)
		f.sigTracks[def.anim] = ok and tr or false
		if ok then tr.Priority = Enum.AnimationPriority.Action else warn("[CC] Signatur-Animation fehlt: " .. def.anim) end
	end
	return f.sigTracks[def.anim] or nil
end
-- Signatur: echte Attacke mit eigenen Trefferfenstern; Server prueft Ausruestung, Fokus, Ausdauer, Kampfzustand und Reichweite.
local function signature(f)
	local id = equippedSig(f); if not id then return end
	local def = SIG.list[id]
	local function fail(why) f.char:SetAttribute("CC_SigDenied", why .. "|" .. workspace:GetServerTimeNow()) end
	if f.ko or f.blocking or f.wr or f.down or frozen(f) or f.sigActive then return end
	local ms = RS:FindFirstChild("CC_MatchState")
	if not f.char:GetAttribute("CC_Opponent") or not ms or ms:GetAttribute("Mode") == "tutorial" or ms:GetAttribute("State") ~= "fight" then return end
	if os.clock() < f.busyUntil then return end
	if (f.focus or 0) < SIG.FOCUS_MAX then fail("focus") return end
	if f.stamina < def.stamina then f.char:SetAttribute("CC_Tired", workspace:GetServerTimeNow()); fail("stamina") return end
	local opp = opponentOf(f)
	if not opp or opp.ko or opp.wr or opp.down then fail("position") return end
	if def.special == "instinct" then
		-- Ali: Instinkt-Modus. Weicht def.dodges Treffern automatisch aus, Calf Kick (Low Kick) mit def.calfMult Schaden; endet nach def.duration s
		f.focus = 0; f.char:SetAttribute("CC_Focus", 0); spend(f, def.stamina)
		local token = {}
		f.instinct = { untilT = os.clock() + def.duration, dodges = def.dodges, token = token }
		f.char:SetAttribute("CC_InstinctDodges", def.dodges)
		f.char:SetAttribute("CC_Instinct", workspace:GetServerTimeNow() + def.duration)
		sigFX:FireAllClients("start", f.char, id, workspace:GetServerTimeNow())
		print(("[CC] %s Signatur %s (Instinkt %.1f s)"):format(f.char.Name, id, def.duration))
		task.delay(def.duration, function()
			if f.instinct and f.instinct.token == token then
				f.instinct = nil; f.char:SetAttribute("CC_Instinct", nil); f.char:SetAttribute("CC_InstinctDodges", nil)
				sigFX:FireAllClients("instinct_end", f.char)
			end
			if workspace:GetAttribute(SIG.TEST_ATTR) then f.focus = SIG.FOCUS_MAX; f.char:SetAttribute("CC_Focus", f.focus) end
		end)
		return
	end
	local d = (opp.char.HumanoidRootPart.Position - f.char.HumanoidRootPart.Position) * Vector3.new(1, 0, 1)
	if d.Magnitude > def.range then f.char:SetAttribute("CC_OutOfRange", workspace:GetServerTimeNow()); fail("range") return end
	if f.char.HumanoidRootPart.CFrame.LookVector:Dot(d.Unit) < 0.5 then fail("position") return end
	if def.special == "takedown" then
		f.focus = 0; f.char:SetAttribute("CC_Focus", 0); spend(f, def.stamina)
		f.sigActive = true; sigFX:FireAllClients("start", f.char, id, workspace:GetServerTimeNow())
		task.spawn(function()
			tryTakedown(f, true, def.slam and def or nil)
			f.sigActive = false
			if workspace:GetAttribute(SIG.TEST_ATTR) then f.focus = SIG.FOCUS_MAX; f.char:SetAttribute("CC_Focus", f.focus) end
		end)
		return
	end
	local track = sigTrackFor(f, def); if not track then fail("anim") return end
	-- Versuch: ganzer Fokus und Ausdauer werden verbraucht (auch wenn er verfehlt, geblockt oder unterbrochen wird)
	f.focus = 0; f.char:SetAttribute("CC_Focus", 0)
	if workspace:GetAttribute(SIG.TEST_ATTR) then task.delay(def.length + 0.3, function() f.focus = SIG.FOCUS_MAX; f.char:SetAttribute("CC_Focus", f.focus) end) end
	spend(f, def.stamina)
	for k in pairs(MOVES) do local tr = f.tracks[k]; if tr.IsPlaying then tr:Stop(0.06) end end
	f.attackToken = (f.attackToken or 0) + 1
	local token = f.attackToken
	local speed = 1
	f.animSpeed = speed; f.sigActive = true; f.sigTrack = track
	f.busyUntil = os.clock() + def.lock
	track:Play(0.05, 1, speed)
	local start = workspace:GetServerTimeNow()
	sigFX:FireAllClients("start", f.char, id, start)
	print(("[CC] %s Signatur %s"):format(f.char.Name, id))
	local t0 = os.clock()
	for i, h in ipairs(def.hits) do
		local base = MOVES[h.move]
		local m = { win = h.win, limb = h.limb, zone = h.zone, damage = base.damage * h.scale, react = h.react, ko = h.ko,
			heavy = true, bodyShot = h.bodyShot, noRewind = true }
		local done = false
		local conn
		conn = RunService.Heartbeat:Connect(function()
			local t = track.IsPlaying and track.TimePosition or math.huge     -- Trefferfenster in Animationszeit (Hitstop verschiebt nichts)
			if done or f.ko or not f.char.Parent or f.attackToken ~= token or t > h.win[2] then
				conn:Disconnect()
				if not done and f.attackToken == token and not f.ko then sigFX:FireAllClients("miss", f.char, i) end
				return
			end
			if t < h.win[1] then return end
			local fist = bonePos(f.char, h.limb, LIMB_OFFSET[h.limb])
			if not fist or opp.ko or opp.wr or opp.down then return end
			local hitZone = false
			for _, z in ipairs(ZONES[h.zone]) do
				local zp = bonePos(opp.char, z.bone, z.along)
				if zp and (fist - zp).Magnitude <= z.radius + (base.hitRadius or 0.4) then hitZone = true break end
			end
			if hitZone then
				done = true; conn:Disconnect()
				local blocked = opp.blocking
				land(f, opp, "sig_" .. id .. "_" .. i, m, track)
				sigFX:FireAllClients(blocked and "block" or "hit", f.char, i, opp.char)
				local pl = game.Players:GetPlayerFromCharacter(f.char)
				if pl and not blocked and i == #def.hits and pl:GetAttribute("CC_SigTrial") == id then
					-- Uebung bestanden: letzter Schlag der Kombination sauber gelandet -> freischalten (Profil) und Uebung beenden
					pl:SetAttribute("CC_SigTrial", nil)
					local pe = game.ServerStorage:FindFirstChild("CC_ProfileEvent"); if pe then pe:Fire(pl, "sig_unlock", id) end
					pl:SetAttribute("CC_SigLearned", id .. "|" .. workspace:GetServerTimeNow())
				end
				if opp.ko and not blocked and ms then
					-- Finisher: Ergebnis steht (K.o. durch Signatur, vom Server bestaetigt); CC_Match zeigt danach die Wiederholung
					ms:SetAttribute("Finisher", game:GetService("HttpService"):JSONEncode({ attacker = f.char.Name, target = opp.char.Name,
						sig = id, start = start, impact = workspace:GetServerTimeNow() }))
				end
			end
		end)
	end
	task.spawn(function()
		local deadline = os.clock() + def.length + 1.5
		while track.IsPlaying and f.attackToken == token and os.clock() < deadline do RunService.Heartbeat:Wait() end
		if f.sigTrack == track and f.attackToken == token then f.sigActive = false end
	end)
end

RS.CC_Action.OnServerEvent:Connect(function(player, move)
	local f = player.Character and fighters[player.Character]
	if not (f and type(move) == "string") then return end
	if f.sigActive then return end -- auch waehrend Treffer-Hitstop keine zweite Attacke ueber die Signatur legen
	if not f.char:GetAttribute("CC_Opponent") then return end   -- in der Lobby wird nicht gekaempft
	if f.down then                                                   -- am Boden (liegend/sitzend/kniend), Gegner steht
		if move == "escape" then task.spawn(downGetUp, f)
		elseif move == "takedown" then task.spawn(downPosture, f)
		elseif move == "jab" or move == "cross" or move == "jabBody" or move == "crossBody" then task.spawn(downKick, f, "up")
		elseif move == "lowkick" or move == "bodykick" or move == "frontkick" then task.spawn(downKick, f, "leg") end
		return
	end
	local opp = not f.wr and opponentOf(f)
	if opp and opp.down then                                         -- stehend gegen Liegenden: nur Beine treten oder in die Guard
		if move == "lowkick" then task.spawn(legKickDown, f, opp) return end
		if move == "takedown" then task.spawn(enterGuardFromStand, f, opp) return end
	end
	if move == "escape" then groundEscape(f)
	elseif f.wr then
		if f.wr.role == "top" and f.wr.state == "sub" then if move == "hook" then f.mash = (f.mash or 0) + 1 end
		elseif f.wr.role == "top" then
			if move == "jab" then task.spawn(groundPunch, f) elseif move == "takedown" then task.spawn(groundAdvance, f) elseif move == "hook" then task.spawn(groundSubmit, f) end
		end
	elseif move == "takedown" then tryTakedown(f)
	elseif move == "signature" then signature(f)
	else attack(f, move) end
end)
RS.CC_Block.OnServerEvent:Connect(function(player, on)
	local f = player.Character and fighters[player.Character]
	if f and on and f.sigActive then return end                         -- Signatur laeuft als Ganzes (oder wird durch Treffer unterbrochen)
	if f and on and not f.char:GetAttribute("CC_Opponent") then return end
	if f and f.down then                                              -- Block am Boden: enge Deckung (Rueckenlage) und weniger Schaden
		f.downBlock = on == true
		if not f.down.busy then downIdle(f, 0.12) end
	elseif f and not f.wr then setBlock(f, on == true) end
	if f and on then f.sprawlAt = os.clock() end -- F gedrueckt = Sprawl-Versuch gegen Takedowns
end)

local dummy = workspace:WaitForChild("CC_TrainingDummy")
local D = setup(dummy)
local fill = dummy.HumanoidRootPart.HealthBar.Frame.Fill
D.hum.HealthChanged:Connect(function(h) fill.Size = UDim2.fromScale(math.max(h, 0) / D.hum.MaxHealth, 1) end)
-- Trainingsgegner (Section 7): bewegt sich wie ein Kaempfer. Laeuft ueber Humanoid:Move (Server-Physik, nicht mehr verankert),
-- dadurch spielen die Fussarbeit-Loops automatisch. Verhalten:
--   weit weg -> Druck nach vorn; in Distanz (Wunschabstand) -> umkreisen, Richtungswechsel, kleine Vor-/Rueckschritte;
--   Angriff: in Reichweite schlagen/treten, sonst erst hineinsteppen; nach Kombinationen oft wieder heraus;
--   wenig Leben/Ausdauer -> mehr Abstand; am Gitter -> zur Mitte hin kreisen.
-- CC_Passive = Trainingsmodus (steht nur und dreht sich), CC_ForceTD = Test-Takedown, CC_NoTD = Test ohne Takedowns,
-- CC_ForceLegKick = Test: sofort Low Kick gegen den liegenden Gegner.
local root0 = dummy.HumanoidRootPart
root0.Anchored = false
pcall(function() root0:SetNetworkOwner(nil) end)
D.hum.AutoRotate = false
local DUMMY_RANGE = { jab = 4.4, cross = 4.4, hook = 3.2, uppercut = 3.0, lowkick = 3.2, bodykick = 3.8, highkick = 3.0, frontkick = 4.0, jabBody = 4.4, crossBody = 4.4 }
local CAGE_SAFE = 11.5         -- ab hier Richtung Mitte kreisen
local TURN = 10                -- Drehrate zum Gegner (1/s)
local nextThink, circleDir, nextSwitch, stepUntil, stepDir = 0, 1, 0, 0, 0
local combo, comboAt = nil, 0
local function arenaCenter()
	local arena = workspace:FindFirstChild("CC_Arena")
	local c = arena and arena:FindFirstChild("Platform_Canvas_FightSurface", true)
	return c and Vector3.new(c.Position.X, 0, c.Position.Z) or Vector3.zero
end
local CENTER = arenaCenter()
local lastAnchored = false
-- Reaktion auf eingesteckte Treffer: Schaden der letzten Sekunden (klingt ab). Ein Treffer bricht die eigene Kombination ab;
-- danach je nach Schaden/Angeschlagen: Deckung + Rueckzug ("cover") oder sofortiger Konter ("counter").
local hitDmg, lastHitAt, lastHP, reactUntil, reactKind = 0, -99, D.hum.Health, 0, nil
D.hum.HealthChanged:Connect(function(hp)
	local d = lastHP - hp; lastHP = hp
	if d <= 0.5 or D.wr or D.down or D.ko then return end
	local now = os.clock()
	hitDmg = hitDmg * math.exp(-(now - lastHitAt) / 2.0) + d
	lastHitAt = now
	combo = nil                                                       -- getroffen: eigene Serie bricht ab
	if dummy:GetAttribute("CC_Passive") or dummy:GetAttribute("CC_Tutor") then return end
	local LV = DummyLevel()
	local rocked = dummy:GetAttribute("CC_Rocked") == true
	if rocked or hitDmg >= 14 or D.hum.Health < 30 then
		reactKind, reactUntil = "cover", now + 0.9 + math.min(hitDmg, 30) / 30   -- schwer getroffen: Deckung hoch, Abstand holen
	elseif math.random() < math.clamp(0.25 + LV.aggr * 0.35, 0.2, 0.6) then
		reactKind, reactUntil = "counter", now + 0.6                      -- leichter Treffer: zurueckschlagen
	else
		reactKind, reactUntil = "cover", now + 0.5
	end
end)
RunService.Heartbeat:Connect(function(dt)
	local root = dummy.HumanoidRootPart
	if root.Anchored ~= lastAnchored then        -- nach dem Ringkampf wieder vom Server steuern
		lastAnchored = root.Anchored
		if not root.Anchored then pcall(function() root:SetNetworkOwner(nil) end) end
	end
	if D.ko or D.wr then return end
	if frozen(D) then setBlock(D, false); D.hum:Move(Vector3.zero); return end
	if D.down then                                                   -- Trainingsgegner liegt: aufstehen, Tritte, Haltung
		local nowD = os.clock()
		if nowD >= (D.downThink or 0) and not D.down.busy and not dummy:GetAttribute("CC_Passive") and dummy:GetAttribute("CC_InMatch") ~= false then
			D.downThink = nowD + 0.8 + math.random() * 0.9
			local o = opponentOf(D)
			local dist = o and ((o.char.HumanoidRootPart.Position - downBodyPos(D)) * Vector3.new(1, 0, 1)).Magnitude or 99
			local r = math.random()
			local downFor = nowD - (D.down.enteredAt or nowD)
			if dist >= PRESSURE_DIST and downFor >= 2.2 then task.spawn(downGetUp, D) -- nicht zufaellig liegenbleiben
			elseif D.down.state == "back" and dist < 5.5 and r < 0.60 then task.spawn(downKick, D, dist < 4.2 and "up" or "leg")
			elseif dist >= PRESSURE_DIST and r < 0.82 then task.spawn(downGetUp, D)
			elseif r < 0.92 then task.spawn(downPosture, D) end
		end
		D.hum:Move(Vector3.zero)
		return
	end
	-- nur im aktiven Kampf: CC_Match setzt den exakten Gegner erst nach Walkout/Intro.
	-- Ohne CC_Opponent darf die KI niemanden in Lobby oder Einlauf angreifen.
	if dummy:GetAttribute("CC_InMatch") == false then setBlock(D, false); D.hum:Move(Vector3.zero) return end
	local oppName = dummy:GetAttribute("CC_Opponent")
	local oppChar = type(oppName) == "string" and oppName ~= "" and workspace:FindFirstChild(oppName) or nil
	if not oppChar then setBlock(D, false); D.hum:Move(Vector3.zero) return end
	local best, bestDist
	for char, f in pairs(fighters) do
		if f ~= D and not f.ko and not f.knocked and char == oppChar then
			local dist = (char.HumanoidRootPart.Position - root.Position).Magnitude
			if not bestDist or dist < bestDist then best, bestDist = f, dist end
		end
	end
	if not best then setBlock(D, false); D.hum:Move(Vector3.zero) return end
	local tp = best.char.HumanoidRootPart.Position
	local toT = Vector3.new(tp.X - root.Position.X, 0, tp.Z - root.Position.Z)
	local dist = toT.Magnitude
	-- zum Gegner drehen (nur Drehung, Position bleibt der Physik ueberlassen)
	if dist > 0.1 then
		local goal = CFrame.lookAt(root.Position, root.Position + toT)
		root.CFrame = root.CFrame:Lerp(goal, 1 - math.exp(-TURN * dt))
	end
	if dummy:GetAttribute("CC_ForceTD") then dummy:SetAttribute("CC_ForceTD", nil); task.spawn(tryTakedown, D) return end -- Test: Takedown sofort
	local fa = dummy:GetAttribute("CC_ForceAttack")
	if fa and MOVES[fa] then dummy:SetAttribute("CC_ForceAttack", nil); setBlock(D, false); task.spawn(attack, D, fa) return end -- Test: ein Schlag sofort
	local style, styleName = DummyStyle()
	if dummy:GetAttribute("CC_AIStyleActive") ~= styleName then dummy:SetAttribute("CC_AIStyleActive", styleName) end
	if dummy:GetAttribute("CC_Passive") or frozen(D) then
		setBlock(D, dummy:GetAttribute("CC_ForceBlock") == true and not frozen(D)); D.hum:Move(Vector3.zero)   -- CC_ForceBlock: Test (Dauerblock)
		-- Tutorial (CC_Tutor am Gegner, von CC_Tutorial gesetzt): langsam angekuendigte Einzelaktionen statt normaler KI.
		--   "strike" = Jab, "td"/"ground" = Takedown. Ankuendigung 1,0 s vorher als Attribut CC_Telegraph ("strike|zeit" / "td|zeit"), dann 3 s Pause.
		local tutor = not frozen(D) and dummy:GetAttribute("CC_Tutor")
		if (tutor == "strike" or tutor == "td" or tutor == "ground") and (best.down or best.wr) then
			-- Spieler liegt/ringt: keine neue Ankuendigung; Lektion 6: Platz machen, damit Aufstehen moeglich ist (Druck-Abstand 4,2)
			D.tutorAt = nil
			if tutor == "ground" and best.down and dist < 7 then D.hum:Move(-toT.Unit, false) end
		elseif tutor == "strike" or tutor == "td" or tutor == "ground" then
			local reach = tutor == "strike" and 4.0 or TD_RANGE - 0.6
			if dist > reach and not D.tutorAt then D.hum:Move(toT.Unit, false) end
			local now = os.clock()
			if not D.tutorAt and dist <= reach + 0.5 and now >= (D.tutorNext or 0) and now >= D.busyUntil then
				D.tutorAt = now + 1.0
				dummy:SetAttribute("CC_Telegraph", (tutor == "strike" and "strike" or "td") .. "|" .. workspace:GetServerTimeNow())
			elseif D.tutorAt and now >= D.tutorAt then
				D.tutorAt = nil; D.tutorNext = now + 3.0
				if tutor == "strike" then task.spawn(attack, D, "jab") else task.spawn(tryTakedown, D) end
			end
		else D.tutorAt = nil end
		local rg = DummyLevel().regen                              -- Passiv: Leben langsam zurueck (zum Ueben von Angriffen)
		if dummy:GetAttribute("CC_Passive") and rg > 0 and D.hum.Health > HP_FLOOR then D.hum.Health = math.min(D.hum.MaxHealth, D.hum.Health + rg * dt) end
		return
	end
	if best.down then                                                -- Gegner liegt: an die Beine heran, Low Kicks oder in die Guard
		local bp = downBodyPos(best)
		local toB = (bp - root.Position) * Vector3.new(1, 0, 1)
		local dB = toB.Magnitude
		setBlock(D, false)
		if dummy:GetAttribute("CC_ForceLegKick") then dummy:SetAttribute("CC_ForceLegKick", nil); task.spawn(legKickDown, D, best) end   -- Test-Attribut
		D.hum:Move((dB > 6.0 and toB.Unit) or (dB < 4.8 and -toB.Unit) or Vector3.zero, false)
		if os.clock() >= nextThink and os.clock() >= D.busyUntil and dB <= 6.6 then
			nextThink = os.clock() + 1.4 + math.random() * 1.2
			local r = math.random()
			if r < 0.4 then task.spawn(legKickDown, D, best)
			elseif r < 0.7 and best.down.state == "back" then task.spawn(enterGuardFromStand, D, best) end
		end
		return
	end
	local now = os.clock()
	local fwd = dist > 0.1 and toT.Unit or root.CFrame.LookVector
	local right = Vector3.new(-fwd.Z, 0, fwd.X)
	local hurt = D.hum.Health < 35 or D.stamina < 30
	local want = style.want + (hurt and 1.2 or 0)
	-- ---- Reaktion auf Treffer (siehe HealthChanged oben) ----
	if reactKind and now < reactUntil and not D.down and not (D.busyUntil and now < D.busyUntil) then
		if reactKind == "cover" then
			setBlock(D, true)
			local away = -fwd + right * circleDir * 0.6
			D.hum:Move(dist < want + 2 and away.Unit or Vector3.zero, false)
			if now + 0.05 >= reactUntil then setBlock(D, false); reactKind = nil; nextThink = math.max(nextThink, now + 0.3) end
			return
		elseif reactKind == "counter" then
			reactKind = nil
			if dist <= (DUMMY_RANGE.jab or 4.4) + 0.4 and D.stamina >= 10 then
				setBlock(D, false)
				combo = (math.random() < 0.5) and { "jab", "cross" } or { "hook" }
				if dist > (DUMMY_RANGE[combo[1]] or 4) then combo = { "jab", "cross" } end
				comboAt = now
			end
		end
	elseif reactKind and now >= reactUntil then
		if reactKind == "cover" then setBlock(D, false) end
		reactKind = nil
	end
	-- ---- Bewegung ----
	if now > nextSwitch then circleDir = -circleDir; nextSwitch = now + 1.2 + math.random() * 2.0 end
	local off = Vector3.new(root.Position.X, 0, root.Position.Z) - CENTER
	if off.Magnitude > CAGE_SAFE then                     -- am Gitter: in die Richtung kreisen, die zur Mitte fuehrt
		circleDir = (right:Dot(-off) >= 0) and 1 or -1
	end
	local move
	local busy = now < D.busyUntil
	if busy then
		move = Vector3.zero                                -- waehrend eines Schlags nicht laufen (Schritt steckt in der Animation)
	elseif now < stepUntil then
		move = fwd * stepDir                               -- kurzer Schritt hinein / heraus
	elseif dist > want + 2.5 then
		move = fwd + right * circleDir * 0.25              -- Druck nach vorn, leicht versetzt
	else
		local radial = math.clamp((dist - want) * 0.8, -1, 1)
		if math.abs(dist - want) < 0.35 then radial = 0 end
		move = fwd * radial + right * circleDir * 0.75
		if off.Magnitude > CAGE_SAFE + 1.5 then move += -off.Unit * 0.6 end
	end
	-- immer volle Geschwindigkeit oder Stillstand (wie Tastatur): bei Teilgeschwindigkeit sind die Lauf-Loops nur halb
	-- eingeblendet und die Fuesse rutschen (gemessen: Median 54 % der Koerpergeschwindigkeit)
	D.hum:Move(move.Magnitude > 0.35 and move.Unit or Vector3.zero, false)
	-- ---- laufende Kombination fortsetzen ----
	if combo and now >= comboAt and not busy then
		local m = table.remove(combo, 1)
		if m and dist <= (DUMMY_RANGE[m] or 4) + 0.6 then attack(D, m); comboAt = now + 0.05 else combo = nil end
		if combo and #combo == 0 then
			combo = nil
			-- Nach jeder Kombination eine sichtbare Erholungsphase: verhindert endlose Trefferketten,
			-- gibt dem Spieler Zeit zum Blocken/Ausweichen und wirkt wie echtes Zuruecksetzen der Deckung.
			nextThink = math.max(nextThink, now + 0.55 + math.random() * 0.35)
			if math.random() < 0.55 then stepDir, stepUntil = -1, now + 0.6 + 0.35 end
		end
		return
	end
	-- ---- Entscheidung ----
	if now < nextThink or busy then return end
	local LV = DummyLevel()
	-- Fairness: "Fehler" wird erst nach einem vollstaendig verfehlten Angriff sichtbar. Keine RemoteEvent-/Tasteneingabe wird gelesen.
	local punish = best.lastMissAt and now - best.lastMissAt < 0.9
	local predictable = best.repeatCount and best.repeatCount >= 3 and best.lastResolvedAt and now - best.lastResolvedAt < 1.4
	nextThink = now + LV.reaction[1] + math.random() * LV.reaction[2]
	if dist <= 5.8 then
		local r = math.random()
		local tdChance = math.clamp(LV.td * style.td + (punish and style.td > 1 and 0.08 or 0), 0, 0.45)
		local blockChance = math.clamp(LV.block * style.block + (predictable and 0.10 or 0), 0, 0.48)
		local aggression = math.clamp(LV.aggr * style.aggr + (punish and 0.22 or 0), 0, 0.88)
		local tdT, blkT = tdChance, tdChance + blockChance
		if r < tdT and best.hum.Health > HP_FLOOR and not best.wr and dist <= 5 and not dummy:GetAttribute("CC_NoTD") then
			setBlock(D, false); task.spawn(tryTakedown, D)
		elseif r < blkT then
			setBlock(D, true)
			task.delay(0.55 + math.random() * 0.55, function() setBlock(D, false) end)
		elseif (r < blkT + aggression and not hurt or r < blkT + aggression * 0.6) and LV.combo > 0 then
			setBlock(D, false)
			local c = table.clone(style.combos[math.random(#style.combos)])
			while #c > LV.combo do table.remove(c) end               -- Kombolaenge je Stufe begrenzen
			local first = c[1]
			if dist > (DUMMY_RANGE[first] or 4) then
				stepDir, stepUntil = 1, now + math.clamp((dist - (DUMMY_RANGE[first] or 4) + 0.3) / 8, 0.1, 0.35)   -- erst hineinsteppen
				comboAt = stepUntil
			else
				comboAt = now
			end
			combo = c
		else
			setBlock(D, false)
			if math.random() < 0.4 then stepDir, stepUntil = (math.random() < 0.5 and 1 or -1), now + 0.25 end    -- Finte / Rhythmus
		end
	else
		setBlock(D, false)
	end
end)
