-- ServerScriptService.CC_Referee
-- Ringrichter in jedem laufenden Kampf (mehrere Kaefige gleichzeitig): erscheint mit dem Walkout, bleibt seitlich zu den Kaempfern
-- (gegenueber der Kamera-Linie, nie zwischen ihnen), schaut ihnen zu und reagiert auf den Kampf:
--   Banner "FIGHT!"            -> Ref_Fight (Startzeichen)
--   Attribut Stoppage (CC_Match) -> rennt zwischen die Kaempfer, Ref_Stop (Abbruch bei K.o., Submission, T.K.O., Arzt)
--   State "over" mit Sieger     -> stellt sich links neben den Sieger und haelt dessen Arm hoch (Ref_RaiseHand + Fighter_WinRaise)
-- Modell: ServerStorage.CC_Referee (Import aus export/Referee_Rigged_v01.fbx, setup_referee_v01.luau). Fehlt es, steht ein
-- Platzhalter (Story-Darsteller im schwarzen Trainingsanzug) im Kaefig.
-- Animationen: ServerStorage.CC_Animations (CC_AnimIds hochgeladen, sonst KeyframeSequence nur in Studio).
local Players, RS, SS = game:GetService("Players"), game:GetService("ReplicatedStorage"), game:GetService("ServerStorage")
local KSP, RunService = game:GetService("KeyframeSequenceProvider"), game:GetService("RunService")
local REG = require(RS:WaitForChild("CC_MatchRegistry"))
local A = SS:WaitForChild("CC_Animations")
local ids = {}
pcall(function() ids = require(A:FindFirstChild("CC_AnimIds")) end)

local SPEED, RUN_SPEED = 9, 20                -- Studs/s (normal / beim Eingreifen)
local SIDE = 7.5                               -- Abstand zur Kampflinie
local folder = workspace:FindFirstChild("CC_Referees") or Instance.new("Folder")
folder.Name = "CC_Referees"; folder.Parent = workspace

local animCache = {}
local function animFor(name)
	if animCache[name] ~= nil then return animCache[name] or nil end
	local a = Instance.new("Animation")
	if ids[name] then a.AnimationId = "rbxassetid://" .. tostring(ids[name])
	else
		local ks = A:FindFirstChild(name)
		local ok, id = pcall(function() return KSP:RegisterKeyframeSequence(ks) end)
		if not (ks and ok) then animCache[name] = false; warn("[CC] Ringrichter: Animation fehlt " .. name); return nil end
		a.AnimationId = id
	end
	animCache[name] = a; return a
end

-- Modell bauen: echtes Ringrichter-Modell oder Platzhalter
local function buildModel()
	local src = SS:FindFirstChild("CC_Referee")
	local m
	if src then
		m = src:Clone()
	else
		local SH = RS:FindFirstChild("CC_StoryShared")
		if not (SH and SH:FindFirstChild("ActorBase")) then return nil end
		m = SH.ActorBase:Clone()
		for _, n in ipairs({ "Fighter_Gloves", "Fighter_Shorts" }) do local x = m:FindFirstChild(n); if x then x.Transparency = 1 end end
		local Look = require(RS:WaitForChild("CC_LookShared"))
		pcall(function() Look.apply(m, { hair = "Hair_Buzzcut", beard = "Beard_Short", face = "Face_Focused", skin = 2, hairColor = 6 }, RS:FindFirstChild("CC_CustomShared")) end)
		local skin = Look.SKIN[2]
		for pname, col in pairs({ Coach_Jacket = Color3.fromRGB(20, 20, 22), Coach_Pants = Color3.fromRGB(20, 20, 22), Casual_Shoes = Color3.fromRGB(20, 20, 22), Casual_Hands = "skin" }) do
			local t = SH.Outfit:FindFirstChild(pname)
			if t then
				local p = t:Clone(); p.Massless = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
				p.Color = col == "skin" and skin or col
				local mo = Instance.new("Motor6D"); mo.Part0 = m.HumanoidRootPart; mo.Part1 = p; mo.C0 = t:GetAttribute("CC_C0"); mo.Parent = p
				p.Parent = m
			end
		end
	end
	m.Name = "Referee"
	local hum = m:FindFirstChildOfClass("Humanoid")
	if hum then hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None end
	for _, p in ipairs(m:GetDescendants()) do
		if p:IsA("BasePart") then p.CanCollide = false; p.CanQuery = false; p.CanTouch = false end
	end
	local root = m:FindFirstChild("HumanoidRootPart") or m.PrimaryPart
	root.Anchored = true
	local animator = m:FindFirstChildWhichIsA("Animator", true)
	if not animator then
		local host = hum or m:FindFirstChildOfClass("AnimationController") or Instance.new("AnimationController", m)
		animator = Instance.new("Animator"); animator.Parent = host
	end
	return m, root, animator
