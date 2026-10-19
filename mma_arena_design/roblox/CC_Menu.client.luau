-- StarterGui.CC_MenuGui.Menu (LocalScript in einer ScreenGui)
-- Lobby-Menue: TRAINING (gegen den Trainingsgegner) oder VS PLAYERS (Warteschlange, die ersten zwei kaempfen).
-- Sichtbar, solange der eigene Charakter in keinem Kampf ist (kein Attribut CC_Opponent).
-- Server: ReplicatedStorage.CC_Menu ("training" | "pvp" | "cancel"); Stand aus ReplicatedStorage.CC_MatchState und Player.CC_Queue.
local player = game.Players.LocalPlayer
local RS = game.ReplicatedStorage
local menuEvent = RS:WaitForChild("CC_Menu")
local state = RS:WaitForChild("CC_MatchState")
local gui = script.Parent
gui.ResetOnSpawn = false

local panel = Instance.new("Frame")
panel.AnchorPoint = Vector2.new(0, 0.5); panel.Position = UDim2.new(0, 24, 0.5, 0); panel.Size = UDim2.fromOffset(320, 575)
panel.BackgroundColor3 = Color3.fromRGB(18, 18, 22); panel.BackgroundTransparency = 0.12; panel.BorderSizePixel = 0; panel.Parent = gui
Instance.new("UICorner", panel).CornerRadius = UDim.new(0, 10)
local pad = Instance.new("UIPadding", panel)
pad.PaddingLeft = UDim.new(0, 18); pad.PaddingRight = UDim.new(0, 18); pad.PaddingTop = UDim.new(0, 16); pad.PaddingBottom = UDim.new(0, 16)
local list = Instance.new("UIListLayout", panel); list.Padding = UDim.new(0, 10); list.SortOrder = Enum.SortOrder.LayoutOrder

local function label(text, size, font, color, order, h)
	local l = Instance.new("TextLabel")
	l.BackgroundTransparency = 1; l.Size = UDim2.new(1, 0, 0, h or size + 8); l.Font = font; l.TextSize = size
	l.TextColor3 = color; l.Text = text; l.TextXAlignment = Enum.TextXAlignment.Left; l.TextWrapped = true; l.LayoutOrder = order
	l.Parent = panel; return l
end
local function button(text, color, order)
	local b = Instance.new("TextButton")
	b.Size = UDim2.new(1, 0, 0, 52); b.BackgroundColor3 = color; b.BorderSizePixel = 0; b.AutoButtonColor = true
	b.Font = Enum.Font.GothamBlack; b.TextSize = 22; b.TextColor3 = Color3.new(1, 1, 1); b.Text = text; b.LayoutOrder = order
	Instance.new("UICorner", b).CornerRadius = UDim.new(0, 8)
	b.Parent = panel; return b
end
label("CAGE CHAMPIONS", 30, Enum.Font.GothamBlack, Color3.fromRGB(255, 220, 60), 1, 36)
local trainingB = button("TRAINING", Color3.fromRGB(40, 90, 200), 2)
local pvpB = button("VS PLAYERS", Color3.fromRGB(200, 40, 50), 3)
local cancelB = button("CANCEL", Color3.fromRGB(70, 70, 78), 4)
local fighterB = button("FIGHTER", Color3.fromRGB(60, 140, 90), 4)
local status = label("", 16, Enum.Font.GothamBold, Color3.fromRGB(220, 220, 225), 5, 44)
-- Profil (CC_Profile): Level, XP-Balken, Werte mit Trainingspunkten, Bilanz
local levelL = label("", 18, Enum.Font.GothamBlack, Color3.fromRGB(255, 220, 60), 6, 22)
local function bar(order, color)
	local f = Instance.new("Frame"); f.Size = UDim2.new(1, 0, 0, 8); f.BackgroundColor3 = Color3.fromRGB(40, 40, 46); f.BorderSizePixel = 0; f.LayoutOrder = order; f.Parent = panel
	local fill = Instance.new("Frame"); fill.Size = UDim2.fromScale(0, 1); fill.BackgroundColor3 = color; fill.BorderSizePixel = 0; fill.Parent = f
	return fill
end
local xpFill = bar(7, Color3.fromRGB(255, 200, 40))
local STAT_NAMES = { { "Power", "Power" }, { "Cardio", "Cardio" }, { "Wrestling", "Wrestling" }, { "Grappling", "Grappling" } }
local statRows = {}
for i, s_ in ipairs(STAT_NAMES) do
	local l = label("", 14, Enum.Font.GothamBold, Color3.fromRGB(220, 220, 225), 7 + i * 2, 16)
	statRows[s_[1]] = { l, bar(8 + i * 2, Color3.fromRGB(80, 150, 255)), s_[2] }
end
local recordL = label("", 14, Enum.Font.Gotham, Color3.fromRGB(190, 190, 198), 20, 18)

