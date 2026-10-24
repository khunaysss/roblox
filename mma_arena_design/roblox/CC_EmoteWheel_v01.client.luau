-- StarterPlayer.StarterPlayerScripts.CC_EmoteWheel
-- Emote-Rad: B gedrueckt halten oeffnet, Maus waehlt das Segment (relativ zur Radmitte), B loslassen startet,
-- Mitte oder ESC schliesst ohne Emote. Touch: Emote-Button oeffnet, Segment antippen startet, ausserhalb antippen schliesst.
-- Acht gleich grosse Segmente; das gewaehlte Segment wird als echter Kreisausschnitt rot gezeichnet (verschachtelte, gedrehte
-- CanvasGroups = zwei Halbebenen im kreisfoermig beschnittenen Rad). Figuren-Symbole aus UI-Bloecken im Stil des Spiel-Rigs.
-- Keine globalen Lighting-Aenderungen; nur ein halbtransparenter Abdunkler. Mausmodus wird beim Schliessen wiederhergestellt.
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local UIS = game:GetService("UserInputService")
local CAS = game:GetService("ContextActionService")
local RunService = game:GetService("RunService")
local Http = game:GetService("HttpService")
local player = Players.LocalPlayer
local CFG = require(RS:WaitForChild("CC_EmoteConfig"))
local remote = RS:WaitForChild("CC_EmoteRequest")

local HEAD = Font.new("rbxasset://fonts/families/RobotoCondensed.json", Enum.FontWeight.Bold)
local RED = Color3.fromRGB(205, 30, 40)
local function new(class, props, parent) local o = Instance.new(class); for k, v in pairs(props) do o[k] = v end; o.Parent = parent; return o end

local gui = new("ScreenGui", { Name = "CC_EmoteWheel", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 80, Enabled = false,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, player:WaitForChild("PlayerGui"))
local dim = new("TextButton", { Name = "Dim", Text = "", AutoButtonColor = false, Size = UDim2.fromScale(1, 1), BackgroundColor3 = Color3.new(0, 0, 0),
	BackgroundTransparency = 0.5, BorderSizePixel = 0 }, gui)
local holder = new("Frame", { Name = "Wheel", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.new(0.5, 0, 0.5, -24), BackgroundTransparency = 1 }, gui)

-- Grundscheibe (Kreis beschneidet alles Innere)
local clip = new("CanvasGroup", { Name = "Disc", Size = UDim2.fromScale(1, 1), BackgroundColor3 = Color3.fromRGB(28, 29, 33), BackgroundTransparency = 0.12, BorderSizePixel = 0 }, holder)
new("UICorner", { CornerRadius = UDim.new(1, 0) }, clip)
local rim = new("Frame", { Size = UDim2.fromScale(1, 1), BackgroundTransparency = 1, ZIndex = 6 }, holder)
new("UICorner", { CornerRadius = UDim.new(1, 0) }, rim)
new("UIStroke", { Color = Color3.fromRGB(70, 72, 80), Thickness = 2, Transparency = 0.2 }, rim)
-- Rote Auswahl: Halbebene G2 (in G1 gedreht) geschnitten mit Halbebene G3 (zusaetzlich 135 Grad) = 45-Grad-Ausschnitt
local G1 = new("CanvasGroup", { Name = "Sel", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromScale(2, 2), BackgroundTransparency = 1, Visible = false }, clip)
local G2 = new("CanvasGroup", { Size = UDim2.fromScale(1, 0.5), BackgroundTransparency = 1 }, G1)
local G3 = new("CanvasGroup", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 1), Size = UDim2.fromScale(1, 2), Rotation = 135, BackgroundTransparency = 1 }, G2)
new("Frame", { Size = UDim2.fromScale(1, 0.5), BackgroundColor3 = RED, BackgroundTransparency = 0.04, BorderSizePixel = 0 }, G3)
local selRing = new("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromScale(0.5, 0.5), BackgroundTransparency = 1 }, G3)
new("UICorner", { CornerRadius = UDim.new(1, 0) }, selRing)
new("UIStroke", { Color = Color3.fromRGB(255, 95, 100), Thickness = 3, Transparency = 0.1 }, selRing)

local INNER = 0.36           -- Innenradius relativ zum Aussenradius
local spokes, cells = {}, {}
for k = 0, 7 do
	local a = math.rad(22.5 + k * 45)
	local mid = (1 + INNER) / 2 * 0.5
	spokes[k] = new("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5 + math.sin(a) * mid, 0.5 - math.cos(a) * mid),
		Size = UDim2.new(0, 3, (1 - INNER) * 0.5, 0), Rotation = math.deg(a), BackgroundColor3 = Color3.fromRGB(14, 15, 18), BorderSizePixel = 0, ZIndex = 3 }, holder)
