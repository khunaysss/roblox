-- setup_trainer_rigged_v01.luau (einmal in Studio im Edit-Modus ausfuehren, nach dem Import von export/Trainer_<Name>_Rigged_v01.fbx)
-- Import: Import 3D, Rig-Typ Custom, Einheit Centimeter, Faktor 1 (wie der Kaempfer).
-- Macht aus dem importierten Modell einen animierbaren Trainer fuer CC_Trainers:
--   Teile nach export/Trainer_<Name>_Rigged_v01_data.luau faerben, Kollision nur ueber den Wurzelteil (unsichtbare Saeule),
--   Drehpunkt an der Fusssohle (Blick -Z wie bisher), AnimationController + Animator,
--   ersetzt ServerStorage.CC_StyleTrainers.<Name> (das starre Modell wandert nach ServerStorage.CC_Old).
-- Aufruf: _G.CC_SetupTrainerRig("Mike_Tyson")
local HS = game:GetService("HttpService")

_G.CC_SetupTrainerRig = function(name)
	local src = workspace:FindFirstChild("Trainer_" .. name .. "_Rigged_v01")
	assert(src, "Importiertes Modell 'Trainer_" .. name .. "_Rigged_v01' nicht gefunden")
	HS.HttpEnabled = true
	local ok, txt = pcall(function() return HS:GetAsync("http://127.0.0.1:8766/export/Trainer_" .. name .. "_Rigged_v01_data.luau") end)
	HS.HttpEnabled = false
	assert(ok, "Daten nicht geladen (lokaler Server 8766?): " .. tostring(txt))
	local data = loadstring(txt)()

	local root = src:FindFirstChild("RootPart") or src.PrimaryPart
	assert(root and root:FindFirstChild("Root"), "Wurzelteil mit Bone 'Root' fehlt")
	local colored, parts = 0, 0
	for _, d in ipairs(src:GetDescendants()) do
		if d:IsA("MeshPart") then
			parts += 1
			local key = d.Name:gsub("%.%d+$", "")
			local c = data.colors[d.Name] or data.colors[key]
			if c then d.Color = Color3.fromRGB(c[1], c[2], c[3]); colored += 1 end
			d.Material = Enum.Material.SmoothPlastic
			d.Anchored = false; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.Massless = true; d.CastShadow = true
		end
	end
	-- Hoehe pruefen (nur Meshes)
	local lo, hi = math.huge, -math.huge
	for _, d in ipairs(src:GetDescendants()) do
		if d:IsA("MeshPart") then lo = math.min(lo, d.Position.Y - d.Size.Y / 2); hi = math.max(hi, d.Position.Y + d.Size.Y / 2) end
	end
	local h = hi - lo
	-- Wurzelteil = unsichtbare Kollisionssaeule, Drehpunkt an der Fusssohle
	root.Anchored = true; root.CanCollide = true; root.CanQuery = true; root.CanTouch = false; root.Transparency = 1
	local rootCF = root.CFrame
	src.PrimaryPart = root
	root.PivotOffset = rootCF:ToObjectSpace(CFrame.new(rootCF.Position.X, lo, rootCF.Position.Z) * rootCF.Rotation)
	local ac = src:FindFirstChildOfClass("AnimationController") or Instance.new("AnimationController", src)
	if not ac:FindFirstChildOfClass("Animator") then Instance.new("Animator", ac) end
	src:SetAttribute("CC_TrainerRig", true)
	src:SetAttribute("CC_TrainerId", name)
	-- an die Stelle des starren Modells
	local folder = game.ServerStorage:FindFirstChild("CC_StyleTrainers")
	assert(folder, "ServerStorage.CC_StyleTrainers fehlt")
	local old = folder:FindFirstChild(name)
	if old then
		local arch = game.ServerStorage:FindFirstChild("CC_Old") or Instance.new("Folder", game.ServerStorage); arch.Name = "CC_Old"
		old.Name = name .. "_Static_v01"; old.Parent = arch
	end
	src.Name = name
	src:PivotTo(CFrame.new())
	src.Parent = folder
	return ("Trainer %s: %d Teile, %d gefaerbt, Hoehe %.2f Studs (Soll %.2f)"):format(name, parts, colored, h, data.height)
end
