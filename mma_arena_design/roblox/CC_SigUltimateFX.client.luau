-- StarterPlayer.StarterPlayerScripts.CC_SigUltimateFX
-- Zusaetzliche Effekte der Signaturen (nur Optik, alles lokal; Regeln und Schaden bleiben auf dem Server):
--   Tyson  "PEEK-A-BOO KOMBINATION": dunkelrote Aura waehrend der Kombination; Uppercut-Treffer im Anime-Stil:
--          Schweiss-Spritzer, Luft-Schockwelle, Impact-Frame (kurz schwarz-weiss), Speedlines, Kamera-Stoss.
--   Ali    "INSTINKT-MODUS": silbrig-blaue Aura fuer die Dauer des Modus, Anzeige mit Restzeit und Ausweich-Punkten,
--          Nachbild beim automatischen Ausweichen, Calf-Kick-Einschlag am Bein (Druckwelle, roter Rand beim Getroffenen).
-- Ereignisse kommen ueber ReplicatedStorage.CC_SigFX (start, hit, dodge, calf, instinct_end, cancel).
-- Bildschirm-Effekte nur fuer Angreifer/Getroffenen; Attribut CC_ReduceFX am Spieler schaltet sie ab.
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Lighting = game:GetService("Lighting")
local Debris = game:GetService("Debris")
local player = Players.LocalPlayer
local fx = RS:WaitForChild("CC_SigFX")
local SIG = require(RS:WaitForChild("CC_Signatures"))

local SMOKE = "rbxasset://textures/particles/smoke_main.dds"
local SPARK = "rbxasset://textures/particles/sparkles_main.dds"

local function reduced() return player:GetAttribute("CC_ReduceFX") == true end
local function involved(...) local me = player.Character; for _, c in ipairs({ ... }) do if c and c == me then return true end end return false end
local function sound(name, vol, pitch, at)
	local src = game:GetService("SoundService"):FindFirstChild("CC_Sounds"); src = src and src:FindFirstChild(name)
	if not src then return end
	local s = src:Clone(); s.Volume = vol or src.Volume; s.PlaybackSpeed = pitch or 1
	if at then
		local a = Instance.new("Attachment"); a.WorldPosition = at; a.Parent = workspace.Terrain; s.Parent = a; Debris:AddItem(a, 4)
	else s.Parent = workspace end
	s:Play(); Debris:AddItem(s, 4)
end
local function bonePos(char, name)
	local b = char and char:FindFirstChild(name, true)
	return b and b:IsA("Bone") and b.WorldPosition or (char and char:FindFirstChild("HumanoidRootPart") and char.HumanoidRootPart.Position)
end

-- ---------- Aura (Partikel am Koerper + Licht) ----------
local auras = {}                      -- [char] = { parts..., untilT }
local function stopAura(char)
	local a = auras[char]; if not a then return end
	auras[char] = nil
	for _, e in ipairs(a.emitters) do e.Enabled = false end
	if a.outline then TweenService:Create(a.outline, TweenInfo.new(0.35), { FillTransparency = 1, OutlineTransparency = 1 }):Play() end
	if a.light then TweenService:Create(a.light, TweenInfo.new(0.4), { Brightness = 0 }):Play() end
	task.delay(1.2, function() for _, o in ipairs(a.objects) do o:Destroy() end end)
