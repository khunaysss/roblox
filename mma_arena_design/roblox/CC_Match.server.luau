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
local function corners()
	local y = canvasY() + 3                   -- HumanoidRootPart-Mitte 3 Studs ueber den Fuessen
	return CFrame.lookAt(Vector3.new(0, y, 7), Vector3.new(0, y, -7)), CFrame.lookAt(Vector3.new(0, y, -7), Vector3.new(0, y, 7))
end
-- Lobby: Hallenboden vor dem Kaefig (Blick zum Kaefig); Spieler werden nebeneinander aufgestellt
local LOBBY_Y = 3                              -- Hallenboden (0) + 3
local function lobbyCF(i)
	local x = ((i or 1) % 7 - 3) * 3
	return CFrame.lookAt(Vector3.new(x, LOBBY_Y, 25), Vector3.new(x, LOBBY_Y, 0))
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
menu.OnServerEvent:Connect(function(p, what)
	if type(what) ~= "string" then return end
	local i = inQueue(p)
	if what == "cancel" then
		if i then table.remove(queue, i) end
		p:SetAttribute("CC_Queue", nil)
	elseif (what == "training" or what == "pvp") and not isFighting(p) then
		if i then table.remove(queue, i) end
		table.insert(queue, { p, what })
		p:SetAttribute("CC_Queue", what)
	end
	updateQueueAttrs()
end)
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
	local cr, cb = corners()
	if r then reset:Invoke(r, cr, heal and math.min(100, r.Humanoid.Health + heal) or nil) end
	if b then reset:Invoke(b, cb, heal and math.min(100, b.Humanoid.Health + heal) or nil) end
	if r and b then r:SetAttribute("CC_Opponent", b.Name); b:SetAttribute("CC_Opponent", r.Name) end
end
local function present(m)                    -- beide Kaempfer noch da?
	local r, b = chars(m)
	return r ~= nil and r.Parent ~= nil and m.red.Parent ~= nil, b ~= nil and b.Parent ~= nil and (not m.blue or m.blue.Parent ~= nil)
end
local function koWinner(m)
	local r, b = chars(m)
	if r and r:GetAttribute("CC_KO") then return "blue" end
	if b and b:GetAttribute("CC_KO") then return "red" end
	return nil
end

local function runMatch(m)
	current = m
	set("Mode", m.mode); set("RedName", m.red.Name); set("BlueName", m.blue and m.blue.Name or "Trainingsgegner"); set("WinnerName", "")
	set("Winner", ""); set("ScoreRed", 0); set("ScoreBlue", 0)
	if m.mode == "training" then dummy:SetAttribute("CC_InMatch", true) end
	print(("[CC] Kampf startet (%s): %s gegen %s"):format(m.mode, m.red.Name, m.blue and m.blue.Name or "Trainingsgegner"))
	local totalRed, totalBlue, winner, method = 0, 0, nil, nil
	for round = 1, ROUNDS do
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
	for t = OVER_TIME, 1, -1 do set("TimeLeft", t); task.wait(1) end
	-- zurueck in die Lobby
	freeze(m, false)
	current = nil
	for _, p in ipairs({ m.red, m.blue }) do if p and p.Parent then toLobby(p) end end
	if m.mode == "training" then parkDummy() end
	set("State", "idle"); set("Mode", ""); set("Banner", ""); set("BannerSub", ""); set("RedName", ""); set("BlueName", "")
end

-- naechsten Kampf aus der Warteschlange bilden (Gegen-Spieler hat Vorrang)
local function nextMatch()
	while true do
		for i = #queue, 1, -1 do if not queue[i][1].Parent or not queue[i][1].Character then table.remove(queue, i) end end
		local pvp = {}
		for i, e in ipairs(queue) do if e[2] == "pvp" then table.insert(pvp, i) end end
		if #pvp >= 2 then
			local a, b = queue[pvp[1]][1], queue[pvp[2]][1]
			table.remove(queue, pvp[2]); table.remove(queue, pvp[1])
			a:SetAttribute("CC_Queue", nil); b:SetAttribute("CC_Queue", nil); updateQueueAttrs()
			return { red = a, blue = b, mode = "pvp" }
		end
		for i, e in ipairs(queue) do
			if e[2] == "training" then
				table.remove(queue, i); e[1]:SetAttribute("CC_Queue", nil); updateQueueAttrs()
				return { red = e[1], mode = "training" }
			end
		end
		task.wait(0.5)
	end
end

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
