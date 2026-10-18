-- ServerScriptService.CC_Match
-- Kampf-Ablauf mit Menue: eine Arena, ein Kampf gleichzeitig.
--   Training: Spieler (Rot) gegen den Trainingsgegner (Blau).  Gegen Spieler: die ersten zwei aus der Warteschlange (Rot/Blau).
--   Wer nicht kaempft, steht in der Lobby vor dem Kaefig (Menue sichtbar). Gegen-Spieler-Kaempfe haben Vorrang.
-- Runden: 3 x 2:00, 10 s Pause, Sieg durch K.o., Submission oder nach Punkten (verursachter Schaden); Aufgabe, wenn ein Spieler geht.
-- Menue -> Server: ReplicatedStorage.CC_Menu (RemoteEvent) mit "training" | "pvp" | "career" | "cancel".
-- Zustand fuer HUD/Menue als Attribute an ReplicatedStorage.CC_MatchState:
--   State ("idle" | "intro" | "fight" | "break" | "over"), Mode ("" | "training" | "pvp"), Round, TimeLeft (s),
--   Banner, BannerSub, ScoreRed, ScoreBlue, Winner ("red" | "blue" | "draw" | ""), RedName, BlueName, WinnerName, QueuePvp (Anzahl)
-- Am Spieler: Attribut CC_Queue ("training" | "pvp" | nil). Am Charakter: CC_Opponent (Modellname des Gegners) waehrend des Kampfs.
-- Test: workspace-Attribut CC_RoundTime (Sekunden) ueberschreibt die Rundenzeit.
-- Einstieg (CC_Tutorial, nur serverseitig ueber CC_MenuServer): "tutorial" = Grundlagen im Kaefig gegen den passiven Gegner, ohne Uhr
--   (Ablauf steuert ServerStorage.CC_TutorialRun, Rueckgabe "sparring" -> direkt im Kaefig weiter); "sparring" = erster Kampf,
--   1 Runde gegen den Anfaenger-Gegner, Belohnung wie Training. Nach jedem Kampf: Attribut CC_LastFight am Spieler (JSON: mode, result, method, xp).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local RS = game.ReplicatedStorage
local SS = game.ServerStorage
local HttpService = game:GetService("HttpService")
local reset = SS:WaitForChild("CC_ResetFighter")
local OPP = require(RS:WaitForChild("CC_Opponents"))
local SIGPROG = require(RS:WaitForChild("CC_SignatureProgression"))
local Look = require(RS:WaitForChild("CC_LookShared"))
local DUMMY_LOBBY_LOOK = { hair = "Hair_QuiffV03", beard = "none", face = "Face_Focused", skin = 2, hairColor = 1 }

local ROUNDS, BREAK_TIME, INTRO_TIME, OVER_TIME = 3, 10, 4, 7
local BREAK_HEAL = 20                       -- Erholung in der Pause (max. volle Leben)

local state = RS:FindFirstChild("CC_MatchState") or Instance.new("Folder")
state.Name = "CC_MatchState"; state.Parent = RS
local function set(k, v) state:SetAttribute(k, v) end
local menu = RS:FindFirstChild("CC_Menu") or Instance.new("RemoteEvent")
menu.Name = "CC_Menu"; menu.Parent = RS
local resultContinue = RS:FindFirstChild("CC_ResultContinue") or Instance.new("RemoteEvent")
resultContinue.Name = "CC_ResultContinue"; resultContinue.Parent = RS

-- Sounds: Gong bei Rundenstart/-ende, Publikum als Dauerschleife (lauter bei K.o./Sieg)
local SFX = game:GetService("SoundService"):WaitForChild("CC_Sounds")
local function bell(times) task.spawn(function() for i = 1, times do SFX.Bell:Play(); task.wait(0.45) end end) end
SFX.Crowd.Looped = true; SFX.Crowd.Volume = 0.3; SFX.Crowd:Play()
local function crowd(v) game:GetService("TweenService"):Create(SFX.Crowd, TweenInfo.new(0.6), { Volume = v }):Play() end
state:GetAttributeChangedSignal("CrowdBoost"):Connect(function() crowd(0.8); task.delay(3, function() crowd(0.3) end) end)

