-- StarterGui.CC_MainMenuGui.MainMenu (LocalScript in einer ScreenGui)
-- Ladebildschirm, Hauptmenue, Navigation und Charakter-Editor (UI-Ueberarbeitung Schritt 1+2, Designsystem: ReplicatedStorage.CC_UI).
-- Hintergrund: die Arena (Blick vom Einlaufsteg auf den Kaefig) mit blauer Fight-Night-Beleuchtung (nur lokal, solange
-- das Menue offen ist). Rechts der eigene Kaempfer in Kampfhaltung: lokale Kopie des Charakters, nur fuer diesen Spieler.
-- Der echte Charakter bleibt im Gym.
-- Waehrend das Menue offen ist (Attribut CC_UIBlock am Spieler, nur lokal): keine Kampf-Eingaben, kein Laufen,
-- kein HUD, keine Gym-Interaktionen. Ein Kampf (CC_Opponent) oder ein Minispiel (CC_Minigame) schliesst das Menue.
-- Menuepunkte:
--   KARRIERE      = Fortschritt (Level, Werte, Bilanz) + ins Gym. Eine echte Karriere (Gegnerliste, Titel) gibt es noch nicht.
--   ONLINE        = Warteschlange gegen Spieler (ReplicatedStorage.CC_Menu "pvp" / "cancel")
--   TRAINING      = Trainingskampf (CC_Menu "training") oder Gym-Training (Menue schliessen)
--   MEIN KAEMPFER = Charakter-Editor: Vorschau nur lokal (ReplicatedStorage.CC_LookShared + CC_CustomShared),
--                   erst SPEICHERN schickt das Aussehen an den Server (CC_Look) -> Profil speichert sofort (CC_SaveStatus).
--   EINSTELLUNGEN = noch nicht vorhanden (als "BALD" markiert)
-- Spiegel/Spind im Gym (Attribut CC_OpenCustomize vom Server) oeffnen direkt den Editor.
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local CAS = game:GetService("ContextActionService")
local GuiService = game:GetService("GuiService")
local TweenService = game:GetService("TweenService")
local UIS = game:GetService("UserInputService")
local PPS = game:GetService("ProximityPromptService")
local Lighting = game:GetService("Lighting")
local HS = game:GetService("HttpService")

local player = Players.LocalPlayer
local UI = require(RS:WaitForChild("CC_UI"))
local Look = require(RS:WaitForChild("CC_LookShared"))
local C, F = UI.C, UI.F
local menuEvent = RS:WaitForChild("CC_Menu")
local lookEvent = RS:WaitForChild("CC_Look")
local state = RS:WaitForChild("CC_MatchState")
local gui = script.Parent
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = true
gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
gui.DisplayOrder = 20

-- Buehne in der Arena (Einlaufsteg suedlich vom Kaefig)
local CAM_POS = Vector3.new(1.8, 4.0, -48)
local CAM_AIM = Vector3.new(0.2, 5.0, 0)
local FIGHTER_POS = Vector3.new(-2.6, 0, -35)
local CAM_FOV = 45
local FIGHTER_YAW = 28            -- Grad zur Kamera gedreht
local GUARD_LOWER = -22           -- Oberarme etwas senken, damit die Handschuhe das Gesicht nicht verdecken (nur Menue-Kopie)

local canvas = UI.new("Frame", { Name = "Canvas", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Parent = gui })
UI.autoscale(canvas, 720)

---------------------------------------------------------------------------------------------------
-- Hauptmenue-Ebene
---------------------------------------------------------------------------------------------------
local menu = UI.new("Frame", { Name = "Menu", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Visible = false, Parent = canvas })
local shadeL = UI.new("Frame", { BackgroundColor3 = C.bg0, BorderSizePixel = 0, Size = UDim2.fromScale(0.6, 1), Parent = menu })
UI.new("UIGradient", { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.05), NumberSequenceKeypoint.new(0.6, 0.35), NumberSequenceKeypoint.new(1, 1) }), Parent = shadeL })
local shadeB = UI.new("Frame", { BackgroundColor3 = C.bg0, BorderSizePixel = 0, AnchorPoint = Vector2.new(0, 1), Position = UDim2.fromScale(0, 1), Size = UDim2.new(1, 0, 0, 150), Parent = menu })
UI.new("UIGradient", { Rotation = -90, Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.15), NumberSequenceKeypoint.new(1, 1) }), Parent = shadeB })

local function logo(parent, pos, size, anchor)
	local f = UI.new("Frame", { BackgroundTransparency = 1, Position = pos, AnchorPoint = anchor or Vector2.zero, Size = UDim2.fromOffset(600, size + 30), Parent = parent })
	local words = UI.new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, size + 6), Parent = f })
	UI.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 12), SortOrder = Enum.SortOrder.LayoutOrder,
		HorizontalAlignment = anchor and anchor.X == 0.5 and Enum.HorizontalAlignment.Center or Enum.HorizontalAlignment.Left, Parent = words })
	UI.label({ Text = "CAGE", FontFace = F.title, TextSize = size, TextColor3 = C.red, AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, size + 6), TextWrapped = false, LayoutOrder = 1, Parent = words })
	UI.label({ Text = "CHAMPIONS", FontFace = F.title, TextSize = size, TextColor3 = C.text, AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, size + 6), TextWrapped = false, LayoutOrder = 2, Parent = words })
	UI.new("Frame", { BackgroundColor3 = C.red, BorderSizePixel = 0, Position = UDim2.fromOffset(anchor and 150 or 2, size + 12), Size = UDim2.fromOffset(anchor and 300 or 120, 4), Parent = f })
	return f
end
local menuLogo = logo(menu, UDim2.fromOffset(56, 34), 46)

-- Bereich links: Navigation bzw. Unterseite
local area = UI.new("Frame", { Name = "Area", BackgroundTransparency = 1, Position = UDim2.fromOffset(56, 132), Size = UDim2.fromOffset(470, 440), Parent = menu })

-- Profil-Karte unten links
local profile = UI.panel({ Name = "Profile", AnchorPoint = Vector2.new(0, 1), Position = UDim2.new(0, 56, 1, -32), Size = UDim2.fromOffset(470, 96), Parent = menu })
UI.label({ Text = player.DisplayName, FontFace = F.head, TextSize = 22, Position = UDim2.fromOffset(20, 10), Size = UDim2.new(1, -40, 0, 28), Parent = profile })
local pLevel = UI.label({ Text = "", FontFace = F.bold, TextSize = 17, TextColor3 = C.gold, TextXAlignment = Enum.TextXAlignment.Right, Position = UDim2.fromOffset(20, 12), Size = UDim2.new(1, -40, 0, 24), Parent = profile })
local _, pXP = UI.bar({ Position = UDim2.fromOffset(20, 44), Size = UDim2.new(1, -40, 0, 6), Parent = profile }, C.gold)
local pInfo = UI.label({ Text = "", TextSize = 16, TextColor3 = C.dim, Position = UDim2.fromOffset(20, 58), Size = UDim2.new(1, -40, 0, 26), Parent = profile })

