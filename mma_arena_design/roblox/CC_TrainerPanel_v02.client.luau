-- CC_TrainerPanel_v02: vorhandene Quests und servergepruefte Aktionen.
local RS = game:GetService("ReplicatedStorage")
local HS = game:GetService("HttpService")
local player = game.Players.LocalPlayer
local UI = require(RS:WaitForChild("CC_UI"))
local Progression = require(RS:WaitForChild("CC_SignatureProgression"))
local event = RS:WaitForChild("CC_TrainerPanel")
local C,F=UI.C,UI.F
local gui=UI.new("ScreenGui",{Name="CC_TrainerPanel",ResetOnSpawn=false,IgnoreGuiInset=false,DisplayOrder=45,Enabled=false,Parent=player:WaitForChild("PlayerGui")})
local canvas=UI.new("Frame",{BackgroundTransparency=1,Size=UDim2.fromScale(1,1),Parent=gui})
UI.autoscale(canvas,840)
local modal=UI.new("TextButton",{Name="InputShield",Text="",AutoButtonColor=false,Modal=true,BackgroundColor3=C.bg0,BackgroundTransparency=.35,Size=UDim2.fromScale(1,1),Parent=canvas})
local card=UI.panel({Name="CoachCard",AnchorPoint=Vector2.new(.5,.5),Position=UDim2.fromScale(.5,.5),Size=UDim2.fromOffset(640,492),ImageColor3=C.bg1,Parent=modal})
local function label(name,y,height,size,font,color)
	return UI.label({Name=name,Text="",Position=UDim2.fromOffset(24,y),Size=UDim2.new(1,-48,0,height),TextSize=size,FontFace=font,TextColor3=color or C.text,Parent=card})
end
local title=label("CoachName",20,36,28,F.title)
local style=label("Style",60,24,17,F.body,C.dim)
local signature=label("Signature",96,28,21,F.bold,C.gold)
local description=label("Description",128,42,16,F.body,C.dim)
local rows={}
for i=1,3 do
	local y=184+(i-1)*64
	local text=label("Requirement"..i,y,22,16,F.body)
	local _,fill=UI.bar({Position=UDim2.fromOffset(24,y+32),Size=UDim2.new(1,-48,0,6),Parent=card},C.gold)
	rows[i]={text=text,fill=fill}
end
local condition=label("Condition",380,32,16,F.bold,C.dim)
local footer=UI.new("Frame",{BackgroundTransparency=1,Position=UDim2.fromOffset(24,428),Size=UDim2.new(1,-48,0,40),Parent=card})
local current,action
local function close()
	gui.Enabled=false
	current=nil
	player:SetAttribute("CC_TrainerPanelOpen",nil)
end
local function unlocked()
	return current and table.find(string.split(player:GetAttribute("CC_SigUnlocked") or "",","),current.sig or "")~=nil
end
local function progress()
	local ok,data=pcall(HS.JSONDecode,HS,player:GetAttribute("CC_SigProgress") or "{}")
	return ok and type(data)=="table" and data or {}
end
local primary,parts=UI.button({Name="CoachAction",Text="START QUEST",Style="primary",Size=UDim2.new(.65,-8,1,0),Parent=footer,OnClick=function()
	if not current or not action then return end
	event:FireServer(action,current.sig)
	close()
end})
local cancel=UI.button({Name="Close",Text="CLOSE",Style="secondary",Position=UDim2.new(.65,0,0,0),Size=UDim2.new(.35,0,1,0),Parent=footer,OnClick=close})
-- Position wird separat gesetzt, da die Button-API nur ihre zugesicherten Optionen liest.
cancel.Position=UDim2.new(.65,0,0,0)
local function refresh()
	if not current then return end
	local def=Progression.list[current.sig]
	local data=progress()
	local values=data[current.sig] or {}
	local equipped=player:GetAttribute("CC_Signature")==current.sig
	local free=unlocked()
	title.Text=current.name or "COACH"
	style.Text=current.style or ""
	signature.Text=current.sigName or (def and def.signatureName) or "SIGNATURE"
	description.Text=current.move or ""
	for i,row in ipairs(rows) do
		local requirement=def and def.requirements[i]
		row.text.Visible=requirement~=nil
		row.fill.Parent.Visible=requirement~=nil
		if requirement then
			local n=math.max(0,tonumber(values[requirement.key]) or 0)
			row.text.Text=string.format("%s  ·  %d / %d",requirement.label,math.min(n,requirement.target),requirement.target)
			row.fill.Size=UDim2.fromScale(math.clamp(n/math.max(requirement.target,1),0,1),1)
			row.fill.BackgroundColor3=n>=requirement.target and C.green or C.gold
		end
	end
	local ready=def and Progression.ready(current.sig,data)
	action=free and (equipped and "unequip" or "equip") or not values.started and "start" or ready and "challenge" or nil
	parts.title.Text=free and (equipped and "UNEQUIP" or "EQUIP (G)") or not values.started and "START QUEST" or ready and "CHALLENGE COACH" or "QUEST IN PROGRESS"
	primary:SetAttribute("Disabled",not def or action==nil)
	condition.Text=free and "MASTERED · Use G in a fight with full focus."
		or ready and "All requirements met. Win the coach final fight."
		or values.started and "Complete these requirements, then return to the coach."
		or "Start the quest before earning progress."
	condition.TextColor3=free and C.gold or ready and C.green or C.dim
end
event.OnClientEvent:Connect(function(kind,data)
	if kind~="open" or type(data)~="table" then return end
	current=data
	refresh()
	player:SetAttribute("CC_TrainerPanelOpen",true)
	gui.Enabled=true
end)
for _,name in ipairs({"CC_Signature","CC_SigUnlocked","CC_SigProgress"}) do
	player:GetAttributeChangedSignal(name):Connect(refresh)
end
RS:WaitForChild("CC_MatchState"):GetAttributeChangedSignal("State"):Connect(function()
	local state=RS.CC_MatchState:GetAttribute("State")
	if state~="idle" then close() end
end)
