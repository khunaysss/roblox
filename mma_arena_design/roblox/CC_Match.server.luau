-- ServerScriptService.CC_Match
-- Kampf-Ablauf mit Menue. MEHRERE KAEMPFE GLEICHZEITIG (2026-10-19):
--   Jeder Kampf hat einen eigenen Zustand (ReplicatedStorage.CC_Matches.<id>, siehe CC_MatchRegistry) und einen eigenen Kaefig.
--   Kaefige: Fight Night (Walkout; Online/Karriere/Trainer bevorzugt), kleine Arena (CC_Arena; Training/Tutorial/Sparring),
--   Online-Kaefige CC_PvpArena_2..4. KI-Kaempfe (Training, Sparring, Tutorial, Karriere, Trainer) laufen einzeln, weil es nur
--   einen KI-Gegner gibt (CC_TrainingDummy); Online-Kaempfe laufen parallel dazu, so viele wie Kaefige frei sind.
--   Training: Spieler (Rot) gegen den Trainingsgegner (Blau).  Gegen Spieler: die ersten zwei aus der Warteschlange (Rot/Blau).
-- Runden: 3 x 2:00, 10 s Pause, Sieg durch K.o., Submission oder nach Punkten; Aufgabe, wenn ein Spieler geht.
-- Menue -> Server: ReplicatedStorage.CC_Menu (RemoteEvent) mit "training" | "pvp" | "career" | "cancel".
-- Zustand je Kampf (Attribute am Ordner): State ("idle" | "walkout" | "intro" | "fight" | "break" | "finisher" | "over"),
--   Mode, Round, TimeLeft, Banner, BannerSub, ScoreRed, ScoreBlue, Winner, RedName, BlueName, WinnerName, QueuePvp,
--   CageCenter (Vector3, Boden-Oberkante in Y), CageRadius, MatchId.
-- Am Spieler: CC_Queue ("training" | "pvp" | ... | nil), CC_MatchId (waehrend des Kampfs). Am Charakter: CC_Opponent, CC_MatchId.
-- Test: workspace-Attribut CC_RoundTime (Sekunden) ueberschreibt die Rundenzeit; CC_TestPvpDummy = Online gegen KI (1 Spieler).
-- Einstieg (CC_Tutorial, serverseitig ueber CC_MenuServer): "tutorial" / "sparring" wie zuvor.
-- Nach jedem Kampf: Attribut CC_LastFight am Spieler (JSON: mode, result, method, xp).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local RS = game.ReplicatedStorage
local SS = game.ServerStorage
local HttpService = game:GetService("HttpService")
local reset = SS:WaitForChild("CC_ResetFighter")
local OPP = require(RS:WaitForChild("CC_Opponents"))
local SIGPROG = require(RS:WaitForChild("CC_SignatureProgression"))
local Look = require(RS:WaitForChild("CC_LookShared"))
local REG = require(RS:WaitForChild("CC_MatchRegistry"))
local DUMMY_LOBBY_LOOK = { hair = "Hair_QuiffV03", beard = "none", face = "Face_Focused", skin = 2, hairColor = 1 }

local ROUNDS, BREAK_TIME, INTRO_TIME, OVER_TIME = 3, 10, 4, 7
local BREAK_HEAL = 20

-- alter globaler Zustand (ein Kampf) entfaellt: Clients spiegeln ihren Kampf lokal nach CC_MatchState
do local old = RS:FindFirstChild("CC_MatchState"); if old then old:Destroy() end end
local matchRoot = REG.root()
local idle = REG.idle()
local menu = RS:FindFirstChild("CC_Menu") or Instance.new("RemoteEvent")
menu.Name = "CC_Menu"; menu.Parent = RS
local resultContinue = RS:FindFirstChild("CC_ResultContinue") or Instance.new("RemoteEvent")
resultContinue.Name = "CC_ResultContinue"; resultContinue.Parent = RS

-- Sounds (global): Gong und Publikum
local SFX = game:GetService("SoundService"):WaitForChild("CC_Sounds")
local function bell(times) task.spawn(function() for i = 1, times do SFX.Bell:Play(); task.wait(0.45) end end) end
SFX.Crowd.Looped = true; SFX.Crowd.Volume = 0.3; SFX.Crowd:Play()
local function crowd(v) game:GetService("TweenService"):Create(SFX.Crowd, TweenInfo.new(0.6), { Volume = v }):Play() end

local dummy = workspace:WaitForChild("CC_TrainingDummy")

-- ---------------- Kaefige ----------------
-- id, Modell, Walkout (nur Fight Night), erlaubte Arten
local ARENAS = {}
local function addArena(id, model, opts)
	if not model then return end
	local a = { id = id, model = model, fn = opts.fn or false, kinds = opts.kinds, busy = nil }
	table.insert(ARENAS, a)
end
do
	local arena = workspace:FindFirstChild("CC_Arena")
	if arena and not arena:GetAttribute("CC_CageCenter") then
		local c = arena:FindFirstChild("Platform_Canvas_FightSurface", true)
		if c then arena:SetAttribute("CC_CageCenter", Vector3.new(c.Position.X, c.Position.Y + c.Size.Y / 2, c.Position.Z)); arena:SetAttribute("CC_CageRadius", math.min(c.Size.X, c.Size.Z) * 0.5) end
	end
	local fn = workspace:FindFirstChild("CC_FightNight")
	if fn and fn:GetAttribute("CC_CageCenter") and workspace:GetAttribute("CC_PvpArena") ~= "arena" then
		addArena("fightnight", fn, { fn = true, kinds = { pvp = true, career = true, trainer = true } })
	end
	addArena("arena", arena, { kinds = { training = true, tutorial = true, sparring = true, career = true, trainer = true, pvp = true } })
	for i = 2, 9 do
		local m = workspace:FindFirstChild("CC_PvpArena_" .. i)
		if m and m:GetAttribute("CC_CageCenter") then addArena("pvp" .. i, m, { kinds = { pvp = true } }) end
	end
