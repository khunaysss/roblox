-- Einmalige Einrichtung des importierten Trainings-Gyms in Studio (Edit-Modus, z. B. ueber die Befehlszeile bzw. MCP).
-- Voraussetzung: export/Training_Gym_v02_Roblox.fbx ueber Import 3D importiert (Centimeter, Faktor 1) und
-- export/Training_Gym_v02_data.luau als ServerStorage.CC_GymData (ModuleScript) vorhanden.
-- Ergebnis: Workspace.CC_Gym (Modell, Bodenoberkante y = 0, Bodenmitte bei GYM_CENTER), Farben/Materialien,
-- Kollision (Waende/Boeden selbst, Einrichtung ueber unsichtbare COL-Teile), Lampen, Interaktionspunkte (CC_GymInteractions).
local GYM_CENTER = Vector3.new(160, 0, 0)          -- weit neben der Arena-Halle (die liegt um x = 0)

local SS = game:GetService("ServerStorage")
local data = require(SS:WaitForChild("CC_GymData"))
local model = workspace:FindFirstChild("CC_Gym") or workspace:FindFirstChild("Training_Gym_v02_Roblox")
assert(model, "Importiertes Gym-Modell nicht gefunden (Training_Gym_v02_Roblox)")
model.Name = "CC_Gym"

-- 1) Ausrichten: Bezugs-Boden auf die Zielposition
local floor = model:FindFirstChild(data.ref.parts[1], true)
assert(floor and floor:IsA("BasePart"), "Bezugsboden fehlt: " .. tostring(data.ref.parts[1]))
local floorCenter = GYM_CENTER - Vector3.new(0, data.ref.size[2] / 2, 0)
model:PivotTo(model:GetPivot() + (floorCenter - floor.Position))
-- Der FBX-Import dreht das Modell um 180 Grad um Y (gemessen: Sack, Trainer-Tisch, Spinde, Tuer liegen bei (-x, y, -z)).
-- Daten aus Blender (Roblox-Achsen, relativ zur Bodenmitte) deshalb ebenfalls um 180 Grad drehen.
local FLIP = CFrame.Angles(0, math.pi, 0)
local BASE = CFrame.new(floorCenter) * FLIP
local function world(p) return BASE * Vector3.new(p[1], p[2], p[3]) end

-- 2) Teile: Farbe, Material, Kollision
local function starts(s, list) for _, x in ipairs(list) do if s:sub(1, #x) == x then return true end end return false end
local PRECISE = { "Wall_North", "Wall_South", "Wall_East", "Wall_West", "LockerRoom_Shell", "Door_Entrance_Frame", "Door_LockerRoom_Frame", "Cage_Door_Frame_Static", "Window_" }
local SOLID = { "Floor_", "Rubber_Floor", "Mat_Tile", "Cage_Canvas", "Cage_Platform_Skirt", "Cage_Apron", "Wall_Pad", "Cage_Post", "Mirror_Large", "Customization_Spot", "Exercise_Mat", "Cage_Mat_Logo", "Cage_Corner" }
local hasCol = {}
for _, c in ipairs(data.collision) do if c.parent then hasCol[c.parent] = true end end
local MATERIAL = {
	GY_Chrome = Enum.Material.Metal, M_Metal_Dark = Enum.Material.Metal, GY_Painted_Metal_Black = Enum.Material.Metal, GY_Painted_Metal_Red = Enum.Material.Metal,
	GY_Steel_Beam = Enum.Material.Metal, GY_Locker_Metal_Grey = Enum.Material.Metal, GY_Door_Steel = Enum.Material.DiamondPlate, GY_Chain_Metal = Enum.Material.Metal,
	GY_Wood_Warm = Enum.Material.WoodPlanks, GY_Floor_Concrete_Warm = Enum.Material.Concrete, GY_Floor_Rubber_Tiles = Enum.Material.Rubber,
	GY_Bag_Fabric = Enum.Material.Fabric, GY_Leather_Red_Worn = Enum.Material.Leather, GY_Leather_Black_Worn = Enum.Material.Leather,
	GY_Wall_Paint = Enum.Material.Plaster, GY_Cork = Enum.Material.Cardboard, GY_Mat_Charcoal = Enum.Material.Rubber,
}
local stats = { parts = 0, colored = 0, precise = 0, solid = 0, open = 0, missing = 0 }
for _, p in ipairs(model:GetDescendants()) do
	if p:IsA("BasePart") then
		stats.parts += 1
		p.Anchored = true
		local c = data.colors[p.Name]
		if c then
			stats.colored += 1
			p.Color = Color3.fromRGB(c.rgb[1], c.rgb[2], c.rgb[3])
			if c.glow then p.Material = Enum.Material.Neon
			elseif MATERIAL[c.mat] then p.Material = MATERIAL[c.mat] end
			if c.mat == "GY_Chrome" then p.Reflectance = 0.25 end
			if c.mat == "GY_Mirror_Preview" then p.Material = Enum.Material.Glass; p.Reflectance = 0.6 end
			if c.mat == "M_Fence_Diamond" then p.Transparency = 0.55 end
			local src = c.src
			if starts(src, PRECISE) then
				p.CanCollide = true
				pcall(function() p.CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition end)
				stats.precise += 1
			elseif starts(src, SOLID) and not hasCol[src] then
				p.CanCollide = true; stats.solid += 1
			else
				p.CanCollide = false; p.CanTouch = false; stats.open += 1
			end
			p.CastShadow = not (c.glow or c.coll == "Lights")
		else
			stats.missing += 1
		end
	end
end

-- 3) Kollisionsteile (unsichtbar)
local colF = model:FindFirstChild("CC_GymCollision") or Instance.new("Folder")
colF.Name = "CC_GymCollision"; colF:ClearAllChildren(); colF.Parent = model
for _, c in ipairs(data.collision) do
	local pt = Instance.new("Part")
	pt.Name = c.name; pt.Anchored = true; pt.Transparency = 1; pt.CanCollide = true; pt.CanTouch = false; pt.CastShadow = false
	local r, w = c.rot, world(c.pos)
	pt.Size = Vector3.new(math.max(c.size[1], 0.2), math.max(c.size[2], 0.2), math.max(c.size[3], 0.2))
	pt.CFrame = BASE * CFrame.new(c.pos[1], c.pos[2], c.pos[3], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9])
	pt.Parent = colF
