-- StarterGui.CC_HUD (LocalScript in einer ScreenGui)
-- Zwei Lebensbalken oben: Spieler links (rot), Trainingsgegner rechts (blau). K.o.-Hinweis in der Mitte.
local player = game.Players.LocalPlayer
local gui = script.Parent

local function bar(name, anchorX, color, label)
	local frame = Instance.new("Frame")
	frame.Name = name
	frame.AnchorPoint = Vector2.new(anchorX, 0)
	frame.Position = UDim2.new(anchorX, anchorX == 0 and 20 or -20, 0, 20)
	frame.Size = UDim2.fromOffset(320, 26)
	frame.BackgroundColor3 = Color3.fromRGB(25, 25, 28)
	frame.BorderSizePixel = 0
	frame.Parent = gui
	local fill = Instance.new("Frame")
	fill.Name = "Fill"
	fill.AnchorPoint = Vector2.new(anchorX, 0)
	fill.Position = UDim2.fromScale(anchorX, 0)
	fill.Size = UDim2.fromScale(1, 1)
	fill.BackgroundColor3 = color
	fill.BorderSizePixel = 0
	fill.Parent = frame
	local text = Instance.new("TextLabel")
	text.BackgroundTransparency = 1
	text.Size = UDim2.fromScale(1, 1)
	text.Font = Enum.Font.GothamBold
	text.TextSize = 16
	text.TextColor3 = Color3.new(1, 1, 1)
	text.TextStrokeTransparency = 0.5
	text.Text = label
	text.Parent = frame
	return fill
end

local myFill = bar("Player", 0, Color3.fromRGB(200, 40, 50), "DU")
local foeFill = bar("Opponent", 1, Color3.fromRGB(40, 90, 200), "GEGNER")
-- Ausdauer: gelber Balken unter den Lebensbalken, mit Beschriftung; wird bei wenig Ausdauer rot und blinkt
local function sbar(anchorX)
	local frame = Instance.new("Frame")
	frame.AnchorPoint = Vector2.new(anchorX, 0)
	frame.Position = UDim2.new(anchorX, anchorX == 0 and 20 or -20, 0, 50)
	frame.Size = UDim2.fromOffset(320, 14); frame.BackgroundColor3 = Color3.fromRGB(25, 25, 28); frame.BorderSizePixel = 0; frame.Parent = gui
	local fill = Instance.new("Frame"); fill.AnchorPoint = Vector2.new(anchorX, 0); fill.Position = UDim2.fromScale(anchorX, 0)
	fill.Size = UDim2.fromScale(1, 1); fill.BackgroundColor3 = Color3.fromRGB(240, 200, 40); fill.BorderSizePixel = 0; fill.Parent = frame
	local t = Instance.new("TextLabel"); t.Name = "Label"; t.BackgroundTransparency = 1; t.Size = UDim2.fromScale(1, 1); t.ZIndex = 2
	t.Font = Enum.Font.GothamBold; t.TextSize = 11; t.TextColor3 = Color3.new(1, 1, 1); t.TextStrokeTransparency = 0.4; t.Text = "AUSDAUER"; t.Parent = frame
	return fill, t
