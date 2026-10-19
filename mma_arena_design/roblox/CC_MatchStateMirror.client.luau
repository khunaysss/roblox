-- StarterPlayer.StarterPlayerScripts.CC_MatchStateMirror
-- Lokaler Spiegel: ReplicatedStorage.CC_MatchState (nur auf diesem Client) = Zustand des eigenen Kampfs
-- (ReplicatedStorage.CC_Matches.<CC_MatchId>) oder Ruhezustand (CC_Matches.idle). So lesen HUD, Menue, Kamera,
-- Finisher und Tutorial weiterhin "CC_MatchState", auch wenn mehrere Kaempfe gleichzeitig laufen.
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local player = Players.LocalPlayer

local mirror = RS:FindFirstChild("CC_MatchState")
if not mirror then
	mirror = Instance.new("Folder"); mirror.Name = "CC_MatchState"; mirror.Parent = RS
end
local root = RS:WaitForChild("CC_Matches")
local source, conn

local function copyAll(src)
	local attrs = src and src:GetAttributes() or {}
	for k in pairs(mirror:GetAttributes()) do
		if attrs[k] == nil then mirror:SetAttribute(k, nil) end
	end
	for k, v in pairs(attrs) do
		if mirror:GetAttribute(k) ~= v then mirror:SetAttribute(k, v) end
	end
end

local function bind()
	local id = player:GetAttribute("CC_MatchId")
	local src = (id and root:FindFirstChild(id)) or root:FindFirstChild("idle")
	if src == source then return end
	if conn then conn:Disconnect(); conn = nil end
	source = src
	copyAll(src)
	if src then
		conn = src.AttributeChanged:Connect(function(k) mirror:SetAttribute(k, src:GetAttribute(k)) end)
	end
end

player:GetAttributeChangedSignal("CC_MatchId"):Connect(bind)
root.ChildAdded:Connect(function() task.defer(bind) end)
root.ChildRemoved:Connect(function(c) if c == source then source = nil; task.defer(bind) end end)
bind()
