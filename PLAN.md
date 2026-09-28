# Steal a Car – Spielplan

Status: **Entwurf – wartet auf Freigabe.** Es wird nichts gebaut, bevor der Plan freigegeben ist.

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
- Weiter hinten (Stadt 1 → 5) gibt es seltenere Autos.
- **Spawn:** Häufige Autos stehen **geparkt**. Seltene Autos **fahren herum**, und zwar nur innerhalb ihrer Stadt.
  Je seltener ein Auto ist, desto wahrscheinlicher fährt es.
- Jedes Auto hat einen Preis und ein **Einkommen $/s**.

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

## 7. Safe Zone
- **Verkaufs-Stand:** Autos gegen Geld verkaufen.
- **Upgrade-Shop:** schnelleres Starter-Auto, längeres Schutz-Tor, mehr Stellplätze.
- **Trails-Shop:** Kosmetik (Spuren hinter dem Auto/Spieler).
- **Rebirth:** alles zurücksetzen, dafür dauerhaft einen Geld-Multiplikator bekommen.

## 8. Robux
- **2x Geld** (Gamepass)
- **VIP** (Gamepass): extra Stellplätze + VIP-Tag im Chat
- **Polizei-Immunität** (Einmal-Kauf): Polizei für eine Weile aus *(Vorschlag: 60 s)*

## 9. Speichern
Geld, Autos, Upgrades, Rebirths und Trails werden gespeichert (DataStore).

## 10. Bau-Reihenfolge
Jede Phase wird erst gebaut, getestet und von dir abgenickt, bevor die nächste startet.

1. **Map-Grundgerüst:** Safe Zone, 8 Autohäuser, Straße, 5 leere Stadtflächen
2. **Städte bauen:** Paris → London → Las Vegas → Tokyo → Dubai
3. **Autos:** Modelle, Seltenheiten, Spawnen (geparkt + fahrend)
4. **Starter-Auto & Kaufen**
5. **Autohaus:** Stellplätze, Geld/s, Geld abholen
6. **Polizei-Verfolgung**
7. **Klauen & Schutz-Tor**
8. **Safe-Zone-Shops:** Verkaufen, Upgrades, Trails, Rebirth
9. **Speichern**
10. **Robux-Käufe**

## Offene Fragen (vor Phase 2 klären)
- Farben/Design des Autohauses
- Größe der Map (wie lang ist jede Stadt?)
