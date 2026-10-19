-- ServerScriptService.CC_Tutorial
-- Einstieg (GAME_DESIGN.md, Schritt 1): Kaempfer-Editor -> Begruessung durch den Haupttrainer -> 6 Lektionen im Kaefig -> erstes Sparring.
-- Der Server entscheidet ueber Fortschritt: Lektionen zaehlen nur echte Aktionen (Treffer, Block, Sprawl, Aufstehen aus CC_FightEvent
-- bzw. Positionen/Attributen), nicht blosse Tastendruecke.
--
-- Zustand fuer die Anzeige (CC_Tutorial.client) als Attribute am Spieler:
--   CC_OnbPhase  "" | "editor" | "welcome" | "lesson" | "done" | "spar" | "after"
--   CC_TutState  JSON { lesson, title, task, keys = { {k, label} }, icon, n, of, step, steps, done = {6 x bool}, help, struggle }
--   CC_CoachTip  JSON { text, kind = "tip" | "good" | "bad", t }
-- Client -> Server: ReplicatedStorage.CC_Tutorial (RemoteEvent) mit "editorDone" | "start" | "skipAll" | "skipLesson" |
--   "choice", "sparring"|"gym" | "retry" | "closeWelcome" | "closeAfter"
-- Ablauf im Kaefig: CC_Match ("tutorial") ruft ServerStorage.CC_TutorialRun (BindableFunction) auf; Rueckgabe "sparring" | "gym".
-- Fortschritt wird im Profil gespeichert (CC_Profile, onb): editor, offered, lessons[1..6], done, firstFight.
-- Keine Erstabschluss-Belohnung im Tutorial; das erste Sparring belohnt wie ein normaler Trainingskampf (CC_Match).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local HS = game:GetService("HttpService")
local RS = game.ReplicatedStorage
local SS = game.ServerStorage

local remote = RS:FindFirstChild("CC_Tutorial") or Instance.new("RemoteEvent")
remote.Name = "CC_Tutorial"; remote.Parent = RS
local runFn = SS:FindFirstChild("CC_TutorialRun") or Instance.new("BindableFunction")
runFn.Name = "CC_TutorialRun"; runFn.Parent = SS
local fightEvent = SS:WaitForChild("CC_FightEvent")
local reset = SS:WaitForChild("CC_ResetFighter")
local menuServer = SS:WaitForChild("CC_MenuServer")
local dummy = workspace:WaitForChild("CC_TrainingDummy")
local REG = require(RS:WaitForChild("CC_MatchRegistry"))   -- Zustand je Kampf

local function profile(p, kind, a, b)
	local ev = SS:FindFirstChild("CC_ProfileEvent")
	if ev and p.Parent then ev:Fire(p, kind, a, b) end
end
local function onb(p)
	local ok, t = pcall(function() return HS:JSONDecode(p:GetAttribute("CC_Onb") or "") end)
	return ok and type(t) == "table" and t or nil
end
local function phase(p, ph) p:SetAttribute("CC_OnbPhase", ph or "") end
-- Story-Einstieg (CC_Story.client): Phase "story" spielt den Film lokal; Schule und Gym-Front vorher streamen lassen.
local storyRemote = RS:FindFirstChild("CC_Story") or Instance.new("RemoteEvent"); storyRemote.Name = "CC_Story"; storyRemote.Parent = RS
local function streamStory(p)
	local s = workspace:FindFirstChild("CC_StorySchool")
	local o = s and s:GetAttribute("CC_Origin")
	if o then
		pcall(function() p:RequestStreamAroundAsync(o + Vector3.new(0, 0, 20), 8) end)
		pcall(function() p:RequestStreamAroundAsync(o + Vector3.new(120, 0, -118), 8) end)
	end
end
local function startStory(p)
	task.spawn(function() streamStory(p); if p.Parent then phase(p, "story") end end)
