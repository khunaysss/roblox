-- StarterGui.CC_MainMenuGui.MainMenu (LocalScript in einer ScreenGui)
-- Ladebildschirm, Hauptmenue, Navigation und Charakter-Editor (UI-Ueberarbeitung Schritt 1+2, Designsystem: ReplicatedStorage.CC_UI).
-- Hintergrund: die Arena (Blick vom Einlaufsteg auf den Kaefig) mit blauer Fight-Night-Beleuchtung (nur lokal, solange
-- das Menue offen ist). Rechts der eigene Kaempfer in Kampfhaltung: lokale Kopie des Charakters, nur fuer diesen Spieler.
-- Der echte Charakter bleibt im Gym.
-- Waehrend das Menue offen ist (Attribut CC_UIBlock am Spieler, nur lokal): keine Kampf-Eingaben, kein Laufen,
-- kein HUD, keine Gym-Interaktionen. Ein Kampf (CC_Opponent) oder ein Minispiel (CC_Minigame) schliesst das Menue.
-- Menuepunkte:
--   KARRIERE      = sechs freischaltbare Gegner, Rivalenkampf, Ranglistenweg und Titelkampf; echte Vorschau aus vorhandenen Modellen.
--   ONLINE        = Warteschlange gegen Spieler (ReplicatedStorage.CC_Menu "pvp" / "cancel")
--   TRAINING      = Trainingskampf (CC_Menu "training") oder Gym-Training (Menue schliessen)
--   MEIN KAEMPFER = Charakter-Editor: Vorschau nur lokal (ReplicatedStorage.CC_LookShared + CC_CustomShared),
--                   erst SPEICHERN schickt das Aussehen an den Server (CC_Look) -> Profil speichert sofort (CC_SaveStatus).
--   EINSTELLUNGEN = Audio, Anzeige, Steuerungshilfe und Tutorial-Zugriff
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
local SoundService = game:GetService("SoundService")
local HS = game:GetService("HttpService")

local player = Players.LocalPlayer
local UI = require(RS:WaitForChild("CC_UI"))
local Look = require(RS:WaitForChild("CC_LookShared"))
local Opponents = require(RS:WaitForChild("CC_Opponents"))
local Progression = require(RS:WaitForChild("CC_Progression"))
local C, F = UI.C, UI.F
local menuEvent = RS:WaitForChild("CC_Menu")
local lookEvent = RS:WaitForChild("CC_Look")
local progressEvent = RS:WaitForChild("CC_Progress")
local state = RS:WaitForChild("CC_MatchState")
local gui = script.Parent
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = false
gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
gui.DisplayOrder = 20

-- Buehne in der Arena (Einlaufsteg suedlich vom Kaefig)
local CAM_POS = Vector3.new(1.8, 4.0, -48)
local CAM_AIM = Vector3.new(0.2, 5.0, 0)
local FIGHTER_POS = Vector3.new(-2.6, 0, -35)
local CAM_FOV = 39
local FIGHTER_YAW = 28            -- Grad zur Kamera gedreht
local GUARD_LOWER = -22           -- Oberarme etwas senken, damit die Handschuhe das Gesicht nicht verdecken (nur Menue-Kopie)

local canvas = UI.new("Frame", { Name = "Canvas", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Parent = gui })
UI.autoscale(canvas, 840)

---------------------------------------------------------------------------------------------------
-- Hauptmenue-Ebene
---------------------------------------------------------------------------------------------------
local menu = UI.new("Frame", { Name = "Menu", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Visible = false, Parent = canvas })
local shadeL = UI.new("Frame", { BackgroundColor3 = C.bg0, BorderSizePixel = 0, Size = UDim2.fromScale(0.6, 1), Parent = menu })
UI.new("UIGradient", { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.05), NumberSequenceKeypoint.new(0.6, 0.35), NumberSequenceKeypoint.new(1, 1) }), Parent = shadeL })
local shadeB = UI.new("Frame", { BackgroundColor3 = C.bg0, BorderSizePixel = 0, AnchorPoint = Vector2.new(0, 1), Position = UDim2.fromScale(0, 1), Size = UDim2.new(1, 0, 0, 170), Parent = menu })
UI.new("UIGradient", { Rotation = -90, Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.08), NumberSequenceKeypoint.new(1, 1) }), Parent = shadeB })
local function logo(parent,pos,size,anchor)
 local height=size*1.35
 local width=height*(48/15.6)
 return UI.sprite("logo",{Name="CC_Logo",Position=pos,AnchorPoint=anchor or Vector2.zero,Size=UDim2.fromOffset(width,height),Parent=parent})
end

local menuLogo = logo(menu, UDim2.fromOffset(30, 8), 73)
local menuTagline = UI.label({ Text = "", FontFace = F.bold, TextSize = 11, TextColor3 = C.mute,
	Position = UDim2.fromOffset(46, 116), Size = UDim2.fromOffset(600, 20), TextWrapped = false, Parent = menu })

-- Bereich links: Navigation bzw. Unterseite
local area = UI.new("Frame", { Name = "Area", BackgroundTransparency = 1, Position = UDim2.fromOffset(36, 154), Size = UDim2.fromOffset(660, 470), Parent = menu })

-- Profil-Karte unten links
local profile = UI.panel({ Name = "Profile", AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -42, 0, 28), Size = UDim2.fromOffset(450, 88), ImageColor3 = C.bg0, Parent = menu })
UI.label({ Text = player.DisplayName, FontFace = F.head, TextSize = 22, Position = UDim2.fromOffset(20, 10), Size = UDim2.new(1, -40, 0, 28), Parent = profile })
local pLevel = UI.label({ Text = "", FontFace = F.bold, TextSize = 17, TextColor3 = C.gold, TextXAlignment = Enum.TextXAlignment.Right, Position = UDim2.fromOffset(20, 12), Size = UDim2.new(1, -40, 0, 24), Parent = profile })
local _, pXP = UI.bar({ Position = UDim2.fromOffset(20, 44), Size = UDim2.new(1, -40, 0, 6), Parent = profile }, C.gold)
local pInfo = UI.label({ Text = "", TextSize = 16, TextColor3 = C.dim, Position = UDim2.fromOffset(20, 58), Size = UDim2.new(1, -190, 0, 26), Parent = profile })
local profileMore = UI.label({ Text = "PROGRESS  ›", FontFace = F.bold, TextSize = 14, TextColor3 = C.dim,
	TextXAlignment = Enum.TextXAlignment.Right, Position = UDim2.new(1, -174, 0, 58), Size = UDim2.fromOffset(145, 26), ZIndex = 8, Parent = profile })

local menuHints = UI.hints({ AnchorPoint = Vector2.new(1, 1), Position = UDim2.new(1, -40, 1, -32), Entries = {
	{ pc = "CLICK", pad = "A", text = "Select" }, { pc = "BACKSPACE", pad = "B", text = "Back" } }, Parent = menu })

local status = UI.panel({ Name = "Status", AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0, 34), Size = UDim2.fromOffset(500, 54), Visible = false, Parent = menu })
local statusL = UI.label({ Text = "", FontFace = F.bold, TextSize = 18, TextXAlignment = Enum.TextXAlignment.Center, Size = UDim2.fromScale(1, 1), Parent = status })

---------------------------------------------------------------------------------------------------
-- Seiten
---------------------------------------------------------------------------------------------------
local pages, stack = {}, {}
local open, close, go, back
local profileOpen = UI.new("TextButton", { Name = "OpenProgress", Text = "", AutoButtonColor = false, BackgroundTransparency = 1,
	Size = UDim2.fromScale(1, 1), ZIndex = 7, Selectable = true, Parent = profile })
