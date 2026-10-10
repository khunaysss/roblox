# Trefferreaktionen v01 – schlagabhängig, Taumeln, K.o. nach vorne, Hitstop

Stand: 2026-10-10. Place `CageChampions_ImportTest_v01.rbxl` (in Studio). Nicht veröffentlicht, nichts hochgeladen.

## Blender
- `Fighter_Rigged_v08.blend` = v07 + 6 Actions (Skript `build_fighter_rigged_v08.py`, Werte `renders/fighter_rigged_v08_checks.json`). v07 unverändert.
  | Action | Frames | Inhalt |
  |---|---|---|
  | `Fighter_HitStraight` | 14 | Jab/Cross: Kopf schnappt in Frame 2 zurück (34°), Rumpf folgt, Deckung öffnet kurz |
  | `Fighter_HitHook` | 16 | Haken: Kopf dreht 48° weg + kippt 18°, Schulter rollt mit |
  | `Fighter_HitUpper` | 16 | Aufwärtshaken: Kinn 48° hoch, Arme fallen |
  | `Fighter_HitLeg` | 18 | Low Kick: vorderes Knie knickt, Hüfte fällt zur Seite |
  | `Fighter_Stagger` | 30 | schwerer Treffer: Knie wackeln, Kopf pendelt, Deckung kommt mühsam zurück |
  | `Fighter_KOForward` | 32 | K.o. nach vorne: Kopf dreht weg, Knie geben nach, auf die Knie, flach auf den Bauch (Wange am Boden) |
- Technik: Kopf wird gezielt um Welt-Achsen gedreht (`head_delta`), Deckung im Brustraum (Handschuhe bleiben nicht am Kopf kleben), Becken-Neigung für das Liegen, Kniepole fixiert (verhindert Umklappen), Handschuhe nie unter dem Boden.
- Korrekturen während der Prüfung: Kopf drehte anfangs kaum (alte Kopfsteuerung gedämpft); K.o. zuerst wie Liegestütz (Becken blieb aufrecht) und Knie 25 cm im Boden / Knie klappte in 1 Frame um – behoben. Rest: am Boden liegend höchstens 4–6 cm Kontakt unter Bodenniveau.
- Export `export_actions_roblox_v09.py` → `export/*_v09_keyframes.luau`; Studio-Loader `ServerStorage.CC_Animations.CC_Loader`.

## Spiel (`roblox/CC_CharacterAnimations.server.luau`, `roblox/CC_HitFX.client.luau`)
- Reaktion je Schlag: Jab/Cross → HitStraight, Haken → HitHook, Aufwärtshaken → HitUpper, Low Kick → HitLeg.
- Schwerer Treffer (Cross/Haken/Uppercut) unter 35 Leben: 60 % Taumeln (1,1 s, WalkSpeed 2).
- K.o.: nach Haken nach vorne, sonst nach hinten.
- Getroffene verlieren ihren laufenden Angriff (Unterbrechung).
- Hitstop 0,07 s (geblockt 0,035 s), Kamera-Ruck und rotes Aufblitzen bei eigenen Treffern (Remote `CC_HitFX`).
- Gegner-Attribut `CC_Passive` = steht nur (Training/Prüfung). Attribut `CC_LastReact` zeigt die letzte Reaktion.

## Geprüft (Playtest, echte Tasten/Klicks)
- Haken → hitHook, Aufwärtshaken → hitUpper, Low Kick → hitLeg, Jab/Cross → hitStraight.
- Bei 30 Leben: Haken → Taumeln (18), Haken → hitHook (6), Haken → K.o. nach vorne; nach 3 s wieder 100.
- Standbilder: Hakenreaktion (Kopf weggedreht), Gerade (Kopf zurück), K.o. nach vorne (flach liegend).
- Keine Fehler in der Konsole.

## Offen
- Taumeln, Aufwärtshaken- und Low-Kick-Reaktion nur über Zustände/Messwerte geprüft, nicht im Bild; Kamera-Ruck nicht im Bild prüfbar.
- Keine Körpertreffer (Leber/Bauch) und keine Kopf-Treffer-Varianten von links/rechts für den Cross.
- Kein Sound.
