-- StarterPlayer.StarterPlayerScripts.CC_Minigame
-- Trainings-Minispiele im Gym (Aufgaben vom Server, Attribut CC_Minigame als JSON am Spieler; Rueckmeldung ueber CC_Train):
--   "seq":    Tastenfolge (Q E R F) der Reihe nach druecken, Zeitlimit; falsche Taste = Fehler (Kombo bricht)
--   "rhythm": Taste druecken, wenn der Ring den Kreis erreicht (gut +-0,18 s, perfekt +-0,08 s); Q/E abwechselnd bei Curls
-- Controller: Q=X, E=Y, R=B, F=A, Leertaste=A. Touch: auf die angezeigte Taste tippen.
-- Kamera waehrend des Trainings: von vorn (Bank: von der Fussseite schraeg oben, Sack: seitlich).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local CAS = game:GetService("ContextActionService")
local HS = game:GetService("HttpService")
local PPS = game:GetService("ProximityPromptService")
local player = Players.LocalPlayer
local trainEv = game.ReplicatedStorage:WaitForChild("CC_Train")
local cam = workspace.CurrentCamera

local GOOD, PERFECT, LATE = 0.18, 0.08, 0.25
local PAD = { [Enum.KeyCode.ButtonX] = "Q", [Enum.KeyCode.ButtonY] = "E", [Enum.KeyCode.ButtonB] = "R", [Enum.KeyCode.ButtonA] = "F" }
local KEYMAP = { [Enum.KeyCode.Q] = "Q", [Enum.KeyCode.E] = "E", [Enum.KeyCode.R] = "R", [Enum.KeyCode.F] = "F", [Enum.KeyCode.Space] = "Space" }
local PAD_LABEL = { Q = "X", E = "Y", R = "B", F = "A", Space = "A" }

-- ---------- Oberflaeche ----------
local gui = Instance.new("ScreenGui"); gui.Name = "CC_MinigameGui"; gui.ResetOnSpawn = false; gui.Enabled = false; gui.Parent = player:WaitForChild("PlayerGui")
local function lbl(parent, size, font, pos, sz, text)
	local l = Instance.new("TextLabel"); l.BackgroundTransparency = 1; l.Font = font; l.TextSize = size; l.TextColor3 = Color3.new(1, 1, 1)
	l.TextStrokeTransparency = 0.3; l.AnchorPoint = Vector2.new(0.5, 0.5); l.Position = pos; l.Size = sz; l.Text = text or ""; l.Parent = parent; return l
end
local title = lbl(gui, 28, Enum.Font.GothamBlack, UDim2.new(0.5, 0, 0.16, 0), UDim2.fromOffset(600, 40))
local info = lbl(gui, 18, Enum.Font.GothamBold, UDim2.new(0.5, 0, 0.16, 34), UDim2.fromOffset(600, 26))
local feedback = lbl(gui, 34, Enum.Font.GothamBlack, UDim2.new(0.5, 0, 0.62, 0), UDim2.fromOffset(400, 50))
-- Rhythmus: Ziel-Kreis + schrumpfender Ring
local ring = Instance.new("Frame"); ring.AnchorPoint = Vector2.new(0.5, 0.5); ring.Position = UDim2.fromScale(0.5, 0.78); ring.BackgroundTransparency = 1; ring.Parent = gui
local ringStroke = Instance.new("UIStroke", ring); ringStroke.Thickness = 4; ringStroke.Color = Color3.fromRGB(255, 220, 60)
Instance.new("UICorner", ring).CornerRadius = UDim.new(1, 0)
local target = Instance.new("TextButton"); target.AnchorPoint = Vector2.new(0.5, 0.5); target.Position = UDim2.fromScale(0.5, 0.78); target.Size = UDim2.fromOffset(84, 84)
target.BackgroundColor3 = Color3.fromRGB(25, 25, 30); target.BackgroundTransparency = 0.15; target.Font = Enum.Font.GothamBlack; target.TextSize = 30
target.TextColor3 = Color3.new(1, 1, 1); target.TextScaled = false; target.AutoButtonColor = false; target.Parent = gui
Instance.new("UICorner", target).CornerRadius = UDim.new(1, 0)
local tStroke = Instance.new("UIStroke", target); tStroke.Thickness = 3; tStroke.Color = Color3.new(1, 1, 1)
-- Tastenfolge: Reihe von Kaestchen + Zeitbalken
local row = Instance.new("Frame"); row.AnchorPoint = Vector2.new(0.5, 0.5); row.Position = UDim2.fromScale(0.5, 0.78); row.Size = UDim2.fromOffset(640, 70)
row.BackgroundTransparency = 1; row.Parent = gui
local rowLayout = Instance.new("UIListLayout", row); rowLayout.FillDirection = Enum.FillDirection.Horizontal; rowLayout.HorizontalAlignment = Enum.HorizontalAlignment.Center
rowLayout.Padding = UDim.new(0, 8)
local timeBar = Instance.new("Frame"); timeBar.AnchorPoint = Vector2.new(0.5, 0.5); timeBar.Position = UDim2.new(0.5, 0, 0.78, 52); timeBar.Size = UDim2.fromOffset(500, 10)
timeBar.BackgroundColor3 = Color3.fromRGB(40, 40, 46); timeBar.BorderSizePixel = 0; timeBar.Parent = gui
local timeFill = Instance.new("Frame"); timeFill.Size = UDim2.fromScale(1, 1); timeFill.BackgroundColor3 = Color3.fromRGB(255, 200, 40); timeFill.BorderSizePixel = 0; timeFill.Parent = timeBar

