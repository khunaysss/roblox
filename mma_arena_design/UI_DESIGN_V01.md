# UI-Überarbeitung v01 – Designsystem und Hauptmenü (Schritt 1 von 5)

Stand 2026-10-12. Getestet in Studio (1 Spieler, PC, Maus und Tastatur).

## Designsystem `roblox/CC_UI.module.luau` (ReplicatedStorage.CC_UI)
- **Farben:**
  - Hintergrund: dunkles Anthrazit (bg0–bg3)
  - Schrift: weiß, Nebentext grau
  - Rot = Auswahl und Hauptaktion; Blau = Arenalicht und Werte; Gold = Level und XP
- **Schrift:** Montserrat (Titel Heavy Italic, Knöpfe Bold, Text Medium).
- **Formen:** Flächen mit abgeschrägten Ecken (oben links, unten rechts).
- **Icons:** selbst gezeichnet, im Modul als Vektorformen definiert (`ICONS`), mit einheitlicher Strichstärke.
  - Sie werden zur Laufzeit per EditableImage gerastert: keine Uploads, keine Toolbox, keine Emojis.
  - Vorhanden: trophy, globe, dumbbell, fighter, gear, menu, back, next, check, close, lock, rotate, play, search, user2, glove, star, clock, warn.
- **Bausteine:** `panel`, `button` (Stile nav/primary/secondary/danger/ghost), `label`, `bar`, `tag`, `key`, `hints`, `icon`, `autoscale`, `focus`, `device`.
  - Zustände über die Attribute `Selected` und `Disabled`; dazu Hover- und Controller-Fokus mit Rahmen.
- **Ersatz ohne EditableImage:** runde Ecken statt Abschrägung, Knöpfe ohne Icon (der Text bleibt).
- **Skalierung:** virtuelle Höhe 760, Faktor 0,5–1,6.

## Ladebildschirm und Hauptmenü `roblox/CC_MainMenu.client.luau` (StarterGui.CC_MainMenuGui.MainMenu)
- **Ladebildschirm:** Logo und Balken; wartet auf Spielwelt, Kämpfer, Profil und Arena.
- **Hauptmenü:**
  - Hintergrund: die Arena (Blick vom Einlaufsteg), Tiefenunschärfe.
  - Rechts: lokale Kopie des eigenen Kämpfers in Kampfhaltung (Fighter_Idle_v08, hochgeladene ID).
- **Menüpunkte:**
  - **KARRIERE:** Level, XP, 4 Werte, Bilanz, „INS GYM“. Eine echte Karriere gibt es noch nicht, der Text sagt das.
  - **ONLINE:** Warteschlange (Suche starten/abbrechen, Status). „Gewertet“ ist als nicht verfügbar markiert.
  - **TRAINING:** Trainingskampf oder Gym-Training.
  - **MEIN KÄMPFER:** vorerst das bisherige Anpassungsfenster; die Vorschau übernimmt Änderungen. Wird in Schritt 2 ersetzt.
  - **EINSTELLUNGEN:** als „BALD“ gesperrt (Schritt 5).
- **Während das Menü offen ist** (lokales Attribut `CC_UIBlock`): keine Kampf-Eingaben, kein Laufen oder Springen, HUD aus, Gym-Interaktionen aus. Ein Kampf oder ein Minispiel schließt das Menü.
- **Zurück:** Rücktaste bzw. Controller B. ESC bleibt das Roblox-Systemmenü.
- **Im Gym:** Knopf „MENÜ“ oben links, Taste M bzw. Controller Select.
- **Angepasste Skripte:**
  - `CC_Input`: Sperre bei `CC_UIBlock`
  - `CC_Camera`: lässt die Menükamera in Ruhe
  - `CC_HUD`: kein Lobby-Text mehr
  - `CC_Menu`: alte Leiste ausgeblendet, Anpassungsfenster bleibt
  - `CC_CharacterAnimations`: Idle-IDs als Attribute an ReplicatedStorage

## Geprüft (Studio, PC)
- Laden → Menü mit Arena und Kämpfer
- Online: Suche starten, Status „1 von 2“, Abbrechen
- Zurück per Rücktaste
- Training → Trainingskampf: das Menü schließt, der Kampf läuft
- Mein Kämpfer: Frisur geändert, Vorschau aktualisiert, zurückgesetzt
- Karriere → INS GYM: Laufen geht wieder; M öffnet das Menü
- Keine Fehler in der Konsole

## Nicht getestet / fehlt noch
- **Controller-Fokus und Touch:** nur eingebaut, nicht getestet.
- **Touch-Kampfknöpfe** (ContextActionService) bleiben im Menü sichtbar; Lösung kommt mit dem neuen Kampf-HUD (Schritt 4).
- **Fehlende Systeme:** Einstellungen, Tutorial, echte Karriere und Rangliste gibt es nicht.
- **Nächste Schritte:** 2 = Charakter-Editor, Gym-UI und Training; 3 = Online-Suche und Kämpfer-Vorstellung; 4 = Kampf-HUD und Ergebnis; 5 = Tutorial, Einstellungen und Gesamttest.
