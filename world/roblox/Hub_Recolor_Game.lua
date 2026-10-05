-- Faerbt den vorhandenen Hub (Workspace/MemeWorld/MemeHub) von Pastel auf die Spiel-Farben um.
-- Baut NICHTS neu: Skripte, ProximityPrompts usw. an den Staenden bleiben erhalten.
-- Korrigiert ausserdem den Bordstein, der die Platzflaeche verdeckt hat.
-- Ausfuehren in Roblox Studio (Command Bar oder MCP). Mehrfaches Ausfuehren ist harmlos.

local hub = workspace:FindFirstChild("MemeWorld") and workspace.MemeWorld:FindFirstChild("MemeHub")
assert(hub, "Workspace/MemeWorld/MemeHub nicht gefunden")

local MAP = {
	["fbf6f0"] = "#f4f5f7", -- plaza
	["efe4f3"] = "#dde2ea", -- plaza2
	["d9cde6"] = "#2f6fe0", -- curb
	["f2868f"] = "#e2393f", -- accent
	["ffcf9e"] = "#f4b42c", -- accent2
	["86c3e3"] = "#33c8f0", -- accent3
	["c79a78"] = "#a8703f", -- wood
	["fff0b3"] = "#ffe68a", -- glow
	["79bf86"] = "#2f9e44", -- leaf
	["9fd6a2"] = "#4cc25a", -- leaf2
	["ffffff"] = "#ffffff", -- sign_text
}
local TRIM = "#1f3fa8"   -- Rahmen, Dach-Ring, Saeulen-Fuesse ...
local METAL = "#1c2342"  -- Laternen, Bank-Beine, Fahnenmasten
local OLD_TRIM = "5f5490" -- in Pastel waren Rahmen und Metall gleich

local function isMetal(name)
	return string.find(name, "Lamp") or string.find(name, "BenchLeg") or string.find(name, "FlagPole")
end

local changed = 0
for _, d in ipairs(hub:GetDescendants()) do
	if d:IsA("BasePart") then
		local hex = string.lower(d.Color:ToHex())
		if hex == OLD_TRIM then
			d.Color = Color3.fromHex(isMetal(d.Name) and METAL or TRIM)
			changed += 1
		elseif MAP[hex] then
			d.Color = Color3.fromHex(MAP[hex])
			changed += 1
		end
		if d.Name == "Curb" and d.Size.X > 1 then -- Zylinder: Hoehe = Size.X
			local old = d.Size.X
			d.Size = Vector3.new(0.8, d.Size.Y, d.Size.Z)
			d.CFrame = d.CFrame - Vector3.new(0, (old - 0.8) / 2, 0)
		end
	elseif d:IsA("TextLabel") then
		d.TextColor3 = Color3.fromHex("#ffffff")
	end
end
print("Hub umgefaerbt: " .. changed .. " Teile")
