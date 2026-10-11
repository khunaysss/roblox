-- StarterPlayer.StarterPlayerScripts.CC_Minigame
-- Trainings-Minispiele im Gym (Aufgaben vom Server, Attribut CC_Minigame als JSON am Spieler; Rueckmeldung ueber CC_Train):
--   "seq":    Tastenfolge (Q E R F) der Reihe nach druecken, Zeitlimit; falsche Taste = Fehler (Kombo bricht)
--   "rhythm": Taste druecken, wenn der Ring den Kreis erreicht (gut +-0,18 s, perfekt +-0,08 s); Q/E abwechselnd bei Curls
-- Controller: Q=X, E=Y, R=B, F=A, Leertaste=A. Touch: auf die angezeigte Taste tippen.
-- Kamera waehrend des Trainings: von vorn (Bank: von der Fussseite schraeg oben, Sack: seitlich).
-- Oberflaeche (UI-Ueberarbeitung Schritt 2, ReplicatedStorage.CC_UI): Aufgabenkarte mit Anleitung, Countdown,
-- Fortschritt, Timing-Rueckmeldung und Ergebnis mit den echten Belohnungen vom Server (Attribut CC_TrainResult).
-- Ergebnis: NOCHMAL (CC_Train "again" = gleiche Station) oder WEITER.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local CAS = game:GetService("ContextActionService")
local HS = game:GetService("HttpService")
local PPS = game:GetService("ProximityPromptService")
local TweenService = game:GetService("TweenService")
local UIS = game:GetService("UserInputService")
local RS = game:GetService("ReplicatedStorage")
local player = Players.LocalPlayer
local trainEv = RS:WaitForChild("CC_Train")
local UI = require(RS:WaitForChild("CC_UI"))
local C, F = UI.C, UI.F
local cam = workspace.CurrentCamera

local GOOD, PERFECT, LATE = 0.18, 0.08, 0.25
local PAD = { [Enum.KeyCode.ButtonX] = "Q", [Enum.KeyCode.ButtonY] = "E", [Enum.KeyCode.ButtonB] = "R", [Enum.KeyCode.ButtonA] = "F" }
local KEYMAP = { [Enum.KeyCode.Q] = "Q", [Enum.KeyCode.E] = "E", [Enum.KeyCode.R] = "R", [Enum.KeyCode.F] = "F", [Enum.KeyCode.Space] = "Space" }
local PAD_LABEL = { Q = "X", E = "Y", R = "B", F = "A", Space = "A" }
local STAT_DE = { Power = "SCHLAGKRAFT", Cardio = "KONDITION" }

-- ---------- Oberflaeche ----------
local gui = Instance.new("ScreenGui"); gui.Name = "CC_MinigameGui"; gui.ResetOnSpawn = false; gui.Enabled = false; gui.IgnoreGuiInset = true
gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling; gui.DisplayOrder = 15; gui.Parent = player:WaitForChild("PlayerGui")
local canvas = UI.new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Parent = gui })
UI.autoscale(canvas, 720)

-- Aufgabenkarte oben
local card = UI.panel({ AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0, 24), Size = UDim2.fromOffset(640, 128), Parent = canvas })
UI.new("UIPadding", { PaddingLeft = UDim.new(0, 22), PaddingRight = UDim.new(0, 22), PaddingTop = UDim.new(0, 14), Parent = card })
local title = UI.label({ Text = "", FontFace = F.title, TextSize = 30, Size = UDim2.new(1, 0, 0, 36), TextWrapped = false, Parent = card })
local statTag = UI.tag({ Text = "", Color = C.blueDark, AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, 0, 0, 8), Parent = card })
local howRow = UI.new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 42), Size = UDim2.new(1, 0, 0, 32), Parent = card })
UI.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, VerticalAlignment = Enum.VerticalAlignment.Center, Padding = UDim.new(0, 8), SortOrder = Enum.SortOrder.LayoutOrder, Parent = howRow })
local progL = UI.label({ Text = "", FontFace = F.bold, TextSize = 16, TextColor3 = C.dim, Position = UDim2.fromOffset(0, 80), Size = UDim2.new(1, 0, 0, 20), Parent = card })
local _, progFill = UI.bar({ Position = UDim2.fromOffset(0, 104), Size = UDim2.new(1, 0, 0, 6), Parent = card }, C.green)

