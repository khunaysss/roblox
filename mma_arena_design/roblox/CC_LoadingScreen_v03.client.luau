-- CC_LoadingScreen (v02)
-- LocalScript in ReplicatedFirst ablegen.
-- Vollstaendig aus Frames und Text aufgebaut; keine Uploads erforderlich.
-- Ablauf: Oberflaeche -> Charakter laedt -> rote Linie fegt quer ueber den Schirm -> Abblende -> Spiel uebernimmt.

local Players = game:GetService("Players")
local ReplicatedFirst = game:GetService("ReplicatedFirst")
local TweenService = game:GetService("TweenService")

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

if playerGui:FindFirstChild("CC_LoadingScreen") then
	return
end

local colors = {
	background = Color3.fromRGB(21, 23, 28),
	bottom = Color3.fromRGB(139, 26, 26),
	red = Color3.fromRGB(224, 36, 54),
	ring = Color3.fromRGB(220, 36, 48),
	grid = Color3.fromRGB(112, 114, 122),
	gray = Color3.fromRGB(166, 169, 180),
	track = Color3.fromRGB(58, 61, 70),
	goldTop = Color3.fromRGB(255, 231, 160),
	goldBottom = Color3.fromRGB(200, 137, 30),
	goldBorder = Color3.fromRGB(232, 182, 90),
	shadow = Color3.fromRGB(90, 58, 0),
	fillStart = Color3.fromRGB(255, 179, 71),
	fillEnd = Color3.fromRGB(224, 36, 47),
}

local gui = Instance.new("ScreenGui")
gui.Name = "CC_LoadingScreen"
gui.IgnoreGuiInset = true
gui.ResetOnSpawn = false
gui.DisplayOrder = 10000
gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling

local surface = Instance.new("CanvasGroup")
surface.Name = "Surface"
surface.Size = UDim2.fromScale(1, 1)
surface.BackgroundColor3 = Color3.new(1, 1, 1)
surface.BorderSizePixel = 0
surface.GroupTransparency = 0
surface.Active = true
surface.ClipsDescendants = true
surface.ZIndex = 1
surface.Parent = gui

do
	local gradient = Instance.new("UIGradient")
	gradient.Name = "ArenaGradient"
	gradient.Rotation = 90
	gradient.Color = ColorSequence.new({
		ColorSequenceKeypoint.new(0, colors.background),
		ColorSequenceKeypoint.new(0.55, colors.background),
		ColorSequenceKeypoint.new(0.8, Color3.fromRGB(44, 15, 20)),
		ColorSequenceKeypoint.new(1, colors.bottom),
	})
	gradient.Parent = surface
end

do
	-- Acht dezente Streben bilden das Gitter hinter dem Titel.
	local grid = Instance.new("Frame")
	grid.Name = "CageGrid"
	grid.Size = UDim2.fromScale(1, 1)
	grid.BackgroundTransparency = 1
	grid.ClipsDescendants = true
	grid.ZIndex = 2
	grid.Parent = surface

	for index = 1, 8 do
		local line = Instance.new("Frame")
		line.Name = "GridLine_" .. index
		line.AnchorPoint = Vector2.new(0.5, 0.5)
		line.Position = UDim2.fromScale(index / 9, 0.5)
		line.Size = UDim2.new(0, 1, 1, 0)
		line.BackgroundColor3 = colors.grid
		line.BackgroundTransparency = 0.85
		line.BorderSizePixel = 0
		line.ZIndex = 2
		line.Parent = grid

		local gradient = Instance.new("UIGradient")
		gradient.Rotation = 90
		gradient.Transparency = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 1),
			NumberSequenceKeypoint.new(0.2, 0),
			NumberSequenceKeypoint.new(0.8, 0),
			NumberSequenceKeypoint.new(1, 1),
		})
		gradient.Parent = line
	end

	local ringEdge = Instance.new("Frame")
	ringEdge.Name = "RingEdge"
	ringEdge.AnchorPoint = Vector2.new(0, 1)
	ringEdge.Position = UDim2.fromScale(0, 1)
	ringEdge.Size = UDim2.new(1, 0, 0, 6)
	ringEdge.BackgroundColor3 = colors.ring
	ringEdge.BorderSizePixel = 0
	ringEdge.ZIndex = 3
	ringEdge.Parent = surface
end

