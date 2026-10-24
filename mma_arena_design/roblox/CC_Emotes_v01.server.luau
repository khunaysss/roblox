-- ServerScriptService.CC_Emotes
-- Emotes serverseitig: prueft Emote-ID, Besitz, Slot, Zustand und Cooldown, spielt die Animation auf dem Animator des Charakters
-- (repliziert an alle Spieler) und bricht bei Bewegung, Angriff, Block, Treffer, Zustandswechsel, Teleport oder Respawn sofort ab.
-- Keine Unverwundbarkeit, keine Hitbox- oder Tempo-Aenderung. Attribut CC_Emote am Charakter waehrend des Emotes (Client-Optik
-- CC_CombatMotion pausiert dann ihre Fussarbeit-Ueberlagerung). Loop-Emotes wiederholen nur ausserhalb eines Kampfes.
local Players, RS, SS = game:GetService("Players"), game:GetService("ReplicatedStorage"), game:GetService("ServerStorage")
local RunService, KSP, Http = game:GetService("RunService"), game:GetService("KeyframeSequenceProvider"), game:GetService("HttpService")
local CFG = require(RS:WaitForChild("CC_EmoteConfig"))
local A = SS:WaitForChild("CC_Animations")
local ids = {}
pcall(function() ids = require(A:FindFirstChild("CC_AnimIds")) end)

local remote = RS:FindFirstChild("CC_EmoteRequest") or Instance.new("RemoteEvent")
remote.Name = "CC_EmoteRequest"; remote.Parent = RS

local anims = {}
local function animFor(name)
	if anims[name] ~= nil then return anims[name] or nil end
	local a = Instance.new("Animation")
	if ids[name] then a.AnimationId = "rbxassetid://" .. tostring(ids[name])
	elseif RunService:IsStudio() and A:FindFirstChild(name) then
		local ok, id = pcall(function() return KSP:RegisterKeyframeSequence(A[name]) end)   -- nur Studio-Vorschau
		if not ok then anims[name] = false; return nil end
		a.AnimationId = id
	else
		anims[name] = false; warn("[CC] Emote-Animation nicht hochgeladen: " .. name); return nil
	end
	anims[name] = a; return a
end

-- Besitz/Slots (heute: alles frei, Standard-Slots). Spaeter: Profil-Inventar hier einhaengen.
local function owns(_plr, def) return def.free == true end
local function slotsOf(plr)
	local ok, t = pcall(function() return Http:JSONDecode(plr:GetAttribute("CC_EmoteSlots") or "") end)
	return ok and type(t) == "table" and t or CFG.DEFAULT_SLOTS
end

local active = {}     -- [plr] = { track, char, root, hum, hp, pos, conns, def }
local lastEnd, lastReq = {}, {}
local function deny(plr, reason) plr:SetAttribute("CC_EmoteDenied", reason .. "|" .. tostring(os.clock())) end

local BLOCK_ATTRS = { "CC_KO", "CC_Knockdown", "CC_Down", "CC_Block", "CC_Frozen", "CC_SubRole", "CC_BagPractice" }
local function matchState(char)
	local id = char:GetAttribute("CC_MatchId")
	local ms = id and RS:FindFirstChild("CC_Matches") and RS.CC_Matches:FindFirstChild(id)
	return ms, ms and ms:GetAttribute("State")
end
local function blockedReason(plr, char, hum, root)
	if hum.Health <= 0 then return "dead" end
	for _, k in ipairs(BLOCK_ATTRS) do local v = char:GetAttribute(k); if v ~= nil and v ~= false and v ~= "" then return k end end
	local w = char:GetAttribute("CC_Wrestle"); if w ~= nil and w ~= false and w ~= "" then return "grappling" end
	if plr:GetAttribute("CC_Minigame") then return "minigame" end
	if root.Anchored or hum.Sit then return "busy" end
	if hum.FloorMaterial == Enum.Material.Air then return "air" end
	local ms, st = matchState(char)
	if ms and (st ~= "fight" or ms:GetAttribute("Corner") == true or (ms:GetAttribute("EventStep") or "") ~= "") then return "match_state" end
	local animator = hum:FindFirstChildOfClass("Animator")
	if animator then
		for _, tr in ipairs(animator:GetPlayingAnimationTracks()) do
			local p = tr.Priority
			if (p == Enum.AnimationPriority.Action4 or p == Enum.AnimationPriority.Action3 or p == Enum.AnimationPriority.Action)
				and tr.WeightCurrent > 0.2 and tr.Name ~= "CC_Emote" then return "action" end
		end
	end
	return nil
end

