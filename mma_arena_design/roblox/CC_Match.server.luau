-- ServerScriptService.CC_Match
-- Runden-System: 3 Runden à 2:00, 10 s Pause, Sieg durch K.o. oder nach Punkten (verursachter Schaden).
-- Zustand fuer HUD/Clients als Attribute an ReplicatedStorage.CC_MatchState:
--   State ("intro" | "fight" | "break" | "over"), Round, TimeLeft (s), Banner (Text), BannerSub (Text),
--   ScoreRed / ScoreBlue (Punkte), Winner ("red" | "blue" | "draw" | "").
-- Rot = Spieler, Blau = Trainingsgegner. Waehrend intro/break/over sind beide eingefroren (CC_Frozen, WalkSpeed 0).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local RS = game.ReplicatedStorage
local reset = game.ServerStorage:WaitForChild("CC_ResetFighter")

local ROUNDS, ROUND_TIME, BREAK_TIME, INTRO_TIME, OVER_TIME = 3, 120, 10, 4, 7
local BREAK_HEAL = 20                       -- Erholung in der Pause (max. volle Leben)

local state = RS:FindFirstChild("CC_MatchState") or Instance.new("Folder")
state.Name = "CC_MatchState"; state.Parent = RS
local function set(k, v) state:SetAttribute(k, v) end

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
local function red() local p = Players:GetPlayers()[1]; return p and p.Character end
local function fighters() local r = red(); return r, dummy end

local frozen = false
local function freeze(on)
	frozen = on
	for _, c in ipairs({ fighters() }) do
		if c then c:SetAttribute("CC_Frozen", on) end
	end
end
RunService.Heartbeat:Connect(function()
	for _, c in ipairs({ fighters() }) do
		local h = c and c:FindFirstChildOfClass("Humanoid")
		if h then
			if frozen then h.WalkSpeed = 0 elseif h.WalkSpeed == 0 and not c:GetAttribute("CC_KO") and not c:GetAttribute("CC_Wrestle") then h.WalkSpeed = 8 end
		end
	end
end)

local function damage(c) return c and (c:GetAttribute("CC_DamageDealt") or 0) or 0 end
local function clearDamage() for _, c in ipairs({ fighters() }) do if c then c:SetAttribute("CC_DamageDealt", 0) end end end

local function placeBoth(heal)
	local r, b = fighters()
	local cr, cb = corners()
	if r then reset:Invoke(r, cr, heal and math.min(100, r.Humanoid.Health + heal) or nil) end
	reset:Invoke(b, cb, heal and math.min(100, b.Humanoid.Health + heal) or nil)
end

local function waitForPlayer()
	while not (red() and red():FindFirstChild("HumanoidRootPart")) do task.wait(0.5) end
	task.wait(1)
end

-- K.o. waehrend der Runde beendet den Kampf
local function koWinner()
	local r, b = fighters()
	if r and r:GetAttribute("CC_KO") then return "blue" end
	if b:GetAttribute("CC_KO") then return "red" end
	return nil
end

while true do
	waitForPlayer()
	set("Winner", ""); set("ScoreRed", 0); set("ScoreBlue", 0)
	local totalRed, totalBlue, winner, method = 0, 0, nil, nil
	for round = 1, ROUNDS do
		-- Vorstellung / Pause
		freeze(true)
		placeBoth(round > 1 and BREAK_HEAL or nil)
		clearDamage()
		set("Round", round)
		set("State", round == 1 and "intro" or "break")
		local wait = round == 1 and INTRO_TIME or BREAK_TIME
		for t = wait, 1, -1 do
			set("TimeLeft", t)
			set("Banner", "RUNDE " .. round); set("BannerSub", t <= 3 and tostring(t) or (round == 1 and "Kampf beginnt" or "Pause"))
			task.wait(1)
		end
		-- Kampf
		set("Banner", "FIGHT!"); set("BannerSub", "")
		set("State", "fight"); set("TimeLeft", ROUND_TIME)
		bell(1)
		freeze(false)
		task.delay(1, function() if state:GetAttribute("Banner") == "FIGHT!" then set("Banner", ""); set("BannerSub", "") end end)
		local t0 = os.clock()
		while os.clock() - t0 < ROUND_TIME do
			task.wait(0.1)
			set("TimeLeft", math.max(0, math.ceil(ROUND_TIME - (os.clock() - t0))))
			local r = red(); if not r then break end
			set("ScoreRed", totalRed + damage(r)); set("ScoreBlue", totalBlue + damage(dummy))
			winner = koWinner()
			if winner then method = "K.O."; break end
		end
		local r = red()
		totalRed += damage(r); totalBlue += damage(dummy)
		set("ScoreRed", totalRed); set("ScoreBlue", totalBlue)
		if winner or not r then break end
		freeze(true)
		bell(3)
		set("Banner", "ENDE RUNDE " .. round); set("BannerSub", string.format("Punkte  %d : %d", totalRed, totalBlue))
		task.wait(2)
	end
	-- Ergebnis
	if not winner then
		method = "Punktentscheidung"
		winner = totalRed > totalBlue and "red" or totalBlue > totalRed and "blue" or "draw"
	end
	if method == "K.O." then task.wait(1.5) end
	freeze(true)
	set("State", "over"); set("Winner", winner)
	bell(3); crowd(0.8); task.delay(4, function() crowd(0.3) end)
	set("Banner", winner == "red" and "SIEG" or winner == "blue" and "NIEDERLAGE" or "UNENTSCHIEDEN")
	set("BannerSub", method .. string.format("   ·   %d : %d", totalRed, totalBlue))
	print(("[CC] Kampf vorbei: %s (%s) %d:%d"):format(winner, method, totalRed, totalBlue))
	for t = OVER_TIME, 1, -1 do set("TimeLeft", t); task.wait(1) end
end