end
-- Vorlieben je Art: erster freier Kaefig der Liste
local PREFER = {
	pvp = { "fightnight", "pvp2", "pvp3", "pvp4", "pvp5", "pvp6", "pvp7", "pvp8", "pvp9", "arena" },
	career = { "fightnight", "arena" }, trainer = { "fightnight", "arena" },
	training = { "arena" }, tutorial = { "arena" }, sparring = { "arena" },
}
local function arenaById(id) for _, a in ipairs(ARENAS) do if a.id == id then return a end end end
-- Online-Arena-Wahl: "fightnight" = nur Fight Night, "cage" = Kaefige (ohne Fight Night), "any" = egal
local PICK = { fightnight = { "fightnight" }, cage = { "pvp2", "pvp3", "pvp4", "pvp5", "pvp6", "pvp7", "pvp8", "pvp9", "arena" } }   -- 8 Kaefige (CC_PvpArena_2..9) + Fight Night + Arena = 10 Plaetze fuer gleichzeitige Kaempfe
local function freeArena(kind, pick)
	local force = workspace:GetAttribute("CC_TestArena")                -- Test (Studio): bestimmten Kaefig erzwingen, z. B. "pvp2"
	if force then local a = arenaById(force); if a and not a.busy then return a end end
	for _, id in ipairs((kind == "pvp" and PICK[pick]) or PREFER[kind] or {}) do
		local a = arenaById(id)
		if a and not a.busy and a.kinds[kind] then return a end
	end
	return nil
end
local function cageOf(a)
	local c = a.model:GetAttribute("CC_CageCenter")
	return Vector3.new(c.X, 0, c.Z), c.Y, a.model:GetAttribute("CC_CageRadius") or 16
end
local function corners(m)
	local c, fy = cageOf(m.arena)
	local y = fy + 3
	return CFrame.lookAt(c + Vector3.new(0, y, 7), c + Vector3.new(0, y, -7)), CFrame.lookAt(c + Vector3.new(0, y, -7), c + Vector3.new(0, y, 7))
end

-- Lobby: im Trainings-Gym
local LOBBY_Y = 3
local function lobbyCF(i)
	local k = ((i or 1) % 7 - 3) * 2.5
	if workspace:FindFirstChild("CC_Gym") then
		return CFrame.lookAt(Vector3.new(160 + k, LOBBY_Y, 38), Vector3.new(160, LOBBY_Y, 4))
	end
	return CFrame.lookAt(Vector3.new(k, LOBBY_Y, 25), Vector3.new(k, LOBBY_Y, 0))
end

-- Shorts: Spieler tragen ihre freigeschalteten Shorts; KI-Gegner bekommen die Eckfarbe
local SHORTS = { red = Color3.new(0.564706, 0.0823529, 0.117647), blue = Color3.new(0.117647, 0.235294, 0.627451) }
local function paint(c, side)
	local s = c and c:FindFirstChild("Fighter_Shorts", true)
	if not (s and s:IsA("BasePart")) then return end
	local plr = Players:GetPlayerFromCharacter(c)
	if plr then
		local ok, look = pcall(function() return HttpService:JSONDecode(plr:GetAttribute("CC_Look") or "{}") end)
		local it = ok and look.shorts and Look.SHORTS[look.shorts]
		if it then s.Color = it.color; return end
	end
	s.Color = SHORTS[side]
end

-- ---------------- Kaempfe (aktiv) ----------------
local matches = {}          -- [id] = m
local kiBusy = false        -- der eine KI-Gegner ist belegt
local nextId = 0
local function activeOf(p)
	for _, m in pairs(matches) do if m.red == p or m.blue == p then return m end end
	return nil
end
local function isFighting(p) return activeOf(p) ~= nil end

-- Warteschlange (global, fuer alle Menues sichtbar ueber QueuePvp)
local queue = {}
local function inQueue(p) for i, e in ipairs(queue) do if e[1] == p then return i end end end
local function updateQueueAttrs()
	local n = 0
	for _, e in ipairs(queue) do if e[2] == "pvp" then n += 1 end end
	idle:SetAttribute("QueuePvp", n)
	for _, m in pairs(matches) do m.state:SetAttribute("QueuePvp", n) end
end
resultContinue.OnServerEvent:Connect(function(p)
	local m = activeOf(p)
	if m and m.state:GetAttribute("State") == "over" then p:SetAttribute("CC_ResultReady", true) end
end)

local menuServer = SS:FindFirstChild("CC_MenuServer") or Instance.new("BindableEvent")
menuServer.Name = "CC_MenuServer"; menuServer.Parent = SS
local LEVELS = { passiv = true, anfaenger = true, fortgeschritten = true }
local function careerReady(p, id)
	return type(id) == "string" and OPP.byId[id] and OPP.isUnlocked(id, p:GetAttribute("CC_CareerBeaten"))
end
local function trainerReady(p, id)
	if type(id) ~= "string" or not SIGPROG.list[id] then return false end
	local ok, data = pcall(function() return HttpService:JSONDecode(p:GetAttribute("CC_SigProgress") or "{}") end)
	return ok and SIGPROG.ready(id, data)
