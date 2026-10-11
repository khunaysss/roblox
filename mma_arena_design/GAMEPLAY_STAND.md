# Cage Champions – wie das Spiel jetzt abläuft (Stand 2026-10-12)

Für die Gameplay-Planung, zum Beispiel mit ChatGPT. Alles hier ist eingebaut und in Studio getestet (1 Spieler), außer es steht „nicht getestet“ dabei.

## 1. Start und Lobby (Trainings-Gym)
- Der Spieler erscheint im **Trainings-Gym**. Dort gibt es einen Käfig, Sandsäcke, einen Kraftbereich, Matten, eine Umkleide mit Spinden und Spiegel sowie einen Trainer-Tisch.
- Im Gym ist der Kämpfer im **Locker-Modus**: er steht entspannt und geht normal (Tempo 6,4). Mit Umschalttaste bzw. L3 läuft er (Tempo 15).
- Links ist das **Menü**:
  - TRAINING (Kampf gegen den Trainingsgegner)
  - GEGEN SPIELER (Warteschlange, die ersten zwei kämpfen)
  - KÄMPFER (Aussehen ändern)
  - darunter Level, XP-Balken, 4 Werte, Bilanz
- **Gespeichert** wird pro Spieler: Level, XP, Siege/Niederlagen/K.o./Submissions, 4 Werte, Aussehen.

## 2. Kämpfer-Werte und Fortschritt
| Wert | Wirkung im Kampf (pro Punkt, max. 20) | Wie man ihn steigert |
|---|---|---|
| Schlagkraft | +1,5 % Schaden | Sandsack, Bankdrücken, Kurzhanteln |
| Kondition | +2 maximale Ausdauer, +2 % Erholung | Hampelmann auf der Matte, jede gekämpfte Runde |
| Ringen | Sprawl-Fenster länger, eigene Takedowns schwerer abzuwehren | Takedowns und Sprawls im Kampf |
| Bodenkampf | +2,5 % Wirkung im Submission-Duell | Positionswechsel, Befreien, Submissions |
- 10 Trainingspunkte ergeben +1 Wert.
- XP für Level: 100 + 50 × (Level − 1) pro Level. Das Level hat noch **keine** eigene Wirkung, es zeigt nur den Fortschritt.
- XP gibt es aus Kämpfen und Training.
  - Spieler gegen Spieler: Sieg 60 (+20 bei K.o./Submission), Niederlage 25; zählt in die Bilanz.
  - Training gegen den Trainingsgegner: 30 bzw. 15 XP, zählt nicht in die Bilanz.

## 3. Training im Gym = Minispiele
An einer Station **E** drücken (Controller X). Der Kämpfer stellt sich hin, die Kamera zeigt ihn **von vorn**, dann läuft ein Minispiel:

| Station | Minispiel | Animation / Gewicht |
|---|---|---|
| Sandsack, Standsack | **Tastenfolge** aus 10 Tasten (Q E R F) in Reihenfolge, 7 Sekunden. Jede richtige Taste ist ein Schlag; falsche Taste bricht die Kombo | Kombination Jab/Cross/Haken/Uppercut, Sack schwingt |
| Hantelbank (im Rack) | **Rhythmus**: Leertaste drücken, wenn der Ring den Kreis trifft; 8 Wiederholungen alle 1,2 s | liegt auf der Bank, Langhantel mit Scheiben in den Händen |
| Kurzhanteln | **Rhythmus**: Q und E abwechselnd (linker/rechter Arm), 10 Wiederholungen alle 0,95 s | Kurzhanteln in beiden Händen |
| Matten | **Rhythmus**: schnelle Leertaste, 14 Wiederholungen alle 0,62 s | Hampelmann mit Sprung und Klatschen über dem Kopf |
- **Wertung:** „PERFEKT“ (±0,08 s), „GUT“ (±0,18 s), sonst „ZU FRÜH/ZU SPÄT/FALSCHE TASTE“.
  - Ein Treffer spielt eine Wiederholung ab, ein Fehler lässt den Kämpfer sichtbar stocken.
- **Belohnung nach Trefferquote:**
  - 90 % und mehr: 3 Trainingspunkte
  - 60 % und mehr: 2
  - 30 % und mehr: 1
  - dazu 1 XP je Treffer
- **Weitere Stationen:**
  - Trainer-Tisch: startet einen Trainingskampf
  - Trainingsplan: zeigt die eigenen Werte
  - Spiegel/Spinde: Kämpfer-Anpassung
- Steuerung: Controller X/Y/B/A statt Q/E/R/F; Touch durch Antippen der angezeigten Taste (nicht getestet).

