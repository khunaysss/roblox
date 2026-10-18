-- StarterPlayer.StarterPlayerScripts.CC_Story
-- Story-Einstieg "Der erste Schritt" (Szenen 1-9) als Film, komplett lokal beim Spieler (eigene Darsteller-Kopien, keine
-- Ueberschneidung mit anderen Spielern). Start: Server setzt CC_OnbPhase = "story" (neuer Spieler nach dem Editor) oder
-- RemoteEvent CC_Story "play" (Wiederholung aus den Einstellungen). Ende/Ueberspringen -> CC_Story "done" an den Server.
-- Darsteller: ReplicatedStorage.CC_StoryShared.ActorBase (Kopie des Kaempfers) + Aussehen (CC_LookShared) + Kleidung (Outfit).
-- Animationen: CC_StoryShared.AnimIds (hochgeladen) oder KeyframeSequences in CC_StoryShared.Anims (nur Studio).
-- Waehrend des Films: Steuerung aus (CC_UIBlock), andere Oberflaechen aus, eigene Kamera (hoechste Prioritaet), eigenes Licht.
-- Danach wird alles exakt wiederhergestellt (Kamera, FOV, Oberflaechen, Licht, Effekte).
local Players, RS, RunService = game:GetService("Players"), game:GetService("ReplicatedStorage"), game:GetService("RunService")
local TweenService, UIS, KSP, Lighting = game:GetService("TweenService"), game:GetService("UserInputService"), game:GetService("KeyframeSequenceProvider"), game:GetService("Lighting")
local player = Players.LocalPlayer
local SH = RS:WaitForChild("CC_StoryShared")
local Look = require(RS:WaitForChild("CC_LookShared"))
local UI = require(RS:WaitForChild("CC_UI"))
local remote = RS:WaitForChild("CC_Story")
local IDS = SH:FindFirstChild("AnimIds") and require(SH.AnimIds) or {}
local HS = game:GetService("HttpService")

local O = CFrame.new(-600, 0, 600)                  -- Schule (Tormitte), build_story_school_v01
local M2S = 1 / 0.28                                -- Meter -> Studs
local WALK = 6.43                                   -- Studs/s = Schritttempo Fighter_CasualWalk_v2
local GROUND = 0.46
local HRP_Y = 3.0
local function W(x, z, y) return (O * CFrame.new(x, (y or GROUND) + HRP_Y, z)).Position end
local function WP(x, y, z) return (O * CFrame.new(x, y, z)).Position end

local running, skipFlag = false, false
local actors, props, conns = {}, {}, {}

---------------------------------------------------------------------------------------------------- Darsteller
local function animOf(name)
	local a = Instance.new("Animation")
	if IDS[name] then a.AnimationId = "rbxassetid://" .. IDS[name]
	elseif SH.Anims:FindFirstChild(name) then a.AnimationId = KSP:RegisterKeyframeSequence(SH.Anims[name])
	else warn("[Story] Animation fehlt: " .. name); return nil end
	return a
end
local function makeActor(name, look, outfit, cf)
	local c = SH.ActorBase:Clone(); c.Name = "Story_" .. name
	for _, n in ipairs({ "Fighter_Gloves", "Fighter_Shorts" }) do local x = c:FindFirstChild(n); if x then x.Transparency = 1 end end
	local hum = c:FindFirstChildOfClass("Humanoid"); hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	local hrp = c.HumanoidRootPart; hrp.Anchored = true
	for _, p in ipairs(c:GetDescendants()) do if p:IsA("BasePart") then p.CanCollide = false; p.CanQuery = false; p.CanTouch = false end end
	c.Parent = workspace
	Look.apply(c, look, RS:FindFirstChild("CC_CustomShared"))
	local skin = Look.SKIN[look.skin or 2]
	for pname, col in pairs(outfit) do
		local t = SH.Outfit:FindFirstChild(pname)
		if t then
			local p = t:Clone(); p.Massless = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
			p.Color = (col == "skin") and skin or col
			local mo = Instance.new("Motor6D"); mo.Part0 = hrp; mo.Part1 = p; mo.C0 = t:GetAttribute("CC_C0"); mo.Parent = p
			p.Parent = c
		end
	end
	hrp.CFrame = cf
	local animator = hum:FindFirstChildOfClass("Animator") or Instance.new("Animator", hum)
	local a = { model = c, hrp = hrp, animator = animator, tracks = {} }
	function a.track(n)
		if a.tracks[n] == nil then
			local an = animOf(n)
			a.tracks[n] = an and animator:LoadAnimation(an) or false
		end
		return a.tracks[n] or nil
	end
	function a.play(n, fade, looped, prio)
		local t = a.track(n); if not t then return nil end
		t.Looped = looped or false; t.Priority = prio or Enum.AnimationPriority.Action
		t:Play(fade or 0.25); return t
	end
	function a.stop(n, fade) local t = a.tracks[n]; if t then t:Stop(fade or 0.25) end end
	local idle = a.play("Fighter_CasualIdle_v01", 0, true, Enum.AnimationPriority.Idle)
	table.insert(actors, a)
	return a
