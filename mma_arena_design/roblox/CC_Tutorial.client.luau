-- StarterPlayer.StarterPlayerScripts.CC_Tutorial
-- Anzeigen fuer den Einstieg (Vorlagen GAME_DESIGN.md, Schritt 1):
--   Begruessung (Bild 1, Phase "welcome"), kompakte Aufgabenkarte waehrend der Lektionen (Bild 2, "lesson"),
--   Abschluss mit Sparring/Gym (Bild 3, "done"), Trainertipps im ersten Sparring ("spar") und Ergebnis danach ("after").
-- Der Server (CC_Tutorial) entscheidet ueber Phase und Fortschritt; dieses Skript zeigt nur an und schickt Knopfdruecke.
-- Grosse Panels nur vor/nach Uebungen (Spielereingaben gesperrt ueber CC_UIBlock), waehrend der Uebung nur kompakte Anzeigen.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local UIS = game:GetService("UserInputService")
local CAS = game:GetService("ContextActionService")
local PPS = game:GetService("ProximityPromptService")
local HS = game:GetService("HttpService")
local RS = game.ReplicatedStorage
local player = Players.LocalPlayer
local UI = require(RS:WaitForChild("CC_UI"))
local C, F = UI.C, UI.F
local remote = RS:WaitForChild("CC_Tutorial")
local matchState = RS:WaitForChild("CC_MatchState")
local cam = workspace.CurrentCamera

local gui = UI.new("ScreenGui", { Name = "CC_TutorialGui", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 12,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling, Parent = player:WaitForChild("PlayerGui") })
local canvas = UI.new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Parent = gui })
UI.autoscale(canvas, 720)
-- Nie gleichzeitig mit dem Hauptmenue: solange das Menue offen ist, sind die Tutorial-Panels ausgeblendet (keine Ueberlagerung)
task.spawn(function()
	local mg = player:WaitForChild("PlayerGui"):WaitForChild("CC_MainMenuGui", 30)
	local menu = mg and mg:WaitForChild("Canvas", 10) and mg.Canvas:WaitForChild("Menu", 10)
	if not menu then return end
	local function sync() canvas.Visible = not (mg.Enabled and menu.Visible) end
	menu:GetPropertyChangedSignal("Visible"):Connect(sync); mg:GetPropertyChangedSignal("Enabled"):Connect(sync); sync()
end)
local function fade(obj, on, t)
	obj.Visible = true
	local g = obj:FindFirstChildOfClass("CanvasGroup") or obj
	if g:IsA("CanvasGroup") then
		TweenService:Create(g, TweenInfo.new(t or 0.18), { GroupTransparency = on and 0 or 1 }):Play()
		if not on then task.delay(t or 0.18, function() if g.GroupTransparency > 0.99 then obj.Visible = false end end) end
	else obj.Visible = on end
end
local function group(props)                       -- Ebene mit weichem Ein-/Ausblenden
	local g = UI.new("CanvasGroup", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), GroupTransparency = 1, Visible = false })
	for k, v in pairs(props or {}) do if k ~= "Parent" then g[k] = v end end
	g.Parent = props.Parent
	return g
end
local function accent(parent, h)                  -- roter Streifen links (wie die Vorlagen)
	return UI.new("Frame", { BackgroundColor3 = C.red, BorderSizePixel = 0, Size = UDim2.new(0, 5, 1, -(h or 24)), Position = UDim2.fromOffset(0, (h or 24) / 2), ZIndex = 3, Parent = parent })
end
local function divider(parent, y, inset)
	return UI.new("Frame", { BackgroundColor3 = C.line, BackgroundTransparency = 0.4, BorderSizePixel = 0, Position = UDim2.fromOffset(inset or 24, y),
		Size = UDim2.new(1, -2 * (inset or 24), 0, 1), ZIndex = 3, Parent = parent })
end

---------------------------------------------------------------------------------------------------
-- Trainer-Dialog (unten): Portraet, "TRAINER", kurzer Satz
---------------------------------------------------------------------------------------------------
local coachBox = group({ Name = "Coach", AnchorPoint = Vector2.new(0, 1), Size = UDim2.fromOffset(560, 84), Parent = canvas })
UI.panel({ Size = UDim2.fromScale(1, 1), ImageTransparency = 0.04, Cut = 14, Parent = coachBox })
accent(coachBox, 20)
local portrait = UI.new("ViewportFrame", { BackgroundColor3 = C.bg2, BorderSizePixel = 0, Position = UDim2.fromOffset(14, 10), Size = UDim2.fromOffset(64, 64),
	Ambient = Color3.fromRGB(190, 190, 200), LightDirection = Vector3.new(-0.3, -0.5, -1), ZIndex = 3, Parent = coachBox })
