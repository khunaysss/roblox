-- Open MMA stance and responsive local locomotion for Cage Champions' custom Bone rig.
-- Runs after Animator evaluation on every client; existing hit/block/ground clips keep priority.
-- (Stand aus Studio 2026-10-17, von Codex erstellt; Aenderung Claude: CC_UIBlock stoppt die Steh-Animation nicht mehr -> keine T-Pose
--  bei offenem Menue oder in Filmszenen. Original in ServerStorage.CC_TPoseFixBackup.)
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
local RS=game:GetService("ReplicatedStorage")
local player=Players.LocalPlayer
local poses=require(RS:WaitForChild("CC_CombatPoseData"))
local manifest=RS:WaitForChild("CC_AnimationManifest")
local records={}
local upper={UpperTorso=true,Head=true,LeftUpperArm=true,LeftLowerArm=true,LeftHand=true,RightUpperArm=true,RightLowerArm=true,RightHand=true}
local kickNames={
 Fighter_LowKick_v5="lowkick",Fighter_BodyKick_v3="bodykick",
 Fighter_HighKick_v3="highkick",Fighter_FrontKick_v3="frontkick",
}
local kickIds={}
local function rememberKick(clip)
 if clip:IsA("Animation") and kickNames[clip.Name] then kickIds[clip.AnimationId]=kickNames[clip.Name] end
end
for _,clip in ipairs(manifest:GetChildren()) do rememberKick(clip) end
manifest.ChildAdded:Connect(rememberKick)
local function correctedKickPose(r)
 local track,kind
 for _,tr in ipairs(r.animator:GetPlayingAnimationTracks()) do
  local k=tr.Animation and kickIds[tr.Animation.AnimationId]
  if k and tr.Priority.Value>=Enum.AnimationPriority.Action.Value and tr.WeightCurrent>.05
   and (not track or tr.WeightCurrent>track.WeightCurrent) then track,kind=tr,k end
 end
 if not track or track.Length<=0 then return end
 local phase=math.clamp(track.TimePosition/track.Length,0,1)
 local envelope=math.min(math.clamp((phase-.04)/.13,0,1),math.clamp((1-phase)/.12,0,1))
 local strength=envelope*math.clamp(track.WeightCurrent,0,1)
 if strength<.002 then return end
 local function adjust(name,goal,blend)
  local b=r.bones[name]
  if not b then return end
  if not r.raw[b] then r.raw[b]=b.Transform end
  b.Transform=b.Transform:Lerp(goal,math.clamp(blend*strength,0,1))
 end
 local hip=r.bones.LowerTorso
 if hip then
  local cf=hip.Transform
  local x,y,z=cf:ToEulerAnglesXYZ()
  local p=cf.Position
  local grounded=CFrame.new(math.clamp(p.X,-.14,.14),math.clamp(p.Y,-.38,.08),math.clamp(p.Z,-.40,.18))
   *CFrame.Angles(math.clamp(x,-.12,.12),math.clamp(y,-.60,.60),math.clamp(z,-.12,.12))
  adjust("LowerTorso",grounded,1)
 end
 local torso=r.bones.UpperTorso
 if torso then
  local cf=torso.Transform
  local x,y,z=cf:ToEulerAnglesXYZ()
  local guarded=CFrame.new(cf.Position)
   *CFrame.Angles(math.clamp(x,-.14,.14),math.clamp(y,-.42,.42),math.clamp(z,-.14,.14))
  adjust("UpperTorso",guarded,.9)
 end
 -- Both hands stay close enough to guard during the turn.
 adjust("RightUpperArm",poses.normal.RightUpperArm,.76)
 adjust("LeftUpperArm",poses.normal.LeftUpperArm,.42)
 local support=kind=="frontkick" and "Right" or "Left"
 adjust(support.."UpperLeg",poses.normal[support.."UpperLeg"],.56)
 adjust(support.."LowerLeg",poses.normal[support.."LowerLeg"],.56)
 adjust(support.."Foot",poses.normal[support.."Foot"],.78)
 -- The chambered leg returns before the clip finishes; the standing foot is left alone.
 local recoil=math.clamp((phase-.63)/.24,0,1)
 local leg=kind=="frontkick" and "Left" or "Right"
 adjust(leg.."UpperLeg",poses.normal[leg.."UpperLeg"],recoil*.46)
 adjust(leg.."LowerLeg",poses.normal[leg.."LowerLeg"],recoil*.34)