-- Countdown und Rueckmeldung
local countL = UI.label({ Text = "", FontFace = F.title, TextSize = 96, TextXAlignment = Enum.TextXAlignment.Center, AnchorPoint = Vector2.new(0.5, 0.5),
	Position = UDim2.fromScale(0.5, 0.42), Size = UDim2.fromOffset(400, 120), TextStrokeTransparency = 0.5, Parent = canvas })
local feedback = UI.label({ Text = "", FontFace = F.title, TextSize = 44, TextXAlignment = Enum.TextXAlignment.Center, AnchorPoint = Vector2.new(0.5, 0.5),
	Position = UDim2.fromScale(0.5, 0.6), Size = UDim2.fromOffset(500, 60), TextStrokeTransparency = 0.4, Parent = canvas })
local fbScale = UI.new("UIScale", { Parent = feedback })

-- Rhythmus: Ziel-Kreis + schrumpfender Ring
local ring = UI.new("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.8), BackgroundTransparency = 1, Parent = canvas })
local ringStroke = UI.new("UIStroke", { Thickness = 5, Color = C.text, Parent = ring })
UI.new("UICorner", { CornerRadius = UDim.new(1, 0), Parent = ring })
local target = UI.new("TextButton", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.8), Size = UDim2.fromOffset(92, 92),
	BackgroundColor3 = C.bg1, BackgroundTransparency = 0.02, FontFace = F.title, TextSize = 30, TextColor3 = C.text, AutoButtonColor = false, Text = "", Parent = canvas })
UI.new("UICorner", { CornerRadius = UDim.new(1, 0), Parent = target })
local tStroke = UI.new("UIStroke", { Thickness = 4, Color = C.red, ApplyStrokeMode = Enum.ApplyStrokeMode.Border, Parent = target })
-- Tastenfolge: Reihe von Kaestchen + Zeitbalken
local row = UI.new("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.8), Size = UDim2.fromOffset(700, 74), BackgroundTransparency = 1, Parent = canvas })
UI.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, HorizontalAlignment = Enum.HorizontalAlignment.Center, VerticalAlignment = Enum.VerticalAlignment.Center,
	Padding = UDim.new(0, 8), SortOrder = Enum.SortOrder.LayoutOrder, Parent = row })
local timeBar, timeFill = UI.bar({ AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.new(0.5, 0, 0.8, 54), Size = UDim2.fromOffset(560, 8), Parent = canvas }, C.gold)

