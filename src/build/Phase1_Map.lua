--[[
	Steal a Car – Phase 1: Map-Grundgerüst
	Baut: Safe Zone mit Spawn, 8 Autohäuser (4 links, 4 rechts), Hauptstraße,
	5 leere Stadtflächen mit Torbogen (Paris, London, Las Vegas, Tokyo, Dubai).

	Ausführen: In Roblox Studio unter View → Command Bar den ganzen Inhalt einfügen und Enter drücken.
	Das Skript kann man mehrmals ausführen, die alte Map wird dabei vorher gelöscht.
]]

local MAP_NAME = "StealACar_Map"

-- Maße (Studs)
local ROAD_WIDTH = 40
local PLOT_W, PLOT_D = 60, 80 -- Autohaus: Breite (X) × Tiefe (Z)
local PLOT_X = ROAD_WIDTH / 2 + 10 + PLOT_W / 2 -- Abstand der Autohäuser von der Straßenmitte
local PLOT_ZS = { -135, -45, 45, 135 } -- 4 Autohäuser pro Seite
local SAFE_Z, SAFE_SIZE = -250, 100
local CITY_START_Z, CITY_LEN, CITY_W = 200, 300, 260

local CITIES = {
	{ name = "Paris", floor = Color3.fromRGB(226, 205, 160), accent = Color3.fromRGB(40, 60, 140) },
	{ name = "London", floor = Color3.fromRGB(150, 150, 155), accent = Color3.fromRGB(200, 30, 35) },
	{ name = "Las Vegas", floor = Color3.fromRGB(45, 30, 60), accent = Color3.fromRGB(255, 60, 200) },
	{ name = "Tokyo", floor = Color3.fromRGB(60, 45, 70), accent = Color3.fromRGB(255, 150, 200) },
	{ name = "Dubai", floor = Color3.fromRGB(235, 200, 120), accent = Color3.fromRGB(255, 200, 40) },
}

local GRASS = Color3.fromRGB(90, 200, 70)
local ROAD = Color3.fromRGB(55, 55, 60)
local WALL = Color3.fromRGB(190, 120, 70)

local old = workspace:FindFirstChild(MAP_NAME)
if old then
	old:Destroy()
end
local map = Instance.new("Folder")
map.Name = MAP_NAME
map.Parent = workspace

local function part(parent, name, size, cframe, color, props)
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored = true
	p.Size = size
	p.CFrame = cframe
	p.Color = color
	p.Material = Enum.Material.SmoothPlastic
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	for k, v in pairs(props or {}) do
		p[k] = v
	end
	p.Parent = parent
	return p
end

local function label(p, face, text, color, bg)
	local gui = Instance.new("SurfaceGui")
	gui.Face = face
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = 20
	gui.Parent = p
	local t = Instance.new("TextLabel")
	t.Size = UDim2.fromScale(1, 1)
	t.BackgroundColor3 = bg or Color3.new(0, 0, 0)
	t.BackgroundTransparency = bg and 0 or 1
	t.TextColor3 = color
	t.TextScaled = true
	t.Font = Enum.Font.FredokaOne
	t.Text = text
	t.Parent = gui
	return t
end

local function folder(parent, name)
	local f = Instance.new("Folder")
	f.Name = name
	f.Parent = parent
	return f
end

-- Boden & Hauptstraße
local ground = folder(map, "Ground")
local mapEndZ = CITY_START_Z + #CITIES * CITY_LEN
part(ground, "Grass", Vector3.new(PLOT_X * 2 + PLOT_W + 60, 2, CITY_START_Z - (SAFE_Z - SAFE_SIZE / 2)),
	CFrame.new(0, -1, (SAFE_Z - SAFE_SIZE / 2 + CITY_START_Z) / 2), GRASS, { Material = Enum.Material.Grass })
part(ground, "MainRoad", Vector3.new(ROAD_WIDTH, 0.2, mapEndZ - SAFE_Z), CFrame.new(0, 0.1, (SAFE_Z + mapEndZ) / 2), ROAD)

-- Safe Zone
local safe = folder(map, "SafeZone")
part(safe, "SafeZoneFloor", Vector3.new(SAFE_SIZE, 1, SAFE_SIZE), CFrame.new(0, 0.5, SAFE_Z),
	Color3.fromRGB(120, 220, 255), { Material = Enum.Material.Neon, Transparency = 0.6 })
