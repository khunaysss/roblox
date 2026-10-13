-- StarterGui.CC_GymHUD.GymHUD (LocalScript in einer ScreenGui)
-- Gym-Oberflaeche (UI-Ueberarbeitung Schritt 2, Designsystem ReplicatedStorage.CC_UI):
--   * Profil-Karte oben links: Level, XP, 4 Werte mit Trainingspunkten (10 TP = +1 Wert)
--   * "NAECHSTE AUFGABE" oben rechts: aus den echten Werten abgeleitet (schwaecherer Gym-Wert -> passende Station)
--   * eigene Interaktions-Hinweise fuer die Gym-Stationen (ProximityPrompt Style Custom, nur lokal umgestellt):
--     Taste je Geraet (PC-Taste / Controller-Taste / Antippen auf Touch), Station, Aktion, was trainiert wird
--   * Trainingsplan (Station "Trainingsplan", Attribut CC_OpenPlan vom Server)
--   * Hinweise (CC_Notice, CC_LevelUp, CC_StatUp) als Meldungen oben mittig (ersetzt die alten HUD-Meldungen)
-- Ausgeblendet im Kampf (Profil/Aufgabe), im Hauptmenue (ganze Ebene) und waehrend eines Minispiels (Profil/Aufgabe).
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local PPS = game:GetService("ProximityPromptService")
local TweenService = game:GetService("TweenService")
local CAS = game:GetService("ContextActionService")

local player = Players.LocalPlayer
local UI = require(RS:WaitForChild("CC_UI"))
local C, F = UI.C, UI.F
local gui = script.Parent
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = true
gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
gui.DisplayOrder = 10

local canvas = UI.new("Frame", { Name = "Canvas", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Parent = gui })
UI.autoscale(canvas, 720)

local STATS = { { "Power", "Schlagkraft" }, { "Cardio", "Kondition" }, { "Wrestling", "Ringen" }, { "Grappling", "Bodenkampf" } }
local STAT_DE = { Power = "Schlagkraft", Cardio = "Kondition", Wrestling = "Ringen", Grappling = "Bodenkampf" }
local WHERE = {
	Power = "Sandsack, Hantelbank oder Kurzhanteln",
	Cardio = "Laufband, Hampelmann auf der Trainingsmatte · jede Kampfrunde",
	Wrestling = "Takedowns und Sprawls im Kampf",
	Grappling = "Positionen, Befreien und Submissions im Kampf",
}

---------------------------------------------------------------------------------------------------
-- Profil-Karte
---------------------------------------------------------------------------------------------------
local prof = UI.panel({ Name = "Profile", Position = UDim2.fromOffset(20, 130), Size = UDim2.fromOffset(300, 214), Parent = canvas })
UI.new("UIPadding", { PaddingLeft = UDim.new(0, 16), PaddingRight = UDim.new(0, 16), PaddingTop = UDim.new(0, 12), Parent = prof })
local lvL = UI.label({ Text = "", FontFace = F.head, TextSize = 20, TextColor3 = C.gold, Size = UDim2.new(1, 0, 0, 26), Parent = prof })
local xpL = UI.label({ Text = "", FontFace = F.bold, TextSize = 15, TextColor3 = C.dim, TextXAlignment = Enum.TextXAlignment.Right, Size = UDim2.new(1, 0, 0, 26), Parent = prof })
local _, xpFill = UI.bar({ Position = UDim2.fromOffset(0, 30), Size = UDim2.new(1, 0, 0, 6), Parent = prof }, C.gold)
local rows = {}
for i, s in ipairs(STATS) do
	local y = 46 + (i - 1) * 40
	local name = UI.label({ Text = s[2], FontFace = F.bold, TextSize = 16, Position = UDim2.fromOffset(0, y), Size = UDim2.new(0.6, 0, 0, 22), Parent = prof })
	local val = UI.label({ Text = "", FontFace = F.bold, TextSize = 16, TextXAlignment = Enum.TextXAlignment.Right, Position = UDim2.fromOffset(0, y), Size = UDim2.new(1, 0, 0, 22), Parent = prof })
	-- 10 Trainingspunkte als Segmente
	local pips = {}
	for k = 1, 10 do
		pips[k] = UI.new("Frame", { BackgroundColor3 = C.bg3, BorderSizePixel = 0, Position = UDim2.new((k - 1) / 10, 1, 0, y + 25), Size = UDim2.new(0.1, -3, 0, 6), Parent = prof })
	end
	rows[s[1]] = { name = name, val = val, pips = pips }
