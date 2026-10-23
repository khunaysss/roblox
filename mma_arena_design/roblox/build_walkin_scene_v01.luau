-- build_walkin_scene_v01.luau (einmal in Studio im Edit-Modus ausfuehren)
-- Baut die Inhalte fuer den Ladefilm "The Walk to the Cage" nach ReplicatedFirst.CC_WalkIn (wird vor der Hauptwelt geladen):
--   Scene   Betontunnel (Anthrazit, schwarzes Metall, dezente rote Lichtstreifen, warmweisse Deckenlampen, Kabelkanal,
--           Seitentueren, Bodenmarkierungen), am Ende Kaefigtuer (Teile aus CC_Arena geklont), heller Kaefigboden, angedeutetes Publikum.
--           Lokale Koordinaten: Boden-Oberkante y = 0, Tunnel von z = 0 nach z = -66 (Blickrichtung -Z), Kaefigtuer bei z = -66.
--   Fighter Kaempfer-Rig (Kopie von CC_StoryShared.ActorBase, Standardaussehen; das gespeicherte Aussehen setzt der Client)
--   Coach   gleicher Rig mit Trainingsanzug (Outfit-Teile) und festem Aussehen
--   Anims   Animation-Objekte mit hochgeladenen IDs (CC_AnimIds) und KeyframeSequences (nur Studio-Ersatz)
--   Attribute am Ordner: Logo, Gehtempo je Animation (gemessen), Zielpunkte.
-- Vorhandenes ReplicatedFirst.CC_WalkIn wird vorher nach ServerStorage.CC_Backup_WalkIn_<Zeit> verschoben.
local RF, RS, SS = game:GetService("ReplicatedFirst"), game:GetService("ReplicatedStorage"), game:GetService("ServerStorage")

local old = RF:FindFirstChild("CC_WalkIn")
if old then old.Name = "CC_Backup_WalkIn_" .. os.time(); old.Parent = SS end
local root = Instance.new("Folder"); root.Name = "CC_WalkIn"
local scene = Instance.new("Model"); scene.Name = "Scene"; scene.Parent = root

-- Farben und Materialien (passend zum urbanen Gym)
local CONCRETE = Color3.fromRGB(58, 59, 64)
local CONCRETE_DARK = Color3.fromRGB(38, 39, 43)
local FLOOR = Color3.fromRGB(34, 35, 39)
local METAL = Color3.fromRGB(22, 22, 25)
local RED = Color3.fromRGB(200, 28, 40)
local WARM = Color3.fromRGB(255, 232, 205)
local L = 66                                   -- Tunnellaenge bis zur Kaefigtuer
local W, H = 14, 11                            -- lichte Breite und Hoehe

local function part(name, size, cf, color, material, extra)
	local p = Instance.new("Part")
	p.Name = name; p.Size = size; p.CFrame = cf; p.Color = color; p.Material = material or Enum.Material.SmoothPlastic
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = true
	p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
	for k, v in pairs(extra or {}) do p[k] = v end
	p.Parent = scene
	return p
end
local function zc(z0, z1) return (z0 + z1) / 2 end

do -- Tunnel-Rohbau
	part("Floor", Vector3.new(W, 1, L + 2), CFrame.new(0, -0.5, -L / 2), FLOOR, Enum.Material.Concrete)
	part("Ceiling", Vector3.new(W + 2, 1, L), CFrame.new(0, H + 0.5, -L / 2), CONCRETE_DARK, Enum.Material.Concrete)
	for _, s in ipairs({ -1, 1 }) do
		part("Wall", Vector3.new(1, H + 1, L), CFrame.new(s * (W / 2 + 0.5), H / 2, -L / 2), CONCRETE, Enum.Material.Concrete)
		-- abgeschraegte Kanten Boden/Wand und Decke/Wand
		part("Chamfer_Low", Vector3.new(1.1, 0.25, L), CFrame.new(s * (W / 2 - 0.3), 0.3, -L / 2) * CFrame.Angles(0, 0, s * math.rad(45)), CONCRETE_DARK, Enum.Material.Concrete)
		part("Chamfer_High", Vector3.new(1.1, 0.25, L), CFrame.new(s * (W / 2 - 0.3), H - 0.3, -L / 2) * CFrame.Angles(0, 0, -s * math.rad(45)), CONCRETE_DARK, Enum.Material.Concrete)
		-- Sockelleiste aus Metall und dezenter roter Lichtstreifen darueber
		part("Skirting", Vector3.new(0.15, 0.6, L), CFrame.new(s * (W / 2 - 0.08), 0.75, -L / 2), METAL, Enum.Material.Metal)
		part("RedStrip", Vector3.new(0.08, 0.08, L - 4), CFrame.new(s * (W / 2 - 0.2), 1.15, -L / 2), RED, Enum.Material.Neon, { Transparency = 0.25, CastShadow = false })
	end
	-- Rueckwand hinter dem Startpunkt (damit die Kamera nie ins Leere schaut)
	part("BackWall", Vector3.new(W + 2, H + 1, 1), CFrame.new(0, H / 2, 1.5), CONCRETE_DARK, Enum.Material.Concrete)
