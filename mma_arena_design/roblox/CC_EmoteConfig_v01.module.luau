-- ReplicatedStorage.CC_EmoteConfig
-- Zentrale Emote-Konfiguration mit stabilen IDs (nie umbenennen: Profile/Shop verweisen spaeter darauf).
-- Besitz (owned) und belegte Rad-Slots (slots) sind getrennt: heute sind alle 8 frei (free = true) und die Slots = Standard.
-- anim = Name der KeyframeSequence in ServerStorage.CC_Animations; die hochgeladene Asset-ID kommt aus CC_AnimIds (gleicher Name).
-- Der Client sendet nur die Emote-ID; der Server waehlt die Animation selbst (keine vom Client gelieferten Asset-IDs).
local C = {}
C.LIST = {
	{ id = "cry_about_it", name = "CRY ABOUT IT", anim = "Emote_CryAboutIt", loop = false, free = true },
	{ id = "keep_talking", name = "KEEP TALKING", anim = "Emote_KeepTalking", loop = false, free = true },
	{ id = "go_to_sleep", name = "GO TO SLEEP", anim = "Emote_GoToSleep", loop = true, free = true },
	{ id = "take_the_l", name = "TAKE THE L", anim = "Emote_TakeTheL", loop = false, free = true },
	{ id = "champ_walk", name = "CHAMP WALK", anim = "Emote_ChampWalk", loop = true, free = true },
	{ id = "stone_face", name = "STONE FACE", anim = "Emote_StoneFace", loop = false, free = true },
	{ id = "bow_shot", name = "BOW SHOT", anim = "Emote_BowShot", loop = false, free = true },
	{ id = "dust_off", name = "DUST OFF", anim = "Emote_DustOff", loop = false, free = true },
}
C.BY_ID = {}
for i, e in ipairs(C.LIST) do e.order = i; C.BY_ID[e.id] = e end
C.SLOT_COUNT = 8
C.DEFAULT_SLOTS = {}
for i, e in ipairs(C.LIST) do C.DEFAULT_SLOTS[i] = e.id end
C.COOLDOWN = 1.5          -- Sekunden nach Ende eines Emotes
C.MIN_INTERVAL = 0.5      -- Mindestabstand zwischen Anfragen
return C
