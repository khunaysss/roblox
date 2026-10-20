-- StarterPlayer.StarterPlayerScripts.CC_BeltAward
-- Ehrung, sobald ein neuer Guertel erspielt ist (CC_LookShared.BELTS): grosses goldenes Banner mit Name und Grund,
-- Hinweis, wo man ihn anlegt. Nicht waehrend einer laufenden Runde (wartet bis Ergebnis oder Gym).
-- Beim Betreten des Spiels werden bereits vorhandene Guertel nicht erneut gefeiert.
local Players, RS, TweenService = game:GetService("Players"), game:GetService("ReplicatedStorage"), game:GetService("TweenService")
local Look = require(RS:WaitForChild("CC_LookShared"))
local player = Players.LocalPlayer
local mirror = RS:WaitForChild("CC_MatchState")

local known = nil              -- [Name] = true, bereits bekannte Guertel
local queue, showing = {}, false

local function unlockedSet()
	local prog, set = Look.progressOf(player), {}
	for _, b in ipairs(Look.BELTS) do
		if (b.kind == "title" or b.kind == "style") and Look.unlocked(b, prog) then set[b.name] = b end
	end
	return set
end

local function busy()
	local st = mirror:GetAttribute("State")
	local onb = player:GetAttribute("CC_OnbPhase")
	return st == "fight" or st == "break" or st == "intro" or st == "finisher" or player:GetAttribute("CC_UIBlock") == true
		or (onb ~= nil and onb ~= "")                    -- Einstieg (Editor, Story, Tutorial) erst abschliessen
end

local function banner(belt)
	local gui = Instance.new("ScreenGui"); gui.Name = "CC_BeltAward"; gui.IgnoreGuiInset = true; gui.DisplayOrder = 70; gui.ResetOnSpawn = false
	local bg = Instance.new("Frame"); bg.Size = UDim2.fromScale(1, 1); bg.BackgroundColor3 = Color3.new(0, 0, 0); bg.BackgroundTransparency = 1; bg.BorderSizePixel = 0; bg.Parent = gui
	local card = Instance.new("Frame"); card.AnchorPoint = Vector2.new(0.5, 0.5); card.Position = UDim2.fromScale(0.5, 0.42)
	card.Size = UDim2.fromOffset(620, 230); card.BackgroundColor3 = Color3.fromRGB(14, 14, 18); card.BorderSizePixel = 0; card.Parent = bg
	Instance.new("UICorner", card).CornerRadius = UDim.new(0, 12)
	local st = Instance.new("UIStroke", card); st.Thickness = 3; st.Color = Color3.fromRGB(232, 182, 90)
	local sc = Instance.new("UIScale", card); sc.Scale = 0.6
	local function label(text, y, size, font, color)
		local l = Instance.new("TextLabel"); l.BackgroundTransparency = 1; l.AnchorPoint = Vector2.new(0.5, 0); l.Position = UDim2.new(0.5, 0, 0, y)
		l.Size = UDim2.new(1, -40, 0, size + 8); l.Font = font; l.TextSize = size; l.TextColor3 = color; l.Text = text; l.TextWrapped = true; l.Parent = card
		return l
	end
	label("NEW BELT EARNED", 22, 20, Enum.Font.GothamBold, Color3.fromRGB(232, 182, 90))
	local title = label(string.upper(belt.name), 56, 44, Enum.Font.GothamBlack, Color3.new(1, 1, 1))
	local g = Instance.new("UIGradient"); g.Rotation = 90
	g.Color = ColorSequence.new(Color3.fromRGB(255, 231, 160), Color3.fromRGB(200, 137, 30)); g.Parent = title
	local why = belt.kind == "style" and ("Signature mastered: " .. (belt.sigName or "")) or ("Career title: " .. (belt.title or belt.name))
	label(why, 118, 18, Enum.Font.GothamMedium, Color3.fromRGB(200, 204, 212))
	label("Wear it: Menu (M) → MY FIGHTER → BELT", 160, 16, Enum.Font.GothamMedium, Color3.fromRGB(160, 162, 174))
	local swatch = Instance.new("Frame"); swatch.AnchorPoint = Vector2.new(0.5, 0); swatch.Position = UDim2.new(0.5, 0, 0, 200)
	swatch.Size = UDim2.fromOffset(180, 8); swatch.BorderSizePixel = 0; swatch.BackgroundColor3 = belt.plate or belt.color; swatch.Parent = card
	gui.Parent = player:WaitForChild("PlayerGui")
	local sfx = game:GetService("SoundService"):FindFirstChild("CC_Sounds")
	if sfx and sfx:FindFirstChild("Bell") then local s = sfx.Bell:Clone(); s.Parent = gui; s:Play() end
	TweenService:Create(bg, TweenInfo.new(0.3), { BackgroundTransparency = 0.45 }):Play()
	TweenService:Create(sc, TweenInfo.new(0.45, Enum.EasingStyle.Back), { Scale = 1 }):Play()
	task.wait(4.2)
	TweenService:Create(bg, TweenInfo.new(0.4), { BackgroundTransparency = 1 }):Play()
	TweenService:Create(sc, TweenInfo.new(0.3), { Scale = 0.01 }):Play()
	task.wait(0.45)
	gui:Destroy()
end

local function pump()
	if showing then return end
	showing = true
	task.spawn(function()
		while #queue > 0 do
			while busy() do task.wait(0.5) end
			banner(table.remove(queue, 1))
			task.wait(0.4)
		end
		showing = false
	end)
end

local function check()
	if not known then return end
	for name, belt in pairs(unlockedSet()) do
		if not known[name] then known[name] = true; table.insert(queue, belt) end
	end
	if #queue > 0 then pump() end
end

-- Start: Profil abwarten (CC_Level wird beim Laden gesetzt), dann den Ist-Stand merken
task.spawn(function()
	local t0 = os.clock()
	while player:GetAttribute("CC_Level") == nil and os.clock() - t0 < 30 do task.wait(0.25) end
	task.wait(2)
	known = {}
	for name in pairs(unlockedSet()) do known[name] = true end
end)
for _, attr in ipairs({ "CC_CareerWins", "CC_SigUnlocked" }) do
	player:GetAttributeChangedSignal(attr):Connect(function() task.defer(check) end)
end
