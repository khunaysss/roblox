-- StarterPlayer.StarterPlayerScripts.CC_FinishReactions
-- Lokale Zusatzbewegung und Gesicht fuer Submission und K.o. (nur Optik, jeder Client fuer alle Kaempfer, nichts wird gespeichert).
-- Gebunden an bestaetigte Serverzustaende aus CC_CharacterAnimations:
--   CC_SubRole = "defend" + CC_SubProgress  -> Verteidiger: kurze, unregelmaessige Befreiungsstoesse (Schultern, Oberkoerper, freie Hand).
--                                             Der gegriffene Arm und die Huefte bleiben unberuehrt (Griffkontakt der Paar-Animation).
--   CC_SubProgress zuletzt >= 0.99 und Duell vom Server beendet, oder CC_LastReact = "submission" -> sichtbares Abklopfen (3x, freie Hand).
--   CC_KO = true (nicht Submission)          -> benommenes Gesicht (Augen fast geschlossen). Der Fall selbst bleibt die vorhandene
--                                             K.o.-Animation (Rig = ein Skin-Mesh mit Bones, keine Teile fuer eine Physik-Ragdoll).
-- Submission-Verteidiger: angestrengtes Gesicht (Augen zusammengekniffen, Mund flach). Alles wird beim Ende des Zustands, bei
-- Kampfende, Reset und Respawn zurueckgesetzt (Originalgroessen pro Teil gemerkt; Aussehen im Profil bleibt unveraendert).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local okX, XRay = pcall(require, game:GetService("ReplicatedStorage"):WaitForChild("CC_XRay", 10))
local localPlayer = Players.LocalPlayer
local records = {}          -- [char] = { bones, raw, face, sub = {...}, tap = {...} }
local lastSub = {}          -- [char] = { name, at } -- bleibt ueber das Aufraeumen hinaus (KO-Bestaetigung kommt bis ~3 s spaeter)
local BONES = { "UpperTorso", "Head", "LeftUpperArm", "LeftLowerArm", "RightUpperArm", "RightLowerArm" }

local function fighterChars()
	local list = {}
	for _, p in ipairs(Players:GetPlayers()) do if p.Character then table.insert(list, p.Character) end end
	local d = workspace:FindFirstChild("CC_TrainingDummy")
	if d then table.insert(list, d) end
	return list
end

