# Fighter_Rigged_v04 – Jab-Action

Stand: 2026-10-09. Skript: `build_fighter_rigged_v04.py`. Messwerte: `renders/fighter_rigged_v04_jab_checks.json`. Nichts davon ist in Roblox getestet.

## Prüfung vorab: Gab es schon eine Jab-Action?
Nein. `Fighter_Rigged_v03.blend` enthält drei Actions: `Fighter_Idle_Bounce`, `Fighter_Test_Poses` und `Fighter_Preview_Sequence`.
Einen Jab gibt es dort nur als **Endpose**: Frame 21 in den Testposen (Marker `Jab_Endposition`) und als Abschnitt der Vorschau-Sequenz.
Deshalb habe ich **eine einzelne neue Action** `Fighter_Jab` auf dem vorhandenen Rig angelegt.

## Datei
- `Fighter_Rigged_v04.blend`: Kopie von v03. v03 selbst bleibt unverändert.
- Modell, Rig, Gewichtung, Anpassungsoptionen und Idle-Loop sind unverändert.
- `Fighter_Jab` ist aktiv, die Szene läuft von Frame 1 bis 18.
- Vorschau: `renders/fighter_rigged_v04_jab_preview.mp4`.
  - 3 s, 24 fps, 800 × 528, Cycles mit 8 Samples.
  - Inhalt: zweimal normale Geschwindigkeit, einmal halbe Geschwindigkeit. Links eine Ansicht von vorne (3/4), rechts von der Seite.

## Ablauf (24 fps, 18 Frames = 0,75 s, jeder Frame geschlüsselt)
| Frames | Phase | Inhalt |
|---|---|---|
| 1 | Start | Kampfhaltung, identisch mit Frame 1 des Idle-Loops |
| 1–3 | Vorbereitung | Kleiner Knie-Dip (1 cm), minimale Ausholbewegung der Hüfte (1,5°) |
| 3–6 | Schlag | Gerade Linie von der Deckung zum Kinn des Gegners: Hüfte dreht 6° ein, Schulter-Twist bis 15° |
| 6–8 | Halten | Arm gestreckt, Ellbogen 12° gebeugt |
| 8–15 | Rückkehr | Kontrolliert zurück, die Hüfte folgt der Hand leicht verzögert |
| 15–18 | Ende | Kampfhaltung, identisch mit Frame 1 |

Marker in der Action: `Start_Kampfhaltung` (1), `Vorbereitung` (3), `Jab_Treffer` (6), `Rueckkehr` (8), `Ende_Kampfhaltung` (18).

## Gemessene Werte
- Ellbogen der Schlaghand: minimal 12,0° gebeugt, also nie überstreckt. Kein Ellbogen-Flip.
- Reichweite: Der vordere Handschuh geht 0,50 m nach vorne. Die vordere Schulter kommt 9,6 cm mit.
- Hüftdrehung: von −28° auf −34°.
- Füße: 0,0 mm Rutschen. Die IK-Ziele der Füße sind die konstanten Fußpositionen der v03-Haltung. Tiefster Mesh-Punkt: z = −0,5 mm.
- Start und Ende weichen um 0,0 mm von der Idle-Haltung ab. Der Übergang zum Idle ist daher nahtlos.
- Hinterer Handschuh: dringt höchstens 1,2 cm in den Kopf ein. Unterarm in der Brust: 0. Vorderer Handschuh im Kopf: 0.

## Verbleibende Fehler / Einschränkungen
1. **Hinterer Handschuh** dringt bis zu 1,2 cm in Wange/Kinn ein (v02-Endpose: 0,9 cm). Das ist leicht sichtbar, aber nicht korrigiert.
2. **Handgelenk/Faust:** Die Rotation des Hand-IK-Ziels wird nicht animiert. Die Faust dreht beim Schlag nicht ein, in der Seitenansicht wirkt der Handschuh leicht verkippt.
3. **Abstand zum Kinn:** Der Messwert für den hinteren Handschuh (13–18 cm zum Kinnpunkt) beruht auf einem geschätzten Kinnpunkt. Optisch liegt der Handschuh an Wange/Kinn, der Wert ist aber nur ein Richtwert.
4. **Penetrationsmessung:** Sie nutzt die einfache Normalen-Methode wie in v03, nicht die robustere Paritätsmethode. Kleine Fehlwerte sind möglich.
5. **Schulter/Deltoid:** Die Mesh-Verformung an der Schulter bei gestrecktem Arm wurde nur in der Vorschau angesehen, nicht vermessen.
6. **Export:** Kein Export der Jab-Action. Die FBX-Dateien aus v03 enthalten nur das Idle. Roblox ist nicht getestet.
