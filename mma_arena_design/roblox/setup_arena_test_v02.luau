-- setup_arena_test_v02.luau (einmal in Studio im Edit-Modus ausfuehren, nach dem Import von export/Arena_Hall_v05_Roblox.fbx)
-- v02: Quelle Arena_Hall_v05 (Dachluecke im Blender-Modell geschlossen, keine Handreparatur), Lichtdurchgang eingebaut (Treppe,
-- Podest/Polster, Wandaufhellung staerker, Raenge-Aufhellung schwaecher), Kaefig-Bezugsattribute fuer den Studio-Test (CC_TestArena),
-- vorhandene Testkopie v04 wird nach ServerStorage verschoben (nicht geloescht).
-- Import: Studio -> Import 3D -> export/Arena_Hall_v05_Roblox.fbx, Einheit Centimeter, Faktor 1, kein Rig (wie Gym/Arena/Fight Night).
-- Legt eine TESTKOPIE an: Workspace.CC_ArenaTest_v04, Kaefigmitte bei TEST_C (weit weg von Gym, Schule, Arenen, Fight Night).
-- Veraendert NICHT: Workspace.CC_Arena, CC_Match, Kameras, Profile, globale Beleuchtung (nur lokale Lichter in der Testkopie).
-- Die Testkopie ist nicht im Spiel registriert (CC_Match kennt nur CC_Arena, CC_FightNight, CC_PvpArena_2..9).
-- Daten: export/Arena_Hall_v05_data.json ueber den lokalen Server 127.0.0.1:8766 (Farben, Instanzen, Licht, Bezugspunkte).
-- Ergebnis: Struktur-Teile (verankert, ohne Mesh-Kollision), Tuer als Modell mit Pivot am Scharnier, Zuschauer/Sitze als Kopien
-- weniger Vorlagen (ServerStorage.CC_ArenaTest_v04_Templates), einfache unsichtbare Kollisionsboxen, lokale Lichter.
local HS = game:GetService("HttpService")
local SS = game:GetService("ServerStorage")
local TEST_C = Vector3.new(1200, 0, -1200)                       -- Hallenboden y = 0, Kaefigmitte
local src = workspace:FindFirstChild("Arena_Hall_v05_Roblox")
assert(src, "Importiertes Modell 'Arena_Hall_v05_Roblox' nicht gefunden - bitte zuerst importieren")
assert(not workspace:FindFirstChild("CC_ArenaTest_v05"), "Testkopie v05 existiert bereits")
local oldCopy = workspace:FindFirstChild("CC_ArenaTest_v04")
if oldCopy then oldCopy.Name = "CC_ArenaTest_v04_Backup_" .. os.time(); oldCopy.Parent = game:GetService("ServerStorage") end
local was = HS.HttpEnabled; HS.HttpEnabled = true
local ok, txt = pcall(function() return HS:GetAsync("http://127.0.0.1:8766/export/Arena_Hall_v05_data.json", true) end)
HS.HttpEnabled = was
assert(ok, "Daten nicht geladen (lokaler Server 8766?): " .. tostring(txt))
local data = HS:JSONDecode(txt)
local ref = data.ref
local S = 1 / 0.28
local function V(t) return Vector3.new(t[1], t[2], t[3]) end

-- Importierte Teile sammeln
local parts = {}
for _, d in ipairs(src:GetDescendants()) do if d:IsA("BasePart") then parts[d.Name] = d end end
local canvas = parts["Canvas__AR_Canvas_WarmGrey"]; assert(canvas, "Matte nicht gefunden")
local doorRef = parts["Tuer__AR_Metal_Anthracite"]; assert(doorRef, "Tuer nicht gefunden")
-- Lage im Import: Matte (Datenraum-Mitte 0,58 m ueber dem Boden) als Bezug; Tuer liegt im SO = Roblox (+x, +z)
local canvasData = Vector3.new(0, 0.58 * S, 0)
local rel = doorRef.Position - canvas.Position
local rotated = rel.X + rel.Z < 0                                -- Import 180 Grad gedreht?
local Rinv = rotated and CFrame.Angles(0, math.pi, 0) or CFrame.new()
local canvasImp = canvas.Position                                -- vor dem Verschieben festhalten (die Matte wird selbst mit verschoben)
local function toWorld(cf) return CFrame.new(TEST_C) * CFrame.new(canvasData) * Rinv * CFrame.new(-canvasImp) * cf end
local function dataToWorld(p) return TEST_C + p end             -- Datenraum: Blender-Ursprung = Hallenmitte am Boden

