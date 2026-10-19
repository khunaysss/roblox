-- ServerScriptService.CC_Corner
-- Rundenpause in der Ecke (CC_Match setzt am Kampf-Ordner das Attribut Corner = true/false):
-- je Kaempfer ein Hocker und ein Eck-Trainer, der vor ihm kniet, ihm die Flasche gibt und erklaert.
-- Animationen (gleich lang, synchron, build_corner_anims_v01.py): Fighter_CornerRest (Kaempfer), Coach_CornerTalk (Trainer).
-- Aufstellung wie in Blender: Trainer 0,95 m vor dem Kaempfer, Blick zu ihm. Die Flasche zeichnet der Client (CC_CornerView).
-- Eck-Trainer: Story-Darsteller (CC_StoryShared.ActorBase) mit Trainingsanzug, rote Ecke schwarz, blaue Ecke dunkelblau.
local Players, RS, SS = game:GetService("Players"), game:GetService("ReplicatedStorage"), game:GetService("ServerStorage")
local KSP = game:GetService("KeyframeSequenceProvider")
local REG = require(RS:WaitForChild("CC_MatchRegistry"))
local A = SS:WaitForChild("CC_Animations")
local ids = {}
pcall(function() ids = require(A:FindFirstChild("CC_AnimIds")) end)

local M2S = 1 / 0.28
local COACH_DIST = 0.95 * M2S
local SEAT_H = 0.47 * M2S                     -- Sitzflaeche ueber dem Boden
local folder = workspace:FindFirstChild("CC_Corners") or Instance.new("Folder")
folder.Name = "CC_Corners"; folder.Parent = workspace

local animCache = {}
local function animFor(name)
	if animCache[name] ~= nil then return animCache[name] or nil end
	local a = Instance.new("Animation")
	if ids[name] then a.AnimationId = "rbxassetid://" .. tostring(ids[name])
	else
		local ks = A:FindFirstChild(name)
		local ok, id = pcall(function() return KSP:RegisterKeyframeSequence(ks) end)
		if not (ks and ok) then animCache[name] = false; warn("[CC] Ecke: Animation fehlt " .. name); return nil end
		a.AnimationId = id
	end
	animCache[name] = a; return a
end

local COACH_LOOKS = {
	red = { look = { hair = "Hair_QuiffV03", beard = "Beard_Full", face = "Face_Focused", skin = 2, hairColor = 6 }, color = Color3.fromRGB(26, 27, 30) },
	blue = { look = { hair = "Hair_SidePart", beard = "Beard_Short", face = "Face_Neutral", skin = 3, hairColor = 1 }, color = Color3.fromRGB(24, 40, 78) },
}
local function buildCoach(side)
	local SH = RS:FindFirstChild("CC_StoryShared")
	if not (SH and SH:FindFirstChild("ActorBase")) then return nil end
	local m = SH.ActorBase:Clone(); m.Name = "CornerCoach_" .. side
	for _, n in ipairs({ "Fighter_Gloves", "Fighter_Shorts" }) do local x = m:FindFirstChild(n); if x then x.Transparency = 1 end end
	local Look = require(RS:WaitForChild("CC_LookShared"))
	local def = COACH_LOOKS[side]
	pcall(function() Look.apply(m, def.look, RS:FindFirstChild("CC_CustomShared")) end)
	local skin = Look.SKIN[def.look.skin]
	for pname, col in pairs({ Coach_Jacket = def.color, Coach_Pants = def.color, Casual_Shoes = Color3.fromRGB(236, 236, 232), Casual_Hands = "skin" }) do
		local t = SH.Outfit:FindFirstChild(pname)
		if t then
			local p = t:Clone(); p.Massless = true
			p.Color = col == "skin" and skin or col
			local mo = Instance.new("Motor6D"); mo.Part0 = m.HumanoidRootPart; mo.Part1 = p; mo.C0 = t:GetAttribute("CC_C0"); mo.Parent = p
			p.Parent = m
		end
	end
	local hum = m:FindFirstChildOfClass("Humanoid"); hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	for _, p in ipairs(m:GetDescendants()) do if p:IsA("BasePart") then p.CanCollide = false; p.CanQuery = false; p.CanTouch = false end end
	m.HumanoidRootPart.Anchored = true
	local animator = hum:FindFirstChildOfClass("Animator") or Instance.new("Animator", hum)
	return m, animator
end