local portraitIcon = UI.icon("coach", { Size = UDim2.fromOffset(44, 44), Position = UDim2.fromOffset(24, 20), ImageColor3 = C.dim, ZIndex = 4, Parent = coachBox })
local coachName = UI.label({ Text = "TRAINER", FontFace = F.bold, TextSize = 14, TextColor3 = C.red, Position = UDim2.fromOffset(94, 12), Size = UDim2.new(1, -110, 0, 18), ZIndex = 3, Parent = coachBox })
local coachText = UI.label({ Text = "", TextSize = 18, TextYAlignment = Enum.TextYAlignment.Top, Position = UDim2.fromOffset(94, 34), Size = UDim2.new(1, -110, 0, 44), ZIndex = 3, Parent = coachBox })
local portraitDone = false
local function buildPortrait()
	if portraitDone then return end
	local src = workspace:FindFirstChild("CC_CoachGym") or workspace:FindFirstChild("CC_CoachCage")
	if not src then return end
	portraitDone = true
	local m = src:Clone()
	for _, d in ipairs(m:GetDescendants()) do if d:IsA("ProximityPrompt") then d:Destroy() end end
	m:PivotTo(CFrame.new())
	m.Parent = portrait
	local vc = Instance.new("Camera"); vc.FieldOfView = 24; vc.Parent = portrait
	local cf, size = m:GetBoundingBox()
	local head = cf.Position + Vector3.new(0, size.Y / 2 - 1.0, 0)
	vc.CFrame = CFrame.lookAt(head + Vector3.new(1.2, 0.2, -4.6), head)    -- Modell schaut nach -Z
	portrait.CurrentCamera = vc
	portraitIcon.Visible = false
end
local tipKindColor = { tip = C.text, good = C.green, bad = C.warn }
local coachUntil = 0
local function say(text, kind, hold)
	buildPortrait()
	coachText.Text = text
	coachText.TextColor3 = tipKindColor[kind or "tip"] or C.text
	fade(coachBox, true)
	coachUntil = hold and math.huge or (os.clock() + 6)
end

---------------------------------------------------------------------------------------------------
-- Bild 1: Begruessung und Tutorial-Angebot
---------------------------------------------------------------------------------------------------
local welcome = group({ Name = "Welcome", Position = UDim2.fromOffset(28, 56), Size = UDim2.fromOffset(500, 644), Parent = canvas })
UI.panel({ Size = UDim2.fromScale(1, 1), Cut = 22, Parent = welcome })
local wPad = 30
UI.label({ Text = "C A G E   C H A M P I O N S", FontFace = F.bold, TextSize = 13, TextColor3 = C.dim, Position = UDim2.fromOffset(wPad, 24), Size = UDim2.fromOffset(300, 18), ZIndex = 3, Parent = welcome })
UI.new("Frame", { BackgroundColor3 = C.red, BorderSizePixel = 0, Position = UDim2.fromOffset(wPad, 46), Size = UDim2.fromOffset(36, 3), ZIndex = 3, Parent = welcome })
local wTag = UI.chamfer({ Position = UDim2.fromOffset(wPad, 62), Size = UDim2.fromOffset(250, 30), ImageColor3 = C.red, ImageTransparency = 0, ZIndex = 3, Parent = welcome }, "fill", 8)
local wTagL = UI.label({ Text = "DEIN ERSTER SCHRITT", FontFace = F.bold, TextSize = 15, TextXAlignment = Enum.TextXAlignment.Center, Size = UDim2.fromScale(1, 1), ZIndex = 4, Parent = wTag })
local wTitle = UI.label({ Text = "BEREIT FÜR\nDEN KÄFIG?", FontFace = F.title, TextSize = 50, TextWrapped = false, TextYAlignment = Enum.TextYAlignment.Top,
	Position = UDim2.fromOffset(wPad - 2, 104), Size = UDim2.new(1, -2 * wPad, 0, 116), ZIndex = 3, Parent = welcome })
UI.label({ Text = "Lerne die Grundlagen. Danach wartet dein erster Kampf.", TextSize = 17, TextYAlignment = Enum.TextYAlignment.Top,
	Position = UDim2.fromOffset(wPad, 222), Size = UDim2.new(1, -2 * wPad, 0, 44), ZIndex = 3, Parent = welcome })
local GROUPS = {
	{ icon = "run", title = "Bewegen & Deckung", sub = "Laufe, halte Abstand und blocke Angriffe.", lessons = { 1, 3 } },
	{ icon = "glove", title = "Schläge & Kicks", sub = "Lerne die wichtigsten Angriffe.", lessons = { 2, 4 } },
	{ icon = "wrestle", title = "Takedown & Aufstehen", sub = "Bring den Gegner zu Boden und steh wieder auf.", lessons = { 5, 6 } },
}
local function groupRow(parent, y, g, h)
	local row = UI.chamfer({ Position = UDim2.fromOffset(wPad - 8, y), Size = UDim2.new(1, -2 * wPad + 16, 0, h or 70), ImageColor3 = C.bg2, ImageTransparency = 0.1, ZIndex = 3, Parent = parent }, "fill", 10)
	UI.icon(g.icon, { Size = UDim2.fromOffset(34, 34), AnchorPoint = Vector2.new(0, 0.5), Position = UDim2.new(0, 18, 0.5, 0), ZIndex = 4, Parent = row })
	UI.label({ Text = g.title, FontFace = F.bold, TextSize = 17, Position = UDim2.fromOffset(68, g.sub and 12 or 0), Size = UDim2.new(1, -120, 0, g.sub and 22 or (h or 70)), ZIndex = 4, Parent = row })
	if g.sub then UI.label({ Text = g.sub, TextSize = 14, TextColor3 = C.dim, Position = UDim2.fromOffset(68, 36), Size = UDim2.new(1, -120, 0, 20), TextTruncate = Enum.TextTruncate.AtEnd, TextWrapped = false, ZIndex = 4, Parent = row }) end
	local state = UI.new("Frame", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -16, 0.5, 0), Size = UDim2.fromOffset(34, 34), ZIndex = 4, Parent = row })
	local ring = UI.new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = 4, Visible = false, Parent = state })
	UI.new("UICorner", { CornerRadius = UDim.new(1, 0), Parent = ring }); UI.new("UIStroke", { Color = C.red, Thickness = 2.5, Parent = ring })
	UI.icon("check", { Size = UDim2.fromOffset(20, 20), Position = UDim2.fromOffset(7, 7), ZIndex = 5, Parent = ring })
	local chev = UI.icon("next", { Size = UDim2.fromOffset(18, 18), Position = UDim2.fromOffset(8, 8), ImageColor3 = C.dim, ZIndex = 5, Parent = state })
	return function(done) ring.Visible = done; chev.Visible = not done end
