# Fortschritt, Speicherung, Gym-Training (v01)

Stand: 2026-10-11. Studio-Place „CageChampions“ (Gruppe ANIMEXGANG). Nicht veröffentlicht.

## Profil (`roblox/CC_Profile.server.luau`)
- **Gespeichert** im DataStore `CC_Profiles_v1`, Schlüssel `u_<UserId>`: Level, XP, Siege, Niederlagen, K.o., Submissions und 4 Werte (0–20) mit Trainingspunkten.
- **Werte:**
  - Schlagkraft (Power)
  - Kondition (Cardio)
  - Ringen (Wrestling)
  - Bodenkampf (Grappling)
- **Steigerung:** 10 Trainingspunkte = +1 Wert. Level-Grenze: 100 + 50 × (Level − 1) XP.
- **Speichern:** beim Verlassen, alle 120 s und beim Server-Ende. Ein nicht geladenes Profil wird nie überschrieben.
- **XP aus Kämpfen:**
  - Spieler gegen Spieler: Sieg 60 (+20 bei K.o. oder Submission), Niederlage 25, Unentschieden 35; zählt in die Bilanz.
  - Training: 30 bzw. 15 XP, zählt nicht in die Bilanz.
- **Trainingspunkte aus Kämpfen:**
  - je Runde Kondition +2
  - Takedown bzw. Sprawl: Ringen +2
  - Positionswechsel bzw. Befreien: Bodenkampf +1
  - Submission gewonnen: +3, abgewehrt: +2

## Wirkung im Kampf (`CC_CharacterAnimations`)
- **Schlagkraft:** +1,5 % Schaden je Punkt (auch Bodenschläge).
- **Kondition:** +2 maximale Ausdauer und +2 % Erholung je Punkt. Das HUD nutzt `CC_StaminaMax`.
- **Ringen:** Sprawl-Fenster +0,01 s je Punkt des Verteidigers, −0,005 s je Punkt des Angreifers; gegen den Trainingsgegner seltener abgewehrt (mindestens 10 %).
- **Bodenkampf:** +2,5 % Wirkung je Tastendruck im Submission-Duell.
- Nebenbei behoben: Die Erschöpfungsanzeige am Boden nutzte die falsche Uhr.

## Gym-Stationen (`roblox/CC_GymTraining.server.luau`)
- Laufen erst nach dem Gym-Import. Sie nutzen die Interaktionspunkte aus `setup_gym_v01`.
- **Sandsack/Standsack:** 5er-Kombination mit Animationen, der Sack schwingt. Ergibt Schlagkraft +1 TP und 3 XP.
- **Hantelbank/Bankdrücken:** 4 s Schlagkraft +1 TP. **Matten:** 5 s Kondition +1 TP. Beides noch ohne eigene Animation.
- **Trainer-Tisch:** startet einen Trainingskampf. **Trainingsplan:** zeigt die eigenen Werte.
- **Menü:** Level, XP-Balken, 4 Werte mit Balken, Bilanz. **HUD:** Hinweise für Training, Level-Up, Wert-Anstieg und Übungsfortschritt.

## Geprüft (Studio, 1 Spieler)
- Profil lädt aus dem DataStore. 12 × Training ergab Schlagkraft 1 (2 TP); 130 XP ergaben Level 2.
- Ein Trainingskampf (verloren) ergab +15 XP und Kondition +4 TP (2 Runden); die Bilanz blieb unverändert.
- Testwerte danach auf den Startstand zurückgesetzt.
- **Nicht geprüft:**
  - Gym-Stationen (Gym noch nicht importiert)
  - Profil-Anzeige im Menü als Bild (Bildschirmfoto lief in die Zeitbegrenzung)
  - Speichern über das Verlassen hinaus mit echtem Server
