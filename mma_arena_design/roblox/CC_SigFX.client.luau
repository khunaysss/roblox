-- StarterPlayer.StarterPlayerScripts.CC_SigFX
-- Signaturtechniken – lokale Darstellung (Werte in ReplicatedStorage.CC_Signatures). Alles nur sichtbar, nichts veraendert das Spiel:
--   * Bewegungsspur am Handschuh nur in den schnellen Schlagphasen (ab Server-Ereignis "start", zeitlich am Server ausgerichtet)
--   * Luftgeraeusch zu Beginn jedes Schlags, sobald ein Projekt-Sound CC_Sounds.Whoosh existiert (offen: passender freier Sound)
--   * bestaetigter Treffer: kurzer Akzent (Koerper klein, Uppercut etwas staerker, nicht vor dem Gesicht); Block: eigener heller Akzent
--   * Fehlschlag: nur Spur und Luftgeraeusch; Unterbrechung ("cancel"): Spuren sofort aus, nichts kommt verspaetet nach
--   * Finisher: nur wenn der Server einen K.o. durch eine Signatur bestaetigt hat (CC_MatchState.State = "finisher", Attribut Finisher).
--     Wiedergabe der letzten Aktion mit LOKALEN Kopien der beiden Kaempfer aus einer laufenden Aufzeichnung der Knochen-Stellungen
--     (keine erneuten Treffer, kein Schaden, keine Physik), seitliche Nahaufnahme, kurze Zeitlupe am Kontakt. Ueberspringen mit
--     Leertaste, Ruecktaste oder Klick beendet nur die eigene Darstellung. Fehlt etwas, geht es direkt zur Ergebnisanzeige.
-- Intensive Effekte abschaltbar: Attribut CC_ReduceFX am Spieler (vorbereitet fuer Einstellungen).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local UIS = game:GetService("UserInputService")
local HS = game:GetService("HttpService")
local RS = game.ReplicatedStorage
local player = Players.LocalPlayer
local SIG = require(RS:WaitForChild("CC_Signatures"))
local fx = RS:WaitForChild("CC_SigFX")
local ms = RS:WaitForChild("CC_MatchState")
local cam = workspace.CurrentCamera
local function now() return workspace:GetServerTimeNow() end
local function reduced() return player:GetAttribute("CC_ReduceFX") == true end
local fxFolder = Instance.new("Folder"); fxFolder.Name = "CC_SigFXLocal"; fxFolder.Parent = workspace

local function boneOf(char, name)
	local hrp = char and char:FindFirstChild("HumanoidRootPart")
	return hrp and hrp:FindFirstChild(name, true)
end

---------------------------------------------------------------------------------------------------
-- Bewegungsspur: zwei lokale Hilfs-Bones am Hand-Bone, Trail dazwischen; nur waehrend der Zeitfenster aktiv
---------------------------------------------------------------------------------------------------
local trails = {}              -- [char] = { token, list of trails }
local function trailFor(char, boneName, color)
	local b = boneOf(char, boneName); if not b then return nil end
	local key = "CC_SigTrail_" .. boneName
	local tr = b:FindFirstChild(key)
	if not tr then
		local a0 = Instance.new("Bone"); a0.Name = key .. "_A"; a0.CFrame = CFrame.new(0, 0.25, 0); a0.Parent = b
		local a1 = Instance.new("Bone"); a1.Name = key .. "_B"; a1.CFrame = CFrame.new(0, 0.75, 0); a1.Parent = b
		tr = Instance.new("Trail"); tr.Name = key; tr.Attachment0 = a0; tr.Attachment1 = a1
		tr.Lifetime = 0.14; tr.MinLength = 0.05; tr.FaceCamera = true; tr.LightEmission = 0.2; tr.Enabled = false
		tr.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.25), NumberSequenceKeypoint.new(1, 1) })
		tr.WidthScale = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(1, 0.2) })
		tr.Parent = b
	end
	tr.Color = ColorSequence.new(color)
	return tr
end
local function swoosh(char, pitch)
	local hrp = char and char:FindFirstChild("HumanoidRootPart"); if not hrp then return end
	-- Luftgeraeusch nur mit vorhandenem Projekt-Sound SoundService.CC_Sounds.Whoosh (eingebauter Roblox-Swoosh ist nicht freigegeben)
	local src = game:GetService("SoundService"):FindFirstChild("CC_Sounds") and game:GetService("SoundService").CC_Sounds:FindFirstChild("Whoosh")
	if not src then return end
	local s = src:Clone(); s.Volume = 0.45; s.PlaybackSpeed = pitch or 1
	s.RollOffMaxDistance = 80; s.Parent = hrp; s:Play()
	game:GetService("Debris"):AddItem(s, 1.5)
