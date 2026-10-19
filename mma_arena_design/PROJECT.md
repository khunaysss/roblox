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
- Story-Film überarbeitet (2026-10-19, in Studio getestet): englische Texte (Film, Rundflug, Hinweise, Tutorial), Schule „NORTHPARK HIGH SCHOOL“; Schubser mit Zeitlupe, Wackeln und Sound; Trainer rennt durchs Schultor und schreit (rot, Kamera-Stoß); Mobber rennen weg; größere Karte + lesbare Karten-Nahaufnahme; Zwischentitel „DAY 1 – FIRST LESSON“ (Film → Tutorial), „FIRST SPARRING“, „YOUR CAREER“ (nach dem Abschluss). Hände waren im Film sichtbar (geprüft).
- Spiel komplett auf Englisch (2026-10-19, in Studio getestet): Menü, Kampf-HUD, Gym-HUD, Minispiele, Trainer-Panel, Trainer-/Signaturtexte, Gegner und Tipps, Ziele/Titel (neu im Repo: roblox/CC_Progression.module.luau), Meldungen. Roblox kann von Englisch aus automatisch in andere Sprachen übersetzen (Creator Hub → Localization). Signaturen umbenannt: STONE HAND COUNTER (Pereira), WHEEL KICK (Saenchai).
- Ringrichter (2026-10-19, in Studio getestet mit Trainingskampf): ServerScriptService.CC_Referee (roblox/CC_Referee.server.luau), ein Ringrichter pro laufendem Kampf (alle Käfige). Geht seitlich der Kämpfer mit, „Fight!“-Zeichen, rennt bei K.o./Submission/T.K.O./Arzt dazwischen (neues Match-Attribut `Stoppage`), hält am Ende den Arm des Siegers hoch. Animationen Ref_Idle, Ref_Fight, Ref_Stop, Ref_RaiseHand, Fighter_WinRaise (build_referee_anims_v01.py → Fighter_Casual_v05.blend, Export v28, in CC_Animations geladen). Modell-Export export/Referee_Rigged_v01.fbx + setup_referee_v01.luau; bis zum Import steht ein Platzhalter (Story-Figur in Schwarz).
- Rundenpause in der Ecke (2026-10-19, in Studio getestet mit Trainingskampf, Runde 1→2→3): Beide Kämpfer sitzen in ihrer Ecke auf einem Hocker, ein Eck-Trainer kniet davor und gibt Wasser (Flasche am Mund), danach erklärt er. 3 s vor Rundenbeginn zurück in die Startposition. Kamera: eigene Ecke → Ecke des Gegners → Totale; unten beide Kämpfer mit Gesundheit, Ausdauer, Punkten. Neu: CC_Corner.server, CC_CornerView.client, Match-Attribut `Corner`; Animationen Fighter_CornerRest, Coach_CornerTalk (build_corner_anims_v01.py → Fighter_Casual_v06.blend, Export v29). Nur wenn die Pause ≥ 6 s ist.
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
- Sprache: Spiel ist englisch; Code-Kommentare, Logs und Backups in ServerStorage bleiben deutsch. `CC_BagPracticeUI` (Sandsack-Übung) liegt nur in Studio, nicht im Repo (englisch angepasst). Tutorial-Kasten überdeckt oben links teilweise Name/Ausdauerleiste.
- Upload (Stand 2026-10-19): 40 Animationen liegen als `export/anim_rbxmx/*.rbxmx` bereit und sind noch nicht hochgeladen: Ref_Idle/Fight/Stop/RaiseHand, Fighter_WinRaise, Fighter_CornerRest, Coach_CornerTalk, 12× Story_*, 21× Fighter_Sig_*/Trainer_*. Erzeugt mit `make_rbxmx_from_keyframes.js` (Umrechnung gegen DN_Down_Hit geprüft, Abweichung 0,000001). Nutzer startet `upload_starten.ps1`, danach trägt Claude die IDs in `CC_AnimIds` ein (Repo + Studio) und testet.
- Ringrichter: Modell noch importieren (Referee_Rigged_v01.fbx, dann `_G.CC_SetupReferee()`). Nicht geprüft: PvP mit zwei Spielern, Submission-Ende, Arzt-Abbruch, Bodenkampf (Ringrichter-Position), Regelverstöße (gibt es im Spiel noch nicht).
- Ecke: Animationen Fighter_CornerRest und Coach_CornerTalk hochladen. Eck-Trainer sind Story-Darsteller (kein eigenes Modell). Großes „ROUND 2 / Break“-Banner liegt mitten im Bild. Nicht geprüft: PvP mit zwei Spielern (beide Kameras), Fight Night.
- Beim Laden von Skripten nach Studio: LocalScript und Script heißen gleich (CC_Tutorial, CC_TrainerScenes) – immer nach ClassName unterscheiden.
- „FIRST SPARRING“-Titel und „YOUR CAREER“-Titel noch nicht im echten Ablauf gesehen (nur „DAY 1“ geprüft).

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