local model = Instance.new("Model"); model.Name = "CC_ArenaTest_v05"
local fStruct = Instance.new("Folder", model); fStruct.Name = "Structure"
local fCrowd = Instance.new("Folder", model); fCrowd.Name = "Crowd"
local fLights = Instance.new("Folder", model); fLights.Name = "Lights"
local fCol = Instance.new("Folder", model); fCol.Name = "TestCollision"
local door = Instance.new("Model"); door.Name = "CC_TestDoor"; door.Parent = model
local tplFolder = Instance.new("Folder"); tplFolder.Name = "CC_ArenaTest_v05_Templates"

local function matOf(name, info)
	local m = (info and info.mat or ""):lower()
	if info and info.glow then return Enum.Material.Neon end
	if m:find("canvas") then return info.textured and Enum.Material.SmoothPlastic or Enum.Material.Fabric end
	if m:find("strap") or m:find("skirt") or m:find("runner") then return Enum.Material.Fabric end
	if m:find("metal") or m:find("steel") or m:find("railing") or m:find("roof") or m:find("door_steel") or m:find("frame") or m:find("trim") then return Enum.Material.Metal end
	if m:find("concrete") or m:find("tier") or m:find("wall") or m:find("floor") then return Enum.Material.Concrete end
	return Enum.Material.SmoothPlastic
end
local fenceParts, textured, missingTex = {}, {}, {}
for name, p in pairs(parts) do
	local info = data.parts[name]
	local cf = toWorld(p.CFrame)
	p.Anchored = true; p.CanCollide = false; p.CanTouch = false; p.CanQuery = false
	if info then
		p.Color = Color3.fromRGB(info.rgb[1], info.rgb[2], info.rgb[3])
		p.Material = matOf(name, info)
		p.CastShadow = not info.glow
		if info.textured then
			local tex = p:IsA("MeshPart") and p.TextureID or ""
			if tex == "" then
				local sa = p:FindFirstChildWhichIsA("SurfaceAppearance"); if sa then tex = "sa" end
			end
			if tex == "" then table.insert(missingTex, name) else table.insert(textured, name) end
		end
		if info.alpha then table.insert(fenceParts, p) end
		if name:find("Pad") or (info.mat and info.mat:find("Pad")) then p.Reflectance = 0.02 end
	end
	if name:sub(1, 7) == "Crowd__" then
		p.CFrame = Rinv * p.CFrame.Rotation + Vector3.new(0, -500, 0); p.Parent = tplFolder
		p:SetAttribute("CC_Offset", info and info.offset and V(info.offset) or Vector3.zero)
	elseif name:sub(1, 6) == "Tuer__" then
		p.CFrame = cf; p.Parent = door
	else
		p.CFrame = cf; p.Parent = fStruct
	end
end
src:Destroy()
model.Parent = workspace
tplFolder.Parent = SS

-- Gitter: Alpha als echte Durchsicht (SurfaceAppearance, AlphaMode Transparency); ohne Textur halb durchsichtig wie CC_Arena
local fenceMode = {}
for _, p in ipairs(fenceParts) do
	local tex = p:IsA("MeshPart") and p.TextureID or ""
	if tex ~= "" then
		local sa = Instance.new("SurfaceAppearance"); sa.AlphaMode = Enum.AlphaMode.Transparency
		local okSA = pcall(function() sa.ColorMap = tex end)
		if okSA then sa.Parent = p; p.TextureID = ""; table.insert(fenceMode, p.Name .. "=SurfaceAppearance") else sa:Destroy(); table.insert(fenceMode, p.Name .. "=TextureID") end
	else
		p.Transparency = 0.6; table.insert(fenceMode, p.Name .. "=Transparenz 0.6 (keine Textur)")
	end
end

-- Tuer: Pivot an der Scharnierachse (Mattenhoehe), lokale X-Achse zum Schloss; geschlossen = CC_ClosedPivot
local hinge = dataToWorld(V(ref.door_hinge))
local latch = V(ref.door_latch_dir); if rotated then latch = -latch end
door.WorldPivot = CFrame.lookAt(hinge, hinge + Vector3.new(-latch.Z, 0, latch.X)) * CFrame.Angles(0, 0, 0)
door.WorldPivot = CFrame.fromMatrix(hinge, latch, Vector3.yAxis)
door:SetAttribute("CC_ClosedPivot", door.WorldPivot)

-- Zuschauer und Sitze: Kopien der Vorlagen (gleiche Meshes, keine Rigs)
local tpls = {}
for _, t in ipairs(tplFolder:GetChildren()) do tpls[t.Name] = t end
local nCrowd = 0
for _, it in ipairs(data.instances) do
	local t = tpls[it.part]
	if t then
		local c = t:Clone()
		local off = t:GetAttribute("CC_Offset")
		c.Size = Vector3.new(t.Size.X * it.s, t.Size.Y * it.sz, t.Size.Z * it.s)
		c.CFrame = CFrame.new(dataToWorld(V(it.pos))) * CFrame.Angles(0, it.yaw, 0) * CFrame.Angles(it.rx, 0, -it.ry)
			* CFrame.new(off.X * it.s, off.Y * it.sz, off.Z * it.s) * t.CFrame.Rotation
		c.Anchored = true; c.CanCollide = false; c.CanTouch = false; c.CanQuery = false; c.CastShadow = false
		c.Parent = fCrowd; nCrowd += 1
	end
