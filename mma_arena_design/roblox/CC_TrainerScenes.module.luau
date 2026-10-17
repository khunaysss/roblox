-- ReplicatedStorage.CC_TrainerScenes (ModuleScript) – Filmszenen der Stil-Trainer (Server und Client lesen dieselben Werte)
-- Szenen: greet (erstes Ansprechen in der Sitzung), demo (nach "Quest starten": Trainer zeigt die Signatur),
--         challenge (Herausforderung zum Endkampf, danach Kampf in der Fight Night), unlock (zurueck im Gym nach dem Sieg).
-- Kamera-Einstellungen relativ zum Trainer (Drehpunkt an den Fuessen, Trainer blickt nach -Z):
--   { t = Dauer s, from = Vector3, to = Vector3 (Kamerafahrt), look = Vector3 (Blickpunkt), fov = Grad }
-- anims: { at = s ab Szenenbeginn, name = Animation, slow = { von, bis, Tempo } (Zeitlupe in Animationszeit) }
-- Texte: title/sub erscheinen ab titleAt. Alle Werte VORLAEUFIG; Saetze der Trainer folgen spaeter (Platzhalter = nil).
local V = Vector3.new
local S = {}

S.list = {
	Mike_Tyson = {
		-- Tyson: lauernd, tief. Kamera von unten, langsames Heranfahren, harte Schnitte. (Kopf ca. 5,4 Studs ueber den Fuessen)
		greet = {
			length = 4.4, anims = { { at = 0.7, name = "Trainer_Tyson_Greet" } },
			shots = {
				{ t = 2.2, from = V(3.6, 1.9, -10.5), to = V(2.2, 2.3, -8.0), look = V(0, 4.8, 0), fov = 50 },
				{ t = 2.2, from = V(-2.0, 5.7, -4.5), to = V(-1.6, 5.6, -4.0), look = V(0, 5.4, -0.3), fov = 38 },
			},
			title = "MIKE TYSON", sub = "PEEK-A-BOO BOXEN", titleAt = 0.4,
		},
		demo = {
			length = 5.2, anims = { { at = 0.8, name = "Fighter_Sig_Tyson", slow = { 0.30, 0.74, 0.32 } } },
			shots = {
				{ t = 1.6, from = V(6.5, 3.8, -2.5), to = V(6.0, 3.8, -2.2), look = V(0, 4.2, -1.6), fov = 45 },
				{ t = 2.2, from = V(-3.4, 1.6, -5.2), to = V(-2.8, 1.8, -4.6), look = V(0, 4.6, -1.2), fov = 48 },
				{ t = 1.4, from = V(2.8, 5.2, -6.4), to = V(2.4, 5.0, -5.8), look = V(0, 4.6, 0), fov = 50 },
			},
			title = "PEEK-A-BOO KOMBINATION", sub = "Linker Körperhaken + rechter Uppercut", titleAt = 3.9,
		},
		challenge = {
			length = 3.8, anims = {},
			shots = {
				{ t = 1.6, from = V(0, 3.0, -11.0), to = V(0, 3.4, -8.5), look = V(0, 4.8, 0), fov = 45 },
				{ t = 2.2, from = V(-1.5, 5.7, -4.4), to = V(-1.2, 5.65, -3.9), look = V(0, 5.4, -0.3), fov = 36 },
			},
			title = "MIKE TYSON", sub = "FORDERT DICH HERAUS", titleAt = 1.6,
		},
		unlock = {
			length = 5.0, anims = { { at = 0.4, name = "Trainer_Tyson_Respect" } },
			shots = {
				{ t = 2.4, from = V(-5.0, 3.4, -5.0), to = V(-3.2, 3.8, -6.4), look = V(0, 4.6, -2.2), fov = 50 },
				{ t = 2.6, from = V(-7.0, 5.0, -2.4), to = V(-6.2, 5.0, -2.3), look = V(0, 4.6, -2.3), fov = 50 },
			},
			title = "SIGNATUR FREIGESCHALTET", sub = "PEEK-A-BOO KOMBINATION · Taste G", titleAt = 2.4,
		},
	},
}

-- Fallback fuer Trainer ohne eigene Szenen (ruhige Standardkamera, keine eigene Animation)
S.default = {
	greet = { length = 3.0, anims = {}, shots = { { t = 3.0, from = V(2.5, 3.0, -8.0), to = V(1.5, 3.4, -6.0), look = V(0, 4.8, 0), fov = 45 } }, titleAt = 0.4 },
	demo = { length = 0, anims = {}, shots = {} },
	challenge = { length = 3.0, anims = {}, shots = { { t = 3.0, from = V(0, 2.4, -9), to = V(0, 2.8, -7), look = V(0, 4.0, 0), fov = 45 } }, sub = "FORDERT DICH HERAUS", titleAt = 1.0 },
	unlock = { length = 3.5, anims = {}, shots = { { t = 3.5, from = V(4.0, 3.0, -6.0), to = V(2.8, 3.2, -6.5), look = V(0, 3.8, -2.0), fov = 48 } }, title = "SIGNATUR FREIGESCHALTET", titleAt = 1.2 },
}

function S.get(trainerId, kind)
	local t = S.list[trainerId]
	return (t and t[kind]) or S.default[kind]
end

S.UNLOCK_SPOT = V(0, 0, -4.5)          -- Spielerposition vor dem Trainer in der Freischalt-Szene (relativ zum Trainer)

return S
