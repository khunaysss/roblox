# Cage Champions – PROJECT.md (zentraler Stand)

Neu zusammengestellt am 2026-10-17 aus `CURRENT.md`, `TASKS.md`, `GAME_DESIGN.md`, `CHATGPT_HANDOFF.md`.
Ältere Dokumente bleiben gültig für Details. Bei Widersprüchen gilt dieser Stand, bis der Nutzer ihn bestätigt.

## Festgelegte Entscheidungen (nicht ohne Zustimmung des Nutzers ändern)
- Projektleitung: Nutzer. Umsetzung: Claude (Blender, Roblox Studio über MCP). Planung, Balancing, Texte: ChatGPT (kein Repo-Zugriff).
- Desktop zuerst, Mobile später.
- Kein Veröffentlichen des Place, nichts Kostenpflichtiges.
- Keine Roblox-Arbeit ohne ausdrücklichen Auftrag.
- Bestehende Dateien nicht überschreiben; neue Version (v03 → v04 …).
- Nicht mit dem echten Profil testen: Testschlüssel `CC_TestProfileKey` benutzen; Testschalter danach entfernen.
- Animations-Upload nur durch den Nutzer (`upload_starten.ps1`), API-Schlüssel nie an Claude.
- Gruppe ANIMEXGANG (ID 7160158) für alle Uploads.
- Das Meme-Roll-Spiel im Repo (`characters/`, `world/`) nicht verändern.
- Spielkonzept: MMA-Spiel mit eigenem Kämpfer, Training, Kampfstilen, Karriere, Online. Gym und Lobby sind der Mittelpunkt, die Fight Night ist für besondere Kämpfe und Online-Events.
- Kampfstile haben Stärken und Schwächen; keiner ist grundsätzlich besser.
- Rangkämpfe nutzen gleiche Grundwerte.
- Freischaltungen dürfen Anfänger nicht chancenlos machen. Keine täglichen Energiegrenzen, keine bezahlten Stärkevorteile.
- Vorhandene Maps, Modelle, Animationen und UIs weiterverwenden.
- Signatur-Regeln: Fokus nur durch gelandete Treffer und erfolgreiche Abwehr im echten Kampf (nicht im Tutorial). Ein Versuch verbraucht den ganzen Fokus plus Ausdauer. Server prüft alles, Schaden kommt aus den normalen Techniken. Blut gibt es nicht.

## Fertig
### Spielablauf
- Einstieg: Editor mit „Fertig“ → Haupttrainer begrüßt → 6 Lektionen im Käfig → erster Trainingskampf (Tutorial, Studio getestet).
- Hauptmenü: Karriere (Fortschritt), Online, Training, Mein Kämpfer, Einstellungen = „bald“.
- Training: Trainingskampf gegen Dummy; Gym mit 20 Minispielen (Sandsack, Bank, Curls, Hampelmann).
- Kampfablauf: 3 Runden à 2:00, K.o./Punktsieg, HUD, Sounds.
- Spieler gegen Spieler: Warteschlange, Fight Night mit Walkout (Studio mit Testschaltern geprüft, nicht mit zwei echten Spielern).
- Profil im DataStore: Level, XP, Siege, Werte, Aussehen, Tutorial-Fortschritt.
- Fallschutz im Gym und Kampf.

### Kampfsystem
- Bewegung, Anvisierung, Kamera (Abschnitt A, PC geprüft).
- Schlagreichweite, Trefferprüfung, Kombos, Ausdauer (B, PC geprüft).
- Kicks und Basis-Moveset (C, PC geprüft).
- Takedowns, Kamera (D, PC geprüft).
- Bodenpositionen und Submissions (E, PC geprüft).
- Ringen, Trefferreaktionen, K.o. am Boden (Playtest geprüft).
- Bodenkampf-Übergang ohne Stand-Idle-Aufblitzen (2026-10-13, getestet).

### Signaturen
- Tyson „PEEK-A-BOO KOMBINATION“ (Körperhaken + Uppercut): Animation v19, Treffer, Fokus, VFX, HUD, Finisher, Unterbrechung getestet.
- Ali „SCHMETTERLING-SERIE“ (Jab-Jab-Cross): Animation v20, in Studio getestet (Reichweite 4,1 Studs).
- Whoosh-Sound: Roblox Pro Sound Effects 9120728815, in `SoundService.CC_Sounds`.
- Freischaltung beim Trainer: „Lernen“ → im Trainingskampf Kombination einmal landen → im Profil gespeichert (getestet mit Testprofil inkl. Neustart).