end

do -- Stahlrahmen, Deckenlampen, Kabelkanal
	for i = 0, 5 do
		local z = -6 - i * 11
		for _, s in ipairs({ -1, 1 }) do
			part("FrameColumn", Vector3.new(0.7, H, 0.7), CFrame.new(s * (W / 2 - 0.35), H / 2, z), METAL, Enum.Material.Metal)
		end
		part("FrameBeam", Vector3.new(W, 0.7, 0.7), CFrame.new(0, H - 0.35, z), METAL, Enum.Material.Metal)
		-- Lampe zwischen zwei Rahmen: Gehaeuse + warmweisse Leuchtflaeche + Spot nach unten
		local lz = z - 5.5
		part("LampHousing", Vector3.new(3.2, 0.35, 0.9), CFrame.new(0, H - 0.2, lz), METAL, Enum.Material.Metal)
		local glow = part("LampGlow", Vector3.new(3.0, 0.06, 0.7), CFrame.new(0, H - 0.4, lz), WARM, Enum.Material.Neon, { CastShadow = false })
		local sl = Instance.new("SpotLight"); sl.Face = Enum.NormalId.Bottom; sl.Angle = 120; sl.Range = 22; sl.Brightness = 3.2; sl.Color = WARM; sl.Shadows = true; sl.Parent = glow
		local fillL = Instance.new("PointLight"); fillL.Range = 15; fillL.Brightness = 0.9; fillL.Color = WARM; fillL.Shadows = false; fillL.Parent = glow   -- weiches Licht auf die Waende
	end
	-- Kabelkanal links oben mit drei Kabeln
	part("CableTray", Vector3.new(0.9, 0.12, L - 2), CFrame.new(-(W / 2 - 0.7), H - 1.6, -L / 2), METAL, Enum.Material.Metal)
	part("CableTrayLip", Vector3.new(0.08, 0.35, L - 2), CFrame.new(-(W / 2 - 1.1), H - 1.45, -L / 2), METAL, Enum.Material.Metal)
	for k = 0, 2 do
		local c = part("Cable", Vector3.new(L - 2, 0.16, 0.16), CFrame.new(-(W / 2 - 0.45 - k * 0.2), H - 1.45, -L / 2) * CFrame.Angles(0, math.rad(90), 0),
			Color3.fromRGB(16 + k * 4, 16 + k * 4, 18 + k * 4), Enum.Material.SmoothPlastic, { Shape = Enum.PartType.Cylinder })
	end
end

