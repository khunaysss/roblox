-- ServerScriptService.CC_Presentation
-- Einlauf, Ergebnisposen und Ringarzt mit kampfgebundener Bereinigung.
local Players = game:GetService("Players")
local RS, SS = game:GetService("ReplicatedStorage"), game:GetService("ServerStorage")
local KSP = game:GetService("KeyframeSequenceProvider")
local A = SS:WaitForChild("CC_Animations")
local ids = {}
pcall(function() ids = require(A:WaitForChild("CC_AnimIds")) end)
local cache, actors, watched = {}, {}, {}
local doctors = workspace:FindFirstChild("CC_Doctors") or Instance.new("Folder")
doctors.Name = "CC_Doctors"; doctors.Parent = workspace

local function animFor(name)
	if cache[name] ~= nil then return cache[name] or nil end
	local a = Instance.new("Animation")
	if ids[name] then
		a.AnimationId = "rbxassetid://" .. tostring(ids[name])
	else
		local ks = A:FindFirstChild(name)
		local ok, id = pcall(function() return KSP:RegisterKeyframeSequence(ks) end)
		if not (ks and ok) then
			a:Destroy(); cache[name] = false
			warn("[CC] Praesentation: Animation fehlt " .. name); return nil
		end
		a.AnimationId = id
	end
	cache[name] = a; return a
end

local function play(char, name, looped, priority)
	local animator = char:FindFirstChildWhichIsA("Animator", true)
	local a = animFor(name)
	if not (animator and a) then return nil end
	local ok, track = pcall(function() return animator:LoadAnimation(a) end)
	if not ok then warn("[CC] Praesentation: " .. tostring(track)); return nil end
	track.Name = "CC_Presentation_" .. name
	track.Priority = priority; track.Looped = looped
	track:Play(0.15)
	return track
end

local function clearActor(char)
	local entry = actors[char]
	if not entry then return end
	actors[char] = nil
	for _, connection in ipairs(entry.connections) do connection:Disconnect() end
	if entry.track then entry.track:Stop(0.15); entry.track:Destroy() end
end

local function fighters(state)
	local red, blue
	for _, player in ipairs(Players:GetPlayers()) do
		local char = player.Character
		if char and char:GetAttribute("CC_MatchId") == state.Name then
			if player.Name == state:GetAttribute("RedName") then red = char else blue = char end
		end
	end
	local dummy = workspace:FindFirstChild("CC_TrainingDummy")
	if not blue and dummy and dummy:GetAttribute("CC_MatchId") == state.Name then blue = dummy end
	return red, blue
end

local function pose(char, state, mode)
	if not char then return end
	local old = actors[char]
	if old and old.id == state.Name and old.mode == mode then return end
	clearActor(char)
	if not mode then return end
	local entry = { id = state.Name, mode = mode, connections = {} }
	actors[char] = entry
	local function valid()
		return actors[char] == entry and char.Parent and state.Parent
			and char:GetAttribute("CC_MatchId") == state.Name
	end
	local function startCelebration()
		if not valid() or entry.track then return end
		if state:GetAttribute("State") == "over" and char:GetAttribute("CC_WinRaiseDone") == state.Name then
			entry.track = play(char, "Fighter_Celebrate", false, Enum.AnimationPriority.Action4)
		end
	end
	table.insert(entry.connections, char:GetAttributeChangedSignal("CC_MatchId"):Connect(function()
		if not valid() then clearActor(char) end
	end))
	table.insert(entry.connections, char.Destroying:Connect(function() clearActor(char) end))
	if mode == "walkout" then
		entry.track = play(char, "Fighter_Walkout", true, Enum.AnimationPriority.Action)
		task.spawn(function()
			while valid() and state:GetAttribute("State") == "walkout" do
				if entry.track and not entry.track.IsPlaying then entry.track:Play(0.15) end
				task.wait(0.2)
			end
		end)
	elseif mode == "loser" then
		entry.track = play(char, "Fighter_Dejected", true, Enum.AnimationPriority.Action4)
	elseif mode == "winner" then
		table.insert(entry.connections, char:GetAttributeChangedSignal("CC_WinRaiseDone"):Connect(startCelebration))
		startCelebration()
	end
end

local function removeDoctor(entry)
	entry.doctorToken = (entry.doctorToken or 0) + 1
	if entry.doctorTrack then entry.doctorTrack:Stop(0.1); entry.doctorTrack:Destroy(); entry.doctorTrack = nil end
	if entry.doctor then entry.doctor:Destroy(); entry.doctor = nil end
