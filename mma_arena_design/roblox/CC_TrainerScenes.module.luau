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
			title = "MIKE TYSON", sub = "PEEK-A-BOO BOXING", titleAt = 0.4,
		},
		demo = {
			length = 5.2, anims = { { at = 0.8, name = "Fighter_Sig_Tyson", slow = { 0.30, 0.74, 0.32 } } },
			shots = {
				{ t = 1.6, from = V(6.5, 3.8, -2.5), to = V(6.0, 3.8, -2.2), look = V(0, 4.2, -1.6), fov = 45 },
				{ t = 2.2, from = V(-3.4, 1.6, -5.2), to = V(-2.8, 1.8, -4.6), look = V(0, 4.6, -1.2), fov = 48 },
				{ t = 1.4, from = V(2.8, 5.2, -6.4), to = V(2.4, 5.0, -5.8), look = V(0, 4.6, 0), fov = 50 },
			},
			title = "PEEK-A-BOO COMBO", sub = "Left body hook + right uppercut", titleAt = 3.9,
		},
		challenge = {
			length = 3.8, anims = {},
			shots = {
				{ t = 1.6, from = V(0, 3.0, -11.0), to = V(0, 3.4, -8.5), look = V(0, 4.8, 0), fov = 45 },
				{ t = 2.2, from = V(-1.5, 5.7, -4.4), to = V(-1.2, 5.65, -3.9), look = V(0, 5.4, -0.3), fov = 36 },
			},
			title = "MIKE TYSON", sub = "CHALLENGES YOU", titleAt = 1.6,
		},
		unlock = {
			length = 5.0, anims = { { at = 0.4, name = "Trainer_Tyson_Respect" } },
			shots = {
				{ t = 2.4, from = V(-5.0, 3.4, -5.0), to = V(-3.2, 3.8, -6.4), look = V(0, 4.6, -2.2), fov = 50 },
				{ t = 2.6, from = V(-7.0, 5.0, -2.4), to = V(-6.2, 5.0, -2.3), look = V(0, 4.6, -2.3), fov = 50 },
			},
			title = "SIGNATURE UNLOCKED", sub = "PEEK-A-BOO COMBO · Key G", titleAt = 2.4,
		},
	},
}

-- Fallback fuer Trainer ohne eigene Szenen (ruhige Standardkamera, keine eigene Animation)
S.default = {
	greet = { length = 3.0, anims = {}, shots = { { t = 3.0, from = V(2.5, 3.0, -8.0), to = V(1.5, 3.4, -6.0), look = V(0, 4.8, 0), fov = 45 } }, titleAt = 0.4 },
	demo = { length = 0, anims = {}, shots = {} },
	challenge = { length = 3.0, anims = {}, shots = { { t = 3.0, from = V(0, 2.4, -9), to = V(0, 2.8, -7), look = V(0, 4.0, 0), fov = 45 } }, sub = "CHALLENGES YOU", titleAt = 1.0 },
	unlock = { length = 3.5, anims = {}, shots = { { t = 3.5, from = V(4.0, 3.0, -6.0), to = V(2.8, 3.2, -6.5), look = V(0, 3.8, -2.0), fov = 48 } }, title = "SIGNATURE UNLOCKED", titleAt = 1.2 },
}

-- Weitere Trainer: gleicher Aufbau, eigene Kameraart und eigene Animationen (Fighter_Rigged_v22, Export v24).
-- h = Kopfhoehe (Studs ueber den Fuessen) in der Haltung; demo = vorhandene Kampfanimation als Vorfuehrung.
local function trainer(o)
	local h, c = o.h, o.cam
	return {
		greet = { length = 4.4, anims = { { at = 0.6, name = o.prefix .. "_Greet" } },
			shots = { c.greet1, { t = 2.2, from = V(-1.8, h + 0.3, -4.6), to = V(-1.4, h + 0.2, -4.0), look = V(0, h, -0.3), fov = 38 } },
			title = o.name, sub = o.style, titleAt = 0.4 },
		demo = { length = 5.0, anims = { { at = 0.8, name = o.demo, slow = o.slow } },
			shots = { c.demo1, { t = 2.0, from = V(-3.4, 1.6, -5.4), to = V(-2.8, 1.8, -4.8), look = V(0, h - 1.0, -1.2), fov = 48 },
				{ t = 1.4, from = V(2.8, h - 0.2, -6.4), to = V(2.4, h - 0.4, -5.8), look = V(0, h - 1.0, 0), fov = 50 } },
			title = o.sigName, sub = o.sigSub, titleAt = 3.7 },
		challenge = { length = 3.8, anims = {},
			shots = { c.challenge1, { t = 2.2, from = V(-1.5, h + 0.3, -4.4), to = V(-1.2, h + 0.25, -3.9), look = V(0, h, -0.3), fov = 36 } },
			title = o.name, sub = "CHALLENGES YOU", titleAt = 1.6 },
		unlock = { length = 5.0, anims = { { at = 0.4, name = o.prefix .. "_Respect" } },
			shots = { { t = 2.4, from = V(-6.8, 3.6, -7.4), to = V(-4.6, 4.0, -8.8), look = V(0, h - 0.8, -2.4), fov = 46 },
				{ t = 2.6, from = V(-7.0, h - 0.4, -2.4), to = V(-6.2, h - 0.4, -2.3), look = V(0, h - 0.8, -2.3), fov = 50 } },
			title = "SIGNATURE UNLOCKED", sub = o.sigName .. " · Key G", titleAt = 2.4 },
	}