end
local function onMenu(p, what, level, fromServer)
	if type(what) ~= "string" then return end
	if what == "training" then
		if type(level) == "string" and LEVELS[level] then p:SetAttribute("CC_DummyLevel", level)
		elseif not p:GetAttribute("CC_DummyLevel") then p:SetAttribute("CC_DummyLevel", "anfaenger") end
	elseif what == "career" then
		if not careerReady(p, level) then p:SetAttribute("CC_Notice", "This career opponent is still locked.|" .. tostring(workspace:GetServerTimeNow())); return end
		p:SetAttribute("CC_CareerSelected", level)
	elseif what == "trainer" then
		if not fromServer or not trainerReady(p, level) then p:SetAttribute("CC_Notice", "Finish all coach quests first.|" .. tostring(workspace:GetServerTimeNow())); return end
		p:SetAttribute("CC_TrainerSelected", level)
	end
	local i = inQueue(p)
	if what == "cancel" then
		if i then table.remove(queue, i) end
		p:SetAttribute("CC_Queue", nil)
	elseif (what == "training" or what == "pvp" or what == "career" or (what == "trainer" and fromServer) or ((what == "tutorial" or what == "sparring") and fromServer)) and not isFighting(p) then
		if i then table.remove(queue, i) end
		local arg = (what == "career" or what == "trainer") and level or nil
		if what == "pvp" then arg = (level == "fightnight" or level == "cage") and level or "any" end   -- Arena-Wahl online
		table.insert(queue, { p, what, arg })
		p:SetAttribute("CC_Queue", what)
	end
	updateQueueAttrs()
end
menu.OnServerEvent:Connect(function(p, what, level) onMenu(p, what, level, false) end)
menuServer.Event:Connect(function(p, what, level) onMenu(p, what, level, true) end)
Players.PlayerRemoving:Connect(function(p)
	local i = inQueue(p); if i then table.remove(queue, i) end
	updateQueueAttrs()
end)

local lobbyCount = 0
local function toLobby(p)
	local c = p.Character
	p:SetAttribute("CC_MatchId", nil)
	if c and c:FindFirstChild("HumanoidRootPart") then
		lobbyCount += 1
		c:SetAttribute("CC_MatchId", nil)
		reset:Invoke(c, lobbyCF(lobbyCount), nil)
		c:SetAttribute("CC_Opponent", nil); c:SetAttribute("CC_Frozen", false)
		paint(c, "red")
	end
end
local function hookPlayer(p)
	p.CharacterAdded:Connect(function(c)
		c:WaitForChild("HumanoidRootPart"); task.wait(0.5)
		local m = activeOf(p)
		if m then c:SetAttribute("CC_MatchId", m.id) else toLobby(p) end
	end)
	if p.Character then task.spawn(function() task.wait(0.5); if not isFighting(p) then toLobby(p) end end) end
end
Players.PlayerAdded:Connect(hookPlayer)
for _, p in ipairs(Players:GetPlayers()) do hookPlayer(p) end

local DUMMY_PARK = CFrame.lookAt(Vector3.new(26, LOBBY_Y, -26), Vector3.new(0, LOBBY_Y, 0))
local function parkDummy()
	dummy:SetAttribute("CC_InMatch", false); dummy:SetAttribute("CC_Opponent", nil); dummy:SetAttribute("CC_MatchId", nil)
	dummy:SetAttribute("CC_CareerId", nil); dummy:SetAttribute("CC_CareerName", nil); dummy:SetAttribute("CC_TrainerBoss", nil)
	for _, s in ipairs({ "Power", "Cardio", "Wrestling", "Grappling" }) do dummy:SetAttribute("CC_" .. s, nil) end
	Look.apply(dummy, DUMMY_LOBBY_LOOK, SS:FindFirstChild("CC_Custom"))
	reset:Invoke(dummy, DUMMY_PARK, nil)
end

-- ---------------- Kampf ----------------
local function chars(m)
	local r = m.red.Character
	local b = m.blue and m.blue.Character or (not m.blue and dummy) or nil
	return r, b
end
local function freeze(m, on)
	m.frozen = on
	for _, c in ipairs({ chars(m) }) do if c then c:SetAttribute("CC_Frozen", on) end end
end
RunService.Heartbeat:Connect(function()
	for _, m in pairs(matches) do
		for _, c in ipairs({ chars(m) }) do
			local h = c and c:FindFirstChildOfClass("Humanoid")
			if h then
				if m.frozen then h.WalkSpeed = 0 elseif h.WalkSpeed == 0 and not c:GetAttribute("CC_KO") and not c:GetAttribute("CC_Wrestle") then h.WalkSpeed = c:GetAttribute("CC_MobilitySpeed") or 8 end
			end
		end
	end
end)
local function damage(c) return c and (c:GetAttribute("CC_DamageDealt") or 0) or 0 end
local function clearDamage(m) for _, c in ipairs({ chars(m) }) do if c then c:SetAttribute("CC_DamageDealt", 0) end end end
local JUDGE_BIAS = { -1.35, 0, 1.35 }
local function scoreRound(m, cards, totalsRed, totalsBlue, round, r, b, kdRedStart, kdBlueStart)
	local rd, bd = damage(r), damage(b)
	local rkd = math.max(0, (r:GetAttribute("CC_Knockdowns") or 0) - kdRedStart)
	local bkd = math.max(0, (b:GetAttribute("CC_Knockdowns") or 0) - kdBlueStart)
	local margin = rd - bd + (rkd - bkd) * 14
	local swing = math.max(1, math.min(4, (rd + bd) * 0.03))
	local card = { round = round, red = {}, blue = {}, damageRed = math.floor(rd + 0.5), damageBlue = math.floor(bd + 0.5), knockdownsRed = rkd, knockdownsBlue = bkd }
	for j, bias in ipairs(JUDGE_BIAS) do
		local adjusted = margin + bias * swing
		local sr, sb
		if math.abs(adjusted) < 1.5 then sr, sb = 10, 10
		elseif adjusted > 0 then sr, sb = 10, (adjusted >= 24 or rkd > bkd) and 8 or 9
		else sr, sb = (adjusted <= -24 or bkd > rkd) and 8 or 9, 10 end
		card.red[j], card.blue[j] = sr, sb
		totalsRed[j] += sr; totalsBlue[j] += sb
	end
	table.insert(cards, card)
	m.set("JudgeCards", HttpService:JSONEncode(cards))
	m.set("JudgeRed", totalsRed[1] + totalsRed[2] + totalsRed[3])
	m.set("JudgeBlue", totalsBlue[1] + totalsBlue[2] + totalsBlue[3])
