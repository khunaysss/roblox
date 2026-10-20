-- ReplicatedStorage.CC_LookShared (ModuleScript)
-- Gemeinsame Daten fuer Kaempfer-Aussehen (Server CC_Customize + Client-Vorschau im Charakter-Editor).
-- Vorlagen: Server kopiert ServerStorage.CC_Custom beim Start nach ReplicatedStorage.CC_CustomShared,
-- damit der Client Aenderungen an seiner lokalen Vorschau zeigen kann, bevor gespeichert wird.
local M = {}

M.HAIR = { "Hair_QuiffV03", "Hair_Buzzcut", "Hair_SidePart", "Hair_ShortCurls" }
M.BEARD = { "none", "Beard_Short", "Beard_Full" }
M.FACE = { "Face_Focused", "Face_Neutral", "Face_Friendly" }
M.SKIN = { Color3.fromRGB(232, 194, 166), Color3.fromRGB(184, 148, 123), Color3.fromRGB(140, 98, 70), Color3.fromRGB(92, 62, 44) }
M.HAIRCOL = { Color3.fromRGB(38, 32, 28), Color3.fromRGB(78, 52, 34), Color3.fromRGB(128, 86, 50), Color3.fromRGB(205, 168, 104),
	Color3.fromRGB(150, 62, 30), Color3.fromRGB(150, 150, 150) }
M.NAMES = { Hair_QuiffV03 = "Quiff", Hair_Buzzcut = "Buzzcut", Hair_SidePart = "Side Part", Hair_ShortCurls = "Curls",
	none = "No Beard", Beard_Short = "Short", Beard_Full = "Full Beard", Face_Focused = "Focused", Face_Neutral = "Neutral", Face_Friendly = "Friendly" }
