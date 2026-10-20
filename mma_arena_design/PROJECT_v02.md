# Cage Champions – Launch-Checkliste v02
Stand: 2026-10-20. Ergänzt PROJECT.md, ersetzt es nicht: Bestehende Dateien dürfen laut Auftrag nicht überschrieben werden.
Place 106346306418073; Branch claude/cage-champions-skills. Kein Publish, kein Kauf, keine Animations-Uploads.

## Abnahmegrenze
**Noch kein vollständiger Launch-Stand.** Implementiert und im Studio mit einem isolierten Testprofil geprüft; Zwei-Spieler-Test, Zielauflösungen und Namensfreigabe fehlen.
Alle Screenshots: tatsächlicher Viewport 1914×753. 1280×720 und 1920×1080 wurden NICHT getestet; Skalierung im Code ist kein Ersatz für Sichtprüfung.
Nur Profil CC_TestProfileKey=chatgpt_launch verwendet; echte Spielerprofildaten nicht absichtlich verändert.
Das Testprofil speichert tatsächlich separat. Reduce motion blieb nach Neustart erhalten; Claim hat echte Testprofil-XP erhöht.

## Phase 1
- [x] 54 vorhandene englische Ansagen, neun Kategorien; Textlänge höchstens acht Wörter geprüft.
- [x] Eigener Kampf, Entry/Fight/Corner/KO/Winner; Trainingsstart und erzwungener KO mit State=over, Winner=red, Stoppage=K.O.
- [x] Decision-Klassifikation nutzt auch BannerSub; tatsächlicher zeitbegrenzter Decision-Kampf geprüft.
- [ ] Echter schlagbedingter Knockdown nicht getestet. Nur CC_Knockdowns-Zählerfixture und dazugehörige Anzeige geprüft.
- [ ] Submission und Doctor-Ansage nicht durch tatsächlichen Abbruch getestet.
- [ ] Gewinnertext-Seitenkorrektur zuletzt statisch geprüft, nicht erneut zur Laufzeit.

## Phase 2 – implementiert, Abnahme jeweils begrenzt
| Bereich | Tatsächlicher Nachweis | Offen |
|---|---|---|
| a Hauptmenü | Screenshot, Navigation, Backspace schließt | Beide Zielauflösungen |
| b Karriere | Liste/Details gesichtet; READY rot/Schloss zuletzt im Code geprüft | Finale Aufnahme nach Status-Fix; Karriere-Kampf |
| c Online | Suchoberfläche/Arenawahl/Rangdarstellung gesichtet | Vollständiges Matchmaking/Abbruch mit zwei Accounts |
| d Training | Trainingskampf startet; reale aktivierte Stationen gezählt | Jede einzelne Station |
| e My Fighter | Editor/Einstieg/Done und Auswahloberfläche gesichtet, Farbfelder46px | Jede kosmetische Option, alle Sperren, Save-dialog-Regressionsmatrix |
| f Progress | Echte Tagesbelohnung abgeholt, Testprofil Level1 XP90→Level2 XP30 | Alle Zielvarianten |
| g Settings | Layout passt im tatsächlichen Viewport; Reduce motion serverseitig und nach Neustart true | Jede Regler-/Schalterkombination |
| h HUD | Echte HP/Stamina/Namen/Timer, Ground-Keycaps, Pause, KO und Decision geprüft | Fokus voll/alle Signaturen, echte PvP-Seiten |
| i BeltAward | Popup per Karriere-Siege-Attributfixture gesichtet | Regulär erspielte Freischaltung; keine echte Karriereunlock-Abnahme |
| j Corner | Echter Pausenzustand, Karten/Trainer; kontrastierter Titel und freie Announcerposition | Zielauflösungen |
| k Trainer | Reales E-Panel, Queststart → Server bestätigt started=true | Bosskampf/Ausrüsten jeder Signatur |
| l Tutorial | Sechs-Lektionen-Struktur, erste Lektion nach Content.none-Fix, Skip geprüft | Gesamter erneuter sechs-Lektionen-Durchlauf |
| m Story | Einstieg/Skip/Day1 geprüft; dunkle Untertitelunterlegung implementiert | Abschlussaufnahme nach Kontrast-Fix; kompletter Film |
| n Minigame | Laufband normal betreten/gestartet, Abbruch, Ergebnis, M dahinter blockiert | Alle Minispiele/Timingvarianten |
| o Loading | Replay des echten Scripts, große responsive Schrift, 100% bei vorhandenem HRP, Entfernung | Langsames Laden ohne vorhandenen Charakter; Zielauflösungen |
Die Lade-Meilensteine bleiben echte Zustände (UI10%, Character55%, HRP100%), kein Scheinfortschritt.

