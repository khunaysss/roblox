"""Autobahn-Rundkurs fuer "Roll a Meme" (Ghost-Driver-Stil).

In Blender: Scripting-Tab -> Datei oeffnen -> Run Script.
Headless:   blender -b -P autobahn_strecke.py -- --export <ordner>

1 Blender-Einheit = 1 Roblox-Stud. Z ist oben.
"""

import bpy
import math
import os
import sys
from mathutils import Vector

# --------------------------------------------------------------------------
# Einstellungen
# --------------------------------------------------------------------------
DS = 3.0                 # Abstand der Querschnitte entlang der Strecke (Studs)
CHUNK_SAMPLES = 134      # ~400 Studs pro Teilstueck (Roblox: max 2048 Studs / 20k Dreiecke pro MeshPart)

MEDIAN_HALF = 3.0        # Mittelstreifen
LANE_W = 14.0            # Spurbreite
LANES = 3                # Spuren pro Richtung
SHOULDER_W = 7.0         # Standstreifen
LANE_START = MEDIAN_HALF + 1.0
LANE_END = LANE_START + LANES * LANE_W               # 46
ROAD_HALF = LANE_END + SHOULDER_W + 4.0              # 57 (inkl. Platz fuer Leitplanke)
RAIL_X = ROAD_HALF - 2.0                             # 55
ROAD_THICK = 3.0

# Grobe Form des Rundkurses (x, y) – wird zu einer glatten Kurve
CONTROL_POINTS = [
    (0, 0), (700, 0), (1400, 0), (1950, 200), (2200, 650), (2100, 1150),
    (1700, 1400), (1250, 1300), (850, 1050), (450, 1150), (100, 1550),
    (-450, 1650), (-950, 1400), (-1150, 900), (-1000, 400), (-600, 50),
]

TUNNEL = (0.30, 0.355)                     # Anteil der Streckenlaenge
OVERPASSES = [0.17, 0.62, 0.86]
GANTRIES = [0.06, 0.44, 0.74, 0.93]

COLORS = {
    "Asphalt":   ((0.06, 0.06, 0.07), 0.9, 0.0),
    "Markierung": ((0.92, 0.92, 0.9), 0.6, 0.0),
    "Beton":     ((0.55, 0.55, 0.52), 0.85, 0.0),
    "Metall":    ((0.7, 0.72, 0.75), 0.35, 0.8),
    "Gras":      ((0.16, 0.38, 0.09), 1.0, 0.0),
    "Schild":    ((0.02, 0.18, 0.55), 0.5, 0.0),
    "Banner":    ((0.75, 0.05, 0.05), 0.6, 0.0),
    "Schwarz":   ((0.02, 0.02, 0.02), 0.7, 0.0),
}


# --------------------------------------------------------------------------
# Streckenverlauf
# --------------------------------------------------------------------------
def catmull_rom_closed(pts, steps=400, alpha=0.5):
    pts = [Vector((p[0], p[1], 0.0)) for p in pts]
    n = len(pts)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        t0 = 0.0
        t1 = t0 + (p1 - p0).length ** alpha
        t2 = t1 + (p2 - p1).length ** alpha
        t3 = t2 + (p3 - p2).length ** alpha
        for k in range(steps):
            t = t1 + (t2 - t1) * k / steps
            a1 = p0 * ((t1 - t) / (t1 - t0)) + p1 * ((t - t0) / (t1 - t0))
            a2 = p1 * ((t2 - t) / (t2 - t1)) + p2 * ((t - t1) / (t2 - t1))
            a3 = p2 * ((t3 - t) / (t3 - t2)) + p3 * ((t - t2) / (t3 - t2))
            b1 = a1 * ((t2 - t) / (t2 - t0)) + a2 * ((t - t0) / (t2 - t0))
            b2 = a2 * ((t3 - t) / (t3 - t1)) + a3 * ((t - t1) / (t3 - t1))
            out.append(b1 * ((t2 - t) / (t2 - t1)) + b2 * ((t - t1) / (t2 - t1)))
    return out


