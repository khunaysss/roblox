# Animations-Upload (vorbereitet, NICHT ausgeführt)

- Ziel: Gruppe **ANIMEXGANG (7160158)**. Upload nur nach ausdrücklicher Freigabe des Nutzers.
- Ohne Upload laufen die Animationen nur in Studio (temporäre IDs über `KeyframeSequenceProvider:RegisterKeyframeSequence`).
- Vorbereitet:
  - `ServerStorage.CC_Animations.CC_AnimIds` (ModuleScript, zunächst leer): `[KeyframeSequence-Name] = Asset-ID`.
  - `CC_CharacterAnimations` nimmt eine eingetragene ID automatisch, sonst die temporäre.
- **64 Animationen** (alle als KeyframeSequence in `ServerStorage.CC_Animations` vorhanden):
  - **30 Steh-Animationen:**
    - Idle_v08, Walk/WalkBack/StrafeL/StrafeR_v01, MoveF/B/L/R_v01
    - Jab_v03, Cross_v03, Hook_v03, Uppercut_v02, JabBody/CrossBody_v01, LowKick_v03, BodyKick/HighKick/FrontKick_v01
    - Block/BlockHit_v01
    - HitReact/HitStraight/HitHook/HitUpper/HitLeg/HitBody/Stagger_v01
    - KO/KOForward_v01
  - **34 Paar-Animationen `WR_*`:** Takedown, Guard, Positionen, Submissions; je A und B.
- Ablauf nach Freigabe: in Studio jede KeyframeSequence als Animation für die Gruppe hochladen (Animation Editor → Veröffentlichen, oder per Studio-Skript über AssetService) und die IDs in `CC_AnimIds` eintragen. Danach testen.
