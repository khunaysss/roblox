-- ReplicatedStorage.CC_UI (ModuleScript)
-- Designsystem fuer Cage Champions: Farben, Schriften, selbst gezeichnete Icons und wiederverwendbare Bausteine.
-- Icons und abgeschraegte Flaechen werden zur Laufzeit per EditableImage aus eigenen Vektorformen gezeichnet
-- (Signed-Distance-Formen mit Kantenglaettung, einheitliche Strichstaerke). Keine Uploads, keine Toolbox-Grafiken.
-- Herkunft der Icons: komplett in dieser Datei definiert (ICONS), siehe UI_DESIGN_V01.md.
-- Faellt EditableImage aus, gibt es runde Ecken statt Abschraegungen und Knoepfe ohne Icon (Text bleibt).
local AssetService = game:GetService("AssetService")
local GuiService = game:GetService("GuiService")
local UIS = game:GetService("UserInputService")
local TweenService = game:GetService("TweenService")

local UI = {}

-- Farben: dunkles Anthrazit, weisse Schrift, blaues Arenalicht, Rot fuer Auswahl
UI.C = {
	bg0 = Color3.fromRGB(11, 12, 16),
	bg1 = Color3.fromRGB(21, 23, 29),
	bg2 = Color3.fromRGB(33, 36, 44),
	bg3 = Color3.fromRGB(48, 52, 63),
	line = Color3.fromRGB(70, 75, 90),
	text = Color3.fromRGB(242, 243, 246),
	dim = Color3.fromRGB(150, 156, 172),
	mute = Color3.fromRGB(96, 101, 116),
	red = Color3.fromRGB(214, 36, 46),
	redDark = Color3.fromRGB(120, 18, 26),
	blue = Color3.fromRGB(46, 124, 232),
	blueDark = Color3.fromRGB(20, 52, 110),
	gold = Color3.fromRGB(236, 190, 76),
	green = Color3.fromRGB(64, 186, 112),
	warn = Color3.fromRGB(242, 168, 42),
}
local MONT = "rbxasset://fonts/families/Montserrat.json"
UI.F = {
	title = Font.new(MONT, Enum.FontWeight.Heavy, Enum.FontStyle.Italic),
	head = Font.new(MONT, Enum.FontWeight.ExtraBold, Enum.FontStyle.Italic),
	bold = Font.new(MONT, Enum.FontWeight.Bold),
	body = Font.new(MONT, Enum.FontWeight.Medium),
}

---------------------------------------------------------------------------------------------------
-- Vektor-Rasterer (Abstandsfunktionen im 64er-Raster, negativ = innen)
---------------------------------------------------------------------------------------------------
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