-- Kaempfer-Anpassung (CC_Customize): Frisur, Bart, Gesicht, Haut, Haarfarbe; jede Aenderung wirkt sofort am eigenen Kaempfer
local HS = game:GetService("HttpService")
local lookEvent = RS:WaitForChild("CC_Look", 10)
local lookOpts = RS:WaitForChild("CC_LookOptions", 10)
local NAMES = { Hair_QuiffV03 = "Tolle", Hair_Buzzcut = "Buzzcut", Hair_SidePart = "Seitenscheitel", Hair_ShortCurls = "Locken",
	none = "no beard", Beard_Short = "kurz", Beard_Full = "Vollbart", Face_Focused = "fokussiert", Face_Neutral = "neutral", Face_Friendly = "freundlich" }
local SKIN_N = { "light", "medium", "tan", "dark" }
local HAIRC_N = { "schwarz", "dunkelbraun", "braun", "blond", "rot", "grau" }
local custom = Instance.new("Frame")
custom.AnchorPoint = Vector2.new(0, 0.5); custom.Position = UDim2.new(0, 360, 0.5, 0); custom.Size = UDim2.fromOffset(330, 330)
custom.BackgroundColor3 = Color3.fromRGB(18, 18, 22); custom.BackgroundTransparency = 0.12; custom.BorderSizePixel = 0; custom.Visible = false; custom.Parent = gui
Instance.new("UICorner", custom).CornerRadius = UDim.new(0, 10)
local cpad = Instance.new("UIPadding", custom); cpad.PaddingLeft = UDim.new(0, 16); cpad.PaddingRight = UDim.new(0, 16); cpad.PaddingTop = UDim.new(0, 14)
local clist = Instance.new("UIListLayout", custom); clist.Padding = UDim.new(0, 8); clist.SortOrder = Enum.SortOrder.LayoutOrder
local ct = Instance.new("TextLabel"); ct.BackgroundTransparency = 1; ct.Size = UDim2.new(1, 0, 0, 30); ct.Font = Enum.Font.GothamBlack; ct.TextSize = 22
ct.TextColor3 = Color3.fromRGB(255, 220, 60); ct.Text = "YOUR FIGHTER"; ct.TextXAlignment = Enum.TextXAlignment.Left; ct.LayoutOrder = 0; ct.Parent = custom
local function list_(attr) local t = {}; for x in string.gmatch(lookOpts and lookOpts:GetAttribute(attr) or "", "[^,]+") do table.insert(t, x) end; return t end
local function currentLook()
	local ok, t = pcall(function() return HS:JSONDecode(player:GetAttribute("CC_Look") or "") end)
	return ok and type(t) == "table" and t or { hair = "Hair_QuiffV03", beard = "none", face = "Face_Focused", skin = 2, hairColor = 1 }
