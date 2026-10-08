# Fighter-Anpassung v04 – was vorbereitet ist

Datei: `Fighter_Customization_v04.blend` (Basis: `Fighter_Design_v03.blend`, unverändert). Skript: `build_fighter_customization_v04.py`.
Übersicht: `renders/fighter_customization_v04_overview.png`, Einzelbilder: `renders/custom_v04/`.

## Tatsächlich austauschbar vorbereitet (in Blender)
| Bereich | Varianten (Collections) | Befestigung | Material |
|---|---|---|---|
| Frisur | `Hair_QuiffV03`, `Hair_Buzzcut`, `Hair_SidePart`, `Hair_ShortCurls` | `Attach_Hair` | `FC4_Hair_Color` (gemeinsam, eine Farbe für alle Frisuren + Augenbrauen) |
| Bart | `Beard_None`, `Beard_Short`, `Beard_Full` | `Attach_Beard` | `FC4_Beard_Color` (unabhängig von der Haarfarbe) |
| Gesicht | `Face_Neutral`, `Face_Focused`, `Face_Friendly` (je Augen, Lichtpunkte, Brauen, Mund als eigene Objekte) | `Attach_Face` | Brauen = Haarfarbe, Augen/Mund = `FD3_Face_Features` |
| Hautfarbe | hell / mittel / dunkel | – | ein Material `FC4_Skin_Shared` am ganzen Körper; Ton nur über Node `Skin_Tone` |
| Tattoo | Testmotiv (eigenes Achteck + Stern) auf linkem Oberarm | UV-Map `TattooUV` nur auf `Fighter_UpperArm_L` | Bild `FC4_Tattoo_Test` (512², eingebettet), Stärke über Node `Tattoo_Strength` |

- Alle drei Befestigungspunkte sind Empties am Kopf-Ursprung (Kind von `Fighter_Head`, Identitäts-Transform). Alle Varianten liegen in kopf-lokalen Koordinaten → gleiche Ausrichtung, ein Kopf.
- Gesichtselemente, Haare und Bärte sind nicht mit dem Kopf verschmolzen (eigene Objekte).
- Umschalten: Eigenschaften `hair`/`beard`/`face`/`skin` am Empty `Fighter_Customization` setzen und Textblock `fighter_customize.py` ausführen (blendet Collections ein/aus, setzt `Skin_Tone`).
- Der rechte Oberarm teilt weiter das Mesh ohne UVs → dort erscheint kein Tattoo; der linke hat eine eigene Mesh-Kopie mit UVs.

## Später technisch zu testen (nicht geprüft)
- Roblox: ob Haare/Bart/Gesicht als Accessories (Attachment-Punkte) oder als Teile des Kopf-Meshes umgesetzt werden; Attachment-Namen/-Orientierung gegen Roblox-Standard (z. B. HairAttachment, FaceFrontAttachment).
- Roblox-Hautfarbe: dort meist Part-Farbe/SurfaceAppearance statt Blender-Node – Tattoo als Decal/Textur-Overlay mit Hautton testen.
- Tattoo-UVs nach Export (FBX), Textur-Auflösung und Sichtbarkeit auf dunklen Tönen im Spiel-Licht.
- Boolean- und Bevel-Modifier müssen vor dem Export angewendet werden; danach Dreiecke und Normalen prüfen.
- Bärte und Mundformen bei Animation/Rig (Mund-Ausschnitt muss zu allen Mündern passen; derzeit statisch passend).
- Keine R15-Kompatibilität geprüft, kein Rig, keine Animation.

---

# v05 – Verfeinerung + Modularitätstest

Datei: `Fighter_Customization_v05.blend` (Basis v04, unverändert). Skript: `build_fighter_customization_v05.py`.
Übersicht: `renders/fighter_customization_v05_overview.png`; Einzelbilder + Messwerte: `renders/custom_v05/` (`checks_v05.json`).

## Geändert (nur Modelle/Materialien)
- **Buzzcut:** eng anliegende Kappe, 3–6 mm über dem Kopf, gerader Haaransatz vorn, Schläfenecken per Boolean (`FC5_Cut_Temples`). 160 Dreiecke.
- **Kurze Locken:** dünne Grundkappe + facettiert gerundete Büschel (Icosphere, 3 Größen, gestaucht), Stirnbogen aus 7 Büscheln. ~4.000 Dreiecke.
- **Kurzer Bart:** eine anliegende Schale (6 mm Abstand, 5 mm stark) mit Wangenlinie, Mundöffnung und hinterem Schnitt vor den Ohren; seitliche Leisten entfernt. Schnurrbart als schmales Band integriert.
- **Vollbart:** ein zusammenhängendes Volumen Wange → Kiefer → Kinn, eigene Wangenlinie, Mundöffnung, separater hängender Schnurrbart.
- **Tattoo:** Deckkraft 0,92 → 1,0. Auf dunkler Haut wird **nur die schwarze Konturtinte** automatisch aufgehellt (Node `Ink_Lift`, gesteuert über Hauthelligkeit und Tintenhelligkeit); der rote Stern und die Motivform bleiben unverändert. Hautton bleibt allein über `Skin_Tone` steuerbar.

## Prüfergebnisse
- Frisur × Bart: alle 12 Kombinationen gerendert; geometrische Überschneidung Frisur↔Bart in allen 12 Fällen **0**.
- Gegen Ohren und Oberkörper: alle Frisuren und Bärte **0** Überschneidungen.
- **Nase:** kurzer Bart und Vollbart berühren die Nasenunterkante (je 10 Flächenpaare, wenige mm). Behebung später: Wangen-/Schnurrbartlinie in der Mitte 3 mm absenken.
- Haar- und Bartfarbe unabhängig: `FC4_Hair_Color` (Haare + Augenbrauen) und `FC4_Beard_Color`; getestet mit braun/rot und schwarz/grau.
- Tattoo-Kontrast (mittlerer Helligkeitsabstand Tinte↔Haut aus Renderings, Tattoo an/aus, gleiche Kamera):
  hell 0,27 → 0,34 · mittel 0,24 → 0,28 · dunkel 0,07 → 0,21.

## Bekannte Probleme
- Augenbrauen hängen an der Haarfarbe (bei Blond sehr hell) – ggf. eigenes Brauenmaterial.
- Locken sind mit ~4.000 Dreiecken die teuerste Variante; für Handy reduzieren (weniger Büschel oder Unterteilung 1).
- Vollbart wirkt von vorn noch kastenförmig (gerade Unterkante).
- Hautton „Dunkel“ wirkt unter dem hellen Präsentationslicht noch mittelbraun.
- Bilder und Blender-Prüfungen beweisen **keine** technische Austauschbarkeit in Roblox – Accessory-/Attachment-Test, Export und Materialumsetzung bleiben offen.