local dummy = workspace:WaitForChild("CC_TrainingDummy")
local function canvasY()
	local c = workspace.CC_Arena:FindFirstChild("Platform_Canvas_FightSurface", true)
	return c.Position.Y + c.Size.Y / 2
end
-- Kampfort: Online-Kaempfe (pvp) in der Fight-Night-Arena (Workspace.CC_FightNight, setup_fight_night_v01; Entscheidung 2026-10-13),
-- Tutorial, Training und erstes Sparring in der kleinen Arena (CC_Arena, Kaefig bei 0,0).
-- workspace-Attribut CC_PvpArena = "arena" schaltet Online-Kaempfe zurueck in die kleine Arena.
local function fightNight(m)
	local fn = workspace:FindFirstChild("CC_FightNight")
	return m and (m.mode == "pvp" or m.mode == "career" or m.mode == "trainer") and fn and workspace:GetAttribute("CC_PvpArena") ~= "arena" and fn:GetAttribute("CC_CageCenter") and fn or nil
end
local function arenaCenter(m)
	local fn = fightNight(m)
	if fn then
		local c = fn:GetAttribute("CC_CageCenter")
		if c then return Vector3.new(c.X, 0, c.Z), c.Y end
	end
	return Vector3.zero, canvasY()
end
local function corners(m)
	local c, fy = arenaCenter(m)
	local y = fy + 3                          -- HumanoidRootPart-Mitte 3 Studs ueber den Fuessen
	return CFrame.lookAt(c + Vector3.new(0, y, 7), c + Vector3.new(0, y, -7)), CFrame.lookAt(c + Vector3.new(0, y, -7), c + Vector3.new(0, y, 7))
end
-- Lobby: im Trainings-Gym (Workspace.CC_Gym, Boden y = 0, Mitte x = 160), sonst Hallenboden vor dem Kaefig; Spieler nebeneinander
local LOBBY_Y = 3                              -- Hallenboden (0) + 3
local function lobbyCF(i)
	local k = ((i or 1) % 7 - 3) * 2.5
	local gym = workspace:FindFirstChild("CC_Gym")
	if gym then                                  -- Startort im Trainings-Gym: hinter dem Eingang, Blick in die Halle
		local x = 160 + k                         -- Lobby V8: innen mit freiem Blick aufs Oktagon
		return CFrame.lookAt(Vector3.new(x, LOBBY_Y, 38), Vector3.new(160, LOBBY_Y, 4))
	end
	local x = k
	return CFrame.lookAt(Vector3.new(x, LOBBY_Y, 25), Vector3.new(x, LOBBY_Y, 0))
end

-- Shorts-Farbe nach Ecke: Rot (Standard des Charakters) / Blau (wie der Trainingsgegner)
local SHORTS = { red = Color3.new(0.564706, 0.0823529, 0.117647), blue = Color3.new(0.117647, 0.235294, 0.627451) }
local function paint(c, side)
	local s = c and c:FindFirstChild("Fighter_Shorts", true)
	if not (s and s:IsA("BasePart")) then return end
	-- Spieler tragen ihre freigeschalteten Shorts (Belohnung); nur KI-Gegner bekommen die Eckfarbe
	local plr = Players:GetPlayerFromCharacter(c)
	if plr then
		local ok, look = pcall(function() return HttpService:JSONDecode(plr:GetAttribute("CC_Look") or "{}") end)
		local LookS = require(RS:WaitForChild("CC_LookShared"))
		local it = ok and look.shorts and LookS.SHORTS[look.shorts]
		if it then s.Color = it.color; return end
	end
	s.Color = SHORTS[side]
end

-- ---------------- Warteschlange ----------------
local queue = {}            -- { player, mode }
local function inQueue(p) for i, e in ipairs(queue) do if e[1] == p then return i end end end
local function updateQueueAttrs()
	local n = 0
	for _, e in ipairs(queue) do if e[2] == "pvp" then n += 1 end end
	set("QueuePvp", n)
