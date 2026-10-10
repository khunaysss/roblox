-- StarterGui.CC_HUD (LocalScript in einer ScreenGui)
-- Zwei Lebensbalken oben: Spieler links (rot), Trainingsgegner rechts (blau). K.o.-Hinweis in der Mitte.
local player = game.Players.LocalPlayer
local gui = script.Parent

local function bar(name, anchorX, color, label)
	local frame = Instance.new("Frame")
	frame.Name = name
	frame.AnchorPoint = Vector2.new(anchorX, 0)
	frame.Position = UDim2.new(anchorX, anchorX == 0 and 20 or -20, 0, 20)
	frame.Size = UDim2.fromOffset(320, 26)
	frame.BackgroundColor3 = Color3.fromRGB(25, 25, 28)
	frame.BorderSizePixel = 0
	frame.Parent = gui
	local fill = Instance.new("Frame")
	fill.Name = "Fill"
	fill.AnchorPoint = Vector2.new(anchorX, 0)
	fill.Position = UDim2.fromScale(anchorX, 0)
	fill.Size = UDim2.fromScale(1, 1)
	fill.BackgroundColor3 = color
	fill.BorderSizePixel = 0
	fill.Parent = frame
	local text = Instance.new("TextLabel")
	text.BackgroundTransparency = 1
	text.Size = UDim2.fromScale(1, 1)
	text.Font = Enum.Font.GothamBold
	text.TextSize = 16
	text.TextColor3 = Color3.new(1, 1, 1)
	text.TextStrokeTransparency = 0.5
	text.Text = label
	text.Parent = frame
	return fill
end

local myFill = bar("Player", 0, Color3.fromRGB(200, 40, 50), "DU")
local foeFill = bar("Opponent", 1, Color3.fromRGB(40, 90, 200), "GEGNER")
-- Ausdauer: schmaler gelber Balken unter den Lebensbalken
local function sbar(anchorX)
	local frame = Instance.new("Frame")
	frame.AnchorPoint = Vector2.new(anchorX, 0)
	frame.Position = UDim2.new(anchorX, anchorX == 0 and 20 or -20, 0, 50)
	frame.Size = UDim2.fromOffset(320, 8); frame.BackgroundColor3 = Color3.fromRGB(25, 25, 28); frame.BorderSizePixel = 0; frame.Parent = gui
	local fill = Instance.new("Frame"); fill.AnchorPoint = Vector2.new(anchorX, 0); fill.Position = UDim2.fromScale(anchorX, 0)
	fill.Size = UDim2.fromScale(1, 1); fill.BackgroundColor3 = Color3.fromRGB(240, 200, 40); fill.BorderSizePixel = 0; fill.Parent = frame
	return fill
end
local myStam, foeStam = sbar(0), sbar(1)

local ko = Instance.new("TextLabel")
ko.AnchorPoint = Vector2.new(0.5, 0.5)
ko.Position = UDim2.fromScale(0.5, 0.35)
ko.Size = UDim2.fromOffset(400, 80)
ko.BackgroundTransparency = 1
ko.Font = Enum.Font.GothamBlack
ko.TextSize = 64
ko.TextColor3 = Color3.fromRGB(255, 220, 60)
ko.TextStrokeTransparency = 0
ko.Text = "K.O.!"
ko.Visible = false
ko.Parent = gui

