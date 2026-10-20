# Launch v02 – Quelldateien / Studio-Ziele

Stand2026-10-20. Nicht zusätzlich parallel starten: Versionierte Datei ersetzt Source am angegebenen Ziel. AnnouncerHUD und VisualTheme sind neue LocalScripts; alle anderen Ziele existierten bereits. Backups zuerst. Keine Änderungen an Kampfschaden, Remotes, Animationen, Maps oder Kleidung.

| Repository: roblox/ | Aktives Studio-Ziel |
|---|---|
| CC_UI_v02.module.luau | ReplicatedStorage.CC_UI |
| CC_MainMenu_v02.client.luau | StarterGui.CC_MainMenuGui.MainMenu |
| CC_HUD_v02.client.luau | StarterGui.CC_HUD.HUD |
| CC_GymHUD_v02.client.luau | StarterGui.CC_GymHUD.GymHUD |
| CC_Profile_v02.server.luau | ServerScriptService.CC_Profile |
| CC_LoadingScreen_v03.client.luau | ReplicatedFirst.CC_LoadingScreen |
| CC_Minigame_v02.client.luau | StarterPlayer.StarterPlayerScripts.CC_Minigame |
| CC_TrainerPanel_v02.client.luau | StarterPlayer.StarterPlayerScripts.CC_TrainerPanel |
| CC_BeltAward_v02.client.luau | StarterPlayer.StarterPlayerScripts.CC_BeltAward |
| CC_Story_v02.client.luau | StarterPlayer.StarterPlayerScripts.CC_Story |
| CC_CornerView_v02.client.luau | StarterPlayer.StarterPlayerScripts.CC_CornerView |
| CC_AnnouncerHUD_v02.client.luau | StarterPlayer.StarterPlayerScripts.CC_AnnouncerHUD |
| CC_VisualTheme_v02.client.luau | StarterPlayer.StarterPlayerScripts.CC_VisualTheme |

CC_Profile ergänzt ausschließlich persistentes settings.reduceMotion + Attribut CC_ReduceMotion. TrainerPanel nutzt existierende Serveraktionen start/challenge/equip/unequip; keine neue Freischaltlogik. CC_UI ersetzt native Darstellung und erhält öffentliche Helper-Signaturen. CC_VisualTheme passt direkt erzeugte Legacy-UI an; markierte native CC_UI-Elemente und LoadingScreen sind ausgenommen.

Quellen wurden im Edit-Modus exakt auf Gleichheit geprüft. Place-Speicherung durch Nutzer offen. Testnachweise und Einschränkungen: PROJECT_v02.md. Keine Asset-IDs neu erfunden, keine Bilder erforderlich.
