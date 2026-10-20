-- ServerScriptService.CC_BeltDisplay
-- Titelguertel am Charakter, ohne Aenderung gespeicherter Fortschrittswerte.
local Players = game:GetService("Players")
local RS, SS = game:GetService("ReplicatedStorage"), game:GetService("ServerStorage")
local templates = SS:WaitForChild("CC_Belts")
local matches = RS:WaitForChild("CC_Matches")
local entries = {}
local names = { "Belt_Title_Band", "Belt_Title_Plate", "Belt_Title_Trim", "Belt_Title_Gem" }

local function clear(entry)
	for _, connection in ipairs(entry.connections) do connection:Disconnect() end
	for _, part in pairs(entry.parts) do part:Destroy() end
	entries[entry.player] = nil
end

local function update(entry)
	local player, char = entry.player, entry.char
	if not char.Parent or player.Character ~= char then return end
	local wins = tonumber(player:GetAttribute("CC_CareerWins")) or 0
	local id = char:GetAttribute("CC_MatchId")
	local state = type(id) == "string" and matches:FindFirstChild(id)
	local st = state and state:GetAttribute("State")
	local visible = wins >= 2 and (not state or st == "idle" or st == "walkout" or st == "intro" or st == "over")
	local plateColor = wins >= 10 and Color3.fromRGB(232, 190, 70)
		or wins >= 4 and Color3.fromRGB(212, 168, 56) or Color3.fromRGB(170, 174, 182)
	for name, part in pairs(entry.parts) do
		part.Transparency = visible and (name ~= "Belt_Title_Gem" or wins >= 7) and 0 or 1
		if name == "Belt_Title_Plate" then
			part.Color = plateColor
			local gui = part:FindFirstChild("CC_BeltTitle")
			if gui then gui.Enabled = visible end
		elseif name == "Belt_Title_Trim" then
			part.Color = plateColor
		end
	end
end

local function attach(player, char)
	if entries[player] then clear(entries[player]) end
	local root = char:WaitForChild("HumanoidRootPart", 10)
	if not root or player.Character ~= char then return end
	local entry = { player = player, char = char, parts = {}, connections = {} }
	entries[player] = entry
	for _, name in ipairs(names) do
		local template = templates:FindFirstChild(name)
		if template and template:IsA("BasePart") and typeof(template:GetAttribute("CC_C0")) == "CFrame" then
			local part = template:Clone()
			part.Anchored = false; part.Massless = true
			part.CanCollide = false; part.CanTouch = false; part.CanQuery = false
			part:SetAttribute("CC_CosmeticBelt", true)
			local motor = Instance.new("Motor6D")
			motor.Name = name .. "Motor6D"; motor.Part0 = root; motor.Part1 = part
			motor.C0 = template:GetAttribute("CC_C0"); motor.Parent = part
			part.CFrame = root.CFrame * motor.C0
			part.Parent = char; entry.parts[name] = part
			if name == "Belt_Title_Plate" then
				local gui = Instance.new("SurfaceGui")
				gui.Name = "CC_BeltTitle"; gui.Face = Enum.NormalId.Front
				gui.SizingMode = Enum.SurfaceGuiSizingMode.FixedSize
				gui.CanvasSize = Vector2.new(768, 256); gui.LightInfluence = 0.5
				gui.AlwaysOnTop = false; gui.Parent = part
				local label = Instance.new("TextLabel")
				label.Name = "Title"; label.BackgroundTransparency = 1
				label.Position = UDim2.fromScale(0.08, 0.2); label.Size = UDim2.fromScale(0.84, 0.6)
				label.Text = "CAGE CHAMPIONS"; label.TextColor3 = Color3.fromRGB(24, 21, 16)
				label.Font = Enum.Font.GothamBold; label.TextScaled = true; label.Parent = gui
			end
		else
			warn("[CC] Guertel-Vorlage oder CC_C0 fehlt: " .. name)
		end
	end
	table.insert(entry.connections, player:GetAttributeChangedSignal("CC_CareerWins"):Connect(function() update(entry) end))
	table.insert(entry.connections, char:GetAttributeChangedSignal("CC_MatchId"):Connect(function() update(entry) end))
	table.insert(entry.connections, char.Destroying:Connect(function()
		if entries[player] == entry then clear(entry) end
	end))
	update(entry)
end

local function watchMatch(state)
	local connection
	connection = state:GetAttributeChangedSignal("State"):Connect(function()
		for _, entry in pairs(entries) do
			if entry.char:GetAttribute("CC_MatchId") == state.Name then update(entry) end
		end
	end)
	state.Destroying:Once(function() connection:Disconnect() end)
end

local function watchPlayer(player)
	player.CharacterAdded:Connect(function(char) attach(player, char) end)
	if player.Character then task.spawn(attach, player, player.Character) end
end
Players.PlayerAdded:Connect(watchPlayer)
Players.PlayerRemoving:Connect(function(player) if entries[player] then clear(entries[player]) end end)
matches.ChildAdded:Connect(watchMatch)
for _, state in ipairs(matches:GetChildren()) do watchMatch(state) end
for _, player in ipairs(Players:GetPlayers()) do watchPlayer(player) end