end

---------------------------------------------------------------------------------------------------
-- Naechste Aufgabe
---------------------------------------------------------------------------------------------------
local task_ = UI.panel({ Name = "NextTask", AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -20, 0, 70), Size = UDim2.fromOffset(380, 112), Parent = canvas })
UI.new("UIPadding", { PaddingLeft = UDim.new(0, 18), PaddingRight = UDim.new(0, 18), PaddingTop = UDim.new(0, 12), Parent = task_ })
UI.new("Frame", { BackgroundColor3 = C.red, BorderSizePixel = 0, Position = UDim2.new(0, -18, 0, 4), Size = UDim2.new(0, 5, 1, -28), Parent = task_ })
UI.label({ Text = "NÄCHSTE AUFGABE", FontFace = F.bold, TextSize = 14, TextColor3 = C.red, Size = UDim2.new(1, 0, 0, 18), Parent = task_ })
local taskTitle = UI.label({ Text = "", FontFace = F.head, TextSize = 21, Position = UDim2.fromOffset(0, 20), Size = UDim2.new(1, 0, 0, 28), Parent = task_ })
local taskSub = UI.label({ Text = "", TextSize = 16, TextColor3 = C.dim, TextYAlignment = Enum.TextYAlignment.Top, Position = UDim2.fromOffset(0, 50), Size = UDim2.new(1, 0, 0, 44), Parent = task_ })

local function attr(n, d) return player:GetAttribute(n) or d end
local function updateTask()
	-- schwaecherer der beiden Gym-Werte (Wert*10 + TP); bei Gleichstand Schlagkraft
	local best, bestV
	for _, s in ipairs({ "Power", "Cardio" }) do
		local v = attr("CC_" .. s, 0) * 10 + attr("CC_" .. s .. "TP", 0)
		if attr("CC_" .. s, 0) < 20 and (not bestV or v < bestV) then best, bestV = s, v end
	end
	if not best then
		taskTitle.Text = "Kämpfen"
		taskSub.Text = "Schlagkraft und Kondition sind voll. Ringen und Bodenkampf steigen im Kampf (Trainer: Trainingskampf)."
		return
	end
	local v, tp = attr("CC_" .. best, 0), attr("CC_" .. best .. "TP", 0)
	taskTitle.Text = STAT_DE[best] .. " trainieren"
	taskSub.Text = ("%s · noch %d TP bis %s %d"):format(best == "Power" and "Sandsack, Hantelbank, Kurzhanteln" or "Laufband oder Hampelmann",
		10 - tp, STAT_DE[best], v + 1)
end