end
local current = nil         -- laufender Kampf: { red = Player, blue = Player | nil, mode = "training" | "pvp" }
local function isFighting(p) return current ~= nil and (current.red == p or current.blue == p) end
resultContinue.OnServerEvent:Connect(function(p)
	if state:GetAttribute("State") == "over" and isFighting(p) then p:SetAttribute("CC_ResultReady", true) end
end)
-- Menue-Wahl: vom Client (CC_Menu) oder serverseitig (ServerStorage.CC_MenuServer, z. B. Trainer im Gym)
local menuServer = game.ServerStorage:FindFirstChild("CC_MenuServer") or Instance.new("BindableEvent")
menuServer.Name = "CC_MenuServer"; menuServer.Parent = game.ServerStorage
local LEVELS = { passiv = true, anfaenger = true, fortgeschritten = true }   -- Trainingsgegner-Stufen (CC_CharacterAnimations)
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
	if what == "training" then                                     -- gewaehlte Stufe merken (Standard: Anfaenger); Trainer im Gym nutzt die letzte Wahl
		if type(level) == "string" and LEVELS[level] then p:SetAttribute("CC_DummyLevel", level)
		elseif not p:GetAttribute("CC_DummyLevel") then p:SetAttribute("CC_DummyLevel", "anfaenger") end
	elseif what == "career" then
		if not careerReady(p, level) then p:SetAttribute("CC_Notice", "Dieser Karriere-Gegner ist noch gesperrt.|" .. tostring(workspace:GetServerTimeNow())); return end
		p:SetAttribute("CC_CareerSelected", level)
	elseif what == "trainer" then
		if not fromServer or not trainerReady(p, level) then p:SetAttribute("CC_Notice", "Erledige zuerst alle Trainer-Quests.|" .. tostring(workspace:GetServerTimeNow())); return end
		p:SetAttribute("CC_TrainerSelected", level)
	end
	local i = inQueue(p)
	if what == "cancel" then
		if i then table.remove(queue, i) end
		p:SetAttribute("CC_Queue", nil)
	elseif (what == "training" or what == "pvp" or what == "career" or (what == "trainer" and fromServer) or ((what == "tutorial" or what == "sparring") and fromServer)) and not isFighting(p) then
		if i then table.remove(queue, i) end
		table.insert(queue, { p, what, (what == "career" or what == "trainer") and level or nil })
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
-- Charaktere ausserhalb eines Kampfs stehen in der Lobby (der Spawn liegt im Kaefig)
local lobbyCount = 0
local function toLobby(p)
	local c = p.Character
	if c and c:FindFirstChild("HumanoidRootPart") then
		lobbyCount += 1
		reset:Invoke(c, lobbyCF(lobbyCount), nil)
		c:SetAttribute("CC_Opponent", nil); c:SetAttribute("CC_Frozen", false)
		paint(c, "red")
	end
end
local function hookPlayer(p)
	p.CharacterAdded:Connect(function(c)
		c:WaitForChild("HumanoidRootPart"); task.wait(0.5)
		if not isFighting(p) then toLobby(p) end
	end)
	if p.Character then task.spawn(function() task.wait(0.5); if not isFighting(p) then toLobby(p) end end) end
end
Players.PlayerAdded:Connect(hookPlayer)
for _, p in ipairs(Players:GetPlayers()) do hookPlayer(p) end

local DUMMY_PARK = CFrame.lookAt(Vector3.new(26, LOBBY_Y, -26), Vector3.new(0, LOBBY_Y, 0))   -- Hallenecke, ausserhalb des Kaefigs
local function parkDummy()        -- Trainingsgegner wartet ausserhalb des Kaefigs und greift nicht an
	dummy:SetAttribute("CC_InMatch", false); dummy:SetAttribute("CC_Opponent", nil)
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
local frozen = false
local function freeze(m, on)
	frozen = on
	for _, c in ipairs({ chars(m) }) do if c then c:SetAttribute("CC_Frozen", on) end end