end

local refs = {}            -- [matchId] = ref

local function fightersOf(state)
	local id = state.Name
	local red, blue
	local rp = Players:FindFirstChild(state:GetAttribute("RedName") or "")
	if rp and rp.Character and rp.Character:GetAttribute("CC_MatchId") == id then red = rp.Character end
	for _, p in ipairs(Players:GetPlayers()) do
		local c = p.Character
		if c and c ~= red and c:GetAttribute("CC_MatchId") == id then blue = c end
	end
	if not blue then
		local d = workspace:FindFirstChild("CC_TrainingDummy")
		if d and d:GetAttribute("CC_MatchId") == id then blue = d end
	end
	return red, blue
end
local function rootOf(c) return c and c:FindFirstChild("HumanoidRootPart") end

local function floorY(state, pos, ignore)
	local rp = RaycastParams.new(); rp.FilterType = Enum.RaycastFilterType.Exclude; rp.FilterDescendantsInstances = ignore
	local hit = workspace:Raycast(Vector3.new(pos.X, pos.Y + 8, pos.Z), Vector3.new(0, -30, 0), rp)
	return hit and hit.Position.Y
end

local function play(ref, name, fade, looped)
	local a = animFor(name); if not a then return nil end
	local t = ref.tracks[name]
	if not t then t = ref.animator:LoadAnimation(a); ref.tracks[name] = t end
	t.Looped = looped or false
	t:Play(fade or 0.2)
	return t
end

local function spawnRef(state)
	local m, root, animator = buildModel()
	if not m then return nil end
	local center = state:GetAttribute("CageCenter")
	if typeof(center) ~= "Vector3" then m:Destroy(); return nil end
	local ref = { model = m, root = root, animator = animator, tracks = {}, state = state, mode = "watch", hipY = nil }
	m.Parent = folder
	-- Hoehe der Huefte ueber dem Boden aus dem Modell (Fusssohle = unterste Kante)
	local cf, size = m:GetBoundingBox()
	ref.hipY = root.Position.Y - (cf.Position.Y - size.Y / 2)
	local radius = state:GetAttribute("CageRadius") or 20
	local start = center + Vector3.new(0, 0, radius - 3)
	local y = floorY(state, start, { m, folder }) or center.Y
	root.CFrame = CFrame.lookAt(Vector3.new(start.X, y + ref.hipY, start.Z), Vector3.new(center.X, y + ref.hipY, center.Z))
	play(ref, "Ref_Idle", 0, true)
	return ref
end

local function moveTowards(ref, goal, faceAt, speed, dt)
	local p = ref.root.Position
	local flat = Vector3.new(goal.X - p.X, 0, goal.Z - p.Z)
	local step = math.min(flat.Magnitude, speed * dt)
	local np = p + (flat.Magnitude > 0.01 and flat.Unit * step or Vector3.zero)
	local y = floorY(ref.state, np, { ref.model, folder, workspace:FindFirstChild("CC_TrainingDummy") })
	if y then np = Vector3.new(np.X, y + ref.hipY, np.Z) end
	local look = Vector3.new(faceAt.X, np.Y, faceAt.Z)
	if (look - np).Magnitude > 0.1 then ref.root.CFrame = CFrame.lookAt(np, look) else ref.root.CFrame = CFrame.new(np) * ref.root.CFrame.Rotation end
	return flat.Magnitude - step