local menuHints = UI.hints({ AnchorPoint = Vector2.new(1, 1), Position = UDim2.new(1, -40, 1, -32), Entries = {
	{ pc = "KLICK", pad = "A", text = "Auswählen" }, { pc = "RÜCKTASTE", pad = "B", text = "Zurück" } }, Parent = menu })

local status = UI.panel({ Name = "Status", AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0, 34), Size = UDim2.fromOffset(500, 54), Visible = false, Parent = menu })
local statusL = UI.label({ Text = "", FontFace = F.bold, TextSize = 18, TextXAlignment = Enum.TextXAlignment.Center, Size = UDim2.fromScale(1, 1), Parent = status })

---------------------------------------------------------------------------------------------------
-- Seiten
---------------------------------------------------------------------------------------------------
local pages, stack = {}, {}
local open, close, go, back

local function page(name, parent)
	local f = UI.new("Frame", { Name = name, BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Visible = false, Parent = parent or area })
	if not parent then UI.new("UIListLayout", { Padding = UDim.new(0, 10), SortOrder = Enum.SortOrder.LayoutOrder, Parent = f }) end
	pages[name] = f
	return f
end
local function header(p, title, order)
	local h = UI.new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 48), LayoutOrder = order or 0, Parent = p })
	UI.button({ Icon = "back", Style = "ghost", Size = UDim2.fromOffset(48, 46), Name = "Back", OnClick = function() back() end, Parent = h })
	UI.label({ Text = title, FontFace = F.title, TextSize = 34, Position = UDim2.fromOffset(62, 0), Size = UDim2.new(1, -62, 1, 0), TextWrapped = false, Parent = h })
	return h
end
local function card(p, order, h)
	local c = UI.panel({ Size = UDim2.new(1, 0, 0, h), LayoutOrder = order, Parent = p })
	UI.new("UIPadding", { PaddingLeft = UDim.new(0, 18), PaddingRight = UDim.new(0, 18), PaddingTop = UDim.new(0, 14), PaddingBottom = UDim.new(0, 14), Parent = c })
	return c
end

-- Start
local home = page("home")
local navButtons = {}
local function nav(order, text, sub, icon, fn, disabled, badge)
	local b = UI.button({ Style = "nav", Text = text, Sub = sub, Icon = icon, LayoutOrder = order, OnClick = fn, Disabled = disabled, Badge = badge, Parent = home })
	table.insert(navButtons, b)
	return b
end
nav(1, "KARRIERE", "Fortschritt · Werte · Bilanz", "trophy", function() go("career") end)
nav(2, "ONLINE", "Gegen echte Spieler kämpfen", "globe", function() go("online") end)
nav(3, "TRAINING", "Trainingskampf oder Gym", "dumbbell", function() go("training") end)
nav(4, "MEIN KÄMPFER", "Aussehen anpassen", "fighter", function() go("fighter") end)
nav(5, "EINSTELLUNGEN", "Noch nicht verfügbar", "gear", nil, true, "BALD")

-- Karriere (= ehrlicher Fortschritt; eine echte Karriere gibt es noch nicht)
local career = page("career")
header(career, "KARRIERE")
local cStats = card(career, 1, 262)
UI.new("UIListLayout", { Padding = UDim.new(0, 6), SortOrder = Enum.SortOrder.LayoutOrder, Parent = cStats })
local cLevel = UI.label({ Text = "", FontFace = F.head, TextSize = 20, TextColor3 = C.gold, LayoutOrder = 1, Parent = cStats })
local _, cXP = UI.bar({ LayoutOrder = 2, Parent = cStats }, C.gold)
local STATS = { { "Power", "Schlagkraft" }, { "Cardio", "Kondition" }, { "Wrestling", "Ringen" }, { "Grappling", "Bodenkampf" } }
local statRows = {}
for i, s in ipairs(STATS) do
	local r = UI.new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 36), LayoutOrder = 2 + i, Parent = cStats })
	UI.label({ Text = s[2], FontFace = F.bold, TextSize = 17, Size = UDim2.new(0.5, 0, 0, 24), Parent = r })
	local v = UI.label({ Text = "", FontFace = F.bold, TextSize = 17, TextXAlignment = Enum.TextXAlignment.Right, Size = UDim2.new(1, 0, 0, 24), Parent = r })
	local _, fill = UI.bar({ Position = UDim2.fromOffset(0, 27), Size = UDim2.new(1, 0, 0, 5), Parent = r }, C.blue)
	statRows[s[1]] = { v, fill }
end
local cRecord = UI.label({ Text = "", TextSize = 16, TextColor3 = C.dim, LayoutOrder = 9, Parent = cStats })
local cNote = card(career, 2, 74)
UI.label({ Text = "Werte steigen durch Gym-Training und Kämpfe. Eine Karriere mit Gegnerliste und Titeln gibt es noch nicht.",
	TextSize = 16, TextColor3 = C.dim, Size = UDim2.fromScale(1, 1), Parent = cNote })
UI.button({ Style = "primary", Text = "INS GYM", Icon = "dumbbell", LayoutOrder = 3, OnClick = function() close() end, Parent = career })

-- Online
local online = page("online")
header(online, "ONLINE")
local oCard = card(online, 1, 100)
UI.label({ Text = "SCHNELLER KAMPF", FontFace = F.head, TextSize = 19, Size = UDim2.new(1, 0, 0, 26), Parent = oCard })
UI.label({ Text = "Gegen den nächsten Spieler in der Warteschlange. 3 Runden, je 2 Minuten.",
	TextSize = 16, TextColor3 = C.dim, Position = UDim2.fromOffset(0, 30), Size = UDim2.new(1, 0, 0, 40), Parent = oCard })
local oState = UI.label({ Text = "", FontFace = F.bold, TextSize = 17, LayoutOrder = 2, Size = UDim2.new(1, 0, 0, 28), Parent = online })
local bSearch = UI.button({ Style = "primary", Text = "SUCHE STARTEN", Icon = "search", LayoutOrder = 3, OnClick = function() menuEvent:FireServer("pvp") end, Parent = online })
local bCancel = UI.button({ Style = "danger", Text = "SUCHE ABBRECHEN", Icon = "close", LayoutOrder = 4, OnClick = function() menuEvent:FireServer("cancel") end, Parent = online })
UI.button({ Style = "secondary", Text = "GEWERTET", Sub = "Rangliste gibt es noch nicht", Icon = "star", LayoutOrder = 5, Disabled = true, Badge = "NICHT VERFÜGBAR",
	Size = UDim2.new(1, 0, 0, 66), Parent = online })

