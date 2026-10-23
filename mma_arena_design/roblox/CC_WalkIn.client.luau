-- ReplicatedFirst.CC_WalkIn_Client (LocalScript) – Ladefilm "The Walk to the Cage"
-- Ersetzt den alten Ladebildschirm (ReplicatedFirst.CC_LoadingScreen, gesichert in ServerStorage).
-- Warum ReplicatedFirst: nur dessen Inhalte sind garantiert vor der Hauptwelt beim Spieler. Szene, Kaempfer, Coach und
-- Animationen liegen in ReplicatedFirst.CC_WalkIn (build_walkin_scene_v01.luau). Die Szene wird lokal weit abseits der Map
-- aufgebaut, mit eigener Scriptable-Kamera; die Hauptwelt wird nicht vorgeladen.
-- Ablauf: 1) sofort dunkler Hintergrund mit Logo  2) sobald Rig und Animationen bereit: Ueberblendung in den Tunnel, Kaempfer
-- (gespeichertes Aussehen, sonst Standard) geht mit Coach zur Kaefigtuer  3) Warteanimation, bis das Spiel wirklich bereit ist
-- 4) Tuer oeffnet, Licht faellt herein, Kaempfer geht los  5) Abblende, Uebergabe an Menue/Einstieg (kein Kampfstart).
-- Bereit = Kaempfer da + Profil geladen (CC_Level) + Welt geladen + Arena da + Menue fertig (CC_BootDone, CC_MainMenu).
-- Sicherheit: harte Zeitgrenze, Fehler oder fehlende Assets -> schlichte Logo-Ansicht; alles wird am Ende aufgeraeumt.
local Players = game:GetService("Players")
local RF = game:GetService("ReplicatedFirst")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local ContentProvider = game:GetService("ContentProvider")
local CAS = game:GetService("ContextActionService")
local UIS = game:GetService("UserInputService")
local Lighting = game:GetService("Lighting")
local KSP = game:GetService("KeyframeSequenceProvider")

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")
if playerGui:FindFirstChild("CC_WalkInGui") then return end

local HARD_LIMIT = 45                -- Sekunden: spaetestens dann ins Spiel
local BASE = CFrame.new(0, 2500, 8000)
local t0 = os.clock()
-- Nur Studio: workspace-Attribute zum Testen. CC_WalkInDelay = Sekunden kuenstliche Verzoegerung von "bereit",
-- Attribut TestBreak = true an ReplicatedFirst.CC_WalkIn simuliert ein fehlendes Asset (-> schlichte Logo-Ansicht). Protokoll in _G.CC_WalkInLog.
local STUDIO = RunService:IsStudio()
local function testDelay() return STUDIO and tonumber(workspace:GetAttribute("CC_WalkInDelay")) or 0 end
-- TestBreak sitzt am Asset-Ordner, weil workspace-Attribute beim Start noch nicht repliziert sind.
local function testBreak() local a = RF:FindFirstChild("CC_WalkIn"); return STUDIO and a ~= nil and a:GetAttribute("TestBreak") == true end
local function log(msg)
	if not STUDIO then return end
	player:SetAttribute("CC_WalkInLog", (player:GetAttribute("CC_WalkInLog") or "") .. ("%.1f %s | "):format(os.clock() - t0, msg))
end
local conns, tracks = {}, {}
local finished, skipFlag = false, false

