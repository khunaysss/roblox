-- ReplicatedStorage.CC_Hands (ModuleScript) – Haende mit Fingern fuer Darsteller in Kleidung (Story, Ecke, Ringrichter, Ladefilm, Thumbnail)
-- Warum: Fighter_Body hat Block-Haende; Casual_Hands war nur eine Huelle davor und wirkte wie ein schwebender Klotz. Neu: Koerper ohne Haende
-- (Fighter_BodyNoHands) plus je Seite fuenf Hand-Posen als eigene Teile (Hand_<Pose>_<L|R>), Manschette liegt unter dem Aermel.
-- Die Teile liegen in ReplicatedStorage.CC_StoryShared.Hands (setup_hands_v01.luau) und werden wie die Kleidung (Outfit) per Motor6D an den
-- HumanoidRootPart des Darstellers gehaengt. Posen = Teile ein-/ausblenden (das Roblox-Rig hat keine Finger-Knochen).
-- Nur verwenden, wenn die Handschuhe aus sind (Darsteller in Alltagskleidung/Trainingsanzug); im Kampf bleiben Handschuhe + Fighter_Body.
-- API:
--   Hands.available()                       -> true, wenn die Teile eingerichtet sind
--   Hands.attach(model, skinColor?, pose?)  -> true, wenn die neuen Haende sitzen (sonst false: Aufrufer nimmt wie bisher Casual_Hands)
--   Hands.setPose(model, pose, rightPose?)  -> beide Haende auf pose (Open/Relaxed/Point/Fist/Thumb), optional rechts abweichend
--   Hands.recolor(model, color)             -> Hautfarbe nachtragen (z. B. nach Look.apply)
--   Hands.detach(model)                     -> zurueck zum alten Koerper (Fighter_Body sichtbar)
local RS = game:GetService("ReplicatedStorage")
local Hands = {}
Hands.POSES = { "Open", "Relaxed", "Point", "Fist", "Thumb" }
Hands.DEFAULT = "Relaxed"

local function source()
	local sh = RS:FindFirstChild("CC_StoryShared")
	local f = sh and sh:FindFirstChild("Hands")
	return f and f:FindFirstChild("Fighter_BodyNoHands") and f or nil
end

function Hands.available() return source() ~= nil end

local function isHandPart(p) return p:IsA("MeshPart") and (p.Name:sub(1, 5) == "Hand_" or p.Name == "Fighter_BodyNoHands") and p:GetAttribute("CC_HandsPart") == true end

function Hands.attach(model, skinColor, pose)
	local src = source(); if not src then return false end
	local hrp = model:FindFirstChild("HumanoidRootPart"); if not hrp then return false end
	local gloves = model:FindFirstChild("Fighter_Gloves")
	if gloves and gloves.Transparency < 0.5 then return false end          -- Handschuhe an: keine Haende
	if model:FindFirstChild("Fighter_BodyNoHands") then Hands.setPose(model, pose or Hands.DEFAULT); return true end
	local body = model:FindFirstChild("Fighter_Body")
	local color = skinColor or (body and body.Color) or Color3.fromRGB(184, 148, 123)
	for _, t in ipairs(src:GetChildren()) do
		if t:IsA("MeshPart") and t:GetAttribute("CC_C0") then
			local p = t:Clone(); p.Massless = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.Color = color
			p:SetAttribute("CC_HandsPart", true)
			local mo = Instance.new("Motor6D"); mo.Name = "CC_HandsMotor"; mo.Part0 = hrp; mo.Part1 = p; mo.C0 = t:GetAttribute("CC_C0"); mo.Parent = p
			p.Parent = model
		end
	end
	if body then body:SetAttribute("CC_HandsPrevT", body.Transparency); body.Transparency = 1 end
	Hands.setPose(model, pose or Hands.DEFAULT)
	return true
end

function Hands.setPose(model, pose, rightPose)
	local want = { L = pose or Hands.DEFAULT, R = rightPose or pose or Hands.DEFAULT }
	for side, name in pairs(want) do
		for _, n in ipairs(Hands.POSES) do
			local p = model:FindFirstChild("Hand_" .. n .. "_" .. side)
			if p then p.Transparency = (n == name) and 0 or 1 end
		end
	end
	model:SetAttribute("CC_HandPose", want.L .. "/" .. want.R)
end

function Hands.recolor(model, color)
	for _, p in ipairs(model:GetChildren()) do if isHandPart(p) then p.Color = color end end
end

function Hands.detach(model)
	for _, p in ipairs(model:GetChildren()) do if isHandPart(p) then p:Destroy() end end
	local body = model:FindFirstChild("Fighter_Body")
	if body then body.Transparency = body:GetAttribute("CC_HandsPrevT") or 0 end
	model:SetAttribute("CC_HandPose", nil)
end

return Hands