end
local function register(char)
 if records[char] then return end
 local root=char:FindFirstChild("HumanoidRootPart")
 local hum=char:FindFirstChildOfClass("Humanoid")
 local animator=hum and hum:FindFirstChildOfClass("Animator")
 if not (root and animator and root:FindFirstChild("Root")) then return end
 local bones={}
 for _,b in ipairs(root:GetDescendants()) do if b:IsA("Bone") and poses.normal[b.Name] then bones[b.Name]=b end end
 if not bones.LeftHand then return end
 local r={root=root,hum=hum,animator=animator,bones=bones,raw={},weight=0,fatigue=0}
 if char==player.Character then
  r.casual={}
  for key,name in pairs({idle="Fighter_CasualIdle_v01",walk="Fighter_CasualWalk_v2",run="Fighter_CasualRun_v3"}) do
   local clip=manifest:FindFirstChild(name)
   if clip then local tr=animator:LoadAnimation(clip);tr.Name="CC_Local_"..key;tr.Looped=true;tr.Priority=key=="idle" and Enum.AnimationPriority.Idle or Enum.AnimationPriority.Movement;r.casual[key]=tr end
  end
 end
 records[char]=r
end
local function blocked(char)
 return char:GetAttribute("CC_Wrestle") or char:GetAttribute("CC_Down") or char:GetAttribute("CC_KO")
  or char:GetAttribute("CC_Knockdown") or char:GetAttribute("CC_Block") or char:GetAttribute("CC_Frozen")
end
local function releaseStaleTracks(char,r)
 local blockClip=manifest:FindFirstChild("Fighter_Block_v01")
 for _,tr in ipairs(r.animator:GetPlayingAnimationTracks()) do
  if blockClip and tr.Animation and tr.Animation.AnimationId==blockClip.AnimationId
    and not char:GetAttribute("CC_Block") and tr.Speed==0 then tr:AdjustSpeed(1);tr:Stop(0.12) end
 end
end
local function restore(r)
 for b,cf in pairs(r.raw) do if b.Parent then b.Transform=cf end end
 table.clear(r.raw)