end
local function tip(p, text, kind)
	p:SetAttribute("CC_CoachTip", HS:JSONEncode({ text = text, kind = kind or "tip", t = workspace:GetServerTimeNow() }))
end

---------------------------------------------------------------------------------------------------
-- Haupttrainer im Gym und am Kaefigrand (Modell ServerStorage.CC_Coach aus setup_coach_v01; fehlt es, spricht er nur im Dialogfeld)
---------------------------------------------------------------------------------------------------
local coachGym, coachCage
-- Standpunkte (Studs, Welt): Gym = neben dem Trainertisch (Stuhl-Seite, Tisch an der Ostwand), Blick in die Halle;
-- Arena = Hallenboden ausserhalb der Plattform auf der roten Seite, Blick zur Kaefigmitte. Ueberschreibbar per Attribut CC_CoachSpot.
local GYM_SPOT, GYM_LOOK = Vector3.new(208, 0, -46), Vector3.new(160, 0, 4)
local CAGE_SPOT, CAGE_LOOK = Vector3.new(-8, 0, 22.5), Vector3.new(0, 0, 0)
local function groundAt(v)
	local rp = RaycastParams.new(); rp.FilterType = Enum.RaycastFilterType.Exclude
	rp.FilterDescendantsInstances = { workspace:FindFirstChild("CC_CoachGym"), workspace:FindFirstChild("CC_CoachCage") }
	local hit = workspace:Raycast(Vector3.new(v.X, v.Y + 12, v.Z), Vector3.new(0, -40, 0), rp)
	return hit and hit.Position.Y or v.Y
end
local function placeCoach()
	local tpl = SS:FindFirstChild("CC_Coach")
	if not tpl then return end
	local gi = workspace:FindFirstChild("CC_GymInteractions")
	local desk = gi and gi:FindFirstChild("Coach_Desk")
	if desk and not coachGym then
		coachGym = tpl:Clone(); coachGym.Name = "CC_CoachGym"
		local pos = desk:GetAttribute("CC_CoachSpot") or GYM_SPOT
		local y = groundAt(pos)
		coachGym:PivotTo(CFrame.lookAt(Vector3.new(pos.X, y, pos.Z), Vector3.new(GYM_LOOK.X, y, GYM_LOOK.Z)))
		coachGym.Parent = workspace
		-- Ansprechen: Tutorial wiederholen
		local pr = Instance.new("ProximityPrompt")
		pr.ObjectText = "Haupttrainer"; pr.ActionText = "Sprechen"; pr.KeyboardKeyCode = Enum.KeyCode.E; pr.GamepadKeyCode = Enum.KeyCode.ButtonX
		pr.HoldDuration = 0; pr.MaxActivationDistance = 8; pr.RequiresLineOfSight = false
		pr.Parent = coachGym.PrimaryPart or coachGym:FindFirstChildWhichIsA("BasePart")
		pr.Triggered:Connect(function(p)
			local c = p.Character
			if c and not c:GetAttribute("CC_Opponent") and not p:GetAttribute("CC_Minigame") and (p:GetAttribute("CC_OnbPhase") or "") == "" then phase(p, "welcome") end
		end)
	end
	local arena = workspace:FindFirstChild("CC_Arena")
	if arena and not coachCage then
		coachCage = tpl:Clone(); coachCage.Name = "CC_CoachCage"
		local spot = arena:GetAttribute("CC_CoachSpot") or CAGE_SPOT
		local y = groundAt(spot)
		coachCage:PivotTo(CFrame.lookAt(Vector3.new(spot.X, y, spot.Z), Vector3.new(CAGE_LOOK.X, y, CAGE_LOOK.Z)))
		coachCage.Parent = workspace
	end
end
task.spawn(function() task.wait(2); placeCoach() end)
SS.ChildAdded:Connect(function(c) if c.Name == "CC_Coach" then placeCoach() end end)