end
local wRows = {}
for i, g in ipairs(GROUPS) do wRows[i] = groupRow(welcome, 268 + (i - 1) * 72, g, 64) end
local bStart, bStartParts = UI.button({ Style = "primary", Text = "TRAINING STARTEN", Size = UDim2.new(1, -2 * wPad + 16, 0, 56), Parent = welcome,
	OnClick = function() remote:FireServer("start") end })
bStart.Position = UDim2.fromOffset(wPad - 8, 490)
UI.icon("next", { Size = UDim2.fromOffset(20, 20), AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -18, 0.5, 0), ZIndex = 4, Parent = bStart })
local bSkipW = UI.button({ Style = "secondary", Text = "ÜBERSPRINGEN", Size = UDim2.new(1, -2 * wPad + 16, 0, 46), Parent = welcome,
	OnClick = function() remote:FireServer("closeWelcome") end })
bSkipW.Position = UDim2.fromOffset(wPad - 8, 554)
local wInfo = UI.new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(wPad - 6, 614), Size = UDim2.new(1, -2 * wPad, 0, 0), ZIndex = 3, Parent = welcome })
local wInfoRow = UI.new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, -2), Size = UDim2.fromOffset(400, 20), ZIndex = 3, Parent = wInfo })
UI.icon("info", { Size = UDim2.fromOffset(18, 18), ZIndex = 3, Parent = wInfoRow, ImageColor3 = C.dim })
UI.label({ Text = "Später beim Trainer wiederholbar.", TextSize = 14, TextColor3 = C.dim, Position = UDim2.fromOffset(26, -1), Size = UDim2.fromOffset(360, 20), ZIndex = 3, Parent = wInfoRow })

---------------------------------------------------------------------------------------------------
-- Bild 2: Aufgabenkarte waehrend der Lektion (kompakt), Fortschritt oben links, Ueberspringen oben rechts, Hilfe unten rechts
---------------------------------------------------------------------------------------------------
local lessonUI = group({ Name = "Lesson", Parent = canvas })
local tab = UI.chamfer({ Position = UDim2.fromOffset(24, 78), Size = UDim2.fromOffset(250, 38), ImageColor3 = C.bg1, ImageTransparency = 0.04, ZIndex = 2, Parent = lessonUI }, "fill", 10)
accent(tab, 12)
local tabL = UI.label({ Text = "GRUNDLAGEN", FontFace = F.bold, TextSize = 16, Position = UDim2.fromOffset(18, 0), Size = UDim2.new(1, -30, 1, 0), ZIndex = 3, Parent = tab })
local pips = {}
for i = 1, 6 do
	local p = UI.chamfer({ Position = UDim2.fromOffset(26 + (i - 1) * 30, 124), Size = UDim2.fromOffset(22, 22), ImageColor3 = C.line, ImageTransparency = 0, ZIndex = 2, Parent = lessonUI }, "outline_thick", 6)
	local fill = UI.chamfer({ Size = UDim2.fromScale(1, 1), ImageColor3 = C.red, ImageTransparency = 0, ZIndex = 3, Visible = false, Parent = p }, "fill", 6)
	local ck = UI.icon("check", { Size = UDim2.fromOffset(14, 14), Position = UDim2.fromOffset(4, 4), ZIndex = 4, Visible = false, Parent = p })
	pips[i] = { p, fill, ck }
end
local card = UI.panel({ Position = UDim2.fromOffset(24, 156), Size = UDim2.fromOffset(400, 262), ImageTransparency = 0.04, Cut = 16, ZIndex = 2, Parent = lessonUI })
accent(card, 20)
local cardRing = UI.ring(card, 16, C.green); cardRing.ZIndex = 6
local cIcon = UI.icon("glove", { Size = UDim2.fromOffset(52, 52), Position = UDim2.fromOffset(24, 22), ZIndex = 3, Parent = card })
local cTitle = UI.label({ Text = "", FontFace = F.title, TextSize = 27, TextWrapped = false, TextTruncate = Enum.TextTruncate.AtEnd,
	Position = UDim2.fromOffset(92, 18), Size = UDim2.new(1, -108, 0, 32), ZIndex = 3, Parent = card })