-- Training
local training = page("training")
header(training, "TRAINING")
-- Stufe des Trainingsgegners (Server prueft den Wert): Passiv / Anfaenger / Fortgeschritten
local dummyLevel = player:GetAttribute("CC_DummyLevel") or "anfaenger"
local lvRow = UI.new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 44), LayoutOrder = 1, Parent = training })
UI.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 8), SortOrder = Enum.SortOrder.LayoutOrder, Parent = lvRow })
local lvButtons = {}
for i, e in ipairs({ { "passiv", "PASSIV" }, { "anfaenger", "ANFÄNGER" }, { "fortgeschritten", "PROFI" } }) do
	local b = UI.button({ Style = "ghost", Text = e[2], Size = UDim2.new(1 / 3, -6, 1, 0), LayoutOrder = i, Name = "Lv_" .. e[1], Parent = lvRow,
		OnClick = function() dummyLevel = e[1]; for k, x in pairs(lvButtons) do x:SetAttribute("Selected", k == dummyLevel) end end })
	lvButtons[e[1]] = b
	b:SetAttribute("Selected", e[1] == dummyLevel)
end
local bFight = UI.button({ Style = "nav", Text = "TRAININGSKAMPF", Sub = "Gegen den Trainingsgegner · ohne Bilanz", Icon = "glove", LayoutOrder = 2,
	OnClick = function() menuEvent:FireServer("training", dummyLevel) end, Parent = training })
UI.button({ Style = "nav", Text = "GYM-TRAINING", Sub = "Minispiele an den Stationen", Icon = "dumbbell", LayoutOrder = 3,
	OnClick = function() close() end, Parent = training })
UI.button({ Style = "ghost", Text = "GRUNDLAGEN WIEDERHOLEN (TUTORIAL)", Icon = "help", LayoutOrder = 6, Name = "Tutorial",
	OnClick = function() close(); RS:WaitForChild("CC_Tutorial"):FireServer("openWelcome") end, Parent = training })
local tState = UI.label({ Text = "", FontFace = F.bold, TextSize = 17, LayoutOrder = 4, Size = UDim2.new(1, 0, 0, 28), Parent = training })
local bTCancel = UI.button({ Style = "danger", Text = "ABBRECHEN", Icon = "close", LayoutOrder = 5, OnClick = function() menuEvent:FireServer("cancel") end, Parent = training })

---------------------------------------------------------------------------------------------------
-- Buehne: Kopie des eigenen Kaempfers in Kampfhaltung, Kamera auf dem Einlaufsteg, Fight-Night-Licht
---------------------------------------------------------------------------------------------------
local stage, stageTrack
local stageYaw = 0
local stageBones = {}
local draft = Look.copy(Look.DEFAULT)      -- Editor-Entwurf (Vorschau)
local saved = Look.copy(Look.DEFAULT)      -- zuletzt gespeichertes Aussehen
local rayParams = RaycastParams.new(); rayParams.FilterType = Enum.RaycastFilterType.Exclude
local function floorY(pos, ignore)
	rayParams.FilterDescendantsInstances = ignore
	local hit = workspace:Raycast(pos + Vector3.new(0, 4, 0), Vector3.new(0, -30, 0), rayParams)
	return hit and hit.Position.Y
end
local function serverLook()
	local ok, t = pcall(function() return HS:JSONDecode(player:GetAttribute("CC_Look") or "") end)
	local l = Look.copy(Look.DEFAULT)
	if ok and type(t) == "table" then for k, v in pairs(Look.sanitize(t)) do l[k] = v end end
	return l
end
local function templates() return RS:FindFirstChild("CC_CustomShared") end

-- Kopie des echten Charakters ohne Skripte/Attribute
local function cloneFighter()
	local char = player.Character
	if not (char and char:FindFirstChild("HumanoidRootPart") and char:FindFirstChildOfClass("Humanoid")) then return nil end
	char.Archivable = true
	local ok, c = pcall(function() return char:Clone() end)
	char.Archivable = false
	if not ok or not c then return nil end
	for _, d in ipairs(c:GetDescendants()) do
		if d:IsA("BaseScript") or d:IsA("ProximityPrompt") or d:IsA("BillboardGui") or d:IsA("Sound") then d:Destroy() end
	end
	for a in pairs(c:GetAttributes()) do if a:sub(1, 3) == "CC_" then c:SetAttribute(a, nil) end end
	local h = c:FindFirstChildOfClass("Humanoid")
	h.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	h.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
	c.HumanoidRootPart.Anchored = true
	return c
end
local function stageCF(base)
	return CFrame.lookAt(base, Vector3.new(CAM_POS.X, base.Y, CAM_POS.Z)) * CFrame.Angles(0, math.rad(FIGHTER_YAW + stageYaw), 0)
end
local function buildStage()
	if stage then stage:Destroy(); stage = nil end
	local char = player.Character
	local c = cloneFighter()
	if not c then return end
	Look.apply(c, draft, templates())
	c.Name = "CC_MenuFighter"
	local root = char.HumanoidRootPart
	local gymFloor = floorY(root.Position, { char, workspace:FindFirstChild("CC_Props") })
	local hipOff = gymFloor and (root.Position.Y - gymFloor) or 3
	local base = Vector3.new(FIGHTER_POS.X, (floorY(FIGHTER_POS, { char }) or FIGHTER_POS.Y) + hipOff, FIGHTER_POS.Z)
	c:PivotTo(stageCF(base))
	c.Parent = workspace
	stage = c
	stageBones = {}
	for _, b in ipairs(c:GetDescendants()) do if b:IsA("Bone") then stageBones[b.Name] = b end end
	local id = RS:GetAttribute("CC_AnimId_Fighter_Idle_v08")
	if id then
		local h = c:FindFirstChildOfClass("Humanoid")
		local an = h:FindFirstChildOfClass("Animator") or Instance.new("Animator", h)
		local a = Instance.new("Animation"); a.AnimationId = "rbxassetid://" .. tostring(id)
		stageTrack = an:LoadAnimation(a); stageTrack.Looped = true; stageTrack:Play(0)
	end
end
local function setStageYaw(y)
	stageYaw = y
	if stage then stage:PivotTo(stageCF(stage:GetPivot().Position)) end
end
-- Vorschau aktualisieren (nur Kopf-Teile und Farben, ohne neue Kopie)
local function previewDraft() if stage then Look.apply(stage, draft, templates()) end end

-- Kamera: Hauptmenue = weite Einstellung; Editor = naeher, Kaempfer rechts gross
local cam = workspace.CurrentCamera
local camMode = "menu"
local camCF
local function targetCam()
	if camMode == "editor" and stage then
		local base = stage:GetPivot().Position
		local toCam = Vector3.new(CAM_POS.X - base.X, 0, CAM_POS.Z - base.Z).Unit
		local pos = base + toCam * 14 + Vector3.new(0, 1.4, 0)
		local right = (base - pos):Cross(Vector3.yAxis).Unit
		return CFrame.lookAt(pos, base + Vector3.new(0, 1.0, 0) - right * 4.6)
	end
	local t = os.clock()
	local sway = Vector3.new(math.sin(t * 0.25) * 0.25, math.sin(t * 0.33) * 0.08, 0)   -- leichte Kamerabewegung
	return CFrame.lookAt(CAM_POS + sway, CAM_AIM)