local W = 5.5                                  -- einheitliche Strichstaerke (bei 64 Einheiten)
local ICONS = {
	-- Karriere: Pokal
	trophy = function()
		return S.union(
			S.poly({ 19, 11, 45, 11, 45, 21, 41, 31, 32, 37, 23, 31, 19, 21 }),
			S.cut(S.ring(18, 20, 7, W), S.box(24, 20, 6, 12)),
			S.cut(S.ring(46, 20, 7, W), S.box(40, 20, 6, 12)),
			S.box(32, 42, 3, 6),
			S.box(32, 51, 12, 3.5, 1.5))
	end,
	-- Online: Globus
	globe = function()
		local pts = {}
		for i = 0, 24 do local a = math.rad(i * 15); table.insert(pts, 32 + math.cos(a) * 9); table.insert(pts, 32 + math.sin(a) * 22) end
		return S.union(S.ring(32, 32, 22, W), S.line(pts, W * 0.8), S.seg(11, 32, 53, 32, W * 0.8),
			S.seg(15, 21, 49, 21, W * 0.7), S.seg(15, 43, 49, 43, W * 0.7))
	end,
	-- Training: Hantel
	dumbbell = function()
		return S.union(S.seg(16, 32, 48, 32, W), S.box(17, 32, 4, 12, 1.5), S.box(47, 32, 4, 12, 1.5),
			S.box(9.5, 32, 2.6, 7.5, 1.2), S.box(54.5, 32, 2.6, 7.5, 1.2))
	end,
	-- Mein Kaempfer: Kopf und Schultern
	fighter = function()
		return S.union(S.circle(32, 21, 10.5), S.both(S.circle(32, 58, 21), S.box(32, 46, 30, 9)))
	end,
	-- Einstellungen: Zahnrad
	gear = function()
		local parts = { S.circle(32, 32, 17) }
		for k = 0, 7 do
			local a = k * math.pi / 4
			table.insert(parts, S.box(32 + math.cos(a) * 21, 32 + math.sin(a) * 21, 5, 4.2, 1, a))
		end
		return S.cut(S.union(table.unpack(parts)), S.circle(32, 32, 7.5))
	end,
	menu = function() return S.union(S.seg(14, 18, 50, 18, W), S.seg(14, 32, 50, 32, W), S.seg(14, 46, 50, 46, W)) end,
	-- Editor-Kategorien
	hair = function() return S.union(S.ring(32, 36, 17, W), S.cut(S.circle(32, 33, 19.5), S.box(32, 47, 24, 13))) end,
	beard = function() return S.union(S.ring(32, 30, 17, W), S.both(S.circle(32, 30, 19.5), S.box(32, 45, 24, 12))) end,
	face = function() return S.union(S.ring(32, 32, 22, W), S.circle(24, 27, 3.6), S.circle(40, 27, 3.6), S.arc(32, 33, 11, 25, 155, W * 0.8)) end,
	skin = function() return S.union(S.circle(32, 39, 15), S.poly({ 32, 7, 45.5, 31, 18.5, 31 })) end,
	shorts = function() return S.poly({ 13, 14, 51, 14, 54, 50, 37, 50, 32, 31, 27, 50, 10, 50 }) end,
	back = function() return S.line({ 38, 15, 22, 32, 38, 49 }, W + 1) end,
	next = function() return S.line({ 26, 15, 42, 32, 26, 49 }, W + 1) end,
	check = function() return S.line({ 15, 33, 27, 45, 49, 20 }, W + 1) end,
	close = function() return S.union(S.seg(18, 18, 46, 46, W + 1), S.seg(46, 18, 18, 46, W + 1)) end,
	lock = function()
		return S.union(
			S.cut(S.box(32, 41, 15, 12, 3), S.union(S.circle(32, 38, 3.5), S.box(32, 44, 1.6, 5))),
			S.arc(32, 25, 9.5, 180, 360, W), S.seg(22.5, 25, 22.5, 30, W), S.seg(41.5, 25, 41.5, 30, W))
	end,
	rotate = function()
		return S.union(S.arc(32, 32, 17, -60, 200, W), S.poly({ 40, 9, 52, 20, 37, 25 }))
	end,
	play = function() return S.poly({ 22, 13, 50, 32, 22, 51 }) end,
	search = function() return S.union(S.ring(28, 28, 14, W), S.seg(38, 38, 51, 51, W + 1.5)) end,
	user2 = function()                          -- zwei Kaempfer (Gegner gefunden)
		return S.union(S.circle(22, 23, 8), S.both(S.circle(22, 56, 16), S.box(22, 47, 20, 8)),
			S.circle(42, 23, 8), S.both(S.circle(42, 56, 16), S.box(42, 47, 20, 8)))
	end,
	glove = function()                          -- Boxhandschuh (Kampf)
		return S.union(S.cut(S.union(S.circle(30, 26, 15), S.box(30, 34, 15, 8, 6)), S.box(44, 32, 2, 8)),
			S.circle(45, 34, 5.5), S.box(30, 50, 12, 5, 1.5))
	end,
	star = function()
		local pts = {}
		for i = 0, 9 do
			local a = math.rad(-90 + i * 36); local r = i % 2 == 0 and 23 or 10
			table.insert(pts, 32 + math.cos(a) * r); table.insert(pts, 33 + math.sin(a) * r)
		end
		return S.poly(pts)
	end,
	clock = function() return S.union(S.ring(32, 32, 21, W), S.line({ 32, 18, 32, 32, 42, 38 }, W)) end,
	warn = function()
		return S.cut(S.poly({ 32, 8, 57, 53, 7, 53 }), S.union(S.box(32, 32, 2.6, 10, 1.2), S.circle(32, 46, 3)))
	end,
	-- Einstieg/Tutorial (gleiche Strichstaerke)
	run = function()                              -- laufende Figur mit Tempo-Strichen
		return S.union(S.circle(38, 12, 5.5), S.line({ 35, 21, 30, 36, 38, 44, 36, 56 }, W), S.line({ 30, 36, 22, 44, 14, 44 }, W),
			S.line({ 34, 23, 44, 30, 50, 26 }, W), S.line({ 34, 23, 24, 26, 20, 33 }, W),
			S.seg(6, 22, 16, 22, W * 0.7), S.seg(4, 30, 14, 30, W * 0.7))
	end,
	shield = function() return S.poly({ 32, 8, 51, 15, 49, 34, 32, 56, 15, 34, 13, 15 }) end,
	kick = function()                             -- Figur mit gestrecktem Bein
		return S.union(S.circle(18, 13, 5.5), S.line({ 20, 21, 26, 36 }, W), S.line({ 26, 36, 24, 54 }, W), S.line({ 26, 36, 54, 28 }, W),
			S.line({ 21, 25, 12, 34 }, W), S.line({ 21, 25, 31, 22 }, W))
	end,
	wrestle = function()                          -- zwei Figuren im Griff
		return S.union(S.circle(18, 14, 5.5), S.circle(46, 22, 5.5), S.line({ 20, 22, 28, 34, 22, 54 }, W), S.line({ 28, 34, 34, 54 }, W),
			S.line({ 44, 30, 36, 36, 42, 54 }, W), S.line({ 36, 36, 50, 54 }, W), S.line({ 22, 26, 38, 32 }, W))
	end,
	octagon = function()
		local pts = {}
		for i = 0, 8 do local a = math.rad(22.5 + i * 45); table.insert(pts, 32 + math.cos(a) * 23); table.insert(pts, 32 + math.sin(a) * 23) end
		local inner = {}
		for i = 0, 8 do local a = math.rad(22.5 + i * 45); table.insert(inner, 32 + math.cos(a) * 14); table.insert(inner, 32 + math.sin(a) * 14) end
		return S.union(S.line(pts, W), S.line(inner, W * 0.6))
	end,
	skip = function() return S.union(S.poly({ 14, 14, 40, 32, 14, 50 }), S.box(46, 32, 3.2, 18, 1)) end,
	mouse = function()                            -- Maus, linke Taste betont
		return S.union(S.outline(S.box(32, 34, 14, 21, 13), W * 0.8), S.seg(32, 13, 32, 27, W * 0.7), S.both(S.box(32, 34, 14, 21, 13), S.box(25, 20, 7, 7)))
	end,
	help = function()
		return S.union(S.ring(32, 32, 22, W), S.arc(32, 25, 7.5, 180, 405, W * 0.9), S.seg(32, 32, 32, 37, W * 0.9), S.circle(32, 45, 3))
	end,
	info = function() return S.union(S.ring(32, 32, 22, W), S.box(32, 36, 2.6, 9, 1.2), S.circle(32, 21, 3.2)) end,
	coach = function()                            -- Kopf mit Kappe
		return S.union(S.both(S.circle(32, 26, 15), S.box(32, 19, 16, 8)), S.box(40, 26, 13, 2.6, 1.2),
			S.ring(32, 32, 11, W * 0.8), S.both(S.circle(32, 66, 24), S.box(32, 55, 26, 8)))
	end,
}
UI.IconNames = {}
for k in pairs(ICONS) do table.insert(UI.IconNames, k) end

