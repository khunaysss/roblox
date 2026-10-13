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

### Schritt 1 – Einstieg (bestätigt 2026-10-13)
- Ablauf:
  - Beim ersten Start der volle Kämpfer-Editor mit gutem Standardaussehen und klarem „Fertig“-Button.
  - Danach begrüßt der Haupttrainer den Spieler im Gym.
  - Das Tutorial wird automatisch angeboten, ist jederzeit überspringbar und später beim Trainer wiederholbar.
  - Erster Kampf gegen den vorhandenen Anfänger-Trainingsgegner (1 Runde); der Haupttrainer gibt kurze Tipps vom Käfigrand.
  - Danach sind Gym und Online frei.
- Die ersten 15 Minuten sind Orientierung, keine Wartezeit: Aufgaben enden, sobald sie erfüllt sind. Der Tutorial-Fortschritt wird gespeichert und beim erneuten Beitritt fortgesetzt.
- Visuelle Vorlagen (verbindlich für Layout und Stil, nicht für Figuren oder Hintergrund):
  - Bild 1 „Bereit für den Käfig?“: Begrüßung und Angebot (Training starten / Überspringen)
  - Bild 2: kompakte Aufgabenkarte (Lektion x/6, Taste, Fortschritt 2/3, Trainer-Tipp unten, „H · Hilfe“ unten rechts, „Tutorial überspringen“ oben rechts)
  - Bild 3 „Grundlagen geschafft“: Abschluss mit Sparring starten / Zurück ins Gym
- Gestaltung:
  - Anthrazit, weiße Schrift, Rot als Akzent, leicht abgeschrägte Ecken, einheitliche Komponenten aus `CC_UI`.
  - Keine Emojis und kein starker Glow. Echte, bedienbare UI statt Bildern.
  - Große Panels nur vor und nach Übungen, im Kampf kompakt. Kurze weiche Übergänge.
  - Roblox-Systembuttons und Kämpfer nicht verdecken. Desktop zuerst.
- Sechs Lektionen, nur mit vorhandenen Mechaniken:
  1. Bewegen, Abstand, Anvisieren
  2. Jab und Cross
  3. Blocken und Ausdauer
  4. Kick und zurück in die Deckung
  5. Takedown und Sprawl
  6. Am Boden befreien und aufstehen
- Jede Lektion zeigt Titel, Aufgabe, echte Taste, Fortschritt und einen Trainertipp. Fortschritt zählt nur echte Aktionen und Treffer, nicht bloße Tastendrücke. Fehlversuche werden freundlich erklärt; bei wiederholten Problemen gibt es Hilfe oder „Überspringen“.
- Der Übungsgegner passt sich der Lektion an: erst passiv, für Block und Sprawl mit langsam angekündigten Angriffen. In den Grundlagen gibt es keine Niederlage und keinen K.o.
- „Überspringen“ setzt Kamera, Gegner, Eingabesperren und Position sauber zurück.
- Abschluss:
  - Nur absolvierte Lektionen werden abgehakt.
  - Bei einer Niederlage im ersten Sparring gibt es trotzdem Fortschritt und einen schnellen neuen Versuch.
  - Belohnungen nur aus dem echten System. Die Erstabschluss-Belohnung gibt es nur einmal.

### Umsetzungsliste Einstieg (freigegeben 2026-10-13, Stand siehe „Bereits umgesetzt“)
| # | Aufgabe | Nutzt | Fertig, wenn |
|---|---|---|---|
| V1 | Profil um Einstiegsfortschritt erweitern (Editor fertig, Lektionen 1–6, Erstbelohnung erhalten), alte Profile kompatibel | `CC_Profile` | Neues und altes Profil laden; Fortschritt übersteht Neubeitritt |
| V2 | Haupttrainer als stehende Figur ins Gym und an den Käfigrand (Pose, keine Kampfanimationen) | `main_coach_v03.blend` | Trainer sichtbar, kollidiert sauber, Ansprechen per E |
| V3 | Übungsgegner-Modi: passiv, langsam angekündigte Schläge (Block), angekündigter Takedown (Sprawl), kein K.o. in den Grundlagen | Gegnerstufen, `CC_ForceTD` | Jede Lektion mit Gegnermodus 3× ohne Fehler getestet |
| V4 | Kampfeinstellung „1 Runde“ für das erste Sparring | `CC_Match` | Kampf endet nach 1 Runde mit Ergebnis |
| V5 | Ersten Start lenken: Editor → Begrüßung (Bild 1) | Editor, Hauptmenü | Neuer Spieler landet nacheinander dort; bekannter Spieler nicht |
| V6 | Lektionen-Logik mit Erkennung echter Aktionen (Treffer, Block, Sprawl, Befreien, Aufstehen) | Kampfskript, Treffer-Rückmeldungen | Alle 6 Lektionen erkennen Erfolg und Fehlversuch |
| V7 | Aufgabenkarte (Bild 2), Trainertipps, „H · Hilfe“, Überspringen mit sauberem Zurücksetzen | `CC_UI` | 1280×720 bis 1920×1080 ohne Überlappung; Überspringen in jeder Lektion getestet |
| V8 | Abschluss (Bild 3) → Sparring 1 Runde mit Trainertipps → Ergebnis → Gym/Online frei | V4, Ergebnisanzeige | Sieg und Niederlage durchgespielt; Erstbelohnung nur einmal |
| V9 | Gesamttest neuer Spieler (ca. 15 Min.) und Wiederholung beim Trainer | alles | Ablauf ohne Hänger und ohne Konsolenfehler |

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
- Schritt 1: entschieden (siehe oben).
- Schritte 2–6 sind noch nicht besprochen.

