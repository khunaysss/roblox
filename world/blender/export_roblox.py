"""Exportiert Figuren und Bauwerke als Luau-Bauskripte fuer Roblox Studio.

Jedes Blender-Teil wird zu einem Roblox-Part:
  Quader -> Part (Block), Zylinder -> Part (Cylinder), Kugel -> Part + SpecialMesh(Sphere),
  Kegel -> gestapelte Zylinder/Bloecke, Ring (Torus) -> Kreis aus kleinen Bloecken,
  Dreiecks-Prisma -> gestufte Platten (Lego-Look).
Koordinaten: Blender (Z oben, Front -Y) -> Roblox (Y oben, Front -Z).

Aufruf: python3 export_roblox.py
Ausgabe: world/roblox/*.lua
"""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
CHAR = os.path.join(HERE, "..", "..", "characters", "blender")
sys.path.insert(0, CHAR); sys.path.insert(0, HERE)
import bpy
from mathutils import Matrix, Vector
import avatar_lib as L
from avatar_lib import S
import roster
import designs, buildings

OUT = os.path.join(HERE, "..", "roblox")
C = Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0)))  # Blender -> Roblox (Rotation, det +1)
ROTZ = lambda a: Matrix(((math.cos(a), -math.sin(a), 0), (math.sin(a), math.cos(a), 0), (0, 0, 1)))
CYL_AXES = Matrix(((0, 1, 0), (0, 0, 1), (1, 0, 0)))  # Part-X = lokales Z (Zylinderachse)

def fmt(v):
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s

def mat_info(o):
    if not o.data.materials:
        return "#a0a0a0", 0
    m = o.data.materials[0]
    hexc = m.get("hex", "#a0a0a0")
    if m.get("emit", 0):
        return hexc, 1          # Neon
    if m.get("metal", 0) >= 0.5:
        return hexc, 2          # glaenzend
    if m.get("rough", 0.5) <= 0.1:
        return hexc, 3          # Glas-artig
    return hexc, 0

class Emitter:
    def __init__(self, scale):
        self.scale = scale
        self.rows = []

    def emit(self, o, kind, center_local, size_local, local_rot=Matrix.Identity(3)):
        mw = o.matrix_world
        loc, rot, sc = mw.decompose()
        R = rot.to_matrix()
        cw = mw @ Vector(center_local)
        p = (C @ cw) * self.scale
        A = C @ R @ local_rot
        size = []
        for i in range(3):
            col = local_rot.col[i]
            s_eff = math.sqrt(sum((col[k] * sc[k]) ** 2 for k in range(3)))
            size.append(max(size_local[i] * s_eff * self.scale, 0.05))
        hexc, mcode = mat_info(o)
        name = o.name.split(".")[0]
        r = [A[0][0], A[0][1], A[0][2], A[1][0], A[1][1], A[1][2], A[2][0], A[2][1], A[2][2]]
        self.rows.append("{" + ",".join([f'"{name}"', f'"{kind}"'] + [fmt(x) for x in size] + [fmt(x) for x in p] +
                                         [fmt(x) for x in r] + [f'"{hexc}"', str(mcode)]) + "}")

    def obj(self, o):
        if o.type != "MESH" or o.hide_render:
            return
        bb = [Vector(c) for c in o.bound_box]
        mn = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
        mx = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
        ctr, dim = (mn + mx) / 2, mx - mn
        prim = o.get("prim", "box")
        if prim == "box":
            self.emit(o, "B", ctr, dim)
        elif prim == "ball":
            self.emit(o, "S", ctr, dim)
        elif prim == "cyl" and o.get("verts", 24) == 3:
            r, h = o["r"], dim.z
            n = 8; dy = 1.5 * r / n
            for k in range(n):
                y = -r / 2 + (k + 0.5) * dy
                w = 2 * r * math.cos(math.pi / 6) * (r - y) / (1.5 * r)
                self.emit(o, "B", (ctr.x, y, ctr.z), (max(w, 0.05), dy, h))
        elif prim == "cyl":
            d = max(dim.x, dim.y)
            self.emit(o, "C", ctr, (dim.z, d, d), CYL_AXES)
        elif prim == "cone":
            r1, r2, h = o["r1"], o["r2"], o["h"]
            n = 4
            for k in range(n):
                t = (k + 0.5) / n
                r = r1 + (r2 - r1) * t
                if r < 0.02:
                    continue
                z = -h / 2 + t * h
                if o.get("verts", 24) <= 4:
                    sd = r * math.sqrt(2)
                    self.emit(o, "B", (0, 0, z), (sd, sd, h / n), ROTZ(math.pi / 4))
                else:
                    self.emit(o, "C", (0, 0, z), (h / n, 2 * r, 2 * r), CYL_AXES)
        elif prim == "torus":
            R, r = o["R"], o["r"]
            n = 18
            for k in range(n):
                a = 2 * math.pi * k / n
                self.emit(o, "B", (R * math.cos(a), R * math.sin(a), 0), (2 * math.pi * R / n * 1.08, 2 * r, 2 * r),
                          ROTZ(a + math.pi / 2))

