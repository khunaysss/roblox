-- CC_UI_v02 – zentrales natives Launch-Designsystem.
-- Keine Bild-Assets, Uploads oder rasterisierten Flaechen.
local GuiService = game:GetService("GuiService")
local UIS = game:GetService("UserInputService")
local TweenService = game:GetService("TweenService")
local UI = {}
local sqrt, abs, max, min, clamp = math.sqrt, math.abs, math.max, math.min, math.clamp
local S = {}
function S.seg(ax, ay, bx, by, w)
	local dx, dy = bx - ax, by - ay
	local l2 = dx * dx + dy * dy
	return function(x, y)
		local t = l2 > 0 and clamp(((x - ax) * dx + (y - ay) * dy) / l2, 0, 1) or 0
		local px, py = ax + dx * t - x, ay + dy * t - y
		return sqrt(px * px + py * py) - w / 2
	end
end
function S.line(pts, w)                        -- offene Linie durch Punkte {x1,y1,x2,y2,...}
	local parts = {}
	for i = 1, #pts - 3, 2 do table.insert(parts, S.seg(pts[i], pts[i + 1], pts[i + 2], pts[i + 3], w)) end
	return S.union(table.unpack(parts))
end
function S.circle(cx, cy, r)
	return function(x, y) return sqrt((x - cx) ^ 2 + (y - cy) ^ 2) - r end
end
function S.ring(cx, cy, r, w)
	return function(x, y) return abs(sqrt((x - cx) ^ 2 + (y - cy) ^ 2) - r) - w / 2 end
end
function S.box(cx, cy, hx, hy, rad, ang)
	rad = rad or 0
	local c, s = math.cos(ang or 0), math.sin(ang or 0)
	return function(x, y)
		local lx, ly = x - cx, y - cy
		lx, ly = lx * c + ly * s, -lx * s + ly * c
		local qx, qy = abs(lx) - hx + rad, abs(ly) - hy + rad
		local ox, oy = max(qx, 0), max(qy, 0)
		return sqrt(ox * ox + oy * oy) + min(max(qx, qy), 0) - rad
	end
end
function S.poly(pts)                           -- gefuelltes Polygon
	local n = #pts / 2
	return function(x, y)
		local d, inside, j = math.huge, false, n
		for i = 1, n do
			local xi, yi, xj, yj = pts[2 * i - 1], pts[2 * i], pts[2 * j - 1], pts[2 * j]
			local ex, ey = xj - xi, yj - yi
			local t = clamp(((x - xi) * ex + (y - yi) * ey) / (ex * ex + ey * ey), 0, 1)
			local px, py = xi + ex * t - x, yi + ey * t - y
			d = min(d, px * px + py * py)
			if (yi > y) ~= (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi then inside = not inside end
			j = i
		end
		d = sqrt(d)
		return inside and -d or d
	end
end
function S.arc(cx, cy, r, a0, a1, w)           -- Bogen (Grad, 0 = rechts, im Uhrzeigersinn nach unten)
	local pts, steps = {}, max(6, math.floor(abs(a1 - a0) / 8))
	for i = 0, steps do
		local a = math.rad(a0 + (a1 - a0) * i / steps)
		table.insert(pts, cx + math.cos(a) * r); table.insert(pts, cy + math.sin(a) * r)
	end
	return S.line(pts, w)
end
function S.union(...)
	local fs = { ... }
	return function(x, y)
		local d = math.huge
		for _, f in ipairs(fs) do d = min(d, f(x, y)) end
		return d
	end
end
function S.cut(a, b) return function(x, y) return max(a(x, y), -b(x, y)) end end
function S.both(a, b) return function(x, y) return max(a(x, y), b(x, y)) end end
function S.outline(a, w) return function(x, y) return abs(a(x, y) + w / 2) - w / 2 end end   -- Rand nach innen
UI.Shapes = S


function UI.new(class, props, children)
	local o = Instance.new(class)
	o:SetAttribute("CC_NativeUI", true)
	local parent
	for k, v in pairs(props or {}) do
		if k == "Parent" then parent = v else o[k] = v end
	end
	for _, c in ipairs(children or {}) do c.Parent = o end
	if parent then o.Parent = parent end
	return o
end


function UI.label(props)
	local l = UI.new("TextLabel", { BackgroundTransparency = 1, FontFace = UI.F.body, TextColor3 = UI.C.text,
		TextXAlignment = Enum.TextXAlignment.Left, TextYAlignment = Enum.TextYAlignment.Center, Size = UDim2.new(1, 0, 0, 24), TextSize = 17, TextWrapped = true })
	for k, v in pairs(props) do if k ~= "Parent" then l[k] = v end end
	if props.Parent then l.Parent = props.Parent end
	return l
end


local function selectionImage() return UI.new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }) end
UI.noSelectionImage = selectionImage


