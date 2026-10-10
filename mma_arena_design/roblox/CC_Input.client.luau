-- StarterPlayer.StarterPlayerScripts.CC_Input
-- Eingaben fuer PC, Controller und Touch (ContextActionService) + Gegner-Anvisierung.
--   PC:         Linksklick Jab · Rechtsklick Cross (mit Umschalttaste: zum Koerper) · Q Haken · R Aufwaertshaken · C Low Kick · F halten Block/Sprawl
--               E Takedown · Leertaste Befreien/Aufstehen (am Boden) · T oder mittlere Maustaste = Anvisieren an/aus
--               X Body Kick · V High Kick · Z Front Kick
--   Controller: X Jab · Y Cross · B Haken · R1 Aufwaertshaken · R2 Low Kick · L2 halten Block/Sprawl · L1 Takedown
--               A Befreien (am Boden, sonst Springen) · R3 Anvisieren an/aus
--   Touch:      Bildschirm-Knoepfe fuer Jab, Cross, Haken, Block, Takedown, Anvisieren
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

local function inWrestle() local c = player.Character; return c and c:GetAttribute("CC_Wrestle") end
local UIS = game:GetService("UserInputService")
local BODY = { jab = "jabBody", cross = "crossBody" }   -- mit gehaltener Umschalttaste zum Koerper
local function bindMove(name, move, touch, ...)
	CAS:BindAction(name, function(_, state)
		if state == Enum.UserInputState.Begin then
			local m = move
			if BODY[m] and (UIS:IsKeyDown(Enum.KeyCode.LeftShift) or UIS:IsKeyDown(Enum.KeyCode.RightShift)) then m = BODY[m] end
			action:FireServer(m)
		end
		return Enum.ContextActionResult.Pass
	end, touch, ...)
	if touch then CAS:SetTitle(name, ({ jab = "Jab", cross = "Cross", hook = "Haken", takedown = "TD" })[move] or move) end
end
bindMove("CC_Jab", "jab", true, Enum.UserInputType.MouseButton1, Enum.KeyCode.ButtonX)
bindMove("CC_Cross", "cross", true, Enum.UserInputType.MouseButton2, Enum.KeyCode.ButtonY)
bindMove("CC_Hook", "hook", true, Enum.KeyCode.Q, Enum.KeyCode.ButtonB)
bindMove("CC_Uppercut", "uppercut", false, Enum.KeyCode.R, Enum.KeyCode.ButtonR1)
bindMove("CC_LowKick", "lowkick", false, Enum.KeyCode.C, Enum.KeyCode.ButtonR2)
bindMove("CC_BodyKick", "bodykick", false, Enum.KeyCode.X)
bindMove("CC_HighKick", "highkick", false, Enum.KeyCode.V)
bindMove("CC_FrontKick", "frontkick", false, Enum.KeyCode.Z)
bindMove("CC_Takedown", "takedown", true, Enum.KeyCode.E, Enum.KeyCode.ButtonL1)

CAS:BindAction("CC_Block", function(_, state)
	if state == Enum.UserInputState.Begin then block:FireServer(true)
	elseif state == Enum.UserInputState.End or state == Enum.UserInputState.Cancel then block:FireServer(false) end
	return Enum.ContextActionResult.Pass
end, true, Enum.KeyCode.F, Enum.KeyCode.ButtonL2)
CAS:SetTitle("CC_Block", "Block")

-- Befreien/Aufstehen nur am Boden; sonst bleibt Leertaste/A normales Springen
CAS:BindAction("CC_Escape", function(_, state)
	if state == Enum.UserInputState.Begin and inWrestle() then action:FireServer("escape"); return Enum.ContextActionResult.Sink end
	return Enum.ContextActionResult.Pass
end, false, Enum.KeyCode.Space, Enum.KeyCode.ButtonA)

CAS:BindAction("CC_Lock", function(_, state)
	if state == Enum.UserInputState.Begin then lockWanted = not lockWanted end
	return Enum.ContextActionResult.Pass
end, true, Enum.KeyCode.T, Enum.UserInputType.MouseButton3, Enum.KeyCode.ButtonR3)
CAS:SetTitle("CC_Lock", "Ziel")

local function findOpponent(root)
	local best, bestDist = nil, LOCK_RANGE
	for _, m in ipairs(workspace:GetChildren()) do
		local h = m:IsA("Model") and m ~= player.Character and m:FindFirstChildOfClass("Humanoid")
		local r = h and m:FindFirstChild("HumanoidRootPart")
		if r and not m:GetAttribute("CC_KO") then
			local d = (r.Position - root.Position).Magnitude
			if d < bestDist then best, bestDist = m, d end
		end
	end
	return best
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
RunService.RenderStepped:Connect(function(dt)
	local char = player.Character
	local hum = char and char:FindFirstChildOfClass("Humanoid")
	local root = char and char:FindFirstChild("HumanoidRootPart")
	if not (hum and root) then return end
	if inWrestle() or char:GetAttribute("CC_KO") then
		hum.AutoRotate = false
		char:SetAttribute("CC_LockTarget", inWrestle() and (current and current.Name or "") or "")
		return
	end
	-- Ziel pruefen / loesen / neu aufnehmen
	if current and (not current.Parent or current:GetAttribute("CC_KO") or not current:FindFirstChild("HumanoidRootPart")
		or (current.HumanoidRootPart.Position - root.Position).Magnitude > LOCK_RANGE + 5) then
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
