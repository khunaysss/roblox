-- StarterGui.CC_MainMenuGui.MainMenu (LocalScript in einer ScreenGui)
-- Ladebildschirm, Hauptmenue und Navigation (UI-Ueberarbeitung Schritt 1, Designsystem: ReplicatedStorage.CC_UI).
-- Hintergrund: die Arena (Blick vom Einlaufsteg auf den Kaefig), rechts der eigene Kaempfer in Kampfhaltung
-- (lokale Kopie des Charakters, nur fuer diesen Spieler sichtbar). Der echte Charakter bleibt im Gym.
-- Waehrend das Menue offen ist (Attribut CC_UIBlock am Spieler, nur lokal): keine Kampf-Eingaben, kein Laufen,
-- kein HUD, keine Gym-Interaktionen. Ein Kampf (CC_Opponent) oder ein Minispiel (CC_Minigame) schliesst das Menue.
-- Menuepunkte:
--   KARRIERE      = Fortschritt (Level, Werte, Bilanz) + ins Gym. Eine echte Karriere (Gegnerliste, Titel) gibt es noch nicht.
--   ONLINE        = Warteschlange gegen Spieler (ReplicatedStorage.CC_Menu "pvp" / "cancel")
--   TRAINING      = Trainingskampf (CC_Menu "training") oder Gym-Training (Menue schliessen)
--   MEIN KAEMPFER = Aussehen (vorerst das bisherige Anpassungsfenster aus CC_MenuGui)
--   EINSTELLUNGEN = noch nicht vorhanden (als "BALD" markiert)
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local CAS = game:GetService("ContextActionService")
local GuiService = game:GetService("GuiService")
local TweenService = game:GetService("TweenService")
local PPS = game:GetService("ProximityPromptService")
local Lighting = game:GetService("Lighting")

local player = Players.LocalPlayer
local UI = require(RS:WaitForChild("CC_UI"))
local C, F = UI.C, UI.F
local menuEvent = RS:WaitForChild("CC_Menu")
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

local canvas = UI.new("Frame", { Name = "Canvas", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Parent = gui })
UI.autoscale(canvas, 760)

---------------------------------------------------------------------------------------------------
-- Hauptmenue-Ebene
---------------------------------------------------------------------------------------------------
local menu = UI.new("Frame", { Name = "Menu", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Visible = false, Parent = canvas })
local shadeL = UI.new("Frame", { BackgroundColor3 = C.bg0, BorderSizePixel = 0, Size = UDim2.fromScale(0.62, 1), Parent = menu })
UI.new("UIGradient", { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.08), NumberSequenceKeypoint.new(0.55, 0.45), NumberSequenceKeypoint.new(1, 1) }), Parent = shadeL })
local shadeB = UI.new("Frame", { BackgroundColor3 = C.bg0, BorderSizePixel = 0, AnchorPoint = Vector2.new(0, 1), Position = UDim2.fromScale(0, 1), Size = UDim2.new(1, 0, 0, 160), Parent = menu })
UI.new("UIGradient", { Rotation = -90, Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2), NumberSequenceKeypoint.new(1, 1) }), Parent = shadeB })

local function logo(parent, pos, size, anchor)
	local f = UI.new("Frame", { BackgroundTransparency = 1, Position = pos, AnchorPoint = anchor or Vector2.zero, Size = UDim2.fromOffset(600, size + 30), Parent = parent })
	local words = UI.new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, size + 6), Parent = f })
	UI.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 12), SortOrder = Enum.SortOrder.LayoutOrder,
		HorizontalAlignment = anchor and anchor.X == 0.5 and Enum.HorizontalAlignment.Center or Enum.HorizontalAlignment.Left, Parent = words })
	UI.label({ Text = "CAGE", FontFace = F.title, TextSize = size, TextColor3 = C.red, AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, size + 6), TextWrapped = false, LayoutOrder = 1, Parent = words })
	UI.label({ Text = "CHAMPIONS", FontFace = F.title, TextSize = size, TextColor3 = C.text, AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, size + 6), TextWrapped = false, LayoutOrder = 2, Parent = words })
	UI.new("Frame", { BackgroundColor3 = C.red, BorderSizePixel = 0, Position = UDim2.fromOffset(anchor and 150 or 2, size + 14), Size = UDim2.fromOffset(anchor and 300 or 120, 4), Parent = f })
	return f