## Bereits umgesetzt (laut Projektstand, Studio-Tests mit 1 Spieler)
### Einstieg (2026-10-13, in Studio getestet mit Testschalter CC_TestNewPlayer, 1 Spieler, Desktop)
- **V1 Profil:** onb (editor, offered, lessons 1–6, done, firstFight) wird gespeichert; alte Profile ohne onb gelten als bekannte Spieler. Getestet: neuer Spieler und Fortsetzen nach Neubeitritt (mit vorgegebenem Stand). Echtes Speichern in den DataStore nicht getestet (Testmodus speichert nicht).
- **V2 Haupttrainer:** Export fertig (`export/Main_Coach_v01_Roblox.fbx`, Standhaltung, Vorschau `renders/coach_roblox_v01_preview.png`), Einrichtungsskript `roblox/setup_coach_v01.luau`. **Offen:** Import in Studio durch den Nutzer (Import 3D, Centimeter, Faktor 1), danach Platzierung im Gym und am Käfigrand testen. Bis dahin spricht der Trainer nur im Dialogfeld (Symbol statt Porträt).
- **V3 Gegner-Modi:** angekündigter Jab (Block), angekündigter Takedown (Sprawl), erzwungener Takedown (Lektion 6), Platz machen zum Aufstehen; im Tutorial kein K.o. (Leben min. 40) und kein Schaden durch den passiven Gegner. Getestet.
- **V4 Sparring 1 Runde:** getestet (Sieg und Niederlage), Anzeige „RUNDE 1 / 1“.
- **V5 Erster Start:** Editor mit FERTIG → Begrüßung; bekannte Spieler sehen das normale Hauptmenü. Getestet.
- **V6 Lektionen:** alle 6 mit echten Aktionen getestet (Lauf-Strecke, Umkreisen, Abstand, gelandete Jabs/Crosses, geblockte Schläge, Ausdauer verbrauchen/erholen, Kick + Deckung, Takedown, Sprawl, Befreien + Aufstehen); freundliche Fehlerhinweise (z. B. „Zu weit weg“) getestet.
- **V7 Anzeigen:** Begrüßung, Aufgabenkarte, Hilfe (H) mit „Lektion überspringen“, „Tutorial überspringen“ (setzt Kamera, Gegner, Sperren, Position zurück) getestet bei 1516×753 (UI skaliert mit der Höhe).
- **V8 Abschluss/Sparring/Ergebnis:** getestet; Belohnung = echter Trainingskampf (Sieg 30 XP, Niederlage 15 XP, +2 TP Kondition je Runde); das Tutorial selbst gibt keine Belohnung (kein Mehrfach-Abholen möglich).
- **V9 Gesamttest:** einmal komplett durchgespielt (Editor → Begrüßung → 6 Lektionen → Abschluss → Sparring → Ergebnis → frei), Wiederholen über Hauptmenü → Training → „Grundlagen wiederholen“. Ohne Konsolenfehler.
- **Gefundenes Problem (nicht vom Einstieg verursacht):** Das Modell `CC_Gym` ist im Place um (−52,5; −11,1; +9,2) Studs verschoben (Boden, Laufband), die Stationen und der Startpunkt nicht. Spieler fallen im Gym durch den Boden. Zurücksetzen auf Bodenmitte (160, 0, 0) braucht die Freigabe des Nutzers.

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