end
local myStam, myStamL = sbar(0)
local foeStam = sbar(1)
-- Zustand unter der eigenen Ausdauer: BLOCK / WENIG AUSDAUER
local stateL = Instance.new("TextLabel")
stateL.Position = UDim2.fromOffset(20, 84); stateL.Size = UDim2.fromOffset(320, 22); stateL.BackgroundTransparency = 1
stateL.Font = Enum.Font.GothamBlack; stateL.TextSize = 18; stateL.TextXAlignment = Enum.TextXAlignment.Left
stateL.TextStrokeTransparency = 0.3; stateL.Text = ""; stateL.Parent = gui
local LOW_STAMINA = 25   -- wie im Kampfskript: darunter weniger Schaden und langsamere Schlaege
-- Signatur-Fokus (CC_Signatures): schmaler Balken unter der Ausdauer, nur mit ausgeruesteter Signatur; voll = gold + Taste G
local SIGCFG = require(game.ReplicatedStorage:WaitForChild("CC_Signatures"))
local focusF = Instance.new("Frame"); focusF.Position = UDim2.fromOffset(20, 68); focusF.Size = UDim2.fromOffset(320, 10)
focusF.BackgroundColor3 = Color3.fromRGB(25, 25, 28); focusF.BorderSizePixel = 0; focusF.Visible = false; focusF.Parent = gui
local focusFill = Instance.new("Frame"); focusFill.Size = UDim2.fromScale(0, 1); focusFill.BorderSizePixel = 0; focusFill.BackgroundColor3 = Color3.fromRGB(150, 20, 28); focusFill.Parent = focusF
local focusL = Instance.new("TextLabel"); focusL.BackgroundTransparency = 1; focusL.Size = UDim2.fromScale(1, 1); focusL.ZIndex = 2; focusL.Font = Enum.Font.GothamBold
focusL.TextSize = 10; focusL.TextColor3 = Color3.new(1, 1, 1); focusL.TextStrokeTransparency = 0.4; focusL.Text = "FOKUS"; focusL.Parent = focusF
local function sigEquipped() local id = workspace:GetAttribute(SIGCFG.TEST_ATTR) or player:GetAttribute("CC_SigTrial") or player:GetAttribute("CC_Signature"); return id and SIGCFG.list[id] end

local ko = Instance.new("TextLabel")
ko.AnchorPoint = Vector2.new(0.5, 0.5)
ko.Position = UDim2.fromScale(0.5, 0.35)
ko.Size = UDim2.fromOffset(400, 80)
ko.BackgroundTransparency = 1
ko.Font = Enum.Font.GothamBlack
ko.TextSize = 64
ko.TextColor3 = Color3.fromRGB(255, 220, 60)
ko.TextStrokeTransparency = 0
ko.Text = "K.O.!"
ko.Visible = false
ko.Parent = gui