------------------------------------------------------------------ Oberflaeche (sofort)
local C = { bg = Color3.fromRGB(13, 14, 17), red = Color3.fromRGB(224, 36, 54), text = Color3.fromRGB(238, 238, 242), dim = Color3.fromRGB(150, 153, 164), track = Color3.fromRGB(46, 48, 56) }
local gui = Instance.new("ScreenGui")
gui.Name = "CC_WalkInGui"; gui.IgnoreGuiInset = true; gui.ResetOnSpawn = false; gui.DisplayOrder = 10000; gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
local cover = Instance.new("Frame"); cover.Name = "Cover"; cover.Size = UDim2.fromScale(1, 1); cover.BackgroundColor3 = C.bg; cover.BorderSizePixel = 0; cover.ZIndex = 1; cover.Parent = gui
local assets = RF:FindFirstChild("CC_WalkIn") or RF:WaitForChild("CC_WalkIn", 3)
local logo = Instance.new("ImageLabel"); logo.Name = "Logo"; logo.BackgroundTransparency = 1; logo.AnchorPoint = Vector2.new(0.5, 0.5)
logo.Position = UDim2.fromScale(0.5, 0.45); logo.Size = UDim2.fromOffset(420, 210); logo.ScaleType = Enum.ScaleType.Fit; logo.ZIndex = 5
logo.Image = assets and assets:GetAttribute("Logo") or ""; logo.Parent = gui
local status = Instance.new("TextLabel"); status.BackgroundTransparency = 1; status.AnchorPoint = Vector2.new(0.5, 1); status.Position = UDim2.new(0.5, 0, 1, -44)
status.Size = UDim2.fromOffset(520, 20); status.Font = Enum.Font.GothamMedium; status.TextSize = 14; status.TextColor3 = C.dim; status.Text = "Preparing your fighter"; status.ZIndex = 5; status.Parent = gui
local track = Instance.new("Frame"); track.AnchorPoint = Vector2.new(0.5, 1); track.Position = UDim2.new(0.5, 0, 1, -30); track.Size = UDim2.fromOffset(520, 3)
track.BackgroundColor3 = C.track; track.BorderSizePixel = 0; track.ZIndex = 5; track.Parent = gui
local fill = Instance.new("Frame"); fill.Size = UDim2.fromScale(0, 1); fill.BackgroundColor3 = C.red; fill.BorderSizePixel = 0; fill.ZIndex = 6; fill.Parent = track
local skipHint = Instance.new("TextLabel"); skipHint.BackgroundTransparency = 1; skipHint.AnchorPoint = Vector2.new(1, 1); skipHint.Position = UDim2.new(1, -28, 1, -26)
skipHint.Size = UDim2.fromOffset(260, 18); skipHint.Font = Enum.Font.GothamMedium; skipHint.TextSize = 13; skipHint.TextColor3 = C.dim; skipHint.TextXAlignment = Enum.TextXAlignment.Right
skipHint.Text = "SPACE / CLICK  ·  ENTER NOW"; skipHint.TextTransparency = 1; skipHint.ZIndex = 5; skipHint.Parent = gui
local black = Instance.new("Frame"); black.Size = UDim2.fromScale(1, 1); black.BackgroundColor3 = Color3.new(0, 0, 0); black.BackgroundTransparency = 1; black.BorderSizePixel = 0; black.ZIndex = 20; black.Parent = gui
gui.Parent = playerGui
pcall(function() RF:RemoveDefaultLoadingScreen() end)
if logo.Image ~= "" then task.spawn(function() pcall(function() ContentProvider:PreloadAsync({ logo }) end) end) end

local function tween(obj, t, props, style)
	local tw = TweenService:Create(obj, TweenInfo.new(t, style or Enum.EasingStyle.Quad, Enum.EasingDirection.InOut), props); tw:Play(); return tw
end
local function reduceMotion() return player:GetAttribute("CC_ReduceMotion") == true or player:GetAttribute("CC_ReduceFX") == true end

------------------------------------------------------------------ echter Ladezustand
local progress, ready = 0, false
local function setStage(frac, text)
	if frac <= progress then return end
	progress = frac; status.Text = text
	tween(fill, 0.35, { Size = UDim2.fromScale(frac, 1) })
