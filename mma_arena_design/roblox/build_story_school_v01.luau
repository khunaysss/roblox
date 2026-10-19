-- build_story_school_v01.luau  (ModuleScript-Inhalt; Aufruf: require(ms)(abschnitt) fuer "ground", "street", "fence", "yard", "school", "background", "trees")
-- Schulausschnitt fuer den Story-Einstieg (Szene 1-6). Workspace.CC_StorySchool, Mitte (Tor) bei ORIGIN.
-- Massstab: Kaempfer 6,45 Studs = 1,8 m -> 1 m = 3,57 Studs. Lokale Achsen: +Z = vom Tor zum Schulgebaeude, +X = rechts, Boden y = 0.
-- Nur fuer die Kameras sichtbare Bereiche werden ausgearbeitet; dahinter schliessen Haeuser, Wohnbloecke und Baeume den Horizont.
local ORIGIN = CFrame.new(-600, 0, 600)
local root = workspace:FindFirstChild("CC_StorySchool")
if not root then root = Instance.new("Model"); root.Name = "CC_StorySchool"; root.Parent = workspace end
root:SetAttribute("CC_Origin", ORIGIN.Position)

local function folder(name)
	local f = root:FindFirstChild(name)
	if f then f:Destroy() end
	f = Instance.new("Model"); f.Name = name
	return f
end
local cur
local function P(name, size, cf, color, mat, opts)
	local p = Instance.new((opts and opts.shape) and "Part" or (opts and opts.wedge and "WedgePart") or "Part")
	if opts and opts.shape then p.Shape = opts.shape end
	p.Name = name; p.Size = size; p.CFrame = ORIGIN * cf; p.Color = color; p.Material = mat or Enum.Material.SmoothPlastic
	p.Anchored = true; p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
	p.CastShadow = not (opts and opts.noShadow) and (size.X * size.Y * size.Z > 6)
	if opts and opts.trans then p.Transparency = opts.trans end
	if opts and opts.refl then p.Reflectance = opts.refl end
	p.CanCollide = not (opts and opts.noCollide)
	p.Parent = cur
	return p
end
local function C(r, g, b) return Color3.fromRGB(r, g, b) end
local M = Enum.Material
local V, CF = Vector3.new, CFrame.new

local S = {}

-- ---------- Boden: grosse Grundflaeche, damit keine Kartenkante sichtbar ist ----------
function S.ground()
	cur = folder("Ground")
	P("BaseGrass", V(1400, 2, 1400), CF(0, -1.05, 60), C(92, 98, 62), M.Grass)
	return cur
end

-- ---------- Strasse und Gehwege (z -30 .. -112) ----------
function S.street()
	cur = folder("Street")
	local ASPH, WALK, CURB = C(58, 60, 64), C(150, 147, 140), C(118, 116, 112)
	P("Asphalt", V(560, 1, 40), CF(0, -0.5, -75), ASPH, M.Asphalt)
	for x = -270, 270, 24 do P("LaneMark", V(10, 0.08, 0.6), CF(x, 0.04, -75), C(214, 210, 196), M.SmoothPlastic, { noShadow = true }) end
	for _, z in ipairs({ -55, -95 }) do P("Curb", V(560, 0.9, 1.0), CF(0, 0.0, z + (z == -55 and 0.5 or -0.5)), CURB, M.Concrete) end
	-- Gehweg Nord (Schulseite) mit Plattenfugen, Gehweg Sued (Haeuserseite)
	P("WalkN", V(560, 0.4, 24), CF(0, 0.2, -43), WALK, M.Pavement)
	P("WalkS", V(560, 0.4, 16), CF(0, 0.2, -103.5), WALK, M.Pavement)
	for x = -276, 276, 8 do
		P("JointN", V(0.18, 0.02, 24), CF(x, 0.41, -43), C(120, 118, 112), M.SmoothPlastic, { noShadow = true, noCollide = true })
	end
	for z = -53, -33, 8 do P("JointNz", V(560, 0.02, 0.18), CF(0, 0.41, z), C(120, 118, 112), M.SmoothPlastic, { noShadow = true, noCollide = true }) end
	-- Strassenlaternen auf dem Gehweg
	for _, x in ipairs({ -120, -40, 60, 140 }) do
		P("LampPole", V(0.8, 22, 0.8), CF(x, 11, -53), C(48, 50, 54), M.Metal)
		P("LampArm", V(0.5, 0.5, 6), CF(x, 21.8, -56), C(48, 50, 54), M.Metal)
		local head = P("LampHead", V(2.2, 0.7, 3.2), CF(x, 21.4, -59), C(40, 42, 46), M.Metal)
		local l = Instance.new("SpotLight"); l.Face = Enum.NormalId.Bottom; l.Angle = 100; l.Range = 30; l.Brightness = 0.6
		l.Color = C(255, 226, 180); l.Enabled = false; l.Name = "EveningLight"; l.Parent = head
	end
	-- Zebrastreifen vor dem Schultor
	for i = -4, 4 do P("Zebra", V(2.2, 0.08, 34), CF(i * 4, 0.04, -75), C(222, 220, 210), M.SmoothPlastic, { noShadow = true }) end
	return cur
