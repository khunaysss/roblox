-- ReplicatedStorage.CC_Announcer
-- Englische Ansagen; jede Variante besteht aus hoechstens acht Woertern.
local Announcer = {
	walkout = {
		"The cage awaits its next challenger.",
		"Two fighters. One chance to shine.",
		"The walk ends. The challenge begins.",
		"Every step brings the fight closer.",
		"The crowd is ready. Are you?",
		"Time to make this cage your own.",
	},
	fightStart = {
		"Touch gloves. Find your moment. Fight!",
		"The bell has sounded. Let's fight!",
		"Stay sharp. The round starts now!",
		"Both corners ready. Let them fight!",
		"No more waiting. Here we go!",
		"The cage is yours. Fight!",
	},
	knockdown = {
		"Down, but this fight isn't over!",
		"A huge shot changes everything!",
		"That punch shook the whole cage!",
		"One opening. One massive knockdown!",
		"The momentum just changed hands!",
		"Can they recover from that shot?",
	},
	ko = {
		"It's over! A decisive knockout!",
		"One clean finish. No doubt tonight!",
		"The referee waves this fight off!",
		"A knockout that silences the cage!",
		"That is how you finish a fight!",
		"The final shot seals the victory!",
	},
	submission = {
		"The tap ends this contest!",
		"Control, patience, and a submission finish!",
		"The hold is secured. It's over!",
		"A technical finish on the ground!",
		"The referee sees the tap!",
		"A submission victory inside the cage!",
	},
	doctor = {
		"The doctor has stopped this contest.",
		"Fighter safety comes first. It's over.",
		"This fight ends by doctor stoppage.",
		"Medical advice brings this contest to an end.",
		"The referee calls for the doctor.",
		"No further action. The contest is stopped.",
	},
	decision = {
		"We go to the judges' scorecards.",
		"Three rounds complete. The judges will decide.",
		"The final bell leaves the judges working.",
		"Every round mattered. Here comes the decision.",
		"The cards are in. Let's hear them.",
		"A hard contest goes to the scorecards.",
	},
	winner = {
		"Raise that hand. The victory is yours!",
		"Tonight, this cage belongs to the winner!",
		"A hard earned win under the lights!",
		"The result is clear. Celebrate this moment!",
		"Your winner stands tall inside the cage!",
		"One victory. Another step toward the top!",
	},
	cornerAdvice = {
		"Breathe. Listen. Return with a clear plan.",
		"Keep your guard. Don't chase every opening.",
		"Manage your energy. Make each movement count.",
		"Stay patient. Find space before you attack.",
		"Reset your stance. Trust your training.",
		"Watch the rhythm. Choose your moment carefully.",
	},
}
for _, variants in pairs(Announcer) do table.freeze(variants) end
return table.freeze(Announcer)
