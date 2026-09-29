# Steal a Car – Spielplan

Status: **Freigegeben.** Gebaut wird Phase für Phase.

Werte mit *(Vorschlag)* hat Claude festgelegt und kann man noch ändern.

## 1. Grundidee
Aufbau wie **Steal a Egg**, aber mit **Autos**. Man fährt in berühmte Städte, kauft dort Autos,
flieht vor der Polizei zurück ins eigene Autohaus. Autos im Autohaus verdienen Geld pro Sekunde.
Andere Spieler können einem Autos klauen.

## 2. Map-Aufbau
- **8 Spieler** pro Server → **8 Autohäuser**, je **4 links und 4 rechts** vom Hauptweg.
- **Safe Zone** in der Mitte beim Spawn (keine Polizei, kein Klauen).
- Vom Basis-Bereich führt eine lange Straße nach hinten durch **5 Stadt-Zonen**:

| # | Stadt | Wahrzeichen & Deko | Autos dort |
|---|---|---|---|
| 1 | **Paris** | Eiffelturm, Cafés, Laternen, Kopfsteinpflaster | billigste |
| 2 | **London** | Big Ben, rote Doppeldeckerbusse, Telefonzellen | |
| 3 | **Las Vegas** | Casinos, Neon-Schilder, Glitzer | |
| 4 | **Tokyo** | Neon, Kirschblüten, Tokyo Tower | |
| 5 | **Dubai** | Wüste, Burj Khalifa, Gold/Luxus | seltenste |

- Stil: bunt und blockig wie Steal a Egg, **alles von Claude aus Blöcken gebaut** (keine Toolbox-Modelle).
- Zwischen den Städten gibt es sichtbare Übergänge (Torbogen mit Stadtnamen).

## 3. Autos
- Stil: **echte Auto-Formen mit lustiger Deko** passend zur Stadt (z. B. Baguette auf dem Dach), **ohne echte Markennamen**.
- **7 Seltenheiten:** Common, Uncommon, Rare, Epic, Legendary, Mythic, Secret.
- **8 Autos pro Stadt, also 40 Autos insgesamt.** Die Vorlagen sind die „Collection“-Bilder des Nutzers.
- **Wichtig:** Der Nutzer hat die Autos eventuell schon mit einer anderen KI in Studio gebaut.
  **Vor dem Bauen in Studio nachschauen**, ob es die Modelle schon gibt, und vorhandene Modelle verwenden.
- Weiter hinten (Stadt 1 → 5) gibt es seltenere Autos.
- **Spawn:** Häufige Autos stehen **geparkt**. Seltene Autos **fahren herum**, und zwar nur innerhalb ihrer Stadt.
  Je seltener ein Auto ist, desto wahrscheinlicher fährt es.
- Jedes Auto hat einen Preis und ein **Einkommen $/s**.

### Auto-Liste

| # | Seltenheit | Paris | London | Las Vegas | Tokyo | Dubai |
|---|---|---|---|---|---|---|
| 1 | Common | Baguette Buggy | Teacup Taxi | Dice Roller | Kei Box | Dune Hopper |
| 2 | Common | Petit Coupe | Foggy Hatch | Slot Machine Sedan | Ramen Roller | Camel Cruiser |
| 3 | Uncommon | Croissant Cruiser | Crumpet Mini | Chip Stack Coupe | Neko Mini | Oasis Wagon |
| 4 | Rare | Beret Racer | Double Decker Dash | Neon Nightrider | Drift Kitsune | Mirage GT |
| 5 | Epic | Riviera GT | Thames Tourer | High Roller | Shibuya Streetrunner | Falcon Fury |
| 6 | Legendary | Eiffel Express | Royal Guard Rover | Rockstar Cruiser | Sushi Drifter | Golden Sandstorm |
| 7 | Mythic | Le Mime Mobile | Clockwork Coupe | Jackpot Jet | Mecha Ronin | Sultan Supreme |
| 8 | Secret | Lumiere Phantom | Crown Jewel GT | The Golden Ace | Sakura Dragon | Diamond Oasis |

### Geld *(Vorschlag)*
- **Einkommen $/s** = Grundwert der Seltenheit × Stadt-Faktor
  - Grundwerte: Common 5 · Uncommon 15 · Rare 50 · Epic 150 · Legendary 500 · Mythic 2.000 · Secret 10.000
  - Stadt-Faktor: Paris ×1 · London ×5 · Las Vegas ×25 · Tokyo ×125 · Dubai ×625