-- Ergebnis (eigene Ebene, bleibt nach dem Minispiel sichtbar)
local resGui = Instance.new("ScreenGui"); resGui.Name = "CC_TrainResultGui"; resGui.ResetOnSpawn = false; resGui.IgnoreGuiInset = true
resGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling; resGui.DisplayOrder = 16; resGui.Enabled = false; resGui.Parent = player.PlayerGui
local resCanvas = UI.new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Parent = resGui })
UI.autoscale(resCanvas, 720)
local res = UI.panel({ AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.52), Size = UDim2.fromOffset(580, 330), Parent = resCanvas })
UI.new("UIPadding", { PaddingLeft = UDim.new(0, 28), PaddingRight = UDim.new(0, 28), PaddingTop = UDim.new(0, 20), Parent = res })
UI.label({ Text = "TRAINING BEENDET", FontFace = F.bold, TextSize = 15, TextColor3 = C.red, Size = UDim2.new(1, 0, 0, 20), Parent = res })
local resTitle = UI.label({ Text = "", FontFace = F.title, TextSize = 40, Position = UDim2.fromOffset(0, 22), Size = UDim2.new(1, 0, 0, 48), TextWrapped = false, Parent = res })
local resLine = UI.label({ Text = "", TextSize = 17, TextColor3 = C.dim, Position = UDim2.fromOffset(0, 72), Size = UDim2.new(1, 0, 0, 24), Parent = res })
local rewardRow = UI.new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 108), Size = UDim2.new(1, 0, 0, 44), Parent = res })
UI.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 10), VerticalAlignment = Enum.VerticalAlignment.Center, SortOrder = Enum.SortOrder.LayoutOrder, Parent = rewardRow })
local statL = UI.label({ Text = "", FontFace = F.bold, TextSize = 16, Position = UDim2.fromOffset(0, 164), Size = UDim2.new(1, 0, 0, 22), Parent = res })
local resPips = {}
for k = 1, 10 do resPips[k] = UI.new("Frame", { BackgroundColor3 = C.bg3, BorderSizePixel = 0, Position = UDim2.new((k - 1) / 10, 1, 0, 192), Size = UDim2.new(0.1, -4, 0, 8), Parent = res }) end
local btnRow = UI.new("Frame", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0, 1), Position = UDim2.new(0, 0, 1, -20), Size = UDim2.new(1, 0, 0, 56), Parent = res })
UI.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, HorizontalAlignment = Enum.HorizontalAlignment.Right, Padding = UDim.new(0, 12), SortOrder = Enum.SortOrder.LayoutOrder, Parent = btnRow })
local resultUntil = 0
local function closeResult()
	resGui.Enabled = false
	player:SetAttribute("CC_TrainResultOpen", nil)
	game:GetService("GuiService").SelectedObject = nil
end
UI.button({ Style = "secondary", Text = "NOCHMAL", Icon = "rotate", Size = UDim2.fromOffset(220, 56), LayoutOrder = 1, Parent = btnRow,
	OnClick = function() closeResult(); trainEv:FireServer("again") end })
local bNext = UI.button({ Style = "primary", Text = "WEITER", Icon = "next", Size = UDim2.fromOffset(220, 56), LayoutOrder = 2, Parent = btnRow, OnClick = closeResult })

-- ---------- Zustand ----------
local game_ = nil          -- aktuelle Aufgabe (Tabelle aus JSON + Laufzeitdaten)
local boxes = {}
local feedbackUntil = 0
local function isPad() return UIS:GetLastInputType().Name:find("Gamepad") ~= nil end
local function label(key)
	if isPad() then return PAD_LABEL[key] or key end
	return key == "Space" and "LEER" or key
end
local function showFeedback(text, color)
	feedback.Text = text; feedback.TextColor3 = color; feedbackUntil = os.clock() + 0.55
	fbScale.Scale = 1.35
	TweenService:Create(fbScale, TweenInfo.new(0.18, Enum.EasingStyle.Back), { Scale = 1 }):Play()
end
local function report(what, i)
	if not game_ or game_.done[i] then return end
	game_.done[i] = what
	if what == "hit" then game_.hits += 1 else game_.misses += 1 end
	trainEv:FireServer(what, game_.id, i)
end

local function press(key)
	local g = game_; if not g then return end
	local now = workspace:GetServerTimeNow()
	if now < g.start - 0.2 then return end
	if g.game == "seq" then
		local i = g.cur; if i > g.n then return end
		if key == g.keys[i] then
			report("hit", i); showFeedback("TREFFER", C.green)
		else
			report("miss", i); showFeedback("FALSCHE TASTE", C.red)
		end
		g.cur = i + 1
	else
		local best, bestD
		for i = 1, g.n do
			if not g.done[i] then
				local due = g.start + (i - 1) * g.interval
				local d = math.abs(now - due)
				if d <= LATE + 0.15 and (not bestD or d < bestD) then best, bestD = i, d end
			end
		end
		if not best then return end
		if key ~= g.keys[best] then report("miss", best); showFeedback("FALSCHE TASTE", C.red); return end
		if bestD <= PERFECT then report("hit", best); g.perfect += 1; showFeedback("PERFEKT!", C.gold)
		elseif bestD <= GOOD then report("hit", best); showFeedback("GUT", C.green)
		else report("miss", best); showFeedback(now < g.start + (best - 1) * g.interval and "ZU FRÜH" or "ZU SPÄT", C.red) end
	end
