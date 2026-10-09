# Wrestling v02 – Korrektur der Guard-Kontakte

Datei: `mma_arena_design/Wrestling_Prototype_v02.blend` · Skript: `build_wrestling_v02.py` · Video: `renders/wrestling_v02_guard_punch.mp4` (3,5 s: Guard-Idle + Schlag, links Seite, rechts Dreiviertel)
Prüfwerte:
- `renders/wrestling_v02_checks.json`: Gesamtprüfung
- `renders/wrestling_v02_guard_contacts.json`: B's Beine gegen A's Hüfte und Rumpf
- `renders/wrestling_v01_guard_contacts_remeasured.json`: dieselbe Prüfung an v01

**v01 bleibt unverändert und gesichert:** `Wrestling_Prototype_v01.blend`, beide v01-Videos und `WRESTLING_ANIMATIONS.md` (Commit `616c9e1`, Prüfsummen kontrolliert). Ein Git-Tag ließ sich nicht pushen (der Remote lehnt Tags mit 403 ab).
Nur Blender. Nichts ist in Roblox getestet.

## Was korrigiert wurde
Körpermaße, Charakterdesign und Rig sind unverändert. Geändert wurden nur die Guard-Pose und die unmittelbar angrenzenden Schlüssel. Action-Namen, Längen und Timing sind wie in v01.

| Punkt | v01 | v02 |
|---|---|---|
| B's Becken (liegend) | y −0,80 | y −0,88 (8 cm mehr Hüftabstand) |
| B's Knöchel hinter A's Rücken | x ±0,15, y −0,15, z 0,66 | x ±0,16, y −0,26, z 0,84 (hohe geschlossene Guard) |
| B's Knie-Pole (Knieöffnung / Beinrotation) | x ±1,3, z 1,0 | x ±3,2, z 0,6 (Knie weit nach außen geöffnet, Oberschenkel um A's Hüfte gedreht) |
| A's kniende Position | Becken z 0,52 | Becken z 0,56 (4 cm höher, gleiche Neigung) |
| A's Hände | B's Becken, 12 cm Richtung Kopf | B's Becken, 3 cm Richtung Kopf, damit sie bei größerem Abstand erreichbar bleiben |
| B's Griffe | A's Unterarm, 8 cm vom Ellbogen | A's Unterarm, 17 cm vom Ellbogen (näher am Handgelenk, damit die Hände in Reichweite bleiben) |
| Idle-Bewegung | Becken A vor/zurück ±1,2 cm | ±0,6 cm |
| Landung (Takedown Frame 34) | B's Becken y −0,80, Füße z 0,54 | y −0,84, Füße weiter offen (x ±0,24, z 0,80); A's Becken z 0,56 |
| Schlag-Kontakt (Frame 11) | A lehnt bis y −0,42 nach vorn | A bleibt bei y −0,39 |
| Escape-Beginn | Beine direkt von hinten nach vorn zu A's Hüfte | Frame 4: Knöchel zuerst nach oben hinter A's Hüfte; Frame 6: zur Seite; ab Frame 8 wie v01 |

Unverändert (gleicher Code, gleiche Schlüssel): Takedown bis Frame 22, Sprawl, Escape ab Frame 8, Aufstehen.

## Messung: Durchdringung B's Beine ↔ A's Hüfte, Oberschenkel und Rumpf
Methode `check_guard_contacts.py`: jede geschlossene Mesh-Schale einzeln; ein Punkt gilt nur dann als „innen“, wenn er in der Bounding-Box liegt **und** zwei Strahlen in Gegenrichtung übereinstimmen. Geprüft wurde v01 und v02 mit derselben Methode.

| Prüfstelle | v01 | v02 |
|---|---|---|
| Ende Takedown (Frame 34–56) | 6,2 cm; 12 von 12 Frames über 3 cm | 6,9 cm nur bei Frame 34 (Landung); 2 von 12 Frames über 3 cm; ab Frame 38 unter 3 cm |
| Guard-Idle (1–48) | 6,8 cm; 24 von 24 über 3 cm | **3,6 cm**; 21 von 24 knapp über 3 cm |
| Guard-Schlag (1–36) | 6,7 cm; 18 von 18 | **4,8 cm**; 18 von 18 (B's Schienbein an A's Rücken) |
| Escape-Beginn (1–14) | 8,6 cm; 10 von 14 | 8,5 cm, nur bei Frame 5; 11 von 14 über 3 cm |