profileOpen.SelectionImageObject = UI.noSelectionImage()
profileOpen.Activated:Connect(function() if go then go("progress") end end)
local profileOutline = profile:FindFirstChild("PanelOutline")
profileOpen.MouseEnter:Connect(function()
	profileMore.TextColor3 = C.red
	if profileOutline then profileOutline.Color = C.red; profileOutline.Transparency = 0 end
end)
profileOpen.MouseLeave:Connect(function()
	profileMore.TextColor3 = C.dim
	if profileOutline then profileOutline.Color = C.line; profileOutline.Transparency = 0.28 end
end)
UI.icon("next", { AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -14, 0.72, 0), Size = UDim2.fromOffset(20, 20), ImageColor3 = C.dim, ZIndex = 8, Parent = profile })
local stage, stageTrack
local draft = Look.copy(Look.DEFAULT)
local saved = Look.copy(Look.DEFAULT)

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
home.Size = UDim2.fromOffset(650, 460)
local navButtons = {}
local function nav(order, text, sub, icon, fn, disabled, badge)
	local b = UI.button({ Style = "nav", Text = text, Sub = sub, Icon = icon, LayoutOrder = order, OnClick = fn, Disabled = disabled, Badge = badge, Parent = home })
	table.insert(navButtons, b)
	return b
end
nav(1, "CAREER", "Progress · Stats · Record", "trophy", function() go("career") end)
nav(2, "ONLINE", "Fight real players", "globe", function() go("online") end)
nav(3, "TRAINING", "Training fight or gym", "dumbbell", function() go("training") end)
nav(4, "MY FIGHTER", "Customize your look", "fighter", function() go("fighter") end)
nav(5, "SETTINGS", "Sound · Display · Tutorial", "gear", function() go("settings") end)
navButtons[1]:SetAttribute("Selected", true)
for _, button in ipairs(navButtons) do
	button.MouseEnter:Connect(function()
		for _, other in ipairs(navButtons) do other:SetAttribute("Selected", other == button) end
	end)
	button.SelectionGained:Connect(function()
		for _, other in ipairs(navButtons) do other:SetAttribute("Selected", other == button) end
	end)
end

-- Karriere: Ranglistenweg mit zehn Gegnern (Liste scrollbar), Rivalen- und Titelkampf, Karriere-Titel (CC_CareerTitle)
local career = page("career")
header(career, "CAREER")
local cSummary = card(career, 1, 62)
local cLevel = UI.label({ Text = "", FontFace = F.head, TextSize = 19, TextColor3 = C.gold, Size = UDim2.new(1, 0, 0, 24), Parent = cSummary })
local cRecord = UI.label({ Text = "", TextSize = 15, TextColor3 = C.dim, Position = UDim2.fromOffset(0, 26), Size = UDim2.new(1, 0, 0, 20), Parent = cSummary })
local _, cXP = UI.bar({ Position = UDim2.fromOffset(0, 48), Size = UDim2.new(1, 0, 0, 5), Parent = cSummary }, C.gold)
local cRosterCard = card(career, 2, 368)
local cRoster = UI.new("ScrollingFrame", { BackgroundTransparency = 1, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), CanvasSize = UDim2.new(),
	AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollBarThickness = 4, ScrollBarImageColor3 = C.red, ScrollingDirection = Enum.ScrollingDirection.Y, Parent = cRosterCard })
UI.new("UIListLayout", { Padding = UDim.new(0, 3), SortOrder = Enum.SortOrder.LayoutOrder, Parent = cRoster })
UI.new("UIPadding", { PaddingRight = UDim.new(0, 8), Parent = cRoster })
local cRows = {}
local selectedCareerId = Opponents.list[1].id

local careerDetail=UI.panel({Name="OpponentDetails",AnchorPoint=Vector2.new(1,1),Position=UDim2.new(1,-42,1,-75),Size=UDim2.fromOffset(570,230),Visible=false,Parent=menu})
local careerOpponentName=UI.label({Text="",FontFace=F.title,TextSize=27,Position=UDim2.fromOffset(30,15),Size=UDim2.new(1,-60,0,40),TextWrapped=false,Parent=careerDetail})
local careerStyle=UI.label({Text="",TextSize=16,TextColor3=C.dim,Position=UDim2.fromOffset(30,53),Size=UDim2.new(1,-60,0,25),Parent=careerDetail})
local careerStats={}
for i,entry in ipairs({{"Power","Power"},{"Cardio","Cardio"},{"Wrestling","Wrestling"},{"Grappling","Grappling"}}) do
 local y=85+(i-1)*31
 UI.label({Text=entry[2],TextSize=15,Position=UDim2.fromOffset(30,y),Size=UDim2.fromOffset(150,24),Parent=careerDetail})
 local _,fill=UI.bar({Position=UDim2.fromOffset(190,y+7),Size=UDim2.fromOffset(220,10),Parent=careerDetail},i<=2 and C.red or C.gold)
 local val=UI.label({Text="",FontFace=F.bold,TextSize=15,TextXAlignment=Enum.TextXAlignment.Right,Position=UDim2.fromOffset(420,y),Size=UDim2.fromOffset(100,24),Parent=careerDetail})
 careerStats[entry[1]]={fill=fill,value=val}
end

local cTip = UI.label({ Text = "", TextSize = 15, TextColor3 = C.dim, LayoutOrder = 3, Size = UDim2.new(1, 0, 0, 34), TextWrapped = true, Parent = career })
local cFight, cFightParts
local function selectCareer(id)
	local def = Opponents.byId[id]; if not def then return end
	selectedCareerId = id
 careerOpponentName.Text=("#%d  %s"):format(def.rank or 0,def.name):upper()
 careerStyle.Text=(def.style.."  /  "..def.stage):upper()
 for key,row in pairs(careerStats) do
  local v=def.stats and def.stats[key]
  row.value.Text=v and (tostring(v).." / 20") or "—"
  row.fill.Size=UDim2.fromScale(math.clamp((v or 0)/20,0,1),1)
 end
 for rid, row in pairs(cRows) do row.button:SetAttribute("Selected", rid == id) end
	cTip.Text = "COACH TIP  ·  " .. def.tip
	if cFightParts then cFightParts.title.Text = "FIGHT VS " .. def.name:upper() end
	if cFight then
		local beaten=Opponents.beatenSet(player:GetAttribute("CC_CareerBeaten"))
		local unlocked=Opponents.isUnlocked(id,beaten)
		cFight:SetAttribute("Disabled",not unlocked)
		if not unlocked then cFightParts.title.Text="LOCKED · WIN PREVIOUS FIGHT" end
	end
	if stage then
		Look.apply(stage, def.look, RS:FindFirstChild("CC_CustomShared"))
		local shorts = stage:FindFirstChild("Fighter_Shorts", true); if shorts and shorts:IsA("BasePart") then shorts.Color = C.blue end
	end
end
for i, def in ipairs(Opponents.list) do
	local d = def
	local b, parts = UI.button({ Style = "ghost", Text = ("#%d  %s"):format(d.rank or i,d.name):upper(), Sub = ("RANK #%d  ·  %s  ·  %s"):format(d.rank or i, d.stage, d.style),
		Size = UDim2.new(1, 0, 0, 56), LayoutOrder = 11-i, Name = d.id, OnClick = function() selectCareer(d.id) end, Parent = cRoster })
	parts.title.TextSize=19
	parts.title:FindFirstChildWhichIsA("UITextSizeConstraint").MaxTextSize=19
	parts.title.Position=UDim2.fromOffset(18,3);parts.title.Size=UDim2.new(1,-112,0,27);parts.title.TextYAlignment=Enum.TextYAlignment.Center
	parts.sub.Position=UDim2.fromOffset(18,30);parts.sub.Size=UDim2.new(1,-48,0,20);parts.sub.TextSize=13;parts.sub.TextYAlignment=Enum.TextYAlignment.Center
 local lockIcon = UI.icon("lock", {Position = UDim2.new(1,-24,0.5,-8), Size = UDim2.fromOffset(16,16), ImageColor3 = C.mute, Parent = b})
 cRows[d.id] = { button = b, parts = parts, def = d, index = i, lock = lockIcon }
