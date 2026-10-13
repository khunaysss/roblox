-- setup_fight_night_v01.luau (einmal in Studio im Edit-Modus ausfuehren, nach dem Import von export/Fight_Night_v01_Roblox.fbx)
-- Import: Studio -> Import 3D -> export/Fight_Night_v01_Roblox.fbx, Einheit Centimeter, Faktor 1, kein Rig (wie Gym/Arena).
-- Das Skript sucht das importierte Modell ("Fight_Night_v01_Roblox"), setzt es weit neben Arena und Gym
-- (Kaefigmitte bei FN_REF, Hallenboden auf y = 0), dreht es bei Bedarf (der FBX-Import dreht manche Modelle um 180 Grad um Y),
-- faerbt nach export/Fight_Night_v01_data.luau, verankert alles, schaltet die Mesh-Kollision aus und baut stattdessen
-- unsichtbare Kollisionsboxen (CC_FightNight.FN_Collision). Gitter halb durchsichtig wie in CC_Arena.
-- Bezugspunkte: Attribute am Modell (CC_CageCenter, CC_CanvasY) und Teile unter CC_FightNight.FN_Spots.
-- Ergebnis: Workspace.CC_FightNight. Vorhandene Maps werden nicht veraendert.
local HS = game:GetService("HttpService")
local src = workspace:FindFirstChild("Fight_Night_v01_Roblox") or workspace:FindFirstChild("Fight_Night_v01_Roblox", true)
assert(src, "Importiertes Modell 'Fight_Night_v01_Roblox' nicht gefunden – bitte zuerst importieren")
HS.HttpEnabled = true
local ok, txt = pcall(function() return HS:GetAsync("http://127.0.0.1:8766/export/Fight_Night_v01_data.luau") end)
HS.HttpEnabled = false
assert(ok, "Daten nicht geladen (lokaler Server 8766?): " .. tostring(txt))
local data = loadstring(txt)()
local S = 1 / 0.28
local FN_REF = Vector3.new(0, data.ref.world_m[3] * S, -700)     -- Kaefigmitte auf Kampfflaeche; Hallenboden y = 0

local model = Instance.new("Model"); model.Name = "CC_FightNight"
local parts, colored = {}, 0
for _, d in ipairs(src:GetDescendants()) do if d:IsA("BasePart") then table.insert(parts, d) end end
for _, p in ipairs(parts) do p.Parent = model end
src:Destroy()
-- Lage: Kampfflaeche (Bezugsmesh) finden und Modell so verschieben, dass ihre Oberkante-Mitte auf FN_REF liegt
local canvas
for _, p in ipairs(parts) do if p.Name:find("Platform") and p.Name:find("Canvas") then canvas = p end end
local cf, size = model:GetBoundingBox()
local refNow = canvas and (canvas.Position + Vector3.new(0, canvas.Size.Y / 2, 0)) or (cf.Position)
model:PivotTo(model:GetPivot() + (FN_REF - refNow))
-- Drehung pruefen: Walkout/Backstage liegt in Blender bei -y (weit), in Roblox also bei +z (Achsen x, z, -y)
cf, size = model:GetBoundingBox()
local farPlus = (cf.Position.Z + size.Z / 2) - FN_REF.Z
local farMinus = FN_REF.Z - (cf.Position.Z - size.Z / 2)
local rotated = farMinus > farPlus + 5
if rotated then model:PivotTo(CFrame.new(FN_REF) * CFrame.Angles(0, math.pi, 0) * (CFrame.new(FN_REF):Inverse() * model:GetPivot())) end
-- Farben, Materialien
for _, p in ipairs(parts) do
	local c = data.colors[p.Name]
	p.Anchored = true; p.CanCollide = false; p.CanTouch = false; p.CanQuery = false
	if c then
		p.Color = Color3.fromRGB(c.rgb[1], c.rgb[2], c.rgb[3]); colored += 1
		p.Material = c.glow and Enum.Material.Neon or Enum.Material.SmoothPlastic
		if c.alpha and c.alpha < 0.99 then p.Transparency = math.clamp(1 - c.alpha, 0, 0.9) end
		if c.group == "Crowd_Spectators_Near" or c.group == "Crowd_Silhouettes_Far" then p.CastShadow = false end
	end
	if p.Name:find("Fence") then p.Transparency = math.max(p.Transparency, 0.35) end
	if p.Name:find("Platform") or p.Name:find("Canvas") then p.CanQuery = true end
end
-- Kollision: unsichtbare Boxen
local col = Instance.new("Folder"); col.Name = "FN_Collision"; col.Parent = model
local function m3(r) return r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9] end
for _, c in ipairs(data.collision) do
	local b = Instance.new("Part"); b.Name = "COL_" .. c.name
	b.Size = Vector3.new(math.max(c.size[1], 0.2), math.max(c.size[2], 0.2), math.max(c.size[3], 0.2))
	local pos = FN_REF + Vector3.new(c.pos[1], c.pos[2], c.pos[3])
	local cfr = CFrame.new(pos.X, pos.Y, pos.Z, m3(c.rot))
	if rotated then cfr = CFrame.new(FN_REF) * CFrame.Angles(0, math.pi, 0) * (CFrame.new(FN_REF):Inverse() * cfr) end
	b.CFrame = cfr
	b.Transparency = 1; b.Anchored = true; b.CanCollide = true; b.CanQuery = true; b.CanTouch = false
	b.Parent = col
end
-- Bezugspunkte
local spots = Instance.new("Folder"); spots.Name = "FN_Spots"; spots.Parent = model
for _, s in ipairs(data.spots) do
	local m = Instance.new("Part"); m.Name = s.name; m.Size = Vector3.new(1, 1, 1); m.Transparency = 1; m.Anchored = true
	m.CanCollide = false; m.CanQuery = false; m.CanTouch = false
	local pos = FN_REF + Vector3.new(s.pos[1], s.pos[2], s.pos[3])
	if rotated then pos = FN_REF + (CFrame.Angles(0, math.pi, 0) * (pos - FN_REF)) end
	m.Position = pos; m.Parent = spots
end
model:SetAttribute("CC_CageCenter", FN_REF)
model:SetAttribute("CC_CanvasY", FN_REF.Y)
model.Parent = workspace
return ("Fight Night eingerichtet: %d Meshes (%d gefaerbt), %d Kollisionsboxen, %d Bezugspunkte, gedreht: %s, Kaefigmitte %s")
	:format(#parts, colored, #data.collision, #data.spots, tostring(rotated), tostring(FN_REF))