local hint = Instance.new("TextLabel")
hint.AnchorPoint = Vector2.new(0.5, 1)
hint.Position = UDim2.new(0.5, 0, 1, -20)
hint.Size = UDim2.fromOffset(1200, 24)
hint.BackgroundTransparency = 1
hint.Font = Enum.Font.Gotham
hint.TextSize = 16
hint.TextColor3 = Color3.new(1, 1, 1)
hint.TextStrokeTransparency = 0.5
hint.Text = "WASD laufen · LMB Jab · RMB Cross (+Umschalt: Koerper) · Q Haken · R Uppercut · C/X/V/Z Kicks · F Block/Sprawl · E Takedown · T Ziel · Leertaste Aufstehen"
hint.Parent = gui
local HINT_STAND = hint.Text
-- Bodenkampf: Hinweise je Position und Rolle; Submission-Duell als Balken in der Mitte
local POS_NAME = { guard = "GUARD", half = "HALF GUARD", side = "SIDE CONTROL", mount = "MOUNT", back = "RUECKEN" }
local posL = Instance.new("TextLabel")
posL.AnchorPoint = Vector2.new(0.5, 1); posL.Position = UDim2.new(0.5, 0, 1, -48); posL.Size = UDim2.fromOffset(400, 30)
posL.BackgroundTransparency = 1; posL.Font = Enum.Font.GothamBlack; posL.TextSize = 24; posL.TextColor3 = Color3.fromRGB(255, 220, 60)
posL.TextStrokeTransparency = 0.3; posL.Text = ""; posL.Parent = gui
local duel = Instance.new("Frame")
duel.AnchorPoint = Vector2.new(0.5, 0.5); duel.Position = UDim2.fromScale(0.5, 0.62); duel.Size = UDim2.fromOffset(420, 22)
duel.BackgroundColor3 = Color3.fromRGB(40, 90, 200); duel.BorderSizePixel = 0; duel.Visible = false; duel.Parent = gui
local duelFill = Instance.new("Frame"); duelFill.Size = UDim2.fromScale(0.35, 1); duelFill.BackgroundColor3 = Color3.fromRGB(200, 40, 50)
duelFill.BorderSizePixel = 0; duelFill.Parent = duel
local duelL = Instance.new("TextLabel"); duelL.AnchorPoint = Vector2.new(0.5, 1); duelL.Position = UDim2.new(0.5, 0, 0, -4); duelL.Size = UDim2.fromOffset(600, 30)
duelL.BackgroundTransparency = 1; duelL.Font = Enum.Font.GothamBlack; duelL.TextSize = 24; duelL.TextColor3 = Color3.new(1, 1, 1)
duelL.TextStrokeTransparency = 0.2; duelL.Parent = duel
local function groundHint(char)
	local role, pos = char:GetAttribute("CC_Wrestle"), char:GetAttribute("CC_GroundPos")
	if not role or not pos then return nil end
	if role == "top" then
		local t = {}
		if pos ~= "back" then table.insert(t, "E Position verbessern") end
		if pos == "guard" or pos == "mount" then table.insert(t, "LMB Schlag") end
		if pos == "mount" or pos == "back" then table.insert(t, "Q Submission") end
		table.insert(t, "F Konter"); if pos == "guard" then table.insert(t, "Leertaste Aufstehen") end
		return table.concat(t, " · ")
	end
	return (pos == "guard" and "Leertaste Aufstehen" or "Leertaste Befreien") .. " · F Konter (wenn der Gegner die Position wechselt)"
end

-- Rundenanzeige oben mittig: Runde, Zeit, Punkte; grosses Banner in der Mitte
local match = game.ReplicatedStorage:WaitForChild("CC_MatchState", 10)
local clock = Instance.new("Frame")
clock.AnchorPoint = Vector2.new(0.5, 0); clock.Position = UDim2.new(0.5, 0, 0, 14); clock.Size = UDim2.fromOffset(190, 58)
clock.BackgroundColor3 = Color3.fromRGB(20, 20, 24); clock.BackgroundTransparency = 0.15; clock.BorderSizePixel = 0; clock.Parent = gui
local function label(parent, y, h, size, font)
	local l = Instance.new("TextLabel"); l.BackgroundTransparency = 1; l.Position = UDim2.new(0, 0, 0, y); l.Size = UDim2.new(1, 0, 0, h)
	l.Font = font; l.TextSize = size; l.TextColor3 = Color3.new(1, 1, 1); l.Parent = parent; return l
end
local roundL = label(clock, 2, 18, 14, Enum.Font.GothamBold)
local timeL = label(clock, 18, 26, 26, Enum.Font.GothamBlack)
local scoreL = label(clock, 42, 14, 12, Enum.Font.Gotham); scoreL.TextColor3 = Color3.fromRGB(200, 200, 205)
local banner = Instance.new("TextLabel")
banner.AnchorPoint = Vector2.new(0.5, 0.5); banner.Position = UDim2.fromScale(0.5, 0.3); banner.Size = UDim2.fromOffset(700, 90)
banner.BackgroundTransparency = 1; banner.Font = Enum.Font.GothamBlack; banner.TextSize = 72
banner.TextColor3 = Color3.fromRGB(255, 255, 255); banner.TextStrokeTransparency = 0; banner.Parent = gui
local bannerSub = Instance.new("TextLabel")
bannerSub.AnchorPoint = Vector2.new(0.5, 0); bannerSub.Position = UDim2.new(0.5, 0, 0.3, 46); bannerSub.Size = UDim2.fromOffset(700, 36)
bannerSub.BackgroundTransparency = 1; bannerSub.Font = Enum.Font.GothamBold; bannerSub.TextSize = 26
bannerSub.TextColor3 = Color3.fromRGB(255, 220, 60); bannerSub.TextStrokeTransparency = 0.3; bannerSub.Parent = gui

