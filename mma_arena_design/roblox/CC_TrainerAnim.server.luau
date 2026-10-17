-- ServerScriptService.CC_TrainerAnim
-- Animiert die Stil-Trainer im Gym (Modelle mit Attribut CC_TrainerRig aus setup_trainer_rigged_v01, gleiche Bones wie der Kaempfer).
-- Idle: eigene Trainer-Idle (TRAINER_IDLE[id]) falls vorhanden, sonst die Kampf-Idle des Kaempfers.
-- Animationen: hochgeladene IDs (ServerStorage.CC_Animations.CC_AnimIds); in Studio ohne ID die KeyframeSequence aus CC_Animations.
local SS = game:GetService("ServerStorage")
local KSP = game:GetService("KeyframeSequenceProvider")

local TRAINER_IDLE = {}                               -- spaeter: [trainerId] = "Trainer_Tyson_Idle" usw.
local DEFAULT_IDLE = "Fighter_Idle_v08"

local animFolder = SS:WaitForChild("CC_Animations", 10)
local ids = {}
pcall(function() ids = require(animFolder:FindFirstChild("CC_AnimIds")) end)

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

local function setup(m)
	if not m:IsA("Model") or not m:GetAttribute("CC_TrainerRig") or m:GetAttribute("CC_AnimReady") then return end
	local ac = m:FindFirstChildOfClass("AnimationController")
	local animator = ac and ac:FindFirstChildOfClass("Animator")
	if not animator then return end
	m:SetAttribute("CC_AnimReady", true)
	local a = animFor(TRAINER_IDLE[m:GetAttribute("CC_TrainerId")] or DEFAULT_IDLE)
	if not a then warn("[CC] Trainer-Idle fehlt fuer " .. m.Name) return end
	local tr = animator:LoadAnimation(a)
	tr.Looped = true; tr.Priority = Enum.AnimationPriority.Idle
	tr:Play(0.2)
	tr:AdjustSpeed(0.92 + math.random() * 0.16)        -- Trainer nicht im Gleichtakt
end

local function watch(folder)
	for _, m in ipairs(folder:GetChildren()) do task.spawn(setup, m) end
	folder.ChildAdded:Connect(function(m) task.defer(setup, m) end)
end
local f = workspace:FindFirstChild("CC_StyleTrainersGym")
if f then watch(f) end
workspace.ChildAdded:Connect(function(c) if c.Name == "CC_StyleTrainersGym" then watch(c) end end)
