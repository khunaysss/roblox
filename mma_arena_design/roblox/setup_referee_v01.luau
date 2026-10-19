-- setup_referee_v01.luau (einmal in Studio im Edit-Modus ausfuehren, nach dem Import von export/Referee_Rigged_v01.fbx)
-- Import: Import 3D, Rig-Typ Custom, Einheit Centimeter, Faktor 1 (wie Kaempfer und Trainer).
-- Wie setup_trainer_rigged_v01.luau: Farben aus export/Referee_Rigged_v01_data.luau, Drehpunkt an der Fusssohle,
-- AnimationController + Animator. Ergebnis: ServerStorage.CC_Referee (CC_Referee.server nimmt es statt des Platzhalters).
-- Aufruf: _G.CC_SetupReferee()
local HS = game:GetService("HttpService")

_G.CC_SetupReferee = function()
	local src = workspace:FindFirstChild("Referee_Rigged_v01")
	assert(src, "Importiertes Modell 'Referee_Rigged_v01' nicht gefunden")
	HS.HttpEnabled = true
	local ok, txt = pcall(function() return HS:GetAsync("http://127.0.0.1:8766/export/Referee_Rigged_v01_data.luau") end)
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
	local old = game.ServerStorage:FindFirstChild("CC_Referee")
	if old then old.Name = "CC_Referee_Old" end
	src.Name = "CC_Referee"
	src:PivotTo(CFrame.new())
	src.Parent = game.ServerStorage
	return ("Ringrichter: %d Teile, %d gefaerbt, Hoehe %.2f Studs (Soll %.2f)"):format(parts, colored, h, data.height)
end
