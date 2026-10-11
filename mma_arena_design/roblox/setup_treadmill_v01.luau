-- setup_treadmill_v01.luau (einmal in Studio im Edit-Modus ausfuehren; Gameplay-Ueberarbeitung Abschnitt 6)
-- Baut ein Laufband aus Teilen in der Farbwelt des Gyms (dunkles Metall, schwarzes Band, rote Markierung, weisse Akzente)
-- und einen Interaktionspunkt (CC_GymInteractions.Treadmill_1, CC_Interaction = "treadmill").
-- Platz: freier Betonboden vor der Ostwand (x 182-191, z -10 bis -6; die Mattenflaeche bleibt frei), Laufrichtung +X (Konsole vorn zur Wand).
-- Bewegte Bandlamellen (CC_BeltSlat_*) werden im Spiel vom Client verschoben (CC_Minigame), sie kollidieren nicht.
-- Masse: Band 6,8 x 2,4 Studs (1,9 x 0,7 m), Bandoberkante 0,63 Studs (18 cm) ueber dem Boden.
local gym = workspace:FindFirstChild("CC_Gym") or workspace
local old = gym:FindFirstChild("Treadmill_1"); if old then old:Destroy() end
local oldM = workspace.CC_GymInteractions:FindFirstChild("Treadmill_1"); if oldM then oldM:Destroy() end

local C = Vector3.new(186, 0, -8)                 -- Mitte auf dem Boden (Beton vor der Wand, Konsole zur Wand)
local model = Instance.new("Model"); model.Name = "Treadmill_1"
local METAL, BLACK, BELT, RED, WHITE, SLAT = Color3.fromRGB(69, 69, 72), Color3.fromRGB(44, 44, 47), Color3.fromRGB(28, 28, 30),
	Color3.fromRGB(188, 39, 44), Color3.fromRGB(231, 231, 231), Color3.fromRGB(78, 78, 82)
local function part(name, size, cf, color, mat, shape)
	local p = Instance.new("Part"); p.Name = name; p.Size = size; p.CFrame = cf; p.Color = color; p.Material = mat or Enum.Material.Metal
	p.Anchored = true; p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
	if shape then p.Shape = shape end
	p.Parent = model; return p
end
local at = function(x, y, z) return CFrame.new(C + Vector3.new(x, y, z)) end
-- Unterbau und Band
part("Deck_Frame", Vector3.new(7.4, 0.5, 3.0), at(0, 0.27, 0), BLACK, Enum.Material.SmoothPlastic)
part("Belt", Vector3.new(6.8, 0.08, 2.4), at(0, 0.58, 0), BELT, Enum.Material.Rubber)
for _, z in ipairs({ -1.38, 1.38 }) do
	part("Side_Rail", Vector3.new(7.4, 0.22, 0.36), at(0, 0.62, z), METAL)
	part("Side_Rail_Red", Vector3.new(7.0, 0.07, 0.02), at(0, 0.62, z + (z > 0 and 0.19 or -0.19)), RED, Enum.Material.SmoothPlastic)
end
for _, x in ipairs({ -3.5, 3.5 }) do
	part("Roller", Vector3.new(2.6, 0.5, 0.5), CFrame.new(C + Vector3.new(x, 0.42, 0)) * CFrame.Angles(0, math.rad(90), 0), METAL, Enum.Material.Metal, Enum.PartType.Cylinder)
end
part("Motor_Hood", Vector3.new(1.2, 0.7, 3.0), at(3.9, 0.42, 0), BLACK, Enum.Material.SmoothPlastic)
-- Lamellen (bewegen sich im Spiel)
local SLATS = 14
for i = 1, SLATS do
	local s = part("CC_BeltSlat_" .. i, Vector3.new(0.1, 0.02, 2.3), at(-3.35 + (i - 1) * 6.7 / SLATS, 0.63, 0), SLAT, Enum.Material.SmoothPlastic)
	s.CanCollide = false; s.CanQuery = false; s.CanTouch = false
end
-- Staender, Handlaeufe, Konsole
for _, z in ipairs({ -1.45, 1.45 }) do
	part("Upright", Vector3.new(0.28, 4.4, 0.28), CFrame.new(C + Vector3.new(3.75, 2.55, z)) * CFrame.Angles(0, 0, math.rad(-8)), METAL)
	part("Handrail", Vector3.new(2.2, 0.22, 0.22), at(2.75, 3.75, z), METAL)
	part("Handrail_Grip", Vector3.new(1.2, 0.26, 0.26), at(2.4, 3.75, z), BLACK, Enum.Material.Rubber)
end
local console = part("Console", Vector3.new(0.35, 1.3, 3.2), CFrame.new(C + Vector3.new(3.9, 4.55, 0)) * CFrame.Angles(0, 0, math.rad(28)), BLACK, Enum.Material.SmoothPlastic)
part("Console_Trim", Vector3.new(0.38, 0.08, 3.2), CFrame.new(C + Vector3.new(3.98, 4.0, 0)) * CFrame.Angles(0, 0, math.rad(28)), RED, Enum.Material.SmoothPlastic)
-- Anzeige auf der Konsole (Tempo), Text setzt der Client
local sg = Instance.new("SurfaceGui"); sg.Name = "CC_TreadDisplay"; sg.Face = Enum.NormalId.Left; sg.CanvasSize = Vector2.new(320, 130)
sg.LightInfluence = 0; sg.Parent = console
local bg = Instance.new("Frame"); bg.Size = UDim2.fromScale(1, 1); bg.BackgroundColor3 = Color3.fromRGB(14, 16, 20); bg.BorderSizePixel = 0; bg.Parent = sg
local t = Instance.new("TextLabel"); t.Name = "Speed"; t.Size = UDim2.fromScale(1, 1); t.BackgroundTransparency = 1; t.TextColor3 = WHITE
t.FontFace = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Bold); t.TextScaled = true; t.Text = "0.0 km/h"; t.Parent = bg
model.PrimaryPart = model:FindFirstChild("Deck_Frame")
model:SetAttribute("CC_BeltLength", 6.7); model:SetAttribute("CC_BeltDir", "+X")
model.Parent = gym

-- Interaktionspunkt am hinteren Ende (Aufstieg)
local m = Instance.new("Part"); m.Name = "Treadmill_1"; m.Size = Vector3.new(1, 1, 1); m.Transparency = 1; m.Anchored = true
m.CanCollide = false; m.CanQuery = false; m.CanTouch = false
m.CFrame = CFrame.new(C + Vector3.new(-4.6, 1.5, 0))
m:SetAttribute("CC_Interaction", "treadmill")
m:SetAttribute("CC_BeltTop", C.Y + 0.63)
m:SetAttribute("CC_BeltCenter", C + Vector3.new(-0.4, 0, 0))
m.Parent = workspace.CC_GymInteractions
return "Laufband gebaut: " .. #model:GetChildren() .. " Teile"