end
task.spawn(function()
	-- 1) Kaempfer und Profil
	local char = player.Character or player.CharacterAdded:Wait()
	char:WaitForChild("HumanoidRootPart", 20)
	setStage(0.2, "Preparing your fighter")
	while player:GetAttribute("CC_Level") == nil and os.clock() - t0 < HARD_LIMIT do task.wait(0.1) end
	setStage(0.4, "Preparing the arena")
	-- 2) Welt und Arena
	if not game:IsLoaded() then game.Loaded:Wait() end
	setStage(0.6, "Preparing the arena")
	local tA = os.clock()
	while not workspace:FindFirstChild("CC_Arena") and os.clock() - tA < 15 and os.clock() - t0 < HARD_LIMIT do task.wait(0.1) end
	setStage(0.8, "Preparing the arena")
	-- 3) Menue und Einstieg fertig (CC_MainMenu setzt CC_BootDone)
	while player:GetAttribute("CC_BootDone") ~= true and os.clock() - t0 < HARD_LIMIT do task.wait(0.1) end
	while os.clock() - t0 < testDelay() and os.clock() - t0 < HARD_LIMIT do task.wait(0.1) end
	setStage(1, "Ready to enter")
	ready = true; log("ready")
end)
task.delay(HARD_LIMIT, function() if not ready then ready = true; status.Text = "Ready to enter" end end)
-- Nur Studio: CC_WalkInForceReady = Sekunden -> "bereit" erzwingen (Test "sehr schnelles Laden")
task.spawn(function()
	if not STUDIO then return end
	while not ready do
		local f = tonumber(workspace:GetAttribute("CC_WalkInForceReady"))
		if f and os.clock() - t0 >= f then setStage(1, "Ready to enter"); ready = true; log("ready (test)") end
		task.wait(0.1)
	end
end)

------------------------------------------------------------------ Szene vorbereiten (bei Fehler: nur Logo)
local runtime, scene, fighter, coach
local anim = {}
local savedLight, hiddenGuis = nil, {}
local crowd, crowdEq, spillLight, door, doorParts = nil, nil, nil, nil, {}

local function animFor(names)
	local folder = assets and assets:FindFirstChild("Anims")
	if not folder then return nil end
	for _, n in ipairs(names) do
		local a = folder:FindFirstChild(n)
		if a and a:IsA("Animation") then return a, n end
		local ks = folder:FindFirstChild(n .. "_KS")
		if ks and RunService:IsStudio() then
			local ok, id = pcall(function() return KSP:RegisterKeyframeSequence(ks) end)
			if ok then local x = Instance.new("Animation"); x.AnimationId = id; return x, n end
		end
	end
	return nil
end

local function applyLook()
	-- gespeichertes Aussehen, sobald Profil und Vorlagen da sind (kurz, sonst Standard)
	local RS = game:GetService("ReplicatedStorage")
	local raw = player:GetAttribute("CC_Look")
	local lookMod, tpl = RS:FindFirstChild("CC_LookShared"), RS:FindFirstChild("CC_CustomShared")
	if not (raw and lookMod and tpl) then return false end
	return pcall(function()
		local Look = require(lookMod)
		local look = game:GetService("HttpService"):JSONDecode(raw)
		Look.apply(fighter, Look.sanitize(look), tpl)
	end)
end