end
logo(menu, UDim2.fromOffset(64, 56), 52)

-- Bereich links: Navigation bzw. Unterseite
local area = UI.new("Frame", { Name = "Area", BackgroundTransparency = 1, Position = UDim2.fromOffset(64, 176), Size = UDim2.fromOffset(470, 560), Parent = menu })

-- Profil-Karte unten links
local profile = UI.panel({ Name = "Profile", AnchorPoint = Vector2.new(0, 1), Position = UDim2.new(0, 64, 1, -56), Size = UDim2.fromOffset(470, 104), Parent = menu })
local pName = UI.label({ Text = player.DisplayName, FontFace = F.head, TextSize = 22, Position = UDim2.fromOffset(20, 12), Size = UDim2.new(1, -40, 0, 26), Parent = profile })
local pLevel = UI.label({ Text = "", FontFace = F.bold, TextSize = 15, TextColor3 = C.gold, TextXAlignment = Enum.TextXAlignment.Right, Position = UDim2.fromOffset(20, 14), Size = UDim2.new(1, -40, 0, 22), Parent = profile })
local _, pXP = UI.bar({ Position = UDim2.fromOffset(20, 46), Size = UDim2.new(1, -40, 0, 6), Parent = profile }, C.gold)
local pInfo = UI.label({ Text = "", TextSize = 14, TextColor3 = C.dim, Position = UDim2.fromOffset(20, 60), Size = UDim2.new(1, -40, 0, 30), Parent = profile })

UI.hints({ AnchorPoint = Vector2.new(1, 1), Position = UDim2.new(1, -48, 1, -40), Entries = {
	{ pc = "KLICK", pad = "A", text = "Auswählen" }, { pc = "RÜCKTASTE", pad = "B", text = "Zurück" } }, Parent = menu })

local status = UI.panel({ Name = "Status", AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0, 40), Size = UDim2.fromOffset(460, 54), Visible = false, Parent = menu })
local statusL = UI.label({ Text = "", FontFace = F.bold, TextSize = 17, TextXAlignment = Enum.TextXAlignment.Center, Size = UDim2.fromScale(1, 1), Parent = status })

---------------------------------------------------------------------------------------------------
-- Seiten
---------------------------------------------------------------------------------------------------
local pages, stack = {}, {}
local open, close, go, back

local function page(name)
	local f = UI.new("Frame", { Name = name, BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Visible = false, Parent = area })
	UI.new("UIListLayout", { Padding = UDim.new(0, 10), SortOrder = Enum.SortOrder.LayoutOrder, Parent = f })
	pages[name] = f
	return f
end
local function header(p, title)
	local h = UI.new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 48), LayoutOrder = 0, Parent = p })
	UI.button({ Icon = "back", Style = "ghost", Size = UDim2.fromOffset(48, 44), Name = "Back", OnClick = function() back() end, Parent = h })
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
nav(3, "TRAINING", "Trainingskampf oder Gym-Training", "dumbbell", function() go("training") end)
nav(4, "MEIN KÄMPFER", "Aussehen anpassen", "fighter", function() go("fighter") end)
nav(5, "EINSTELLUNGEN", "Noch nicht verfügbar", "gear", nil, true, "BALD")

-- Karriere (= ehrlicher Fortschritt; eine echte Karriere gibt es noch nicht)
local career = page("career")
header(career, "KARRIERE")
local cStats = card(career, 1, 236)
UI.new("UIListLayout", { Padding = UDim.new(0, 6), SortOrder = Enum.SortOrder.LayoutOrder, Parent = cStats })
local cLevel = UI.label({ Text = "", FontFace = F.head, TextSize = 20, TextColor3 = C.gold, LayoutOrder = 1, Parent = cStats })
local _, cXP = UI.bar({ LayoutOrder = 2, Parent = cStats }, C.gold)
local STATS = { { "Power", "Schlagkraft" }, { "Cardio", "Kondition" }, { "Wrestling", "Ringen" }, { "Grappling", "Bodenkampf" } }
local statRows = {}
for i, s in ipairs(STATS) do
	local r = UI.new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 30), LayoutOrder = 2 + i, Parent = cStats })
	local l = UI.label({ Text = s[2], FontFace = F.bold, TextSize = 15, Size = UDim2.new(0.4, 0, 0, 20), Parent = r })
	local v = UI.label({ Text = "", FontFace = F.bold, TextSize = 15, TextXAlignment = Enum.TextXAlignment.Right, Size = UDim2.new(1, 0, 0, 20), Parent = r })
	local _, fill = UI.bar({ Position = UDim2.fromOffset(0, 22), Size = UDim2.new(1, 0, 0, 5), Parent = r }, C.blue)
	statRows[s[1]] = { v, fill, l }