end
local function decisionWinner(totalsRed, totalsBlue)
	local redVotes, blueVotes = 0, 0
	for j = 1, 3 do
		if totalsRed[j] > totalsBlue[j] then redVotes += 1 elseif totalsBlue[j] > totalsRed[j] then blueVotes += 1 end
	end
	if redVotes >= 2 then return "red" end
	if blueVotes >= 2 then return "blue" end
	return "draw"
end
local function doctorWinner(m)
	local r, b = chars(m)
	local function unsafe(c)
		if not c then return false end
		return (c:GetAttribute("CC_HeadDamage") or 0) >= 55
			or (c:GetAttribute("CC_Injury_Nose") or 0) >= 90
			or (c:GetAttribute("CC_Injury_Head") or 0) >= 90
			or (c:GetAttribute("CC_Injury_Ribs") or 0) >= 95
			or (c:GetAttribute("CC_DoctorRisk") == true and c.Humanoid.Health <= 25)
	end
	local ru, bu = unsafe(r), unsafe(b)
	if ru == bu then return nil end
	return ru and "blue" or "red"
end
local function tagMatch(m)                              -- Zuordnung Spieler/Charaktere -> Kampf (Anzeige, Fokus, Signaturen)
	for _, p in ipairs({ m.red, m.blue }) do if p and p.Parent then p:SetAttribute("CC_MatchId", m.id) end end
	for _, c in ipairs({ chars(m) }) do if c then c:SetAttribute("CC_MatchId", m.id) end end
end
-- Rundenpause: beide in ihre Ecke (Hocker + Eck-Trainer: CC_Corner.server), Blick zur Kaefigmitte
local function placeCorners(m, heal)
	local r, b = chars(m)
	local c, fy, rad = cageOf(m.arena)
	local y, d = fy + 3, math.max(8, rad - 4.5)
	local cr = CFrame.lookAt(c + Vector3.new(0, y, d), c + Vector3.new(0, y, 0))
	local cb = CFrame.lookAt(c + Vector3.new(0, y, -d), c + Vector3.new(0, y, 0))
	if r then reset:Invoke(r, cr, heal and math.min(100, r.Humanoid.Health + heal) or nil) end
	if b then reset:Invoke(b, cb, heal and math.min(100, b.Humanoid.Health + heal) or nil) end
	paint(r, "red"); paint(b, "blue")
	tagMatch(m)
end
local function placeBoth(m, heal)
	local r, b = chars(m)
	local cr, cb = corners(m)
	if r then reset:Invoke(r, cr, heal and math.min(100, r.Humanoid.Health + heal) or nil) end
	if b then reset:Invoke(b, cb, heal and math.min(100, b.Humanoid.Health + heal) or nil) end
	if r and b then r:SetAttribute("CC_Opponent", b.Name); b:SetAttribute("CC_Opponent", r.Name) end
	paint(r, "red"); paint(b, "blue")
	tagMatch(m)
end
local function present(m)
	local r, b = chars(m)
	return r ~= nil and r.Parent ~= nil and m.red.Parent ~= nil, b ~= nil and b.Parent ~= nil and (not m.blue or m.blue.Parent ~= nil)
end
local function profile(p, kind, a, b, c)
	local ev = SS:FindFirstChild("CC_ProfileEvent")
	if ev and p and p.Parent then ev:Fire(p, kind, a, b, c) end
end
local function koWinner(m)
	local r, b = chars(m)
	if r and r:GetAttribute("CC_KO") then return "blue" end
	if b and b:GetAttribute("CC_KO") then return "red" end
	return nil
end
local function streamTo(m, pos)
	for _, pl in ipairs({ m.red, m.blue }) do
		if pl and pl.Parent then pcall(function() pl:RequestStreamAroundAsync(pos, 10) end) end
	end
end

-- neuen Kampf anlegen (Zustands-Ordner, Kaefig belegen)
local function newMatch(e, arena)
	nextId += 1
	local m = e
	m.id = "M" .. nextId
	m.arena = arena
	arena.busy = m.id
	local st = Instance.new("Folder"); st.Name = m.id; st.Parent = matchRoot
	m.state = st
	function m.set(k, v) st:SetAttribute(k, v) end
	local c, fy, r = cageOf(arena)
	m.set("MatchId", m.id); m.set("Arena", arena.id); m.set("CageCenter", Vector3.new(c.X, fy, c.Z)); m.set("CageRadius", r)
	m.set("State", "idle"); m.set("Mode", m.mode); m.set("QueuePvp", idle:GetAttribute("QueuePvp") or 0)
	st:GetAttributeChangedSignal("CrowdBoost"):Connect(function() crowd(0.8); task.delay(3, function() crowd(0.3) end) end)
	if not m.blue then kiBusy = true end
	matches[m.id] = m
	tagMatch(m)
	return m
end
local function endMatch(m)
	matches[m.id] = nil
	if m.arena and m.arena.busy == m.id then m.arena.busy = nil end
	if not m.blue then kiBusy = false end
	for _, p in ipairs({ m.red, m.blue }) do if p and p.Parent then toLobby(p) end end
	if not m.blue then parkDummy() end
	task.delay(2, function() if m.state then m.state:Destroy() end end)   -- Clients haben dann auf "idle" umgeschaltet
end