---------------------------------------------------------------------------------------------------
-- Meldungen (oben mittig, gestapelt)
---------------------------------------------------------------------------------------------------
local toastHolder = UI.new("Frame", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0, 92), Size = UDim2.fromOffset(620, 300), Parent = canvas })
UI.new("UIListLayout", { Padding = UDim.new(0, 8), HorizontalAlignment = Enum.HorizontalAlignment.Center, SortOrder = Enum.SortOrder.LayoutOrder, Parent = toastHolder })
local toastN = 0
local function toast(text, color, icon)
	toastN += 1
	local t = UI.panel({ AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, 46), LayoutOrder = toastN, Parent = toastHolder })
	UI.new("UIPadding", { PaddingLeft = UDim.new(0, 16), PaddingRight = UDim.new(0, 20), Parent = t })
	UI.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, VerticalAlignment = Enum.VerticalAlignment.Center, Padding = UDim.new(0, 10), Parent = t })
	if icon then UI.icon(icon, { Size = UDim2.fromOffset(24, 24), ImageColor3 = color or C.text, Parent = t }) end
	UI.label({ Text = text, FontFace = F.bold, TextSize = 18, TextColor3 = color or C.text, AutomaticSize = Enum.AutomaticSize.X, TextWrapped = false,
		Size = UDim2.fromOffset(0, 46), Parent = t })
	task.delay(3.6, function() if t.Parent then t:Destroy() end end)
	if #toastHolder:GetChildren() > 4 then
		local oldest
		for _, c in ipairs(toastHolder:GetChildren()) do if c:IsA("GuiObject") and (not oldest or c.LayoutOrder < oldest.LayoutOrder) then oldest = c end end
		if oldest then oldest:Destroy() end
	end
end
player:GetAttributeChangedSignal("CC_Notice"):Connect(function()
	local t = player:GetAttribute("CC_Notice"); if t then toast(t:match("^(.*)|") or t, C.text, "warn") end
end)
-- Bodenlage: Aufstehen nicht moeglich, weil der Gegner direkt am Koerper steht
local function hookChar(c)
	c:GetAttributeChangedSignal("CC_DownBlocked"):Connect(function() toast("Gegner zu nah – erst Abstand schaffen (Stoßtritt)", C.warn, "warn") end)
end
player.CharacterAdded:Connect(hookChar)
if player.Character then hookChar(player.Character) end
player:GetAttributeChangedSignal("CC_LevelUp"):Connect(function()
	toast("LEVEL UP!  Level " .. tostring(player:GetAttribute("CC_LevelUp")), C.gold, "star")
end)
player:GetAttributeChangedSignal("CC_StatUp"):Connect(function()
	local s_, v = tostring(player:GetAttribute("CC_StatUp")):match("^(%w+):(%d+)")
	if s_ then toast((STAT_DE[s_] or s_) .. " steigt auf " .. v .. " / 20", C.blue, "trophy") end
end)

---------------------------------------------------------------------------------------------------
-- Stations-Hinweise (eigene ProximityPrompt-Darstellung)
---------------------------------------------------------------------------------------------------
local gymFolder = workspace:WaitForChild("CC_GymInteractions", 20)
local TRAINS = {
	punch_bag = "Schlagkraft · Tastenfolge", punch_bag_standing = "Schlagkraft · Tastenfolge",
	bench_press = "Schlagkraft · Rhythmus", bench_dumbbell = "Schlagkraft · Rhythmus",
	stretch_spot = "Kondition · Rhythmus", treadmill = "Kondition · Tempo halten", coach_talk = "Trainingskampf (ohne Bilanz)",
	character_customization = "Aussehen ändern", locker = "Aussehen ändern", read_plan = "Werte und Trainingsorte",
}
local function isGymPrompt(p) return gymFolder and p:IsA("ProximityPrompt") and p:IsDescendantOf(gymFolder) end
local function styleCustom(p) if isGymPrompt(p) then p.Style = Enum.ProximityPromptStyle.Custom end end
if gymFolder then
	for _, d in ipairs(gymFolder:GetDescendants()) do styleCustom(d) end
	gymFolder.DescendantAdded:Connect(styleCustom)
