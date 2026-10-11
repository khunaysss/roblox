-- StarterPlayer.StarterPlayerScripts.CC_Props
-- Haelt Trainingsgewichte (Workspace.CC_Props, vom Server angelegt) in den Haenden der Kaempfer.
-- Die Kaempfer sind skinned Meshes: die Hand-Bones bewegen sich nur in der Animation (TransformedWorldCFrame),
-- deshalb setzt jeder Client die Gewichte jedes Bild an die animierte Hand. Attribute am Modell:
--   Owner = Charakter-Name, Mode = "hand" (eine Hand, Bone) | "between" (Stange zwischen beiden Haenden, Bone = "L,R")
local RunService = game:GetService("RunService")
local props = workspace:WaitForChild("CC_Props")
local GRIP = 0.30                                   -- Faustmitte entlang des Hand-Bones (Studs)

local function boneOf(char, name)
	local hrp = char and char:FindFirstChild("HumanoidRootPart")
	return hrp and hrp:FindFirstChild(name, true)
end
local function grip(b)
	local cf = b.TransformedWorldCFrame
	return cf, cf.Position + cf.UpVector * GRIP
end

RunService:BindToRenderStep("CC_Props", Enum.RenderPriority.Camera.Value - 1, function()
	for _, m in ipairs(props:GetChildren()) do
		if m:IsA("Model") and m.PrimaryPart then
			local char = workspace:FindFirstChild(m:GetAttribute("Owner") or "")
			local mode, bone = m:GetAttribute("Mode"), m:GetAttribute("Bone") or ""
			if char then
				if mode == "hand" then
					local b = boneOf(char, bone)
					if b then
						local cf, p = grip(b)
						-- Griff quer durch die Faust: Hantel-Laengsachse (Z) = X-Achse des Hand-Bones
						m:PivotTo(CFrame.fromMatrix(p, cf.LookVector, cf.UpVector))
					end
				elseif mode == "between" then
					local a, b = bone:match("^(%w+),(%w+)$")
					local ba, bb = a and boneOf(char, a), b and boneOf(char, b)
					if ba and bb then
						local _, pa = grip(ba); local _, pb = grip(bb)
						local axis = pb - pa
						if axis.Magnitude > 0.05 then
							axis = axis.Unit
							local up = Vector3.yAxis - axis * axis:Dot(Vector3.yAxis)
							up = up.Magnitude > 0.05 and up.Unit or Vector3.zAxis
							m:PivotTo(CFrame.fromMatrix((pa + pb) / 2, axis, up))   -- Stange (X) entlang der Haende
						end
					end
				end
			end
		end
	end
end)
