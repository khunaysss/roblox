# UI-Überarbeitung Schritt 2 – Hauptmenü verbessert, Charakter-Editor, Gym und Training

Stand 2026-10-12. Getestet in Studio (1 Spieler, PC, Maus und Tastatur). Grundlage: `UI_DESIGN_V01.md` (Schritt 1).

## Hauptmenü (`roblox/CC_MainMenu.client.luau`)
- **Fight-Night-Licht** (nur lokal, solange das Menü offen ist):
  - dunkle Halle, blaues Licht an den Tribünen, heller Käfig
  - leichte Farbkorrektur, Unschärfe deutlich schwächer
- **Kämpfer** um 28° zur Kamera gedreht.
  - Deckung leicht gesenkt, damit das Gesicht frei ist (Oberarm-Bones der Menü-Kopie werden nach der Animation um 22° gedreht; nur lokal).
- **Ruhigere Flächen:** kaum noch Durchsicht, größere Schrift (Nebentexte 16–17 statt 14).
- **Hover und Controller-Fokus:** roter Rahmen plus roter Balken; das Roblox-Auswahlbild ist ersetzt. Ausgewählt = rot gefüllt.
- **Neue Icons:** hair, beard, face, skin, shorts (selbst gezeichnet in `CC_UI`).

## Charakter-Editor (Menü: MEIN KÄMPFER, Spiegel oder Spind im Gym)
- **Links Kategorien:**
  - wählbar: Haare, Bart, Gesicht, Hautfarbe
  - mit Schloss gesperrt, weil noch nicht vorhanden: Tattoos, Shorts (Farbe richtet sich nach der Ecke), Handschuhe
- **Mitte Vorschaukarten:** Kopfbild des eigenen Kämpfers mit der jeweiligen Variante (ViewportFrame).
  - Zustände: ausgewählt (rot, Haken), Hover/Fokus (Rahmen), gesperrt (Schloss).
- **Farbfelder:** Haarfarbe (6) bei Haaren und Bart. Der Bart nutzt die Haarfarbe; das steht dabei.
- **Rechts große Vorschau** des eigenen Kämpfers in der Arena. Drehen mit Maus ziehen, Pfeilknöpfen, Q/E, LB/RB oder dem rechten Stick.
- **Vorschau bis zum Speichern:**
  - Änderungen wirken zuerst nur lokal (`ReplicatedStorage.CC_LookShared` + Vorlagen-Kopie `CC_CustomShared`).
  - SPEICHERN schickt das Aussehen an den Server, und das Profil speichert sofort (höchstens alle 7 s).
  - Die Anzeige zeigt „Gespeichert“, „Speichern fehlgeschlagen“ oder „Nur für diese Sitzung“.
- **ZURÜCKSETZEN** stellt den gespeicherten Stand wieder her.
- **Verlassen mit ungespeicherten Änderungen** öffnet die Abfrage „Speichern / Verwerfen“.

## Behobener Fehler
- **Gesicht fehlte bei Spielern ohne Bart:** Lua-Liste mit Lücke, `ipairs` brach ab. Behoben in `CC_LookShared.apply`, das Server und Vorschau gemeinsam nutzen.

## Gym (`roblox/CC_GymHUD.client.luau`, StarterGui.CC_GymHUD)
- **Profil oben links:** Level, XP, 4 Werte, je 10 TP-Segmente.
- **„Nächste Aufgabe“ oben rechts:** aus den echten Werten (schwächerer Gym-Wert, passende Station, fehlende TP).
- **Stations-Hinweise:** eigene Darstellung der ProximityPrompts (Style Custom, lokal).
  - Inhalt: Taste je Gerät, Aktion, Station und was trainiert wird.
  - Touch: Antippen des Hinweises.
- **Trainingsplan-Station** öffnet ein Fenster mit Werten und Trainingsorten (statt Textmeldung).
- **Meldungen** (Hinweise, Level up, Wert steigt) oben mittig im neuen Stil. Die alten HUD-Meldungen sind aus.
- **Alte Menüleiste** `CC_MenuGui` aus StarterGui entfernt; als `ServerStorage.CC_Old_MenuGui` aufbewahrt. `roblox/CC_Menu.client.luau` wird nicht mehr benutzt.

## Training (`roblox/CC_Minigame.client.luau`, Server `CC_GymTraining`)
- **Aufgabenkarte:** Name, trainierter Wert, Anleitung mit Tastensymbolen je Gerät, Fortschritt.
- **Ablauf:** Countdown „3 2 1 LOS!“, große Rückmeldung (PERFEKT / GUT / ZU FRÜH / ZU SPÄT / FALSCHE TASTE / VERPASST).
- **Ergebnis:**
  - Bewertung, Treffer, Anzahl perfekt.
  - Echte Belohnung vom Server: `CC_TrainResult` mit TP und XP, dieselbe Vergabe wie vorher.
  - Fortschritt des Werts.
  - Knöpfe NOCHMAL (`CC_Train "again"`) und WEITER.
  - Schließt sich nach 12 s oder wenn man losläuft.
- **Spielmechanik unverändert** (Takte, Fenster, Belohnungsstufen).

## Geprüft (Studio, PC)
- **Hauptmenü:** Licht, Kämpfer mit freiem Gesicht, breites und schmales Fenster.
- **Editor:**
  - Haare/Bart/Hautfarbe gewählt, Vorschau ändert sich sofort.
  - Drehen mit E.
  - Speichern zweimal hintereinander: DataStore-Wert geprüft, Status „Gespeichert“.
  - Zurück-Abfrage erscheint.
  - Profil danach wieder auf den Ausgangsstand gebracht: Tolle, kein Bart, XP 15.
- **Gym und Training:**
  - Gym-Anzeigen mit echten Werten.
  - Sandsack-Minispiel (Karte, Tasten, Rückmeldung) und Ergebnis mit +2 TP / +8 XP.
  - Curls-Karte mit Q/E-Anleitung.
- **Konsole:** keine Fehler.

## Nicht getestet / offen
- **Stations-Hinweis:** im Spiel erzeugt, Inhalt geprüft; Studio-Bildschirmfotos zeigen aber keine BillboardGuis. Bitte im eigenen Test ansehen.
- **Controller und Touch:** nur eingebaut, nicht getestet.
- **NOCHMAL-Knopf** nicht einzeln getestet.
- Die Kopfbilder der Frisuren Tolle, Buzzcut und Seitenscheitel sind klein und sehen ähnlich aus.
- In schmalen Fenstern liegt die große Editor-Vorschau teils unter den Drehknöpfen.
- **Weiter offen:** Schritte 3–5 (Suche und Vorstellung, Kampf-HUD und Ergebnis, Tutorial, Einstellungen, Gesamttest).
