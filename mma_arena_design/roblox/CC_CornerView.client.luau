-- StarterPlayer.StarterPlayerScripts.CC_CornerView
-- Rundenpause in der Ecke, Sicht des Spielers (Attribut Corner am eigenen Kampf, gespiegelt in ReplicatedStorage.CC_MatchState):
--   * Kamera-Schnitte: eigene Ecke (Trainer gibt Wasser) -> Ecke des Gegners -> Totale, dann zurueck zur Kampfkamera
--   * Anzeige unten: beide Kaempfer nebeneinander (Name, Gesundheit, Ausdauer, Punkte)
--   * Wasserflasche in der rechten Hand jedes Eck-Trainers (nur lokal gezeichnet, folgt dem Hand-Bone)
local Players, RS, RunService, TweenService = game:GetService("Players"), game:GetService("ReplicatedStorage"), game:GetService("RunService"), game:GetService("TweenService")
local player = Players.LocalPlayer
local mirror = RS:WaitForChild("CC_MatchState")

local running = false
local bottles = {}           -- [coach model] = part
local gui

local function head(c) local r = c and c:FindFirstChild("HumanoidRootPart"); return r and r.Position + Vector3.new(0, 1.2, 0) end
local function fightersInMatch()
	local id = player:GetAttribute("CC_MatchId")
	local red, blue
	local rp = Players:FindFirstChild(mirror:GetAttribute("RedName") or "")
	if rp and rp.Character then red = rp.Character end
	for _, p in ipairs(Players:GetPlayers()) do
		local c = p.Character
		if c and c ~= red and c:GetAttribute("CC_MatchId") == id then blue = c end
	end
	if not blue then local d = workspace:FindFirstChild("CC_TrainingDummy"); if d and d:GetAttribute("CC_MatchId") == id then blue = d end end
	return red, blue
end

-- Flasche
local function makeBottle(coach)
	local b = Instance.new("Part"); b.Name = "CornerBottle"; b.Shape = Enum.PartType.Cylinder
	b.Size = Vector3.new(0.95, 0.38, 0.38); b.Color = Color3.fromRGB(70, 150, 225); b.Material = Enum.Material.Glass; b.Transparency = 0.15
	b.Anchored = true; b.CanCollide = false; b.CanQuery = false; b.CanTouch = false; b.CastShadow = false
	local cap = Instance.new("Part"); cap.Shape = Enum.PartType.Cylinder; cap.Size = Vector3.new(0.12, 0.18, 0.18); cap.Color = Color3.fromRGB(240, 240, 240)
	cap.Anchored = true; cap.CanCollide = false; cap.CanQuery = false; cap.CanTouch = false; cap.Name = "Cap"; cap.Parent = b
	b.Parent = workspace.CurrentCamera
	return b
end

-- Anzeige beider Kaempfer
local function bar(parent, y, color)
	local bg = Instance.new("Frame"); bg.BackgroundColor3 = Color3.fromRGB(30, 32, 38); bg.BorderSizePixel = 0; bg.Position = UDim2.new(0, 16, 0, y); bg.Size = UDim2.new(1, -32, 0, 8); bg.Parent = parent
	local fill = Instance.new("Frame"); fill.BackgroundColor3 = color; fill.BorderSizePixel = 0; fill.Size = UDim2.fromScale(1, 1); fill.Parent = bg
	return fill
