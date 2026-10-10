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
local WR_BLEND = 0.6      -- Sekunden fuer den Wechsel Stand <-> Bodenkampf-Ansicht
local camPos, aimPos = nil, nil
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
	return list
end
local params = RaycastParams.new(); params.FilterType = Enum.RaycastFilterType.Exclude
local lastIgnore = 0

RunService:BindToRenderStep("CC_FightCamera", Enum.RenderPriority.Camera.Value, function(dt)  -- vor dem Treffer-Ruck (CC_HitFX, +1)
	local char = player.Character
	local targetName = char and char:GetAttribute("CC_LockTarget")
	local target = targetName and targetName ~= "" and workspace:FindFirstChild(targetName)
	if not (char and target and char:FindFirstChild("HumanoidRootPart") and target:FindFirstChild("HumanoidRootPart")) then
		if cam.CameraType == Enum.CameraType.Scriptable then cam.CameraType = Enum.CameraType.Custom end
		camPos, aimPos = nil, nil
		return
	end
	cam.CameraType = Enum.CameraType.Scriptable
	if os.clock() - lastIgnore > 2 then params.FilterDescendantsInstances = ignoreList(); lastIgnore = os.clock() end

	local me, foe = bodyPoint(char), bodyPoint(target)
	local wrestling = char:GetAttribute("CC_Wrestle")
	wrW = math.clamp(wrW + (wrestling and 1 or -1) * dt / WR_BLEND, 0, 1)
	local w = wrW * wrW * (3 - 2 * wrW)   -- weich ein/aus
	local mid = (me + foe) / 2
	local gap = (Vector3.new(foe.X, 0, foe.Z) - Vector3.new(me.X, 0, me.Z)).Magnitude
	local aim = mid + Vector3.new(0, 1.2 - 0.6 * w, 0)
	-- Richtung: hinter dem eigenen Kaempfer (vom Gegner weg); im Ringkampf seitlich auf die Szene
	local away = Vector3.new(me.X - foe.X, 0, me.Z - foe.Z)
	away = away.Magnitude > 0.1 and away.Unit or -char.HumanoidRootPart.CFrame.LookVector
	local right = Vector3.new(-away.Z, 0, away.X)
	local dist = math.clamp(9 + gap * 0.85, 11, 24) * (1 - w) + 8.5 * w   -- am Boden naeher dran
	local height = math.clamp(4 + gap * 0.18, 4.5, 7.5) * (1 - w) + 4.2 * w
	-- Kaefigmitte (Kamera bleibt innerhalb von CAGE_R)
	local center = Vector3.new(0, 0, 0)
	local arena = workspace:FindFirstChild("CC_Arena")
	local canvas = arena and arena:FindFirstChild("Platform_Canvas_FightSurface", true)
	if canvas then center = Vector3.new(canvas.Position.X, 0, canvas.Position.Z) end
	local function inside(p) return Vector3.new(p.X - center.X, 0, p.Z - center.Z).Magnitude <= CAGE_R end
	local function candidate(dirH, d)
		local r = Vector3.new(-dirH.Z, 0, dirH.X)
		return aim + dirH * d + r * SIDE * (1 - w) + Vector3.new(0, height, 0)
	end
	-- Grundrichtung: hinter dem eigenen Kaempfer; im Ringkampf seitlich auf die Szene
	local baseDir = (away * (1 - w) + (right * 0.85 + away * 0.35).Unit * w).Unit
	-- Kandidaten (Winkel um den Blickpunkt x Abstand) bewerten: im Kaefig UND beide Kaempfer (Fuesse bis Kopf) im Bild;
	-- bevorzugt: wenig Schwenk gegenueber "hinter dem Spieler" und nah am Wunschabstand
	local vp = cam.ViewportSize
	local tv = math.tan(math.rad(cam.FieldOfView) / 2) * 0.82
	local th = tv * (vp.X / math.max(vp.Y, 1))
	local pts = { me + Vector3.new(0, -0.6, 0), me + Vector3.new(0, 2.6, 0), foe + Vector3.new(0, -0.6, 0), foe + Vector3.new(0, 2.6, 0) }
	local function framed(p)
		local cf = CFrame.lookAt(p, aim)
		for _, q in ipairs(pts) do
			local l = cf:PointToObjectSpace(q)
			if l.Z > -2 or math.abs(l.X / -l.Z) > th or math.abs(l.Y / -l.Z) > tv then return false end
		end
		return true
	end
	local want, bestScore = nil, math.huge
	for _, deg in ipairs({ 0, 15, -15, 30, -30, 45, -45, 60, -60, 75, -75, 90, -90, 110, -110 }) do
		local c = math.cos(math.rad(deg)); local s_ = math.sin(math.rad(deg))
		local dH = Vector3.new(baseDir.X * c - baseDir.Z * s_, 0, baseDir.X * s_ + baseDir.Z * c)
		-- Stand: vom weitesten Abstand nach innen (bewaehrte Ansicht); Boden: vom Wunschabstand nach aussen (moeglichst nah)
		local d0, d1, step = dist + 4, 7, -1
		if w > 0.5 then d0, d1, step = dist, dist + 8, 0.5 end
		for d = d0, d1, step do
			local p = candidate(dH, d)
			if inside(p) and framed(p) then
				local score = math.abs(deg) * 0.12 + math.abs(d - dist) * 0.5
				if score < bestScore then want, bestScore = p, score end
				break
			end
		end
	end
	-- notfalls: hoch ueber der Mitte (Uebersicht), damit nie ein Kaempfer verloren geht
	if not want then want = aim + baseDir * 6 + Vector3.new(0, 14 + gap * 0.3, 0) end
	-- Wand-/Deckenschutz: vom Blickpunkt zur Wunschposition casten
	local dir = want - aim
	local hit = workspace:Raycast(aim, dir, params)
	if hit then want = hit.Position - dir.Unit * 0.8 end

	if not camPos then camPos, aimPos = want, aim end
	local nextPos = camPos:Lerp(want, 1 - math.exp(-FOLLOW * dt))
	local step = nextPos - camPos
	if step.Magnitude > MAX_SPEED * dt then nextPos = camPos + step.Unit * MAX_SPEED * dt end
	camPos = nextPos
	aimPos = aimPos:Lerp(aim, 1 - math.exp(-AIM * dt))
	cam.CFrame = CFrame.lookAt(camPos, aimPos)
end)