M.SKIN_N = { "Light", "Medium", "Tan", "Dark" }
M.HAIRCOL_N = { "Black", "Dark Brown", "Brown", "Blonde", "Red", "Grey" }
M.DEFAULT = { hair = "Hair_QuiffV03", beard = "none", face = "Face_Focused", skin = 2, hairColor = 1, shorts = 1, gloves = 1, belt = 1 }
-- Belohnungen: Shorts- und Handschuhfarben. req: lvl = Level, wins = Karriere-Siege (Titel), sigs = freigeschaltete Signaturen.
-- Nur Aussehen, keine Staerke. Freigeschaltet ist, was die Bedingung erfuellt (wird nicht gespeichert, sondern aus dem Profil berechnet).
M.SHORTS = {
	{ name = "Red", color = Color3.fromRGB(196, 32, 40) },
	{ name = "Black", color = Color3.fromRGB(28, 29, 33), req = { lvl = 2 } },
	{ name = "Blue", color = Color3.fromRGB(38, 82, 170), req = { lvl = 4 } },
	{ name = "White", color = Color3.fromRGB(232, 232, 228), req = { wins = 2 }, title = "AMATEUR CHAMPION" },
	{ name = "Green", color = Color3.fromRGB(34, 120, 64), req = { lvl = 7 } },
	{ name = "Purple", color = Color3.fromRGB(104, 52, 160), req = { wins = 4 }, title = "PRO" },
	{ name = "Orange", color = Color3.fromRGB(220, 110, 30), req = { sigs = 1 } },
	{ name = "Olive", color = Color3.fromRGB(86, 92, 58), req = { lvl = 12 } },
	{ name = "Silver", color = Color3.fromRGB(170, 174, 182), req = { wins = 7 }, title = "TOP CONTENDER" },
	{ name = "Gold", color = Color3.fromRGB(214, 168, 48), req = { wins = 10 }, title = "LIGHTWEIGHT CHAMPION" },
}
M.GLOVES = {
	{ name = "Black", color = Color3.fromRGB(26, 26, 30) },
	{ name = "Red", color = Color3.fromRGB(180, 28, 36), req = { lvl = 3 } },
	{ name = "White", color = Color3.fromRGB(230, 230, 226), req = { wins = 2 }, title = "AMATEUR CHAMPION" },
	{ name = "Blue", color = Color3.fromRGB(36, 76, 160), req = { lvl = 5 } },
	{ name = "Pink", color = Color3.fromRGB(214, 70, 140), req = { sigs = 1 } },
	{ name = "Green", color = Color3.fromRGB(40, 130, 70), req = { lvl = 9 } },
	{ name = "Purple", color = Color3.fromRGB(110, 56, 170), req = { sigs = 3 } },
	{ name = "Silver", color = Color3.fromRGB(176, 180, 188), req = { wins = 7 }, title = "TOP CONTENDER" },
	{ name = "Gold", color = Color3.fromRGB(218, 172, 52), req = { wins = 10 }, title = "LIGHTWEIGHT CHAMPION" },
}
-- Guertel: jeder steht fuer einen Erfolg. Getragen wird einer (Auswahl in "My Fighter"), sichtbar im Gym und beim Walkout.
--   kind "auto"  = automatisch der hoechste erreichte Titelguertel (oder keiner)
--   kind "title" = Titelguertel (Ledergurt mit Platte, Teile Belt_Title_*): plate = Plattenfarbe, gems = Steine sichtbar
--   kind "style" = Stilguertel (Stoffguertel, Teile Belt_Cloth_*): color = Band, accent = Enden; erspielt mit der Signatur des Trainers
--   kind "none"  = ohne Guertel
-- req.sig = Schluessel einer bestimmten Signatur (CC_SigUnlocked), req.sigs = Anzahl, req.wins = Karriere-Siege.
M.BELTS = {
	{ name = "Best Title (Auto)", kind = "auto", color = Color3.fromRGB(212, 168, 56) },
	{ name = "No Belt", kind = "none", color = Color3.fromRGB(60, 62, 70) },
	{ name = "Amateur Champion", kind = "title", color = Color3.fromRGB(170, 174, 182), plate = Color3.fromRGB(170, 174, 182), req = { wins = 2 }, title = "AMATEUR CHAMPION" },
	{ name = "Pro", kind = "title", color = Color3.fromRGB(212, 168, 56), plate = Color3.fromRGB(212, 168, 56), req = { wins = 4 }, title = "PRO" },
	{ name = "Top Contender", kind = "title", color = Color3.fromRGB(212, 168, 56), plate = Color3.fromRGB(212, 168, 56), gems = true, req = { wins = 7 }, title = "TOP CONTENDER" },
	{ name = "Lightweight Champion", kind = "title", color = Color3.fromRGB(232, 190, 70), plate = Color3.fromRGB(232, 190, 70), gems = true, req = { wins = 10 }, title = "LIGHTWEIGHT CHAMPION" },
	{ name = "Peek-a-Boo Belt", kind = "style", color = Color3.fromRGB(180, 28, 36), accent = Color3.fromRGB(20, 20, 22), req = { sig = "tyson" }, sigName = "PEEK-A-BOO COMBO" },
	{ name = "Dancing Boxing Belt", kind = "style", color = Color3.fromRGB(235, 235, 230), accent = Color3.fromRGB(214, 168, 56), req = { sig = "ali" }, sigName = "INSTINCT MODE" },
	{ name = "Kickboxing Belt", kind = "style", color = Color3.fromRGB(26, 26, 30), accent = Color3.fromRGB(196, 32, 40), req = { sig = "pereira" }, sigName = "STONE HAND COUNTER" },
	{ name = "Muay Thai Belt", kind = "style", color = Color3.fromRGB(214, 168, 56), accent = Color3.fromRGB(150, 22, 30), req = { sig = "saenchai" }, sigName = "WHEEL KICK" },
	{ name = "Wrestling Belt", kind = "style", color = Color3.fromRGB(36, 76, 160), accent = Color3.fromRGB(20, 20, 22), req = { sig = "khabib" }, sigName = "EAGLE SLAM" },
	{ name = "BJJ Belt", kind = "style", color = Color3.fromRGB(104, 52, 160), accent = Color3.fromRGB(20, 20, 22), req = { sig = "oliveira" }, sigName = "BRONX CHOKE" },
	{ name = "Cage Legend", kind = "title", color = Color3.fromRGB(24, 24, 28), plate = Color3.fromRGB(28, 28, 32), trim = Color3.fromRGB(232, 190, 70), gems = true, req = { wins = 10, sigs = 6 }, title = "CAGE LEGEND" },
}
-- hoechster erreichter Titelguertel (fuer "auto"); nil = noch keiner
function M.bestTitleBelt(prog)
	local best
	for _, b in ipairs(M.BELTS) do
		if b.kind == "title" and M.unlocked(b, prog) then best = b end
	end
	return best
end

-- Fortschritt eines Spielers (Attribute vom Profil); funktioniert auf Server und Client
function M.progressOf(plr)
	local sigs = plr:GetAttribute("CC_SigUnlocked") or ""
	local n, set = 0, {}
	for s in sigs:gmatch("[^,]+") do n += 1; set[s] = true end
	return { lvl = plr:GetAttribute("CC_Level") or 1, wins = plr:GetAttribute("CC_CareerWins") or 0, sigs = n, sigSet = set }
