-- Boss-Turm A: Festung. Dach = Boss-Arena, Leiter an der Rueckseite.
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
	{"Layer","B",24,24,2,0,1,0,-1,0,0,0,0,1,0,1,0,"#9aa0a8",0},
	{"Layer","B",24,24,2,0,3,0,-1,0,0,0,0,1,0,1,0,"#7f858d",0},
	{"Layer","B",24,24,2,0,5,0,-1,0,0,0,0,1,0,1,0,"#b0b5bc",0},
	{"Layer","B",24,24,2,0,7,0,-1,0,0,0,0,1,0,1,0,"#9aa0a8",0},
	{"Layer","B",24,24,2,0,9,0,-1,0,0,0,0,1,0,1,0,"#7f858d",0},
	{"Layer","B",24,24,2,0,11,0,-1,0,0,0,0,1,0,1,0,"#b0b5bc",0},
	{"Layer","B",24,24,2,0,13,0,-1,0,0,0,0,1,0,1,0,"#9aa0a8",0},
	{"Layer","B",24,24,2,0,15,0,-1,0,0,0,0,1,0,1,0,"#7f858d",0},
	{"Layer","B",24,24,2,0,17,0,-1,0,0,0,0,1,0,1,0,"#b0b5bc",0},
	{"Layer","B",24,24,2,0,19,0,-1,0,0,0,0,1,0,1,0,"#9aa0a8",0},
	{"Layer","B",24,24,2,0,21,0,-1,0,0,0,0,1,0,1,0,"#7f858d",0},
	{"Layer","B",24,24,2,0,23,0,-1,0,0,0,0,1,0,1,0,"#b0b5bc",0},
	{"Layer","B",24,24,2,0,25,0,-1,0,0,0,0,1,0,1,0,"#9aa0a8",0},
	{"Layer","B",24,24,2,0,27,0,-1,0,0,0,0,1,0,1,0,"#7f858d",0},
	{"Layer","B",24,24,2,0,29,0,-1,0,0,0,0,1,0,1,0,"#b0b5bc",0},
	{"Layer","B",24,24,2,0,31,0,-1,0,0,0,0,1,0,1,0,"#9aa0a8",0},
	{"Layer","B",24,24,2,0,33,0,-1,0,0,0,0,1,0,1,0,"#7f858d",0},
	{"Layer","B",24,24,2,0,35,0,-1,0,0,0,0,1,0,1,0,"#b0b5bc",0},
	{"Layer","B",24,24,2,0,37,0,-1,0,0,0,0,1,0,1,0,"#9aa0a8",0},
	{"Layer","B",24,24,2,0,39,0,-1,0,0,0,0,1,0,1,0,"#7f858d",0},
	{"Layer","B",24,24,2,0,41,0,-1,0,0,0,0,1,0,1,0,"#b0b5bc",0},
	{"Layer","B",24,24,2,0,43,0,-1,0,0,0,0,1,0,1,0,"#9aa0a8",0},
	{"Corner","B",4.8,4.8,50,12,25,-12,-1,0,0,0,0,1,0,1,0,"#5a6068",0},
	{"CornerRoof","B",4.702,4.702,1.75,12,50.875,-12,0,1,0,0,0,1,1,0,0,"#d81818",0},
	{"CornerRoof","B",3.359,3.359,1.75,12,52.625,-12,0,1,0,0,0,1,1,0,0,"#d81818",0},
	{"CornerRoof","B",2.015,2.015,1.75,12,54.375,-12,0,1,0,0,0,1,1,0,0,"#d81818",0},
	{"CornerRoof","B",0.672,0.672,1.75,12,56.125,-12,0,1,0,0,0,1,1,0,0,"#d81818",0},
	{"Corner","B",4.8,4.8,50,12,25,12,-1,0,0,0,0,1,0,1,0,"#5a6068",0},
	{"CornerRoof","B",4.702,4.702,1.75,12,50.875,12,0,1,0,0,0,1,1,0,0,"#d81818",0},
	{"CornerRoof","B",3.359,3.359,1.75,12,52.625,12,0,1,0,0,0,1,1,0,0,"#d81818",0},
	{"CornerRoof","B",2.015,2.015,1.75,12,54.375,12,0,1,0,0,0,1,1,0,0,"#d81818",0},
	{"CornerRoof","B",0.672,0.672,1.75,12,56.125,12,0,1,0,0,0,1,1,0,0,"#d81818",0},
	{"Corner","B",4.8,4.8,50,-12,25,-12,-1,0,0,0,0,1,0,1,0,"#5a6068",0},
	{"CornerRoof","B",4.702,4.702,1.75,-12,50.875,-12,0,1,0,0,0,1,1,0,0,"#d81818",0},
	{"CornerRoof","B",3.359,3.359,1.75,-12,52.625,-12,0,1,0,0,0,1,1,0,0,"#d81818",0},
	{"CornerRoof","B",2.015,2.015,1.75,-12,54.375,-12,0,1,0,0,0,1,1,0,0,"#d81818",0},
	{"CornerRoof","B",0.672,0.672,1.75,-12,56.125,-12,0,1,0,0,0,1,1,0,0,"#d81818",0},
	{"Corner","B",4.8,4.8,50,-12,25,12,-1,0,0,0,0,1,0,1,0,"#5a6068",0},
	{"CornerRoof","B",4.702,4.702,1.75,-12,50.875,12,0,1,0,0,0,1,1,0,0,"#d81818",0},
	{"CornerRoof","B",3.359,3.359,1.75,-12,52.625,12,0,1,0,0,0,1,1,0,0,"#d81818",0},
	{"CornerRoof","B",2.015,2.015,1.75,-12,54.375,12,0,1,0,0,0,1,1,0,0,"#d81818",0},
	{"CornerRoof","B",0.672,0.672,1.75,-12,56.125,12,0,1,0,0,0,1,1,0,0,"#d81818",0},
	{"Merlon","B",2.4,2.4,2.8,12,45.4,-12,-1,0,0,0,0,1,0,1,0,"#9aa0a8",0},
	{"Stud","C",0.4,1.2,1.2,12,47,-12,0,-1,0,1,0,0,0,0,1,"#9aa0a8",0},
	{"Merlon","B",2.4,2.4,2.8,12,45.4,12,-1,0,0,0,0,1,0,1,0,"#9aa0a8",0},
	{"Stud","C",0.4,1.2,1.2,12,47,12,0,-1,0,1,0,0,0,0,1,"#9aa0a8",0},
	{"Merlon","B",2.4,2.4,2.8,12,45.4,-12,-1,0,0,0,0,1,0,1,0,"#9aa0a8",0},
	{"Stud","C",0.4,1.2,1.2,12,47,-12,0,-1,0,1,0,0,0,0,1,"#9aa0a8",0},
	{"Merlon","B",2.4,2.4,2.8,-12,45.4,-12,-1,0,0,0,0,1,0,1,0,"#9aa0a8",0},
	{"Stud","C",0.4,1.2,1.2,-12,47,-12,0,-1,0,1,0,0,0,0,1,"#9aa0a8",0},
	{"Merlon","B",2.4,2.4,2.8,4,45.4,-12,-1,0,0,0,0,1,0,1,0,"#9aa0a8",0},
	{"Stud","C",0.4,1.2,1.2,4,47,-12,0,-1,0,1,0,0,0,0,1,"#9aa0a8",0},
	{"Merlon","B",2.4,2.4,2.8,4,45.4,12,-1,0,0,0,0,1,0,1,0,"#9aa0a8",0},
	{"Stud","C",0.4,1.2,1.2,4,47,12,0,-1,0,1,0,0,0,0,1,"#9aa0a8",0},
	{"Merlon","B",2.4,2.4,2.8,12,45.4,-4,-1,0,0,0,0,1,0,1,0,"#9aa0a8",0},
	{"Stud","C",0.4,1.2,1.2,12,47,-4,0,-1,0,1,0,0,0,0,1,"#9aa0a8",0},
	{"Merlon","B",2.4,2.4,2.8,-12,45.4,-4,-1,0,0,0,0,1,0,1,0,"#9aa0a8",0},
	{"Stud","C",0.4,1.2,1.2,-12,47,-4,0,-1,0,1,0,0,0,0,1,"#9aa0a8",0},
	{"Merlon","B",2.4,2.4,2.8,-4,45.4,-12,-1,0,0,0,0,1,0,1,0,"#9aa0a8",0},
	{"Stud","C",0.4,1.2,1.2,-4,47,-12,0,-1,0,1,0,0,0,0,1,"#9aa0a8",0},
	{"Merlon","B",2.4,2.4,2.8,-4,45.4,12,-1,0,0,0,0,1,0,1,0,"#9aa0a8",0},
	{"Stud","C",0.4,1.2,1.2,-4,47,12,0,-1,0,1,0,0,0,0,1,"#9aa0a8",0},
	{"Merlon","B",2.4,2.4,2.8,12,45.4,4,-1,0,0,0,0,1,0,1,0,"#9aa0a8",0},
	{"Stud","C",0.4,1.2,1.2,12,47,4,0,-1,0,1,0,0,0,0,1,"#9aa0a8",0},
	{"Merlon","B",2.4,2.4,2.8,-12,45.4,4,-1,0,0,0,0,1,0,1,0,"#9aa0a8",0},
	{"Stud","C",0.4,1.2,1.2,-12,47,4,0,-1,0,1,0,0,0,0,1,"#9aa0a8",0},
	{"Merlon","B",2.4,2.4,2.8,-12,45.4,-12,-1,0,0,0,0,1,0,1,0,"#9aa0a8",0},
	{"Stud","C",0.4,1.2,1.2,-12,47,-12,0,-1,0,1,0,0,0,0,1,"#9aa0a8",0},
	{"Merlon","B",2.4,2.4,2.8,-12,45.4,12,-1,0,0,0,0,1,0,1,0,"#9aa0a8",0},
	{"Stud","C",0.4,1.2,1.2,-12,47,12,0,-1,0,1,0,0,0,0,1,"#9aa0a8",0},
	{"Merlon","B",2.4,2.4,2.8,12,45.4,12,-1,0,0,0,0,1,0,1,0,"#9aa0a8",0},
	{"Stud","C",0.4,1.2,1.2,12,47,12,0,-1,0,1,0,0,0,0,1,"#9aa0a8",0},
	{"Merlon","B",2.4,2.4,2.8,-12,45.4,12,-1,0,0,0,0,1,0,1,0,"#9aa0a8",0},
	{"Stud","C",0.4,1.2,1.2,-12,47,12,0,-1,0,1,0,0,0,0,1,"#9aa0a8",0},
	{"Door","B",7.2,0.8,10.4,0,5.2,-12.2,-1,0,0,0,0,1,0,1,0,"#5a3a22",0},
	{"DoorArch","B",8.8,1,1.6,0,11.2,-12.3,-1,0,0,0,0,1,0,1,0,"#ffc83a",0},
	{"Window","B",2.4,0.6,4.4,6,18,-12.1,-1,0,0,0,0,1,0,1,0,"#ffd23a",1},
	{"Window","B",2.4,0.6,4.4,0,18,-12.1,-1,0,0,0,0,1,0,1,0,"#ffd23a",1},
	{"Window","B",2.4,0.6,4.4,-6,18,-12.1,-1,0,0,0,0,1,0,1,0,"#ffd23a",1},
	{"Window","B",2.4,0.6,4.4,6,30,-12.1,-1,0,0,0,0,1,0,1,0,"#ffd23a",1},
	{"Window","B",2.4,0.6,4.4,0,30,-12.1,-1,0,0,0,0,1,0,1,0,"#ffd23a",1},
	{"Window","B",2.4,0.6,4.4,-6,30,-12.1,-1,0,0,0,0,1,0,1,0,"#ffd23a",1},
	{"Pole","C",14,0.48,0.48,0,51,0,0,-1,0,1,0,0,0,0,1,"#3a3a3a",0},
	{"Flag","B",6,0.2,3.6,-3.1,56,0,-1,0,0,0,0,1,0,1,0,"#d81818",0},
	{"FX_BossOrb","S",4.8,4.8,4.8,0,49,0,-1,0,0,0,0,1,0,1,0,"#ff3f3f",1},
}

local ORIGIN = CFrame.new(150, 0, 0)
local parent = folder(workspace, "MemeWorld")
local old = parent:FindFirstChild("BossTurm")
if old then old:Destroy() end
local model = buildModel("BossTurm", ROWS, true)
-- Leiter an der Rueckseite, damit Spieler aufs Dach (Boss-Arena) kommen
local ladder = Instance.new("TrussPart")
ladder.Name = "Leiter"
ladder.Size = Vector3.new(2, 46, 2)
ladder.CFrame = CFrame.new(0, 23, 13.4)
ladder.Color = Color3.fromHex("#5a3a22")
ladder.Anchored = true
ladder.Parent = model
local arena = Instance.new("Part")
arena.Name = "BossArena"
arena.Size = Vector3.new(22, 1, 22)
arena.CFrame = CFrame.new(0, 44.5, 0)
arena.Transparency = 1
arena.Anchored = true
arena.CanCollide = false
arena.Parent = model -- unsichtbarer Marker fuer das Boss-Skript (Mitte der Dachflaeche)
model:PivotTo(ORIGIN)
model.Parent = parent
print("BossTurm gebaut (" .. #ROWS .. " Teile)")
