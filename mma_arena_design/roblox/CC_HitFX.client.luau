-- StarterPlayer.StarterPlayerScripts.CC_HitFX
-- Treffer-Gefuehl auf dem Bildschirm, nur nach Bestaetigung durch den Server (ReplicatedStorage.CC_HitFX, Staerke 0..1, Art: hit, stagger, ko, block, land):
--   eigener Treffer (land): kurzer Text TREFFER / SCHWERER TREFFER, bei schweren Treffern ein sehr kurzer lokaler Kamera-Halt (Hitstop)
--   getroffen werden (hit/stagger/ko): rotes Aufblitzen, kleiner Kamera-Ruck nur bei schweren Treffern
--   Block: Text GEBLOCKT (statt Aufblitzen)
-- Ausserdem Hinweise aus Attributen am Charakter: CC_Tired (zu wenig Ausdauer) und CC_OutOfRange (Schlag zu weit weg).
local RunService = game:GetService("RunService")
local player = game.Players.LocalPlayer
local fx = game.ReplicatedStorage:WaitForChild("CC_HitFX")

local gui = Instance.new("ScreenGui")
gui.Name = "CC_HitFlash"; gui.IgnoreGuiInset = true; gui.ResetOnSpawn = false; gui.DisplayOrder = 5
gui.Parent = player:WaitForChild("PlayerGui")
local flash = Instance.new("Frame")
flash.Size = UDim2.fromScale(1, 1); flash.BackgroundColor3 = Color3.fromRGB(170, 0, 0)
flash.BackgroundTransparency = 1; flash.BorderSizePixel = 0; flash.Parent = gui
local msg = Instance.new("TextLabel")
msg.AnchorPoint = Vector2.new(0.5, 0.5); msg.Position = UDim2.fromScale(0.5, 0.42); msg.Size = UDim2.fromOffset(500, 40)
msg.BackgroundTransparency = 1; msg.Font = Enum.Font.GothamBlack; msg.TextSize = 30; msg.TextStrokeTransparency = 0.2
msg.TextTransparency = 1; msg.TextStrokeColor3 = Color3.new(0, 0, 0); msg.Text = ""; msg.Parent = gui

local shake, flashA = 0, 0
local msgUntil, msgPrio = 0, 0
local holdUntil, holdCF = 0, nil
local function show(text, color, prio, dur)
	local now = os.clock()
	if now < msgUntil and prio < msgPrio then return end   -- wichtigere Meldung nicht sofort ueberschreiben
	msg.Text = text; msg.TextColor3 = color; msgUntil = now + (dur or 0.6); msgPrio = prio
end
local function grounded()
	local c = player.Character
	return c and (c:GetAttribute("CC_Wrestle") or c:GetAttribute("CC_Down"))
end

fx.OnClientEvent:Connect(function(strength, kind)
	if kind == "hit" or kind == "stagger" or kind == "ko" or kind == "knockdown" then
		flashA = math.max(flashA, (player:GetAttribute("CC_ReduceFX") and 0.08 or 0.25 + 0.35 * strength))   -- Einstellung: starke Effekte aus = nur schwacher Blitz
		if strength >= 0.4 and not player:GetAttribute("CC_NoShake") then shake = math.max(shake, strength) end   -- nur schwere Treffer ruckeln
		if kind == "knockdown" then show("KNOCKDOWN!", Color3.fromRGB(255, 196, 46), 5, 1.1) end
	elseif kind == "land" then
		local heavy = strength >= 0.3
		show(heavy and "SCHWERER TREFFER" or "TREFFER", heavy and Color3.fromRGB(255, 170, 60) or Color3.new(1, 1, 1), heavy and 2 or 1)
		if heavy then holdUntil = os.clock() + 0.06; holdCF = nil end
	elseif kind == "block" and not grounded() then
		show("GEBLOCKT", Color3.fromRGB(120, 190, 255), 2)
	end
end)

-- Hinweise vom Server am Charakter
local function watch(char)
	char:GetAttributeChangedSignal("CC_Tired"):Connect(function() show("ZU WENIG AUSDAUER", Color3.fromRGB(255, 90, 70), 3, 0.9) end)
	char:GetAttributeChangedSignal("CC_OutOfRange"):Connect(function() show("ZU WEIT WEG", Color3.fromRGB(220, 220, 225), 0, 0.7) end)
	char:GetAttributeChangedSignal("CC_SigDenied"):Connect(function()   -- Signatur abgelehnt (Server)
		local why = tostring(char:GetAttribute("CC_SigDenied")):match("^(%a+)")
		local txt = ({ focus = "FOKUS NOCH NICHT VOLL", position = "NICHT IN POSITION", anim = "SIGNATUR NICHT VERFÜGBAR" })[why]
		if txt then show(txt, Color3.fromRGB(220, 220, 225), 1, 0.8) end
	end)
end
player:GetAttributeChangedSignal("CC_SigLearned"):Connect(function()   -- Uebung beim Trainer bestanden
	show("SIGNATUR FREIGESCHALTET!", Color3.fromRGB(255, 200, 80), 4, 2.0)
end)
if player.Character then watch(player.Character) end
player.CharacterAdded:Connect(watch)

RunService:BindToRenderStep("CC_HitShake", Enum.RenderPriority.Camera.Value + 1, function(dt)
	local cam = workspace.CurrentCamera
	local now = os.clock()
	if now < holdUntil then
		holdCF = holdCF or cam.CFrame          -- Hitstop: Kamera haelt fuer wenige Frames an (nur lokal)
		cam.CFrame = holdCF
	end
	if shake > 0.001 then
		local a = shake * 0.02
		local t = now * 60
		cam.CFrame = cam.CFrame * CFrame.Angles(math.sin(t * 1.3) * a, math.cos(t * 1.7) * a, math.sin(t * 2.1) * a * 0.5)
		shake = shake * math.exp(-dt * 16)
	else
		shake = 0
	end
	flashA = flashA * math.exp(-dt * 9)
	flash.BackgroundTransparency = 1 - flashA
	local left = msgUntil - now
	msg.TextTransparency = left > 0.2 and 0 or math.clamp(1 - left / 0.2, 0, 1)
	msg.TextStrokeTransparency = 0.2 + 0.8 * msg.TextTransparency
end)