local function setupScene()
	if not assets or testBreak() then return false, "assets fehlen" end
	local sc, fi, co = assets:FindFirstChild("Scene"), assets:FindFirstChild("Fighter"), assets:FindFirstChild("Coach")
	if not (sc and fi) then return false, "Szene oder Kaempfer fehlen" end
	runtime = Instance.new("Folder"); runtime.Name = "CC_WalkInRuntime"
	scene = sc:Clone(); scene:PivotTo(BASE * scene:GetPivot()); scene.Parent = runtime
	fighter = fi:Clone(); fighter.Parent = runtime
	coach = co and co:Clone() or nil
	if coach then coach.Parent = runtime end
	runtime.Parent = workspace
	door = scene:FindFirstChild("CageDoor")
	for _, p in ipairs(scene:GetChildren()) do if p:GetAttribute("CC_DoorPart") then table.insert(doorParts, { part = p, cf = p.CFrame }) end end
	local spill = scene:FindFirstChild("DoorSpill"); spillLight = spill and spill:FindFirstChild("Spill")
	local startZ, stopZ = assets:GetAttribute("StartZ") or -24, assets:GetAttribute("StopZ") or -61
	fighter.HumanoidRootPart.CFrame = BASE * CFrame.new(0, 3, startZ) * CFrame.Angles(0, 0, 0)
	if coach then coach.HumanoidRootPart.CFrame = BASE * CFrame.new(-3.2, 3, startZ + 0.4) end
	log("setup start")
	local lookDone = false
	task.spawn(function()                     -- parallel; Ergebnis zaehlt nur bis zur Ueberblendung (kein sichtbarer Wechsel)
		local tL = os.clock()
		local RS = game:GetService("ReplicatedStorage")
		while not (player:GetAttribute("CC_Look") and RS:FindFirstChild("CC_LookShared") and RS:FindFirstChild("CC_CustomShared")) and os.clock() - tL < 30 and not finished do task.wait(0.1) end
		if not finished and fighter and fighter.Parent then applyLook(); log("look applied") end
		lookDone = true
	end)
	-- Animationen: Walkout/Warten wenn vorhanden, sonst normales Gehen/Stehen
	local wA, wName = animFor({ "Fighter_Walkout", "Fighter_CasualWalk_v2" })
	local iA = animFor({ "Fighter_TunnelWait", "Fighter_CasualIdle_v01" })
	local cwA = animFor({ "Fighter_CasualWalk_v2" })
	local ciA = animFor({ "Fighter_CasualIdle_v01" })
	if not (wA and iA) then return false, "Animationen fehlen" end
	anim.speed = assets:GetAttribute("Speed_" .. wName) or 6.41
	-- nur hochgeladene Animationen vorladen (Studio-Ersatz ist sofort da), hoechstens 3 s
	local list = {}
	for _, a in ipairs({ wA, iA, cwA, ciA }) do if a and a.AnimationId:find("rbxassetid") then table.insert(list, a) end end
	if #list > 0 then task.spawn(function() pcall(function() ContentProvider:PreloadAsync(list) end) end) end
	local fa = fighter:FindFirstChildWhichIsA("Animator", true)
	anim.walk = fa:LoadAnimation(wA); anim.walk.Looped = true; anim.walk.Priority = Enum.AnimationPriority.Movement
	anim.wait = fa:LoadAnimation(iA); anim.wait.Looped = true; anim.wait.Priority = Enum.AnimationPriority.Idle
	table.insert(tracks, anim.walk); table.insert(tracks, anim.wait)
	if coach and cwA and ciA then
		local ca = coach:FindFirstChildWhichIsA("Animator", true)
		anim.cWalk = ca:LoadAnimation(cwA); anim.cWalk.Looped = true; anim.cWalk.Priority = Enum.AnimationPriority.Movement
		anim.cIdle = ca:LoadAnimation(ciA); anim.cIdle.Looped = true; anim.cIdle.Priority = Enum.AnimationPriority.Idle
		table.insert(tracks, anim.cWalk); table.insert(tracks, anim.cIdle)
	elseif coach then coach:Destroy(); coach = nil end
	-- Animation erst zeigen, wenn sie wirklich geladen ist (keine T-Pose)
	anim.walk:Play(0); anim.wait:Play(0, 0.001)
	if anim.cWalk then anim.cWalk:Play(0); anim.cIdle:Play(0, 0.001) end
	local tW = os.clock()
	while (anim.walk.Length == 0 or anim.wait.Length == 0) and os.clock() - tW < 6 do task.wait(0.05) end
	log("tracks")
	if anim.walk.Length == 0 or anim.wait.Length == 0 then return false, "Animation nicht ladbar" end
	if anim.cWalk then anim.cWalk:AdjustSpeed(anim.speed / ((assets:GetAttribute("Speed_Fighter_CasualWalk_v2")) or 6.41)) end
	if testBreak() then return false, "assets fehlen (Test)" end
	anim.startZ, anim.stopZ = startZ, stopZ
	return true
end

local LIGHT = { ClockTime = 0, Brightness = 0, Ambient = Color3.fromRGB(56, 56, 62), OutdoorAmbient = Color3.fromRGB(44, 44, 50),
	EnvironmentDiffuseScale = 0.25, EnvironmentSpecularScale = 0.3, FogEnd = 100000, ExposureCompensation = 0 }
