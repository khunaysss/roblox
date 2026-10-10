# E: Bodenpositionen + Submissions (v01)

Stand: 2026-10-10. Place `CageChampions_ImportTest_v01.rbxl` (in Studio). Nicht veröffentlicht.

## Blender `Ground_Positions_v01.blend`
- Skript `build_ground_v01.py`. Es nutzt die Kontakt- und Prüf-Werkzeuge aus `build_wrestling_v03.py` unverändert.
- Werte in `renders/ground_v01_checks.json`, Vorschaubilder `renders/ground_v01_*.png`.
- Export mit `export_ground_roblox_v01.py` nach `export/*_v01_keyframes.luau`. Bezugspunkt ist derselbe wie beim Takedown (Startposition aus `TD_DoubleLeg_Success` Frame 1).

| Action (A oben, B unten) | Frames | Inhalt |
|---|---|---|
| Ground_Pass_Half | 36 | Guard öffnet, rechtes Knie rutscht durch → Half Guard |
| Ground_HalfGuard_Idle | 48 Loop | |
| Ground_Pass_Side | 40 | Hüfte hoch, Bein frei, Drehung → Side Control (A quer, Brust auf Brust) |
| Ground_Side_Idle | 48 Loop | |
| Ground_Side_To_Mount | 36 | Knie über den Bauch → Mount |
| Ground_Mount_Idle | 48 Loop | |
| Ground_Mount_Punch | 30 | Ausholen (5), Treffer (10), B deckt ab |
| Ground_Mount_To_Back | 48 | B dreht sich auf den Bauch, A steigt mit und setzt die Haken (Rücken flach) |
| Ground_Back_Idle | 48 Loop | |
| Sub_RNC | 60 | Arm unters Kinn (10), Griff (18), Würgen/Halten (30), Abklopfen auf die Matte (38–54) |
| Sub_Armbar | 60 | Handgelenk greifen (10), Drehen (20), Beine über Kopf/Brust (30), zurückfallen/Halten (40), Strecken (48), Abklopfen am Bein |

- Alle Übergänge sind nahtlos (0 cm zwischen Ende und nächster Position); Loops schließen bei 0 cm.
- Größte Überschneidung je Abschnitt: 11–14 cm, meist Hand bzw. Handschuh am Oberkörper des Gegners.
- Boden: meist innerhalb 4 cm. Ausnahmen:
  - Rollen auf den Bauch: B bis 15 cm
  - Rücken-Position: B bis 8 cm
  - RNC: A bis 8 cm
  - Armbar: A bis 7 cm
- Ein schneller Frame: beim RNC-Abklopfen bewegt sich Bs Arm 37 cm in einem Frame.

## Spiel (`roblox/CC_CharacterAnimations.server.luau`, HUD, Input)
- **Oben:**
  - E: Position verbessern (Guard → Half → Side → Mount → Rücken)
  - Linksklick: Schlag in Guard und Mount
  - Q: Submission (Mount: Armbar, Rücken: RNC)
- **Unten:** Leertaste befreit (eine Position zurück, aus der Guard aufstehen).
- **Konter:** F kurz nach Beginn des gegnerischen Wechsels. Die Animation läuft dann rückwärts zurück.
- **Submission-Duell:** Die Animation hält am Haltepunkt an. Oben hämmert Q, unten die Leertaste; ein Balken zeigt den Stand, weniger Leben unten hilft dem Angreifer. Bei 100 % wird abgeklopft, der Kampf endet als „Submission“. Bei 0 % oder nach 4 s läuft die Animation rückwärts zurück.
- **Kosten:**
  - Ausdauer: Positionswechsel 10, Befreien 14, Submission 16.
  - Ein Positionsgewinn zählt 4 Punkte für die Wertung, eine Submission 20.
- Trainingsgegner (wenn nicht passiv): schlägt, wechselt Position, versucht Submissions, befreit sich, kontert zu 30 % und hämmert im Duell.
- HUD: Positionsname, passende Tasten, Duell-Balken, „SUBMISSION!“; die Kampfwertung nennt „Submission“.
- **Fehler behoben (älter):** Fiel das Leben des Spielers auf 0 (jeder K.o.), stand er danach dauerhaft 2 Studs zu tief im Boden. Jetzt fällt das Leben nur auf 0,01.

## Geprüft (Playtest PC, nur ausgelöste Eingaben, kein echtes Tastendrücken)
- **Spieler oben:**
  - Positionen: Takedown → Half → Side → Mount → Rücken
  - Schlag aus dem Mount (−9)
  - RNC gewonnen: Duell 0,43 → 1,0, Abklopfen, K.o.-Status „submission“
  - Armbar: Gegner befreit sich, die Animation läuft rückwärts in den Mount
- **Gegner oben:**
  - Gegner: Schläge (Guard), Positionswechsel, Armbar und RNC
  - Spieler befreit sich (Half → Guard) und gewinnt beide Duelle durch Hämmern
  - Der Gegner kontert einen Befreiungsversuch
- Submission-Niederlage: „Kampf vorbei: blue (Submission)“; danach steht der Spieler wieder auf richtiger Höhe (5,14).
- Rückwärtslauf gemessen: Zeit läuft gleichmäßig von 1,52 auf 0 s.
- Standbilder:
  - Rücken-Position aus der Spielkamera
  - Duell-Balken („REAR NAKED CHOKE – Leertaste hämmern!“), aufgenommen, als der Spieler noch im Boden steckte (siehe Fehler oben)

## Offen
- F-Konter durch den Spieler nicht gezielt getestet (nur Konter des Gegners).
- Controller und Touch nicht getestet.
- Kein Video.
- Überschneidungen 11–14 cm.
- Positionswechsel nur in eine Richtung; Befreien geht genau eine Position zurück.
- Aus Half Guard, Side Control, Mount und Rücken kann man nicht direkt aufstehen.
