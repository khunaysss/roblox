-- build_emotes_v01.luau  (in Studio im Edit-Modus ausfuehren; ueberschreibt nichts Fremdes)
-- Erzeugt 8 Emote-KeyframeSequences in ServerStorage.CC_Animations (Emote_*), direkt auf dem Bone-Rig von StarterCharacter.
-- Posen in Charakter-Achsen (Blick -Z, rechts +X, oben +Y): Rumpf/Kopf als FK, Arme und Beine per Zwei-Knochen-IK auf
-- Handgelenk-/Knoechel-Ziele (Fuesse bleiben stehen, keine Ortsveraenderung). 30 fps.
local A = game.ServerStorage.CC_Animations
local sc = game.StarterPlayer.StarterCharacter
local hrp = sc.HumanoidRootPart
local V = Vector3.new
local rad = math.rad

local bones, parentOf = {}, {}
for _, b in ipairs(hrp:GetDescendants()) do
	if b:IsA("Bone") then bones[b.Name] = b; parentOf[b.Name] = b.Parent:IsA("Bone") and b.Parent.Name or nil end
end
local ORDER = { "Root", "LowerTorso", "UpperTorso", "Head", "LeftUpperArm", "LeftLowerArm", "LeftHand", "RightUpperArm", "RightLowerArm", "RightHand",
	"LeftUpperLeg", "LeftLowerLeg", "LeftFoot", "RightUpperLeg", "RightLowerLeg", "RightFoot" }
local REST = {}
local function restW(n)
	if REST[n] then return REST[n] end
	local p = parentOf[n]
	local w = (p and restW(p) or CFrame.new()) * bones[n].CFrame
	REST[n] = w; return w
end
for _, n in ipairs(ORDER) do restW(n) end
local function len(a, b) return (REST[b].Position - REST[a].Position).Magnitude end
local L1, L2 = len("LeftUpperArm", "LeftLowerArm"), len("LeftLowerArm", "LeftHand")
local G1, G2 = len("LeftUpperLeg", "LeftLowerLeg"), len("LeftLowerLeg", "LeftFoot")

local function R(v) v = v or Vector3.zero; return CFrame.Angles(rad(v.X), rad(v.Y), rad(v.Z)) end
local function swing(a, b)
	local d = math.clamp(a:Dot(b), -1, 1)
	if d > 0.99999 then return CFrame.new() end
	local axis = a:Cross(b)
	if axis.Magnitude < 1e-6 then axis = Vector3.yAxis end
	return CFrame.fromAxisAngle(axis.Unit, math.acos(d))
end
local function ik(S, W, l1, l2, pole)
	local d = W - S
	local dist = math.clamp(d.Magnitude, 0.05, (l1 + l2) * 0.999)
	local dir = d.Unit
	local a = math.acos(math.clamp((l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist), -1, 1))
	local perp = pole - dir * pole:Dot(dir)
	perp = perp.Magnitude > 1e-4 and perp.Unit or Vector3.yAxis:Cross(dir).Unit
	local E = S + (dir * math.cos(a) + perp * math.sin(a)) * l1
	local Wc = S + dir * dist
	return (E - S).Unit, (Wc - E).Unit
end

-- Neutrale Standpose
local function neutral()
	return { hip = V(0, -0.06, 0), lt = V(), ut = V(), hd = V(),
		L = V(-1.3, 0.42, -0.12), R = V(1.3, 0.42, -0.12), Lp = V(-1, 0, 0.6), Rp = V(1, 0, 0.6), Lh = V(), Rh = V(),
		FL = REST.LeftFoot.Position, FR = REST.RightFoot.Position, follow = V() }
end
local function mixv(a, b, w) return a:Lerp(b, w) end
local function mix(a, b, w)
	local o = {}
	for k, v in pairs(a) do o[k] = mixv(v, b[k] or v, w) end
	return o
end

