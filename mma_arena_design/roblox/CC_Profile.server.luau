-- ServerScriptService.CC_Profile
-- Spielerprofil mit Speicherung (DataStore "CC_Profiles_v1", Schluessel "u_<UserId>"):
--   Level, XP, Siege/Niederlagen/K.o./Submissions und 4 Kaempfer-Werte (0..20):
--   Power (Schlagkraft), Cardio (Kondition), Wrestling (Ringen), Grappling (Bodenkampf).
-- Jeder Wert steigt ueber eigene Trainingspunkte (10 Punkte = +1). Werte wirken im Kampf (siehe CC_CharacterAnimations).
-- Fuer HUD/Menue als Attribute am Spieler: CC_Level, CC_XP, CC_XPNext, CC_Wins, CC_Losses, CC_KOs, CC_Subs,
--   CC_Power/CC_Cardio/CC_Wrestling/CC_Grappling (Wert) und CC_PowerTP ... (Trainingspunkte 0..9), CC_ProfileSaved (bool).
-- Andere Skripte melden ueber ServerStorage.CC_ProfileEvent (BindableEvent):
--   Fire(player, "xp", menge) | Fire(player, "train", "Power"|"Cardio"|"Wrestling"|"Grappling", punkte)
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

local SIG = require(game:GetService("ReplicatedStorage"):WaitForChild("CC_Signatures"))
local event = SS:FindFirstChild("CC_ProfileEvent") or Instance.new("BindableEvent")
event.Name = "CC_ProfileEvent"; event.Parent = SS

local profiles = {}            -- [player] = Tabelle
local function default()
	local p = { v = 1, level = 1, xp = 0, wins = 0, losses = 0, kos = 0, subs = 0, stats = {}, tp = {},
		look = { hair = "Hair_QuiffV03", beard = "none", face = "Face_Focused", skin = 2, hairColor = 1 },
		onb = { editor = false, offered = false, lessons = { false, false, false, false, false, false }, done = false, firstFight = false },
		sig = "", sigs = {} }                     -- Signaturen: ausgeruestet (Schluessel aus CC_Signatures.list oder "") und freigeschaltet (Liste)
	for _, s in ipairs(STATS) do p.stats[s] = 0; p.tp[s] = 0 end
	return p
end
local function xpNext(level) return 100 + 50 * (level - 1) end

local function publish(plr)
	local p = profiles[plr]; if not p then return end
	plr:SetAttribute("CC_Level", p.level); plr:SetAttribute("CC_XP", p.xp); plr:SetAttribute("CC_XPNext", xpNext(p.level))
	plr:SetAttribute("CC_Wins", p.wins); plr:SetAttribute("CC_Losses", p.losses); plr:SetAttribute("CC_KOs", p.kos); plr:SetAttribute("CC_Subs", p.subs)
	for _, s in ipairs(STATS) do plr:SetAttribute("CC_" .. s, p.stats[s]); plr:SetAttribute("CC_" .. s .. "TP", p.tp[s]) end
	plr:SetAttribute("CC_Look", game:GetService("HttpService"):JSONEncode(p.look))
	plr:SetAttribute("CC_Onb", game:GetService("HttpService"):JSONEncode(p.onb))
	plr:SetAttribute("CC_Signature", p.sig ~= "" and p.sig or nil)
	plr:SetAttribute("CC_SigUnlocked", table.concat(p.sigs, ","))
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
		for k, v in pairs(data) do if k ~= "stats" and k ~= "tp" and k ~= "look" and k ~= "onb" and k ~= "sigs" and k ~= "sig" and p[k] ~= nil then p[k] = v end end
		if type(data.onb) == "table" then
			for k, v in pairs(data.onb) do if k ~= "lessons" and type(p.onb[k]) == "boolean" and type(v) == "boolean" then p.onb[k] = v end end
			if type(data.onb.lessons) == "table" then for i = 1, 6 do p.onb.lessons[i] = data.onb.lessons[i] == true end end
		else
			p.onb.editor = true; p.onb.offered = true; p.onb.firstFight = true   -- bekannter Spieler aus der Zeit vor dem Einstieg
		end
		if type(data.sigs) == "table" then for _, id in ipairs(data.sigs) do if SIG.list[id] and not table.find(p.sigs, id) then table.insert(p.sigs, id) end end end
		if type(data.sig) == "string" and table.find(p.sigs, data.sig) then p.sig = data.sig end
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
		onb = { editor = p.onb.editor, offered = p.onb.offered, lessons = table.clone(p.onb.lessons), done = p.onb.done, firstFight = p.onb.firstFight },
		sig = p.sig, sigs = table.clone(p.sigs) }
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

event.Event:Connect(function(plr, kind, a, b)
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
	elseif kind == "sig_unlock" and SIG.list[a] then             -- Signatur freischalten (nach bestandener Uebung, CC_CharacterAnimations)
		local p = profiles[plr]
		if not table.find(p.sigs, a) then table.insert(p.sigs, a) end
		p.sig = a; p.dirty = true; publish(plr); saveSoon(plr)
	elseif kind == "sig_equip" then                                -- a = Schluessel oder "" (ablegen); nur Freigeschaltetes
		local p = profiles[plr]
		if a == "" or (SIG.list[a] and table.find(p.sigs, a)) then p.sig = a; p.dirty = true; publish(plr); saveSoon(plr) end
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