end
local cActions = UI.new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 54), LayoutOrder = 4, Parent = career })
UI.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, HorizontalAlignment = Enum.HorizontalAlignment.Right,
	Padding = UDim.new(0, 10), SortOrder = Enum.SortOrder.LayoutOrder, Parent = cActions })
UI.button({ Style = "secondary", Text = "TO THE GYM", Icon = "dumbbell", Size = UDim2.new(0.34, -5, 1, 0), LayoutOrder = 1, OnClick = function() close() end, Parent = cActions })
cFight, cFightParts = UI.button({ Style = "primary", Text = "START FIGHT", Icon = "glove", Size = UDim2.new(0.66, -5, 1, 0), LayoutOrder = 2,
	OnClick = function()
		if player:GetAttribute("CC_Queue") == "career" then menuEvent:FireServer("cancel")
		elseif player:GetAttribute("CC_Queue") == nil and Opponents.isUnlocked(selectedCareerId,Opponents.beatenSet(player:GetAttribute("CC_CareerBeaten"))) then menuEvent:FireServer("career", selectedCareerId) end
	end, Parent = cActions })
local function refreshCareer()
	local lv, xp, nx = player:GetAttribute("CC_Level") or 1, player:GetAttribute("CC_XP") or 0, player:GetAttribute("CC_XPNext") or 100
	local beaten = Opponents.beatenSet(player:GetAttribute("CC_CareerBeaten"))
	local cw, cl = player:GetAttribute("CC_CareerWins") or 0, player:GetAttribute("CC_CareerLosses") or 0
	cLevel.Text = ("LEVEL %d   ·   %d / %d XP"):format(lv, xp, nx)
	cXP.Size = UDim2.fromScale(math.clamp(xp / nx, 0, 1), 1)
	local title = player:GetAttribute("CC_CareerTitle") or (Opponents.titleFor and Opponents.titleFor(cw).name) or "AMATEUR"
	cRecord.Text = ("%s   ·   %s   ·   Career %d/%d   ·   Record %d-%d"):format(title, Opponents.division or "DIVISION", cw, #Opponents.list, cw, cl)
	for id, row in pairs(cRows) do
		local unlocked = Opponents.isUnlocked(id, beaten)
		row.button:SetAttribute("Disabled", false)
		if row.lock then row.lock.Visible = not unlocked end
		local stateText = beaten[id] and "WIN" or (unlocked and "READY" or "LOCKED")
		row.parts.sub.Text = stateText .. "  ·  " .. row.def.style
 row.parts.sub.TextColor3=row.button:GetAttribute("Selected") and C.text or beaten[id] and C.green or (unlocked and C.red or C.mute)
	end
	local unlocked = Opponents.isUnlocked(selectedCareerId, beaten)
	local q = player:GetAttribute("CC_Queue")
	cFight:SetAttribute("Disabled", not unlocked or (q ~= nil and q ~= "career"))
	cFightParts.title.Text = q == "career" and "CANCEL WAIT" or not unlocked and "LOCKED · WIN PREVIOUS FIGHT" or ("FIGHT VS " .. Opponents.byId[selectedCareerId].name:upper())
end
selectCareer(selectedCareerId)

-- Fortschritt: echte Tages-/Wochenziele und abgeleitete Level-Titel.
local progress = page("progress")
header(progress, "PROGRESS")
local pgSummary = card(progress, 1, 62)
local pgRank = UI.label({ Text = "", FontFace = F.head, TextSize = 20, TextColor3 = C.gold, Size = UDim2.new(1, 0, 0, 24), Parent = pgSummary })
local pgXPText = UI.label({ Text = "", TextSize = 15, TextColor3 = C.dim, TextXAlignment = Enum.TextXAlignment.Right, Size = UDim2.new(1, 0, 0, 24), Parent = pgSummary })
local _, pgXP = UI.bar({ Position = UDim2.fromOffset(0, 42), Size = UDim2.new(1, 0, 0, 6), Parent = pgSummary }, C.gold)

local pgTabs = UI.new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 44), LayoutOrder = 2, Parent = progress })
UI.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 8), SortOrder = Enum.SortOrder.LayoutOrder, Parent = pgTabs })
local pgGoalsTab = UI.button({ Style = "ghost", Text = "GOALS & REWARDS", Icon = "trophy", Size = UDim2.new(0.5, -4, 1, 0), LayoutOrder = 1, Parent = pgTabs })
local pgLevelsTab = UI.button({ Style = "ghost", Text = "LEVEL & TITLE", Icon = "star", Size = UDim2.new(0.5, -4, 1, 0), LayoutOrder = 2, Parent = pgTabs })

local pgBody = UI.new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 276), LayoutOrder = 3, Parent = progress })
local pgGoals = UI.new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Parent = pgBody })
local pgLevels = UI.new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Visible = false, Parent = pgBody })
UI.new("UIListLayout", { Padding = UDim.new(0, 5), SortOrder = Enum.SortOrder.LayoutOrder, Parent = pgGoals })
UI.new("UIListLayout", { Padding = UDim.new(0, 4), SortOrder = Enum.SortOrder.LayoutOrder, Parent = pgLevels })

local goalRows = {}
for i, def in ipairs(Progression.goals) do
	local d = def
	local row = UI.panel({ Size = UDim2.new(1, 0, 0, 62), LayoutOrder = i, ImageColor3 = C.bg1, Parent = pgGoals })
	UI.label({ Text = d.title, FontFace = F.bold, TextSize = 16, Position = UDim2.fromOffset(14, 5), Size = UDim2.new(1, -160, 0, 23), Parent = row })
	local statusText = UI.label({ Text = "", TextSize = 14, TextColor3 = C.dim, Position = UDim2.fromOffset(14, 27), Size = UDim2.new(1, -165, 0, 19), Parent = row })
	local _, fill = UI.bar({ Position = UDim2.fromOffset(14, 50), Size = UDim2.new(1, -170, 0, 5), Parent = row }, C.red)
	local claim, claimParts = UI.button({ Style = "primary", Text = "+" .. d.xp .. " XP", Size = UDim2.fromOffset(136, 40), Parent = row,
		OnClick = function() progressEvent:FireServer("claim", d.id) end })
	claim.AnchorPoint = Vector2.new(1, 0.5); claim.Position = UDim2.new(1, -10, 0.5, 0)
	goalRows[d.id] = { def = d, status = statusText, fill = fill, button = claim, parts = claimParts }
end

local levelRows = {}
for i, def in ipairs(Progression.titles) do
	local row = UI.panel({ Size = UDim2.new(1, 0, 0, 42), LayoutOrder = i, ImageColor3 = C.bg1, Parent = pgLevels })
	local title = UI.label({ Text = ("LEVEL %d  ·  %s"):format(def.level, def.title), FontFace = F.bold, TextSize = 16,
		Position = UDim2.fromOffset(14, 0), Size = UDim2.new(0.48, 0, 1, 0), Parent = row })
	UI.label({ Text = def.reward, TextSize = 14, TextColor3 = C.dim, Position = UDim2.new(0.48, 0, 0, 0), Size = UDim2.new(0.34, 0, 1, 0), Parent = row })
	local stateText = UI.label({ Text = "", FontFace = F.bold, TextSize = 14, TextXAlignment = Enum.TextXAlignment.Right,
		Position = UDim2.new(0.82, 0, 0, 0), Size = UDim2.new(0.15, 0, 1, 0), Parent = row })
	levelRows[i] = { def = def, title = title, state = stateText }
end

local function setProgressTab(which)
	pgGoals.Visible = which == "goals"; pgLevels.Visible = which == "levels"
	pgGoalsTab:SetAttribute("Selected", which == "goals"); pgLevelsTab:SetAttribute("Selected", which == "levels")
end
pgGoalsTab.Activated:Connect(function() setProgressTab("goals") end)
pgLevelsTab.Activated:Connect(function() setProgressTab("levels") end)
setProgressTab("goals")