do -- zwei Seitentueren rechts (Kabinen) mit Rahmen und Schild
	for _, z in ipairs({ -20, -42 }) do
		local x = W / 2 - 0.05
		part("DoorFrame_L", Vector3.new(0.25, 7.4, 0.35), CFrame.new(x, 3.7, z - 2.1), METAL, Enum.Material.Metal)
		part("DoorFrame_R", Vector3.new(0.25, 7.4, 0.35), CFrame.new(x, 3.7, z + 2.1), METAL, Enum.Material.Metal)
		part("DoorFrame_Top", Vector3.new(0.25, 0.35, 4.55), CFrame.new(x, 7.4, z), METAL, Enum.Material.Metal)
		part("DoorLeaf", Vector3.new(0.12, 7.2, 3.9), CFrame.new(x + 0.05, 3.6, z), Color3.fromRGB(46, 47, 52), Enum.Material.Metal)
		part("DoorHandle", Vector3.new(0.18, 0.12, 0.6), CFrame.new(x - 0.08, 3.4, z - 1.3), Color3.fromRGB(150, 152, 158), Enum.Material.Metal)
		local sign = part("DoorSign", Vector3.new(0.06, 0.6, 2.2), CFrame.new(x - 0.04, 8.3, z), Color3.fromRGB(28, 28, 31), Enum.Material.SmoothPlastic)
		local sg = Instance.new("SurfaceGui"); sg.Face = Enum.NormalId.Left; sg.CanvasSize = Vector2.new(440, 120); sg.LightInfluence = 0.6; sg.Parent = sign
		local t = Instance.new("TextLabel"); t.BackgroundTransparency = 1; t.Size = UDim2.fromScale(1, 1); t.Font = Enum.Font.GothamBold
		t.TextScaled = true; t.TextColor3 = Color3.fromRGB(205, 206, 210); t.Text = z == -20 and "LOCKER ROOM A" or "MEDICAL"; t.Parent = sg
	end
end

do -- Bodenmarkierungen: Laufbahn-Linien und rote Haltelinie vor der Kaefigtuer
	for _, s in ipairs({ -1, 1 }) do
		part("LaneLine", Vector3.new(0.18, 0.03, L - 10), CFrame.new(s * 3.6, 0.015, -L / 2 - 2), Color3.fromRGB(150, 150, 150), Enum.Material.SmoothPlastic, { CastShadow = false })
	end
	part("StopLine", Vector3.new(7.2, 0.03, 0.35), CFrame.new(0, 0.015, -(L - 4)), RED, Enum.Material.SmoothPlastic, { CastShadow = false })
end

-- Kaefig: Teile aus der Arena klonen (gleiche Optik wie im Spiel), sonst einfache Ersatzteile
local arena = workspace:FindFirstChild("CC_Arena")
local function cloneArena(name)
	local p = arena and arena:FindFirstChild(name, true)
	if not p then return nil end
	local c = p:Clone(); c.Anchored = true; c.CanCollide = false; c.CanQuery = false; c.CanTouch = false
	for _, x in ipairs(c:GetChildren()) do if not x:IsA("DataModelMesh") and not x:IsA("SurfaceAppearance") and not x:IsA("Texture") then x:Destroy() end end
	c.Parent = scene
	return c
end
local DOOR_W, CAGE_H = 5.4, 6.0
local doorZ = -L
do -- Pfosten, Zaunfelder, Tuer
	for _, s in ipairs({ -1, 1 }) do
		local x = s * (DOOR_W / 2 + 0.25)
		local post = cloneArena("Cage_Post_1") or part("Cage_Post", Vector3.new(0.43, 6.96, 0.43), CFrame.new(), METAL)
		post.CFrame = CFrame.new(x, post.Size.Y / 2, doorZ)
		local pad = cloneArena("Cage_Post_1_Pad")
		if pad then pad.CFrame = CFrame.new(x, pad.Size.Y / 2 + 0.6, doorZ) end
		local cap = cloneArena("Cage_Post_1_Cap")
		if cap then cap.CFrame = CFrame.new(x, post.Size.Y + cap.Size.Y / 2, doorZ) end
		-- Zaunfeld schraeg nach hinten (Achteck-Kante)
		local fence = cloneArena("Cage_Fence_1")
		if fence then
			fence.Size = Vector3.new(fence.Size.X, CAGE_H, 8.4)
			fence.CFrame = CFrame.new(s * (DOOR_W / 2 + 0.25 + 2.95), CAGE_H / 2 + 0.6, doorZ - 2.95) * CFrame.Angles(0, -s * math.rad(45), 0)   -- Achteck-Kante vom Tuerpfosten nach hinten
		end
		local outer = cloneArena("Cage_Post_1")
		if outer then outer.CFrame = CFrame.new(s * (DOOR_W / 2 + 0.25 + 5.9), outer.Size.Y / 2, doorZ - 5.9) end
	end
	-- Tuerfeld (Zaun) am Scharnier links, oeffnet nach innen in den Kaefig
	local door = cloneArena("Cage_Fence_1") or part("CageDoor", Vector3.new(0.05, CAGE_H, DOOR_W), CFrame.new(), METAL, Enum.Material.DiamondPlate, { Transparency = 0.35 })
	door.Name = "CageDoor"; door.Size = Vector3.new(door.Size.X, CAGE_H, DOOR_W)
	door.CFrame = CFrame.new(0, CAGE_H / 2 + 0.6, doorZ) * CFrame.Angles(0, math.rad(90), 0)
	door:SetAttribute("CC_Hinge", Vector3.new(-DOOR_W / 2, 0, doorZ))
	local frameTop = cloneArena("Cage_TopRail_1")
	if frameTop then frameTop.Size = Vector3.new(frameTop.Size.X, frameTop.Size.Y, DOOR_W + 0.6); frameTop.CFrame = CFrame.new(0, CAGE_H + 0.75, doorZ) * CFrame.Angles(0, math.rad(90), 0) end
	local frameBottom = cloneArena("Cage_BottomRail_1")
	if frameBottom then frameBottom.Size = Vector3.new(frameBottom.Size.X, frameBottom.Size.Y, DOOR_W + 0.6); frameBottom.CFrame = CFrame.new(0, 0.35, doorZ) * CFrame.Angles(0, math.rad(90), 0) end
	-- Tuerrahmen-Leisten an beiden Seiten (bewegen sich mit der Tuer)
	local edge = part("CageDoorEdge", Vector3.new(0.22, CAGE_H, 0.22), CFrame.new(DOOR_W / 2 - 0.15, CAGE_H / 2 + 0.6, doorZ), METAL, Enum.Material.Metal)
	edge:SetAttribute("CC_DoorPart", true)
	door:SetAttribute("CC_DoorPart", true)