local hint = Instance.new("TextLabel")
hint.AnchorPoint = Vector2.new(0.5, 1)
hint.Position = UDim2.new(0.5, 0, 1, -20)
hint.Size = UDim2.fromOffset(1200, 24)
hint.BackgroundTransparency = 1
hint.Font = Enum.Font.Gotham
hint.TextSize = 16
hint.TextColor3 = Color3.new(1, 1, 1)
hint.TextStrokeTransparency = 0.5
hint.Text = "WASD laufen · LMB Jab · RMB Cross (+Umschalt: Koerper) · Q Haken · R Uppercut · C/X/V/Z Kicks · F Block/Sprawl · E Takedown · T Ziel · Leertaste Aufstehen"
hint.Parent = gui
local HINT_STAND = hint.Text
-- Bodenkampf: Hinweise je Position und Rolle; Submission-Duell als Balken in der Mitte
local POS_NAME = { guard = "GUARD", half = "HALF GUARD", side = "SIDE CONTROL", mount = "MOUNT", back = "RUECKEN" }
local posL = Instance.new("TextLabel")
posL.AnchorPoint = Vector2.new(0.5, 1); posL.Position = UDim2.new(0.5, 0, 1, -48); posL.Size = UDim2.fromOffset(400, 30)
posL.BackgroundTransparency = 1; posL.Font = Enum.Font.GothamBlack; posL.TextSize = 24; posL.TextColor3 = Color3.fromRGB(255, 220, 60)
posL.TextStrokeTransparency = 0.3; posL.Text = ""; posL.Parent = gui
local duel = Instance.new("Frame")
duel.AnchorPoint = Vector2.new(0.5, 0.5); duel.Position = UDim2.fromScale(0.5, 0.62); duel.Size = UDim2.fromOffset(420, 22)
duel.BackgroundColor3 = Color3.fromRGB(40, 90, 200); duel.BorderSizePixel = 0; duel.Visible = false; duel.Parent = gui
local duelFill = Instance.new("Frame"); duelFill.Size = UDim2.fromScale(0.35, 1); duelFill.BackgroundColor3 = Color3.fromRGB(200, 40, 50)
duelFill.BorderSizePixel = 0; duelFill.Parent = duel
local duelL = Instance.new("TextLabel"); duelL.AnchorPoint = Vector2.new(0.5, 1); duelL.Position = UDim2.new(0.5, 0, 0, -4); duelL.Size = UDim2.fromOffset(600, 30)
duelL.BackgroundTransparency = 1; duelL.Font = Enum.Font.GothamBlack; duelL.TextSize = 24; duelL.TextColor3 = Color3.new(1, 1, 1)
duelL.TextStrokeTransparency = 0.2; duelL.Parent = duel
local DOWN_NAME = { back = "RÜCKENLAGE", side = "SEITENLAGE", seated = "SITZEND", kneel = "KNIEND" }
local function groundHint(char)
	local down = char:GetAttribute("CC_Down")
	if down then
		local t = { "Leertaste Aufstehen" }
		if down ~= "kneel" then table.insert(t, "E höher (Seite/Sitzen/Knien)") end
		if down == "back" then table.insert(t, "LMB Stoßtritt"); table.insert(t, "C Beintritt") end
		table.insert(t, "F Block")
		return table.concat(t, " · ")
	end
	local oppName = char:GetAttribute("CC_Opponent")
	local opp = oppName and workspace:FindFirstChild(oppName)
	if opp and opp:GetAttribute("CC_Down") and not char:GetAttribute("CC_Wrestle") then
		return "Gegner am Boden: C Low Kick auf die Beine" .. (opp:GetAttribute("CC_Down") == "back" and " · E in die Guard" or "")
	end
	local role, pos = char:GetAttribute("CC_Wrestle"), char:GetAttribute("CC_GroundPos")
	if not role or not pos then return nil end
	if role == "top" then
		local t = {}
		if pos ~= "back" then table.insert(t, "E Position verbessern") end
		if pos == "guard" or pos == "mount" then table.insert(t, "LMB Schlag") end
		if pos == "mount" or pos == "back" then table.insert(t, "Q Submission") end
		table.insert(t, "F Konter"); if pos == "guard" then table.insert(t, "Leertaste Aufstehen (Gegner bleibt liegen)") end
		return table.concat(t, " · ")
	end
	return (pos == "guard" and "Leertaste Aufstehen" or "Leertaste Befreien") .. " · F Konter (wenn der Gegner die Position wechselt)"
end

-- Rundenanzeige oben mittig: Runde, Zeit, Punkte; grosses Banner in der Mitte
local match = game.ReplicatedStorage:WaitForChild("CC_MatchState", 10)
local clock = Instance.new("Frame")
clock.AnchorPoint = Vector2.new(0.5, 0); clock.Position = UDim2.new(0.5, 0, 0, 14); clock.Size = UDim2.fromOffset(190, 58)
clock.BackgroundColor3 = Color3.fromRGB(20, 20, 24); clock.BackgroundTransparency = 0.15; clock.BorderSizePixel = 0; clock.Parent = gui
local function label(parent, y, h, size, font)
	local l = Instance.new("TextLabel"); l.BackgroundTransparency = 1; l.Position = UDim2.new(0, 0, 0, y); l.Size = UDim2.new(1, 0, 0, h)
	l.Font = font; l.TextSize = size; l.TextColor3 = Color3.new(1, 1, 1); l.Parent = parent; return l