local runMatch
local function runTutorial(m)
	m.set("Mode", "tutorial"); m.set("RedName", m.red.Name); m.set("BlueName", "Training Partner"); m.set("Winner", ""); m.set("WinnerName", "")
	dummy:SetAttribute("CC_Difficulty", "passiv"); dummy:SetAttribute("CC_Passive", true); dummy:SetAttribute("CC_InMatch", true)
	freeze(m, false)
	placeBoth(m)
	clearDamage(m)
	m.set("State", "tutorial"); m.set("Banner", ""); m.set("BannerSub", "")
	print("[CC] Tutorial startet: " .. m.red.Name .. " (" .. m.id .. ")")
	local run = SS:FindFirstChild("CC_TutorialRun")
	local ok, nextStep = pcall(function() return run and run:Invoke(m.red) end)
	if not ok then warn("[CC] Tutorial-Fehler: " .. tostring(nextStep)) end
	dummy:SetAttribute("CC_Tutor", nil); dummy:SetAttribute("CC_Passive", nil)
	if ok and nextStep == "sparring" and m.red.Parent and m.red.Character then
		m.mode = "sparring"; m.set("Mode", "sparring")
		return runMatch(m)                                          -- gleicher Kaefig, gleicher Zustand
	end
end

function runMatch(m)
	if m.mode == "tutorial" then return runTutorial(m) end
	-- Kampfclips vorladen (keine T-Pose beim ersten Abspielen)
	local preloadDeadline = os.clock() + 8
	while os.clock() < preloadDeadline do
		local pending = false
		for _, p in ipairs({ m.red, m.blue }) do
			if p and p.Parent and p:GetAttribute("CC_AnimationsReady") ~= true then pending = true; break end
		end
		if not pending then break end
		task.wait(0.1)
	end
	for _, p in ipairs({ m.red, m.blue }) do if p then p:SetAttribute("CC_ResultReady", nil); p:SetAttribute("CC_LastFight", nil) end end
	local career = m.mode == "career" and OPP.byId[m.opponentId] or nil
	local trainerDef = m.mode == "trainer" and SIGPROG.list[m.opponentId] or nil
	local trainer = trainerDef and trainerDef.boss or nil
	local blueLabel = career and career.name or trainer and trainer.name or (m.blue and m.blue.Name or "Training Partner")
	local rounds = career and career.rounds or trainer and trainer.rounds or (m.mode == "sparring" and 1 or ROUNDS)
	local set = m.set
	set("Rounds", rounds)
	set("Mode", m.mode); set("OpponentId", career and career.id or trainerDef and m.opponentId or ""); set("RedName", m.red.Name); set("BlueName", blueLabel); set("WinnerName", "")
	set("Winner", ""); set("Stoppage", ""); set("ScoreRed", 0); set("ScoreBlue", 0); set("JudgeCards", "[]"); set("JudgeRed", 0); set("JudgeBlue", 0)
	if not m.blue then
		if m.mode == "training" or m.mode == "sparring" then
			local lv = m.mode == "sparring" and "anfaenger" or (m.red:GetAttribute("CC_DummyLevel") or "anfaenger")
			dummy:SetAttribute("CC_Difficulty", lv); dummy:SetAttribute("CC_Passive", lv == "passiv" or nil)
			local styleByLevel = { passiv = "Boxer", anfaenger = "Boxer", fortgeschritten = "Kickboxer" }
			dummy:SetAttribute("CC_AIStyle", workspace:GetAttribute("CC_TestAIStyle") or styleByLevel[lv] or "Boxer")
			dummy:SetAttribute("CC_InMatch", true)
		elseif career then
			dummy:SetAttribute("CC_Difficulty", career.difficulty); dummy:SetAttribute("CC_Passive", nil); dummy:SetAttribute("CC_InMatch", true)
			dummy:SetAttribute("CC_AIStyle", workspace:GetAttribute("CC_TestAIStyle") or career.aiStyle or "Boxer")
			dummy:SetAttribute("CC_CareerId", career.id); dummy:SetAttribute("CC_CareerName", career.name)
			for s, v in pairs(career.stats) do dummy:SetAttribute("CC_" .. s, v) end
			Look.apply(dummy, career.look, SS:FindFirstChild("CC_Custom"))
		elseif trainer then
			dummy:SetAttribute("CC_Difficulty", trainer.difficulty); dummy:SetAttribute("CC_Passive", nil); dummy:SetAttribute("CC_InMatch", true)
			dummy:SetAttribute("CC_AIStyle", workspace:GetAttribute("CC_TestAIStyle") or trainer.aiStyle or "Boxer")
			dummy:SetAttribute("CC_TrainerBoss", m.opponentId); dummy:SetAttribute("CC_CareerName", trainer.name)
			for s, v in pairs(trainer.stats) do dummy:SetAttribute("CC_" .. s, v) end
			Look.apply(dummy, trainer.look, SS:FindFirstChild("CC_Custom"))
		else
			dummy:SetAttribute("CC_AIStyle", workspace:GetAttribute("CC_TestAIStyle") or "Grappler")
			dummy:SetAttribute("CC_InMatch", true)
		end
	end
	do
		local r0, b0 = chars(m)
		for _, c in ipairs({ r0, b0 }) do
			if c then
				c:SetAttribute("CC_ResetKnockdowns", true)
				for _, key in ipairs({ "CC_DamageDealt", "CC_StrikesLanded", "CC_HeadHits", "CC_BodyHits", "CC_BlockedHits", "CC_Blocks", "CC_CounterHits", "CC_JabHits", "CC_KickHits", "CC_Takedowns", "CC_GroundHits", "CC_SubmissionWins", "CC_HeadDamage", "CC_Knockdowns" }) do c:SetAttribute(key, 0) end
				c:SetAttribute("CC_DoctorRisk", nil); c:SetAttribute("CC_Stoppage", nil)
			end
		end
	end
	print(("[CC] Kampf %s startet (%s, Kaefig %s): %s gegen %s"):format(m.id, m.mode, m.arena.id, m.red.Name, blueLabel))
	set("Finisher", nil)
	do local r0, b0 = chars(m); for _, c in ipairs({ r0, b0 }) do if c then c:SetAttribute("CC_FocusReset", os.clock()) end end end
	-- Kaefig vorladen (weit entfernte Kaefige: sonst faellt der Spieler beim Teleport durch)
	do local c, fy = cageOf(m.arena); streamTo(m, Vector3.new(c.X, fy, c.Z)) end
	-- Fight Night: Walkout
	if m.arena.fn then
		local fn = m.arena.model
		local spots = fn:FindFirstChild("FN_Spots")
		local startP, door = spots and spots:FindFirstChild("Fighter_Walkout_Main"), spots and spots:FindFirstChild("Cage_Door")
		if startP and door then
			set("State", "walkout")
			if trainer then set("Banner", "COACH FINAL FIGHT"); set("BannerSub", m.red.Name .. "  vs.  " .. blueLabel)
			elseif career then set("Banner", "CAREER"); set("BannerSub", m.red.Name .. "  vs.  " .. blueLabel)
			else set("Banner", "FIGHT NIGHT"); set("BannerSub", "Walkout") end
			local r, b = chars(m)
			streamTo(m, startP.Position); streamTo(m, door.Position)
			local list = {}
			for i, c in ipairs({ r, b }) do
				local h, root = c and c:FindFirstChildOfClass("Humanoid"), c and c:FindFirstChild("HumanoidRootPart")
				if h and root then
					local side = (i == 1) and -2.5 or 2.5
					local mid = door.Position + (startP.Position - door.Position) * 0.55
					local from = Vector3.new(mid.X, startP.Position.Y, mid.Z) + Vector3.new(side, 0, (i - 1) * 4)
					local rpar = RaycastParams.new(); rpar.FilterType = Enum.RaycastFilterType.Include; rpar.FilterDescendantsInstances = { fn:FindFirstChild("FN_Collision") }
					local hit = workspace:Raycast(from + Vector3.new(0, 10, 0), Vector3.new(0, -30, 0), rpar)
					from = Vector3.new(from.X, (hit and hit.Position.Y or from.Y) + 3.1, from.Z)
					reset:Invoke(c, CFrame.lookAt(from, Vector3.new(door.Position.X + side, from.Y, door.Position.Z)), nil)
					c:SetAttribute("CC_Opponent", nil); c:SetAttribute("CC_Frozen", false)
					h.WalkSpeed = 16
					table.insert(list, { c = c, h = h, root = root, goal = Vector3.new(door.Position.X + side * 0.6, from.Y, door.Position.Z + 6) })
				end
			end
			paint(r, "red"); paint(b, "blue")
			for _, e in ipairs(list) do
				if e.c == dummy and not (trainer or career) then e.root.CFrame = CFrame.lookAt(e.goal, e.goal - Vector3.new(0, 0, 1)) else e.h:MoveTo(e.goal) end
			end
			local t0 = os.clock()
			while os.clock() - t0 < 10 do
				local done = true
				for _, e in ipairs(list) do
					if e.c.Parent and ((e.root.Position - e.goal) * Vector3.new(1, 0, 1)).Magnitude > 3 then done = false; e.h:MoveTo(e.goal) end
				end
				if done then break end
				task.wait(0.25)
			end
		end
	end
	local totalRed, totalBlue, winner, method = 0, 0, nil, nil
	local scorecards, judgeRed, judgeBlue = {}, { 0, 0, 0 }, { 0, 0, 0 }
	for round = 1, rounds do
		freeze(m, true)
		local corner = round > 1 and (workspace:GetAttribute("CC_BreakTime") or BREAK_TIME) >= 6
		if corner then placeCorners(m, BREAK_HEAL); set("Corner", true) else placeBoth(m, round > 1 and BREAK_HEAL or nil) end
		clearDamage(m)
		local roundRed, roundBlue = chars(m)
		local kdRedStart = roundRed and (roundRed:GetAttribute("CC_Knockdowns") or 0) or 0
		local kdBlueStart = roundBlue and (roundBlue:GetAttribute("CC_Knockdowns") or 0) or 0
		set("Round", round)
		set("State", round == 1 and "intro" or "break")
		local wait = round == 1 and (workspace:GetAttribute("CC_IntroTime") or INTRO_TIME) or (workspace:GetAttribute("CC_BreakTime") or BREAK_TIME)
		for t = wait, 1, -1 do
			set("TimeLeft", t)
			if corner and t == 3 then set("Corner", false); placeBoth(m, nil) end   -- aufstehen, zurueck in die Startpositionen
			set("Banner", "ROUND " .. round); set("BannerSub", t <= 3 and tostring(t) or (round == 1 and "Fight begins" or "Break"))
			task.wait(1)
		end
		set("Banner", "FIGHT!"); set("BannerSub", "")
		local roundTime = workspace:GetAttribute("CC_RoundTime") or 120
		set("State", "fight"); set("TimeLeft", roundTime)
		bell(1)
		freeze(m, false)
		task.delay(1, function() if m.state.Parent and m.state:GetAttribute("Banner") == "FIGHT!" then set("Banner", ""); set("BannerSub", "") end end)
		local t0 = os.clock()
		-- Testschalter: nur Studio, fuenf Sekunden nach Beginn der ersten Runde.
		local testDoctorAt = RunService:IsStudio() and round == 1 and workspace:GetAttribute("CC_TestDoctor") == true and (t0 + 5) or nil
		while os.clock() - t0 < roundTime do
			task.wait(0.1)
			set("TimeLeft", math.max(0, math.ceil(roundTime - (os.clock() - t0))))
			local rOk, bOk = present(m)
			if not (rOk and bOk) then winner = rOk and "red" or "blue"; method = "Forfeit"; break end
			local r, b = chars(m)
			set("ScoreRed", totalRed + damage(r)); set("ScoreBlue", totalBlue + damage(b))
			if testDoctorAt and workspace:GetAttribute("CC_TestDoctor") == true and os.clock() >= testDoctorAt then
				winner, method = "red", "Doctor stoppage"
				set("Stoppage", method); set("Banner", "DOCTOR STOPPAGE"); set("BannerSub", "Fight is being stopped")
				break
			end
			winner = koWinner(m)
			if winner then
				local loser = winner == "red" and b or r
				local stop = loser and loser:GetAttribute("CC_Stoppage")
				method = (loser and loser:GetAttribute("CC_LastReact") == "submission") and "Submission"
					or stop == "LEG_TKO" and "T.K.O. · Leg injury"
					or stop == "ARM_TKO" and "T.K.O. · Arm injury"
					or stop == "BODY_TKO" and "T.K.O. · Rib injury"
					or stop == "GROUND_TKO" and "T.K.O. · Ground-and-Pound"
					or stop == "TKO" and "T.K.O." or "K.O."
				set("Stoppage", method)               -- Ringrichter (CC_Referee) greift sofort ein
				break
			end
		end
		local r, b = chars(m)
		totalRed += damage(r); totalBlue += damage(b)
		set("ScoreRed", totalRed); set("ScoreBlue", totalBlue)
		if r and b then scoreRound(m, scorecards, judgeRed, judgeBlue, round, r, b, kdRedStart, kdBlueStart) end
		for _, p in ipairs({ m.red, m.blue }) do profile(p, "train", "Cardio", 2) end
		if not winner then
			local dw = doctorWinner(m)
			if dw then winner, method = dw, "Doctor stoppage"; set("Stoppage", method); set("Banner", "DOCTOR STOPPAGE"); set("BannerSub", "Fight is being stopped") end
		end
		if winner then break end
		freeze(m, true)
		bell(3)
		set("Banner", "END OF ROUND " .. round); set("BannerSub", string.format("Points  %d : %d", totalRed, totalBlue))
		task.wait(2)
	end
	if not winner then
		method = "Decision"
		winner = decisionWinner(judgeRed, judgeBlue)
	end
	if method == "K.O." or method == "Submission" then task.wait(1.5) end
	local fin = m.state:GetAttribute("Finisher")
	if fin and method == "K.O." then
		local wn = winner == "red" and m.red.Name or winner == "blue" and blueLabel or ""
		set("Winner", winner); set("WinnerName", wn)
		set("State", "finisher"); set("Banner", ""); set("BannerSub", "")
		task.wait(require(RS:WaitForChild("CC_Signatures")).FINISHER.total)
	end
	freeze(m, true)
	local wname = winner == "red" and m.red.Name or winner == "blue" and blueLabel or ""
	set("State", "over"); set("Winner", winner); set("WinnerName", wname)
	bell(3); crowd(0.8); task.delay(4, function() crowd(0.3) end)
	set("Banner", winner == "draw" and "DRAW" or (wname .. " WINS"))
	set("BannerSub", method .. string.format("   ·   %d : %d", totalRed, totalBlue))
	print(("[CC] Kampf %s vorbei: %s (%s) %d:%d"):format(m.id, winner, method, totalRed, totalBlue))
	for side, p in pairs({ red = m.red, blue = m.blue or false }) do
		if p then
			local res = winner == "draw" and "draw" or (winner == side and "win" or "loss")
			local xp = nil
			profile(p, "goal", "fights", 1)
			local ch = p.Character
			if side == "red" or m.mode == "pvp" then
				profile(p, "sig_fight_result", { body = ch and ch:GetAttribute("CC_BodyHits") or 0, counters = ch and ch:GetAttribute("CC_CounterHits") or 0, jabs = ch and ch:GetAttribute("CC_JabHits") or 0, blocks = ch and ch:GetAttribute("CC_Blocks") or 0, kicks = ch and ch:GetAttribute("CC_KickHits") or 0, takedowns = ch and ch:GetAttribute("CC_Takedowns") or 0, groundHits = ch and ch:GetAttribute("CC_GroundHits") or 0, subs = (res == "win" and method == "Submission") and 1 or 0, career = m.mode == "career", result = res })
			end
			if m.mode == "career" and side == "red" and career then
				xp = res == "win" and (career.rewardXP + ((method == "K.O." or method == "Submission") and 20 or 0)) or (res == "draw" and 35 or 20)
				profile(p, "career_result", career.id, res, method)
				profile(p, "goal", "career", 1)
			elseif m.mode == "trainer" and side == "red" and trainerDef then
				xp = res == "win" and trainer.rewardXP or 25
				profile(p, "sig_boss_result", m.opponentId, res, method)
				profile(p, "xp", xp)
			elseif m.mode == "pvp" then
				xp = res == "win" and (60 + ((method == "K.O." or method == "Submission") and 20 or 0)) or (res == "draw" and 35 or 25)
				profile(p, "result", res, method)
			else
				xp = res == "win" and 30 or 15; profile(p, "xp", xp)
			end
			p:SetAttribute("CC_LastFight", HttpService:JSONEncode({ mode = m.mode, opponentId = career and career.id or trainerDef and m.opponentId or nil, opponentName = career and career.name or trainer and trainer.name or (m.mode == "pvp" and (side == "red" and (m.blue and m.blue.Name) or m.red.Name)) or nil, result = res, method = method, xp = xp, scorecards = scorecards, judgeRed = judgeRed, judgeBlue = judgeBlue }))
		end
	end
	for t = OVER_TIME, 1, -1 do
		set("TimeLeft", t)
		local ready = m.red:GetAttribute("CC_ResultReady") == true and (not m.blue or m.blue:GetAttribute("CC_ResultReady") == true)
		if ready then break end
		task.wait(1)
	end
	for _, p in ipairs({ m.red, m.blue }) do if p then p:SetAttribute("CC_ResultReady", nil) end end
	freeze(m, false)
