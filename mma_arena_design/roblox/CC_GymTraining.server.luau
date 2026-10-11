-- ServerScriptService.CC_GymTraining
-- Trainings-Stationen im Gym (Interaktionspunkte aus Workspace.CC_GymInteractions, angelegt von setup_gym_v01):
--   Sandsaecke (punch_bag, punch_bag_standing): Schlagkombination am Sack -> Schlagkraft (Power) + XP, der Sack schwingt
--   Hantelbank / Bank im Rack (bench_dumbbell, bench_press): Krafttraining -> Schlagkraft
--   Matten (stretch_spot): Dehnen/Ausdauer -> Kondition (Cardio)
--   Trainer-Tisch (coach_talk): Trainingskampf gegen den Trainingsgegner (wie Menue TRAINING)
--   Trainingsplan (read_plan): zeigt die eigenen Werte
--   Spiegel/Spinde in der Umkleide (character_customization, locker): oeffnet die Kaempfer-Anpassung im Menue
-- Fortschritt ueber ServerStorage.CC_ProfileEvent (CC_Profile). Hinweise an den Spieler: Attribut CC_Notice ("Text|Zeit").
-- Uebungs-Animationen (Fighter_Rigged_v13): Bankdruecken (liegt auf der Bank, Kopf unter der Stange), Kurzhantel-Curls, Hampelmann.
-- Waehrend einer Uebung ist das HumanoidRootPart verankert (kein Wegschieben durch die Bank, kein Laufen).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local SS = game:GetService("ServerStorage")
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
local COMBO = { animOf("Fighter_Jab_v03"), animOf("Fighter_Cross_v03"), animOf("Fighter_Hook_v03"), animOf("Fighter_Jab_v03"), animOf("Fighter_Uppercut_v02") }
local COMBO_GAP = { 0.42, 0.55, 0.62, 0.42, 0.7 }
local EX = { bench = animOf("Fighter_ExBenchPress_v01"), curl = animOf("Fighter_ExCurl_v01"), jack = animOf("Fighter_ExJumpingJack_v01") }

local function profile(p, kind, a, b)
	local ev = SS:FindFirstChild("CC_ProfileEvent")
	if ev then ev:Fire(p, kind, a, b) end
end
local function notice(p, text) p:SetAttribute("CC_Notice", text .. "|" .. tostring(workspace:GetServerTimeNow())) end

local busy = {}                  -- [player] = true waehrend einer Uebung
local function canTrain(p)
	local c = p.Character
	return c and c:FindFirstChild("HumanoidRootPart") and not busy[p] and not c:GetAttribute("CC_Opponent") and not c:GetAttribute("CC_Wrestle")
end

-- Sack schwingen lassen: alle Gym-Teile dieses Sacks um den Aufhaengepunkt drehen
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

local function faceStation(p, marker, dist)
	local root = p.Character.HumanoidRootPart
	local mp = Vector3.new(marker.Position.X, root.Position.Y, marker.Position.Z)
	local away = Vector3.new(root.Position.X, 0, root.Position.Z) - Vector3.new(mp.X, 0, mp.Z)
	away = away.Magnitude > 0.1 and away.Unit or Vector3.new(0, 0, 1)
	local pos = mp + away * dist
	root.CFrame = CFrame.lookAt(pos, mp)
	return -away
end

local function bagCombo(p, marker)
	if not canTrain(p) then return end
	busy[p] = true
	local hum = p.Character:FindFirstChildOfClass("Humanoid")
	local animator = hum and hum:FindFirstChildOfClass("Animator")
	local dir = faceStation(p, marker, 3.6)
	local root = p.Character.HumanoidRootPart
	root.Anchored = true
	for i, a in ipairs(COMBO) do
		if not p.Character then break end
		local tr = animator:LoadAnimation(a)
		tr.Priority = Enum.AnimationPriority.Action
		tr:Play(0.05)
		task.delay(0.2, function() swing(marker, dir, 6 + i) end)
		local sfx = game:GetService("SoundService"):FindFirstChild("CC_Sounds")
		local s = sfx and (sfx:FindFirstChild("Hit") or sfx:FindFirstChildWhichIsA("Sound"))
		if s then task.delay(0.2, function() local c = s:Clone(); c.Parent = marker; c:Play(); game:GetService("Debris"):AddItem(c, 2) end) end
		task.wait(COMBO_GAP[i])
	end
	if root.Parent then root.Anchored = false end
	profile(p, "train", "Power", 1); profile(p, "xp", 3)
	notice(p, "Sandsack: Schlagkraft +1 Trainingspunkt")
	busy[p] = nil
