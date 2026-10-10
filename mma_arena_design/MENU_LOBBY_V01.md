# Menü, Lobby, Training und Spieler gegen Spieler (v01)

Stand: 2026-10-10. Studio-Place „CageChampions“ (Gruppe ANIMEXGANG, Place-ID 106346306418073). Nicht veröffentlicht.

## Ablauf
- **Lobby:** Neue Spieler stehen auf dem Hallenboden vor dem Käfig (0, 0, 25). Der Spawn im Käfig bleibt; das Skript versetzt sie.
- **Menü** (links, `StarterGui.CC_MenuGui.Menu` = `roblox/CC_Menu.client.luau`):
  - TRAINING: Kampf gegen den Trainingsgegner.
  - GEGEN SPIELER: Warteschlange; die ersten zwei kämpfen.
  - ABBRECHEN verlässt die Warteschlange.
  - Statuszeile zeigt z. B. „Kampf läuft: A gegen B“ oder „Warte auf einen Gegner … (1/2)“.
- **Arena-Regel:** eine Arena, ein Kampf gleichzeitig. Spieler-gegen-Spieler hat Vorrang, die anderen warten in der Lobby und sehen zu.
- **Kampf:** 3 × 2:00, Sieg durch K.o., Submission, Punkte oder „Aufgabe“, wenn ein Kämpfer das Spiel verlässt. Danach geht es zurück in die Lobby.
- **Trainingsgegner:** parkt außerhalb des Käfigs (Hallenecke) und ist nur im Trainingskampf aktiv (`CC_InMatch`).
- **In der Lobby wird nicht gekämpft:** Aktionen und Block nur mit `CC_Opponent`.
  - Anvisieren und Kampfkamera nur gegen den eigenen Gegner.
  - Das HUD zeigt Lebensbalken nur im Kampf und den Namen des Gegners.
  - Kämpfer sehen SIEG oder NIEDERLAGE, Zuschauer „<Name> GEWINNT“.

## Geprüft (Studio, ein Spieler)
- Lobby mit Menü (Standbild).
- TRAINING:
  - Der Kampf startet; Gegner, Zielerfassung und HUD stimmen, das Menü ist ausgeblendet.
  - Der Gegner gewann per Armbar.
  - Danach steht der Spieler in der Lobby (richtige Höhe), der Gegner parkt außerhalb.
- GEGEN SPIELER allein: „Warte auf einen Gegner … (1/2)“, ABBRECHEN setzt zurück.
- **Nicht getestet:** echter Kampf zweier Spieler, Zuschauer, Spieler verlässt das Spiel.
  - Testen: Studio → Test → Clients und Server: 2 Spieler → Start. In beiden Fenstern GEGEN SPIELER klicken.
