# Aufgaben für ChatGPT / Astra

Stand 2026-10-19. Gedacht für Planung, Texte und Entwürfe. ChatGPT/Astra haben keinen Repo-Zugriff und keinen Studio-Zugriff: Alles, was sie liefern, prüft und baut Claude.

Regeln für alle Aufgaben:
- Keine echten Verbandsmarken, Logos oder Namen (kein UFC, BJJ-Verband, Judo-Verband, keine echten Personen).
- Eigenes Design: Rot und Schwarz als Grundfarben, Gold für Akzente.
- Englische Texte im Spiel, Erklärungen an den Nutzer auf Deutsch.
- Antwort bitte im angegebenen Format, damit Claude es direkt übernehmen kann.

---

## 1. Gürtel-Design (Dojo, Muay Thai, Ringen, BJJ, Titel)

Ziel: Jede Stufe jedes Stils als Daten, die Claude in Blender und Roblox umsetzt.

Prompt:

```
Du bist Game-Designer und Ausstatter für ein Roblox-MMA-Spiel namens "Cage Champions".
Entwirf ein Gürtelsystem mit Kampfsport-Stilen. Die Gürtel sind reine Kosmetik (zeigen den Stil, geben keine Werte) und werden durch Spielen freigeschaltet.

WICHTIG:
- Keine echten Verbandsmarken, Logos oder Namen. Nur allgemeine Gürtelfarben und Formen.
- Eigenes Design: Rot und Schwarz als Grundfarben, Gold für Akzente.
- Alles muss in Blender als einfaches Low-Poly-Mesh umsetzbar sein (keine Fotorealistik).

STILE (je 3 Stufen, aufsteigend):
1. Titel (Karriere): große Mittelplatte mit Gravur, Ledergurt. Stufen: AMATEUR, PRO, LIGHTWEIGHT CHAMPION.
2. Dojo (Striking): Farbstufen im Stil klassischer Kampfsport-Gürtel. Stufen: Weiß, Gelb/Orange, Grün.
3. Muay Thai: Stoffgürtel mit Wickel-Optik. Stufen: Rot, Schwarz mit Gold-Streifen, Gold.
4. Ringen: breiter, schlichter Gürtel, Metallschnalle. Stufen: Grau, Blau, Schwarz.
5. BJJ / Grappling: dunkler Gürtel mit Streifen-Enden. Stufen: Blau, Violett, Schwarz mit Rot-Streifen.

Für JEDEN Gürtel und JEDE Stufe liefere:
- Name (englisch, max. 3 Wörter)
- Farbe: Hauptfarbe und Akzentfarbe als Hex-Code (#RRGGBB)
- Form: Breite in cm, Dicke in mm, Knoten oder Schnalle, Platte in der Mitte (Größe in cm, Form)
- Textur: glatt / Stoff / Leder / Metall, Glanz (matt / glänzend), Abnutzung ja/nein
- Beschriftung: genauer Text, Position, Schriftstil, Größe, oder "keine Beschriftung"
- Freischaltung: genaue Bedingung (Karriere-Siege, Kampf-Typ, Prüfung)
- Beschreibung in 2 Sätzen

Antwort: erst Tabelle, dann JSON-Liste mit den Feldern style, stage, name, mainColor, accentColor, widthCm, thicknessMm, closure, plate, texture, gloss, wear, text, unlock, description.
Antworte auf Deutsch, Namen und Texte auf Englisch.
```

## 2. Kampf-Texte (Englisch, kurz)

Ziel: Texte für Ringrichter, Ecke, Walkout und Sieg.

Prompt:

```
Du schreibst Kommentar- und Ansage-Texte für ein Roblox-MMA-Spiel namens "Cage Champions". Stil: direkt, laut, wie eine Live-Übertragung, aber ohne echte Personen oder Marken.

Liefere auf Englisch, je Kategorie 6 Varianten, maximal 8 Wörter pro Zeile:
1. Kampfstart (Ringrichter ruft "Fight!")
2. Knockdown und K.o.
3. Submission (Aufgabe durch Würgegriff oder Hebel)
4. Arztabbruch (Kämpfer ist zu stark verletzt)
5. Sieg nach Punkten
6. Rundenpause: Trainer in der Ecke (ruhig, motivierend)
7. Walkout: Ansage des Kämpfers
8. Sieger-Ehrung nach dem Kampf

Keine Gewaltverherrlichung über das Sportliche hinaus, keine Beleidigungen, keine Slurs.
Gib die Texte als Liste mit Kategorie-Nummer.
```

## 3. Ringarzt-Konzept

Ziel: Ablauf und Regel für Arztabbruch als Vorschlag. Claude setzt es danach in Roblox um.

Prompt:

```
Entwirf für ein Roblox-MMA-Spiel ("Cage Champions") ein einfaches Konzept für einen Ringarzt, der bei zu starker Verletzung den Kampf stoppt.

Liefere:
1. Auslöser: welche Werte oder Ereignisse (z. B. Gesundheit unter X %, mehrere harte Treffer hintereinander, Knockdown-Anzahl). Mit konkreten Zahlen für 3 Schwierigkeiten: Anfänger, Fortgeschritten, Champion.
2. Ablauf in Schritten: Ringrichter stoppt, Arzt kommt in den Käfig, Entscheidung, Kampfende oder Weiterkampf.
3. Was der Spieler sieht (Text, Zeit, Kamera).
4. Was passiert bei Weiterkampf (Erholung, Malus?).
5. Drei Balance-Risiken, die man im Test prüfen muss.

Kurz halten, maximal eine Seite. Keine medizinischen Details, nur Spielregeln.
```

## 4. Walkout und Siegerauftritt (Konzept)

Prompt:

```
Entwirf für ein Roblox-MMA-Spiel ("Cage Champions") den Ablauf von Walkout und Siegerauftritt:

1. Walkout beider Kämpfer: Reihenfolge, Musik-Stimmung (Beschreibung, keine echten Songs), Kamera-Schnitte, Namens-Einblendung (Text, Position).
2. Siegerauftritt: Arm-Hochhalten durch den Ringrichter, Kamera, Jubel, Text.
3. Verlierer: wie er den Käfig verlässt (kurz).

Liefere: Ablauf als nummerierte Liste mit Sekunden-Angaben, dazu 3 Vorschläge für Musik-Stimmung (nur Beschreibung: Tempo, Instrumente).
Keine echten Songs, keine Marken.
```

---

## Was Claude macht (nicht an ChatGPT geben)

- Blender-Modelle und Animationen
- Roblox-Skripte, Einbau und Tests in Studio
- Commits und Doku

## Was du machst

- Upload der Animationen (`upload_starten.ps1`)
- Import der Modelle in Studio (Ringrichter: `export/Referee_Rigged_v01.fbx`, dann `_G.CC_SetupReferee()`)
- Entscheidungen (Stufen, Namen, Balance)