end
local function stageCamera(dt)
	cam.CameraType = Enum.CameraType.Scriptable
	cam.FieldOfView = CAM_FOV
	local goal = targetCam()
	camCF = camCF and camCF:Lerp(goal, 1 - math.exp(-6 * dt)) or goal
	cam.CFrame = camCF
	-- Haltung der Menue-Kopie: Deckung etwas tiefer, Gesicht frei (nach der Animation, nur lokal)
	local l, r = stageBones.LeftUpperArm, stageBones.RightUpperArm
	if l and r then
		l.Transform = l.Transform * CFrame.Angles(0, 0, math.rad(GUARD_LOWER))
		r.Transform = r.Transform * CFrame.Angles(0, 0, math.rad(-GUARD_LOWER))
	end
end

-- Fight-Night-Licht: dunkle Halle, blaues Licht, heller Kaefig (nur lokal)
local lightSaved, lightFolder
local function fightNight(on)
	if on then
		if lightSaved then return end
		local dof = Lighting:FindFirstChildOfClass("DepthOfFieldEffect")
		lightSaved = { Lighting.ClockTime, Lighting.Brightness, Lighting.Ambient, Lighting.OutdoorAmbient, Lighting.ExposureCompensation,
			dof and { dof.Enabled, dof.FarIntensity, dof.FocusDistance, dof.InFocusRadius, dof.NearIntensity } }
		Lighting.ClockTime = 0; Lighting.Brightness = 1; Lighting.ExposureCompensation = 0
		Lighting.Ambient = Color3.fromRGB(26, 36, 70); Lighting.OutdoorAmbient = Color3.fromRGB(30, 44, 90)
		if dof then dof.Enabled = true; dof.FarIntensity = 0.08; dof.FocusDistance = (FIGHTER_POS - CAM_POS).Magnitude; dof.InFocusRadius = 12; dof.NearIntensity = 0 end
		lightFolder = Instance.new("Folder"); lightFolder.Name = "CC_MenuLights"; lightFolder.Parent = workspace
		local cc = Instance.new("ColorCorrectionEffect"); cc.Name = "CC_MenuGrade"; cc.TintColor = Color3.fromRGB(228, 232, 255); cc.Contrast = 0.15; cc.Saturation = 0.1
		cc.Parent = Lighting
		local function light(pos, color, br, range, spot)
			local p = Instance.new("Part"); p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.Transparency = 1
			p.Size = Vector3.one; p.Position = pos; p.Parent = lightFolder
			local l = Instance.new(spot and "SpotLight" or "PointLight"); l.Color = color; l.Brightness = br; l.Range = range; l.Shadows = false
			if spot then l.Face = Enum.NormalId.Bottom; l.Angle = 70 end
			l.Parent = p
		end
		light(Vector3.new(0, 20, 0), Color3.fromRGB(235, 240, 255), 3, 40, true)            -- Kaefig
		for _, x in ipairs({ -26, 26 }) do for _, z in ipairs({ -20, 0, 20 }) do light(Vector3.new(x, 8, z), Color3.fromRGB(40, 90, 255), 3, 24) end end
		light(Vector3.new(0, 10, 30), Color3.fromRGB(40, 90, 255), 4, 30)
		light(Vector3.new(-6, 7, -31), Color3.fromRGB(60, 120, 255), 2.5, 14)                -- Kantenlicht hinter dem Kaempfer
		light(Vector3.new(1, 6, -41), Color3.fromRGB(255, 232, 210), 1.1, 14)                 -- Fuelllicht von vorn
	elseif lightSaved then
		local s = lightSaved
		Lighting.ClockTime, Lighting.Brightness, Lighting.Ambient, Lighting.OutdoorAmbient, Lighting.ExposureCompensation = s[1], s[2], s[3], s[4], s[5]
		local dof = Lighting:FindFirstChildOfClass("DepthOfFieldEffect")
		if dof and s[6] then dof.Enabled, dof.FarIntensity, dof.FocusDistance, dof.InFocusRadius, dof.NearIntensity = table.unpack(s[6]) end
		local cc = Lighting:FindFirstChild("CC_MenuGrade"); if cc then cc:Destroy() end
		if lightFolder then lightFolder:Destroy(); lightFolder = nil end
		lightSaved = nil
	end
end

---------------------------------------------------------------------------------------------------
-- Charakter-Editor (Seite "fighter", eigene Vollbild-Ebene)
---------------------------------------------------------------------------------------------------
local editor = page("fighter", menu)
local edLeft = UI.new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(56, 34), Size = UDim2.fromOffset(250, 600), Parent = editor })
header(edLeft, "MEIN KÄMPFER").Size = UDim2.fromOffset(420, 48)
local catList = UI.new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 72), Size = UDim2.new(1, 0, 0, 520), Parent = edLeft })
UI.new("UIListLayout", { Padding = UDim.new(0, 8), SortOrder = Enum.SortOrder.LayoutOrder, Parent = catList })
local edMid = UI.panel({ Position = UDim2.fromOffset(326, 106), Size = UDim2.fromOffset(560, 380), Parent = editor })
UI.new("UIPadding", { PaddingLeft = UDim.new(0, 22), PaddingRight = UDim.new(0, 22), PaddingTop = UDim.new(0, 18), PaddingBottom = UDim.new(0, 18), Parent = edMid })
local midTitle = UI.label({ Text = "", FontFace = F.head, TextSize = 24, Size = UDim2.new(1, 0, 0, 30), Parent = edMid })
local midSub = UI.label({ Text = "", TextSize = 16, TextColor3 = C.dim, Position = UDim2.fromOffset(0, 32), Size = UDim2.new(1, 0, 0, 22), Parent = edMid })
local grid = UI.new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 66), Size = UDim2.new(1, 0, 0, 160), Parent = edMid })
UI.new("UIGridLayout", { CellSize = UDim2.fromOffset(119, 158), CellPadding = UDim2.fromOffset(10, 10), SortOrder = Enum.SortOrder.LayoutOrder, Parent = grid })
local colorTitle = UI.label({ Text = "", FontFace = F.bold, TextSize = 17, Position = UDim2.fromOffset(0, 240), Size = UDim2.new(1, 0, 0, 24), Parent = edMid })
local swRow = UI.new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 270), Size = UDim2.new(1, 0, 0, 60), Parent = edMid })
UI.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 6), SortOrder = Enum.SortOrder.LayoutOrder, Parent = swRow })
local lockedNote = UI.label({ Text = "", TextSize = 17, TextColor3 = C.dim, TextYAlignment = Enum.TextYAlignment.Top, Position = UDim2.fromOffset(0, 66), Size = UDim2.new(1, 0, 0, 120), Visible = false, Parent = edMid })

-- rechts: Drehen + Speichern
local edRight = UI.new("Frame", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(1, 1), Position = UDim2.new(1, -40, 1, -32), Size = UDim2.fromOffset(440, 190), Parent = editor })
local rotRow = UI.new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 50), Parent = edRight })
UI.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, HorizontalAlignment = Enum.HorizontalAlignment.Center, VerticalAlignment = Enum.VerticalAlignment.Center,
	Padding = UDim.new(0, 10), SortOrder = Enum.SortOrder.LayoutOrder, Parent = rotRow })