### Trainer
- Haupttrainer im Gym (E) und am Käfigrand.
- Sechs Stil-Trainer im Gym an der Ostseite (`CC_Trainers`), mit E: Panel mit Name, Stil, Signatur; lernen und ausrüsten (getestet).
- Trainer-Modelle importiert aus `export/Trainers_v01_Roblox.fbx` (`setup_trainers_v01.luau`).

### Animationen
- Hochgeladen in ANIMEXGANG: 64 IDs (Stand 2026-10-11) plus 34 weitere (105 insgesamt, geladen und geprüft).
- Ali und Tyson: als Keyframes in Studio, Upload noch offen.

### Gym-Lobby Design (2026-10-17, nur in Studio)
- Backup vorher: ServerStorage.CC_GymDesignBackup_Claude_20261017 (ganzes CC_Gym + Lighting-Effekte und -Werte).
- Boden: matte Anthrazit-Betonplatten, Trainingsflächen dunkler Gummi, Grappling dunkler Stoff; rote Neon-Bodenlinien → eingelassene matte Metallfugen.
- Licht: neutral-weiße Deckenspots, leicht kühle Fülllichter, Ambient weniger blau (Lighting.Ambient/OutdoorAmbient, CC_GymColor-Tönung neutral). Schatten nur noch 8 Spots (4 über dem Oktagon, je 1 pro Zone) statt 26. Neue Downlights über Empfang und Lounge.
- Rot nur noch als dunkle, kurze Akzente (Säulenbänder, Türen, Theke, Podest). Weiße Neon-Galeriekante und Treppen-Neon → Metall.
- Materialien: Säulen/Träger matt schwarzes Metall, Wände dunkler Beton, Wandpaneele dunkles Holz, Geräte gebürstetes Metall, Säcke schwarzes Leder.
- Zonenschilder (BOXEN, BODENKAMPF, KRAFT, KONDITION) jetzt fest an den Galerie-Stirnseiten statt schwebend.
- 6 Pflanzen (3 Typen, alle unterschiedlich) in dunklen Töpfen: Empfang (2), Lounge (2), Treppe, Trainertisch. Keine Überschneidungen (geprüft).
- Nachbesserung: Laufwege per Pfadsuche geprüft (Eingang → Empfang, Box, Bodenkampf, Kraft, Kondition, Treppe, Trainertisch, Spinde, Oktagon-Stufen: alle erreichbar). Käfigboden weniger grell. Warmes Licht auf die Empfangs-Holzwand. Poster (Fight Night, Disziplin, Respekt) und Gürtel-Vitrine an den Wänden unter den Galerien. Fugen im Gummiboden (6-Stud-Raster). Rote Säcke des Original-Gyms farblich angeglichen (Interaktionen unverändert). Wasserspender und Handtuchregal zwischen Kraft und Kondition.
- Neues Script roblox/CC_ZoneLighting.client.luau (nur Optik): Gym neutral, Fight Night (Kamera z < -400) behält die alten, kühleren Werte.
- Keine Kampf-/Trainings-/UI-Scripts geändert; kein Script greift auf die geänderten Teile zu (geprüft).

### Trainer-Quests und Endkampf (2026-10-17)
- System von Codex (CC_SignatureProgression, CC_Trainers, CC_Match Modus trainer, CC_Profile sig_start/sig_fight_result/sig_boss_result) in Studio durchgetestet: Quest starten → Fortschritt zählt → Herausforderung → Endkampf in der Fight Night → Niederlage gibt 25 XP ohne Freischaltung, Sieg schaltet frei und rüstet aus; bleibt nach Neustart erhalten (Testprofil).
- Behoben: Trainingsgegner (CC_TrainingDummy) war im Place komplett verankert (Körper, Handschuhe, Shorts) → stand in allen KI-Kämpfen fest (beim Trainer-Endkampf außerhalb des Käfigs). Körperteile gelöst (wie StarterCharacter).
- Behoben: Testschalter CC_TestNewPlayer stand noch am Workspace → es wurde kein Profil gespeichert. Entfernt.
- Trainer animierbar (Weg A): export_trainer_rigged_v01.py richtet das Trainer-Skelett auf die Kämpfer-Ruhehaltung aus (vorher bis 10° Abweichung, danach 0). check_trainer_rig_v01.py: Kämpfer-Animation auf die exportierte FBX übertragen, max. 3,6° Abweichung, Hände in Deckung. Tyson exportiert: export/Trainer_Mike_Tyson_Rigged_v01.fbx (wartet auf Import).