---------------------------------------------------------------------------------------------------
-- Lektionen
---------------------------------------------------------------------------------------------------
-- Tasten wie im Steuerungssystem (CC_Input / GAMEPLAY_STAND.md)
local KEY = {
	move = { { "W A S D", "Laufen" } }, circle = { { "A / D", "Umkreisen" } }, dist = { { "W / S", "Vor / zurück" } },
	jab = { { "LMB", "Jab" } }, cross = { { "RMB", "Cross" } }, block = { { "F", "Block halten" } },
	stam = { { "LMB", "Jab" }, { "RMB", "Cross" } }, rest = { { "—", "Nicht angreifen" } },
	kick = { { "C X V Z", "Kick" }, { "F", "Deckung" } }, td = { { "E", "Takedown" } }, sprawl = { { "F", "Sprawl" } },
	getup = { { "LEERTASTE", "Befreien / Aufstehen" } },
}
local LESSONS = {
	{ title = "BEWEGEN & ABSTAND", icon = "run", group = 1, steps = {
		{ task = "Lauf ein paar Schritte durch den Käfig.", keys = KEY.move, of = 3, kind = "walk",
			tip = "Locker bleiben. Dein Blick bleibt automatisch beim Gegner." },
		{ task = "Umkreise den Gegner seitlich.", keys = KEY.circle, of = 3, kind = "circle",
			tip = "Seitlich bewegen ist sicherer als gerade zurück." },
		{ task = "Stell dich in Jab-Reichweite und halte den Abstand.", keys = KEY.dist, of = 1, kind = "range",
			tip = "Etwa eine Armlänge Abstand. Nicht zu nah, nicht zu weit." },
	} },
	{ title = "JAB & CROSS", icon = "glove", group = 2, steps = {
		{ task = "Lande 3 Jabs am Gegner.", keys = KEY.jab, of = 3, kind = "hit", moves = { jab = true, jabBody = true },
			tip = "Der Jab ist schnell und hält den Gegner auf Abstand." },
		{ task = "Lande 2 Crosses am Gegner.", keys = KEY.cross, of = 2, kind = "hit", moves = { cross = true, crossBody = true },
			tip = "Der Cross ist stärker. Zurück in die Deckung. Dann der nächste Schlag." },
	} },
	{ title = "BLOCK & AUSDAUER", icon = "shield", group = 1, steps = {
		{ task = "Blocke 2 angekündigte Schläge.", keys = KEY.block, of = 2, kind = "block", tutor = "strike",
			tip = "Wenn „Schlag kommt“ erscheint: F gedrückt halten." },
		{ task = "Verbrauche Ausdauer mit Schlägen (gelber Balken).", keys = KEY.stam, of = 1, kind = "spend",
			tip = "Jede Aktion kostet Ausdauer. Unter einem Viertel schlägst du schwächer." },
		{ task = "Lass die Ausdauer wieder volllaufen.", keys = KEY.rest, of = 1, kind = "recover",
			tip = "Kurz nichts tun und nicht blocken – dann füllt sich der Balken." },
	} },
	{ title = "KICK & DECKUNG", icon = "kick", group = 2, steps = {
		{ task = "Lande einen Kick und geh sofort zurück in die Deckung.", keys = KEY.kick, of = 2, kind = "kickguard",
			tip = "Nach dem Kick sofort F – sonst stehst du offen." },
	} },
	{ title = "TAKEDOWN & SPRAWL", icon = "wrestle", group = 3, steps = {
		{ task = "Bring den Gegner mit einem Takedown zu Boden.", keys = KEY.td, of = 1, kind = "takedown",
			tip = "Nah heran, dann E. Aus der Distanz klappt kein Takedown." },
		{ task = "Wehre einen angekündigten Takedown mit Sprawl ab.", keys = KEY.sprawl, of = 1, kind = "sprawl", tutor = "td",
			tip = "Wenn „Takedown kommt“ erscheint: genau dann F drücken." },
	} },
	{ title = "AM BODEN AUFSTEHEN", icon = "rotate", group = 3, steps = {
		{ task = "Der Gegner bringt dich zu Boden. Befrei dich und steh auf.", keys = KEY.getup, of = 1, kind = "getup", tutor = "ground",
			tip = "Unten: Leertaste befreit dich. Dann noch einmal Leertaste – du stehst auf." },
	} },
}

