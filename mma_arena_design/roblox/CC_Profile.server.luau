-- ServerScriptService.CC_Profile
-- Spielerprofil mit Speicherung (DataStore "CC_Profiles_v1", Schluessel "u_<UserId>"):
--   Level, XP, Siege/Niederlagen/K.o./Submissions und 4 Kaempfer-Werte (0..20):
--   Power (Schlagkraft), Cardio (Kondition), Wrestling (Ringen), Grappling (Bodenkampf).
-- Jeder Wert steigt ueber eigene Trainingspunkte (10 Punkte = +1). Werte wirken im Kampf (siehe CC_CharacterAnimations).
-- Fuer HUD/Menue als Attribute am Spieler: CC_Level, CC_XP, CC_XPNext, CC_Wins, CC_Losses, CC_KOs, CC_Subs,
--   CC_Power/CC_Cardio/CC_Wrestling/CC_Grappling (Wert) und CC_PowerTP ... (Trainingspunkte 0..9), CC_ProfileSaved (bool).
-- Andere Skripte melden ueber ServerStorage.CC_ProfileEvent (BindableEvent):
--   Fire(player, "xp", menge) | Fire(player, "train", "Power"|"Cardio"|"Wrestling"|"Grappling", punkte) | Fire(player, "goal", zaehler, menge)
--   | Fire(player, "result", "win"|"loss"|"draw", methode) | Fire(player, "look", { hair=, beard=, face=, skin=, hairColor= })
-- Aussehen (CC_Customize liest es): Attribut CC_Look am Spieler (JSON).
-- Einstieg (CC_Tutorial): Tabelle onb = { editor, offered, lessons = {6 x bool}, done, firstFight } -> Attribut CC_Onb (JSON);
--   Fire(player, "onb", schluessel, wert) bzw. Fire(player, "onb", "lesson", nummer). Alte Profile ohne onb gelten als bekannte Spieler
--   (Editor und Angebot erledigt, Tutorial bleibt beim Trainer wiederholbar).
-- Speicherstand fuer die UI: Attribut CC_SaveStatus = "ok|<zeit>" | "error|<zeit>" | "offline|<zeit>" (nach jedem Speicherversuch).
-- Aussehen wird sofort gespeichert (hoechstens alle 7 s pro Spieler), alles andere alle 120 s und beim Verlassen.
-- Ohne DataStore-Zugriff (z. B. Studio ohne API-Freigabe) laeuft alles nur fuer die Sitzung.
local Players = game:GetService("Players")
local DSS = game:GetService("DataStoreService")
local SS = game:GetService("ServerStorage")

local STATS = { "Power", "Cardio", "Wrestling", "Grappling" }
local STAT_MAX, TP_PER_LEVEL = 20, 10
local SAVE_EVERY = 120
local XP_WIN, XP_LOSS, XP_DRAW, XP_FINISH = 60, 25, 35, 20

local store
do
	local ok, s = pcall(function() return DSS:GetDataStore("CC_Profiles_v1") end)
	store = ok and s or nil
	if not ok then warn("[CC] Profil: kein DataStore (" .. tostring(s) .. ") – Fortschritt nur fuer diese Sitzung") end
end

local RS = game:GetService("ReplicatedStorage")
local SIG = require(RS:WaitForChild("CC_Signatures"))
local OPP = require(RS:WaitForChild("CC_Opponents"))
local PROG = require(RS:WaitForChild("CC_Progression"))
local SIGPROG = require(RS:WaitForChild("CC_SignatureProgression"))
local event = SS:FindFirstChild("CC_ProfileEvent") or Instance.new("BindableEvent")
event.Name = "CC_ProfileEvent"; event.Parent = SS
local progressRemote = RS:FindFirstChild("CC_Progress") or Instance.new("RemoteEvent")
progressRemote.Name = "CC_Progress"; progressRemote.Parent = RS