def resample_closed(dense, ds):
    cum = [0.0]
    for i in range(1, len(dense) + 1):
        cum.append(cum[-1] + (dense[i % len(dense)] - dense[i - 1]).length)
    total = cum[-1]
    n = max(8, round(total / ds))
    step = total / n
    pts, j = [], 0
    for k in range(n):
        s = k * step
        while cum[j + 1] < s:
            j += 1
        f = (s - cum[j]) / (cum[j + 1] - cum[j])
        pts.append(dense[j].lerp(dense[(j + 1) % len(dense)], f))
    return pts, total


def elevation(s, total):
    u = 2 * math.pi * s / total
    return 14.0 * math.sin(2 * u) + 6.0 * math.sin(5 * u + 1.0)


class Frame:
    __slots__ = ("p", "t", "n", "z", "s")


def build_frames():
    pts, total = resample_closed(catmull_rom_closed(CONTROL_POINTS), DS)
    n = len(pts)
    frames = []
    for i in range(n):
        t = (pts[(i + 1) % n] - pts[i - 1])
        t.z = 0.0
        t.normalize()
        f = Frame()
        f.s = i * total / n
        f.p = Vector((pts[i].x, pts[i].y, elevation(f.s, total)))
        f.t = t
        f.z = Vector((0, 0, 1))
        f.n = f.z.cross(t).normalized()  # links von Fahrtrichtung
        frames.append(f)
    return frames, total


def min_radius(frames):
    r = float("inf")
    n = len(frames)
    for i in range(n):
        a, b, c = frames[i - 1].p.xy, frames[i].p.xy, frames[(i + 1) % n].p.xy
        ab, bc, ca = (b - a).length, (c - b).length, (a - c).length
        area2 = abs((b - a).x * (c - a).y - (b - a).y * (c - a).x)
        if area2 > 1e-9:
            r = min(r, ab * bc * ca / (2 * area2))
    return r


# --------------------------------------------------------------------------
# Mesh-Bau
# --------------------------------------------------------------------------
class MeshBuilder:
    def __init__(self):
        self.verts, self.faces, self.uvs = [], [], []

    def add_vert(self, co):
        self.verts.append((co.x, co.y, co.z))
        return len(self.verts) - 1

    def add_face(self, cos, uvs, normal=None):
        if normal is not None:
            fn = (cos[1] - cos[0]).cross(cos[2] - cos[0])
            if fn.dot(normal) < 0:
                cos, uvs = cos[::-1], uvs[::-1]
        idx = [self.add_vert(c) for c in cos]
        self.faces.append(tuple(idx))
        self.uvs.append(list(uvs))


BUILDERS = {}
FRAMES = []
N = 0


def builder(cat, chunk):
    return BUILDERS.setdefault((cat, chunk), MeshBuilder())