local cache, eiOk = {}, true
local function raster(size, f, unit)
	if not eiOk then return nil end
	local ok, img = pcall(function() return AssetService:CreateEditableImage({ Size = Vector2.new(size, size) }) end)
	if not ok or not img then eiOk = false; warn("[CC_UI] EditableImage nicht verfuegbar: ", img); return nil end
	local buf = buffer.create(size * size * 4)
	local k = unit / size
	for py = 0, size - 1 do
		for px = 0, size - 1 do
			local d = f((px + 0.5) * k, (py + 0.5) * k) / k          -- Abstand in Pixeln
			local a = clamp(0.5 - d, 0, 1)
			local o = (py * size + px) * 4
			buffer.writeu8(buf, o, 255); buffer.writeu8(buf, o + 1, 255); buffer.writeu8(buf, o + 2, 255)
			buffer.writeu8(buf, o + 3, math.floor(a * 255 + 0.5))
		end
	end
	img:WritePixelsBuffer(Vector2.zero, Vector2.new(size, size), buf)
	return Content.fromObject(img)
end
function UI.iconContent(name, size)
	size = size or 64
	local key = name .. "@" .. size
	if cache[key] == nil then
		cache[key] = (ICONS[name] and raster(size, ICONS[name](), 64)) or false
	end
	return cache[key] or nil
