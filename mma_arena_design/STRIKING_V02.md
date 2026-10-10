# B: Schlagreichweite, Trefferprüfung, Kombinationen, Ausdauer (v02)

Stand: 2026-10-10. Place `CageChampions_ImportTest_v01.rbxl` (in Studio). Nicht veröffentlicht.

## Animationen (Blender `Fighter_Rigged_v11.blend` = v10 + 8 Actions; Skript `build_fighter_rigged_v11.py`, Werte `renders/fighter_rigged_v11_checks.json`, Export `export_actions_roblox_v13.py`)
| Action | Änderung | Handschuh vorn (m) |
|---|---|---|
| `Fighter_Jab_v3` | vorderer Fuß 22 cm Schritt, Hüfte 8 cm vor, Faust eingedreht | 0,94 (v2: 0,88) |
| `Fighter_Cross_v3` | Schritt 20 cm + hinterer Fuß zieht nach, Hüfte 17 cm vor | 0,91 |
| `Fighter_JabBody` / `Fighter_CrossBody` | Körperschläge: tief über die Knie, Schritt | 1,03 / 1,00 (Bauchhöhe) |
| `Fighter_Hook_v3` | Schritt 25 cm, Hüfte vor, Ellbogen bleibt gebeugt, Ziel vor der Kinnmitte | 0,70 |
| `Fighter_Uppercut_v2` | Schritt 14 cm, Hüfte vor | 0,60 |
| `Fighter_LowKick_v3` | Treffpunkt weiter vorn, Standbein schiebt nach | – |
| `Fighter_HitBody` | Körpertreffer-Reaktion: klappt zusammen, Hände zum Bauch | – |
Phasen der Geraden: 1–3 Vorbereitung, 3–6 Streckung mit Schritt, 6–8 Treffer, 8–15 Rückkehr (Fuß zieht zurück), 15–18 Deckung. Ellbogen nie unter 10° (keine Überstreckung). Kein Körperpunkt unter dem Boden.

## Trefferprüfung (`roblox/CC_CharacterAnimations.server.luau`)
- Treffer nur, wenn die **sichtbare Faust bzw. der Fuß** (Hand-/Fuß-Bone auf dem Server) im Trefferfenster in der Trefferkugel des Gegners ist: Kopf (Radius 0,95 Studs, am Oberkörper verankert), Körper (1,25), Bein (1,1). Keine Reichweitenzahl mehr.
- Trefferfenster je Schlag (Gerade 0,10–0,30 s, Haken 0,27–0,40, Uppercut 0,32–0,46, Low Kick 0,36–0,50).
- Kopf-/Körpertreffer mit eigener Reaktion; hohe Deckung schützt den Körper nur halb.
- Neuer Schlag blendet den vorherigen aus (sonst mischen sich zwei Schläge und der Arm streckt sich nicht).
- Diagnose: workspace-Attribut `CC_DebugHits` → Konsole zeigt bei Fehlschlag den kleinsten Abstand zur Trefferzone.

## Kombinationen und Ausdauer
- Ausdauer 100; Kosten Jab 5, Cross 8, Haken 10, Uppercut 11, Körper 5/8, Low Kick 12; Treffer/Block kosten den Getroffenen 2–4; Erholung 16/s nach 0,6 s Pause (nicht im Block).
- Unter 25 Ausdauer: 70 % Schaden, Schläge 15 % langsamer; zu wenig Ausdauer → Schlag wird nicht ausgeführt (Balken blinkt rot).
- Eingaben während eines Schlags werden nur in den letzten 0,3 s gepuffert (genau eine) → flüssige Kombos, kein Dauerfeuer.
- HUD: gelbe Ausdauerbalken unter den Lebensbalken. Umschalttaste + Links-/Rechtsklick = Körperschlag.
- Test-Attribut: workspace `CC_RoundTime` (Sekunden) verlängert die Rundenzeit.

## Geprüft (Playtest PC, Eingaben über den echten Remote-Weg)
| Schlag | trifft bei Abstand (Studs) |
|---|---|
| Jab, Cross, Körper-Jab, Körper-Cross | 2,5–4,5 |
| Haken, Uppercut, Low Kick | 2,5–3,0 (Nahdistanz; Haken vorher nur 2,5) |
- Kombinationen: Jab-Jab-Cross 22 (alle treffen), Cross-Haken 22, Jab-Cross 16. Vorher verfehlte der zweite Schlag (Mischung zweier Schläge, zurückweichender Kopf) – behoben.
- Spammen: 20 Klicks in 1 s → 4 Jabs. 40 Cross nacheinander → Ausdauer bis 10, Schaden fällt von 10 auf 7.
- Standbild: Jab mit Schritt erreicht das Gesicht des Gegners.

## Offen
- Kopf-Hitbox folgt nicht der Kopfreaktion (bewusst, damit Kombos nicht ausweichen).
- Haken/Uppercut nur Nahdistanz; Uppercut-Ausholen streckt den Arm kurz (im Bild nicht geprüft).
- Controller/Touch: Körperschläge nicht belegt; nicht getestet.
- Trainingsgegner bewegt sich nicht (verankert) – nötig für echtes Distanzspiel (Abschnitt 7).
