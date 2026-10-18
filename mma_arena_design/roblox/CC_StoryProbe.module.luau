-- ServerStorage.CC_Story.CC_StoryProbe (ModuleScript) - Qualitaetsprobe Story-Einstieg (Szene 1-2): Gehen -> Anhalten -> Konfrontation.
-- Nur fuer die Abnahme in Studio (Play). Darsteller = Kopien des echten Kaempfers (StarterCharacter) mit Aussehen (CC_LookShared)
-- und Alltagskleidung (ServerStorage.CC_Story.Outfit_Casual, skinned, aus Fighter_Casual_v01). Kampf-Handschuhe/Shorts ausgeblendet.
-- Ablauf (Sekunden ab Start, workspace-Attribut CC_StoryProbeStart = Serverzeit; der Client richtet Kamera/Licht/Untertitel danach aus):
--   0,0  Spieler geht vom Schulgebaeude Richtung Tor (Fighter_CasualWalk_v2, 6,43 Studs/s = Schritttempo der Animation)
--   3,2  Schueler kommt von rechts und stellt sich in den Weg;  6,2 Spieler bleibt stehen
--   6,8  Story_P_Confront / Story_S_Confront (4 s): "Wohin so schnell?" - Griff an den Rucksacktraeger - "Lass mich einfach durch."
--  12,5  Ende (Darsteller bleiben stehen, bis Cleanup)
local SS, RS = game:GetService("ServerStorage"), game:GetService("ReplicatedStorage")
local RunService, KSP = game:GetService("RunService"), game:GetService("KeyframeSequenceProvider")
local Look = require(RS:WaitForChild("CC_LookShared"))
local A = SS.CC_Animations
local IDS = require(A.CC_AnimIds)

local O = CFrame.new(-600, 0, 600)                    -- Schul-Ursprung (Tormitte), siehe build_story_school_v01
local GROUND = 0.46                                    -- Oberkante Hauptweg
local HRP_Y = GROUND + 3.0
local WALK = 6.43                                      -- Studs/s (Fusskontakt Fighter_CasualWalk_v2: 0,075 m/Frame)
local GAP = 0.80 / 0.28                                -- Abstand der Konfrontation wie in Blender (0,8 m)

local M = {}
local actors = {}

local function anim(name)
	local a = Instance.new("Animation")
	local id = IDS[name]
	a.AnimationId = id and ("rbxassetid://" .. id) or KSP:RegisterKeyframeSequence(A[name])
	return a
end

local function makeActor(name, look, colors, pos, lookAt)
	local c = game.StarterPlayer.StarterCharacter:Clone(); c.Name = name
	for _, n in ipairs({ "Fighter_Gloves", "Fighter_Shorts" }) do local x = c:FindFirstChild(n); if x then x.Transparency = 1 end end
	local hum = c:FindFirstChildOfClass("Humanoid")
	hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	local hrp = c.HumanoidRootPart; hrp.Anchored = true
	c.Parent = workspace
	Look.apply(c, look, SS:FindFirstChild("CC_Custom"))
	for _, t in ipairs(SS.CC_Story.Outfit_Casual:GetChildren()) do
		if colors[t.Name] ~= false then
			local p = t:Clone(); p.Massless = true; p.CanQuery = false; p.CanTouch = false
			if colors[t.Name] then p.Color = colors[t.Name] end
			local mo = Instance.new("Motor6D"); mo.Part0 = hrp; mo.Part1 = p; mo.C0 = t:GetAttribute("CC_C0"); mo.Parent = p
			p.Parent = c
		end
	end
	hrp.CFrame = CFrame.lookAt(pos, Vector3.new(lookAt.X, pos.Y, lookAt.Z))
	local animator = hum:FindFirstChildOfClass("Animator") or Instance.new("Animator", hum)
	local tr = {}
	for k, n in pairs({ walk = "Fighter_CasualWalk_v2", idle = "Fighter_CasualIdle_v01", P = "Story_P_Confront", S = "Story_S_Confront" }) do
		tr[k] = animator:LoadAnimation(anim(n))
	end
	tr.walk.Looped = true; tr.idle.Looped = true; tr.walk.Priority = Enum.AnimationPriority.Movement; tr.idle.Priority = Enum.AnimationPriority.Idle
	tr.P.Priority = Enum.AnimationPriority.Action; tr.S.Priority = Enum.AnimationPriority.Action
	tr.idle:Play(0)
	local a = { model = c, hrp = hrp, tr = tr }
	table.insert(actors, a)
	return a
