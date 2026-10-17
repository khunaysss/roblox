-- Gemeinsame Definitionen fuer Trainer-Quests und Signatur-Endkaempfe.
local M = {}

M.ORDER = { "tyson", "ali", "pereira", "khabib", "saenchai", "oliveira" }
M.list = {
	tyson = {
		trainerId = "Mike_Tyson", trainerName = "Mike Tyson", signatureName = "PEEK-A-BOO KOMBINATION",
		requirements = {
			{ key = "body", target = 15, label = "15 klare Koerpertreffer landen" },
			{ key = "counters", target = 5, label = "5 Kontertreffer landen" },
			{ key = "careerWins", target = 3, label = "3 Karrierekaempfe gewinnen" },
		},
		boss = {
			name = "Mike Tyson", style = "Peek-a-boo Boxen", aiStyle = "Boxer", difficulty = "champion", rounds = 3, rewardXP = 180,
			look = { hair = "none", beard = "none", face = "Face_Focused", skin = 4, hairColor = 1 },
			stats = { Power = 17, Cardio = 15, Wrestling = 11, Grappling = 10 },
		},
	},
	ali = {
		trainerId = "Muhammad_Ali", trainerName = "Muhammad Ali", signatureName = "INSTINKT-MODUS",
		requirements = {
			{ key = "jabs", target = 20, label = "20 Jabs sauber landen" },
			{ key = "blocks", target = 8, label = "8 Angriffe erfolgreich blocken" },
			{ key = "careerWins", target = 3, label = "3 Karrierekaempfe gewinnen" },
		},
		boss = {
			name = "Muhammad Ali", style = "Taenzelndes Boxen", aiStyle = "Boxer", difficulty = "champion", rounds = 3, rewardXP = 200,
			look = { hair = "Hair_ShortCurls", beard = "none", face = "Face_Focused", skin = 3, hairColor = 1 },
			stats = { Power = 14, Cardio = 19, Wrestling = 10, Grappling = 10 },
		},
	},
	pereira = {
		trainerId = "Alex_Pereira", trainerName = "Alex Pereira", signatureName = "STEINHAND-KONTER",
		requirements = {
			{ key = "counters", target = 8, label = "8 harte Kontertreffer landen" },
			{ key = "kicks", target = 20, label = "20 Kicks sauber landen" },
			{ key = "careerWins", target = 4, label = "4 Karrierekaempfe gewinnen" },
		},
		boss = {
			name = "Alex Pereira", style = "Kickboxen", aiStyle = "Kickboxer", difficulty = "champion", rounds = 3, rewardXP = 220,
			look = { hair = "Hair_Buzzcut", beard = "none", face = "Face_Focused", skin = 3, hairColor = 1 },
			stats = { Power = 19, Cardio = 16, Wrestling = 10, Grappling = 9 },
		},
	},
	khabib = {
		trainerId = "Khabib_Nurmagomedov", trainerName = "Khabib Nurmagomedov", signatureName = "EAGLE DOUBLE-LEG",
		requirements = {
			{ key = "takedowns", target = 10, label = "10 Takedowns landen" },
			{ key = "groundHits", target = 20, label = "20 Bodentreffer landen" },
			{ key = "careerWins", target = 4, label = "4 Karrierekaempfe gewinnen" },
		},
		boss = {
			name = "Khabib Nurmagomedov", style = "Ringen", aiStyle = "Wrestler", difficulty = "champion", rounds = 3, rewardXP = 240,
			look = { hair = "Hair_ShortCurls", beard = "Beard_Full", face = "Face_Focused", skin = 2, hairColor = 1 },
			stats = { Power = 15, Cardio = 18, Wrestling = 20, Grappling = 19 },
		},
	},
	saenchai = {
		trainerId = "Saenchai", trainerName = "Saenchai", signatureName = "FINTEN-TEEP",
		requirements = {
			{ key = "kicks", target = 30, label = "30 Kicks sauber landen" },
			{ key = "counters", target = 6, label = "6 Kontertreffer landen" },
			{ key = "careerWins", target = 4, label = "4 Karrierekaempfe gewinnen" },
		},
		boss = {
			name = "Saenchai", style = "Muay Thai", aiStyle = "Kickboxer", difficulty = "champion", rounds = 3, rewardXP = 220,
			look = { hair = "Hair_SidePart", beard = "none", face = "Face_Friendly", skin = 3, hairColor = 1 },
			stats = { Power = 16, Cardio = 19, Wrestling = 12, Grappling = 13 },
		},
	},
	oliveira = {
		trainerId = "Charles_Oliveira", trainerName = "Charles Oliveira", signatureName = "CHUTE BOXE KICK",
		requirements = {
			{ key = "groundHits", target = 20, label = "20 Bodentreffer landen" },
			{ key = "subs", target = 2, label = "2 Kaempfe per Submission gewinnen" },
			{ key = "careerWins", target = 4, label = "4 Karrierekaempfe gewinnen" },
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