end
S.list.Muhammad_Ali = trainer({   -- Ali: tanzend, selbstbewusst. Kamera schwenkt seitlich vor ihm vorbei.
	name = "MUHAMMAD ALI", style = "DANCING BOXING", prefix = "Trainer_Ali", h = 6.0,
	demo = "Fighter_LowKick_v5", slow = { 0.12, 0.40, 0.35 }, sigName = "INSTINCT MODE", sigSub = "Automatisch ausweichen · Calf Kick",
	cam = { greet1 = { t = 2.2, from = V(-5.0, 4.6, -8.5), to = V(4.0, 4.8, -8.5), look = V(0, 5.0, 0), fov = 48 },
		demo1 = { t = 1.6, from = V(6.5, 4.2, -2.5), to = V(6.0, 4.2, -2.2), look = V(0, 4.6, -1.6), fov = 45 },
		challenge1 = { t = 1.6, from = V(3.5, 4.5, -9.5), to = V(-3.0, 4.6, -8.5), look = V(0, 5.2, 0), fov = 45 } },
})
S.list.Alex_Pereira = trainer({   -- Pereira: ruhig, kalt. Lange, fast statische Einstellungen aus der Distanz.
	name = "ALEX PEREIRA", style = "KICKBOXING", prefix = "Trainer_Pereira", h = 6.0,
	demo = "Fighter_Hook_v03", slow = { 0.12, 0.36, 0.3 }, sigName = "STONE HAND COUNTER", sigSub = "Linker Konterhaken",
	cam = { greet1 = { t = 2.2, from = V(0, 4.4, -12.5), to = V(0, 4.4, -12.0), look = V(0, 5.0, 0), fov = 34 },
		demo1 = { t = 1.6, from = V(6.5, 4.4, -2.0), to = V(6.4, 4.4, -2.0), look = V(0, 4.8, -1.2), fov = 42 },
		challenge1 = { t = 1.6, from = V(0, 4.6, -13.0), to = V(0, 4.6, -12.6), look = V(0, 5.2, 0), fov = 32 } },
})
S.list.Khabib_Nurmagomedov = trainer({   -- Khabib: Ringer. Kamera tief am Boden, Druck nach vorn.
	name = "KHABIB NURMAGOMEDOV", style = "WRESTLING", prefix = "Trainer_Khabib", h = 5.1,
	demo = "WR_TD_LiftSlam_A", slow = { 0.70, 0.84, 0.35 }, sigName = "EAGLE SLAM", sigSub = "Hochheben, tragen, slammen",
	cam = { greet1 = { t = 2.2, from = V(2.6, 0.8, -8.5), to = V(1.8, 1.0, -6.6), look = V(0, 4.2, 0), fov = 52 },
		demo1 = { t = 1.6, from = V(7.0, 1.4, -3.0), to = V(6.5, 1.5, -3.0), look = V(0, 3.0, -2.0), fov = 48 },
		challenge1 = { t = 1.6, from = V(0, 0.9, -9.5), to = V(0, 1.2, -7.5), look = V(0, 4.4, 0), fov = 48 } },
})
S.list.Saenchai = trainer({   -- Saenchai: verspielt, leicht. Kamera seitlich, gleitend.
	name = "SAENCHAI", style = "MUAY THAI", prefix = "Trainer_Saenchai", h = 5.9,
	demo = "Fighter_Sig_Saenchai_Wheel", slow = { 0.42, 0.70, 0.3 }, sigName = "WHEEL KICK", sigSub = "Cartwheel kick to the head",
	cam = { greet1 = { t = 2.2, from = V(8.5, 3.8, -2.0), to = V(6.5, 4.0, -6.0), look = V(0, 4.4, -0.5), fov = 46 },
		demo1 = { t = 1.6, from = V(6.8, 3.4, -2.6), to = V(6.4, 3.4, -2.4), look = V(0, 3.8, -1.8), fov = 46 },
		challenge1 = { t = 1.6, from = V(5.5, 4.0, -6.0), to = V(3.0, 4.4, -7.5), look = V(0, 5.0, 0), fov = 44 } },
})
S.list.Charles_Oliveira = trainer({   -- Oliveira: Grappler mit Muay Thai. Kamera nah dran, ueber die Schulter.
	name = "CHARLES OLIVEIRA", style = "MUAY THAI / BJJ", prefix = "Trainer_Oliveira", h = 6.0,
	demo = "WR_Sig_BackTake_A", slow = { 0.40, 0.70, 0.4 }, sigName = "BRONX CHOKE", sigSub = "Take the back, then choke",
	cam = { greet1 = { t = 2.2, from = V(-2.6, 4.8, -5.4), to = V(-1.8, 5.0, -4.4), look = V(0, 5.4, 0), fov = 42 },
		demo1 = { t = 1.6, from = V(6.5, 3.8, -2.4), to = V(6.0, 3.8, -2.2), look = V(0, 4.0, -1.4), fov = 46 },
		challenge1 = { t = 1.6, from = V(-2.2, 4.6, -6.5), to = V(-1.6, 4.9, -5.2), look = V(0, 5.5, 0), fov = 40 } },
})

function S.get(trainerId, kind)
	local t = S.list[trainerId]
	return (t and t[kind]) or S.default[kind]
end

S.UNLOCK_SPOT = V(0, 0, -4.5)          -- Spielerposition vor dem Trainer in der Freischalt-Szene (relativ zum Trainer)

return S
