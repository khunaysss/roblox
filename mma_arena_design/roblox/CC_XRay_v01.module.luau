-- ReplicatedStorage.CC_XRay
-- Roentgen-Einblendung bei bestaetigter Armbar-Aufgabe (wie eine Roentgenaufnahme: dunkler Film, helle Knochen, kein Blut).
-- Ablauf ca. 2,4 s: Panel faehrt ein, Scan-Linie, Ueberstreckung des Unterarms, Bruch am unteren Oberarm (Riss, Splitter,
-- weisser Blitz, kurzes Wackeln), Schriftzug, Ausblenden. Rein lokal (ScreenGui), raeumt sich selbst auf.
-- Aufruf: require(CC_XRay).play(playerGui)  (CC_FinishReactions, nur fuer Spieler im selben Kampf)
local TweenService = game:GetService("TweenService")
local RS = game:GetService("ReplicatedStorage")
local okUI, UI = pcall(require, RS:FindFirstChild("CC_UI"))

local X = {}
local active = nil

local W, H = 340, 420
local BONE = Color3.fromRGB(226, 234, 242)
local FILM = Color3.fromRGB(7, 11, 17)

local function tween(o, t, props, style, dir)
	local tw = TweenService:Create(o, TweenInfo.new(t, style or Enum.EasingStyle.Quad, dir or Enum.EasingDirection.Out), props)
	tw:Play(); return tw
end
local function new(class, props, parent)
	local o = Instance.new(class)
	for k, v in pairs(props) do o[k] = v end
	o.Parent = parent
	return o
end
-- Knochen: helle Kortikalis an den Raendern, dunkleres Mark in der Mitte (Roentgen-Optik ueber UIGradient)
local function bone(parent, cx, cy, w, h, rot, radius)
	local f = new("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromOffset(cx, cy), Size = UDim2.fromOffset(w, h),
		Rotation = rot or 0, BackgroundColor3 = BONE, BackgroundTransparency = 0.08, BorderSizePixel = 0 }, parent)
	new("UICorner", { CornerRadius = UDim.new(0, radius or math.floor(w / 2)) }, f)
	new("UIGradient", { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.18, 0.25),
		NumberSequenceKeypoint.new(0.5, 0.55), NumberSequenceKeypoint.new(0.82, 0.25), NumberSequenceKeypoint.new(1, 0) }) }, f)
	new("UIStroke", { Color = Color3.fromRGB(190, 215, 255), Transparency = 0.55, Thickness = 1.5 }, f)
	return f
end