local profiles = {}            -- [player] = Tabelle
local function default()
	local p = { v = 4, level = 1, xp = 0, wins = 0, losses = 0, kos = 0, subs = 0, stats = {}, tp = {},
		look = { hair = "Hair_QuiffV03", beard = "none", face = "Face_Focused", skin = 2, hairColor = 1, shorts = 1, gloves = 1 },
		onb = { editor = false, offered = false, lessons = { false, false, false, false, false, false }, done = false, firstFight = false, story = false, outro = false, careerTip = false,
			gymTour = false, sigTour = false, onlineHint = false, editorHint = false, focusTip = false },  -- Erklaerungen beim ersten Mal (alle Spieler einmal)
		sig = "", sigs = {}, sigProgress = SIGPROG.newProgress(), career = { beaten = {}, losses = 0 },
		goals = { day = PROG.dayKey(), week = PROG.weekKey(), counts = {}, claimed = {} }, -- Signaturen, Karriere und servergepruefte Ziele
		settings = { master = 0.8, music = 0.4, effects = 0.7, reduceFx = false, noShake = false } } -- Einstellungen (Menue), Client sendet CC_Progress "settings"
	for _, s in ipairs(STATS) do p.stats[s] = 0; p.tp[s] = 0 end
	return p
end
local function xpNext(level) return 100 + 50 * (level - 1) end

local function resetGoals(p)
	local day, week = PROG.dayKey(), PROG.weekKey()
	local changed = false
	if p.goals.day ~= day then
		p.goals.day = day; changed = true
		for _, def in ipairs(PROG.goals) do if def.period == "day" then p.goals.counts[def.id] = nil; p.goals.claimed[def.id] = nil end end
	end
	if p.goals.week ~= week then
		p.goals.week = week; changed = true
		for _, def in ipairs(PROG.goals) do if def.period == "week" then p.goals.counts[def.id] = nil; p.goals.claimed[def.id] = nil end end
	end
	if changed then p.dirty = true end
end

-- Belohnungen: neu freigeschaltete Shorts/Handschuhe melden (Vergleich mit dem letzten Stand, nur waehrend der Sitzung)
local LookS = require(RS:WaitForChild("CC_LookShared"))
local lastUnlocked = {}
local function rewardCheck(plr)
	local prog = LookS.progressOf(plr)
	local now, names = {}, {}
	for _, kind in ipairs({ { "SHORTS", "Shorts" }, { "GLOVES", "Handschuhe" } }) do
		for i, it in ipairs(LookS[kind[1]]) do
			if LookS.unlocked(it, prog) then
				local key = kind[1] .. i; now[key] = true
				if lastUnlocked[plr] and not lastUnlocked[plr][key] then table.insert(names, kind[2] .. " " .. it.name) end
			end
		end
	end
	lastUnlocked[plr] = now
	if #names > 0 then
		plr:SetAttribute("CC_Notice", "Newly unlocked: " .. table.concat(names, ", ") .. " (My Fighter)|" .. tostring(workspace:GetServerTimeNow()))
	end
end
Players.PlayerRemoving:Connect(function(plr) lastUnlocked[plr] = nil end)

