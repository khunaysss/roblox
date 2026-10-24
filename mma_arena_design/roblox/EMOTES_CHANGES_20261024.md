# Emotes – Änderungen 24.10.2026 (nach erstem Test)
- **Schnellerer Start (CC_Emotes):** Tracks je Charakter einmal laden und wiederverwenden, Animationen beim Serverstart vorladen (PreloadAsync),
  Einblendung 0,08 s statt 0,2 s, `skip = 0.3` in CC_EmoteConfig überspringt den eingebauten Anlauf (Cry About It, Keep Talking, Stone Face).
  Gemessen (Studio): volle Pose nach 136–167 ms.
- **Take the L neu:** `Emote_TakeTheL_v2` (CC_EmoteConfig zeigt darauf): beide Hände als L seitlich an der Stirn, Takt 0,55 s, Hüftschwung,
  Stampfen links/rechts, kein Anlauf. Erzeugt mit ServerStorage.CC_EmoteBuilder (Studio-Hilfsmodul, siehe build_emotes_v01.luau für die Berechnung).
  Neue Animation muss hochgeladen werden (Ordner ServerStorage.CC_AnimUpload_20261024b), ID in CC_AnimIds.
- Backups: ServerStorage.CC_Backup_20261024_ReleaseCand.Scripts (CC_Emotes_before_speedfix, CC_EmoteConfig_before_speedfix).
