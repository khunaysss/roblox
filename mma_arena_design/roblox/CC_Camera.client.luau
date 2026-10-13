-- StarterPlayer.StarterPlayerScripts.CC_Camera
-- Kampfkamera bei aktiver Anvisierung (Attribut CC_LockTarget am eigenen Charakter):
--   - Blickpunkt = Mitte zwischen beiden Kaempfern (Brusthoehe; am Boden Hoehe der Koerper ueber die Root-Bones)
--   - Kamera hinter/schraeg ueber dem eigenen Kaempfer, Abstand waechst mit dem Abstand der Kaempfer -> beide sichtbar
--   - Takedown/Boden: Ansicht wird in WR_BLEND s weich zur Seitenansicht ueberblendet, Kamerageschwindigkeit begrenzt
--   - weich nachgefuehrt (exponentiell), keine Spruenge; Wand-/Deckenschutz per Raycast (Gitter und Kaempfer ausgenommen)
-- Ohne Anvisierung: normale Roblox-Kamera.
local RunService = game:GetService("RunService")
local player = game.Players.LocalPlayer
local cam = workspace.CurrentCamera

local FOLLOW = 7          -- Nachfuehr-Rate Position (1/s)
local AIM = 9             -- Nachfuehr-Rate Blickpunkt (1/s)
local SIDE = 4.0          -- ueber die rechte Schulter, damit der Gegner neben dem eigenen Kaempfer sichtbar ist
local CAGE_R = 14.5       -- Kamera bleibt innerhalb des Kaefigs
local MAX_SPEED = 32      -- Kamera bewegt sich hoechstens so schnell (Studs/s): keine Schwenk-Spruenge beim Takedown
local WR_BLEND = 0.9      -- Sekunden fuer den Wechsel Stand <-> Bodenkampf-Ansicht
local camPos, aimPos = nil, nil
local filt = {}            -- geglaettete Koerperpunkte je Modell (Ausreisser beim Animationswechsel abfangen)
local BODY_MAX_SPEED = 14  -- Studs/s: schneller bewegt sich kein Koerper sichtbar; groessere Spruenge = Wechsel-Frame
local groundSide = nil   -- Bodenansicht: Seite (+1/-1), beim Eintritt festgelegt
local wrW = 0             -- 0 = Stand-Ansicht, 1 = Bodenkampf-Ansicht (weich ueberblendet)

local function bodyPoint(model)
	-- im Ringkampf stehen die HumanoidRootParts still; die sichtbare Position steckt im Root-Bone
	local hrp = model:FindFirstChild("HumanoidRootPart")
	local rootBone = hrp and hrp:FindFirstChild("Root")
	local lt = rootBone and rootBone:FindFirstChild("LowerTorso", true)
	if lt then return lt.TransformedWorldCFrame.Position end
	return hrp and hrp.Position
end

local function ignoreList()
	local list = {}
	for _, m in ipairs(workspace:GetChildren()) do
		if m:IsA("Model") and m:FindFirstChildOfClass("Humanoid") then table.insert(list, m) end
	end
	local arena = workspace:FindFirstChild("CC_Arena")
	if arena then
		local col = arena:FindFirstChild("CC_CageCollision"); if col then table.insert(list, col) end
		for _, p in ipairs(arena:GetDescendants()) do
			if p:IsA("BasePart") and (p.Transparency > 0.2 or p.Name:find("Fence") or p.Name:find("LightRig") or p.Name:find("Truss")) then table.insert(list, p) end
		end
	end
	-- Fight-Night-Arena: Gitter, Traversen und unsichtbare Kollisionsboxen versperren die Kamera nicht
	local fn = workspace:FindFirstChild("CC_FightNight")
	if fn then
		for _, p in ipairs(fn:GetDescendants()) do
			if p:IsA("BasePart") and (p.Transparency > 0.2 or p.Name:find("Fence") or p.Name:find("Truss") or p.Name:find("Crowd")) then table.insert(list, p) end
		end
	end
	return list
end
local params = RaycastParams.new(); params.FilterType = Enum.RaycastFilterType.Exclude
local lastIgnore = 0
-- Koerperpunkt mit Glaettung: beim Wechsel zweier Ringkampf-Animationen steht der Root-Bone fuer einen Frame
-- auf der Ruheposition (Sprung um mehrere Studs); solche Spruenge werden auf BODY_MAX_SPEED begrenzt und weich nachgezogen.
local function smoothBody(model, dt)
	local p = bodyPoint(model)
	if not p then return nil end
	local s = filt[model]
	if not s or (p - s).Magnitude > 25 then filt[model] = p; return p end   -- neu oder teleportiert (Rundenstart)
	local d = p - s
	local maxStep = BODY_MAX_SPEED * dt
	if d.Magnitude > maxStep then d = d.Unit * maxStep end
	s = s + d
	filt[model] = s
	return s