end

local function showDoctor(state, entry)
	if entry.doctorStarted or state:GetAttribute("Stoppage") ~= "Doctor stoppage" then return end
	local winner = state:GetAttribute("Winner")
	if winner ~= "red" and winner ~= "blue" then return end
	local red, blue = fighters(state)
	local loser = winner == "red" and blue or red
	local root = loser and loser:FindFirstChild("HumanoidRootPart")
	local template = SS:FindFirstChild("Doctor")
	if not (root and template) then return end
	entry.doctorStarted = true
	local doctor = template:Clone(); doctor.Name = "Doctor"
	doctor:SetAttribute("CC_MatchId", state.Name)
	local dr = doctor:FindFirstChild("HumanoidRootPart") or doctor.PrimaryPart
	if not dr then doctor:Destroy(); return end
	local forward = root.CFrame.LookVector * Vector3.new(1, 0, 1)
	if forward.Magnitude < 0.01 then forward = Vector3.new(0, 0, -1) end
	local pos = root.Position + forward.Unit * (0.62 / 0.28)
	local center = state:GetAttribute("CageCenter")
	doctor.Parent = doctors
	local box, size = doctor:GetBoundingBox()
	local hip = dr.Position.Y - (box.Position.Y - size.Y / 2)
	local soles = doctor:FindFirstChild("Referee__Shoe_Soles", true)
	if soles and soles:IsA("BasePart") then hip = dr.Position.Y - soles.Position.Y + soles.Size.Y / 2 end
	local floor = typeof(center) == "Vector3" and center.Y or root.Position.Y - 3
	pos = Vector3.new(pos.X, floor + hip, pos.Z)
	dr.CFrame = CFrame.lookAt(pos, Vector3.new(root.Position.X, pos.Y, root.Position.Z))
	entry.doctor = doctor
	entry.doctorTrack = play(doctor, "Doc_Check", false, Enum.AnimationPriority.Action4)
	local token = (entry.doctorToken or 0) + 1; entry.doctorToken = token
	task.spawn(function()
		local started = os.clock()
		while entry.doctorToken == token and doctor.Parent and state.Parent
			and loser.Parent and loser:GetAttribute("CC_MatchId") == state.Name do
			local track = entry.doctorTrack
			if os.clock() - started >= 5 then break end
			if track and track.Length > 0 and not track.IsPlaying then break end
			task.wait(0.1)
		end
		if entry.doctorToken == token then removeDoctor(entry) end
	end)
end

local function refresh(state)
	local entry = watched[state]
	if not entry then return end
	local red, blue = fighters(state)
	local st, winner = state:GetAttribute("State"), state:GetAttribute("Winner")
	local function mode(side)
		if st == "walkout" then return "walkout" end
		if st == "over" and (winner == "red" or winner == "blue") then
			return winner == side and "winner" or "loser"
		end
		return nil
	end
	pose(red, state, mode("red")); pose(blue, state, mode("blue"))
	showDoctor(state, entry)
end

local function watchState(state)
	if state.Name == "idle" or watched[state] then return end
	local entry = { connections = {} }; watched[state] = entry
	table.insert(entry.connections, state.AttributeChanged:Connect(function(key)
		if key == "State" or key == "Winner" or key == "Stoppage" or key == "RedName" then refresh(state) end
	end))
	table.insert(entry.connections, state.Destroying:Connect(function()
		for char, actor in pairs(actors) do if actor.id == state.Name then clearActor(char) end end
		removeDoctor(entry)
		for _, connection in ipairs(entry.connections) do connection:Disconnect() end
		watched[state] = nil
	end))
	refresh(state)
end

local function watchCharacter(char)
	local function changed()
		local id = char:GetAttribute("CC_MatchId")
		if type(id) ~= "string" or id == "" then clearActor(char); return end
		local state = RS.CC_Matches:FindFirstChild(id)
		if state then refresh(state) end
	end
	char:GetAttributeChangedSignal("CC_MatchId"):Connect(changed)
	changed()
end

local function watchPlayer(player)
	player.CharacterAdded:Connect(watchCharacter)
	if player.Character then watchCharacter(player.Character) end
end

local root = RS:WaitForChild("CC_Matches")
root.ChildAdded:Connect(watchState)
for _, state in ipairs(root:GetChildren()) do watchState(state) end
Players.PlayerAdded:Connect(watchPlayer)
for _, player in ipairs(Players:GetPlayers()) do watchPlayer(player) end
watchCharacter(workspace:WaitForChild("CC_TrainingDummy"))

