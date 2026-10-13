# Cage Champions – Spielkonzept (Game Design)

Gemeinsame Planung mit dem Nutzer (Projektleitung). Grundlage: `CURRENT.md`, `TASKS.md`, `GAMEPLAY_STAND.md` und der Stand im Studio-Place „CageChampions“.
Planungsschritte: 1 Einstieg/erste 15 Minuten · 2 Gym/Training/Trainer/Stile · 3 Karriere/Story/Gegner · 4 Online/Ränge · 5 Belohnungen/Langzeit · 6 Umfang Release/Updates.
Erst nach Freigabe der fertigen Planung wird gebaut.

## Bestätigt
Richtung vom Nutzer (Auftrag 2026-10-13):
- Ziel: verständliches MMA-Spiel – eigenen Kämpfer erstellen, trainieren, Kampfstile lernen, Karriere durchlaufen, gegen andere Spieler kämpfen.
- Gym und Lobby sind der Mittelpunkt. Die große Fight-Night-Arena ist für besondere Kämpfe und Online-Events.
- Einstieg: Kämpfer erstellen → Haupttrainer → kurzes Tutorial → erster Trainingskampf.
- Karriere: Amateurkämpfe → stärkere Gegner → Fight Night → Titelkampf.
- Spezialisierte Trainer vermitteln Boxen, Kickboxen und Wrestling.
- Kampfstile haben Stärken und Schwächen; keiner ist grundsätzlich besser.
- Rangkämpfe verwenden gleiche Grundwerte, damit Können entscheidet.
- Siege und Niederlagen ermöglichen Fortschritt.
- Langfristige Ziele: Ränge, Kosmetik, Titel und Titelverteidigung.
- Desktop zuerst, Mobile später.
- Leitlinien:
  - Training soll Spaß machen und echte Kampffähigkeiten vermitteln.
  - Kein endloses Pflichttraining vor dem Kämpfen.
  - Freischaltungen dürfen Anfänger nicht chancenlos machen.
  - Karriere und Online haben unterschiedliche, klare Ziele.
  - Keine täglichen Energiegrenzen und keine bezahlten Stärkevorteile ohne ausdrückliche Entscheidung des Nutzers.
  - Für den Start ein überschaubarer, vollständiger Spielablauf; Erweiterungen getrennt vormerken.
  - Vorhandene Maps, Modelle, Animationen und UIs nutzen.

## Vorgeschlagen (noch nicht bestätigt)
### Schritt 1 – Die ersten 15 Minuten (Vorschlag 2026-10-13)
| Minute | Was passiert | Nutzt Vorhandenes |
|---|---|---|
| 0–2 | Ladebildschirm → Kämpfer erstellen (Frisur, Bart, Gesicht, Haut, Haarfarbe) | Ladebildschirm, Charakter-Editor |
| 2–3 | Start im Gym; der Haupttrainer begrüßt den Spieler und nennt das erste Ziel: „Zeig mir, was du kannst“ | Gym, Haupttrainer-Modell (noch nicht im Spiel) |
| 3–7 | Kurzes Tutorial im Gym-Käfig gegen den passiven Gegner: Laufen, Jab/Cross, Block, ein Kick, Takedown. Jede Aufgabe ist eine kurze Anzeige, z. B. „Lande 3 Jabs“ | Kampfsystem, passiver Trainingsgegner, Kampf-HUD |
| 7–11 | Erster Trainingskampf gegen den Anfänger-Gegner (1 Runde); Sieg ist gut erreichbar | Anfänger-Stufe, Kampfablauf |
| 11–13 | Ergebnis mit XP; der Trainer zeigt eine Gym-Station (z. B. Sandsack) als erstes Training | Ergebnisanzeige, Minispiele |
| 13–15 | Freies Gym mit klarem nächstem Ziel: „Erster Amateurkampf“ (Karriere) – Online ist frei zugänglich | Hauptmenü Karriere/Online |
- Grundsatz: Der erste echte Kampf kommt nach ca. 7 Minuten; Gym-Training ist danach Angebot, keine Pflicht.

## Noch zu entscheiden
- Schritt 1: Tutorial Pflicht oder überspringbar? · Wer ist der erste Gegner? · Kämpfer-Erstellung vollständig am Anfang oder Schnellwahl?
- Schritte 2–6 sind noch nicht besprochen.

## Bereits umgesetzt (laut Projektstand, Studio-Tests mit 1 Spieler)
- Kampfsystem:
  - Stand-Kampf mit Schlägen, Tritten, Block, Kombos und Ausdauer
  - Takedown/Sprawl, Bodenpositionen, Submissions mit Duell
  - 3 Runden à 2 Minuten, Sieg durch K.o., Submission oder Punkte
- Trainingsgegner mit Stufen Passiv / Anfänger / Profi, im Trainingsmenü wählbar.
- Gym als Startort, 20 Stationen. Minispiele:
  - Sandsack/Standsack (Tastenfolge)
  - Bank, Curls, Hampelmann (Rhythmus)
  - Laufband (Tempo halten)
- Belohnung mit Trainingspunkten und XP, serverseitig geprüft.
- Profil wird gespeichert: Level, XP, Bilanz, 4 Werte (Schlagkraft, Kondition, Ringen, Bodenkampf), Aussehen. Das Level hat noch keine eigene Wirkung.
- Charakter-Editor und Hauptmenü:
  - Karriere: nur Werteübersicht, noch keine echte Karriere
  - Online: Warteschlange, mit 2 echten Spielern noch nicht getestet
  - Training, Mein Kämpfer
  - Einstellungen gesperrt
- Kampf-HUD und Treffer-Rückmeldungen.
- Nur als Modell, noch nicht im Spiel:
  - Haupttrainer, Trainer, Ringrichter
  - Fight Night Arena mit Backstage (für Roblox zu schwer, muss vereinfacht werden)

## Für spätere Updates
- Mobile/Touch und Controller-Feinschliff (Desktop zuerst, bestätigt).
