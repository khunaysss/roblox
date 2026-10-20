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
-- Schweiss vom Kopf des Gegners bei harten Treffern: kleine helle Tropfen, weg vom Angreifer, fallen nach unten (nur lokal)
local function opponentChar()
	local c = player.Character
	local name = c and c:GetAttribute("CC_Opponent")
	return name and (workspace:FindFirstChild(name) or (Players:FindFirstChild(name) and Players[name].Character)) or nil
end
local function sweat(strength)
	local foe = opponentChar()
	local root = foe and foe:FindFirstChild("HumanoidRootPart")
	if not root or player:GetAttribute("CC_ReduceFX") then return end
	local head = foe:FindFirstChild("Head", true)
	local pos = head and (head:IsA("Bone") and head.TransformedWorldCFrame.Position or head:IsA("BasePart") and head.Position) or root.Position + Vector3.new(0, 1.6, 0)
	local me = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	local away = me and (root.Position - me.Position) * Vector3.new(1, 0, 1)
	away = (away and away.Magnitude > 0.1) and away.Unit or root.CFrame.LookVector * -1
	local anchor = Instance.new("Part")
	anchor.Anchored = true; anchor.CanCollide = false; anchor.CanQuery = false; anchor.CanTouch = false
	anchor.Transparency = 1; anchor.Size = Vector3.new(0.2, 0.2, 0.2)
	anchor.CFrame = CFrame.lookAt(pos, pos + away + Vector3.new(0, 0.35, 0))
	anchor.Parent = workspace
	local drops = Instance.new("ParticleEmitter")
	drops.Texture = "rbxasset://textures/particles/smoke_main.dds"          -- runde, weiche Tropfen (Standard waere ein Stern)
	drops.EmissionDirection = Enum.NormalId.Front
	drops.Color = ColorSequence.new(Color3.fromRGB(235, 240, 245))
	drops.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.25), NumberSequenceKeypoint.new(1, 1) })
	drops.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.24), NumberSequenceKeypoint.new(1, 0.1) })
	drops.Lifetime = NumberRange.new(0.35, 0.6)
	drops.Speed = NumberRange.new(6 + 6 * strength, 10 + 8 * strength)
	drops.SpreadAngle = Vector2.new(28, 28)
	drops.Acceleration = Vector3.new(0, -40, 0)
	drops.Drag = 2
	drops.LightEmission = 0
	drops.Parent = anchor
	drops:Emit(math.floor(14 + 18 * strength))
	Debris:AddItem(anchor, 1)
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
			sweat(math.min(1, strength))
		end
	elseif kind == "block" and not grounded() then
		show("BLOCKED", Color3.fromRGB(120, 190, 255), 2)
	end
end)

-- K.o. / Submission / T.K.O. im eigenen Kampf (ReplicatedStorage.CC_MatchState.Stoppage): TV-Schnitt in Zeitlupe.
-- Kamera springt in einen tiefen Seitenwinkel auf den Verlierer, beide Kaempfer laufen ~1,5 s mit 30 % Tempo (nur lokal), dann zurueck.
do
	local mirror = game.ReplicatedStorage:WaitForChild("CC_MatchState")
	local function fighters()
		local list = {}
		for _, p in ipairs(Players:GetPlayers()) do
			local c = p.Character
			if c and c:GetAttribute("CC_MatchId") and c:GetAttribute("CC_MatchId") == (player.Character and player.Character:GetAttribute("CC_MatchId")) then table.insert(list, c) end
		end
		local d = workspace:FindFirstChild("CC_TrainingDummy")
		if d and player.Character and d:GetAttribute("CC_MatchId") == player.Character:GetAttribute("CC_MatchId") then table.insert(list, d) end
		return list
	end
	mirror:GetAttributeChangedSignal("Stoppage"):Connect(function()
		local st = tostring(mirror:GetAttribute("Stoppage") or "")
		if st == "" or st == "Forfeit" then return end
		local list = fighters()
		local loser
		for _, c in ipairs(list) do if c:GetAttribute("CC_KO") or c:GetAttribute("CC_Down") then loser = c end end
		loser = loser or opponentChar() or list[1]
		local lr = loser and loser:FindFirstChild("HumanoidRootPart")
		if not lr then return end
		local tracks = {}
		for _, c in ipairs(list) do
			local an = c:FindFirstChildWhichIsA("Animator", true)
			if an then for _, t in ipairs(an:GetPlayingAnimationTracks()) do table.insert(tracks, { t, t.Speed }); t:AdjustSpeed(t.Speed * 0.3) end end
		end
		local cam = workspace.CurrentCamera
		local side = lr.CFrame.RightVector
		-- Seite ohne Ringrichter waehlen (er soll nicht vor der Kamera stehen)
		local refs = workspace:FindFirstChild("CC_Referees")
		for _, r in ipairs(refs and refs:GetChildren() or {}) do
			local rp = r:IsA("Model") and r.PrimaryPart
			if rp and (rp.Position - (lr.Position + side * 8)).Magnitude < (rp.Position - (lr.Position - side * 8)).Magnitude then side = -side end
		end
		local t0 = os.clock()
		RunService:BindToRenderStep("CC_KOReplay", Enum.RenderPriority.Last.Value + 40, function()
			local u = os.clock() - t0
			local focus = lr.Position + Vector3.new(0, 0.4, 0)
			cam.CameraType = Enum.CameraType.Scriptable
			cam.CFrame = CFrame.lookAt(focus + side * (14 - u * 1.2) + Vector3.new(0, 1.2, 0) + lr.CFrame.LookVector * 3, focus)   -- ganzer Kaempfer im Bild, langsame Fahrt
			cam.FieldOfView = 38
		end)
		task.delay(1.5, function()
			pcall(function() RunService:UnbindFromRenderStep("CC_KOReplay") end)
			for _, e in ipairs(tracks) do pcall(function() e[1]:AdjustSpeed(e[2]) end) end
			cam.CameraType = Enum.CameraType.Custom; cam.FieldOfView = 70
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
