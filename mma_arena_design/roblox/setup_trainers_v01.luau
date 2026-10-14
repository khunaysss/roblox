-- setup_trainers_v01.luau (einmal in Studio im Edit-Modus ausfuehren, nach dem Import von export/Trainers_v01_Roblox.fbx)
-- Gleiches Verfahren wie setup_coach_v01.luau, aber fuer die sechs Stil-Trainer: Teile nach Namensanfang auf sechs Modelle
-- verteilen, nach export/Trainers_v01_data.luau faerben, verankern, Kollision nur ueber eine unsichtbare Saeule "Root",
-- Drehpunkt an der Fusssohle (Blick nach -Z). Ergebnis: ServerStorage.CC_StyleTrainers.<Name>. CC_Trainers stellt sie ins Gym.
local HS = game:GetService("HttpService")
local src = workspace:FindFirstChild("Trainers_v01_Roblox") or workspace:FindFirstChild("Trainers_v01_Roblox", true)
assert(src, "Importiertes Modell 'Trainers_v01_Roblox' nicht gefunden – bitte zuerst importieren")
HS.HttpEnabled = true
local ok, txt = pcall(function() return HS:GetAsync("http://127.0.0.1:8766/export/Trainers_v01_data.luau") end)
HS.HttpEnabled = false
assert(ok, "Daten nicht geladen (lokaler Server 8766?): " .. tostring(txt))
local data = loadstring(txt)()

local folder = game.ServerStorage:FindFirstChild("CC_StyleTrainers")
if folder then folder.Parent = game.ServerStorage:FindFirstChild("CC_Old") or game.ServerStorage; folder.Name = "CC_StyleTrainers_alt" end
folder = Instance.new("Folder"); folder.Name = "CC_StyleTrainers"
local models, report = {}, {}
local function colorFor(t, name)
	local cols = data[t].colors
	if cols[name] then return cols[name] end
	local base = name:gsub("%.%d+$", "")
	for k, v in pairs(cols) do if k:gsub("%.%d+$", "") == base then return v end end
	local head, tail = name:match("^(.-)%.%.%.(.*)$")             -- von Studio gekuerzte Namen
	if head then for k, v in pairs(cols) do if k:sub(1, #head) == head and k:sub(-#tail) == tail then return v end end end
end
for _, d in ipairs(src:GetDescendants()) do
	if d:IsA("BasePart") then
		local t
		for name in pairs(data) do if d.Name:sub(1, #name) == name then t = name end end
		if t then
			models[t] = models[t] or { parts = {}, colored = 0 }
			local c = colorFor(t, d.Name)
			if c then d.Color = Color3.fromRGB(c.rgb[1], c.rgb[2], c.rgb[3]); models[t].colored += 1 end
			d.Material = Enum.Material.SmoothPlastic
			d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.CastShadow = true
			table.insert(models[t].parts, d)
		end
	end
end
for t, info in pairs(models) do
	local model = Instance.new("Model"); model.Name = t
	for _, p in ipairs(info.parts) do p.Parent = model end
	local cf, size = model:GetBoundingBox()
	local scale = data[t].height / size.Y
	if math.abs(scale - 1) > 0.05 then model:ScaleTo(scale); cf, size = model:GetBoundingBox() end
	local foot = Vector3.new(cf.Position.X, cf.Position.Y - size.Y / 2, cf.Position.Z)
	local root = Instance.new("Part"); root.Name = "Root"; root.Size = Vector3.new(2.2, size.Y, 1.6)
	root.CFrame = CFrame.new(foot + Vector3.new(0, size.Y / 2, 0))
	root.Transparency = 1; root.Anchored = true; root.CanCollide = true; root.CanQuery = true; root.CanTouch = false; root.Parent = model
	model.PrimaryPart = root
	root.PivotOffset = CFrame.new(0, -size.Y / 2, 0)
	model.Parent = folder
	table.insert(report, ("%s %d/%d %.2f"):format(t, info.colored, #info.parts, size.Y))
end
folder.Parent = game.ServerStorage
src:Destroy()
table.sort(report)
return "Trainer eingerichtet: " .. table.concat(report, " | ")