local function progressData()
	local ok, data = pcall(function() return HS:JSONDecode(player:GetAttribute("CC_Goals") or "") end)
	return ok and type(data) == "table" and data or { counts = {}, claimed = {} }
end
local function refreshProgress()
	local lv, xp, nx = player:GetAttribute("CC_Level") or 1, player:GetAttribute("CC_XP") or 0, player:GetAttribute("CC_XPNext") or 100
	pgRank.Text = ("%s  ·  LEVEL %d"):format(player:GetAttribute("CC_RankTitle") or "ROOKIE", lv)
	pgXPText.Text = ("%d / %d XP"):format(xp, nx)
	pgXP.Size = UDim2.fromScale(math.clamp(xp / nx, 0, 1), 1)
	local data = progressData(); data.counts = data.counts or {}; data.claimed = data.claimed or {}
	for id, row in pairs(goalRows) do
		local count = math.min(tonumber(data.counts[id]) or 0, row.def.target)
		local claimed = data.claimed[id] == true
		row.status.Text = ("%s  ·  %d / %d"):format(row.def.period == "day" and "DAILY" or "WEEKLY", count, row.def.target)
		row.fill.Size = UDim2.fromScale(count / row.def.target, 1)
		row.button:SetAttribute("Disabled", claimed or count < row.def.target)
		row.button:SetAttribute("RewardReady", not claimed and count >= row.def.target)
		row.parts.title.Text = claimed and "CLAIMED" or (count >= row.def.target and "CLAIM" or ("+" .. row.def.xp .. " XP"))
	end
	local currentTitle = player:GetAttribute("CC_RankTitle")
	for _, row in ipairs(levelRows) do
		local unlocked = lv >= row.def.level
		row.title.TextColor3 = unlocked and (currentTitle == row.def.title and C.gold or C.text) or C.mute
		row.state.Text = unlocked and (currentTitle == row.def.title and "ACTIVE" or "REACHED") or "LOCKED"
		row.state.TextColor3 = unlocked and (currentTitle == row.def.title and C.gold or C.green) or C.mute
	end
end
for _, attr in ipairs({ "CC_Goals", "CC_Level", "CC_XP", "CC_XPNext", "CC_RankTitle" }) do
	player:GetAttributeChangedSignal(attr):Connect(refreshProgress)
end
refreshProgress()

-- Online
local online = page("online")
header(online, "ONLINE")
local oCard = card(online, 1, 100)
UI.label({ Text = "QUICK FIGHT", FontFace = F.head, TextSize = 19, Size = UDim2.new(1, 0, 0, 26), Parent = oCard })
UI.label({ Text = "Fight the next player in the queue. 3 rounds, 45 seconds each. Every online fight is ranked.",
	TextSize = 16, TextColor3 = C.dim, Position = UDim2.fromOffset(0, 30), Size = UDim2.new(1, 0, 0, 40), Parent = oCard })
-- Arena-Wahl (Server paart nur Spieler mit passender Wahl; "egal" passt zu allen)
do
local pvpArena = player:GetAttribute("CC_PvpArenaPick") or "any"
local arRow = UI.new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 44), LayoutOrder = 1, Parent = online })
UI.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 8), SortOrder = Enum.SortOrder.LayoutOrder, Parent = arRow })
local arButtons = {}
for i, e in ipairs({ { "fightnight", "FIGHT NIGHT" }, { "cage", "CAGE" }, { "any", "ANY" } }) do
	local b = UI.button({ Style = "ghost", Text = e[2], Size = UDim2.new(1 / 3, -6, 1, 0), LayoutOrder = i, Name = "Ar_" .. e[1], Parent = arRow,
		OnClick = function() pvpArena = e[1]; player:SetAttribute("CC_PvpArenaPick", e[1]); for k, x in pairs(arButtons) do x:SetAttribute("Selected", k == pvpArena) end end })
	arButtons[e[1]] = b
	b:SetAttribute("Selected", e[1] == pvpArena)
end
arRow.LayoutOrder = 2
end
local oState = UI.label({ Text = "", FontFace = F.bold, TextSize = 17, LayoutOrder = 3, Size = UDim2.new(1, 0, 0, 28), Parent = online })
local bSearch = UI.button({ Style = "primary", Text = "START SEARCH", Icon = "search", LayoutOrder = 4, OnClick = function() menuEvent:FireServer("pvp", player:GetAttribute("CC_PvpArenaPick") or "any"); close() end, Parent = online })
local bCancel = UI.button({ Style = "danger", Text = "CANCEL SEARCH", Icon = "close", LayoutOrder = 5, OnClick = function() menuEvent:FireServer("cancel") end, Parent = online })
-- Online-Rang (CC_Rank): Stufe und Punkte vom Server, jeder Online-Kampf zaehlt (Sieg +25, Niederlage -15)
local RANK = require(RS:WaitForChild("CC_Rank"))
local rankBtn, rankParts = UI.button({ Style = "secondary", Text = "RANK: BRONZE", Sub = "0 points", Icon = "star", LayoutOrder = 6, Disabled = true,
	Size = UDim2.new(1, 0, 0, 66), Parent = online })
local rankTrack, rankFill = UI.bar({Name = "RankProgress", Position = UDim2.new(0, 24, 1, -10), Size = UDim2.new(1, -48, 0, 4), Parent = rankBtn}, C.gold)
local function refreshRank()
	local pts = player:GetAttribute("CC_RankPoints") or 0
	local target = player:GetAttribute("CC_RankNextAt")
	rankFill.Size = UDim2.fromScale(target and math.clamp(pts / math.max(target, 1), 0, 1) or 1, 1)
	local tier = player:GetAttribute("CC_RankTier") or "Bronze"
	local nxt, at = player:GetAttribute("CC_RankNext"), player:GetAttribute("CC_RankNextAt")
	if rankParts and rankParts.title then rankParts.title.Text = "RANK: " .. string.upper(tier); rankParts.title.TextColor3 = RANK.colorOf(tier) end
	if rankParts and rankParts.sub then
		rankParts.sub.Text = nxt and ("%d points  ·  %d more for %s"):format(pts, math.max(0, (at or pts) - pts), nxt) or ("%d points  ·  highest rank reached"):format(pts)
	end
end
for _, attr in ipairs({ "CC_RankPoints", "CC_RankTier", "CC_RankNext", "CC_RankNextAt" }) do player:GetAttributeChangedSignal(attr):Connect(refreshRank) end
refreshRank()

-- Training
local training = page("training")
header(training, "TRAINING")
-- Stufe des Trainingsgegners (Server prueft den Wert): Passiv / Anfaenger / Fortgeschritten
local dummyLevel = player:GetAttribute("CC_DummyLevel") or "anfaenger"
local lvRow = UI.new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 44), LayoutOrder = 1, Parent = training })
UI.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 8), SortOrder = Enum.SortOrder.LayoutOrder, Parent = lvRow })
local lvButtons = {}
for i, e in ipairs({ { "passiv", "PASSIVE" }, { "anfaenger", "BEGINNER" }, { "fortgeschritten", "PRO" } }) do
	local b = UI.button({ Style = "ghost", Text = e[2], Size = UDim2.new(1 / 3, -6, 1, 0), LayoutOrder = i, Name = "Lv_" .. e[1], Parent = lvRow,
		OnClick = function() dummyLevel = e[1]; for k, x in pairs(lvButtons) do x:SetAttribute("Selected", k == dummyLevel) end end })
	lvButtons[e[1]] = b
	b:SetAttribute("Selected", e[1] == dummyLevel)
end
local bFight = UI.button({ Style = "nav", Text = "TRAINING FIGHT", Sub = "Against the training opponent · no record", Icon = "glove", LayoutOrder = 2,
	OnClick = function() menuEvent:FireServer("training", dummyLevel) end, Parent = training })
UI.button({ Style = "nav", Text = "GYM TRAINING", Sub = "Minigames at the stations", Icon = "dumbbell", LayoutOrder = 3,
	OnClick = function() close() end, Parent = training })