end
-- Mitte
local center = new("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromScale(INNER, INNER),
	BackgroundColor3 = Color3.fromRGB(15, 16, 19), BorderSizePixel = 0, ZIndex = 7 }, holder)
new("UICorner", { CornerRadius = UDim.new(1, 0) }, center)
new("UIStroke", { Color = Color3.fromRGB(58, 60, 68), Thickness = 3 }, center)
local small = new("TextLabel", { Text = "E M O T E S", FontFace = HEAD, TextScaled = true, TextColor3 = RED, BackgroundTransparency = 1,
	AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.3), Size = UDim2.fromScale(0.5, 0.08), ZIndex = 8 }, center)
new("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.38), Size = UDim2.new(0.16, 0, 0, 3), BackgroundColor3 = RED, BorderSizePixel = 0, ZIndex = 8 }, center)
local bigName = new("TextLabel", { Text = "", FontFace = HEAD, TextScaled = true, TextColor3 = Color3.new(1, 1, 1), BackgroundTransparency = 1,
	AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.55), Size = UDim2.fromScale(0.82, 0.17), ZIndex = 8 }, center)
_ = small
-- Hinweise unten
local hints = new("Frame", { AnchorPoint = Vector2.new(0.5, 0), BackgroundTransparency = 1, Size = UDim2.fromOffset(520, 34) }, gui)
local function keycap(text, x, w)
	local f = new("Frame", { Position = UDim2.fromOffset(x, 0), Size = UDim2.fromOffset(w, 34), BackgroundColor3 = Color3.fromRGB(10, 10, 12), BackgroundTransparency = 0.2 }, hints)
	new("UICorner", { CornerRadius = UDim.new(0, 6) }, f); new("UIStroke", { Color = Color3.new(1, 1, 1), Thickness = 2, Transparency = 0.1 }, f)
	new("TextLabel", { Text = text, FontFace = HEAD, TextSize = 18, TextColor3 = Color3.new(1, 1, 1), BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, f)
end
local function hintText(text, x, w) return new("TextLabel", { Text = text, FontFace = HEAD, TextSize = 18, TextColor3 = Color3.fromRGB(225, 225, 230), BackgroundTransparency = 1,
	TextXAlignment = Enum.TextXAlignment.Left, Position = UDim2.fromOffset(x, 0), Size = UDim2.fromOffset(w, 34) }, hints) end
keycap("B", 0, 40); local h1 = hintText("RELEASE B TO EMOTE", 54, 230)
new("Frame", { Position = UDim2.fromOffset(292, 8), Size = UDim2.fromOffset(2, 18), BackgroundColor3 = Color3.fromRGB(200, 200, 205), BorderSizePixel = 0 }, hints)
keycap("ESC", 312, 58); local h2 = hintText("CANCEL", 384, 130)
local toast = new("TextLabel", { Text = "", FontFace = HEAD, TextSize = 18, TextColor3 = Color3.fromRGB(235, 235, 240), BackgroundColor3 = Color3.fromRGB(20, 21, 25),
	BackgroundTransparency = 0.15, AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, -150), Size = UDim2.fromOffset(340, 34), Visible = false }, player.PlayerGui:WaitForChild("CC_EmoteWheel"))
new("UICorner", { CornerRadius = UDim.new(0, 6) }, toast)
toast.Parent = new("ScreenGui", { Name = "CC_EmoteToast", ResetOnSpawn = false, DisplayOrder = 81 }, player.PlayerGui)

