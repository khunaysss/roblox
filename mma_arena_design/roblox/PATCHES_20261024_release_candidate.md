# Studio-Patches 24.10.2026 (Release-Kandidat, nur Studio, nicht veröffentlicht)

Backups vor jeder Änderung: `ServerStorage.CC_Backup_20261024_ReleaseCand` (Testarena-Kopie, Lighting, Skripte; `*_before_xray`).
Neue Dateien: `CC_FinishReactions_v03.client.luau` (StarterPlayerScripts), `CC_XRay_v01.module.luau` (ReplicatedStorage).

| Skript | Änderung | Grund (belegt) | Test |
|---|---|---|---|
| CC_Referee (Server) | Modus `present` bei EventStep `decision`: Ringrichter geht nach Mitte + (2,2 / 0 / −6,8) | stand zwischen Ergebniskamera (+13,2 Z) und Kämpfern | Decision-Sieg + Draw: frei |
| CC_EventDirector (Client) | Draw: frontale Einstellung statt Sieger-Kamera; Abbruch-Kamera in den Käfig (Radius − 2) | Rot füllte Draw-Bild; Kamera stand hinter Zaunstange | Draw + Submission-Abbruch |
| CC_Corner (Server) | Trainer 40° um die Mund-Achse versetzt (`COACH_ANGLE`) | Körperüberlagerung (Blender: −58 %, `check_corner_overlap_v01.py`) | Pause-Screenshot |
| CC_CornerView (Client) | Kamera rechts vom Kämpfer; Flasche zielt auf Mund, Mitte 0,3 Studs; dunkles Statusband | Trainer verdeckte; Flasche im Kopf; Text unlesbar | Pause-Screenshot |
| CC_ConnectionCrowd (Client) | Ordner an `CurrentCamera` statt PlayerGui, Neuaufbau bei Entfernen | nach Respawn alle 192 Bilder dauerhaft weg | Respawn: 192 bleiben |
| CC_DayNightClient (Client) | Hallen-Lichtprofil für Arenen mit `CC_LightProfile="hall_v1"` (fest, Ambient 138/130/122, ohne doppelte Farbkorrektur) | Tageszyklus + dunkler Gym-Ambient in der Halle; Kontrast doppelt | Vorher/Nachher-Bilder |
| CC_ArenaTest_v04 (Modell) | Matte Fabric, schwarze Polster Leather 40/40/44, Spots 1,8, Attribut `CC_LightProfile` | Lesbarkeit | Bilder |
| CC_FinishReactions (neu) | Submission-Verteidiger: Rucke, Abklopfen, angestrengtes Gesicht; KO: Augen fast zu; Armbar → Röntgen | Auftrag | Armbar real, T.K.O. real |
| CC_XRay (neu) | Röntgen-Einblendung Ellbogenbruch (2,4 s, ohne Blut) | Auftrag | im echten Kampf ausgelöst |