end

-- Aufstellung je Uebung: Bank = auf der Bank liegend (Becken nahe Bankmitte, Fuesse vom Rack weg), sonst vor bzw. auf der Station
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
		root.CFrame = CFrame.lookAt(c + dir * 0.6, c + dir * 5)        -- Blick = Richtung Fuesse (Animation liegt nach hinten)
	elseif kind == "jack" then
		local c = Vector3.new(marker.Position.X, y, marker.Position.Z)
		local toward = Vector3.new(160, y, 0)                             -- Blick in die Halle
		root.CFrame = CFrame.lookAt(c, (toward - c).Magnitude > 0.5 and toward or c + Vector3.new(0, 0, 1))
	else
		faceStation(p, marker, 2.6)
	end
end

local function holdExercise(p, marker, statName, seconds, label, kind)
	if not canTrain(p) then return end
	busy[p] = true
	local hum = p.Character:FindFirstChildOfClass("Humanoid")
	local animator = hum and hum:FindFirstChildOfClass("Animator")
	local root = p.Character.HumanoidRootPart
	local startCF = root.CFrame
	place(p, marker, kind)
	root.Anchored = true
	local tr = animator and EX[kind] and animator:LoadAnimation(EX[kind])
	if tr then tr.Priority = Enum.AnimationPriority.Action; tr.Looped = true; tr:Play(0.3) end
	p:SetAttribute("CC_Exercise", label .. "|" .. tostring(workspace:GetServerTimeNow()) .. "|" .. seconds)
	local t0 = os.clock()
	while os.clock() - t0 < seconds and p.Character and root.Parent do task.wait(0.1) end
	p:SetAttribute("CC_Exercise", nil)
	if tr then tr:Stop(0.3) end
	if root.Parent then
		if kind == "bench" then root.CFrame = startCF end            -- vom Liegen zurueck an den Ausgangspunkt
		root.Anchored = false
	end
	if p.Character then
		profile(p, "train", statName, 1); profile(p, "xp", 3)
		notice(p, label .. ": " .. (statName == "Power" and "Schlagkraft" or "Kondition") .. " +1 Trainingspunkt")
	end
	busy[p] = nil
end

local function statText(p)
	return ("Level %d · Schlagkraft %d · Kondition %d · Ringen %d · Bodenkampf %d · Bilanz %d-%d"):format(
		p:GetAttribute("CC_Level") or 1, p:GetAttribute("CC_Power") or 0, p:GetAttribute("CC_Cardio") or 0,
		p:GetAttribute("CC_Wrestling") or 0, p:GetAttribute("CC_Grappling") or 0, p:GetAttribute("CC_Wins") or 0, p:GetAttribute("CC_Losses") or 0)
end

local STATIONS = {
	punch_bag = { "Sandsack", "Schlagen", function(p, m) bagCombo(p, m) end },
	punch_bag_standing = { "Standsack", "Schlagen", function(p, m) bagCombo(p, m) end },
	bench_dumbbell = { "Kurzhanteln", "Curls", function(p, m) holdExercise(p, m, "Power", 5, "Kurzhantel-Curls", "curl") end },
	bench_press = { "Hantelbank", "Bankdrücken", function(p, m) holdExercise(p, m, "Power", 5, "Bankdrücken", "bench") end },
	stretch_spot = { "Matte", "Hampelmann", function(p, m) holdExercise(p, m, "Cardio", 5, "Hampelmann", "jack") end },
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
		local pr = Instance.new("ProximityPrompt")
		pr.ObjectText = st[1]; pr.ActionText = st[2]; pr.KeyboardKeyCode = Enum.KeyCode.E; pr.GamepadKeyCode = Enum.KeyCode.ButtonX
		pr.HoldDuration = 0; pr.MaxActivationDistance = 7; pr.RequiresLineOfSight = false
		pr.Triggered:Connect(function(p) task.spawn(st[3], p, marker) end)
		pr.Parent = marker
		n += 1
	end
end
Players.PlayerRemoving:Connect(function(p) busy[p] = nil end)
print("[CC] Gym-Training: " .. n .. " Stationen")
