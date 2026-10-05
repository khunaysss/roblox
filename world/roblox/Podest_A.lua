-- Podest A (klassisch) als Vorlage: ReplicatedStorage/MemeWorld/PodestA. Oberkante der Noppen: 2.2 Studs.
-- Automatisch erzeugt aus world/blender. Ausfuehren in Roblox Studio (Command Bar oder MCP).
-- Position anpassen: ORIGIN unten aendern oder das Model danach verschieben.

local CollectionService = game:GetService("CollectionService")
local MATERIAL = {[0] = Enum.Material.SmoothPlastic, [1] = Enum.Material.Neon, [2] = Enum.Material.SmoothPlastic, [3] = Enum.Material.Glass}

-- Baut ein Model aus der Teile-Liste. Jede Zeile:
-- {Name, Art("B"=Block,"C"=Zylinder,"S"=Kugel), GroesseX,Y,Z, PosX,Y,Z, R00..R22 (Rotationsmatrix), Farbe, Material}
local function buildModel(name, rows, collide)
	local model = Instance.new("Model")
	model.Name = name
	local root = Instance.new("Part")
	root.Name = "RootPart"
	root.Size = Vector3.new(1, 1, 1)
	root.CFrame = CFrame.new(0, 0.5, 0)
	root.Transparency = 1
	root.Anchored = true
	root.CanCollide = false
	root.CanQuery = false
	root.CanTouch = false
	root.Parent = model
	model.PrimaryPart = root
	for _, r in ipairs(rows) do
		local part = Instance.new("Part")
		part.Name = r[1]
		if r[2] == "C" then
			part.Shape = Enum.PartType.Cylinder
		elseif r[2] == "S" then
			local mesh = Instance.new("SpecialMesh")
			mesh.MeshType = Enum.MeshType.Sphere
			mesh.Parent = part
		end
		part.Size = Vector3.new(r[3], r[4], r[5])
		part.CFrame = CFrame.new(r[6], r[7], r[8], r[9], r[10], r[11], r[12], r[13], r[14], r[15], r[16], r[17])
		part.Color = Color3.fromHex(r[18])
		part.Material = MATERIAL[r[19]] or Enum.Material.SmoothPlastic
		if r[19] == 2 then part.Reflectance = 0.25 end
		if r[19] == 3 then part.Transparency = 0.2 end
		part.TopSurface = Enum.SurfaceType.Smooth
		part.BottomSurface = Enum.SurfaceType.Smooth
		part.Anchored = true
		part.CanCollide = collide and string.sub(r[1], 1, 3) ~= "FX_"
		part.CastShadow = true
		part.Parent = model
	end
	return model
end

local function folder(parent, name)
	local f = parent:FindFirstChild(name)
	if not f then
		f = Instance.new("Folder")
		f.Name = name
		f.Parent = parent
	end
	return f
end

local ROWS = {
	{"Base","B",5,5,1.2,0,0.6,0,-1,0,0,0,0,1,0,1,0,"#2f6fe0",0},
	{"Top","B",4.2,4.2,0.8,0,1.6,0,-1,0,0,0,0,1,0,1,0,"#f2f2f2",0},
	{"Plate","B",3.2,0.2,0.7,0,0.6,-2.55,-1,0,0,0,0,1,0,1,0,"#ffc83a",2},
	{"Stud","C",0.2,0.593,0.593,1.5,2.1,-1.5,0,-1,0,1,0,0,0,0,1,"#f2f2f2",0},
	{"Stud","C",0.2,0.593,0.593,1.5,2.1,-0.5,0,-1,0,1,0,0,0,0,1,"#f2f2f2",0},
	{"Stud","C",0.2,0.593,0.593,1.5,2.1,0.5,0,-1,0,1,0,0,0,0,1,"#f2f2f2",0},
	{"Stud","C",0.2,0.593,0.593,1.5,2.1,1.5,0,-1,0,1,0,0,0,0,1,"#f2f2f2",0},
	{"Stud","C",0.2,0.593,0.593,0.5,2.1,-1.5,0,-1,0,1,0,0,0,0,1,"#f2f2f2",0},
	{"Stud","C",0.2,0.593,0.593,0.5,2.1,-0.5,0,-1,0,1,0,0,0,0,1,"#f2f2f2",0},
	{"Stud","C",0.2,0.593,0.593,0.5,2.1,0.5,0,-1,0,1,0,0,0,0,1,"#f2f2f2",0},
	{"Stud","C",0.2,0.593,0.593,0.5,2.1,1.5,0,-1,0,1,0,0,0,0,1,"#f2f2f2",0},
	{"Stud","C",0.2,0.593,0.593,-0.5,2.1,-1.5,0,-1,0,1,0,0,0,0,1,"#f2f2f2",0},
	{"Stud","C",0.2,0.593,0.593,-0.5,2.1,-0.5,0,-1,0,1,0,0,0,0,1,"#f2f2f2",0},
	{"Stud","C",0.2,0.593,0.593,-0.5,2.1,0.5,0,-1,0,1,0,0,0,0,1,"#f2f2f2",0},
	{"Stud","C",0.2,0.593,0.593,-0.5,2.1,1.5,0,-1,0,1,0,0,0,0,1,"#f2f2f2",0},
	{"Stud","C",0.2,0.593,0.593,-1.5,2.1,-1.5,0,-1,0,1,0,0,0,0,1,"#f2f2f2",0},
	{"Stud","C",0.2,0.593,0.593,-1.5,2.1,-0.5,0,-1,0,1,0,0,0,0,1,"#f2f2f2",0},
	{"Stud","C",0.2,0.593,0.593,-1.5,2.1,0.5,0,-1,0,1,0,0,0,0,1,"#f2f2f2",0},
	{"Stud","C",0.2,0.593,0.593,-1.5,2.1,1.5,0,-1,0,1,0,0,0,0,1,"#f2f2f2",0},
}

local ORIGIN = CFrame.new(0, 0, 0)
local parent = folder(game:GetService("ReplicatedStorage"), "MemeWorld")
local old = parent:FindFirstChild("PodestA")
if old then old:Destroy() end
local model = buildModel("PodestA", ROWS, true)

model:PivotTo(ORIGIN)
model.Parent = parent
print("PodestA gebaut (" .. #ROWS .. " Teile)")