local function publish(plr)
	local p = profiles[plr]; if not p then return end
	resetGoals(p)
	plr:SetAttribute("CC_Level", p.level); plr:SetAttribute("CC_XP", p.xp); plr:SetAttribute("CC_XPNext", xpNext(p.level))
	plr:SetAttribute("CC_Wins", p.wins); plr:SetAttribute("CC_Losses", p.losses); plr:SetAttribute("CC_KOs", p.kos); plr:SetAttribute("CC_Subs", p.subs)
	for _, s in ipairs(STATS) do plr:SetAttribute("CC_" .. s, p.stats[s]); plr:SetAttribute("CC_" .. s .. "TP", p.tp[s]) end
	plr:SetAttribute("CC_Look", game:GetService("HttpService"):JSONEncode(p.look))
	plr:SetAttribute("CC_Onb", game:GetService("HttpService"):JSONEncode(p.onb))
	plr:SetAttribute("CC_Signature", p.sig ~= "" and p.sig or nil)
	plr:SetAttribute("CC_SigUnlocked", table.concat(p.sigs, ","))
	plr:SetAttribute("CC_SigProgress", game:GetService("HttpService"):JSONEncode(p.sigProgress))
	plr:SetAttribute("CC_CareerBeaten", table.concat(p.career.beaten, ","))
	plr:SetAttribute("CC_CareerWins", #p.career.beaten)
	plr:SetAttribute("CC_CareerLosses", p.career.losses)
	plr:SetAttribute("CC_CareerNext", OPP.nextId(p.career.beaten))
	plr:SetAttribute("CC_CareerTitle", OPP.titleFor and OPP.titleFor(#p.career.beaten).name or nil)
	plr:SetAttribute("CC_RankTitle", PROG.titleForLevel(p.level))
	plr:SetAttribute("CC_MasterVolume", p.settings.master); plr:SetAttribute("CC_MusicVolume", p.settings.music); plr:SetAttribute("CC_EffectsVolume", p.settings.effects)
	plr:SetAttribute("CC_ReduceFX", p.settings.reduceFx); plr:SetAttribute("CC_NoShake", p.settings.noShake); plr:SetAttribute("CC_SettingsLoaded", true)
	plr:SetAttribute("CC_Goals", game:GetService("HttpService"):JSONEncode({
		day = p.goals.day, week = p.goals.week, counts = p.goals.counts, claimed = p.goals.claimed,
	}))
	rewardCheck(plr)
end

local function addXP(plr, n)
	local p = profiles[plr]; if not p or n <= 0 then return end
	p.xp += math.floor(n)
	while p.xp >= xpNext(p.level) do
		p.xp -= xpNext(p.level); p.level += 1
		plr:SetAttribute("CC_LevelUp", p.level)        -- Hinweis fuer das HUD
	end
	p.dirty = true; publish(plr)
end
local function train(plr, statName, points)
	local p = profiles[plr]; if not p or not p.stats[statName] then return end
	if p.stats[statName] >= STAT_MAX then return end
	p.tp[statName] += points
	while p.tp[statName] >= TP_PER_LEVEL and p.stats[statName] < STAT_MAX do
		p.tp[statName] -= TP_PER_LEVEL; p.stats[statName] += 1
		plr:SetAttribute("CC_StatUp", statName .. ":" .. p.stats[statName])
	end
	if p.stats[statName] >= STAT_MAX then p.tp[statName] = 0 end
	p.dirty = true; publish(plr)
end

-- Schluessel: "u_<UserId>". Test (Studio): workspace-Attribut CC_TestProfileKey = "<name>" -> eigener Testschluessel
-- "test_<name>_<UserId>" (echtes Speichern und Laden, echtes Profil bleibt unberuehrt)
local function keyOf(plr)
	local t = workspace:GetAttribute("CC_TestProfileKey")
	return (type(t) == "string" and t ~= "") and ("test_" .. t .. "_" .. plr.UserId) or ("u_" .. plr.UserId)
end
local function load(plr)
	local data
	if store then
		for i = 1, 3 do
			local ok, res = pcall(function() return store:GetAsync(keyOf(plr)) end)
			if ok then data = res; plr:SetAttribute("CC_ProfileSaved", true); break end
			warn("[CC] Profil laden fehlgeschlagen (" .. i .. "): " .. tostring(res)); task.wait(2 * i)
		end
	end
	-- Test (Studio): workspace-Attribut CC_TestNewPlayer = wie ein neuer Spieler, ohne Speichern (echtes Profil bleibt unberuehrt)
	--   Als Text (JSON) = Einstiegsstand zum Testen, z. B. {"editor":true,"offered":true,"lessons":[true,true,false,false,false,false]}
	local test = workspace:GetAttribute("CC_TestNewPlayer")
	if test then
		data = nil; plr:SetAttribute("CC_ProfileSaved", false)
		if type(test) == "string" then local ok, t = pcall(function() return game:GetService("HttpService"):JSONDecode(test) end); if ok and type(t) == "table" then data = { onb = t } end end
	end
	local p = default()
	if type(data) == "table" then
		for k, v in pairs(data) do if k ~= "stats" and k ~= "tp" and k ~= "look" and k ~= "onb" and k ~= "sigs" and k ~= "sig" and k ~= "sigProgress" and k ~= "career" and k ~= "goals" and k ~= "settings" and p[k] ~= nil then p[k] = v end end
		if type(data.settings) == "table" then for k, v in pairs(data.settings) do if p.settings[k] ~= nil and type(v) == type(p.settings[k]) then p.settings[k] = type(v) == "number" and math.clamp(v, 0, 1) or v end end end
		if type(data.onb) == "table" then
			for k, v in pairs(data.onb) do if k ~= "lessons" and type(p.onb[k]) == "boolean" and type(v) == "boolean" then p.onb[k] = v end end
			if type(data.onb.lessons) == "table" then for i = 1, 6 do p.onb.lessons[i] = data.onb.lessons[i] == true end end
			if data.onb.story == nil then p.onb.story = data.onb.editor == true end      -- Spieler vor dem Story-Einstieg: Film nicht nachholen
			if data.onb.outro == nil then p.onb.outro = data.onb.firstFight == true end
			if data.onb.careerTip == nil then p.onb.careerTip = data.onb.firstFight == true end
		else
			p.onb.editor = true; p.onb.offered = true; p.onb.firstFight = true; p.onb.story = true; p.onb.outro = true; p.onb.careerTip = true   -- bekannter Spieler aus der Zeit vor dem Einstieg
		end
		if type(data.sigs) == "table" then for _, id in ipairs(data.sigs) do if SIG.list[id] and not table.find(p.sigs, id) then table.insert(p.sigs, id) end end end
		if type(data.sig) == "string" and table.find(p.sigs, data.sig) then p.sig = data.sig end
		p.sigProgress = SIGPROG.normalize(data.sigProgress)
		if type(data.career) == "table" then
			p.career.losses = math.max(0, math.floor(tonumber(data.career.losses) or 0))
			local saved = {}
			if type(data.career.beaten) == "table" then for _, id in ipairs(data.career.beaten) do saved[id] = true end end
			for _, def in ipairs(OPP.list) do if saved[def.id] then table.insert(p.career.beaten, def.id) end end
		end
		if type(data.goals) == "table" then
			if type(data.goals.day) == "string" then p.goals.day = data.goals.day end
			if type(data.goals.week) == "string" then p.goals.week = data.goals.week end
			if type(data.goals.counts) == "table" then
				for id, value in pairs(data.goals.counts) do if PROG.goalById[id] and tonumber(value) then p.goals.counts[id] = math.max(0, math.floor(value)) end end
			end
			if type(data.goals.claimed) == "table" then
				for id, value in pairs(data.goals.claimed) do if PROG.goalById[id] and value == true then p.goals.claimed[id] = true end end
			end
		end
		if type(data.look) == "table" then for k, v in pairs(data.look) do if p.look[k] ~= nil and type(v) == type(p.look[k]) then p.look[k] = v end end end
		for _, s in ipairs(STATS) do
			if type(data.stats) == "table" and tonumber(data.stats[s]) then p.stats[s] = math.clamp(math.floor(data.stats[s]), 0, STAT_MAX) end
			if type(data.tp) == "table" and tonumber(data.tp[s]) then p.tp[s] = math.clamp(math.floor(data.tp[s]), 0, TP_PER_LEVEL - 1) end
		end
	end
	profiles[plr] = p
	publish(plr)
end
local function status(plr, s) if plr.Parent then plr:SetAttribute("CC_SaveStatus", s .. "|" .. tostring(workspace:GetServerTimeNow())) end end
-- Speichern: pro Spieler nie parallel (p.saving). Wer waehrenddessen speichern will, wartet auf den laufenden Vorgang
-- und speichert danach nur, wenn sich seitdem etwas geaendert hat (p.dirty). UpdateAsync mit bis zu 3 Versuchen (1 s / 2 s Pause).
local function save(plr)
	local p = profiles[plr]
	if not (store and p and plr:GetAttribute("CC_ProfileSaved")) then if p then status(plr, "offline") end; return false end   -- nie ein nicht geladenes Profil ueberschreiben
	while p.saving do task.wait(0.1) end
	if not p.dirty then return true end
	p.saving = true; p.dirty = false
	local copy = { v = p.v, level = p.level, xp = p.xp, wins = p.wins, losses = p.losses, kos = p.kos, subs = p.subs,
		stats = table.clone(p.stats), tp = table.clone(p.tp), look = table.clone(p.look),
		onb = { editor = p.onb.editor, offered = p.onb.offered, lessons = table.clone(p.onb.lessons), done = p.onb.done, firstFight = p.onb.firstFight, story = p.onb.story, outro = p.onb.outro, careerTip = p.onb.careerTip,
			gymTour = p.onb.gymTour, sigTour = p.onb.sigTour, onlineHint = p.onb.onlineHint, editorHint = p.onb.editorHint, focusTip = p.onb.focusTip },
		sig = p.sig, sigs = table.clone(p.sigs), sigProgress = SIGPROG.normalize(p.sigProgress), career = { beaten = table.clone(p.career.beaten), losses = p.career.losses },
		goals = { day = p.goals.day, week = p.goals.week, counts = table.clone(p.goals.counts), claimed = table.clone(p.goals.claimed) },
		settings = table.clone(p.settings) }
	local ok, err
	for i = 1, 3 do
		ok, err = pcall(function() store:UpdateAsync(keyOf(plr), function() return copy end) end)
		if ok then break end
		if i < 3 then task.wait(i) end
	end
	if ok then p.lastSave = os.clock() else p.dirty = true; warn("[CC] Profil " .. plr.UserId .. " nicht gespeichert (3 Versuche): " .. tostring(err)) end
	p.saving = false
	status(plr, ok and "ok" or "error")
	return ok
end
-- bald speichern (DataStore-Grenze: ein Schreibvorgang pro Schluessel alle ~6 s)
local function saveSoon(plr)
	local p = profiles[plr]; if not p or p.saveQueued then return end
	p.saveQueued = true
	task.delay(math.max(0, 7 - (os.clock() - (p.lastSave or -100))), function()
		p.saveQueued = false
		if profiles[plr] == p then save(plr) end
	end)
end

progressRemote.OnServerEvent:Connect(function(plr, action, id)
	if action == "settings" then                                 -- Einstellungen aus dem Menue: nur bekannte Schluessel, Zahlen 0..1
		local p = profiles[plr]; if not p or type(id) ~= "table" then return end
		local changed = false
		for k, v in pairs(id) do
			if p.settings[k] ~= nil and type(v) == type(p.settings[k]) then
				if type(v) == "number" then v = math.clamp(math.floor(v * 20 + 0.5) / 20, 0, 1) end
				if p.settings[k] ~= v then p.settings[k] = v; changed = true end
			end
		end
		if changed then p.dirty = true; publish(plr); saveSoon(plr) end
		return
	end
	local p, def = profiles[plr], type(id) == "string" and PROG.goalById[id] or nil
	if action ~= "claim" or not p or not def then return end
	resetGoals(p)
	local count = p.goals.counts[id] or 0
	if count < def.target or p.goals.claimed[id] then return end
	p.goals.claimed[id] = true; p.dirty = true
	addXP(plr, def.xp)
	publish(plr); saveSoon(plr)
	plr:SetAttribute("CC_GoalClaimed", id .. "|" .. tostring(workspace:GetServerTimeNow()))
end)

event.Event:Connect(function(plr, kind, a, b, c)
	if typeof(plr) ~= "Instance" or not plr:IsA("Player") or not profiles[plr] then return end
	if kind == "xp" then addXP(plr, tonumber(a) or 0)
	elseif kind == "train" then train(plr, a, tonumber(b) or 1)
	elseif kind == "look" and type(a) == "table" then
		local p = profiles[plr]
		for k, v in pairs(a) do if p.look[k] ~= nil and type(v) == type(p.look[k]) then p.look[k] = v end end
		p.dirty = true; publish(plr)
		saveSoon(plr)
	elseif kind == "onb" then
		local p = profiles[plr]
		if a == "lesson" and tonumber(b) and p.onb.lessons[tonumber(b)] ~= nil then p.onb.lessons[tonumber(b)] = true
		elseif type(a) == "string" and type(p.onb[a]) == "boolean" and type(b) == "boolean" then p.onb[a] = b
		else return end
		p.dirty = true; publish(plr)
		saveSoon(plr)
	elseif kind == "sig_start" and SIGPROG.list[a] then
		local p = profiles[plr]
		p.sigProgress[a] = p.sigProgress[a] or SIGPROG.newProgress()[a]
		p.sigProgress[a].started = true
		p.dirty = true; publish(plr); saveSoon(plr)
		plr:SetAttribute("CC_Notice", "Coach quest started.|" .. tostring(workspace:GetServerTimeNow()))
	elseif kind == "sig_fight_result" and type(a) == "table" then
		local p = profiles[plr]
		for id, def in pairs(SIGPROG.list) do
			local q = p.sigProgress[id]
			if q and q.started and not table.find(p.sigs, id) then
				q.body += math.max(0, math.floor(tonumber(a.body) or 0))
				q.counters += math.max(0, math.floor(tonumber(a.counters) or 0))
				q.jabs += math.max(0, math.floor(tonumber(a.jabs) or 0))
				q.blocks += math.max(0, math.floor(tonumber(a.blocks) or 0))
				q.kicks += math.max(0, math.floor(tonumber(a.kicks) or 0))
				q.takedowns += math.max(0, math.floor(tonumber(a.takedowns) or 0))
				q.groundHits += math.max(0, math.floor(tonumber(a.groundHits) or 0))
				q.subs += math.max(0, math.floor(tonumber(a.subs) or 0))
				if a.career == true and a.result == "win" then q.careerWins += 1 end
			end
		end
		p.dirty = true; publish(plr); saveSoon(plr)
	elseif kind == "sig_boss_result" and SIGPROG.list[a] and (b == "win" or b == "loss" or b == "draw") then
		local p, q = profiles[plr], profiles[plr].sigProgress[a]
		if b == "win" and SIGPROG.ready(a, p.sigProgress) then
			q.bossWins = (q.bossWins or 0) + 1
			if not table.find(p.sigs, a) then table.insert(p.sigs, a) end
			p.sig = a
			plr:SetAttribute("CC_Notice", SIGPROG.list[a].signatureName .. " unlocked!|" .. tostring(workspace:GetServerTimeNow()))
		end
		p.dirty = true; publish(plr); saveSoon(plr)
	elseif kind == "sig_unlock" and SIG.list[a] then
		-- Alte direkte Trainings-Freischaltung bleibt gesperrt; Signaturen kommen nur noch aus dem Trainer-Endkampf.
		return
	elseif kind == "sig_equip" then                                -- a = Schluessel oder "" (ablegen); nur Freigeschaltetes
		local p = profiles[plr]
		if a == "" or (SIG.list[a] and table.find(p.sigs, a)) then p.sig = a; p.dirty = true; publish(plr); saveSoon(plr) end
	elseif kind == "goal" and type(a) == "string" then
		local p, amount, changed = profiles[plr], math.clamp(math.floor(tonumber(b) or 1), 1, 100), false
		resetGoals(p)
		for _, def in ipairs(PROG.goals) do
			if def.counter == a then
				p.goals.counts[def.id] = math.min(def.target, (p.goals.counts[def.id] or 0) + amount)
				changed = true
			end
		end
		if changed then p.dirty = true; publish(plr); saveSoon(plr) end
	elseif kind == "career_result" and OPP.byId[a] and (b == "win" or b == "loss" or b == "draw") then
		local p, def = profiles[plr], OPP.byId[a]
		if b == "win" then
			p.wins += 1
			if c == "K.O." then p.kos += 1 elseif c == "Submission" then p.subs += 1 end
			if not table.find(p.career.beaten, a) then
				local before = OPP.titleFor(#p.career.beaten)
				table.insert(p.career.beaten, a)
				local after = OPP.titleFor(#p.career.beaten)
				if after ~= before then                                  -- neuer Karriere-Titel: einmalige Belohnung
					addXP(plr, after.bonusXP or 0)
					plr:SetAttribute("CC_Notice", ("New title: %s  (+%d XP)|%s"):format(after.name, after.bonusXP or 0, tostring(workspace:GetServerTimeNow())))
				end
			end
		elseif b == "loss" then p.losses += 1; p.career.losses += 1 end
		local xp = b == "win" and (def.rewardXP + ((c == "K.O." or c == "Submission") and XP_FINISH or 0)) or (b == "draw" and XP_DRAW or 20)
		addXP(plr, xp)
		p.dirty = true; publish(plr); saveSoon(plr)
		plr:SetAttribute("CC_CareerAdvance", a .. "|" .. b .. "|" .. tostring(workspace:GetServerTimeNow()))
		if not p.onb.careerTip then                                   -- erster offizieller Kampf: Belohnungen kurz erklaeren (auch nach Niederlage)
			p.onb.careerTip = true
			local text = b == "win" and ("First career win! +%d XP. More XP = higher level, new opponents unlock."):format(xp)
				or ("+%d XP even without a win. Train in the gym and try again – your career goes on."):format(xp)
			plr:SetAttribute("CC_CoachTip", game:GetService("HttpService"):JSONEncode({ text = text, kind = b == "win" and "good" or "tip", t = workspace:GetServerTimeNow() }))
		end
	elseif kind == "result" then
		local p = profiles[plr]
		if a == "win" then
			p.wins += 1
			if b == "K.O." then p.kos += 1 elseif b == "Submission" then p.subs += 1 end
			addXP(plr, XP_WIN + ((b == "K.O." or b == "Submission") and XP_FINISH or 0))
		elseif a == "loss" then p.losses += 1; addXP(plr, XP_LOSS)
		else addXP(plr, XP_DRAW) end
		p.dirty = true; publish(plr)
	end
end)

Players.PlayerAdded:Connect(load)
for _, plr in ipairs(Players:GetPlayers()) do task.spawn(load, plr) end
-- Verlassen und Server-Ende: jeder Spieler wird hoechstens einmal zusaetzlich gespeichert (save wartet auf laufende Vorgaenge, ohne Aenderung kein Schreiben)
local pending = 0
local function finalSave(plr)
	local p = profiles[plr]; if not p or p.closing then return end
	p.closing = true; pending += 1
	save(plr)
	pending -= 1
	if profiles[plr] == p then profiles[plr] = nil end
end
Players.PlayerRemoving:Connect(finalSave)
game:BindToClose(function()
	for plr in pairs(profiles) do task.spawn(finalSave, plr) end
	local t0 = os.clock()
	while pending > 0 and os.clock() - t0 < 25 do task.wait(0.1) end
end)
task.spawn(function()
	while true do
		task.wait(SAVE_EVERY)
		for plr, p in pairs(profiles) do if p.dirty and not p.closing then task.spawn(save, plr) end end
	end
end)