end
local roundL = label(clock, 2, 18, 14, Enum.Font.GothamBold)
local timeL = label(clock, 18, 26, 26, Enum.Font.GothamBlack)
local scoreL = label(clock, 42, 14, 12, Enum.Font.Gotham); scoreL.TextColor3 = Color3.fromRGB(200, 200, 205)
local banner = Instance.new("TextLabel")
banner.AnchorPoint = Vector2.new(0.5, 0.5); banner.Position = UDim2.fromScale(0.5, 0.3); banner.Size = UDim2.fromOffset(700, 90)
banner.BackgroundTransparency = 1; banner.Font = Enum.Font.GothamBlack; banner.TextSize = 72
banner.TextColor3 = Color3.fromRGB(255, 255, 255); banner.TextStrokeTransparency = 0; banner.Parent = gui
local bannerSub = Instance.new("TextLabel")
bannerSub.AnchorPoint = Vector2.new(0.5, 0); bannerSub.Position = UDim2.new(0.5, 0, 0.3, 46); bannerSub.Size = UDim2.fromOffset(700, 36)
bannerSub.BackgroundTransparency = 1; bannerSub.Font = Enum.Font.GothamBold; bannerSub.TextSize = 26
bannerSub.TextColor3 = Color3.fromRGB(255, 220, 60); bannerSub.TextStrokeTransparency = 0.3; bannerSub.Parent = gui

-- Hinweise: Training/Level/Werte (Attribute am Spieler von CC_Profile / CC_GymTraining)
local toast = Instance.new("TextLabel")
toast.AnchorPoint = Vector2.new(0.5, 0); toast.Position = UDim2.new(0.5, 0, 0, 92); toast.Size = UDim2.fromOffset(700, 34)
toast.BackgroundColor3 = Color3.fromRGB(18, 18, 22); toast.BackgroundTransparency = 0.25; toast.BorderSizePixel = 0
toast.Font = Enum.Font.GothamBold; toast.TextSize = 18; toast.TextColor3 = Color3.new(1, 1, 1); toast.Visible = false; toast.Parent = gui
Instance.new("UICorner", toast).CornerRadius = UDim.new(0, 8)
local toastUntil = 0
local function showToast(text, color)
	if true then return end   -- Meldungen zeigt jetzt CC_GymHUD (UI-Ueberarbeitung Schritt 2)
	toast.Text = text; toast.TextColor3 = color or Color3.new(1, 1, 1); toast.Visible = true; toastUntil = os.clock() + 3