game:GetService("RunService").RenderStepped:Connect(function()
	local char = player.Character
	local hum = char and char:FindFirstChildOfClass("Humanoid")
	if hum then myFill.Size = UDim2.fromScale(math.clamp(hum.Health / hum.MaxHealth, 0, 1), 1) end
	-- Gegner = CC_Opponent (Kampf-System); ohne Kampf: Lobby (nur Uhr/Banner fuer Zuschauer)
	local oppName = char and char:GetAttribute("CC_Opponent")
	local dummy = oppName and workspace:FindFirstChild(oppName)
	local inMatch = dummy ~= nil
	for _, b in ipairs({ myFill.Parent, foeFill.Parent, myStam.Parent, foeStam.Parent }) do b.Visible = inMatch end
	foeFill.Parent:FindFirstChildOfClass("TextLabel").Text = dummy and (dummy == workspace:FindFirstChild("CC_TrainingDummy") and "GEGNER" or string.upper(dummy.Name)) or "GEGNER"
	local dh = dummy and dummy:FindFirstChildOfClass("Humanoid")
	if dh then foeFill.Size = UDim2.fromScale(math.clamp(dh.Health / dh.MaxHealth, 0, 1), 1) end
	ko.Visible = (char and char:GetAttribute("CC_KO")) or (dummy and dummy:GetAttribute("CC_KO")) or false
	local loser = (char and char:GetAttribute("CC_KO")) and char or dummy
	ko.Text = (loser and loser:GetAttribute("CC_LastReact") == "submission") and "SUBMISSION!" or "K.O.!"
	if char then
		myStam.Size = UDim2.fromScale(math.clamp((char:GetAttribute("CC_Stamina") or 100) / 100, 0, 1), 1)
		local tired = char:GetAttribute("CC_Tired")
		myStam.BackgroundColor3 = (tired and workspace:GetServerTimeNow() - tired < 0.4) and Color3.fromRGB(255, 80, 60) or Color3.fromRGB(240, 200, 40)
	end
	if char then
		local gh = groundHint(char)
		hint.Text = gh or (inMatch and HINT_STAND or "Lobby: Modus im Menü links wählen")
		posL.Text = gh and (POS_NAME[char:GetAttribute("CC_GroundPos")] or "") or ""
		local p = char:GetAttribute("CC_SubProgress")
		duel.Visible = p ~= nil
		if p then
			duelFill.Size = UDim2.fromScale(p, 1)
			local mine = char:GetAttribute("CC_SubRole") == "attack"
			duelL.Text = (char:GetAttribute("CC_SubName") or "SUBMISSION") .. (mine and "  –  Q haemmern!" or "  –  Leertaste haemmern!")
		end
	end
	if dummy then foeStam.Size = UDim2.fromScale(math.clamp((dummy:GetAttribute("CC_Stamina") or 100) / 100, 0, 1), 1) end
	if match then
		local st, t = match:GetAttribute("State"), match:GetAttribute("TimeLeft") or 0
		roundL.Text = st == "over" and "ENDE" or ("RUNDE " .. tostring(match:GetAttribute("Round") or 1) .. " / 3")
		timeL.Text = st == "fight" and string.format("%d:%02d", t // 60, t % 60) or (st == "break" and "PAUSE" or "--:--")
		scoreL.Text = string.format("Punkte  %d : %d", match:GetAttribute("ScoreRed") or 0, match:GetAttribute("ScoreBlue") or 0)
		banner.Text = match:GetAttribute("Banner") or ""
		-- Kaempfer sehen ihr eigenes Ergebnis; Zuschauer den Servertext ("<Name> GEWINNT")
		local me = player.Name
		local fighter = me == match:GetAttribute("RedName") or me == match:GetAttribute("BlueName")
		if st == "over" and fighter and match:GetAttribute("Winner") ~= "draw" then banner.Text = match:GetAttribute("WinnerName") == me and "SIEG" or "NIEDERLAGE" end
		local w = match:GetAttribute("Winner")
		banner.TextColor3 = (st == "over" and w == "red") and Color3.fromRGB(255, 215, 70) or (st == "over" and w == "blue") and Color3.fromRGB(120, 160, 255) or Color3.new(1, 1, 1)
		clock.Visible = st ~= "idle"
		if fighter then
			local mine, theirs = match:GetAttribute("ScoreRed") or 0, match:GetAttribute("ScoreBlue") or 0
			if me == match:GetAttribute("BlueName") then mine, theirs = theirs, mine end
			scoreL.Text = string.format("Punkte  %d : %d", mine, theirs)
		end
		bannerSub.Text = match:GetAttribute("BannerSub") or ""
		if banner.Text ~= "" then ko.Visible = false end
	end
end)