end

-- Position: seitlich der Kampflinie, auf der Seite, auf der er schon steht; immer im Kaefig
local function watchSpot(ref, a, b)
	local state = ref.state
	local center = state:GetAttribute("CageCenter"); local radius = state:GetAttribute("CageRadius") or 20
	local mid = (a + b) / 2
	local line = Vector3.new(b.X - a.X, 0, b.Z - a.Z)
	local perp = line.Magnitude > 0.1 and Vector3.new(-line.Z, 0, line.X).Unit or Vector3.new(1, 0, 0)
	local cur = ref.root.Position
	if (cur - (mid + perp)).Magnitude > (cur - (mid - perp)).Magnitude then perp = -perp end
	local spot = mid + perp * SIDE
	local off = Vector3.new(spot.X - center.X, 0, spot.Z - center.Z)
	local maxR = radius - 3
	if off.Magnitude > maxR then
		spot = Vector3.new(center.X, spot.Y, center.Z) + off.Unit * maxR
		-- an der Wand: auf die andere Seite wechseln, wenn die dort mehr Platz hat
		local other = mid - perp * SIDE
		local o2 = Vector3.new(other.X - center.X, 0, other.Z - center.Z)
		if o2.Magnitude < maxR - 2 then spot = other end
	end
	return spot, mid
end

local function stopFight(ref)
	ref.mode = "stop"
	task.spawn(function()
		local a, b = fightersOf(ref.state)
		local ra, rb = rootOf(a), rootOf(b)
		if not (ra and rb) then return end
		-- zwischen die Kaempfer, aber seitlich versetzt (nicht in sie hinein), Blick auf den Getroffenen
		local mid = (ra.Position + rb.Position) / 2
		local line = Vector3.new(rb.Position.X - ra.Position.X, 0, rb.Position.Z - ra.Position.Z)
		local perp = line.Magnitude > 0.1 and Vector3.new(-line.Z, 0, line.X).Unit or Vector3.xAxis
		if (ref.root.Position - (mid + perp)).Magnitude > (ref.root.Position - (mid - perp)).Magnitude then perp = -perp end
		local goal = mid + perp * 2.6
		local t0 = os.clock()
		while ref.model.Parent and os.clock() - t0 < 1.6 do
			local dt = RunService.Heartbeat:Wait()
			if moveTowards(ref, goal, mid, RUN_SPEED, dt) < 0.3 then break end
		end
		if ref.model.Parent then play(ref, "Ref_Stop", 0.1) end
	end)
end

local function raiseHand(ref)
	ref.mode = "raise"
	task.spawn(function()
		local state = ref.state
		local w = state:GetAttribute("Winner")
		local a, b = fightersOf(state)
		local winner = (w == "red" and a) or (w == "blue" and b) or nil
		local wr = rootOf(winner)
		if not wr then ref.mode = "watch"; return end
		local alive = function() return refs[state.Name] == ref and ref.model.Parent ~= nil end
		task.wait(0.5)
		if not alive() then return end
		-- links neben dem Sieger (aus dessen Sicht), gleiche Blickrichtung; Abstand 0,55 m wie in Blender
		local cf = wr.CFrame
		local goal = (cf * CFrame.new(-0.55 / 0.28, 0, 0)).Position
		local t0 = os.clock()
		while alive() and os.clock() - t0 < 2 do
			local dt = RunService.Heartbeat:Wait()
			if moveTowards(ref, goal, goal + cf.LookVector * 5, RUN_SPEED, dt) < 0.15 then break end
		end
		if not alive() then return end
		ref.root.CFrame = CFrame.lookAt(Vector3.new(goal.X, ref.root.Position.Y, goal.Z), Vector3.new(goal.X, ref.root.Position.Y, goal.Z) + cf.LookVector)
		for _, n in ipairs({ "Ref_Stop", "Ref_Fight" }) do local t = ref.tracks[n]; if t then t:Stop(0.2) end end
		local rt = play(ref, "Ref_RaiseHand", 0.2)
		local wa = winner:FindFirstChildWhichIsA("Animator", true)
		local an = animFor("Fighter_WinRaise")
		if wa and an then
			local wt = wa:LoadAnimation(an); wt.Priority = Enum.AnimationPriority.Action4; wt:Play(0.2)
			ref.winTrack = wt
			-- Sicherheit: Pose endet spaetestens, wenn der Sieger den Kampf verlaesst
			local c; c = winner:GetAttributeChangedSignal("CC_MatchId"):Connect(function() c:Disconnect(); pcall(function() wt:Stop(0.3) end) end)
			task.delay(12, function() if c.Connected then c:Disconnect() end; pcall(function() wt:Stop(0.3) end) end)
		end
		if rt then rt.Stopped:Wait() end
		if not alive() then if ref.winTrack then pcall(function() ref.winTrack:Stop(0.3) end) end return end
		local t = ref.tracks["Ref_RaiseHand"]
		if t then t:Play(0); t.TimePosition = t.Length * 0.85; t:AdjustSpeed(0) end      -- Arm oben halten bis zum Ende
		if ref.winTrack then ref.winTrack.TimePosition = ref.winTrack.Length * 0.85; ref.winTrack:AdjustSpeed(0) end
	end)