function UI.button(opts)
 local style=opts.Style or "secondary"
 local nav=style=="nav"
 local b=UI.new("TextButton",{Text="",AutoButtonColor=false,BackgroundTransparency=1,BorderSizePixel=0,
  Size=opts.Size or UDim2.new(1,0,0,nav and 82 or (style=="ghost" and 44 or 58)),
  LayoutOrder=opts.LayoutOrder or 0,Selectable=true,Name=opts.Name or opts.Text or "Button"})
 b.SelectionImageObject=selectionImage()
 local bg=UI.sprite(nav and "skin_menu_normal" or (style=="primary" and "skin_primary" or "skin_secondary"),
  {Name="KitBackground",Size=UDim2.fromScale(1,1),ZIndex=1,Parent=b})
 local x=nav and 28 or 26
 local icon
 if opts.Icon then
  local sz=nav and 34 or (style=="ghost" and 21 or 26)
  icon=UI.icon(opts.Icon,{Size=UDim2.fromOffset(sz,sz),AnchorPoint=Vector2.new(0,0.5),Position=UDim2.new(0,x,0.5,0),ZIndex=3,Parent=b})
  x+=sz+(nav and 18 or 12)
 end
 local centered=not opts.Icon and not nav and not opts.Sub
 local title=UI.label({Text=opts.Text or "",FontFace=nav and UI.F.title or UI.F.head,TextSize=nav and 26 or (style=="ghost" and 16 or 21),
  TextXAlignment=centered and Enum.TextXAlignment.Center or Enum.TextXAlignment.Left,TextWrapped=false,TextTruncate=Enum.TextTruncate.AtEnd,
  Position=UDim2.new(0,centered and 12 or x,0,opts.Sub and 4 or 0),Size=UDim2.new(1,-(centered and 24 or x+(nav and 42 or 24)),opts.Sub and 0.55 or 1,0),ZIndex=3,Parent=b})
 if opts.Icon and opts.Size and opts.Size.X.Scale==0 and opts.Size.X.Offset<=80 then
  icon.AnchorPoint=Vector2.new(0.5,0.5);icon.Position=UDim2.fromScale(0.5,0.5)
  title.Size=UDim2.new(0,0,1,0);title.Visible=false
 end
 title.TextScaled=true
 UI.new("UITextSizeConstraint",{MaxTextSize=nav and 26 or (style=="ghost" and 16 or 21),MinTextSize=12,Parent=title})
 local sub
 if opts.Sub then
  title.TextYAlignment=Enum.TextYAlignment.Bottom
  sub=UI.label({Text=opts.Sub,TextSize=nav and 16 or 13,TextColor3=UI.C.dim,TextWrapped=false,TextTruncate=Enum.TextTruncate.AtEnd,
   TextYAlignment=Enum.TextYAlignment.Top,Position=UDim2.new(0,x,0.61,0),Size=UDim2.new(1,-x-32,0.3,0),ZIndex=3,Parent=b})
 end
 if nav then UI.icon("next",{AnchorPoint=Vector2.new(1,0.5),Position=UDim2.new(1,-23,0.5,0),Size=UDim2.fromOffset(18,24),ZIndex=3,Parent=b}) end
 local badge=opts.Badge and UI.tag({Text=opts.Badge,AnchorPoint=Vector2.new(1,0.5),Position=UDim2.new(1,-20,0.5,0),ZIndex=4,Parent=b}) or nil
 local hot=false
 local function refresh()
  local dis=b:GetAttribute("Disabled"); local sel=b:GetAttribute("Selected")
  local key=dis and "skin_disabled" or (nav and ((hot or sel) and "skin_menu_selected" or "skin_menu_normal") or
   ((style=="primary" or sel) and (hot and "skin_hover" or "skin_primary") or (hot and "skin_small" or "skin_secondary")))
    local active=not dis and (sel or style=="primary")
  bg.ImageColor3=dis and UI.C.bg2 or (active and UI.C.red or (hot and UI.C.bg3 or UI.C.bg1))
  bg.ImageTransparency=dis and 0.3 or 0.02
  if b:GetAttribute("KitSprite") then title.Text=sel and "ON" or "OFF" end
  local reward=b:GetAttribute("RewardReady") and not dis
  if reward then bg.ImageColor3=UI.C.gold end
  title.TextColor3=reward and UI.C.bg0 or dis and UI.C.dim or UI.C.text
  if icon then icon.ImageColor3=dis and UI.C.dim or UI.C.text end
  if sub then sub.TextColor3=dis and UI.C.mute or UI.C.dim end
  b.Active=not dis;b.Selectable=not dis
 end
 b.MouseEnter:Connect(function() hot=true;refresh() end);b.MouseLeave:Connect(function() hot=false;refresh() end)
 b.SelectionGained:Connect(function() hot=true;refresh() end);b.SelectionLost:Connect(function() hot=false;refresh() end)
 b:GetAttributeChangedSignal("Disabled"):Connect(refresh);b:GetAttributeChangedSignal("Selected"):Connect(refresh);b:GetAttributeChangedSignal("KitSprite"):Connect(refresh);b:GetAttributeChangedSignal("RewardReady"):Connect(refresh)
 b.Activated:Connect(function() if not b:GetAttribute("Disabled") and opts.OnClick then opts.OnClick(b) end end)
 b:SetAttribute("Disabled",opts.Disabled or false);refresh()
 if opts.Parent then b.Parent=opts.Parent end
 return b,{title=title,sub=sub,icon=icon,badge=badge,bg=bg}
