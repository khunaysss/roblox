-- StarterPlayer.StarterPlayerScripts.CC_TrainerPanel
-- Panel beim Ansprechen eines Stil-Trainers (CC_Trainers): Name, Kampfstil, Signatur; Ausruesten/Ablegen wenn die Signatur fertig ist.
local RS = game:GetService("ReplicatedStorage")
local player = game.Players.LocalPlayer
local ev = RS:WaitForChild("CC_TrainerPanel")

local gui = Instance.new("ScreenGui"); gui.Name = "CC_TrainerPanel"; gui.ResetOnSpawn = false; gui.DisplayOrder = 8; gui.Enabled = false
gui.Parent = player:WaitForChild("PlayerGui")
local f = Instance.new("Frame"); f.AnchorPoint = Vector2.new(0.5, 0.5); f.Position = UDim2.fromScale(0.5, 0.55); f.Size = UDim2.fromOffset(420, 230)
f.BackgroundColor3 = Color3.fromRGB(18, 20, 26); f.BackgroundTransparency = 0.08; f.BorderSizePixel = 0; f.Parent = gui
Instance.new("UICorner", f).CornerRadius = UDim.new(0, 10)
local function label(y, size, font, color)
	local l = Instance.new("TextLabel"); l.BackgroundTransparency = 1; l.Position = UDim2.fromOffset(20, y); l.Size = UDim2.new(1, -40, 0, size + 6)
	l.Font = font; l.TextSize = size; l.TextColor3 = color; l.TextXAlignment = Enum.TextXAlignment.Left; l.TextWrapped = true; l.Parent = f
	return l
end
local title = label(16, 26, Enum.Font.GothamBlack, Color3.new(1, 1, 1))
local style = label(50, 16, Enum.Font.GothamMedium, Color3.fromRGB(170, 175, 190))
local sigL = label(84, 18, Enum.Font.GothamBold, Color3.fromRGB(255, 200, 80))
local move = label(110, 16, Enum.Font.Gotham, Color3.fromRGB(220, 220, 225))
move.Size = UDim2.new(1, -40, 0, 58); move.TextYAlignment = Enum.TextYAlignment.Top
local function button(x, text, color)
	local b = Instance.new("TextButton"); b.Position = UDim2.fromOffset(x, 172); b.Size = UDim2.fromOffset(180, 40)
	b.BackgroundColor3 = color; b.BorderSizePixel = 0; b.Font = Enum.Font.GothamBold; b.TextSize = 16; b.TextColor3 = Color3.new(1, 1, 1)
	b.Text = text; b.Parent = f; Instance.new("UICorner", b).CornerRadius = UDim.new(0, 8)
	return b
end
local act = button(20, "", Color3.fromRGB(170, 30, 40))
local close = button(220, "Close", Color3.fromRGB(60, 64, 76))

local cur
local function refresh()
	if not cur then return end
	local eq = player:GetAttribute("CC_Signature")
	local unlocked = table.find(string.split(player:GetAttribute("CC_SigUnlocked") or "", ","), cur.sig or "") ~= nil
	local trial = player:GetAttribute("CC_SigTrial") == cur.sig
	if cur.sig then
		act.Visible = true
		if unlocked then
			act.Text = eq == cur.sig and "Ablegen" or "Equip (G)"
			move.Text = cur.move
		else
			act.Text = trial and "Cancel practice" or "Lernen"
			move.Text = cur.move .. (trial and "\nPRACTICE: start a training fight and land the combo once (G with full focus)."
				or "\nNot unlocked yet.")
		end
		sigL.Text = "Signature: " .. cur.sigName .. (eq == cur.sig and "  ✓" or "")
	else
		act.Visible = false
		sigL.Text = "Signature: coming soon"
	end
end
ev.OnClientEvent:Connect(function(kind, data)
	if kind ~= "open" then return end
	cur = data
	title.Text = data.name; style.Text = data.style; move.Text = data.move
	refresh(); gui.Enabled = true
end)
act.Activated:Connect(function()
	if not cur or not cur.sig then return end
	local unlocked = table.find(string.split(player:GetAttribute("CC_SigUnlocked") or "", ","), cur.sig) ~= nil
	if unlocked then ev:FireServer(player:GetAttribute("CC_Signature") == cur.sig and "unequip" or "equip", cur.sig)
	else ev:FireServer(player:GetAttribute("CC_SigTrial") == cur.sig and "stoplearn" or "learn", cur.sig) end
end)
close.Activated:Connect(function() gui.Enabled = false; cur = nil end)
for _, a in ipairs({ "CC_Signature", "CC_SigUnlocked", "CC_SigTrial" }) do player:GetAttributeChangedSignal(a):Connect(refresh) end
-- Kampfbeginn schliesst das Panel
local ms = RS:WaitForChild("CC_MatchState")
ms:GetAttributeChangedSignal("State"):Connect(function() if ms:GetAttribute("State") ~= "idle" then gui.Enabled = false; cur = nil end end)