local sessions = {}            -- [player] = laufende Lektion (Steuerung durch Remote)
local function stateOf(p, L, li, si, n, extra)
	local o = onb(p)
	local st = L.steps[si]
	local t = { lesson = li, title = L.title, icon = L.icon, task = st.task, keys = st.keys, n = n, of = st.of, step = si, steps = #L.steps,
		done = o and o.lessons or {}, help = st.tip }
	for k, v in pairs(extra or {}) do t[k] = v end
	p:SetAttribute("CC_TutState", HS:JSONEncode(t))
end
local function corners()
	local c = workspace.CC_Arena:FindFirstChild("Platform_Canvas_FightSurface", true)
	local y = c.Position.Y + c.Size.Y / 2 + 3
	return CFrame.lookAt(Vector3.new(0, y, 7), Vector3.new(0, y, -7)), CFrame.lookAt(Vector3.new(0, y, -7), Vector3.new(0, y, 7))
end
local function resetBoth(p)
	local cr, cb = corners()
	if p.Character then reset:Invoke(p.Character, cr, nil) end
	reset:Invoke(dummy, cb, nil)
	if p.Character then p.Character:SetAttribute("CC_Opponent", dummy.Name) end
	dummy:SetAttribute("CC_Opponent", p.Character and p.Character.Name or nil)
end
local function rootOf(c) return c and c:FindFirstChild("HumanoidRootPart") end

