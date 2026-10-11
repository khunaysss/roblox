-- StarterPlayer.StarterPlayerScripts.CC_Input
-- Eingaben fuer PC, Controller und Touch (ContextActionService) + Gegner-Anvisierung.
--   PC:         Linksklick Jab · Rechtsklick Cross (mit Umschalttaste: zum Koerper) · Q Haken · R Aufwaertshaken · C Low Kick · F halten Block/Sprawl
--               E Takedown · Leertaste Befreien/Aufstehen (am Boden) · T oder mittlere Maustaste = Anvisieren an/aus
--               X Body Kick · V High Kick · Z Front Kick
--   Controller: X Jab · Y Cross · B Haken · R1 Aufwaertshaken · R2 Low Kick · L2 halten Block/Sprawl · L1 Takedown
--               Steuerkreuz links Body Kick · rechts High Kick · unten Front Kick (oben ist bei Roblox fuer Menues reserviert)
--               A Befreien (am Boden, sonst Springen) · R3 Anvisieren an/aus
--   Am Boden (oben): E/L1 Position verbessern · Linksklick/X Schlag · Q/B Submission (Mount, Ruecken) · F/L2 Konter
--   Am Boden (unten): Leertaste/A befreien (haemmern im Submission-Duell) · F/L2 Konter
--   Touch:      Bildschirm-Knoepfe fuer Jab, Cross, Haken, Upper, Low, Kick, High, Block, Takedown, Anvisieren, Los (befreien)
-- Anvisierung: Kaempfer dreht sich weich zum Gegner (seitlich laufen = umkreisen). Loest sich automatisch, wenn der
-- Gegner weg, K.o. oder weiter als 40 Studs entfernt ist; wird wieder aufgenommen, sobald er verfuegbar ist.
-- Zustand fuer die Kamera: Attribut CC_LockTarget (Modellname oder leer) am eigenen Charakter.
local Players = game:GetService("Players")
local CAS = game:GetService("ContextActionService")
local RunService = game:GetService("RunService")
local action = game.ReplicatedStorage:WaitForChild("CC_Action")
local block = game.ReplicatedStorage:WaitForChild("CC_Block")
local player = Players.LocalPlayer

local lockWanted = true          -- Spieler-Einstellung (Standard: an)
local LOCK_RANGE = 40
local TURN_RATE = 14             -- wie schnell der Kaempfer zum Gegner dreht (1/s)

local function inWrestle() local c = player.Character; return c and (c:GetAttribute("CC_Wrestle") or c:GetAttribute("CC_Down")) end   -- Ringkampf oder Bodenlage
local UIS = game:GetService("UserInputService")
local BODY = { jab = "jabBody", cross = "crossBody" }   -- mit gehaltener Umschalttaste zum Koerper
local function bindMove(name, move, touch, ...)
	CAS:BindAction(name, function(_, state)
		if player:GetAttribute("CC_UIBlock") then return Enum.ContextActionResult.Pass end   -- Hauptmenue offen
		if state == Enum.UserInputState.Begin then
			local m = move
			if BODY[m] and (UIS:IsKeyDown(Enum.KeyCode.LeftShift) or UIS:IsKeyDown(Enum.KeyCode.RightShift)) then m = BODY[m] end
			action:FireServer(m)
		end
		return Enum.ContextActionResult.Pass
	end, touch, ...)
	if touch then CAS:SetTitle(name, ({ jab = "Jab", cross = "Cross", hook = "Haken", takedown = "TD", uppercut = "Upper", lowkick = "Low", bodykick = "Kick", highkick = "High" })[move] or move) end
