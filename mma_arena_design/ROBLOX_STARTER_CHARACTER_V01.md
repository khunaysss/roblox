# Spielbarer Kämpfer v01 (Roblox Studio)

Stand: 2026-10-10. Place `CageChampions_ImportTest_v01.rbxl`. Nicht veröffentlicht, nichts hochgeladen.

## Aufbau
- `StarterPlayer.StarterCharacter` = Kopie von `Workspace.CC_ImportTest.CC_Fighter_Base_v03`. Meshes, Bones, Gewichtung und Farben sind unverändert.
- `RootPart` heißt jetzt `HumanoidRootPart` und liegt 3 Studs höher (Mitte über den Füßen). Der `Root`-Bone und die 13 Motor6D (`C0`) sind um −3 Studs gegenkompensiert, Weltlage aller Bones und Meshes bleibt gleich.
- `Humanoid` (R15, HipHeight 2, WalkSpeed 12, ohne Auto-Skalierung) mit `Animator`. `AnimationController` und `InitialPoses` entfernt. MeshParts ohne Kollision, masselos.
- `ServerStorage.CC_Animations.Fighter_Idle_v08` = `Fighter_Idle_v07` mit Wurzel-Pose `HumanoidRootPart`.
- `ServerScriptService.CC_CharacterAnimations` spielt den Idle auf jedem Spielercharakter (temporäre Studio-ID).
- `StarterCharacterScripts.Animate` = leerer Platzhalter, damit das Standard-R15-Animate nicht startet.

## Playtest (geprüft)
- Spieler spawnt als Kämpfer, Zustand `Running`, 100 Leben, 1 Animations-Track (Idle).
- Fuß-Bones auf derselben Höhe wie im Testmodell (0,325 Studs über Boden-Nullpunkt der Figur), Figur steht auf dem Boden.
- WASD-Steuerung (W 1,5 s, D 0,8 s, Sprung): Figur bewegt sich ~13,7 Studs, Kamera folgt (Abstand 7,7 Studs).
- Standbild im Playtest: Kampfhaltung, Körper zusammenhängend. Keine Fehler in der Konsole.

## Offen
- Keine Laufanimation: Die Figur gleitet in Kampfhaltung. Sprung ohne Animation.
- Animations-IDs nur in Studio gültig; Upload in Gruppe ANIMEXGANG (ID 7160158) erst nach Freigabe.
