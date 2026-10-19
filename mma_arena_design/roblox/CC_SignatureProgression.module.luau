-- Gemeinsame Definitionen fuer Trainer-Quests und Signatur-Endkaempfe.
local M = {}

M.ORDER = { "tyson", "ali", "pereira", "khabib", "saenchai", "oliveira" }
M.list = {
	tyson = {
		trainerId = "Mike_Tyson", trainerName = "Mike Tyson", signatureName = "PEEK-A-BOO COMBO",
		requirements = {
			{ key = "body", target = 15, label = "Land 15 clean body shots" },
			{ key = "counters", target = 5, label = "Land 5 counter hits" },
			{ key = "careerWins", target = 3, label = "Win 3 career fights" },
		},
		boss = {
			name = "Mike Tyson", style = "Peek-a-boo Boxing", aiStyle = "Boxer", difficulty = "champion", rounds = 3, rewardXP = 180,
			look = { hair = "none", beard = "none", face = "Face_Focused", skin = 4, hairColor = 1 },
			stats = { Power = 17, Cardio = 15, Wrestling = 11, Grappling = 10 },
		},
	},
	ali = {
		trainerId = "Muhammad_Ali", trainerName = "Muhammad Ali", signatureName = "INSTINCT MODE",
		requirements = {
			{ key = "jabs", target = 20, label = "Land 20 clean jabs" },
			{ key = "blocks", target = 8, label = "Block 8 attacks" },
			{ key = "careerWins", target = 3, label = "Win 3 career fights" },
		},
		boss = {
			name = "Muhammad Ali", style = "Dancing Boxing", aiStyle = "Boxer", difficulty = "champion", rounds = 3, rewardXP = 200,
			look = { hair = "Hair_ShortCurls", beard = "none", face = "Face_Focused", skin = 3, hairColor = 1 },
			stats = { Power = 14, Cardio = 19, Wrestling = 10, Grappling = 10 },
		},
	},
	pereira = {
		trainerId = "Alex_Pereira", trainerName = "Alex Pereira", signatureName = "STONE HAND COUNTER",
		requirements = {
			{ key = "counters", target = 8, label = "Land 8 hard counter hits" },
			{ key = "kicks", target = 20, label = "Land 20 clean kicks" },
			{ key = "careerWins", target = 4, label = "Win 4 career fights" },
		},
		boss = {
			name = "Alex Pereira", style = "Kickboxing", aiStyle = "Kickboxer", difficulty = "champion", rounds = 3, rewardXP = 220,
			look = { hair = "Hair_Buzzcut", beard = "none", face = "Face_Focused", skin = 3, hairColor = 1 },
			stats = { Power = 19, Cardio = 16, Wrestling = 10, Grappling = 9 },
		},
	},
	khabib = {
		trainerId = "Khabib_Nurmagomedov", trainerName = "Khabib Nurmagomedov", signatureName = "EAGLE SLAM",
		requirements = {
			{ key = "takedowns", target = 10, label = "Land 10 takedowns" },
			{ key = "groundHits", target = 20, label = "Land 20 ground hits" },
			{ key = "careerWins", target = 4, label = "Win 4 career fights" },
		},
		boss = {
			name = "Khabib Nurmagomedov", style = "Wrestling", aiStyle = "Wrestler", difficulty = "champion", rounds = 3, rewardXP = 240,
			look = { hair = "Hair_ShortCurls", beard = "Beard_Full", face = "Face_Focused", skin = 2, hairColor = 1 },
			stats = { Power = 15, Cardio = 18, Wrestling = 20, Grappling = 19 },
		},
	},
	saenchai = {
		trainerId = "Saenchai", trainerName = "Saenchai", signatureName = "WHEEL KICK",
		requirements = {
			{ key = "kicks", target = 30, label = "Land 30 clean kicks" },
			{ key = "counters", target = 6, label = "Land 6 counter hits" },
			{ key = "careerWins", target = 4, label = "Win 4 career fights" },
		},
		boss = {
			name = "Saenchai", style = "Muay Thai", aiStyle = "Kickboxer", difficulty = "champion", rounds = 3, rewardXP = 220,
			look = { hair = "Hair_SidePart", beard = "none", face = "Face_Friendly", skin = 3, hairColor = 1 },
			stats = { Power = 16, Cardio = 19, Wrestling = 12, Grappling = 13 },
		},
	},
	oliveira = {
		trainerId = "Charles_Oliveira", trainerName = "Charles Oliveira", signatureName = "BRONX CHOKE",
		requirements = {
			{ key = "groundHits", target = 20, label = "Land 20 ground hits" },
			{ key = "subs", target = 2, label = "Win 2 fights by submission" },
			{ key = "careerWins", target = 4, label = "Win 4 career fights" },
		},
		boss = {
			name = "Charles Oliveira", style = "Muay Thai / BJJ", aiStyle = "Grappler", difficulty = "champion", rounds = 3, rewardXP = 240,
			look = { hair = "Hair_QuiffV03", beard = "Beard_Short", face = "Face_Focused", skin = 2, hairColor = 3 },
			stats = { Power = 16, Cardio = 17, Wrestling = 17, Grappling = 20 },
		},
	},
}

function M.newProgress()
	local t = {}
	for _, id in ipairs(M.ORDER) do
		t[id] = { started = false, body = 0, counters = 0, jabs = 0, blocks = 0, kicks = 0, takedowns = 0, groundHits = 0, subs = 0, careerWins = 0, bossWins = 0 }
	end
	return t
end

function M.normalize(saved)
	local out = M.newProgress()
	if type(saved) ~= "table" then return out end
	for id, base in pairs(out) do
		local old = saved[id]
		if type(old) == "table" then
			base.started = old.started == true
			for k, v in pairs(base) do
				if k ~= "started" and tonumber(old[k]) then base[k] = math.max(0, math.floor(old[k])) end
			end
		end
	end
	return out
end

function M.ready(id, progress)
	local def = M.list[id]
	local p = progress and progress[id]
	if not def or not p or not p.started then return false end
	for _, req in ipairs(def.requirements) do
		if (tonumber(p[req.key]) or 0) < req.target then return false end
	end
	return true
end

return M