end
local cRecord = UI.label({ Text = "", TextSize = 15, TextColor3 = C.dim, LayoutOrder = 9, Parent = cStats })
local cNote = card(career, 2, 70)
UI.label({ Text = "Werte steigen durch Gym-Training und Kämpfe. Eine Karriere mit Gegnerliste und Titeln gibt es noch nicht.",
	TextSize = 14, TextColor3 = C.dim, Size = UDim2.fromScale(1, 1), Parent = cNote })
local bGym = UI.button({ Style = "primary", Text = "INS GYM", Icon = "dumbbell", LayoutOrder = 3, OnClick = function() close() end, Parent = career })

-- Online
local online = page("online")
header(online, "ONLINE")
local oCard = card(online, 1, 92)
UI.label({ Text = "SCHNELLER KAMPF", FontFace = F.head, TextSize = 18, Size = UDim2.new(1, 0, 0, 24), Parent = oCard })
UI.label({ Text = "Du kämpfst gegen den nächsten Spieler in der Warteschlange. 3 Runden, je 2 Minuten.",
	TextSize = 14, TextColor3 = C.dim, Position = UDim2.fromOffset(0, 28), Size = UDim2.new(1, 0, 0, 36), Parent = oCard })
local oState = UI.label({ Text = "", FontFace = F.bold, TextSize = 16, LayoutOrder = 2, Size = UDim2.new(1, 0, 0, 26), Parent = online })
local bSearch = UI.button({ Style = "primary", Text = "SUCHE STARTEN", Icon = "search", LayoutOrder = 3, OnClick = function() menuEvent:FireServer("pvp") end, Parent = online })
local bCancel = UI.button({ Style = "danger", Text = "SUCHE ABBRECHEN", Icon = "close", LayoutOrder = 4, OnClick = function() menuEvent:FireServer("cancel") end, Parent = online })
UI.button({ Style = "secondary", Text = "GEWERTET", Sub = "Rangliste gibt es noch nicht", Icon = "star", LayoutOrder = 5, Disabled = true, Badge = "NICHT VERFÜGBAR", Parent = online })

-- Training
local training = page("training")
header(training, "TRAINING")
local bFight = UI.button({ Style = "nav", Text = "TRAININGSKAMPF", Sub = "Gegen den Trainingsgegner · zählt nicht zur Bilanz", Icon = "glove", LayoutOrder = 1,
	OnClick = function() menuEvent:FireServer("training") end, Parent = training })
UI.button({ Style = "nav", Text = "GYM-TRAINING", Sub = "Minispiele an den Stationen · Werte steigern", Icon = "dumbbell", LayoutOrder = 2,
	OnClick = function() close() end, Parent = training })
local tState = UI.label({ Text = "", FontFace = F.bold, TextSize = 16, LayoutOrder = 3, Size = UDim2.new(1, 0, 0, 26), Parent = training })
local bTCancel = UI.button({ Style = "danger", Text = "ABBRECHEN", Icon = "close", LayoutOrder = 4, OnClick = function() menuEvent:FireServer("cancel") end, Parent = training })

-- Mein Kaempfer (vorerst: bisheriges Anpassungsfenster aus CC_MenuGui)
local fighter = page("fighter")
header(fighter, "MEIN KÄMPFER")

