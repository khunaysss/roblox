-- build_emote_takethel_v03.luau  (Studio, Edit-Modus; nutzt ServerStorage.CC_EmoteBuilder = Rechenkern aus build_emotes_v01.luau)
-- Emote_TakeTheL_v3: nach Referenzvideo (Ablauf/Takt, eigene Umsetzung): rechte Hand als "L" an der Stirn, linker Arm angewinkelt
-- vor dem Bauch; im Wechsel alle 0,5 s Knie hoch -> weiter Diagonaltritt nach vorn-aussen -> zurueck, Standbein hopst, Oberkoerper
-- leicht zurueck und vom Trittbein weg. 4,0 s, kein Anlauf. CC_EmoteConfig: take_the_l -> Emote_TakeTheL_v3.
local B = require(game.ServerStorage.CC_EmoteBuilder)
local V = Vector3.new
local LF, RF = B.LF, B.RF
local function sm(x) x = math.clamp(x, 0, 1) return x * x * (3 - 2 * x) end
local CYC = 0.5
B.build("Emote_TakeTheL_v3", 4.0, false, function(t)
	local P = B.neutral()
	local k = math.floor(t / CYC); local u = (t % CYC) / CYC
	local s = (k % 2 == 0) and 1 or -1
	local tuck = sm(u / 0.28) * (1 - sm((u - 0.28) / 0.2))
	local kick = sm((u - 0.28) / 0.18) * (1 - sm((u - 0.62) / 0.33))
	local lift = math.max(tuck, kick)
	local hop = math.sin(math.min(u / 0.65, 1) * math.pi)
	local fRest = s > 0 and RF or LF
	local tuckPos = fRest + V(s * 0.25, 1.75, -0.8)
	local kickPos = fRest + V(s * 1.75, 1.65, -1.05)
	local foot = fRest:Lerp(tuckPos, tuck):Lerp(kickPos, kick)
	local sup = V(0, hop * 0.28, 0)
	if s > 0 then P.FR = foot + sup; P.FL = LF + sup else P.FL = foot + sup; P.FR = RF + sup end
	P.hip = V(-s * 0.18, -0.2 + hop * 0.28, 0.08 * lift)
	P.follow = V(-s * 0.18, -0.12 + hop * 0.28, 0)
	P.lt = V(6 * lift, s * 18 * lift, -s * 10 * lift)
	P.ut = V(9 + 4 * lift, -s * 10 * lift, s * 4 * lift)
	P.hd = V(5, -s * 8 * lift, 6)
	P.R = V(0.4, 3.12, -0.58); P.Rp = V(1.3, -0.1, 0.3); P.Rh = V(0, 25, -80)
	P.L = V(-0.2, 1.5, -0.78); P.Lp = V(-1, -0.4, 0.3); P.Lh = V(0, 0, 10)
	return P
end)