UI.button({ Style = "ghost", Text = "REPLAY BASICS (TUTORIAL)", Icon = "help", LayoutOrder = 6, Name = "Tutorial",
	OnClick = function() close(); RS:WaitForChild("CC_Tutorial"):FireServer("openWelcome") end, Parent = training })
local tState = UI.label({ Text = "", FontFace = F.bold, TextSize = 17, LayoutOrder = 4, Size = UDim2.new(1, 0, 0, 28), Parent = training })
local bTCancel = UI.button({ Style = "danger", Text = "CANCEL", Icon = "close", LayoutOrder = 5, OnClick = function() menuEvent:FireServer("cancel") end, Parent = training })


-- Status stammt aus den vorhandenen Interaktionen, nicht aus erfundenen Belegungen.
do
	local summary=card(training,7,174)
	UI.label({Text="GYM STATIONS",FontFace=F.head,TextSize=17,Size=UDim2.new(1,0,0,24),Parent=summary})
	local groups={
		{label="Heavy bags",kinds={punch_bag=true,punch_bag_standing=true}},
		{label="Strength",kinds={bench_press=true,bench_dumbbell=true}},
		{label="Cardio",kinds={stretch_spot=true,treadmill=true}},
	}
	local rows={}
	for i,group in ipairs(groups) do
		rows[i]=UI.label({Text="",TextSize=15,Position=UDim2.fromOffset(0,28+(i-1)*30),Size=UDim2.new(1,0,0,26),Parent=summary})
	end
	UI.label({Text="READY = interaction enabled. Visit the gym to begin.",TextSize=12,TextColor3=C.dim,Position=UDim2.fromOffset(0,126),Size=UDim2.new(1,0,0,20),Parent=summary})
	local elapsed=0
	RunService.Heartbeat:Connect(function(dt)
		elapsed+=dt
		if elapsed<.5 or not training.Visible then return end
		elapsed=0
		local folder=workspace:FindFirstChild("CC_GymInteractions")
		for i,group in ipairs(groups) do
			local enabled,total=0,0
			if folder then
				for _,marker in ipairs(folder:GetChildren()) do
					if group.kinds[marker:GetAttribute("CC_Interaction")] then
						local prompt=marker:FindFirstChildOfClass("ProximityPrompt")
						total+=1
						if prompt and prompt.Enabled then enabled+=1 end
					end
				end
			end
			rows[i].Text=string.format("%s  ·  %d / %d READY",group.label,enabled,total)
			rows[i].TextColor3=enabled>0 and C.green or C.mute
		end
	end)
end

-- Einstellungen: lokal und sofort wirksam. Musik wird anhand des Sound-Namens erkannt;
-- nicht erkannte Sounds gelten als Effekte. Gespeichert im Profil (CC_Progress "settings"; CC_Profile setzt die Attribute beim Laden).
local settings = page("settings")
header(settings, "SETTINGS")
local settingsCard = card(settings, 1, 272)
UI.label({ Text = "SOUND", FontFace = F.head, TextSize = 21, TextColor3 = C.text, Size = UDim2.new(1, 0, 0, 28), Parent = settingsCard })

local volume = {
	master = player:GetAttribute("CC_MasterVolume") or 0.8,
	music = player:GetAttribute("CC_MusicVolume") or 0.4,
	effects = player:GetAttribute("CC_EffectsVolume") or 0.7,
}
local baseVolumes = setmetatable({}, { __mode = "k" })
local function isMusic(sound)
	local n = sound.Name:lower()
	return n:find("music", 1, true) or n:find("theme", 1, true) or n:find("ambience", 1, true)
end
local function applySound(sound)
	if not sound:IsA("Sound") then return end
	if baseVolumes[sound] == nil then baseVolumes[sound] = sound.Volume end
	local channel = isMusic(sound) and volume.music or volume.effects
	sound.Volume = baseVolumes[sound] * volume.master * channel
end
local display = { reduceFx = player:GetAttribute("CC_ReduceFX") == true, noShake = player:GetAttribute("CC_NoShake") == true, reduceMotion = player:GetAttribute("CC_ReduceMotion") == true }
local sendQueued = false
local function sendSettings()   -- hoechstens alle 0,6 s an den Server (Profil speichert selbst gedrosselt)
	if sendQueued then return end
	sendQueued = true
	task.delay(0.6, function()
		sendQueued = false
		progressEvent:FireServer("settings", { master = volume.master, music = volume.music, effects = volume.effects,
			reduceFx = display.reduceFx, noShake = display.noShake, reduceMotion = display.reduceMotion })
	end)
end
local function applyVolumes()
	player:SetAttribute("CC_MasterVolume", volume.master)
	player:SetAttribute("CC_MusicVolume", volume.music)
	player:SetAttribute("CC_EffectsVolume", volume.effects)
	for _, root in ipairs({ SoundService, workspace }) do
		for _, d in ipairs(root:GetDescendants()) do applySound(d) end
	end
end
SoundService.DescendantAdded:Connect(applySound)
workspace.DescendantAdded:Connect(applySound)

local sliderSet = {}
local function slider(parent, y, title, key)
	local row = UI.new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, y), Size = UDim2.new(1, 0, 0, 64), Parent = parent })
	UI.label({ Text = title, FontFace = F.bold, TextSize = 17, Size = UDim2.new(0.6, 0, 0, 24), Parent = row })
	local percent = UI.label({ Text = "", FontFace = F.bold, TextSize = 17, TextColor3 = C.dim, TextXAlignment = Enum.TextXAlignment.Right,
		Size = UDim2.new(1, 0, 0, 24), Parent = row })
	local track = UI.new("TextButton", { Text = "", AutoButtonColor = false, BackgroundColor3 = C.bg3, BorderSizePixel = 0,
		Position = UDim2.fromOffset(0, 34), Size = UDim2.new(1, 0, 0, 10), Parent = row })
	UI.new("UICorner", { CornerRadius = UDim.new(0, 2), Parent = track })
 UI.new("UIStroke",{Color=C.line,Thickness=1,Transparency=0.4,Parent=track})
 track.ZIndex=2
	local fill = UI.new("Frame", { BackgroundColor3 = C.red, BorderSizePixel = 0, Size = UDim2.fromScale(volume[key], 1), ZIndex=2, Parent = track })
	UI.new("UICorner", { CornerRadius = UDim.new(1, 0), Parent = fill })
	local knob = UI.new("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.new(volume[key], 0, 0.5, 0), Size = UDim2.fromOffset(22, 22),
		BackgroundColor3 = C.red, BorderSizePixel = 0, ZIndex = 3, Parent = track })
	UI.new("UICorner", { CornerRadius = UDim.new(1, 0), Parent = knob })
	UI.new("UIStroke", { Color = C.text, Transparency = 0.12, Thickness = 2, Parent = knob })
	local dragging = false
	local function setAt(x)
		local v = math.clamp((x - track.AbsolutePosition.X) / math.max(track.AbsoluteSize.X, 1), 0, 1)
		v = math.floor(v * 20 + 0.5) / 20
		volume[key] = v
		fill.Size = UDim2.fromScale(v, 1)
		knob.Position = UDim2.new(v, 0, 0.5, 0)
		percent.Text = ("%d %%"):format(math.floor(v * 100 + 0.5))
		applyVolumes(); sendSettings()
	end
	sliderSet[key] = function(v)
		fill.Size = UDim2.fromScale(v, 1); knob.Position = UDim2.new(v, 0, 0.5, 0); percent.Text = ("%d %%"):format(math.floor(v * 100 + 0.5))
	end
	percent.Text = ("%d %%"):format(math.floor(volume[key] * 100 + 0.5))
	track.InputBegan:Connect(function(input)
		if input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.Touch then dragging = true; setAt(input.Position.X) end
	end)
	UIS.InputChanged:Connect(function(input)
		if dragging and (input.UserInputType == Enum.UserInputType.MouseMovement or input.UserInputType == Enum.UserInputType.Touch) then setAt(input.Position.X) end
	end)
	UIS.InputEnded:Connect(function(input)
		if input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.Touch then dragging = false end
	end)
	return track