local topLine = Instance.new("Frame")
topLine.Name = "UpperCageLine"
topLine.AnchorPoint = Vector2.new(0.5, 0.5)
topLine.Position = UDim2.fromScale(0.5, -0.03)
topLine.Size = UDim2.new(0.3, 0, 0, 3)
topLine.BackgroundColor3 = colors.red
topLine.BorderSizePixel = 0
topLine.ZIndex = 4
topLine.Parent = surface

local bottomLine = topLine:Clone()
bottomLine.Name = "LowerCageLine"
bottomLine.Position = UDim2.fromScale(0.5, 1.03)
bottomLine.Parent = surface

do
	for _, line in ipairs({ topLine, bottomLine }) do
		local constraint = Instance.new("UISizeConstraint")
		constraint.MaxSize = Vector2.new(430, 3)
		constraint.Parent = line

		local gradient = Instance.new("UIGradient")
		gradient.Transparency = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 1),
			NumberSequenceKeypoint.new(0.16, 0),
			NumberSequenceKeypoint.new(0.84, 0),
			NumberSequenceKeypoint.new(1, 1),
		})
		gradient.Parent = line
	end
end

local titleShadow = Instance.new("TextLabel")
titleShadow.Name = "TitleShadow"
titleShadow.AnchorPoint = Vector2.new(0.5, 0.5)
titleShadow.Position = UDim2.new(0.5, 3, 0.46, 3)
titleShadow.Size = UDim2.fromScale(0.86, 0.12)
titleShadow.BackgroundTransparency = 1
titleShadow.Font = Enum.Font.GothamBlack
titleShadow.Text = "CAGE CHAMPIONS"
titleShadow.TextColor3 = colors.shadow
titleShadow.TextTransparency = 1
titleShadow.TextScaled = true
titleShadow.TextWrapped = false
titleShadow.TextXAlignment = Enum.TextXAlignment.Center
titleShadow.TextYAlignment = Enum.TextYAlignment.Center
titleShadow.ZIndex = 5
titleShadow.Parent = surface

do
	local constraint = Instance.new("UITextSizeConstraint")
	constraint.MinTextSize = 12
	constraint.MaxTextSize = 84
	constraint.Parent = titleShadow
end

local title = titleShadow:Clone()
title.Name = "Title"
title.Position = UDim2.fromScale(0.5, 0.46)
title.TextColor3 = Color3.new(1, 1, 1)
title.ZIndex = 6
title.Parent = surface

local titleStroke = Instance.new("UIStroke")
titleStroke.Name = "TitleOutline"
titleStroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual
titleStroke.Color = Color3.new(0, 0, 0)
titleStroke.Thickness = 2
titleStroke.Transparency = 1
titleStroke.LineJoinMode = Enum.LineJoinMode.Round
titleStroke.Parent = title

do
	local gradient = Instance.new("UIGradient")
	gradient.Name = "GoldGradient"
	gradient.Rotation = 90
	gradient.Color = ColorSequence.new({
		ColorSequenceKeypoint.new(0, colors.goldTop),
		ColorSequenceKeypoint.new(1, colors.goldBottom),
	})
	gradient.Parent = title
end

local subtitle = Instance.new("TextLabel")
subtitle.Name = "Subtitle"
subtitle.AnchorPoint = Vector2.new(0.5, 0.5)
subtitle.Position = UDim2.fromScale(0.5, 0.55)
subtitle.Size = UDim2.fromScale(0.8, 0.045)
subtitle.BackgroundTransparency = 1
subtitle.Font = Enum.Font.Gotham
subtitle.Text = "Entering the cage..."
subtitle.TextColor3 = colors.gray
subtitle.TextTransparency = 1
subtitle.TextScaled = true
subtitle.TextWrapped = false
subtitle.ZIndex = 6
subtitle.Parent = surface

do
	local constraint = Instance.new("UITextSizeConstraint")
	constraint.MinTextSize = 10
	constraint.MaxTextSize = 22
	constraint.Parent = subtitle
end

local loadingArea = Instance.new("Frame")
loadingArea.Name = "LoadingArea"
loadingArea.AnchorPoint = Vector2.new(0.5, 1)
loadingArea.Position = UDim2.fromScale(0.5, 0.91)
loadingArea.Size = UDim2.new(0.76, 0, 0, 16)
loadingArea.BackgroundTransparency = 1
loadingArea.ZIndex = 6
loadingArea.Parent = surface

