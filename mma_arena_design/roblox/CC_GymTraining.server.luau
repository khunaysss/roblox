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
-- Gewichtstraining als einzelne Wiederholungen (Fighter_Rigged_v18): Ruhepose (Loop) + je Treffer genau eine Wiederholung,
-- die letzten zwei langsamer mit Anstrengung (Grind), ein Fehler = Fehlversuch (stockt, Zittern). Alle starten/enden in der Ruhepose.
local function maybeAnim(name) return (IDS[name] or ANIM:FindFirstChild(name)) and animOf(name) or nil end
local EXR = {
	bench = { rest = maybeAnim("Fighter_ExBench_Rest"), rep = maybeAnim("Fighter_ExBench_Rep"), grind = maybeAnim("Fighter_ExBench_Grind"), fail = maybeAnim("Fighter_ExBench_Fail") },
	curl = { rest = maybeAnim("Fighter_ExCurl_Rest"), repL = maybeAnim("Fighter_ExCurl_RepL"), repR = maybeAnim("Fighter_ExCurl_RepR"),
		grindL = maybeAnim("Fighter_ExCurl_GrindL"), grindR = maybeAnim("Fighter_ExCurl_GrindR"), failL = maybeAnim("Fighter_ExCurl_FailL"), failR = maybeAnim("Fighter_ExCurl_FailR") },
}

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
	tread = { label = "Laufband", stat = "Cardio", game = "tread", n = 30, time = 30, keys = { "Q", "E" }, cam = "side" },   -- Laufband: 30 s Tempo halten
	jack = { label = "Hampelmann", stat = "Cardio", game = "rhythm", n = 14, interval = 0.62, keys = { "Space" }, anim = "jack", cam = "front" },
}
local SEQ_KEYS = { "Q", "E", "R", "F" }
local LEAD = 1.6                 -- Sekunden Vorlauf (Countdown) bis zur ersten Aufgabe

local sessions = {}              -- [player] = Sitzung
local nextId = 0

-- Abklingzeit nach Sitzungsende (Server): pro Spieler 1 s, pro Spieler und Station 1,5 s -> E (Prompt/Minispiel) startet nicht doppelt
local lastEnd = {}               -- [player] = { any = Zeit, [marker] = Zeit }
local function cooling(p, marker)
	local l = lastEnd[p]; if not l then return false end
	local now = os.clock()
	return now - (l.any or 0) < 1.0 or (marker and now - (l[marker] or 0) < 1.5)