local zone = part(safe, "SafeZoneArea", Vector3.new(SAFE_SIZE, 30, SAFE_SIZE), CFrame.new(0, 15, SAFE_Z),
	Color3.new(1, 1, 1), { Transparency = 1, CanCollide = false, CanQuery = false })
zone:SetAttribute("SafeZone", true)
local spawn = Instance.new("SpawnLocation")
spawn.Name = "Spawn"
spawn.Anchored = true
spawn.Size = Vector3.new(12, 1, 12)
spawn.CFrame = CFrame.new(0, 1.5, SAFE_Z)
spawn.Color = Color3.fromRGB(255, 255, 255)
spawn.Parent = safe
local sign = part(safe, "SafeZoneSign", Vector3.new(40, 8, 1), CFrame.new(0, 20, SAFE_Z + SAFE_SIZE / 2), Color3.new(1, 1, 1),
	{ Transparency = 1, CanCollide = false })
label(sign, Enum.NormalId.Back, "SAFE ZONE", Color3.fromRGB(120, 220, 255))
label(sign, Enum.NormalId.Front, "SAFE ZONE", Color3.fromRGB(120, 220, 255))
-- Platzhalter für die Shops aus Phase 8
for i, shopName in ipairs({ "SellStand", "UpgradeShop", "TrailsShop", "Rebirth" }) do
	local x = (i - 2.5) * 22
	local pad = part(safe, shopName, Vector3.new(14, 1, 14), CFrame.new(x, 1.1, SAFE_Z - 30), Color3.fromRGB(255, 220, 80))
	pad:SetAttribute("ShopPlaceholder", true)
end

-- Autohäuser
local plots = folder(map, "Dealerships")
local GLASS = { Material = Enum.Material.Glass, Transparency = 0.5 }
local function buildDealership(index, side, z)
	local model = Instance.new("Model")
	model.Name = "Dealership" .. index
	model:SetAttribute("PlotIndex", index)
	model:SetAttribute("Owner", 0) -- UserId, 0 = frei
	model:SetAttribute("UnlockedSlots", 5)
	model.Parent = plots

	-- die Einfahrt zeigt zur Straße
	local cx = side * PLOT_X
	local frontX = cx - side * PLOT_W / 2
	local backX = cx + side * PLOT_W / 2
	local wallH = 14

	local floor = part(model, "Floor", Vector3.new(PLOT_W, 1, PLOT_D), CFrame.new(cx, 0.5, z), Color3.fromRGB(235, 235, 240),
		{ Material = Enum.Material.Marble })
	model.PrimaryPart = floor
	part(model, "BackWall", Vector3.new(1, wallH, PLOT_D), CFrame.new(backX, wallH / 2 + 1, z), Color3.fromRGB(180, 220, 255), GLASS)
	part(model, "SideWallA", Vector3.new(PLOT_W, wallH, 1), CFrame.new(cx, wallH / 2 + 1, z - PLOT_D / 2), Color3.fromRGB(180, 220, 255), GLASS)
	part(model, "SideWallB", Vector3.new(PLOT_W, wallH, 1), CFrame.new(cx, wallH / 2 + 1, z + PLOT_D / 2), Color3.fromRGB(180, 220, 255), GLASS)
	part(model, "Roof", Vector3.new(PLOT_W, 1, PLOT_D), CFrame.new(cx, wallH + 1.5, z), Color3.fromRGB(200, 230, 255),
		{ Material = Enum.Material.Glass, Transparency = 0.7 })
	-- Rahmen an der Vorderseite
	part(model, "FrontPillarA", Vector3.new(2, wallH, 2), CFrame.new(frontX, wallH / 2 + 1, z - PLOT_D / 2), Color3.fromRGB(40, 40, 45))
	part(model, "FrontPillarB", Vector3.new(2, wallH, 2), CFrame.new(frontX, wallH / 2 + 1, z + PLOT_D / 2), Color3.fromRGB(40, 40, 45))
	local header = part(model, "Sign", Vector3.new(2, 4, PLOT_D), CFrame.new(frontX, wallH + 3, z), Color3.fromRGB(40, 40, 45))
	label(header, side < 0 and Enum.NormalId.Right or Enum.NormalId.Left, "Freies Autohaus", Color3.new(1, 1, 1))

	-- Schutz-Tor (Laser), am Anfang offen
	local gate = part(model, "Gate", Vector3.new(1, wallH, PLOT_D - 2), CFrame.new(frontX, wallH / 2 + 1, z), Color3.fromRGB(255, 40, 40),
		{ Material = Enum.Material.Neon, Transparency = 1, CanCollide = false })
	gate:SetAttribute("Closed", false)

	-- 20 Stellplätze (4 Reihen × 5), die ersten 5 sind frei
	local slots = folder(model, "Slots")
	for n = 1, 20 do
		local row = math.floor((n - 1) / 5)
		local col = (n - 1) % 5
		local sx = backX - side * (8 + row * 12)
		local sz = z - PLOT_D / 2 + 8 + col * 16
		local unlocked = n <= 5
		local slot = part(slots, "Slot" .. n, Vector3.new(10, 0.2, 14), CFrame.new(sx, 1.1, sz),
			unlocked and Color3.fromRGB(80, 200, 255) or Color3.fromRGB(120, 120, 120),
			{ Material = Enum.Material.Neon, Transparency = unlocked and 0.3 or 0.85, CanCollide = false })
		slot:SetAttribute("SlotIndex", n)
		slot:SetAttribute("Unlocked", unlocked)
	end

	-- Zone zum Geld-Abholen (Phase 5)
	local collect = part(model, "CollectPad", Vector3.new(8, 0.4, 8), CFrame.new(frontX + side * 6, 1.2, z + PLOT_D / 2 - 6),
		Color3.fromRGB(60, 220, 90), { Material = Enum.Material.Neon })
	collect:SetAttribute("CollectPad", true)

	-- Bereich, in dem man vor der Polizei sicher ist (Phase 6)
	local home = part(model, "HomeZone", Vector3.new(PLOT_W, 20, PLOT_D), CFrame.new(cx, 10, z), Color3.new(1, 1, 1),
		{ Transparency = 1, CanCollide = false, CanQuery = false })
	home:SetAttribute("HomeZone", true)

	-- Zufahrt von der Straße
	part(model, "Driveway", Vector3.new(PLOT_X - PLOT_W / 2 - ROAD_WIDTH / 2, 0.2, 24),
		CFrame.new(side * (ROAD_WIDTH / 2 + (PLOT_X - PLOT_W / 2 - ROAD_WIDTH / 2) / 2), 0.1, z), ROAD)
