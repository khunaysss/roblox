-- ServerScriptService.CC_BeltDisplay
-- Getragener Guertel am Charakter (nur Aussehen, keine Werte). Auswahl: look.belt (CC_LookShared.BELTS, Editor "My Fighter" -> BELT).
--   "auto"  = hoechster erreichter Titelguertel (unter 2 Karriere-Siegen keiner)
--   "title" = Ledergurt mit Platte (ServerStorage.CC_Belts.Belt_Title_*), "CAGE CHAMPIONS" auf der Platte
--   "style" = Stoffguertel (Belt_Cloth_*) in den Farben des Stils
-- Sichtbar im Gym, beim Walkout, im Intro und nach dem Kampf; waehrend der Runden und Pausen ausgeblendet.
-- Ein gesperrter Guertel wird nie gezeigt (Pruefung mit dem Profil-Fortschritt, falls das Profil veraltet ist).
local Players = game:GetService("Players")
local RS, SS = game:GetService("ReplicatedStorage"), game:GetService("ServerStorage")
local HS = game:GetService("HttpService")
local Look = require(RS:WaitForChild("CC_LookShared"))
local templates = SS:WaitForChild("CC_Belts")
local matches = RS:WaitForChild("CC_Matches")
local entries = {}
local TITLE = { "Belt_Title_Band", "Belt_Title_Plate", "Belt_Title_Trim", "Belt_Title_Gem" }
local CLOTH = { "Belt_Cloth_Band", "Belt_Cloth_Tip" }
local LEATHER, TRIM = Color3.fromRGB(16, 16, 18), Color3.fromRGB(242, 204, 96)
local SHOW = { idle = true, walkout = true, intro = true, over = true }

local function clear(entry)
	for _, c in ipairs(entry.connections) do c:Disconnect() end
	for _, part in pairs(entry.parts) do part:Destroy() end
	if entries[entry.player] == entry then entries[entry.player] = nil end
end

-- gewaehlter (und freigeschalteter) Guertel des Spielers
local function beltOf(player)
	local ok, look = pcall(function() return HS:JSONDecode(player:GetAttribute("CC_Look") or "{}") end)
	local idx = ok and type(look) == "table" and tonumber(look.belt) or 1
	local item = Look.BELTS[idx] or Look.BELTS[1]
	local prog = Look.progressOf(player)
	if not Look.unlocked(item, prog) then item = Look.BELTS[1] end
	if item.kind == "auto" then return Look.bestTitleBelt(prog) end
	if item.kind == "none" then return nil end
	return item
end

local function update(entry)
	local player, char = entry.player, entry.char
	if not char.Parent or player.Character ~= char then return end
	local id = char:GetAttribute("CC_MatchId")
	local state = type(id) == "string" and matches:FindFirstChild(id)
	local st = state and state:GetAttribute("State")
	local belt = beltOf(player)
	local visible = belt ~= nil and (not state or SHOW[st] == true)
	for name, part in pairs(entry.parts) do
		local isTitle = name:find("Belt_Title_") ~= nil
		local on = visible and ((isTitle and belt.kind == "title") or (not isTitle and belt.kind == "style"))
		if on and name == "Belt_Title_Gem" then on = belt.gems == true end
		part.Transparency = on and 0 or 1
		if on then
			if name == "Belt_Title_Band" then part.Color = LEATHER
			elseif name == "Belt_Title_Plate" then part.Color = belt.plate
			elseif name == "Belt_Title_Trim" then part.Color = belt.trim or TRIM
			elseif name == "Belt_Cloth_Band" then part.Color = belt.color
			elseif name == "Belt_Cloth_Tip" then part.Color = belt.accent end
		end
		local gui = part:FindFirstChild("CC_BeltTitle")
		if gui then
			gui.Enabled = on
			gui.Title.Text = belt and belt.kind == "title" and (belt.title == "CAGE LEGEND" and "CAGE LEGEND" or "CAGE CHAMPIONS") or ""
			gui.Title.TextColor3 = belt and belt.trim and belt.trim or Color3.fromRGB(24, 21, 16)
		end
	end
	player:SetAttribute("CC_BeltName", belt and belt.name or nil)        -- fuer Anzeigen (Namensschild, Menue)
end

local function plateText(part)
	local gui = Instance.new("SurfaceGui"); gui.Name = "CC_BeltTitle"; gui.Face = Enum.NormalId.Front
	gui.SizingMode = Enum.SurfaceGuiSizingMode.FixedSize; gui.CanvasSize = Vector2.new(768, 256); gui.LightInfluence = 0.5
	gui.Parent = part
	local label = Instance.new("TextLabel"); label.Name = "Title"; label.BackgroundTransparency = 1
	label.Position = UDim2.fromScale(0.08, 0.2); label.Size = UDim2.fromScale(0.84, 0.6)
	label.Text = "CAGE CHAMPIONS"; label.TextColor3 = Color3.fromRGB(24, 21, 16); label.Font = Enum.Font.GothamBold; label.TextScaled = true
	label.Parent = gui
end

local function attach(player, char)
	if entries[player] then clear(entries[player]) end
	local root = char:WaitForChild("HumanoidRootPart", 10)
	if not root or player.Character ~= char then return end
	local entry = { player = player, char = char, parts = {}, connections = {} }
	entries[player] = entry
	for _, list in ipairs({ TITLE, CLOTH }) do
		for _, name in ipairs(list) do
			local t = templates:FindFirstChild(name)
			if t and t:IsA("BasePart") and typeof(t:GetAttribute("CC_C0")) == "CFrame" then
				local part = t:Clone()
				part.Anchored = false; part.Massless = true; part.CanCollide = false; part.CanTouch = false; part.CanQuery = false
				part.Transparency = 1; part:SetAttribute("CC_CosmeticBelt", true)
				local motor = Instance.new("Motor6D"); motor.Name = name .. "Motor6D"
				motor.Part0 = root; motor.Part1 = part; motor.C0 = t:GetAttribute("CC_C0"); motor.Parent = part
				part.CFrame = root.CFrame * motor.C0
				part.Parent = char
				entry.parts[name] = part
				if name == "Belt_Title_Plate" then plateText(part) end
			else
				warn("[CC] Guertel-Vorlage oder CC_C0 fehlt: " .. name)
			end
		end
	end
	for _, attr in ipairs({ "CC_Look", "CC_CareerWins", "CC_SigUnlocked" }) do
		table.insert(entry.connections, player:GetAttributeChangedSignal(attr):Connect(function() update(entry) end))
	end
	table.insert(entry.connections, char:GetAttributeChangedSignal("CC_MatchId"):Connect(function() update(entry) end))
	table.insert(entry.connections, char.Destroying:Connect(function() clear(entry) end))
	update(entry)
end

local function watchMatch(state)
	local c = state:GetAttributeChangedSignal("State"):Connect(function()
		for _, entry in pairs(entries) do
			if entry.char:GetAttribute("CC_MatchId") == state.Name then update(entry) end
		end
	end)
	state.Destroying:Once(function() c:Disconnect() end)
end

local function watchPlayer(player)
	player.CharacterAdded:Connect(function(char) attach(player, char) end)
	if player.Character then task.spawn(attach, player, player.Character) end
end
Players.PlayerAdded:Connect(watchPlayer)
Players.PlayerRemoving:Connect(function(player) if entries[player] then clear(entries[player]) end end)
matches.ChildAdded:Connect(watchMatch)
for _, s in ipairs(matches:GetChildren()) do watchMatch(s) end
for _, p in ipairs(Players:GetPlayers()) do watchPlayer(p) end