end
-- Remove our previous frame before Animator evaluates, including when an action interrupts.
RunService.PreAnimation:Connect(function()
 for char,r in pairs(records) do
  restore(r)
  releaseStaleTracks(char,r)
  if not char.Parent then records[char]=nil end
 end
 local char=player.Character
 local r=char and records[char]
 if not r or not r.casual then return end
 local exercise=player:GetAttribute("CC_Minigame")~=nil
 local allowed=not r.root.Anchored and not blocked(char) and not char:GetAttribute("CC_Opponent") and not char:GetAttribute("CC_BagPractice")
   and not exercise   -- CC_UIBlock (Menue, Filmszenen) sperrt nur Eingaben, nicht die Steh-Animation (sonst T-Pose)
 if not allowed then
  if r.casualOn then
   r.casualOn=false
   for _,tr in pairs(r.casual) do tr:AdjustSpeed(1);tr:Stop(0.10) end
  end
  return
 end
 r.casualOn=true
 local v=r.root.AssemblyLinearVelocity
 local actual=Vector3.new(v.X,0,v.Z).Magnitude
 local intent=r.hum.MoveDirection.Magnitude
 local moving=math.max(actual,intent>0.05 and math.min(r.hum.WalkSpeed,2.4)*intent or 0)
 local amount=math.clamp(moving/2.4,0,1)
 local runK=math.clamp((math.max(actual,r.hum.WalkSpeed*intent)-9)/4,0,1)
 local desired={idle=1,walk=math.max(amount*(1-runK),0.001),run=math.max(amount*runK,0.001)}
 for key,tr in pairs(r.casual) do
  if not tr.IsPlaying then tr:Play(0.07,desired[key],1) end
  tr:AdjustWeight(desired[key],0.07)
  tr:AdjustSpeed(key=="walk" and math.max(moving,0.5)/(1.8/0.28) or key=="run" and math.max(moving,0.5)/15 or 1)
 end
 char:SetAttribute("CC_Loco",amount<0.05 and "idle" or runK>0.5 and "run" or "walk")

end)
RunService.PreSimulation:Connect(function(dt)
 local now=workspace:GetServerTimeNow()
 for char,r in pairs(records) do
  local eligible=char.Parent and char:GetAttribute("CC_Stamina")~=nil
    and (char:GetAttribute("CC_Opponent")~=nil or char:GetAttribute("CC_BagPractice")==true) and not blocked(char)
  if not eligible then
   r.weight=0
   -- A fully specified relaxed pose covers asset-loading or a same-ID exercise stop.
   if r.casualOn and r.casual then
    local idle=r.casual.idle
    if not idle or not idle.IsPlaying or idle.Length==0 or idle.WeightCurrent<0.5 then
     for name,b in pairs(r.bones) do
      if poses.casual[name] then r.raw[b]=b.Transform;b.Transform=poses.casual[name] end
     end
    end
   end
   continue
  end
  local actionWeight=0
  for _,tr in ipairs(r.animator:GetPlayingAnimationTracks()) do
   if tr.Priority.Value>=Enum.AnimationPriority.Action.Value then actionWeight=math.max(actionWeight,tr.WeightCurrent) end
  end
  local target=1-math.clamp(actionWeight,0,1)
  r.weight+=(target-r.weight)*(1-math.exp(-(target<r.weight and 35 or 16)*dt))
  if r.weight<0.002 then correctedKickPose(r); continue end
  local stamina=char:GetAttribute("CC_Stamina") or 100
  local maxStamina=char:GetAttribute("CC_StaminaMax") or 100
  local fatigue=math.clamp((0.45-stamina/math.max(maxStamina,1))/0.35,0,1)
  r.fatigue+=(fatigue-r.fatigue)*(1-math.exp(-5*dt))
  local l=char:GetAttribute("CC_Injury_LeftLeg") or 0
  local rr=char:GetAttribute("CC_Injury_RightLeg") or 0
  local hurt=math.clamp((math.max(l,rr)-30)/55,0,1)
  local injured=poses[l>=rr and "left" or "right"]
  local v=r.root.AssemblyLinearVelocity
  local movement=math.clamp((Vector3.new(v.X,0,v.Z).Magnitude-0.25)/1.5,0,1)
  local spring=math.sin(now*math.pi*2/1.15)*(1-r.fatigue)*(1-hurt)*0.016
  local breathing=math.sin(now*math.pi*2/(2.8-r.fatigue*1.2))
  for name,b in pairs(r.bones) do
   local raw=b.Transform;r.raw[b]=raw
   local desired=poses.normal[name]:Lerp(poses.tired[name],r.fatigue)
   if hurt>0 then desired=desired*CFrame.identity:Lerp(poses.normal[name]:Inverse()*injured[name],hurt) end
   local w=r.weight*(upper[name] and 1 or (1-movement))
   if name=="UpperTorso" then
    desired=desired*CFrame.Angles(math.rad(breathing*(0.35+r.fatigue*0.65)),0,0)
   elseif name=="LowerTorso" then
    desired=CFrame.new(0,spring,0)*desired
   end
   b.Transform=raw:Lerp(desired,w)
  end
  correctedKickPose(r)
 end
end)
task.spawn(function()
 while script.Parent do
  for _,char in ipairs(workspace:GetChildren()) do if char:IsA("Model") then register(char) end end
  task.wait(0.5)
 end
end)