-- Figuren-Symbole (Koordinaten 0..100, y nach unten; Kopf, Rumpf, Arme/Beine aus je zwei Gliedern)
local POSE = {
	cry_about_it = { L = { { 38, 34 }, { 30, 47 }, { 44, 21 } }, R = { { 62, 34 }, { 70, 47 }, { 56, 21 } }, glyph = "' '", gx = 50, gy = 4 },
	keep_talking = { L = { { 38, 34 }, { 27, 46 }, { 40, 58 } }, R = { { 62, 34 }, { 75, 38 }, { 72, 17 } }, glyph = "≈", gx = 86, gy = 12 },
	go_to_sleep = { L = { { 38, 34 }, { 46, 44 }, { 60, 25 } }, R = { { 62, 34 }, { 72, 40 }, { 64, 22 } }, head = { 57, 20 }, glyph = "zZ", gx = 84, gy = 6 },
	take_the_l = { L = { { 38, 34 }, { 22, 34 }, { 22, 14 } }, R = { { 62, 34 }, { 72, 28 }, { 55, 12 } }, LL = { { 44, 62 }, { 36, 74 }, { 42, 88 } } },
	champ_walk = { L = { { 38, 34 }, { 27, 44 }, { 19, 55 } }, R = { { 62, 34 }, { 73, 45 }, { 81, 53 } }, LL = { { 44, 62 }, { 37, 75 }, { 30, 89 } }, RL = { { 56, 62 }, { 61, 76 }, { 66, 90 } } },
	stone_face = { L = { { 38, 34 }, { 37, 48 }, { 36, 62 } }, R = { { 62, 34 }, { 63, 48 }, { 64, 62 } } },
	bow_shot = { L = { { 38, 34 }, { 24, 33 }, { 10, 32 } }, R = { { 62, 34 }, { 58, 42 }, { 47, 27 } }, glyph = "(", gx = 6, gy = 32, gsize = 46 },
	dust_off = { L = { { 38, 34 }, { 37, 48 }, { 36, 62 } }, R = { { 62, 34 }, { 60, 46 }, { 37, 31 } }, glyph = "~", gx = 26, gy = 20 },
}
local function limb(parent, p0, p1, w)
	local dx, dy = p1[1] - p0[1], p1[2] - p0[2]
	local l = math.sqrt(dx * dx + dy * dy)
	local f = new("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale((p0[1] + p1[1]) / 200, (p0[2] + p1[2]) / 200),
		Size = UDim2.fromScale((l + w * 0.6) / 100, w / 100), Rotation = math.deg(math.atan2(dy, dx)), BackgroundColor3 = Color3.new(1, 1, 1), BorderSizePixel = 0 }, parent)
	new("UICorner", { CornerRadius = UDim.new(0.3, 0) }, f)
