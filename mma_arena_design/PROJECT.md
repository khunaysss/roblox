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
- Ali: neu „INSTINKT-MODUS“ statt Jab-Jab-Cross: 5 s Modus, weicht bis zu 3 Treffern automatisch aus (Faust oder Tritt; Nachbild + Seitschritt), Low Kick wird zum Calf Kick mit 2,5-fachem Schaden und +35 Bein-Verletzung (beendet den Modus). Silbrig-blaue Aura, Anzeige mit Restzeit und Ausweich-Punkten, bläuliche Tönung. Getestet: 2 Schläge ausgewichen ohne Schaden; Calf Kick 22 Schaden, Bein 35. Takedown gegen Ali im Modus: Knie-Konter zum Kopf (18 Schaden, Kopf-Verletzung), Angreifer fällt und steht nach 1,6 s wieder auf (kein Knockdown-Zähler), verbraucht ein Ausweichen – getestet.
- Neues Script roblox/CC_SigUltimateFX.client.luau (nur Optik). Server-Änderungen in CC_CharacterAnimations (land: Ausweichen/Calf Kick; signature: Instinkt; Reset beendet Modus). Backup: ServerStorage.CC_UltimateBackup_20261017.

### Saenchai Rad-Kick (2026-10-17, in Studio getestet)
- Neue Animation Fighter_Sig_Saenchai_Wheel (Fighter_Rigged_v23, Export v25): Anlauf, Rad um die aufgesetzte linke Hand (Root-Drehung bis 126 Grad um die Hüfte), rechter Fuß trifft das Kopfziel genau (Frame 14), Landung in der Haltung. Boden: max. 2 cm Handschuh in einem Bild.
- Signatur „RAD-KICK“ (Kopftreffer, highkick x1,35, Reichweite 4,4): getestet Treffer bei 4,3 und 2,6 Studs (24 Schaden; teils Flash-K.o. mit Finisher-Wiederholung). Effekte: Wind-Ring beim Abdrücken, Anime-Treffer (wie Tyson, helle Farben), Spuren an beiden Füßen. Trainer-Text und Vorführung angepasst.

### Khabib Eagle Slam (2026-10-17, in Studio getestet)
- Neue Paar-Animation TD_LiftSlam_A/B (Wrestling_Prototype_v04, build_wrestling_v04.py, Export export_wrestling_roblox_v12): Schuss wie Double-Leg, Anheben über die Schulter, zwei Schritte tragen, Slam auf den Rücken (Aufprall Frame 45), Ende = Guard-Position wie TD_DoubleLeg_Success. Griffe 7 cm in den Schlüsselposen, im Slam bis 29 cm (schnelle Bewegung).
- Signatur „EAGLE SLAM“ (special takedown, slam=true): Zusatzschaden 14 + Rippen-Verletzung 10 beim Aufprall, danach Bodenkampf. Effekte: Staub, Schockwellen, Impact-Frame beim Angreifer, rötlicher Bildschirm + roter Rand + Kamera-Stoß beim Opfer. Getestet: Dummy 100 → 81 HP, Ereignis nach 2,4 s, Guard danach, roter Bildschirm sichtbar. Trainer-Text und Vorführung angepasst.