end

-- Kollision: einfache unsichtbare Boxen (Boden, Podest, Kaefigwaende + Tuer, Treppe, Brustwehr, Raenge, Wand)
local function col(name, cf, size)
	local p = Instance.new("Part"); p.Name = name; p.Anchored = true; p.CanCollide = true; p.CanQuery = true; p.CanTouch = false
	p.Transparency = 1; p.CastShadow = false; p.Size = size; p.CFrame = cf; p.Parent = fCol; return p
end
local C0 = TEST_C
local function sideDir(k) local a = math.rad(90 - 45 * k); return Vector3.new(math.cos(a), 0, -math.sin(a)) end   -- Blender (cos, sin) -> Roblox (x, -y)
local function sideCF(k, apothem, y) local n = sideDir(k); return CFrame.lookAt(C0 + n * apothem + Vector3.new(0, y, 0), C0 + Vector3.new(0, y, 0)) end
local T225 = math.tan(math.rad(22.5))
col("COL_Floor", CFrame.new(C0 + Vector3.new(0, -0.5, 0)), Vector3.new(160, 1, 160))
local PA, A, CY = ref.platform_apothem, ref.cage_apothem, ref.canvas_y
for i = 0, 3 do col("COL_Platform_" .. i, CFrame.new(C0 + Vector3.new(0, CY / 2, 0)) * CFrame.Angles(0, math.rad(45 * i), 0), Vector3.new(2 * PA, CY, 2 * PA * T225)) end
local H = 2.2 * S
for k = 0, 7 do
	local L = 2 * A * T225
	if k == 3 then                                                   -- SO: Tuer-Oeffnung frei, Tuer als eigene Box
		local w = ref.door_clear_w; local seg = (L - w) / 2
		for s = -1, 1, 2 do col("COL_Cage_" .. (k + 1) .. (s < 0 and "_L" or "_R"), sideCF(k, A + 0.6, CY + H / 2) * CFrame.new(s * (w / 2 + seg / 2), 0, 0), Vector3.new(seg + 0.2, H, 1.2)) end
		col("COL_TestDoor", sideCF(k, A + 0.6, CY + H / 2), Vector3.new(w, H, 1.2))
	else
		col("COL_Cage_" .. (k + 1), sideCF(k, A + 0.6, CY + H / 2), Vector3.new(L + 0.4, H, 1.2))
	end
end
local st = ref.stairs                                               -- zwei Auftritte vor der Tuer (SO)
for i = 1, 2 do
	local top = CY - st.rise * i
	col("COL_Stair_" .. i, sideCF(3, PA + st.run * (i - 0.5), top / 2), Vector3.new(st.width, top, st.run))
end
local BA = ref.barrier_apothem
for k = 0, 7 do
	local L = 2 * BA * T225
	if k == 3 then
		local seg = (L - 2 * ref.entry_half) / 2
		for s = -1, 1, 2 do col("COL_Barrier_4" .. (s < 0 and "L" or "R"), sideCF(k, BA + 0.3, 1.05 * S / 2) * CFrame.new(s * (ref.entry_half + seg / 2), 0, 0), Vector3.new(seg, 1.05 * S, 0.6)) end
	else col("COL_Barrier_" .. (k + 1), sideCF(k, BA + 0.3, 1.05 * S / 2), Vector3.new(L, 1.05 * S, 0.6)) end
end
local rows = ref.rows
for k = 0, 7 do
	for r = 0, rows.count - 1 do
		local a0 = rows.row0 + r * rows.depth; local top = rows.z0 + r * rows.rise
		local L = 2 * (a0 + rows.depth / 2) * T225 - 1.5 * S
		if k == 3 then
			local seg = (L - 2 * ref.entry_half) / 2
			for s = -1, 1, 2 do col("COL_Tier_4_" .. r .. (s < 0 and "L" or "R"), sideCF(k, a0 + rows.depth / 2, top / 2) * CFrame.new(s * (ref.entry_half + seg / 2), 0, 0), Vector3.new(seg, top, rows.depth)) end
		else col("COL_Tier_" .. (k + 1) .. "_" .. r, sideCF(k, a0 + rows.depth / 2, top / 2), Vector3.new(L, top, rows.depth)) end
	end
	col("COL_Wall_" .. (k + 1), sideCF(k, ref.hall_apothem + 0.6, 30), Vector3.new(2 * ref.hall_apothem * T225 + 2, 60, 1.2))