end
local function card(side, x)
	local f = Instance.new("Frame"); f.AnchorPoint = Vector2.new(0.5, 1); f.Position = UDim2.new(x, 0, 1, -64); f.Size = UDim2.fromOffset(300, 116)
	f.BackgroundColor3 = Color3.fromRGB(12, 14, 18); f.BackgroundTransparency = 0.12; f.BorderSizePixel = 0; f.Parent = gui
	Instance.new("UICorner", f).CornerRadius = UDim.new(0, 8)
	local st = Instance.new("UIStroke", f); st.Thickness = 2; st.Color = side == "red" and Color3.fromRGB(210, 40, 44) or Color3.fromRGB(46, 96, 214)
	local n = Instance.new("TextLabel"); n.BackgroundTransparency = 1; n.Position = UDim2.fromOffset(16, 10); n.Size = UDim2.new(1, -32, 0, 26)
	n.Font = Enum.Font.GothamBlack; n.TextSize = 20; n.TextXAlignment = Enum.TextXAlignment.Left; n.TextColor3 = Color3.new(1, 1, 1); n.Parent = f
	local s = Instance.new("TextLabel"); s.BackgroundTransparency = 1; s.Position = UDim2.fromOffset(16, 10); s.Size = UDim2.new(1, -32, 0, 26)
	s.Font = Enum.Font.GothamBold; s.TextSize = 16; s.TextXAlignment = Enum.TextXAlignment.Right; s.TextColor3 = Color3.fromRGB(200, 204, 212); s.Parent = f
	local l1 = Instance.new("TextLabel"); l1.BackgroundTransparency = 1; l1.Position = UDim2.fromOffset(16, 42); l1.Size = UDim2.new(1, -32, 0, 14)
	l1.Font = Enum.Font.GothamMedium; l1.TextSize = 12; l1.TextXAlignment = Enum.TextXAlignment.Left; l1.TextColor3 = Color3.fromRGB(170, 176, 186); l1.Text = "HEALTH"; l1.Parent = f
	local hp = bar(f, 60, side == "red" and Color3.fromRGB(210, 40, 44) or Color3.fromRGB(46, 96, 214))
	local l2 = l1:Clone(); l2.Position = UDim2.fromOffset(16, 76); l2.Text = "STAMINA"; l2.Parent = f
	local stm = bar(f, 94, Color3.fromRGB(240, 196, 40))
	return { name = n, score = s, hp = hp, stm = stm }
end
local function buildGui()
	gui = Instance.new("ScreenGui"); gui.Name = "CC_CornerView"; gui.DisplayOrder = 40; gui.ResetOnSpawn = false; gui.IgnoreGuiInset = true
	local title = Instance.new("TextLabel"); title.BackgroundTransparency = 1; title.AnchorPoint = Vector2.new(0.5, 1); title.Position = UDim2.new(0.5, 0, 1, -188)
	title.Size = UDim2.fromOffset(400, 30); title.Font = Enum.Font.GothamBlack; title.TextSize = 22; title.TextColor3 = Color3.new(1, 1, 1)
	title.TextStrokeTransparency = 0.5; title.Text = ("BETWEEN ROUNDS  ·  ROUND %d NEXT"):format(mirror:GetAttribute("Round") or 2); title.Parent = gui
	local red, blue = card("red", 0.5 - 0.17), card("blue", 0.5 + 0.17)
	gui.Parent = player:WaitForChild("PlayerGui")
	return red, blue
end

local function stamina(c)
	local v = c and c:GetAttribute("CC_Stamina")
	return typeof(v) == "number" and math.clamp(v / (c:GetAttribute("CC_StaminaMax") or 100), 0, 1) or nil
end

