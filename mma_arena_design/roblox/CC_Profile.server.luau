-- ServerScriptService.CC_Profile
-- Spielerprofil mit Speicherung (DataStore "CC_Profiles_v1", Schluessel "u_<UserId>"):
--   Level, XP, Siege/Niederlagen/K.o./Submissions und 4 Kaempfer-Werte (0..20):
--   Power (Schlagkraft), Cardio (Kondition), Wrestling (Ringen), Grappling (Bodenkampf).
-- Jeder Wert steigt ueber eigene Trainingspunkte (10 Punkte = +1). Werte wirken im Kampf (siehe CC_CharacterAnimations).
-- Fuer HUD/Menue als Attribute am Spieler: CC_Level, CC_XP, CC_XPNext, CC_Wins, CC_Losses, CC_KOs, CC_Subs,
--   CC_Power/CC_Cardio/CC_Wrestling/CC_Grappling (Wert) und CC_PowerTP ... (Trainingspunkte 0..9), CC_ProfileSaved (bool).
-- Andere Skripte melden ueber ServerStorage.CC_ProfileEvent (BindableEvent):
--   Fire(player, "xp", menge) | Fire(player, "train", "Power"|"Cardio"|"Wrestling"|"Grappling", punkte)
--   | Fire(player, "result", "win"|"loss"|"draw", methode)
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

local event = SS:FindFirstChild("CC_ProfileEvent") or Instance.new("BindableEvent")
event.Name = "CC_ProfileEvent"; event.Parent = SS

local profiles = {}            -- [player] = Tabelle
local function default()
	local p = { v = 1, level = 1, xp = 0, wins = 0, losses = 0, kos = 0, subs = 0, stats = {}, tp = {} }
	for _, s in ipairs(STATS) do p.stats[s] = 0; p.tp[s] = 0 end
	return p
end
local function xpNext(level) return 100 + 50 * (level - 1) end

local function publish(plr)
	local p = profiles[plr]; if not p then return end
	plr:SetAttribute("CC_Level", p.level); plr:SetAttribute("CC_XP", p.xp); plr:SetAttribute("CC_XPNext", xpNext(p.level))
	plr:SetAttribute("CC_Wins", p.wins); plr:SetAttribute("CC_Losses", p.losses); plr:SetAttribute("CC_KOs", p.kos); plr:SetAttribute("CC_Subs", p.subs)
	for _, s in ipairs(STATS) do plr:SetAttribute("CC_" .. s, p.stats[s]); plr:SetAttribute("CC_" .. s .. "TP", p.tp[s]) end
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

local function load(plr)
	local data
	if store then
		for i = 1, 3 do
			local ok, res = pcall(function() return store:GetAsync("u_" .. plr.UserId) end)
			if ok then data = res; plr:SetAttribute("CC_ProfileSaved", true); break end
			warn("[CC] Profil laden fehlgeschlagen (" .. i .. "): " .. tostring(res)); task.wait(2 * i)
		end
	end
	local p = default()
	if type(data) == "table" then
		for k, v in pairs(data) do if k ~= "stats" and k ~= "tp" and p[k] ~= nil then p[k] = v end end
		for _, s in ipairs(STATS) do
			if type(data.stats) == "table" and tonumber(data.stats[s]) then p.stats[s] = math.clamp(math.floor(data.stats[s]), 0, STAT_MAX) end
			if type(data.tp) == "table" and tonumber(data.tp[s]) then p.tp[s] = math.clamp(math.floor(data.tp[s]), 0, TP_PER_LEVEL - 1) end
		end
	end
	profiles[plr] = p
	publish(plr)
end
local function save(plr)
	local p = profiles[plr]
	if not (store and p and plr:GetAttribute("CC_ProfileSaved")) then return end   -- nie ein nicht geladenes Profil ueberschreiben
	local copy = { v = p.v, level = p.level, xp = p.xp, wins = p.wins, losses = p.losses, kos = p.kos, subs = p.subs, stats = p.stats, tp = p.tp }
	local ok, err = pcall(function() store:SetAsync("u_" .. plr.UserId, copy) end)
	if ok then p.dirty = false else warn("[CC] Profil speichern fehlgeschlagen: " .. tostring(err)) end
end

event.Event:Connect(function(plr, kind, a, b)
	if typeof(plr) ~= "Instance" or not plr:IsA("Player") or not profiles[plr] then return end
	if kind == "xp" then addXP(plr, tonumber(a) or 0)
	elseif kind == "train" then train(plr, a, tonumber(b) or 1)
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
Players.PlayerRemoving:Connect(function(plr) save(plr); profiles[plr] = nil end)
game:BindToClose(function() for plr in pairs(profiles) do task.spawn(save, plr) end task.wait(3) end)
task.spawn(function()
	while true do
		task.wait(SAVE_EVERY)
		for plr, p in pairs(profiles) do if p.dirty then save(plr) end end
	end
end)