end
-- Ziel: anvisiertes Modell; im Ringkampf/Boden immer der Kampfgegner (auch wenn die Anvisierung aus ist)
local function fightTarget(char)
	local n = char:GetAttribute("CC_LockTarget")
	if (not n or n == "") and (char:GetAttribute("CC_Wrestle") or char:GetAttribute("CC_Down")) then n = char:GetAttribute("CC_Opponent") end
	return n and n ~= "" and workspace:FindFirstChild(n) or nil
end
local FLOOR_CLEAR = 1.6    -- Kamera bleibt so weit ueber dem Kaefigboden

RunService:BindToRenderStep("CC_FightCamera", Enum.RenderPriority.Camera.Value, function(dt)  -- vor dem Treffer-Ruck (CC_HitFX, +1)
	local char = player.Character
	local target = char and fightTarget(char)
	if not (char and target and char:FindFirstChild("HumanoidRootPart") and target:FindFirstChild("HumanoidRootPart")) then
		if cam.CameraType == Enum.CameraType.Scriptable and not player:GetAttribute("CC_Minigame") and not player:GetAttribute("CC_UIBlock") then cam.CameraType = Enum.CameraType.Custom end   -- Training-Kamera (CC_Minigame) nicht stoeren
		camPos, aimPos = nil, nil
		filt = {}
		return
	end
	cam.CameraType = Enum.CameraType.Scriptable
	if os.clock() - lastIgnore > 2 then params.FilterDescendantsInstances = ignoreList(); lastIgnore = os.clock() end

	local me, foe = smoothBody(char, dt), smoothBody(target, dt)
	if not (me and foe) then return end
	local wrestling = char:GetAttribute("CC_Wrestle") or char:GetAttribute("CC_Down")   -- selbst am Boden: Bodenansicht
	wrW = math.clamp(wrW + (wrestling and 1 or -1) * dt / WR_BLEND, 0, 1)
	local w = wrW * wrW * (3 - 2 * wrW)   -- weich ein/aus
	local mid = (me + foe) / 2
	local gap = (Vector3.new(foe.X, 0, foe.Z) - Vector3.new(me.X, 0, me.Z)).Magnitude
	-- Kaefigmitte (Kamera bleibt innerhalb von CAGE_R)
	local center = Vector3.new(0, 0, 0)
	local arena = workspace:FindFirstChild("CC_Arena")
	local canvas = arena and arena:FindFirstChild("Platform_Canvas_FightSurface", true)
	if canvas then center = Vector3.new(canvas.Position.X, 0, canvas.Position.Z) end
	-- naechster Kaefig: Fight-Night-Arena (Online-Kaempfe), sonst die kleine Arena
	local fnArena = workspace:FindFirstChild("CC_FightNight")
	local fc = fnArena and fnArena:GetAttribute("CC_CageCenter")
	if fc and (Vector3.new(me.X, 0, me.Z) - Vector3.new(fc.X, 0, fc.Z)).Magnitude < (Vector3.new(me.X, 0, me.Z) - center).Magnitude then center = Vector3.new(fc.X, 0, fc.Z) end
	local function inside(p) return Vector3.new(p.X - center.X, 0, p.Z - center.Z).Magnitude <= CAGE_R end
	local away = Vector3.new(me.X - foe.X, 0, me.Z - foe.Z)
	away = away.Magnitude > 0.1 and away.Unit or -char.HumanoidRootPart.CFrame.LookVector
	local vp = cam.ViewportSize
	local tv = math.tan(math.rad(cam.FieldOfView) / 2) * 0.82
	local th = tv * (vp.X / math.max(vp.Y, 1))

	-- ---- Stand-Ansicht: hinter dem eigenen Kaempfer; Kandidaten (Winkel x Abstand), beide Kaempfer im Bild ----
	local aimS = mid + Vector3.new(0, 1.2, 0)
	local distS = math.clamp(9 + gap * 0.85, 11, 24)
	local heightS = math.clamp(4 + gap * 0.18, 4.5, 7.5)
	local pts = { me + Vector3.new(0, -0.6, 0), me + Vector3.new(0, 2.6, 0), foe + Vector3.new(0, -0.6, 0), foe + Vector3.new(0, 2.6, 0) }
	local function framed(p, a)
		local cf = CFrame.lookAt(p, a)
		for _, q in ipairs(pts) do
			local l = cf:PointToObjectSpace(q)
			if l.Z > -2 or math.abs(l.X / -l.Z) > th or math.abs(l.Y / -l.Z) > tv then return false end
		end
		return true
	end
	local wantS, bestScore = nil, math.huge
	if w < 0.999 then
		for _, deg in ipairs({ 0, 15, -15, 30, -30, 45, -45, 60, -60, 75, -75, 90, -90, 110, -110 }) do
			local c = math.cos(math.rad(deg)); local s_ = math.sin(math.rad(deg))
			local dH = Vector3.new(away.X * c - away.Z * s_, 0, away.X * s_ + away.Z * c)
			local r = Vector3.new(-dH.Z, 0, dH.X)
			for d = distS + 4, 7, -1 do
				local p = aimS + dH * d + r * SIDE + Vector3.new(0, heightS, 0)
				if inside(p) and framed(p, aimS) then
					local score = math.abs(deg) * 0.12 + math.abs(d - distS) * 0.5
					if score < bestScore then wantS, bestScore = p, score end
					break
				end
			end
		end
		-- notfalls: hoch ueber der Mitte (Uebersicht), damit nie ein Kaempfer verloren geht
		if not wantS then wantS = aimS + away * 6 + Vector3.new(0, 14 + gap * 0.3, 0) end
	end

	-- ---- Boden-Ansicht: stetig (keine Kandidatenwechsel = kein Wackeln). Seite wird beim Eintritt festgelegt
	-- (die Seite, auf der die Kamera gerade ist) und nur gewechselt, wenn sie ausserhalb des Kaefigs laege. ----
	local aimG = mid + Vector3.new(0, 0.6, 0)
	local wantG
	if wrestling or w > 0 then
		local line = Vector3.new(foe.X - me.X, 0, foe.Z - me.Z)
		line = line.Magnitude > 0.1 and line.Unit or -away
		local perp = Vector3.new(-line.Z, 0, line.X)
		if not groundSide then
			local ref = camPos or (aimG + away * 10)
			groundSide = ((ref - mid):Dot(perp) >= 0) and 1 or -1
		end
		-- Abstand aus der Ausdehnung der Szene (Kaempfer-Abstand + Koerperlaenge am Boden), stetig
		local span = gap + 3.5
		local dG = math.clamp(span / (2 * th) + 3.0, 8, 13)
		local function g(side)
			local dir = (perp * side * 0.92 + away * 0.38).Unit
			return aimG + dir * dG + Vector3.new(0, 3.6 + dG * 0.12, 0)
		end
		wantG = g(groundSide)
		if not inside(wantG) and inside(g(-groundSide)) then groundSide = -groundSide; wantG = g(groundSide) end
	end
	if not wrestling and w <= 0 then groundSide = nil end

	local aim = wantG and aimS:Lerp(aimG, w) or aimS
	local want
	if not wantS then want = wantG
	elseif not wantG then want = wantS
	else want = wantS:Lerp(wantG, w) end
	-- Wand-/Deckenschutz: vom Blickpunkt zur Wunschposition casten
	local dir = want - aim
	local hit = workspace:Raycast(aim, dir, params)
	if hit then want = hit.Position - dir.Unit * 0.8 end
	-- nie unter/durch den Boden
	local floorY = (canvas and canvas.Position.Y or 0) + FLOOR_CLEAR
	if want.Y < floorY then want = Vector3.new(want.X, floorY, want.Z) end

	if not camPos then camPos, aimPos = want, aim end
	local nextPos = camPos:Lerp(want, 1 - math.exp(-FOLLOW * dt))
	local step = nextPos - camPos
	local maxSpeed = MAX_SPEED * (1 - 0.55 * math.min(1, wrW * (1 - wrW) * 4))   -- waehrend des Ueberblendens langsamer schwenken
	if step.Magnitude > maxSpeed * dt then nextPos = camPos + step.Unit * maxSpeed * dt end
	camPos = nextPos
	aimPos = aimPos:Lerp(aim, 1 - math.exp(-AIM * dt))
	cam.CFrame = CFrame.lookAt(camPos, aimPos)
end)