-- Eine Teilaufgabe ausfuehren; liefert "ok" | "skip" | "skipAll" | "left"
local function runStep(p, L, li, si)
	local st = L.steps[si]
	local s = sessions[p]
	s.cmd = nil
	local n, fails, lastFailTip = 0, 0, 0
	dummy:SetAttribute("CC_Tutor", st.tutor)
	dummy:SetAttribute("CC_Passive", true)
	stateOf(p, L, li, si, 0)
	tip(p, st.tip)
	local conns = {}
	local function progress(k)
		n = math.min(st.of, n + (k or 1))
		stateOf(p, L, li, si, n, { pulse = workspace:GetServerTimeNow() })
	end
	local function fail(text)
		fails += 1
		if os.clock() - lastFailTip > 1.2 then tip(p, text, "bad"); lastFailTip = os.clock() end
		if fails >= 3 then stateOf(p, L, li, si, n, { struggle = true }) end
	end
	local char = p.Character
	local kickAt                                   -- Lektion 4: Zeit des gelandeten Kicks
	table.insert(conns, fightEvent.Event:Connect(function(kind, a, b, x, y)
		if not char or (a ~= char and b ~= char) then return end
		if kind == "hit" then
			local move, blocked = x, y
			if st.kind == "hit" and a == char then
				if st.moves[move] then progress()
				else fail("Das war kein " .. (st.moves.jab and "Jab (linke Maustaste)" or "Cross (rechte Maustaste)") .. ".") end
			elseif st.kind == "block" and b == char then
				if blocked then progress() else fail("Halte F schon gedrückt, wenn „Schlag kommt“ erscheint.") end
			elseif st.kind == "kickguard" and a == char then
				if move == "lowkick" or move == "bodykick" or move == "highkick" or move == "frontkick" then kickAt = os.clock()
				else fail("Das war ein Schlag. Für Kicks: C, X, V oder Z.") end
			end
		elseif kind == "td" then
			local defended = x
			if st.kind == "takedown" and a == char then
				if not defended then progress() else fail("Abgewehrt – versuch es noch einmal.") end
			elseif st.kind == "sprawl" and b == char then
				if defended then progress() else fail("Zu spät oder zu früh. Drück F genau bei „Takedown kommt“.") end
			end
		end
	end))
	table.insert(conns, char:GetAttributeChangedSignal("CC_OutOfRange"):Connect(function()
		if st.kind == "hit" or st.kind == "kickguard" then fail("Zu weit weg – geh einen Schritt näher (W).") end
	end))
	table.insert(conns, char:GetAttributeChangedSignal("CC_Tired"):Connect(function()
		if st.kind ~= "spend" then fail("Keine Ausdauer – kurz durchatmen.") end
	end))
	-- Ablauf je Art (Positionen, Ausdauer, Ringen) im Takt pruefen
	local last = rootOf(char) and rootOf(char).Position
	local walked, angle, lastAng, inRange = 0, 0, nil, 0
	local spentLow, wasBottom = false, false
	local t0, idleHint = os.clock(), false
	local result
	while true do
		local dt = task.wait(0.1)
		if not p.Parent or not char.Parent or p.Character ~= char then result = "left"; break end
		if s.cmd then result = s.cmd; s.cmd = nil; break end
		local r, dr = rootOf(char), rootOf(dummy)
		if not (r and dr) then continue end
		-- Grundlagen ohne Niederlage: Leben nie unter 40
		for _, c in ipairs({ char, dummy }) do
			local h = c:FindFirstChildOfClass("Humanoid")
			if h and h.Health < 40 then h.Health = 40 end
		end
		local flat = (r.Position - dr.Position) * Vector3.new(1, 0, 1)
		local dist = flat.Magnitude
		if st.kind == "walk" then
			local d = ((r.Position - last) * Vector3.new(1, 0, 1)).Magnitude
			if d < 4 then walked += d end
			if math.floor(walked / 5) > n then progress(math.floor(walked / 5) - n) end
		elseif st.kind == "circle" then
			local a = math.atan2(flat.X, flat.Z)
			if lastAng then
				local da = (a - lastAng + math.pi) % (2 * math.pi) - math.pi
				angle += math.abs(da)
			end
			lastAng = a
			if math.floor(math.deg(angle) / 30) > n then progress(math.floor(math.deg(angle) / 30) - n) end
		elseif st.kind == "range" then
			if dist >= 3.0 and dist <= 4.8 then inRange += dt else inRange = 0 end
			if inRange >= 1.5 then progress() end
			if os.clock() - t0 > 12 and not idleHint and n == 0 then idleHint = true; tip(p, dist > 4.8 and "Noch etwas näher heran (W)." or "Ein kleines Stück zurück (S).") end
		elseif st.kind == "spend" then
			local smax = char:GetAttribute("CC_StaminaMax") or 100
			if (char:GetAttribute("CC_Stamina") or smax) <= smax - 25 then progress() end
		elseif st.kind == "recover" then
			local smax = char:GetAttribute("CC_StaminaMax") or 100
			if (char:GetAttribute("CC_Stamina") or 0) >= smax - 3 then progress() end
		elseif st.kind == "kickguard" then
			if kickAt then
				if char:GetAttribute("CC_Block") then kickAt = nil; progress()
				elseif os.clock() - kickAt > 1.5 then kickAt = nil; fail("Nach dem Kick sofort F – sonst stehst du offen.") end
			end
		elseif st.kind == "takedown" then
			-- nach dem gelungenen Takedown liegt der Gegner unten; Fortschritt kommt aus dem Ereignis
			if n == 0 and os.clock() - t0 > 15 and not idleHint then idleHint = true; tip(p, "Geh ganz nah an den Gegner (W) und drück dann E.") end
		elseif st.kind == "getup" then
			local w = char:GetAttribute("CC_Wrestle")
			if w == "bottom" then wasBottom = true end
			if wasBottom and (w == false or w == nil) and not char:GetAttribute("CC_Down") then progress() end
		end
		last = r.Position
		if n >= st.of then
			dummy:SetAttribute("CC_Tutor", nil)               -- keine neue Aktion des Gegners waehrend der Abschluss-Pause
			-- Ringen beenden, bevor die naechste Aufgabe startet (Takedown-Animation auslaufen lassen)
			task.wait((st.kind == "takedown" or st.kind == "sprawl" or st.kind == "getup") and 1.6 or 0.5)
			result = "ok"; break
		end
		-- misslungener Sprawl/Takedown gegen den Spieler: nach dem Takedown wieder aufstellen
		if st.kind == "sprawl" and char:GetAttribute("CC_Wrestle") == "bottom" then
			task.wait(1.2); resetBoth(p)
		end
	end
	for _, c in ipairs(conns) do c:Disconnect() end
	dummy:SetAttribute("CC_Tutor", nil)
	return result
