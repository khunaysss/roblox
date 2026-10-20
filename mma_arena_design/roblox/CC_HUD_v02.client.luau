-- CC_HUD_v02 – echte Kampfwerte, native Broadcast-Anzeige.
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local player = Players.LocalPlayer
local UI = require(RS:WaitForChild("CC_UI"))
local SIG = require(RS:WaitForChild("CC_Signatures"))
local match = RS:WaitForChild("CC_MatchState")
local gui = script.Parent
gui.IgnoreGuiInset = false
gui.ResetOnSpawn = false
gui.DisplayOrder = 5
local C, F = UI.C, UI.F
local function label(parent, name, text, position, size, font, textSize)
	return UI.label({Name = name, Text = text, Position = position, Size = size,
		FontFace = font or F.bold, TextSize = textSize or 16, TextWrapped = false, Parent = parent})
end
local function fighterCard(name, side, color)
	local root = UI.panel({Name = name, AnchorPoint = Vector2.new(side, 0),
		Position = UDim2.new(side, side == 0 and 24 or -24, 0, 24),
		Size = UDim2.new(.34, -24, 0, 112), ImageColor3 = C.bg0, Parent = gui})
	local identity = label(root, "Identity", "", UDim2.fromOffset(16, 8), UDim2.new(1,-32,0,24), F.head, 20)
	identity.TextTruncate = Enum.TextTruncate.AtEnd
	local hp = label(root, "HealthValue", "", UDim2.fromOffset(16, 34), UDim2.new(1,-32,0,20))
	hp.TextXAlignment = Enum.TextXAlignment.Right
	local _, health = UI.bar({Position=UDim2.fromOffset(16,58),Size=UDim2.new(1,-32,0,12),Parent=root},color)
	local staminaText = label(root,"StaminaValue","",UDim2.fromOffset(16,76),UDim2.new(1,-32,0,18),F.bold,14)
	staminaText.TextColor3=C.dim
	local _, stamina = UI.bar({Position=UDim2.fromOffset(16,98),Size=UDim2.new(1,-32,0,6),Parent=root},C.stamina)
	return {root=root,identity=identity,hp=hp,health=health,stamina=stamina,staminaText=staminaText}
end
local mine = fighterCard("PlayerCard",0,C.red)
local theirs = fighterCard("OpponentCard",1,C.blue)
local clock = UI.panel({Name="Clock",AnchorPoint=Vector2.new(.5,0),Position=UDim2.new(.5,0,0,24),Size=UDim2.fromOffset(184,96),ImageColor3=C.bg0,Parent=gui})
local roundL = label(clock,"Round","",UDim2.fromOffset(8,8),UDim2.new(1,-16,0,20),F.bold,14)
local timeL = label(clock,"Time","",UDim2.fromOffset(8,28),UDim2.new(1,-16,0,36),F.title,30)
local scoreL = label(clock,"Score","",UDim2.fromOffset(8,70),UDim2.new(1,-16,0,18),F.body,14)
for _,l in ipairs({roundL,timeL,scoreL}) do l.TextXAlignment=Enum.TextXAlignment.Center end
local focus = UI.panel({Name="Focus",Position=UDim2.fromOffset(24,144),Size=UDim2.new(.34,-24,0,48),Visible=false,Parent=gui})
local focusText = label(focus,"Signature","",UDim2.fromOffset(16,4),UDim2.new(1,-32,0,24),F.bold,14)
focusText.TextTruncate=Enum.TextTruncate.AtEnd
local _,focusFill = UI.bar({Position=UDim2.fromOffset(16,34),Size=UDim2.new(1,-32,0,6),Parent=focus},C.gold)
local focusStroke=focus:FindFirstChildOfClass("UIStroke")
local condition = label(gui,"Condition","",UDim2.fromOffset(24,200),UDim2.new(.34,-24,0,24),F.bold,16)
local controls = UI.panel({Name="Controls",AnchorPoint=Vector2.new(.5,1),Position=UDim2.new(.5,0,1,-16),Size=UDim2.new(.9,0,0,96),Parent=gui})
local controlsLimit = UI.new("UISizeConstraint",{MaxSize=Vector2.new(1120,112),Parent=controls})
local cells={}
for i=1,12 do
	local row,col=math.floor((i-1)/6),(i-1)%6
	local cell=UI.new("Frame",{Name="Action"..i,BackgroundTransparency=1,Position=UDim2.new(col/6,8,0,8+row*42),Size=UDim2.new(1/6,-16,0,36),Parent=controls})
	local key=UI.key("",{Position=UDim2.new(),Size=UDim2.fromOffset(48,32),Parent=cell})
	local text=label(cell,"Action","",UDim2.fromOffset(56,0),UDim2.new(1,-56,1,0),F.body,13)
	text.TextWrapped=true
	cells[i]={root=cell,key=key,text=text}
