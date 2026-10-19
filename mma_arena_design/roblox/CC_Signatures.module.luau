-- ReplicatedStorage.CC_Signatures (ModuleScript) – Signaturtechniken der Stil-Trainer (Server und Client lesen dieselben Werte)
-- ALLE ZAHLEN SIND VORLAEUFIG (Startwerte fuer Spieltests, Signatur-Ultimates Prototyp 2026-10-14).
--
-- Fokus: nur im echten Kampf (Training, Sparring, Online; nicht im Tutorial) durch gelandete Angriffe und erfolgreiche Abwehr.
--   Leerschlaege, blosses Blockhalten und Aktionen im Tutorial geben nichts. Bleibt zwischen Runden, neues Match = 0.
-- Ausloesen (Taste G / Controller Steuerkreuz hoch): Server prueft Ausruestung, voller Fokus, Ausdauer, Kampfzustand, Reichweite.
--   Ein Versuch verbraucht den ganzen Fokus und zusaetzlich Ausdauer. Keine Unverwundbarkeit, kein garantierter Treffer:
--   jeder Schlag hat ein eigenes Trefferfenster und kann verfehlen, geblockt oder durch einen Treffer unterbrochen werden.
--   Schaden = Schaden der beteiligten normalen Technik (CC_CharacterAnimations.MOVES) x scale, ohne K.o.-Bonus.
local S = {}

S.FOCUS_MAX = 100
S.FOCUS = {                    -- Gewinn je Ereignis (vorlaeufig)
	hit = 10,                  -- eigener gelandeter Schlag/Tritt (nicht geblockt)
	heavy = 14,                -- schwerer Treffer (Cross, Haken, Uppercut, Tritte)
	blockedHit = 3,            -- eigener Treffer in die Deckung (wenig: Druck zaehlt etwas)
	block = 6,                 -- gegnerischen Treffer erfolgreich geblockt
	sprawl = 18,               -- Takedown abgewehrt
	takedown = 14,             -- eigener Takedown gelungen
	groundHit = 6,             -- Bodenschlag gelandet
}

