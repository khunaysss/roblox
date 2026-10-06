-- Verkehr fuer die Autobahn (LocalScript in StarterPlayer > StarterPlayerScripts)
--
-- Braucht:
--   workspace.Autobahn                     importierte Strecke (mit Teil "TrackOrigin")
--   ReplicatedStorage.TrackLanes           ModuleScript aus export/TrackLanes.lua
--   ReplicatedStorage.TrafficCars          Ordner mit den importierten Auto-Models
--                                          (Limousine, SUV, Kompakt, Sportwagen, Transporter, LKW)
--
-- Jedes Auto faehrt mit fester Geschwindigkeit auf seiner Spur, die Abstaende bleiben also immer
-- gleich gross -> es gibt immer Luecken zum Durchcutten. Die Positionen werden aus der Serverzeit
-- berechnet, darum sehen alle Spieler denselben Verkehr, ohne dass der Server etwas senden muss.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local CONFIG = {
	Seed = 2026,

	-- Studs pro Sekunde, Spur 1 = innen (schnell), Spur 3 = aussen (langsam)
	LaneSpeed = { 105, 80, 55 },

	-- Abstand zwischen zwei Autos auf derselben Spur (Heck bis Front, in Studs)
	GapMin = 170,
	GapMax = 420,

	-- Nur Autos in diesem Umkreis um die Kamera werden gezeigt
	DrawDistance = 1500,

	-- Welche Autos auf welcher Spur fahren (mehrfach nennen = haeufiger)
	LaneCars = {
		{ "Sportwagen", "Sportwagen", "Limousine", "SUV", "Kompakt" },
		{ "Limousine", "SUV", "Kompakt", "Kompakt", "Transporter" },
		{ "LKW", "LKW", "Transporter", "Kompakt", "Limousine" },
	},

	BodyColors = {
		Color3.fromRGB(200, 30, 30), Color3.fromRGB(20, 60, 160), Color3.fromRGB(235, 235, 235),
		Color3.fromRGB(25, 25, 28), Color3.fromRGB(120, 125, 130), Color3.fromRGB(240, 170, 20),
		Color3.fromRGB(40, 100, 60), Color3.fromRGB(90, 20, 30), Color3.fromRGB(70, 170, 220),
	},
	TrailerColors = {
		Color3.fromRGB(240, 240, 240), Color3.fromRGB(200, 205, 210), Color3.fromRGB(30, 80, 150),
		Color3.fromRGB(180, 40, 30),
	},
}

local TrackLanes = require(ReplicatedStorage:WaitForChild("TrackLanes"))
local track = workspace:WaitForChild("Autobahn")
local carFolder = ReplicatedStorage:WaitForChild("TrafficCars")
track:WaitForChild("TrackOrigin", 30)

local trafficFolder = Instance.new("Folder")
trafficFolder.Name = "Traffic"
trafficFolder.Parent = workspace

------------------------------------------------------------------------------
-- Spur-Pfade
------------------------------------------------------------------------------
type Path = { pos: { Vector3 }, cum: { number }, length: number, n: number }