end
bindMove("CC_Jab", "jab", true, Enum.UserInputType.MouseButton1, Enum.KeyCode.ButtonX)
bindMove("CC_Cross", "cross", true, Enum.UserInputType.MouseButton2, Enum.KeyCode.ButtonY)
bindMove("CC_Hook", "hook", true, Enum.KeyCode.Q, Enum.KeyCode.ButtonB)
bindMove("CC_Uppercut", "uppercut", true, Enum.KeyCode.R, Enum.KeyCode.ButtonR1)
bindMove("CC_LowKick", "lowkick", true, Enum.KeyCode.C, Enum.KeyCode.ButtonR2)
bindMove("CC_BodyKick", "bodykick", true, Enum.KeyCode.X, Enum.KeyCode.DPadLeft)
bindMove("CC_HighKick", "highkick", true, Enum.KeyCode.V, Enum.KeyCode.DPadRight)
bindMove("CC_FrontKick", "frontkick", false, Enum.KeyCode.Z, Enum.KeyCode.DPadDown)
bindMove("CC_Takedown", "takedown", true, Enum.KeyCode.E, Enum.KeyCode.ButtonL1)

CAS:BindAction("CC_Block", function(_, state)
	if state == Enum.UserInputState.Begin then block:FireServer(true)
	elseif state == Enum.UserInputState.End or state == Enum.UserInputState.Cancel then block:FireServer(false) end
	return Enum.ContextActionResult.Pass
end, true, Enum.KeyCode.F, Enum.KeyCode.ButtonL2)
CAS:SetTitle("CC_Block", "Block")

-- Befreien/Aufstehen nur am Boden. Im 1-gegen-1-Kampf (CC_Opponent) kein Springen: Leertaste/A wird dort geschluckt;
-- ausserhalb des Kampfs bleibt Leertaste/A normales Springen.
local function inFight() local c = player.Character; return c and c:GetAttribute("CC_Opponent") ~= nil end
CAS:BindAction("CC_Escape", function(_, state)
	if state == Enum.UserInputState.Begin and inWrestle() then action:FireServer("escape"); return Enum.ContextActionResult.Sink end
	if inFight() then return Enum.ContextActionResult.Sink end
	return Enum.ContextActionResult.Pass
end, true, Enum.KeyCode.Space, Enum.KeyCode.ButtonA)
CAS:SetTitle("CC_Escape", "Los")

CAS:BindAction("CC_Lock", function(_, state)
	if state == Enum.UserInputState.Begin then lockWanted = not lockWanted end
	return Enum.ContextActionResult.Pass
end, true, Enum.KeyCode.T, Enum.UserInputType.MouseButton3, Enum.KeyCode.ButtonR3)
CAS:SetTitle("CC_Lock", "Ziel")

-- Gegner = vom Kampf-System gesetztes Attribut CC_Opponent; in der Lobby (kein Kampf) wird nicht anvisiert
local function findOpponent(root)
	local c = player.Character
	local name = c and c:GetAttribute("CC_Opponent")
	if not name then return nil end
	local m = workspace:FindFirstChild(name)
	if m and m:FindFirstChild("HumanoidRootPart") and not m:GetAttribute("CC_KO") then return m end
	return nil
end