end
local function stopTrails(char)
	local e = trails[char]; if not e then return end
	e.token += 1
	for _, tr in ipairs(e.list) do tr.Enabled = false end
end
local function startSig(char, id, startAt)
	local def = SIG.list[id]; if not (def and char) then return end
	trails[char] = trails[char] or { token = 0, list = {} }
	local e = trails[char]; e.token += 1
	local token = e.token
	for _, w in ipairs(def.trails) do
		local tr = trailFor(char, w.bone, def.color)
		if tr then
			table.insert(e.list, tr)
			task.delay(math.max(0, startAt + w.t[1] - now()), function()
				if e.token ~= token or not char.Parent then return end
				tr.Enabled = true; swoosh(char, 0.95 + math.random() * 0.15)
				task.delay(w.t[2] - w.t[1], function() if e.token == token then tr.Enabled = false end end)
			end)
		end
	end
end

---------------------------------------------------------------------------------------------------
-- Trefferakzente (kurz, kein Blut): Koerper klein, Uppercut staerker und unter dem Kinn; Block hell und flach
---------------------------------------------------------------------------------------------------
local function flash(pos, size, color, life, shape)
	local p = Instance.new("Part"); p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	p.Material = Enum.Material.Neon; p.Color = color; p.Shape = shape or Enum.PartType.Ball
	p.Size = Vector3.new(size, size, size) * 0.5; p.Transparency = 0.15; p.CFrame = pos; p.Parent = fxFolder
	TweenService:Create(p, TweenInfo.new(life, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(size, size, size), Transparency = 1 }):Play()
	game:GetService("Debris"):AddItem(p, life + 0.05)
end
local function impact(attacker, target, idx, blocked)
	local hrpA, ut = attacker and attacker:FindFirstChild("HumanoidRootPart"), boneOf(target, "UpperTorso")
	if not (hrpA and ut) then return end
	local d = SIG.list[attacker:GetAttribute("CC_LastSig") or ""]
	local h = (d and d.hits[idx]) or { zone = "body", impact = 1 }
	local c = ut.TransformedWorldCFrame
	local toward = (hrpA.Position - c.Position) * Vector3.new(1, 0, 1)
	toward = toward.Magnitude > 0.01 and toward.Unit or Vector3.new(0, 0, 1)
	local k = reduced() and 0.6 or 1
	if blocked then
		local at = c.Position + c.UpVector * 1.3 + toward * 0.9
		flash(CFrame.lookAt(at, at + toward) * CFrame.Angles(0, math.rad(90), 0), 1.6 * k, Color3.fromRGB(200, 225, 255), 0.12, Enum.PartType.Cylinder)
	elseif h.zone == "head" then
		local at = c.Position + c.UpVector * 0.95 + toward * 0.85      -- unter dem Kinn, vor dem Hals (Gesicht bleibt frei)
		flash(CFrame.new(at), 1.5 * (h.impact or 1) * k, Color3.fromRGB(255, 120, 70), 0.16)
		flash(CFrame.new(at), 0.8 * k, Color3.fromRGB(255, 240, 220), 0.08)
	else
		local at = c.Position + c.UpVector * 0.4 + toward * 0.7
		flash(CFrame.new(at), 1.1 * (h.impact or 1) * k, Color3.fromRGB(190, 40, 40), 0.13)
	end
end

fx.OnClientEvent:Connect(function(kind, char, a, b)
	if kind == "start" then
		if char then char:SetAttribute("CC_LastSig", a) end
		startSig(char, a, b)
	elseif kind == "hit" then impact(char, b, a, false)
	elseif kind == "block" then impact(char, b, a, true)
	elseif kind == "cancel" then stopTrails(char) end
	-- "miss": nur Spur und Luftgeraeusch (schon gelaufen)
end)

---------------------------------------------------------------------------------------------------
-- Aufzeichnung fuer die Finisher-Wiederholung: Knochen-Stellungen beider Kaempfer der letzten 4 s (nur im Kampf)
---------------------------------------------------------------------------------------------------
local BUF_SEC = 4
local rec = {}                 -- [char] = { bones = {Bone}, frames = { {t, root=CFrame, tr={CFrame}} } }
local function fighterChars()
	local out = {}
	local r, b = ms:GetAttribute("RedName"), ms:GetAttribute("BlueName")
	for _, n in ipairs({ r, b }) do
		local c = n and n ~= "" and workspace:FindFirstChild(n)
		if c then table.insert(out, c) end
	end
	if (ms:GetAttribute("Mode") == "training" or ms:GetAttribute("Mode") == "sparring") then
		local d = workspace:FindFirstChild("CC_TrainingDummy"); if d then table.insert(out, d) end
	end
	return out