end

local function runLesson(p, li)
	local L = LESSONS[li]
	for si = 1, #L.steps do
		local r = runStep(p, L, li, si)
		if r ~= "ok" then return r end
		tip(p, si < #L.steps and "Gut gemacht." or "Lektion geschafft!", "good")
		if L.steps[si].kind == "takedown" or L.steps[si].kind == "sprawl" or L.steps[si].kind == "getup" or L.steps[si + 1] and L.steps[si + 1].tutor then
			resetBoth(p)
		end
		task.wait(0.4)
	end
	profile(p, "onb", "lesson", li)
	return "ok"
end

-- Ablauf im Kaefig (von CC_Match aufgerufen, blockiert bis zum Ende)
runFn.OnInvoke = function(p)
	local s = { cmd = nil }
	sessions[p] = s
	p:SetAttribute("CC_TutState", nil)
	phase(p, "lesson")
	profile(p, "onb", "offered", true)
	local o = onb(p) or { lessons = {} }
	-- Fortsetzen: ab der ersten nicht geschafften Lektion; alles geschafft = von vorn (Wiederholung beim Trainer)
	local first = 1
	for i = 1, #LESSONS do if not o.lessons[i] then first = i; break end; if i == #LESSONS then first = 1 end end
	local outcome = "done"
	for li = first, #LESSONS do
		local r = runLesson(p, li)
		if r == "left" then outcome = "left"; break end
		if r == "skipAll" then outcome = "skipAll"; break end
		-- "skip" = Lektion uebersprungen (nicht abgehakt), weiter mit der naechsten
		if li < #LESSONS then resetBoth(p); task.wait(0.6) end
	end
	dummy:SetAttribute("CC_Tutor", nil)
	if outcome == "left" then                        -- Respawn/Tod/Verlassen: Fortschritt bleibt, Angebot zum Weitermachen im Gym
		sessions[p] = nil
		if p.Parent then phase(p, "welcome") end
		return "gym"
	end
	resetBoth(p)
	if outcome == "skipAll" then
		sessions[p] = nil; phase(p, ""); tip(p, "Kein Problem. Das Tutorial kannst du bei mir im Gym jederzeit wiederholen.")
		return "gym"
	end
	profile(p, "onb", "done", true)
	-- Abschluss (Bild 3): Sparring starten oder zurueck ins Gym
	stateOf(p, LESSONS[#LESSONS], #LESSONS, 1, 0)
	phase(p, "done")
	tip(p, "Stark. Jetzt setzt du das Gelernte im Sparring ein.", "good")
	local t0 = os.clock()
	local choice
	while p.Parent and os.clock() - t0 < 300 do
		if s.cmd == "sparring" or s.cmd == "gym" then choice = s.cmd; break end
		task.wait(0.1)
	end
	sessions[p] = nil
	if choice == "sparring" then phase(p, "spar"); return "sparring" end
	phase(p, "")
	return "gym"
end

---------------------------------------------------------------------------------------------------
-- Erstes Sparring: kurze Tipps vom Kaefigrand, danach Ergebnis
---------------------------------------------------------------------------------------------------
local sparWatch = {}
local function watchSparring(p)
	if sparWatch[p] then return end
	sparWatch[p] = true
	task.spawn(function()
		local t0 = os.clock()
		while p.Parent and REG.stateOf(p):GetAttribute("Mode") ~= "sparring" and os.clock() - t0 < 30 do task.wait(0.2) end
		local char = p.Character
		if not char or REG.stateOf(p):GetAttribute("Mode") ~= "sparring" then sparWatch[p] = nil; return end
		while p.Parent and REG.stateOf(p):GetAttribute("State") ~= "fight" and REG.stateOf(p):GetAttribute("Mode") == "sparring" do task.wait(0.1) end
		tip(p, "Ruhig bleiben. Jab, dann Cross. Wenn er kommt: F.")
		local takenInRow, landed, lastTip = 0, 0, os.clock()
		local function say(text, kind) if os.clock() - lastTip > 4 then lastTip = os.clock(); tip(p, text, kind) end end
		local c1 = fightEvent.Event:Connect(function(kind, a, b, move, blocked)
			if kind == "hit" and b == char and not blocked then
				takenInRow += 1
				if takenInRow >= 3 then takenInRow = 0; say("Deckung hoch – F halten, wenn er angreift.") end
			elseif kind == "hit" and a == char then
				takenInRow = 0; landed += 1
				if landed == 3 then say("Gut so! Treffen und wieder raus.", "good") end
			elseif kind == "td" and b == char and not move then   -- bei "td" ist das 4. Argument "abgewehrt"
				say("Am Boden: Leertaste – steh wieder auf.")
			end
		end)
		local c2 = char:GetAttributeChangedSignal("CC_Tired"):Connect(function() say("Ausdauer leer. Kurz Abstand nehmen und durchatmen.") end)
		local c3 = char:GetAttributeChangedSignal("CC_OutOfRange"):Connect(function() say("Zu weit weg – erst näher heran.") end)
		while p.Parent and REG.stateOf(p):GetAttribute("Mode") == "sparring" and REG.stateOf(p):GetAttribute("State") ~= "over" do task.wait(0.2) end
		c1:Disconnect(); c2:Disconnect(); c3:Disconnect()
		sparWatch[p] = nil
	end)
end

-- Nach dem Sparring (CC_LastFight von CC_Match): Fortschritt immer, Ergebnis anzeigen
local function hookPlayer(p)
	p:GetAttributeChangedSignal("CC_LastFight"):Connect(function()
		if p:GetAttribute("CC_OnbPhase") ~= "spar" then return end
		local ok, r = pcall(function() return HS:JSONDecode(p:GetAttribute("CC_LastFight")) end)
		if not ok or r.mode ~= "sparring" then return end
		profile(p, "onb", "firstFight", true)
		tip(p, r.result == "win" and "Starker erster Kampf! Das Gym und Online stehen dir offen."
			or "Kopf hoch – jeder fängt so an. Noch ein Versuch?", r.result == "win" and "good" or "tip")
		task.wait(7.5)                               -- Ergebnis im Kaefig (CC_Match OVER_TIME), dann im Gym
		local o = onb(p)
		if p.Parent and o and o.story and o.outro == false then phase(p, "outro")   -- Story-Abschluss ("War das schlecht?") einmalig
		elseif p.Parent then phase(p, "after") end
	end)
	p:GetAttributeChangedSignal("CC_OnbPhase"):Connect(function()
		if p:GetAttribute("CC_OnbPhase") == "spar" then watchSparring(p) end
	end)
	-- Startphase nach dem Laden des Profils
	task.spawn(function()
		local t0 = os.clock()
		while p.Parent and p:GetAttribute("CC_Onb") == nil and os.clock() - t0 < 20 do task.wait(0.1) end
		local o = onb(p)
		if not o then phase(p, ""); return end
		local anyLesson = false
		for i = 1, 6 do if o.lessons[i] then anyLesson = true end end
		if not o.editor then phase(p, "editor")
		elseif o.story == false then startStory(p)                  -- Film noch nicht gesehen (z. B. waehrenddessen verlassen)
		elseif not o.offered or (anyLesson and not o.done) then phase(p, "welcome")
		else phase(p, "") end
	end)
end
Players.PlayerAdded:Connect(hookPlayer)
for _, p in ipairs(Players:GetPlayers()) do hookPlayer(p) end
Players.PlayerRemoving:Connect(function(p) local s = sessions[p]; if s then s.cmd = "skipAll" end; sparWatch[p] = nil end)

-- Story: Ende/Ueberspringen -> gespeichert, danach direkt die erste Lektion im Kaefig (Film endet mit "Wir beginnen langsam").
-- Wiederholung aus den Einstellungen: nur Film, kein Fortschritt, keine Belohnung.
storyRemote.OnServerEvent:Connect(function(p, what, arg)
	local ph = p:GetAttribute("CC_OnbPhase") or ""
	if what == "done" and ph == "story" then
		profile(p, "onb", "story", true)
		profile(p, "onb", "offered", true)
		phase(p, "lesson")
		menuServer:Fire(p, "tutorial")
	elseif what == "explained" and (arg == "gymTour" or arg == "sigTour" or arg == "onlineHint" or arg == "editorHint" or arg == "focusTip") then
		profile(p, "onb", arg, true)                                    -- Erklaerung beim ersten Mal gesehen (CC_Story.client)
	elseif what == "outroDone" and ph == "outro" then
		profile(p, "onb", "outro", true)
		phase(p, "after")
		-- Karriere kurz erklaeren (bestehende Karriereansicht im Menue), einzeln nacheinander
		task.spawn(function()
			for _, t in ipairs({
				"Karriere: Menü (M) → KARRIERE. Dort siehst du deinen nächsten Gegner.",
				"Bei jedem Gegner stehen seine Stärken und mein Tipp. KAMPF STARTEN, wenn du bereit bist.",
				"Du kannst auch erst im Gym weitertrainieren – jede Station macht dich stärker." }) do
				task.wait(5.5); if not p.Parent then return end
				tip(p, t)
			end
		end)
	elseif what == "replay" and ph == "" and p.Character and not p.Character:GetAttribute("CC_Opponent") and not p:GetAttribute("CC_Queue") then
		task.spawn(function() streamStory(p); if p.Parent then storyRemote:FireClient(p, "play") end end)
	end
end)

remote.OnServerEvent:Connect(function(p, what, arg)
	local ph = p:GetAttribute("CC_OnbPhase") or ""
	local s = sessions[p]
	if what == "editorDone" and ph == "editor" then
		profile(p, "onb", "editor", true)
		local o = onb(p)
		if o and o.story == false then startStory(p) else phase(p, "welcome") end
	elseif what == "start" and ph == "welcome" then
		phase(p, "lesson")
		menuServer:Fire(p, "tutorial")
	elseif what == "closeWelcome" and ph == "welcome" then             -- Ueberspringen im Begruessungsfenster
		profile(p, "onb", "offered", true)
		phase(p, "")
		tip(p, "Alles klar. Das Tutorial kannst du bei mir im Gym jederzeit wiederholen.")
	elseif (what == "skipLesson" or what == "skipAll") and s and ph == "lesson" then
		s.cmd = what == "skipLesson" and "skip" or "skipAll"
	elseif what == "choice" and s and ph == "done" and (arg == "sparring" or arg == "gym") then
		s.cmd = arg
	elseif what == "retry" and ph == "after" then
		phase(p, "spar")
		menuServer:Fire(p, "sparring")
	elseif what == "closeAfter" and ph == "after" then
		phase(p, "")
	elseif what == "openWelcome" and ph == "" and p.Character and not p.Character:GetAttribute("CC_Opponent") then   -- Hauptmenue: Tutorial wiederholen
		phase(p, "welcome")
	end
end)