end
RunService.Heartbeat:Connect(function()
	if not current then return end
	for _, c in ipairs({ chars(current) }) do
		local h = c and c:FindFirstChildOfClass("Humanoid")
		if h then
			if frozen then h.WalkSpeed = 0 elseif h.WalkSpeed == 0 and not c:GetAttribute("CC_KO") and not c:GetAttribute("CC_Wrestle") then h.WalkSpeed = c:GetAttribute("CC_MobilitySpeed") or 8 end
		end
	end
end)
local function damage(c) return c and (c:GetAttribute("CC_DamageDealt") or 0) or 0 end
local function clearDamage(m) for _, c in ipairs({ chars(m) }) do if c then c:SetAttribute("CC_DamageDealt", 0) end end end
local JUDGE_BIAS = { -1.35, 0, 1.35 }
local function scoreRound(cards, totalsRed, totalsBlue, round, r, b, kdRedStart, kdBlueStart)
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
	set("JudgeCards", HttpService:JSONEncode(cards))
	set("JudgeRed", totalsRed[1] + totalsRed[2] + totalsRed[3])
	set("JudgeBlue", totalsBlue[1] + totalsBlue[2] + totalsBlue[3])
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
local function placeBoth(m, heal)
	local r, b = chars(m)
	local cr, cb = corners(m)
	if r then reset:Invoke(r, cr, heal and math.min(100, r.Humanoid.Health + heal) or nil) end
	if b then reset:Invoke(b, cb, heal and math.min(100, b.Humanoid.Health + heal) or nil) end
	if r and b then r:SetAttribute("CC_Opponent", b.Name); b:SetAttribute("CC_Opponent", r.Name) end
	paint(r, "red"); paint(b, "blue")
end
local function present(m)                    -- beide Kaempfer noch da?
	local r, b = chars(m)
	return r ~= nil and r.Parent ~= nil and m.red.Parent ~= nil, b ~= nil and b.Parent ~= nil and (not m.blue or m.blue.Parent ~= nil)
end
-- Fortschritt (CC_Profile): Spieler gegen Spieler zaehlt in die Bilanz, Training gibt nur XP; jede Runde trainiert Kondition
local function profile(p, kind, a, b, c)
	local ev = game.ServerStorage:FindFirstChild("CC_ProfileEvent")
	if ev and p and p.Parent then ev:Fire(p, kind, a, b, c) end
end
local function koWinner(m)
	local r, b = chars(m)
	if r and r:GetAttribute("CC_KO") then return "blue" end
	if b and b:GetAttribute("CC_KO") then return "red" end
	return nil
end

local runMatch
-- Tutorial: Spieler und passiver Gegner im Kaefig, keine Uhr und kein Ergebnis; CC_Tutorial fuehrt durch die Lektionen
local function runTutorial(m)
	current = m
	set("Mode", "tutorial"); set("RedName", m.red.Name); set("BlueName", "Trainingsgegner"); set("Winner", ""); set("WinnerName", "")
	dummy:SetAttribute("CC_Difficulty", "passiv"); dummy:SetAttribute("CC_Passive", true); dummy:SetAttribute("CC_InMatch", true)
	freeze(m, false)
	placeBoth(m)
	clearDamage(m)
	set("State", "tutorial"); set("Banner", ""); set("BannerSub", "")
	print("[CC] Tutorial startet: " .. m.red.Name)
	local run = game.ServerStorage:FindFirstChild("CC_TutorialRun")
	local ok, nextStep = pcall(function() return run and run:Invoke(m.red) end)
	if not ok then warn("[CC] Tutorial-Fehler: " .. tostring(nextStep)) end
	dummy:SetAttribute("CC_Tutor", nil); dummy:SetAttribute("CC_Passive", nil)
	if ok and nextStep == "sparring" and m.red.Parent and m.red.Character then
		return runMatch({ red = m.red, mode = "sparring" })   -- direkt im Kaefig weiter
	end
	current = nil
	if m.red.Parent then toLobby(m.red) end
	parkDummy()
	set("State", "idle"); set("Mode", ""); set("RedName", ""); set("BlueName", "")
end

