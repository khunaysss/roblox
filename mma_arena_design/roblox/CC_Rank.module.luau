-- ReplicatedStorage.CC_Rank (ModuleScript)
-- Online-Ranking: nur Kaempfe gegen echte Spieler (CC_Match Modus "pvp"). Sieg +25, Niederlage -15, Unentschieden 0, nie unter 0.
-- Stufen: Bronze 0, Silver 200, Gold 500, Platinum 900, Champion 1400. Punkte liegen im Profil (rank.points), Server-only veraenderbar.
local M = {}

M.WIN, M.LOSS, M.DRAW = 25, -15, 0
M.MAX_POINTS = 99999
M.TIERS = {
	{ name = "Bronze", min = 0, color = Color3.fromRGB(176, 112, 64) },
	{ name = "Silver", min = 200, color = Color3.fromRGB(180, 186, 196) },
	{ name = "Gold", min = 500, color = Color3.fromRGB(232, 182, 70) },
	{ name = "Platinum", min = 900, color = Color3.fromRGB(120, 210, 226) },
	{ name = "Champion", min = 1400, color = Color3.fromRGB(224, 36, 54) },
}

-- Stufe zu einer Punktzahl; zweiter Rueckgabewert = naechste Stufe (nil beim Champion)
function M.tierOf(points)
	points = math.max(0, math.floor(tonumber(points) or 0))
	local tier, nextTier = M.TIERS[1], nil
	for i, t in ipairs(M.TIERS) do
		if points >= t.min then tier = t; nextTier = M.TIERS[i + 1] end
	end
	return tier, nextTier
end

-- neue Punktzahl nach einem Ergebnis ("win" | "loss" | "draw")
function M.apply(points, result)
	points = math.max(0, math.floor(tonumber(points) or 0))
	local delta = result == "win" and M.WIN or result == "loss" and M.LOSS or M.DRAW
	return math.clamp(points + delta, 0, M.MAX_POINTS)
end

function M.colorOf(tierName)
	for _, t in ipairs(M.TIERS) do if t.name == tierName then return t.color end end
	return M.TIERS[1].color
end

return M