local cTask = UI.label({ Text = "", TextSize = 16, TextYAlignment = Enum.TextYAlignment.Top, Position = UDim2.fromOffset(92, 52), Size = UDim2.new(1, -108, 0, 42), ZIndex = 3, Parent = card })
divider(card, 104)
local keyRow = UI.new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(24, 116), Size = UDim2.new(1, -48, 0, 70), ZIndex = 3, Parent = card })
UI.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, VerticalAlignment = Enum.VerticalAlignment.Center, Padding = UDim.new(0, 12), SortOrder = Enum.SortOrder.LayoutOrder, Parent = keyRow })
divider(card, 196)
local cProg = UI.label({ Text = "0 / 3", FontFace = F.bold, TextSize = 22, Position = UDim2.fromOffset(24, 206), Size = UDim2.fromOffset(80, 40), ZIndex = 3, Parent = card })
local dotRow = UI.new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(108, 206), Size = UDim2.fromOffset(260, 40), ZIndex = 3, Parent = card })
UI.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, VerticalAlignment = Enum.VerticalAlignment.Center, Padding = UDim.new(0, 12), SortOrder = Enum.SortOrder.LayoutOrder, Parent = dotRow })
local stepL = UI.label({ Text = "", TextSize = 13, TextColor3 = C.dim, TextXAlignment = Enum.TextXAlignment.Right, AnchorPoint = Vector2.new(1, 0),
	Position = UDim2.new(1, -20, 0, 206), Size = UDim2.fromOffset(120, 40), ZIndex = 3, Parent = card })
local bSkipAll = UI.button({ Style = "ghost", Text = "Tutorial überspringen", Icon = "skip", Size = UDim2.fromOffset(260, 46), Parent = lessonUI,
	OnClick = function() remote:FireServer("skipAll") end })
bSkipAll.AnchorPoint = Vector2.new(1, 0); bSkipAll.Position = UDim2.new(1, -24, 0, 64)
local bHelp = UI.button({ Style = "ghost", Text = "Hilfe", Size = UDim2.fromOffset(140, 50), Parent = lessonUI })
bHelp.AnchorPoint = Vector2.new(1, 1); bHelp.Position = UDim2.new(1, -24, 1, -24)
do
	local t = bHelp:FindFirstChildWhichIsA("TextLabel")
	t.TextXAlignment = Enum.TextXAlignment.Left; t.Position = UDim2.fromOffset(62, 0); t.Size = UDim2.new(1, -70, 1, 0)
	UI.key("H", { AnchorPoint = Vector2.new(0, 0.5), Position = UDim2.new(0, 16, 0.5, 0), ZIndex = 4, Parent = bHelp })
end
-- Ankuendigung des Gegners (oben mittig)
local tele = UI.chamfer({ AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0, 120), Size = UDim2.fromOffset(420, 46), ImageColor3 = C.red, ImageTransparency = 0, ZIndex = 5, Visible = false, Parent = canvas }, "fill", 10)
local teleL = UI.label({ Text = "", FontFace = F.bold, TextSize = 19, TextXAlignment = Enum.TextXAlignment.Center, Size = UDim2.fromScale(1, 1), ZIndex = 6, Parent = tele })
-- Warten auf freie Arena
local waitTag = UI.chamfer({ AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0, 120), Size = UDim2.fromOffset(460, 44), ImageColor3 = C.bg1, ImageTransparency = 0.05, ZIndex = 5, Visible = false, Parent = canvas }, "fill", 10)
UI.label({ Text = "Arena belegt – das Tutorial startet gleich.", FontFace = F.bold, TextSize = 16, TextXAlignment = Enum.TextXAlignment.Center, Size = UDim2.fromScale(1, 1), ZIndex = 6, Parent = waitTag })

-- Hilfe-Fenster (H): Erklaerung der aktuellen Aufgabe, Lektion ueberspringen
local helpUI = group({ Name = "Help", AnchorPoint = Vector2.new(1, 1), Position = UDim2.new(1, -24, 1, -88), Size = UDim2.fromOffset(520, 250), Parent = canvas })
UI.panel({ Size = UDim2.fromScale(1, 1), Cut = 16, Parent = helpUI })
accent(helpUI, 20)
UI.icon("help", { Size = UDim2.fromOffset(28, 28), Position = UDim2.fromOffset(24, 20), ImageColor3 = C.red, ZIndex = 3, Parent = helpUI })
local hTitle = UI.label({ Text = "HILFE", FontFace = F.title, TextSize = 22, Position = UDim2.fromOffset(62, 18), Size = UDim2.new(1, -80, 0, 32), ZIndex = 3, Parent = helpUI })
local hText = UI.label({ Text = "", TextSize = 16, TextYAlignment = Enum.TextYAlignment.Top, Position = UDim2.fromOffset(24, 62), Size = UDim2.new(1, -48, 0, 90), ZIndex = 3, Parent = helpUI })
local hRow = UI.new("Frame", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0, 1), Position = UDim2.new(0, 24, 1, -20), Size = UDim2.new(1, -48, 0, 50), ZIndex = 3, Parent = helpUI })
UI.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 10), HorizontalAlignment = Enum.HorizontalAlignment.Right, SortOrder = Enum.SortOrder.LayoutOrder, Parent = hRow })
local helpOpen = false
local function showHelp(on)
	helpOpen = on
	fade(helpUI, on)
