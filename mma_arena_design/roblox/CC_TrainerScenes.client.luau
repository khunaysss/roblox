-- StarterPlayer.StarterPlayerScripts.CC_TrainerScenes
-- Zeigt die Filmszenen der Stil-Trainer (ReplicatedStorage.CC_TrainerScenes, ausgeloest vom Server CC_TrainerScenes):
-- Kamerafahrten relativ zum Trainer, Kinobalken, Titel, Ueberspringen (Leertaste / Enter / Klick / Controller A).
-- Waehrend der Szene: Steuerung aus (CC_UIBlock + PlayerModule-Controls), alle anderen Oberflaechen ausgeblendet.
-- Danach wird alles exakt zurueckgesetzt (Kamera, Sichtfeld, Oberflaechen, Steuerung), auch beim Ueberspringen oder Abbruch.
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local TweenService = game:GetService("TweenService")
local player = Players.LocalPlayer
local SC = require(RS:WaitForChild("CC_TrainerScenes"))
local ev = RS:WaitForChild("CC_TrainerScene")

-- Steuerung: das Spiel nutzt eigene Scripts (CC_Input beachtet CC_UIBlock); Robloxs PlayerModule nur, falls vorhanden
local controls
task.spawn(function()
	local ps = player:WaitForChild("PlayerScripts", 5)
	local pm = ps and ps:FindFirstChild("PlayerModule")
	if pm then pcall(function() controls = require(pm):GetControls() end) end
end)

local running = nil
local function ease(x) x = math.clamp(x, 0, 1); return x * x * (3 - 2 * x) end

local function makeGui(def, info)
	local gui = Instance.new("ScreenGui"); gui.Name = "CC_TrainerSceneGui"; gui.IgnoreGuiInset = true; gui.ResetOnSpawn = false; gui.DisplayOrder = 40
	local function bar(top)
		local f = Instance.new("Frame"); f.BorderSizePixel = 0; f.BackgroundColor3 = Color3.new(0, 0, 0)
		f.Size = UDim2.new(1, 0, 0, 0); f.Position = top and UDim2.fromScale(0, 0) or UDim2.fromScale(0, 1); f.AnchorPoint = top and Vector2.zero or Vector2.new(0, 1)
		f.Parent = gui
		TweenService:Create(f, TweenInfo.new(0.35, Enum.EasingStyle.Quad), { Size = UDim2.new(1, 0, 0.11, 0) }):Play()
		return f
	end
	bar(true); local bottom = bar(false)
	local title = Instance.new("TextLabel"); title.BackgroundTransparency = 1; title.AnchorPoint = Vector2.new(0, 1)
	title.Position = UDim2.new(0.05, 0, 0.82, 0); title.Size = UDim2.new(0.7, 0, 0.075, 0); title.Font = Enum.Font.GothamBlack
	title.TextScaled = true; title.TextXAlignment = Enum.TextXAlignment.Left; title.TextColor3 = Color3.fromRGB(235, 236, 240)
	title.Text = def.title or info.trainerName or ""; title.TextTransparency = 1; title.Parent = gui
	local sub = Instance.new("TextLabel"); sub.BackgroundTransparency = 1; sub.AnchorPoint = Vector2.new(0, 0)
	sub.Position = UDim2.new(0.05, 0, 0.825, 0); sub.Size = UDim2.new(0.7, 0, 0.035, 0); sub.Font = Enum.Font.GothamBold
	sub.TextScaled = true; sub.TextXAlignment = Enum.TextXAlignment.Left; sub.TextColor3 = Color3.fromRGB(200, 40, 50)
	sub.Text = def.sub or ""; sub.TextTransparency = 1; sub.Parent = gui
	local skip = Instance.new("TextLabel"); skip.BackgroundTransparency = 1; skip.AnchorPoint = Vector2.new(1, 0.5)
	skip.Position = UDim2.new(0.97, 0, 0.5, 0); skip.Size = UDim2.new(0.3, 0, 0.32, 0); skip.Font = Enum.Font.GothamMedium
	skip.TextScaled = true; skip.TextXAlignment = Enum.TextXAlignment.Right; skip.TextColor3 = Color3.fromRGB(150, 152, 158)
	skip.Text = "LEERTASTE  Überspringen"; skip.Parent = bottom
	gui.Parent = player:WaitForChild("PlayerGui")
	return gui, title, sub
