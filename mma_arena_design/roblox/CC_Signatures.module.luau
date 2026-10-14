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
		name = "PEEK-A-BOO KOMBINATION", short = "Linker Koerperhaken + rechter Uppercut", trainer = "Mike_Tyson",
		anim = "Fighter_Sig_Tyson", length = 30 / 24, lock = 1.18,
		stamina = 20, range = 4.1,                      -- Studs zwischen den Kaempfern: Start nur, wenn die Kombination real treffen kann (gemessen: trifft bis ~4,0)
		color = Color3.fromRGB(150, 20, 28),           -- dunkelrot
		hits = {
			{ win = { 0.30, 0.50 }, limb = "LeftHand", zone = "body", move = "hook", scale = 0.85, react = "hitBody", ko = "koFwd", impact = 0.8, bodyShot = true },
			{ win = { 0.58, 0.76 }, limb = "RightHand", zone = "head", move = "uppercut", scale = 1.0, react = "hitUpper", ko = "ko", impact = 1.3 },
		},
		trails = { { t = { 0.24, 0.48 }, bone = "LeftHand" }, { t = { 0.55, 0.76 }, bone = "RightHand" } },
	},
}
S.ORDER = { "tyson" }           -- Reihenfolge in Menues (weitere Trainer folgen, siehe GAME_DESIGN.md)

-- Finisher-Wiederholung (nur nach vom Server bestaetigtem K.o. durch eine Signatur)
S.FINISHER = { before = 0.9, after = 0.6, slowFrom = -0.12, slowTo = 0.22, slowRate = 0.3, total = 2.6 }

-- Test (Studio): workspace-Attribut CC_TestSignature = "<id>" ruestet die Signatur aus und fuellt den Fokus nach jedem Versuch
-- wieder auf. Nie in regulaeren Matches setzen (wird beim Speichern des Place nicht gebraucht).
S.TEST_ATTR = "CC_TestSignature"

return S
