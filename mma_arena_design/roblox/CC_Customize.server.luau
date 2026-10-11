-- ServerScriptService.CC_Customize
-- Kaempfer-Aussehen: Frisur, Bart, Gesicht, Hautton, Haarfarbe. Gespeichert im Profil (CC_Profile, Attribut CC_Look als JSON).
-- Vorlagen: ServerStorage.CC_Custom.<Variante> (skinned MeshParts aus export/Fighter_Custom_v01.fbx, eingerichtet von
-- setup_custom_v01.luau; jedes Teil hat Attribut CC_C0 = Versatz zum HumanoidRootPart wie die Motor6D des Basis-Charakters).
-- Ohne Vorlagen (noch nicht importiert) wirken nur Hautton und Haarfarbe auf die vorhandenen Teile.
-- Client -> Server: ReplicatedStorage.CC_Look (RemoteEvent) mit { hair, beard, face, skin, hairColor }.
-- Auswahl fuer das Menue: ReplicatedStorage.CC_LookOptions (Attribute Hair, Beard, Face als Komma-Listen, SkinCount, HairColorCount).
local Players = game:GetService("Players")
local HS = game:GetService("HttpService")
local SS = game:GetService("ServerStorage")
local RS = game.ReplicatedStorage

local HAIR = { "Hair_QuiffV03", "Hair_Buzzcut", "Hair_SidePart", "Hair_ShortCurls" }
local BEARD = { "none", "Beard_Short", "Beard_Full" }
local FACE = { "Face_Focused", "Face_Neutral", "Face_Friendly" }
local SKIN = { Color3.fromRGB(232, 194, 166), Color3.fromRGB(184, 148, 123), Color3.fromRGB(140, 98, 70), Color3.fromRGB(92, 62, 44) }
local HAIRCOL = { Color3.fromRGB(38, 32, 28), Color3.fromRGB(78, 52, 34), Color3.fromRGB(128, 86, 50), Color3.fromRGB(205, 168, 104),
	Color3.fromRGB(150, 62, 30), Color3.fromRGB(150, 150, 150) }

local remote = RS:FindFirstChild("CC_Look") or Instance.new("RemoteEvent"); remote.Name = "CC_Look"; remote.Parent = RS
local opts = RS:FindFirstChild("CC_LookOptions") or Instance.new("Folder"); opts.Name = "CC_LookOptions"; opts.Parent = RS
opts:SetAttribute("Hair", table.concat(HAIR, ",")); opts:SetAttribute("Beard", table.concat(BEARD, ",")); opts:SetAttribute("Face", table.concat(FACE, ","))
opts:SetAttribute("SkinCount", #SKIN); opts:SetAttribute("HairColorCount", #HAIRCOL)

local function find(list, v) for _, x in ipairs(list) do if x == v then return true end end return false end
local function templates() return SS:FindFirstChild("CC_Custom") end
local function isHead(name) return name:sub(1, 5) == "Hair_" or name:sub(1, 6) == "Beard_" or name:sub(1, 5) == "Face_" end

local function apply(char, look)
	local hrp = char and char:FindFirstChild("HumanoidRootPart")
	if not hrp or type(look) ~= "table" then return end
	local tpl = templates()
	if tpl then
		-- alte Kopfteile entfernen, gewaehlte Varianten einsetzen
		for _, p in ipairs(char:GetChildren()) do if p:IsA("BasePart") and isHead(p.Name) then p:Destroy() end end
		for _, v in ipairs({ look.hair, look.beard ~= "none" and look.beard or nil, look.face }) do
			local folder = v and tpl:FindFirstChild(v)
			if folder then
				for _, t in ipairs(folder:GetChildren()) do
					if t:IsA("BasePart") then
						local p = t:Clone()
						p.Anchored = false; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.Massless = true
						local m = Instance.new("Motor6D"); m.Name = p.Name .. "Motor6D"
						m.Part0 = hrp; m.Part1 = p; m.C0 = t:GetAttribute("CC_C0") or CFrame.new(); m.Parent = p
						p.Parent = char
					end
				end
			end
		end
	end
	-- Farben
	local skin = SKIN[look.skin] or SKIN[2]
	local hc = HAIRCOL[look.hairColor] or HAIRCOL[1]
	local body = char:FindFirstChild("Fighter_Body"); if body then body.Color = skin end
	for _, p in ipairs(char:GetChildren()) do
		if p:IsA("BasePart") then
			if p.Name:sub(1, 5) == "Hair_" or p.Name:sub(1, 6) == "Beard_" or p.Name:find("_Brow_") then p.Color = hc end
		end
	end
end

local function lookOf(plr)
	local ok, t = pcall(function() return HS:JSONDecode(plr:GetAttribute("CC_Look") or "") end)
	return ok and type(t) == "table" and t or nil
end
local function hook(plr)
	local function onChar(char)
		char:WaitForChild("HumanoidRootPart")
		task.wait(0.2)
		local l = lookOf(plr); if l then apply(char, l) end
	end
	plr.CharacterAdded:Connect(onChar)
	if plr.Character then task.spawn(onChar, plr.Character) end
	plr:GetAttributeChangedSignal("CC_Look"):Connect(function()
		local l = lookOf(plr); if l and plr.Character then apply(plr.Character, l) end
	end)
end
Players.PlayerAdded:Connect(hook)
for _, plr in ipairs(Players:GetPlayers()) do hook(plr) end

remote.OnServerEvent:Connect(function(plr, t)
	if type(t) ~= "table" then return end
	local c = plr.Character
	if c and (c:GetAttribute("CC_Opponent") or c:GetAttribute("CC_Wrestle")) then return end   -- nicht waehrend eines Kampfs
	local look = {}
	if type(t.hair) == "string" and find(HAIR, t.hair) then look.hair = t.hair end
	if type(t.beard) == "string" and find(BEARD, t.beard) then look.beard = t.beard end
	if type(t.face) == "string" and find(FACE, t.face) then look.face = t.face end
	if type(t.skin) == "number" and SKIN[t.skin] then look.skin = t.skin end
	if type(t.hairColor) == "number" and HAIRCOL[t.hairColor] then look.hairColor = t.hairColor end
	local ev = SS:FindFirstChild("CC_ProfileEvent")
	if ev then ev:Fire(plr, "look", look) end
end)