-- Ausserhalb des Kampfs (normale Roblox-Kamera): Kamera nicht in Waende/Geraete schieben.
-- In diesem Place fehlt das Roblox-Kameramodul (PlayerModule) und damit dessen Hindernis-Ausweichen;
-- deshalb hier: vom Kopf zur Kamera casten und die Kamera vor das erste Hindernis setzen.
local popParams = RaycastParams.new(); popParams.FilterType = Enum.RaycastFilterType.Exclude
local popIgnoreAt = 0
RunService:BindToRenderStep("CC_CameraPopper", Enum.RenderPriority.Camera.Value + 2, function()
	if cam.CameraType ~= Enum.CameraType.Custom then return end
	local char = player.Character
	local head = char and char:FindFirstChild("HumanoidRootPart")
	if not head then return end
	if os.clock() - popIgnoreAt > 2 then
		local list = {}
		for _, m in ipairs(workspace:GetChildren()) do
			if m:IsA("Model") and m:FindFirstChildOfClass("Humanoid") then table.insert(list, m) end
		end
		popParams.FilterDescendantsInstances = list; popIgnoreAt = os.clock()
	end
	local from = head.Position + Vector3.new(0, 2.2, 0)
	local to = cam.CFrame.Position
	local d = to - from
	if d.Magnitude < 0.5 then return end
	local hit = workspace:Raycast(from, d, popParams)
	if hit then
		local p = hit.Position - d.Unit * 0.6
		cam.CFrame = CFrame.new(p) * (cam.CFrame - cam.CFrame.Position)
	end
end)