end

-- Lokale Lichter nach der Blender-Lichtplanung (keine globale Lighting-Aenderung)
local function anchor(name, pos, dir)
	local p = Instance.new("Part"); p.Name = name; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
	p.Transparency = 1; p.Size = Vector3.new(0.4, 0.4, 0.4); p.CastShadow = false
	p.CFrame = dir and CFrame.lookAt(pos, pos + dir) or CFrame.new(pos); p.Parent = fLights; return p
end
local nl = 0
for _, l in ipairs(data.lights) do
	local pos, dir = dataToWorld(V(l.pos)), V(l.dir); if rotated then dir = Vector3.new(-dir.X, dir.Y, -dir.Z) end
	local c = Color3.new(l.rgb[1], l.rgb[2], l.rgb[3]); local n = l.name
	local a = anchor(n, pos, dir); local li
	if n:find("Spot_") then li = Instance.new("SpotLight"); li.Brightness = 2.0; li.Range = 60; li.Angle = 48; li.Shadows = true
	elseif n:find("Key_Soft") then li = Instance.new("SurfaceLight"); li.Brightness = 0.9; li.Range = 60; li.Angle = 80; li.Shadows = false; a.Size = Vector3.new(20, 0.2, 20)
	elseif n:find("Side_") then li = Instance.new("SpotLight"); li.Brightness = 1.1; li.Range = 40; li.Angle = 50; li.Shadows = false
	elseif n:find("Fill_Cool") then li = Instance.new("SpotLight"); li.Brightness = 0.32; li.Range = 55; li.Angle = 90; li.Shadows = false
	elseif n:find("WallWash") then li = Instance.new("SpotLight"); li.Brightness = 1.6; li.Range = 45; li.Angle = 80; li.Shadows = false
	elseif n:find("Accent_") then li = Instance.new("SpotLight"); li.Brightness = 2.5; li.Range = 35; li.Angle = 70; li.Shadows = false
	elseif n:find("Sign_Wash") then li = Instance.new("SpotLight"); li.Brightness = 1.2; li.Range = 35; li.Angle = 50; li.Shadows = false end
	if li then li.Face = Enum.NormalId.Front; li.Color = c; li.Parent = a; nl += 1 else a:Destroy() end
end
if fLights:FindFirstChild("LT_Key_Soft") then local k = fLights.LT_Key_Soft; k.CFrame = CFrame.new(k.Position); k:FindFirstChildOfClass("SurfaceLight").Face = Enum.NormalId.Bottom end

-- gezielte weiche Aufhellung (Lichtdurchgang 2026-10-24): Treppe, Podest und schwarze Polster, ohne die Matte heller zu machen
local warm = Color3.fromRGB(255, 232, 205)
local function spot(name, pos, target, br, range, angle)
	local a = anchor(name, pos, target - pos); local l = Instance.new("SpotLight"); l.Face = Enum.NormalId.Front; l.Brightness = br; l.Range = range; l.Angle = angle; l.Color = warm; l.Shadows = false; l.Parent = a; nl += 1
end
local seN = Vector3.new(0.7071, 0, 0.7071); if rotated then seN = Vector3.new(0.7071, 0, 0.7071) end
spot("LT_Stairs", TEST_C + seN * 8.5 * S + Vector3.new(0, 5.5 * S, 0), TEST_C + seN * 5.7 * S + Vector3.new(0, 0.3 * S, 0), 1.6, 30, 55)
for k = 0, 3 do
	local a = math.rad(45 + 90 * k); local d = Vector3.new(math.cos(a), 0, -math.sin(a))
	spot("LT_Podium_" .. (k + 1), TEST_C + d * 8.6 * S + Vector3.new(0, 1.3 * S, 0), TEST_C + d * 5.0 * S + Vector3.new(0, 0.9 * S, 0), 0.7, 32, 70)
end
model:SetAttribute("CC_CageCenter", TEST_C + Vector3.new(0, CY, 0)); model:SetAttribute("CC_CageRadius", A)   -- nur fuer CC_TestArena = "test_v04" (Studio)
model:SetAttribute("CC_TestArena", true)
model:SetAttribute("CC_CageCenterTest", TEST_C + Vector3.new(0, CY, 0))
model:SetAttribute("CC_CageRadiusTest", A)
local nStruct = #fStruct:GetChildren()
return ("Testkopie gebaut: %d Struktur-Teile, Tuer %d Teile, %d Zuschauer/Sitze, %d Kollisionsboxen, %d Lichter, Import gedreht=%s | texturiert: %d, Textur fehlt: %s | Gitter: %s")
	:format(nStruct, #door:GetChildren(), nCrowd, #fCol:GetChildren(), nl, tostring(rotated), #textured, table.concat(missingTex, ","), table.concat(fenceMode, "; "))