end
local function canTrain(p, marker)
	local c = p.Character
	if cooling(p, marker) then return false end
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
	elseif kind == "tread" then
		-- auf dem Band stehen, Blick zur Konsole (+X); Hoehe = Bandoberkante + Standhoehe des HumanoidRootPart (wie auf dem Boden)
		local c = marker:GetAttribute("CC_BeltCenter") or marker.Position
		local rp = RaycastParams.new(); rp.FilterDescendantsInstances = { p.Character }
		local hit = workspace:Raycast(root.Position, Vector3.new(0, -10, 0), rp)
		local standH = hit and (y - hit.Position.Y) or 3.05
		local pos = Vector3.new(c.X, (marker:GetAttribute("CC_BeltTop") or 0.63) + standH, c.Z)
		root.CFrame = CFrame.lookAt(pos, pos + Vector3.new(1, 0, 0))
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
	if sessions[p] ~= s or s.ended then return end
	s.ended = true                                                -- jede Sitzung wird hoechstens einmal beendet/belohnt
	sessions[p] = nil
	lastEnd[p] = lastEnd[p] or {}; lastEnd[p].any = os.clock(); lastEnd[p][s.marker] = os.clock()
	p:SetAttribute("CC_Minigame", nil)
	for _, t in pairs(s.comboTracks or {}) do t:Stop(0.1) end
	if s.track then s.track:Stop(0.3) end
	if s.restTrack then s.restTrack:Stop(0.3) end
	for _, t in pairs(s.repTracks or {}) do if t.IsPlaying then t:Stop(0.25) end end
	if s.tread then
		for _, t in pairs(s.tread.tracks) do t:Stop(0.3) end
		if s.tread.model then s.tread.model:SetAttribute("CC_BeltSpeed", 0); s.tread.model:SetAttribute("CC_BeltKmh", 0) end
		p:SetAttribute("CC_Tread", nil)
	end
	-- Tracks dieser Sitzung nach dem Ausblenden freigeben (sonst sammeln sie sich pro Sitzung im Animator an)
	local all = {}
	for _, g in ipairs({ { s.track or false, s.restTrack or false }, s.comboTracks or {}, s.repTracks or {}, s.tread and s.tread.tracks or {} }) do
		for _, t in pairs(g) do if t then table.insert(all, t) end end
	end
	task.delay(0.5, function() for _, t in pairs(all) do t:Destroy() end end)
	clearProps(s)
	local root = s.root
	if root and root.Parent then
		if s.kind == "bench" or s.kind == "tread" then root.CFrame = s.startCF end   -- von Bank/Band zurueck an den Ausgangspunkt
		root.Anchored = false
	end
	if not p.Parent then return end
	-- Belohnung nur bei gueltigem Abschluss (Server: alle Aufgaben gewertet bzw. Zeit abgelaufen); Abbruch (manuell, Tod, Reset) = 0 XP/0 TP
	local valid = reason == "fertig" or reason == "Zeit"
	local rate = s.hits / s.n
	local tp = valid and (rate >= 0.9 and 3 or rate >= 0.6 and 2 or rate >= 0.3 and 1 or 0) or 0
	if tp > 0 then profile(p, "train", s.kindDef.stat, tp) end
	local xp = not valid and 0 or (s.kind == "tread" and math.floor(s.hits / 2) or s.hits)   -- Laufband: 30 s -> hoechstens 15 XP
	if xp > 0 then profile(p, "xp", xp) end
	-- Ergebnis fuer die Trainings-Anzeige (CC_Minigame): echte Belohnung wie oben vergeben
	p:SetAttribute("CC_TrainResult", HS:JSONEncode({ id = s.id, kind = s.kind, label = s.kindDef.label, stat = s.kindDef.stat,
		hits = s.hits, n = s.n, tp = tp, xp = xp, reason = reason }))
	print(("[CC] Training %s %s: %d/%d (%s) -> %d TP"):format(p.Name, s.kind, s.hits, s.n, reason, tp))
end

local lastStation = {}         -- [player] = { marker, kind } fuer "Nochmal"
local function start(p, marker, kind)
	if not canTrain(p, marker) then return end
	lastStation[p] = { marker, kind }
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
	local set = def.anim and EXR[def.anim]
	if set and set.rest and animator then                          -- Gewichte: Ruhepose halten, Wiederholungen einzeln
		s.reps, s.animator, s.repTracks = set, animator, {}
		s.restTrack = animator:LoadAnimation(set.rest); s.restTrack.Priority = Enum.AnimationPriority.Action; s.restTrack.Looped = true
		s.restTrack:Play(0.3)
	elseif def.anim and animator then
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
	s.deadline = (def.game == "seq" or def.game == "tread") and (s.t0 + def.time) or (s.t0 + def.n * def.interval + 0.6)
	if def.game == "tread" and animator then                        -- Laufband: Gehen/Laufen auf der Stelle (Standfuss gleitet mit dem Band)
		local tr = {}
		for k, n in pairs({ walk = "Fighter_CasualWalk_v2", run = "Fighter_CasualRun_v3", stand = "Fighter_CasualIdle_v01" }) do
			local a = maybeAnim(n)
			if a then
				tr[k] = animator:LoadAnimation(a); tr[k].Priority = Enum.AnimationPriority.Action; tr[k].Looped = true
				tr[k]:Play(0.3, k == "stand" and 1 or 0.001, 1)
			end
		end
		s.tread = { speed = 0, target = 7.0, lastTarget = 7.0, nextChange = s.t0 + 6, stamina = 100, inBand = 0, input = 0, tracks = tr, lastPub = 0,
			model = workspace:FindFirstChild("CC_Gym") and workspace.CC_Gym:FindFirstChild("Treadmill_1") }
	end
	p:SetAttribute("CC_Minigame", HS:JSONEncode({ id = s.id, kind = kind, game = def.game, label = def.label, keys = keys,
		interval = def.interval, n = def.n, time = def.time, start = s.t0, cam = def.cam }))
	task.delay(s.deadline - workspace:GetServerTimeNow() + 1.0, function() finish(p, s, "Zeit") end)