end
slider(settingsCard, 42, "Master", "master")
slider(settingsCard, 108, "Music", "music")
slider(settingsCard, 174, "Effects", "effects")
local settingsNote = card(settings, 2, 192)
UI.label({ Text = "DISPLAY", FontFace = F.head, TextSize = 21, TextColor3 = C.text, Size = UDim2.new(1, 0, 0, 28), Parent = settingsNote })
do
local toggleSet = {}
local function toggle(y, title, key, invert)   -- invert: Schalter zeigt "AN", wenn der gespeicherte Wert false ist (Kamera-Wackeln an = noShake false)
	local row = UI.new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, y), Size = UDim2.new(1, 0, 0, 40), Parent = settingsNote })
	UI.label({ Text = title, FontFace = F.bold, TextSize = 17, Size = UDim2.new(0.62, 0, 1, 0), Parent = row })
	local b, parts
	local function show() local on = display[key] ~= (invert == true); b:SetAttribute("KitSprite",on and "toggle_on" or "toggle_off"); b:SetAttribute("Selected", on); parts.title.Text = on and "ON" or "OFF" end
	b, parts = UI.button({ Style = "secondary", Text = "", Size = UDim2.new(0.3, 0, 1, 0), Name = key, OnClick = function()
		display[key] = not display[key]; player:SetAttribute(key == "reduceFx" and "CC_ReduceFX" or key == "reduceMotion" and "CC_ReduceMotion" or "CC_NoShake", display[key]); show(); sendSettings()
	end, Parent = row })
	b.AnchorPoint = Vector2.new(1, 0); b.Position = UDim2.new(1, 0, 0, 0)
	toggleSet[key] = show; show()
end
toggle(34, "Strong effects (flashes, tint)", "reduceFx", true)
toggle(80, "Camera shake", "noShake", true)
toggle(126, "Reduce motion", "reduceMotion", false)
-- Gespeicherte Werte uebernehmen, sobald das Profil geladen ist (und bei spaeteren Server-Aenderungen)
local function loadSettings()
	if not player:GetAttribute("CC_SettingsLoaded") then return end
	volume.master = player:GetAttribute("CC_MasterVolume") or volume.master
	volume.music = player:GetAttribute("CC_MusicVolume") or volume.music
	volume.effects = player:GetAttribute("CC_EffectsVolume") or volume.effects
	display.reduceFx = player:GetAttribute("CC_ReduceFX") == true; display.noShake = player:GetAttribute("CC_NoShake") == true
	display.reduceMotion = player:GetAttribute("CC_ReduceMotion") == true
	for k, f in pairs(sliderSet) do f(volume[k]) end
	for _, f in pairs(toggleSet) do f() end
	applyVolumes()
end
player:GetAttributeChangedSignal("CC_SettingsLoaded"):Connect(loadSettings)
task.defer(loadSettings)
end
local settingsActions = UI.new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 56), LayoutOrder = 3, Parent = settings })
UI.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, HorizontalAlignment = Enum.HorizontalAlignment.Right,
	Padding = UDim.new(0, 10), SortOrder = Enum.SortOrder.LayoutOrder, Parent = settingsActions })
UI.button({ Style = "secondary", Text = "TUTORIAL", Icon = "help", Size = UDim2.new(0.34, -7, 1, 0), LayoutOrder = 1,
	OnClick = function() close(); RS:WaitForChild("CC_Tutorial"):FireServer("openWelcome") end, Parent = settingsActions })
UI.button({ Style = "secondary", Text = "WATCH INTRO", Size = UDim2.new(0.36, -7, 1, 0), LayoutOrder = 2,       -- Story-Film erneut (ohne Fortschritt)
	OnClick = function() close(); local r = RS:FindFirstChild("CC_Story"); if r then r:FireServer("replay") end end, Parent = settingsActions })
UI.button({ Style = "primary", Text = "DONE", Icon = "check", Size = UDim2.new(0.30, -6, 1, 0), LayoutOrder = 3,
	OnClick = function() back() end, Parent = settingsActions })
applyVolumes()

---------------------------------------------------------------------------------------------------
-- Buehne: Kopie des eigenen Kaempfers in Kampfhaltung, Kamera auf dem Einlaufsteg, Fight-Night-Licht
---------------------------------------------------------------------------------------------------
local stageYaw = 0
local stageBones = {}
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
	local wasArchivable = char.Archivable
	char.Archivable = true
	local ok, c = pcall(function() return char:Clone() end)
	char.Archivable = wasArchivable
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
local function previewDraft()
	if stage then
		Look.apply(stage, draft, templates())
		Look.applyBelt(stage, Look.resolveBelt(draft, Look.progressOf(player)), RS:FindFirstChild("CC_BeltParts"), true)   -- Guertel auch in der Vorschau
	end
end

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
	Lighting:SetAttribute("CC_MenuLighting", on == true)
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
header(edLeft, "MY FIGHTER").Size = UDim2.fromOffset(420, 48)
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
local rotText = UI.label({ Text = "ROTATE", FontFace = F.bold, TextSize = 17, TextColor3 = C.dim, Position = UDim2.fromOffset(38, 0), Size = UDim2.new(1, -38, 1, 0), Parent = rotLabel })
rotButton("next", 1, 3)
local saveState = UI.label({ Text = "", FontFace = F.bold, TextSize = 17, TextXAlignment = Enum.TextXAlignment.Right, Position = UDim2.fromOffset(0, 62), Size = UDim2.new(1, 0, 0, 26), Parent = edRight })
local btnRow = UI.new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 96), Size = UDim2.new(1, 0, 0, 58), Parent = edRight })
UI.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, HorizontalAlignment = Enum.HorizontalAlignment.Right, Padding = UDim.new(0, 12), SortOrder = Enum.SortOrder.LayoutOrder, Parent = btnRow })
local saving = false
local pending                      -- gesendetes Aussehen (wird nach Bestaetigung zu saved)
local saveMsg, saveMsgColor
local bReset = UI.button({ Style = "secondary", Text = "RESET", Size = UDim2.fromOffset(210, 58), LayoutOrder = 1, Parent = btnRow })
local bSave = UI.button({ Style = "primary", Text = "SAVE", Icon = "check", Size = UDim2.fromOffset(210, 58), LayoutOrder = 2, Parent = btnRow })
local edHints = UI.hints({ AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, 0, 0, 162), Size = UDim2.new(1, 0, 0, 28), Entries = {
	{ pc = "Q / E", pad = "LB / RB", text = "Rotate" }, { pc = "BACKSPACE", pad = "B", text = "Back" } }, Parent = edRight })