### Tyson animiert + Filmszenen (2026-10-17, in Studio getestet)
- Tyson als animierbares Modell im Gym (setup_trainer_rigged_v01.luau, ersetzt das starre Modell; altes nach ServerStorage.CC_Old). CC_TrainerAnim spielt die Idle.
- Eigene Tyson-Animationen (Fighter_Rigged_v21.blend, Export v23): Trainer_Tyson_Idle (Peek-a-boo, Bob & Weave), Trainer_Tyson_Greet, Trainer_Tyson_Respect. Füße fest, Start = Ende.
- Szenen-System: ReplicatedStorage.CC_TrainerScenes (Kamerafahrten/Animationen/Texte je Trainer), CC_TrainerScenes Server + Client. Szenen: greet (erstes Ansprechen je Sitzung), demo (nach Quest starten, Signatur in Zeitlupe), challenge (vor dem Endkampf; CC_Trainers startet den Kampf erst danach), unlock (automatisch zurück im Gym nach dem Sieg, Spieler vor dem Trainer).
- Kinobalken, Titel, Filmlicht nur lokal, Kamera-Kollision, Überspringen (Leertaste/Enter/Klick/Controller), sauberes Zurücksetzen (Kamera, Oberflächen, CC_UIBlock) – geprüft.
- Andere Trainer: Standard-Szenen (ruhige Kamera, ohne eigene Animation) bis ihre eigenen gebaut sind.

### T-Pose behoben (2026-10-17)
- Ursache: CC_CombatMotion stoppte die Steh-Animation des Spielers, solange CC_UIBlock gesetzt war (offenes Hauptmenü, Filmszenen) → T-Pose. Bedingung entfernt (UIBlock sperrt nur Eingaben); zusätzlich spielt die Szene selbst eine Steh-Animation. Getestet: Menü offen, Szene, danach → keine T-Pose. Original in ServerStorage.CC_TPoseFixBackup.

### Signaturen Tyson + Ali überarbeitet (2026-10-17, in Studio getestet)
- Tyson: dunkelrote Flammen-Aura mit leuchtendem Umriss während der Kombination; Uppercut-Treffer im Anime-Stil (Schweiß-Spritzer, Luft-Schockwellen, Impact-Frame schwarz-weiß, Speedlines, Kamera-Stoß). Schaden unverändert. Getestet: beide Treffer, Effekte sichtbar.
- Ali: neu „INSTINKT-MODUS“ statt Jab-Jab-Cross: 5 s Modus, weicht bis zu 3 Treffern automatisch aus (Faust oder Tritt; Nachbild + Seitschritt), Low Kick wird zum Calf Kick mit 2,5-fachem Schaden und +35 Bein-Verletzung (beendet den Modus). Silbrig-blaue Aura, Anzeige mit Restzeit und Ausweich-Punkten, bläuliche Tönung. Getestet: 2 Schläge ausgewichen ohne Schaden; Calf Kick 22 Schaden, Bein 35.
- Neues Script roblox/CC_SigUltimateFX.client.luau (nur Optik). Server-Änderungen in CC_CharacterAnimations (land: Ausweichen/Calf Kick; signature: Instinkt; Reset beendet Modus). Backup: ServerStorage.CC_UltimateBackup_20261017.

### Weitere Fertigstellungen
- Gym-Startort, Fallschutz, Curls auf der Hallenseite.
- Fight Night eingerichtet (`CC_FightNight` bei 0, 2,14, −700), Kollision, Kamera nimmt nächsten Käfig.
- Kämpfer-Anpassung (Frisur, Bart, Gesicht, Haut, Haarfarbe).
- UI-Schritte 1 und 2 (Designsystem `CC_UI`, Hauptmenü, Editor, Gym-Anzeigen, Ergebnisanzeige) – PC getestet.
- Blender-Modelle: Arena, Event-Map mit Backstage, Trainings-Gym v02, Haupttrainer v03, Ringrichter v02, Trainer v02, Fighter Design v03/Customization v05, Fighter Rigged bis v20.