end
local PAD_NAME = { ButtonX = "X", ButtonY = "Y", ButtonA = "A", ButtonB = "B" }
local shown = {}
PPS.PromptShown:Connect(function(prompt, inputType)
	if not isGymPrompt(prompt) then return end
	if shown[prompt] then shown[prompt]:Destroy() end
	local bb = UI.new("BillboardGui", { Name = "CC_Prompt", Adornee = prompt.Parent, AlwaysOnTop = true, Size = UDim2.fromOffset(340, 86),
		StudsOffset = Vector3.new(0, 2.6, 0), LightInfluence = 0, Active = true, ResetOnSpawn = false })
	local btn = UI.new("TextButton", { Text = "", AutoButtonColor = false, BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Parent = bb })
	UI.chamfer({ Size = UDim2.fromScale(1, 1), ImageColor3 = C.bg1, ImageTransparency = 0.02, Parent = btn }, "fill", 12)
	UI.new("Frame", { BackgroundColor3 = C.red, BorderSizePixel = 0, Position = UDim2.fromOffset(0, 10), Size = UDim2.new(0, 5, 1, -20), Parent = btn })
	local keyText
	if inputType == Enum.ProximityPromptInputType.Gamepad then keyText = PAD_NAME[prompt.GamepadKeyCode.Name] or prompt.GamepadKeyCode.Name
	elseif inputType == Enum.ProximityPromptInputType.Touch then keyText = nil
	else keyText = prompt.KeyboardKeyCode.Name end
	local x = 18
	if keyText then
		local k = UI.key(keyText, { AnchorPoint = Vector2.new(0, 0.5), Position = UDim2.new(0, x, 0.5, 0), Size = UDim2.fromOffset(40, 40), Parent = btn })
		k:FindFirstChildWhichIsA("TextLabel").TextSize = 20
		x += 56
	else
		UI.icon("play", { Size = UDim2.fromOffset(34, 34), AnchorPoint = Vector2.new(0, 0.5), Position = UDim2.new(0, x, 0.5, 0), ImageColor3 = C.red, Parent = btn })
		x += 48
	end
	UI.label({ Text = (prompt.ActionText or ""):upper(), FontFace = F.head, TextSize = 19, Position = UDim2.fromOffset(x, 10), Size = UDim2.new(1, -x - 12, 0, 26), TextWrapped = false,
		TextTruncate = Enum.TextTruncate.AtEnd, Parent = btn })
	local kind = prompt.Parent:GetAttribute("CC_Interaction")
	UI.label({ Text = prompt.ObjectText .. (TRAINS[kind] and ("  ·  " .. TRAINS[kind]) or "") .. (keyText and "" or "  ·  Antippen"),
		TextSize = 15, TextColor3 = C.dim, Position = UDim2.fromOffset(x, 40), Size = UDim2.new(1, -x - 12, 0, 34), TextYAlignment = Enum.TextYAlignment.Top, Parent = btn })
	btn.Activated:Connect(function() prompt:InputHoldBegin(); task.wait(); prompt:InputHoldEnd() end)
	bb.Parent = player:WaitForChild("PlayerGui")
	shown[prompt] = bb
	local hidden
	hidden = prompt.PromptHidden:Connect(function()
		hidden:Disconnect()
		if shown[prompt] == bb then shown[prompt] = nil end
		bb:Destroy()
	end)
end)