end
local function startAura(char, style, duration)
	local hrp = char and char:FindFirstChild("HumanoidRootPart"); if not hrp then return end
	stopAura(char)
	local a = { emitters = {}, objects = {} }
	-- Koerper-Volumen (unsichtbar, an der Huefte festgeschweisst): Partikel steigen aus der ganzen Figur auf, nicht aus einem Punkt
	local vol = Instance.new("Part"); vol.Name = "CC_AuraVolume"; vol.Size = Vector3.new(2.4, 5.6, 1.4); vol.Transparency = 1
	vol.CanCollide = false; vol.CanQuery = false; vol.CanTouch = false; vol.Massless = true; vol.CastShadow = false
	vol.CFrame = hrp.CFrame * CFrame.new(0, 0.2, 0); vol.Parent = char
	local w = Instance.new("WeldConstraint"); w.Part0 = hrp; w.Part1 = vol; w.Parent = vol
	table.insert(a.objects, vol)
	local att = vol
	-- leuchtender Umriss um die ganze Figur
	local hl = Instance.new("Highlight"); hl.Name = "CC_AuraOutline"; hl.Adornee = char; hl.DepthMode = Enum.HighlightDepthMode.Occluded
	hl.FillColor = style == "tyson" and Color3.fromRGB(120, 0, 10) or Color3.fromRGB(190, 215, 255)
	hl.OutlineColor = style == "tyson" and Color3.fromRGB(255, 40, 40) or Color3.fromRGB(225, 240, 255)
	hl.FillTransparency = 1; hl.OutlineTransparency = 1; hl.Parent = char
	TweenService:Create(hl, TweenInfo.new(0.15), { FillTransparency = 0.82, OutlineTransparency = 0 }):Play()
	a.outline = hl; table.insert(a.objects, hl)
	local function emitter(props)
		local e = Instance.new("ParticleEmitter")
		for k, v in pairs(props) do e[k] = v end
		e.Parent = att; table.insert(a.emitters, e); table.insert(a.objects, e)
	end
	if style == "tyson" then
		-- dunkelrote, schwere Flammen-Aura, steigt langsam, dazu Funken
		emitter({ Texture = SMOKE, Color = ColorSequence.new(Color3.fromRGB(200, 20, 30), Color3.fromRGB(40, 0, 6)), LightEmission = 0.35,
			Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1.9), NumberSequenceKeypoint.new(1, 0.4) }),
			Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.25), NumberSequenceKeypoint.new(1, 1) }),
			Lifetime = NumberRange.new(0.45, 0.8), Rate = 150, Shape = Enum.ParticleEmitterShape.Box, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume, Speed = NumberRange.new(4, 7), SpreadAngle = Vector2.new(18, 18),
			EmissionDirection = Enum.NormalId.Top,
			Acceleration = Vector3.new(0, 4, 0), RotSpeed = NumberRange.new(-90, 90), LockedToPart = false })
		emitter({ Texture = SPARK, Color = ColorSequence.new(Color3.fromRGB(255, 70, 50)), LightEmission = 1,
			Size = NumberSequence.new(0.25, 0), Lifetime = NumberRange.new(0.3, 0.5), Rate = 30, Speed = NumberRange.new(6, 10),
			SpreadAngle = Vector2.new(35, 35), EmissionDirection = Enum.NormalId.Top })
		local light = Instance.new("PointLight"); light.Color = Color3.fromRGB(220, 40, 40); light.Range = 12; light.Brightness = 0; light.Parent = hrp
		TweenService:Create(light, TweenInfo.new(0.2), { Brightness = 2.2 }):Play()
		a.light = light; table.insert(a.objects, light)
	else -- ali: silbrig-blaue, ruhige Aura, nach oben fliessend
		emitter({ Texture = SMOKE, Color = ColorSequence.new(Color3.fromRGB(235, 242, 255), Color3.fromRGB(110, 150, 255)), LightEmission = 0.8,
			Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1.4), NumberSequenceKeypoint.new(1, 0.2) }),
			Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(1, 1) }),
			Lifetime = NumberRange.new(0.6, 1.0), Rate = 110, Shape = Enum.ParticleEmitterShape.Box, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume, Speed = NumberRange.new(3, 5), SpreadAngle = Vector2.new(12, 12),
			EmissionDirection = Enum.NormalId.Top, Acceleration = Vector3.new(0, 3, 0), RotSpeed = NumberRange.new(-40, 40) })
		emitter({ Texture = SPARK, Color = ColorSequence.new(Color3.fromRGB(200, 225, 255)), LightEmission = 1,
			Size = NumberSequence.new(0.18, 0), Lifetime = NumberRange.new(0.5, 0.9), Rate = 18, Speed = NumberRange.new(1, 3),
			SpreadAngle = Vector2.new(180, 180) })
		local light = Instance.new("PointLight"); light.Color = Color3.fromRGB(170, 200, 255); light.Range = 14; light.Brightness = 0; light.Parent = hrp
		TweenService:Create(light, TweenInfo.new(0.3), { Brightness = 2.6 }):Play()
		a.light = light; table.insert(a.objects, light)
	end
	auras[char] = a
	if duration then task.delay(duration, function() if auras[char] == a then stopAura(char) end end) end
end

