-- CC_LoadingScreen
-- LocalScript in ReplicatedFirst ablegen.
-- Einmaliger Ladebildschirm im rot-schwarzen Stil von Cage Champions.
-- Die Animation zeigt den Startzustand und wird bei Entfernung sauber beendet.

local Players = game:GetService("Players")
local ReplicatedFirst = game:GetService("ReplicatedFirst")
local TweenService = game:GetService("TweenService")

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

if playerGui:FindFirstChild("CC_LoadingScreen") then
	return
end

local colors = {
	background = Color3.fromRGB(11, 11, 14),
	bottom = Color3.fromRGB(139, 26, 26),
	red = Color3.fromRGB(224, 36, 54),
	white = Color3.fromRGB(248, 248, 250),
	gray = Color3.fromRGB(160, 162, 174),
	track = Color3.fromRGB(43, 43, 51),
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
surface.Position = UDim2.fromScale(0, 0)
surface.BackgroundColor3 = Color3.new(1, 1, 1)
surface.BorderSizePixel = 0
surface.GroupTransparency = 0
surface.Active = true
surface.ClipsDescendants = true
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

local topLine = Instance.new("Frame")
topLine.Name = "UpperCageLine"
topLine.AnchorPoint = Vector2.new(0.5, 0.5)
topLine.Position = UDim2.fromScale(0.5, -0.03)
topLine.Size = UDim2.new(0.3, 0, 0, 3)
topLine.BackgroundColor3 = colors.red
topLine.BorderSizePixel = 0
topLine.ZIndex = 2
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

local title = Instance.new("TextLabel")
title.Name = "Title"
title.AnchorPoint = Vector2.new(0.5, 0.5)
title.Position = UDim2.fromScale(0.5, 0.46)
title.Size = UDim2.fromScale(0.86, 0.12)
title.BackgroundTransparency = 1
title.Font = Enum.Font.GothamBlack
title.Text = "CAGE CHAMPIONS"
title.TextColor3 = colors.white
title.TextTransparency = 1
title.TextScaled = true
title.TextWrapped = false
title.TextXAlignment = Enum.TextXAlignment.Center
title.TextYAlignment = Enum.TextYAlignment.Center
title.ZIndex = 3
title.Parent = surface

do
	local constraint = Instance.new("UITextSizeConstraint")
	constraint.MinTextSize = 12
	constraint.MaxTextSize = 84
	constraint.Parent = title
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
subtitle.ZIndex = 3
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
loadingArea.Size = UDim2.new(0.76, 0, 0, 46)
loadingArea.BackgroundTransparency = 1
loadingArea.ZIndex = 3
loadingArea.Parent = surface

do
	local constraint = Instance.new("UISizeConstraint")
	constraint.MaxSize = Vector2.new(760, 46)
	constraint.Parent = loadingArea
end

local status = Instance.new("TextLabel")
status.Name = "Status"
status.Size = UDim2.new(1, 0, 0, 20)
status.BackgroundTransparency = 1
status.Font = Enum.Font.GothamMedium
status.Text = "WAITING FOR CHARACTER"
status.TextColor3 = colors.gray
status.TextSize = 11
status.TextXAlignment = Enum.TextXAlignment.Left
status.ZIndex = 3
status.Parent = loadingArea

local barTrack = Instance.new("Frame")
barTrack.Name = "ProgressTrack"
barTrack.Position = UDim2.new(0, 0, 0, 30)
barTrack.Size = UDim2.new(1, 0, 0, 5)
barTrack.BackgroundColor3 = colors.track
barTrack.BorderSizePixel = 0
barTrack.ClipsDescendants = true
barTrack.ZIndex = 3
barTrack.Parent = loadingArea

local barFill = Instance.new("Frame")
barFill.Name = "ProgressFill"
barFill.Size = UDim2.fromScale(0, 1)
barFill.BackgroundColor3 = colors.red
barFill.BorderSizePixel = 0
barFill.ZIndex = 4
barFill.Parent = barTrack

local activeTweens = {}
local progressTween = nil
local progress = 0
local characterReady = false
local disposed = false

local function tween(instance, duration, properties, direction)
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

local function setProgress(value, message)
	if disposed then
		return
	end

	status.Text = message
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

gui.Parent = playerGui

-- Der eigene Bildschirm wird vor dem Entfernen des Standardbildschirms erstellt.
ReplicatedFirst:RemoveDefaultLoadingScreen()

-- Der Balken folgt echten Meilensteinen, nicht einer erfundenen Dateiprozentzahl.
-- Oberfläche vorhanden: 10 %, Charakter vorhanden: 55 %, RootPart vorhanden: 100 %.
setProgress(0.1, "WAITING FOR CHARACTER")

task.spawn(function()
	while not disposed do
		local character = player.Character

		if character and character.Parent then
			setProgress(0.55, "PREPARING FIGHTER")

			local root = character:FindFirstChild("HumanoidRootPart")

			if root
				and root:IsA("BasePart")
				and root.Parent == character
				and player.Character == character then
				characterReady = true
				setProgress(1, "READY")
				return
			end
		end

		task.wait(0.1)
	end
end)

do
	-- Die vorhandene Einstellung reduziert die Bewegung auf ein Einblenden.
	local reduceMotion = player:GetAttribute("CC_ReduceFX") == true

	if reduceMotion then
		topLine.Position = UDim2.fromScale(0.5, 0.37)
		bottomLine.Position = UDim2.fromScale(0.5, 0.63)
		topLine.BackgroundTransparency = 1
		bottomLine.BackgroundTransparency = 1

		tween(topLine, 0.2, { BackgroundTransparency = 0 })
		local entrance = tween(bottomLine, 0.2, { BackgroundTransparency = 0 })
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

	tween(subtitle, 0.6, { TextTransparency = 0 })
	local titleEntrance = tween(title, 0.6, { TextTransparency = 0 })
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

-- Die Einblendung wird auch bei einem bereits geladenen Charakter abgeschlossen.
-- Anschließend bleibt der fertige Ladezustand eine Sekunde sichtbar.
task.wait(1)

if disposed then
	return
end

local exit = tween(surface, 0.8, { GroupTransparency = 1 })
exit.Completed:Wait()

if not disposed then
	gui:Destroy()
end
