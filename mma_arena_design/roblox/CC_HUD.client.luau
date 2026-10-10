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
hint.Size = UDim2.fromOffset(1000, 24)
hint.BackgroundTransparency = 1
hint.Font = Enum.Font.Gotham
hint.TextSize = 16
hint.TextColor3 = Color3.new(1, 1, 1)
hint.TextStrokeTransparency = 0.5
hint.Text = "WASD laufen · LMB Jab · RMB Cross · Q Haken · R Uppercut · C Low Kick · F Block/Sprawl · E Takedown · Leertaste Aufstehen"
hint.Parent = gui

game:GetService("RunService").RenderStepped:Connect(function()
	local char = player.Character
	local hum = char and char:FindFirstChildOfClass("Humanoid")
	if hum then myFill.Size = UDim2.fromScale(math.clamp(hum.Health / hum.MaxHealth, 0, 1), 1) end
	local dummy = workspace:FindFirstChild("CC_TrainingDummy")
	local dh = dummy and dummy:FindFirstChildOfClass("Humanoid")
	if dh then foeFill.Size = UDim2.fromScale(math.clamp(dh.Health / dh.MaxHealth, 0, 1), 1) end
	ko.Visible = (char and char:GetAttribute("CC_KO")) or (dummy and dummy:GetAttribute("CC_KO")) or false
end)