end

-- ---------- Grundstuecksgrenze: Ziegelpfeiler, Sockelmauer, Metallzaun, offenes Tor ----------
function S.fence()
	cur = folder("Fence")
	local BRICK, CAP, IRON = C(128, 74, 58), C(170, 164, 154), C(36, 40, 46)
	local function bay(x0, x1, z, alongX)
		local len = math.abs(x1 - x0); local mid = (x0 + x1) / 2
		local function at(t, y) if alongX then return CF(t, y, z) else return CF(z, y, t) end end
		local sz = function(a, b, c) if alongX then return V(a, b, c) else return V(c, b, a) end end
		P("Wall", sz(len, 2.4, 1.6), at(mid, 1.6), BRICK, M.Brick)
		P("WallCap", sz(len, 0.4, 2.0), at(mid, 3.0), CAP, M.Concrete)
		P("RailLow", sz(len, 0.35, 0.35), at(mid, 3.8), IRON, M.Metal)
		P("RailTop", sz(len, 0.35, 0.35), at(mid, 9.6), IRON, M.Metal)
		local n = math.floor(len / 2.4)   -- Staebe alle 2,4 Studs (weniger Teile)
		for i = 1, n - 1 do
			local t = math.min(x0, x1) + i * len / n
			P("Bar", sz(0.28, 6.4, 0.28), at(t, 6.7), IRON, M.Metal, { noShadow = true })
		end
	end
	local function pillar(x, z, big)
		local w = big and 3.6 or 2.8; local h = big and 12 or 10.4
		P("Pillar", V(w, h, w), CF(x, h / 2, z), BRICK, M.Brick)
		P("PillarCap", V(w + 0.8, 0.8, w + 0.8), CF(x, h + 0.4, z), CAP, M.Concrete)
		P("PillarCap2", V(w * 0.6, 0.6, w * 0.6), CF(x, h + 1.1, z), CAP, M.Concrete)
	end
	-- Front (z = -30): Tor in der Mitte (x -12..12)
	local xs = { -204, -180, -156, -132, -108, -84, -60, -36, -12 }
	for i = 1, #xs - 1 do bay(xs[i], xs[i + 1], -30, true) end
	for i = 1, #xs - 1 do bay(-xs[i], -xs[i + 1], -30, true) end
	for _, x in ipairs(xs) do pillar(x, -30, x == -12); pillar(-x, -30, x == -12) end
	-- Seiten (x = +-204) bis zum Gebaeude
	for z = -30, 66, 24 do
		bay(z, math.min(z + 24, 84), -204, false); bay(z, math.min(z + 24, 84), 204, false)
		pillar(-204, z + 24, false); pillar(204, z + 24, false)
	end
	-- Torfluegel, nach innen geoeffnet
	for _, side in ipairs({ -1, 1 }) do
		local hinge = CF(side * 10.2, 0, -30)
		local leaf = hinge * CFrame.Angles(0, math.rad(side * -72), 0)
		local function lp(name, size, off) local p = P(name, size, CF(), IRON, M.Metal); p.CFrame = ORIGIN * leaf * CF(-side * off.X, off.Y, off.Z) end
		lp("GateFrameB", V(10, 0.4, 0.4), V(5, 1.2, 0)); lp("GateFrameT", V(10, 0.4, 0.4), V(5, 9.4, 0))
		lp("GateFrameO", V(0.4, 8.6, 0.4), V(9.8, 5.3, 0)); lp("GateFrameI", V(0.4, 8.6, 0.4), V(0.3, 5.3, 0))
		for i = 1, 6 do lp("GateBar", V(0.26, 8.2, 0.26), V(i * 1.4, 5.3, 0)) end
	end
	-- Schulschild am rechten Torpfeiler
	local sign = P("SchoolSign", V(0.3, 2.6, 6.0), CF(14.2, 7.4, -31.9), C(32, 36, 42), M.Metal)
	sign.CFrame = ORIGIN * CF(15.6, 7.4, -32.0) * CFrame.Angles(0, math.rad(90), 0)
	local sg = Instance.new("SurfaceGui"); sg.Face = Enum.NormalId.Right; sg.CanvasSize = Vector2.new(600, 260); sg.LightInfluence = 1; sg.Parent = sign
	local t = Instance.new("TextLabel"); t.Size = UDim2.fromScale(1, 1); t.BackgroundTransparency = 1; t.TextColor3 = C(232, 230, 222)
	t.Font = Enum.Font.GothamBold; t.TextScaled = true; t.Text = "NORTHPARK\nHIGH SCHOOL"; t.Parent = sg
	local pad = Instance.new("UIPadding"); pad.PaddingLeft = UDim.new(0.08, 0); pad.PaddingRight = UDim.new(0.08, 0); pad.PaddingTop = UDim.new(0.14, 0); pad.PaddingBottom = UDim.new(0.14, 0); pad.Parent = t
	return cur