---------------------------------------------------------------------------------------------------
-- Buehne: Kopie des eigenen Kaempfers in Kampfhaltung, Kamera auf dem Einlaufsteg
---------------------------------------------------------------------------------------------------
local stage, stageTrack
local stageYaw = 0
local dofSaved
local rayParams = RaycastParams.new(); rayParams.FilterType = Enum.RaycastFilterType.Exclude
local function floorY(pos, ignore)
	rayParams.FilterDescendantsInstances = ignore
	local hit = workspace:Raycast(pos + Vector3.new(0, 4, 0), Vector3.new(0, -30, 0), rayParams)
	return hit and hit.Position.Y
end
local function buildStage()
	if stage then stage:Destroy(); stage = nil end
	local char = player.Character
	local root = char and char:FindFirstChild("HumanoidRootPart")
	local hum = char and char:FindFirstChildOfClass("Humanoid")
	if not (root and hum) then return end
	char.Archivable = true
	local ok, c = pcall(function() return char:Clone() end)
	char.Archivable = false
	if not ok or not c then return end
	for _, d in ipairs(c:GetDescendants()) do
		if d:IsA("BaseScript") or d:IsA("ProximityPrompt") or d:IsA("BillboardGui") then d:Destroy() end
	end
	c.Name = "CC_MenuFighter"
	for _, a in ipairs(c:GetAttributes()) do c:SetAttribute(a, nil) end
	local h = c:FindFirstChildOfClass("Humanoid")
	h.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	h.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
	local cr = c:FindFirstChild("HumanoidRootPart")
	cr.Anchored = true
	local gymFloor = floorY(root.Position, { char, workspace:FindFirstChild("CC_Props") })
	local hipOff = gymFloor and (root.Position.Y - gymFloor) or 3
	local base = Vector3.new(FIGHTER_POS.X, (floorY(FIGHTER_POS, { char }) or FIGHTER_POS.Y) + hipOff, FIGHTER_POS.Z)
	local face = Vector3.new(CAM_POS.X, base.Y, CAM_POS.Z)
	c:PivotTo(CFrame.lookAt(base, face) * CFrame.Angles(0, math.rad(-18 + stageYaw), 0))
	c.Parent = workspace
	stage = c
	local id = RS:GetAttribute("CC_AnimId_Fighter_Idle_v08")
	if id then
		local an = h:FindFirstChildOfClass("Animator") or Instance.new("Animator", h)
		local a = Instance.new("Animation"); a.AnimationId = "rbxassetid://" .. tostring(id)
		stageTrack = an:LoadAnimation(a); stageTrack.Looped = true; stageTrack:Play(0)
	end
end
local function setStageYaw(y)
	stageYaw = y
	if stage then
		local p = stage:GetPivot().Position
		stage:PivotTo(CFrame.lookAt(p, Vector3.new(CAM_POS.X, p.Y, CAM_POS.Z)) * CFrame.Angles(0, math.rad(-18 + stageYaw), 0))
	end
end
local cam = workspace.CurrentCamera
local function stageCamera()
	cam.CameraType = Enum.CameraType.Scriptable
	cam.FieldOfView = CAM_FOV
	local t = os.clock()
	local sway = Vector3.new(math.sin(t * 0.25) * 0.25, math.sin(t * 0.33) * 0.08, 0)   -- leichte Kamerabewegung
	cam.CFrame = CFrame.lookAt(CAM_POS + sway, CAM_AIM)
end
local function setDof(on)
	local dof = Lighting:FindFirstChildOfClass("DepthOfFieldEffect")
	if not dof then return end
	if on then
		dofSaved = dofSaved or { dof.Enabled, dof.FarIntensity, dof.FocusDistance, dof.InFocusRadius, dof.NearIntensity }
		dof.Enabled = true; dof.FarIntensity = 0.28; dof.FocusDistance = (FIGHTER_POS - CAM_POS).Magnitude; dof.InFocusRadius = 8; dof.NearIntensity = 0
	elseif dofSaved then
		dof.Enabled, dof.FarIntensity, dof.FocusDistance, dof.InFocusRadius, dof.NearIntensity = table.unpack(dofSaved)
		dofSaved = nil
	end
end