end
local function bone(a, name) return a.model:FindFirstChild(name, true) end

---------------------------------------------------------------------------------------------------- Steuerung des Ablaufs
local function wait_(t)                                   -- false, wenn uebersprungen
	local t0 = os.clock()
	while os.clock() - t0 < t do if skipFlag or not running then return false end; RunService.Heartbeat:Wait() end
	return not skipFlag
end
local function walkTo(a, target, faceAt, speed)
	local start = a.hrp.Position
	local d = (target - start) * Vector3.new(1, 0, 1)
	if d.Magnitude < 0.05 then return end
	local dur = d.Magnitude / (speed or WALK)
	local w = a.play("Fighter_CasualWalk_v2", 0.25, true, Enum.AnimationPriority.Movement)
	local t0 = os.clock()
	while true do
		local u = math.min((os.clock() - t0) / dur, 1)
		local p = start + d * u
		a.hrp.CFrame = CFrame.lookAt(p, p + d.Unit)
		if u >= 1 or skipFlag or not running then break end
		RunService.Heartbeat:Wait()
	end
	if w then w:Stop(0.3) end
	if faceAt then
		local from = a.hrp.CFrame
		local to = CFrame.lookAt(a.hrp.Position, Vector3.new(faceAt.X, a.hrp.Position.Y, faceAt.Z))
		local t1 = os.clock()
		while os.clock() - t1 < 0.35 and running do
			local u = (os.clock() - t1) / 0.35; u = u * u * (3 - 2 * u)
			a.hrp.CFrame = from:Lerp(to, u); RunService.Heartbeat:Wait()
		end
		a.hrp.CFrame = to
	end
end
local function face(a, at) a.hrp.CFrame = CFrame.lookAt(a.hrp.Position, Vector3.new(at.X, a.hrp.Position.Y, at.Z)) end

---------------------------------------------------------------------------------------------------- Oberflaeche: Kinobalken, Untertitel, Ueberspringen, Blende
local gui, sub, card, black, skipBtn
local function buildGui()
	gui = Instance.new("ScreenGui"); gui.Name = "CC_StoryGui"; gui.IgnoreGuiInset = true; gui.DisplayOrder = 60; gui.ResetOnSpawn = false
	for _, top in ipairs({ true, false }) do
		local b = Instance.new("Frame"); b.BackgroundColor3 = Color3.new(0, 0, 0); b.BorderSizePixel = 0; b.Size = UDim2.new(1, 0, 0.09, 0)
		b.Position = UDim2.fromScale(0, top and 0 or 0.91); b.Parent = gui
	end
	sub = Instance.new("TextLabel"); sub.BackgroundTransparency = 1; sub.AnchorPoint = Vector2.new(0.5, 1); sub.Position = UDim2.new(0.5, 0, 0.885, 0)
	sub.Size = UDim2.new(0.72, 0, 0, 64); sub.Font = Enum.Font.GothamMedium; sub.TextSize = 26; sub.TextWrapped = true; sub.RichText = true
	sub.TextColor3 = Color3.new(1, 1, 1); sub.TextStrokeTransparency = 0.5; sub.Text = ""; sub.TextYAlignment = Enum.TextYAlignment.Bottom; sub.Parent = gui
	card = Instance.new("TextLabel"); card.BackgroundTransparency = 1; card.Size = UDim2.fromScale(1, 0.2); card.AnchorPoint = Vector2.new(0.5, 0.5)
	card.Position = UDim2.fromScale(0.5, 0.5); card.Font = Enum.Font.GothamMedium; card.TextSize = 30; card.TextColor3 = Color3.fromRGB(230, 232, 236)
	card.TextTransparency = 1; card.Text = ""; card.ZIndex = 5; card.Parent = gui
	black = Instance.new("Frame"); black.BackgroundColor3 = Color3.new(0, 0, 0); black.BorderSizePixel = 0; black.Size = UDim2.fromScale(1, 1)
	black.BackgroundTransparency = 0; black.ZIndex = 4; black.Parent = gui
	skipBtn = Instance.new("TextButton"); skipBtn.AnchorPoint = Vector2.new(1, 0); skipBtn.Position = UDim2.new(1, -24, 0.09, 16)
	skipBtn.Size = UDim2.fromOffset(230, 40); skipBtn.BackgroundColor3 = Color3.fromRGB(12, 21, 29); skipBtn.BackgroundTransparency = 0.25
	skipBtn.BorderSizePixel = 0; skipBtn.Font = Enum.Font.GothamBold; skipBtn.TextSize = 15; skipBtn.TextColor3 = Color3.fromRGB(230, 232, 236)
	skipBtn.Text = "ÜBERSPRINGEN  [LEERTASTE]"; skipBtn.ZIndex = 6; skipBtn.Parent = gui
	Instance.new("UICorner", skipBtn).CornerRadius = UDim.new(0, 6)
	skipBtn.Activated:Connect(function() skipFlag = true end)
	gui.Parent = player:WaitForChild("PlayerGui")