local function record(char)
	local r = records[char]
	if r then return r end
	local root = char:FindFirstChild("HumanoidRootPart")
	if not root then return nil end
	local bones = {}
	for _, n in ipairs(BONES) do
		local b = root:FindFirstChild(n, true)
		if b and b:IsA("Bone") then bones[n] = b end
	end
	if not bones.UpperTorso then return nil end
	r = { char = char, bones = bones, raw = {}, face = {}, faceMode = nil, rng = Random.new(#char.Name * 7919 + os.clock() * 1000) }
	records[char] = r
	return r
end

-- Gesicht: Teile Face_*_Eye_*, *_Eye_Glint_*, *_Mouth am Charakter (CC_LookShared). Nur lokal skaliert/ausgeblendet.
local function faceParts(char)
	local eyes, glints, mouths = {}, {}, {}
	for _, p in ipairs(char:GetChildren()) do
		if p:IsA("BasePart") and p.Name:sub(1, 5) == "Face_" then
			if p.Name:find("_Eye_Glint_") then table.insert(glints, p)
			elseif p.Name:find("_Eye_") then table.insert(eyes, p)
			elseif p.Name:find("_Mouth") then table.insert(mouths, p) end
		end
	end
	return eyes, glints, mouths
end
local function restoreFace(r)
	for part, orig in pairs(r.face) do
		if part.Parent then part.Size = orig.size; part.LocalTransparencyModifier = orig.ltm end
	end
	table.clear(r.face)
	r.faceMode = nil
end
local function setFace(r, mode)
	if r.faceMode == mode then return end
	restoreFace(r)
	if not mode then return end
	r.faceMode = mode
	local eyes, glints, mouths = faceParts(r.char)
	local function keep(p) if not r.face[p] then r.face[p] = { size = p.Size, ltm = p.LocalTransparencyModifier } end end
	local eyeY = mode == "ko" and 0.14 or 0.5           -- K.o.: fast geschlossen; Submission: zusammengekniffen
	for _, p in ipairs(eyes) do keep(p); p.Size = Vector3.new(p.Size.X, p.Size.Y * eyeY, p.Size.Z) end
	for _, p in ipairs(glints) do keep(p); p.LocalTransparencyModifier = 1 end
	for _, p in ipairs(mouths) do keep(p); p.Size = Vector3.new(p.Size.X * (mode == "sub" and 1.08 or 0.9), p.Size.Y * 0.45, p.Size.Z) end
end

local function restoreBones(r)
	for b, cf in pairs(r.raw) do if b.Parent then b.Transform = cf end end
	table.clear(r.raw)
end
local function cleanup(char)
	local r = records[char]
	if not r then return end
	restoreBones(r); restoreFace(r)
	records[char] = nil
end

local function boneWorld(char, name)
	local root = char:FindFirstChild("HumanoidRootPart")
	local b = root and root:FindFirstChild(name, true)
	return b and b:IsA("Bone") and b.TransformedWorldCFrame.Position
end
-- Freie Hand = die Hand des Verteidigers, die weiter von beiden Haenden des Angreifers entfernt ist (gegriffener Arm bleibt ruhig).
local function freeSide(char)
	local opp = workspace:FindFirstChild(char:GetAttribute("CC_Opponent") or "", true)
	if not (opp and opp:IsA("Model")) then
		for _, c in ipairs(fighterChars()) do if c ~= char and c:GetAttribute("CC_SubRole") == "attack" then opp = c end end
	end
	if not opp then return "Left" end
	local function near(side)
		local h = boneWorld(char, side .. "Hand"); if not h then return 0 end
		local best = math.huge
		for _, n in ipairs({ "LeftHand", "RightHand", "LeftLowerArm", "RightLowerArm" }) do
			local q = boneWorld(opp, n); if q then best = math.min(best, (q - h).Magnitude) end
		end
		return best
	end
	return near("Left") >= near("Right") and "Left" or "Right"
end

-- Unregelmaessige Stoesse: alle 0,25-0,7 s ein kurzer Impuls (Anstieg 0,07 s, Abklingen ~0,25 s) mit zufaelliger Richtung.
local function pulse(s, now)
	if now >= s.nextAt then
		s.at = now; s.nextAt = now + s.rng:NextNumber(0.25, 0.7)
		s.dir = Vector3.new(s.rng:NextNumber(-1, 1), s.rng:NextNumber(-1, 1), s.rng:NextNumber(-0.6, 0.6))
		s.amp = s.rng:NextNumber(0.6, 1)
	end
	local t = now - s.at
	local env = t < 0.07 and t / 0.07 or math.exp(-(t - 0.07) / 0.12)
	return s.dir * env * s.amp
end
local function rot(v, deg) local k = math.rad(deg); return CFrame.Angles(v.X * k, v.Y * k, v.Z * k) end

local function apply(r, b, cf)
	if not b or not b.Parent then return end
	if not r.raw[b] then r.raw[b] = b.Transform end
	b.Transform = b.Transform * cf
end

RunService.PreAnimation:Connect(function()
	for char, r in pairs(records) do
		restoreBones(r)
		if not char.Parent then cleanup(char) end
	end
end)

RunService:BindToRenderStep("CC_FinishReactions", Enum.RenderPriority.Character.Value + 20, function()
	local now = os.clock()
	for _, char in ipairs(fighterChars()) do
		local role, prog = char:GetAttribute("CC_SubRole"), char:GetAttribute("CC_SubProgress")
		local ko, last = char:GetAttribute("CC_KO") == true, char:GetAttribute("CC_LastReact")
		local r = records[char]
		local defending = role == "defend" and typeof(prog) == "number"
		if r and r.hold and now > r.hold then r.hold = nil end
		if not (defending or ko or (r and (r.tap or r.sub or r.hold))) then
			if r then cleanup(char) end
			continue
		end
		r = r or record(char)
		if not r then continue end
		-- Duellverlauf merken; Ende mit Fortschritt 1 = vom Server bestaetigte Aufgabe
		if defending then
			if not r.sub then r.sub = { rng = r.rng, nextAt = now, at = now - 1, dir = Vector3.zero, amp = 0, side = freeSide(char) } end
			r.sub.last = prog
			local sn = char:GetAttribute("CC_SubName")
			if sn then lastSub[char] = { name = sn, at = now } end
		elseif r.sub then
			-- Fortschritt 1,0 erreicht den Client nicht (Server loescht die Attribute im selben Schritt). Hoher Endstand: angestrengtes
			-- Gesicht bis zur Bestaetigung (CC_LastReact = "submission") halten, hoechstens 3 s; Abklopfen erst nach Bestaetigung.
			if (r.sub.last or 0) >= 0.6 then r.hold = now + 3; r.holdSide = r.sub.side end
			r.sub = nil
		end
		if ko and last == "submission" and not r.tap and not r.tapDone then
			r.tap = { t0 = now, side = r.holdSide or freeSide(char) }; r.hold = nil
			-- Roentgen-Bruch nur bei bestaetigter Armbar und nur fuer Spieler in diesem Kampf (Angreifer und Verteidiger)
			local mine = localPlayer.Character
			if okX and XRay and lastSub[char] and lastSub[char].name == "ARMBAR" and now - lastSub[char].at < 8 and mine and mine:GetAttribute("CC_MatchId") ~= nil
				and mine:GetAttribute("CC_MatchId") == char:GetAttribute("CC_MatchId") then
				lastSub[char] = nil
				XRay.play(localPlayer:WaitForChild("PlayerGui"))
			end
		end
		if not ko and not defending then r.tapDone = nil end
		-- Gesicht
		setFace(r, (defending or r.tap ~= nil or r.hold ~= nil or (ko and last == "submission")) and "sub" or ko and "ko" or nil)
		local B = r.bones
		if defending then
			local s, free = r.sub, r.sub.side
			local v = pulse(s, now)
			local strain = 0.35 + 0.65 * math.clamp(1 - (prog or 0.5), 0, 1)      -- je naeher am Aufgeben, desto verzweifelter
			apply(r, B.UpperTorso, rot(v, 3.2 * strain))
			apply(r, B.Head, rot(Vector3.new(v.Y, v.X, 0), 4 * strain))
			apply(r, B[free .. "UpperArm"], rot(v, 11 * strain))
			apply(r, B[free .. "LowerArm"], rot(Vector3.new(v.Z, v.X, v.Y), 14 * strain))
			local other = free == "Left" and "Right" or "Left"
			apply(r, B[other .. "UpperArm"], rot(v, 2))                  -- gegriffener Arm: nur Anspannung, kein Loesen
		elseif r.tap then
			local t = now - r.tap.t0
			if t > 1.35 then r.tap = nil; r.tapDone = true
			else
				local beat = math.max(0, math.sin(t / 0.45 * math.pi * 2))        -- 3 Schlaege in 1,35 s
				local side = r.tap.side
				apply(r, B[side .. "UpperArm"], CFrame.Angles(math.rad(-24 * beat), 0, 0))
				apply(r, B[side .. "LowerArm"], CFrame.Angles(math.rad(-18 * beat), 0, 0))
			end
		end
	end
end)

Players.PlayerRemoving:Connect(function(p) if p.Character then cleanup(p.Character) end end)
local function hook(p) p.CharacterRemoving:Connect(function(c) cleanup(c); lastSub[c] = nil; if p == localPlayer and okX and XRay then XRay.stop() end end) end
for _, p in ipairs(Players:GetPlayers()) do hook(p) end
Players.PlayerAdded:Connect(hook)
script.Destroying:Connect(function()
	RunService:UnbindFromRenderStep("CC_FinishReactions")
	for char in pairs(records) do cleanup(char) end
end)
