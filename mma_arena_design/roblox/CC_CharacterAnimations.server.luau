-- ServerScriptService.CC_CharacterAnimations
-- Cage Champions Prototyp v03: Spieler und Trainingsgegner kaempfen mit Jab, Treffer-Reaktion und K.o.
-- Animationen ueber temporaere Studio-IDs (RegisterKeyframeSequence); fuer das veroeffentlichte Spiel
-- muessen sie in die Gruppe ANIMEXGANG (7160158) hochgeladen und die IDs hier eingetragen werden.
local KSP = game:GetService("KeyframeSequenceProvider")
local RunService = game:GetService("RunService")
local A = game.ServerStorage.CC_Animations
local function anim(name) local a = Instance.new("Animation"); a.AnimationId = KSP:RegisterKeyframeSequence(A[name]); return a end
local ANIMS = {
	idle = anim("Fighter_Idle_v08"), walk = anim("Fighter_Walk_v01"), jab = anim("Fighter_Jab_v01"),
	hit = anim("Fighter_HitReact_v01"), ko = anim("Fighter_KO_v01"),
}
local WALK_REF = 6         -- Laufzyklus ist fuer WalkSpeed 6 gebaut
local JAB_HIT_TIME = 0.21  -- Frame 6 = Treffer
local JAB_COOLDOWN = 0.75
local JAB_RANGE = 4.5
local KO_TIME = 3
local PLAYER_DAMAGE, DUMMY_DAMAGE = 10, 8

local fighters = {} -- [char] = {hum, tracks, last, ko}

local function setup(char)
	local hum = char:WaitForChild("Humanoid"); local animator = hum:WaitForChild("Animator")
	hum.BreakJointsOnDeath = false
	hum:SetStateEnabled(Enum.HumanoidStateType.Dead, false)
	local t = {}
	for k, a in pairs(ANIMS) do t[k] = animator:LoadAnimation(a) end
	t.idle.Looped = true; t.walk.Looped = true
	t.idle:Play(0.2)
	local f = { char = char, hum = hum, tracks = t, last = 0, ko = false, speed = hum.WalkSpeed }
	hum.Running:Connect(function(speed)
		if f.ko then return end
		if speed > 0.5 then
			if not t.walk.IsPlaying then t.walk:Play(0.15) end
			t.walk:AdjustSpeed(speed / WALK_REF)
		elseif t.walk.IsPlaying then
			t.walk:Stop(0.15)
		end
	end)
	fighters[char] = f
	char.AncestryChanged:Connect(function() if not char.Parent then fighters[char] = nil end end)
	return f
end

local function knockout(f)
	f.ko = true
	f.hum.WalkSpeed = 0
	f.tracks.walk:Stop(0.1); f.tracks.jab:Stop(0.1); f.tracks.hit:Stop(0.1)
	local ko = f.tracks.ko
	ko:Play(0.1)
	task.delay(ko.Length - 0.05, function() if f.ko then ko:AdjustSpeed(0) end end) -- liegen bleiben
	f.char:SetAttribute("CC_KO", true)
	task.delay(KO_TIME, function()
		if not f.char.Parent then return end
		ko:Stop(0.4)
		f.hum.Health = f.hum.MaxHealth
		f.hum.WalkSpeed = f.speed
		f.ko = false
		f.char:SetAttribute("CC_KO", false)
	end)
end

local function inFront(attacker, target)
	local a, b = attacker.char.HumanoidRootPart, target.char.HumanoidRootPart
	local d = b.Position - a.Position; local flat = Vector3.new(d.X, 0, d.Z)
	return flat.Magnitude <= JAB_RANGE and flat.Magnitude > 0 and a.CFrame.LookVector:Dot(flat.Unit) > 0.5
end

local function jab(attacker, damage)
	if attacker.ko or os.clock() - attacker.last < JAB_COOLDOWN then return end
	attacker.last = os.clock()
	attacker.tracks.jab:Play(0.05)
	task.delay(JAB_HIT_TIME, function()
		if attacker.ko or not attacker.char.Parent then return end
		for _, target in pairs(fighters) do
			if target ~= attacker and not target.ko and inFront(attacker, target) then
				target.hum.Health = math.max(0, target.hum.Health - damage)
				print("[CC] Treffer", target.char.Name, target.hum.Health)
				if target.hum.Health <= 0 then
					print("[CC] K.o.!", target.char.Name)
					knockout(target)
				else
					target.tracks.hit:Play(0.05)
				end
			end
		end
	end)
end

local function hook(p) p.CharacterAdded:Connect(setup); if p.Character then task.spawn(setup, p.Character) end end
game.Players.PlayerAdded:Connect(hook); for _, p in ipairs(game.Players:GetPlayers()) do hook(p) end

game.ReplicatedStorage.CC_Jab.OnServerEvent:Connect(function(player)
	local f = player.Character and fighters[player.Character]
	if f then jab(f, PLAYER_DAMAGE) end
end)

-- Trainingsgegner: dreht sich zum naechsten Spieler und schlaegt zu, wenn er in Reichweite ist
local dummy = workspace:WaitForChild("CC_TrainingDummy")
local D = setup(dummy)
local fill = dummy.HumanoidRootPart.HealthBar.Frame.Fill
D.hum.HealthChanged:Connect(function(h) fill.Size = UDim2.fromScale(math.max(h, 0) / D.hum.MaxHealth, 1) end)
local nextAttack = 0
RunService.Heartbeat:Connect(function()
	if D.ko then return end
	local root = dummy.HumanoidRootPart
	local best, bestDist
	for char, f in pairs(fighters) do
		if f ~= D and not f.ko then
			local dist = (char.HumanoidRootPart.Position - root.Position).Magnitude
			if not bestDist or dist < bestDist then best, bestDist = f, dist end
		end
	end
	if not best then return end
	local tp = best.char.HumanoidRootPart.Position
	local look = Vector3.new(tp.X, root.Position.Y, tp.Z)
	if (look - root.Position).Magnitude > 0.1 then
		local goal = CFrame.lookAt(root.Position, look)
		root.CFrame = root.CFrame:Lerp(goal, 0.15)
	end
	if bestDist <= JAB_RANGE and os.clock() > nextAttack then
		nextAttack = os.clock() + 1.4 + math.random() * 1.2
		jab(D, DUMMY_DAMAGE)
	end
end)
