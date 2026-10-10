-- StarterPlayer.StarterPlayerScripts.CC_HitFX
-- Treffer-Gefuehl auf dem Bildschirm: kurzer Kamera-Ruck (abklingend) und bei eigenen Treffern ein rotes Aufblitzen.
-- Ausgeloest vom Server (ReplicatedStorage.CC_HitFX) mit Staerke 0..1 und Art: hit, stagger, ko, block, land.
local RunService = game:GetService("RunService")
local player = game.Players.LocalPlayer
local fx = game.ReplicatedStorage:WaitForChild("CC_HitFX")

local gui = Instance.new("ScreenGui")
gui.Name = "CC_HitFlash"; gui.IgnoreGuiInset = true; gui.ResetOnSpawn = false; gui.DisplayOrder = 5
gui.Parent = player:WaitForChild("PlayerGui")
local flash = Instance.new("Frame")
flash.Size = UDim2.fromScale(1, 1); flash.BackgroundColor3 = Color3.fromRGB(170, 0, 0)
flash.BackgroundTransparency = 1; flash.BorderSizePixel = 0; flash.Parent = gui

local shake, flashA = 0, 0
fx.OnClientEvent:Connect(function(strength, kind)
	shake = math.max(shake, strength)
	if kind == "hit" or kind == "stagger" or kind == "ko" then flashA = math.max(flashA, 0.25 + 0.35 * strength) end
end)

RunService:BindToRenderStep("CC_HitShake", Enum.RenderPriority.Camera.Value + 1, function(dt)
	if shake > 0.001 then
		local cam = workspace.CurrentCamera
		local a = shake * 0.035
		local t = os.clock() * 60
		cam.CFrame = cam.CFrame * CFrame.Angles(math.sin(t * 1.3) * a, math.cos(t * 1.7) * a, math.sin(t * 2.1) * a * 0.5)
		shake = shake * math.exp(-dt * 14)
	else
		shake = 0
	end
	flashA = flashA * math.exp(-dt * 9)
	flash.BackgroundTransparency = 1 - flashA
end)