-- Bewegung bei Anvisierung: W/S = zum Gegner hin/weg, A/D = auf einem Kreis um den Gegner (Abstand bleibt).
-- Laeuft nach der Roblox-Steuerung (egal ob Tastatur, Controller oder Touch): liest deren Laufrichtung
-- (Humanoid.MoveDirection, kamerabezogen) und ueberschreibt sie. Kein PlayerModule noetig (fehlt in dieser Studio-Version).
local orbitRadius = nil
local current = nil
RunService:BindToRenderStep("CC_LockMove", Enum.RenderPriority.Input.Value + 1, function()
	local char = player.Character
	local hum = char and char:FindFirstChildOfClass("Humanoid")
	local root = char and char:FindFirstChild("HumanoidRootPart")
	if not (hum and root and current and current:FindFirstChild("HumanoidRootPart")) or inWrestle() then orbitRadius = nil; return end
	local md = hum.MoveDirection
	local cam = workspace.CurrentCamera
	local cf = Vector3.new(cam.CFrame.LookVector.X, 0, cam.CFrame.LookVector.Z); cf = cf.Magnitude > 0.01 and cf.Unit or Vector3.new(0, 0, -1)
	local cr = Vector3.new(-cf.Z, 0, cf.X)
	local mv = Vector3.new(md:Dot(cr), 0, -md:Dot(cf))     -- x = rechts, z = -vorwaerts (bezogen auf die Kamera)
	local tp = current.HumanoidRootPart.Position
	local toT = Vector3.new(tp.X - root.Position.X, 0, tp.Z - root.Position.Z)
	local r = toT.Magnitude
	if r < 0.5 or mv.Magnitude < 0.05 then orbitRadius = nil; return end
	local t = toT.Unit
	local right = Vector3.new(-t.Z, 0, t.X)
	local fwdIn, sideIn = -mv.Z, mv.X
	if math.abs(fwdIn) > 0.2 or not orbitRadius then orbitRadius = r end   -- Radius merken, solange nur seitlich gelaufen wird
	local dir = t * fwdIn + right * sideIn
	if math.abs(fwdIn) <= 0.2 and math.abs(sideIn) > 0.2 then
		dir += t * math.clamp((r - orbitRadius) * 1.5, -0.6, 0.6)            -- Abdriften nach aussen ausgleichen
	end
	if dir.Magnitude > 0.01 then hum:Move(dir.Unit * math.min(mv.Magnitude, 1), false) end
end)
-- Locker-Modus (kein Kampf): normales Gehtempo, Umschalttaste bzw. linker Stick gedrueckt = Laufen.
-- Waehrend Uebungen (verankert) und eingefroren nichts aendern.
local CASUAL_WALK, CASUAL_RUN = 6.4, 15
local sprintPad = false
UIS.InputBegan:Connect(function(i) if i.KeyCode == Enum.KeyCode.ButtonL3 then sprintPad = not sprintPad end end)
RunService.RenderStepped:Connect(function(dt)
	local char = player.Character
	local hum = char and char:FindFirstChildOfClass("Humanoid")
	local root = char and char:FindFirstChild("HumanoidRootPart")
	if not (hum and root) then return end
	-- Springen im Kampf aus (auch Touch-Sprungknopf und Controller); ausserhalb wieder an (ausser das Hauptmenue sperrt)
	local noJump = char:GetAttribute("CC_Opponent") ~= nil or player:GetAttribute("CC_UIBlock") ~= nil
	if hum:GetStateEnabled(Enum.HumanoidStateType.Jumping) == noJump then hum:SetStateEnabled(Enum.HumanoidStateType.Jumping, not noJump) end
	if noJump and hum.Jump then hum.Jump = false end
	if not char:GetAttribute("CC_Opponent") and not inWrestle() and not root.Anchored and not char:GetAttribute("CC_Frozen") and not player:GetAttribute("CC_UIBlock") then
		local sprint = UIS:IsKeyDown(Enum.KeyCode.LeftShift) or sprintPad
		local want = sprint and CASUAL_RUN or CASUAL_WALK
		if hum.WalkSpeed ~= want then hum.WalkSpeed = want end
		if hum.MoveDirection.Magnitude < 0.1 then sprintPad = false end
	end
	if inWrestle() or char:GetAttribute("CC_KO") then
		hum.AutoRotate = false
		char:SetAttribute("CC_LockTarget", inWrestle() and (current and current.Name or "") or "")
		return
	end
	-- Ziel pruefen / loesen / neu aufnehmen
	if current and (not current.Parent or current:GetAttribute("CC_KO") or not current:FindFirstChild("HumanoidRootPart")
		or (current.HumanoidRootPart.Position - root.Position).Magnitude > LOCK_RANGE + 5 or current.Name ~= char:GetAttribute("CC_Opponent")) then
		current = nil
	end
	if lockWanted and not current then current = findOpponent(root) end
	if not lockWanted then current = nil end
	char:SetAttribute("CC_LockTarget", current and current.Name or "")
	hum.AutoRotate = current == nil
	if current and not root.Anchored then
		local tp = current.HumanoidRootPart.Position
		local flat = Vector3.new(tp.X - root.Position.X, 0, tp.Z - root.Position.Z)
		if flat.Magnitude > 0.5 then
			local goal = CFrame.lookAt(root.Position, root.Position + flat)
			root.CFrame = root.CFrame:Lerp(goal, 1 - math.exp(-TURN_RATE * dt))
		end
	end
end)