end

local function bindInput(on)
	if on then
		CAS:BindActionAtPriority("CC_Minigame", function(_, state, input)
			if state ~= Enum.UserInputState.Begin then return Enum.ContextActionResult.Sink end
			local key = KEYMAP[input.KeyCode] or PAD[input.KeyCode]
			if game_ and game_.game == "rhythm" and input.KeyCode == Enum.KeyCode.ButtonA then key = game_.keys[1] == "Space" and "Space" or key end
			if key then press(key) end
			return Enum.ContextActionResult.Sink
		end, false, 3000, Enum.KeyCode.Q, Enum.KeyCode.E, Enum.KeyCode.R, Enum.KeyCode.F, Enum.KeyCode.Space,
			Enum.KeyCode.ButtonX, Enum.KeyCode.ButtonY, Enum.KeyCode.ButtonB, Enum.KeyCode.ButtonA)
	else
		CAS:UnbindAction("CC_Minigame")
	end
end
-- Touch/Maus: auf die angezeigte Taste tippen
target.Activated:Connect(function()
	local g = game_; if not g or g.game ~= "rhythm" then return end
	local now = workspace:GetServerTimeNow()
	local best, bestD
	for i = 1, g.n do
		if not g.done[i] then
			local d = math.abs(now - (g.start + (i - 1) * g.interval))
			if not bestD or d < bestD then best, bestD = i, d end
		end
	end
	if best then press(g.keys[best]) end
end)

-- Anleitung mit Tastensymbolen (je Geraet)
local function buildHow(g)
	for _, c in ipairs(howRow:GetChildren()) do if c:IsA("GuiObject") then c:Destroy() end end
	local touch = UI.device() == "touch"
	local function txt(t, o) UI.label({ Text = t, TextSize = 17, TextColor3 = C.text, AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, 30), TextWrapped = false, LayoutOrder = o, Parent = howRow }) end
	local function key(k, o) UI.key(label(k), { LayoutOrder = o, Parent = howRow }) end
	if g.game == "seq" then
		txt((touch and "Tippe die Tasten der Reihe nach an" or "Drücke die Tasten der Reihe nach") .. (" – %d Schläge in %d Sekunden"):format(g.n, g.time), 1)
	elseif g.keys[2] and g.keys[1] ~= g.keys[2] then
		txt(touch and "Tippe" or "Drücke", 1); key(g.keys[1], 2); txt("und", 3); key(g.keys[2], 4); txt("abwechselnd, wenn der Ring den Kreis berührt", 5)
	elseif touch then
		txt("Tippe den Kreis an, wenn der Ring ihn berührt", 1)
	else
		txt("Drücke", 1); key(g.keys[1], 2); txt("wenn der Ring den Kreis berührt", 3)
	end
end

local function startGame(t)
	game_ = { id = t.id, kind = t.kind, game = t.game, keys = t.keys, n = t.n, interval = t.interval, time = t.time, start = t.start,
		camKind = t.cam, label = t.label, done = {}, hits = 0, misses = 0, perfect = 0, cur = 1 }
	for _, b in ipairs(boxes) do b:Destroy() end
	boxes = {}
	if t.game == "seq" then
		for i, k in ipairs(t.keys) do
			local b = UI.new("TextButton", { Text = "", AutoButtonColor = false, BackgroundTransparency = 1, Size = UDim2.fromOffset(58, 66), LayoutOrder = i, Parent = row })
			UI.chamfer({ Name = "Bg", Size = UDim2.fromScale(1, 1), ImageColor3 = C.bg1, ImageTransparency = 0.02, Parent = b }, "fill", 10)
			UI.label({ Name = "Key", Text = label(k), FontFace = F.title, TextSize = 26, TextXAlignment = Enum.TextXAlignment.Center, Size = UDim2.fromScale(1, 1), ZIndex = 3, Parent = b })
			UI.ring(b, 10, C.red).Name = "Ring"
			b.Activated:Connect(function() if game_ and game_.cur == i then press(k) end end)
			boxes[i] = b
		end
	end
	row.Visible = t.game == "seq"; timeBar.Visible = t.game == "seq"
	target.Visible = t.game == "rhythm"; ring.Visible = t.game == "rhythm"
	title.Text = t.label:upper()
	statTag:FindFirstChildWhichIsA("TextLabel").Text = STAT_DE[t.kind == "jack" and "Cardio" or "Power"]
	buildHow(game_)
	closeResult()
	gui.Enabled = true
	PPS.Enabled = false
	bindInput(true)
