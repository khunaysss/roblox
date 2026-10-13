-- ServerScriptService.CC_Match
-- Kampf-Ablauf mit Menue: eine Arena, ein Kampf gleichzeitig.
--   Training: Spieler (Rot) gegen den Trainingsgegner (Blau).  Gegen Spieler: die ersten zwei aus der Warteschlange (Rot/Blau).
--   Wer nicht kaempft, steht in der Lobby vor dem Kaefig (Menue sichtbar). Gegen-Spieler-Kaempfe haben Vorrang.
-- Runden: 3 x 2:00, 10 s Pause, Sieg durch K.o., Submission oder nach Punkten (verursachter Schaden); Aufgabe, wenn ein Spieler geht.
-- Menue -> Server: ReplicatedStorage.CC_Menu (RemoteEvent) mit "training" | "pvp" | "cancel".
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
local reset = game.ServerStorage:WaitForChild("CC_ResetFighter")

local ROUNDS, BREAK_TIME, INTRO_TIME, OVER_TIME = 3, 10, 4, 7
local BREAK_HEAL = 20                       -- Erholung in der Pause (max. volle Leben)

local state = RS:FindFirstChild("CC_MatchState") or Instance.new("Folder")
state.Name = "CC_MatchState"; state.Parent = RS
local function set(k, v) state:SetAttribute(k, v) end
local menu = RS:FindFirstChild("CC_Menu") or Instance.new("RemoteEvent")
menu.Name = "CC_Menu"; menu.Parent = RS

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
	return m and m.mode == "pvp" and fn and workspace:GetAttribute("CC_PvpArena") ~= "arena" and fn:GetAttribute("CC_CageCenter") and fn or nil
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
		local x = 160 - 20 + k                    -- Eingang liegt nach dem Import bei z = -25 (Modell um 180 Grad gedreht)
		return CFrame.lookAt(Vector3.new(x, LOBBY_Y, -19), Vector3.new(x, LOBBY_Y, 0))
	end
	local x = k
	return CFrame.lookAt(Vector3.new(x, LOBBY_Y, 25), Vector3.new(x, LOBBY_Y, 0))
end

-- Shorts-Farbe nach Ecke: Rot (Standard des Charakters) / Blau (wie der Trainingsgegner)
local SHORTS = { red = Color3.new(0.564706, 0.0823529, 0.117647), blue = Color3.new(0.117647, 0.235294, 0.627451) }
local function paint(c, side)
	local s = c and c:FindFirstChild("Fighter_Shorts", true)
	if s and s:IsA("BasePart") then s.Color = SHORTS[side] end
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
-- Menue-Wahl: vom Client (CC_Menu) oder serverseitig (ServerStorage.CC_MenuServer, z. B. Trainer im Gym)
local menuServer = game.ServerStorage:FindFirstChild("CC_MenuServer") or Instance.new("BindableEvent")
menuServer.Name = "CC_MenuServer"; menuServer.Parent = game.ServerStorage
local LEVELS = { passiv = true, anfaenger = true, fortgeschritten = true }   -- Trainingsgegner-Stufen (CC_CharacterAnimations)
local function onMenu(p, what, level, fromServer)
	if type(what) ~= "string" then return end
	if what == "training" then                                     -- gewaehlte Stufe merken (Standard: Anfaenger); Trainer im Gym nutzt die letzte Wahl
		if type(level) == "string" and LEVELS[level] then p:SetAttribute("CC_DummyLevel", level)
		elseif not p:GetAttribute("CC_DummyLevel") then p:SetAttribute("CC_DummyLevel", "anfaenger") end
	end
	local i = inQueue(p)
	if what == "cancel" then
		if i then table.remove(queue, i) end
		p:SetAttribute("CC_Queue", nil)
	elseif (what == "training" or what == "pvp" or ((what == "tutorial" or what == "sparring") and fromServer)) and not isFighting(p) then
		if i then table.remove(queue, i) end
		table.insert(queue, { p, what })
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
			if frozen then h.WalkSpeed = 0 elseif h.WalkSpeed == 0 and not c:GetAttribute("CC_KO") and not c:GetAttribute("CC_Wrestle") then h.WalkSpeed = 8 end
		end
	end