def collect(scale):
    bpy.context.view_layer.update()
    e = Emitter(scale)
    for o in S.objs:
        if o.name in bpy.data.objects:
            e.obj(o)
    return e.rows

# ---------------------------------------------------------------- Luau-Vorlagen
BUILDER = r'''
local CollectionService = game:GetService("CollectionService")
local MATERIAL = {[0] = Enum.Material.SmoothPlastic, [1] = Enum.Material.Neon, [2] = Enum.Material.SmoothPlastic, [3] = Enum.Material.Glass}

-- Baut ein Model aus der Teile-Liste. Jede Zeile:
-- {Name, Art("B"=Block,"C"=Zylinder,"S"=Kugel), GroesseX,Y,Z, PosX,Y,Z, R00..R22 (Rotationsmatrix), Farbe, Material}
local function buildModel(name, rows, collide)
	local model = Instance.new("Model")
	model.Name = name
	local root = Instance.new("Part")
	root.Name = "RootPart"
	root.Size = Vector3.new(1, 1, 1)
	root.CFrame = CFrame.new(0, 0.5, 0)
	root.Transparency = 1
	root.Anchored = true
	root.CanCollide = false
	root.CanQuery = false
	root.CanTouch = false
	root.Parent = model
	model.PrimaryPart = root
	for _, r in ipairs(rows) do
		local part = Instance.new("Part")
		part.Name = r[1]
		if r[2] == "C" then
			part.Shape = Enum.PartType.Cylinder
		elseif r[2] == "S" then
			local mesh = Instance.new("SpecialMesh")
			mesh.MeshType = Enum.MeshType.Sphere
			mesh.Parent = part
		end
		part.Size = Vector3.new(r[3], r[4], r[5])
		part.CFrame = CFrame.new(r[6], r[7], r[8], r[9], r[10], r[11], r[12], r[13], r[14], r[15], r[16], r[17])
		part.Color = Color3.fromHex(r[18])
		part.Material = MATERIAL[r[19]] or Enum.Material.SmoothPlastic
		if r[19] == 2 then part.Reflectance = 0.25 end
		if r[19] == 3 then part.Transparency = 0.2 end
		part.TopSurface = Enum.SurfaceType.Smooth
		part.BottomSurface = Enum.SurfaceType.Smooth
		part.Anchored = true
		part.CanCollide = collide and string.sub(r[1], 1, 3) ~= "FX_"
		part.CastShadow = true
		part.Parent = model
	end
	return model
end

local function folder(parent, name)
	local f = parent:FindFirstChild(name)
	if not f then
		f = Instance.new("Folder")
		f.Name = name
		f.Parent = parent
	end
	return f
end
'''

def write_tier(tier, figs):
    lines = [f"-- Meme-Figuren: {tier} ({len(figs)} Figuren). Automatisch erzeugt aus characters/blender/roster.py.",
             "-- Ausfuehren in Roblox Studio (Command Bar oder MCP). Legt die Figuren als Vorlagen an:",
             f"-- ReplicatedStorage/MemeFigures/{tier}/<Name>. Erneutes Ausfuehren ersetzt sie.",
             BUILDER,
             "local FIGURES = {"]
    for key, name, rows in figs:
        lines.append(f'\t{{"{name}", "{key}", {{')
        lines += ["\t\t" + r + "," for r in rows]
        lines.append("\t}},")
    lines.append("}")
    lines.append(f'''
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local tierFolder = folder(folder(ReplicatedStorage, "MemeFigures"), "{tier}")
for i, fig in ipairs(FIGURES) do
	local old = tierFolder:FindFirstChild(fig[1])
	if old then old:Destroy() end
	local model = buildModel(fig[1], fig[3], false)
	model:SetAttribute("Tier", "{tier}")
	model:SetAttribute("Order", i)
	model:SetAttribute("Key", fig[2])
	CollectionService:AddTag(model, "MemeFigure")
	model.Parent = tierFolder
end
print("MemeFigures/{tier}: " .. #FIGURES .. " Figuren gebaut")
''')
    path = os.path.join(OUT, f"MemeFigures_{tier}.lua")
    open(path, "w").write("\n".join(lines))
    return path