end
local function figure(parent, id)
	local P = POSE[id] or POSE.stone_face
	local box = new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, parent)
	new("UIAspectRatioConstraint", {}, box)
	local hx, hy = (P.head or { 50, 20 })[1], (P.head or { 50, 20 })[2]
	local head = new("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(hx / 100, hy / 100), Size = UDim2.fromScale(0.2, 0.2), BackgroundColor3 = Color3.new(1, 1, 1), BorderSizePixel = 0 }, box)
	new("UICorner", { CornerRadius = UDim.new(0.25, 0) }, head)
	local torso = new("Frame", { AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromScale(0.5, 0.3), Size = UDim2.fromScale(0.26, 0.33), BackgroundColor3 = Color3.new(1, 1, 1), BorderSizePixel = 0 }, box)
	new("UICorner", { CornerRadius = UDim.new(0.15, 0) }, torso)
	for _, arm in ipairs({ P.L, P.R }) do limb(box, arm[1], arm[2], 10); limb(box, arm[2], arm[3], 10) end
	local LL = P.LL or { { 44, 62 }, { 43, 76 }, { 42, 90 } }
	local RL = P.RL or { { 56, 62 }, { 57, 76 }, { 58, 90 } }
	for _, leg in ipairs({ LL, RL }) do limb(box, leg[1], leg[2], 12); limb(box, leg[2], leg[3], 12) end
	if P.glyph then
		new("TextLabel", { Text = P.glyph, FontFace = HEAD, TextScaled = true, TextColor3 = Color3.new(1, 1, 1), BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.fromScale(P.gx / 100, P.gy / 100), Size = UDim2.fromScale((P.gsize or 22) / 100, (P.gsize or 22) / 100) }, box)
	end
	return box
end

local slots = {}
local function rebuild()
	for _, c in pairs(cells) do c:Destroy() end
	table.clear(cells)
	local ok, t = pcall(function() return Http:JSONDecode(player:GetAttribute("CC_EmoteSlots") or "") end)
	slots = ok and type(t) == "table" and t or CFG.DEFAULT_SLOTS
	for i = 1, CFG.SLOT_COUNT do
		local def = CFG.BY_ID[slots[i] or ""]
		local a = math.rad((i - 1) * 45)
		local rr = (1 + INNER) / 2 * 0.5
		local cell = new("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5 + math.sin(a) * rr, 0.5 - math.cos(a) * rr),
			Size = UDim2.fromScale(0.24, 0.24), BackgroundTransparency = 1, ZIndex = 5 }, holder)
		cells[i] = cell
		if def then
			local icon = new("Frame", { AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromScale(0.5, 0), Size = UDim2.fromScale(0.62, 0.62), BackgroundTransparency = 1 }, cell)
			figure(icon, def.id)
			new("TextLabel", { Text = def.name, FontFace = HEAD, TextScaled = true, TextColor3 = Color3.new(1, 1, 1), BackgroundTransparency = 1,
				AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromScale(0.5, 0.68), Size = UDim2.fromScale(1.1, 0.2) }, cell)
		end
	end
end
rebuild()
player:GetAttributeChangedSignal("CC_EmoteSlots"):Connect(rebuild)

local function layout()
	local vp = workspace.CurrentCamera.ViewportSize
	local d = math.clamp(math.min(vp.X * 0.9, (vp.Y - 120) * 0.92), 240, 640)
	holder.Size = UDim2.fromOffset(d, d)
	local hs = math.clamp(d / 640, 0.62, 1)
	hints.Size = UDim2.fromOffset(520, 34)
	hints.Position = UDim2.new(0.5, -260 * hs, 0.5, d / 2 - 4)
	hints.AnchorPoint = Vector2.new(0, 0)
	local sc = hints:FindFirstChildOfClass("UIScale") or new("UIScale", {}, hints)
	sc.Scale = hs
end
workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(layout)
layout()

-- Auswahl
local selected, isOpen, touchMode = nil, false, false
local savedBehavior, savedIcon
local function setSelected(i)
	if selected == i then return end
	selected = i
	for k, s in pairs(spokes) do s.BackgroundColor3 = Color3.fromRGB(14, 15, 18) end
	if i then
		G1.Visible = true
		G1.Rotation = (i - 1) * 45 - 67.5
		local def = CFG.BY_ID[slots[i] or ""]
		bigName.Text = def and def.name or ""
	else
		G1.Visible = false
		bigName.Text = "EMOTES"
	end
end
local function indexAt(pos)
	local c = holder.AbsolutePosition + holder.AbsoluteSize / 2
	local d = pos - c
	local r = holder.AbsoluteSize.X / 2
	if d.Magnitude < r * INNER or d.Magnitude > r * 1.15 then return nil end
	local deg = (math.deg(math.atan2(d.X, -d.Y)) + 360) % 360
	local i = math.floor((deg + 22.5) / 45) % 8 + 1
	return CFG.BY_ID[slots[i] or ""] and i or nil
end
local function canOpen()
	if UIS:GetFocusedTextBox() then return false end
	if player:GetAttribute("CC_UIBlock") or player:GetAttribute("CC_Minigame") then return false end
	local c = player.Character
	local h = c and c:FindFirstChildOfClass("Humanoid")
	return h ~= nil and h.Health > 0
end
local function close()
	if not isOpen then return end
	isOpen = false
	gui.Enabled = false
	RunService:UnbindFromRenderStep("CC_EmoteWheelMouse")
	CAS:UnbindAction("CC_EmoteCancel")
	if savedBehavior then UIS.MouseBehavior = savedBehavior end
	if savedIcon ~= nil then UIS.MouseIconEnabled = savedIcon end
	savedBehavior, savedIcon = nil, nil
	setSelected(nil)