-- ---------- Welt-Effekte ----------
local function burst(at, props, count, life)
	local p = Instance.new("Part"); p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
	p.Transparency = 1; p.Size = Vector3.new(0.2, 0.2, 0.2); p.CFrame = CFrame.new(at); p.Parent = workspace
	local e = Instance.new("ParticleEmitter")
	for k, v in pairs(props) do e[k] = v end
	e.Enabled = false; e.Parent = p; e:Emit(count)
	Debris:AddItem(p, life or 2)
end
local function shockwave(at, normal, color, size, time)
	local ring = Instance.new("Part"); ring.Shape = Enum.PartType.Cylinder; ring.Anchored = true; ring.CanCollide = false; ring.CanQuery = false
	ring.CanTouch = false; ring.CastShadow = false; ring.Material = Enum.Material.Neon; ring.Color = color; ring.Transparency = 0.25
	ring.Size = Vector3.new(0.08, 0.6, 0.6)
	ring.CFrame = CFrame.lookAt(at, at + normal) * CFrame.Angles(0, math.rad(90), 0)
	ring.Parent = workspace
	TweenService:Create(ring, TweenInfo.new(time or 0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(0.02, size, size), Transparency = 1 }):Play()
	Debris:AddItem(ring, (time or 0.35) + 0.1)
end
local function afterimage(char)
	if not char then return end
	local folder = Instance.new("Folder"); folder.Name = "CC_Afterimage"; folder.Parent = workspace
	for _, d in ipairs(char:GetDescendants()) do
		if d:IsA("MeshPart") and d.Transparency < 1 then
			local c = Instance.new("Part"); c.Anchored = true; c.CanCollide = false; c.CanQuery = false; c.CanTouch = false; c.CastShadow = false
			c.Material = Enum.Material.Neon; c.Color = Color3.fromRGB(190, 215, 255); c.Transparency = 0.55
			c.Size = d.Size; c.CFrame = d.CFrame; c.Parent = folder
			TweenService:Create(c, TweenInfo.new(0.45), { Transparency = 1, Size = d.Size * 1.08 }):Play()
		end
	end
	Debris:AddItem(folder, 0.6)
end

-- ---------- Bildschirm (Anime-Impact) ----------
local screen = Instance.new("ScreenGui"); screen.Name = "CC_SigUltimateGui"; screen.IgnoreGuiInset = true; screen.ResetOnSpawn = false
screen.DisplayOrder = 35; screen.Parent = player:WaitForChild("PlayerGui")
local function speedlines(dur, color)
	local holder = Instance.new("Frame"); holder.BackgroundTransparency = 1; holder.Size = UDim2.fromScale(1, 1); holder.Parent = screen
	-- Linien quer durch die Bildmitte (drehen um ihre Mitte = Bildmitte); innen durchsichtig, aussen sichtbar
	for i = 1, 18 do
		local ang = (i / 18) * 180 + math.random(-5, 5)
		local l = Instance.new("Frame"); l.BorderSizePixel = 0; l.BackgroundColor3 = color or Color3.new(1, 1, 1)
		l.AnchorPoint = Vector2.new(0.5, 0.5); l.Position = UDim2.fromScale(0.5, 0.5); l.Rotation = ang
		l.Size = UDim2.new(2.2, 0, 0, math.random(2, 5)); l.BackgroundTransparency = 0.15; l.Parent = holder
		local g = Instance.new("UIGradient")
		g.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.3, 0.3), NumberSequenceKeypoint.new(0.4, 1),
			NumberSequenceKeypoint.new(0.6, 1), NumberSequenceKeypoint.new(0.7, 0.3), NumberSequenceKeypoint.new(1, 0) })
		g.Parent = l
		TweenService:Create(l, TweenInfo.new(dur), { BackgroundTransparency = 1 }):Play()
	end
	Debris:AddItem(holder, dur + 0.05)
end
local function impactFrame(strength)
	-- 2 Frames schwarz-weiss mit hohem Kontrast (klassischer Anime-Impact-Frame), dann zurueck
	local cc = Instance.new("ColorCorrectionEffect"); cc.Name = "CC_ImpactFrame"
	cc.Saturation = -1; cc.Contrast = 0.9 * strength; cc.Brightness = 0.12 * strength; cc.Parent = Lighting
	task.delay(0.09, function()
		TweenService:Create(cc, TweenInfo.new(0.18), { Saturation = 0, Contrast = 0, Brightness = 0 }):Play()
		Debris:AddItem(cc, 0.25)
	end)