## Phase 3
- [ ] Namenfreigabe: Marcus Vale, Julian Reed, Adrian Stone, Niran Voss, Viktor Orlov, Lucas Navarro vorgeschlagen. Keine Antwort erhalten, daher noch NICHT ersetzt. Aktuelle reale Namen bleiben Launch-Blocker.
- [x] Edit-Modus am Schluss. CC_TestDoctor, CC_TestArena, CC_TestPvpDummy, CC_TestAIStyle, CC_TestProfileKey, CC_TestNewPlayer, CC_RoundTime, CC_BreakTime, CC_IntroTime alle nil, gelesen und geprüft.
- [x] Letzter Start/Trainingskampf: nur bekannte Asset203785492-/FoundationProvider-Warnungen, keine neuen Spielskriptfehler im Abschlusslauf.
- [x] 13 ausgelieferte Quellen mit Studio-Source exakt verglichen.
- [ ] Animationen vollständig: 150 IDs /174 Sequenzen. Client meldet87 vorgeladene Clips,0 Ladefehler; nicht174 visuell getestet.
- [x] Backups nicht gelöscht.
- [ ] Place muss Nutzer mit Strg+S speichern. Studio-Änderungen nicht als gespeicherte Place-Datei behaupten.
- [ ] Creator-Hub-Einrichtung und Veröffentlichung nicht ausgeführt.

### Sequenzen ohne veröffentlichte ID
Doc_Check; Fighter_BodyKick_v2; Fighter_CasualRun_v01; Fighter_Celebrate; Fighter_Cross_v01; Fighter_Cross_v02; Fighter_Dejected; Fighter_FrontKick_v2; Fighter_HighKick_v2; Fighter_Hook_v01; Fighter_Hook_v02; Fighter_Idle_v07; Fighter_Jab_v01; Fighter_Jab_v02; Fighter_LowKick_v01; Fighter_LowKick_v02; Fighter_LowKick_v4; Fighter_Sig_Saenchai_Wheel; Fighter_Uppercut_v01; Fighter_Walkout; WR_Sig_BackTake_A; WR_Sig_BackTake_B; WR_TD_LiftSlam_A; WR_TD_LiftSlam_B.
Einige sind ältere Varianten; fehlende ID bedeutet nicht automatisch aktiven Defekt. Walkout/Jubel/Verlierer/Arzt und aktive Signature-Paare separat im veröffentlichten Client prüfen. Upload nur durch Nutzer.

## Sichtprüfer-Urteil
Unabhängiger Fixlisten-Verdict: Decision, native Balkenspuren, Pausenlesbarkeit/Position, Stationsstatus und Ladetitel resolved; englische Copy/Karrierestatus im Code resolved.
Partial: echter Knockdown-Nachweis, Story-Abschlussaufnahme, Gewinnertext-Seitenkorrektur zur Laufzeit.
Keine Vollzertifizierung, kein Rebuild nötig. Native Luau: kein HTML/CSS-Detektor eingesetzt.

## Wiederherstellung
Backups liegen ausschließlich im geöffneten Studio-Place unter ServerStorage:
CC_Backup_20261020 (1 älterer Eintrag),
CC_Backup_20261020_CC_UI (4), _MainMenu (3), _HUD (2), _GymHUD (2),
_CC_Profile (1), _CC_LoadingScreen (2), _CC_Minigame (2),
_CC_TrainerPanel (2), _CC_BeltAward (2), _CC_AnnouncerHUD (3),
_CC_Story (1), _CC_CornerView (1).
Vor jedem Ersatz wurde der unmittelbar vorherige Source geklont. Kein Backup entfernt.
Zur Rücknahme Source aus passendem Before_*-Klon in ursprüngliches aktives Script übernehmen; neue CC_AnnouncerHUD/CC_VisualTheme deaktivieren, wenn vollständig auf alten Stil zurückgegangen wird.
Die bereits vor Auftrag veränderte CageChampions_ImportTest_v01.rbxl und renders/ui_screens_20261017 wurden nicht überschrieben und nicht in diesen Commit aufgenommen.

## Nutzer-Test: Clients 2
1. Studio im Edit-Modus öffnen; isolierten Testschlüssel setzen. Nur Testkonten, nie echte Profile.
2. Test-Tab → Clients 2 → Start. In beiden Fenstern ONLINE → identische Arena/ANY → START SEARCH.
3. Beide Seiten prüfen: eigener Kämpfer/Namen, Gegner, Kamera, Walkout, Timer, HP/Stamina und Ansagen.
4. Kampf beenden: beide Ergebnisse/XP/Bilanz vergleichen. Spieler verlassen lassen, Suche abbrechen, Rückkehr ins Gym prüfen.
5. Stop. Testattribute wieder entfernen. Beide Zielauflösungen pro Oberfläche prüfen.
6. Strg+S. Creator Hub: Name, Beschreibung, Icon, Thumbnail, Altersfreigabe und Preis selbst prüfen; erst danach Veröffentlichung erwägen.

## Dateien und Import
Siehe LAUNCH_MANIFEST_v02.md; Screenshots liegen in renders/launch_v02_20261020.