end
local function stopGame()
	game_ = nil
	gui.Enabled = false
	PPS.Enabled = true
	bindInput(false)
	if cam.CameraType == Enum.CameraType.Scriptable then cam.CameraType = Enum.CameraType.Custom end
end
local lastPerfect = 0
player:GetAttributeChangedSignal("CC_Minigame"):Connect(function()
	local raw = player:GetAttribute("CC_Minigame")
	if not raw then if game_ then lastPerfect = game_.perfect end; stopGame(); return end
	local ok, t = pcall(function() return HS:JSONDecode(raw) end)
	if ok and type(t) == "table" then startGame(t) end
end)

-- Ergebnis vom Server (echte Belohnung)
player:GetAttributeChangedSignal("CC_TrainResult"):Connect(function()
	local ok, r = pcall(function() return HS:JSONDecode(player:GetAttribute("CC_TrainResult") or "") end)
	if not ok or type(r) ~= "table" then return end
	local rate = r.n > 0 and r.hits / r.n or 0
	resTitle.Text = rate >= 0.9 and "SEHR STARK" or rate >= 0.6 and "STARK" or rate >= 0.3 and "GESCHAFFT" or "NOCHMAL VERSUCHEN"
	resTitle.TextColor3 = rate >= 0.6 and C.gold or (rate >= 0.3 and C.text or C.warn)
	task.wait()                                      -- lastPerfect wird beim Ende des Minispiels gesetzt
	resLine.Text = ("%s  ·  %d von %d getroffen%s"):format(r.label or "", r.hits, r.n, lastPerfect > 0 and ("  ·  %d perfekt"):format(lastPerfect) or "")
	for _, c in ipairs(rewardRow:GetChildren()) do if c:IsA("GuiObject") then c:Destroy() end end
	local statDe = STAT_DE[r.stat] or r.stat
	UI.tag({ Text = ("+%d TP  %s"):format(r.tp, statDe), Color = r.tp > 0 and C.blue or C.bg3, Size = UDim2.fromOffset(0, 36), Parent = rewardRow })
	UI.tag({ Text = ("+%d XP"):format(r.xp), Color = r.xp > 0 and C.gold or C.bg3, TextColor = C.bg0, Size = UDim2.fromOffset(0, 36), Parent = rewardRow })
	if r.tp == 0 then UI.label({ Text = "Ab 30 % Treffern gibt es Trainingspunkte.", TextSize = 15, TextColor3 = C.dim, AutomaticSize = Enum.AutomaticSize.X, TextWrapped = false, Size = UDim2.fromOffset(0, 36), Parent = rewardRow }) end
	-- Fortschritt des Werts (Attribute kommen vom Profil-Server, kurz warten)
	task.delay(0.3, function()
		local v, tp = player:GetAttribute("CC_" .. r.stat) or 0, player:GetAttribute("CC_" .. r.stat .. "TP") or 0
		statL.Text = ("%s %d / 20   ·   %d/10 TP bis zum nächsten Punkt"):format(statDe, v, tp)
		for k, pip in ipairs(resPips) do pip.BackgroundColor3 = k <= tp and C.blue or C.bg3 end
	end)
	resGui.Enabled = true
	player:SetAttribute("CC_TrainResultOpen", true)
	resultUntil = os.clock() + 12
	UI.focus(bNext)
end)
CAS:BindActionAtPriority("CC_TrainResultClose", function(_, st)
	if not resGui.Enabled then return Enum.ContextActionResult.Pass end
	if st == Enum.UserInputState.Begin then closeResult() end
	return Enum.ContextActionResult.Sink
end, false, 3050, Enum.KeyCode.Backspace, Enum.KeyCode.ButtonB)