end
local function fovPunch(amount)
	local cam = workspace.CurrentCamera; local base = cam.FieldOfView
	cam.FieldOfView = base - amount
	TweenService:Create(cam, TweenInfo.new(0.35, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { FieldOfView = base }):Play()
end
local function redEdge(dur)
	local f = Instance.new("Frame"); f.BackgroundColor3 = Color3.fromRGB(170, 0, 0); f.BackgroundTransparency = 0.55; f.BorderSizePixel = 0
	f.Size = UDim2.fromScale(1, 1); f.Parent = screen
	local g = Instance.new("UIGradient"); g.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.25, 1), NumberSequenceKeypoint.new(0.75, 1), NumberSequenceKeypoint.new(1, 0) }); g.Parent = f
	local g2 = f:Clone(); g2.UIGradient.Rotation = 90; g2.Parent = screen
	for _, x in ipairs({ f, g2 }) do TweenService:Create(x, TweenInfo.new(dur), { BackgroundTransparency = 1 }):Play(); Debris:AddItem(x, dur + 0.05) end
end

-- ---------- Instinkt-Anzeige (nur fuer den Ali-Spieler selbst) ----------
local hud = Instance.new("Frame"); hud.Name = "Instinct"; hud.AnchorPoint = Vector2.new(0.5, 0); hud.Position = UDim2.new(0.5, 0, 0, 150)
hud.Size = UDim2.fromOffset(300, 46); hud.BackgroundColor3 = Color3.fromRGB(14, 18, 28); hud.BackgroundTransparency = 0.25; hud.Visible = false; hud.Parent = screen
Instance.new("UICorner", hud).CornerRadius = UDim.new(0, 6)
local hudT = Instance.new("TextLabel"); hudT.BackgroundTransparency = 1; hudT.Size = UDim2.new(1, -16, 0, 24); hudT.Position = UDim2.fromOffset(8, 3)
hudT.Font = Enum.Font.GothamBlack; hudT.TextSize = 18; hudT.TextColor3 = Color3.fromRGB(205, 225, 255); hudT.TextXAlignment = Enum.TextXAlignment.Left; hudT.Parent = hud
local bar = Instance.new("Frame"); bar.BorderSizePixel = 0; bar.BackgroundColor3 = Color3.fromRGB(170, 200, 255); bar.Position = UDim2.fromOffset(8, 32); bar.Size = UDim2.new(1, -16, 0, 6); bar.Parent = hud
local hudConn
local function showInstinctHud(char)
	if hudConn then hudConn:Disconnect() end
	hud.Visible = true
	local def = SIG.list.ali
	hudConn = RunService.RenderStepped:Connect(function()
		local untilT = char:GetAttribute("CC_Instinct")
		if not untilT or not char.Parent then hud.Visible = false; hudConn:Disconnect(); hudConn = nil return end
		local left = math.max(0, untilT - workspace:GetServerTimeNow())
		local d = char:GetAttribute("CC_InstinctDodges") or 0
		hudT.Text = ("INSTINKT  %.1f s   %s"):format(left, string.rep("◆", d) .. string.rep("◇", math.max(0, def.dodges - d)))
		bar.Size = UDim2.new(math.clamp(left / def.duration, 0, 1), -16, 0, 6)
	end)
end
local cc; local function instinctTint(on)
	if on then
		cc = cc or Instance.new("ColorCorrectionEffect"); cc.Name = "CC_InstinctTint"; cc.Parent = Lighting
		cc.TintColor = Color3.new(1, 1, 1); cc.Saturation = 0
		TweenService:Create(cc, TweenInfo.new(0.4), { TintColor = Color3.fromRGB(215, 228, 255), Saturation = -0.25 }):Play()
	elseif cc then
		local c = cc; cc = nil
		TweenService:Create(c, TweenInfo.new(0.4), { TintColor = Color3.new(1, 1, 1), Saturation = 0 }):Play(); Debris:AddItem(c, 0.5)
	end
end