end
-- Abgeschraegte Flaeche (oben links und unten rechts abgeschnitten), 9-Slice
local CH, CUT = 48, 12
local function chamferShape() return S.poly({ CUT, 0, CH, 0, CH, CH - CUT, CH - CUT, CH, 0, CH, 0, CUT }) end
function UI.chamferContent(kind)
	local key = "chamfer_" .. kind
	if cache[key] == nil then
		local f = chamferShape()
		if kind == "outline" then f = S.outline(f, 2.5) elseif kind == "outline_thick" then f = S.outline(f, 4) end
		cache[key] = raster(CH, f, CH) or false
	end
	return cache[key] or nil
end

---------------------------------------------------------------------------------------------------
-- Bausteine
---------------------------------------------------------------------------------------------------
function UI.new(class, props, children)
	local o = Instance.new(class)
	local parent
	for k, v in pairs(props or {}) do
		if k == "Parent" then parent = v else o[k] = v end
	end
	for _, c in ipairs(children or {}) do c.Parent = o end
	if parent then o.Parent = parent end
	return o
end

-- Flaeche mit Abschraegung; cut = Groesse der Schraege in Pixeln
function UI.chamfer(props, kind, cut)
	local content = UI.chamferContent(kind or "fill")
	local img = UI.new("ImageLabel", { BackgroundTransparency = 1, ScaleType = Enum.ScaleType.Slice,
		SliceCenter = Rect.new(CUT + 1, CUT + 1, CH - CUT - 1, CH - CUT - 1), SliceScale = (cut or 10) / CUT, BorderSizePixel = 0 })
	if content then
		img.ImageContent = content
	else
		img.BackgroundTransparency = props.ImageTransparency or 0
		img.BackgroundColor3 = props.ImageColor3 or UI.C.bg1
		UI.new("UICorner", { CornerRadius = UDim.new(0, 6), Parent = img })
	end
	for k, v in pairs(props) do
		if not content and (k == "ImageColor3" or k == "ImageTransparency") then continue end
		if k ~= "Parent" then img[k] = v end
	end
	if props.Parent then img.Parent = props.Parent end
	return img
end
function UI.panel(props)
	props.ImageColor3 = props.ImageColor3 or UI.C.bg1
	props.ImageTransparency = props.ImageTransparency or 0.02
	local cut = props.Cut; props.Cut = nil
	return UI.chamfer(props, "fill", cut or 16)
end

function UI.icon(name, props)
	local content = UI.iconContent(name, props and props.Res or 64)
	local img = UI.new("ImageLabel", { BackgroundTransparency = 1, Size = UDim2.fromOffset(32, 32), ImageColor3 = UI.C.text })
	if content then img.ImageContent = content else img.Visible = false end
	for k, v in pairs(props or {}) do if k ~= "Res" and k ~= "Parent" then img[k] = v end end
	if props and props.Parent then img.Parent = props.Parent end
	return img
end

function UI.label(props)
	local l = UI.new("TextLabel", { BackgroundTransparency = 1, FontFace = UI.F.body, TextColor3 = UI.C.text,
		TextXAlignment = Enum.TextXAlignment.Left, TextYAlignment = Enum.TextYAlignment.Center, Size = UDim2.new(1, 0, 0, 24), TextSize = 17, TextWrapped = true })
	for k, v in pairs(props) do if k ~= "Parent" then l[k] = v end end
	if props.Parent then l.Parent = props.Parent end
	return l