end

local function removeRef(id)
	local ref = refs[id]; refs[id] = nil
	if not ref then return end
	if ref.winTrack then pcall(function() ref.winTrack:Stop(0.3) end) end
	ref.model:Destroy()
end

local ACTIVE = { walkout = true, intro = true, fight = true, ["break"] = true, finisher = true, over = true }
local function onState(state)
	if state.Name == "idle" then return end
	local function check()
		local st, mode = state:GetAttribute("State"), state:GetAttribute("Mode")
		local ref = refs[state.Name]
		if not ACTIVE[st] or mode == "tutorial" then if ref then removeRef(state.Name) end return end
		if not ref then ref = spawnRef(state); refs[state.Name] = ref end
		if not ref then return end
		if st == "over" and ref.mode ~= "raise" and (state:GetAttribute("Winner") == "red" or state:GetAttribute("Winner") == "blue") then raiseHand(ref) end
		if st == "intro" or st == "fight" then if ref.mode ~= "watch" and ref.mode ~= "stop" then ref.mode = "watch" end end
	end
	state.AttributeChanged:Connect(function(k)
		if k == "State" or k == "Mode" or k == "Winner" then check() end
		local ref = refs[state.Name]
		if not ref then return end
		if k == "Banner" and state:GetAttribute("Banner") == "FIGHT!" then ref.mode = "watch"; play(ref, "Ref_Fight", 0.1) end
		if k == "Stoppage" and (state:GetAttribute("Stoppage") or "") ~= "" and ref.mode ~= "stop" then stopFight(ref) end
	end)
	check()
end
local root = REG.root()
root.ChildAdded:Connect(onState)
root.ChildRemoved:Connect(function(c) removeRef(c.Name) end)
for _, c in ipairs(root:GetChildren()) do onState(c) end

-- Beobachten: seitlich der Kaempfer mitgehen, Blick zur Mitte
RunService.Heartbeat:Connect(function(dt)
	for id, ref in pairs(refs) do
		if ref.mode == "watch" and ref.model.Parent then
			local a, b = fightersOf(ref.state)
			local ra, rb = rootOf(a), rootOf(b)
			if ra and rb then
				local spot, mid = watchSpot(ref, ra.Position, rb.Position)
				local left = moveTowards(ref, spot, mid, SPEED, dt)
				local walking = left > 0.6
				local wt = ref.tracks["Fighter_CasualWalk_v2"]
				if walking and not (wt and wt.IsPlaying) then play(ref, "Fighter_CasualWalk_v2", 0.2, true)
				elseif not walking and wt and wt.IsPlaying then wt:Stop(0.3) end
			end
		end
	end
end)
print("[CC] Ringrichter bereit (" .. (SS:FindFirstChild("CC_Referee") and "Modell" or "Platzhalter") .. ")")