end

do -- Kaefigboden und Arena hinter der Tuer (hell), Publikum angedeutet, Dach dunkel
	part("Canvas", Vector3.new(40, 0.4, 32), CFrame.new(0, 0.2, doorZ - 17), Color3.fromRGB(226, 226, 222), Enum.Material.Fabric)
	part("CanvasEdge", Vector3.new(40, 0.42, 1.2), CFrame.new(0, 0.21, doorZ - 1.2), RED, Enum.Material.Fabric)
	part("ArenaFloor", Vector3.new(120, 1, 80), CFrame.new(0, -0.6, doorZ - 40), Color3.fromRGB(18, 18, 21), Enum.Material.Concrete)
	part("ArenaRoof", Vector3.new(120, 1, 80), CFrame.new(0, 30, doorZ - 40), Color3.fromRGB(10, 10, 12), Enum.Material.SmoothPlastic)
	part("ArenaBackWall", Vector3.new(120, 32, 1), CFrame.new(0, 14, doorZ - 80), Color3.fromRGB(12, 12, 14), Enum.Material.SmoothPlastic)
	for _, s in ipairs({ -1, 1 }) do
		part("ArenaSideWall", Vector3.new(1, 32, 80), CFrame.new(s * 60, 14, doorZ - 40), Color3.fromRGB(12, 12, 14), Enum.Material.SmoothPlastic)
	end
	-- Tunnelmund: Wand um die Oeffnung (Arena-Seite)
	for _, s in ipairs({ -1, 1 }) do
		part("PortalWall", Vector3.new(53, H + 22, 1), CFrame.new(s * (W / 2 + 26.5), (H + 22) / 2, -L + 0.6), Color3.fromRGB(14, 14, 16), Enum.Material.SmoothPlastic)
	end
	part("PortalTop", Vector3.new(W + 2, 21, 1), CFrame.new(0, H + 10.5, -L + 0.6), Color3.fromRGB(14, 14, 16), Enum.Material.SmoothPlastic)
	-- Licht ueber dem Kaefig: vier Strahler (kuehl-warm weiss), hell auf den Boden
	for i, p in ipairs({ Vector3.new(-9, 22, doorZ - 10), Vector3.new(9, 22, doorZ - 10), Vector3.new(-9, 22, doorZ - 24), Vector3.new(9, 22, doorZ - 24) }) do
		local lamp = part("ArenaLamp", Vector3.new(2.2, 0.5, 2.2), CFrame.new(p), Color3.fromRGB(255, 248, 235), Enum.Material.Neon, { CastShadow = false })
		local sp = Instance.new("SpotLight"); sp.Face = Enum.NormalId.Bottom; sp.Angle = 70; sp.Range = 40; sp.Brightness = 4; sp.Color = Color3.fromRGB(255, 246, 232); sp.Shadows = i <= 2; sp.Parent = lamp
	end
	-- Licht, das durch die Tuer in den Tunnel faellt (wird beim Oeffnen hochgeregelt)
	local spill = part("DoorSpill", Vector3.new(0.2, 0.2, 0.2), CFrame.new(0, 6, doorZ - 3) * CFrame.Angles(0, 0, 0), WARM, Enum.Material.SmoothPlastic, { Transparency = 1, CastShadow = false })
	local sl = Instance.new("SpotLight"); sl.Name = "Spill"; sl.Face = Enum.NormalId.Back; sl.Angle = 60; sl.Range = 34; sl.Brightness = 0.6; sl.Color = Color3.fromRGB(255, 244, 226); sl.Shadows = true; sl.Parent = spill
	-- Publikum: dunkle Silhouetten in drei Reihen links und rechts, leicht erhoeht, Variation in Groesse und Ton
	local rnd = Random.new(7)
	for _, s in ipairs({ -1, 1 }) do
		for row = 0, 2 do
			part("Tier", Vector3.new(26, 1.2 + row * 1.6, 3.2), CFrame.new(s * (24 + row * 3.2), (1.2 + row * 1.6) / 2, doorZ - 20), Color3.fromRGB(20, 20, 23), Enum.Material.Concrete)
			for k = 0, 9 do --
				local x = s * (24 + row * 3.2)
				local z = doorZ - 9 - k * 2.4 + rnd:NextNumber(-0.3, 0.3)
				local y = 1.2 + row * 1.6
				local tone = rnd:NextInteger(18, 34)
				local hgt = rnd:NextNumber(2.0, 2.5)
				part("Spectator", Vector3.new(1.4, hgt, 1.1), CFrame.new(x, y + hgt / 2, z), Color3.fromRGB(tone, tone, tone + 3), Enum.Material.SmoothPlastic, { CastShadow = false })
				part("SpectatorHead", Vector3.new(0.75, 0.75, 0.75), CFrame.new(x, y + hgt + 0.4, z), Color3.fromRGB(tone + 4, tone + 2, tone), Enum.Material.SmoothPlastic, { CastShadow = false })
			end
		end
	end
	-- gedaempftes Licht ueber den Raengen (Publikum soll angedeutet sichtbar sein, nicht hell)
	for _, p in ipairs({ Vector3.new(-12, 12, doorZ - 38), Vector3.new(0, 12, doorZ - 38), Vector3.new(12, 12, doorZ - 38), Vector3.new(-27, 10, doorZ - 20), Vector3.new(27, 10, doorZ - 20) }) do
		local h = part("CrowdLight", Vector3.new(0.2, 0.2, 0.2), CFrame.new(p), WARM, Enum.Material.SmoothPlastic, { Transparency = 1, CastShadow = false })
		local pl = Instance.new("PointLight"); pl.Range = 26; pl.Brightness = 2.2; pl.Color = Color3.fromRGB(255, 226, 196); pl.Shadows = false; pl.Parent = h
	end
	-- Publikum gegenueber (durch den Tunnel geradeaus sichtbar): drei Reihen hinter dem Kaefig, Blick zum Tunnel
	for row = 0, 2 do
		local z = doorZ - 36 - row * 3.2
		local y = 1.2 + row * 1.6
		part("TierBack", Vector3.new(44, y, 3.2), CFrame.new(0, y / 2, z), Color3.fromRGB(20, 20, 23), Enum.Material.Concrete)
		for k = 0, 17 do
			local x = -20 + k * 2.35 + rnd:NextNumber(-0.3, 0.3)
			local tone = rnd:NextInteger(18, 34)
			local hgt = rnd:NextNumber(2.0, 2.5)
			part("Spectator", Vector3.new(1.4, hgt, 1.1), CFrame.new(x, y + hgt / 2, z), Color3.fromRGB(tone, tone, tone + 3), Enum.Material.SmoothPlastic, { CastShadow = false })
			part("SpectatorHead", Vector3.new(0.75, 0.75, 0.75), CFrame.new(x, y + hgt + 0.4, z), Color3.fromRGB(tone + 4, tone + 2, tone), Enum.Material.SmoothPlastic, { CastShadow = false })
		end
	end