end

-- Geht in gerader Linie mit Animationstempo; dreht sich am Ziel weich zum Blickziel
local function walkTo(a, target, faceAt)
	local start = a.hrp.Position
	local d = (target - start) * Vector3.new(1, 0, 1)
	local dur = d.Magnitude / WALK
	a.tr.walk:Play(0.25); a.tr.idle:AdjustWeight(0.001, 0.25)
	local t0 = os.clock()
	while true do
		local u = math.min((os.clock() - t0) / dur, 1)
		local p = start + d * u
		a.hrp.CFrame = CFrame.lookAt(p, p + d.Unit)
		if u >= 1 then break end
		RunService.Heartbeat:Wait()
	end
	a.tr.walk:Stop(0.3); a.tr.idle:AdjustWeight(1, 0.3)
	if faceAt then
		local from = a.hrp.CFrame
		local to = CFrame.lookAt(a.hrp.Position, Vector3.new(faceAt.X, a.hrp.Position.Y, faceAt.Z))
		local t1 = os.clock()
		while os.clock() - t1 < 0.35 do
			local u = (os.clock() - t1) / 0.35; u = u * u * (3 - 2 * u)
			a.hrp.CFrame = from:Lerp(to, u); RunService.Heartbeat:Wait()
		end
		a.hrp.CFrame = to
	end
end

function M.cleanup()
	for _, a in ipairs(actors) do if a.model then a.model:Destroy() end end
	actors = {}
end

function M.run(playerLook)
	M.cleanup()
	local W = function(x, z) return (O * CFrame.new(x, HRP_Y, z)).Position end
	local stopP = W(-3, 0)
	local P = makeActor("Story_Player", playerLook or Look.DEFAULT, {}, W(-3, 40), stopP)
	local S = makeActor("Story_StudentA", { hair = "Hair_Buzzcut", beard = "none", face = "Face_Neutral", skin = 1, hairColor = 4 },
		{ Casual_Hoodie = Color3.fromRGB(30, 31, 35), Casual_Pants = Color3.fromRGB(96, 98, 104), Casual_Shoes = Color3.fromRGB(236, 236, 232), Casual_Backpack = false },
		W(17, -9), W(-3, -9))
	-- Hintergrund: zwei Schueler gehen links ueber den Hof Richtung Tor
	local B1 = makeActor("Story_Bg1", { hair = "Hair_ShortCurls", beard = "none", face = "Face_Friendly", skin = 3, hairColor = 1 },
		{ Casual_Hoodie = Color3.fromRGB(64, 92, 132), Casual_Pants = Color3.fromRGB(60, 74, 98) }, W(-9, 64), W(-9, -60))
	local B2 = makeActor("Story_Bg2", { hair = "Hair_SidePart", beard = "none", face = "Face_Focused", skin = 2, hairColor = 3 },
		{ Casual_Hoodie = Color3.fromRGB(150, 74, 62), Casual_Pants = Color3.fromRGB(44, 46, 52) }, W(-6, 70), W(-6, -60))
	task.wait(0.6)                                               -- Animationen laden (keine T-Pose beim Start)
	workspace:SetAttribute("CC_StoryProbeStart", workspace:GetServerTimeNow())
	task.spawn(walkTo, B1, W(-9, -40), nil)
	task.delay(1.2, function() walkTo(B2, W(-6, -40), nil) end)
	task.delay(3.2, function() walkTo(S, (O * CFrame.new(-3, HRP_Y, -GAP)).Position, stopP) end)
	walkTo(P, stopP, (O * CFrame.new(-3, HRP_Y, -GAP)).Position)
	-- exakt wie in Blender aufstellen: Spieler blickt zum Tor (-Z), Schueler steht GAP davor und blickt zurueck
	P.hrp.CFrame = CFrame.lookAt(stopP, stopP + O.LookVector * 1)
	while os.clock() < 0 do end
	local t = workspace:GetServerTimeNow() - workspace:GetAttribute("CC_StoryProbeStart")
	if t < 6.8 then task.wait(6.8 - t) end
	local sPos = (O * CFrame.new(-3, HRP_Y, -GAP)).Position
	S.hrp.CFrame = CFrame.lookAt(sPos, Vector3.new(stopP.X, sPos.Y, stopP.Z))
	P.tr.P:Play(0.3); S.tr.S:Play(0.3)
	task.wait(4.0)
	P.tr.P:Stop(0.4); S.tr.S:Stop(0.4)
	return "fertig"
end

return M
