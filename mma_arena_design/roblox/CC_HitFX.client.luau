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
-- Funken und Staub am Gegner bei schweren Treffern (rein lokal, verschwinden nach einer Sekunde)
local Players = game:GetService("Players")
local Debris = game:GetService("Debris")
local function opponentRoot()
	local c = player.Character
	local name = c and c:GetAttribute("CC_Opponent")
	local foe = name and (workspace:FindFirstChild(name) or (Players:FindFirstChild(name) and Players[name].Character))
	return foe and foe:FindFirstChild("HumanoidRootPart")
end
local function sparks(strength)
	local root = opponentRoot()
	if not root or player:GetAttribute("CC_ReduceFX") then return end
	local anchor = Instance.new("Part")
	anchor.Anchored = true; anchor.CanCollide = false; anchor.CanQuery = false; anchor.CanTouch = false
	anchor.Transparency = 1; anchor.Size = Vector3.new(0.2, 0.2, 0.2)
	local me = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	local toMe = me and (me.Position - root.Position) * Vector3.new(1, 0, 1)
	anchor.CFrame = CFrame.new(root.Position + Vector3.new(0, 1.2, 0) + ((toMe and toMe.Magnitude > 0.1) and toMe.Unit * 0.9 or Vector3.zero))
	anchor.Parent = workspace
	local spark = Instance.new("ParticleEmitter")
	spark.Texture = "rbxasset://textures/particles/sparkles_main.dds"
	spark.Color = ColorSequence.new(Color3.fromRGB(255, 230, 150), Color3.fromRGB(255, 120, 40))
	spark.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.7), NumberSequenceKeypoint.new(1, 0) })
	spark.Lifetime = NumberRange.new(0.25, 0.45)
	spark.Speed = NumberRange.new(8 + 8 * strength, 14 + 10 * strength)
	spark.SpreadAngle = Vector2.new(180, 180)
	spark.LightEmission = 1
	spark.Parent = anchor
	spark:Emit(math.floor(24 + 26 * strength))
	local dust = spark:Clone()
	dust.Color = ColorSequence.new(Color3.fromRGB(200, 196, 190))
	dust.Speed = NumberRange.new(2, 4); dust.Lifetime = NumberRange.new(0.6, 0.9)
	dust.Size = NumberSequence.new(1.2, 3.0); dust.LightEmission = 0; dust.Transparency = NumberSequence.new(0.4, 1)
	dust.Parent = anchor
	dust:Emit(6)
	Debris:AddItem(anchor, 1.2)
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
		show(heavy and "HEAVY HIT" or "HIT", heavy and Color3.fromRGB(255, 170, 60) or Color3.new(1, 1, 1), heavy and 2 or 1)
		if heavy then
			holdUntil = os.clock() + 0.04 + 0.06 * math.min(1, strength); holdCF = nil   -- staerkerer Treffer = laenger Halt
			sparks(math.min(1, strength))
		end
	elseif kind == "block" and not grounded() then
		show("BLOCKED", Color3.fromRGB(120, 190, 255), 2)
	end
end)

-- K.o. / Submission / T.K.O. im eigenen Kampf (ReplicatedStorage.CC_MatchState.Stoppage): kurzer Blitz, Farbe raus, Unschaerfe, dann zurueck
do
	local Lighting, TweenService = game:GetService("Lighting"), game:GetService("TweenService")
	local mirror = game.ReplicatedStorage:WaitForChild("CC_MatchState")
	local white = Instance.new("Frame"); white.Size = UDim2.fromScale(1, 1); white.BackgroundColor3 = Color3.new(1, 1, 1)
	white.BackgroundTransparency = 1; white.BorderSizePixel = 0; white.ZIndex = 3; white.Parent = gui
	mirror:GetAttributeChangedSignal("Stoppage"):Connect(function()
		local st = tostring(mirror:GetAttribute("Stoppage") or "")
		if st == "" or st == "Forfeit" then return end
		white.BackgroundTransparency = 0.25
		TweenService:Create(white, TweenInfo.new(0.35), { BackgroundTransparency = 1 }):Play()
		if player:GetAttribute("CC_ReduceFX") then return end
		local cc = Instance.new("ColorCorrectionEffect"); cc.Name = "CC_KOGrade"; cc.Saturation = -0.75; cc.Contrast = 0.25; cc.Parent = Lighting
		local blur = Instance.new("BlurEffect"); blur.Name = "CC_KOBlur"; blur.Size = 10; blur.Parent = Lighting
		shake = math.max(shake, 1)
		task.delay(0.9, function()
			TweenService:Create(cc, TweenInfo.new(1.4), { Saturation = 0, Contrast = 0 }):Play()
			TweenService:Create(blur, TweenInfo.new(1.0), { Size = 0 }):Play()
			task.delay(1.5, function() cc:Destroy(); blur:Destroy() end)
		end)
	end)
end

-- Hinweise vom Server am Charakter
local function watch(char)
	char:GetAttributeChangedSignal("CC_Tired"):Connect(function() show("NOT ENOUGH STAMINA", Color3.fromRGB(255, 90, 70), 3, 0.9) end)
	char:GetAttributeChangedSignal("CC_OutOfRange"):Connect(function() show("TOO FAR", Color3.fromRGB(220, 220, 225), 0, 0.7) end)
	char:GetAttributeChangedSignal("CC_SigDenied"):Connect(function()   -- Signatur abgelehnt (Server)
		local why = tostring(char:GetAttribute("CC_SigDenied")):match("^(%a+)")
		local txt = ({ focus = "FOCUS NOT FULL YET", position = "NOT IN POSITION", anim = "SIGNATURE NOT AVAILABLE" })[why]
		if txt then show(txt, Color3.fromRGB(220, 220, 225), 1, 0.8) end
	end)
end
player:GetAttributeChangedSignal("CC_SigLearned"):Connect(function()   -- Uebung beim Trainer bestanden
	show("SIGNATURE UNLOCKED!", Color3.fromRGB(255, 200, 80), 4, 2.0)
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