end

-- ---------- Schulhof: Pflaster, Hauptweg, Rasenbeete mit Kanten, Baenke, Muelleimer, Fahrradstaender ----------
function S.yard()
	cur = folder("Yard")
	local PAVE, PATH, EDGE, LAWN = C(168, 162, 152), C(190, 184, 172), C(130, 126, 118), C(88, 104, 58)
	P("Paving", V(408, 0.4, 116), CF(0, 0.2, 26), PAVE, M.Pavement)
	P("MainPath", V(26, 0.06, 100), CF(0, 0.43, 22), PATH, M.Pavement, { noShadow = true })
	for z = -26, 70, 6 do P("PathJoint", V(26, 0.02, 0.16), CF(0, 0.47, z), C(140, 136, 128), M.SmoothPlastic, { noShadow = true, noCollide = true }) end
	for _, x in ipairs({ -13, 13 }) do P("PathEdge", V(0.6, 0.12, 100), CF(x, 0.46, 22), EDGE, M.Concrete, { noShadow = true }) end
	-- Rasenbeete links/rechts des Weges
	for _, sx in ipairs({ -1, 1 }) do
		local cx = sx * 62
		P("Lawn", V(76, 0.6, 52), CF(cx, 0.5, 22), LAWN, M.Grass)
		P("LawnEdgeA", V(77.2, 0.9, 0.6), CF(cx, 0.55, -4.3), EDGE, M.Concrete)
		P("LawnEdgeB", V(77.2, 0.9, 0.6), CF(cx, 0.55, 48.3), EDGE, M.Concrete)
		P("LawnEdgeC", V(0.6, 0.9, 52), CF(cx - 38.3, 0.55, 22), EDGE, M.Concrete)
		P("LawnEdgeD", V(0.6, 0.9, 52), CF(cx + 38.3, 0.55, 22), EDGE, M.Concrete)
	end
	-- Baenke am Weg (Sitz aus Holzlatten, Metallfuesse)
	local WOOD, IRONC = C(140, 98, 62), C(46, 48, 52)
	local function bench(x, z, yaw)
		local base = CF(x, 0, z) * CFrame.Angles(0, math.rad(yaw), 0)
		local function bp(name, size, off, col, mat) local p = P(name, size, CF(), col, mat); p.CFrame = ORIGIN * base * CF(off) end
		for i = 0, 2 do bp("Slat", V(6.4, 0.25, 0.55), V(0, 1.75, -0.7 + i * 0.6), WOOD, M.Wood) end
		for i = 0, 1 do bp("BackSlat", V(6.4, 0.5, 0.22), V(0, 2.6 + i * 0.7, 0.95), WOOD, M.Wood) end
		for _, lx in ipairs({ -2.7, 2.7 }) do
			bp("Leg", V(0.3, 1.7, 1.8), V(lx, 0.85, -0.1), IRONC, M.Metal); bp("BackLeg", V(0.3, 2.2, 0.3), V(lx, 2.6, 1.05), IRONC, M.Metal)
		end
	end
	bench(-17.5, 6, 90); bench(-17.5, 34, 90); bench(17.5, 20, -90)
	-- Muelleimer neben den Baenken
	local function bin(x, z)
		P("Bin", V(1.8, 3.0, 1.8), CF(x, 1.9, z), C(62, 78, 64), M.Metal, { shape = Enum.PartType.Cylinder }).CFrame = ORIGIN * CF(x, 1.9, z) * CFrame.Angles(0, 0, math.rad(90))
		P("BinRim", V(0.3, 2.0, 2.0), CF(x, 3.4, z), C(44, 52, 46), M.Metal, { shape = Enum.PartType.Cylinder }).CFrame = ORIGIN * CF(x, 3.45, z) * CFrame.Angles(0, 0, math.rad(90))
		P("BinPost", V(0.4, 1.6, 0.4), CF(x, 0.8, z + 1.2), C(46, 48, 52), M.Metal)
	end
	bin(-17.5, 13); bin(17.5, 27)
	-- Fahrradstaender rechts hinter dem Tor (Buegel)
	for i = 0, 5 do
		local x = 40 + i * 4
		P("RackL", V(0.3, 3.0, 0.3), CF(x, 1.9, -20), C(150, 152, 156), M.Metal)
		P("RackR", V(0.3, 3.0, 0.3), CF(x, 1.9, -17), C(150, 152, 156), M.Metal)
		P("RackT", V(0.3, 0.3, 3.3), CF(x, 3.4, -18.5), C(150, 152, 156), M.Metal)
	end
	P("RackPad", V(26, 0.08, 7), CF(50, 0.44, -18.5), C(120, 118, 112), M.Concrete, { noShadow = true })
	-- zwei Fahrraeder (Rahmen, Raeder als duenne Zylinder) im Staender
	local function bike(x, z, col)
		local function wheel(dz) local w = P("Wheel", V(0.25, 2.6, 2.6), CF(), C(30, 30, 32), M.Rubber, { shape = Enum.PartType.Cylinder }); w.CFrame = ORIGIN * CF(x, 1.75, z + dz) end
		wheel(-1.7); wheel(1.7)
		local f1 = P("Frame", V(0.22, 0.22, 3.4), CF(x, 2.6, z), col, M.Metal); f1.CFrame = ORIGIN * CF(x, 2.55, z) * CFrame.Angles(math.rad(-12), 0, 0)
		P("Seat", V(0.5, 0.25, 0.9), CF(x, 3.45, z + 1.0), C(28, 28, 30), M.Fabric)
		P("Bar", V(1.6, 0.18, 0.18), CF(x, 3.5, z - 1.4), C(40, 40, 42), M.Metal)
	end
	bike(44, -18.5, C(42, 92, 140)); bike(56, -18.5, C(150, 50, 44))
	-- Laternen im Hof
	for _, z in ipairs({ 0, 40 }) do for _, x in ipairs({ -16, 16 }) do
		P("YardLamp", V(0.5, 11, 0.5), CF(x, 5.9, z + 10), C(46, 48, 52), M.Metal)
		P("YardLampHead", V(1.4, 1.6, 1.4), CF(x, 12.0, z + 10), C(230, 226, 214), M.SmoothPlastic)
	end end
	return cur
