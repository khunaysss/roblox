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
local okHands, Hands = pcall(function() return require(RS:WaitForChild("CC_Hands", 5)) end)   -- Haende mit Fingern (optional)
if not okHands then Hands = nil end
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
local function makeActor(name, look, outfit, cf, keepFight)
	local c = SH.ActorBase:Clone(); c.Name = "Story_" .. name
	if not keepFight then for _, n in ipairs({ "Fighter_Gloves", "Fighter_Shorts" }) do local x = c:FindFirstChild(n); if x then x.Transparency = 1 end end end
	local hum = c:FindFirstChildOfClass("Humanoid"); hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	local hrp = c.HumanoidRootPart; hrp.Anchored = true
	for _, p in ipairs(c:GetDescendants()) do if p:IsA("BasePart") then p.CanCollide = false; p.CanQuery = false; p.CanTouch = false end end
	c.Parent = workspace
	Look.apply(c, look, RS:FindFirstChild("CC_CustomShared"))
	local skin = Look.SKIN[look.skin or 2]
	-- Haende mit Fingern (CC_Hands) statt der Block-Huelle Casual_Hands; nur ohne Handschuhe
	local handsOn = outfit.Casual_Hands ~= nil and not keepFight and Hands ~= nil and Hands.attach(c, skin) or false
	for pname, col in pairs(outfit) do
		local t = SH.Outfit:FindFirstChild(pname)
		if t and not (pname == "Casual_Hands" and handsOn) then
			local p = t:Clone(); p.Massless = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
			p.Color = (col == "skin") and skin or col
			local mo = Instance.new("Motor6D"); mo.Part0 = hrp; mo.Part1 = p; mo.C0 = t:GetAttribute("CC_C0"); mo.Parent = p
			p.Parent = c
		end
	end
	hrp.CFrame = cf
	local animator = hum:FindFirstChildOfClass("Animator") or Instance.new("Animator", hum)
	local a = { model = c, hrp = hrp, animator = animator, tracks = {} }
	function a.hands(pose, right) if handsOn then Hands.setPose(c, pose, right) end end   -- Handpose (Open/Relaxed/Point/Fist/Thumb)
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
local PACE = 0.8                                        -- Tempo des Films: Pausen auf 80 % (Szenen bleiben)
local function wait_(t)                                   -- false, wenn uebersprungen
	t = t * PACE
	local t0 = os.clock()
	while os.clock() - t0 < t do if skipFlag or not running then return false end; RunService.Heartbeat:Wait() end
	return not skipFlag