end

-- Kampf starten (eigener Thread), danach Kaefig/KI-Gegner wieder freigeben
local function launch(m)
	task.spawn(function()
		local ok, err = pcall(runMatch, m)
		if not ok then warn("[CC] Kampf-Fehler (" .. tostring(m.id) .. "): " .. tostring(err)) end
		endMatch(m)
	end)
end

-- Warteschlange abarbeiten: Online-Paare und KI-Kaempfe, solange Kaefige frei sind
local function schedule()
	for i = #queue, 1, -1 do if not queue[i][1].Parent or not queue[i][1].Character then table.remove(queue, i) end end
	-- Online: Paare bilden
	local pvp = {}
	for i, e in ipairs(queue) do if e[2] == "pvp" then table.insert(pvp, i) end end
	-- Paare nur mit passender Arena-Wahl ("any" passt zu allem); gemeinsame Wahl bestimmt den Kaefig
	local paired = true
	while paired do
		paired = false
		for x = 1, #pvp do
			for y = x + 1, #pvp do
				local ea, eb = queue[pvp[x]], queue[pvp[y]]
				local pa, pb = ea[3] or "any", eb[3] or "any"
				if pa == pb or pa == "any" or pb == "any" then
					local pick = (pa ~= "any") and pa or pb
					local arena = freeArena("pvp", pick)
					if arena then
						local a, b = ea[1], eb[1]
						table.remove(queue, pvp[y]); table.remove(queue, pvp[x])
						a:SetAttribute("CC_Queue", nil); b:SetAttribute("CC_Queue", nil)
						launch(newMatch({ red = a, blue = b, mode = "pvp" }, arena))
						paired = true
						break
					end
				end
			end
			if paired then break end
		end
		pvp = {}; for i, e in ipairs(queue) do if e[2] == "pvp" then table.insert(pvp, i) end end
	end
	if #pvp == 1 and workspace:GetAttribute("CC_TestPvpDummy") and not kiBusy then          -- Test (Studio, 1 Spieler)
		local arena = freeArena("pvp", queue[pvp[1]][3])
		if arena then
			local a = queue[pvp[1]][1]
			table.remove(queue, pvp[1]); a:SetAttribute("CC_Queue", nil)
			launch(newMatch({ red = a, mode = "pvp" }, arena))
		end
	end
	-- KI-Kaempfe: einer gleichzeitig (ein KI-Gegner)
	if not kiBusy then
		for i, e in ipairs(queue) do
			local kind = e[2]
			if kind == "training" or kind == "tutorial" or kind == "sparring" or kind == "career" or kind == "trainer" then
				local arena = freeArena(kind)
				if arena then
					table.remove(queue, i); e[1]:SetAttribute("CC_Queue", nil)
					launch(newMatch({ red = e[1], mode = kind, opponentId = e[3] }, arena))
					break
				end
			end
		end
	end
	updateQueueAttrs()