local function enforceLight()
	if not savedLight then return end
	for k, v in pairs(LIGHT) do if Lighting[k] ~= v then pcall(function() Lighting[k] = v end) end end
	for _, e in ipairs(Lighting:GetChildren()) do
		if e:IsA("PostEffect") and e.Name ~= "CC_WalkInGrade" and e.Enabled then
			if savedLight.fx[e] == nil then savedLight.fx[e] = true end
			e.Enabled = false
		elseif e:IsA("Atmosphere") or e:IsA("Sky") then table.insert(savedLight.moved, e); e.Parent = nil end
	end
end
local function lightOn()
	savedLight = { props = { ClockTime = Lighting.ClockTime, Brightness = Lighting.Brightness, Ambient = Lighting.Ambient, OutdoorAmbient = Lighting.OutdoorAmbient,
		EnvironmentDiffuseScale = Lighting.EnvironmentDiffuseScale, EnvironmentSpecularScale = Lighting.EnvironmentSpecularScale, FogEnd = Lighting.FogEnd, ExposureCompensation = Lighting.ExposureCompensation }, fx = {}, moved = {} }
	for _, e in ipairs(Lighting:GetChildren()) do if e:IsA("PostEffect") then savedLight.fx[e] = e.Enabled end end
	enforceLight()
	local cc = Instance.new("ColorCorrectionEffect"); cc.Name = "CC_WalkInGrade"; cc.Contrast = 0.12; cc.Saturation = -0.08; cc.TintColor = Color3.fromRGB(255, 246, 238); cc.Parent = Lighting
end
local function lightOff()
	if not savedLight then return end
	for k, v in pairs(savedLight.props) do pcall(function() Lighting[k] = v end) end
	for e, en in pairs(savedLight.fx) do if e.Parent then e.Enabled = en end end
	for _, e in ipairs(savedLight.moved) do e.Parent = Lighting end
	local cc = Lighting:FindFirstChild("CC_WalkInGrade"); if cc then cc:Destroy() end
	savedLight = nil
end

------------------------------------------------------------------ Abschluss (immer, auch bei Fehlern)
local function finish()
	if finished then return end
	finished = true; log("finish")
	pcall(function() RunService:UnbindFromRenderStep("CC_WalkInCam") end)
	pcall(function() CAS:UnbindAction("CC_WalkInBlock") end)
	for _, c in ipairs(conns) do c:Disconnect() end
	for _, t in ipairs(tracks) do pcall(function() t:Stop(0) end) end
	if crowd then crowd:Stop() end
	if runtime then runtime:Destroy(); runtime = nil end
	lightOff()
	for g in pairs(hiddenGuis) do if g.Parent then g.Enabled = true end end
	local cam = workspace.CurrentCamera
	cam.CameraType = Enum.CameraType.Custom; cam.FieldOfView = 70
	local hum = player.Character and player.Character:FindFirstChildOfClass("Humanoid"); if hum then cam.CameraSubject = hum end
	-- Schwarz ausblenden, Menue darunter ist fertig
	for _, x in ipairs({ logo, status, track, fill, skipHint }) do x.Visible = false end
	cover.BackgroundTransparency = 1
	tween(black, 0.6, { BackgroundTransparency = 1 }).Completed:Wait()
	gui:Destroy()
end
task.delay(HARD_LIMIT + 8, function() if not finished then pcall(finish) end end)   -- Notbremse: nie im Ladebildschirm haengen bleiben