function runMatch(m)
	if m.mode == "tutorial" then return runTutorial(m) end
	current = m

	-- Der Client muss die Kampfclips bereits besitzen, bevor Walkout/Takedown beginnt.
	-- Ohne diese Schranke kann Roblox beim ersten Abspielen kurz die Bind-/T-Pose zeigen.
	local preloadDeadline = os.clock() + 8
	while os.clock() < preloadDeadline do
		local pending = false
		for _, p in ipairs({ m.red, m.blue }) do
			if p and p.Parent and p:GetAttribute("CC_AnimationsReady") ~= true then
				pending = true
				break
			end
		end
		if not pending then break end
		task.wait(0.1)
	end

	for _, p in ipairs({ m.red, m.blue }) do if p then p:SetAttribute("CC_ResultReady", nil); p:SetAttribute("CC_LastFight", nil) end end
	local career = m.mode == "career" and OPP.byId[m.opponentId] or nil
	local trainerDef = m.mode == "trainer" and SIGPROG.list[m.opponentId] or nil
	local trainer = trainerDef and trainerDef.boss or nil
	local blueLabel = career and career.name or trainer and trainer.name or (m.blue and m.blue.Name or "Trainingsgegner")
	local rounds = career and career.rounds or trainer and trainer.rounds or (m.mode == "sparring" and 1 or ROUNDS)
	set("Rounds", rounds)
	set("Mode", m.mode); set("OpponentId", career and career.id or trainerDef and m.opponentId or ""); set("RedName", m.red.Name); set("BlueName", blueLabel); set("WinnerName", "")
	set("Winner", ""); set("ScoreRed", 0); set("ScoreBlue", 0); set("JudgeCards", "[]"); set("JudgeRed", 0); set("JudgeBlue", 0)
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
	elseif not m.blue then
		dummy:SetAttribute("CC_AIStyle", workspace:GetAttribute("CC_TestAIStyle") or "Grappler")
		dummy:SetAttribute("CC_InMatch", true)
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
	print(("[CC] Kampf startet (%s): %s gegen %s"):format(m.mode, m.red.Name, blueLabel))
	set("Finisher", nil)
	do local r0, b0 = chars(m); for _, c in ipairs({ r0, b0 }) do if c then c:SetAttribute("CC_FocusReset", os.clock()) end end end   -- Signatur-Fokus: neues Match = 0
	-- Fight Night: Walkout ueber den vorhandenen Einlaufweg bis zur Kaefigtuer, danach wie gewohnt in die Ecken
	local fn = fightNight(m)
	if fn then
		local spots = fn:FindFirstChild("FN_Spots")
		local startP, door = spots and spots:FindFirstChild("Fighter_Walkout_Main"), spots and spots:FindFirstChild("Cage_Door")
		if startP and door then
			set("Mode", m.mode); set("State", "walkout")
			if trainer then set("Banner", "TRAINER-ENDKAMPF"); set("BannerSub", m.red.Name .. "  vs.  " .. blueLabel)
			elseif career then set("Banner", "KARRIERE"); set("BannerSub", m.red.Name .. "  vs.  " .. blueLabel)
			else set("Banner", "FIGHT NIGHT"); set("BannerSub", "Walkout") end
			local r, b = chars(m)
			-- Streaming: Boden am Ziel vorher laden lassen, sonst faellt der Spieler beim Teleport durch (Map liegt weit entfernt)
			for _, pl in ipairs({ m.red, m.blue }) do
				if pl and pl.Parent then
					pcall(function() pl:RequestStreamAroundAsync(startP.Position, 10) end)
					pcall(function() pl:RequestStreamAroundAsync(door.Position, 10) end)
				end
			end
			local list = {}
			for i, c in ipairs({ r, b }) do
				local h, root = c and c:FindFirstChildOfClass("Humanoid"), c and c:FindFirstChild("HumanoidRootPart")
				if h and root then
					local side = (i == 1) and -2.5 or 2.5
					local mid = door.Position + (startP.Position - door.Position) * 0.55   -- ab der Mitte des Einlaufwegs (Gehtempo: gut 6 s bis zur Tuer)
					local from = Vector3.new(mid.X, startP.Position.Y, mid.Z) + Vector3.new(side, 0, (i - 1) * 4)        -- Rot vorn, Blau dahinter
					-- auf die Oberkante der Bodenkollision stellen (duenne Laufsteg-Platte: sonst starten die Fuesse darin und fallen durch)
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
				-- Trainer-Endkampf und Karriere: der KI-Gegner laeuft mit ein (hinter dem Spieler); sonst (nur Test) steht er schon an der Tuer
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
			print(("[CC] Walkout fertig nach %.1f s"):format(os.clock() - t0))
		end
	end
	local totalRed, totalBlue, winner, method = 0, 0, nil, nil
	local scorecards, judgeRed, judgeBlue = {}, { 0, 0, 0 }, { 0, 0, 0 }
	for round = 1, rounds do
		freeze(m, true)
		placeBoth(m, round > 1 and BREAK_HEAL or nil)
		clearDamage(m)
		local roundRed, roundBlue = chars(m)
		local kdRedStart = roundRed and (roundRed:GetAttribute("CC_Knockdowns") or 0) or 0
		local kdBlueStart = roundBlue and (roundBlue:GetAttribute("CC_Knockdowns") or 0) or 0
		set("Round", round)
		set("State", round == 1 and "intro" or "break")
		local wait = round == 1 and (workspace:GetAttribute("CC_IntroTime") or INTRO_TIME) or (workspace:GetAttribute("CC_BreakTime") or BREAK_TIME)
		for t = wait, 1, -1 do
			set("TimeLeft", t)
			set("Banner", "RUNDE " .. round); set("BannerSub", t <= 3 and tostring(t) or (round == 1 and "Kampf beginnt" or "Pause"))
			task.wait(1)
		end
		set("Banner", "FIGHT!"); set("BannerSub", "")
		local roundTime = workspace:GetAttribute("CC_RoundTime") or 120
		set("State", "fight"); set("TimeLeft", roundTime)
		bell(1)
		freeze(m, false)
		task.delay(1, function() if state:GetAttribute("Banner") == "FIGHT!" then set("Banner", ""); set("BannerSub", "") end end)
		local t0 = os.clock()
		while os.clock() - t0 < roundTime do
			task.wait(0.1)
			set("TimeLeft", math.max(0, math.ceil(roundTime - (os.clock() - t0))))
			local rOk, bOk = present(m)
			if not (rOk and bOk) then winner = rOk and "red" or "blue"; method = "Aufgabe"; break end
			local r, b = chars(m)
			set("ScoreRed", totalRed + damage(r)); set("ScoreBlue", totalBlue + damage(b))
			winner = koWinner(m)
			if winner then
				local loser = winner == "red" and b or r
				local stop = loser and loser:GetAttribute("CC_Stoppage")
				method = (loser and loser:GetAttribute("CC_LastReact") == "submission") and "Submission"
					or stop == "LEG_TKO" and "T.K.O. · Beinverletzung"
					or stop == "ARM_TKO" and "T.K.O. · Armverletzung"
					or stop == "BODY_TKO" and "T.K.O. · Rippenverletzung"
					or stop == "GROUND_TKO" and "T.K.O. · Ground-and-Pound"
					or stop == "TKO" and "T.K.O." or "K.O."
				break
			end
		end
		local r, b = chars(m)
		totalRed += damage(r); totalBlue += damage(b)
		set("ScoreRed", totalRed); set("ScoreBlue", totalBlue)
		if r and b then scoreRound(scorecards, judgeRed, judgeBlue, round, r, b, kdRedStart, kdBlueStart) end
		for _, p in ipairs({ m.red, m.blue }) do profile(p, "train", "Cardio", 2) end
		if not winner then
			local dw = doctorWinner(m)
			if dw then winner, method = dw, "Arztabbruch"; set("Banner", "ARZTABBRUCH"); set("BannerSub", "Kampf wird beendet") end
		end
		if winner then break end
		freeze(m, true)
		bell(3)
		set("Banner", "ENDE RUNDE " .. round); set("BannerSub", string.format("Punkte  %d : %d", totalRed, totalBlue))
		task.wait(2)
	end
	if not winner then
		method = "Punktentscheidung"
		winner = decisionWinner(judgeRed, judgeBlue)
	end
	if method == "K.O." or method == "Submission" then task.wait(1.5) end
	-- Finisher-Wiederholung: nur wenn der Server den K.o. durch eine Signatur bestaetigt hat. Ergebnis steht bereits fest
	-- (Winner wird vorher gesetzt); die Clients zeigen die letzte Aktion als lokale Kopie und koennen sie ueberspringen.
	local fin = state:GetAttribute("Finisher")
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
	-- Text fuer Zuschauer; die Kaempfer sehen im HUD SIEG / NIEDERLAGE
	set("Banner", winner == "draw" and "UNENTSCHIEDEN" or (wname .. " GEWINNT"))
	set("BannerSub", method .. string.format("   ·   %d : %d", totalRed, totalBlue))
	print(("[CC] Kampf vorbei: %s (%s) %d:%d"):format(winner, method, totalRed, totalBlue))
	for side, p in pairs({ red = m.red, blue = m.blue or false }) do
		if p then
			local res = winner == "draw" and "draw" or (winner == side and "win" or "loss")
			local xp = nil                                 -- Online/Karriere: XP vergibt CC_Profile selbst
			profile(p, "goal", "fights", 1)
			if side == "red" then
				local ch = p.Character
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
			p:SetAttribute("CC_LastFight", HttpService:JSONEncode({ mode = m.mode, opponentId = career and career.id or trainerDef and m.opponentId or nil, opponentName = career and career.name or trainer and trainer.name or nil, result = res, method = method, xp = xp, scorecards = scorecards, judgeRed = judgeRed, judgeBlue = judgeBlue }))
		end
	end
	for t = OVER_TIME, 1, -1 do
		set("TimeLeft", t)
		local ready = m.red:GetAttribute("CC_ResultReady") == true and (not m.blue or m.blue:GetAttribute("CC_ResultReady") == true)
		if ready then break end
		task.wait(1)
	end
	for _, p in ipairs({ m.red, m.blue }) do if p then p:SetAttribute("CC_ResultReady", nil) end end
	-- zurueck in die Lobby
	freeze(m, false)
	current = nil
	for _, p in ipairs({ m.red, m.blue }) do if p and p.Parent then toLobby(p) end end
	if not m.blue then parkDummy() end                -- Trainingsgegner war beteiligt (Training, Sparring, Test)
	set("State", "idle"); set("Mode", ""); set("OpponentId", ""); set("Banner", ""); set("BannerSub", ""); set("RedName", ""); set("BlueName", "")
