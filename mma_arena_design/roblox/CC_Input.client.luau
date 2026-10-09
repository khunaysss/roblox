-- StarterPlayer.StarterPlayerScripts.CC_Input
-- Steuerung: WASD laufen · Linksklick Jab · Rechtsklick Cross · Q Haken · R Aufwaertshaken · C Low Kick · F halten = Block
-- Der Kaempfer schaut automatisch zum naechsten Gegner (bis 40 Studs); sonst dreht er sich in Laufrichtung.
local Players = game:GetService("Players")
local UIS = game:GetService("UserInputService")
local RunService = game:GetService("RunService")
local action = game.ReplicatedStorage:WaitForChild("CC_Action")
local block = game.ReplicatedStorage:WaitForChild("CC_Block")
local player = Players.LocalPlayer

local KEYS = {
	[Enum.UserInputType.MouseButton1] = "jab",
	[Enum.UserInputType.MouseButton2] = "cross",
	[Enum.KeyCode.Q] = "hook",
	[Enum.KeyCode.R] = "uppercut",
	[Enum.KeyCode.C] = "lowkick",
}
UIS.InputBegan:Connect(function(input, gp)
	if gp then return end
	local move = KEYS[input.UserInputType] or KEYS[input.KeyCode]
	if move then action:FireServer(move) end
	if input.KeyCode == Enum.KeyCode.F then block:FireServer(true) end
end)
UIS.InputEnded:Connect(function(input)
	if input.KeyCode == Enum.KeyCode.F then block:FireServer(false) end
end)

local function opponent(root)
	local best, bestDist = nil, 40
	for _, m in ipairs(workspace:GetChildren()) do
		local h = m:IsA("Model") and m ~= player.Character and m:FindFirstChildOfClass("Humanoid")
		local r = h and m:FindFirstChild("HumanoidRootPart")
		if r and not m:GetAttribute("CC_KO") then
			local d = (r.Position - root.Position).Magnitude
			if d < bestDist then best, bestDist = r, d end
		end
	end
	return best
end

RunService.RenderStepped:Connect(function()
	local char = player.Character
	local hum = char and char:FindFirstChildOfClass("Humanoid")
	local root = char and char:FindFirstChild("HumanoidRootPart")
	if not (hum and root) then return end
	local target = (not char:GetAttribute("CC_KO")) and opponent(root)
	hum.AutoRotate = target == nil
	if target then
		local p = Vector3.new(target.Position.X, root.Position.Y, target.Position.Z)
		if (p - root.Position).Magnitude > 0.5 then
			root.CFrame = CFrame.lookAt(root.Position, p)
		end
	end
end)