local function stop(plr, why)
	local e = active[plr]; if not e then return end
	active[plr] = nil
	for _, c in ipairs(e.conns) do c:Disconnect() end
	pcall(function() e.track:Stop(0.25) end)
	task.delay(0.4, function() pcall(function() e.track:Destroy() end) end)
	if e.char.Parent then e.char:SetAttribute("CC_Emote", nil) end
	plr:SetAttribute("CC_EmoteEnd", tostring(why))
	lastEnd[plr] = os.clock()
end

local function play(plr, id)
	local now = os.clock()
	if now - (lastReq[plr] or 0) < CFG.MIN_INTERVAL then return end
	lastReq[plr] = now
	local def = type(id) == "string" and CFG.BY_ID[id]
	if not def then return deny(plr, "unknown") end
	if not owns(plr, def) then return deny(plr, "locked") end
	if not table.find(slotsOf(plr), id) then return deny(plr, "not_equipped") end
	if active[plr] then stop(plr, "replace") end
	if now - (lastEnd[plr] or 0) < CFG.COOLDOWN then return deny(plr, "cooldown") end
	local char = plr.Character
	local hum = char and char:FindFirstChildOfClass("Humanoid")
	local root = char and char:FindFirstChild("HumanoidRootPart")
	local animator = hum and hum:FindFirstChildOfClass("Animator")
	if not (hum and root and animator) then return end
	local why = blockedReason(plr, char, hum, root)
	if why then return deny(plr, why) end
	local anim = animFor(def.anim)
	if not anim then return deny(plr, "not_uploaded") end
	local track = animator:LoadAnimation(anim)
	track.Name = "CC_Emote"
	track.Priority = Enum.AnimationPriority.Action2
	local inMatch = matchState(char) ~= nil
	track.Looped = def.loop and not inMatch
	local e = { track = track, char = char, root = root, hum = hum, hp = hum.Health, pos = root.Position, conns = {}, def = def, t0 = now }
	active[plr] = e
	char:SetAttribute("CC_Emote", id)
	track:Play(0.2)
	local function guard(k) return function() stop(plr, k) end end
	for _, k in ipairs(BLOCK_ATTRS) do table.insert(e.conns, char:GetAttributeChangedSignal(k):Connect(function() local v = char:GetAttribute(k); if v ~= nil and v ~= false and v ~= "" then stop(plr, k) end end)) end
	for _, k in ipairs({ "CC_Wrestle", "CC_LastAttack", "CC_LastReact", "CC_MatchId", "CC_DodgeUntil" }) do table.insert(e.conns, char:GetAttributeChangedSignal(k):Connect(guard(k))) end
	table.insert(e.conns, hum.HealthChanged:Connect(function(h) if h < e.hp - 0.01 then stop(plr, "hit") end; e.hp = math.max(e.hp, h) end))
	table.insert(e.conns, track.Stopped:Connect(function() if active[plr] == e then stop(plr, "ended") end end))
	table.insert(e.conns, char.AncestryChanged:Connect(function() if not char.Parent then stop(plr, "removed") end end))
	local ms = matchState(char)
	if ms then table.insert(e.conns, ms.AttributeChanged:Connect(function(k) if k == "State" or k == "Corner" or k == "EventStep" then stop(plr, "match") end end)) end
end

-- Bewegung / Teleport: horizontale Geschwindigkeit oder Sprung der Position beendet das Emote
RunService.Heartbeat:Connect(function()
	for plr, e in pairs(active) do
		if not e.root.Parent then stop(plr, "removed")
		else
			local v = e.root.AssemblyLinearVelocity
			if os.clock() - e.t0 > 0.15 and Vector3.new(v.X, 0, v.Z).Magnitude > 2 then stop(plr, "move")
			elseif (e.root.Position - e.pos).Magnitude > 5 then stop(plr, "teleport")
			elseif e.hum.FloorMaterial == Enum.Material.Air and os.clock() - e.t0 > 0.15 then stop(plr, "air") end
		end
	end
end)

remote.OnServerEvent:Connect(function(plr, action, id)
	if action == "play" then play(plr, id)
	elseif action == "stop" then stop(plr, "client") end
end)

local function setup(plr)
	if plr:GetAttribute("CC_EmoteSlots") == nil then plr:SetAttribute("CC_EmoteSlots", Http:JSONEncode(CFG.DEFAULT_SLOTS)) end
	plr.CharacterRemoving:Connect(function() stop(plr, "respawn") end)
end
Players.PlayerAdded:Connect(setup)
for _, p in ipairs(Players:GetPlayers()) do setup(p) end
Players.PlayerRemoving:Connect(function(p) stop(p, "left"); lastEnd[p] = nil; lastReq[p] = nil end)
print("[CC] Emotes bereit (" .. #CFG.LIST .. ")")