### Story-Einstieg „Der erste Schritt“ (2026-10-18, in Studio getestet)
- Film Szenen 1–9 (StarterPlayerScripts.CC_Story, roblox/CC_Story.client.luau), komplett lokal beim Spieler (eigene Darsteller, keine Überschneidung zwischen Spielern): Schulschluss → Konfrontation → Schubser mit Sturz → Trainer greift ein → Aufhelfen → Gym-Karte (echtes Logo) → „Am nächsten Nachmittag“ Gym-Tür → echtes Gym → Kampfstellung. Überspringen (Leertaste/Knopf), Kamera/FOV/Oberflächen/Licht werden wiederhergestellt.
- Ablauf: neuer Spieler → Editor „Fertig“ → Film → Profil onb.story = true → direkt erste Tutorial-Lektion (getestet mit Testprofil). Bestehende Spieler sehen den Film nicht (onb.story wird aus onb.editor übernommen). Einstellungen: „INTRO ANSEHEN“ (nur Film, kein Fortschritt).
- Kleidung v2 (Fighter_Casual_v04, export/Fighter_Casual_v02.fbx, importiert): einfache Hände, flachere Kapuze, Trainer-Trainingsanzug mit Streifen und Abzeichen. Story-Animationen (Export v27): Schubsen, Sturz/Sitzen, Hand heben, Aufhelfen (Hände 3,5 cm), Karte (5 cm), Tür, Nicken.
- Schule: Dächer korrigiert, Zaun 921 → 437 Teile, Gym-Front mit echtem Logo in der Häuserzeile (Szene 7). Filmlichter lokal für Tür- und Gym-Szene.
- Offen: alle Story-Animationen + Kleidung hochladen (sonst nur in Studio sichtbar); Abschlussszene nach dem ersten Sparring („War das schlecht?“) und Karriere-Erklärung noch nicht gebaut; einige Kameras noch eng (Kartenübergabe, Kampfstellung); beim Aufhelfen erreicht die Hand des Sitzenden die Trainerhand erst beim Hochziehen (vorher 17 cm Abstand); Hände am Boden beim Sitzen 15 cm über dem Boden.
- Story abgeschlossen (2026-10-18): Abschlussszene nach dem ersten Sparring („War das schlecht?“ – „Das war dein erster Tag.“ – „Morgen wieder?“ – Nicken), danach Karriere-Erklärung als Trainer-Hinweise (Menü → KARRIERE, Gegner-Stärken, Tipp, KAMPF STARTEN, alternativ weitertrainieren); erster offizieller Karriere-Kampf erklärt XP/Belohnung (Sieg oder Niederlage). Profil: onb.outro, onb.careerTip (bestehende Spieler gelten als erledigt). Getestet: Szene → gespeichert → Ergebnis-Panel → Karriere-Hinweis.
- GUI-Prüfung: Roblox-Leiste (0–208 × 0–58 px) überdeckt nichts (Menü-Logo ab y 85, Gym- und Kampfanzeige frei). Behoben: Tutorial-Panels lagen unter dem offenen Hauptmenü → werden jetzt ausgeblendet, solange das Menü offen ist (getestet).

