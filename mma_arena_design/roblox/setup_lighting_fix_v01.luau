-- setup_lighting_fix_v01.luau (einmal in Studio im Edit-Modus ausfuehren; Qualitaetsrunde Punkt 7)
-- Charaktere wirkten unter den Lampen fast weiss: Gesamthelligkeit, Bloom und die starken Akzent-Spots etwas zuruecknehmen.
-- Vorher: Lighting.Brightness 3, ExposureCompensation 0, Bloom Intensity 1 / Threshold 2,
--         Spots Cage_Accent 2.2, LockerRoom_Style_Spot 1.8, Strength_Accent 1.7, Bag_Accent 1.5, Poster_Wall_Accent 1.3.
-- Atmosphaere (Farben, Deckenlampen, Fensterlicht) bleibt unveraendert. Zuruecksetzen: Werte oben wieder eintragen.
local L = game:GetService("Lighting")
L.Brightness = 2.4
L.ExposureCompensation = -0.2
local bloom = L:FindFirstChildOfClass("BloomEffect")
if bloom then bloom.Intensity = 0.5; bloom.Threshold = 2.4 end
local lights = workspace:FindFirstChild("CC_Gym") and workspace.CC_Gym:FindFirstChild("CC_GymLights")
local n = 0
if lights then
	for _, d in ipairs(lights:GetDescendants()) do
		if d:IsA("SpotLight") and d.Brightness > 1.2 then d.Brightness = math.floor(d.Brightness * 0.7 * 10 + 0.5) / 10; n += 1 end
	end
end
return ("Licht angepasst: Brightness %.1f, Exposure %.1f, %d Spots"):format(L.Brightness, L.ExposureCompensation, n)