end

-- Kaempfer und Coach (Rig-Kopien)
local SH = RS:WaitForChild("CC_StoryShared")
local Look = require(RS:WaitForChild("CC_LookShared"))
local function rig(name)
	local m = SH.ActorBase:Clone(); m.Name = name
	local hum = m:FindFirstChildOfClass("Humanoid"); hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	if not hum:FindFirstChildOfClass("Animator") then Instance.new("Animator", hum) end
	for _, p in ipairs(m:GetDescendants()) do if p:IsA("BasePart") then p.CanCollide = false; p.CanQuery = false; p.CanTouch = false end end
	m.HumanoidRootPart.Anchored = true
	local saves = m:FindFirstChild("AnimSaves"); if saves then saves:Destroy() end
	return m
end
local fighter = rig("Fighter"); fighter.Parent = root
local coach = rig("Coach")
for _, n in ipairs({ "Fighter_Gloves", "Fighter_Shorts" }) do local x = coach:FindFirstChild(n); if x then x.Transparency = 1 end end
pcall(function() Look.apply(coach, { hair = "Hair_SidePart", beard = "Beard_Full", face = "Face_Focused", skin = 2, hairColor = 6 }, RS:FindFirstChild("CC_CustomShared")) end)
for pname, col in pairs({ Coach_Jacket = Color3.fromRGB(26, 27, 30), Coach_Pants = Color3.fromRGB(26, 27, 30), Casual_Shoes = Color3.fromRGB(236, 236, 232), Casual_Hands = "skin" }) do
	local t = SH.Outfit:FindFirstChild(pname)
	if t then
		local p = t:Clone(); p.Massless = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
		p.Color = col == "skin" and Look.SKIN[2] or col
		local mo = Instance.new("Motor6D"); mo.Part0 = coach.HumanoidRootPart; mo.Part1 = p; mo.C0 = t:GetAttribute("CC_C0"); mo.Parent = p
		p.Parent = coach
	end