end

-- Fortschrittsbalken; liefert (Rahmen, Fuellung)
function UI.bar(props, color)
	local f = UI.new("Frame", { BackgroundColor3 = UI.C.bg3, BorderSizePixel = 0, Size = UDim2.new(1, 0, 0, 6) })
	for k, v in pairs(props) do if k ~= "Parent" then f[k] = v end end
	local fill = UI.new("Frame", { BackgroundColor3 = color or UI.C.red, BorderSizePixel = 0, Size = UDim2.fromScale(0, 1), Parent = f })
	if props.Parent then f.Parent = props.Parent end
	return f, fill
end

-- Roter Rahmen fuer Hover und Controller-Fokus (gleiches Aussehen fuer Maus und Controller);
-- das Roblox-Auswahlbild wird durch ein unsichtbares ersetzt.
function UI.ring(parent, cut, color)
	local content = UI.chamferContent("outline_thick")
	local r = UI.new("ImageLabel", { Name = "FocusRing", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ImageColor3 = color or UI.C.red,
		ScaleType = Enum.ScaleType.Slice, SliceCenter = Rect.new(CUT + 1, CUT + 1, CH - CUT - 1, CH - CUT - 1), SliceScale = (cut or 12) / CUT, ZIndex = 5, Visible = false, Parent = parent })
	if content then r.ImageContent = content else UI.new("UIStroke", { Color = color or UI.C.red, Thickness = 3, Parent = r }) end
	return r
end
local function selectionImage() return UI.new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }) end
UI.noSelectionImage = selectionImage