do
	local constraint = Instance.new("UISizeConstraint")
	constraint.MaxSize = Vector2.new(760, 16)
	constraint.Parent = loadingArea
end

local barTrack = Instance.new("Frame")
barTrack.Name = "ProgressTrack"
barTrack.AnchorPoint = Vector2.new(0, 0.5)
barTrack.Position = UDim2.fromScale(0, 0.5)
barTrack.Size = UDim2.new(1, 0, 0, 5)
barTrack.BackgroundColor3 = colors.track
barTrack.BorderSizePixel = 0
barTrack.ZIndex = 6
barTrack.Parent = loadingArea

do
	local stroke = Instance.new("UIStroke")
	stroke.Name = "GoldBorder"
	stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	stroke.Color = colors.goldBorder
	stroke.Thickness = 1
	stroke.Parent = barTrack
end

local barClip = Instance.new("Frame")
barClip.Name = "FillClip"
barClip.Size = UDim2.fromScale(1, 1)
barClip.BackgroundTransparency = 1
barClip.ClipsDescendants = true
barClip.ZIndex = 7
barClip.Parent = barTrack

local barFill = Instance.new("Frame")
barFill.Name = "ProgressFill"
barFill.Size = UDim2.fromScale(0, 1)
barFill.BackgroundColor3 = Color3.new(1, 1, 1)
barFill.BorderSizePixel = 0
barFill.ZIndex = 7
barFill.Parent = barClip

do
	local gradient = Instance.new("UIGradient")
	gradient.Name = "FillGradient"
	gradient.Rotation = 0
	gradient.Color = ColorSequence.new({
		ColorSequenceKeypoint.new(0, colors.fillStart),
		ColorSequenceKeypoint.new(1, colors.fillEnd),
	})
	gradient.Parent = barFill
end

-- Rote Lichtlinie fuer den Uebergang (startet ausserhalb links, unsichtbar).
local sweep = Instance.new("Frame")
sweep.Name = "TransitionSweep"
sweep.AnchorPoint = Vector2.new(0.5, 0)
sweep.Position = UDim2.fromScale(-0.4, 0)
sweep.Size = UDim2.new(0.22, 0, 1, 0)
sweep.BackgroundColor3 = colors.red
sweep.BackgroundTransparency = 1
sweep.BorderSizePixel = 0
sweep.ZIndex = 9
sweep.Parent = surface

do
	local gradient = Instance.new("UIGradient")
	gradient.Rotation = 0
	gradient.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 1),
		NumberSequenceKeypoint.new(0.5, 0.15),
		NumberSequenceKeypoint.new(1, 1),
	})
	gradient.Parent = sweep
end

local activeTweens = {}
local progressTween = nil
local progress = 0
local characterReady = false
local disposed = false

local function tween(instance, duration, properties, direction)
	if (player:GetAttribute("CC_ReduceMotion") or player:GetAttribute("CC_ReduceFX")) and properties.Position then duration = 0 end
	local animation = TweenService:Create(
		instance,
		TweenInfo.new(
			duration,
			Enum.EasingStyle.Quad,
			direction or Enum.EasingDirection.Out
		),
		properties
	)

	table.insert(activeTweens, animation)
	animation:Play()
	return animation
end

local function setProgress(value)
	if disposed then
		return
	end

	value = math.clamp(value, 0, 1)

	if value <= progress then
		return
	end

	progress = value

	if progressTween then
		progressTween:Cancel()
	end

	progressTween = tween(barFill, 0.2, {
		Size = UDim2.fromScale(progress, 1),
	})
end

gui.Destroying:Connect(function()
	disposed = true

	for _, animation in ipairs(activeTweens) do
		animation:Cancel()
	end
end)

-- Flache Launch-Farben; Meilensteine und Ladebedingungen bleiben unveraendert.
surface.BackgroundColor3 = colors.background
title.TextColor3 = colors.goldBorder
barFill.BackgroundColor3 = Color3.fromRGB(224, 36, 58)
for _, item in ipairs(surface:GetDescendants()) do
	if item:IsA("UIGradient") and (item.Name == "GoldGradient" or item.Name == "ArenaGradient" or item.Name == "FillGradient") then
		item.Enabled = false
	end