local rotHeld = 0
local function rotButton(icon, dir, order)
	local b = UI.button({ Icon = icon, Style = "ghost", Size = UDim2.fromOffset(50, 46), LayoutOrder = order, Name = "Rot" .. dir, Parent = rotRow })
	b.MouseButton1Down:Connect(function() rotHeld = dir end)
	b.MouseButton1Up:Connect(function() rotHeld = 0 end)
	b.MouseLeave:Connect(function() if rotHeld == dir then rotHeld = 0 end end)
	b.Activated:Connect(function() if UI.device() ~= "pc" then setStageYaw(stageYaw + dir * 30) end end)
	return b
end
rotButton("back", -1, 1)
local rotLabel = UI.new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromOffset(150, 40), LayoutOrder = 2, Parent = rotRow })
UI.icon("rotate", { Size = UDim2.fromOffset(26, 26), Position = UDim2.fromOffset(4, 7), ImageColor3 = C.dim, Parent = rotLabel })
local rotText = UI.label({ Text = "DREHEN", FontFace = F.bold, TextSize = 17, TextColor3 = C.dim, Position = UDim2.fromOffset(38, 0), Size = UDim2.new(1, -38, 1, 0), Parent = rotLabel })
rotButton("next", 1, 3)
local saveState = UI.label({ Text = "", FontFace = F.bold, TextSize = 17, TextXAlignment = Enum.TextXAlignment.Right, Position = UDim2.fromOffset(0, 62), Size = UDim2.new(1, 0, 0, 26), Parent = edRight })
local btnRow = UI.new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 96), Size = UDim2.new(1, 0, 0, 58), Parent = edRight })
UI.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, HorizontalAlignment = Enum.HorizontalAlignment.Right, Padding = UDim.new(0, 12), SortOrder = Enum.SortOrder.LayoutOrder, Parent = btnRow })
local saving = false
local pending                      -- gesendetes Aussehen (wird nach Bestaetigung zu saved)
local saveMsg, saveMsgColor
local bReset = UI.button({ Style = "secondary", Text = "ZURÜCKSETZEN", Size = UDim2.fromOffset(210, 58), LayoutOrder = 1, Parent = btnRow })
local bSave = UI.button({ Style = "primary", Text = "SPEICHERN", Icon = "check", Size = UDim2.fromOffset(210, 58), LayoutOrder = 2, Parent = btnRow })
local edHints = UI.hints({ AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, 0, 0, 162), Size = UDim2.new(1, 0, 0, 28), Entries = {
	{ pc = "Q / E", pad = "LB / RB", text = "Drehen" }, { pc = "RÜCKTASTE", pad = "B", text = "Zurück" } }, Parent = edRight })

-- Kategorien (nur vorhandene Anpassungen waehlbar)
local CATS = {
	{ id = "hair", name = "HAARE", icon = "hair", key = "hair", list = Look.HAIR, colors = "hairColor", colorTitle = "HAARFARBE" },
	{ id = "beard", name = "BART", icon = "beard", key = "beard", list = Look.BEARD, colors = "hairColor", colorTitle = "BARTFARBE (= HAARFARBE)" },
	{ id = "face", name = "GESICHT", icon = "face", key = "face", list = Look.FACE },
	{ id = "skin", name = "HAUTFARBE", icon = "skin", key = "skin", skin = true },
	{ id = "tattoo", name = "TATTOOS", icon = "star", locked = "Tattoos gibt es noch nicht." },
	{ id = "shorts", name = "SHORTS", icon = "shorts", locked = "Die Shorts-Farbe richtet sich nach der Ecke: rote Ecke rot, blaue Ecke blau. Eigene Shorts gibt es noch nicht." },
	{ id = "gloves", name = "HANDSCHUHE", icon = "glove", locked = "Andere Handschuhe gibt es noch nicht." },
}
local catButtons = {}
local currentCat
local cards, swatches = {}, {}

-- Vorschau-Karte: Kopfbild des Kaempfers mit der Variante (ViewportFrame, Teile per C0 platziert, da dort keine Physik laeuft)
local function cardModel(vp, look)
	for _, ch in ipairs(vp:GetChildren()) do ch:Destroy() end
	local c = cloneFighter()
	if not c then return end
	Look.apply(c, look, templates())
	c:PivotTo(CFrame.new())
	local hrp = c.HumanoidRootPart
	local sum, n = Vector3.zero, 0
	for _, p in ipairs(c:GetChildren()) do
		if p:IsA("BasePart") then
			local m = p:FindFirstChildOfClass("Motor6D")
			if m and m.Part0 == hrp then p.CFrame = hrp.CFrame * m.C0 * m.C1:Inverse() end
			if Look.isHead(p.Name) then sum += p.Position; n += 1 end
		end
	end
	local center = n > 0 and sum / n or (hrp.Position + Vector3.new(0, 3, 0))
	c.Parent = vp
	local vc = Instance.new("Camera"); vc.FieldOfView = 34
	local fwd = hrp.CFrame.LookVector
	vc.CFrame = CFrame.lookAt(center + fwd * 2.9 + hrp.CFrame.RightVector * 0.7 + Vector3.new(0, 0.15, 0), center - Vector3.new(0, 0.1, 0))
	vc.Parent = vp
	vp.CurrentCamera = vc
end

local function refreshSelection()
	for _, e in ipairs(cards) do e.btn:SetAttribute("Selected", draft[e.key] == e.value) end
	for _, e in ipairs(swatches) do e.btn:SetAttribute("Selected", draft[e.key] == e.value) end