-- Pose -> Transform je Bone
local function solve(P)
	local W, D, T = {}, {}, {}
	local function place(n, delta, extraPos)
		local p = parentOf[n]
		local base = (p and W[p] or CFrame.new()) * bones[n].CFrame
		local want = CFrame.new(base.Position + (extraPos or Vector3.zero)) * delta.Rotation * REST[n].Rotation
		W[n] = want; D[n] = delta
		T[n] = base:Inverse() * want
	end
	place("Root", CFrame.new())
	place("LowerTorso", R(P.lt), P.hip)
	place("UpperTorso", D.LowerTorso * R(P.ut))
	place("Head", D.UpperTorso * R(P.hd))
	for _, s in ipairs({ "Left", "Right" }) do
		local up, lo, hand = s .. "UpperArm", s .. "LowerArm", s .. "Hand"
		local S = ((W.UpperTorso) * bones[up].CFrame).Position
		local u0 = (REST[lo].Position - REST[up].Position).Unit
		local f0 = (REST[hand].Position - REST[lo].Position).Unit
		local tgt = (s == "Left" and P.L or P.R) + P.follow
		local uD, fD = ik(S, tgt, L1, L2, s == "Left" and P.Lp or P.Rp)
		local dU = swing(D.UpperTorso * u0, uD) * D.UpperTorso
		place(up, dU)
		local dL = swing(dU * f0, fD) * dU
		place(lo, dL)
		place(hand, dL * R(s == "Left" and P.Lh or P.Rh))
		local th, sh = s .. "UpperLeg", s .. "LowerLeg"
		local ft = s .. "Foot"
		local H = (W.LowerTorso * bones[th].CFrame).Position
		local g0 = (REST[sh].Position - REST[th].Position).Unit
		local k0 = (REST[ft].Position - REST[sh].Position).Unit
		local fT = s == "Left" and P.FL or P.FR
		local gD, kD = ik(H, fT, G1, G2, V(s == "Left" and -0.15 or 0.15, 0, -1))
		local dG = swing(D.LowerTorso * g0, gD) * D.LowerTorso
		place(th, dG)
		local dK = swing(dG * k0, kD) * dG
		place(sh, dK)
		place(ft, CFrame.new())                                  -- Fuss bleibt flach
	end
	return T
end

local function smooth(x) x = math.clamp(x, 0, 1); return x * x * (3 - 2 * x) end
local function env(t, D, a, b) return smooth(math.min(t / a, (D - t) / b)) end
local function seg(t, a, b) return smooth((t - a) / (b - a)) end
local TAU = math.pi * 2
local LF, RF = REST.LeftFoot.Position, REST.RightFoot.Position