-- ---------- Ereignisse ----------
fx.OnClientEvent:Connect(function(kind, char, a, b, c)
	local ok, err = pcall(function()
		if kind == "start" then
			if a == "tyson" then
				startAura(char, "tyson", SIG.list.tyson.length + 0.2)
				sound("Whoosh", 0.5, 0.7, char and char:FindFirstChild("HumanoidRootPart") and char.HumanoidRootPart.Position)
			elseif a == "ali" then
				startAura(char, "ali", SIG.list.ali.duration)
				if char == player.Character then
					showInstinctHud(char)
					if not reduced() then instinctTint(true); speedlines(0.35, Color3.fromRGB(200, 225, 255)) end
				end
			end
		elseif kind == "hit" and char and (char:GetAttribute("CC_LastSig") == "tyson" or char:GetAttribute("CC_LastSig") == "saenchai")
			and SIG.list[char:GetAttribute("CC_LastSig")] and a == #SIG.list[char:GetAttribute("CC_LastSig")].hits then
			-- letzter Treffer einer Anime-Signatur (Tyson-Uppercut, Saenchai-Rad-Kick)
			local sae = char:GetAttribute("CC_LastSig") == "saenchai"
			-- Tyson-Uppercut gelandet: Anime-Treffer
			local target = b
			local head = bonePos(target, "Head"); if not head then return end
			local up = Vector3.new(0, 1, 0)
			local from = char:FindFirstChild("HumanoidRootPart") and char.HumanoidRootPart.Position or head
			local dir = (head - from) * Vector3.new(1, 0, 1); dir = dir.Magnitude > 0 and dir.Unit or Vector3.new(0, 0, -1)
			-- Schweiss: helle Tropfen spritzen nach hinten-oben
			burst(head + Vector3.new(0, 0.6, 0), { Texture = SPARK, Color = ColorSequence.new(Color3.fromRGB(220, 240, 255)), LightEmission = 0.4,
				Size = NumberSequence.new(0.22, 0.05), Lifetime = NumberRange.new(0.4, 0.75), Speed = NumberRange.new(14, 24),
				SpreadAngle = Vector2.new(40, 40), Acceleration = Vector3.new(0, -45, 0), EmissionDirection = Enum.NormalId.Top }, 40, 1.5)
			-- Luft: weisse Druckwolke + zwei Schockwellen-Ringe in Schlagrichtung
			burst(head, { Texture = SMOKE, Color = ColorSequence.new(Color3.fromRGB(255, 255, 255)), LightEmission = 0.3,
				Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.8), NumberSequenceKeypoint.new(1, 3.2) }),
				Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(1, 1) }),
				Lifetime = NumberRange.new(0.35, 0.5), Speed = NumberRange.new(8, 14), SpreadAngle = Vector2.new(70, 70) }, 16, 1.2)
			shockwave(head, (dir + up).Unit, Color3.fromRGB(255, 255, 255), 9, 0.35)
			task.delay(0.06, function() shockwave(head, up, sae and Color3.fromRGB(255, 230, 170) or Color3.fromRGB(255, 120, 110), 6, 0.3) end)
			sound("HitHeavy", 1.2, 0.8, head)
			if involved(char, target) and not reduced() then
				impactFrame(1); speedlines(0.4); fovPunch(9)
			end
			stopAura(char)
		elseif kind == "dodge" then
			-- char = Ausweichender (Ali), a = Angreifer
			afterimage(char)
			sound("Whoosh", 0.7, 1.4, char and char:FindFirstChild("HumanoidRootPart") and char.HumanoidRootPart.Position)
			if char == player.Character and not reduced() then speedlines(0.25, Color3.fromRGB(200, 225, 255)) end
		elseif kind == "calf" then
			-- char = Ali, a = Getroffener
			local target = a
			local shin = bonePos(target, "LeftLowerLeg") or bonePos(target, "RightLowerLeg"); if not shin then return end
			shockwave(shin, Vector3.new(0, 1, 0), Color3.fromRGB(205, 225, 255), 8, 0.35)
			burst(shin, { Texture = SMOKE, Color = ColorSequence.new(Color3.fromRGB(200, 220, 255)), LightEmission = 0.5,
				Size = NumberSequence.new(0.6, 2.4), Transparency = NumberSequence.new(0.3, 1), Lifetime = NumberRange.new(0.3, 0.45),
				Speed = NumberRange.new(10, 16), SpreadAngle = Vector2.new(80, 20) }, 14, 1.2)
			sound("HitHeavy", 1.3, 0.65, shin)
			if not reduced() then
				if target == player.Character then redEdge(0.8); fovPunch(6) end
				if char == player.Character then impactFrame(0.7); speedlines(0.3, Color3.fromRGB(200, 225, 255)) end
			end
			stopAura(char)
			if char == player.Character then instinctTint(false) end
		elseif kind == "knee" then
			-- char = Ali (Knie), a = Angreifer des Takedowns (getroffen am Kopf)
			local target = a
			local head = bonePos(target, "Head"); if not head then return end
			afterimage(char)
			shockwave(head, Vector3.new(0, 1, 0), Color3.fromRGB(205, 225, 255), 8, 0.35)
			burst(head, { Texture = SPARK, Color = ColorSequence.new(Color3.fromRGB(220, 240, 255)), LightEmission = 0.5,
				Size = NumberSequence.new(0.22, 0.04), Lifetime = NumberRange.new(0.35, 0.6), Speed = NumberRange.new(12, 20),
				SpreadAngle = Vector2.new(60, 60), Acceleration = Vector3.new(0, -40, 0), EmissionDirection = Enum.NormalId.Top }, 30, 1.2)
			sound("HitHeavy", 1.3, 0.75, head)
			if not reduced() then
				if target == player.Character then redEdge(0.9); fovPunch(8) end
				if char == player.Character then impactFrame(0.8); speedlines(0.3, Color3.fromRGB(200, 225, 255)) end
			end
		elseif kind == "slam" then
			-- char = Khabib, a = Opfer (mit dem Ruecken auf die Matte geslammt)
			local target = a
			local torso = bonePos(target, "UpperTorso") or bonePos(target, "LowerTorso"); if not torso then return end
			local rp = RaycastParams.new(); rp.FilterType = Enum.RaycastFilterType.Exclude; rp.FilterDescendantsInstances = { char, target }
			local hit = workspace:Raycast(torso + Vector3.new(0, 2, 0), Vector3.new(0, -8, 0), rp)
			local ground = hit and hit.Position or (torso - Vector3.new(0, 0.6, 0))
			shockwave(ground + Vector3.new(0, 0.1, 0), Vector3.new(0, 1, 0), Color3.fromRGB(255, 120, 90), 16, 0.45)
			shockwave(ground + Vector3.new(0, 0.15, 0), Vector3.new(0, 1, 0), Color3.fromRGB(255, 235, 220), 9, 0.3)
			burst(ground, { Texture = SMOKE, Color = ColorSequence.new(Color3.fromRGB(200, 185, 165)), LightEmission = 0,
				Transparency = NumberSequence.new(0.35, 1), Size = NumberSequence.new(1.2, 3.2), Lifetime = NumberRange.new(0.6, 1.1),
				Speed = NumberRange.new(10, 18), SpreadAngle = Vector2.new(180, 8), Drag = 4, EmissionDirection = Enum.NormalId.Top }, 40, 1.6)
			burst(torso, { Texture = SPARK, Color = ColorSequence.new(Color3.fromRGB(255, 220, 200)), LightEmission = 0.5,
				Size = NumberSequence.new(0.25, 0.04), Lifetime = NumberRange.new(0.3, 0.5), Speed = NumberRange.new(14, 22),
				SpreadAngle = Vector2.new(70, 70), Acceleration = Vector3.new(0, -40, 0), EmissionDirection = Enum.NormalId.Top }, 26, 1)
			sound("HitHeavy", 1.5, 0.55, ground)
			if not reduced() then
				if target == player.Character then
					-- Opfer: Bildschirm wird roetlich (Toenung + roter Rand), klingt langsam ab
					local cc = Instance.new("ColorCorrectionEffect"); cc.Name = "CC_SlamRed"; cc.TintColor = Color3.fromRGB(255, 120, 110)
					cc.Saturation = -0.25; cc.Contrast = 0.15; cc.Parent = Lighting
					TweenService:Create(cc, TweenInfo.new(1.8, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { TintColor = Color3.new(1, 1, 1), Saturation = 0, Contrast = 0 }):Play()
					Debris:AddItem(cc, 1.9)
					redEdge(1.6); fovPunch(10)
				end
				if char == player.Character then impactFrame(0.8); fovPunch(6) end
			end
		elseif kind == "instinct_end" then
			stopAura(char)
			if char == player.Character then instinctTint(false) end
		elseif kind == "cancel" then
			if char and char:GetAttribute("CC_LastSig") == "tyson" then stopAura(char) end
		end
	end)
	if not ok then warn("[CC] SigUltimateFX: " .. tostring(err)) end
end)
-- Sicherheit: Charakter weg -> Aura und Toenung weg
player.CharacterRemoving:Connect(function(c) stopAura(c); instinctTint(false) end)