local function buildStool(cf)
	local model = Instance.new("Model"); model.Name = "Stool"
	local function part(name, size, offset, shape, color)
		local p = Instance.new("Part"); p.Name = name; p.Size = size; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
		p.Material = Enum.Material.SmoothPlastic; p.Color = color or Color3.fromRGB(32, 33, 37)
		if shape then p.Shape = shape end
		p.CFrame = cf * offset; p.Parent = model
		return p
	end
	part("Seat", Vector3.new(0.25, 1.5, 1.5), CFrame.new(0, SEAT_H - 0.12, 0) * CFrame.Angles(0, 0, math.rad(90)), Enum.PartType.Cylinder, Color3.fromRGB(150, 24, 30))
	for i = 0, 2 do
		local a = math.rad(i * 120 + 30)
		local x, z = math.cos(a) * 0.55, math.sin(a) * 0.55
		part("Leg" .. i, Vector3.new(0.14, SEAT_H - 0.25, 0.14), CFrame.new(x, (SEAT_H - 0.25) / 2, z))
	end
	return model
end

local function floorUnder(pos, ignore)
	local rp = RaycastParams.new(); rp.FilterType = Enum.RaycastFilterType.Exclude; rp.FilterDescendantsInstances = ignore
	local hit = workspace:Raycast(pos + Vector3.new(0, 2, 0), Vector3.new(0, -12, 0), rp)
	return hit and hit.Position.Y or (pos.Y - 3)
end

local active = {}       -- [matchId] = { items = {...}, tracks = {...} }
local function clear(id)
	local e = active[id]; active[id] = nil
	if not e then return end
	for _, t in ipairs(e.tracks) do pcall(function() t:Stop(0.3) end) end
	for _, x in ipairs(e.items) do x:Destroy() end
end

local function fighters(state)
	local list = {}
	local rp = Players:FindFirstChild(state:GetAttribute("RedName") or "")
	local red = rp and rp.Character and rp.Character:GetAttribute("CC_MatchId") == state.Name and rp.Character or nil
	if red then list.red = red end
	for _, p in ipairs(Players:GetPlayers()) do
		local c = p.Character
		if c and c ~= red and c:GetAttribute("CC_MatchId") == state.Name then list.blue = c end
	end
	if not list.blue then
		local d = workspace:FindFirstChild("CC_TrainingDummy")
		if d and d:GetAttribute("CC_MatchId") == state.Name then list.blue = d end
	end
	return list
end

local function start(state)
	clear(state.Name)
	local e = { items = {}, tracks = {} }
	active[state.Name] = e
	task.wait(0.15)                               -- CC_Match hat gerade teleportiert
	if active[state.Name] ~= e then return end
	for side, c in pairs(fighters(state)) do
		local root = c:FindFirstChild("HumanoidRootPart")
		if root then
			local look = root.CFrame.LookVector * Vector3.new(1, 0, 1)
			look = look.Magnitude > 0.1 and look.Unit or Vector3.new(0, 0, -1)
			local fy = floorUnder(root.Position, { c, folder })
			local base = CFrame.lookAt(Vector3.new(root.Position.X, fy, root.Position.Z), Vector3.new(root.Position.X, fy, root.Position.Z) + look)
			local stool = buildStool(base * CFrame.new(0, 0, 0.35)); stool.Name = "Stool_" .. side; stool.Parent = folder
			table.insert(e.items, stool)
			local coach, canim = buildCoach(side)
			if coach then
				coach:SetAttribute("CC_CornerOf", c.Name); coach:SetAttribute("CC_MatchId", state.Name)
				local cpos = base.Position + look * COACH_DIST
				local hipY = root.Position.Y - fy                   -- gleicher Huefte-Abstand wie beim Kaempfer (gleiches Rig)
				coach.HumanoidRootPart.CFrame = CFrame.lookAt(Vector3.new(cpos.X, fy + hipY, cpos.Z), Vector3.new(root.Position.X, fy + hipY, root.Position.Z))
				coach.Parent = folder
				table.insert(e.items, coach)
				local a = animFor("Coach_CornerTalk")
				if a then local t = canim:LoadAnimation(a); t.Priority = Enum.AnimationPriority.Action4; t:Play(0.1); table.insert(e.tracks, t) end
			end
			local fa = c:FindFirstChildWhichIsA("Animator", true)
			local a = animFor("Fighter_CornerRest")
			if fa and a then local t = fa:LoadAnimation(a); t.Priority = Enum.AnimationPriority.Action4; t:Play(0.15); table.insert(e.tracks, t) end
		end
	end
end

local function watch(state)
	if state.Name == "idle" then return end
	state:GetAttributeChangedSignal("Corner"):Connect(function()
		if state:GetAttribute("Corner") == true then task.spawn(start, state) else clear(state.Name) end
	end)
	state:GetAttributeChangedSignal("State"):Connect(function()
		local st = state:GetAttribute("State")
		if st == "fight" or st == "over" or st == "idle" then clear(state.Name) end
	end)
end
local root = REG.root()
root.ChildAdded:Connect(watch)
root.ChildRemoved:Connect(function(c) clear(c.Name) end)
for _, c in ipairs(root:GetChildren()) do watch(c) end
