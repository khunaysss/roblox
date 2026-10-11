-- Einmalige Einrichtung der Anpassungs-Vorlagen in Studio (Edit-Modus).
-- Voraussetzung: export/Fighter_Custom_v02.fbx (v01 enthielt nur die sichtbare Standard-Variante) ueber Import 3D importiert (Rig: Custom, Centimeter, Faktor 1)
-- und export/Fighter_Custom_v02_data.luau als ServerStorage.CC_CustomData (ModuleScript).
-- Ergebnis: ServerStorage.CC_Custom.<Variante>.<Teil> mit Attribut CC_C0 (Versatz zum HumanoidRootPart wie beim Basis-Charakter:
-- Teilposition - Root-Bone - 3 Studs, weil das HumanoidRootPart 3 Studs ueber dem Root-Bone sitzt).
local SS = game:GetService("ServerStorage")
local data = require(SS:WaitForChild("CC_CustomData"))
local model = workspace:FindFirstChild("Fighter_Custom_v02") or workspace:FindFirstChild("Fighter_Custom_v01")
assert(model, "Importiertes Modell Fighter_Custom_v02 nicht gefunden")
local root = model:FindFirstChild("Root", true)
assert(root and root:IsA("Bone"), "Root-Bone fehlt")

local out = SS:FindFirstChild("CC_Custom") or Instance.new("Folder")
out.Name = "CC_Custom"; out.Parent = SS
local missing, n = {}, 0
for variant, names in pairs(data.variants) do
	local f = out:FindFirstChild(variant) or Instance.new("Folder"); f.Name = variant; f:ClearAllChildren(); f.Parent = out
	for _, name in ipairs(names) do
		local p = model:FindFirstChild(name, true)
		if p and p:IsA("BasePart") then
			local off = p.Position - root.WorldPosition - Vector3.new(0, 3, 0)
			p:SetAttribute("CC_C0", CFrame.new(off))
			local c = data.parts[name]
			if c then p.Color = Color3.fromRGB(c.rgb[1], c.rgb[2], c.rgb[3]) end
			p.Anchored = false
			for _, j in ipairs(p:GetChildren()) do if j:IsA("JointInstance") then j:Destroy() end end
			p.Parent = f; n += 1
		else
			table.insert(missing, name)
		end
	end
end
-- Pruefung: Quiff-Kappe muss denselben Versatz haben wie im Basis-Charakter
local check = ""
local base = game.StarterPlayer:FindFirstChild("StarterCharacter")
local cap = out:FindFirstChild("Hair_QuiffV03") and out.Hair_QuiffV03:FindFirstChild("Hair_Cap")
local bm = base and base:FindFirstChild("Hair_Cap") and base.Hair_Cap:FindFirstChildOfClass("Motor6D")
if cap and bm then check = ("Hair_Cap-Versatz Abweichung zum Basis-Charakter: %.4f Studs"):format((cap:GetAttribute("CC_C0").Position - bm.C0.Position).Magnitude) end
-- Rest des Imports aufheben (nicht loeschen)
local old = SS:FindFirstChild("CC_Old") or Instance.new("Folder"); old.Name = "CC_Old"; old.Parent = SS
model.Parent = old
return ("%d Teile eingerichtet, fehlend: %s | %s"):format(n, #missing > 0 and table.concat(missing, ",") or "keine", check)