def chunk_of(i):
    return min((i % N) // CHUNK_SAMPLES, (N - 1) // CHUNK_SAMPLES)


def local(i, x, z, along=0.0):
    f = FRAMES[i % N]
    return f.p + f.n * x + f.z * z + f.t * along


def extrude(cat, profile, i0, i1, closed=False, uv=8.0):
    """Profil (x, z) entlang Samples i0..i1 ziehen.

    Offene Profile von -x nach +x (ueber die Oberseite) angeben, geschlossene
    im Uhrzeigersinn (oben links -> oben rechts -> unten rechts -> unten links),
    dann zeigen die Normalen nach aussen.
    """
    prof = list(profile) + ([profile[0]] if closed else [])
    plen = [0.0]
    for a, b in zip(prof, prof[1:]):
        plen.append(plen[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))

    i = i0
    while i < i1:
        c = chunk_of(i)
        end = min(i1, (c + 1) * CHUNK_SAMPLES)
        mb = builder(cat, c)
        rows = []
        for k in range(i, end + 1):
            rows.append([mb.add_vert(local(k, x, z)) for x, z in prof])
        for r in range(len(rows) - 1):
            v0 = (i + r) * DS / uv
            v1 = (i + r + 1) * DS / uv
            for p in range(len(prof) - 1):
                a, b = rows[r][p], rows[r + 1][p]
                cc, d = rows[r + 1][p + 1], rows[r][p + 1]
                mb.faces.append((a, b, cc, d))
                u0, u1 = plen[p] / uv, plen[p + 1] / uv
                mb.uvs.append([(u0, v0), (u0, v1), (u1, v1), (u1, v0)])
        i = end


def box(cat, i, x, z, along, size_t, size_n, size_z, bottom=False, uv=8.0):
    f = FRAMES[i % N]
    c = local(i, x, z, along)
    ht, hn, hz = f.t * (size_t / 2), f.n * (size_n / 2), f.z * (size_z / 2)
    mb = builder(cat, chunk_of(i))
    faces = [
        (f.z, [c + hz - ht - hn, c + hz + ht - hn, c + hz + ht + hn, c + hz - ht + hn], size_t, size_n),
        (f.t, [c + ht - hn - hz, c + ht + hn - hz, c + ht + hn + hz, c + ht - hn + hz], size_n, size_z),
        (-f.t, [c - ht - hn - hz, c - ht + hn - hz, c - ht + hn + hz, c - ht - hn + hz], size_n, size_z),
        (f.n, [c + hn - ht - hz, c + hn + ht - hz, c + hn + ht + hz, c + hn - ht + hz], size_t, size_z),
        (-f.n, [c - hn - ht - hz, c - hn + ht - hz, c - hn + ht + hz, c - hn - ht + hz], size_t, size_z),
    ]
    if bottom:
        faces.append((-f.z, [c - hz - ht - hn, c - hz + ht - hn, c - hz + ht + hn, c - hz - ht + hn], size_t, size_n))
    for normal, cos, w, h in faces:
        mb.add_face(cos, [(0, 0), (w / uv, 0), (w / uv, h / uv), (0, h / uv)], normal)


def flat_quad(cat, i, x0, x1, a0, a1, z):
    mb = builder(cat, chunk_of(i))
    cos = [local(i, x0, z, a0), local(i, x1, z, a0), local(i, x1, z, a1), local(i, x0, z, a1)]
    mb.add_face(cos, [(0, 0), (1, 0), (1, 1), (0, 1)], FRAMES[i % N].z)


# --------------------------------------------------------------------------
# Streckenteile
# --------------------------------------------------------------------------
def build_road():
    extrude("Asphalt", [(-ROAD_HALF, 0), (ROAD_HALF, 0), (ROAD_HALF, -ROAD_THICK), (-ROAD_HALF, -ROAD_THICK)],
            0, N, closed=True)

    verge = [(ROAD_HALF, 0), (ROAD_HALF + 13, -0.5), (ROAD_HALF + 68, -1.5), (ROAD_HALF + 85, -14)]
    extrude("Gras", verge, 0, N, uv=16.0)
    extrude("Gras", [(-x, z) for x, z in reversed(verge)], 0, N, uv=16.0)


def build_markings():
    z = 0.06
    for side in (-1, 1):
        for cx, w in ((LANE_START - 0.5, 0.6), (LANE_END + 0.3, 0.6)):
            x = side * cx
            extrude("Markierung", [(x - w / 2, z), (x + w / 2, z)], 0, N)
        for lane in range(1, LANES):
            x = side * (LANE_START + lane * LANE_W)
            for i in range(N):
                if i % 10 < 4:  # 12 Studs Strich, 18 Studs Luecke
                    mb = builder("Markierung", chunk_of(i))
                    cos = [local(i, x - 0.25, z), local(i, x + 0.25, z), local(i + 1, x + 0.25, z), local(i + 1, x - 0.25, z)]
                    mb.add_face(cos, [(0, 0), (1, 0), (1, 1), (0, 1)], Vector((0, 0, 1)))


def build_barriers():
    jersey = [(-1.5, 0), (-1.5, 0.9), (-0.7, 2.4), (-0.5, 3.6), (0.5, 3.6), (0.7, 2.4), (1.5, 0.9), (1.5, 0)]
    extrude("Beton", jersey, 0, N)
    for side in (-1, 1):
        x = side * RAIL_X
        extrude("Metall", [(x - 0.2, 3.2), (x + 0.2, 3.2), (x + 0.2, 2.0), (x - 0.2, 2.0)], 0, N, closed=True)
        for i in range(0, N, 4):
            box("Metall", i, x + side * 0.45, 1.6, 0, 0.5, 0.5, 3.2)


def in_tunnel(i, margin=0):
    a, b = int(TUNNEL[0] * N) - margin, int(TUNNEL[1] * N) + margin
    return a <= i <= b


def build_lamps():
    for i in range(0, N, 20):
        if in_tunnel(i, 20):
            continue
        box("Metall", i, 0, 15, 0, 0.8, 0.8, 30)
        for side in (-1, 1):
            box("Metall", i, side * 7, 29.6, 0, 0.6, 14, 0.6)
            box("Metall", i, side * 14, 29.3, 0, 1.4, 3.5, 0.8)


def arch(half, wall_h, rise, steps=14):
    pts = [(half, 0.0), (half, wall_h)]
    for k in range(1, steps):
        th = math.pi * k / steps
        pts.append((half * math.cos(th), wall_h + rise * math.sin(th)))
    pts += [(-half, wall_h), (-half, 0.0)]
    return pts


def build_tunnel():
    i0, i1 = int(TUNNEL[0] * N), int(TUNNEL[1] * N)
    inner = arch(ROAD_HALF + 1, 12, 10)
    outer = arch(ROAD_HALF + 4, 12, 13)
    ring = inner + list(reversed(outer))  # innen rechts->links, aussen links->rechts
    extrude("Beton", ring, i0, i1, closed=True)

    for i, normal_sign in ((i0, -1), (i1, 1)):
        f = FRAMES[i % N]
        mb = builder("Beton", chunk_of(i))
        for k in range(len(inner) - 1):
            cos = [local(i, *inner[k]), local(i, *inner[k + 1]), local(i, *outer[k + 1]), local(i, *outer[k])]
            mb.add_face(cos, [(0, 0), (1, 0), (1, 1), (0, 1)], f.t * normal_sign)
        # Portal-Rahmen
        box("Beton", i, 0, 26.5, normal_sign * 1.5, 3, 2 * (ROAD_HALF + 6), 3)
        for side in (-1, 1):
            box("Beton", i, side * (ROAD_HALF + 5), 13, normal_sign * 1.5, 3, 4, 26)


def build_overpass(i):
    deck_top, deck_t = 27.0, 3.0
    span = ROAD_HALF + 85
    box("Beton", i, 0, deck_top - deck_t / 2, 0, 22, 2 * span, deck_t, bottom=True)
    box("Asphalt", i, 0, deck_top + 0.05, 0, 16, 2 * span, 0.1)
    for edge in (-1, 1):
        box("Beton", i, 0, deck_top + 1.5, edge * 10.25, 1.5, 2 * span, 3)
    for x in (-(ROAD_HALF + 6), 0, ROAD_HALF + 6):
        box("Beton", i, x, (deck_top - deck_t) / 2, 0, 6, 3.5 if x == 0 else 5, deck_top - deck_t)
    for side in (-1, 1):
        box("Beton", i, side * (span - 6), (deck_top - deck_t - 14) / 2, 0, 22, 12, deck_top - deck_t + 14)


def build_gantry(i, cat_board="Schild", full_banner=False):
    beam_z = 21.0
    for side in (-1, 1):
        box("Metall", i, side * (RAIL_X + 5), beam_z / 2 + 1, 0, 1.6, 1.6, beam_z + 2)
    box("Metall", i, 0, beam_z, 0, 1.5, 2 * (RAIL_X + 5) + 1.6, 2)
    box("Metall", i, 0, beam_z + 3.5, 0, 1.0, 2 * (RAIL_X + 5) + 1.6, 1)
    if full_banner:
        box(cat_board, i, 0, beam_z + 4.5, 0.9, 0.4, 2 * RAIL_X, 7)
        box(cat_board, i, 0, beam_z + 4.5, -0.9, 0.4, 2 * RAIL_X, 7)
    else:
        for side in (-1, 1):
            box(cat_board, i, side * 25, beam_z - 4, side * -0.9, 0.4, 30, 7)


def build_start():
    sq = 3.5
    for side in (-1, 1):
        for row in range(4):
            for col in range(int((LANE_END - LANE_START) / sq)):
                x0 = side * (LANE_START + col * sq)
                x1 = side * (LANE_START + (col + 1) * sq)
                cat = "Markierung" if (row + col) % 2 == 0 else "Schwarz"
                flat_quad(cat, 0, min(x0, x1), max(x0, x1), row * sq, (row + 1) * sq, 0.07)
    build_gantry(0, "Banner", full_banner=True)


def build_origin_marker():
    mb = builder("Origin", 0)
    c, h = Vector((0, 0, 0)), 0.5
    for normal in (Vector((1, 0, 0)), Vector((-1, 0, 0)), Vector((0, 1, 0)),
                   Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((0, 0, -1))):
        a = Vector((normal.y, normal.z, normal.x)) * h
        b = normal.cross(a)
        cos = [c + normal * h - a - b, c + normal * h + a - b, c + normal * h + a + b, c + normal * h - a + b]
        mb.add_face(cos, [(0, 0), (1, 0), (1, 1), (0, 1)], normal)


# --------------------------------------------------------------------------
# Blender-Objekte
# --------------------------------------------------------------------------
def make_material(name):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    color, rough, metal = COLORS.get(name, ((0.8, 0.8, 0.8), 0.5, 0.0))
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
    mat.diffuse_color = (*color, 1.0)
    return mat


def realize(collection):
    count_tris = 0
    for (cat, chunk), mb in sorted(BUILDERS.items()):
        name = "TrackOrigin" if cat == "Origin" else f"{cat}_{chunk:02d}"
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(mb.verts, [], mb.faces)
        uv_layer = mesh.uv_layers.new(name="UVMap")
        li = 0
        for face_uvs in mb.uvs:
            for uv in face_uvs:
                uv_layer.data[li].uv = uv
                li += 1
        mesh.update()
        mesh.validate()
        mesh.materials.append(make_material(cat))
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        tris = sum(len(f) - 2 for f in mb.faces)
        count_tris += tris
        if tris > 20000:
            print(f"WARNUNG: {name} hat {tris} Dreiecke (Roblox-Limit 20000)")
    return count_tris


def clean_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)


