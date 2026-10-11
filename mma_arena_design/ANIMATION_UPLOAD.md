# Animations-Upload (erledigt 2026-10-11, Gruppe ANIMEXGANG 7160158)

**Erledigt:** alle 64 hochgeladen (vom Nutzer gestartet), IDs in `roblox/CC_AnimIds.luau` und in Studio (`ServerStorage.CC_Animations.CC_AnimIds`). Geprüft: alle 64 laden in Roblox, Längen gleich wie in Studio; Charaktere spielen die hochgeladenen IDs. **Neue oder geänderte Animationen** müssen erneut hochgeladen werden (Datei in export/anim_rbxmx ersetzen bzw. Eintrag in CC_AnimIds löschen, dann upload_starten.ps1).

## Warum
Mit temporären Studio-IDs laufen die Animationen nur im Einzel-Test. Beim Test mit 2 Clients und im echten Spiel bekommen die Spieler nur leere Animationen (Länge 0), die Kämpfer stehen in der T-Pose (geprüft 2026-10-11).

## Stand
- Studios direkte Upload-Funktion (`AssetService:CreateAssetAsync`) ist von Roblox gesperrt („not available yet“).
- Weg: Roblox Open Cloud Assets API (Animation als .rbxmx).
- `export/anim_rbxmx/*.rbxmx`: 64 Animationen, direkt aus den KeyframeSequences in Studio geschrieben (Loop, Priorität, Keyframes, Posen, Easing).
- `upload_animations_v01.js` lädt sie hoch und schreibt `roblox/CC_AnimIds.luau`. Bei einem Abbruch macht ein erneuter Start weiter.
- `CC_CharacterAnimations` nimmt eingetragene IDs automatisch (`ServerStorage.CC_Animations.CC_AnimIds`).

## Schritte für den Nutzer
1. **API-Schlüssel für die Gruppe** auf create.roblox.com:
   - Oben links als Ersteller die Gruppe **ANIMEXGANG** wählen, dann **Open Cloud → API Keys → Create API Key**.
   - Zugriff: **Assets** mit **Read** und **Write**.
   - Erlaubte IP: `0.0.0.0/0` oder die eigene IP. Ablaufdatum nach Wunsch.
   - Den Schlüssel geheim halten und nicht in den Chat schreiben.
2. **PowerShell im Ordner `mma_arena_design`:**
   - Test mit 1 Animation:
     ```powershell
     $env:CC_ROBLOX_API_KEY = "<Schlüssel>"; node upload_animations_v01.js --test
     ```
   - Wenn „OK … -> <Zahl>“ kommt, den Rest hochladen:
     ```powershell
     node upload_animations_v01.js
     ```
3. Danach setzt Claude `CC_AnimIds` in Studio ein und testet mit 2 Clients.