end
local positionL=label(gui,"Position","",UDim2.new(.5,0,1,-152),UDim2.fromOffset(620,28),F.head,22)
positionL.AnchorPoint=Vector2.new(.5,1)
positionL.TextXAlignment=Enum.TextXAlignment.Center
local duel=UI.panel({Name="Submission",AnchorPoint=Vector2.new(.5,1),Position=UDim2.new(.5,0,1,-192),Size=UDim2.new(.55,0,0,72),Visible=false,Parent=gui})
local duelName=label(duel,"Name","",UDim2.fromOffset(16,8),UDim2.new(1,-32,0,24),F.head,20)
duelName.TextXAlignment=Enum.TextXAlignment.Center
local track,duelFill=UI.bar({Position=UDim2.fromOffset(16,44),Size=UDim2.new(1,-32,0,12),Parent=duel},C.red)
track.BackgroundColor3=C.blue
local banner=label(gui,"Banner","",UDim2.fromScale(.5,.34),UDim2.new(.8,0,0,72),F.title,48)
banner.AnchorPoint=Vector2.new(.5,.5);banner.TextXAlignment=Enum.TextXAlignment.Center
local bannerSub=label(gui,"BannerSub","",UDim2.fromScale(.5,.4),UDim2.new(.8,0,0,48),F.bold,20)
bannerSub.AnchorPoint=Vector2.new(.5,0);bannerSub.TextXAlignment=Enum.TextXAlignment.Center;bannerSub.TextWrapped=true
local POS={guard="GUARD",half="HALF GUARD",side="SIDE CONTROL",mount="MOUNT",back="BACK CONTROL",seated="SEATED",kneel="KNEELING"}
local function signature()
	local id=workspace:GetAttribute(SIG.TEST_ATTR) or player:GetAttribute("CC_SigTrial") or player:GetAttribute("CC_Signature")
	return id and SIG.list[id]
