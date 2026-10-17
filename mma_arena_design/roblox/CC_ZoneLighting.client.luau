-- StarterPlayer.StarterPlayerScripts.CC_ZoneLighting
-- Lichtstimmung je Bereich (nur lokal, nur Optik): Gym = neutral-weiss (Redesign 2026-10-17), Fight Night (Kaefig bei z = -700)
-- = die Werte von vorher (kuehler, bläulich). Umschalten nach Kameraposition, weich ueber 0,6 s.
local Lighting = game:GetService("Lighting")
local RunService = game:GetService("RunService")

local GYM = {
	Ambient = Color3.new(0.30, 0.31, 0.34), OutdoorAmbient = Color3.new(0.20, 0.21, 0.235),
	Tint = Color3.new(1, 0.995, 0.99), Contrast = 0.06, Saturation = -0.04,
}
local FIGHT = {
	Ambient = Color3.new(0.345, 0.376, 0.455), OutdoorAmbient = Color3.new(0.216, 0.243, 0.314),
	Tint = Color3.new(0.949, 0.965, 1), Contrast = 0.03, Saturation = -0.03,
}
local FIGHT_Z = -400                       -- Kamera hinter dieser Linie = Fight Night

local cc = Lighting:WaitForChild("CC_GymColor", 10)
local w = 0                                -- 0 = Gym, 1 = Fight Night
RunService.RenderStepped:Connect(function(dt)
	local cam = workspace.CurrentCamera
	if not cam then return end
	local target = cam.CFrame.Position.Z < FIGHT_Z and 1 or 0
	if math.abs(target - w) < 0.001 then return end
	w = w + math.clamp(target - w, -dt / 0.6, dt / 0.6)
	Lighting.Ambient = GYM.Ambient:Lerp(FIGHT.Ambient, w)
	Lighting.OutdoorAmbient = GYM.OutdoorAmbient:Lerp(FIGHT.OutdoorAmbient, w)
	if cc then
		cc.TintColor = GYM.Tint:Lerp(FIGHT.Tint, w)
		cc.Contrast = GYM.Contrast + (FIGHT.Contrast - GYM.Contrast) * w
		cc.Saturation = GYM.Saturation + (FIGHT.Saturation - GYM.Saturation) * w
	end
end)
