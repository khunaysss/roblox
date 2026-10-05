-- Wahrzeichen B: Tempel. Wird in Workspace/MemeWorld/Tempel gebaut.
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
	{"Stair","B",44,30.8,2,0,1,0,-1,0,0,0,0,1,0,1,0,"#9aa0a8",0},
	{"Stair","B",38,26.6,2,0,3,0,-1,0,0,0,0,1,0,1,0,"#b8bcc4",0},
	{"Stair","B",32,22.4,2,0,5,0,-1,0,0,0,0,1,0,1,0,"#d8dce2",0},
	{"Column","C",18,2.971,2.971,13,15,-8.4,0,-1,0,1,0,0,0,0,1,"#f4f4f4",0},
	{"ColTop","B",3.6,3.6,1.2,13,24.4,-8.4,-1,0,0,0,0,1,0,1,0,"#ffc83a",0},
	{"Column","C",18,2.971,2.971,13,15,8.4,0,-1,0,1,0,0,0,0,1,"#f4f4f4",0},
	{"ColTop","B",3.6,3.6,1.2,13,24.4,8.4,-1,0,0,0,0,1,0,1,0,"#ffc83a",0},
	{"Column","C",18,2.971,2.971,7.8,15,-8.4,0,-1,0,1,0,0,0,0,1,"#f4f4f4",0},
	{"ColTop","B",3.6,3.6,1.2,7.8,24.4,-8.4,-1,0,0,0,0,1,0,1,0,"#ffc83a",0},
	{"Column","C",18,2.971,2.971,7.8,15,8.4,0,-1,0,1,0,0,0,0,1,"#f4f4f4",0},
	{"ColTop","B",3.6,3.6,1.2,7.8,24.4,8.4,-1,0,0,0,0,1,0,1,0,"#ffc83a",0},
	{"Column","C",18,2.971,2.971,2.6,15,-8.4,0,-1,0,1,0,0,0,0,1,"#f4f4f4",0},
	{"ColTop","B",3.6,3.6,1.2,2.6,24.4,-8.4,-1,0,0,0,0,1,0,1,0,"#ffc83a",0},
	{"Column","C",18,2.971,2.971,2.6,15,8.4,0,-1,0,1,0,0,0,0,1,"#f4f4f4",0},
	{"ColTop","B",3.6,3.6,1.2,2.6,24.4,8.4,-1,0,0,0,0,1,0,1,0,"#ffc83a",0},
	{"Column","C",18,2.971,2.971,-2.6,15,-8.4,0,-1,0,1,0,0,0,0,1,"#f4f4f4",0},
	{"ColTop","B",3.6,3.6,1.2,-2.6,24.4,-8.4,-1,0,0,0,0,1,0,1,0,"#ffc83a",0},
	{"Column","C",18,2.971,2.971,-2.6,15,8.4,0,-1,0,1,0,0,0,0,1,"#f4f4f4",0},
	{"ColTop","B",3.6,3.6,1.2,-2.6,24.4,8.4,-1,0,0,0,0,1,0,1,0,"#ffc83a",0},
	{"Column","C",18,2.971,2.971,-7.8,15,-8.4,0,-1,0,1,0,0,0,0,1,"#f4f4f4",0},
	{"ColTop","B",3.6,3.6,1.2,-7.8,24.4,-8.4,-1,0,0,0,0,1,0,1,0,"#ffc83a",0},
	{"Column","C",18,2.971,2.971,-7.8,15,8.4,0,-1,0,1,0,0,0,0,1,"#f4f4f4",0},
	{"ColTop","B",3.6,3.6,1.2,-7.8,24.4,8.4,-1,0,0,0,0,1,0,1,0,"#ffc83a",0},
	{"Column","C",18,2.971,2.971,-13,15,-8.4,0,-1,0,1,0,0,0,0,1,"#f4f4f4",0},
	{"ColTop","B",3.6,3.6,1.2,-13,24.4,-8.4,-1,0,0,0,0,1,0,1,0,"#ffc83a",0},
	{"Column","C",18,2.971,2.971,-13,15,8.4,0,-1,0,1,0,0,0,0,1,"#f4f4f4",0},
	{"ColTop","B",3.6,3.6,1.2,-13,24.4,8.4,-1,0,0,0,0,1,0,1,0,"#ffc83a",0},
	{"Roof","B",34,22,2.4,0,26.2,0,-1,0,0,0,0,1,0,1,0,"#d81818",0},
	{"RoofStep","B",30,18,2,0,28.4,0,-1,0,0,0,0,1,0,1,0,"#b81414",0},
	{"RoofStep","B",23,14.8,2,0,30.4,0,-1,0,0,0,0,1,0,1,0,"#d81818",0},
	{"RoofStep","B",16,11.6,2,0,32.4,0,-1,0,0,0,0,1,0,1,0,"#b81414",0},
	{"RoofStep","B",9,8.4,2,0,34.4,0,-1,0,0,0,0,1,0,1,0,"#d81818",0},
	{"Stud","C",0.4,1.186,1.186,2.6,35.6,-1.3,0,-1,0,1,0,0,0,0,1,"#d81818",0},
	{"Stud","C",0.4,1.186,1.186,2.6,35.6,1.3,0,-1,0,1,0,0,0,0,1,"#d81818",0},
	{"Stud","C",0.4,1.186,1.186,0,35.6,-1.3,0,-1,0,1,0,0,0,0,1,"#d81818",0},
	{"Stud","C",0.4,1.186,1.186,0,35.6,1.3,0,-1,0,1,0,0,0,0,1,"#d81818",0},
	{"Stud","C",0.4,1.186,1.186,-2.6,35.6,-1.3,0,-1,0,1,0,0,0,0,1,"#d81818",0},
	{"Stud","C",0.4,1.186,1.186,-2.6,35.6,1.3,0,-1,0,1,0,0,0,0,1,"#d81818",0},
	{"Dice","B",6.4,6.4,6.4,0,14,0,-0.88,0.081,-0.468,-0.389,0.442,0.808,0.272,0.894,-0.357,"#f4f4f4",0},
}

local ORIGIN = CFrame.new(-150, 0, 0)
local parent = folder(workspace, "MemeWorld")
local old = parent:FindFirstChild("Tempel")
if old then old:Destroy() end
local model = buildModel("Tempel", ROWS, true)

model:PivotTo(ORIGIN)
model.Parent = parent
print("Tempel gebaut (" .. #ROWS .. " Teile)")