-- ---------- Ablauf je Bild ----------
RunService:BindToRenderStep("CC_Minigame", Enum.RenderPriority.Camera.Value + 5, function()
	if resGui.Enabled then
		local c = player.Character
		local hum = c and c:FindFirstChildOfClass("Humanoid")
		-- schliessen nach Zeit oder wenn der Spieler losgeht
		if os.clock() > resultUntil or (hum and hum.MoveDirection.Magnitude > 0.5 and os.clock() > resultUntil - 10.5) then closeResult() end
	end
	local g = game_; if not g then return end
	local now = workspace:GetServerTimeNow()
	-- Kamera von vorn
	local char = player.Character
	local root = char and char:FindFirstChild("HumanoidRootPart")
	if root then
		local cf = root.CFrame
		local pos, look
		if g.camKind == "bench" then
			pos = cf.Position + cf.LookVector * 5.5 + Vector3.new(0, 4.2, 0) + cf.RightVector * 1.5
			look = cf.Position - cf.LookVector * 1.2 + Vector3.new(0, -0.6, 0)
		elseif g.camKind == "side" then
			pos = cf.Position + cf.RightVector * 7 + cf.LookVector * 1.8 + Vector3.new(0, 1.4, 0)
			look = cf.Position + cf.LookVector * 1.6 + Vector3.new(0, 0.6, 0)
		else
			pos = cf.Position + cf.LookVector * 8.5 + Vector3.new(0, 1.2, 0)
			look = cf.Position + Vector3.new(0, 0.4, 0)
		end
		cam.CameraType = Enum.CameraType.Scriptable
		cam.CFrame = cam.CFrame:Lerp(CFrame.lookAt(pos, look), 0.2)
	end
	if os.clock() > feedbackUntil then feedback.Text = "" end
	local done = g.hits + g.misses
	progFill.Size = UDim2.fromScale(done / g.n, 1)
	if now < g.start then
		countL.Text = tostring(math.ceil(g.start - now))
		progL.Text = "Gleich geht's los …"
		if g.game == "rhythm" then target.Text = label(g.keys[1]); ring.Size = UDim2.fromOffset(92, 92) end
		return
	end
	countL.Text = (now - g.start < 0.5) and "LOS!" or ""
	if g.game == "seq" then
		local left = math.max(0, g.start + g.time - now)
		timeFill.Size = UDim2.fromScale(left / g.time, 1)
		progL.Text = ("Schlag %d / %d   ·   Treffer %d   ·   Fehler %d   ·   noch %.1f s"):format(math.min(g.cur, g.n), g.n, g.hits, g.misses, left)
		for i, b in ipairs(boxes) do
			local d = g.done[i]
			b.Bg.ImageColor3 = d == "hit" and C.green or d == "miss" and C.redDark or C.bg1
			b.Ring.Visible = i == g.cur
			b.Key.TextColor3 = (d or i == g.cur) and C.text or C.dim
		end
		if left <= 0 then for i = g.cur, g.n do report("miss", i) end; g.cur = g.n + 1 end
	else
		for i = 1, g.n do
			if not g.done[i] and now > g.start + (i - 1) * g.interval + LATE then report("miss", i); showFeedback("VERPASST", C.red) end
		end
		local nxt
		for i = 1, g.n do if not g.done[i] then nxt = i; break end end
		if nxt then
			local due = g.start + (nxt - 1) * g.interval
			local k = math.clamp((due - now) / g.interval, 0, 1)
			local sz = 92 + 160 * k
			ring.Size = UDim2.fromOffset(sz, sz)
			local inWin = math.abs(due - now) <= GOOD
			ringStroke.Color = inWin and C.green or C.text
			tStroke.Color = inWin and C.green or C.red
			target.Text = label(g.keys[nxt])
		end
		progL.Text = ("Wiederholung %d / %d   ·   Treffer %d   ·   perfekt %d"):format(math.min(done + 1, g.n), g.n, g.hits, g.perfect)
	end
end)