end

-- naechsten Kampf aus der Warteschlange bilden (Gegen-Spieler hat Vorrang)
local function nextMatch()
	while true do
		for i = #queue, 1, -1 do if not queue[i][1].Parent or not queue[i][1].Character then table.remove(queue, i) end end
		local pvp = {}
		for i, e in ipairs(queue) do if e[2] == "pvp" then table.insert(pvp, i) end end
		if #pvp == 1 and workspace:GetAttribute("CC_TestPvpDummy") then          -- Test (Studio, 1 Spieler): Online-Ablauf gegen den Trainingsgegner
			local a = queue[pvp[1]][1]
			table.remove(queue, pvp[1]); a:SetAttribute("CC_Queue", nil); updateQueueAttrs()
			return { red = a, mode = "pvp" }
		end
		if #pvp >= 2 then
			local a, b = queue[pvp[1]][1], queue[pvp[2]][1]
			table.remove(queue, pvp[2]); table.remove(queue, pvp[1])
			a:SetAttribute("CC_Queue", nil); b:SetAttribute("CC_Queue", nil); updateQueueAttrs()
			return { red = a, blue = b, mode = "pvp" }
		end
		for i, e in ipairs(queue) do
			if e[2] == "training" or e[2] == "tutorial" or e[2] == "sparring" or e[2] == "career" or e[2] == "trainer" then
				table.remove(queue, i); e[1]:SetAttribute("CC_Queue", nil); updateQueueAttrs()
				return { red = e[1], mode = e[2], opponentId = e[3] }
			end
		end
		task.wait(0.5)
	end