---------------------------------------------------------------------------------------------------
-- Oeffnen / Schliessen / Navigation
---------------------------------------------------------------------------------------------------
local isOpen = false
local function otherGuis(on)
	local pg = player:FindFirstChildOfClass("PlayerGui")
	local hud = pg and pg:FindFirstChild("CC_HUD")
	if hud then hud.Enabled = on end
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
	local p = pages[name]
	-- Controller: erstes waehlbares Element der Seite
	local first
	for _, d in ipairs(p:GetDescendants()) do
		if d:IsA("GuiButton") and d.Selectable and d.Visible and d.Name ~= "Back" then
			if not first or d.AbsolutePosition.Y < first.AbsolutePosition.Y then first = d end
		end
	end
	UI.focus(first or p:FindFirstChild("Back", true))
	if name == "fighter" then player:SetAttribute("CC_OpenCustomize", os.clock()) end
end
function go(name)
	table.insert(stack, name)
	showPage(name)
end
function back()
	if #stack <= 1 then return end
	local leaving = table.remove(stack)
	if leaving == "fighter" then player:SetAttribute("CC_CloseCustomize", os.clock()) end
	showPage(stack[#stack])
end
function open()
	if isOpen then return end
	isOpen = true
	stack = { "home" }
	showPage("home")
	menu.Visible = true
	blockGameplay(true)
	otherGuis(false)
	buildStage()
	setDof(true)
	RunService:BindToRenderStep("CC_MenuCamera", Enum.RenderPriority.Camera.Value + 10, stageCamera)
	UI.focus(navButtons[1])
end
function close()
	if not isOpen then return end
	isOpen = false
	if stack[#stack] == "fighter" then player:SetAttribute("CC_CloseCustomize", os.clock()) end
	menu.Visible = false
	RunService:UnbindFromRenderStep("CC_MenuCamera")
	if stage then stage:Destroy(); stage = nil end
	setDof(false)
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
	if st == Enum.UserInputState.Begin then back() end
	return Enum.ContextActionResult.Sink
end, false, 3000, Enum.KeyCode.Backspace, Enum.KeyCode.ButtonB)

---------------------------------------------------------------------------------------------------
-- Menue-Knopf im Gym (wenn das Menue zu ist): Klick, M oder Controller-Select
---------------------------------------------------------------------------------------------------
local menuBtn = UI.button({ Style = "secondary", Text = "MENÜ", Icon = "menu", Size = UDim2.fromOffset(150, 46), Name = "MenuButton",
	OnClick = function() open() end })
menuBtn.Position = UDim2.fromOffset(24, 76)
menuBtn.Parent = canvas
local menuKey = UI.key("M", { AnchorPoint = Vector2.new(0, 0.5), Position = UDim2.new(1, 8, 0.5, 0), Parent = menuBtn })
local function canOpen()
	local char = player.Character
	return not isOpen and char and not char:GetAttribute("CC_Opponent") and not player:GetAttribute("CC_Minigame")
		and not char:GetAttribute("CC_Wrestle")
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
	local mode = state:GetAttribute("Mode") or ""
	local busy = mode ~= ""
	if q == "pvp" then
		local n = state:GetAttribute("QueuePvp") or 0
		if n >= 2 then return "Gegner gefunden – " .. (busy and "ihr seid nach dem laufenden Kampf dran." or "Kampf startet …") end
		return "Suche läuft … (" .. n .. " von 2 Spielern)"
	elseif q == "training" then
		return busy and "Arena belegt – Training startet nach dem laufenden Kampf." or "Training startet …"
	end
	return nil
end
RunService.Heartbeat:Connect(function()
	local char = player.Character
	-- Kampf oder Minispiel beginnt: Menue zu
	if isOpen and char and (char:GetAttribute("CC_Opponent") or player:GetAttribute("CC_Minigame")) then close() end
	if isOpen and char then
		local hum = char:FindFirstChildOfClass("Humanoid")
		if hum and hum.WalkSpeed ~= 0 then hum.WalkSpeed = 0 end
	end
	menuBtn.Visible = canOpen() and true or false
	menuKey.Visible = UI.device() == "pc"
	if not isOpen then return end
	-- Profil
	local lv, xp, nx = player:GetAttribute("CC_Level") or 1, player:GetAttribute("CC_XP") or 0, player:GetAttribute("CC_XPNext") or 100
	local w, l = player:GetAttribute("CC_Wins") or 0, player:GetAttribute("CC_Losses") or 0
	pLevel.Text = ("LEVEL %d"):format(lv)
	pXP.Size = UDim2.fromScale(math.clamp(xp / nx, 0, 1), 1)
	local saved = player:GetAttribute("CC_ProfileSaved")
	pInfo.Text = ("%d / %d XP   ·   Bilanz %d-%d%s"):format(xp, nx, w, l, saved == false and "   ·   Speichern fehlgeschlagen" or "")
	pInfo.TextColor3 = saved == false and C.warn or C.dim
	if pages.career.Visible then
		cLevel.Text = ("LEVEL %d   ·   %d / %d XP"):format(lv, xp, nx)
		cXP.Size = UDim2.fromScale(math.clamp(xp / nx, 0, 1), 1)
		for key, row in pairs(statRows) do
			local v, tp = player:GetAttribute("CC_" .. key) or 0, player:GetAttribute("CC_" .. key .. "TP") or 0
			row[1].Text = ("%d / 20   (+%d/10)"):format(v, tp)
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

-- Aussehen geaendert: Buehnen-Kopie neu aufbauen (der Server tauscht die Teile am echten Charakter)
player:GetAttributeChangedSignal("CC_Look"):Connect(function()
	if not isOpen then return end
	task.delay(0.4, function() if isOpen then buildStage() end end)
end)

---------------------------------------------------------------------------------------------------
-- Ladebildschirm, dann Hauptmenue
---------------------------------------------------------------------------------------------------
local loading = UI.new("Frame", { Name = "Loading", BackgroundColor3 = C.bg0, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 50, Parent = canvas })
local lLogo = logo(loading, UDim2.fromScale(0.5, 0.42), 64, Vector2.new(0.5, 0.5))
for _, d in ipairs(lLogo:GetDescendants()) do if d:IsA("GuiObject") then d.ZIndex = 51 end end
local _, lFill = UI.bar({ AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0.56, 0), Size = UDim2.fromOffset(360, 4), ZIndex = 51, Parent = loading }, C.red)
lFill.ZIndex = 52
local lText = UI.label({ Text = "LÄDT …", FontFace = F.bold, TextSize = 14, TextColor3 = C.dim, TextXAlignment = Enum.TextXAlignment.Center,
	AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0.56, 14), Size = UDim2.fromOffset(360, 20), ZIndex = 51, Parent = loading })

task.spawn(function()
	local steps = {
		{ "Spielwelt", function() if not game:IsLoaded() then game.Loaded:Wait() end end },
		{ "Kämpfer", function() local c = player.Character or player.CharacterAdded:Wait(); c:WaitForChild("HumanoidRootPart", 15) end },
		{ "Profil", function() local t0 = os.clock(); while player:GetAttribute("CC_Level") == nil and os.clock() - t0 < 8 do task.wait(0.1) end end },
		{ "Arena", function() workspace:WaitForChild("CC_Arena", 15) end },
	}
	for i, s in ipairs(steps) do
		lText.Text = "LÄDT … " .. s[1]
		pcall(s[2])
		TweenService:Create(lFill, TweenInfo.new(0.25), { Size = UDim2.fromScale(i / #steps, 1) }):Play()
		task.wait(0.15)
	end
	task.wait(0.2)
	local char = player.Character
	if char and not char:GetAttribute("CC_Opponent") then open() end
	TweenService:Create(loading, TweenInfo.new(0.5), { BackgroundTransparency = 1 }):Play()
	for _, d in ipairs(loading:GetDescendants()) do
		if d:IsA("TextLabel") then TweenService:Create(d, TweenInfo.new(0.4), { TextTransparency = 1 }):Play()
		elseif d:IsA("Frame") then TweenService:Create(d, TweenInfo.new(0.4), { BackgroundTransparency = 1 }):Play() end
	end
	task.wait(0.55)
	loading.Visible = false
end)

-- nach Respawn: Bewegungssperre ggf. neu setzen
player.CharacterAdded:Connect(function()
	task.wait(0.2)
	if isOpen then blockGameplay(true); buildStage() end
end)

-- fuer andere UI-Skripte (z. B. Ergebnis-Bildschirm): Menue oeffnen per Attribut
player:GetAttributeChangedSignal("CC_OpenMainMenu"):Connect(function() if canOpen() then open() end end)