end
UI.button({ Style = "secondary", Text = "LEKTION ÜBERSPRINGEN", Size = UDim2.fromOffset(270, 50), LayoutOrder = 1, Parent = hRow,
	OnClick = function() showHelp(false); remote:FireServer("skipLesson") end })
UI.button({ Style = "primary", Text = "WEITER ÜBEN", Size = UDim2.fromOffset(160, 50), LayoutOrder = 2, Parent = hRow, OnClick = function() showHelp(false) end })
bHelp.Activated:Connect(function() showHelp(not helpOpen) end)

---------------------------------------------------------------------------------------------------
-- Bild 3: Grundlagen geschafft -> Sparring / Gym
---------------------------------------------------------------------------------------------------
local doneUI = group({ Name = "Done", AnchorPoint = Vector2.new(0, 0.5), Position = UDim2.new(0, 70, 0.5, 10), Size = UDim2.fromOffset(560, 560), Parent = canvas })
UI.panel({ Size = UDim2.fromScale(1, 1), Cut = 22, Parent = doneUI })
local dPad = 34
local bigRing = UI.new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(dPad, 30), Size = UDim2.fromOffset(70, 70), ZIndex = 3, Parent = doneUI })
UI.new("UICorner", { CornerRadius = UDim.new(1, 0), Parent = bigRing }); UI.new("UIStroke", { Color = C.red, Thickness = 4, Parent = bigRing })
UI.icon("check", { Size = UDim2.fromOffset(40, 40), Position = UDim2.fromOffset(15, 15), ZIndex = 4, Parent = bigRing })
local dTitle = UI.label({ Text = "GRUNDLAGEN GESCHAFFT", FontFace = F.title, TextSize = 31, TextWrapped = false, Position = UDim2.fromOffset(dPad + 92, 34), Size = UDim2.new(1, -dPad * 2 - 92, 0, 36), ZIndex = 3, Parent = doneUI })
local dSub = UI.label({ Text = "Jetzt setzt du das Gelernte im Sparring ein.", TextSize = 16, TextColor3 = C.dim, Position = UDim2.fromOffset(dPad + 92, 72), Size = UDim2.new(1, -dPad * 2 - 92, 0, 22), ZIndex = 3, Parent = doneUI })
local dRows = {}
local DGROUPS = { { icon = "shield", title = "Deckung & Distanz", lessons = { 1, 3 } }, { icon = "glove", title = "Schläge & Kicks", lessons = { 2, 4 } },
	{ icon = "wrestle", title = "Takedown & Aufstehen", lessons = { 5, 6 } } }
do
	local save = wPad; wPad = dPad
	for i, g in ipairs(DGROUPS) do dRows[i] = groupRow(doneUI, 120 + (i - 1) * 64, g, 54) end
	wPad = save
end
divider(doneUI, 322, dPad)
UI.icon("octagon", { Size = UDim2.fromOffset(52, 52), Position = UDim2.fromOffset(dPad + 4, 340), ZIndex = 3, Parent = doneUI })
UI.label({ Text = "DEIN ERSTER KAMPF", FontFace = F.title, TextSize = 27, Position = UDim2.fromOffset(dPad + 76, 338), Size = UDim2.new(1, -dPad * 2 - 76, 0, 32), ZIndex = 3, Parent = doneUI })
UI.label({ Text = "Anfänger-Gegner  ·  1 Runde", TextSize = 16, TextColor3 = C.dim, Position = UDim2.fromOffset(dPad + 76, 370), Size = UDim2.new(1, -dPad * 2 - 76, 0, 22), ZIndex = 3, Parent = doneUI })
local bSpar = UI.button({ Style = "primary", Text = "SPARRING STARTEN", Size = UDim2.new(1, -2 * dPad, 0, 56), Parent = doneUI, OnClick = function() remote:FireServer("choice", "sparring") end })
bSpar.Position = UDim2.fromOffset(dPad, 410)
local bGym = UI.button({ Style = "secondary", Text = "ZURÜCK INS GYM", Size = UDim2.new(1, -2 * dPad, 0, 48), Parent = doneUI, OnClick = function() remote:FireServer("choice", "gym") end })
bGym.Position = UDim2.fromOffset(dPad, 474)
local dInfo = UI.new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(dPad, 530), Size = UDim2.fromOffset(460, 20), ZIndex = 3, Parent = doneUI })
UI.icon("info", { Size = UDim2.fromOffset(18, 18), ImageColor3 = C.dim, ZIndex = 3, Parent = dInfo })
UI.label({ Text = "Das Tutorial kannst du jederzeit wiederholen.", TextSize = 14, TextColor3 = C.dim, Position = UDim2.fromOffset(26, -1), Size = UDim2.fromOffset(420, 20), ZIndex = 3, Parent = dInfo })