end
coach.Parent = root

-- Animationen: IDs (online) und KeyframeSequences (nur Studio)
local anims = Instance.new("Folder"); anims.Name = "Anims"; anims.Parent = root
local idsOk, ids = pcall(function() return require(SS.CC_Animations.CC_AnimIds:Clone()) end)
ids = idsOk and ids or {}
for _, n in ipairs({ "Fighter_Walkout", "Fighter_TunnelWait", "Fighter_CasualWalk_v2", "Fighter_CasualIdle_v01" }) do
	if ids[n] then local a = Instance.new("Animation"); a.Name = n; a.AnimationId = "rbxassetid://" .. tostring(ids[n]); a.Parent = anims end
	local ks = SS.CC_Animations:FindFirstChild(n)
	if ks and ks:IsA("KeyframeSequence") then local c = ks:Clone(); c.Name = n .. "_KS"; c.Parent = anims end
end

-- Einstellungen fuer das Client-Skript
root:SetAttribute("Logo", "rbxassetid://105923753646979")               -- Original-Logo (CC_StoryShared.CardLogo)
root:SetAttribute("Speed_Fighter_Walkout", 4.23)                          -- gemessen: Standfuss gleitet nicht
root:SetAttribute("Speed_Fighter_CasualWalk_v2", 6.41)
root:SetAttribute("StartZ", -24)                                          -- Startpunkt des Kaempfers
root:SetAttribute("StopZ", -(L - 4.6))                                    -- Halt vor der Kaefigtuer (Haltelinie)
root:SetAttribute("DoorZ", doorZ)
root.Parent = RF
local n = 0; for _ in ipairs(scene:GetDescendants()) do n += 1 end
local an = {} for _, a in ipairs(anims:GetChildren()) do table.insert(an, a.Name) end
return ("CC_WalkIn gebaut: Szene %d Objekte, Arena-Teile geklont=%s, Anims: %s"):format(n, tostring(arena ~= nil), table.concat(an, ", "))
