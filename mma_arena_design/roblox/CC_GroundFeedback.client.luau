-- Sichtbares Boden-Kampf-Feedback fuer Desktop
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local player = Players.LocalPlayer

local gui = Instance.new("ScreenGui")
gui.Name = "CC_GroundFeedback"
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = true
gui.DisplayOrder = 24
gui.Parent = player:WaitForChild("PlayerGui")

local panel = Instance.new("Frame")
panel.Name = "Panel"
panel.AnchorPoint = Vector2.new(0.5, 0.5)
panel.Position = UDim2.fromScale(0.5, 0.78)
panel.Size = UDim2.fromOffset(430, 82)
panel.BackgroundColor3 = Color3.fromRGB(10, 17, 25)
panel.BackgroundTransparency = 0.08
panel.BorderSizePixel = 0
panel.Visible = false
panel.Parent = gui
Instance.new("UICorner", panel).CornerRadius = UDim.new(0, 8)

local stroke = Instance.new("UIStroke")
stroke.Color = Color3.fromRGB(67, 82, 99)
stroke.Thickness = 2
stroke.Transparency = 0.1
stroke.Parent = panel

local accent = Instance.new("Frame")
accent.Name = "Accent"
accent.Size = UDim2.new(0, 5, 1, 0)
accent.BackgroundColor3 = Color3.fromRGB(255, 45, 61)
accent.BorderSizePixel = 0
accent.Parent = panel
Instance.new("UICorner", accent).CornerRadius = UDim.new(0, 8)

local title = Instance.new("TextLabel")
title.Name = "Title"
title.Position = UDim2.fromOffset(22, 10)
title.Size = UDim2.new(1, -44, 0, 27)
title.BackgroundTransparency = 1
title.Font = Enum.Font.GothamBold
title.TextSize = 19
title.TextColor3 = Color3.fromRGB(245, 248, 252)
title.TextXAlignment = Enum.TextXAlignment.Left
title.Parent = panel

local detail = Instance.new("TextLabel")
detail.Name = "Detail"
detail.Position = UDim2.fromOffset(22, 37)
detail.Size = UDim2.new(1, -44, 0, 19)
detail.BackgroundTransparency = 1
detail.Font = Enum.Font.GothamMedium
detail.TextSize = 13
detail.TextColor3 = Color3.fromRGB(173, 187, 205)
detail.TextXAlignment = Enum.TextXAlignment.Left
detail.Parent = panel

local track = Instance.new("Frame")
track.Name = "ProgressTrack"
track.Position = UDim2.new(0, 22, 1, -15)
track.Size = UDim2.new(1, -44, 0, 5)
track.BackgroundColor3 = Color3.fromRGB(48, 61, 77)
track.BorderSizePixel = 0
track.Parent = panel
Instance.new("UICorner", track).CornerRadius = UDim.new(1, 0)

local fill = Instance.new("Frame")
fill.Name = "Fill"
fill.Size = UDim2.fromScale(0, 1)
fill.BackgroundColor3 = Color3.fromRGB(255, 45, 61)
fill.BorderSizePixel = 0
fill.Parent = track
Instance.new("UICorner", fill).CornerRadius = UDim.new(1, 0)

local sizeLimit = Instance.new("UISizeConstraint")
sizeLimit.MinSize = Vector2.new(330, 76)
sizeLimit.MaxSize = Vector2.new(480, 88)
sizeLimit.Parent = panel

local names = {
	guard = "GUARD",
	half = "HALF GUARD",
	side = "SIDE CONTROL",
	mount = "MOUNT",
	back = "BACK CONTROL",
	stand = "STAND",
}
local function positionName(value)
	return names[value] or string.upper(tostring(value or ""))
end

RunService.RenderStepped:Connect(function()
	local char = player.Character
	if not char then panel.Visible = false return end
	local role = char:GetAttribute("CC_Wrestle")
	if not role or role == "shoot" or role == "defend" then panel.Visible = false return end   -- waehrend des Takedowns (auch Eagle Slam) noch keine Boden-Hinweise
	panel.Visible = true

	local now = workspace:GetServerTimeNow()
	local counterUntil = char:GetAttribute("CC_CounterUntil")
	if counterUntil and counterUntil > now then
		local remaining = math.clamp((counterUntil - now) / 0.4, 0, 1)
		title.Text = "F  ·  JETZT KONTERN"
		detail.Text = char:GetAttribute("CC_CounterLabel") or "ANGRIFF ABWEHREN"
		fill.Size = UDim2.fromScale(remaining, 1)
		fill.BackgroundColor3 = Color3.fromRGB(255, 196, 46)
		accent.BackgroundColor3 = Color3.fromRGB(255, 196, 46)
		stroke.Color = Color3.fromRGB(255, 196, 46)
		panel.BackgroundTransparency = 0
		return
	end

	local action = char:GetAttribute("CC_GroundAction")
	local started = char:GetAttribute("CC_GroundActionStart")
	local duration = char:GetAttribute("CC_GroundActionDuration")
	if action and started and duration then
		local progress = math.clamp((now - started) / math.max(duration, 0.1), 0, 1)
		title.Text = action
		detail.Text = positionName(char:GetAttribute("CC_GroundActionFrom")) .. "  →  " .. positionName(char:GetAttribute("CC_GroundActionTo"))
		fill.Size = UDim2.fromScale(progress, 1)
	else
		local pos = positionName(char:GetAttribute("CC_GroundPos"))
		if role == "bottom" then
			title.Text = "SPACE  ·  BEFREIEN & AUFSTEHEN"
			detail.Text = pos .. "  ·  F kontert einen Positionswechsel"
		else
			title.Text = "E  ·  POSITION  /  SPACE  ·  AUFSTEHEN"
			detail.Text = pos .. "  ·  F kontert eine Befreiung"
		end
		fill.Size = UDim2.fromScale(0, 1)
	end
	fill.BackgroundColor3 = Color3.fromRGB(255, 45, 61)
	accent.BackgroundColor3 = Color3.fromRGB(255, 45, 61)
	stroke.Color = Color3.fromRGB(67, 82, 99)
	panel.BackgroundTransparency = 0.08
end)