function X.play(playerGui)
	if active and active.Parent then active:Destroy() end
	local reduce = okUI and UI and UI.reduceMotion and UI.reduceMotion() or false
	local gui = new("ScreenGui", { Name = "CC_XRay", IgnoreGuiInset = true, ResetOnSpawn = true, DisplayOrder = 72,
		ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, playerGui)
	active = gui
	local home = UDim2.new(1, -36, 0.46, 0)
	local panel = new("CanvasGroup", { Name = "Film", AnchorPoint = Vector2.new(1, 0.5), Position = home + UDim2.fromOffset(60, 0),
		Size = UDim2.fromOffset(W, H), BackgroundColor3 = FILM, BorderSizePixel = 0, GroupTransparency = 1 }, gui)
	new("UICorner", { CornerRadius = UDim.new(0, 6) }, panel)
	new("UIStroke", { Color = Color3.fromRGB(70, 92, 118), Thickness = 1, Transparency = 0.2 }, panel)
	-- Weichteil-Schatten des Arms: weiche Raender (kein harter Streifen)
	local flesh = new("Frame", { AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromOffset(W / 2, -20), Size = UDim2.fromOffset(190, H + 40),
		BackgroundColor3 = Color3.fromRGB(110, 128, 148), BackgroundTransparency = 0, BorderSizePixel = 0 }, panel)
	new("UIGradient", { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.25, 0.86),
		NumberSequenceKeypoint.new(0.5, 0.82), NumberSequenceKeypoint.new(0.75, 0.86), NumberSequenceKeypoint.new(1, 1) }) }, flesh)
	-- Vignette oben/unten wie auf einem Roentgenfilm
	for _, top in ipairs({ true, false }) do
		local v = new("Frame", { Position = top and UDim2.new() or UDim2.new(0, 0, 1, -70), Size = UDim2.new(1, 0, 0, 70), BackgroundColor3 = FILM,
			BorderSizePixel = 0, ZIndex = 3 }, panel)
		new("UIGradient", { Rotation = 90, Transparency = NumberSequence.new(top and 0 or 1, top and 1 or 0) }, v)
	end
	-- Oberarm (Humerus): Schaft, zur Bruchstelle hin breiter werdend
	local CRACK = 182
	bone(panel, W / 2, 96, 40, 200, 0, 18)
	bone(panel, W / 2, CRACK - 10, 52, 30, 0, 12)
	-- Unterer Teil als eigene Gruppe, dreht um die Bruchstelle (CanvasGroup dreht ihren Inhalt mit)
	local GH = 2 * (H + 20 - CRACK)
	local lower = new("CanvasGroup", { Name = "Lower", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromOffset(W / 2, CRACK),
		Size = UDim2.fromOffset(W, GH), BackgroundTransparency = 1 }, panel)
	local function ly(y) return GH / 2 + (y - CRACK) end
	bone(lower, W / 2, ly(200), 70, 36, 0, 16)                     -- unteres Oberarmende (Metaphyse)
	bone(lower, W / 2 - 24, ly(224), 46, 40, 0, 20)                -- Gelenkrolle innen
	bone(lower, W / 2 + 24, ly(224), 46, 40, 0, 20)                -- Gelenkrolle aussen
	bone(lower, W / 2 + 20, ly(252), 34, 30, 0, 14)                -- Olekranon (Ellenhaken)
	bone(lower, W / 2 - 24, ly(254), 30, 16, 0, 8)                 -- Speichenkopf
	bone(lower, W / 2 - 24, ly(338), 24, 160, -3, 12)              -- Speiche
	bone(lower, W / 2 + 19, ly(346), 22, 176, 2, 11)               -- Elle
	-- Schmerzpunkt am Bruch (anfangs unsichtbar)
	local hurt = new("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromOffset(W / 2, CRACK), Size = UDim2.fromOffset(120, 120),
		BackgroundColor3 = Color3.fromRGB(255, 40, 40), BackgroundTransparency = 1, BorderSizePixel = 0, ZIndex = 3 }, panel)
	new("UICorner", { CornerRadius = UDim.new(1, 0) }, hurt)
	-- Riss (anfangs unsichtbar): dunkle Zickzack-Spalte mit hellem Rand
	local crack = {}
	local pts = { { -26, -3 }, { -12, 4 }, { 0, -4 }, { 12, 5 }, { 26, -2 } }
	for i = 1, #pts - 1 do
		local a, b = pts[i], pts[i + 1]
		local dx, dy = b[1] - a[1], b[2] - a[2]
		local len = math.sqrt(dx * dx + dy * dy)
		local seg = new("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromOffset(W / 2 + (a[1] + b[1]) / 2, CRACK + (a[2] + b[2]) / 2),
			Size = UDim2.fromOffset(len + 2, 4), Rotation = math.deg(math.atan2(dy, dx)), BackgroundColor3 = FILM, BackgroundTransparency = 1,
			BorderSizePixel = 0, ZIndex = 4 }, panel)
		new("UIStroke", { Color = Color3.fromRGB(255, 255, 255), Thickness = 1, Transparency = 1 }, seg)
		table.insert(crack, seg)
	end
	-- Beschriftung wie auf einem Roentgenbild
	new("TextLabel", { Text = "X-RAY  ·  R ELBOW", Font = Enum.Font.GothamBold, TextSize = 12, TextColor3 = Color3.fromRGB(200, 214, 230),
		TextXAlignment = Enum.TextXAlignment.Left, BackgroundTransparency = 1, Position = UDim2.fromOffset(14, 10), Size = UDim2.fromOffset(200, 16), ZIndex = 5 }, panel)
	local tag = new("TextLabel", { Text = "ELBOW FRACTURE", Font = Enum.Font.GothamBlack, TextSize = 18, TextColor3 = Color3.new(1, 1, 1),
		BackgroundColor3 = Color3.fromRGB(200, 30, 36), BackgroundTransparency = 1, TextTransparency = 1, AnchorPoint = Vector2.new(0.5, 1),
		Position = UDim2.new(0.5, 0, 1, -14), Size = UDim2.fromOffset(196, 32), ZIndex = 6 }, panel)
	new("UICorner", { CornerRadius = UDim.new(0, 4) }, tag)
	local scan = new("Frame", { Position = UDim2.fromOffset(0, -4), Size = UDim2.new(1, 0, 0, 3), BackgroundColor3 = Color3.fromRGB(170, 220, 255),
		BackgroundTransparency = 0.35, BorderSizePixel = 0, ZIndex = 5 }, panel)
	local flash = new("Frame", { Size = UDim2.fromScale(1, 1), BackgroundColor3 = Color3.new(1, 1, 1), BackgroundTransparency = 1, BorderSizePixel = 0, ZIndex = 7 }, panel)

	task.spawn(function()
		local function alive() return gui.Parent ~= nil end
		tween(panel, 0.18, { GroupTransparency = 0, Position = home })
		tween(scan, 0.4, { Position = UDim2.new(0, 0, 1, 0) }, Enum.EasingStyle.Linear)
		task.wait(0.42); if not alive() then return end
		scan.Visible = false
		tween(lower, 0.3, { Rotation = -5 }, Enum.EasingStyle.Sine, Enum.EasingDirection.In)          -- Ueberstreckung unter Last
		task.wait(0.32); if not alive() then return end
		-- Bruch
		lower.Rotation = 9; lower.Position = UDim2.fromOffset(W / 2 + 9, CRACK + 5)
		for _, seg in ipairs(crack) do seg.BackgroundTransparency = 0; seg:FindFirstChildOfClass("UIStroke").Transparency = 0.15 end
		flash.BackgroundTransparency = 0.25
		tween(flash, 0.35, { BackgroundTransparency = 1 })
		hurt.BackgroundTransparency = 0.45
		tween(hurt, 0.7, { BackgroundTransparency = 0.82, Size = UDim2.fromOffset(150, 150) })
		for i = 1, 4 do                                                                             -- Splitter
			local chip = new("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromOffset(W / 2 + (i - 2.5) * 12, CRACK),
				Size = UDim2.fromOffset(5 + i % 2 * 3, 4), Rotation = i * 37, BackgroundColor3 = BONE, BorderSizePixel = 0, ZIndex = 5 }, panel)
			tween(chip, 0.45, { Position = UDim2.fromOffset(W / 2 + (i - 2.5) * 34, CRACK + (i % 2 == 0 and -18 or 16)), Rotation = i * 37 + 120, BackgroundTransparency = 0.6 })
		end
		if not reduce then
			for k = 1, 7 do
				panel.Position = home + UDim2.fromOffset(math.random(-6, 6), math.random(-4, 4))
				task.wait(0.03)
			end
			panel.Position = home
		end
		tag.BackgroundTransparency = 0; tween(tag, 0.15, { TextTransparency = 0 })
		task.wait(1.15); if not alive() then return end
		local out = tween(panel, 0.3, { GroupTransparency = 1, Position = home + UDim2.fromOffset(60, 0) })
		out.Completed:Wait()
		if gui.Parent then gui:Destroy() end
	end)
	return gui
end

function X.stop()
	if active and active.Parent then active:Destroy() end
	active = nil
end

return X
