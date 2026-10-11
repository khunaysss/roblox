-- StarterGui.CC_MenuGui.Menu (LocalScript in einer ScreenGui)
-- Lobby-Menue: TRAINING (gegen den Trainingsgegner) oder GEGEN SPIELER (Warteschlange, die ersten zwei kaempfen).
-- Sichtbar, solange der eigene Charakter in keinem Kampf ist (kein Attribut CC_Opponent).
-- Server: ReplicatedStorage.CC_Menu ("training" | "pvp" | "cancel"); Stand aus ReplicatedStorage.CC_MatchState und Player.CC_Queue.
local player = game.Players.LocalPlayer
local RS = game.ReplicatedStorage
local menuEvent = RS:WaitForChild("CC_Menu")
local state = RS:WaitForChild("CC_MatchState")
local gui = script.Parent
gui.ResetOnSpawn = false

local panel = Instance.new("Frame")
panel.AnchorPoint = Vector2.new(0, 0.5); panel.Position = UDim2.new(0, 24, 0.5, 0); panel.Size = UDim2.fromOffset(320, 470)
panel.BackgroundColor3 = Color3.fromRGB(18, 18, 22); panel.BackgroundTransparency = 0.12; panel.BorderSizePixel = 0; panel.Parent = gui
Instance.new("UICorner", panel).CornerRadius = UDim.new(0, 10)
local pad = Instance.new("UIPadding", panel)
pad.PaddingLeft = UDim.new(0, 18); pad.PaddingRight = UDim.new(0, 18); pad.PaddingTop = UDim.new(0, 16); pad.PaddingBottom = UDim.new(0, 16)
local list = Instance.new("UIListLayout", panel); list.Padding = UDim.new(0, 10); list.SortOrder = Enum.SortOrder.LayoutOrder

local function label(text, size, font, color, order, h)
	local l = Instance.new("TextLabel")
	l.BackgroundTransparency = 1; l.Size = UDim2.new(1, 0, 0, h or size + 8); l.Font = font; l.TextSize = size
	l.TextColor3 = color; l.Text = text; l.TextXAlignment = Enum.TextXAlignment.Left; l.TextWrapped = true; l.LayoutOrder = order
	l.Parent = panel; return l
end
local function button(text, color, order)
	local b = Instance.new("TextButton")
	b.Size = UDim2.new(1, 0, 0, 52); b.BackgroundColor3 = color; b.BorderSizePixel = 0; b.AutoButtonColor = true
	b.Font = Enum.Font.GothamBlack; b.TextSize = 22; b.TextColor3 = Color3.new(1, 1, 1); b.Text = text; b.LayoutOrder = order
	Instance.new("UICorner", b).CornerRadius = UDim.new(0, 8)
	b.Parent = panel; return b
end
label("CAGE CHAMPIONS", 30, Enum.Font.GothamBlack, Color3.fromRGB(255, 220, 60), 1, 36)
local trainingB = button("TRAINING", Color3.fromRGB(40, 90, 200), 2)
local pvpB = button("GEGEN SPIELER", Color3.fromRGB(200, 40, 50), 3)
local cancelB = button("ABBRECHEN", Color3.fromRGB(70, 70, 78), 4)
local status = label("", 16, Enum.Font.GothamBold, Color3.fromRGB(220, 220, 225), 5, 44)
-- Profil (CC_Profile): Level, XP-Balken, Werte mit Trainingspunkten, Bilanz
local levelL = label("", 18, Enum.Font.GothamBlack, Color3.fromRGB(255, 220, 60), 6, 22)
local function bar(order, color)
	local f = Instance.new("Frame"); f.Size = UDim2.new(1, 0, 0, 8); f.BackgroundColor3 = Color3.fromRGB(40, 40, 46); f.BorderSizePixel = 0; f.LayoutOrder = order; f.Parent = panel
	local fill = Instance.new("Frame"); fill.Size = UDim2.fromScale(0, 1); fill.BackgroundColor3 = color; fill.BorderSizePixel = 0; fill.Parent = f
	return fill
end
local xpFill = bar(7, Color3.fromRGB(255, 200, 40))
local STAT_NAMES = { { "Power", "Schlagkraft" }, { "Cardio", "Kondition" }, { "Wrestling", "Ringen" }, { "Grappling", "Bodenkampf" } }
local statRows = {}
for i, s_ in ipairs(STAT_NAMES) do
	local l = label("", 14, Enum.Font.GothamBold, Color3.fromRGB(220, 220, 225), 7 + i * 2, 16)
	statRows[s_[1]] = { l, bar(8 + i * 2, Color3.fromRGB(80, 150, 255)), s_[2] }
end
local recordL = label("", 14, Enum.Font.Gotham, Color3.fromRGB(190, 190, 198), 20, 18)

trainingB.Activated:Connect(function() menuEvent:FireServer("training") end)
pvpB.Activated:Connect(function() menuEvent:FireServer("pvp") end)
cancelB.Activated:Connect(function() menuEvent:FireServer("cancel") end)

game:GetService("RunService").RenderStepped:Connect(function()
	local char = player.Character
	local inMatch = char and char:GetAttribute("CC_Opponent") ~= nil
	panel.Visible = not inMatch
	if inMatch then return end
	local q = player:GetAttribute("CC_Queue")
	local mode, st = state:GetAttribute("Mode") or "", state:GetAttribute("State") or "idle"
	local busy = mode ~= ""
	trainingB.Visible = q == nil; pvpB.Visible = q == nil; cancelB.Visible = q ~= nil
	local lines = {}
	if busy then
		table.insert(lines, ("Kampf läuft: %s gegen %s"):format(state:GetAttribute("RedName") or "?", state:GetAttribute("BlueName") or "?"))
	end
	if q == "pvp" then
		local n = state:GetAttribute("QueuePvp") or 0
		table.insert(lines, n >= 2 and "Gegner gefunden – du bist als Nächstes dran." or "Warte auf einen Gegner … (" .. n .. "/2)")
	elseif q == "training" then
		table.insert(lines, busy and "Training startet nach diesem Kampf." or "Training startet …")
	elseif not busy then
		table.insert(lines, "Wähle einen Modus.")
	end
	status.Text = table.concat(lines, "\n")
	local lv, xp, nx = player:GetAttribute("CC_Level") or 1, player:GetAttribute("CC_XP") or 0, player:GetAttribute("CC_XPNext") or 100
	levelL.Text = ("LEVEL %d   ·   %d / %d XP"):format(lv, xp, nx)
	xpFill.Size = UDim2.fromScale(math.clamp(xp / nx, 0, 1), 1)
	for key, row in pairs(statRows) do
		local v, tp = player:GetAttribute("CC_" .. key) or 0, player:GetAttribute("CC_" .. key .. "TP") or 0
		row[1].Text = ("%s  %d / 20"):format(row[3], v)
		row[2].Size = UDim2.fromScale(math.clamp((v + tp / 10) / 20, 0, 1), 1)
	end
	recordL.Text = ("Bilanz %d-%d   ·   K.o. %d   ·   Sub %d%s"):format(player:GetAttribute("CC_Wins") or 0, player:GetAttribute("CC_Losses") or 0,
		player:GetAttribute("CC_KOs") or 0, player:GetAttribute("CC_Subs") or 0, player:GetAttribute("CC_ProfileSaved") and "" or "  (nicht gespeichert)")
end)