-- Signaturen. hits: eigene Trefferfenster (s ab Start der Animation bei Tempo 1), Bone, Zone und die normale Technik,
-- aus der Schaden/Reaktion kommen. trails: Zeitfenster (s) und Bones fuer die Bewegungsspur (nur schnelle Phasen).
S.list = {
	tyson = {
		name = "PEEK-A-BOO COMBO", short = "Left body hook + right uppercut", trainer = "Mike_Tyson",
		anim = "Fighter_Sig_Tyson", length = 30 / 24, lock = 1.18,
		stamina = 20, range = 4.1,                      -- Studs zwischen den Kaempfern: Start nur, wenn die Kombination real treffen kann (gemessen: trifft bis ~4,0)
		color = Color3.fromRGB(150, 20, 28),           -- dunkelrot
		hits = {
			{ win = { 0.30, 0.50 }, limb = "LeftHand", zone = "body", move = "hook", scale = 0.85, react = "hitBody", ko = "koFwd", impact = 0.8, bodyShot = true },
			{ win = { 0.58, 0.76 }, limb = "RightHand", zone = "head", move = "uppercut", scale = 1.0, react = "hitUpper", ko = "ko", impact = 1.3 },
		},
		trails = { { t = { 0.24, 0.48 }, bone = "LeftHand" }, { t = { 0.55, 0.76 }, bone = "RightHand" } },
	},
	ali = {
		-- Instinkt-Modus (Ultra-Instinkt-Idee): kein fester Schlag, sondern 5 s Zustand. Ali weicht bis zu 3 Treffern automatisch aus
		-- (Faust oder Tritt), sein Low Kick wird zum Calf Kick mit 2,5-fachem Schaden und schwerer Bein-Verletzung (beendet den Modus).
		-- Takedown-Versuch gegen ihn im Modus: Knie zum Kopf, Angreifer faellt kurz um (kein Knockdown), verbraucht ein Ausweichen.
		name = "INSTINCT MODE", short = "Dodges automatically · full-force calf kick", trainer = "Muhammad_Ali",
		special = "instinct", duration = 5.0, dodges = 3, calfMult = 2.5, calfInjury = 35,
		kneeDamage = 18, kneeInjury = 15, kneeDownTime = 1.6,   -- Takedown gegen Ali im Modus: Knie-Konter, Angreifer faellt und steht wieder auf
		anim = "Fighter_Sig_Ali", length = 26 / 24, lock = 0.2,
		stamina = 18, range = 99,
		color = Color3.fromRGB(205, 225, 255),         -- silbrig-blau
		hits = {},
		trails = {},
	},
	pereira = {
		name = "STONE HAND COUNTER", short = "Explosive left counter hook", trainer = "Alex_Pereira",
		anim = "Fighter_Sig_Pereira", length = 0.98, lock = 0.98, stamina = 22, range = 4.5,
		color = Color3.fromRGB(190, 44, 34),
		hits = { { win = { 0.33, 0.49 }, limb = "LeftHand", zone = "head", move = "hook", scale = 1.35, react = "hitHook", ko = "koFwd", impact = 1.4 } },
		trails = { { t = { 0.28, 0.49 }, bone = "LeftHand" } },
	},
	khabib = {
		-- Hochheben, Tragen, Slam (Paar TD_LiftSlam, Wrestling_Prototype_v04): Aufprall Frame 45 -> Zusatzschaden, roter Bildschirm beim Opfer.
		name = "EAGLE SLAM", short = "Lift, carry and slam onto the mat", trainer = "Khabib_Nurmagomedov",
		special = "takedown", slam = true, impactFrame = 45, slamDamage = 14, slamInjury = 10, stamina = 24, range = 5.0, length = 56 / 24, lock = 56 / 24,
		color = Color3.fromRGB(120, 95, 55), hits = {}, trails = {},
	},
	saenchai = {
		-- Rad-Kick (Cartwheel Kick): Saenchai dreht sich auf der linken Hand ins Rad, der rechte Fuss trifft von oben den Kopf.
		-- Animation Fighter_Sig_Saenchai_Wheel (Fighter_Rigged_v23): Treffer bei Frame 13-16 (0,50-0,66 s), Fuss erreicht das Kopfziel genau.
		name = "WHEEL KICK", short = "Cartwheel kick to the head", trainer = "Saenchai",
		anim = "Fighter_Sig_Saenchai_Wheel", length = 30 / 24, lock = 1.25, stamina = 22, range = 4.4,
		color = Color3.fromRGB(240, 235, 215),
		hits = { { win = { 0.48, 0.68 }, limb = "RightFoot", zone = "head", move = "highkick", scale = 1.35, react = "hitHook", ko = "ko", impact = 1.5 } },
		trails = { { t = { 0.36, 0.70 }, bone = "RightFoot" }, { t = { 0.30, 0.70 }, bone = "LeftFoot" } },
	},
	oliveira = {
		-- Ruecken nehmen + Rear Naked Choke (Paar Sig_BackTake, Ground_Positions_v02): unblockbar (Block/Sprawl helfen nicht),
		-- danach sofort das Wuerge-Duell mit Vorsprung (subStart) und staerkerem Zug (subPower). Befreien bleibt moeglich.
		name = "BRONX CHOKE", short = "Jump on the back and choke (unblockable)", trainer = "Charles_Oliveira",
		special = "backtake", stamina = 24, range = 4.8, length = 48 / 24, lock = 48 / 24,
		subStart = 0.50, subPower = 1.25, subTime = 4.5,
		color = Color3.fromRGB(220, 190, 85), hits = {}, trails = {},
	},
}
S.ORDER = { "tyson", "ali", "pereira", "khabib", "saenchai", "oliveira" }

-- Finisher-Wiederholung (nur nach vom Server bestaetigtem K.o. durch eine Signatur)
S.FINISHER = { before = 0.9, after = 0.6, slowFrom = -0.12, slowTo = 0.22, slowRate = 0.3, total = 2.6 }

-- Test (Studio): workspace-Attribut CC_TestSignature = "<id>" ruestet die Signatur aus und fuellt den Fokus nach jedem Versuch
-- wieder auf. Nie in regulaeren Matches setzen (wird beim Speichern des Place nicht gebraucht).
S.TEST_ATTR = "CC_TestSignature"

return S
