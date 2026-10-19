-- Karriere-Gegner (10, steigend); ausschliesslich vorhandene Cage-Champions-Modelle. Titel in M.titles.
local M = {}
M.division = "LIGHTWEIGHT"
M.list = {
 {id="rafael_costa",name="Rafael Costa",style="Pressure Boxer",aiStyle="Boxer",stage="AMATEUR",rank=10,difficulty="anfaenger",rounds=3,rewardXP=45,
  look={hair="Hair_SidePart",beard="none",face="Face_Friendly",skin=2,hairColor=2},
  stats={Power=2,Cardio=3,Wrestling=1,Grappling=1},tip="Stay outside his jab range and counter after the cross."},
 {id="tomas_novak",name="Tomas Novak",style="Young Kickboxer",aiStyle="Kickboxer",stage="AMATEUR",rank=9,difficulty="anfaenger",rounds=3,rewardXP=50,
  look={hair="Hair_ShortCurls",beard="none",face="Face_Friendly",skin=1,hairColor=3},
  stats={Power=3,Cardio=4,Wrestling=2,Grappling=1},tip="He kicks a lot, but slowly. Block the kick and go in right away with jab-cross."},
 {id="viktor_petrov",name="Viktor Petrov",style="Wrestler",aiStyle="Wrestler",stage="AMATEUR FINAL",rank=8,difficulty="fortgeschritten",rounds=3,rewardXP=60,
  look={hair="Hair_Buzzcut",beard="Beard_Full",face="Face_Focused",skin=1,hairColor=4},
  stats={Power=4,Cardio=5,Wrestling=7,Grappling=5},tip="Sprawl early. Stay calm on the ground and save stamina."},
 {id="leon_brandt",name="Leon Brandt",style="BJJ Specialist",aiStyle="Grappler",stage="PRO DEBUT",rank=7,difficulty="fortgeschritten",rounds=3,rewardXP=70,
  look={hair="Hair_QuiffV03",beard="Beard_Short",face="Face_Neutral",skin=2,hairColor=2},
  stats={Power=5,Cardio=6,Wrestling=6,Grappling=9},tip="Do not get pulled into his guard. He is weak standing up."},
 {id="malik_reed",name="Malik Reed",style="Counter Boxer",aiStyle="Boxer",stage="PRO",rank=6,rival=true,difficulty="contender",rounds=3,rewardXP=80,
  look={hair="Hair_ShortCurls",beard="none",face="Face_Focused",skin=3,hairColor=1},
  stats={Power=7,Cardio=8,Wrestling=4,Grappling=4},tip="Fake attacks. Do not repeat the same combo every time."},
 {id="omar_haddad",name="Omar Haddad",style="Chain Wrestler",aiStyle="Wrestler",stage="PRO",rank=5,difficulty="contender",rounds=3,rewardXP=88,
  look={hair="Hair_Buzzcut",beard="Beard_Full",face="Face_Focused",skin=3,hairColor=1},
  stats={Power=7,Cardio=10,Wrestling=11,Grappling=8},tip="He shoots after every block. Keep F ready and punish the sprawl with hooks."},
 {id="kenji_sato",name="Kenji Sato",style="Precision Kickboxer",aiStyle="Kickboxer",stage="RANKED",rank=4,difficulty="contender",rounds=3,rewardXP=95,
  look={hair="Hair_SidePart",beard="none",face="Face_Focused",skin=2,hairColor=1},
  stats={Power=9,Cardio=11,Wrestling=6,Grappling=6},tip="His kicks come after the jab. Check the leg and counter right away."},
 {id="ivan_morozov",name="Ivan Morozov",style="Heavy Puncher",aiStyle="Boxer",stage="RANKED TOP 3",rank=3,difficulty="champion",rounds=3,rewardXP=105,
  look={hair="Hair_Buzzcut",beard="none",face="Face_Neutral",skin=1,hairColor=4},
  stats={Power=14,Cardio=10,Wrestling=7,Grappling=7},tip="His hooks hit hard. Stay at range; low kicks take his legs away."},
 {id="bruno_silva",name="Bruno Silva",style="Pressure Grappler",aiStyle="Grappler",stage="NUMBER ONE FIGHT",rank=2,difficulty="champion",rounds=3,rewardXP=120,
  look={hair="Hair_Buzzcut",beard="Beard_Short",face="Face_Neutral",skin=4,hairColor=2},
  stats={Power=11,Cardio=13,Wrestling=14,Grappling=15},tip="Keep the center free and do not waste stamina on the ground."},
 {id="darius_cole",name="Darius Cole",style="Kickboxer",aiStyle="Kickboxer",stage="TITLE FIGHT",rank=1,difficulty="champion",rounds=5,rewardXP=160,
  look={hair="Hair_QuiffV03",beard="Beard_Short",face="Face_Neutral",skin=4,hairColor=1},
  stats={Power=15,Cardio=16,Wrestling=11,Grappling=12},tip="Control the distance, block high kicks and attack the body."},
}
-- Karriere-Titel: werden nach Siegen (Anzahl besiegter Gegner) erreicht; beim ersten Erreichen einmalig Bonus-XP (CC_Profile)
M.titles = {
 {wins=0,name="AMATEUR",bonusXP=0},
 {wins=2,name="AMATEUR CHAMPION",bonusXP=50},
 {wins=4,name="PRO",bonusXP=80},
 {wins=7,name="TOP CONTENDER",bonusXP=120},
 {wins=10,name="LIGHTWEIGHT CHAMPION",bonusXP=250},
}
function M.titleFor(wins)
 local t=M.titles[1]
 for _,d in ipairs(M.titles) do if (wins or 0)>=d.wins then t=d end end
 return t
end
M.byId,M.index={},{}
for i,d in ipairs(M.list) do M.byId[d.id]=d; M.index[d.id]=i end
function M.beatenSet(value)
 local t={}
 if type(value)=="string" then
  for id in value:gmatch("[^,]+") do t[id]=true end
 elseif type(value)=="table" then
  for key,entry in pairs(value) do
   if type(key)=="string" and entry==true then t[key]=true
   elseif type(entry)=="string" then t[entry]=true end
  end
 end
 return t
end
function M.isUnlocked(id,value)
 local i=M.index[id]
 if not i then return false end
 if i==1 then return true end
 local b=M.beatenSet(value)
 return b[M.list[i-1].id]==true
end
function M.nextId(value)
 local b=M.beatenSet(value)
 for _,d in ipairs(M.list) do if not b[d.id] then return d.id end end
 return M.list[#M.list].id
end
return M
