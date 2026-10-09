-- StarterPlayer.StarterPlayerScripts.CC_Input
-- Linksklick = Jab
local UIS = game:GetService("UserInputService")
local jab = game.ReplicatedStorage:WaitForChild("CC_Jab")
UIS.InputBegan:Connect(function(input, gp)
	if gp then return end
	if input.UserInputType == Enum.UserInputType.MouseButton1 then jab:FireServer() end
end)
