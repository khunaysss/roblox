-- setup_belts_v01.luau (einmal in Studio im Edit-Modus ausfuehren)
-- Voraussetzung: export/Fighter_Belts_v01.fbx ueber Import 3D importiert (Rig: Custom, Centimeter, Faktor 1) -> Workspace.Fighter_Belts_v01
-- Ergebnis: ServerStorage.CC_Belts.<Teil> mit Attribut CC_C0 (Versatz zum HumanoidRootPart wie bei setup_custom_v01.luau:
-- Teilposition - Root-Bone - 3 Studs). Anbringen wie die Kleidung: Motor6D (Part0 = HumanoidRootPart, C0 = CC_C0).
-- Teile: Titelguertel = Belt_Title_Band, Belt_Title_Plate, Belt_Title_Trim, Belt_Title_Gem; Stoffguertel = Belt_Cloth_Band, Belt_Cloth_Tip.
-- Farben setzt das Spiel je Stil/Stufe (CC_Belts.module); hier nur Grundfarben.
local SS = game:GetService("ServerStorage")
local model = workspace:FindFirstChild("Fighter_Belts_v01")
assert(model, "Importiertes Modell Fighter_Belts_v01 nicht gefunden")
local root = model:FindFirstChild("Root", true)
assert(root and root:IsA("Bone"), "Root-Bone fehlt")

local BASE = {
	Belt_Title_Band = Color3.fromRGB(16, 16, 18), Belt_Title_Plate = Color3.fromRGB(212, 168, 56), Belt_Title_Trim = Color3.fromRGB(242, 204, 96),
	Belt_Title_Gem = Color3.fromRGB(190, 20, 30), Belt_Cloth_Band = Color3.fromRGB(235, 235, 230), Belt_Cloth_Tip = Color3.fromRGB(20, 20, 22),
}
local out = SS:FindFirstChild("CC_Belts") or Instance.new("Folder")
out.Name = "CC_Belts"; out:ClearAllChildren(); out.Parent = SS
local missing, n = {}, 0
for name, color in pairs(BASE) do
	local p = model:FindFirstChild(name, true)
	if p and p:IsA("BasePart") then
		p:SetAttribute("CC_C0", CFrame.new(p.Position - root.WorldPosition - Vector3.new(0, 3, 0)))
		p.Color = color
		p.Material = (name == "Belt_Title_Plate" or name == "Belt_Title_Trim") and Enum.Material.Metal or Enum.Material.SmoothPlastic
		p.Anchored = false; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.Massless = true
		for _, j in ipairs(p:GetChildren()) do if j:IsA("JointInstance") then j:Destroy() end end
		p.Parent = out; n += 1
	else
		table.insert(missing, name)
	end
end
return ("Guertel: %d Teile eingerichtet%s"):format(n, #missing > 0 and (", fehlen: " .. table.concat(missing, ", ")) or "")
