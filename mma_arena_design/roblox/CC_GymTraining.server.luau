-- ServerScriptService.CC_GymTraining
-- Trainings-Stationen im Gym (Interaktionspunkte aus Workspace.CC_GymInteractions, angelegt von setup_gym_v01).
-- Training = Minispiel (Client: CC_Minigame), der Server prueft und belohnt:
--   Sandsack/Standsack (punch_bag, punch_bag_standing): Tastenfolge (Q E R F) in Reihenfolge, jeder Treffer = Schlag am Sack -> Schlagkraft
--   Hantelbank im Rack (bench_press): Rhythmus, Leertaste im Takt, liegt mit Langhantel auf der Bank -> Schlagkraft
--   Kurzhanteln (bench_dumbbell): Rhythmus, Q/E abwechselnd (links/rechts), Kurzhanteln in beiden Haenden -> Schlagkraft
--   Matten (stretch_spot): Rhythmus, schnelle Leertaste, Hampelmann -> Kondition
--   Trainer-Tisch (coach_talk): Trainingskampf; Trainingsplan (read_plan): eigene Werte; Spiegel/Spinde: Kaempfer-Anpassung
-- Ablauf: Station -> Aufstellung (HumanoidRootPart verankert) -> Attribut CC_Minigame (JSON) am Spieler -> Client meldet je Aufgabe
-- "hit"/"miss" ueber ReplicatedStorage.CC_Train -> Wirkung sofort (Schlag, Wiederholung, Stocken) -> am Ende Trainingspunkte
-- nach Trefferquote (>= 90 %: 3, >= 60 %: 2, >= 30 %: 1) und XP je Treffer. Gewichte werden als Kopien der Gym-Hanteln
-- in Workspace.CC_Props gelegt; die Clients halten sie in den Haenden (CC_Props.client).
local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local HS = game:GetService("HttpService")
local SS = game:GetService("ServerStorage")
local RS = game.ReplicatedStorage
local KSP = game:GetService("KeyframeSequenceProvider")

local folder = workspace:WaitForChild("CC_GymInteractions", 60)
if not folder then return end
local gym = workspace:FindFirstChild("CC_Gym")

local ANIM = SS.CC_Animations
local IDS = ANIM:FindFirstChild("CC_AnimIds") and require(ANIM.CC_AnimIds) or {}
local function animOf(name)
	local a = Instance.new("Animation")
	a.AnimationId = IDS[name] and ("rbxassetid://" .. IDS[name]) or KSP:RegisterKeyframeSequence(ANIM[name])
	return a
end
local COMBO = { animOf("Fighter_Jab_v03"), animOf("Fighter_Cross_v03"), animOf("Fighter_Hook_v03"), animOf("Fighter_Uppercut_v02") }
local EX = { bench = animOf("Fighter_ExBenchPress_v01"), curl = animOf("Fighter_ExCurl_v01"), jack = animOf("Fighter_ExJumpingJack_v2") }

local trainEv = RS:FindFirstChild("CC_Train") or Instance.new("RemoteEvent"); trainEv.Name = "CC_Train"; trainEv.Parent = RS
local propsF = workspace:FindFirstChild("CC_Props") or Instance.new("Folder"); propsF.Name = "CC_Props"; propsF.Parent = workspace

local function profile(p, kind, a, b)
	local ev = SS:FindFirstChild("CC_ProfileEvent")
	if ev then ev:Fire(p, kind, a, b) end
end
local function notice(p, text) p:SetAttribute("CC_Notice", text .. "|" .. tostring(workspace:GetServerTimeNow())) end

-- ---------- Uebungen ----------
local KINDS = {
	bag = { label = "Sandsack", stat = "Power", game = "seq", n = 10, time = 7.0, cam = "side" },
	bench = { label = "Bankdrücken", stat = "Power", game = "rhythm", n = 8, interval = 1.2, keys = { "Space" }, anim = "bench", prop = "barbell", cam = "bench" },
	curl = { label = "Kurzhantel-Curls", stat = "Power", game = "rhythm", n = 10, interval = 0.95, keys = { "Q", "E" }, anim = "curl", prop = "dumbbells", cam = "front" },
	jack = { label = "Hampelmann", stat = "Cardio", game = "rhythm", n = 14, interval = 0.62, keys = { "Space" }, anim = "jack", cam = "front" },
}
local SEQ_KEYS = { "Q", "E", "R", "F" }
local LEAD = 1.6                 -- Sekunden Vorlauf (Countdown) bis zur ersten Aufgabe