local function run()
	if running then return end
	running = true
	local red, blue = fightersInMatch()
	local redCard, blueCard = buildGui()
	local mine = (red and red == player.Character) and red or blue
	local other = mine == red and blue or red
	local cam = workspace.CurrentCamera
	local saved = { type = cam.CameraType, fov = cam.FieldOfView }
	local t0 = os.clock()
	local function coachOf(c)
		local f = workspace:FindFirstChild("CC_Corners")
		if not (f and c) then return nil end
		for _, m in ipairs(f:GetChildren()) do if m:GetAttribute("CC_CornerOf") == c.Name then return m end end
	end
	RunService:BindToRenderStep("CC_CornerCam", Enum.RenderPriority.Last.Value + 55, function()
		if not running then return end
		local t = os.clock() - t0
		-- Schnitte: 0-3,4 s eigene Ecke, 3,4-5,6 s Gegner, danach Totale
		local subject = t < 3.4 and mine or (t < 5.6 and other or nil)
		local root = subject and subject:FindFirstChild("HumanoidRootPart")
		cam.CameraType = Enum.CameraType.Scriptable
		if root then
			local look = root.CFrame.LookVector * Vector3.new(1, 0, 1)
			local side = -root.CFrame.RightVector            -- Seite der Trainer-Hand mit der Flasche
			local hp = root.Position + Vector3.new(0, 0.2, 0)
			local u = (subject == mine) and t or (t - 3.4)
			local mid = hp + look * 1.7
			cam.CFrame = CFrame.lookAt(mid + side * (11 - u * 0.4) + look * 2.5 + Vector3.new(0, 2.6, 0), mid + Vector3.new(0, -0.4, 0))
			cam.FieldOfView = 40
		elseif red and blue and red:FindFirstChild("HumanoidRootPart") and blue:FindFirstChild("HumanoidRootPart") then
			local a, b = red.HumanoidRootPart.Position, blue.HumanoidRootPart.Position
			local mid = (a + b) / 2
			local perp = (b - a):Cross(Vector3.yAxis).Unit
			cam.CFrame = CFrame.lookAt(mid + perp * 20 + Vector3.new(0, 9, 0), mid)
			cam.FieldOfView = 55
		end
		-- Flaschen an den Trainer-Haenden
		for _, c in ipairs({ red, blue }) do
			local coach = coachOf(c)
			if coach then
				local bone = coach:FindFirstChild("RightHand", true)
				if bone and bone:IsA("Bone") then
					local b = bottles[coach] or makeBottle(coach); bottles[coach] = b
					if not _G.CC_BottleSeen then _G.CC_BottleSeen = true; print("[CC] Ecke: Flasche an " .. coach.Name) end
					-- Flasche zeigt von der Hand zum Mund des Kaempfers (Kopf), Mitte 0,4 Studs vor der Hand
					local hand = bone.TransformedWorldCFrame.Position
					local hd = c:FindFirstChild("Head", true)
					local mouth = hd and (hd:IsA("Bone") and hd.TransformedWorldCFrame.Position or hd.Position) or head(c)
					local dir = (mouth - hand).Magnitude > 0.05 and (mouth - hand).Unit or Vector3.yAxis
					local ctr = hand + dir * 0.45
					b.CFrame = CFrame.lookAt(ctr, ctr + dir) * CFrame.Angles(0, math.rad(90), 0)
					b.Cap.CFrame = b.CFrame * CFrame.new(0.55, 0, 0)
				end
			end
		end
		-- Anzeige
		for _, e in ipairs({ { red, redCard, "ScoreRed", mirror:GetAttribute("RedName") }, { blue, blueCard, "ScoreBlue", mirror:GetAttribute("BlueName") } }) do
			local c, cd = e[1], e[2]
			local h = c and c:FindFirstChildOfClass("Humanoid")
			cd.name.Text = string.upper(tostring(e[4] or "?"))
			cd.score.Text = ("%d PTS"):format(mirror:GetAttribute(e[3]) or 0)
			cd.hp.Size = UDim2.fromScale(h and math.clamp(h.Health / h.MaxHealth, 0, 1) or 0, 1)
			local s = stamina(c); cd.stm.Size = UDim2.fromScale(s or 1, 1)
		end
	end)
	while running and mirror:GetAttribute("Corner") == true do task.wait(0.1) end
	running = false
	pcall(function() RunService:UnbindFromRenderStep("CC_CornerCam") end)
	for k, b in pairs(bottles) do b:Destroy(); bottles[k] = nil end
	if gui then gui:Destroy(); gui = nil end
	cam.CameraType = Enum.CameraType.Custom; cam.FieldOfView = saved.fov
	local hum = player.Character and player.Character:FindFirstChildOfClass("Humanoid"); if hum then cam.CameraSubject = hum end
end

mirror:GetAttributeChangedSignal("Corner"):Connect(function()
	if mirror:GetAttribute("Corner") == true then task.spawn(run) else running = false end
end)