local E = {}
-- 1 Cry About It: beide Faeuste reiben die Augen, Schultern zucken
E.Emote_CryAboutIt = { D = 3.2, loop = false, f = function(t, D)
	local P = neutral(); local ph = t * TAU * 3.2
	P.ut = V(-10, 0, math.sin(t * TAU * 3) * 4); P.hd = V(-12, math.sin(t * TAU * 1.5) * 8, -math.sin(t * TAU * 3) * 5)
	P.hip = V(0, -0.1 - math.abs(math.sin(t * TAU * 3)) * 0.03, 0)
	P.L = V(-0.3, 2.5, -0.95) + V(math.cos(ph) * 0.09, math.sin(ph) * 0.09, 0)
	P.R = V(0.3, 2.5, -0.95) + V(math.cos(ph + math.pi) * 0.09, math.sin(ph + math.pi) * 0.09, 0)
	P.Lp, P.Rp = V(-1, -1, 0.2), V(1, -1, 0.2)
	return mix(neutral(), P, env(t, D, 0.3, 0.35))
end }
-- 2 Keep Talking: Hand an der Huefte, andere Hand "plappert" neben dem Kopf, gelangweilt
E.Emote_KeepTalking = { D = 3.4, loop = false, f = function(t, D)
	local P = neutral()
	P.hip = V(0.14, -0.08, 0); P.lt = V(0, 8, -3); P.ut = V(4, 0, 4); P.hd = V(4, -8, 12 + math.sin(t * TAU * 0.5) * 3)
	P.L = V(-1.0, 1.0, 0.18); P.Lp = V(-1, 0, 0.4); P.Lh = V(0, 0, 30)
	P.R = V(1.0, 2.62, -0.8); P.Rp = V(1, -0.6, 0.4)
	P.Rh = V(math.max(0, math.sin(t * TAU * 4.5)) * 32 - 8, 0, 0)
	return mix(neutral(), P, env(t, D, 0.3, 0.35))
end }
-- 3 Go To Sleep: Haende zusammen an der Wange, Kopf darauf, ruhiges Atmen (Loop im Gym)
E.Emote_GoToSleep = { D = 3.6, loop = true, f = function(t, D)
	local P = neutral(); local br = math.sin(t * TAU / 1.8)
	P.hip = V(0.05, -0.08 + br * 0.015, 0); P.ut = V(-3 + br * 2, 0, -6); P.hd = V(-4, -6, -24)
	P.R = V(0.72, 2.5, -0.62); P.L = V(0.36, 2.42, -0.78); P.Rp = V(1, -1, 0.2); P.Lp = V(-0.4, -1, 0.3)
	P.Rh = V(0, 0, -20); P.Lh = V(0, 0, -20)
	return P
end }
-- 4 Take the L: Faust an der Stirn, anderer Arm als grosses "L", freche Schritte
E.Emote_TakeTheL = { D = 3.6, loop = false, f = function(t, D)
	local P = neutral(); local s = math.sin(t * TAU * 1.0); local b = math.abs(math.sin(t * TAU * 1.0))
	P.hip = V(s * 0.22, -0.12 - b * 0.07, 0); P.follow = V(s * 0.22, 0, 0)
	P.lt = V(0, s * 10, -s * 4); P.ut = V(-2, -s * 6, s * 3); P.hd = V(0, 0, s * 9)
	P.R = V(0.12, 2.95, -0.95); P.Rp = V(1, -0.8, 0)
	P.L = V(-2.0, 2.95, -0.1); P.Lp = V(-0.3, -1, 0.3)
	P.FL = LF + V(0, math.max(0, s) * 0.28, 0); P.FR = RF + V(0, math.max(0, -s) * 0.28, 0)
	return mix(neutral(), P, env(t, D, 0.3, 0.35))
end }
-- 5 Champ Walk: Brust raus, Kinn hoch, breite schwingende Arme, Schritte auf der Stelle (Loop im Gym)
E.Emote_ChampWalk = { D = 3.0, loop = true, f = function(t, D)
	local P = neutral(); local s = math.sin(t * TAU / 1.0); local c = math.abs(math.cos(t * TAU / 1.0))
	P.hip = V(s * 0.08, -0.1 - c * 0.06, 0); P.lt = V(0, s * 14, 0); P.ut = V(9, -s * 6, 0); P.hd = V(7, -s * 8, 0)
	P.L = V(-1.75, 0.95, -0.15 + s * 0.55); P.R = V(1.75, 0.95, -0.15 - s * 0.55)
	P.Lp = V(-1, 0, 0.8); P.Rp = V(1, 0, 0.8)
	P.FL = LF + V(0, math.max(0, s) * 0.3, 0); P.FR = RF + V(0, math.max(0, -s) * 0.3, 0)
	return P
end }
-- 6 Stone Face: starr, Arme unten, langsame Kopfdrehung nach vorn zum Gegner
E.Emote_StoneFace = { D = 3.6, loop = false, f = function(t, D)
	local P = neutral(); local turn = seg(t, 0.7, 2.6)
	P.hip = V(0, -0.04, 0); P.ut = V(2 + math.sin(t * TAU / 2.4) * 0.8, 0, 0)
	P.hd = V(-6 * turn, 40 * (1 - turn), 0)
	P.L = V(-1.18, 0.4, 0.02); P.R = V(1.18, 0.4, 0.02); P.Lp = V(-0.2, 0, 1); P.Rp = V(0.2, 0, 1)
	return mix(neutral(), P, env(t, D, 0.35, 0.4))
end }
-- 7 Bow Shot: imaginaeren Bogen heben, Sehne zur Wange ziehen, zielen, loslassen, nachschwingen
E.Emote_BowShot = { D = 3.6, loop = false, f = function(t, D)
	local P = neutral()
	local raise, draw, rel, back = seg(t, 0.1, 0.6), seg(t, 0.6, 1.4), seg(t, 2.0, 2.12), seg(t, 2.8, 3.5)
	local turn = raise * (1 - back)
	P.lt = V(0, -18 * turn, 0); P.ut = V(0, -22 * turn, 0); P.hd = V(-3 * turn, 36 * turn, 0)
	P.hip = V(0, -0.1 * turn, 0)
	local bow = V(-0.4, 2.45, -2.45) + V(0, 0, rel * 0.08 * (1 - seg(t, 2.12, 2.5)))
	local tremble = (t > 1.4 and t < 2.0) and V(math.sin(t * 60) * 0.01, 0, 0) or Vector3.zero
	P.L = neutral().L:Lerp(bow, turn) + tremble; P.Lp = V(-1, -0.5, 0.5)
	local nock, cheek, after = V(0.2, 2.2, -0.9), V(0.25, 2.7, -0.25), V(0.9, 2.65, 0.35)
	local r = nock:Lerp(cheek, draw):Lerp(after, rel)
	P.R = neutral().R:Lerp(r, turn); P.Rp = V(1, -0.2, 0.6)
	P.Rh = V(0, 0, -30 * rel)
	P.FL = LF + V(0.05, 0, -0.25) * turn; P.FR = RF + V(0.1, 0, 0.3) * turn
	return P
end }
-- 8 Dust Off: Schultern abklopfen (erst links, dann rechts), dann selbstsicher zuruecklehnen
E.Emote_DustOff = { D = 3.4, loop = false, f = function(t, D)
	local P = neutral(); local n = neutral()
	local a1, a2, lean = math.clamp((t - 0.2) / 1.1, 0, 1), math.clamp((t - 1.3) / 1.1, 0, 1), seg(t, 2.4, 2.8) * (1 - seg(t, 3.05, 3.4))
	local s1 = (a1 > 0 and a1 < 1) and (math.sin(a1 * TAU * 2 - math.pi / 2) + 1) / 2 or 0
	local s2 = (a2 > 0 and a2 < 1) and (math.sin(a2 * TAU * 2 - math.pi / 2) + 1) / 2 or 0
	local w1, w2 = smooth(math.min(a1 * 6, (1 - a1) * 6)), smooth(math.min(a2 * 6, (1 - a2) * 6))
	P.R = n.R:Lerp(V(-0.5, 2.42, -0.62):Lerp(V(-1.15, 2.2, -0.3), s1), w1); P.Rp = V(1, -1, 0.3)
	P.L = n.L:Lerp(V(0.5, 2.42, -0.62):Lerp(V(1.15, 2.2, -0.3), s2), w2); P.Lp = V(-1, -1, 0.3)
	P.hd = V(-10 * (w1 + w2) + 8 * lean, 25 * w1 - 25 * w2, 0)
	P.ut = V(9 * lean, 0, 0); P.lt = V(3 * lean, 0, 0); P.hip = V(0, -0.06, -0.08 * lean)
	P.L = P.L:Lerp(V(-1.45, 0.55, 0.1), lean * (1 - w2)); P.R = P.R:Lerp(V(1.45, 0.55, 0.1), lean * (1 - w1))
	return P
end }

local FPS = 30
local made = {}
for name, def in pairs(E) do
	local old = A:FindFirstChild(name); if old then old:Destroy() end
	local ks = Instance.new("KeyframeSequence"); ks.Name = name; ks.Loop = def.loop; ks.Priority = Enum.AnimationPriority.Action2
	local frames = math.floor(def.D * FPS + 0.5)
	for i = 0, frames do
		local t = i / FPS
		local T = solve(def.f(t, def.D))
		local kf = Instance.new("Keyframe"); kf.Time = t
		local top = Instance.new("Pose"); top.Name = "HumanoidRootPart"; top.Weight = 0; top.Parent = kf
		local poses = {}
		for _, n in ipairs(ORDER) do
			local p = Instance.new("Pose"); p.Name = n; p.Weight = 1; p.CFrame = T[n] or CFrame.new()
			poses[n] = p
		end
		for _, n in ipairs(ORDER) do poses[n].Parent = parentOf[n] and poses[parentOf[n]] or top end
		kf.Parent = ks
	end
	ks.Parent = A
	table.insert(made, name .. "(" .. frames .. ")")
end
return table.concat(made, ", ")