end

-- Kaefig-Grenze: waehrend eines Kampfs bleiben beide Kaempfer im Kaefig (Wrestling-Animationen koennen den Root
-- seitlich verschieben). Wer den Rand ueberschreitet, wird auf die Innenseite zurueckgesetzt, Blickrichtung bleibt.
local CAGE_MARGIN = 1.5
task.spawn(function()
	while true do
		task.wait(0.1)
		for _, m in pairs(matches) do
			if m.arena and m.state:GetAttribute("State") == "fight" then
				local c, fy, r = cageOf(m.arena)
				local limit = r - CAGE_MARGIN
				for _, ch in ipairs({ chars(m) }) do
					local root = ch and ch:FindFirstChild("HumanoidRootPart")
					if root and root.Parent then
						local flat = Vector3.new(root.Position.X - c.X, 0, root.Position.Z - c.Z)
						if flat.Magnitude > limit then
							local dir = flat.Unit
							local np = Vector3.new(c.X, fy + 3, c.Z) + dir * limit
							root.AssemblyLinearVelocity = Vector3.zero
							root.CFrame = CFrame.new(np) * (root.CFrame - root.CFrame.Position)
							warn(("[CC] Kaefig-Grenze (%s): %s zurueck in den Kaefig"):format(m.id, ch.Name))
						end
					end
				end
			end
		end
	end
end)