end
local stand={{"LMB","Jab"},{"RMB","Cross"},{"Q","Hook"},{"R","Uppercut"},{"C/X","Kicks"},{"V/Z","Kicks"},{"F","Block / Sprawl"},{"E","Takedown"},{"T","Target"},{"SPACE","Get up"},{"WASD","Move"}}
local lastHints=""
local function hints(entries)
	local stamp=""
	for _,entry in ipairs(entries) do stamp ..= entry[1]..entry[2] end
	if stamp==lastHints then return end
	lastHints=stamp
	for i,cell in ipairs(cells) do
		local entry=entries[i]
		cell.root.Visible=entry~=nil
		if entry then
			local keyText=cell.key:FindFirstChildWhichIsA("TextLabel",true)
			if keyText then keyText.Text=entry[1];keyText.TextSize=entry[1]=="SPACE" and 10 or 12 end
			cell.text.Text=entry[2]
		end
	end
	controls.Size=UDim2.new(.9,0,0,#entries>6 and 96 or 56)
end
local function updateCard(card,char,identity)
	card.identity.Text=identity
	local hum=char and char:FindFirstChildOfClass("Humanoid")
	if not hum then card.hp.Text="";return end
	local maxHP=math.max(hum.MaxHealth,1)
	card.health.Size=UDim2.fromScale(math.clamp(hum.Health/maxHP,0,1),1)
	card.hp.Text=string.format("%d / %d HP",math.ceil(hum.Health),math.ceil(maxHP))
	local stamina=char:GetAttribute("CC_Stamina") or 100
	local maxStamina=math.max(char:GetAttribute("CC_StaminaMax") or 100,1)
	card.stamina.Size=UDim2.fromScale(math.clamp(stamina/maxStamina,0,1),1)
	card.staminaText.Text=string.format("STAMINA  %d / %d",math.floor(stamina+.5),maxStamina)
end
local elapsed=0
RunService.Heartbeat:Connect(function(dt)
	elapsed+=dt
	if elapsed<.05 then return end
	elapsed=0
	local char=player.Character
	local oppName=char and char:GetAttribute("CC_Opponent")
	local opp=oppName and workspace:FindFirstChild(oppName)
	local state=match:GetAttribute("State")
	local mode=match:GetAttribute("Mode")
	local active=player:GetAttribute("CC_MatchId")~=nil and player:GetAttribute("CC_MatchId")~=""
	local tutorial=mode=="tutorial"
	local blocked=player:GetAttribute("CC_UIBlock")==true
	local visible=active and not tutorial and not blocked
	mine.root.Visible=visible;theirs.root.Visible=visible;clock.Visible=visible
	controls.Visible=visible and state=="fight"
	condition.Visible=visible
	local feedback=player.PlayerGui:FindFirstChild("CC_GroundFeedback")
	local feedbackPanel=feedback and feedback:FindFirstChild("Panel")
	positionL.Visible=visible and state=="fight" and not (feedbackPanel and feedbackPanel.Visible)
	banner.Visible=visible and match:GetAttribute("Corner")~=true
	bannerSub.Visible=banner.Visible
	local blue=match:GetAttribute("BlueName")==player.Name
	updateCard(mine,char,"YOU · "..player.DisplayName)
	updateCard(theirs,opp,blue and (match:GetAttribute("RedName") or "OPPONENT") or (match:GetAttribute("BlueName") or "OPPONENT"))
	local value=math.max(0,match:GetAttribute("TimeLeft") or 0)
	roundL.Text=string.format("ROUND %d / %d",match:GetAttribute("Round") or 1,match:GetAttribute("Rounds") or 3)
	timeL.Text=state=="fight" and string.format("%d:%02d",value//60,value%60) or state=="break" and "BREAK" or state=="over" and "END" or "READY"
	local redScore,blueScore=match:GetAttribute("ScoreRed") or 0,match:GetAttribute("ScoreBlue") or 0
	if blue then redScore,blueScore=blueScore,redScore end
	scoreL.Text=string.format("%d : %d",redScore,blueScore)
	banner.Text=match:GetAttribute("Banner") or ""
	if state=="over" then banner.Text=match:GetAttribute("Winner")=="draw" and "DRAW" or match:GetAttribute("WinnerName")==player.Name and "WIN" or "LOSS" end
	banner.TextColor3=state=="over" and C.gold or C.text
	bannerSub.Text=match:GetAttribute("BannerSub") or ""
	if not char then focus.Visible=false;duel.Visible=false;return end
	local def=signature()
	local amount=char:GetAttribute("CC_Focus") or 0
	local full=amount>=SIG.FOCUS_MAX
	focus.Visible=visible and def~=nil
	focusFill.Size=UDim2.fromScale(math.clamp(amount/math.max(SIG.FOCUS_MAX,1),0,1),1)
	focusText.Text=full and ("SIGNATURE READY [G] · "..(def and def.name or "")) or "FOCUS"
	focusText.TextColor3=full and C.gold or C.dim
	if focusStroke then
		focusStroke.Color=full and C.gold or C.line
		focusStroke.Transparency=full and not UI.reduceMotion() and (.15+.2*math.sin(os.clock()*3)) or 0
	end
	local stam=char:GetAttribute("CC_Stamina") or 100
	condition.Text=char:GetAttribute("CC_Block") and "BLOCK" or stam<25 and "LOW STAMINA" or ""
	condition.TextColor3=stam<25 and C.red or C.blue
	local role,pos=char:GetAttribute("CC_Wrestle"),char:GetAttribute("CC_GroundPos")
	local down=char:GetAttribute("CC_Down")
	local progress=char:GetAttribute("CC_SubProgress")
	duel.Visible=visible and progress~=nil
	if progress then
		duelFill.Size=UDim2.fromScale(math.clamp(progress,0,1),1)
		local attack=char:GetAttribute("CC_SubRole")=="attack"
		duelName.Text=(char:GetAttribute("CC_SubName") or "SUBMISSION").." · "..(attack and "MASH Q" or "MASH SPACE")
	end
	local entries
	positionL.Text=""
	if down then
		positionL.Text=POS[down] or "DOWN"
		entries={{"SPACE","Get up"},{"F","Block"}}
		if down~="kneel" then table.insert(entries,{"E","Move up"}) end
		if down=="back" then table.insert(entries,{"LMB","Push kick"});table.insert(entries,{"C","Leg kick"}) end
	elseif role and pos then
		positionL.Text=(POS[pos] or string.upper(pos)).." · "..(role=="top" and "TOP" or "BOTTOM")
		if role=="top" then
			entries={{"F","Counter"}}
			if pos~="back" then table.insert(entries,{"E","Improve position"}) end
			if pos=="guard" or pos=="mount" then table.insert(entries,{"LMB","Strike"}) end
			if pos=="mount" or pos=="back" then table.insert(entries,{"Q","Submission"}) end
			if pos=="guard" then table.insert(entries,{"SPACE","Get up"}) end
		else entries={{"SPACE",pos=="guard" and "Get up" or "Escape"},{"F","Counter"}} end
	elseif opp and opp:GetAttribute("CC_Down") then
		positionL.Text="OPPONENT DOWN"
		entries={{"C","Low kick"}}
		if opp:GetAttribute("CC_Down")=="back" then table.insert(entries,{"E","Into guard"}) end
	else
		entries=table.clone(stand)
		if def then table.insert(entries,{"G","Signature"}) end
	end
	hints(entries)
end)
