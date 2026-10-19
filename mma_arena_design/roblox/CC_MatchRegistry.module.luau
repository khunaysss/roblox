-- ReplicatedStorage.CC_MatchRegistry (ModuleScript)
-- Mehrere Kaempfe gleichzeitig: jeder Kampf hat einen eigenen Zustands-Ordner ReplicatedStorage.CC_Matches.<id>
-- (Attribute wie frueher an CC_MatchState: State, Mode, Round, TimeLeft, Banner, ...; dazu CageCenter, CageRadius, MatchId).
-- Ruhezustand ohne Kampf: CC_Matches.idle. Zuordnung: Attribut CC_MatchId am Spieler und am Kaempfer-Modell (auch am KI-Gegner).
-- Server: stateOf(spieler | charakter) liefert den passenden Ordner (nie nil).
-- Client: CC_MatchStateMirror spiegelt den eigenen Ordner lokal nach ReplicatedStorage.CC_MatchState, damit alle
-- Anzeigen (HUD, Menue, Finisher, Tutorial) unveraendert weiterlaufen.
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local M = {}

local function root()
	local f = RS:FindFirstChild("CC_Matches")
	if not f and RunService:IsServer() then
		f = Instance.new("Folder"); f.Name = "CC_Matches"; f.Parent = RS
	end
	return f or RS:WaitForChild("CC_Matches")
end
M.root = root

function M.idle()
	local r = root()
	local f = r:FindFirstChild("idle")
	if not f and RunService:IsServer() then
		f = Instance.new("Folder"); f.Name = "idle"; f:SetAttribute("State", "idle"); f:SetAttribute("Mode", ""); f.Parent = r
	end
	return f or r:WaitForChild("idle")
end

function M.idOf(x)
	if typeof(x) ~= "Instance" then return nil end
	local id = x:GetAttribute("CC_MatchId")
	if id then return id end
	if x:IsA("Model") then
		local p = Players:GetPlayerFromCharacter(x)
		return p and p:GetAttribute("CC_MatchId") or nil
	elseif x:IsA("Player") then
		local c = x.Character
		return c and c:GetAttribute("CC_MatchId") or nil
	end
	return nil
end

-- Zustands-Ordner des Kampfs von Spieler oder Charakter (Ruhezustand, wenn nicht im Kampf)
function M.stateOf(x)
	local id = M.idOf(x)
	local f = id and root():FindFirstChild(id)
	return f or M.idle()
end

return M