end
local function confirm()
	local i = selected
	close()
	if i and slots[i] then remote:FireServer("play", slots[i]) end
end
local function open(viaTouch)
	if isOpen or not canOpen() then return end
	isOpen, touchMode = true, viaTouch == true
	layout(); setSelected(nil)
	h1.Text = touchMode and "TAP AN EMOTE" or "RELEASE B TO EMOTE"
	h2.Text = touchMode and "TAP OUTSIDE" or "CANCEL"
	gui.Enabled = true
	savedBehavior, savedIcon = UIS.MouseBehavior, UIS.MouseIconEnabled
	RunService:BindToRenderStep("CC_EmoteWheelMouse", Enum.RenderPriority.Last.Value + 5, function()
		if not isOpen then return end
		UIS.MouseBehavior = Enum.MouseBehavior.Default; UIS.MouseIconEnabled = true
		if not touchMode then setSelected(indexAt(UIS:GetMouseLocation())) end
		if not canOpen() then close() end
	end)
	CAS:BindActionAtPriority("CC_EmoteCancel", function(_, state)
		if state == Enum.UserInputState.Begin then close() end
		return Enum.ContextActionResult.Sink
	end, false, 3500, Enum.KeyCode.Escape, Enum.KeyCode.ButtonB)
end

CAS:BindActionAtPriority("CC_EmoteWheel", function(_, state, input)
	local touch = input and input.UserInputType == Enum.UserInputType.Touch
	if touch then
		if state == Enum.UserInputState.Begin then if isOpen then close() else open(true) end end
		return Enum.ContextActionResult.Sink
	end
	if state == Enum.UserInputState.Begin then
		if not canOpen() then return Enum.ContextActionResult.Pass end
		open(false)
		return Enum.ContextActionResult.Sink
	elseif state == Enum.UserInputState.End then
		if isOpen and not touchMode then confirm(); return Enum.ContextActionResult.Sink end
	end
	return Enum.ContextActionResult.Pass
end, true, 2500, Enum.KeyCode.B)
CAS:SetTitle("CC_EmoteWheel", "Emote")
-- Fallback: Loslassen von B kommt je nach Eingabestapel als Cancel statt End an
UIS.InputEnded:Connect(function(input)
	if input.KeyCode == Enum.KeyCode.B and isOpen and not touchMode then confirm() end
end)

-- Touch: Segment antippen startet, ausserhalb schliesst
dim.InputBegan:Connect(function(input)
	if not (isOpen and touchMode) then return end
	if input.UserInputType ~= Enum.UserInputType.Touch and input.UserInputType ~= Enum.UserInputType.MouseButton1 then return end
	local i = indexAt(Vector2.new(input.Position.X, input.Position.Y))
	if i then setSelected(i); confirm() else close() end
end)

-- Eigene Bewegung/Angriff beendet das Emote sofort (Server prueft zusaetzlich)
UIS.InputBegan:Connect(function(input, processed)
	local c = player.Character
	if not (c and c:GetAttribute("CC_Emote")) or isOpen then return end
	local k = input.KeyCode
	if k == Enum.KeyCode.W or k == Enum.KeyCode.A or k == Enum.KeyCode.S or k == Enum.KeyCode.D or k == Enum.KeyCode.Space
		or input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.MouseButton2 then
		remote:FireServer("stop")
	end
end)

-- Ablehnungen kurz anzeigen
local REASON = { cooldown = "Emote on cooldown", match_state = "Not available right now", action = "Finish your action first", not_uploaded = "Emote not available yet",
	air = "Land first", grappling = "Not while grappling", CC_Block = "Not while blocking" }
player:GetAttributeChangedSignal("CC_EmoteDenied"):Connect(function()
	local r = (player:GetAttribute("CC_EmoteDenied") or ""):match("^([^|]+)")
	if not r then return end
	toast.Text = REASON[r] or "Not available right now"; toast.Visible = true
	task.delay(1.6, function() toast.Visible = false end)
end)
player.CharacterRemoving:Connect(close)
