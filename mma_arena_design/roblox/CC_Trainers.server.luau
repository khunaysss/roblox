-- ServerScriptService.CC_Trainers
-- Stellt die sechs Stil-Trainer (ServerStorage.CC_StyleTrainers aus setup_trainers_v01) verteilt an passende Trainingsbereiche im Gym.
-- Mit E ansprechen: Das Client-Panel zeigt Stil, Signatur und die gespeicherten Stil-Quests.
-- "Quest starten" aktiviert den Fortschritt; nach allen Aufgaben startet "Trainer herausfordern" einen Champion-Endkampf.
-- Erst ein Sieg im Trainerkampf schaltet die Signatur frei und ruestet sie aus. Freigeschaltete Signaturen koennen hier
-- gewechselt oder abgelegt werden (CC_Profile "sig_equip"). Trainer-Vorfuehrungen und globale Ranked-Regeln folgen spaeter.
local RS, SS = game:GetService("ReplicatedStorage"), game:GetService("ServerStorage")
local SIG = require(RS:WaitForChild("CC_Signatures"))
local SIGPROG = require(RS:WaitForChild("CC_SignatureProgression"))

local INFO = {   -- Reihenfolge = feste Zonen im Gym; sig = Schluessel in CC_Signatures.list
	{ id = "Mike_Tyson", name = "Mike Tyson", style = "Peek-a-boo Boxen", sig = "tyson", move = "Linker Koerperhaken + rechter Uppercut" },
	{ id = "Muhammad_Ali", name = "Muhammad Ali", style = "Tänzelndes Boxen", sig = "ali", move = "Instinkt-Modus: automatisch ausweichen, Calf Kick" },
	{ id = "Alex_Pereira", name = "Alex Pereira", style = "Kickboxen", sig = "pereira", move = "Linker Konterhaken" },
	{ id = "Khabib_Nurmagomedov", name = "Khabib Nurmagomedov", style = "Ringen", sig = "khabib", move = "Double-Leg-Takedown" },
	{ id = "Saenchai", name = "Saenchai", style = "Muay Thai", sig = "saenchai", move = "Rad-Kick: Cartwheel Kick zum Kopf" },
	{ id = "Charles_Oliveira", name = "Charles Oliveira", style = "Muay Thai / BJJ", sig = "oliveira", move = "Harter Koerperkick" },
}
local POSITIONS = { -- Lobby V10: Trainer bleiben an freien Wegen und nahe ihren Trainingsbereichen
	{ pos = Vector3.new(100, 0, 16), look = Vector3.new(91, 0, 12) },   -- Tyson: Boxsäcke
	{ pos = Vector3.new(214, 0, 29), look = Vector3.new(223, 0, 31) }, -- Ali: Cardio / Footwork
	{ pos = Vector3.new(103, 0, -4), look = Vector3.new(92, 0, 4) },   -- Pereira: Kickbox-Zone
	{ pos = Vector3.new(90, 0, -69), look = Vector3.new(105, 0, -68) }, -- Khabib: linke Grappling-Matte
	{ pos = Vector3.new(92, 0, -39), look = Vector3.new(105, 0, -42) }, -- Saenchai: Technik-Matten
	{ pos = Vector3.new(125, 0, -69), look = Vector3.new(108, 0, -68) }, -- Oliveira: rechte Grappling-Matte
}

local panel = RS:FindFirstChild("CC_TrainerPanel") or Instance.new("RemoteEvent"); panel.Name = "CC_TrainerPanel"; panel.Parent = RS

local function groundAt(x, z, ignore)
	local rp = RaycastParams.new(); rp.FilterType = Enum.RaycastFilterType.Exclude; rp.FilterDescendantsInstances = ignore
	local hit = workspace:Raycast(Vector3.new(x, 12, z), Vector3.new(0, -40, 0), rp)
	return hit and hit.Position.Y or 0
end

local placed = false
local function place()
	local src = SS:FindFirstChild("CC_StyleTrainers")
	if placed or not src or not workspace:FindFirstChild("CC_GymInteractions") then return end
	placed = true
	local holder = Instance.new("Folder"); holder.Name = "CC_StyleTrainersGym"; holder.Parent = workspace
	for i, t in ipairs(INFO) do
		local tpl = src:FindFirstChild(t.id)
		if tpl then
			local m = tpl:Clone()
			local spot = POSITIONS[i]
			local x, z = spot.pos.X, spot.pos.Z
			local y = groundAt(x, z, { holder })
			m:PivotTo(CFrame.lookAt(Vector3.new(x, y, z), Vector3.new(spot.look.X, y, spot.look.Z)))
			m.Parent = holder
			local pr = Instance.new("ProximityPrompt")
			pr.ObjectText = t.name; pr.ActionText = "Sprechen"; pr.KeyboardKeyCode = Enum.KeyCode.E; pr.GamepadKeyCode = Enum.KeyCode.ButtonX
			pr.HoldDuration = 0; pr.MaxActivationDistance = 10; pr.RequiresLineOfSight = false
			pr.Parent = m.PrimaryPart
			pr.Triggered:Connect(function(p)
				local c = p.Character
				if not c or c:GetAttribute("CC_Opponent") or p:GetAttribute("CC_Minigame") then return end
				local def = t.sig and SIG.list[t.sig]
				panel:FireClient(p, "open", { id = t.id, name = t.name, style = t.style, move = t.move, sig = def and t.sig or nil,
					sigName = def and def.name or nil })
			end)
		end
	end
end
panel.OnServerEvent:Connect(function(p, action, sig)
	local pe = SS:FindFirstChild("CC_ProfileEvent")
	if type(sig) ~= "string" or not SIG.list[sig] or not SIGPROG.list[sig] or not pe then return end
	local unlocked = table.find(string.split(p:GetAttribute("CC_SigUnlocked") or "", ","), sig) ~= nil
	if action == "equip" and unlocked then
		pe:Fire(p, "sig_equip", sig)
	elseif action == "unequip" then
		pe:Fire(p, "sig_equip", "")
	elseif action == "start" and not unlocked then
		pe:Fire(p, "sig_start", sig)
	elseif action == "challenge" and not unlocked then
		local ok, data = pcall(function() return game:GetService("HttpService"):JSONDecode(p:GetAttribute("CC_SigProgress") or "{}") end)
		if ok and SIGPROG.ready(sig, data) then
			local be = SS:FindFirstChild("CC_MenuServer")
			-- Filmszene "challenge" (CC_TrainerScenes) zuerst, Kampf erst danach
			local scene = SS:FindFirstChild("CC_TrainerScenePlay")
			local wait = 0
			if scene then local ok, len = pcall(function() return scene:Invoke(p, SIGPROG.list[sig].trainerId, "challenge") end); wait = ok and tonumber(len) or 0 end
			if be then task.delay(wait, function() if p.Parent then be:Fire(p, "trainer", sig) end end) end
		else
			p:SetAttribute("CC_Notice", "Erledige zuerst alle Trainer-Quests.|" .. tostring(workspace:GetServerTimeNow()))
		end
	end
end)
task.spawn(function() task.wait(2); place() end)
SS.ChildAdded:Connect(function(c) if c.Name == "CC_StyleTrainers" then place() end end)
