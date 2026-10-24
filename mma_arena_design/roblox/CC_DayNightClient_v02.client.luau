-- StarterPlayer.StarterPlayerScripts.CC_DayNightClient
-- Synchroner Tageslauf; die Referenz-Lichtstimmung gilt nur im Gym.
local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local config = ReplicatedStorage:WaitForChild("CC_DayNightState", 30)
if not config then
	warn("[CC] Tag-Nacht-Zeitbasis fehlt.")
	return
end
local settings = ReplicatedStorage:WaitForChild("CC_GymVisualSettings", 10)
local player = Players.LocalPlayer
local seconds, startHour, epoch, enabled, preview = 1200, 14, 0, true, nil
local function readConfig()
	seconds = math.max(120, tonumber(config:GetAttribute("CycleSeconds")) or 1200)
	startHour = tonumber(config:GetAttribute("StartHour")) or 14
	epoch = tonumber(config:GetAttribute("Epoch")) or workspace:GetServerTimeNow()
	enabled = config:GetAttribute("Enabled") ~= false
	preview = config:GetAttribute("PreviewHour")
end
readConfig()
local changed = config.AttributeChanged:Connect(readConfig)
local currentGym = nil
local function original(property, fallback)
	local value = settings and settings:GetAttribute("Original_" .. property)
	return value == nil and fallback or value
end
-- Zustandsabhaengig und selbstheilend (2026-10-24): Effekt-Schalter werden jedes Bild gegen den Sollzustand geprueft,
-- nicht nur beim Wechsel Gym <-> ausserhalb. Grund: andere Systeme (Ladefilm CC_WalkIn, Menue) stellen beim Beenden den
-- gespeicherten Ausgangszustand der Datei wieder her (= Gym-Effekte an); mit reinem Wechsel-Cache blieben dann Gym-Effekte inkl.
-- Tiefenunschaerfe (CC_GymFocus) im Kampf aktiv. Waehrend Menue/Story das Licht fuehren, bleibt die Tiefenunschaerfe unberuehrt.
local function effectsForGym(active, ownerIsMenu)
	local switched = currentGym ~= active
	currentGym = active
	for _,effect in Lighting:GetChildren() do
		if effect.Name == "CC_GymReferenceGrade" or effect.Name == "CC_GymReferenceBloom" or effect.Name == "CC_GymFocus" then
			if not (ownerIsMenu and effect:IsA("DepthOfFieldEffect")) and effect.Enabled ~= active then effect.Enabled = active end
		elseif effect:IsA("PostEffect") and effect:GetAttribute("CC_OriginalEnabled") ~= nil then
			local want = not active and effect:GetAttribute("CC_OriginalEnabled") == true
			if not (ownerIsMenu and effect:IsA("DepthOfFieldEffect")) and effect.Enabled ~= want then effect.Enabled = want end
		elseif not switched then
			-- Atmosphaere und Lichtwerte nur beim Wechsel setzen (wie bisher)
		elseif effect:IsA("Atmosphere") and effect:GetAttribute("CC_OriginalDensity") ~= nil then
			effect.Density = active and (effect.Name == "Atmosphere" and 0.06 or 0) or effect:GetAttribute("CC_OriginalDensity")
			effect.Haze = active and (effect.Name == "Atmosphere" and 0.2 or 0) or effect:GetAttribute("CC_OriginalHaze")
		end
	end
	if not switched then return end
	Lighting.EnvironmentDiffuseScale = active and 0.52 or original("EnvironmentDiffuseScale", 0.35)
	Lighting.EnvironmentSpecularScale = active and 0.46 or original("EnvironmentSpecularScale", 0.55)
	Lighting.ShadowSoftness = active and 0.75 or original("ShadowSoftness", 0.32)
end
local function update()
	if Lighting:GetAttribute("CC_MenuLighting") or Lighting:GetAttribute("CC_StoryLighting") then
		effectsForGym(false, true)
		return
	end
	local hour = type(preview) == "number" and preview
		or (startHour + (enabled and (workspace:GetServerTimeNow() - epoch) * 24 / seconds or 0)) % 24
	local daylight = math.clamp((math.sin((hour - 6) / 24 * math.pi * 2) + 0.12) / 1.12, 0, 1)
	daylight = daylight * daylight * (3 - 2 * daylight)
	local character = player.Character
	local hrp = character and character:FindFirstChild("HumanoidRootPart")
	local position = hrp and hrp.Position
	local matchId = player:GetAttribute("CC_MatchId") or (character and character:GetAttribute("CC_MatchId"))
	local active = settings ~= nil and position ~= nil
		and position.X > 69 and position.X < 252 and position.Z > -89 and position.Z < 65
		and (matchId == nil or matchId == "")
	effectsForGym(active)
	-- Im Gym bleibt die gewaehlte Abendstimmung stabil; anderswo laeuft der Tageszyklus weiter.
	Lighting.ClockTime = active and 17.55 or hour
	if active then
		Lighting.Brightness = 2.0
		Lighting.ExposureCompensation = 0.12
		Lighting.Ambient = Color3.fromRGB(104, 109, 121)
		Lighting.OutdoorAmbient = Color3.fromRGB(87, 102, 132)
	else
		Lighting.Brightness = 1.3 + 1.3 * daylight
		Lighting.ExposureCompensation = 0.04 + 0.08 * daylight
		Lighting.Ambient = original("Ambient", Color3.fromRGB(77, 79, 87))
		Lighting.OutdoorAmbient = original("OutdoorAmbient", Color3.fromRGB(51, 54, 60))
	end
end
local binding = "CC_DayNightLighting"
RunService:BindToRenderStep(binding, Enum.RenderPriority.Last.Value + 20, update)
script.Destroying:Connect(function()
	RunService:UnbindFromRenderStep(binding)
	changed:Disconnect()
end)
update()

