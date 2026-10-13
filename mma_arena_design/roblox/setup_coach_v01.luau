-- setup_coach_v01.luau (einmal in Studio im Edit-Modus ausfuehren, nach dem Import von export/Main_Coach_v01_Roblox.fbx)
-- Import: Studio -> Import 3D -> export/Main_Coach_v01_Roblox.fbx, Einheit Centimeter, Faktor 1, kein Rig (wie Gym/Arena).
-- Das Skript sucht das importierte Modell im Workspace ("Main_Coach_v01_Roblox"), faerbt die Teile nach export/Main_Coach_v01_data.luau,
-- prueft die Groesse (Soll: data.height Studs), verankert alles, schaltet Kollision aus (eine unsichtbare Saeule als Kollision),
-- setzt einen Bezugspunkt "Root" an die Fussmitte (Modell schaut nach -Z) und legt es als ServerStorage.CC_Coach ab.
-- CC_Tutorial stellt daraus den Trainer ins Gym (am Coach_Desk) und an den Kaefigrand.
local HS = game:GetService("HttpService")
local src = workspace:FindFirstChild("Main_Coach_v01_Roblox") or workspace:FindFirstChild("Main_Coach_v01_Roblox", true)
assert(src, "Importiertes Modell 'Main_Coach_v01_Roblox' nicht gefunden – bitte zuerst importieren")
HS.HttpEnabled = true
local ok, txt = pcall(function() return HS:GetAsync("http://127.0.0.1:8766/export/Main_Coach_v01_data.luau") end)
HS.HttpEnabled = false
assert(ok, "Daten nicht geladen (lokaler Server 8766?): " .. tostring(txt))
local data = loadstring(txt)()

local model = Instance.new("Model"); model.Name = "CC_Coach"
local parts, colored = {}, 0
for _, d in ipairs(src:GetDescendants()) do
	if d:IsA("BasePart") then
		table.insert(parts, d)
		local c = data.colors[d.Name]
		if not c then                                  -- Studio kuerzt lange Namen beim Import ("Anfang..._Ende"): ueber Anfang und Ende zuordnen
			local head, tail = d.Name:match("^(.-)%.%.%.(.*)$")
			if head then for k, v in pairs(data.colors) do if k:sub(1, #head) == head and k:sub(-#tail) == tail then c = v; break end end end
		end
		if c then d.Color = Color3.fromRGB(c.rgb[1], c.rgb[2], c.rgb[3]); colored += 1 end
		d.Material = Enum.Material.SmoothPlastic
		d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.CastShadow = true
	end
end
for _, p in ipairs(parts) do p.Parent = model end
-- Groesse pruefen und bei Bedarf skalieren (Bezug: Fusssohle)
local cf, size = model:GetBoundingBox()
local scale = data.height / size.Y
if math.abs(scale - 1) > 0.05 then model:ScaleTo(scale); cf, size = model:GetBoundingBox() end
local foot = Vector3.new(cf.Position.X, cf.Position.Y - size.Y / 2, cf.Position.Z)
local root = Instance.new("Part"); root.Name = "Root"; root.Size = Vector3.new(2.2, size.Y, 1.6)
root.CFrame = CFrame.new(foot + Vector3.new(0, size.Y / 2, 0))                 -- Modell schaut nach -Z (Blender -Y vorne)
root.Transparency = 1; root.Anchored = true; root.CanCollide = true; root.CanQuery = true; root.CanTouch = false; root.Parent = model
model.PrimaryPart = root
root.PivotOffset = CFrame.new(0, -size.Y / 2, 0)            -- Drehpunkt an der Fusssohle (PivotTo setzt die Fuesse auf den Boden)
-- Pivot an die Fussmitte, Blickrichtung -Z
model.WorldPivot = CFrame.new(foot)
local old = game.ServerStorage:FindFirstChild("CC_Coach"); if old then old.Parent = game.ServerStorage:FindFirstChild("CC_Old") or game.ServerStorage; old.Name = "CC_Coach_alt" end
model.Parent = game.ServerStorage
src:Destroy()
return ("Trainer eingerichtet: %d Teile, %d gefaerbt, Hoehe %.2f Studs (Soll %.2f, Faktor %.2f)"):format(#parts, colored, size.Y, data.height, scale)