### Einstellungen, KI, Karriere, Trainer-Walkout (2026-10-17, in Studio getestet)
- Einstellungen: Lautstärke (Gesamt/Musik/Effekte) + Schalter „Starke Effekte“ und „Kamera-Wackeln“, im Profil gespeichert (CC_Profile settings, Remote CC_Progress "settings"). Getestet mit Testprofil: Klick → Server → gespeichert → nach Neustart geladen. Wackeln aus = kein Treffer-Ruckeln (CC_HitFX) und kein Kamera-Stoß (CC_SigUltimateFX); starke Effekte aus = nur schwacher Treffer-Blitz, keine Signatur-Bildschirmeffekte.
- Ringkampf-Leiste: während Takedown/Eagle Slam (Rolle shoot/defend) ausgeblendet, erst am Boden sichtbar (getestet).
- Gegner-KI reagiert auf Treffer: Kombination bricht ab; schwerer Schaden/angeschlagen/wenig Leben → Deckung + Rückzug (~1–1,8 s); leichter Treffer → oft Konter (Jab-Cross/Haken). Getestet: 16 Schaden → blockt und weicht 2 Studs zurück; leichte Treffer → 5/6 Konter.
- Karriere: 10 Gegner (neu Tomas Novak, Leon Brandt, Omar Haddad, Ivan Morozov), Ränge 10 → 1. Titel AMATEUR → AMATEUR-CHAMPION (2 Siege, +50 XP) → PROFI (4, +80) → TOP-HERAUSFORDERER (7, +120) → LEICHTGEWICHTS-CHAMPION (10, +250); Bonus nur beim ersten Erreichen, Hinweis „Neuer Titel“. Liste scrollbar, Titel in der Karriere-Übersicht (getestet). Backup: ServerStorage.CC_Opponents_PRE_CAREER10.
- Trainer-Endkampf und Karriere: Walkout mit Banner „TRAINER-ENDKAMPF“ / „KARRIERE“ und „Spieler vs. Gegner“; der KI-Gegner läuft mit ein (getestet mit Tyson).

### Oliveira Bronx Choke (2026-10-18, in Studio getestet)
- Neue Paar-Animation Sig_BackTake_A/B (Ground_Positions_v02, build_ground_v02.py, Export export_ground_roblox_v02): Armzug, Gegner dreht sich, Sprung auf den Rücken (Haken, Arm um den Hals), Gegner bricht auf Knie und Hände ein, Ende = Ground_Back_Idle Frame 1 (Übergänge 0,0 cm). Handschuhe beim Umklammern bis 13–15 cm im Körper (wie bei den übrigen Griffen, W1).
- Signatur „BRONX CHOKE“ (special backtake): unblockbar (kein Sprawl, Block wird gelöst), danach sofort Rear-Naked-Choke-Duell mit Vorsprung 0,50 und Zug ×1,25, ohne Ausdauerkosten; Befreien bleibt möglich. Effekt: goldener Ring/Funken, beim Opfer dunkler Bildrand. Getestet: Ablauf → Rücken-Kontrolle → Würge-Duell → Sieg per Submission bei schnellem Hämmern; ohne Hämmern befreit sich der Gegner. Trainer-Text/Vorführung angepasst. Kein Clinch-System nötig.

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
- Wrestling: Handschuh-Überlappung am Knie bis 13 cm (W1), Armbewegungen (W2), Guard-Durchdringung (W3), Aufstehen (W4).
- Gym: Bank/Matten ohne eigene Animation.
- Event-Map: 168 358 Dreiecke, keine Kollision (M1). Maßstabsdatei verweist auf alten Fighter (M2).
- Upload nötig für online: alle Trainer_*-Animationen (18), Fighter_Sig_Tyson, Fighter_Sig_Ali (ohne Upload nur in Studio sichtbar).
- Im Test kamen Schläge über CC_Action im Kampf nicht beim Server an (keine Treffer, keine Meldung) – Codex hat den Angriffsweg evtl. geändert; mit echter Tastatur prüfen.
- Tysons Platz (Boxbereich, 100/16) liegt eng an Säule und Sack: Kamerawinkel mussten angepasst werden.
- Trainer-Endkampf: Champion-Tyson ist sehr stark (im Test 196:10 Schaden gegen mich); Balance noch nicht geprüft.- Trainer-Namen sind echte Personen (rechtlich riskant vor Veröffentlichung).
- Die Animationen Fighter_Sig_Tyson / Fighter_Sig_Ali sind noch nicht hochgeladen; die Animationen Fighter_LegCheck_v01, Fighter_LimpLeft_v01, Fighter_LimpRight_v01 ebenfalls offen.
- Gym-Lobby: Laufen im Play-Modus nicht getestet (Hauptmenü sperrt die Steuerung beim Test). Fight-Night-Licht über CC_ZoneLighting zurückgesetzt (nicht im Spiel geprüft). Empfang noch eher dunkel. Place muss in Studio gespeichert werden (Strg+S).
- `CHATGPT_HANDOFF.md`, `TASKS.md`, `GAME_DESIGN.md` sind nicht immer synchron mit diesem Stand.

