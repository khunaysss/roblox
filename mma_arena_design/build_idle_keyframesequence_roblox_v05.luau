-- Cage Champions: baut die Idle-KeyframeSequence fuer den importierten Kaempfer in Roblox Studio.
-- Ausfuehren in Studio (Command Bar oder MCP execute_luau, Edit-Modus).
-- Voraussetzung:
--   * Workspace.CC_ImportTest.CC_Fighter_Base_v03 (Import von export/Fighter_Base_v03_Model.fbx,
--     Rig-Typ Custom, Einheit Centimeter, Faktor 1)
--   * ServerStorage.CC_Animations.Fighter_Idle_v07_Data = ModuleScript mit dem Inhalt von
--     export/Fighter_Idle_v05_keyframes.luau (erzeugt von export_idle_keyframes_roblox_v05.py)
-- Ergebnis: ServerStorage.CC_Animations.Fighter_Idle_v07 (33 Keyframes, 24 fps, Loop)
--
-- Umrechnung: Roblox legt jeden importierten Bone mit einer um 180 Grad um die Bone-Y-Achse
-- gedrehten Achse an (lokale X- und Z-Achse negiert gegenueber Blender). Darum gilt
-- Bone.Transform = S * matrix_basis * S mit S = diag(-1, 1, -1):
-- Position (x, y, z) -> (-x, y, -z), Quaternion (w, x, y, z) -> (w, -x, y, -z).

local folder = game.ServerStorage.CC_Animations
local d = require(folder.Fighter_Idle_v07_Data)
local rig = workspace.CC_ImportTest.CC_Fighter_Base_v03

local function toCF(v)
	return CFrame.new(-v[1], v[2], -v[3], -v[5], v[6], -v[7], v[4])
end

local old = folder:FindFirstChild("Fighter_Idle_v07")
if old then old:Destroy() end

local ks = Instance.new("KeyframeSequence")
ks.Name = "Fighter_Idle_v07"
ks.Loop = true
ks.Priority = Enum.AnimationPriority.Idle

local function addPoses(parentPose, bone, frame)
	for _, child in ipairs(bone:GetChildren()) do
		if child:IsA("Bone") then
			local pose = Instance.new("Pose")
			pose.Name = child.Name
			pose.CFrame = toCF(frame[child.Name])
			pose.EasingStyle = Enum.PoseEasingStyle.Linear
			pose.Parent = parentPose
			addPoses(pose, child, frame)
		end
	end
end

for _, frame in ipairs(d.frames) do
	local kf = Instance.new("Keyframe")
	kf.Time = frame.t
	local rootPose = Instance.new("Pose")
	rootPose.Name = "RootPart"
	rootPose.Weight = 0
	rootPose.Parent = kf
	addPoses(rootPose, rig.RootPart, frame)
	kf.Parent = ks
end
ks.Parent = folder

-- Testabspielen im Playtest (ServerScriptService.CC_IdleTest):
--   local id = game:GetService("KeyframeSequenceProvider"):RegisterKeyframeSequence(ks)
--   local track = rig.AnimationController.Animator:LoadAnimation(Animation mit AnimationId = id)
--   track.Looped = true; track:Play(0)
-- Die registrierte ID gilt nur in Studio. Fuer das veroeffentlichte Spiel muss die Sequenz
-- in die Roblox-Gruppe hochgeladen werden (Gruppen-ID vorher klaeren).