end

-- kleines Schild (z. B. "BALD", "GESPERRT")
function UI.tag(props)
	local t = UI.chamfer({ AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, 22), ImageColor3 = props.Color or UI.C.bg3, ImageTransparency = 0 }, "fill", 6)
	UI.new("UIPadding", { PaddingLeft = UDim.new(0, 8), PaddingRight = UDim.new(0, 8), Parent = t })
	UI.label({ Text = props.Text, FontFace = UI.F.bold, TextSize = 13, TextColor3 = props.TextColor or UI.C.text, AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromScale(0, 1), TextXAlignment = Enum.TextXAlignment.Center, ZIndex = (props.ZIndex or 1) + 1, Parent = t })
	for k, v in pairs(props) do if k ~= "Parent" and k ~= "Text" and k ~= "Color" and k ~= "TextColor" then t[k] = v end end
	if props.Parent then t.Parent = props.Parent end
	return t
end

-- Tastensymbol fuer Hinweise (Text in einem Kaestchen, z. B. "E", "LEER", "A")
function UI.key(text,props)
 local p=table.clone(props or {});p.Size=p.Size or UDim2.fromOffset(math.max(40,#text*10+20),34)
 local key=UI.sprite("skin_key",p)
 UI.label({Text=text,FontFace=UI.F.bold,TextSize=17,TextColor3=UI.C.text,Size=UDim2.fromScale(1,1),
  TextXAlignment=Enum.TextXAlignment.Center,ZIndex=(p.ZIndex or 1)+1,TextWrapped=false,Parent=key})
 return key
end

-- Geraet: "pad" | "touch" | "pc" (nach letzter Eingabe)
function UI.device()
	local t = UIS:GetLastInputType()
	if t.Name:find("Gamepad") then return "pad" end
	if t == Enum.UserInputType.Touch or (UIS.TouchEnabled and not UIS.KeyboardEnabled) then return "touch" end
	return "pc"
end

-- Zeile mit Tastenhinweisen; entries = { {pc = "ENTER", pad = "A", text = "Auswählen"}, ... } (touch: ohne Tasten)
function UI.hints(props)
	local row = UI.new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromOffset(600, 28) })
	for k, v in pairs(props) do if k ~= "Parent" and k ~= "Entries" then row[k] = v end end
	UI.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, HorizontalAlignment = props.Align or Enum.HorizontalAlignment.Right,
		VerticalAlignment = Enum.VerticalAlignment.Center, Padding = UDim.new(0, 8), SortOrder = Enum.SortOrder.LayoutOrder, Parent = row })
	local function build()
		for _, c in ipairs(row:GetChildren()) do if not c:IsA("UIListLayout") then c:Destroy() end end
		local dev = UI.device()
		if dev == "touch" then return end
		for i, e in ipairs(props.Entries) do
			local key = dev == "pad" and e.pad or e.pc
			if key then
				UI.key(key, { LayoutOrder = i * 2, Parent = row })
				UI.label({ Text = e.text, TextSize = 16, TextColor3 = UI.C.dim, AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, 30),
					TextWrapped = false, LayoutOrder = i * 2 + 1, Parent = row })
			end
		end
	end
	build()
	local last = UI.device()
	UIS.LastInputTypeChanged:Connect(function()
		local d = UI.device()
		if d ~= last then last = d; build() end
	end)
	if props.Parent then row.Parent = props.Parent end
	return row
end

-- Skaliert eine Vollbild-Ebene auf eine virtuelle Hoehe von 900 (Groesse = 1/scale, damit sie den Bildschirm fuellt)
function UI.autoscale(frame, designH)
	designH = designH or 720
	local s = UI.new("UIScale", { Parent = frame })
	local cam = workspace.CurrentCamera
	local function upd()
		local vp = cam.ViewportSize
		local screen = frame:FindFirstAncestorOfClass("ScreenGui")
		local top, bottom = GuiService:GetGuiInset()
		local height = screen and not screen.IgnoreGuiInset and vp.Y - top.Y - bottom.Y or vp.Y
		local k = clamp(min(height / designH, vp.X / (designH * 1.5)), 0.5, 1.6)
		s.Scale = k
		frame.Size = UDim2.fromScale(1 / k, 1 / k)
	end
	cam:GetPropertyChangedSignal("ViewportSize"):Connect(upd)
	upd()
	return s
end

-- Controller: erstes waehlbares Element fokussieren, wenn mit Gamepad gespielt wird
function UI.focus(obj)
	if obj and UI.device() == "pad" then GuiService.SelectedObject = obj end
end

-- gemeinsame Hover/Fokus-Logik fuer Karten und Farbfelder
local function hotState(b, refresh)
	local st = { hover = false, focus = false }
	b.MouseEnter:Connect(function() st.hover = true; refresh() end)
	b.MouseLeave:Connect(function() st.hover = false; refresh() end)
	b.SelectionGained:Connect(function() st.focus = true; refresh() end)
	b.SelectionLost:Connect(function() st.focus = false; refresh() end)
	b.AttributeChanged:Connect(refresh)
	return st