end
local RUN = 17                                        -- Studs/s beim Rennen (Fighter_CasualRun_v3)
local function walkTo(a, target, faceAt, speed, anim)
	local start = a.hrp.Position
	local d = (target - start) * Vector3.new(1, 0, 1)
	if d.Magnitude < 0.05 then return end
	local dur = d.Magnitude / (speed or WALK)
	local w = a.play(anim or "Fighter_CasualWalk_v2", 0.2, true, Enum.AnimationPriority.Movement)
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
local function runPath(a, pts, faceAt)                    -- mehrere Wegpunkte rennend (z. B. durchs Schultor)
	for i, p in ipairs(pts) do
		walkTo(a, p, i == #pts and faceAt or nil, RUN, "Fighter_CasualRun_v3")
		if skipFlag or not running then return end
	end
end
local function sfx(name, vol)                             -- Projekt-Sound einmal abspielen (2D)
	local s = game:GetService("SoundService"):FindFirstChild("CC_Sounds")
	s = s and s:FindFirstChild(name)
	if not s then return end
	local c = s:Clone(); c.Volume = (vol or 1) * (s.Volume > 0 and s.Volume or 0.5); c.Parent = workspace.CurrentCamera
	c:Play(); game:GetService("Debris"):AddItem(c, 4)
end

---------------------------------------------------------------------------------------------------- Oberflaeche: Kinobalken, Untertitel, Ueberspringen, Blende
local gui, sub, card, black, skipBtn
local function buildGui()
	gui = Instance.new("ScreenGui"); gui.Name = "CC_StoryGui"; gui.IgnoreGuiInset = true; gui.DisplayOrder = 60; gui.ResetOnSpawn = false
	for _, top in ipairs({ true, false }) do
		local b = Instance.new("Frame"); b.BackgroundColor3 = Color3.new(0, 0, 0); b.BorderSizePixel = 0; b.Size = UDim2.new(1, 0, 0.09, 0)
		b.Position = UDim2.fromScale(0, top and 0 or 0.91); b.Parent = gui
	end
	sub = Instance.new("TextLabel"); sub.BackgroundColor3 = UI.C.bg0; sub.BackgroundTransparency = 0.12; sub.BorderSizePixel = 0; sub.AnchorPoint = Vector2.new(0.5, 1); sub.Position = UDim2.new(0.5, 0, 0.885, 0)
	sub.Size = UDim2.new(0.72, 0, 0, 64); sub.Font = Enum.Font.GothamMedium; sub.TextSize = 26; sub.TextWrapped = true; sub.RichText = true
	sub.TextColor3 = Color3.new(1, 1, 1); sub.TextStrokeTransparency = 0.5; sub.Text = ""; sub.TextYAlignment = Enum.TextYAlignment.Center; sub.Parent = gui
	Instance.new("UICorner",sub).CornerRadius=UDim.new(0,4)
	local inset=Instance.new("UIPadding");inset.PaddingLeft=UDim.new(0,16);inset.PaddingRight=UDim.new(0,16);inset.Parent=sub
	sub:GetPropertyChangedSignal("Text"):Connect(function() sub.BackgroundTransparency=sub.Text=="" and 1 or .12 end)
	card = Instance.new("TextLabel"); card.BackgroundTransparency = 1; card.Size = UDim2.fromScale(1, 0.2); card.AnchorPoint = Vector2.new(0.5, 0.5)
	card.Position = UDim2.fromScale(0.5, 0.5); card.Font = Enum.Font.GothamMedium; card.TextSize = 30; card.TextColor3 = Color3.fromRGB(230, 232, 236)
	card.TextTransparency = 1; card.Text = ""; card.ZIndex = 5; card.Parent = gui
	black = Instance.new("Frame"); black.BackgroundColor3 = Color3.new(0, 0, 0); black.BorderSizePixel = 0; black.Size = UDim2.fromScale(1, 1)
	black.BackgroundTransparency = 0; black.ZIndex = 4; black.Parent = gui
	skipBtn = Instance.new("TextButton"); skipBtn.AnchorPoint = Vector2.new(1, 0); skipBtn.Position = UDim2.new(1, -24, 0.09, 16)
	skipBtn.Size = UDim2.fromOffset(230, 40); skipBtn.BackgroundColor3 = Color3.fromRGB(12, 21, 29); skipBtn.BackgroundTransparency = 0.25
	skipBtn.BorderSizePixel = 0; skipBtn.Font = Enum.Font.GothamBold; skipBtn.TextSize = 15; skipBtn.TextColor3 = Color3.fromRGB(230, 232, 236)
	skipBtn.Text = "SKIP  [SPACE]"; skipBtn.ZIndex = 6; skipBtn.Parent = gui
	Instance.new("UICorner", skipBtn).CornerRadius = UDim.new(0, 6)
	skipBtn.Activated:Connect(function() skipFlag = true end)
	gui.Parent = player:WaitForChild("PlayerGui")
end
local function fade(to, t)
	TweenService:Create(black, TweenInfo.new(t or 0.5), { BackgroundTransparency = to }):Play()
	return wait_(t or 0.5)
end
local shake = 0                                          -- Kamerawackeln (klingt von selbst ab)
local function say(who, text, dur)
	sub.Text = ('<font color="#A6B3C7">%s</font>   %s'):format(who, text)
	local ok = wait_(dur or (1.2 + #text * 0.055))            -- wait_ rechnet das Tempo selbst ein
	sub.Text = ""
	return ok
end
local function shout(who, text, dur)                      -- Schrei: gross, rot, Kamera-Stoss
	sub.Text = ('<font color="#A6B3C7">%s</font>   <font color="#FF4A3D" size="40"><b>%s</b></font>'):format(who, text)
	shake = 1.0
	local sc = Instance.new("UIScale"); sc.Scale = 1.35; sc.Parent = sub
	TweenService:Create(sc, TweenInfo.new(0.25, Enum.EasingStyle.Back), { Scale = 1 }):Play()
	local ok = wait_(dur or 1.6)
	sub.Text = ""; sc:Destroy()
	return ok
end
-- Nahaufnahme der Visitenkarte als Bild auf dem Schirm (man soll lesen koennen, was er ihm gibt)
local cardView
local function showCardView(on)
	if on and not cardView then
		local logo = SH:FindFirstChild("CardLogo")
		local f = Instance.new("Frame"); f.Name = "CardView"; f.AnchorPoint = Vector2.new(0.5, 0.5); f.Position = UDim2.fromScale(0.5, 0.44)
		f.Size = UDim2.fromOffset(440, 260); f.BackgroundColor3 = Color3.fromRGB(20, 22, 26); f.BorderSizePixel = 0; f.ZIndex = 7; f.Parent = gui
		Instance.new("UICorner", f).CornerRadius = UDim.new(0, 14)
		local st = Instance.new("UIStroke", f); st.Color = Color3.fromRGB(200, 40, 34); st.Thickness = 3
		local img = Instance.new("ImageLabel"); img.BackgroundTransparency = 1; img.Size = UDim2.fromOffset(130, 130); img.Position = UDim2.fromOffset(22, 22)
		img.Image = logo and logo.Texture or ""; img.ZIndex = 8; img.Parent = f
		local function txt(t, y, size, font, col)
			local l = Instance.new("TextLabel"); l.BackgroundTransparency = 1; l.Position = UDim2.fromOffset(168, y); l.Size = UDim2.fromOffset(255, size + 6)
			l.Font = font; l.TextSize = size; l.TextColor3 = col or Color3.fromRGB(236, 236, 240); l.TextXAlignment = Enum.TextXAlignment.Left
			l.Text = t; l.ZIndex = 8; l.Parent = f
		end
		txt("CAGE CHAMPIONS", 34, 30, Enum.Font.GothamBlack)
		txt("MMA GYM", 70, 24, Enum.Font.GothamBold, Color3.fromRGB(220, 52, 44))
		txt("Beginners welcome", 110, 18, Enum.Font.GothamMedium, Color3.fromRGB(180, 186, 196))
		local foot = Instance.new("TextLabel"); foot.BackgroundTransparency = 1; foot.Position = UDim2.fromOffset(22, 180); foot.Size = UDim2.fromOffset(396, 60)
		foot.Font = Enum.Font.GothamMedium; foot.TextSize = 18; foot.TextColor3 = Color3.fromRGB(200, 204, 212); foot.TextWrapped = true
		foot.Text = "Training every day · 4 PM\nAround the corner from Northpark High"; foot.ZIndex = 8; foot.Parent = f
		local sc = Instance.new("UIScale"); sc.Scale = 0.2; sc.Parent = f
		TweenService:Create(sc, TweenInfo.new(0.35, Enum.EasingStyle.Back), { Scale = 1 }):Play()
		cardView = f
	elseif not on and cardView then
		local f = cardView; cardView = nil
		TweenService:Create(f.UIScale, TweenInfo.new(0.2), { Scale = 0.01 }):Play()
		task.delay(0.22, function() f:Destroy() end)
	end
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
	Lighting:SetAttribute("CC_StoryLighting", on == true)
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
	local c = propPart("Story_GymCard", Vector3.new(1.0, 0.62, 0.04), Color3.fromRGB(22, 24, 28))
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
		"Story_T_Stop", "Story_T_KneelHelp", "Story_P_HelpUp", "Story_T_GiveCard", "Story_P_TakeCard", "Fighter_CasualRun_v3" }) do if a == P or a == S or a == S2 or a == T then a.track(n) end end end
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
	task.delay(0.5, function() if running then say("BULLY", "Where do you think you're going, new kid?", 2.2) end end)
	if not wait_(2.9) then return end
	setShot(function(t) local s, p = head(S), head(P); return CFrame.lookAt(p + Vector3.new(-3.6, 0.2, 7.5), (s + p) / 2 + Vector3.new(-0.6, -0.8, 0)), 40 end)
	if not say("YOU", "Just let me through.", 1.5) then return end
	setShot(function(t) local s = head(S); local cf = S.hrp.CFrame; return CFrame.lookAt(s + cf.LookVector * (4.2 - t * 0.3) + cf.RightVector * 2.2 - Vector3.new(0, 0.4, 0), s + Vector3.new(0, -0.3, 0)), 34 end)
	if not say("BULLY", "Make me.", 1.2) then return end
	------------------------------------------------ Szene 3: Der Schubser
	setShot(function(t) local s, p = head(S), head(P); local m = (s + p) / 2; return CFrame.lookAt(m + Vector3.new(9.5, -2.4, -2.5), m + Vector3.new(0, -1.6, 1.0)), 44 end)
	S.stop("Story_S_Confront", 0.2); P.stop("Story_P_Confront", 0.2)
	S.hands("Open")                                          -- Schubsen mit offenen Haenden
	local sv = S.play("Story_S_Shove", 0.15); local sh = P.play("Story_P_Shoved", 0.15)
	-- Zeitlupe im Moment des Stosses, dann Aufprall mit Wackeln und Geraeusch
	task.delay(0.35, function()
		if not running then return end
		sfx("Whoosh", 0.8)
		for _, t in ipairs({ sv, sh }) do if t then t:AdjustSpeed(0.3) end end
		task.wait(0.55)
		for _, t in ipairs({ sv, sh }) do if t then t:AdjustSpeed(1) end end
		shake = 0.7; sfx("BodyHit", 0.9)
		task.wait(0.55)
		if running then shake = 1.1; sfx("BodyFall", 1.2) end
	end)
	-- Rucksack faellt: Traeger am Spieler aus, lose Tasche faellt seitlich
	task.delay(1.55, function()
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
	if not wait_(1.4) then return end
	task.delay(0.2, function() if running then say("BULLY", "Stay down, loser!", 1.4) end end)
	if not wait_(1.5) then return end
	P.play("Story_P_SitIdle", 0.25, true)
	------------------------------------------------ Szene 4: Der Trainer (kommt rennend durchs Schultor, nicht durch die Mauer)
	local tStop = (P.hrp.CFrame * CFrame.new(-2.2, 0, -1.4)).Position
	T.hrp.CFrame = CFrame.lookAt(W(-4, -44), W(-4, 0))
	task.spawn(runPath, T, { W(-4, -36), W(-4, -22), tStop }, head(S))
	-- Schrei vom Tor aus: Kamera ruckt zum Trainer
	setShot(function(t) local h = head(T); return CFrame.lookAt(h + Vector3.new(3.5, -0.6, 9 + t * 1.5), h + Vector3.new(0, -0.4, 0)), 42 - t * 4 end)
	if not wait_(0.45) then return end
	if not shout("COACH", "HEY!! GET AWAY FROM HIM!", 1.5) then return end
	-- Mobber zucken zusammen, drehen sich um und rennen
	setShot(function(t) local m = (head(S) + head(S2)) / 2; return CFrame.lookAt(m + Vector3.new(7, -0.2, -7), m + Vector3.new(0, -0.6, 0)), 38 end)
	S.hands("Relaxed"); S.stop("Story_S_Shove", 0.1); face(S, T.hrp.Position); face(S2, T.hrp.Position)
	shake = 0.4
	if not say("BULLY", "Oh no — RUN!", 0.9) then return end
	task.spawn(runPath, S, { W(-14, -6), W(-46, -4) }); task.delay(0.15, function() if running then runPath(S2, { W(-16, -10), W(-46, -9) }) end end)
	setShot(function(t) local p = P.hrp.Position; return CFrame.lookAt(p + Vector3.new(7, 3.6, 9), head(S) + Vector3.new(0, -1.2, 0)), 44 end)
	if not wait_(1.0) then return end
	T.hands("Open"); T.play("Story_T_Stop", 0.2)
	setShot(function(t) local h = head(T); return CFrame.lookAt(h + T.hrp.CFrame.LookVector * 6 + T.hrp.CFrame.RightVector * 2 + Vector3.new(0, -0.5, 0), h + Vector3.new(0, -0.3, 0)), 36 end)
	if not shout("COACH", "AND DON'T COME BACK!", 1.4) then return end
	------------------------------------------------ Szene 5: Auf Augenhoehe
	-- Trainer kniet vor dem sitzenden Spieler (Blender-Aufstellung: 0,30 m vor dem Spieler-Ursprung, Blick zum Spieler)
	local helpPos = (P.hrp.CFrame * CFrame.new(0, 0, -0.30 * M2S)).Position
	T.hands("Relaxed"); T.stop("Story_T_Stop", 0.3)
	walkTo(T, helpPos + (P.hrp.CFrame.LookVector * 0.05), P.hrp.Position)
	if skipFlag then return end
	T.hrp.CFrame = CFrame.lookAt(helpPos, Vector3.new(P.hrp.Position.X, helpPos.Y, P.hrp.Position.Z))
	setShot(function(t) local p, h = P.hrp.Position, head(T); local m = (p + h) / 2; return CFrame.lookAt(m + P.hrp.CFrame.RightVector * 14 + Vector3.new(0, 0.2, 0), m + Vector3.new(0, -1.6, 0)), 40 end)
	T.play("Story_T_KneelHelp", 0.3); P.stop("Story_P_SitIdle", 0.3); P.play("Story_P_HelpUp", 0.3)
	task.delay(1.0, function() if running then say("COACH", "Hey. You okay? Can you stand up?", 1.9) end end)
	if not wait_(3.0) then return end
	task.delay(0.0, function() if running then say("YOU", "Yeah … I think so.", 1.2) end end)
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
	if not say("COACH", "Guys like that only stop when you stand your ground. I coach at a gym around the corner.", 3.4) then return end
	T.play("Story_T_GiveCard", 0.25); P.play("Story_P_TakeCard", 0.25)
	setShot(function(t) local m = (head(P) + head(T)) / 2; return CFrame.lookAt(m + P.hrp.CFrame.RightVector * 12 + Vector3.new(0, -0.4, 0), m + Vector3.new(0, -1.4, 0)), 38 end)
	if not wait_(1.0) then return end
	holdCard(c, P, "LeftHand", CFrame.new(0, 0, -0.12) * CFrame.Angles(math.rad(90), 0, 0))
	if not wait_(0.6) then return end
	showCardView(true)
	if not wait_(2.4) then showCardView(false); return end
	showCardView(false)
	setShot(function(t) local p = head(P); return CFrame.lookAt(c.Position + P.hrp.CFrame.RightVector * 3.2 + P.hrp.CFrame.LookVector * 1.2 + Vector3.new(0, 0.9, 0), c.Position), 30 end)
	if not say("YOU", "I can't fight.", 1.6) then return end
	setShot(function(t) local h = head(T); local m = (head(P) + h) / 2; return CFrame.lookAt(m + P.hrp.CFrame.RightVector * -9 + Vector3.new(0, 0.2, 0), m + Vector3.new(0, -0.6, 0)), 38 end)
	if not say("COACH", "Not yet. Come by tomorrow — I'll teach you.", 2.4) then return end
	if not fade(0, 0.8) then return end
	------------------------------------------------ Szene 7: Die Entscheidung (Gym-Front in der Nachbarstrasse)
	for _, a in ipairs({ S, S2, T, bg[1], bg[2], bg[3] }) do a.model.Parent = nil end
	for _, p in ipairs(props) do if p ~= c then p.Parent = nil end end
	local bpp = P.model:FindFirstChild("Casual_Backpack"); if bpp then bpp.Transparency = 0 end
	if not titleCard("THE NEXT DAY", 2.0) then return end
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
	if not say("COACH", "You actually came. Good.", 1.8) then return end
	setShot(function(t) local p = head(P); return CFrame.lookAt(head(T) + Vector3.new(5.5, 0.2, -3.2), p + Vector3.new(0, -0.4, 0)), 40 end)
	if not say("YOU", "Can I really start here?", 1.8) then return end
	setShot(function(t) local p = head(P); return CFrame.lookAt(p + Vector3.new(-5.5, 0.4, 3.2), head(T) + Vector3.new(0, -0.6, 0)), 42 end)
	if not say("COACH", "Everyone starts somewhere. Drop your bag — let's work.", 2.6) then return end
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
	if not say("COACH", "Feet apart. Knees loose. Hands up. Stay relaxed.", 3.2) then return end
	-- Uebergang: Kamera faehrt naeher, Abblende -> Titelkarte (laeuft nach dem Film weiter, bis das Tutorial steht)
	local fromCF = workspace.CurrentCamera.CFrame
	setShot(function(t) return fromCF * CFrame.new(0, 0, -t * 1.2), 42 end)
	fade(0, 0.7)
end

---------------------------------------------------------------------------------------------------- Zwischentitel zwischen Film, Tutorial und Sparring
-- Eigene Oberflaeche (bleibt nach dem Film bestehen): schwarz mit Titel, haelt kurz und blendet ins Spiel auf.
local function transition(title, subtitle, hold, fromBlack)
	local old = player.PlayerGui:FindFirstChild("CC_StoryTransition"); if old then old:Destroy() end
	local g = Instance.new("ScreenGui"); g.Name = "CC_StoryTransition"; g.IgnoreGuiInset = true; g.DisplayOrder = 80; g.ResetOnSpawn = false
	local bg = Instance.new("Frame"); bg.Size = UDim2.fromScale(1, 1); bg.BackgroundColor3 = Color3.new(0, 0, 0); bg.BorderSizePixel = 0
	bg.BackgroundTransparency = fromBlack and 0 or 1; bg.Parent = g
	local t = Instance.new("TextLabel"); t.BackgroundTransparency = 1; t.AnchorPoint = Vector2.new(0.5, 0.5); t.Position = UDim2.fromScale(0.5, 0.46)
	t.Size = UDim2.new(1, 0, 0, 70); t.Font = Enum.Font.GothamBlack; t.TextSize = 58; t.TextColor3 = Color3.fromRGB(240, 240, 244); t.Text = title
	t.TextTransparency = 1; t.Parent = bg
	local line = Instance.new("Frame"); line.AnchorPoint = Vector2.new(0.5, 0.5); line.Position = UDim2.fromScale(0.5, 0.53); line.Size = UDim2.fromOffset(0, 4)
	line.BackgroundColor3 = Color3.fromRGB(214, 44, 36); line.BorderSizePixel = 0; line.Parent = bg
	local s = Instance.new("TextLabel"); s.BackgroundTransparency = 1; s.AnchorPoint = Vector2.new(0.5, 0.5); s.Position = UDim2.fromScale(0.5, 0.59)
	s.Size = UDim2.new(1, 0, 0, 34); s.Font = Enum.Font.GothamMedium; s.TextSize = 26; s.TextColor3 = Color3.fromRGB(190, 196, 206); s.Text = subtitle or ""
	s.TextTransparency = 1; s.Parent = bg
	g.Parent = player.PlayerGui
	task.spawn(function()
		if not fromBlack then TweenService:Create(bg, TweenInfo.new(0.4), { BackgroundTransparency = 0.15 }):Play() end
		TweenService:Create(t, TweenInfo.new(0.5), { TextTransparency = 0 }):Play()
		TweenService:Create(line, TweenInfo.new(0.6, Enum.EasingStyle.Quart), { Size = UDim2.fromOffset(320, 4) }):Play()
		task.wait(0.25)
		TweenService:Create(s, TweenInfo.new(0.5), { TextTransparency = 0 }):Play()
		task.wait(hold or 2.0)
		for _, x in ipairs({ t, s }) do TweenService:Create(x, TweenInfo.new(0.4), { TextTransparency = 1 }):Play() end
		TweenService:Create(line, TweenInfo.new(0.4), { BackgroundTransparency = 1 }):Play()
		TweenService:Create(bg, TweenInfo.new(0.9), { BackgroundTransparency = 1 }):Play()
		task.wait(1.0); g:Destroy()
	end)
end

---------------------------------------------------------------------------------------------------- Abschluss nach dem ersten Sparring (Phase "outro")
local function runOutro()
	local plook = Look.sanitize(look()); for k, v in pairs(Look.DEFAULT) do if plook[k] == nil then plook[k] = v end end
	local PP, TP = Vector3.new(153, HRP_Y, 30), Vector3.new(160, HRP_Y, 30)
	local P = makeActor("PlayerFight", plook, {}, CFrame.lookAt(PP, TP), true)
	local T = makeActor("Coach", LOOK_COACH, OUT_COACH, CFrame.lookAt(TP, PP))
	local me = player.Character
	if me then for _, d in ipairs(me:GetDescendants()) do if d:IsA("BasePart") or d:IsA("Decal") then d.LocalTransparencyModifier = 1 end end end
	filmLight(Vector3.new(156, 13, 40), Vector3.new(156, 4, 30), 2.4, 34, 80)
	if not wait_(0.6) then return end
	setShot(function(t) local m = (head(P) + head(T)) / 2; return CFrame.lookAt(m + Vector3.new(0.8, -0.2, 11 - t * 0.25), m + Vector3.new(0, -0.7, 0)), 40 end)
	fade(1, 0.6)
	if not say("YOU", "Was that bad?", 1.6) then return end
	setShot(function(t) return CFrame.lookAt(head(P) + Vector3.new(-3.2, 0.1, 3.6), head(T) + Vector3.new(0, -0.3, 0)), 36 end)
	if not say("COACH", "That was your first day. You didn't quit.", 2.4) then return end
	if not wait_(1.0) then return end
	if not say("COACH", "Same time tomorrow?", 1.4) then return end
	setShot(function(t) return CFrame.lookAt(head(T) + Vector3.new(3.2, 0.1, 3.6), head(P) + Vector3.new(0, -0.3, 0)), 36 end)
	P.play("Story_P_Nod", 0.15)
	if not wait_(1.4) then return end
	setShot(function(t) local m = (head(P) + head(T)) / 2; return CFrame.lookAt(m + Vector3.new(0.8, 0.4, 12), m + Vector3.new(0, -0.7, 0)), 42 end)
	if not say("COACH", "Then let me show you how your career works.", 2.4) then return end
	fade(0, 0.5)
end

---------------------------------------------------------------------------------------------------- Erklaerungen beim ersten Mal (Kamera-Rundflug, Hinweise)
-- Flags im Profil (onb): gymTour, sigTour, onlineHint, editorHint, focusTip. Gespeichert ueber CC_Story "explained".
local function flyShot(fromCF, toCF, dur)
	setShot(function(t) local u = math.min(t / dur, 1); u = u * u * (3 - 2 * u); return fromCF:Lerp(toCF, u), 50 end)
end
local GYM_TOUR = {
	{ cam = Vector3.new(103, 11, 6), at = Vector3.new(103, 5, -16), text = "Heavy bags build punching power. Walk up and press E." },
	{ cam = Vector3.new(210, 10, 22), at = Vector3.new(225, 3, 8), text = "The bench and dumbbells make your strikes hit even harder." },
	{ cam = Vector3.new(205, 10, 26), at = Vector3.new(210, 2, 43), text = "Treadmills and mats build cardio — so you don't gas out in a fight." },
	{ cam = Vector3.new(118, 10, -48), at = Vector3.new(100, 2, -66), text = "Wrestling and grappling you learn in the fight: takedowns, positions, submissions." },
	{ cam = Vector3.new(112, 9, 26), at = Vector3.new(100, 5, 16), text = "These are the style coaches. Each one teaches you a signature move." },
	{ cam = Vector3.new(196, 9, -34), at = Vector3.new(208, 3, -46), text = "Start training fights at the coach's desk. Your career is in the menu (M)." },
	{ cam = Vector3.new(160, 14, 26), at = Vector3.new(160, 4, -10), text = "And this octagon is where you fight — training, career and online." },
}
local function runTour(stops)
	local cam = workspace.CurrentCamera
	local last = cam.CFrame
	if not fade(1, 0.01) then return end
	for _, s in ipairs(stops) do
		local goal = CFrame.lookAt(s.cam, s.at)
		flyShot(last, goal, 1.3)
		if not wait_(1.3) then return end
		setShot(function(t) return goal * CFrame.new(0, 0, -t * 0.25), 50 end)
		if not say("COACH", s.text, 1.2 + #s.text * 0.05) then return end
		last = goal
	end
end
local function nearestTrainer()
	local hold = workspace:FindFirstChild("CC_StyleTrainersGym")
	local me = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	local best, bd
	if hold and me then for _, m in ipairs(hold:GetChildren()) do
		local d = (m:GetPivot().Position - me.Position).Magnitude
		if not bd or d < bd then best, bd = m, d end
	end end
	return best
end
local function runSigTour()
	local t = nearestTrainer(); if not t then return end
	local p = t:GetPivot()
	local headP = p.Position + Vector3.new(0, 5, 0)
	local goal = CFrame.lookAt(headP + p.LookVector * 9 + p.RightVector * 3 + Vector3.new(0, 0.8, 0), headP - Vector3.new(0, 0.6, 0))
	flyShot(workspace.CurrentCamera.CFrame, goal, 1.0)
	fade(1, 0.01)
	if not wait_(1.0) then return end
	setShot(function(tt) return goal * CFrame.new(0, 0, -tt * 0.2), 46 end)
	for _, line in ipairs({
		"Every style coach has a signature — a special attack.",
		"First finish his quests. Then challenge him to a final fight.",
		"Win, and the signature is yours. Equip it right here.",
		"In a fight, landing hits and defending fills your focus bar. When it's full: press G." }) do
		if not say("COACH", line, 1.2 + #line * 0.05) then return end
	end
end
local function onbFlags() local ok, t = pcall(function() return HS:JSONDecode(player:GetAttribute("CC_Onb") or "{}") end); return ok and type(t) == "table" and t or {} end
local function localTip(text, kind) player:SetAttribute("CC_CoachTip", HS:JSONEncode({ text = text, kind = kind or "tip", t = workspace:GetServerTimeNow() })) end
local explained = {}
local function markExplained(key) explained[key] = true; remote:FireServer("explained", key) end

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
		if shake > 0.01 then
			local k = shake * 0.35
			cf = cf * CFrame.new((math.random() - 0.5) * k, (math.random() - 0.5) * k, 0) * CFrame.Angles(0, 0, (math.random() - 0.5) * k * 0.08)
			shake = shake * 0.9
		end
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
	cardFollow = nil; shot = nil; shake = 0; cardView = nil
	local front = workspace:FindFirstChild("CC_StorySchool") and workspace.CC_StorySchool:FindFirstChild("GymFront")
	schoolLight(false)
	if gui then gui:Destroy(); gui = nil end
	local cam = workspace.CurrentCamera
	cam.CameraType = Enum.CameraType.Custom; cam.FieldOfView = saved and saved.fov or 70
	local hum = player.Character and player.Character:FindFirstChildOfClass("Humanoid"); if hum then cam.CameraSubject = hum end
	if saved then for g in pairs(saved.guis) do if g.Parent then g.Enabled = true end end end
	local me = player.Character
	if me then for _, d in ipairs(me:GetDescendants()) do if d:IsA("BasePart") or d:IsA("Decal") then d.LocalTransparencyModifier = 0 end end end
	player:SetAttribute("CC_UIBlock", nil)
	saved = nil
end
local function play(mode)
	if running then return end
	begin()
	if mode == "outro" then schoolLight(false) end
	if mode == "tour" or mode == "sig" then
		schoolLight(false)
		local me = player.Character                                      -- eigener Kaempfer stoert die Kamerafahrt nicht
		if me then for _, d in ipairs(me:GetDescendants()) do if d:IsA("BasePart") or d:IsA("Decal") then d.LocalTransparencyModifier = 1 end end end
	end
	local fn = (mode == "outro" and runOutro) or (mode == "tour" and function() runTour(GYM_TOUR) end) or (mode == "sig" and runSigTour) or runFilm
	local ok, err = pcall(fn)
	if not ok then warn("[Story] Fehler: " .. tostring(err)) end
	local skipped = skipFlag
	finish(skipped)
	if mode == "onboarding" then transition("DAY 1", "FIRST LESSON", 2.2, true)
	elseif mode == "outro" then transition("YOUR CAREER", "From nobody to champion", 1.6, true) end
	if mode == "onboarding" then remote:FireServer("done", skipped and "skip" or "ok") end
	if mode == "outro" then remote:FireServer("outroDone") end
end

remote.OnClientEvent:Connect(function(what) if what == "play" then task.spawn(play, "replay") end end)
local lastPhase = player:GetAttribute("CC_OnbPhase")
local function check()
	local ph = player:GetAttribute("CC_OnbPhase")
	if ph == "story" and not running then task.spawn(play, "onboarding") end
	if ph == "outro" and not running then task.spawn(play, "outro") end
	if ph == "spar" and lastPhase ~= "spar" then transition("FIRST SPARRING", "Show what you learned", 1.6, false) end
	lastPhase = ph
end
player:GetAttributeChangedSignal("CC_OnbPhase"):Connect(check)
task.defer(check)

---------------------------------------------------------------------------------------------------- Beobachter fuer die Erklaerungen beim ersten Mal
local function inGym()
	local r = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	return r and r.Position.X > 70 and r.Position.X < 250 and r.Position.Z > -86 and r.Position.Z < 64
end
local function menuOpen()
	local mg = player.PlayerGui:FindFirstChild("CC_MainMenuGui")
	local m = mg and mg:FindFirstChild("Canvas") and mg.Canvas:FindFirstChild("Menu")
	return mg and mg.Enabled and m and m.Visible
end
local function idle()
	local c = player.Character
	return not running and (player:GetAttribute("CC_OnbPhase") or "") == "" and not player:GetAttribute("CC_UIBlock") and not player:GetAttribute("CC_Queue")
		and not player:GetAttribute("CC_Minigame") and c and not c:GetAttribute("CC_Opponent") and not c:GetAttribute("CC_BagPractice")
end
-- 1) Gym-Rundflug: erstes Mal frei im Gym (Menue zu, nichts anderes aktiv)
task.spawn(function()
	while true do
		task.wait(1.5)
		local f = onbFlags()
		if player:GetAttribute("CC_Onb") and f.gymTour == false and not explained.gymTour and idle() and inGym() and not menuOpen() then
			task.wait(1.0)
			if idle() and not menuOpen() then play("tour"); markExplained("gymTour") end
		end
		if explained.gymTour or f.gymTour == true then break end
	end
end)
-- 2) Signaturen: erstes Trainer-Panel -> erst Erklaerung mit Kamera auf den Trainer, dann das Panel
task.spawn(function()
	local tp = player:WaitForChild("PlayerGui"):WaitForChild("CC_TrainerPanel", 60)
	if not tp then return end
	tp:GetPropertyChangedSignal("Enabled"):Connect(function()
		if not tp.Enabled or explained.sigTour or onbFlags().sigTour ~= false or running then return end
		explained.sigTour = true
		tp.Enabled = false
		task.spawn(function()
			local t0 = os.clock()
			while player:GetAttribute("CC_UIBlock") and os.clock() - t0 < 20 do task.wait(0.2) end   -- Begruessungsszene abwarten
			play("sig"); markExplained("sigTour")
			tp.Enabled = true
		end)
	end)
end)
-- 3) Online / Mein Kaempfer: kurzer Trainer-Hinweis beim ersten Oeffnen
task.spawn(function()
	local mg = player:WaitForChild("PlayerGui"):WaitForChild("CC_MainMenuGui", 60)
	local area = mg and mg:WaitForChild("Canvas", 10) and mg.Canvas:WaitForChild("Menu", 10) and mg.Canvas.Menu:WaitForChild("Area", 10)
	if not area then return end
	local HINTS = {
		online = { "onlineHint", "Online: start a search and you fight the next free player. Same base stats for everyone." },
		fighter = { "editorHint", "My Fighter: change hair, beard, face and skin anytime. More unlocks as you progress." },
	}
	for page, h in pairs(HINTS) do
		local fr = area:FindFirstChild(page) or area.Parent:FindFirstChild(page) or area:WaitForChild(page, 10)
		if fr then fr:GetPropertyChangedSignal("Visible"):Connect(function()
			if fr.Visible and not explained[h[1]] and onbFlags()[h[1]] == false then localTip(h[2]); markExplained(h[1]) end
		end) end
	end
end)
-- 4) Fokus voll im Kampf: einmal erklaeren, wie die Signatur ausgeloest wird
local function hookFocus(c)
	c:GetAttributeChangedSignal("CC_Focus"):Connect(function()
		if (c:GetAttribute("CC_Focus") or 0) >= 100 and not explained.focusTip and onbFlags().focusTip == false then
			localTip("Focus full! Press G for your signature.", "good"); markExplained("focusTip")
		end
	end)
end
player.CharacterAdded:Connect(hookFocus); if player.Character then hookFocus(player.Character) end