end
-- Explizite responsive Schriftgroessen verhindern minimale TextScaled-Messungen beim Aufbau.
local function fitText()
	local size = workspace.CurrentCamera and workspace.CurrentCamera.ViewportSize or Vector2.new(1280, 720)
	title.TextScaled = false
	titleShadow.TextScaled = false
	subtitle.TextScaled = false
	title.TextSize = math.clamp(math.floor(math.min(size.X / 22, size.Y / 10)), 32, 84)
	titleShadow.TextSize = title.TextSize
	subtitle.TextSize = math.clamp(math.floor(size.Y / 34), 16, 22)
end
fitText()
local resizeLink = workspace.CurrentCamera and workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(fitText)
gui.Destroying:Connect(function() if resizeLink then resizeLink:Disconnect() end end)
gui.Parent = playerGui

-- Den Standardbildschirm erst nach Aufbau der eigenen Oberflaeche entfernen.
ReplicatedFirst:RemoveDefaultLoadingScreen()

-- Reale Meilensteine statt eines zeitgesteuerten Scheinfortschritts.
-- Oberflaeche vorhanden: 10 %, Charakter vorhanden: 55 %, RootPart vorhanden: 100 %.
setProgress(0.1)

task.spawn(function()
	while not disposed do
		local character = player.Character

		if character and character.Parent then
			setProgress(0.55)

			local root = character:FindFirstChild("HumanoidRootPart")

			if root
				and root:IsA("BasePart")
				and root.Parent == character
				and player.Character == character then
				characterReady = true
				setProgress(1)
				return
			end
		end

		task.wait(0.1)
	end
end)

do
	local reduceMotion = player:GetAttribute("CC_ReduceMotion") == true or player:GetAttribute("CC_ReduceFX") == true

	if reduceMotion then
		-- Bei reduzierten Effekten erscheinen die Striche ohne Fahrbewegung.
		topLine.Position = UDim2.fromScale(0.5, 0.37)
		bottomLine.Position = UDim2.fromScale(0.5, 0.63)
		topLine.BackgroundTransparency = 1
		bottomLine.BackgroundTransparency = 1

		tween(topLine, 0.2, { BackgroundTransparency = 0 })
		local entrance = tween(bottomLine, 0.2, {
			BackgroundTransparency = 0,
		})
		entrance.Completed:Wait()
	else
		tween(
			topLine,
			0.5,
			{ Position = UDim2.fromScale(0.5, 0.37) },
			Enum.EasingDirection.InOut
		)

		local entrance = tween(
			bottomLine,
			0.5,
			{ Position = UDim2.fromScale(0.5, 0.63) },
			Enum.EasingDirection.InOut
		)
		entrance.Completed:Wait()
	end

	if disposed then
		return
	end

	tween(titleShadow, 0.6, { TextTransparency = 0.35 })
	tween(titleStroke, 0.6, { Transparency = 0 })
	tween(subtitle, 0.6, { TextTransparency = 0 })

	local titleEntrance = tween(title, 0.6, {
		TextTransparency = 0,
	})
	titleEntrance.Completed:Wait()
end

if disposed then
	return
end

while not characterReady and not disposed do
	task.wait(0.1)
end

if disposed then
	return
end

-- Den fertigen Zustand eine Sekunde zeigen.
task.wait(1)

if disposed then
	return
end

-- Uebergang: rote Lichtlinie fegt quer ueber den Titel, Titel und Balken verschwinden,
-- danach blendet der ganze Schirm aus.
tween(sweep, 0.1, { BackgroundTransparency = (player:GetAttribute("CC_ReduceMotion") or player:GetAttribute("CC_ReduceFX")) and 1 or 0 })
local sweepMove = tween(sweep, 0.6, {
	Position = UDim2.fromScale(1.4, 0),
}, Enum.EasingDirection.In)

tween(title, 0.5, { TextTransparency = 1 })
tween(titleShadow, 0.5, { TextTransparency = 1 })
tween(titleStroke, 0.5, { Transparency = 1 })
tween(subtitle, 0.4, { TextTransparency = 1 })
tween(loadingArea, 0.4, { Position = UDim2.fromScale(0.5, 1.05) })

sweepMove.Completed:Wait()
if disposed then
	return
end

local exit = tween(surface, 0.7, {
	GroupTransparency = 1,
})
exit.Completed:Wait()

if not disposed then
	gui:Destroy()
end