end

local function play(kind, id, model, info)
	if running then running.finish() end
	local def = SC.get(id, kind)
	if not def or (def.length or 0) <= 0 or #def.shots == 0 or not model or not model.Parent then return end
	local cam = workspace.CurrentCamera
	local piv = model:GetPivot()
	local saved = { type = cam.CameraType, cf = cam.CFrame, fov = cam.FieldOfView, subject = cam.CameraSubject }
	local pg = player:WaitForChild("PlayerGui")
	local restoreOn = {}                                   -- Oberflaechen, die nach der Szene wieder an sein sollen
	local gui, title, sub = makeGui(def, info)
	-- Wiederherstellen: was beim Start an war, dazu das Trainer-Panel (oeffnet beim Ansprechen gleichzeitig mit der Begruessung).
	-- Andere Oberflaechen, die erst waehrend der Szene angehen (z. B. Reaktion auf das versteckte Menue), bleiben danach aus.
	local LATE_OK = { CC_TrainerPanel = true }
	local startOn = {}
	for _, g in ipairs(pg:GetChildren()) do if g:IsA("ScreenGui") and g.Enabled then startOn[g] = true end end
	local lateOn = {}
	local function hideOthers()
		for _, g in ipairs(pg:GetChildren()) do
			if g:IsA("ScreenGui") and g ~= gui and g.Enabled then
				if startOn[g] or LATE_OK[g.Name] then restoreOn[g] = true else lateOn[g] = true end
				g.Enabled = false
			end
		end
	end
	hideOthers()
	-- Filmlicht (nur lokal): Fuehrungslicht schraeg vorn oben, weiches Fuelllicht von der anderen Seite, Kante von hinten
	local lights = Instance.new("Folder"); lights.Name = "CC_TrainerSceneLights"
	local function lamp(offset, kind, bright, range, color)
		local p = Instance.new("Part"); p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
		p.Transparency = 1; p.Size = Vector3.new(0.2, 0.2, 0.2)
		local target = (piv * CFrame.new(0, 5.0, 0)).Position
		p.CFrame = CFrame.lookAt((piv * CFrame.new(offset)).Position, target); p.Parent = lights
		local l = Instance.new(kind); l.Brightness = bright; l.Range = range; l.Color = color; l.Shadows = false
		if kind == "SpotLight" then l.Face = Enum.NormalId.Front; l.Angle = 60 end
		l.Parent = p
	end
	lamp(Vector3.new(3.5, 7.5, -6.0), "SpotLight", 3.2, 16, Color3.new(1, 0.97, 0.92))
	lamp(Vector3.new(-4.0, 4.0, -4.5), "PointLight", 0.9, 10, Color3.new(0.82, 0.88, 1))
	lamp(Vector3.new(-1.5, 7.0, 4.0), "SpotLight", 2.0, 14, Color3.new(1, 0.95, 0.9))
	lights.Parent = workspace
	player:SetAttribute("CC_UIBlock", true)
	if controls then pcall(function() controls:Disable() end) end
	local t0 = os.clock()
	local done = false
	local conns = {}
	local state = { finish = nil }
	local function finish()
		if done then return end
		done = true
		RunService:UnbindFromRenderStep("CC_TrainerSceneCam")
		for _, c in ipairs(conns) do c:Disconnect() end
		gui:Destroy()
		lights:Destroy()
		cam.CameraType = saved.type; cam.FieldOfView = saved.fov
		if saved.subject then cam.CameraSubject = saved.subject end
		if saved.type == Enum.CameraType.Scriptable then cam.CFrame = saved.cf end
		for g in pairs(restoreOn) do if g.Parent then g.Enabled = true end end
		for g in pairs(lateOn) do if g.Parent and not restoreOn[g] then g.Enabled = false end end   -- nicht vom Start: aus lassen
		player:SetAttribute("CC_UIBlock", nil)
		if controls then pcall(function() controls:Enable() end) end
		if running == state then running = nil end
	end
	state.finish = finish
	running = state
	-- Kamera
	local rayParams = RaycastParams.new(); rayParams.FilterType = Enum.RaycastFilterType.Exclude
	rayParams.FilterDescendantsInstances = { model, player.Character, lights, workspace:FindFirstChild("CC_StyleTrainersGym") }
	-- Seitenwahl: ist eine Einstellung durch Wand/Saeule verdeckt und die gespiegelte Seite frei, die gespiegelte nehmen
	local function blocked(s)
		local look = (piv * CFrame.new(s.look)).Position
		for _, p in ipairs({ s.from, s.to }) do
			local cpos = (piv * CFrame.new(p)).Position
			if workspace:Raycast(look, cpos - look, rayParams) then return true end
		end
		return false
	end
	local shots = {}
	for i, s in ipairs(def.shots) do
		local m = { t = s.t, fov = s.fov, from = s.from * Vector3.new(-1, 1, 1), to = s.to * Vector3.new(-1, 1, 1), look = s.look * Vector3.new(-1, 1, 1) }
		shots[i] = (blocked(s) and not blocked(m)) and m or s
	end
	def = setmetatable({ shots = shots }, { __index = def })
	local total = 0; for _, s in ipairs(def.shots) do total += s.t end
	RunService:BindToRenderStep("CC_TrainerSceneCam", Enum.RenderPriority.Last.Value + 5, function()
		local t = os.clock() - t0
		if t >= def.length or not model.Parent then finish() return end
		hideOthers()                                      -- Panels, die waehrend der Szene aufgehen, erst danach zeigen
		local acc, shot, u = 0, def.shots[#def.shots], 1
		for _, s in ipairs(def.shots) do
			if t < acc + s.t then shot = s; u = (t - acc) / s.t; break end
			acc += s.t
		end
		local pos = (piv * CFrame.new(shot.from:Lerp(shot.to, ease(u)))).Position
		local look = (piv * CFrame.new(shot.look)).Position
		-- Kamera-Kollision: Hindernis zwischen Blickpunkt und Kamera -> Kamera davor
		local hit = workspace:Raycast(look, pos - look, rayParams)
		if hit then pos = hit.Position + (look - pos).Unit * 0.6 end
		cam.CameraType = Enum.CameraType.Scriptable
		cam.FieldOfView = shot.fov or 50
		cam.CFrame = CFrame.lookAt(pos, look)
		local ta = def.titleAt or 0.5
		local a = math.clamp((t - ta) / 0.35, 0, 1) * math.clamp((def.length - t) / 0.4, 0, 1)
		title.TextTransparency = 1 - a; sub.TextTransparency = 1 - a
	end)
	-- Ueberspringen (erst nach 0,4 s, damit der Tastendruck zum Ansprechen nicht sofort ueberspringt)
	table.insert(conns, UIS.InputBegan:Connect(function(input)
		if os.clock() - t0 < 0.4 then return end
		local k = input.KeyCode
		if k == Enum.KeyCode.Space or k == Enum.KeyCode.Return or k == Enum.KeyCode.ButtonA or k == Enum.KeyCode.ButtonB
			or input.UserInputType == Enum.UserInputType.MouseButton1 then finish() end
	end))
	-- Abbruch, wenn ein Kampf beginnt oder die Figur stirbt
	local c = player.Character
	if c then
		table.insert(conns, c:GetAttributeChangedSignal("CC_Opponent"):Connect(function() if c:GetAttribute("CC_Opponent") then finish() end end))
		local h = c:FindFirstChildOfClass("Humanoid")
		if h then table.insert(conns, h.Died:Connect(finish)) end
	end
	table.insert(conns, player.CharacterRemoving:Connect(finish))
end

ev.OnClientEvent:Connect(function(kind, id, model, info)
	local ok, err = pcall(play, kind, id, model, info or {})
	if not ok then
		warn("[CC] Trainer-Szene Fehler: " .. tostring(err))
		if running then running.finish() end
	end
end)