-- Kategorien (nur vorhandene Anpassungen waehlbar)
local CATS = {
	{ id = "hair", name = "HAIR", icon = "hair", key = "hair", list = Look.HAIR, colors = "hairColor", colorTitle = "HAIR COLOR" },
	{ id = "beard", name = "BEARD", icon = "beard", key = "beard", list = Look.BEARD, colors = "hairColor", colorTitle = "BEARD COLOR (= HAIR COLOR)" },
	{ id = "face", name = "FACE", icon = "face", key = "face", list = Look.FACE },
	{ id = "skin", name = "SKIN", icon = "skin", key = "skin", skin = true },
	{ id = "tattoo", name = "TATTOOS", icon = "star", locked = "Tattoos are not available yet." },
	{ id = "shorts", name = "SHORTS", icon = "shorts", key = "shorts", reward = Look.SHORTS },      -- Belohnungen (CC_LookShared): Level, Titel, Signaturen
	{ id = "gloves", name = "GLOVES", icon = "glove", key = "gloves", reward = Look.GLOVES },
	{ id = "belt", name = "BELT", icon = "trophy", key = "belt", reward = Look.BELTS },          -- Guertel: Titel (Karriere) und Stil (Signaturen)
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
	for _, p in ipairs(c:GetDescendants()) do
		if p:IsA("BasePart") then
			local m = p:FindFirstChildOfClass("Motor6D")
			if m and m.Part0 == hrp then p.CFrame = hrp.CFrame * m.C0 * m.C1:Inverse() end
			if Look.isHead(p.Name) then sum += p.Position; n += 1 end
			p.Anchored=true;p.CanCollide=false;p.CanTouch=false;p.CanQuery=false
		end
	end
	local center = hrp.Position + Vector3.new(0, 2.9, 0)
	local world=Instance.new("WorldModel");world.Parent=vp;c.Parent=world
	local vc = Instance.new("Camera"); vc.FieldOfView = 32
	local fwd = hrp.CFrame.LookVector
	vc.CFrame = CFrame.lookAt(center + fwd * 3.5 + hrp.CFrame.RightVector * 1.05 + Vector3.new(0, 0.65, 0), center)
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
	if cat.locked then midSub.Text = "Not available"; return end
	if cat.reward then                                   -- Farben: freigeschaltete waehlbar, gesperrte zeigen ihre Bedingung
		grid.Visible = false
		local prog = Look.progressOf(player)
		local n = 0
		for i, it in ipairs(cat.reward) do
			local ok = Look.unlocked(it, prog); if ok then n += 1 end
			local b = UI.swatch({ Color = it.color, LayoutOrder = i, Name = it.name, Size = UDim2.fromOffset(46, 46), Parent = swRow,
				OnClick = function()
					if ok then draft[cat.key] = i; previewDraft(); showCat(currentCat)
					else colorTitle.Text = it.name:upper() .. "  ·  LOCKED  ·  " .. Look.reqText(it) end
				end })
			if not ok then
				UI.icon("lock", { Size = UDim2.fromOffset(18, 18), AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), ZIndex = 5, ImageColor3 = UI.C.text, Parent = b })
				local dim = Instance.new("Frame"); dim.BackgroundColor3 = UI.C.bg0; dim.BackgroundTransparency = 0.45; dim.BorderSizePixel = 0
				dim.Size = UDim2.new(1, -10, 1, -10); dim.Position = UDim2.fromOffset(5, 5); dim.ZIndex = 3; dim.Parent = b
			end
			table.insert(swatches, { btn = b, key = cat.key, value = i })
		end
		midSub.Text = ("%d of %d unlocked"):format(n, #cat.reward)
		lockedNote.Visible = true
		lockedNote.Text = (cat.key == "belt" and "Each belt proves an achievement: title belts come from career wins, style belts from a coach's signature. Click a locked belt to see how to earn it." or "You unlock new colors through levels, career titles and signatures. Click a locked color to see its requirement.")
		local cur = cat.reward[draft[cat.key] or 1]
		colorTitle.Text = "SELECTED:  " .. (cur and cur.name:upper() or "")
		edMid.Size = UDim2.fromOffset(560, 340)
		refreshSelection()
		return
	end
	if cat.skin then
		midSub.Text = #Look.SKIN .. " Skin tones"
		for i = 1, #Look.SKIN do
			local l = Look.copy(draft); l.skin = i
			local b, vp = UI.optionCard({ Text = Look.SKIN_N[i], LayoutOrder = i, Parent = grid,
				OnClick = function() draft.skin = i; previewDraft(); refreshSelection() end })
			cardModel(vp, l)
			table.insert(cards, { btn = b, key = "skin", value = i })
		end
	else
		midSub.Text = #cat.list .. " Variants"
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
	saveMsg, saveMsgColor = "Saving …", C.dim
	pending = Look.copy(draft)
	lookEvent:FireServer(pending)
	task.delay(10, function() if saving then saving = false; saveMsg, saveMsgColor = "No response from server – please save again.", C.warn end end)
end
bSave:SetAttribute("Disabled", true)
-- Einstieg (CC_Tutorial, Phase "editor"): Knopf heisst FERTIG, ist immer aktiv, speichert bei Aenderungen und schliesst das Menue
local onboarding = false
local function finishOnboarding()
	if not onboarding then return end
	onboarding = false
	doSave()
	RS:WaitForChild("CC_Tutorial"):FireServer("editorDone")
	bSave:FindFirstChildWhichIsA("TextLabel").Text = "SAVE"
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
		saveMsg, saveMsgColor = "Applied – saving …", C.dim
	else
		saveMsg, saveMsgColor = text or "Cannot save.", C.warn
	end
end)
player:GetAttributeChangedSignal("CC_SaveStatus"):Connect(function()
	local s = tostring(player:GetAttribute("CC_SaveStatus")):match("^(%a+)")
	if not saveMsg or saving then return end
	if s == "ok" then saveMsg, saveMsgColor = "Saved", C.green
	elseif s == "offline" then saveMsg, saveMsgColor = "This session only (profile not loaded)", C.warn
	elseif s == "error" then saveMsg, saveMsgColor = "Saving failed – please try again later.", C.warn end
end)

-- Editor oeffnen/schliessen (beim Verlassen mit ungespeicherten Aenderungen nachfragen)
local function editorOpened()
 careerDetail.Visible=false
	saved = serverLook(); draft = Look.copy(saved); saveMsg = nil
	setStageYaw(0)
	previewDraft()
	camMode = "editor"
	menuLogo.Visible = false; menuTagline.Visible = false; profile.Visible = false; area.Visible = false; menuHints.Visible = false
	showCat(CATS[1])
	UI.focus(catButtons.hair)
end
local function editorClosed()
	camMode = "menu"
	draft = Look.copy(saved); previewDraft(); setStageYaw(0)
	menuLogo.Visible = true; menuTagline.Visible = true; profile.Visible = true; area.Visible = true; menuHints.Visible = true