-- Knopf. opts: Parent, Text, Sub, Icon, Size, Style ("nav" | "primary" | "secondary" | "danger" | "ghost"),
-- LayoutOrder, Disabled, Badge, OnClick. Zustaende ueber Attribute "Selected" und "Disabled".
local STYLE = {
	nav = { bg = "bg1", tr = 0.03, hover = "bg2", sel = "red", title = 27, h = 76, cut = 16 },
	primary = { bg = "red", tr = 0, hover = "red", sel = "red", title = 22, h = 58 },
	secondary = { bg = "bg2", tr = 0, hover = "bg3", sel = "red", title = 20, h = 54 },
	danger = { bg = "bg2", tr = 0, hover = "redDark", sel = "red", title = 20, h = 54 },
	ghost = { bg = "bg1", tr = 0.1, hover = "bg2", sel = "red", title = 17, h = 44 },
}
function UI.button(opts)
	local st = STYLE[opts.Style or "secondary"]
	local b = UI.new("TextButton", { Text = "", AutoButtonColor = false, BackgroundTransparency = 1, BorderSizePixel = 0,
		Size = opts.Size or UDim2.new(1, 0, 0, st.h), LayoutOrder = opts.LayoutOrder or 0, Selectable = true, Name = opts.Name or (opts.Text or "Button") })
	b.SelectionImageObject = selectionImage()
	local bg = UI.chamfer({ Size = UDim2.fromScale(1, 1), ImageColor3 = UI.C[st.bg], ImageTransparency = st.tr, ZIndex = 1, Parent = b }, "fill", opts.Cut or st.cut or 12)
	local accent = UI.new("Frame", { BackgroundColor3 = UI.C.red, BorderSizePixel = 0, Size = UDim2.new(0, 6, 1, -16), Position = UDim2.fromOffset(0, 8),
		Visible = false, ZIndex = 3, Parent = b })
	local ring = UI.ring(b, opts.Cut or st.cut or 12, opts.Style == "primary" and UI.C.text or UI.C.red)
	local x = 18
	local icon
	if opts.Icon then
		local isz = opts.Style == "nav" and 40 or (opts.Style == "ghost" and 20 or 28)
		icon = UI.icon(opts.Icon, { Size = UDim2.fromOffset(isz, isz), AnchorPoint = Vector2.new(0, 0.5), Position = UDim2.new(0, x, 0.5, 0), ZIndex = 3, Parent = b })
		if icon.Visible then x += isz + 14 end
	end
	local center = not opts.Icon and opts.Style ~= "nav" and not opts.Sub
	local title = UI.label({ Text = opts.Text or "", FontFace = opts.Style == "nav" and UI.F.head or UI.F.bold, TextSize = st.title, ZIndex = 3,
		TextXAlignment = center and Enum.TextXAlignment.Center or Enum.TextXAlignment.Left, TextWrapped = false, TextTruncate = Enum.TextTruncate.AtEnd,
		Position = UDim2.new(0, center and 0 or x, 0, 0), Size = UDim2.new(1, center and 0 or -x - 12, opts.Sub and 0.58 or 1, 0), Parent = b })
	local sub
	if opts.Sub then
		title.TextYAlignment = Enum.TextYAlignment.Bottom
		sub = UI.label({ Text = opts.Sub, TextSize = 17, TextColor3 = UI.C.dim, ZIndex = 3, TextYAlignment = Enum.TextYAlignment.Top,
			TextWrapped = false, TextTruncate = Enum.TextTruncate.AtEnd, Position = UDim2.new(0, x, 0.6, 0), Size = UDim2.new(1, -x - 12, 0.4, 0), Parent = b })
	end
	local badge
	if opts.Badge then badge = UI.tag({ Text = opts.Badge, AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -14, 0.5, 0), ZIndex = 4, Parent = b }) end
	local hover, focus = false, false
	local function refresh()
		local dis, sel = b:GetAttribute("Disabled"), b:GetAttribute("Selected")
		local hot = (hover or focus) and not dis
		local col = sel and UI.C[st.sel] or (hot and UI.C[st.hover] or UI.C[st.bg])
		if opts.Style == "primary" and hot then col = UI.C.red:Lerp(Color3.new(1, 1, 1), 0.12) end
		if dis and opts.Style == "primary" then col = UI.C.bg2 end
		TweenService:Create(bg, TweenInfo.new(0.12), { ImageColor3 = col, ImageTransparency = (sel or hot) and 0 or st.tr }):Play()
		if not UI.chamferContent("fill") then bg.BackgroundColor3 = col end
		accent.Visible = (hot and not sel and opts.Style ~= "primary")
		ring.Visible = hot
		local fg = dis and UI.C.mute or UI.C.text
		title.TextColor3 = fg
		if icon then icon.ImageColor3 = fg end
		if sub then sub.TextColor3 = dis and UI.C.mute or (sel and UI.C.text or UI.C.dim) end
		b.Selectable = not dis
		b.Active = not dis
	end
	b.MouseEnter:Connect(function() hover = true; refresh() end)
	b.MouseLeave:Connect(function() hover = false; refresh() end)
	b.SelectionGained:Connect(function() focus = true; refresh() end)
	b.SelectionLost:Connect(function() focus = false; refresh() end)
	b.AttributeChanged:Connect(refresh)
	b:SetAttribute("Disabled", opts.Disabled or false)
	b.Activated:Connect(function()
		if b:GetAttribute("Disabled") then return end
		if opts.OnClick then opts.OnClick(b) end
	end)
	refresh()
	if opts.Parent then b.Parent = opts.Parent end
	return b, { title = title, sub = sub, icon = icon, badge = badge, bg = bg }
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
function UI.key(text, props)
	local k = UI.chamfer({ AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(30, 30), ImageColor3 = UI.C.text, ImageTransparency = 0 }, "fill", 6)
	UI.new("UIPadding", { PaddingLeft = UDim.new(0, 7), PaddingRight = UDim.new(0, 7), Parent = k })
	UI.label({ Text = text, FontFace = UI.F.bold, TextSize = 15, TextColor3 = UI.C.bg0, AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromScale(0, 1),
		TextXAlignment = Enum.TextXAlignment.Center, ZIndex = 3, Parent = k })
	for kk, v in pairs(props or {}) do if kk ~= "Parent" then k[kk] = v end end
	if props and props.Parent then k.Parent = props.Parent end
	return k
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
		local k = clamp(min(vp.Y / designH, vp.X / (designH * 1.5)), 0.5, 1.6)
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

return UI