end

-- Auswahlkarte mit Vorschau (ViewportFrame). opts: Parent, Text, Size, LayoutOrder, Locked, OnClick.
-- Zustaende: Attribut "Selected" (rot, Haken), "Locked" (Schloss, nicht waehlbar); Hover/Fokus = roter Rahmen.
function UI.optionCard(opts)
	local b = UI.new("TextButton", { Text = "", AutoButtonColor = false, BackgroundTransparency = 1, Size = opts.Size or UDim2.fromOffset(150, 176),
		LayoutOrder = opts.LayoutOrder or 0, Name = opts.Text or "Card" })
	b.SelectionImageObject = selectionImage()
	local bg = UI.chamfer({ Size = UDim2.fromScale(1, 1), ImageColor3 = UI.C.bg2, ImageTransparency = 0, Parent = b }, "fill", 12)
	local vp = UI.new("ViewportFrame", { BackgroundColor3 = UI.C.bg1, BackgroundTransparency = 0, BorderSizePixel = 0, Position = UDim2.fromOffset(8, 8),
		Size = UDim2.new(1, -16, 1, -48), Ambient = Color3.fromRGB(200, 200, 210), LightColor = Color3.fromRGB(255, 255, 255), LightDirection = Vector3.new(-0.4, -0.6, -1),
		ZIndex = 2, Parent = b })
	local name = UI.label({ Text = opts.Text or "", FontFace = UI.F.bold, TextSize = 15, TextXAlignment = Enum.TextXAlignment.Center, TextWrapped = false,
		TextTruncate = Enum.TextTruncate.AtEnd, AnchorPoint = Vector2.new(0, 1), Position = UDim2.new(0, 6, 1, -8), Size = UDim2.new(1, -12, 0, 26), ZIndex = 3, Parent = b })
	local check = UI.chamfer({ Size = UDim2.fromOffset(30, 30), AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -4, 0, 4), ImageColor3 = UI.C.red, ImageTransparency = 0, ZIndex = 6, Visible = false, Parent = b }, "fill", 6)
	UI.icon("check", { Size = UDim2.fromOffset(20, 20), Position = UDim2.fromOffset(5, 5), ZIndex = 7, Parent = check })
	local lock = UI.icon("lock", { Size = UDim2.fromOffset(34, 34), AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.new(0.5, 0, 0.42, 0), ImageColor3 = UI.C.dim, ZIndex = 6, Visible = false, Parent = b })
	local ring = UI.ring(b, 12, UI.C.red)
	local st
	local function refresh()
		local sel, locked = b:GetAttribute("Selected"), b:GetAttribute("Locked")
		local hot = st and (st.hover or st.focus)
		ring.Visible = hot or sel
		ring.ImageColor3 = sel and UI.C.red or UI.C.text:Lerp(UI.C.red, 0.6)
		check.Visible = sel and true or false
		lock.Visible = locked and true or false
		vp.ImageTransparency = locked and 0.7 or 0
		bg.ImageColor3 = sel and UI.C.redDark or (hot and UI.C.bg3 or UI.C.bg2)
		name.TextColor3 = locked and UI.C.mute or UI.C.text
	end
	st = hotState(b, refresh)
	b:SetAttribute("Locked", opts.Locked or false)
	b.Activated:Connect(function() if not b:GetAttribute("Locked") and opts.OnClick then opts.OnClick(b) end end)
	refresh()
	if opts.Parent then b.Parent = opts.Parent end
	return b, vp
end

-- Farbfeld. opts: Parent, Color, Size, LayoutOrder, OnClick, Name
function UI.swatch(opts)
	local b = UI.new("TextButton", { Text = "", AutoButtonColor = false, BackgroundTransparency = 1, Size = opts.Size or UDim2.fromOffset(56, 56),
		LayoutOrder = opts.LayoutOrder or 0, Name = opts.Name or "Swatch" })
	b.SelectionImageObject = selectionImage()
	UI.chamfer({ Size = UDim2.new(1, -10, 1, -10), Position = UDim2.fromOffset(5, 5), ImageColor3 = opts.Color, ImageTransparency = 0, Parent = b }, "fill", 8)
	local check = UI.icon("check", { Size = UDim2.fromOffset(24, 24), AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), ZIndex = 4, Visible = false, Parent = b })
	local ring = UI.ring(b, 10, UI.C.red)
	local st
	local function refresh()
		local sel = b:GetAttribute("Selected")
		ring.Visible = sel or (st and (st.hover or st.focus)) or false
		ring.ImageColor3 = sel and UI.C.red or UI.C.text
		check.Visible = sel and true or false
		local c = opts.Color
		check.ImageColor3 = (c.R * 0.3 + c.G * 0.59 + c.B * 0.11) > 0.6 and UI.C.bg0 or UI.C.text
	end
	st = hotState(b, refresh)
	b.Activated:Connect(function() if opts.OnClick then opts.OnClick(b) end end)
	refresh()
	if opts.Parent then b.Parent = opts.Parent end
	return b