end

-- Fallschutz: wer unter die Welt faellt (z. B. Boden noch nicht geladen), kommt sicher zurueck.
--   Ausserhalb eines Kampfs: in die Lobby (Gym). Im Kampf: zurueck in die eigene Ecke, Leben unveraendert (keine Flucht aus dem Kampf).
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
			if isFighting(p) then
				local cr, cb = corners(current)
				local cf = (current.red == p) and cr or cb
				reset:Invoke(c, cf, h.Health)
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
		if current and not current.blue then local _, cb = corners(current); reset:Invoke(dummy, cb, dummy.Humanoid.Health) else parkDummy() end
	end
end)

set("State", "idle"); set("Mode", ""); set("OpponentId", ""); set("Banner", ""); set("BannerSub", ""); set("QueuePvp", 0); set("RedName", ""); set("BlueName", "")
parkDummy()
while true do
	local m = nextMatch()
	local ok, err = pcall(runMatch, m)
	if not ok then
		warn("[CC] Kampf-Fehler: " .. tostring(err))
		current = nil; frozen = false
		for _, p in ipairs({ m.red, m.blue }) do if p and p.Parent then toLobby(p) end end
		parkDummy(); set("State", "idle"); set("Mode", ""); set("OpponentId", ""); set("Banner", ""); set("BannerSub", ""); set("RedName", ""); set("BlueName", "")
	end
end