end
function M.unlocked(item, prog)
	local r = item and item.req
	if not r then return item ~= nil end
	if r.sig and not (prog.sigSet and prog.sigSet[r.sig]) then return false end
	return (prog.lvl or 0) >= (r.lvl or 0) and (prog.wins or 0) >= (r.wins or 0) and (prog.sigs or 0) >= (r.sigs or 0)
end
function M.reqText(item)
	local r = item.req
	if not r then return "Default" end
	if r.sig then return ("Unlock the signature %s"):format(item.sigName or r.sig) end
	if r.wins and r.sigs then return ("%d career wins and all %d signatures"):format(r.wins, r.sigs) end
	if r.wins then return ("Title: %s (%d career wins)"):format(item.title or "", r.wins) end
	if r.sigs then return r.sigs == 1 and "Unlock your first signature" or ("Unlock %d signatures"):format(r.sigs) end
	return ("Reach level %d"):format(r.lvl)
end

local function find(list, v) for _, x in ipairs(list) do if x == v then return true end end return false end
-- nur gueltige Werte uebernehmen
function M.sanitize(t)
	local look = {}
	if type(t) ~= "table" then return look end
	if type(t.hair) == "string" and find(M.HAIR, t.hair) then look.hair = t.hair end
	if type(t.beard) == "string" and find(M.BEARD, t.beard) then look.beard = t.beard end
	if type(t.face) == "string" and find(M.FACE, t.face) then look.face = t.face end
	if type(t.skin) == "number" and M.SKIN[t.skin] then look.skin = t.skin end
	if type(t.hairColor) == "number" and M.HAIRCOL[t.hairColor] then look.hairColor = t.hairColor end
	if type(t.shorts) == "number" and M.SHORTS[t.shorts] then look.shorts = t.shorts end
	if type(t.gloves) == "number" and M.GLOVES[t.gloves] then look.gloves = t.gloves end
	if type(t.belt) == "number" and M.BELTS[t.belt] then look.belt = t.belt end
	return look
end
function M.copy(t) local c = {}; for k, v in pairs(t) do c[k] = v end; return c end
function M.same(a, b)
	for _, k in ipairs({ "hair", "beard", "face", "skin", "hairColor", "shorts", "gloves" }) do if a[k] ~= b[k] then return false end end
	return true
end

function M.isHead(name) return name:sub(1, 5) == "Hair_" or name:sub(1, 6) == "Beard_" or name:sub(1, 5) == "Face_" end

-- Aussehen auf ein Kaempfer-Modell anwenden (echter Charakter oder lokale Kopie). tpl = Ordner mit Varianten
function M.apply(char, look, tpl)
	local hrp = char and char:FindFirstChild("HumanoidRootPart")
	if not hrp or type(look) ~= "table" then return end
	if tpl then
		for _, p in ipairs(char:GetChildren()) do if p:IsA("BasePart") and M.isHead(p.Name) then p:Destroy() end end
		-- Achtung: keine nil-Luecke in der Liste (ipairs wuerde dort abbrechen; frueher fehlte so das Gesicht ohne Bart)
		for _, v in ipairs({ look.hair or "", look.beard or "none", look.face or "" }) do
			local folder = v ~= "none" and v ~= "" and tpl:FindFirstChild(v)
			if folder then
				for _, t in ipairs(folder:GetChildren()) do
					if t:IsA("BasePart") then
						local p = t:Clone()
						p.Anchored = false; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.Massless = true
						local m = Instance.new("Motor6D"); m.Name = p.Name .. "Motor6D"
						m.Part0 = hrp; m.Part1 = p; m.C0 = t:GetAttribute("CC_C0") or CFrame.new(); m.Parent = p
						p.Parent = char
					end
				end
			end
		end
	end
	local skin = M.SKIN[look.skin] or M.SKIN[2]
	local hc = M.HAIRCOL[look.hairColor] or M.HAIRCOL[1]
	local body = char:FindFirstChild("Fighter_Body"); if body then body.Color = skin end
	-- Belohnungen: nur setzen, wenn im Aussehen gewaehlt (KI-Gegner ohne Angabe behalten ihre Farben)
	local sh = look.shorts and M.SHORTS[look.shorts]; local shp = char:FindFirstChild("Fighter_Shorts")
	if sh and shp then shp.Color = sh.color end
	local gl = look.gloves and M.GLOVES[look.gloves]; local glp = char:FindFirstChild("Fighter_Gloves")
	if gl and glp then glp.Color = gl.color end
	for _, p in ipairs(char:GetChildren()) do
		if p:IsA("BasePart") and (p.Name:sub(1, 5) == "Hair_" or p.Name:sub(1, 6) == "Beard_" or p.Name:find("_Brow_")) then p.Color = hc end
	end
end

return M