local sessions = {}              -- [player] = Sitzung
local nextId = 0

local function canTrain(p)
	local c = p.Character
	return c and c:FindFirstChild("HumanoidRootPart") and not sessions[p] and not c:GetAttribute("CC_Opponent") and not c:GetAttribute("CC_Wrestle")
end

-- ---------- Sack schwingen lassen ----------
local bagParts = {}
local function partsOf(name)
	if bagParts[name] then return bagParts[name] end
	local list = {}
	if gym then
		for _, d in ipairs(gym:GetDescendants()) do
			if d:IsA("BasePart") and (d.Name == name or d.Name:sub(1, #name + 2) == name .. "__") then table.insert(list, { part = d, cf = d.CFrame }) end
		end
	end
	bagParts[name] = list
	return list
end
local function swing(marker, dir, strength)
	local list = partsOf(marker.Name)
	if #list == 0 then return end
	local pivot = marker.Position + Vector3.new(0, marker.Size.Y / 2, 0)
	local axis = Vector3.new(0, 1, 0):Cross(dir.Unit)
	if axis.Magnitude < 0.01 then return end
	axis = axis.Unit
	local v = Instance.new("NumberValue")
	local conn = v.Changed:Connect(function(a)
		local rot = CFrame.new(pivot) * CFrame.fromAxisAngle(axis, a) * CFrame.new(-pivot)
		for _, e in ipairs(list) do e.part.CFrame = rot * e.cf end
	end)
	local t1 = TweenService:Create(v, TweenInfo.new(0.15, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Value = math.rad(strength) })
	local t2 = TweenService:Create(v, TweenInfo.new(0.9, Enum.EasingStyle.Elastic, Enum.EasingDirection.Out), { Value = 0 })
	t1.Completed:Connect(function() t2:Play() end)
	t2.Completed:Connect(function() conn:Disconnect(); v:Destroy() end)
	t1:Play()
end
local function hitSound(marker)
	local sfx = game:GetService("SoundService"):FindFirstChild("CC_Sounds")
	local s = sfx and (sfx:FindFirstChild("Hit") or sfx:FindFirstChildWhichIsA("Sound"))
	if s then local c = s:Clone(); c.Parent = marker; c:Play(); game:GetService("Debris"):AddItem(c, 2) end
end

-- ---------- Gewichte (Kopien der Gym-Hanteln) ----------
local function gymPart(name) return gym and gym:FindFirstChild(name, true) end
local function propModel(char, parts, mode, bone, pivotPart)
	local m = Instance.new("Model"); m.Name = "CC_Prop_" .. char.Name
	for _, src in ipairs(parts) do
		local c = src:Clone()
		c.Anchored = true; c.CanCollide = false; c.CanQuery = false; c.CanTouch = false; c.CastShadow = true
		c.PivotOffset = CFrame.new()          -- importierte Teile haben ihren Bezugspunkt am Import-Ursprung (weit weg)
		for _, ch in ipairs(c:GetChildren()) do if not ch:IsA("SpecialMesh") and not ch:IsA("SurfaceAppearance") then ch:Destroy() end end
		c.Parent = m
		if src == pivotPart then m.PrimaryPart = c end
	end
	m:SetAttribute("Owner", char.Name); m:SetAttribute("Mode", mode); m:SetAttribute("Bone", bone)
	m.Parent = propsF
	return m
end
local hiddenBar = {}
local function makeProps(p, kind)
	local char = p.Character
	local out = {}
	if kind == "dumbbells" then
		local head, handle = gymPart("Dumbbell_M_A__GY_Bumper_Black"), gymPart("Dumbbell_M_A__GY_Chrome")
		if head and handle then
			table.insert(out, propModel(char, { head, handle }, "hand", "LeftHand", handle))
			table.insert(out, propModel(char, { head, handle }, "hand", "RightHand", handle))
		end
	elseif kind == "barbell" then
		local bar = gymPart("Barbell")
		if bar then
			local list = { bar }
			for _, d in ipairs(gym:GetDescendants()) do if d:IsA("BasePart") and d.Name:find("^Barbell_Plate_") then table.insert(list, d) end end
			table.insert(out, propModel(char, list, "between", "LeftHand,RightHand", bar))
			for _, d in ipairs(list) do hiddenBar[d] = d.Transparency; d.Transparency = 1 end   -- Stange im Rack waehrenddessen ausblenden
		end
	end
	return out
end
local function clearProps(s)
	for _, m in ipairs(s.props or {}) do m:Destroy() end
	if s.kindDef.prop == "barbell" then
		for d, t in pairs(hiddenBar) do d.Transparency = t end
		hiddenBar = {}
	end
end

-- ---------- Aufstellung ----------
local function faceStation(p, marker, dist)
	local root = p.Character.HumanoidRootPart
	local mp = Vector3.new(marker.Position.X, root.Position.Y, marker.Position.Z)
	local away = Vector3.new(root.Position.X, 0, root.Position.Z) - Vector3.new(mp.X, 0, mp.Z)
	away = away.Magnitude > 0.1 and away.Unit or Vector3.new(0, 0, 1)
	root.CFrame = CFrame.lookAt(mp + away * dist, mp)
	return -away
end
local function place(p, marker, kind)
	local root = p.Character.HumanoidRootPart
	local y = root.Position.Y
	if kind == "bench" then
		local rack = folder:FindFirstChild("Power_Rack")
		local c = Vector3.new(marker.Position.X, y, marker.Position.Z)
		local dir
		if rack then dir = c - Vector3.new(rack.Position.X, y, rack.Position.Z) end
		if not dir or dir.Magnitude < 0.3 then dir = marker.Size.X > marker.Size.Z and Vector3.new(1, 0, 0) or Vector3.new(0, 0, 1) end
		dir = dir.Unit
		root.CFrame = CFrame.lookAt(c + dir * 0.6, c + dir * 5)        -- Blick = Richtung Fuesse (die Animation liegt nach hinten)
	elseif kind == "jack" then
		-- Mitte der Matte, Blick entlang der Matte in die Halle (nicht zur Wand)
		local c = Vector3.new(marker.Position.X, y, marker.Position.Z)
		local long = marker.Size.X >= marker.Size.Z and Vector3.new(1, 0, 0) or Vector3.new(0, 0, 1)
		local toHall = Vector3.new(160, y, 0) - c
		local dir = long:Dot(toHall) >= 0 and long or -long
		if math.abs(long:Dot(toHall.Unit)) < 0.3 then dir = toHall.Unit end
		root.CFrame = CFrame.lookAt(c, c + dir)
	elseif kind == "bag" then
		return faceStation(p, marker, 3.6)
	else
		-- Curls: neben der Hantelbank, Blick von der Bank weg (Kamera von vorn ohne Bank im Bild)
		local d = faceStation(p, marker, 2.8)
		local r = p.Character.HumanoidRootPart
		r.CFrame = CFrame.lookAt(r.Position, r.Position - d)
	end
end

-- ---------- Sitzung ----------
local function finish(p, s, reason)
	if sessions[p] ~= s then return end
	sessions[p] = nil
	p:SetAttribute("CC_Minigame", nil)
	if s.track then s.track:Stop(0.3) end
	clearProps(s)
	local root = s.root
	if root and root.Parent then
		if s.kind == "bench" then root.CFrame = s.startCF end
		root.Anchored = false
	end
	if not p.Parent then return end
	local rate = s.hits / s.n
	local tp = rate >= 0.9 and 3 or rate >= 0.6 and 2 or rate >= 0.3 and 1 or 0
	if tp > 0 then profile(p, "train", s.kindDef.stat, tp) end
	profile(p, "xp", s.hits)
	local statName = s.kindDef.stat == "Power" and "Schlagkraft" or "Kondition"
	notice(p, ("%s: %d/%d getroffen – %s +%d TP, +%d XP"):format(s.kindDef.label, s.hits, s.n, statName, tp, s.hits))
	print(("[CC] Training %s %s: %d/%d (%s) -> %d TP"):format(p.Name, s.kind, s.hits, s.n, reason, tp))
end

local function start(p, marker, kind)
	if not canTrain(p) then return end
	local def = KINDS[kind]
	local char = p.Character
	local root = char.HumanoidRootPart
	local hum = char:FindFirstChildOfClass("Humanoid")
	local animator = hum and hum:FindFirstChildOfClass("Animator")
	nextId += 1
	local s = { id = nextId, kind = kind, kindDef = def, marker = marker, n = def.n, hits = 0, misses = 0, done = {}, root = root,
		startCF = root.CFrame, combo = 0 }
	sessions[p] = s
	s.dir = place(p, marker, kind)
	root.Anchored = true
	if def.anim and animator then
		s.track = animator:LoadAnimation(EX[def.anim]); s.track.Priority = Enum.AnimationPriority.Action; s.track.Looped = true
		s.track:Play(0.3); s.track:AdjustSpeed(0)                  -- steht still bis zum ersten Treffer
	end
	if def.prop then s.props = makeProps(p, def.prop) end
	-- Aufgaben festlegen (Server), Client zeigt sie an
	local keys = {}
	for i = 1, def.n do
		if def.game == "seq" then keys[i] = SEQ_KEYS[math.random(#SEQ_KEYS)]
		else keys[i] = def.keys[(i - 1) % #def.keys + 1] end
	end
	s.keys = keys
	s.t0 = workspace:GetServerTimeNow() + LEAD
	s.deadline = def.game == "seq" and (s.t0 + def.time) or (s.t0 + def.n * def.interval + 0.6)
	p:SetAttribute("CC_Minigame", HS:JSONEncode({ id = s.id, kind = kind, game = def.game, label = def.label, keys = keys,
		interval = def.interval, n = def.n, time = def.time, start = s.t0, cam = def.cam }))
	task.delay(s.deadline - workspace:GetServerTimeNow() + 1.0, function() finish(p, s, "Zeit") end)
end

-- Rueckmeldung des Clients je Aufgabe
trainEv.OnServerEvent:Connect(function(p, what, id, i)
	local s = sessions[p]
	if not s or id ~= s.id or type(i) ~= "number" or i < 1 or i > s.n or s.done[i] then return end
	local now = workspace:GetServerTimeNow()
	local def = s.kindDef
	if def.game == "rhythm" and now < s.t0 + (i - 1) * def.interval - 0.6 then return end   -- zu frueh: ignorieren (Schutz)
	if now > s.deadline + 0.8 then return end
	s.done[i] = true
	if what == "hit" then
		s.hits += 1
		if s.kind == "bag" then
			s.combo += 1
			local animator = p.Character and p.Character:FindFirstChildOfClass("Humanoid") and p.Character.Humanoid:FindFirstChildOfClass("Animator")
			if animator then
				local tr = animator:LoadAnimation(COMBO[(s.combo - 1) % #COMBO + 1]); tr.Priority = Enum.AnimationPriority.Action; tr:Play(0.05)
			end
			task.delay(0.18, function() swing(s.marker, s.dir or Vector3.new(1, 0, 0), 5 + math.min(s.combo, 6)); hitSound(s.marker) end)
		elseif s.track then
			-- eine Wiederholung im Takt abspielen (Animationstempo an den Takt angepasst)
			local repLen = s.track.Length / (s.kind == "curl" and 2 or 1)
			s.track:AdjustSpeed(repLen / def.interval)
			s.lastHit = now
		end
	else
		s.misses += 1
		if s.kind == "bag" then s.combo = 0
		elseif s.track then
			s.track:AdjustSpeed(0.15)                                   -- Stocken: Kaempfer kaempft mit dem Gewicht
			local mark = now
			s.lastMiss = mark
			task.delay(0.5, function() if s.track and s.lastMiss == mark and sessions[p] == s then s.track:AdjustSpeed(0) end end)
		end
	end
	if s.hits + s.misses >= s.n then task.delay(0.5, function() finish(p, s, "fertig") end) end
end)
-- Wiederholungs-Animation nach einem Treffer anhalten, wenn der naechste Takt nicht getroffen wird
game:GetService("RunService").Heartbeat:Connect(function()
	local now = workspace:GetServerTimeNow()
	for _, s in pairs(sessions) do
		if s.track and s.lastHit and s.kindDef.interval and now - s.lastHit > s.kindDef.interval * 1.05 and (not s.lastMiss or s.lastMiss < s.lastHit) then
			s.track:AdjustSpeed(0); s.lastHit = nil
		end
	end
end)

local function statText(p)
	return ("Level %d · Schlagkraft %d · Kondition %d · Ringen %d · Bodenkampf %d · Bilanz %d-%d"):format(
		p:GetAttribute("CC_Level") or 1, p:GetAttribute("CC_Power") or 0, p:GetAttribute("CC_Cardio") or 0,
		p:GetAttribute("CC_Wrestling") or 0, p:GetAttribute("CC_Grappling") or 0, p:GetAttribute("CC_Wins") or 0, p:GetAttribute("CC_Losses") or 0)
end

local STATIONS = {
	punch_bag = { "Sandsack", "Training starten", function(p, m) start(p, m, "bag") end },
	punch_bag_standing = { "Standsack", "Training starten", function(p, m) start(p, m, "bag") end },
	bench_dumbbell = { "Kurzhanteln", "Curls trainieren", function(p, m) start(p, m, "curl") end },
	bench_press = { "Hantelbank", "Bankdrücken", function(p, m) start(p, m, "bench") end },
	stretch_spot = { "Trainingsmatte", "Hampelmann", function(p, m) start(p, m, "jack") end },
	coach_talk = { "Trainer", "Trainingskampf starten", function(p)
		notice(p, "Trainer: Zeig mir, was du kannst! Trainingskampf startet …")
		local be = SS:FindFirstChild("CC_MenuServer")      -- gleiche Warteschlange wie das Menue (CC_Match)
		if be then be:Fire(p, "training") end
	end },
	character_customization = { "Spiegel", "Kämpfer anpassen", function(p) p:SetAttribute("CC_OpenCustomize", os.clock()) end },
	locker = { "Spind", "Kämpfer anpassen", function(p) p:SetAttribute("CC_OpenCustomize", os.clock()) end },
	read_plan = { "Trainingsplan", "Ansehen", function(p) notice(p, statText(p)) end },
}

local n = 0
for _, marker in ipairs(folder:GetChildren()) do
	local st = STATIONS[marker:GetAttribute("CC_Interaction")]
	if st and marker:IsA("BasePart") then
		for _, old in ipairs(marker:GetChildren()) do if old:IsA("ProximityPrompt") then old:Destroy() end end
		local pr = Instance.new("ProximityPrompt")
		pr.ObjectText = st[1]; pr.ActionText = st[2]; pr.KeyboardKeyCode = Enum.KeyCode.E; pr.GamepadKeyCode = Enum.KeyCode.ButtonX
		pr.HoldDuration = 0; pr.MaxActivationDistance = 7; pr.RequiresLineOfSight = false
		pr.Triggered:Connect(function(p)
			task.spawn(function()
				local ok, err = pcall(st[3], p, marker)
				if not ok then warn("[CC] Station " .. marker.Name .. " Fehler: " .. tostring(err)); local s_ = sessions[p]; if s_ then sessions[p] = nil; clearProps(s_); if s_.root then s_.root.Anchored = false end; p:SetAttribute("CC_Minigame", nil) end end
			end)
		end)
		pr.Parent = marker
		n += 1
	end
end
Players.PlayerRemoving:Connect(function(p) local s = sessions[p]; if s then clearProps(s); sessions[p] = nil end end)
print("[CC] Gym-Training: " .. n .. " Stationen (Minispiele)")