end
local function showCat(cat)
	currentCat = cat
	for _, b in pairs(catButtons) do b:SetAttribute("Selected", b.Name == cat.id) end
	for _, ch in ipairs(grid:GetChildren()) do if ch:IsA("GuiObject") then ch:Destroy() end end
	for _, ch in ipairs(swRow:GetChildren()) do if ch:IsA("GuiObject") then ch:Destroy() end end
	cards, swatches = {}, {}
	midTitle.Text = cat.name
	edMid.Size = UDim2.fromOffset(560, cat.colors and 380 or (cat.locked and 200 or 270))
	lockedNote.Visible = cat.locked ~= nil
	lockedNote.Text = cat.locked or ""
	grid.Visible = cat.locked == nil
	colorTitle.Text = cat.colors and cat.colorTitle or ""
	if cat.locked then midSub.Text = "Nicht verfügbar"; return end
	if cat.skin then
		midSub.Text = #Look.SKIN .. " Hauttöne"
		for i = 1, #Look.SKIN do
			local l = Look.copy(draft); l.skin = i
			local b, vp = UI.optionCard({ Text = Look.SKIN_N[i], LayoutOrder = i, Parent = grid,
				OnClick = function() draft.skin = i; previewDraft(); refreshSelection() end })
			cardModel(vp, l)
			table.insert(cards, { btn = b, key = "skin", value = i })
		end
	else
		midSub.Text = #cat.list .. " Varianten"
		for i, v in ipairs(cat.list) do
			local l = Look.copy(draft); l[cat.key] = v
			if cat.key == "beard" or cat.key == "face" then l.hair = draft.hair end
			local b, vp = UI.optionCard({ Text = Look.NAMES[v] or v, LayoutOrder = i, Parent = grid,
				OnClick = function() draft[cat.key] = v; previewDraft(); refreshSelection() end })
			cardModel(vp, l)
			table.insert(cards, { btn = b, key = cat.key, value = v })
		end
	end
	if cat.colors then
		for i, col in ipairs(Look.HAIRCOL) do
			local b = UI.swatch({ Color = col, LayoutOrder = i, Name = Look.HAIRCOL_N[i], Parent = swRow,
				OnClick = function() draft.hairColor = i; previewDraft(); showCat(currentCat); UI.focus(swRow:FindFirstChild(Look.HAIRCOL_N[i])) end })
			table.insert(swatches, { btn = b, key = "hairColor", value = i })
		end
		colorTitle.Text = cat.colorTitle .. ":  " .. (Look.HAIRCOL_N[draft.hairColor] or "")
	end
	refreshSelection()
end
for i, cat in ipairs(CATS) do
	local b = UI.button({ Style = "secondary", Text = cat.name, Icon = cat.locked and "lock" or cat.icon, Size = UDim2.new(1, 0, 0, 58), LayoutOrder = i, Name = cat.id,
		OnClick = function() showCat(cat) end, Parent = catList })
	catButtons[cat.id] = b
end

local function dirty() return not Look.same(draft, saved) end
local function doSave()
	if saving or not dirty() then return end
	saving = true
	saveMsg, saveMsgColor = "Speichert …", C.dim
	pending = Look.copy(draft)
	lookEvent:FireServer(pending)
	task.delay(10, function() if saving then saving = false; saveMsg, saveMsgColor = "Keine Antwort vom Server – bitte erneut speichern.", C.warn end end)
end
bSave:SetAttribute("Disabled", true)
-- Einstieg (CC_Tutorial, Phase "editor"): Knopf heisst FERTIG, ist immer aktiv, speichert bei Aenderungen und schliesst das Menue
local onboarding = false
local function finishOnboarding()
	if not onboarding then return end
	onboarding = false
	doSave()
	RS:WaitForChild("CC_Tutorial"):FireServer("editorDone")
	bSave:FindFirstChildWhichIsA("TextLabel").Text = "SPEICHERN"
	close()
end
bSave.Activated:Connect(function() if onboarding then finishOnboarding() else doSave() end end)
bReset.Activated:Connect(function()
	draft = Look.copy(saved); previewDraft()
	if currentCat then showCat(currentCat) end
	saveMsg = nil
end)
lookEvent.OnClientEvent:Connect(function(res, text)
	saving = false
	if res == "ok" then
		saved = Look.copy(pending or draft)
		if not editor.Visible then draft = Look.copy(saved); previewDraft() end   -- z. B. nach SPEICHERN im Abfrage-Fenster
		saveMsg, saveMsgColor = "Übernommen – wird gespeichert …", C.dim
	else
		saveMsg, saveMsgColor = text or "Speichern nicht möglich.", C.warn
	end
end)
player:GetAttributeChangedSignal("CC_SaveStatus"):Connect(function()
	local s = tostring(player:GetAttribute("CC_SaveStatus")):match("^(%a+)")
	if not saveMsg or saving then return end
	if s == "ok" then saveMsg, saveMsgColor = "Gespeichert", C.green
	elseif s == "offline" then saveMsg, saveMsgColor = "Nur für diese Sitzung (Profil nicht geladen)", C.warn
	elseif s == "error" then saveMsg, saveMsgColor = "Speichern fehlgeschlagen – bitte später erneut versuchen.", C.warn end
end)

-- Editor oeffnen/schliessen (beim Verlassen mit ungespeicherten Aenderungen nachfragen)
local function editorOpened()
	saved = serverLook(); draft = Look.copy(saved); saveMsg = nil
	setStageYaw(0)
	previewDraft()
	camMode = "editor"
	menuLogo.Visible = false; profile.Visible = false; area.Visible = false; menuHints.Visible = false
	showCat(CATS[1])
	UI.focus(catButtons.hair)
end
local function editorClosed()
	camMode = "menu"
	draft = Look.copy(saved); previewDraft(); setStageYaw(0)
	menuLogo.Visible = true; profile.Visible = true; area.Visible = true; menuHints.Visible = true
end
local function confirmLeave(onLeave)
	if not dirty() then onLeave(); return end
	UI.dialog(canvas, "ÄNDERUNGEN SPEICHERN?", "Du hast dein Aussehen geändert, aber noch nicht gespeichert.", {
		{ Text = "VERWERFEN", Style = "secondary", OnClick = function() onLeave() end },
			{ Text = "SPEICHERN", Style = "primary", OnClick = function() doSave(); onLeave() end },
	})
end

-- Drehen: Maus ziehen (rechte Bildhaelfte), Knoepfe halten, Q/E bzw. LB/RB, rechter Stick
local dragging, dragX = false, 0
UIS.InputBegan:Connect(function(input, processed)
	if not (editor.Visible and menu.Visible) or processed then return end
	if input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.Touch then
		if input.Position.X > cam.ViewportSize.X * 0.68 then dragging = true; dragX = input.Position.X end
	end
end)
UIS.InputChanged:Connect(function(input)
	if not dragging then return end
	if input.UserInputType == Enum.UserInputType.MouseMovement or input.UserInputType == Enum.UserInputType.Touch then
		setStageYaw(stageYaw + (input.Position.X - dragX) * 0.5); dragX = input.Position.X
	end
end)
UIS.InputEnded:Connect(function(input)
	if input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.Touch then dragging = false end
end)
local keyRot = 0
CAS:BindActionAtPriority("CC_EditorRotate", function(_, st, input)
	if not (editor.Visible and menu.Visible) then return Enum.ContextActionResult.Pass end
	local dir = (input.KeyCode == Enum.KeyCode.Q or input.KeyCode == Enum.KeyCode.ButtonL1) and -1 or 1
	if st == Enum.UserInputState.Begin then keyRot = dir elseif keyRot == dir then keyRot = 0 end
	return Enum.ContextActionResult.Sink
end, false, 3000, Enum.KeyCode.Q, Enum.KeyCode.E, Enum.KeyCode.ButtonL1, Enum.KeyCode.ButtonR1)

---------------------------------------------------------------------------------------------------
-- Oeffnen / Schliessen / Navigation
---------------------------------------------------------------------------------------------------
local isOpen = false
local function otherGuis(on)
	local pg = player:FindFirstChildOfClass("PlayerGui")
	for _, name in ipairs({ "CC_HUD", "CC_GymHUD" }) do
		local g = pg and pg:FindFirstChild(name)
		if g then g.Enabled = on end
	end
	PPS.Enabled = on