## Offene Punkte
### Bugs / Prüfungen
- Zwei-Spieler-Test (Studio → Test → Clients 2) für Online, Fight Night, Walkout, Signatur, Finisher, Ergebnis, XP und Rückkehr ins Gym. **Noch nicht gemacht.**
- Touch (Geräte-Emulator) und echter Controller ungetestet.
- Gegner-KI: Verhalten nach Trefferschaden noch unfertig.
- Wrestling: Handschuh-Überlappung am Knie bis 13 cm (W1), Armbewegungen (W2), Guard-Durchdringung (W3), Aufstehen (W4).
- Gym: Bank/Matten ohne eigene Animation.
- Event-Map: 168 358 Dreiecke, keine Kollision (M1). Maßstabsdatei verweist auf alten Fighter (M2).
- Einstellungen-Menü fehlt; Schalter „Effekte reduzieren“ (`CC_ReduceFX`) ist nur vorbereitet.
- Upload nötig für online: alle Trainer_*-Animationen (18), Fighter_Sig_Tyson, Fighter_Sig_Ali (ohne Upload nur in Studio sichtbar).
- Im Test kamen Schläge über CC_Action im Kampf nicht beim Server an (keine Treffer, keine Meldung) – Codex hat den Angriffsweg evtl. geändert; mit echter Tastatur prüfen.
- Tysons Platz (Boxbereich, 100/16) liegt eng an Säule und Sack: Kamerawinkel mussten angepasst werden.
- Trainer-Endkampf: Champion-Tyson ist sehr stark (im Test 196:10 Schaden gegen mich); Balance noch nicht geprüft. Kein Walkout/Intro beim Trainer-Endkampf (startet direkt).
- Trainer-Namen sind echte Personen (rechtlich riskant vor Veröffentlichung).
- Die Animationen Fighter_Sig_Tyson / Fighter_Sig_Ali sind noch nicht hochgeladen; die Animationen Fighter_LegCheck_v01, Fighter_LimpLeft_v01, Fighter_LimpRight_v01 ebenfalls offen.
- Gym-Lobby: Laufen im Play-Modus nicht getestet (Hauptmenü sperrt die Steuerung beim Test). Fight-Night-Licht über CC_ZoneLighting zurückgesetzt (nicht im Spiel geprüft). Empfang noch eher dunkel. Place muss in Studio gespeichert werden (Strg+S).
- `CHATGPT_HANDOFF.md`, `TASKS.md`, `GAME_DESIGN.md` sind nicht immer synchron mit diesem Stand.

- Ali-Instinkt: Takedowns werden noch nicht ausgewichen (nur Schläge/Tritte). Balance (3 Ausweicher, 2,5-fach) vorläufig.
- Neue Signatur-Ideen offen: Khabib Tragen + Slam (roter Bildschirm), Saenchai Rad-Kick (Cartwheel), Oliveira Würgegriff von hinten (braucht Clinch-System).

### Aufgaben (Reihenfolge laut Nutzer)
1. Zwei-Spieler-Test Fight Night.
2. Einstellungen-Menü (Effekte aus, Kamera-Wackeln, Lautstärke) mit Profil-Speicherung.
3. Balancing der Signaturen (Fokus, Ausdauer, Schaden, Freischaltbedingung).
4. Fiktive Namen und Aussehen für die sechs Trainer.
5. Signaturen Pereira, Saenchai, Khabib (eigene Takedown-Logik, ohne Finisher). Oliveira braucht vorher ein Clinch-System.
6. Karriere: Gegnerliste (ca. 10 KI-Gegner, steigend), Titel, Belohnungen.
7. Ranked (später): gleiche Signatur-Auswahl für alle.
8. Vorführung der Signatur durch den Trainer (Ersatz über Dummy-Kämpfer).
9. Gym-Lobby: erledigt bis auf Laufen im Play-Modus (siehe Offene Punkte).

## Commits
- Letzter Commit mit Signatur-Arbeit: `1da508a` (Ali), `d1838a8` (CHATGPT_HANDOFF).