end
local STAT_DE = { Power = "Schlagkraft", Cardio = "Kondition", Wrestling = "Ringen", Grappling = "Bodenkampf" }
player:GetAttributeChangedSignal("CC_Notice"):Connect(function()
	local t = player:GetAttribute("CC_Notice"); if t then showToast(t:match("^(.*)|") or t) end
end)
player:GetAttributeChangedSignal("CC_LevelUp"):Connect(function()
	showToast("LEVEL UP! Level " .. tostring(player:GetAttribute("CC_LevelUp")), Color3.fromRGB(255, 220, 60))
end)
player:GetAttributeChangedSignal("CC_StatUp"):Connect(function()
	local s_, v = tostring(player:GetAttribute("CC_StatUp")):match("^(%w+):(%d+)")
	if s_ then showToast((STAT_DE[s_] or s_) .. " steigt auf " .. v .. "!", Color3.fromRGB(120, 190, 255)) end
end)
local exBar = Instance.new("Frame")
exBar.AnchorPoint = Vector2.new(0.5, 0.5); exBar.Position = UDim2.fromScale(0.5, 0.7); exBar.Size = UDim2.fromOffset(360, 16)
exBar.BackgroundColor3 = Color3.fromRGB(30, 30, 34); exBar.BorderSizePixel = 0; exBar.Visible = false; exBar.Parent = gui
local exFill = Instance.new("Frame"); exFill.BackgroundColor3 = Color3.fromRGB(80, 200, 120); exFill.BorderSizePixel = 0; exFill.Parent = exBar
local exL = Instance.new("TextLabel"); exL.AnchorPoint = Vector2.new(0.5, 1); exL.Position = UDim2.new(0.5, 0, 0, -4); exL.Size = UDim2.fromOffset(360, 24)
exL.BackgroundTransparency = 1; exL.Font = Enum.Font.GothamBold; exL.TextSize = 18; exL.TextColor3 = Color3.new(1, 1, 1); exL.TextStrokeTransparency = 0.4; exL.Parent = exBar
game:GetService("RunService").RenderStepped:Connect(function()
	if toast.Visible and os.clock() > toastUntil then toast.Visible = false end
	local ex = player:GetAttribute("CC_Exercise")
	exBar.Visible = ex ~= nil
	if ex then
		local name, t0, dur = ex:match("^(.-)|([%d%.]+)|([%d%.]+)$")
		local k = (t0 and dur) and math.clamp((workspace:GetServerTimeNow() - tonumber(t0)) / tonumber(dur), 0, 1) or 0
		exFill.Size = UDim2.fromScale(k, 1); exL.Text = (name or "Training") .. " … (nicht bewegen)"
	end
end)
game:GetService("RunService").RenderStepped:Connect(function()
	local char = player.Character
	local hum = char and char:FindFirstChildOfClass("Humanoid")
	if hum then myFill.Size = UDim2.fromScale(math.clamp(hum.Health / hum.MaxHealth, 0, 1), 1) end
	-- Gegner = CC_Opponent (Kampf-System); ohne Kampf: Lobby (nur Uhr/Banner fuer Zuschauer)
	local oppName = char and char:GetAttribute("CC_Opponent")
	local dummy = oppName and workspace:FindFirstChild(oppName)
	local inMatch = dummy ~= nil
	local tut = match and match:GetAttribute("Mode") == "tutorial"         -- Tutorial: nur die eigene Ausdauer (kein Sieg/Niederlage), Platz fuer die Aufgabenkarte
	for _, b in ipairs({ myFill.Parent, foeFill.Parent, foeStam.Parent }) do b.Visible = inMatch and not tut end
	myStam.Parent.Visible = inMatch
	foeFill.Parent:FindFirstChildOfClass("TextLabel").Text = dummy and (dummy == workspace:FindFirstChild("CC_TrainingDummy") and "GEGNER" or string.upper(dummy.Name)) or "GEGNER"
	local dh = dummy and dummy:FindFirstChildOfClass("Humanoid")
	if dh then foeFill.Size = UDim2.fromScale(math.clamp(dh.Health / dh.MaxHealth, 0, 1), 1) end
	ko.Visible = (char and char:GetAttribute("CC_KO")) or (dummy and dummy:GetAttribute("CC_KO")) or false
	local loser = (char and char:GetAttribute("CC_KO")) and char or dummy
	ko.Text = (loser and loser:GetAttribute("CC_LastReact") == "submission") and "SUBMISSION!" or "K.O.!"
	if char then
		local stam = char:GetAttribute("CC_Stamina") or 100
		myStam.Size = UDim2.fromScale(math.clamp(stam / (char:GetAttribute("CC_StaminaMax") or 100), 0, 1), 1)
		local tired = char:GetAttribute("CC_Tired")
		local low = stam < LOW_STAMINA
		local blink = low and (os.clock() * 3) % 1 < 0.5
		myStam.BackgroundColor3 = ((tired and workspace:GetServerTimeNow() - tired < 0.4) or blink) and Color3.fromRGB(255, 80, 60) or Color3.fromRGB(240, 200, 40)
		myStamL.Text = "AUSDAUER " .. math.floor(stam + 0.5)
		local sdef = sigEquipped()
		local fo = char:GetAttribute("CC_Focus") or 0
		focusF.Visible = inMatch and not tut and sdef ~= nil
		focusFill.Size = UDim2.fromScale(math.clamp(fo / SIGCFG.FOCUS_MAX, 0, 1), 1)
		local full = fo >= SIGCFG.FOCUS_MAX
		focusFill.BackgroundColor3 = full and Color3.fromRGB(236, 190, 76) or Color3.fromRGB(150, 20, 28)
		focusL.Text = full and ("G  " .. (sdef and sdef.name or "SIGNATUR")) or "FOKUS"
		local blocking = char:GetAttribute("CC_Block")
		stateL.Visible = inMatch and not tut
		stateL.Text = blocking and "BLOCK" or (low and "WENIG AUSDAUER" or "")
		stateL.TextColor3 = blocking and Color3.fromRGB(120, 190, 255) or Color3.fromRGB(255, 90, 70)
	end
	if char then
		local gh = groundHint(char)
		local guided = match and (match:GetAttribute("Mode") == "tutorial" or match:GetAttribute("Mode") == "sparring")   -- Einstieg: keine volle Tastenleiste (CC_Tutorial)
		hint.Text = gh or ((inMatch and not guided) and (HINT_STAND .. (sigEquipped() and " · G Signatur" or "")) or "")
		posL.Text = gh and (POS_NAME[char:GetAttribute("CC_GroundPos")] or DOWN_NAME[char:GetAttribute("CC_Down")] or "") or ""
		local p = char:GetAttribute("CC_SubProgress")
		duel.Visible = p ~= nil
		if p then
			duelFill.Size = UDim2.fromScale(p, 1)
			local mine = char:GetAttribute("CC_SubRole") == "attack"
			duelL.Text = (char:GetAttribute("CC_SubName") or "SUBMISSION") .. (mine and "  –  Q haemmern!" or "  –  Leertaste haemmern!")
		end
	end
	if dummy then foeStam.Size = UDim2.fromScale(math.clamp((dummy:GetAttribute("CC_Stamina") or 100) / (dummy:GetAttribute("CC_StaminaMax") or 100), 0, 1), 1) end
	if match then
		local st, t = match:GetAttribute("State"), match:GetAttribute("TimeLeft") or 0
		roundL.Text = st == "over" and "ENDE" or ("RUNDE " .. tostring(match:GetAttribute("Round") or 1) .. " / " .. tostring(match:GetAttribute("Rounds") or 3))
		timeL.Text = st == "fight" and string.format("%d:%02d", t // 60, t % 60) or (st == "break" and "PAUSE" or "--:--")
		scoreL.Text = string.format("Punkte  %d : %d", match:GetAttribute("ScoreRed") or 0, match:GetAttribute("ScoreBlue") or 0)
		banner.Text = match:GetAttribute("Banner") or ""
		-- Kaempfer sehen ihr eigenes Ergebnis; Zuschauer den Servertext ("<Name> GEWINNT")
		local me = player.Name
		local fighter = me == match:GetAttribute("RedName") or me == match:GetAttribute("BlueName")
		if st == "over" and fighter and match:GetAttribute("Winner") ~= "draw" then banner.Text = match:GetAttribute("WinnerName") == me and "SIEG" or "NIEDERLAGE" end
		local w = match:GetAttribute("Winner")
		banner.TextColor3 = (st == "over" and w == "red") and Color3.fromRGB(255, 215, 70) or (st == "over" and w == "blue") and Color3.fromRGB(120, 160, 255) or Color3.new(1, 1, 1)
		clock.Visible = st ~= "idle" and st ~= "tutorial"
		if fighter then
			local mine, theirs = match:GetAttribute("ScoreRed") or 0, match:GetAttribute("ScoreBlue") or 0
			if me == match:GetAttribute("BlueName") then mine, theirs = theirs, mine end
			scoreL.Text = string.format("Punkte  %d : %d", mine, theirs)
		end
		bannerSub.Text = match:GetAttribute("BannerSub") or ""
		if banner.Text ~= "" then ko.Visible = false end
	end
end)