------------------------------------------------------------------ Ablauf
local okScene, why = false, nil
local okRun, errRun = pcall(function()
	okScene, why = setupScene(); log("scene " .. tostring(okScene) .. " " .. tostring(why or ""))
	if not okScene then
		if runtime then runtime:Destroy(); runtime = nil end
		warn("[CC] Ladefilm: schlichte Ansicht (" .. tostring(why) .. ")")
		while not ready do task.wait(0.1) end
		tween(black, 0.5, { BackgroundTransparency = 0 }).Completed:Wait()
		return
	end

	-- Umgebung fuer den Film: Licht, andere Oberflaechen aus, Bewegung sperren, Publikum gedaempft
	lightOn()
	CAS:BindActionAtPriority("CC_WalkInBlock", function() return Enum.ContextActionResult.Sink end, false, 3000,
		Enum.PlayerActions.CharacterForward, Enum.PlayerActions.CharacterBackward, Enum.PlayerActions.CharacterLeft, Enum.PlayerActions.CharacterRight, Enum.PlayerActions.CharacterJump)
	task.spawn(function()
		local sfx = game:GetService("SoundService"):WaitForChild("CC_Sounds", 6)
		local src = sfx and sfx:FindFirstChild("Crowd")
		if not src or finished or not scene then return end
		local holder = Instance.new("Part"); holder.Anchored = true; holder.Transparency = 1; holder.CanCollide = false; holder.CanQuery = false; holder.CanTouch = false
		holder.Size = Vector3.new(1, 1, 1); holder.CFrame = BASE * CFrame.new(0, 6, (assets:GetAttribute("DoorZ") or -66) - 18); holder.Parent = runtime
		crowd = src:Clone(); crowd.Looped = true; crowd.RollOffMode = Enum.RollOffMode.InverseTapered; crowd.RollOffMinDistance = 30; crowd.RollOffMaxDistance = 140
		crowd.Volume = 0.9 * (player:GetAttribute("CC_MasterVolume") or 0.8) * (player:GetAttribute("CC_EffectsVolume") or 0.8)
		crowdEq = Instance.new("EqualizerSoundEffect"); crowdEq.HighGain = -28; crowdEq.MidGain = -10; crowdEq.LowGain = 0; crowdEq.Parent = crowd
		crowd.Parent = holder; crowd:Play()
	end)

	-- Kamera: ruhige Verfolgung hinter dem Kaempfer (Schulterhoehe, leicht rechts); bei "Reduce Motion" fest stehend
	local cam = workspace.CurrentCamera
	local camCF
	local back, side, up = 7.5, 2.2, 1.9
	local function desired()
		local r = fighter.HumanoidRootPart.CFrame
		if reduceMotion() then                -- Einstellung kommt mit dem Profil, auch waehrend des Films
			return CFrame.lookAt((BASE * CFrame.new(2.6, 6.2, anim.startZ + 7)).Position, (BASE * CFrame.new(0, 3.6, anim.stopZ - 4)).Position)
		end
		return CFrame.lookAt((r * CFrame.new(side, up, back)).Position, (r * CFrame.new(0, 1.2, -12)).Position)
	end
	camCF = desired()
	RunService:BindToRenderStep("CC_WalkInCam", Enum.RenderPriority.Last.Value + 70, function(dt)
		if finished then return end
		cam.CameraType = Enum.CameraType.Scriptable
		local goal = desired()
		camCF = camCF:Lerp(goal, 1 - math.exp(-dt * 3.5))
		cam.CFrame = camCF; cam.FieldOfView = 52
		enforceLight()
		for _, g in ipairs(playerGui:GetChildren()) do
			if g:IsA("ScreenGui") and g ~= gui and g.Enabled then hiddenGuis[g] = true; g.Enabled = false end
		end
	end)

	anim.shown = true
	-- Ueberblendung Logo -> Tunnel; Logo klein in die Ecke
	tween(cover, 0.8, { BackgroundTransparency = 1 })
	tween(logo, 0.8, { Size = UDim2.fromOffset(150, 75), Position = UDim2.new(0, 104, 0, 58) })

	table.insert(conns, UIS.InputBegan:Connect(function(input)
		if not ready then return end
		if input.KeyCode == Enum.KeyCode.Space or input.KeyCode == Enum.KeyCode.ButtonA or input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.Touch then skipFlag = true end
	end))
	task.spawn(function() while not ready and not finished do task.wait(0.1) end; if not finished then tween(skipHint, 0.4, { TextTransparency = 0 }) end end)

	-- Gang zur Tuer: Bewegung = Animationstempo (kein Gleiten)
	local root, cRoot = fighter.HumanoidRootPart, coach and coach.HumanoidRootPart
	local z = anim.startZ
	local doorZ = assets:GetAttribute("DoorZ") or -66
	local cutDone = false
	while z > anim.stopZ and not skipFlag do
		local dt = RunService.Heartbeat:Wait()
		-- Spiel frueh bereit: Filmschnitt kurz vor die Tuer statt den ganzen Weg abzuwarten
		if ready and not cutDone and z - anim.stopZ > 12 then
			cutDone = true; log("cut")
			tween(black, 0.25, { BackgroundTransparency = 0 }).Completed:Wait()
			z = anim.stopZ + 8
			root.CFrame = BASE * CFrame.new(0, 3, z)
			if cRoot then cRoot.CFrame = BASE * CFrame.new(-3.2, 3, z + 0.4) end
			camCF = desired()
			tween(black, 0.35, { BackgroundTransparency = 1 })
		end
		z = math.max(anim.stopZ, z - anim.speed * dt)
		root.CFrame = BASE * CFrame.new(0, 3, z)
		if cRoot then cRoot.CFrame = BASE * CFrame.new(-3.2, 3, math.max(anim.stopZ + 0.4, z + 0.4)) end
		if crowdEq then local u = math.clamp((anim.startZ - z) / (anim.startZ - anim.stopZ), 0, 1); crowdEq.HighGain = -28 + 14 * u end
	end
	log("arrived door")
	-- Halt vor der Tuer: weich in die Warteanimation
	anim.walk:AdjustWeight(0.001, 0.4); anim.wait:AdjustWeight(1, 0.4)
	if anim.cWalk then
		anim.cWalk:AdjustWeight(0.001, 0.4); anim.cIdle:AdjustWeight(1, 0.4)
		local cp = cRoot.Position
		cRoot.CFrame = CFrame.lookAt(cp, Vector3.new(root.Position.X, cp.Y, root.Position.Z))   -- Coach dreht sich zum Kaempfer
	end
	back = 6.2; up = 1.6
	while not ready and not skipFlag do task.wait(0.1) end      -- Warteschleife darf auf langsamen Geraeten laenger laufen
	if skipFlag then tween(black, 0.35, { BackgroundTransparency = 0 }).Completed:Wait(); return end

	log("door open")
	-- Tuer oeffnet, Licht faellt herein, Kaempfer geht los
	local hinge = door and door:GetAttribute("CC_Hinge")
	if hinge then
		local h = BASE * CFrame.new(hinge)
		local v = Instance.new("NumberValue")
		v.Changed:Connect(function(a) for _, d in ipairs(doorParts) do d.part.CFrame = h * CFrame.Angles(0, math.rad(a), 0) * h:Inverse() * d.cf end end)
		tween(v, 1.3, { Value = 105 }, Enum.EasingStyle.Sine)          -- oeffnet in den Kaefig hinein
	end
	if spillLight then tween(spillLight, 1.2, { Brightness = 4.5 }) end
	if crowdEq then tween(crowdEq, 1.2, { HighGain = 0, MidGain = 0 }) end
	if crowd then tween(crowd, 1.2, { Volume = crowd.Volume * 1.5 }) end
	task.wait(0.7)
	anim.wait:AdjustWeight(0.001, 0.3); anim.walk:AdjustWeight(1, 0.3)
	local tGo = os.clock()
	back = 8.5
	while os.clock() - tGo < 2.0 and not skipFlag do
		local dt = RunService.Heartbeat:Wait()
		z = math.max(doorZ - 6, z - anim.speed * dt)
		root.CFrame = BASE * CFrame.new(0, 3, z)
	end
	tween(black, 0.6, { BackgroundTransparency = 0 }).Completed:Wait()
end)
if not okRun then warn("[CC] Ladefilm-Fehler: " .. tostring(errRun)); tween(black, 0.3, { BackgroundTransparency = 0 }).Completed:Wait() end
-- Uebergabe erst, wenn das Spiel wirklich bereit ist
while not ready do task.wait(0.1) end
finish()