end

-- Abfrage-Fenster (modal). buttons = { { Text=, Style=, OnClick= }, ... }; schliesst sich nach jedem Knopf.
function UI.dialog(parent, title, text, buttons)
	local dim = UI.new("TextButton", { Name = "Dialog", Text = "", AutoButtonColor = false, BackgroundColor3 = Color3.new(0, 0, 0), BackgroundTransparency = 0.35,
		Size = UDim2.fromScale(1, 1), ZIndex = 80, Modal = true, Selectable = false, Parent = parent })
	local box = UI.panel({ AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(520, 230), ZIndex = 81, Parent = dim })
	UI.label({ Text = title, FontFace = UI.F.title, TextSize = 28, Position = UDim2.fromOffset(28, 22), Size = UDim2.new(1, -56, 0, 34), ZIndex = 82, Parent = box })
	UI.label({ Text = text, TextSize = 17, TextColor3 = UI.C.dim, TextYAlignment = Enum.TextYAlignment.Top, Position = UDim2.fromOffset(28, 66), Size = UDim2.new(1, -56, 0, 60), ZIndex = 82, Parent = box })
	local row = UI.new("Frame", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0, 1), Position = UDim2.new(0, 28, 1, -22), Size = UDim2.new(1, -56, 0, 54), ZIndex = 82, Parent = box })
	UI.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 12), HorizontalAlignment = Enum.HorizontalAlignment.Right, SortOrder = Enum.SortOrder.LayoutOrder, Parent = row })
	local first
	for i, bd in ipairs(buttons) do
		local b = UI.button({ Text = bd.Text, Style = bd.Style or "secondary", Size = UDim2.fromOffset(200, 54), LayoutOrder = i, Parent = row,
			OnClick = function() dim:Destroy(); if bd.OnClick then bd.OnClick() end end })
		for _, d in ipairs(b:GetDescendants()) do if d:IsA("GuiObject") then d.ZIndex += 82 end end
		b.ZIndex = 83
		first = first or b
	end
	UI.focus(first)
	return dim
end

-- Live bars use the extracted border with independent, live fill and damage lag.
function UI.combatBar(opts)
 local root=UI.new("Frame",{Name=opts.Name or "CombatBar",BackgroundTransparency=1,
  Position=opts.Position or UDim2.new(),AnchorPoint=opts.AnchorPoint or Vector2.zero,
  Size=opts.Size or UDim2.fromOffset(540,62),Parent=opts.Parent})
 local art=UI.sprite(opts.Skin or "skin_health_player",{Size=UDim2.fromScale(1,1),ImageColor3=UI.C.bg0,ZIndex=1,Parent=root})
 local clip=UI.new("Frame",{Name="LiveFillClip",BackgroundTransparency=1,BorderSizePixel=0,ClipsDescendants=true,
  Position=UDim2.fromScale(0.02,0.14),Size=UDim2.fromScale(0.96,0.72),ZIndex=2,Parent=root})
 local damage=UI.new("Frame",{Name="DamageLag",BackgroundColor3=(opts.Color or UI.C.red):Lerp(Color3.new(1,1,1),0.45),
  BorderSizePixel=0,Size=UDim2.fromScale(1,1),ZIndex=2,Parent=clip})
 local fill=UI.new("Frame",{Name="Fill",BackgroundColor3=opts.Color or UI.C.red,BorderSizePixel=0,
  Size=UDim2.fromScale(1,1),ZIndex=3,Parent=clip})

 local label=UI.label({Name="Value",Text="",FontFace=UI.F.bold,TextSize=opts.TextSize or 22,
  TextXAlignment=Enum.TextXAlignment.Right,Position=UDim2.fromScale(0.12,0.12),Size=UDim2.fromScale(0.8,0.72),ZIndex=5,Parent=root})
 damage.Visible=(opts.Skin=="skin_health_player" or opts.Skin=="skin_health_opponent")
 return root,fill,label,damage
end

-- Portraits show existing fighter models, never stock faces or invented IDs.
function UI.fighterPortrait(parent,size,color)
 local frame=UI.panel({Name="Portrait",Size=size or UDim2.fromOffset(100,100),Parent=parent})
 local vp=UI.new("ViewportFrame",{BackgroundTransparency=1,Size=UDim2.new(1,-12,1,-12),Position=UDim2.fromOffset(6,6),
  Ambient=Color3.fromRGB(185,185,200),LightColor=Color3.new(1,1,1),LightDirection=Vector3.new(-1,-0.5,-1),ZIndex=3,Parent=frame})
 local line=UI.new("UIStroke",{Color=color or UI.C.red,Thickness=2,Parent=frame})
 local last
 local function show(model)
  if model==last then return end
  last=model
  vp:ClearAllChildren()
  if not model then return end
  local old=model.Archivable;model.Archivable=true
  local ok,copy=pcall(function() return model:Clone() end);model.Archivable=old
  if not ok or not copy then return end
  for _,d in ipairs(copy:GetDescendants()) do
   if d:IsA("LuaSourceContainer") then d:Destroy()
   elseif d:IsA("BasePart") then d.Anchored=true;d.CanCollide=false end
  end
  local world=Instance.new("WorldModel");world.Parent=vp;copy.Parent=world
  copy:PivotTo(CFrame.new())
  local head=copy:FindFirstChild("Head",true)
  local pivot=copy:GetPivot()
  local center=head and (head:IsA("Bone") and head.TransformedWorldCFrame.Position or head.Position) or pivot.Position+Vector3.new(0,2,0)
  local look=pivot.LookVector
  local camera=Instance.new("Camera");camera.FieldOfView=30
  camera.CFrame=CFrame.lookAt(center+look*6.8+Vector3.new(0,0.1,0),center-Vector3.new(0,0.25,0))
  camera.Parent=vp;vp.CurrentCamera=camera
 end
 return frame,show