end
local function blockGameplay(on)
	player:SetAttribute("CC_UIBlock", on or nil)
	local char = player.Character
	local hum = char and char:FindFirstChildOfClass("Humanoid")
	if hum then
		if on then hum.WalkSpeed = 0; hum:Move(Vector3.zero) end
		hum:SetStateEnabled(Enum.HumanoidStateType.Jumping, not on)
	end
end
local function showPage(name)
	for n, p in pairs(pages) do p.Visible = n == name end
	if name == "fighter" then editorOpened(); return end
	-- Karriere zeigt Level/XP/Bilanz selbst und ist hoeher als der Platz ueber der Profilkarte -> Profilkarte dort ausblenden
	profile.Visible = name ~= "career"
	local p = pages[name]
	local first
	for _, d in ipairs(p:GetDescendants()) do
		if d:IsA("GuiButton") and d.Selectable and d.Visible and d.Name ~= "Back" then
			if not first or d.AbsolutePosition.Y < first.AbsolutePosition.Y then first = d end
		end
	end
	UI.focus(first or p:FindFirstChild("Back", true))
end
function go(name)
	table.insert(stack, name)
	showPage(name)
end
function back()
	if onboarding then finishOnboarding() return end
	if #stack <= 1 then return end
	local function leave()
		local leaving = table.remove(stack)
		if leaving == "fighter" then editorClosed() end
		if #stack == 0 then close() else showPage(stack[#stack]) end
	end
	if stack[#stack] == "fighter" then confirmLeave(leave) else leave() end
end
function open(startPage)
	if isOpen then
		if startPage and stack[#stack] ~= startPage then go(startPage) end
		return
	end
	isOpen = true
	stack = { "home" }
	camMode = "menu"; camCF = nil
	menu.Visible = true
	blockGameplay(true)
	otherGuis(false)
	fightNight(true)
	saved = serverLook(); draft = Look.copy(saved)
	buildStage()
	RunService:BindToRenderStep("CC_MenuCamera", Enum.RenderPriority.Camera.Value + 10, stageCamera)
	if startPage then go(startPage) else showPage("home"); UI.focus(navButtons[1]) end
end
function close()
	if not isOpen then return end
	if stack[#stack] == "fighter" then editorClosed() end
	isOpen = false
	menu.Visible = false
	RunService:UnbindFromRenderStep("CC_MenuCamera")
	if stage then stage:Destroy(); stage = nil end
	fightNight(false)
	cam.CameraType = Enum.CameraType.Custom
	cam.FieldOfView = 70
	local char = player.Character
	if char and char:FindFirstChildOfClass("Humanoid") then cam.CameraSubject = char:FindFirstChildOfClass("Humanoid") end
	blockGameplay(false)
	otherGuis(true)
	GuiService.SelectedObject = nil
end

-- Zurueck: Ruecktaste bzw. Controller B (nur bei offenem Menue; ESC ist bei Roblox fuer das Systemmenue reserviert)
CAS:BindActionAtPriority("CC_MenuBack", function(_, st)
	if not isOpen then return Enum.ContextActionResult.Pass end
	if st == Enum.UserInputState.Begin and not canvas:FindFirstChild("Dialog") then back() end
	return Enum.ContextActionResult.Sink
end, false, 3000, Enum.KeyCode.Backspace, Enum.KeyCode.ButtonB)

---------------------------------------------------------------------------------------------------
-- Menue-Knopf im Gym (wenn das Menue zu ist): Klick, M oder Controller-Select
---------------------------------------------------------------------------------------------------
local menuBtn = UI.button({ Style = "secondary", Text = "MENÜ", Icon = "menu", Size = UDim2.fromOffset(150, 48), Name = "MenuButton",
	OnClick = function() open() end })
menuBtn.Position = UDim2.fromOffset(20, 70)
menuBtn.Parent = canvas
local menuKey = UI.key("M", { AnchorPoint = Vector2.new(0, 0.5), Position = UDim2.new(1, 8, 0.5, 0), Parent = menuBtn })
local function canOpen()
	local char = player.Character
	return not isOpen and char and not char:GetAttribute("CC_Opponent") and not player:GetAttribute("CC_Minigame")
		and not char:GetAttribute("CC_Wrestle") and (player:GetAttribute("CC_OnbPhase") or "") == ""   -- waehrend des Einstiegs (CC_Tutorial) nicht
		and not ((state:GetAttribute("Mode") or "") ~= "" and (state:GetAttribute("RedName") == player.Name or state:GetAttribute("BlueName") == player.Name))   -- eigener Kampf inkl. Walkout
end
CAS:BindActionAtPriority("CC_MenuOpen", function(_, st)
	if st ~= Enum.UserInputState.Begin then return Enum.ContextActionResult.Pass end
	if canOpen() then open(); return Enum.ContextActionResult.Sink end
	return Enum.ContextActionResult.Pass
end, false, 2900, Enum.KeyCode.M, Enum.KeyCode.ButtonSelect)

---------------------------------------------------------------------------------------------------
-- Laufende Aktualisierung
---------------------------------------------------------------------------------------------------
local function queueText()
	local q = player:GetAttribute("CC_Queue")
	local busy = (state:GetAttribute("Mode") or "") ~= ""
	if q == "pvp" then
		local n = state:GetAttribute("QueuePvp") or 0
		if n >= 2 then return "Gegner gefunden – " .. (busy and "ihr seid nach dem laufenden Kampf dran." or "Kampf startet …") end
		return "Suche läuft … (" .. n .. " von 2 Spielern)"
	elseif q == "training" then
		return busy and "Arena belegt – Training startet nach dem laufenden Kampf." or "Training startet …"
	end
	return nil
end
RunService.Heartbeat:Connect(function(dt)
	local char = player.Character
	local inFight = (state:GetAttribute("Mode") or "") ~= "" and (state:GetAttribute("RedName") == player.Name or state:GetAttribute("BlueName") == player.Name)   -- auch beim Walkout (noch ohne Gegner)
	if isOpen and char and (char:GetAttribute("CC_Opponent") or player:GetAttribute("CC_Minigame") or inFight) then close() end
	if isOpen and char then
		local hum = char:FindFirstChildOfClass("Humanoid")
		if hum and hum.WalkSpeed ~= 0 then hum.WalkSpeed = 0 end
	end
	menuBtn.Visible = canOpen() and true or false
	menuKey.Visible = UI.device() == "pc"
	if not isOpen then return end
	-- Editor: Drehen und Speicherstand
	if editor.Visible then
		local r = rotHeld ~= 0 and rotHeld or keyRot
		local pad = UIS:GetGamepadState(Enum.UserInputType.Gamepad1)
		for _, s in ipairs(pad) do
			if s.KeyCode == Enum.KeyCode.Thumbstick2 and math.abs(s.Position.X) > 0.25 then r = s.Position.X end
		end
		if r ~= 0 then setStageYaw(stageYaw + r * 120 * dt) end
		local d = dirty()
		bSave:SetAttribute("Disabled", not d or saving)
		bReset:SetAttribute("Disabled", not d)
		if onboarding then bSave:SetAttribute("Disabled", saving); saveState.Text, saveState.TextColor3 = "Wähle dein Aussehen – später jederzeit änderbar.", C.dim
		elseif d and not saving then saveState.Text, saveState.TextColor3 = "Nicht gespeicherte Änderungen", C.warn
		elseif saveMsg then saveState.Text, saveState.TextColor3 = saveMsg, saveMsgColor
		else saveState.Text = "" end
		return
	end
	-- Profil
	local lv, xp, nx = player:GetAttribute("CC_Level") or 1, player:GetAttribute("CC_XP") or 0, player:GetAttribute("CC_XPNext") or 100
	local w, l = player:GetAttribute("CC_Wins") or 0, player:GetAttribute("CC_Losses") or 0
	pLevel.Text = ("LEVEL %d"):format(lv)
	pXP.Size = UDim2.fromScale(math.clamp(xp / nx, 0, 1), 1)
	local loaded = player:GetAttribute("CC_ProfileSaved")
	pInfo.Text = ("%d / %d XP   ·   Bilanz %d-%d%s"):format(xp, nx, w, l, not loaded and "   ·   Profil nicht geladen" or "")
	pInfo.TextColor3 = not loaded and C.warn or C.dim
	if pages.career.Visible then
		cLevel.Text = ("LEVEL %d   ·   %d / %d XP"):format(lv, xp, nx)
		cXP.Size = UDim2.fromScale(math.clamp(xp / nx, 0, 1), 1)
		for key, row in pairs(statRows) do
			local v, tp = player:GetAttribute("CC_" .. key) or 0, player:GetAttribute("CC_" .. key .. "TP") or 0
			row[1].Text = ("%d / 20   ·   %d/10 TP"):format(v, tp)
			row[2].Size = UDim2.fromScale(math.clamp((v + tp / 10) / 20, 0, 1), 1)
		end
		cRecord.Text = ("Bilanz %d-%d   ·   K.o. %d   ·   Submission %d"):format(w, l, player:GetAttribute("CC_KOs") or 0, player:GetAttribute("CC_Subs") or 0)
	end
	-- Warteschlange
	local q = player:GetAttribute("CC_Queue")
	local txt = queueText()
	status.Visible = txt ~= nil and pages.home.Visible
	statusL.Text = txt or ""
	bSearch.Visible = q == nil; bCancel.Visible = q == "pvp"
	bSearch:SetAttribute("Disabled", q ~= nil)
	oState.Text = q == "pvp" and txt or (q == "training" and "Du bist für einen Trainingskampf angemeldet." or "Bereit.")
	oState.TextColor3 = q == "pvp" and C.gold or C.dim
	bFight:SetAttribute("Disabled", q ~= nil)
	tState.Text = q == "training" and txt or ""
	bTCancel.Visible = q == "training"
end)

-- Spiegel/Spind im Gym: Editor direkt oeffnen
player:GetAttributeChangedSignal("CC_OpenCustomize"):Connect(function()
	local char = player.Character
	if char and not char:GetAttribute("CC_Opponent") and not player:GetAttribute("CC_Minigame") then open("fighter") end
end)
-- fuer andere UI-Skripte (z. B. Ergebnis-Bildschirm): Menue oeffnen per Attribut
player:GetAttributeChangedSignal("CC_OpenMainMenu"):Connect(function() if canOpen() then open() end end)

---------------------------------------------------------------------------------------------------
-- Ladebildschirm, dann Hauptmenue
---------------------------------------------------------------------------------------------------
local loading = UI.new("Frame", { Name = "Loading", BackgroundColor3 = C.bg0, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 50, Parent = canvas })
local lLogo = logo(loading, UDim2.fromScale(0.5, 0.42), 64, Vector2.new(0.5, 0.5))
for _, d in ipairs(lLogo:GetDescendants()) do if d:IsA("GuiObject") then d.ZIndex = 51 end end
local _, lFill = UI.bar({ AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0.56, 0), Size = UDim2.fromOffset(360, 4), ZIndex = 51, Parent = loading }, C.red)
lFill.ZIndex = 52
local lText = UI.label({ Text = "LÄDT …", FontFace = F.bold, TextSize = 16, TextColor3 = C.dim, TextXAlignment = Enum.TextXAlignment.Center,
	AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0.56, 14), Size = UDim2.fromOffset(360, 24), ZIndex = 51, Parent = loading })

task.spawn(function()
	local steps = {
		{ "Spielwelt", function() if not game:IsLoaded() then game.Loaded:Wait() end end },
		{ "Kämpfer", function() local c = player.Character or player.CharacterAdded:Wait(); c:WaitForChild("HumanoidRootPart", 15) end },
		{ "Profil", function() local t0 = os.clock(); while player:GetAttribute("CC_Level") == nil and os.clock() - t0 < 8 do task.wait(0.1) end end },
		{ "Aussehen", function() RS:WaitForChild("CC_CustomShared", 5) end },
		{ "Arena", function() workspace:WaitForChild("CC_Arena", 15) end },
		{ "Einstieg", function() local t0 = os.clock(); while player:GetAttribute("CC_OnbPhase") == nil and os.clock() - t0 < 10 do task.wait(0.1) end end },
	}
	for i, s in ipairs(steps) do
		lText.Text = "LÄDT … " .. s[1]
		pcall(s[2])
		TweenService:Create(lFill, TweenInfo.new(0.25), { Size = UDim2.fromScale(i / #steps, 1) }):Play()
		task.wait(0.12)
	end
	task.wait(0.4)                                    -- Server setzt das Aussehen kurz nach dem Spawn
	local char = player.Character
	local ph = player:GetAttribute("CC_OnbPhase") or ""
	if ph == "editor" then                            -- erster Start: direkt in den Editor (Standardaussehen vorausgewaehlt)
		onboarding = true
		open("fighter")
		bSave:FindFirstChildWhichIsA("TextLabel").Text = "FERTIG"
	elseif ph == "" and char and not char:GetAttribute("CC_Opponent") then open() end   -- Begruessung zeigt CC_Tutorial selbst
	TweenService:Create(loading, TweenInfo.new(0.5), { BackgroundTransparency = 1 }):Play()
	for _, d in ipairs(loading:GetDescendants()) do
		if d:IsA("TextLabel") then TweenService:Create(d, TweenInfo.new(0.4), { TextTransparency = 1 }):Play()
		elseif d:IsA("Frame") then TweenService:Create(d, TweenInfo.new(0.4), { BackgroundTransparency = 1 }):Play() end
	end
	task.wait(0.55)
	loading.Visible = false
end)

-- nach Respawn: Bewegungssperre und Buehne neu
player.CharacterAdded:Connect(function()
	task.wait(0.6)
	if isOpen then blockGameplay(true); buildStage() end
end)