end)
local function damage(c) return c and (c:GetAttribute("CC_DamageDealt") or 0) or 0 end
local function clearDamage(m) for _, c in ipairs({ chars(m) }) do if c then c:SetAttribute("CC_DamageDealt", 0) end end end
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
local function profile(p, kind, a, b)
	local ev = game.ServerStorage:FindFirstChild("CC_ProfileEvent")
	if ev and p and p.Parent then ev:Fire(p, kind, a, b) end
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
	local rounds = m.mode == "sparring" and 1 or ROUNDS
	set("Rounds", rounds)
	set("Mode", m.mode); set("RedName", m.red.Name); set("BlueName", m.blue and m.blue.Name or "Trainingsgegner"); set("WinnerName", "")
	set("Winner", ""); set("ScoreRed", 0); set("ScoreBlue", 0)
	if m.mode == "training" or m.mode == "sparring" then
		local lv = m.mode == "sparring" and "anfaenger" or (m.red:GetAttribute("CC_DummyLevel") or "anfaenger")
		dummy:SetAttribute("CC_Difficulty", lv); dummy:SetAttribute("CC_Passive", lv == "passiv" or nil)
		dummy:SetAttribute("CC_InMatch", true)
	end
	print(("[CC] Kampf startet (%s): %s gegen %s"):format(m.mode, m.red.Name, m.blue and m.blue.Name or "Trainingsgegner"))
	-- Fight Night: Walkout ueber den vorhandenen Einlaufweg bis zur Kaefigtuer, danach wie gewohnt in die Ecken
	local fn = fightNight(m)
	if fn then
		local spots = fn:FindFirstChild("FN_Spots")
		local startP, door = spots and spots:FindFirstChild("Fighter_Walkout_Main"), spots and spots:FindFirstChild("Cage_Door")
		if startP and door then
			set("Mode", m.mode); set("State", "walkout"); set("Banner", "FIGHT NIGHT"); set("BannerSub", "Walkout")
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
				if e.c == dummy then e.root.CFrame = CFrame.lookAt(e.goal, e.goal - Vector3.new(0, 0, 1)) else e.h:MoveTo(e.goal) end   -- Trainingsgegner (nur Test) steht schon an der Tuer
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
	for round = 1, rounds do
		freeze(m, true)
		placeBoth(m, round > 1 and BREAK_HEAL or nil)
		clearDamage(m)
		set("Round", round)
		set("State", round == 1 and "intro" or "break")
		local wait = round == 1 and INTRO_TIME or BREAK_TIME
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
				method = (loser and loser:GetAttribute("CC_LastReact") == "submission") and "Submission" or "K.O."; break
			end
		end
		local r, b = chars(m)
		totalRed += damage(r); totalBlue += damage(b)
		set("ScoreRed", totalRed); set("ScoreBlue", totalBlue)
		for _, p in ipairs({ m.red, m.blue }) do profile(p, "train", "Cardio", 2) end
		if winner then break end
		freeze(m, true)
		bell(3)
		set("Banner", "ENDE RUNDE " .. round); set("BannerSub", string.format("Punkte  %d : %d", totalRed, totalBlue))
		task.wait(2)
	end
	if not winner then
		method = "Punktentscheidung"
		winner = totalRed > totalBlue and "red" or totalBlue > totalRed and "blue" or "draw"
	end
	if method == "K.O." or method == "Submission" then task.wait(1.5) end
	freeze(m, true)
	local wname = winner == "red" and m.red.Name or winner == "blue" and (m.blue and m.blue.Name or "Trainingsgegner") or ""
	set("State", "over"); set("Winner", winner); set("WinnerName", wname)
	bell(3); crowd(0.8); task.delay(4, function() crowd(0.3) end)
	-- Text fuer Zuschauer; die Kaempfer sehen im HUD SIEG / NIEDERLAGE
	set("Banner", winner == "draw" and "UNENTSCHIEDEN" or (wname .. " GEWINNT"))
	set("BannerSub", method .. string.format("   ·   %d : %d", totalRed, totalBlue))
	print(("[CC] Kampf vorbei: %s (%s) %d:%d"):format(winner, method, totalRed, totalBlue))
	for side, p in pairs({ red = m.red, blue = m.blue or false }) do
		if p then
			local res = winner == "draw" and "draw" or (winner == side and "win" or "loss")
			local xp = nil                                 -- Online: XP vergibt CC_Profile selbst (Ergebnis + Methode)
			if m.mode ~= "pvp" then xp = res == "win" and 30 or 15 end
			if m.mode == "pvp" then profile(p, "result", res, method)
			else profile(p, "xp", xp) end
			p:SetAttribute("CC_LastFight", game:GetService("HttpService"):JSONEncode({ mode = m.mode, result = res, method = method, xp = xp }))
		end
	end
	for t = OVER_TIME, 1, -1 do set("TimeLeft", t); task.wait(1) end
	-- zurueck in die Lobby
	freeze(m, false)
	current = nil
	for _, p in ipairs({ m.red, m.blue }) do if p and p.Parent then toLobby(p) end end
	if not m.blue then parkDummy() end                -- Trainingsgegner war beteiligt (Training, Sparring, Test)
	set("State", "idle"); set("Mode", ""); set("Banner", ""); set("BannerSub", ""); set("RedName", ""); set("BlueName", "")
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
			if e[2] == "training" or e[2] == "tutorial" or e[2] == "sparring" then
				table.remove(queue, i); e[1]:SetAttribute("CC_Queue", nil); updateQueueAttrs()
				return { red = e[1], mode = e[2] }
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

set("State", "idle"); set("Mode", ""); set("Banner", ""); set("BannerSub", ""); set("QueuePvp", 0); set("RedName", ""); set("BlueName", "")
parkDummy()
while true do
	local m = nextMatch()
	local ok, err = pcall(runMatch, m)
	if not ok then
		warn("[CC] Kampf-Fehler: " .. tostring(err))
		current = nil; frozen = false
		for _, p in ipairs({ m.red, m.blue }) do if p and p.Parent then toLobby(p) end end
		parkDummy(); set("State", "idle"); set("Mode", "")
	end
end
