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

## Kämpfer-Anpassung (v01)
- **Export:** `export_custom_parts_v01.py` aus `Fighter_Rigged_v12.blend`, ohne Kontroll-Bones, gleiche FBX-Einstellungen wie der Basis-Charakter.
  - Ergebnis: `export/Fighter_Custom_v01.fbx` (16 Bones; 4 Frisuren, 2 Bärte, 3 Gesichter; 34 Teile, 5 932 Dreiecke) und `export/Fighter_Custom_v01_data.luau`.
- **`roblox/CC_Customize.server.luau`:** Frisur, Bart, Gesicht, Hautton (4) und Haarfarbe (6). Gespeichert im Profil (`look`, Attribut `CC_Look`); wird bei jedem Spawn und jeder Änderung angewendet.
  - Kopfteile werden über Motor6D mit dem Versatz aus `CC_C0` an das HumanoidRootPart gehängt (wie beim Basis-Charakter).
- **`roblox/setup_custom_v01.luau`:** richtet nach dem Import die Vorlagen ein (`ServerStorage.CC_Custom`). Prüft den Versatz der Quiff-Kappe gegen den Basis-Charakter.
- **Menü:** Knopf **KÄMPFER** öffnet „DEIN KÄMPFER“ mit Pfeilen je Kategorie. Spiegel und Spinde im Gym öffnen die Anpassung ebenfalls.
- **Geprüft (Studio):**
  - Hautton „dunkel“ und Haarfarbe „blond“ (inklusive Brauen) werden sofort angewendet und gespeichert.
  - Panel als Standbild geprüft. Testwerte danach zurückgesetzt.
- **Nicht geprüft (wartet auf Import):** Wechsel von Frisur, Bart und Gesicht, also ob die skinned Teile am Kopf mitlaufen.

## Gym in Studio (2026-10-12)
- **Import und Einrichtung:** Nutzer hat importiert, `setup_gym_v01` ausgeführt. `CC_Gym`: Bodenmitte (160, 0, 0), 433 Teile gefärbt, 22 Teile mit genauer Kollision, 96 fest, 37 COL-Teile, 34 Lampen, 33 Interaktionspunkte.
- **Fehler gefunden und behoben:** Der FBX-Import dreht das Modell um 180° um Y, deshalb lagen Punkte, Kollision und Lampen zuerst gespiegelt. Jetzt liegen Marker und Modell 0–2 Studs auseinander.
- **Startort:** Spieler starten im Gym hinter dem Eingang (HRP-Höhe 3,05). 19 Trainingsstationen mit Hinweis (E).
- **Sandsack mit E getestet:** Kombination läuft, Schlagkraft +1 TP. Standbild geprüft.
- **Kamera:** Außerhalb des Kampfs steckte die Kamera in Geräten, weil das Roblox-Kameramodul im Place fehlt. Neu: Hindernis-Ausweichen in `CC_Camera`, geprüft per Standbild.
- **Anpassung:** Der erste Import enthielt nur die Standard-Variante, weil ausgeblendete Varianten nicht exportiert wurden. Behoben in `export_custom_parts_v02.py` → `export/Fighter_Custom_v02.fbx` (34 Teile). Wartet auf erneuten Import.
- **Anpassung eingerichtet (2026-10-12):** Fighter_Custom_v02 importiert. `setup_custom_v01` hat 34 Teile in `ServerStorage.CC_Custom` eingerichtet; der Versatz der Quiff-Kappe weicht 0,0000 Studs vom Basis-Charakter ab.
  - Im Playtest gewechselt zu Seitenscheitel, Vollbart und „freundlich“: Teile ausgetauscht. Standbild zeigt sie am Kopf in Kampfhaltung, sie bewegen sich mit.
  - Testaussehen danach zurückgesetzt.
  - Nicht geprüft: alle 4 × 3 × 3 Kombinationen einzeln, Locken (3 840 Dreiecke) auf dem Handy.

## Locker-Modus + Gym-Animationen (2026-10-12)
- **Blender** (`build_fighter_rigged_v13.py` → `Fighter_Rigged_v13.blend`, Laufen korrigiert in `build_fighter_rigged_v14.py` → `Fighter_Rigged_v14.blend`).
  - Export: `export_actions_roblox_v15.py` bzw. `v16`. Prüfwerte: `renders/fighter_rigged_v13_checks.json` und `v14`.
  - Locker stehen (48 Frames), Gehen (18 Frames, 1,80 m/s), Laufen (12 Frames, 4,2 m/s; v13 hatte 14 Frames und ein zu langes Bein-Ziel).
  - Bankdrücken (liegt auf dem Rücken, Root −90° um X), Kurzhantel-Curls, Hampelmann; alle als Loops.
- **Spiel:**
  - Ohne Kampf (`CC_Opponent` fehlt) spielt locker Stehen/Gehen/Laufen. Gehtempo 6,4, mit Umschalttaste (Controller: L3) Laufen mit 15.
  - Im Kampf wieder Kampfstellung und Fußarbeit mit Tempo 8 (beim Kampfstart zurückgesetzt).
  - **Gym-Stationen:**
    - Hantelbank: der Kämpfer liegt auf der Bank, Kopf zur Stange.
    - Kurzhanteln: Curls.
    - Matten: Hampelmann.
    - HumanoidRootPart während der Übung verankert.
- **Geprüft (Studio, Spieler):**
  - Gehen: Fußgleiten 0,06 bei 6,4 Studs/s.
  - Laufen: 0,28 bei 15 Studs/s (v13 hatte 3,64).
  - Bankdrücken, Hampelmann und Curls je mit Standbild; nach der Bank wieder an der Ausgangsstelle (Höhe 3,06).
  - Wechsel zur Kampfstellung beim Trainingskampf (Loop 1,33 s, Tempo 8).
- **Upload:** 6 neue Animationen als `export/anim_rbxmx/*.rbxmx` vorbereitet. Upload durch den Nutzer nötig (`upload_starten.ps1`); ohne Upload laufen sie nur im Einzeltest in Studio.
- Nicht geprüft: Controller-Sprint (L3), Dummy im Locker-Modus beim Parken.