end

-- eine Wiederholung abspielen (Treffer) bzw. Fehlversuch; Dauer passt in den Takt, damit die naechste Eingabe frei ist
local function playRep(s, i, ok)
	local side = s.kind == "curl" and ((s.keys[i] == "Q") and "L" or "R") or ""
	local base = (not ok) and "fail" or (i >= s.n - 1 and "grind" or "rep")   -- letzte zwei: langsamer mit Anstrengung
	local key = base .. side
	if not s.reps[key] then return end
	local tr = s.repTracks[key]
	if not tr then
		tr = s.animator:LoadAnimation(s.reps[key]); tr.Priority = Enum.AnimationPriority.Action2; tr.Looped = false
		s.repTracks[key] = tr
	end
	for _, t in pairs(s.repTracks) do if t ~= tr and t.IsPlaying then t:Stop(0.12) end end   -- Ende jeder Wiederholung = Ruhepose -> weicher Uebergang
	local dur = s.kindDef.interval * (base == "rep" and 0.85 or 0.98)
	if tr.IsPlaying then tr:Stop(0) end
	tr:Play(0.08, 1, tr.Length / dur)
end

-- Rueckmeldung des Clients je Aufgabe
trainEv.OnServerEvent:Connect(function(p, what, id, i)
	if what == "tempo" then                                         -- Laufband: -1 langsamer, 0 nichts, +1 schneller (gehalten)
		local s_ = sessions[p]
		if s_ and s_.tread and s_.id == id and (i == -1 or i == 0 or i == 1) then s_.tread.input = i end
		return
	end
	if what == "abort" then                                         -- Minispiel abbrechen (Ruecktaste / Select): sauber beenden
		local s_ = sessions[p]
		if s_ and s_.id == id then finish(p, s_, "Abbruch") end
		return
	end
	if what == "again" then                                         -- gleiche Station noch einmal
		local l, c = lastStation[p], p.Character
		local root = c and c:FindFirstChild("HumanoidRootPart")
		if l and root and l[1].Parent and (root.Position - l[1].Position).Magnitude < 14 then
			task.spawn(function()
				local t0 = os.clock()
				while cooling(p, l[1]) and os.clock() - t0 < 2 do task.wait(0.1) end   -- Abklingzeit abwarten (kein Doppelstart)
				local ok, err = pcall(start, p, l[1], l[2]); if not ok then warn("[CC] Nochmal: " .. tostring(err)) end
			end)
		end
		return
	end
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
			if animator then                                        -- Schlag-Tracks einmal pro Sitzung laden und wiederverwenden
				local k = (s.combo - 1) % #COMBO + 1
				s.comboTracks = s.comboTracks or {}
				local tr = s.comboTracks[k]
				if not tr then tr = animator:LoadAnimation(COMBO[k]); tr.Priority = Enum.AnimationPriority.Action; s.comboTracks[k] = tr end
				tr:Play(0.05)
			end
			task.delay(0.18, function() swing(s.marker, s.dir or Vector3.new(1, 0, 0), 5 + math.min(s.combo, 6)); hitSound(s.marker) end)
		elseif s.reps then
			playRep(s, i, true)
		elseif s.track then
			-- eine Wiederholung im Takt abspielen (Animationstempo an den Takt angepasst)
			local repLen = s.track.Length / (s.kind == "curl" and 2 or 1)
			s.track:AdjustSpeed(repLen / def.interval)
			s.lastHit = now
		end
	else
		s.misses += 1
		if s.kind == "bag" then s.combo = 0
		elseif s.reps then
			playRep(s, i, false)
		elseif s.track then
			s.track:AdjustSpeed(0.15)                                   -- Stocken: Kaempfer kaempft mit dem Gewicht
			local mark = now
			s.lastMiss = mark
			task.delay(0.5, function() if s.track and s.lastMiss == mark and sessions[p] == s then s.track:AdjustSpeed(0) end end)
		end
	end
	if s.hits + s.misses >= s.n and not s.finishing then s.finishing = true; task.delay(0.5, function() finish(p, s, "fertig") end) end
end)
-- ---------- Laufband: Tempo (km/h), wechselndes Zieltempo, Ausdauer, Wertung ----------
-- Zielbereich +-0,8 km/h. Im Bereich sammelt man Sekunden (= Treffer, n = 30). Zu schnell kostet Ausdauer (leer -> man wird
-- langsamer und kann nicht beschleunigen), zu langsam gibt keine Sekunden. Belohnung ueber finish() wie bei allen Uebungen.
local T_BAND, T_MIN, T_MAX, T_ACCEL = 0.8, 3.0, 16.0, 3.5
local WALK_MPS, RUN_MPS = 1.80, 4.20
game:GetService("RunService").Heartbeat:Connect(function(dt)
	local now = workspace:GetServerTimeNow()
	for p, s in pairs(sessions) do
		local t = s.tread
		if t and now >= s.t0 then
			if now >= t.nextChange then                              -- neues Zieltempo (deutlich anders als das vorige)
				local nt
				repeat nt = math.random(12, 26) / 2 until math.abs(nt - t.target) >= 2
				t.target = nt; t.nextChange = now + 5 + math.random() * 2.5
			end
			local tired = t.stamina <= 0
			local dv = t.input * T_ACCEL * dt
			if tired then dv = math.min(dv, 0) - 1.5 * dt end
			t.speed = math.clamp(t.speed + dv, T_MIN, T_MAX)
			if now - s.t0 < 0.3 and t.speed < 4 then t.speed = 4 end                 -- Band laeuft an
			local over = t.speed - (t.target + T_BAND)
			if over > 0 then t.stamina = math.max(0, t.stamina - (5 + 6 * over) * dt)
			else t.stamina = math.min(100, t.stamina + 5 * dt) end
			if math.abs(t.speed - t.target) <= T_BAND then t.inBand += dt end
			s.hits = math.min(s.n, math.floor(t.inBand + 0.5))
			-- Animation: Gehen bis ~8 km/h, darueber Laufen; Abspieltempo = Bandgeschwindigkeit / gebaute Geschwindigkeit
			local mps = t.speed / 3.6
			local runK = math.clamp((mps - 2.1) / 0.5, 0, 1)
			if t.tracks.walk then t.tracks.walk:AdjustWeight(math.max(1 - runK, 0.001), 0.2); t.tracks.walk:AdjustSpeed(mps / WALK_MPS) end
			if t.tracks.run then t.tracks.run:AdjustWeight(math.max(runK, 0.001), 0.2); t.tracks.run:AdjustSpeed(mps / RUN_MPS) end
			if t.tracks.stand and t.tracks.stand.IsPlaying then t.tracks.stand:Stop(0.3) end
			if now - t.lastPub > 0.1 then
				t.lastPub = now
				p:SetAttribute("CC_Tread", ("%.2f|%.1f|%.0f|%.2f|%.2f|%s"):format(t.speed, t.target, t.stamina, math.max(0, s.deadline - now), t.inBand, tired and "1" or "0"))
				if t.model then t.model:SetAttribute("CC_BeltSpeed", mps / 0.28); t.model:SetAttribute("CC_BeltKmh", t.speed) end
			end
		end
	end
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
	treadmill = { "Laufband", "Laufen", function(p, m) start(p, m, "tread") end },
	read_plan = { "Trainingsplan", "Ansehen", function(p) p:SetAttribute("CC_OpenPlan", os.clock()) end },
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
Players.PlayerRemoving:Connect(function(p) local s = sessions[p]; if s then s.ended = true; clearProps(s); sessions[p] = nil end; lastStation[p] = nil; lastEnd[p] = nil end)
-- Charakter weg (Reset/Tod) waehrend einer Uebung: Sitzung sauber beenden (Gewichte weg, kein Haengenbleiben)
local function hookChar(p) p.CharacterRemoving:Connect(function() local s = sessions[p]; if s then finish(p, s, "Abbruch") end end) end
Players.PlayerAdded:Connect(hookChar); for _, p in ipairs(Players:GetPlayers()) do hookChar(p) end
print("[CC] Gym-Training: " .. n .. " Stationen (Minispiele)")