local function buildPath(points: { Vector3 }): Path
	local pos = table.create(#points)
	for i, p in points do
		pos[i] = TrackLanes.ToWorld(track, p)
	end
	local cum = table.create(#pos)
	cum[1] = 0
	for i = 2, #pos do
		cum[i] = cum[i - 1] + (pos[i] - pos[i - 1]).Magnitude
	end
	return {
		pos = pos,
		cum = cum,
		length = cum[#pos] + (pos[1] - pos[#pos]).Magnitude,
		n = #pos,
	}
end

local function sample(path: Path, d: number): Vector3
	d %= path.length
	local cum = path.cum
	local lo, hi = 1, path.n
	while lo < hi do
		local mid = (lo + hi + 1) // 2
		if cum[mid] <= d then
			lo = mid
		else
			hi = mid - 1
		end
	end
	local nextIndex = lo % path.n + 1
	local segEnd = if lo == path.n then path.length else cum[lo + 1]
	return path.pos[lo]:Lerp(path.pos[nextIndex], (d - cum[lo]) / (segEnd - cum[lo]))
end

------------------------------------------------------------------------------
-- Auto-Vorlagen
------------------------------------------------------------------------------
local function styleParts(model: Model)
	for _, part in model:GetDescendants() do
		if not part:IsA("BasePart") then
			continue
		end
		local name = part.Name
		part.Anchored = true
		part.CanTouch = false
		local solid = string.find(name, "Body") or string.find(name, "Trailer")
		part.CanCollide = solid ~= nil
		part.CanQuery = solid ~= nil

		if string.find(name, "Glass") then
			part.Material = Enum.Material.Glass
			part.Color = Color3.fromRGB(25, 30, 40)
			part.Transparency = 0.1
			part.Reflectance = 0.25
		elseif string.find(name, "Headlight") then
			part.Material = Enum.Material.Neon
			part.Color = Color3.fromRGB(255, 245, 215)
		elseif string.find(name, "Taillight") then
			part.Material = Enum.Material.Neon
			part.Color = Color3.fromRGB(200, 0, 0)
		elseif string.find(name, "Tire") then
			part.Material = Enum.Material.Rubber
			part.Color = Color3.fromRGB(20, 20, 20)
		elseif string.find(name, "Rim") then
			part.Material = Enum.Material.Metal
			part.Color = Color3.fromRGB(170, 175, 180)
		elseif string.find(name, "Trim") then
			part.Material = Enum.Material.SmoothPlastic
			part.Color = Color3.fromRGB(15, 15, 15)
		else
			part.Material = Enum.Material.SmoothPlastic
		end
	end
end

-- Gibt Teile + Offsets relativ zum Bodenmittelpunkt zurueck (Front = -Z wie in Roblox ueblich)
local function measure(model: Model): ({ BasePart }, { CFrame }, number)
	local parts = {}
	local minV = Vector3.new(math.huge, math.huge, math.huge)
	local maxV = -minV
	for _, part in model:GetDescendants() do
		if part:IsA("BasePart") then
			table.insert(parts, part)
			local half = part.Size / 2
			for _, sx in { -1, 1 } do
				for _, sy in { -1, 1 } do
					for _, sz in { -1, 1 } do
						local corner = part.CFrame:PointToWorldSpace(half * Vector3.new(sx, sy, sz))
						minV = minV:Min(corner)
						maxV = maxV:Max(corner)
					end
				end
			end
		end
	end
	local center = (minV + maxV) / 2
	local pivot = CFrame.new(center.X, minV.Y, center.Z)
	local offsets = table.create(#parts)
	for i, part in parts do
		offsets[i] = pivot:ToObjectSpace(part.CFrame)
	end
	return parts, offsets, maxV.Z - minV.Z
end

local templates: { [string]: { model: Model, length: number } } = {}
for _, model in carFolder:GetChildren() do
	if model:IsA("Model") then
		local _, _, length = measure(model)
		templates[model.Name] = { model = model, length = length }
	end
end
assert(next(templates), "ReplicatedStorage.TrafficCars enthaelt keine Auto-Models")

------------------------------------------------------------------------------
-- Autos verteilen
------------------------------------------------------------------------------
type Car = {
	model: Model,
	parts: { BasePart },
	offsets: { CFrame },
	path: Path,
	start: number,
	speed: number,
	visible: boolean,
}

local rng = Random.new(CONFIG.Seed)
local cars: { Car } = {}

local function pickTemplate(lane: number)
	local options = {}
	for _, name in CONFIG.LaneCars[lane] or CONFIG.LaneCars[#CONFIG.LaneCars] do
		if templates[name] then
			table.insert(options, name)
		end
	end
	if #options == 0 then
		for name in templates do
			table.insert(options, name)
		end
		table.sort(options)
	end
	local name = options[rng:NextInteger(1, #options)]
	return name, templates[name]
end

local function spawnCar(name: string, template, path: Path, distance: number, speed: number)
	local model = template.model:Clone()
	model.Name = name
	styleParts(model)
	local bodyColor = CONFIG.BodyColors[rng:NextInteger(1, #CONFIG.BodyColors)]
	local trailerColor = CONFIG.TrailerColors[rng:NextInteger(1, #CONFIG.TrailerColors)]
	for _, part in model:GetDescendants() do
		if part:IsA("BasePart") then
			if string.find(part.Name, "Body") then
				part.Color = bodyColor
			elseif string.find(part.Name, "Trailer") then
				part.Color = trailerColor
			end
		end
	end
	local parts, offsets = measure(model)
	table.insert(cars, {
		model = model,
		parts = parts,
		offsets = offsets,
		path = path,
		start = distance,
		speed = speed,
		visible = false,
	})
end

for _, direction in { "Forward", "Backward" } do
	for lane, points in TrackLanes[direction] do
		local path = buildPath(points)
		local speed = CONFIG.LaneSpeed[lane] or CONFIG.LaneSpeed[#CONFIG.LaneSpeed]
		local first = rng:NextNumber(0, CONFIG.GapMax)
		local d = first
		while true do
			local name, template = pickTemplate(lane)
			if d + template.length > first + path.length - CONFIG.GapMin then
				break
			end
			spawnCar(name, template, path, d + template.length / 2, speed)
			d += template.length + rng:NextNumber(CONFIG.GapMin, CONFIG.GapMax)
		end
	end
end

------------------------------------------------------------------------------
-- Bewegen
------------------------------------------------------------------------------
local camera = workspace.CurrentCamera
local moveParts: { BasePart } = {}
local moveCFrames: { CFrame } = {}

RunService.PreSimulation:Connect(function()
	local now = workspace:GetServerTimeNow()
	local camPos = camera.CFrame.Position
	local drawSq = CONFIG.DrawDistance * CONFIG.DrawDistance
	local count = 0

	for _, car in cars do
		local d = car.start + car.speed * now
		local center = sample(car.path, d)
		local offset = center - camPos
		local visible = offset:Dot(offset) < drawSq

		if visible ~= car.visible then
			car.visible = visible
			car.model.Parent = if visible then trafficFolder else nil
		end

		if visible then
			local dir = sample(car.path, d + 6) - sample(car.path, d - 6)
			local cf = CFrame.lookAt(center, center + dir)
			for i, part in car.parts do
				count += 1
				moveParts[count] = part
				moveCFrames[count] = cf * car.offsets[i]
			end
		end
	end

	for i = count + 1, #moveParts do
		moveParts[i] = nil
		moveCFrames[i] = nil
	end
	if count > 0 then
		workspace:BulkMoveTo(moveParts, moveCFrames, Enum.BulkMoveMode.FireCFrameChanged)
	end
end)

print(("[Traffic] %d Autos auf %d Spuren"):format(#cars, #TrackLanes.Forward + #TrackLanes.Backward))