- **Preis** = Einkommen × 60 (also nach 1 Minute wieder verdient)
- Beispiele: Baguette Buggy 5 $/s für 300 $ · Diamond Oasis 6,25 Mio $/s für 375 Mio $

## 4. Auto holen
1. Man fährt mit seinem **kostenlosen Starter-Auto** in eine Stadt.
2. Man **kauft** ein Auto (Knopf/Prompt am Auto).
3. Man **fährt es selbst** zurück ins eigene Autohaus.
4. Beim Kauf beginnt eine **Polizeiverfolgung**.

## 5. Polizei
- Polizeiautos fahren herum und verfolgen dich nach einem Kauf.
- **Stärke je nach Seltenheit:** Common = 1 langsames Polizeiauto … Secret = mehrere schnelle *(Vorschlag: 1 bis 5 Autos)*.
- **Erwischt** (Polizeiauto berührt dich) → **das Auto ist weg**, das Geld auch.
- **Sicher** ist man erst **im eigenen Autohaus**. Dann ist die Jagd vorbei.

## 6. Autohaus (Spieler-Base)
- Glas-Showroom, in dem die Autos ausgestellt sind.
- **Start: 5 Stellplätze**, mit Geld ausbaubar **bis 20**.
- Autos verdienen automatisch Geld/s. Das Geld muss man abholen *(Vorschlag: einfach über einen Geld-Knopf laufen)*.
- **Klauen:** Andere Spieler können ein Auto aus deinem Autohaus nehmen und damit in ihr eigenes fahren.
- **Schutz-Tor:** ein Laser-Tor, das man per Knopf schließt *(Vorschlag: 60 s zu, danach 60 s Abklingzeit)*.

## 6b. Laufband (Speed farmen)
- **Jedes Autohaus hat 1 Laufband**, und zwar in einem **Anbau hinten am Autohaus** *(Vorschlag)*. Man sieht es von der Straße aus durch das Glas.
- Man stellt eines seiner Autos drauf *(Vorschlag: am Stellplatz „Aufs Laufband“ drücken)*. Ist kein Auto drauf, passiert nichts.
- **Speed bekommt man nur auf dem Laufband.** Es farmt automatisch, auch AFK: **Speed + Geld**. Das Auto auf dem Laufband bringt mehr als ein geparktes *(Vorschlag: ×2 Geld)*.
- **Seltenere Autos farmen mehr Speed** *(Vorschlag: Speed/s = Grundwert der Seltenheit ÷ 5, also Common 1/s … Secret 2.000/s, × Stadt-Faktor)*.
- **Animation wie auf der Autobahn:** Die Räder drehen sich, das Band läuft, Fahrbahnstreifen, Leitplanken und Laternen rauschen vorbei,
  dazu Wind-/Speed-Linien und ein Tacho über dem Laufband, der den Speed anzeigt.
- **Offline:** Das Laufband farmt weiter, aber nur sehr wenig *(Vorschlag: 10 %, höchstens 8 Stunden lang)*.
- **Upgrade-Shop:** Das Laufband lässt sich aufrüsten (Stufe 1–10, jede Stufe +25 % Speed) *(Vorschlag)*.
- **Rebirth:** Speed geht auf 0, dafür farmt das Laufband danach schneller (Rebirth-Multiplikator).
- **Wofür Speed gut ist** *(Vorschlag)*:
  - **Alle deine Autos fahren etwas schneller**, auch das Starter-Auto, aber **nur ein bisschen** (z. B. höchstens +50 %).
    Alles bleibt **ausbalanciert**: Die Polizei wird mitgestärkt, damit sie nie zu leicht ist.
  - **Städte freischalten:** Am Torbogen braucht man einen Mindest-Speed *(z. B. London 100, Las Vegas 1.000, Tokyo 10.000, Dubai 100.000)*.

## 7. Safe Zone
- **Verkaufs-Stand:** Autos gegen Geld verkaufen.
- **Upgrade-Shop:** schnelleres Starter-Auto, längeres Schutz-Tor, mehr Stellplätze, Laufband-Stufe.
- **Trails-Shop:** Kosmetik (Spuren hinter dem Auto/Spieler).
- **Rebirth:** alles zurücksetzen, dafür dauerhaft einen Geld-Multiplikator bekommen.

## 8. Robux
- **2x Geld** (Gamepass)
- **VIP** (Gamepass): extra Stellplätze + VIP-Tag im Chat
- **Polizei-Immunität** (Einmal-Kauf): Polizei für eine Weile aus *(Vorschlag: 60 s)*