end

local idx = 0
for _, side in ipairs({ -1, 1 }) do
	for _, z in ipairs(PLOT_ZS) do
		idx += 1
		buildDealership(idx, side, z)
	end
end

-- Städte
local cities = folder(map, "Cities")
for i, c in ipairs(CITIES) do
	local zStart = CITY_START_Z + (i - 1) * CITY_LEN
	local zMid = zStart + CITY_LEN / 2
	local city = folder(cities, c.name)
	city:SetAttribute("CityIndex", i)

	part(city, "Floor", Vector3.new(CITY_W, 2, CITY_LEN), CFrame.new(0, -1, zMid), c.floor)
	local area = part(city, "CityArea", Vector3.new(CITY_W, 40, CITY_LEN), CFrame.new(0, 20, zMid), Color3.new(1, 1, 1),
		{ Transparency = 1, CanCollide = false, CanQuery = false })
	area:SetAttribute("City", c.name)
	-- Seitenwände wie bei Steal a Egg
	for _, s in ipairs({ -1, 1 }) do
		part(city, "Wall", Vector3.new(4, 30, CITY_LEN), CFrame.new(s * (CITY_W / 2 + 2), 15, zMid), WALL, { Material = Enum.Material.Brick })
	end
	-- Torbogen mit Stadtnamen
	local archH, archW = 28, ROAD_WIDTH + 16
	part(city, "ArchPillarA", Vector3.new(4, archH, 4), CFrame.new(-archW / 2, archH / 2, zStart), c.accent)
	part(city, "ArchPillarB", Vector3.new(4, archH, 4), CFrame.new(archW / 2, archH / 2, zStart), c.accent)
	local top = part(city, "ArchTop", Vector3.new(archW + 4, 8, 4), CFrame.new(0, archH + 4, zStart), c.accent)
	label(top, Enum.NormalId.Front, c.name:upper(), Color3.new(1, 1, 1))
	label(top, Enum.NormalId.Back, c.name:upper(), Color3.new(1, 1, 1))
	-- Ordner für Phase 2 (Deko) und Phase 3 (Parkplätze/Autos)
	folder(city, "Buildings")
	folder(city, "ParkingSpots")
end
-- Abschlusswand am Ende
part(map, "EndWall", Vector3.new(CITY_W + 8, 30, 4), CFrame.new(0, 15, mapEndZ + 2), WALL, { Material = Enum.Material.Brick })

print("Steal a Car: Phase 1 fertig gebaut ✔")