## 4. Kämpfer-Anpassung
- Frisur (Tolle, Buzzcut, Seitenscheitel, Locken), Bart (keiner, kurz, Vollbart), Gesicht (fokussiert, neutral, freundlich), Hautton (4), Haarfarbe (6).
- Die rote Ecke trägt rote, die blaue Ecke blaue Shorts.

## 5. Der Kampf
- **Ablauf:**
  - Training gegen den Trainingsgegner oder Spieler gegen Spieler in der Arena (Käfig in einer Halle). Es gibt eine Arena und einen Kampf gleichzeitig; die anderen warten im Gym.
  - **3 Runden × 2 Minuten**, 10 s Pause mit etwas Erholung.
  - **Sieg** durch K.o., Submission oder Punkte (verursachter Schaden). Wer das Spiel verlässt, verliert durch Aufgabe.
  - Danach geht es zurück ins Gym.
- **Kamera:** Kampfkamera mit beiden Kämpfern im Bild. Der Kämpfer ist automatisch auf den Gegner ausgerichtet; links und rechts umkreisen ihn.
- **Steh-Kampf:**
  - Jab (Linksklick), Cross (Rechtsklick)
  - mit Umschalttaste gehen beide zum Körper
  - Haken (Q), Uppercut (R)
  - Low Kick (C), Body Kick (X), High Kick (V), Front Kick (Z)
  - Block (F halten)
  - Treffer werden über die sichtbare Faust bzw. das Schienbein geprüft.
  - Kombos werden gepuffert.
  - Trefferreaktionen hängen vom Schlag ab: gerade, Haken, Uppercut, Körper, Bein. Bei wenig Leben folgt Taumeln, danach K.o. nach vorne oder hinten.
- **Ausdauer:** Jede Aktion kostet Ausdauer. Unter 25 Ausdauer gibt es weniger Schaden und langsamere Schläge.
- **Takedown** (E): Doppelbein. Der Gegner kann im richtigen Moment mit F **sprawlen** und abwehren.
- **Bodenkampf:**
  - Positionen: Guard → Half Guard → Side Control → Mount → Rücken.
  - **Oben:** E = Position verbessern, Linksklick = Schlag (Guard, Mount), Q = Submission (Mount: Armbar, Rücken: Rear Naked Choke).
  - **Unten:** Leertaste = befreien (eine Position zurück; aus der Guard aufstehen).
  - **Konter:** F direkt nach dem gegnerischen Positionswechsel lässt den Wechsel rückwärts laufen.
  - **Submission-Duell:** Angreifer hämmert Q, Verteidiger die Leertaste; der Balken entscheidet. Wenig Leben hilft dem Angreifer.
- **Trainingsgegner:** läuft, kreist, steppt mit Kombinationen hinein, blockt, macht Takedowns und kämpft am Boden inklusive Submissions.
- **Steuerung Controller:**
  - X Jab, Y Cross, B Haken, R1 Uppercut, R2 Low Kick
  - Steuerkreuz ← Body Kick, → High Kick, ↓ Front Kick
  - L2 Block, L1 Takedown, A befreien, R3 Ziel
  - Getestet per Studio-Simulation; B nicht simulierbar.

## 6. Was noch fehlt oder nur vorbereitet ist (für die Planung)
- **Noch nicht getestet:** zwei echte Spieler gegeneinander, Touch.
- **Upload:** Neue Animationen (Locker-Modus, Gym-Übungen) müssen noch hochgeladen werden, sonst laufen sie nur im Einzeltest in Studio.
- **Spielsystem:**
  - kein Clinch und kein Käfig-Ringen
  - kein Ausweichen oder Kopfbewegung, keine Schadenszonen-Anzeige
  - am Boden nur aus der Guard aufstehen
  - Level ohne Belohnung
  - keine Ränge, keine Gegner-Auswahl, keine Kampfstile
- **Maps:** Fight Night Arena mit Backstage/Walkout noch nicht im Spiel, sie ist zu schwer für Roblox und muss vereinfacht werden.
- **Figuren:** Trainer, Haupttrainer und Ringrichter gibt es als Modelle, aber noch nicht im Spiel.
- **Optik:**
  - Handschuhe überschneiden sich am Boden bis ~14 cm
  - Bank- und Hantel-Animationen sind einfach (kein Hantelwechsel, Gewicht fest in der Hand)
- **Ideen zum Ausbauen** (Vorschläge, nicht entschieden):
  - Level schaltet Kampfstile, Kombos oder Kosmetik frei
  - Tagesziele im Gym, Energie oder Müdigkeit beim Training
  - Sparring-Partner, Rangliste, Turniere bzw. „Fight Night“-Events mit Walkout