end



-- Launch-Stil: vorhandene API bleibt kompatibel, alle Flaechen sind nativ.
-- THESIS: Klarer TV-Kampfstatus statt dekorativer Bildtafeln.
-- OWN-WORLD: Anthrazit, Rot/Blau, Gold, Gotham, 4px Ecken, 8px Raster.
-- STORY: Auswaehlen, trainieren, kaempfen; Daten und Eingaben bleiben echt.
-- FIRST VIEWPORT: Navigation links, eigene Figur rechts, Profil getrennt oben.
-- FORM: Vom Nutzer vorgegebenes Broadcast-System, direkte Code-Umsetzung.
do
	UI.C = {
		bg0 = Color3.fromHex("#15171C"), bg1 = Color3.fromHex("#1E2026"),
		bg2 = Color3.fromHex("#1E2026"), bg3 = Color3.fromHex("#3A3D46"),
		line = Color3.fromHex("#3A3D46"), text = Color3.fromHex("#F5F5F7"),
		dim = Color3.fromHex("#A6A9B4"), mute = Color3.fromHex("#6B6E7A"),
		red = Color3.fromHex("#E0243A"), redDark = Color3.fromRGB(98, 25, 36),
		blue = Color3.fromHex("#2F6FE0"), blueDark = Color3.fromRGB(24, 46, 85),
		gold = Color3.fromHex("#E8B65A"), green = Color3.fromHex("#2EB86B"),
		warn = Color3.fromHex("#F2C94C"), stamina = Color3.fromHex("#F2C94C"),
	}
	UI.F = {
		title = Font.fromEnum(Enum.Font.GothamBlack),
		head = Font.fromEnum(Enum.Font.GothamBlack),
		bold = Font.fromEnum(Enum.Font.GothamBold),
		body = Font.fromEnum(Enum.Font.Gotham),
	}
	UI.Grid = 8
	UI.Radius = 4
	UI.Logo = nil
	UI.Ready = true
	UI.IconNames = {"trophy","globe","dumbbell","fighter","gear","menu","hair","beard","face","skin","shorts","back","next","check","close","lock","rotate","play","search","glove","star","clock","help","info","coach","run","shield","kick","wrestle","octagon","skip","mouse","warn","user2"}
	function UI.chamferContent() return nil end
	function UI.iconContent() return Content.none end
	function UI.chamfer(props, kind)
		local surface = UI.new("ImageLabel", {BackgroundTransparency = 1, BorderSizePixel = 0, Image = ""})
		for k, v in pairs(props or {}) do
			if k ~= "Parent" and k ~= "Cut" then surface[k] = v end
		end
		local outline = kind == "outline" or kind == "outline_thick"
		UI.new("UICorner", {CornerRadius = UDim.new(0, 4), Parent = surface})
		local stroke = UI.new("UIStroke", {
			Name = "PanelOutline", Color = UI.C.line, Thickness = 1,
			ApplyStrokeMode = Enum.ApplyStrokeMode.Border, Parent = surface,
		})
		local function sync()
			surface.BackgroundColor3 = surface.ImageColor3
			surface.BackgroundTransparency = outline and 1 or surface.ImageTransparency
			stroke.Color = outline and surface.ImageColor3 or UI.C.line
			stroke.Transparency = outline and surface.ImageTransparency or 0
		end
		surface:GetPropertyChangedSignal("ImageColor3"):Connect(sync)
		surface:GetPropertyChangedSignal("ImageTransparency"):Connect(sync)
		sync()
		if props and props.Parent then surface.Parent = props.Parent end
		return surface
	end
	function UI.panel(props)
		local p = table.clone(props)
		p.Cut = nil
		p.ImageColor3 = p.ImageColor3 or UI.C.bg1
		p.ImageTransparency = p.ImageTransparency or 0
		return UI.chamfer(p, "fill")
	end
	function UI.sprite(name, props)
		if name ~= "logo" then
			local p = table.clone(props or {})
			p.ImageColor3 = p.ImageColor3 or (name == "skin_primary" and UI.C.red or UI.C.bg1)
			return UI.chamfer(p, "fill")
		end
		local root = UI.new("Frame", {Name = "CC_Logo", BackgroundTransparency = 1})
		for k, v in pairs(props or {}) do if k ~= "Parent" then root[k] = v end end
		local title = UI.label({
			Name = "Wordmark", Text = "CAGE CHAMPIONS", FontFace = UI.F.title,
			TextColor3 = UI.C.gold, TextSize = 34, TextScaled = true, TextWrapped = false,
			Size = UDim2.fromScale(1, 1), Parent = root,
		})
		UI.new("UITextSizeConstraint", {MaxTextSize = 42, MinTextSize = 16, Parent = title})
		UI.new("UIStroke", {Color = Color3.new(0, 0, 0), Thickness = 2, Parent = title})
		if props and props.Parent then root.Parent = props.Parent end
		return root
	end
	-- Kontur-Icons aus Linien und Rechtecken; keine Bilder und keine Emoji.
	function UI.icon(name, props)
		local root = UI.new("ImageLabel", {
			Name = "Icon_" .. name, Image = "", BackgroundTransparency = 1,
			Size = UDim2.fromOffset(32, 32), ImageColor3 = UI.C.text,
		})
		for k, v in pairs(props or {}) do
			if k ~= "Res" and k ~= "Parent" then root[k] = v end
		end
		local pieces = {}
		local function box(x, y, w, h, round)
			local p = UI.new("Frame", {
				Position = UDim2.fromScale(x, y), Size = UDim2.fromScale(w, h),
				BorderSizePixel = 0, BackgroundColor3 = root.ImageColor3,
				ZIndex = root.ZIndex, Parent = root,
			})
			if round then UI.new("UICorner", {CornerRadius = UDim.new(1, 0), Parent = p}) end
			table.insert(pieces, p)
			return p
		end
		local function line(ax, ay, bx, by)
			local dx, dy = bx - ax, by - ay
			local p = box((ax + bx) / 2, (ay + by) / 2, math.sqrt(dx * dx + dy * dy), 0.075)
			p.AnchorPoint = Vector2.new(0.5, 0.5)
			p.Rotation = math.deg(math.atan2(dy, dx))
		end
		if name == "check" then line(.18,.53,.4,.75); line(.4,.75,.84,.25)
		elseif name == "close" then line(.23,.23,.77,.77); line(.77,.23,.23,.77)
		elseif name == "back" or name == "next" then
			local a, b = name == "back" and .65 or .35, name == "back" and .35 or .65
			line(a,.2,b,.5); line(b,.5,a,.8)
		elseif name == "menu" then for i = 0, 2 do box(.15,.23 + i*.23,.7,.075) end
		elseif name == "dumbbell" then box(.1,.3,.16,.4);box(.74,.3,.16,.4);box(.26,.46,.48,.08)
		elseif name == "lock" then
			box(.2,.43,.6,.43)
			line(.32,.43,.32,.25);line(.32,.25,.68,.25);line(.68,.25,.68,.43)
		elseif name == "fighter" or name == "coach" or name == "user2" then
			box(.36,.12,.28,.28,true);box(.2,.48,.6,.4,true)
		elseif name == "trophy" then
			box(.28,.15,.44,.42);box(.46,.57,.08,.2);box(.29,.8,.42,.075)
			line(.28,.2,.12,.2);line(.12,.2,.2,.48);line(.72,.2,.88,.2);line(.88,.2,.8,.48)
		elseif name == "globe" or name == "clock" then
			local ring = box(.1,.1,.8,.8,true)
			ring.BackgroundTransparency = 1
			UI.new("UIStroke",{Color=root.ImageColor3,Thickness=2,Parent=ring})
			if name == "clock" then line(.5,.25,.5,.5);line(.5,.5,.7,.6)
			else line(.1,.5,.9,.5);line(.5,.1,.5,.9) end
		elseif name == "play" or name == "skip" then
			line(.3,.18,.7,.5);line(.7,.5,.3,.82);line(.3,.82,.3,.18)
		elseif name == "glove" then box(.2,.18,.55,.5,true);box(.3,.7,.4,.18);box(.7,.4,.16,.26,true)
		elseif name == "star" then
			line(.5,.12,.65,.42);line(.65,.42,.9,.45);line(.9,.45,.68,.64)
			line(.68,.64,.76,.9);line(.76,.9,.5,.74);line(.5,.74,.24,.9)
			line(.24,.9,.32,.64);line(.32,.64,.1,.45);line(.1,.45,.35,.42);line(.35,.42,.5,.12)
		elseif name == "hair" or name == "beard" then
			line(.23,.35,.23,.7);line(.23,.7,.5,.86);line(.5,.86,.77,.7);line(.77,.7,.77,.35)
			if name == "hair" then box(.2,.15,.6,.24);box(.2,.3,.12,.23)
			else line(.3,.58,.5,.7);line(.5,.7,.7,.58) end
		elseif name == "face" then
			local r=box(.16,.1,.68,.8,true);r.BackgroundTransparency=1
			UI.new("UIStroke",{Color=root.ImageColor3,Thickness=2,Parent=r})
			box(.32,.36,.08,.08,true);box(.6,.36,.08,.08,true);line(.34,.66,.66,.66)
		elseif name == "skin" then
			line(.5,.12,.25,.65);line(.25,.65,.5,.86);line(.5,.86,.75,.65);line(.75,.65,.5,.12)
		elseif name == "shorts" then
			box(.22,.2,.56,.18);box(.22,.38,.22,.44);box(.56,.38,.22,.44)
			line(.44,.38,.56,.38)
		elseif name == "rotate" then
			line(.24,.3,.7,.3);line(.7,.3,.82,.5);line(.82,.5,.7,.7);line(.7,.7,.25,.7)
			line(.24,.3,.4,.15);line(.24,.3,.4,.45)
		elseif name == "search" then
			local r=box(.12,.12,.56,.56,true);r.BackgroundTransparency=1
			UI.new("UIStroke",{Color=root.ImageColor3,Thickness=2,Parent=r});line(.6,.6,.87,.87)
		elseif name == "help" or name == "info" then
			local r=box(.12,.12,.76,.76,true);r.BackgroundTransparency=1
			UI.new("UIStroke",{Color=root.ImageColor3,Thickness=2,Parent=r})
			box(.46,.31,.08,.08,true);box(.46,.48,.08,.24)
		elseif name == "gear" then
			box(.28,.28,.44,.44,true)
			for i=0,3 do
				local p=box(.45,.08,.1,.84);p.Rotation=i*45
			end
		else
			-- Einfache, einheitliche neutrale Markierung fuer weitere Kategorien.
			line(.23,.25,.77,.25);line(.77,.25,.77,.75);line(.77,.75,.23,.75);line(.23,.75,.23,.25)
			line(.35,.5,.65,.5)
		end
		root:GetPropertyChangedSignal("ImageColor3"):Connect(function()
			for _, p in ipairs(pieces) do
				p.BackgroundColor3 = root.ImageColor3
				local stroke = p:FindFirstChildOfClass("UIStroke")
				if stroke then stroke.Color = root.ImageColor3 end
			end
		end)
		if props and props.Parent then root.Parent = props.Parent end
		return root
	end
	function UI.ring(parent, cut, color)
		return UI.chamfer({
			Name = "FocusRing", Size = UDim2.fromScale(1, 1), ImageColor3 = color or UI.C.red,
			ZIndex = 5, Visible = false, Parent = parent,
		}, "outline")
	end
	function UI.bar(props, color)
		local root = UI.new("Frame", {BackgroundColor3 = UI.C.bg3, BorderSizePixel = 0,
			Size = UDim2.new(1, 0, 0, 8), ClipsDescendants = true})
		for k,v in pairs(props or {}) do if k ~= "Parent" then root[k] = v end end
		UI.new("UICorner", {CornerRadius = UDim.new(0, 4), Parent = root})
		local fill = UI.new("Frame", {Name = "Fill", BackgroundColor3 = color or UI.C.red,
			BorderSizePixel = 0, Size = UDim2.fromScale(0, 1), Parent = root})
		if props.Parent then root.Parent = props.Parent end
		return root, fill
	end
	local originalSwatch = UI.swatch
	function UI.swatch(opts)
		local p = table.clone(opts)
		p.Size = UDim2.fromOffset(46,46)
		return originalSwatch(p)
	end
	function UI.reduceMotion()
		local p = game:GetService("Players").LocalPlayer
		return p and (p:GetAttribute("CC_ReduceMotion") == true or p:GetAttribute("CC_ReduceFX") == true)
	end
