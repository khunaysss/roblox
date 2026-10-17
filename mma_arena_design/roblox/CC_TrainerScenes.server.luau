-- ServerScriptService.CC_TrainerScenes
-- Loest die Filmszenen der Stil-Trainer aus (Werte: ReplicatedStorage.CC_TrainerScenes) und spielt die Trainer-Animationen
-- auf dem Server ab (alle Spieler sehen den Trainer sich bewegen; Kamera nur beim betroffenen Spieler, CC_TrainerScenes.client).
--   greet:     erstes Ansprechen eines Trainers in dieser Sitzung (ProximityPrompt des Trainers)
--   demo:      nach "Quest starten" im Trainer-Panel
--   challenge: "Trainer herausfordern" mit erfuellten Quests (CC_Trainers startet den Kampf erst nach dieser Szene)
--   unlock:    neue Signatur freigeschaltet und Spieler wieder im Gym (nicht im Kampf) -> vor den Trainer, Szene
local RS, SS = game:GetService("ReplicatedStorage"), game:GetService("ServerStorage")
local Players = game:GetService("Players")
local KSP = game:GetService("KeyframeSequenceProvider")
local PPS = game:GetService("ProximityPromptService")
local HS = game:GetService("HttpService")
local SC = require(RS:WaitForChild("CC_TrainerScenes"))
local SIGPROG = require(RS:WaitForChild("CC_SignatureProgression"))

local ev = RS:FindFirstChild("CC_TrainerScene") or Instance.new("RemoteEvent"); ev.Name = "CC_TrainerScene"; ev.Parent = RS
local animFolder = SS:WaitForChild("CC_Animations", 10)
local ids = {}
pcall(function() ids = require(animFolder:FindFirstChild("CC_AnimIds")) end)

local busy = {}                      -- [player] = Szenen-Ende (os.clock)
local trainerBusy = {}               -- [model] = Ende der laufenden Trainer-Animation

local function trainerModel(id)
	local f = workspace:FindFirstChild("CC_StyleTrainersGym")
	return f and f:FindFirstChild(id)
end
local function animFor(name)
	local a = Instance.new("Animation")
	if ids[name] then a.AnimationId = "rbxassetid://" .. tostring(ids[name]); return a end
	local ks = animFolder and animFolder:FindFirstChild(name)
	if ks and ks:IsA("KeyframeSequence") then
		local ok, id = pcall(function() return KSP:RegisterKeyframeSequence(ks) end)
		if ok then a.AnimationId = id; return a end
	end
	return nil
end
local trackCache = {}
local function playOn(model, spec)
	local ac = model:FindFirstChildOfClass("AnimationController")
	local animator = ac and ac:FindFirstChildOfClass("Animator")
	if not animator then return end
	trackCache[model] = trackCache[model] or {}
	local tr = trackCache[model][spec.name]
	if tr == nil then
		local a = animFor(spec.name)
		tr = a and animator:LoadAnimation(a) or false
		if tr then tr.Priority = Enum.AnimationPriority.Action; tr.Looped = false end
		trackCache[model][spec.name] = tr
	end
	if not tr then warn("[CC] Szenen-Animation fehlt: " .. spec.name) return end
	tr:Play(0.15, 1, 1)
	if spec.slow then                                   -- Zeitlupe im Trefferbereich (Animationszeit)
		local a, b, rate = spec.slow[1], spec.slow[2], spec.slow[3]
		task.spawn(function()
			while tr.IsPlaying and tr.TimePosition < a do task.wait() end
			if tr.IsPlaying then tr:AdjustSpeed(rate) end
			while tr.IsPlaying and tr.TimePosition < b do task.wait() end
			if tr.IsPlaying then tr:AdjustSpeed(1) end
		end)
	end
end

-- Szene starten; gibt die Laenge zurueck (0 = keine Szene)
local function play(p, id, kind)
	local def = SC.get(id, kind)
	local model = trainerModel(id)
	if not def or (def.length or 0) <= 0 or not model or not p.Character then return 0 end
	if busy[p] and os.clock() < busy[p] then return 0 end
	busy[p] = os.clock() + def.length
	local prog = SIGPROG.list[(function() for k, v in pairs(SIGPROG.list) do if v.trainerId == id then return k end end end)()]
	ev:FireClient(p, kind, id, model, { trainerName = prog and prog.trainerName or id, signatureName = prog and prog.signatureName })
	if not trainerBusy[model] or os.clock() > trainerBusy[model] then
		trainerBusy[model] = os.clock() + def.length
		for _, a in ipairs(def.anims or {}) do task.delay(a.at or 0, playOn, model, a) end
	end
	return def.length
end
-- fuer CC_Trainers (Herausforderung) und Tests: ServerStorage.CC_TrainerScenePlay:Invoke(player, trainerId, kind) -> Laenge
local bf = SS:FindFirstChild("CC_TrainerScenePlay") or Instance.new("BindableFunction"); bf.Name = "CC_TrainerScenePlay"; bf.Parent = SS
bf.OnInvoke = play