## 9. Speichern
Geld, Speed, Autos, Upgrades, Rebirths und Trails werden gespeichert, dazu die Offline-Zeit fürs Laufband (DataStore).

## 10. Bau-Reihenfolge
Jede Phase wird erst gebaut, getestet und von dir abgenickt, bevor die nächste startet.

1. **Map-Grundgerüst:** Safe Zone, 8 Autohäuser, Straße, 5 leere Stadtflächen
2. **Städte bauen:** Paris → London → Las Vegas → Tokyo → Dubai
2b. **Look & Lighting** wie Steal a Egg / Steal a Brainrot (siehe Abschnitt 11)
3. **Autos:** Modelle, Seltenheiten, Spawnen (geparkt + fahrend)
4. **Starter-Auto & Kaufen**
5. **Autohaus:** Stellplätze, Geld/s, Geld abholen, **Laufband mit Autobahn-Animation**
6. **Polizei-Verfolgung**
6b. **Gameplay-UI** (siehe Abschnitt 12), Vorlage: `docs/vorlagen/gameplay-ui.webp`
7. **Klauen & Schutz-Tor**
8. **Safe-Zone-Shops:** Verkaufen, Upgrades, Trails, Rebirth
9. **Speichern**
10. **Robux-Käufe**

## 11. Look & Lighting (Phase 2b)
Ziel: hell, bunt, sonnig und „poppig“ wie **Steal a Egg** und **Steal a Brainrot**.
- **Lighting:** Technology `Future`, helle Mittagssonne (ClockTime ~14), weiche Schatten, kräftiges Ambient,
  damit nichts dunkel wirkt.
- **Farben:** `ColorCorrection` mit mehr Sättigung (~0.2) und etwas Kontrast, dazu leichtes `Bloom`, damit Neon und Gold leuchten.
- **Himmel:** knallblauer Himmel mit Cartoon-Wolken (`Clouds`), leichte `Atmosphere` für Tiefe, `SunRays`.
- **Umgebung:** Wasser/Meer rund um die Map wie auf dem Steal-a-Brainrot-Bild, grüner Karo-Rasen, Bäume und Büsche am Rand.
- **Blockige Form wie Steal a Brainrot:** alles aus einfachen, klaren Blöcken (kein Detail-Kleinkram),
  **Karo-Boden aus zwei Grüntönen** (große quadratische Kacheln abwechselnd hell/dunkel), Glaswände mit
  **leuchtenden Neon-Kanten** (blau) an den Rändern, rote Neon-Laserstreifen am Tor, Gebäude und Bäume als klobige Voxel-Formen.
- **Materialien:** überwiegend `SmoothPlastic` mit satten Farben, Neon für Akzente (Schilder, Stellplätze, Laser-Tor).
- **Städte** behalten ihre Stimmung, auch bei Tageslicht: Vegas und Tokyo mit vielen Neon-Schildern, Dubai mit Gold.
- Vorher und nachher Screenshots zeigen, dann auf das OK warten.

## 12. Gameplay-UI (Phase 6b)
Vorlage: **`docs/vorlagen/gameplay-ui.webp`**. Stil: dicke, runde Cartoon-Schrift (FredokaOne) mit schwarzer Kontur,
abgerundete Kästen mit dunklem, halbtransparentem Hintergrund und kräftigen Farben.
- **Links:** Geld-Anzeige (grün, Geldschein-Icon, z. B. „$8.4M“), darunter die Speed-Anzeige (Blitz-Icon, „Speed: 12,800“).
  Zahlen kurz schreiben (K, M, B, T).
- **Oben Mitte (nur während einer Polizeijagd):** Banner „WANTED! Get back to your dealership!“ mit blinkenden
  Blaulichtern und 1–5 Polizei-Sternen, je nach Seltenheit bzw. Anzahl der Polizeiautos.
- **Pfeil zum Autohaus:** gelber Pfeil mit „Your Dealership: 240m“ (während der Jagd).
- **Unten Mitte (wenn man im Auto sitzt):** Auto-Karte mit Bild/Icon, Name, Seltenheits-Tag in der Seltenheitsfarbe
  und Einkommen („+$50K/s“).
- **Unten rechts (im Auto):** runder Tacho mit km/h.
- **Beim Fahren:** Speed-Linien am Bildschirmrand, je schneller, desto mehr.
- Die Shop-Knöpfe (links) und der Knopf fürs Schutz-Tor (rechts) kommen in Phase 7/8 im selben Stil dazu.

## Offene Fragen (vor Phase 2 klären)
- Farben/Design des Autohauses
- Größe der Map (wie lang ist jede Stadt?)