end


-- Bestandsoberflaechen erhalten dieselben Tokens, ohne ihre Aktionen zu ersetzen.
function UI.theme(object)
	if object:GetAttribute("CC_NativeUI") then return end
	if object:IsA("UICorner") then
		if object.CornerRadius.Scale == 0 then object.CornerRadius = UDim.new(0, 4) end
	elseif object:IsA("UIStroke") then
		local round = object.Parent and object.Parent:FindFirstChildOfClass("UICorner")
		if not round or round.CornerRadius.Scale == 0 then object.Thickness = math.min(object.Thickness, 2) end
	elseif object:IsA("TextLabel") or object:IsA("TextButton") or object:IsA("TextBox") then
		local font = object.Font
		object.FontFace = (font == Enum.Font.GothamBlack or font == Enum.Font.ArialBold)
			and UI.F.title or (font == Enum.Font.GothamBold or font == Enum.Font.GothamSemibold)
			and UI.F.bold or UI.F.body
		object.TextStrokeTransparency = 1
		local old = object.TextColor3
		if math.min(old.R,old.G,old.B) > .85 then object.TextColor3 = UI.C.text end
	elseif object:IsA("Frame") or object:IsA("CanvasGroup") then
		local c = object.BackgroundColor3
		if object.BackgroundTransparency < .8 and math.max(c.R,c.G,c.B)<.3 and math.max(c.R,c.G,c.B)>.04 then
			object.BackgroundColor3 = UI.C.bg1
		end
	elseif object:IsA("UIGradient") and object.Color.Keypoints[1].Value ~= Color3.new(1,1,1) then
		object.Enabled = false
	end
end

return UI
