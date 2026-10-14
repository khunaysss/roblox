-- ServerScriptService.CC_Trainers
-- Stellt die sechs Stil-Trainer (ServerStorage.CC_StyleTrainers aus setup_trainers_v01) an die Ostseite des Gyms (neben dem Kaefig).
-- Mit E ansprechen: Panel mit Kampfstil und Signatur (CC_TrainerPanel am Client). Ist die Signatur fertig (CC_Signatures.list),
-- wird sie so freigeschaltet: "Lernen" startet die Uebung (Attribut CC_SigTrial, nur im Trainingskampf nutzbar). Landet der Spieler die
-- Kombination dort einmal sauber, schaltet CC_CharacterAnimations sie im Profil frei (CC_Profile "sig_unlock", wird gespeichert).
-- Freigeschaltete Signaturen hier ausruesten/ablegen (CC_Profile "sig_equip"). VORLAEUFIG: Vorfuehrung durch den Trainer fehlt
-- (Trainer-Modelle sind starr); Ranked-Regel folgt mit dem Ranked-Modus.
local RS, SS = game:GetService("ReplicatedStorage"), game:GetService("ServerStorage")
local SIG = require(RS:WaitForChild("CC_Signatures"))

local INFO = {   -- Reihenfolge = Plaetze von West nach Ost; sig = Schluessel in CC_Signatures.list (nil = noch nicht gebaut)
	{ id = "Mike_Tyson", name = "Mike Tyson", style = "Peek-a-boo Boxen", sig = "tyson", move = "Linker Koerperhaken + rechter Uppercut" },
	{ id = "Muhammad_Ali", name = "Muhammad Ali", style = "Tänzelndes Boxen", move = "Jab-Jab-Cross" },
	{ id = "Alex_Pereira", name = "Alex Pereira", style = "Kickboxen", move = "Linker Konterhaken" },
	{ id = "Khabib_Nurmagomedov", name = "Khabib Nurmagomedov", style = "Ringen", move = "Double-Leg-Takedown" },
	{ id = "Saenchai", name = "Saenchai", style = "Muay Thai", move = "Teep mit Finte" },
	{ id = "Charles_Oliveira", name = "Charles Oliveira", style = "Muay Thai / BJJ", move = "Clinch-Knie" },
}
local ROW_X, ROW_Z0, ROW_DZ, LOOK_X = 186, 4, 3.6, 160  -- Studs, Welt (freier Streifen an der Ostseite zwischen Kaefig und Wand, Blick zum Kaefig)

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
			local x, z = ROW_X, ROW_Z0 + (i - 1) * ROW_DZ
			local y = groundAt(x, z, { holder })
			m:PivotTo(CFrame.lookAt(Vector3.new(x, y, z), Vector3.new(LOOK_X, y, z)))
			m.Parent = holder
			local pr = Instance.new("ProximityPrompt")
			pr.ObjectText = t.name; pr.ActionText = "Sprechen"; pr.KeyboardKeyCode = Enum.KeyCode.E; pr.GamepadKeyCode = Enum.KeyCode.ButtonX
			pr.HoldDuration = 0; pr.MaxActivationDistance = 8; pr.RequiresLineOfSight = false
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
	if type(sig) ~= "string" or not SIG.list[sig] or not pe then return end
	local unlocked = table.find(string.split(p:GetAttribute("CC_SigUnlocked") or "", ","), sig) ~= nil
	if action == "equip" and unlocked then pe:Fire(p, "sig_equip", sig)
	elseif action == "unequip" then pe:Fire(p, "sig_equip", "")
	elseif action == "learn" and not unlocked then p:SetAttribute("CC_SigTrial", sig)
	elseif action == "stoplearn" then p:SetAttribute("CC_SigTrial", nil) end
end)
task.spawn(function() task.wait(2); place() end)
SS.ChildAdded:Connect(function(c) if c.Name == "CC_StyleTrainers" then place() end end)
