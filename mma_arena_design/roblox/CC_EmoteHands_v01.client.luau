-- StarterPlayer.StarterPlayerScripts.CC_EmoteHands
-- Nur Optik, lokal: Waehrend "take_the_l" (Attribut CC_Emote am Charakter) werden Handschuhe und Block-Haende ausgeblendet und die
-- Finger-Haende aus CC_StoryShared.Hands eingeblendet (rechts Zeigefinger = L an der Stirn, links entspannt). Danach alles zurueck.
-- Nichts am Server-Zustand oder am gespeicherten Aussehen aendert sich; jeder Client macht es fuer alle sichtbaren Kaempfer.
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local PAIRS = { take_the_l = { L = "Relaxed", R = "Point" } }
local state = {}      -- [char] = { parts = {...}, hidden = {...} }

local function restore(char)
	local s = state[char]; if not s then return end
	state[char] = nil
	for _, p in ipairs(s.parts) do p:Destroy() end
	for part, prev in pairs(s.hidden) do if part.Parent then part.LocalTransparencyModifier = prev end end
end
local function apply(char, pose)
	if state[char] then return end
	local root = char:FindFirstChild("HumanoidRootPart")
	local sh = RS:FindFirstChild("CC_StoryShared")
	local src = sh and sh:FindFirstChild("Hands")
	if not (root and src and src:FindFirstChild("Fighter_BodyNoHands")) then return end
	local body = char:FindFirstChild("Fighter_Body")
	local color = body and body.Color or Color3.fromRGB(184, 148, 123)
	local s = { parts = {}, hidden = {} }
	state[char] = s
	for _, t in ipairs(src:GetChildren()) do
		if t:IsA("MeshPart") and t:GetAttribute("CC_C0") then
			local n = t.Name
			local keep = n == "Fighter_BodyNoHands"
			local side, name = n:match("^Hand_(%a+)_([LR])$")
			if side then keep = (side == pose[name]) end
			if keep then
				local p = t:Clone(); p.Massless = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.Color = color
				p.Transparency = 0
				local mo = Instance.new("Motor6D"); mo.Name = "CC_EmoteHandsMotor"; mo.Part0 = root; mo.Part1 = p; mo.C0 = t:GetAttribute("CC_C0"); mo.Parent = p
				p.Parent = char
				table.insert(s.parts, p)
			end
		end
	end
	for _, n in ipairs({ "Fighter_Body", "Fighter_Gloves" }) do
		local part = char:FindFirstChild(n)
		if part and part:IsA("BasePart") then s.hidden[part] = part.LocalTransparencyModifier; part.LocalTransparencyModifier = 1 end
	end
end
local function update(char)
	local id = char:GetAttribute("CC_Emote")
	if id and PAIRS[id] then apply(char, PAIRS[id]) else restore(char) end
end
local function watch(char)
	if char:GetAttribute("CC_EmoteHandsWatched") then return end
	char:SetAttribute("CC_EmoteHandsWatched", true)
	char:GetAttributeChangedSignal("CC_Emote"):Connect(function() update(char) end)
	char.AncestryChanged:Connect(function() if not char.Parent then restore(char) end end)
	update(char)
end
local function scan()
	for _, p in ipairs(Players:GetPlayers()) do if p.Character then watch(p.Character) end end
	local d = workspace:FindFirstChild("CC_TrainingDummy"); if d then watch(d) end
end
scan()
local acc = 0
RunService.Heartbeat:Connect(function(dt) acc += dt; if acc > 1 then acc = 0; scan() end end)
-- Sicherheitsnetz: Handschuhe werden auch ohne Attributwechsel zurueckgesetzt, wenn das Emote vorbei ist
RunService.Heartbeat:Connect(function()
	for char in pairs(state) do if not PAIRS[char:GetAttribute("CC_Emote") or ""] then restore(char) end end
end)