---------------------------------------------------------------------------------------------------
-- Ergebnis nach dem ersten Sparring (echte Belohnung aus CC_LastFight)
---------------------------------------------------------------------------------------------------
local afterUI = group({ Name = "After", AnchorPoint = Vector2.new(0, 0.5), Position = UDim2.new(0, 70, 0.5, 0), Size = UDim2.fromOffset(500, 300), Parent = canvas })
UI.panel({ Size = UDim2.fromScale(1, 1), Cut = 20, Parent = afterUI })
accent(afterUI, 24)
local aTag = UI.label({ Text = "DEIN ERSTER KAMPF", FontFace = F.bold, TextSize = 14, TextColor3 = C.red, Position = UDim2.fromOffset(32, 24), Size = UDim2.fromOffset(300, 18), ZIndex = 3, Parent = afterUI })
local aTitle = UI.label({ Text = "", FontFace = F.title, TextSize = 44, Position = UDim2.fromOffset(30, 46), Size = UDim2.new(1, -60, 0, 52), ZIndex = 3, Parent = afterUI })
local aLine = UI.label({ Text = "", TextSize = 16, TextColor3 = C.dim, Position = UDim2.fromOffset(32, 100), Size = UDim2.new(1, -64, 0, 22), ZIndex = 3, Parent = afterUI })
local aReward = UI.new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(32, 134), Size = UDim2.new(1, -64, 0, 40), ZIndex = 3, Parent = afterUI })
UI.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 10), VerticalAlignment = Enum.VerticalAlignment.Center, Parent = aReward })
local aRow = UI.new("Frame", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0, 1), Position = UDim2.new(0, 32, 1, -26), Size = UDim2.new(1, -64, 0, 54), ZIndex = 3, Parent = afterUI })
UI.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 12), SortOrder = Enum.SortOrder.LayoutOrder, Parent = aRow })
local bRetry = UI.button({ Style = "primary", Text = "NOCHMAL", Icon = "rotate", Size = UDim2.fromOffset(210, 54), LayoutOrder = 1, Parent = aRow, OnClick = function() remote:FireServer("retry") end })
local bAfterGym = UI.button({ Style = "secondary", Text = "INS GYM", Size = UDim2.fromOffset(200, 54), LayoutOrder = 2, Parent = aRow, OnClick = function() remote:FireServer("closeAfter") end })
local bContinue = UI.button({ Style = "primary", Text = "WEITER", Icon = "next", Size = UDim2.fromOffset(220, 54), LayoutOrder = 3, Parent = aRow, OnClick = function() remote:FireServer("closeAfter") end })

---------------------------------------------------------------------------------------------------
-- Zustand anwenden
---------------------------------------------------------------------------------------------------
local function decode(attr)
	local ok, t = pcall(function() return HS:JSONDecode(player:GetAttribute(attr) or "") end)
	return ok and type(t) == "table" and t or nil
end
local blocked = false
local function block(on)                          -- grosse Panels: Bewegung/Angriffe aus, Maus frei, andere Gym-Anzeigen aus
	if on == blocked then return end
	blocked = on
	player:SetAttribute("CC_UIBlock", on or nil)
	local char = player.Character
	local hum = char and char:FindFirstChildOfClass("Humanoid")
	if hum and on then hum:Move(Vector3.zero) end
	PPS.Enabled = not on
	local gh = player.PlayerGui:FindFirstChild("CC_GymHUD")
	if gh then gh.Enabled = not on end
end
local modal = UI.new("TextButton", { Text = "", BackgroundTransparency = 1, Size = UDim2.fromOffset(0, 0), Modal = false, Parent = canvas })

-- Kamera zur Begruessung: Spieler und Trainer im Bild (nur wenn der Trainer im Gym steht)
local camHeld = false
local function welcomeCamera(on)
	local coach = workspace:FindFirstChild("CC_CoachGym")
	local char = player.Character
	local r = char and char:FindFirstChild("HumanoidRootPart")
	if on and coach and r and not camHeld then
		camHeld = true
		local cf = coach:GetPivot()
		local mid = (cf.Position + r.Position) / 2 + Vector3.new(0, 2.2, 0)
		local side = (cf.Position - r.Position) * Vector3.new(1, 0, 1)
		local perp = side.Magnitude > 0.1 and Vector3.new(-side.Z, 0, side.X).Unit or Vector3.new(1, 0, 0)
		cam.CameraType = Enum.CameraType.Scriptable
		local goal = CFrame.lookAt(mid + perp * 13 + Vector3.new(0, 1.5, 0) - side.Unit * 3, mid + side.Unit * 2.5)
		TweenService:Create(cam, TweenInfo.new(0.6, Enum.EasingStyle.Sine), { CFrame = goal }):Play()
	elseif not on and camHeld then
		camHeld = false
		cam.CameraType = Enum.CameraType.Custom
		if char and char:FindFirstChildOfClass("Humanoid") then cam.CameraSubject = char:FindFirstChildOfClass("Humanoid") end
	end
end