end
local function confirmLeave(onLeave)
	if not dirty() then onLeave(); return end
	UI.dialog(canvas, "SAVE CHANGES?", "You changed your look but have not saved yet.", {
		{ Text = "DISCARD", Style = "secondary", OnClick = function() onLeave() end },
			{ Text = "SAVE", Style = "primary", OnClick = function() doSave(); onLeave() end },
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
 careerDetail.Visible=name=="career"
 menuLogo.Visible=name~="career" and name~="fighter"
 menuTagline.Visible=false
 area.Position=UDim2.fromOffset(36,name=="career" and 16 or 154)
 for n, p in pairs(pages) do p.Visible = n == name end
	if name == "fighter" then editorOpened(); return end
	if name == "career" then
		local beaten = Opponents.beatenSet(player:GetAttribute("CC_CareerBeaten"))
		local nextId = player:GetAttribute("CC_CareerNext")
		if nextId and Opponents.byId[nextId] then selectedCareerId = nextId end
		selectCareer(selectedCareerId); refreshCareer()
		local selectedRow=cRows[selectedCareerId]
		if selectedRow then task.defer(function()
			if not cRoster.Parent then return end
			local y=selectedRow.button.AbsolutePosition.Y-cRoster.AbsolutePosition.Y+cRoster.CanvasPosition.Y
			cRoster.CanvasPosition=Vector2.new(0,math.max(0,y-cRoster.AbsoluteSize.Y*.38))
		end) end
	elseif name == "progress" then
		refreshProgress()
	elseif stage then
		Look.apply(stage, draft, templates())
		local shorts = stage:FindFirstChild("Fighter_Shorts", true); if shorts and shorts:IsA("BasePart") then shorts.Color = Color3.fromRGB(144, 21, 30) end
	end
	-- Karriere zeigt Level/XP/Bilanz selbst und ist hoeher als der Platz ueber der Profilkarte -> Profilkarte dort ausblenden
	profile.Visible = name ~= "career" and name ~= "settings" and name ~= "progress"
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
	if #stack <= 1 then close(); return end
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
	if char and char:FindFirstChildOfClass("Humanoid") then
		cam.CameraSubject = char:FindFirstChildOfClass("Humanoid")
		local root = char:FindFirstChild("HumanoidRootPart")
		if root then
			cam.CFrame = CFrame.lookAt(root.Position - root.CFrame.LookVector * 9 + Vector3.new(0, 4, 0), root.Position + Vector3.new(0, 2, 0))
		end
	end
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
local menuBtn = UI.button({ Style = "secondary", Text = "MENU", Icon = "menu", Size = UDim2.fromOffset(130, 44), Name = "MenuButton",
	OnClick = function() open() end })
menuBtn.AnchorPoint = Vector2.new(0,1)
menuBtn.Position = UDim2.new(0,16,1,-18)
menuBtn.Parent = canvas
local menuKey = UI.key("M", { AnchorPoint = Vector2.new(0, 0.5), Position = UDim2.new(1, 8, 0.5, 0), Parent = menuBtn })
local function canOpen()
	local char = player.Character
	return not isOpen and (player:GetAttribute("CC_MatchId") or "")=="" and char and not char:GetAttribute("CC_Opponent") and not char:GetAttribute("CC_BagPractice") and not player:GetAttribute("CC_Minigame") and not player:GetAttribute("CC_TrainResultOpen") and not player:GetAttribute("CC_TrainerPanelOpen")
		and not char:GetAttribute("CC_Wrestle") and (player:GetAttribute("CC_OnbPhase") or "") == ""   -- waehrend des Einstiegs (CC_Tutorial) nicht
		and not ((state:GetAttribute("Mode") or "") ~= "" and (state:GetAttribute("RedName") == player.Name or state:GetAttribute("BlueName") == player.Name))   -- eigener Kampf inkl. Walkout
end
-- Lokale Navigation aus dem Gym; keine neuen Remote-Aufrufe fuer Menuewechsel.
local gymNavigate=Instance.new("BindableEvent")
gymNavigate.Name="CC_GymNavigate";gymNavigate.Parent=gui
gymNavigate.Event:Connect(function(page)
	if not ({online=true,fighter=true,progress=true,training=true})[page] then return end
	if canOpen() or isOpen then open(page) end
end)
CAS:BindActionAtPriority("CC_MenuOpen", function(_, st)
	if st ~= Enum.UserInputState.Begin then return Enum.ContextActionResult.Pass end
	if isOpen then
		if not canvas:FindFirstChild("Dialog") then back() end
		return Enum.ContextActionResult.Sink
	end
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
		if n >= 2 then return "Opponent found – " .. (busy and "you are up after the current fight." or "Fight starting …") end
		return "Searching … (" .. n .. " of 2 players)"
	elseif q == "training" then
		return busy and "Arena busy – training starts after the current fight." or "Training starting …"
	elseif q == "career" then
		return busy and "Fight Night busy – your career fight is waiting." or "Career fight starting …"
	end
	return nil
end
RunService.Heartbeat:Connect(function(dt)
	local char = player.Character
	local inFight = (state:GetAttribute("Mode") or "") ~= "" and (state:GetAttribute("RedName") == player.Name or state:GetAttribute("BlueName") == player.Name)   -- auch beim Walkout (noch ohne Gegner)
	if isOpen and char and (char:GetAttribute("CC_Opponent") or char:GetAttribute("CC_BagPractice") or player:GetAttribute("CC_Minigame") or player:GetAttribute("CC_TrainResultOpen") or inFight) then close() end
	if isOpen and char then
		local hum = char:FindFirstChildOfClass("Humanoid")
		if hum and hum.WalkSpeed ~= 0 then hum.WalkSpeed = 0 end
	end
	menuBtn.Visible = canOpen() and player:GetAttribute("CC_UIBlock")==nil and true or false
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
		if onboarding then bSave:SetAttribute("Disabled", saving); saveState.Text, saveState.TextColor3 = "Choose your look – you can change it anytime.", C.dim
		elseif d and not saving then saveState.Text, saveState.TextColor3 = "Unsaved changes", C.warn
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
	pInfo.Text = ("%d / %d XP   ·   Record %d-%d%s"):format(xp, nx, w, l, not loaded and "   ·   Profile not loaded" or "")
	pInfo.TextColor3 = not loaded and C.warn or C.dim
	if pages.career.Visible then refreshCareer() end
	-- Warteschlange
	local q = player:GetAttribute("CC_Queue")
	local txt = queueText()
	status.Visible = txt ~= nil and pages.home.Visible
	statusL.Text = txt or ""
	bSearch.Visible = q == nil; bCancel.Visible = q == "pvp"
	bSearch:SetAttribute("Disabled", q ~= nil)
	oState.Text = q == "pvp" and txt or (q == "training" and "You are signed up for a training fight." or "Ready.")
	oState.TextColor3 = q == "pvp" and C.gold or C.dim
	bFight:SetAttribute("Disabled", q ~= nil)
	tState.Text = q == "training" and txt or ""
	bTCancel.Visible = q == "training"
end)

-- Spiegel/Spind im Gym: Editor direkt oeffnen
player:GetAttributeChangedSignal("CC_OpenCustomize"):Connect(function()
	local char = player.Character
	if char and not char:GetAttribute("CC_Opponent") and not player:GetAttribute("CC_Minigame") and not player:GetAttribute("CC_TrainResultOpen") then open("fighter") end
end)
-- fuer andere UI-Skripte (z. B. Ergebnis-Bildschirm): Menue oeffnen per Attribut
player:GetAttributeChangedSignal("CC_OpenMainMenu"):Connect(function() if canOpen() then open() end end)

---------------------------------------------------------------------------------------------------
-- Ladebildschirm, dann Hauptmenue
---------------------------------------------------------------------------------------------------
local loading = UI.new("Frame", { Name = "Loading", BackgroundColor3 = C.bg0, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 50, Parent = canvas })
local lLogo = logo(loading, UDim2.fromScale(0.5, 0.4), 120, Vector2.new(0.5, 0.5))
for _, d in ipairs(lLogo:GetDescendants()) do if d:IsA("GuiObject") then d.ZIndex = 51 end end
local _, lFill = UI.bar({ AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0.61, 0), Size = UDim2.fromOffset(520, 7), ZIndex = 51, Parent = loading }, C.red)
lFill.ZIndex = 52
local lText = UI.label({ Text = "LOADING …", FontFace = F.bold, TextSize = 16, TextColor3 = C.dim, TextXAlignment = Enum.TextXAlignment.Center,
	AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0.61, 25), Size = UDim2.fromOffset(520, 30), ZIndex = 51, Parent = loading })

task.spawn(function()
	local steps = {
        { "Interface", function() local t0=os.clock(); while not UI.Ready and os.clock()-t0<6 do task.wait(0.1) end end },
		{ "Spielwelt", function() if not game:IsLoaded() then game.Loaded:Wait() end end },
		{ "Fighter", function() local c = player.Character or player.CharacterAdded:Wait(); c:WaitForChild("HumanoidRootPart", 15) end },
		{ "Profil", function() local t0 = os.clock(); while player:GetAttribute("CC_Level") == nil and os.clock() - t0 < 8 do task.wait(0.1) end end },
		{ "Aussehen", function() RS:WaitForChild("CC_CustomShared", 5) end },
		{ "Arena", function() workspace:WaitForChild("CC_Arena", 15) end },
		{ "Einstieg", function() local t0 = os.clock(); while player:GetAttribute("CC_OnbPhase") == nil and os.clock() - t0 < 10 do task.wait(0.1) end end },
	}
	for i, s in ipairs(steps) do
		lText.Text = "LOADING … " .. s[1]
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
		bSave:FindFirstChildWhichIsA("TextLabel").Text = "DONE"
	elseif ph == "" and char and not char:GetAttribute("CC_Opponent") then open() end   -- Begruessung zeigt CC_Tutorial selbst
	player:SetAttribute("CC_BootDone", true)                -- Ladefilm (ReplicatedFirst.CC_WalkIn_Client) darf uebergeben
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