end

-- 4) Lampen (ohne Sonne; Licht der Halle bleibt in Lighting)
local lightF = model:FindFirstChild("CC_GymLights") or Instance.new("Folder")
lightF.Name = "CC_GymLights"; lightF:ClearAllChildren(); lightF.Parent = model
local nLights = 0
for _, l in ipairs(data.lights) do
	if l.type ~= "SUN" then
		local pos, dir = world(l.pos), FLIP * Vector3.new(l.dir[1], l.dir[2], l.dir[3])
		local pt = Instance.new("Part")
		pt.Name = l.name; pt.Size = Vector3.new(0.4, 0.4, 0.4); pt.Anchored = true; pt.Transparency = 1
		pt.CanCollide = false; pt.CanQuery = false; pt.CanTouch = false; pt.CastShadow = false
		pt.CFrame = CFrame.lookAt(pos, pos + (dir.Magnitude > 0.01 and dir or Vector3.new(0, -1, 0)))
		local color = Color3.fromRGB(l.rgb[1], l.rgb[2], l.rgb[3])
		local li
		if l.type == "SPOT" then
			li = Instance.new("SpotLight"); li.Face = Enum.NormalId.Front; li.Angle = math.clamp(l.angle or 60, 20, 120)
			li.Range = 40; li.Brightness = math.clamp(l.energy / 120, 0.4, 2.5)
		else
			li = Instance.new("PointLight"); li.Range = 22; li.Brightness = math.clamp(l.energy / 90, 0.3, 1.6)
		end
		li.Color = color; li.Shadows = l.type == "SPOT"; li.Parent = pt
		pt.Parent = lightF; nLights += 1
	end
end

-- 5) Interaktionspunkte (fuer spaetere Trainings-/Spinde-/Trainer-Logik)
local inter = workspace:FindFirstChild("CC_GymInteractions") or Instance.new("Folder")
inter.Name = "CC_GymInteractions"; inter:ClearAllChildren(); inter.Parent = workspace
for _, i in ipairs(data.interactions) do
	local pt = Instance.new("Part")
	pt.Name = i.name; pt.Anchored = true; pt.Transparency = 1; pt.CanCollide = false; pt.CanQuery = false; pt.CanTouch = false
	pt.Size = Vector3.new(math.max(i.size[1], 1), math.max(i.size[2], 1), math.max(i.size[3], 1))
	pt.Position = world(i.pos)
	pt:SetAttribute("CC_Interaction", i.kind)
	for k, v in pairs(i.props) do if k ~= "interaction" and type(v) ~= "table" then pt:SetAttribute("CC_" .. k, v) end end
	pt.Parent = inter
end

return ("Gym eingerichtet: %d Teile (%d gefaerbt, %d ohne Daten) | Kollision: %d genau, %d fest, %d aus + %d COL-Teile | %d Lampen | %d Interaktionspunkte"):format(
	stats.parts, stats.colored, stats.missing, stats.precise, stats.solid, stats.open, #data.collision, nLights, #data.interactions)