end
RunService.Heartbeat:Connect(function()
	local st = ms:GetAttribute("State")
	if st ~= "fight" and st ~= "over" and st ~= "finisher" then if next(rec) then rec = {} end return end
	if st == "finisher" then return end                    -- waehrend der Wiedergabe nicht weiter aufzeichnen
	local t = now()
	for _, c in ipairs(fighterChars()) do
		local hrp = c:FindFirstChild("HumanoidRootPart")
		if hrp then
			local r = rec[c]
			if not r then
				r = { bones = {}, frames = {} }
				for _, d in ipairs(hrp:GetDescendants()) do if d:IsA("Bone") and not d.Name:find("^CC_SigTrail") then table.insert(r.bones, d) end end
				rec[c] = r
			end
			local tr = table.create(#r.bones)
			for i, bn in ipairs(r.bones) do tr[i] = bn.Transform end
			table.insert(r.frames, { t = t, root = hrp.CFrame, tr = tr })
			while #r.frames > 0 and r.frames[1].t < t - BUF_SEC do table.remove(r.frames, 1) end
		end
	end
end)

---------------------------------------------------------------------------------------------------
-- Finisher-Wiedergabe
---------------------------------------------------------------------------------------------------
local playing = false
local function sampleAt(r, t)
	local fr = r.frames
	if #fr == 0 then return nil end
	if t <= fr[1].t then return fr[1], fr[1], 0 end
	for i = 2, #fr do
		if fr[i].t >= t then local a, b = fr[i - 1], fr[i]; return a, b, (t - a.t) / math.max(b.t - a.t, 1e-4) end
	end
	return fr[#fr], fr[#fr], 0
end
local function cloneFor(char)
	local old = char.Archivable
	char.Archivable = true
	local ok, c = pcall(function() return char:Clone() end)
	char.Archivable = old
	if not ok or not c then return nil end
	for _, d in ipairs(c:GetDescendants()) do
		if d:IsA("Script") or d:IsA("LocalScript") or d:IsA("Animator") or d:IsA("Trail") or d:IsA("ProximityPrompt") or d:IsA("BillboardGui") then d:Destroy()
		elseif d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false end
	end
	local hum = c:FindFirstChildOfClass("Humanoid")
	if hum then hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None end
	c.Name = "CC_Replay_" .. char.Name
	c.Parent = fxFolder
	return c
end
local function setHidden(char, on)
	for _, d in ipairs(char:GetDescendants()) do
		if d:IsA("BasePart") or d:IsA("Decal") then d.LocalTransparencyModifier = on and 1 or 0 end
	end
end
local function playFinisher()
	if playing then return end
	local okj, info = pcall(function() return HS:JSONDecode(ms:GetAttribute("Finisher") or "") end)
	if not okj or type(info) ~= "table" then return end
	local A, T = workspace:FindFirstChild(info.attacker), workspace:FindFirstChild(info.target)
	local ra, rt = A and rec[A], T and rec[T]
	local F = SIG.FINISHER
	local t0, t1 = info.impact - F.before, info.impact + F.after
	if not (ra and rt and #ra.frames > 5 and #rt.frames > 5 and ra.frames[1].t <= t0 + 0.3) then return end   -- keine Aufzeichnung: direkt Ergebnis
	playing = true
	local ca, ct = cloneFor(A), cloneFor(T)
	if not (ca and ct) then if ca then ca:Destroy() end; if ct then ct:Destroy() end; playing = false; return end
	local function bonesOf(c, ref)
		local out = {}
		local hrp = c:FindFirstChild("HumanoidRootPart")
		for i, b in ipairs(ref.bones) do out[i] = hrp and hrp:FindFirstChild(b.Name, true) end
		return out
	end
	local ba, bt = bonesOf(ca, ra), bonesOf(ct, rt)
	setHidden(A, true); setHidden(T, true)
	local hud = player.PlayerGui:FindFirstChild("CC_HUD"); local hudWas = hud and hud.Enabled
	if hud then hud.Enabled = false end
	player:SetAttribute("CC_UIBlock", true)
	-- Balken oben/unten (Kino), Hinweis zum Ueberspringen
	local gui = Instance.new("ScreenGui"); gui.Name = "CC_FinisherGui"; gui.IgnoreGuiInset = true; gui.DisplayOrder = 30; gui.Parent = player.PlayerGui
	for _, top in ipairs({ true, false }) do
		local f = Instance.new("Frame"); f.BackgroundColor3 = Color3.new(0, 0, 0); f.BorderSizePixel = 0; f.Size = UDim2.new(1, 0, 0, 0)
		f.AnchorPoint = Vector2.new(0, top and 0 or 1); f.Position = UDim2.fromScale(0, top and 0 or 1); f.Parent = gui
		TweenService:Create(f, TweenInfo.new(0.25), { Size = UDim2.new(1, 0, 0.11, 0) }):Play()
	end
	local tag = Instance.new("TextLabel"); tag.BackgroundTransparency = 1; tag.AnchorPoint = Vector2.new(1, 1); tag.Position = UDim2.new(1, -28, 1, -14)
	tag.Size = UDim2.fromOffset(360, 30); tag.Font = Enum.Font.GothamBold; tag.TextSize = 16; tag.TextColor3 = Color3.fromRGB(200, 200, 205)
	tag.TextXAlignment = Enum.TextXAlignment.Right; tag.Text = "SPACE  Skip"; tag.Parent = gui
	local title = Instance.new("TextLabel"); title.BackgroundTransparency = 1; title.AnchorPoint = Vector2.new(0, 1); title.Position = UDim2.new(0, 28, 1, -12)
	title.Size = UDim2.fromOffset(500, 36); title.Font = Enum.Font.GothamBlack; title.TextSize = 26; title.TextColor3 = Color3.fromRGB(214, 36, 46)
	title.TextXAlignment = Enum.TextXAlignment.Left; title.Text = (SIG.list[info.sig] and SIG.list[info.sig].name or "FINISHER"); title.Parent = gui
	local camType, camCF = cam.CameraType, cam.CFrame
	cam.CameraType = Enum.CameraType.Scriptable
	local skip = false
	local c1 = UIS.InputBegan:Connect(function(input)
		if input.KeyCode == Enum.KeyCode.Space or input.KeyCode == Enum.KeyCode.Backspace or input.KeyCode == Enum.KeyCode.ButtonA
			or input.KeyCode == Enum.KeyCode.ButtonB or input.UserInputType == Enum.UserInputType.MouseButton1 then skip = true end
	end)
	local simT, impactShown = t0, false
	local done = false
	local function finish()
		if done then return end
		done = true
		c1:Disconnect()
		RunService:UnbindFromRenderStep("CC_Finisher")
		if ca then ca:Destroy() end; if ct then ct:Destroy() end
		if A.Parent then setHidden(A, false) end; if T.Parent then setHidden(T, false) end
		if hud then hud.Enabled = hudWas end
		player:SetAttribute("CC_UIBlock", nil)
		gui:Destroy()
		cam.CameraType = Enum.CameraType.Custom
		local h = player.Character and player.Character:FindFirstChildOfClass("Humanoid"); if h then cam.CameraSubject = h end
		playing = false
	end
	local wall = os.clock()
	RunService:BindToRenderStep("CC_Finisher", Enum.RenderPriority.Camera.Value + 20, function(dt)
		if skip or ms:GetAttribute("State") ~= "finisher" or not (A.Parent and T.Parent) or os.clock() - wall > F.total + 0.5 then finish() return end
		local rel = simT - info.impact
		local rate = (rel > F.slowFrom and rel < F.slowTo) and F.slowRate or 1
		simT = math.min(t1, simT + dt * rate)
		for _, pair in ipairs({ { ca, ra, ba }, { ct, rt, bt } }) do
			local c, r, bones = pair[1], pair[2], pair[3]
			local fa, fb, u = sampleAt(r, simT)
			if fa then
				local hrp = c:FindFirstChild("HumanoidRootPart")
				if hrp then c:PivotTo(fa.root:Lerp(fb.root, u)) end
				for i, bn in ipairs(bones) do if bn then bn.Transform = fa.tr[i]:Lerp(fb.tr[i], u) end end
			end
		end
		if not impactShown and simT >= info.impact then
			impactShown = true
			local hit = SIG.list[info.sig] and SIG.list[info.sig].hits
			impact(ca, ct, hit and #hit or 1, false)
		end
		-- Kamera: seitlich zur Linie der beiden Kaempfer, nah, Blick auf den Kontakt
		local pa, pt = ca:GetPivot().Position, ct:GetPivot().Position
		local line = (pt - pa) * Vector3.new(1, 0, 1); line = line.Magnitude > 0.1 and line.Unit or Vector3.new(0, 0, -1)
		local side = Vector3.new(-line.Z, 0, line.X)
		local focus = (pa + pt) / 2 + Vector3.new(0, 1.6, 0)
		cam.CFrame = CFrame.lookAt(focus + side * 9 + Vector3.new(0, 1.2, 0) - line * 1.0, focus)
		if simT >= t1 then finish() end
	end)
end
ms:GetAttributeChangedSignal("State"):Connect(function()
	if ms:GetAttribute("State") == "finisher" then task.defer(playFinisher) end
end)
-- Aufraeumen bei Respawn: keine uebrig gebliebenen Spuren
player.CharacterAdded:Connect(function() for c in pairs(trails) do if not c.Parent then trails[c] = nil end end end)