- Ali-Instinkt: Balance (3 Ausweicher, 2,5-fach Calf Kick, Knie 18) vorläufig.
- Flash-K.o. (Codex) löst bei starken Kopf-Signaturen oft sofort aus – Balance prüfen.
- Upload nötig: Fighter_Sig_Saenchai_Wheel, WR_TD_LiftSlam_A, WR_TD_LiftSlam_B, WR_Sig_BackTake_A, WR_Sig_BackTake_B.
- Bronx-Choke-Balance (Vorsprung 0,50, Zug ×1,25) vorläufig; mit echtem Gegner-Spieler prüfen.

### Aufgaben (Reihenfolge laut Nutzer)
1. Zwei-Spieler-Test Fight Night.
3. Balancing der Signaturen (Fokus, Ausdauer, Schaden, Freischaltbedingung).
4. Fiktive Namen und Aussehen für die sechs Trainer.
5. Signaturen Pereira, Saenchai, Khabib (eigene Takedown-Logik, ohne Finisher). Oliveira braucht vorher ein Clinch-System.
7. Ranked (später): gleiche Signatur-Auswahl für alle.
8. Vorführung der Signatur durch den Trainer (Ersatz über Dummy-Kämpfer).
9. Gym-Lobby: erledigt bis auf Laufen im Play-Modus (siehe Offene Punkte).

## Commits
- Letzter Commit mit Signatur-Arbeit: `1da508a` (Ali), `d1838a8` (CHATGPT_HANDOFF).

### Story-Einstieg – Qualitätsprobe (2026-10-18, wartet auf Freigabe)
- Alltagskleidung (Hoodie mit Kapuze/Kordeln/Tasche, Hose, Schuhe, Rucksack) als Hülle aus dem echten Körper-Mesh, gleiche Skin-Gewichte (build_casual_outfit_v01.py → Fighter_Casual_v01.blend, export/Fighter_Casual_v01.fbx, vom Nutzer importiert; Vorlage ServerStorage.CC_Story.Outfit_Casual, Farbe je Darsteller).
- Animationen Story_P_Confront / Story_S_Confront (Fighter_Casual_v02, Export v26): Griff an den Rucksackträger 3,5 cm, Füße 0 cm Rutschen. Gehen mit Fighter_CasualWalk_v2 im Animationstempo 6,43 Studs/s.
- Schulausschnitt Workspace.CC_StorySchool bei (-600, 0, 600), ca. 2.270 Teile (roblox/build_story_school_v01.luau): Straße, Gehwege, Ziegelzaun mit offenem Tor, Hof, 3-geschossige Schule mit Eingangsportal, Häuserzeile, Wohnblöcke, Bäume.
- Probe ServerStorage.CC_Story.CC_StoryProbe (roblox/CC_StoryProbe.module.luau): Gehen → Anhalten → Konfrontation mit 4 Kameraeinstellungen und Untertiteln. Aufnahmen: renders/story_probe_20261018/.
- Offen/bekannt: Kapuze wirkt in Nahaufnahmen wulstig; nackte Hände klein; Hausdächer im Hintergrund bilden ein V (falsch herum); Zaun ~920 Teile (zu viele); Menü-Kamera greift in Szenen ein (Szenen-Kamera braucht eigene Sperre); kein Video, nur Standbilder; neue Animationen/Kleidung brauchen Upload.
