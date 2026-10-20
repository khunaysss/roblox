-- CC_AnnouncerHUD_v02 – lokale TV-Ansagen fuer den eigenen Kampf.
-- Keine Netzwerkaufrufe; Texte kommen unveraendert aus CC_Announcer.
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local player = Players.LocalPlayer
local lines = require(RS:WaitForChild("CC_Announcer"))
local gui = Instance.new("ScreenGui")
gui.Name = "CC_AnnouncerHUD"
gui.ResetOnSpawn = false
gui.DisplayOrder = 12
gui.Parent = player:WaitForChild("PlayerGui")
local card = Instance.new("CanvasGroup")
card.Name = "Broadcast"
card.AnchorPoint = Vector2.new(0, 1)
card.Position = UDim2.new(0, 24, 1, -128)
card.Size = UDim2.new(0.36, 0, 0, 72)
card.BackgroundColor3 = Color3.fromRGB(21, 23, 28)
card.BorderSizePixel = 0
card.Visible = false
card.Parent = gui
local bounds = Instance.new("UISizeConstraint")
bounds.MinSize = Vector2.new(300, 72)
bounds.MaxSize = Vector2.new(560, 88)
bounds.Parent = card
local edge = Instance.new("UIStroke")
edge.Color = Color3.fromRGB(224, 36, 58)
edge.Thickness = 1
edge.Parent = card
local corner = Instance.new("UICorner")
corner.CornerRadius = UDim.new(0, 4)
corner.Parent = card
local text = Instance.new("TextLabel")
text.Name = "Announcement"
text.BackgroundTransparency = 1
text.Position = UDim2.fromOffset(16, 8)
text.Size = UDim2.new(1, -32, 1, -16)
text.Font = Enum.Font.GothamBold
text.TextSize = 19
text.TextColor3 = Color3.fromRGB(245, 245, 247)
text.TextXAlignment = Enum.TextXAlignment.Left
text.TextWrapped = true
text.Parent = card
local current, links, generation = nil, {}, 0
local previous, seen, choices = {}, {}, {}
local watched = {}
local function hide()
	generation += 1
	card.Visible = false
end
local function speak(category, key)
	local variants = lines[category]
	if not variants or seen[key] then return end
	seen[key] = true
	local index = ((choices[category] or 0) % #variants) + 1
	if category == "winner" and current then
		local winner = current:GetAttribute("Winner")
		local ownSide = current:GetAttribute("RedName") == player.Name and "red" or "blue"
		if winner ~= ownSide and string.find(string.lower(variants[index]), "yours", 1, true) then
			index = (index % #variants) + 1
		end
	end
	choices[category] = index
	generation += 1
	local token = generation
	text.Text = variants[index]
	card:SetAttribute("Category", category)
	card:SetAttribute("EventKey", key)
	card.GroupTransparency = 0
	card.Visible = true
	task.delay(3.8, function()
		if generation ~= token then return end
		if player:GetAttribute("CC_ReduceMotion") then
			card.Visible = false
			return
		end
		local tween = TweenService:Create(card, TweenInfo.new(0.2), {GroupTransparency = 1})
		tween:Play()
		tween.Completed:Once(function()
			if generation == token then card.Visible = false end
		end)
	end)
end
local function refresh()
	local m = current
	if not m or not m.Parent or m:GetAttribute("Mode") == "tutorial" then hide(); return end
	local state = m:GetAttribute("State")
	card.Position = UDim2.new(0, 24, 1, m:GetAttribute("Corner") == true and -252 or -128)
	for _, character in ipairs(workspace:GetChildren()) do
		if character:IsA("Model") and character:GetAttribute("CC_MatchId") == m.Name and not watched[character] then
			watched[character] = character:GetAttribute("CC_Knockdowns") or 0
			table.insert(links, character:GetAttributeChangedSignal("CC_Knockdowns"):Connect(function()
				local count = character:GetAttribute("CC_Knockdowns") or 0
				if current == m and m:GetAttribute("State") == "fight" and count > watched[character] then
					speak("knockdown", m.Name .. ":" .. tostring(m:GetAttribute("Round")) .. ":" .. character.Name .. ":" .. count)
				end
				watched[character] = count
			end))
		end
	end
	local round = tostring(m:GetAttribute("Round") or 1)
	local prefix = m.Name .. ":" .. round .. ":"
	local stoppage = string.lower(tostring(m:GetAttribute("Stoppage") or "") .. " " .. tostring(m:GetAttribute("BannerSub") or ""))
	local banner = string.upper(tostring(m:GetAttribute("Banner") or ""))
	if state ~= previous.state then
		if state == "walkout" or state == "intro" then
			speak("walkout", m.Name .. ":entry")
		elseif state == "fight" then
			speak("fightStart", prefix .. "fight")
		elseif state == "break" then
			speak("cornerAdvice", prefix .. "corner")
		elseif state == "over" then
			local kind = stoppage:find("doctor", 1, true) and "doctor"
				or stoppage:find("sub", 1, true) and "submission"
				or (stoppage:find("decision", 1, true) or stoppage:find("points", 1, true)) and "decision"
				or (stoppage:find("k.o.", 1, true) or stoppage:find("knockout", 1, true)) and "ko"
				or "winner"
			speak(kind, m.Name .. ":finish")
			local token = generation
			task.delay(2.2, function()
				if current == m and generation == token and m:GetAttribute("State") == "over"
					and m:GetAttribute("Winner") ~= "draw" and kind ~= "winner" then
					speak("winner", m.Name .. ":winner")
				end
			end)
		end
	end
	if state == "fight" and banner ~= previous.banner and banner:find("KNOCKDOWN", 1, true) then
		speak("knockdown", prefix .. banner .. ":" .. tostring(m:GetAttribute("TimeLeft")))
	end
	if m:GetAttribute("Corner") == true and previous.corner ~= true then
		speak("cornerAdvice", prefix .. "corner")
	end
	previous = {state = state, banner = banner, corner = m:GetAttribute("Corner")}
end
local function bind()
	for _, connection in ipairs(links) do connection:Disconnect() end
	table.clear(links)
	hide()
	current, previous, seen, watched = nil, {}, {}, {}
	local id = player:GetAttribute("CC_MatchId")
	if not id or id == "" then return end
	local matches = RS:FindFirstChild("CC_Matches")
	current = matches and matches:FindFirstChild(tostring(id))
	if not current then return end
	local scheduled = false
	table.insert(links, current.AttributeChanged:Connect(function()
		if scheduled then return end
		scheduled = true
		task.defer(function() scheduled = false; refresh() end)
	end))
	refresh()
end
player:GetAttributeChangedSignal("CC_MatchId"):Connect(bind)
RS:WaitForChild("CC_Matches").ChildAdded:Connect(function(m)
	if m.Name == tostring(player:GetAttribute("CC_MatchId")) and current ~= m then task.defer(bind) end
end)
bind()
