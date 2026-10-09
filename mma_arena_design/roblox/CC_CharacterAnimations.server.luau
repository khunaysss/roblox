-- ServerScriptService.CC_CharacterAnimations
-- Cage Champions Prototyp: Idle/Laufen/Jab fuer Spieler, Treffer auf den Trainingsgegner.
-- Animationen ueber temporaere Studio-IDs (RegisterKeyframeSequence); fuer das veroeffentlichte Spiel
-- muessen sie in die Gruppe ANIMEXGANG (7160158) hochgeladen und die IDs hier eingetragen werden.
local KSP = game:GetService("KeyframeSequenceProvider")
local A = game.ServerStorage.CC_Animations
local function anim(name) local a = Instance.new("Animation"); a.AnimationId = KSP:RegisterKeyframeSequence(A[name]); return a end
local IDLE, WALK, JAB = anim("Fighter_Idle_v08"), anim("Fighter_Walk_v01"), anim("Fighter_Jab_v01")
local WALK_REF = 6       -- Laufzyklus ist fuer WalkSpeed 6 gebaut
local JAB_HIT_TIME = 0.21 -- Frame 6 = Treffer
local JAB_COOLDOWN = 0.75
local JAB_RANGE, JAB_DAMAGE = 4.5, 10

local tracks = {}
local function onCharacter(char)
	local hum = char:WaitForChild("Humanoid"); local animator = hum:WaitForChild("Animator")
	local t = { idle = animator:LoadAnimation(IDLE), walk = animator:LoadAnimation(WALK), jab = animator:LoadAnimation(JAB), last = 0 }
	t.idle.Looped = true; t.walk.Looped = true; t.jab.Looped = false
	t.idle:Play(0.2)
	hum.Running:Connect(function(speed)
		if speed > 0.5 then
			if not t.walk.IsPlaying then t.walk:Play(0.15) end
			t.walk:AdjustSpeed(speed / WALK_REF)
		elseif t.walk.IsPlaying then
			t.walk:Stop(0.15)
		end
	end)
	tracks[char] = t
	char.AncestryChanged:Connect(function() if not char.Parent then tracks[char] = nil end end)
end
local function hook(p) p.CharacterAdded:Connect(onCharacter); if p.Character then task.spawn(onCharacter, p.Character) end end
game.Players.PlayerAdded:Connect(hook); for _, p in ipairs(game.Players:GetPlayers()) do hook(p) end

-- Trainingsgegner: Idle + Lebensbalken, nach K.o. 3 s Pause und volle Leben
local dummy = workspace:WaitForChild("CC_TrainingDummy")
local dhum = dummy:WaitForChild("Humanoid")
dhum.BreakJointsOnDeath = false
dhum:SetStateEnabled(Enum.HumanoidStateType.Dead, false)
local di = dhum.Animator:LoadAnimation(IDLE); di.Looped = true; di:Play()
local fill = dummy.HumanoidRootPart.HealthBar.Frame.Fill
dhum.HealthChanged:Connect(function(h) fill.Size = UDim2.fromScale(math.max(h, 0) / dhum.MaxHealth, 1) end)

game.ReplicatedStorage.CC_Jab.OnServerEvent:Connect(function(player)
	local char = player.Character; local t = char and tracks[char]
	if not t or os.clock() - t.last < JAB_COOLDOWN then return end
	t.last = os.clock()
	t.jab:Play(0.05)
	task.delay(JAB_HIT_TIME, function()
		if not char.Parent then return end
		local root = char.HumanoidRootPart
		local d = dummy.HumanoidRootPart.Position - root.Position
		local flat = Vector3.new(d.X, 0, d.Z)
		if flat.Magnitude <= JAB_RANGE and flat.Magnitude > 0 and root.CFrame.LookVector:Dot(flat.Unit) > 0.5 and dhum.Health > 0 then
			dhum.Health = math.max(0, dhum.Health - JAB_DAMAGE)
			print("[CC] Treffer", dhum.Health)
			if dhum.Health <= 0 then
				print("[CC] K.o.!")
				task.delay(3, function() dhum.Health = dhum.MaxHealth end)
			end
		end
	end)
end)