### Gym: mehr Sandsäcke + Erklärungen beim ersten Mal (2026-10-18, in Studio getestet)
- Die 5 Deko-Sandsäcke im Boxbereich (z −16, x 82–124) sind jetzt Trainingsstationen (Heavy_Bag_Z1–Z5, Marker in CC_GymInteractions, Teile umbenannt, störende Pfosten ausgeblendet). Zusammen 7 Hängesäcke + Standsack. Getestet: Training startet, Haken trifft, Sack schwingt. Sicherung: ServerStorage.CC_BagsBackup_20261018.
- Erklärungen einmalig (Profil onb.gymTour/sigTour/onlineHint/editorHint/focusTip): Gym-Rundflug mit Kamera über 7 Stationen (Boxen, Kraft, Kondition, Bodenkampf, Stil-Trainer, Trainer-Tisch, Oktagon); Signatur-Erklärung mit Kamera auf den Stil-Trainer beim ersten Panel (Quests → Endkampf → Signatur, Fokus voll → G); Hinweise beim ersten Öffnen von Online und Mein Kämpfer; Hinweis bei erstem vollen Fokus. Getestet: Rundflug + Signatur-Erklärung (gespeichert, Panel danach offen). Online-/Kämpfer-/Fokus-Hinweis nicht einzeln getestet.
- Achtung: Ein Sack-Test lief versehentlich mit dem echten Profil (2 Schläge, Training nicht beendet).
- OFFEN (braucht Zwei-Spieler-Test): mehrere Online-Kämpfe gleichzeitig (mehrere Käfige, CC_Match verwaltet bisher nur einen Kampf).

### Neues Gym v03 (2026-10-18, in Studio eingebaut und getestet)
- Blender: build_training_gym_v03.py → Training_Gym_v03.blend, Export export_gym_roblox_v02 → export/Training_Gym_v03_Roblox.fbx (108 Teile, 48k Dreiecke), vom Nutzer importiert. In Studio: Workspace.CC_Gym.GymV03 (Floor_Slab-Mitte 160, -0.54, -12; nach Import 180° gedreht).
- Industrie-Studio im Arena-Stil: Stahlfachwerk-Decke, Lüftungsrohre, Hängelampen, Fensterfront rechts, Glas-Eingang, Galerie hinten (4,2 m) mit Glasgeländer + Treppe (unsichtbare Rampe Gallery_Stairs_Ramp), Sackreihe mit 7 Säcken (gleiche Namen wie Stationen → schwingen), rot-schwarze Puzzle-Matten, Zonenböden mit roten Linien, Logo als Steinplatte im Boden vor dem Oktagon, Wandlogo, Banner, Wandgrafik „TRAIN HARD · FIGHT SMART“. Oktagon, Geräte, Trainer, Stationen unverändert.
- Alte Halle ausgeblendet (ServerStorage.CC_GymOld_HiddenByV03), Sicherung des ganzen alten Gyms: ServerStorage.CC_GymBackup_v03_20261018. Alte Lampen-Lichter bleiben (Geometrie unsichtbar).
- Getestet (Testprofil): Laufen zu allen Zonen, Treppe hoch, Galerie entlang, Sack-Training Z2 (startet, schwingt). Oktagon-Podest blockiert den direkten Weg quer durch (gewollt).
- Offen: Licht auf die neue Halle abstimmen (aktuell alte Lichter), Plakate/Vitrine der alten Details evtl. nicht an Wänden; Galerie oben ist leer begehbar (nur Deko-Geräte).