Weitere Werte in v02:
- Guard-Idle wiederholt sich nahtlos: Frame 49 = Frame 1, Nahtschritt 0,27 cm, größter Schritt 0,7 cm pro Frame.
- Übergänge an den Deform-Bones: Takedown → Idle 1,4 cm, Schlag → Idle 1,9 cm, alle anderen 0 cm (wie v01).
- Boden: B höchstens 1,7 cm im Boden (Guard), A nicht unter dem Boden; keine neuen Bodenüberschneidungen.
- Keine neuen Sprünge: Idle median 0,35 cm pro Frame, Schlag wie v01.

**Korrektur zur v01-Doku:** Die Durchdringungs-Prüfung von v01 (Normalen-Test) war bei den dünnen Shorts-Schalen und bei weich gewichteten Teilen unzuverlässig. Die in `WRESTLING_ANIMATIONS.md` genannten 7–9 cm für die Guard waren zu niedrig; mit der robusten Methode sind es 6,2–8,6 cm wie in der Tabelle. Bei der Entwicklung traten zwei weitere Messfehler auf; sie sind behoben und mit offengelegt:
- 0,45 m, weil der Normalen-Test bei Shorts-Schalen versagte
- 0,5 m, weil Teile ohne Bounding-Box-Filter als „innen“ gezählt wurden

## Verbleibende Fehler
- **Leichter Kontakt in der Guard:** B's Unterschenkel liegen an A's unterem Rücken bzw. Hüfte an, 3–5 cm tief. Das wirkt wie eine feste Umklammerung, ist aber technisch eine Überschneidung der Blöcke.
- **Landung (Takedown Frame 34–36):** kurz bis 6,9 cm, während die Beine um A schließen.
- **Escape-Beginn (Frame 5):** 8,5 cm; B's linkes Schienbein streift beim Öffnen A's Shorts-Hüftteil.
- **Griffe:** Die Handschuhe überlappen weiterhin bei den Griffen (Guard bis ca. 7–8 cm, Takedown bis ca. 13 cm).
- **Gleich wie v01, hier nicht bearbeitet:** schnelle Arm- und Fallbewegungen beim Schuss (bis 33 cm pro Frame), Root folgt dem Becken, kein Backen, kein Export, kein Roblox-Test.
- **Gesamtablauf:** Kein vollständiges Neu-Rendering des Ablaufs; die v01-Videos zeigen die alte Guard.

## Nächste Aufgaben (offen, noch nicht begonnen)
1. **Handschuh-Überlappungen korrigieren:** Griffe hinter den Knien (Takedown, bis ca. 13 cm), B's Griffe an A's Unterarmen und Handschuh an Handschuh in der Guard (bis ca. 7–8 cm).
2. **Arm- und Fallbewegungen weicher gestalten:** Schuss (Frame 13–15, bis 33 cm pro Frame), Hände zur Hüfte nach dem Anheben (Frame 26–29) und B's Fall- und Abstützbewegungen; Zwischenschlüssel bzw. Timing strecken.
3. **Guard-Landung und Escape ohne starke Durchdringung:** Landung Takedown Frame 34–36 (bis 6,9 cm) und Escape-Beginn Frame 5 (8,5 cm); zusätzlich der verbleibende Guard-Kontakt von 3–5 cm.
4. **Aufstehbewegung und Abschnittsübergänge prüfen:** `Ground_GetUp` aus Seiten- und Dreiviertelansicht bei normaler Geschwindigkeit. Übergänge Takedown → Idle (1,4 cm) und Schlag → Idle (1,9 cm) an den Gelenken angleichen.
5. **Animationen für den späteren Export vorbereiten:** Exportkopie mit gebackenen Actions (IK, Kontakte), ohne Kontroll-Bones; Root-Bewegung festlegen; Reimport in eine leere Blender-Szene prüfen. Wie beim Basiskämpfer: `export_fighter_rigged_v03.py`. Noch keine Roblox-Arbeit.
