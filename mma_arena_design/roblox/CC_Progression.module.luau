-- ReplicatedStorage.CC_Progression (ModuleScript)
-- Zentrale Definitionen fuer Ziele, Belohnungen und Level-Titel.
local M = {}

M.goals = {
	{ id = "daily_training_2", period = "day", counter = "training", title = "Complete 2 gym exercises", target = 2, xp = 20, icon = "dumbbell" },
	{ id = "daily_career_1", period = "day", counter = "career", title = "Finish 1 career fight", target = 1, xp = 30, icon = "glove" },
	{ id = "daily_fights_3", period = "day", counter = "fights", title = "Finish 3 fights", target = 3, xp = 40, icon = "fighter" },
	{ id = "weekly_fights_10", period = "week", counter = "fights", title = "Finish 10 fights this week", target = 10, xp = 150, icon = "star" },
}
M.goalById = {}
for _, def in ipairs(M.goals) do M.goalById[def.id] = def end

M.titles = {
	{ level = 1, title = "ROOKIE", reward = "Career and gym" },
	{ level = 2, title = "AMATEUR", reward = "Amateur profile badge" },
	{ level = 3, title = "PROSPECT", reward = "Prospect profile badge" },
	{ level = 5, title = "PRO", reward = "Pro profile badge" },
	{ level = 7, title = "CONTENDER", reward = "Contender profile badge" },
	{ level = 10, title = "CAGE CHAMPION", reward = "Champion profile badge" },
}

function M.dayKey(now)
	return os.date("!%Y-%m-%d", now or os.time())
end

function M.weekKey(now)
	return tostring(math.floor((now or os.time()) / 604800))
end

function M.titleForLevel(level)
	local current = M.titles[1]
	for _, def in ipairs(M.titles) do
		if level >= def.level then current = def else break end
	end
	return current.title
end

return M