local lastPhase, lastPulse, lastTip = nil, 0, 0
local function applyLesson(st)
	if not st then return end
	tabL.Text = ("GRUNDLAGEN   %d / 6"):format(st.lesson or 1)
	for i, pp in ipairs(pips) do
		local done = st.done and st.done[i]
		local cur = i == st.lesson
		pp[2].Visible = cur and not done
		pp[3].Visible = done and true or false
		pp[1].ImageColor3 = (done or cur) and C.red or C.line
	end
	cIcon.ImageContent = UI.iconContent(st.icon or "glove", 64)
	cTitle.Text = st.title or ""
	cTask.Text = st.task or ""
	for _, c in ipairs(keyRow:GetChildren()) do if not c:IsA("UIListLayout") then c:Destroy() end end
	for i, k in ipairs(st.keys or {}) do
		if k[1] == "LMB" or k[1] == "RMB" then
			UI.icon("mouse", { Size = UDim2.fromOffset(34, 40), LayoutOrder = i * 3, ZIndex = 4, Parent = keyRow })
		end
		if k[1] ~= "—" then UI.key(k[1], { LayoutOrder = i * 3 + 1, ZIndex = 4, Parent = keyRow }) end
		UI.label({ Text = k[2], TextSize = 16, AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, 30), TextWrapped = false, LayoutOrder = i * 3 + 2, ZIndex = 4, Parent = keyRow })
	end
	cProg.Text = ("%d / %d"):format(st.n or 0, st.of or 1)
	for _, c in ipairs(dotRow:GetChildren()) do if not c:IsA("UIListLayout") then c:Destroy() end end
	for i = 1, st.of or 1 do
		local d = UI.new("Frame", { BackgroundColor3 = C.red, BackgroundTransparency = i <= (st.n or 0) and 0 or 1, Size = UDim2.fromOffset(22, 22), LayoutOrder = i, ZIndex = 4, Parent = dotRow })
		UI.new("UICorner", { CornerRadius = UDim.new(1, 0), Parent = d })
		UI.new("UIStroke", { Color = i <= (st.n or 0) and C.red or C.dim, Thickness = 2, Parent = d })
	end
	stepL.Text = (st.steps or 1) > 1 and ("Teil %d von %d"):format(st.step or 1, st.steps) or ""
	hTitle.Text = "HILFE: " .. (st.title or "")
	local keys = {}
	for _, k in ipairs(st.keys or {}) do table.insert(keys, (k[1] == "—" and "" or (k[1] .. " = ")) .. k[2]) end
	hText.Text = (st.task or "") .. "\n" .. table.concat(keys, "   ·   ") .. "\n\n" .. (st.help or "")
	bHelp:SetAttribute("Selected", st.struggle and true or false)
	if st.pulse and st.pulse ~= lastPulse then              -- dezentes Erfolgsfeedback
		lastPulse = st.pulse
		cardRing.Visible = true; cardRing.ImageTransparency = 0
		TweenService:Create(cardRing, TweenInfo.new(0.45), { ImageTransparency = 1 }):Play()
	end
	if st.struggle then say("Probleme? Drück H – ich erkläre es dir, oder du überspringst die Lektion.", "tip") end
end
local function setDoneRows(rows, lessons)
	for i, g in ipairs(GROUPS) do
		local ok = true
		for _, li in ipairs(g.lessons) do if not (lessons and lessons[li]) then ok = false end end
		rows[i](ok)
	end
end

local function apply()
	local ph = player:GetAttribute("CC_OnbPhase") or ""
	local o = decode("CC_Onb")
	local st = decode("CC_TutState")
	local mine = matchState:GetAttribute("Mode") == "tutorial" and matchState:GetAttribute("RedName") == player.Name
	-- Begruessung
	if ph == "welcome" then
		local any, nextL = false, nil
		for i = 1, 6 do if o and o.lessons and o.lessons[i] then any = true elseif not nextL then nextL = i end end
		local repeat_ = o and o.done
		bStartParts.title.Text = repeat_ and "GRUNDLAGEN WIEDERHOLEN" or ((any and nextL) and ("WEITER MIT LEKTION " .. nextL) or "TRAINING STARTEN")
		bSkipW:FindFirstChildWhichIsA("TextLabel").Text = repeat_ and "SCHLIESSEN" or "ÜBERSPRINGEN"
		setDoneRows(wRows, o and o.lessons)
		if lastPhase ~= "welcome" then
			say(repeat_ and "Lust auf eine Auffrischung? Wir gehen die Grundlagen gern noch einmal durch."
				or any and "Schön, dass du wieder da bist. Machen wir weiter, wo wir aufgehört haben."
				or "Willkommen im Gym. Ich bin dein Trainer. Zeig mir, was du kannst.", "tip", true)
			welcomeCamera(true)
		end
	end
	fade(welcome, ph == "welcome")
	-- Lektionen
	local inLesson = ph == "lesson" and mine and st ~= nil
	fade(lessonUI, inLesson)
	waitTag.Visible = ph == "lesson" and not mine
	if inLesson then applyLesson(st) end
	if not inLesson and helpOpen then showHelp(false) end
	-- Abschluss
	if ph == "done" then setDoneRows(dRows, o and o.lessons) end
	fade(doneUI, ph == "done")
	-- Ergebnis
	if ph == "after" then
		local r = decode("CC_LastFight") or {}
		local win = r.result == "win"
		aTitle.Text = win and "SIEG" or (r.result == "draw" and "UNENTSCHIEDEN" or "NIEDERLAGE")
		aTitle.TextColor3 = win and C.gold or C.text
		aLine.Text = (r.method or "") ~= "" and (r.method .. (win and "  ·  starker Einstand" or "  ·  der nächste Versuch zählt")) or ""
		for _, c in ipairs(aReward:GetChildren()) do if not c:IsA("UIListLayout") then c:Destroy() end end
		if r.xp then UI.tag({ Text = ("+%d XP"):format(r.xp), Color = C.gold, TextColor = C.bg0, Size = UDim2.fromOffset(0, 34), Parent = aReward }) end
		UI.tag({ Text = "+2 TP KONDITION", Color = C.blue, Size = UDim2.fromOffset(0, 34), Parent = aReward })   -- jede gekaempfte Runde (CC_Match)
		bRetry.Visible = not win; bAfterGym.Visible = not win; bContinue.Visible = win
		if lastPhase ~= "after" then say(win and "Starker erster Kampf! Das Gym und Online stehen dir jetzt offen." or "Kopf hoch – jeder fängt so an. Noch ein Versuch?", win and "good" or "tip", true) end
	end
	fade(afterUI, ph == "after")
	if ph ~= "welcome" and lastPhase == "welcome" then welcomeCamera(false) end
	local big = ph == "welcome" or ph == "done" or ph == "after"
	block(big)
	modal.Modal = big                                      -- Maus frei fuer die Knoepfe
	if not big and (ph == "" or ph == "editor") and lastPhase ~= ph then coachUntil = math.min(coachUntil, os.clock() + 5) end
	lastPhase = ph