-- Fallschutz: im Kampf zurueck in die eigene Ecke, sonst ins Gym
local FALL_Y = -25
local lastFallCheck = 0
RunService.Heartbeat:Connect(function()
	if os.clock() - lastFallCheck < 0.25 then return end
	lastFallCheck = os.clock()
	for _, p in ipairs(Players:GetPlayers()) do
		local c = p.Character
		local r = c and c:FindFirstChild("HumanoidRootPart")
		local h = c and c:FindFirstChildOfClass("Humanoid")
		if r and h and r.Position.Y < FALL_Y then
			r.AssemblyLinearVelocity = Vector3.zero
			local m = activeOf(p)
			if m then
				local cr, cb = corners(m)
				reset:Invoke(c, (m.red == p) and cr or cb, h.Health)
				warn(("[CC] Fallschutz: %s im Kampf zurueck in die Ecke"):format(p.Name))
			else
				toLobby(p)
				warn(("[CC] Fallschutz: %s zurueck ins Gym"):format(p.Name))
			end
		end
	end
	local dr = dummy:FindFirstChild("HumanoidRootPart")
	if dr and dr.Position.Y < FALL_Y then
		dr.AssemblyLinearVelocity = Vector3.zero
		local km
		for _, m in pairs(matches) do if not m.blue then km = m end end
		if km then local _, cb = corners(km); reset:Invoke(dummy, cb, dummy.Humanoid.Health) else parkDummy() end
	end
end)

idle:SetAttribute("State", "idle"); idle:SetAttribute("Mode", ""); idle:SetAttribute("QueuePvp", 0)
parkDummy()
local ids = {}; for _, a in ipairs(ARENAS) do table.insert(ids, a.id) end
print("[CC] Kampf-Verwaltung: Kaefige " .. table.concat(ids, ", "))
while true do
	local ok, err = pcall(schedule)
	if not ok then warn("[CC] Warteschlange: " .. tostring(err)) end
	task.wait(0.5)
end