end
local function fade(to, t)
	TweenService:Create(black, TweenInfo.new(t or 0.5), { BackgroundTransparency = to }):Play()
	return wait_(t or 0.5)
end
local function say(who, text, dur)
	sub.Text = ('<font color="#A6B3C7">%s</font>   %s'):format(who, text)
	local ok = wait_(dur or (1.2 + #text * 0.055))
	sub.Text = ""
	return ok
end
local function titleCard(text, dur)
	card.Text = text
	TweenService:Create(card, TweenInfo.new(0.6), { TextTransparency = 0 }):Play()
	local ok = wait_(dur or 2.2)
	TweenService:Create(card, TweenInfo.new(0.5), { TextTransparency = 1 }):Play()
	return ok and wait_(0.5)
end

---------------------------------------------------------------------------------------------------- Kamera
local shot = nil                                         -- function(t) -> CFrame, fov
local shotT0 = 0
local function setShot(fn) shot = fn; shotT0 = os.clock() end
local function head(a) return a.hrp.Position + Vector3.new(0, 2.4, 0) end

---------------------------------------------------------------------------------------------------- Licht (Schule: spaeter Nachmittag, ruhig; Gym: Original)
local savedLight
local function schoolLight(on)
	if on then
		if savedLight then return end
		savedLight = { props = { ClockTime = Lighting.ClockTime, Brightness = Lighting.Brightness, Ambient = Lighting.Ambient, OutdoorAmbient = Lighting.OutdoorAmbient,
			ShadowSoftness = Lighting.ShadowSoftness, EnvironmentDiffuseScale = Lighting.EnvironmentDiffuseScale, EnvironmentSpecularScale = Lighting.EnvironmentSpecularScale }, fx = {}, moved = {} }
		Lighting.ClockTime = 16.7; Lighting.Brightness = 2.0; Lighting.Ambient = Color3.fromRGB(104, 100, 96); Lighting.OutdoorAmbient = Color3.fromRGB(138, 130, 120)
		Lighting.ShadowSoftness = 0.3; Lighting.EnvironmentDiffuseScale = 0.6; Lighting.EnvironmentSpecularScale = 0.3
		for _, e in ipairs(Lighting:GetChildren()) do
			if e:IsA("PostEffect") then savedLight.fx[e] = e.Enabled; e.Enabled = false
			elseif e:IsA("Atmosphere") then table.insert(savedLight.moved, e); e.Parent = nil end
		end
		local atm = Instance.new("Atmosphere"); atm.Name = "CC_StoryAtmosphere"; atm.Density = 0.28; atm.Offset = 0.1; atm.Color = Color3.fromRGB(214, 200, 182)
		atm.Decay = Color3.fromRGB(120, 112, 104); atm.Glare = 0.1; atm.Haze = 1.2; atm.Parent = Lighting
		local cc = Instance.new("ColorCorrectionEffect"); cc.Name = "CC_StoryGrade"; cc.Saturation = -0.05; cc.Contrast = 0.06; cc.TintColor = Color3.fromRGB(255, 246, 236); cc.Parent = Lighting
	elseif savedLight then
		for k, v in pairs(savedLight.props) do pcall(function() Lighting[k] = v end) end
		for e, en in pairs(savedLight.fx) do if e.Parent then e.Enabled = en end end
		for _, e in ipairs(savedLight.moved) do e.Parent = Lighting end
		for _, n in ipairs({ "CC_StoryAtmosphere", "CC_StoryGrade" }) do local x = Lighting:FindFirstChild(n); if x then x:Destroy() end end
		savedLight = nil
	end
end

---------------------------------------------------------------------------------------------------- Requisiten
local function propPart(name, size, color)
	local p = Instance.new("Part"); p.Name = name; p.Size = size; p.Color = color; p.Material = Enum.Material.SmoothPlastic
	p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.Massless = true; p.Anchored = true; p.Parent = workspace
	table.insert(props, p); return p
end
local function makeCard()
	local c = propPart("Story_GymCard", Vector3.new(0.34, 0.22, 0.03), Color3.fromRGB(22, 24, 28))
	local logo = SH:FindFirstChild("CardLogo")
	if logo then local d = logo:Clone(); d.Face = Enum.NormalId.Front; d.Parent = c; local d2 = logo:Clone(); d2.Face = Enum.NormalId.Back; d2.Parent = c end
	return c
end
local function filmLight(pos, target, brightness, range, angle)
	local p = propPart("Story_FilmLight", Vector3.new(0.2, 0.2, 0.2), Color3.new(1, 1, 1)); p.Transparency = 1
	p.CFrame = CFrame.lookAt(pos, target)
	local l = Instance.new("SpotLight"); l.Face = Enum.NormalId.Front; l.Brightness = brightness or 2; l.Range = range or 30; l.Angle = angle or 60
	l.Color = Color3.fromRGB(255, 240, 222); l.Shadows = false; l.Parent = p
	return p
end
local cardFollow = nil                                  -- { a = actor, bone = "LeftHand", off = CFrame }
local function holdCard(c, a, boneName, off) cardFollow = c and { card = c, a = a, bone = boneName, off = off } or nil end

---------------------------------------------------------------------------------------------------- Szenen
local function look(p) local ok, t = pcall(function() return HS:JSONDecode(player:GetAttribute("CC_Look") or "{}") end); return ok and t or Look.DEFAULT end
local OUT_PLAYER = { Casual_Hoodie = Color3.fromRGB(120, 123, 128), Casual_Pants = Color3.fromRGB(34, 37, 44), Casual_Shoes = Color3.fromRGB(226, 226, 220),
	Casual_Backpack = Color3.fromRGB(28, 29, 32), Casual_Hands = "skin" }
local OUT_COACH = { Coach_Jacket = Color3.fromRGB(26, 27, 30), Coach_Pants = Color3.fromRGB(26, 27, 30), Casual_Shoes = Color3.fromRGB(236, 236, 232), Casual_Hands = "skin" }
local LOOK_COACH = { hair = "Hair_QuiffV03", beard = "Beard_Full", face = "Face_Focused", skin = 2, hairColor = 6 }

local function runFilm()
	local stopZ = 0
	local PSTOP = W(-3, stopZ)
	local GAP = 0.80 * M2S
	local plook = Look.sanitize(look())
	for k, v in pairs(Look.DEFAULT) do if plook[k] == nil then plook[k] = v end end
	-- Darsteller
	local P = makeActor("Player", plook, OUT_PLAYER, CFrame.lookAt(W(-3, 52), W(-3, 0)))
	local S = makeActor("StudentA", { hair = "Hair_Buzzcut", beard = "none", face = "Face_Neutral", skin = 1, hairColor = 4 },
		{ Casual_Hoodie = Color3.fromRGB(30, 31, 35), Casual_Pants = Color3.fromRGB(96, 98, 104), Casual_Shoes = Color3.fromRGB(236, 236, 232), Casual_Hands = "skin" },
		CFrame.lookAt(W(16, -12), W(-3, -12)))
	local S2 = makeActor("StudentB", { hair = "Hair_ShortCurls", beard = "none", face = "Face_Focused", skin = 3, hairColor = 1 },
		{ Casual_Hoodie = Color3.fromRGB(176, 178, 182), Casual_Pants = Color3.fromRGB(60, 74, 98), Casual_Shoes = Color3.fromRGB(40, 40, 44), Casual_Backpack = Color3.fromRGB(110, 40, 36), Casual_Hands = "skin" },
		CFrame.lookAt(W(19, -15), W(-3, -15)))
	local T = makeActor("Coach", LOOK_COACH, OUT_COACH, CFrame.lookAt(W(-30, -46), W(-3, -46)))
	local bg = {
		makeActor("Bg1", { hair = "Hair_SidePart", beard = "none", face = "Face_Friendly", skin = 2, hairColor = 3 },
			{ Casual_Hoodie = Color3.fromRGB(150, 74, 62), Casual_Pants = Color3.fromRGB(44, 46, 52), Casual_Shoes = Color3.fromRGB(226, 226, 220), Casual_Backpack = Color3.fromRGB(40, 60, 90), Casual_Hands = "skin" },
			CFrame.lookAt(W(-9, 64), W(-9, -60))),
		makeActor("Bg2", { hair = "Hair_QuiffV03", beard = "none", face = "Face_Neutral", skin = 4, hairColor = 1 },
			{ Casual_Hoodie = Color3.fromRGB(64, 92, 132), Casual_Pants = Color3.fromRGB(40, 42, 48), Casual_Shoes = Color3.fromRGB(226, 226, 220), Casual_Hands = "skin" },
			CFrame.lookAt(W(5, 70), W(5, -60))),
		makeActor("Bg3", { hair = "Hair_Buzzcut", beard = "none", face = "Face_Friendly", skin = 3, hairColor = 2 },
			{ Casual_Hoodie = Color3.fromRGB(70, 96, 70), Casual_Pants = Color3.fromRGB(56, 58, 64), Casual_Shoes = Color3.fromRGB(200, 200, 196), Casual_Backpack = Color3.fromRGB(30, 30, 34), Casual_Hands = "skin" },
			CFrame.lookAt(W(-12, 30), W(-40, 30))),
	}
	for _, a in ipairs(actors) do for _, n in ipairs({ "Fighter_CasualWalk_v2", "Story_P_Confront", "Story_S_Confront", "Story_S_Shove", "Story_P_Shoved", "Story_P_SitIdle",
		"Story_T_Stop", "Story_T_KneelHelp", "Story_P_HelpUp", "Story_T_GiveCard", "Story_P_TakeCard" }) do if a == P or a == S or a == T then a.track(n) end end end
	if not wait_(0.8) then return end                     -- Animationen laden (keine T-Pose)

	------------------------------------------------ Szene 1: Schulschluss
	setShot(function(t) return CFrame.lookAt(WP(16, 6.5 + t * 0.15, -40 + t * 0.6), WP(-2, 9, 40)), 50 end)
	fade(1, 1.0)
	task.spawn(walkTo, bg[1], W(-9, -60))
	task.delay(0.8, function() if running then walkTo(bg[2], W(5, -60)) end end)
	task.spawn(walkTo, bg[3], W(-40, 30))
	task.spawn(walkTo, P, W(-3, 24))
	if not wait_(4.2) then return end
	------------------------------------------------ Szene 2: Der Weg ist zu
	setShot(function(t) local p = head(P); return CFrame.lookAt(Vector3.new(p.X + 10, p.Y - 0.6, p.Z - 7), p + Vector3.new(0, -0.8, -3)), 40 end)
	task.delay(0.2, function() if running then walkTo(S, (O * CFrame.new(-3, GROUND + HRP_Y, stopZ - GAP)).Position, PSTOP) end end)
	task.delay(0.6, function() if running then walkTo(S2, W(-8.5, stopZ - GAP - 1.0), PSTOP) end end)
	walkTo(P, PSTOP)
	if skipFlag then return end
	P.hrp.CFrame = CFrame.lookAt(PSTOP, PSTOP + O.LookVector)
	if not wait_(0.5) then return end
	local sPos = (O * CFrame.new(-3, GROUND + HRP_Y, stopZ - GAP)).Position
	S.hrp.CFrame = CFrame.lookAt(sPos, Vector3.new(PSTOP.X, sPos.Y, PSTOP.Z))
	setShot(function(t) local s, p = head(S), head(P); local m = (s + p) / 2; return CFrame.lookAt(m + Vector3.new(11, -0.6, 1.5 - t * 0.2), m + Vector3.new(0, -1.0, 0)), 40 end)
	P.play("Story_P_Confront", 0.3); S.play("Story_S_Confront", 0.3)
	task.delay(0.5, function() if running then say("SCHÜLER", "Wohin so schnell?", 1.6) end end)
	if not wait_(2.8) then return end
	setShot(function(t) local s, p = head(S), head(P); return CFrame.lookAt(p + Vector3.new(-3.6, 0.2, 7.5), (s + p) / 2 + Vector3.new(-0.6, -0.8, 0)), 40 end)
	if not say("DU", "Lass mich einfach durch.", 1.6) then return end
	------------------------------------------------ Szene 3: Der Schubser
	setShot(function(t) local s, p = head(S), head(P); local m = (s + p) / 2; return CFrame.lookAt(m + Vector3.new(9.5, -2.4, -2.5), m + Vector3.new(0, -1.6, 1.0)), 44 end)
	S.stop("Story_S_Confront", 0.2); P.stop("Story_P_Confront", 0.2)
	S.play("Story_S_Shove", 0.15); local sh = P.play("Story_P_Shoved", 0.15)
	-- Rucksack faellt: Traeger am Spieler aus, lose Tasche faellt seitlich
	task.delay(1.15, function()
		if not running then return end
		local bp = P.model:FindFirstChild("Casual_Backpack")
		if bp then
			local loose = SH.Outfit.Casual_Backpack:Clone(); loose.Color = bp.Color; loose.Anchored = true; loose.CanCollide = false; loose.Parent = workspace
			table.insert(props, loose)
			local from = bp.CFrame
			bp.Transparency = 1
			local to = CFrame.new((P.hrp.CFrame * CFrame.new(-2.6, -HRP_Y + 0.55, 2.0)).Position) * CFrame.Angles(math.rad(-80), math.rad(30), 0)
			loose.CFrame = from
			TweenService:Create(loose, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { CFrame = to }):Play()
		end
	end)
	if not wait_(1.0) then return end
	task.delay(0.3, function() if running then say("SCHÜLER", "Pass doch auf.", 1.3) end end)
	if not wait_(1.5) then return end
	P.play("Story_P_SitIdle", 0.25, true)
	------------------------------------------------ Szene 4: Der Trainer
	local tStop = (P.hrp.CFrame * CFrame.new(-2.2, 0, -1.4)).Position
	setShot(function(t) local p = P.hrp.Position; return CFrame.lookAt(p + Vector3.new(-6, 1.2, 9), p + Vector3.new(0, 1.0, -5)), 46 end)
	task.spawn(walkTo, T, tStop, head(S))
	if not wait_(2.6) then return end
	T.play("Story_T_Stop", 0.25)
	setShot(function(t) local m = (head(T) + head(S)) / 2; return CFrame.lookAt(m + Vector3.new(14 - t * 0.3, -0.4, 5), m + Vector3.new(0, -1.2, 0)), 40 end)
	if not say("TRAINER", "Hey. Schluss jetzt.", 1.6) then return end
	setShot(function(t) local p = P.hrp.Position; return CFrame.lookAt(p + Vector3.new(7, 3.6, 9), head(S) + Vector3.new(0, -1.2, 0)), 44 end)
	task.spawn(walkTo, S, W(-38, -6)); task.delay(0.4, function() if running then walkTo(S2, W(-36, -10)) end end)
	if not wait_(2.0) then return end
	------------------------------------------------ Szene 5: Auf Augenhoehe
	-- Trainer kniet vor dem sitzenden Spieler (Blender-Aufstellung: 0,30 m vor dem Spieler-Ursprung, Blick zum Spieler)
	local helpPos = (P.hrp.CFrame * CFrame.new(0, 0, -0.30 * M2S)).Position
	T.stop("Story_T_Stop", 0.3)
	walkTo(T, helpPos + (P.hrp.CFrame.LookVector * 0.05), P.hrp.Position)
	if skipFlag then return end
	T.hrp.CFrame = CFrame.lookAt(helpPos, Vector3.new(P.hrp.Position.X, helpPos.Y, P.hrp.Position.Z))
	setShot(function(t) local p, h = P.hrp.Position, head(T); local m = (p + h) / 2; return CFrame.lookAt(m + P.hrp.CFrame.RightVector * 14 + Vector3.new(0, 0.2, 0), m + Vector3.new(0, -1.6, 0)), 40 end)
	T.play("Story_T_KneelHelp", 0.3); P.stop("Story_P_SitIdle", 0.3); P.play("Story_P_HelpUp", 0.3)
	task.delay(1.0, function() if running then say("TRAINER", "Alles okay? Kannst du aufstehen?", 1.9) end end)
	if not wait_(3.0) then return end
	task.delay(0.0, function() if running then say("DU", "Ja … geht schon.", 1.2) end end)
	if not wait_(1.0) then return end
	-- Ende Aufhelfen: Spieler steht 0,30 m hinter seinem Ursprung -> Ursprung nachziehen (nahtlos, gleiche Pose)
	P.hrp.CFrame = P.hrp.CFrame * CFrame.new(0, 0, 0.30 * M2S)
	P.stop("Story_P_HelpUp", 0); T.stop("Story_T_KneelHelp", 0.3)
	------------------------------------------------ Szene 6: Die Einladung
	if not fade(0, 0.25) then return end
	for _, a in ipairs({ S, S2, bg[1], bg[2], bg[3] }) do a.model.Parent = nil end
	T.hrp.CFrame = CFrame.lookAt((P.hrp.CFrame * CFrame.new(0, 0, -0.88 * M2S)).Position, P.hrp.Position)
	local c = makeCard()
	holdCard(c, T, "RightHand", CFrame.new(0, 0, -0.12) * CFrame.Angles(math.rad(90), 0, 0))
	setShot(function(t) local p, h = head(P), head(T); local m = (p + h) / 2; return CFrame.lookAt(m + P.hrp.CFrame.RightVector * 11 + Vector3.new(0, 0.2, 0), m + Vector3.new(0, -0.9, 0)), 40 end)
	fade(1, 0.25)
	if not say("TRAINER", "Ich trainiere im Gym um die Ecke. Komm morgen vorbei, wenn du willst.", 3.2) then return end
	T.play("Story_T_GiveCard", 0.25); P.play("Story_P_TakeCard", 0.25)
	setShot(function(t) local m = (head(P) + head(T)) / 2; return CFrame.lookAt(m + P.hrp.CFrame.RightVector * 12 + Vector3.new(0, -0.4, 0), m + Vector3.new(0, -1.4, 0)), 38 end)
	if not wait_(1.0) then return end
	holdCard(c, P, "LeftHand", CFrame.new(0, 0, -0.12) * CFrame.Angles(math.rad(90), 0, 0))
	if not wait_(1.0) then return end
	setShot(function(t) local p = head(P); return CFrame.lookAt(c.Position + P.hrp.CFrame.RightVector * 3.2 + P.hrp.CFrame.LookVector * 1.2 + Vector3.new(0, 0.9, 0), c.Position), 30 end)
	if not say("DU", "Ich kann nicht kämpfen.", 1.6) then return end
	setShot(function(t) local h = head(T); local m = (head(P) + h) / 2; return CFrame.lookAt(m + P.hrp.CFrame.RightVector * -9 + Vector3.new(0, 0.2, 0), m + Vector3.new(0, -0.6, 0)), 38 end)
	if not say("TRAINER", "Musst du auch noch nicht können.", 2.0) then return end
	if not fade(0, 0.8) then return end
	------------------------------------------------ Szene 7: Die Entscheidung (Gym-Front in der Nachbarstrasse)
	for _, a in ipairs({ S, S2, T, bg[1], bg[2], bg[3] }) do a.model.Parent = nil end
	for _, p in ipairs(props) do if p ~= c then p.Parent = nil end end
	local bpp = P.model:FindFirstChild("Casual_Backpack"); if bpp then bpp.Transparency = 0 end
	if not titleCard("Am nächsten Nachmittag.", 2.0) then return end
	local front = workspace.CC_StorySchool:FindFirstChild("GymFront")
	local door = front and front:FindFirstChild("GymDoor")
	local doorCF = door and door.CFrame
	local hinge = door and door:GetAttribute("CC_Hinge")
	local doorPos = door and door.Position or WP(120, 7, -118)
	local standAt = Vector3.new(doorPos.X + 0.35, GROUND + HRP_Y + 0.0, doorPos.Z + 0.80 * M2S + 0.6)
	P.hrp.CFrame = CFrame.lookAt(standAt, Vector3.new(doorPos.X + 0.35, standAt.Y, doorPos.Z))
	filmLight(standAt + Vector3.new(5, 7, 12), standAt + Vector3.new(0, 1, -2), 3, 36, 70)            -- Fuelllicht von der Strassenseite (Fassade liegt im Schatten)
	P.stop("Story_P_TakeCard", 0); local dr = P.play("Story_P_Door", 0)
	if dr then dr:AdjustSpeed(0) end
	setShot(function(t) local p = head(P); return CFrame.lookAt(p + Vector3.new(6.5 - t * 0.3, 1.2, 13 - t * 0.6), p + Vector3.new(-0.4, 2.2, -8)), 46 end)
	if not fade(1, 0.8) then return end
	if dr then dr:AdjustSpeed(1) end
	task.delay(48 / 24, function()                       -- Tuer oeffnet, wenn die Hand sie erreicht
		if running and door and hinge then
			local h = CFrame.new(hinge)
			local rel = h:Inverse() * doorCF
			local v = Instance.new("NumberValue"); v.Value = 0
			v.Changed:Connect(function(x) door.CFrame = h * CFrame.Angles(0, math.rad(-x), 0) * rel end)
			TweenService:Create(v, TweenInfo.new(1.0, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Value = 70 }):Play()
		end
	end)
	task.delay(14 / 24, function() holdCard(nil) ; if c then c.Parent = nil end end)
	if not wait_(3.2) then return end
	if not fade(0, 0.6) then return end
	if door and doorCF then door.CFrame = doorCF end
	------------------------------------------------ Szene 8: Willkommen im Gym (echtes Gym)
	schoolLight(false)
	local GYM_IN = Vector3.new(152, HRP_Y, 30)
	P.hrp.CFrame = CFrame.lookAt(GYM_IN, GYM_IN + Vector3.new(1, 0, 0))
	P.stop("Story_P_Door", 0)
	T.model.Parent = workspace
	T.hrp.CFrame = CFrame.lookAt(Vector3.new(162, HRP_Y, 30), GYM_IN)
	filmLight(Vector3.new(157, 13, 40), Vector3.new(157, 4, 30), 2.4, 34, 80)                          -- Filmlicht im Gym (nur lokal)
	filmLight(Vector3.new(146, 9, 24), Vector3.new(158, 5, 30), 1.2, 30, 70)
	setShot(function(t) local p = head(P); return CFrame.lookAt(p + Vector3.new(-5.5, 0.6, 3.2 - t * 0.3), head(T) + Vector3.new(0, -0.6, 0)), 44 end)
	if not fade(1, 0.6) then return end
	T.play("Trainer_Pereira_Greet", 0.25)
	if not say("TRAINER", "Du bist gekommen.", 1.6) then return end
	setShot(function(t) local p = head(P); return CFrame.lookAt(head(T) + Vector3.new(5.5, 0.2, -3.2), p + Vector3.new(0, -0.4, 0)), 40 end)
	if not say("DU", "Kann ich wirklich hier anfangen?", 1.8) then return end
	setShot(function(t) local p = head(P); return CFrame.lookAt(p + Vector3.new(-5.5, 0.4, 3.2), head(T) + Vector3.new(0, -0.6, 0)), 42 end)
	if not say("TRAINER", "Klar. Tasche dort hin. Wir beginnen langsam.", 2.4) then return end
	if not fade(0, 0.6) then return end
	------------------------------------------------ Szene 9: Die erste Lektion (Trainingskleidung = echter Kaempfer)
	P.model.Parent = nil
	local me = player.Character
	local mePos = Vector3.new(153, HRP_Y, 30)
	if me and me:FindFirstChild("HumanoidRootPart") then me.HumanoidRootPart.CFrame = CFrame.lookAt(mePos, Vector3.new(162, HRP_Y, 30)) end
	T.stop("Trainer_Pereira_Greet", 0)
	T.hrp.CFrame = CFrame.lookAt(Vector3.new(162, HRP_Y, 30), mePos)
	T.play("Fighter_Idle_v08", 0.3, true)
	setShot(function(t) local h = head(T); return CFrame.lookAt(h + Vector3.new(-3.0, -0.6, 8.5 - t * 0.3), h + Vector3.new(-1.5, -1.4, 0)), 42 end)
	if not fade(1, 0.6) then return end
	if not say("TRAINER", "Füße versetzt. Knie locker. Hände hoch. Nicht verkrampfen.", 3.4) then return end
	-- Uebergang zur Spielkamera: hinter den eigenen Kaempfer fahren
	local fromCF = workspace.CurrentCamera.CFrame
	setShot(function(t)
		local u = math.min(t / 1.2, 1); u = u * u * (3 - 2 * u)
		local goal = CFrame.lookAt(mePos + Vector3.new(-10, 4.5, 0), mePos + Vector3.new(6, 2, 0))
		return fromCF:Lerp(goal, u), 70
	end)
	wait_(1.3)
end

---------------------------------------------------------------------------------------------------- Start / Ende
local saved = nil
local function begin()
	running, skipFlag = true, false
	saved = { cam = workspace.CurrentCamera.CameraType, fov = workspace.CurrentCamera.FieldOfView, guis = {} }
	for _, g in ipairs(player.PlayerGui:GetChildren()) do if g:IsA("ScreenGui") and g.Enabled then saved.guis[g] = true; g.Enabled = false end end
	player:SetAttribute("CC_UIBlock", true)
	buildGui()
	schoolLight(true)
	table.insert(conns, UIS.InputBegan:Connect(function(i, gp)
		if i.KeyCode == Enum.KeyCode.Space or i.KeyCode == Enum.KeyCode.Return or i.KeyCode == Enum.KeyCode.ButtonA then skipFlag = true end
	end))
	RunService:BindToRenderStep("CC_StoryCam", Enum.RenderPriority.Last.Value + 60, function()
		local cam = workspace.CurrentCamera
		if not running or not shot then return end
		cam.CameraType = Enum.CameraType.Scriptable
		local cf, fov = shot(os.clock() - shotT0)
		cam.CFrame = cf; cam.FieldOfView = fov or 50
		for g in pairs(saved.guis) do if g.Enabled then g.Enabled = false end end
		if cardFollow and cardFollow.card.Parent then
			local b = bone(cardFollow.a, cardFollow.bone)
			if b then cardFollow.card.CFrame = b.TransformedWorldCFrame * cardFollow.off end
		end
	end)
end
local function finish(skipped)
	running = false
	pcall(function() RunService:UnbindFromRenderStep("CC_StoryCam") end)
	for _, c in ipairs(conns) do c:Disconnect() end; conns = {}
	for _, a in ipairs(actors) do if a.model then a.model:Destroy() end end; actors = {}
	for _, p in ipairs(props) do p:Destroy() end; props = {}
	cardFollow = nil; shot = nil
	local front = workspace:FindFirstChild("CC_StorySchool") and workspace.CC_StorySchool:FindFirstChild("GymFront")
	schoolLight(false)
	if gui then gui:Destroy(); gui = nil end
	local cam = workspace.CurrentCamera
	cam.CameraType = Enum.CameraType.Custom; cam.FieldOfView = saved and saved.fov or 70
	local hum = player.Character and player.Character:FindFirstChildOfClass("Humanoid"); if hum then cam.CameraSubject = hum end
	if saved then for g in pairs(saved.guis) do if g.Parent then g.Enabled = true end end end
	player:SetAttribute("CC_UIBlock", nil)
	saved = nil
end
local function play(mode)
	if running then return end
	begin()
	local ok, err = pcall(runFilm)
	if not ok then warn("[Story] Fehler: " .. tostring(err)) end
	local skipped = skipFlag
	finish(skipped)
	if mode == "onboarding" then remote:FireServer("done", skipped and "skip" or "ok") end
end

remote.OnClientEvent:Connect(function(what) if what == "play" then task.spawn(play, "replay") end end)
local function check()
	if player:GetAttribute("CC_OnbPhase") == "story" and not running then task.spawn(play, "onboarding") end
end
player:GetAttributeChangedSignal("CC_OnbPhase"):Connect(check)
task.defer(check)