end

-- ---------- Schulgebaeude: drei Geschosse, Fensterraster mit Tiefe, Eingangsportal, Fluegel mit Tiefe ----------
function S.school()
	cur = folder("School")
	local WALLC, PLINTH, BAND, FRAME, GLASS, INNER = C(206, 196, 178), C(96, 94, 92), C(178, 170, 156), C(58, 62, 68), C(96, 116, 128), C(46, 50, 56)
	local Z0, W, DEPTH, FLOOR = 84, 300, 50, 13
	local H = FLOOR * 3 + 4
	-- Baukoerper (geschlossen, damit keine leere Rueckseite sichtbar ist)
	P("Body", V(W, H, DEPTH), CF(0, H / 2, Z0 + DEPTH / 2), WALLC, M.Plaster)
	P("Plinth", V(W + 0.6, 3, DEPTH + 0.6), CF(0, 1.5, Z0 + DEPTH / 2), PLINTH, M.Concrete)
	for f = 1, 3 do P("FloorBand", V(W + 1.2, 0.8, DEPTH + 1.2), CF(0, f * FLOOR + 1, Z0 + DEPTH / 2), BAND, M.Concrete) end
	P("Parapet", V(W + 1.6, 1.6, DEPTH + 1.6), CF(0, H + 0.8, Z0 + DEPTH / 2), C(150, 144, 134), M.Concrete)
	P("RoofUnit", V(14, 5, 10), CF(-60, H + 2.5, Z0 + 30), C(140, 142, 144), M.Metal)
	P("RoofUnit2", V(10, 4, 8), CF(70, H + 2, Z0 + 26), C(140, 142, 144), M.Metal)
	-- Fenster: Laibung (dunkle Innenflaeche 1,6 tief), Glas, Rahmen, Sprosse, Fensterbank
	local function window(cfBase, w, h)
		local function wp(name, size, off, col, mat, o) local p = P(name, size, CF(), col, mat, o); p.CFrame = ORIGIN * cfBase * CF(off) end
		-- lokal +Z = aus der Wand heraus; Tiefe entsteht durch die vorstehenden Lisenen links/rechts
		wp("Glass", V(w - 0.2, h - 0.2, 0.1), V(0, 0, 0.06), GLASS, M.Glass, { refl = 0.18, noShadow = true })
		wp("FrameT", V(w + 0.5, 0.45, 0.5), V(0, h / 2, 0.25), FRAME, M.Metal); wp("FrameB", V(w + 0.5, 0.45, 0.5), V(0, -h / 2, 0.25), FRAME, M.Metal)
		wp("FrameL", V(0.45, h, 0.5), V(-w / 2, 0, 0.25), FRAME, M.Metal); wp("FrameR", V(0.45, h, 0.5), V(w / 2, 0, 0.25), FRAME, M.Metal)
		wp("Mullion", V(0.3, h, 0.3), V(0, 0, 0.2), FRAME, M.Metal, { noShadow = true })
		wp("Sill", V(w + 1.0, 0.35, 1.0), V(0, -h / 2 - 0.35, 0.55), BAND, M.Concrete)
	end
	-- Laibungen: Ausschnitte durch vorgesetzte Pfeiler simulieren -> Fassade als Lisenen + Bruestungen
	for f = 0, 2 do
		local yc = f * FLOOR + 3 + 6.6
		for x = -144, 144, 12 do
			if math.abs(x) > 26 then
				-- Fensteroeffnung: die Wand liegt dahinter (Body), vorn Lisenen/Bruestung = Tiefe
				window(CF(x, yc, Z0 - 0.01) * CFrame.Angles(0, math.rad(180), 0), 7.2, 7.6)
			end
		end
	end
	-- Lisenen (senkrechte Pfeiler) zwischen den Fensterachsen geben der Fassade Tiefe
	for x = -150, 138, 12 do
		if math.abs(x + 6) > 27 then P("Pilaster", V(1.6, H - 3, 1.2), CF(x + 6, (H + 3) / 2, Z0 - 0.6), C(196, 186, 168), M.Plaster) end
	end
	-- Eingangsbau in der Mitte: vorgezogen, hoeher, verglaste Tueren, Vordach, Stufen
	P("EntranceBlock", V(52, H + 6, 10), CF(0, (H + 6) / 2, Z0 - 5), C(186, 176, 160), M.Plaster)
	P("EntranceTop", V(53.6, 1.6, 11.6), CF(0, H + 6.8, Z0 - 5), C(150, 144, 134), M.Concrete)
	P("DoorRecess", V(30, 13, 0.2), CF(0, 9.5, Z0 - 10.2), INNER, M.SmoothPlastic)
	for i = -1.5, 1.5 do
		local x = i * 7
		P("DoorGlass", V(6.2, 11, 0.2), CF(x, 8.8, Z0 - 10.6), C(110, 130, 140), M.Glass, { trans = 0.3, refl = 0.15 })
		P("DoorFrame", V(0.5, 11.4, 0.5), CF(x - 3.3, 8.8, Z0 - 10.7), FRAME, M.Metal)
		P("DoorHandle", V(0.25, 2.2, 0.25), CF(x + 2.2, 8.0, Z0 - 11.0), C(180, 182, 186), M.Metal)
	end
	P("DoorFrameR", V(0.5, 11.4, 0.5), CF(14.0, 8.8, Z0 - 10.7), FRAME, M.Metal)
	P("DoorLintel", V(30, 0.8, 0.8), CF(0, 14.6, Z0 - 10.7), FRAME, M.Metal)
	P("Canopy", V(40, 1.2, 14), CF(0, 17.2, Z0 - 16), C(64, 68, 74), M.Metal)
	for _, x in ipairs({ -17, 17 }) do P("CanopyPost", V(1.0, 14, 1.0), CF(x, 10, Z0 - 22), C(64, 68, 74), M.Metal) end
	for s = 0, 2 do P("Step", V(36, 1.0, 3), CF(0, 3.5 - s * 1.0 - 0.5 + 0.0, Z0 - 11.5 - s * 3), C(150, 146, 138), M.Concrete) end
	-- Fenster im Eingangsbau (Treppenhaus, hohe Glasflaeche)
	for f = 1, 2 do window(CF(0, f * FLOOR + 3 + 7, Z0 - 10.01) * CFrame.Angles(0, math.rad(180), 0), 30, 9) end
	-- Schriftzug ueber dem Vordach
	local plate = P("NamePlate", V(34, 3.2, 0.4), CF(0, 21.6, Z0 - 10.4), C(42, 46, 52), M.Metal)
	local sg = Instance.new("SurfaceGui"); sg.Face = Enum.NormalId.Front; sg.CanvasSize = Vector2.new(1200, 112); sg.LightInfluence = 1; sg.Parent = plate
	local t = Instance.new("TextLabel"); t.Size = UDim2.fromScale(1, 1); t.BackgroundTransparency = 1; t.TextColor3 = C(236, 232, 222)
	t.Font = Enum.Font.GothamBold; t.TextScaled = true; t.Text = "NORTHPARK HIGH SCHOOL"; t.Parent = sg
	-- Seitenfassaden der Fluegel (sichtbar in Schraegansichten)
	for _, sx in ipairs({ -1, 1 }) do
		for f = 0, 2 do for z = Z0 + 8, Z0 + DEPTH - 8, 12 do
			window(CF(sx * (W / 2 + 0.01), f * FLOOR + 3 + 6.6, z) * CFrame.Angles(0, math.rad(sx * 90), 0), 7.2, 7.6)
		end end
	end
	return cur
