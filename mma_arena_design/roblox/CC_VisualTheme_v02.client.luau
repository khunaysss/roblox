-- CC_VisualTheme_v02: zentraler Stil fuer bestehende native Anzeigen.
local player = game:GetService("Players").LocalPlayer
local UI = require(game.ReplicatedStorage:WaitForChild("CC_UI"))
local playerGui = player:WaitForChild("PlayerGui")
local attached = setmetatable({}, {__mode="k"})
local function attach(gui)
	if not gui:IsA("ScreenGui") or not gui.Name:match("^CC_") or gui.Name=="CC_LoadingScreen" or attached[gui] then return end
	attached[gui]=true
	for _,object in ipairs(gui:GetDescendants()) do UI.theme(object) end
	gui.DescendantAdded:Connect(function(object)
		task.defer(function() if object.Parent then UI.theme(object) end end)
	end)
end
for _,gui in ipairs(playerGui:GetChildren()) do attach(gui) end
playerGui.ChildAdded:Connect(function(gui) task.defer(attach,gui) end)
