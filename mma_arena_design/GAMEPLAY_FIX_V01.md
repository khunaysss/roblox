# Gameplay-Überarbeitung v01 (Auftrag 2026-10-12)

## Abschnitt 1 – Springen und Takedown-Kamera (erledigt)
- **Kein Springen im 1-gegen-1-Kampf** (`CC_Input`): Springen-Zustand am eigenen Humanoid aus, solange `CC_Opponent` gesetzt ist. Das gilt für PC, Controller und den Touch-Sprungknopf.
  - Leertaste/A werden im Kampf geschluckt. Am Boden bleiben sie „Befreien“ (Submission-Duell: hämmern).
- **Ursache des Kamerafehlers:**
  - Beim Wechsel der Ringkampf-Animationen (Takedown, Positionswechsel) wurden alle Spuren hart gestoppt. Der Root-Bone stand dann einen Frame lang auf der Ruheposition, und der Körperpunkt sprang um ~4 Studs.
  - Zusätzlich wählte die Bodenkamera jedes Bild neu zwischen festen Kandidaten. Das ergab Wackeln um bis zu 1,5 Studs.
- **Behebung:**
  - `playPair` blendet in 0,06 s über.
  - Die Kamera glättet die Körperpunkte (Sprünge über 14 Studs/s werden begrenzt).
  - Die Bodenansicht wird stetig berechnet: Die Seite wird beim Eintritt festgelegt und nur gewechselt, wenn die Kamera außerhalb des Käfigs läge. Abstand und Höhe folgen aus dem Abstand der Kämpfer.
  - Langsameres Schwenken beim Überblenden (0,9 s).
  - Mindesthöhe über dem Käfigboden.
  - Im Ringkampf ist das Ziel immer der Kampfgegner, auch bei ausgeschalteter Anvisierung.
- **Absicherung** (`CC_CharacterAnimations`): Takedown, Befreien und Aufstehen prüfen nach jeder Wartezeit, ob der Ringkampf inzwischen zurückgesetzt wurde. Das betrifft Rundenende, Kampfende und Spieler weg. So gibt es kein Versetzen auf alte Positionen und keinen Fehler bei `a.wr = nil`.
  - K.o. während des Sprawl-Fensters löst den Ringkampf jetzt auf; vorher blieben beide verankert.
- **Geprüft in Studio** (1 Spieler gegen den Trainingsgegner, Kamera-Protokoll alle 0,3–0,4 s):
  - Leertaste im Kampf: kein Sprung.
  - Takedown abgewehrt: Kamera zurück hinter den Spieler.
  - Takedown erfolgreich: Bodenkamera schwankt nur noch 0,1 Studs, vorher 1,5.
  - E gehalten: nur ein Positionswechsel.
  - Rundenende am Boden: Ringkampf aufgelöst, Kampfkamera zurück.
  - Größter Kamerasprung pro Frame: 0,46 Studs.
- **Nicht getestet:** Spieler verlässt das Spiel mitten im Ringkampf (braucht 2 Clients), Controller und Touch.