-- greet: erstes Ansprechen in der Sitzung
PPS.PromptTriggered:Connect(function(prompt, p)
	local f = workspace:FindFirstChild("CC_StyleTrainersGym")
	if not f or not prompt:IsDescendantOf(f) then return end
	local model = prompt:FindFirstAncestorOfClass("Model")
	while model and model.Parent ~= f do model = model.Parent:FindFirstAncestorOfClass("Model") end
	if not model or (p.Character and p.Character:GetAttribute("CC_Opponent")) then return end
	local met = string.split(p:GetAttribute("CC_MetTrainers") or "", ",")
	if table.find(met, model.Name) then return end
	table.insert(met, model.Name); p:SetAttribute("CC_MetTrainers", table.concat(met, ","))
	play(p, model.Name, "greet")
end)

-- demo: nach "Quest starten" (gleiches RemoteEvent wie CC_Trainers, eigene Verbindung)
local panel = RS:WaitForChild("CC_TrainerPanel")
panel.OnServerEvent:Connect(function(p, action, sig)
	if action ~= "start" or type(sig) ~= "string" or not SIGPROG.list[sig] then return end
	local unlocked = table.find(string.split(p:GetAttribute("CC_SigUnlocked") or "", ","), sig) ~= nil
	if unlocked then return end
	task.wait(0.3)
	play(p, SIGPROG.list[sig].trainerId, "demo")
end)

-- unlock: neue Signatur -> sobald der Spieler wieder im Gym steht und nichts laeuft
local function inGym(p)
	local c = p.Character; local r = c and c:FindFirstChild("HumanoidRootPart")
	-- im Gym (Fight Night liegt bei z = -700), nicht im Kampf, kein Minispiel
	return r ~= nil and r.Position.Z > -400 and not c:GetAttribute("CC_Opponent") and not p:GetAttribute("CC_Minigame")
end
local function hookPlayer(p)
	local known = string.split(p:GetAttribute("CC_SigUnlocked") or "", ",")
	local loaded = false
	task.delay(6, function() loaded = true; known = string.split(p:GetAttribute("CC_SigUnlocked") or "", ",") end)   -- Laden des Profils ist keine Freischaltung
	p:GetAttributeChangedSignal("CC_SigUnlocked"):Connect(function()
		local now = string.split(p:GetAttribute("CC_SigUnlocked") or "", ",")
		if not loaded then known = now return end
		for _, sig in ipairs(now) do
			if sig ~= "" and not table.find(known, sig) and SIGPROG.list[sig] then
				task.spawn(function()
					local t0 = os.clock()
					repeat task.wait(0.5) until not p.Parent or os.clock() - t0 > 120 or (inGym(p) and os.clock() - t0 > 2)
					if not p.Parent or not inGym(p) then return end
					local id = SIGPROG.list[sig].trainerId
					local model = trainerModel(id)
					local r = p.Character and p.Character:FindFirstChild("HumanoidRootPart")
					if model and r then                                  -- vor den Trainer stellen, Blick zu ihm
						local piv = model:GetPivot()
						local pos = (piv * CFrame.new(SC.UNLOCK_SPOT)).Position + Vector3.new(0, 3, 0)
						r.CFrame = CFrame.lookAt(pos, Vector3.new(piv.Position.X, pos.Y, piv.Position.Z))
						r.AssemblyLinearVelocity = Vector3.zero
					end
					play(p, id, "unlock")
				end)
			end
		end
		known = now
	end)
end
-- Vorschau (nur Studio): workspace-Attribut CC_ScenePreview = "Mike_Tyson" -> nach dem Start alle vier Szenen nacheinander
-- (greet, demo, challenge ohne Kampf, unlock). Im echten Spiel wirkungslos.
local function preview(p)
	local id = workspace:GetAttribute("CC_ScenePreview")
	if not game:GetService("RunService"):IsStudio() or type(id) ~= "string" then return end
	if not p.Character then p.CharacterAdded:Wait() end
	task.wait(8)                                       -- Trainer werden erst nach dem Start ins Gym gestellt
	if not trainerModel(id) then warn("[CC] Szenen-Vorschau: Trainer " .. id .. " nicht im Gym") return end
	for _, kind in ipairs({ "greet", "demo", "challenge", "unlock" }) do
		if not p.Parent then return end
		local model = trainerModel(id); local r = p.Character and p.Character:FindFirstChild("HumanoidRootPart")
		if kind == "unlock" and model and r then
			local piv = model:GetPivot(); local pos = (piv * CFrame.new(SC.UNLOCK_SPOT)).Position + Vector3.new(0, 3, 0)
			r.CFrame = CFrame.lookAt(pos, Vector3.new(piv.Position.X, pos.Y, piv.Position.Z))
		end
		local len = play(p, id, kind)
		task.wait((len or 0) + 1.2)
	end
end
Players.PlayerAdded:Connect(function(p) task.spawn(preview, p) end)
for _, p in ipairs(Players:GetPlayers()) do task.spawn(preview, p) end
Players.PlayerAdded:Connect(hookPlayer)
for _, p in ipairs(Players:GetPlayers()) do hookPlayer(p) end
Players.PlayerRemoving:Connect(function(p) busy[p] = nil end)