-- ---------- Zustand ----------
local game_ = nil          -- aktuelle Aufgabe (Tabelle aus JSON + Laufzeitdaten)
local boxes = {}
local feedbackUntil = 0
local function label(key)
	local pad = game:GetService("UserInputService"):GetLastInputType().Name:find("Gamepad")
	if pad then return PAD_LABEL[key] or key end
	return key == "Space" and "LEER" or key
end
local function showFeedback(text, color) feedback.Text = text; feedback.TextColor3 = color; feedbackUntil = os.clock() + 0.5 end
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
			report("hit", i); showFeedback("TREFFER", Color3.fromRGB(120, 230, 120))
		else
			report("miss", i); showFeedback("FALSCH", Color3.fromRGB(255, 90, 80))
		end
		g.cur = i + 1
	else
		-- naechste offene Aufgabe in Reichweite suchen
		local best, bestD
		for i = 1, g.n do
			if not g.done[i] then
				local due = g.start + (i - 1) * g.interval
				local d = math.abs(now - due)
				if d <= LATE + 0.15 and (not bestD or d < bestD) then best, bestD = i, d end
			end
		end
		if not best then return end
		if key ~= g.keys[best] then report("miss", best); showFeedback("FALSCHE TASTE", Color3.fromRGB(255, 90, 80)); return end
		if bestD <= PERFECT then report("hit", best); showFeedback("PERFEKT!", Color3.fromRGB(255, 220, 60))
		elseif bestD <= GOOD then report("hit", best); showFeedback("GUT", Color3.fromRGB(120, 230, 120))
		else report("miss", best); showFeedback(now < g.start + (best - 1) * g.interval and "ZU FRÜH" or "ZU SPÄT", Color3.fromRGB(255, 90, 80)) end
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

local function startGame(t)
	game_ = { id = t.id, kind = t.kind, game = t.game, keys = t.keys, n = t.n, interval = t.interval, time = t.time, start = t.start,
		camKind = t.cam, label = t.label, done = {}, hits = 0, misses = 0, cur = 1 }
	for _, b in ipairs(boxes) do b:Destroy() end
	boxes = {}
	if t.game == "seq" then
		for i, k in ipairs(t.keys) do
			local b = Instance.new("TextButton"); b.Size = UDim2.fromOffset(54, 60); b.BackgroundColor3 = Color3.fromRGB(30, 30, 36); b.Text = label(k)
			b.Font = Enum.Font.GothamBlack; b.TextSize = 26; b.TextColor3 = Color3.new(1, 1, 1); b.AutoButtonColor = false; b.LayoutOrder = i
			Instance.new("UICorner", b).CornerRadius = UDim.new(0, 8)
			b.Activated:Connect(function() if game_ and game_.cur == i then press(k) end end)
			b.Parent = row; boxes[i] = b
		end
	end
	row.Visible = t.game == "seq"; timeBar.Visible = t.game == "seq"
	target.Visible = t.game == "rhythm"; ring.Visible = t.game == "rhythm"
	title.Text = t.label:upper()
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
player:GetAttributeChangedSignal("CC_Minigame"):Connect(function()
	local raw = player:GetAttribute("CC_Minigame")
	if not raw then stopGame(); return end
	local ok, t = pcall(function() return HS:JSONDecode(raw) end)
	if ok and type(t) == "table" then startGame(t) end
end)

-- ---------- Ablauf je Bild ----------
RunService:BindToRenderStep("CC_Minigame", Enum.RenderPriority.Camera.Value + 5, function()
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
	if now < g.start then
		info.Text = ("Bereit … %d"):format(math.ceil(g.start - now))
		if g.game == "rhythm" then target.Text = label(g.keys[1]); ring.Size = UDim2.fromOffset(84, 84) end
		return
	end
	if g.game == "seq" then
		local left = math.max(0, g.start + g.time - now)
		timeFill.Size = UDim2.fromScale(left / g.time, 1)
		info.Text = ("Treffer %d · Fehler %d · noch %.1f s"):format(g.hits, g.misses, left)
		for i, b in ipairs(boxes) do
			local d = g.done[i]
			b.BackgroundColor3 = d == "hit" and Color3.fromRGB(60, 160, 80) or d == "miss" and Color3.fromRGB(170, 50, 45)
				or (i == g.cur and Color3.fromRGB(220, 180, 40) or Color3.fromRGB(30, 30, 36))
		end
		if left <= 0 then for i = g.cur, g.n do report("miss", i) end; g.cur = g.n + 1 end
	else
		-- verpasste Takte als Fehler melden
		for i = 1, g.n do
			if not g.done[i] and now > g.start + (i - 1) * g.interval + LATE then report("miss", i); showFeedback("VERPASST", Color3.fromRGB(255, 90, 80)) end
		end
		-- naechster offener Takt
		local nxt
		for i = 1, g.n do if not g.done[i] then nxt = i; break end end
		if nxt then
			local due = g.start + (nxt - 1) * g.interval
			local k = math.clamp((due - now) / g.interval, 0, 1)
			local sz = 84 + 150 * k
			ring.Size = UDim2.fromOffset(sz, sz)
			ringStroke.Color = math.abs(due - now) <= GOOD and Color3.fromRGB(120, 230, 120) or Color3.fromRGB(255, 220, 60)
			target.Text = label(g.keys[nxt])
		end
		info.Text = ("Wiederholung %d / %d · Treffer %d"):format(math.min(g.hits + g.misses + 1, g.n), g.n, g.hits)
	end
end)
