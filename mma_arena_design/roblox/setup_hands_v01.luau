-- setup_hands_v01.luau (einmal in Studio im Edit-Modus ausfuehren, nachdem export/Fighter_Hands_v01.fbx importiert wurde)
-- Erwartet Workspace.Fighter_Hands_v01 (Import 3D, Custom, Centimeter, Faktor 1). Legt die Teile nach
-- ReplicatedStorage.CC_StoryShared.Hands (11 MeshParts: Fighter_BodyNoHands, Hand_<Open|Relaxed|Point|Fist|Thumb>_<L|R>) mit dem Attribut
-- CC_C0 (Motor6D-Offset zum Rig-Wurzelteil, wie bei CC_StoryShared.Outfit). Der Import wandert danach nach ServerStorage.CC_Hands_Import.
-- Verwendet vom Modul ReplicatedStorage.CC_Hands. Vorhandene Hands-Ordner werden nach ServerStorage.CC_Backup_Hands_<Zeit> verschoben.
local RS, SS = game:GetService("ReplicatedStorage"), game:GetService("ServerStorage")
local imp = workspace:FindFirstChild("Fighter_Hands_v01")
assert(imp, "Workspace.Fighter_Hands_v01 fehlt (FBX nicht importiert)")
local SH = RS:WaitForChild("CC_StoryShared")
local old = SH:FindFirstChild("Hands")
if old then old.Name = "CC_Backup_Hands_" .. os.time(); old.Parent = SS end

local SKIN = SH.ActorBase.Fighter_Body.Color
local folder = Instance.new("Folder"); folder.Name = "Hands"
local n = 0
for _, p in ipairs(imp:GetChildren()) do
	if p:IsA("MeshPart") then
		local m = p:FindFirstChildOfClass("Motor6D")
		local c = p:Clone()
		for _, x in ipairs(c:GetChildren()) do if not (x:IsA("SurfaceAppearance") or x:IsA("WrapTarget")) then x:Destroy() end end
		c.Anchored = false; c.Massless = true; c.CanCollide = false; c.CanQuery = false; c.CanTouch = false; c.CastShadow = true
		c.Material = Enum.Material.SmoothPlastic; c.Color = SKIN; c.Transparency = 0
		c:SetAttribute("CC_C0", m.C0)
		c.Parent = folder; n += 1
	end
end
folder.Parent = SH
imp.Name = "CC_Hands_Import"; imp.Parent = SS
return ("Hands eingerichtet: %d Teile"):format(n)