end
local ROWS = {
	{ "Frisur", "hair", function() return list_("Hair") end },
	{ "Bart", "beard", function() return list_("Beard") end },
	{ "Gesicht", "face", function() return list_("Face") end },
	{ "Haut", "skin", function() return SKIN_N end, true },
	{ "Haarfarbe", "hairColor", function() return HAIRC_N end, true },
}
local valueLabels = {}
for i, r in ipairs(ROWS) do
	local row = Instance.new("Frame"); row.BackgroundTransparency = 1; row.Size = UDim2.new(1, 0, 0, 36); row.LayoutOrder = i; row.Parent = custom
	local name = Instance.new("TextLabel"); name.BackgroundTransparency = 1; name.Size = UDim2.new(0.34, 0, 1, 0); name.Font = Enum.Font.GothamBold; name.TextSize = 16
	name.TextColor3 = Color3.fromRGB(220, 220, 225); name.Text = r[1]; name.TextXAlignment = Enum.TextXAlignment.Left; name.Parent = row
	local function arrow(txt, x)
		local b = Instance.new("TextButton"); b.Size = UDim2.fromOffset(34, 32); b.Position = UDim2.new(x, x > 0.5 and -34 or 0, 0, 2)
		b.BackgroundColor3 = Color3.fromRGB(50, 50, 58); b.Font = Enum.Font.GothamBlack; b.TextSize = 18; b.TextColor3 = Color3.new(1, 1, 1); b.Text = txt
		Instance.new("UICorner", b).CornerRadius = UDim.new(0, 6); b.Parent = row; return b
	end
	local left, right = arrow("<", 0.36), arrow(">", 1)
	local val = Instance.new("TextLabel"); val.BackgroundTransparency = 1; val.Position = UDim2.new(0.36, 38, 0, 0); val.Size = UDim2.new(0.64, -76, 1, 0)
	val.Font = Enum.Font.Gotham; val.TextSize = 15; val.TextColor3 = Color3.new(1, 1, 1); val.Parent = row
	valueLabels[r[2]] = { val, r }
	local function step(d)
		local look = currentLook(); local opts = r[3]()
		if #opts == 0 then return end
		if r[4] then look[r[2]] = ((look[r[2]] or 1) - 1 + d) % #opts + 1
		else
			local idx = 1; for k, v in ipairs(opts) do if v == look[r[2]] then idx = k end end
			look[r[2]] = opts[(idx - 1 + d) % #opts + 1]
		end
		if lookEvent then lookEvent:FireServer(look) end
	end
	left.Activated:Connect(function() step(-1) end); right.Activated:Connect(function() step(1) end)
end
local done = Instance.new("TextButton"); done.Size = UDim2.new(1, 0, 0, 40); done.BackgroundColor3 = Color3.fromRGB(60, 140, 90); done.Font = Enum.Font.GothamBlack
done.TextSize = 18; done.TextColor3 = Color3.new(1, 1, 1); done.Text = "DONE"; done.LayoutOrder = 10; done.Parent = custom
Instance.new("UICorner", done).CornerRadius = UDim.new(0, 8)
done.Activated:Connect(function() custom.Visible = false end)
fighterB.Activated:Connect(function() custom.Visible = not custom.Visible end)
-- Umkleide im Gym (Interaktionspunkt) oeffnet ebenfalls die Anpassung
player:GetAttributeChangedSignal("CC_OpenCustomize"):Connect(function() custom.Visible = true end)
-- Hauptmenue (CC_MainMenu) schliesst die Anpassung beim Verlassen der Seite MEIN KAEMPFER
player:GetAttributeChangedSignal("CC_CloseCustomize"):Connect(function() custom.Visible = false end)

trainingB.Activated:Connect(function() menuEvent:FireServer("training") end)
pvpB.Activated:Connect(function() menuEvent:FireServer("pvp") end)
cancelB.Activated:Connect(function() menuEvent:FireServer("cancel") end)

game:GetService("RunService").RenderStepped:Connect(function()
	local char = player.Character
	local inMatch = (char and char:GetAttribute("CC_Opponent") ~= nil) or player:GetAttribute("CC_Minigame") ~= nil   -- auch waehrend Gym-Training ausblenden
	panel.Visible = false   -- ersetzt durch das Hauptmenue (CC_MainMenu); Anpassungsfenster bleibt bis Schritt 2
	if inMatch then custom.Visible = false; return end
	local look = currentLook()
	for key, e in pairs(valueLabels) do
		local v = look[key]
		e[1].Text = e[2][4] and ((e[2][3]())[v] or tostring(v)) or (NAMES[v] or tostring(v))
	end
	local q = player:GetAttribute("CC_Queue")
	local mode, st = state:GetAttribute("Mode") or "", state:GetAttribute("State") or "idle"
	local busy = mode ~= ""
	trainingB.Visible = q == nil; pvpB.Visible = q == nil; cancelB.Visible = q ~= nil; fighterB.Visible = q == nil
	local lines = {}
	if busy then
		table.insert(lines, ("Fight in progress: %s vs %s"):format(state:GetAttribute("RedName") or "?", state:GetAttribute("BlueName") or "?"))
	end
	if q == "pvp" then
		local n = state:GetAttribute("QueuePvp") or 0
		table.insert(lines, n >= 2 and "Opponent found – you are up next." or "Waiting for an opponent … (" .. n .. "/2)")
	elseif q == "training" then
		table.insert(lines, busy and "Training starts after this fight." or "Training starting …")
	elseif not busy then
		table.insert(lines, "Choose a mode.")
	end
	status.Text = table.concat(lines, "\n")
	local lv, xp, nx = player:GetAttribute("CC_Level") or 1, player:GetAttribute("CC_XP") or 0, player:GetAttribute("CC_XPNext") or 100
	levelL.Text = ("LEVEL %d   ·   %d / %d XP"):format(lv, xp, nx)
	xpFill.Size = UDim2.fromScale(math.clamp(xp / nx, 0, 1), 1)
	for key, row in pairs(statRows) do
		local v, tp = player:GetAttribute("CC_" .. key) or 0, player:GetAttribute("CC_" .. key .. "TP") or 0
		row[1].Text = ("%s  %d / 20"):format(row[3], v)
		row[2].Size = UDim2.fromScale(math.clamp((v + tp / 10) / 20, 0, 1), 1)
	end
	recordL.Text = ("Record %d-%d   ·   KO %d   ·   Sub %d%s"):format(player:GetAttribute("CC_Wins") or 0, player:GetAttribute("CC_Losses") or 0,
		player:GetAttribute("CC_KOs") or 0, player:GetAttribute("CC_Subs") or 0, player:GetAttribute("CC_ProfileSaved") and "" or "  (nicht gespeichert)")
end)