def weld_and_smooth(collection):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in collection.objects:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.remove_doubles(threshold=0.001)
        bpy.ops.object.mode_set(mode="OBJECT")
        try:
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
        except (AttributeError, RuntimeError):
            pass
        obj.select_set(False)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    bpy.ops.object.select_all(action="DESELECT")


# --------------------------------------------------------------------------
# Roblox-Daten fuer Verkehr / Spawn
# --------------------------------------------------------------------------
def to_roblox(v):
    return (v.x, v.z, -v.y)


def write_lanes_lua(path, total):
    step = 8
    lines = [
        "-- Automatisch erzeugt von blender/autobahn_strecke.py – nicht von Hand bearbeiten.",
        "-- Positionen sind relativ zum Teil 'TrackOrigin' im importierten Modell.",
        "local TrackLanes = {}",
        "",
        f"TrackLanes.Length = {total:.1f}",
        f"TrackLanes.LaneWidth = {LANE_W}",
        "",
    ]

    def lane_points(x, reverse):
        idx = list(range(0, N, step))
        if reverse:
            idx = [(-k) % N for k in idx]
        pts = []
        for i in idx:
            pts.append("\t\tVector3.new(%.2f, %.2f, %.2f)," % to_roblox(local(i, x, 0.0)))
        return pts

    for key, sign, reverse in (("Forward", -1, False), ("Backward", 1, True)):
        lines.append(f"TrackLanes.{key} = {{")
        for lane in range(LANES):
            x = sign * (LANE_START + LANE_W * (lane + 0.5))
            lines.append(f"\t{{ -- Spur {lane + 1} (1 = innen)")
            lines += lane_points(x, reverse)
            lines.append("\t},")
        lines.append("}")
        lines.append("")

    f0 = FRAMES[0]
    pos = to_roblox(local(-8, -(LANE_START + LANE_W * 1.5), 3.0))
    look = to_roblox(f0.t)
    lines += [
        "-- Spawnpunkt kurz vor der Startlinie, mittlere Spur, Blick in Fahrtrichtung",
        "TrackLanes.StartPosition = Vector3.new(%.2f, %.2f, %.2f)" % pos,
        "TrackLanes.StartDirection = Vector3.new(%.4f, %.4f, %.4f)" % look,
        "",
        "function TrackLanes.ToWorld(trackModel: Model, localPos: Vector3): Vector3",
        '\tlocal origin = trackModel:FindFirstChild("TrackOrigin", true) :: BasePart',
        "\treturn origin.CFrame:PointToWorldSpace(localPos)",
        "end",
        "",
        "function TrackLanes.StartCFrame(trackModel: Model): CFrame",
        "\tlocal pos = TrackLanes.ToWorld(trackModel, TrackLanes.StartPosition)",
        '\tlocal origin = trackModel:FindFirstChild("TrackOrigin", true) :: BasePart',
        "\tlocal dir = origin.CFrame:VectorToWorldSpace(TrackLanes.StartDirection)",
        "\treturn CFrame.lookAt(pos, pos + dir)",
        "end",
        "",
        "return TrackLanes",
        "",
    ]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main(export_dir=None):
    global FRAMES, N
    BUILDERS.clear()
    FRAMES, total = build_frames()
    N = len(FRAMES)

    clean_scene()
    coll = bpy.data.collections.new("Autobahn")
    bpy.context.scene.collection.children.link(coll)

    build_road()
    build_markings()
    build_barriers()
    build_lamps()
    build_tunnel()
    for frac in OVERPASSES:
        build_overpass(int(frac * N))
    for frac in GANTRIES:
        build_gantry(int(frac * N))
    build_start()
    build_origin_marker()

    tris = realize(coll)
    weld_and_smooth(coll)

    print(f"Streckenlaenge: {total:.0f} Studs, Querschnitte: {N}, "
          f"engster Kurvenradius: {min_radius(FRAMES):.0f} Studs, "
          f"Objekte: {len(coll.objects)}, Dreiecke: {tris}")

    if export_dir:
        os.makedirs(export_dir, exist_ok=True)
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.export_scene.fbx(
            filepath=os.path.join(export_dir, "Autobahn.fbx"),
            use_selection=True, axis_forward="-Z", axis_up="Y",
            bake_space_transform=True, apply_scale_options="FBX_SCALE_UNITS",
            mesh_smooth_type="FACE", object_types={"MESH"},
        )
        write_lanes_lua(os.path.join(export_dir, "TrackLanes.lua"), total)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(export_dir, "Autobahn.blend"), compress=True)
        print(f"Exportiert nach {export_dir}")


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = argv[argv.index("--export") + 1] if "--export" in argv else None
    main(out)