end

-- ---------- Hintergrund: Haeuserzeile gegenueber, Wohnbloecke hinter der Schule, Nachbarhaeuser seitlich ----------
function S.background()
	cur = folder("Background")
	local function house(x, z, w, d, h, wallc, roofc, face)
		-- face: Richtung der Vorderseite (+1 = Blick +Z zur Schule, -1 = Blick -Z)
		P("House", V(w, h, d), CF(x, h / 2, z), wallc, M.Brick)
		local r1 = P("Roof", V(w + 1, 7, d / 2 + 0.6), CF(), roofc, M.Slate, { wedge = true })
		r1.CFrame = ORIGIN * CF(x, h + 3.5, z + d / 4) * CFrame.Angles(0, math.rad(180), 0)
		local r2 = P("Roof", V(w + 1, 7, d / 2 + 0.6), CF(), roofc, M.Slate, { wedge = true })
		r2.CFrame = ORIGIN * CF(x, h + 3.5, z - d / 4)
		local fz = z + face * (d / 2 + 0.1)
		for fl = 0, math.floor(h / 11) - 1 do
			for wx = x - w / 2 + 5, x + w / 2 - 5, 8 do
				P("HWin", V(4.2, 5.2, 0.3), CF(wx, fl * 11 + 6.5, fz), C(70, 84, 96), M.Glass, { refl = 0.2, noShadow = true })
				P("HWinSill", V(5.0, 0.4, 0.8), CF(wx, fl * 11 + 3.7, fz + face * 0.3), C(190, 184, 172), M.Concrete, { noShadow = true })
			end
		end
	end
	-- gegenueber der Schule (Suedseite der Strasse), Vorderseite zur Strasse
	local row = { { -200, 34, 26, C(150, 92, 72), C(70, 62, 60) }, { -160, 30, 22, C(196, 184, 160), C(84, 70, 64) }, { -122, 36, 30, C(132, 84, 68), C(62, 58, 58) },
		{ -82, 32, 24, C(170, 160, 146), C(76, 66, 62) }, { -42, 38, 26, C(144, 96, 76), C(66, 60, 58) }, { 0, 34, 22, C(186, 176, 156), C(80, 68, 62) },
		{ 40, 36, 28, C(138, 88, 70), C(64, 58, 58) }, { 80, 30, 24, C(200, 190, 170), C(82, 70, 64) }, { 120, 36, 26, C(148, 98, 80), C(66, 60, 58) },
		{ 160, 32, 30, C(176, 166, 150), C(78, 66, 62) }, { 200, 34, 24, C(140, 90, 72), C(64, 58, 58) } }
	for _, h in ipairs(row) do house(h[1], -132, h[2], 26, h[3], h[4], h[5], 1) end
	-- Wohnbloecke hinter der Schule (fuellen den Horizont ueber dem Dach)
	for i, b in ipairs({ { -150, 60 }, { -50, 72 }, { 60, 66 }, { 160, 58 } }) do
		local x, h = b[1], b[2]
		P("Block", V(60, h, 30), CF(x, h / 2, 190 + (i % 2) * 14), C(170 - i * 6, 166 - i * 6, 160 - i * 6), M.Concrete)
		for fl = 1, math.floor(h / 10) - 1 do
			P("BlockBand", V(61, 0.6, 31), CF(x, fl * 10, 190 + (i % 2) * 14), C(140, 136, 130), M.Concrete, { noShadow = true })
			for wx = x - 24, x + 24, 8 do P("BWin", V(4.5, 5, 0.3), CF(wx, fl * 10 - 4.4, 190 + (i % 2) * 14 - 15.1), C(70, 84, 96), M.Glass, { refl = 0.2, noShadow = true }) end
		end
	end
	-- seitliche Nachbarn hinter dem Zaun
	house(-250, 20, 40, 34, 26, C(176, 166, 150), C(74, 64, 60), -1)
	house(250, 20, 40, 34, 22, C(150, 98, 78), C(66, 60, 58), -1)
	-- Hecken entlang des Zauns innen (vor den Seitenhaeusern)
	for _, sx in ipairs({ -1, 1 }) do P("Hedge", V(5, 6, 110), CF(sx * 198, 3.4, 27), C(58, 78, 46), M.Grass) end
	return cur