---------------------------------------------------------------------------------------------------
-- Trainingsplan
---------------------------------------------------------------------------------------------------
local plan
local function closePlan() if plan then plan:Destroy(); plan = nil end end
local function openPlan()
	closePlan()
	plan = UI.panel({ Name = "Plan", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(620, 420), Parent = canvas })
	UI.new("UIPadding", { PaddingLeft = UDim.new(0, 26), PaddingRight = UDim.new(0, 26), PaddingTop = UDim.new(0, 20), Parent = plan })
	UI.label({ Text = "TRAININGSPLAN", FontFace = F.title, TextSize = 30, Size = UDim2.new(1, 0, 0, 36), Parent = plan })
	UI.label({ Text = ("Level %d  ·  10 Trainingspunkte ergeben +1 Wert (max. 20)"):format(attr("CC_Level", 1)), TextSize = 16, TextColor3 = C.dim,
		Position = UDim2.fromOffset(0, 38), Size = UDim2.new(1, 0, 0, 22), Parent = plan })
	for i, s in ipairs(STATS) do
		local y = 76 + (i - 1) * 64
		local v, tp = attr("CC_" .. s[1], 0), attr("CC_" .. s[1] .. "TP", 0)
		UI.label({ Text = s[2], FontFace = F.bold, TextSize = 18, Position = UDim2.fromOffset(0, y), Size = UDim2.new(0.5, 0, 0, 24), Parent = plan })
		UI.label({ Text = ("%d / 20   ·   %d/10 TP"):format(v, tp), FontFace = F.bold, TextSize = 17, TextXAlignment = Enum.TextXAlignment.Right,
			Position = UDim2.fromOffset(0, y), Size = UDim2.new(1, 0, 0, 24), Parent = plan })
		local _, fill = UI.bar({ Position = UDim2.fromOffset(0, y + 27), Size = UDim2.new(1, 0, 0, 5), Parent = plan }, C.blue)
		fill.Size = UDim2.fromScale(math.clamp((v + tp / 10) / 20, 0, 1), 1)
		UI.label({ Text = WHERE[s[1]], TextSize = 15, TextColor3 = C.dim, Position = UDim2.fromOffset(0, y + 35), Size = UDim2.new(1, 0, 0, 20), Parent = plan })
	end
	local b = UI.button({ Style = "secondary", Text = "SCHLIESSEN", Icon = "close", Size = UDim2.fromOffset(220, 52), OnClick = closePlan, Parent = plan })
	b.AnchorPoint = Vector2.new(1, 1); b.Position = UDim2.new(1, 0, 1, -18)
	UI.focus(b)
end
player:GetAttributeChangedSignal("CC_OpenPlan"):Connect(openPlan)
CAS:BindActionAtPriority("CC_PlanClose", function(_, st)
	if not plan then return Enum.ContextActionResult.Pass end
	if st == Enum.UserInputState.Begin then closePlan() end
	return Enum.ContextActionResult.Sink
end, false, 3100, Enum.KeyCode.Backspace, Enum.KeyCode.ButtonB)

---------------------------------------------------------------------------------------------------
-- Aktualisierung
---------------------------------------------------------------------------------------------------
local acc = 0
RunService.Heartbeat:Connect(function(dt)
	local char = player.Character
	local ms = game.ReplicatedStorage:FindFirstChild("CC_MatchState")
	local inMatch = (char and char:GetAttribute("CC_Opponent") ~= nil)
		or (ms and (ms:GetAttribute("Mode") or "") ~= "" and (ms:GetAttribute("RedName") == player.Name or ms:GetAttribute("BlueName") == player.Name))   -- auch Walkout
	local busy = inMatch or player:GetAttribute("CC_Minigame") ~= nil or player:GetAttribute("CC_TrainResultOpen")
	prof.Visible = not busy
	task_.Visible = not busy
	if plan and (inMatch or player:GetAttribute("CC_Minigame")) then closePlan() end
	if plan and char and char:FindFirstChild("HumanoidRootPart") and char.HumanoidRootPart.AssemblyLinearVelocity.Magnitude > 3 then closePlan() end
	acc += dt
	if acc < 0.25 or busy then return end
	acc = 0
	local lv, xp, nx = attr("CC_Level", 1), attr("CC_XP", 0), attr("CC_XPNext", 100)
	lvL.Text = "LEVEL " .. lv
	xpL.Text = ("%d / %d XP"):format(xp, nx)
	xpFill.Size = UDim2.fromScale(math.clamp(xp / nx, 0, 1), 1)
	for key, r in pairs(rows) do
		local v, tp = attr("CC_" .. key, 0), attr("CC_" .. key .. "TP", 0)
		r.val.Text = v .. " / 20"
		for k, pip in ipairs(r.pips) do pip.BackgroundColor3 = k <= tp and C.blue or C.bg3 end
	end
	updateTask()
end)
