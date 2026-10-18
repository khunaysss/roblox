-- ServerScriptService.CC_Customize
-- Kaempfer-Aussehen: Frisur, Bart, Gesicht, Hautton, Haarfarbe. Gespeichert im Profil (CC_Profile, Attribut CC_Look als JSON).
-- Daten und Anwenden: ReplicatedStorage.CC_LookShared (gemeinsam mit der Client-Vorschau im Charakter-Editor).
-- Vorlagen: ServerStorage.CC_Custom.<Variante> (skinned MeshParts aus export/Fighter_Custom_v02.fbx, eingerichtet von
-- setup_custom_v01.luau; jedes Teil hat Attribut CC_C0 = Versatz zum HumanoidRootPart). Kopie fuer die Vorschau:
-- ReplicatedStorage.CC_CustomShared.
-- Client -> Server: ReplicatedStorage.CC_Look (RemoteEvent) mit { hair, beard, face, skin, hairColor } (nur beim Speichern).
-- Server -> Client: CC_Look:FireClient(plr, "ok" | "rejected" | "error", text). Speicherstand zusaetzlich am Attribut CC_SaveStatus (CC_Profile).
local Players = game:GetService("Players")
local HS = game:GetService("HttpService")
local SS = game:GetService("ServerStorage")
local RS = game.ReplicatedStorage
local Look = require(RS:WaitForChild("CC_LookShared"))

local remote = RS:FindFirstChild("CC_Look") or Instance.new("RemoteEvent"); remote.Name = "CC_Look"; remote.Parent = RS
local opts = RS:FindFirstChild("CC_LookOptions") or Instance.new("Folder"); opts.Name = "CC_LookOptions"; opts.Parent = RS
opts:SetAttribute("Hair", table.concat(Look.HAIR, ",")); opts:SetAttribute("Beard", table.concat(Look.BEARD, ",")); opts:SetAttribute("Face", table.concat(Look.FACE, ","))
opts:SetAttribute("SkinCount", #Look.SKIN); opts:SetAttribute("HairColorCount", #Look.HAIRCOL)

local function templates() return SS:FindFirstChild("CC_Custom") end
-- Vorlagen fuer die Client-Vorschau bereitstellen
do
	local tpl = templates()
	if tpl and not RS:FindFirstChild("CC_CustomShared") then
		local c = tpl:Clone(); c.Name = "CC_CustomShared"; c.Parent = RS
	end
end

local function lookOf(plr)
	local ok, t = pcall(function() return HS:JSONDecode(plr:GetAttribute("CC_Look") or "") end)
	return ok and type(t) == "table" and t or nil
end
local function hook(plr)
	local function onChar(char)
		char:WaitForChild("HumanoidRootPart")
		task.wait(0.2)
		local l = lookOf(plr); if l then Look.apply(char, l, templates()) end
	end
	plr.CharacterAdded:Connect(onChar)
	if plr.Character then task.spawn(onChar, plr.Character) end
	plr:GetAttributeChangedSignal("CC_Look"):Connect(function()
		local l = lookOf(plr); if l and plr.Character then Look.apply(plr.Character, l, templates()) end
	end)
end
Players.PlayerAdded:Connect(hook)
for _, plr in ipairs(Players:GetPlayers()) do hook(plr) end

remote.OnServerEvent:Connect(function(plr, t)
	if type(t) ~= "table" then return end
	local c = plr.Character
	if c and (c:GetAttribute("CC_Opponent") or c:GetAttribute("CC_Wrestle")) then
		remote:FireClient(plr, "rejected", "Nicht während eines Kampfs.")
		return
	end
	local look = Look.sanitize(t)
	-- Belohnungen: nur freigeschaltete Farben uebernehmen (Server prueft, Client kann nichts erzwingen)
	local prog = Look.progressOf(plr)
	if look.shorts and not Look.unlocked(Look.SHORTS[look.shorts], prog) then look.shorts = nil end
	if look.gloves and not Look.unlocked(Look.GLOVES[look.gloves], prog) then look.gloves = nil end
	local ev = SS:FindFirstChild("CC_ProfileEvent")
	if not ev then remote:FireClient(plr, "error", "Profil-System fehlt."); return end
	ev:Fire(plr, "look", look)
	remote:FireClient(plr, "ok")
end)