end

-- ---------- Baeume: stilisiert (Stamm, Aeste, Kronen aus Kugeln) in Herbstfarben ----------
function S.trees()
	cur = folder("Trees")
	local BARK = C(84, 66, 52)
	local LEAF = { C(196, 128, 58), C(184, 150, 70), C(150, 108, 52), C(118, 122, 62) }
	local function tree(x, z, s, tint)
		P("Trunk", V(1.6 * s, 13 * s, 1.6 * s), CF(x, 6.5 * s, z), BARK, M.Wood)
		for i, a in ipairs({ 30, 150, 260 }) do
			local br = P("Branch", V(0.8 * s, 6 * s, 0.8 * s), CF(), BARK, M.Wood)
			br.CFrame = ORIGIN * CF(x, 12 * s, z) * CFrame.Angles(0, math.rad(a), math.rad(38)) * CF(0, 2.6 * s, 0)
		end
		local balls = { { 0, 17, 0, 9 }, { 3.6, 15.5, 1.2, 6.8 }, { -3.4, 15.8, -1.0, 6.6 }, { 0.8, 15.2, -3.5, 6.2 }, { -0.8, 20.2, 0.4, 6.4 }, { 1.6, 16.5, 3.4, 5.8 } }
		for i, b in ipairs(balls) do
			local p = P("Crown", V(b[4] * s, b[4] * s, b[4] * s), CF(x + b[1] * s, b[2] * s, z + b[3] * s), LEAF[((i + tint) % #LEAF) + 1], M.Grass,
				{ shape = Enum.PartType.Ball })
		end
	end
	-- im Hof (Rasenbeete), am Gehweg vor dem Zaun und hinter der Schule
	tree(-44, 10, 1.0, 0); tree(-80, 32, 1.15, 1); tree(48, 32, 1.05, 2); tree(86, 10, 0.95, 3)
	tree(-36, -40, 0.9, 1); tree(36, -40, 0.95, 2); tree(-100, -40, 1.0, 3); tree(110, -40, 0.9, 0)
	tree(-180, 150, 1.4, 2); tree(-10, 156, 1.5, 1); tree(150, 150, 1.3, 3)
	-- herabgefallenes Laub als flache Flecken unter den Hofbaeumen (gezielt, nicht zufaellig verteilt)
	for _, t in ipairs({ { -44, 10 }, { -80, 32 }, { 48, 32 }, { 86, 10 } }) do
		P("LeafPatch", V(14, 0.05, 12), CF(t[1] + 2, 0.82, t[2] - 1), C(176, 120, 56), M.Grass, { noShadow = true, noCollide = true })
	end
	return cur
end

-- ---------- Gym-Front "um die Ecke" (Szene 7): ersetzt das Haus bei x = 120 in der Haeuserzeile; echtes Logo aus dem Gym ----------
function S.gymfront()
	cur = folder("GymFront")
	for _, d in ipairs(root.Background:GetChildren()) do                      -- Haus an dieser Stelle entfernen
		if d:IsA("BasePart") then
			local lp = ORIGIN:PointToObjectSpace(d.Position)
			if math.abs(lp.X - 120) < 16 and lp.Z < -112 and lp.Z > -150 then d:Destroy() end
		end
	end
	local X, Z, W, Dp, H = 120, -132, 40, 26, 28
	local FZ = Z + Dp / 2                                                   -- Vorderseite (Blick +Z zur Strasse)
	local DARK, TRIM, GLASS = C(58, 60, 66), C(36, 38, 42), C(110, 130, 140)
	P("GymBody", V(W, H, Dp), CF(X, H / 2, Z), DARK, M.Concrete)
	P("GymParapet", V(W + 1, 1.2, Dp + 1), CF(X, H + 0.6, Z), TRIM, M.Metal)
	P("GymPlinth", V(W + 0.4, 1.2, Dp + 0.4), CF(X, 0.6, Z), C(70, 70, 72), M.Concrete)
	-- Schaufenster links/rechts der Tuer mit Blick ins helle Innere
	for _, sx in ipairs({ -1, 1 }) do
		local cx = X + sx * 11
		P("ShopInner", V(14, 10, 0.2), CF(cx, 6.6, FZ + 0.05), C(226, 220, 208), M.SmoothPlastic, { noShadow = true }); local sl = Instance.new("SurfaceLight"); sl.Face = Enum.NormalId.Front; sl.Range = 10; sl.Brightness = 1.2; sl.Color = C(255, 238, 214); sl.Parent = cur:GetChildren()[#cur:GetChildren()]
		P("ShopGlass", V(14, 10, 0.2), CF(cx, 6.6, FZ + 1.0), GLASS, M.Glass, { refl = 0.12, trans = 0.55, noShadow = true })
		P("ShopFrameT", V(14.6, 0.5, 0.6), CF(cx, 11.8, FZ + 1.1), TRIM, M.Metal); P("ShopFrameB", V(14.6, 0.5, 0.6), CF(cx, 1.4, FZ + 1.1), TRIM, M.Metal)
		for _, k in ipairs({ -1, 1 }) do P("ShopFrameV", V(0.5, 10.4, 0.6), CF(cx + k * 7.05, 6.6, FZ + 1.1), TRIM, M.Metal) end
		-- roter Sandsack im Fenster
		P("ShopBag", V(5.2, 2.2, 2.2), CF(cx + sx * -2, 6.2, FZ - 3), C(150, 28, 34), M.Leather, { shape = Enum.PartType.Cylinder }).CFrame = ORIGIN * CF(cx + sx * -2, 6.4, FZ + 0.55) * CFrame.Angles(0, 0, math.rad(90))
	end
	-- Eingang: Rahmen, Tuer (Scharnier links, wird in Szene 7 geoeffnet), Griff
	P("DoorInner", V(6.4, 11, 0.2), CF(X, 6.9, FZ + 0.05), C(226, 220, 208), M.SmoothPlastic, { noShadow = true })
	P("DoorFrameL", V(0.6, 11.6, 1.0), CF(X - 3.5, 6.9, FZ + 1.1), TRIM, M.Metal); P("DoorFrameR", V(0.6, 11.6, 1.0), CF(X + 3.5, 6.9, FZ + 1.1), TRIM, M.Metal)
	P("DoorFrameT", V(7.6, 0.6, 1.0), CF(X, 12.9, FZ + 1.1), TRIM, M.Metal)
	local door = P("GymDoor", V(6.2, 11, 0.3), CF(X, 6.9, FZ + 1.0), GLASS, M.Glass, { refl = 0.12, trans = 0.45 })
	door:SetAttribute("CC_Hinge", (ORIGIN * CF(X - 3.1, 6.9, FZ + 1.0)).Position)
	local hdl = P("GymDoorHandle", V(0.3, 2.4, 0.3), CF(X + 2.4, 6.6, FZ + 1.3), C(190, 192, 196), M.Metal)
	local w = Instance.new("WeldConstraint"); w.Part0 = door; w.Part1 = hdl; w.Parent = door
	-- Logo-Schild: Kopie des echten Logo-Panels aus dem Gym (gleiche Grafik, kein neues Logo)
	local src = workspace:FindFirstChild("CC_Gym") and workspace.CC_Gym:FindFirstChild("LogoPanel", true)
	local sign = P("GymSign", V(30, 9.75, 0.3), CF(X, 19.2, FZ + 0.25), C(20, 22, 26), M.SmoothPlastic)
	if src then
		for _, d in ipairs(src:GetChildren()) do
			if d:IsA("Decal") or d:IsA("SurfaceGui") then
				local c = d:Clone(); c.Face = Enum.NormalId.Front; c.Parent = sign
			end
		end
	end
	local spot = Instance.new("SpotLight"); spot.Face = Enum.NormalId.Front; spot.Range = 24; spot.Brightness = 1.6; spot.Angle = 80; spot.Color = C(255, 236, 214); spot.Parent = sign
	-- Fussmatte und Stufe
	P("GymStep", V(12, 0.6, 3), CF(X, 0.3, FZ + 2.6), C(110, 108, 104), M.Concrete)
	P("GymMat", V(6, 0.08, 2.4), CF(X, 0.64, FZ + 2.6), C(34, 34, 36), M.Fabric, { noShadow = true })
	return cur
end

return function(section)
	local fn = S[section]; assert(fn, "unbekannter Abschnitt " .. tostring(section))
	local m = fn(); m.Parent = root
	local n = 0; for _, d in ipairs(m:GetDescendants()) do if d:IsA("BasePart") then n += 1 end end
	return section .. ": " .. n .. " Teile"
end
