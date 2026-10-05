-- Installiert den FigureAnimator als LocalScript in StarterPlayer/StarterPlayerScripts.
-- Ausfuehren in Roblox Studio (Command Bar oder MCP). Erneutes Ausfuehren ersetzt ihn.
local StarterPlayerScripts = game:GetService("StarterPlayer"):WaitForChild("StarterPlayerScripts")
local old = StarterPlayerScripts:FindFirstChild("FigureAnimator")
if old then old:Destroy() end
local s = Instance.new("LocalScript")
s.Name = "FigureAnimator"
s.Source = [==[
-- FigureAnimator (LocalScript in StarterPlayer/StarterPlayerScripts)
-- Animiert alle Figuren mit dem Tag "MemeFigure", die im Workspace stehen:
--   * leichtes Schweben (auf und ab) und Hin-und-her-Drehen
--   * Teile mit "FX_" im Namen (Heiligenschein, Planeten, Aepfel, Burger, Pixel ...) kreisen um die Figur
-- Laeuft nur auf dem Client (fluessig und ohne Server-Last). Figuren in ReplicatedStorage werden ignoriert.

local RunService = game:GetService("RunService")
local CollectionService = game:GetService("CollectionService")

local BOB_HEIGHT = 0.25   -- Studs auf und ab
local BOB_SPEED = 2       -- Geschwindigkeit Schweben
local SWAY_ANGLE = 0.35   -- Radiant hin und her
local SWAY_SPEED = 0.7
local FX_SPIN_SPEED = 1.2 -- Umdrehungen der Effekt-Teile (Radiant pro Sekunde)

local entries = {}

local function add(model)
	if not model:IsA("Model") or not model:IsDescendantOf(workspace) or entries[model] then
		return
	end
	local base = model:GetPivot()
	local fx = {}
	for _, part in ipairs(model:GetDescendants()) do
		if part:IsA("BasePart") and string.sub(part.Name, 1, 3) == "FX_" then
			table.insert(fx, { part = part, rel = base:ToObjectSpace(part.CFrame) })
		end
	end
	entries[model] = { base = base, last = base, fx = fx, phase = math.random() * 10 }
end

local function remove(model)
	local e = entries[model]
	if e and model.Parent then
		model:PivotTo(e.base) -- Ausgangslage wiederherstellen
		for _, f in ipairs(e.fx) do
			f.part.CFrame = e.base * f.rel
		end
	end
	entries[model] = nil
end

CollectionService:GetInstanceAddedSignal("MemeFigure"):Connect(function(model)
	task.defer(add, model) -- kurz warten, bis das Spiel die Figur positioniert hat
end)
CollectionService:GetInstanceRemovedSignal("MemeFigure"):Connect(remove)
for _, model in ipairs(CollectionService:GetTagged("MemeFigure")) do
	add(model)
end
workspace.DescendantAdded:Connect(function(inst)
	if inst:IsA("Model") and CollectionService:HasTag(inst, "MemeFigure") then
		task.defer(add, inst)
	end
end)

RunService.RenderStepped:Connect(function()
	local t = os.clock()
	for model, e in pairs(entries) do
		if not model:IsDescendantOf(workspace) then
			entries[model] = nil
			continue
		end
		-- Wurde die Figur vom Spiel verschoben (z.B. auf ein anderes Podest)? Dann neue Ausgangslage merken.
		local now = model:GetPivot()
		if (now.Position - e.last.Position).Magnitude > 2 then
			e.base = now * (e.last:Inverse() * e.base)
		end
		local tt = t + e.phase
		local cf = e.base
			* CFrame.new(0, (math.sin(tt * BOB_SPEED) + 1) * 0.5 * BOB_HEIGHT, 0)
			* CFrame.Angles(0, math.sin(tt * SWAY_SPEED) * SWAY_ANGLE, 0)
		model:PivotTo(cf)
		local spin = CFrame.Angles(0, tt * FX_SPIN_SPEED, 0)
		for _, f in ipairs(e.fx) do
			f.part.CFrame = cf * spin * f.rel
		end
		e.last = cf
	end
end)
]==]
s.Parent = StarterPlayerScripts
print("FigureAnimator installiert")