def write_building(fname, model_name, rows, where, origin, extra="", collide=True, comment=""):
    lines = [f"-- {comment}", "-- Automatisch erzeugt aus world/blender. Ausfuehren in Roblox Studio (Command Bar oder MCP).",
             "-- Position anpassen: ORIGIN unten aendern oder das Model danach verschieben.", BUILDER,
             "local ROWS = {"]
    lines += ["\t" + r + "," for r in rows]
    lines.append("}")
    lines.append(f'''
local ORIGIN = CFrame.new({origin})
local parent = {where}
local old = parent:FindFirstChild("{model_name}")
if old then old:Destroy() end
local model = buildModel("{model_name}", ROWS, {"true" if collide else "false"})
{extra}
model:PivotTo(ORIGIN)
model.Parent = parent
print("{model_name} gebaut (" .. #ROWS .. " Teile)")
''')
    path = os.path.join(OUT, fname)
    open(path, "w").write("\n".join(lines))
    return path

def main():
    os.makedirs(OUT, exist_ok=True)
    total = 0
    for tier, items in roster.TIERS.items():
        figs = []
        for key, fn in items:
            name = key.split("_", 1)[1]
            L.reset(name)
            fn()
            L.tier_fx(tier)
            rows = collect(1.0)
            figs.append((key, name, rows))
            total += len(rows)
        p = write_tier(tier, figs)
        print("tier", tier, len(figs), "figs", os.path.getsize(p) // 1024, "KB", flush=True)
    print("parts total", total)

    # Podest A (ohne Figur)
    designs.figure_on = lambda *a, **k: None
    L.reset("PodestA"); designs.pod_classic()
    rows = collect(1.0)
    write_building("Podest_A.lua", "PodestA", rows, 'folder(game:GetService("ReplicatedStorage"), "MemeWorld")', "0, 0, 0",
                   comment="Podest A (klassisch) als Vorlage: ReplicatedStorage/MemeWorld/PodestA. Oberkante der Noppen: 2.2 Studs.")
    print("podest", len(rows))

    # Gebaeude: doppelte Groesse fuer Roblox
    buildings.scale_guy = lambda *a, **k: None
    L.reset("Tempel"); buildings.lm_temple()
    rows = collect(2.0)
    write_building("Tempel_B.lua", "Tempel", rows, 'folder(workspace, "MemeWorld")', "-150, 0, 0",
                   comment="Wahrzeichen B: Tempel. Wird in Workspace/MemeWorld/Tempel gebaut.")
    print("tempel", len(rows))

    L.reset("BossTurm"); buildings.tw_fortress()
    rows = collect(2.0)
    ladder = '''-- Leiter an der Rueckseite, damit Spieler aufs Dach (Boss-Arena) kommen
local ladder = Instance.new("TrussPart")
ladder.Name = "Leiter"
ladder.Size = Vector3.new(2, 46, 2)
ladder.CFrame = CFrame.new(0, 23, 13.4)
ladder.Color = Color3.fromHex("#5a3a22")
ladder.Anchored = true
ladder.Parent = model
local arena = Instance.new("Part")
arena.Name = "BossArena"
arena.Size = Vector3.new(22, 1, 22)
arena.CFrame = CFrame.new(0, 44.5, 0)
arena.Transparency = 1
arena.Anchored = true
arena.CanCollide = false
arena.Parent = model -- unsichtbarer Marker fuer das Boss-Skript (Mitte der Dachflaeche)'''
    write_building("BossTurm_A.lua", "BossTurm", rows, 'folder(workspace, "MemeWorld")', "150, 0, 0", extra=ladder,
                   comment="Boss-Turm A: Festung. Dach = Boss-Arena, Leiter an der Rueckseite.")
    print("turm", len(rows))

if __name__ == "__main__":
    main()