end
for _, a in ipairs({ "CC_OnbPhase", "CC_TutState", "CC_Onb", "CC_LastFight" }) do player:GetAttributeChangedSignal(a):Connect(apply) end
matchState:GetAttributeChangedSignal("Mode"):Connect(apply)
player:GetAttributeChangedSignal("CC_CoachTip"):Connect(function()
	local t = decode("CC_CoachTip")
	if t and t.t ~= lastTip then lastTip = t.t; local ph_ = player:GetAttribute("CC_OnbPhase") or ""; say(t.text, t.kind, ph_ == "welcome" or ph_ == "done" or ph_ == "after") end
end)

-- Ankuendigung des Gegners anzeigen (CC_Telegraph am Trainingsgegner)
local dummy = workspace:WaitForChild("CC_TrainingDummy", 30)
if dummy then
	dummy:GetAttributeChangedSignal("CC_Telegraph"):Connect(function()
		local ph = player:GetAttribute("CC_OnbPhase")
		if ph ~= "lesson" then return end
		local kind = tostring(dummy:GetAttribute("CC_Telegraph")):match("^(%a+)")
		teleL.Text = kind == "td" and "TAKEDOWN KOMMT  –  F DRÜCKEN" or "SCHLAG KOMMT  –  F HALTEN"
		tele.Visible = true
		task.delay(1.3, function() tele.Visible = false end)
	end)
end

-- H = Hilfe (nur waehrend einer Lektion)
CAS:BindActionAtPriority("CC_TutHelp", function(_, st)
	if not lessonUI.Visible or player:GetAttribute("CC_OnbPhase") ~= "lesson" then return Enum.ContextActionResult.Pass end
	if st == Enum.UserInputState.Begin then showHelp(not helpOpen) end
	return Enum.ContextActionResult.Sink
end, false, 3100, Enum.KeyCode.H)

-- Trainer-Dialog: Position je Phase, ausblenden nach ein paar Sekunden
RunService.RenderStepped:Connect(function()
	local ph = player:GetAttribute("CC_OnbPhase") or ""
	if ph == "welcome" or ph == "done" or ph == "after" then coachBox.AnchorPoint = Vector2.new(1, 1); coachBox.Position = UDim2.new(1, -24, 1, -24); coachBox.Size = UDim2.fromOffset(600, 90)
	else coachBox.AnchorPoint = Vector2.new(0, 1); coachBox.Position = UDim2.new(0, 24, 1, -24); coachBox.Size = UDim2.fromOffset(560, 84) end
	local mm = player.PlayerGui:FindFirstChild("CC_MainMenuGui")
	local menuOpen = mm and mm:FindFirstChild("Menu", true) and mm:FindFirstChild("Menu", true).Visible
	if menuOpen and coachBox.Visible then coachBox.Visible = false; coachBox.GroupTransparency = 1 end   -- Hauptmenue offen: kein Trainerfeld dahinter
	if coachBox.Visible and os.clock() > coachUntil and coachBox.GroupTransparency < 0.01 then fade(coachBox, false) end
	if blocked then
		UIS.MouseBehavior = Enum.MouseBehavior.Default
		local hum = player.Character and player.Character:FindFirstChildOfClass("Humanoid")
		if hum then hum:Move(Vector3.zero) end
	end
end)

-- Kampf-Hinweisleiste und Rundenuhr im Tutorial/ersten Sparring blendet CC_HUD selbst aus (Mode "tutorial"/"sparring")
apply()
