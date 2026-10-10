# Abschnitt 7: Gegner-KI, Eingabegeräte, Konter (v01)

Stand: 2026-10-10. Getestet in Studio-Place „CageChampions“ (Gruppe ANIMEXGANG, Place-ID 106346306418073). Nicht veröffentlicht.

## Trainingsgegner bewegt sich (`roblox/CC_CharacterAnimations.server.luau`, Ende der Datei)
- Bewegung über `Humanoid:Move` (Server-Physik, nicht mehr verankert, nur im Ringkampf verankert). Die Fußarbeit-Loops laufen automatisch.
- Bewegt sich immer mit voller Geschwindigkeit oder steht still. Bei Teilgeschwindigkeit sind die Loops nur halb eingeblendet und die Füße rutschen.
- Verhalten:
  - hält einen Wunschabstand von 4,6 Studs (mehr bei wenig Leben oder Ausdauer) und kreist mit Richtungswechseln
  - steppt für Kombinationen hinein (12 Kombinationen inklusive Tritten) und danach oft wieder heraus
  - blockt gelegentlich, versucht zu 7 % einen Takedown
  - kreist am Gitter zur Mitte zurück
- Test-Schalter am Gegner:
  - `CC_Passive`: steht nur
  - `CC_ForceTD`: Takedown sofort
  - `CC_NoTD`: keine Takedowns

| Messung (Server, 25 s, Spieler steht) | Wert |
|---|---|
| Abstand | im Mittel 4,0 (2,5–6,8) |
| weitester Abstand zur Mitte | 13,4 (Gitter 14,5) |
| Höhe | 5,12–5,17 (soll 5,14) |
| Fußgleiten (langsamerer Fuß) | 3,05 bei 8 Studs/s = 38 % (vorher 54 %; Spieler zum Vergleich 31 %) |

- Nur kurz zugesehen (Standbild); kein Video.

## Controller (Studio-Eingabesimulation; echte Controller nicht getestet)
- Am Server angekommen:
  - X Jab, Y Cross, R1 Uppercut, R2 Low Kick
  - L2 Block, L1 Takedown, A Befreien
  - R3 Ziel
- **Neu:**
  - Steuerkreuz ← Body Kick, → High Kick, ↓ Front Kick; alle drei getestet.
  - ↑ ist bei Roblox fest für Menüs reserviert und wird nicht verwendet.
- B (Haken / Submission) lässt sich in Studio nicht simulieren, weil Roblox die Taste reserviert. Auf echten Controllern ist das zu prüfen.

## Touch
- Neue Bildschirmknöpfe: Upper, Low, Kick, High (dazu Jab, Cross, Haken, Block, TD, Ziel, Los).
- **Nicht getestet:** Studio meldet kein Touch-Gerät, deshalb erscheinen die Knöpfe nicht. Prüfen mit Studio → Test → Gerät (Handy-Emulator) oder auf dem Handy.

## Konter des Spielers (F) am Boden
- Gegner oben, Spieler drückt F im Rhythmus: Der Gegner versuchte zweimal Guard → Half Guard, beide Male „gekontert“; der Spieler blieb in der Guard.

## Offen
- Zwei-Spieler-Test (manuell zu starten, siehe CURRENT.md).
- Touch.
- Echter Controller mit B.
- Am Boden gibt es gegen Schläge keine Abwehr außer Befreien.