### Mehrere Online-Kämpfe gleichzeitig (2026-10-19, allein getestet – Zwei-Spieler-Test offen)
- CC_Match umgebaut: jeder Kampf hat einen eigenen Zustand (ReplicatedStorage.CC_Matches.<id>, Modul CC_MatchRegistry) und einen eigenen Käfig. Käfige: Fight Night (Walkout), kleine Arena (Training/Tutorial/Sparring), neu CC_PvpArena_2/3/4 (Kopien der Arena bei x −400, z −160/0/160) → bis zu 4 Online-Kämpfe gleichzeitig + 1 KI-Kampf (nur ein KI-Gegner).
- Clients: CC_MatchStateMirror spiegelt den eigenen Kampf lokal nach CC_MatchState → HUD, Menü, Finisher, Tutorial unverändert. Server-Prüfungen (Fokus, Signatur, K.o., Zählen, Publikum) lesen den Zustand des eigenen Kampfs. Kamera und KI nutzen den Käfig des eigenen Kampfs.
- Getestet (1 Spieler): Training in der Arena; Online-Ablauf gegen KI (Testschalter CC_TestPvpDummy) in Fight Night mit Walkout und in Käfig 3 (CC_TestArena = "pvp3"); Ergebnis, XP, Rückkehr ins Gym, Zustand wird aufgeräumt.
- Sicherung: ServerStorage.CC_MultiMatchBackup_20261019.
- OFFEN: echter Test mit 2–4 Spielern (Studio → Test → Clients 2/4), gleichzeitige Kämpfe prüfen; Publikumsgeräusch ist noch global (alle hören jeden Kampf).
- Online-Arena-Wahl (2026-10-19, getestet allein): Online-Seite hat FIGHT NIGHT / KÄFIG / EGAL. Server paart nur passende Wahl („Egal“ passt zu allem); Fight Night → nur Fight Night, Käfig → CC_PvpArena_2..4 bzw. Arena. Getestet: „Käfig“ → pvp2, „Fight Night“ → fightnight.
- 10 Kampfplätze (2026-10-19): Fight Night, Arena, CC_PvpArena_2..9 (8 Käfige). Neue Käfige 5–9 bei x −560, z −320/−160/0/160/320 (Kopien der Arena, Abstand 160 Studs). Im Server registriert (CC_Match: PICK „Käfig“ nutzt 2–9 und Arena). Getestet: alle 8 Käfige im Ort. OFFEN: Test mit 10 gleichzeitigen Kämpfen (20 Spieler / Test-Clients), Trennwände zwischen den Käfigen, Publikum je Käfig (Entscheidung nötig: Trennung, Sichtschutz).
- Kaefig-Grenze (2026-10-19): Während eines Kampfs werden beide Kämpfer auf den Käfig begrenzt (Rand minus 1,5 Studs). Grund: Ein Takedown in der Nähe hat einen Kämpfer aus der Map geschoben. Getestet: 40 Studs nach außen geschoben → zurück im Käfig. Der Fallschutz (unter Y −25) bleibt zusätzlich.
- Menü-Reparatur (2026-10-19): Hauptmenü startete nicht (Roblox-Grenze 200 lokale Variablen überschritten durch Arena-Wahl + Einstellungen) → Teile in eigene Blöcke gefasst. Geprüft: Startmenü, Training, Online (Arena-Wahl), Einstellungen, Mein Kämpfer.
- Belohnungen fertig: Mein Kämpfer → SHORTS / HANDSCHUHE mit Farben, gesperrte mit Schloss + Bedingung. Getestet (Testprofil, Level 4): 3/10 Shorts frei, Hinweis „Neu freigeschaltet“, Blau gewählt + gespeichert → Shorts am Kämpfer blau; gesperrte Farbe per Remote erzwungen → Server lehnt ab.
- Achtung: Ein Testklick hat einen Trainingskampf mit dem echten Profil gestartet (abgebrochen, ggf. wenige XP).
