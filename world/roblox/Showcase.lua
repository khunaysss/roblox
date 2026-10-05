-- Showcase: stellt ALLE Meme-Figuren auf Podest A auf, eine Reihe pro Seltenheit, mit Namensschild.
-- Voraussetzung: vorher Podest_A.lua und alle MemeFigures_<Stufe>.lua ausgefuehrt.
-- Ausfuehren in Roblox Studio (Command Bar oder MCP). Erneutes Ausfuehren baut den Showcase neu.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ORIGIN = CFrame.new(0, 0, 150)   -- hier anpassen, wo der Showcase stehen soll
local SPACING_X = 9                     -- Abstand zwischen Figuren
local SPACING_Z = 14                    -- Abstand zwischen Reihen
local PODEST_TOP = 2.2                  -- Hoehe der Podest-Oberkante (Noppen)

local TIERS = {
	{ "Common", "#b8bcc4" }, { "Uncommon", "#4fd16a" }, { "Rare", "#3f8cff" }, { "Epic", "#b05cff" },
	{ "Legendary", "#ffc83a" }, { "Mythic", "#ff4f6b" }, { "Secret", "#ff3fbf" }, { "Divine", "#fff2b0" },
	{ "Celestial", "#6a8cff" }, { "Cosmic", "#8a5cff" }, { "Eternal", "#ff7a1a" }, { "Infinity", "#33e8ff" },
}

local figures = ReplicatedStorage:FindFirstChild("MemeFigures")
local world = ReplicatedStorage:FindFirstChild("MemeWorld")
local podestTemplate = world and world:FindFirstChild("PodestA")
assert(figures, "MemeFigures fehlt: zuerst die MemeFigures_<Stufe>.lua Skripte ausfuehren")
assert(podestTemplate, "PodestA fehlt: zuerst Podest_A.lua ausfuehren")

local old = workspace:FindFirstChild("MemeShowcase")
if old then old:Destroy() end
local showcase = Instance.new("Folder")
showcase.Name = "MemeShowcase"
showcase.Parent = workspace

local function label(model, text, sub, color)
	local gui = Instance.new("BillboardGui")
	gui.Name = "NameTag"
	gui.Size = UDim2.fromOffset(160, 44)
	gui.StudsOffsetWorldSpace = Vector3.new(0, 7.5, 0)
	gui.AlwaysOnTop = false
	gui.MaxDistance = 80
	gui.Adornee = model.PrimaryPart
	local name = Instance.new("TextLabel")
	name.Size = UDim2.new(1, 0, 0.6, 0)
	name.BackgroundTransparency = 1
	name.Text = text
	name.TextColor3 = Color3.new(1, 1, 1)
	name.TextStrokeTransparency = 0.3
	name.Font = Enum.Font.FredokaOne
	name.TextScaled = true
	name.Parent = gui
	local tier = Instance.new("TextLabel")
	tier.Position = UDim2.new(0, 0, 0.6, 0)
	tier.Size = UDim2.new(1, 0, 0.4, 0)
	tier.BackgroundTransparency = 1
	tier.Text = sub
	tier.TextColor3 = color
	tier.TextStrokeTransparency = 0.3
	tier.Font = Enum.Font.FredokaOne
	tier.TextScaled = true
	tier.Parent = gui
	gui.Parent = model
end

local count = 0
for row, info in ipairs(TIERS) do
	local tierName, hex = info[1], info[2]
	local folder = figures:FindFirstChild(tierName)
	if folder then
		local list = folder:GetChildren()
		table.sort(list, function(a, b)
			return (a:GetAttribute("Order") or 0) < (b:GetAttribute("Order") or 0)
		end)
		for i, template in ipairs(list) do
			local x = (i - (#list + 1) / 2) * SPACING_X
			local spot = ORIGIN * CFrame.new(x, 0, (row - 1) * SPACING_Z)
			local podest = podestTemplate:Clone()
			podest:PivotTo(spot)
			podest.Parent = showcase
			local fig = template:Clone()
			fig.Parent = showcase -- zuerst in den Workspace, dann positionieren (Animator merkt sich die neue Lage)
			fig:PivotTo(spot * CFrame.new(0, PODEST_TOP, 0))
			label(fig, fig.Name, tierName, Color3.fromHex(hex))
			count += 1
		end
	end
end
print("Showcase gebaut: " .. count .. " Figuren")
