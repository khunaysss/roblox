"""Verkehrsautos fuer "Roll a Meme".

In Blender: Scripting-Tab -> Datei oeffnen -> Run Script.
Headless:   blender -b -P autos.py -- --export <ordner>

1 Einheit = 1 Stud, Z oben, Front zeigt nach +Y (in Roblox nach -Z / LookVector).
Jedes Auto steht mit den Raedern auf Z=0, Mitte bei X=0/Y=0.
Pro Auto wird eine FBX exportiert, die Teile heissen <Auto>_<Material>.
"""

import bpy
import bmesh
import math
import os
import sys
from mathutils import Matrix, Vector

MATERIALS = ["Body", "Glass", "Trim", "Tire", "Rim", "Headlight", "Taillight", "Trailer"]
M = {name: i for i, name in enumerate(MATERIALS)}
COLORS = {
    "Body": ((0.55, 0.05, 0.05), 0.25, 0.6),
    "Glass": ((0.02, 0.03, 0.05), 0.05, 0.0),
    "Trim": ((0.03, 0.03, 0.03), 0.6, 0.0),
    "Tire": ((0.015, 0.015, 0.015), 0.9, 0.0),
    "Rim": ((0.6, 0.62, 0.65), 0.25, 1.0),
    "Headlight": ((1.0, 0.95, 0.8), 0.1, 0.0),
    "Taillight": ((0.8, 0.0, 0.0), 0.1, 0.0),
    "Trailer": ((0.85, 0.85, 0.85), 0.5, 0.0),
}

# t = 0 hinten, t = 1 vorne. Werte in Studs.
CARS = {
    "Limousine": dict(
        L=17.0, W=7.4, wheel_r=1.5, wheels=(0.17, 0.80), glass=(0.0, 1.0), roof_w=0.74,
        top=[(0, 2.7), (0.03, 3.35), (0.2, 3.6), (0.27, 3.65), (0.38, 5.0), (0.45, 5.25),
             (0.6, 5.25), (0.73, 3.85), (0.8, 3.62), (0.97, 3.25), (1, 2.6)],
        belt=[(0, 3.35), (1, 3.45)],
        bottom=[(0, 1.25), (0.04, 0.75), (0.96, 0.75), (1, 1.15)],
        width=[(0, 0.86), (0.04, 0.97), (0.12, 1), (0.88, 1), (0.97, 0.94), (1, 0.82)],
    ),
    "SUV": dict(
        L=18.0, W=7.8, wheel_r=1.85, wheels=(0.17, 0.81), glass=(0.0, 1.0), roof_w=0.8,
        top=[(0, 3.3), (0.02, 4.5), (0.06, 6.3), (0.1, 6.65), (0.62, 6.65), (0.74, 4.7),
             (0.8, 4.4), (0.97, 4.05), (1, 3.3)],
        belt=[(0, 4.4), (1, 4.5)],
        bottom=[(0, 1.6), (0.04, 1.05), (0.96, 1.05), (1, 1.55)],
        width=[(0, 0.9), (0.04, 0.98), (0.1, 1), (0.9, 1), (0.97, 0.96), (1, 0.86)],
    ),
    "Kompakt": dict(
        L=14.5, W=7.0, wheel_r=1.45, wheels=(0.16, 0.81), glass=(0.0, 1.0), roof_w=0.78,
        top=[(0, 3.0), (0.02, 3.9), (0.06, 5.0), (0.12, 5.3), (0.55, 5.3), (0.69, 3.75),
             (0.76, 3.5), (0.96, 3.15), (1, 2.6)],
        belt=[(0, 3.55), (1, 3.4)],
        bottom=[(0, 1.2), (0.04, 0.75), (0.96, 0.75), (1, 1.15)],
        width=[(0, 0.88), (0.04, 0.98), (0.1, 1), (0.9, 1), (0.97, 0.95), (1, 0.84)],
    ),
    "Sportwagen": dict(
        L=17.0, W=7.8, wheel_r=1.5, wheels=(0.16, 0.81), glass=(0.0, 1.0), roof_w=0.66,
        top=[(0, 2.5), (0.03, 3.05), (0.12, 3.25), (0.22, 3.4), (0.38, 4.3), (0.52, 4.4),
             (0.65, 3.35), (0.74, 2.95), (0.97, 2.4), (1, 1.95)],
        belt=[(0, 3.05), (0.5, 3.2), (1, 2.6)],
        bottom=[(0, 0.95), (0.04, 0.55), (0.96, 0.55), (1, 0.8)],
        width=[(0, 0.88), (0.05, 0.99), (0.18, 1), (0.85, 0.98), (0.97, 0.92), (1, 0.78)],
    ),
    "Transporter": dict(
        L=19.5, W=7.9, wheel_r=1.65, wheels=(0.18, 0.82), glass=(0.73, 1.0), roof_w=0.92,
        top=[(0, 8.2), (0.015, 8.6), (0.8, 8.6), (0.88, 6.9), (0.92, 4.75), (0.98, 4.35), (1, 3.4)],
        belt=[(0, 4.6), (1, 4.6)],
        bottom=[(0, 1.4), (0.03, 0.95), (0.96, 0.95), (1, 1.35)],
        width=[(0, 0.97), (0.02, 1), (0.95, 1), (1, 0.9)],
    ),
    "LKW": dict(  # Zugmaschine, Auflieger wird extra gebaut
        L=9.5, W=8.4, wheel_r=1.9, wheels=(0.22, 0.78), glass=(0.6, 1.0), roof_w=0.94,
        top=[(0, 12.0), (0.04, 12.4), (0.85, 12.4), (0.93, 11.2), (0.97, 6.6), (1, 5.4)],
        belt=[(0, 7.4), (1, 7.4)],
        bottom=[(0, 2.4), (0.04, 1.6), (1, 1.6)],
        width=[(0, 1), (0.95, 1), (1, 0.94)],
        trailer=dict(L=34.0, H0=4.2, H1=13.2, gap=1.2, axles=(0.08, 0.17, 0.26)),
    ),
}


def keyed(keys, t):
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            u = (t - t0) / (t1 - t0)
            u = u * u * (3 - 2 * u)
            return v0 + (v1 - v0) * u
    return keys[-1][1]


# --------------------------------------------------------------------------
# Bausteine
# --------------------------------------------------------------------------
def merge(dst, src, mat):
    for f in src.faces:
        f.material_index = M[mat]
    mesh = bpy.data.meshes.new("tmp")
    src.to_mesh(mesh)
    src.free()
    dst.from_mesh(mesh)
    bpy.data.meshes.remove(mesh)


def add_box(bm, center, size, mat, bevel=0.0):
    tmp = bmesh.new()
    mtx = Matrix.Translation(Vector(center)) @ Matrix.Diagonal((*size, 1.0))
    bmesh.ops.create_cube(tmp, size=1.0, matrix=mtx)
    if bevel > 0:
        bmesh.ops.bevel(tmp, geom=list(tmp.edges), offset=bevel, segments=2,
                        profile=0.5, affect="EDGES", clamp_overlap=True)
    merge(bm, tmp, mat)


def add_wheel(bm, x, y, r, width):
    rot = Matrix.Rotation(math.radians(90), 4, "Y")
    tmp = bmesh.new()
    bmesh.ops.create_cone(tmp, cap_ends=True, cap_tris=False, segments=24, radius1=r, radius2=r,
                          depth=width, matrix=Matrix.Translation((x, y, r)) @ rot)
    rim_edges = [e for e in tmp.edges
                 if sorted(abs(f.normal.x) > 0.9 for f in e.link_faces) == [False, True]]
    bmesh.ops.bevel(tmp, geom=rim_edges,
                    offset=r * 0.12, segments=2, profile=0.5, affect="EDGES", clamp_overlap=True)
    merge(bm, tmp, "Tire")
    side = 1 if x > 0 else -1
    tmp = bmesh.new()
    bmesh.ops.create_cone(tmp, cap_ends=True, cap_tris=False, segments=12, radius1=r * 0.62,
                          radius2=r * 0.55, depth=0.12,
                          matrix=Matrix.Translation((x + side * (width / 2 + 0.02), y, r)) @
                          Matrix.Rotation(math.radians(90 * side), 4, "Y"))
    merge(bm, tmp, "Rim")


def loft_body(bm, spec, y0=0.0):
    """Karosserie aus Querschnitten entlang Y aufbauen."""
    L, W2, r = spec["L"], spec["W"] / 2, spec["wheel_r"]
    wheel_y = [(-0.5 + t) * L for t in spec["wheels"]]
    arch_r = r + 0.35
    stations = 56
    ts = [0.5 - 0.5 * math.cos(math.pi * k / stations) for k in range(stations + 1)]

    rings, meta = [], []
    for t in ts:
        y = (-0.5 + t) * L
        w = W2 * keyed(spec["width"], t)
        zb_nom = keyed(spec["bottom"], t)
        zb = zb_nom
        for wy in wheel_y:
            dy = y - wy
            if abs(dy) < arch_r:
                zb = max(zb, r + math.sqrt(arch_r * arch_r - dy * dy))
        belt = keyed(spec["belt"], t)
        top = max(keyed(spec["top"], t), belt + 0.12)
        mid = max(zb + 0.05, 0.5 * (zb_nom + belt))
        g = spec["roof_w"]
        green = top - belt

        right = [
            (0.0, zb), (0.78 * w, zb), (0.95 * w, zb + 0.12), (w, mid),
            (0.995 * w, belt - 0.25), (0.975 * w, belt),
        ]
        for k in range(1, 4):
            u = k / 4
            right.append(((0.95 - (0.95 - g) * u) * w, belt + green * (0.03 + 0.85 * u)))
        right += [(g * 0.8 * w, top - 0.05 * green), (0.0, top)]
        fixed = []
        last_z = -1.0
        for x, z in right:
            z = max(z, last_z + 0.01)
            fixed.append((x, z))
            last_z = z
        ring = fixed + [(-x, z) for x, z in reversed(fixed[1:-1])]
        rings.append([bm.verts.new((x, y0 + y, z)) for x, z in ring])
        meta.append((t, belt, green, zb_nom))

    gl0, gl1 = spec["glass"]
    b_pillar = (spec["wheels"][0] + spec["wheels"][1]) / 2 - 0.02
    for s in range(len(rings) - 1):
        ra, rb = rings[s], rings[s + 1]
        t, belt, green, zb_nom = meta[s]
        t_next = meta[s + 1][0]
        for k in range(len(ra)):
            f = bm.faces.new((ra[k], rb[k], rb[(k + 1) % len(rb)], ra[(k + 1) % len(ra)]))
            f.normal_update()
            c = f.calc_center_median()
            n = f.normal
            mat = "Body"
            tc = 0.5 * (t + t_next)
            if green > 0.45 and c.z > belt + 0.08 and n.z < 0.82 and gl0 <= tc <= gl1:
                mat = "Glass"
                if abs(tc - b_pillar) < 0.012 and abs(n.x) > 0.5:
                    mat = "Body"
            if c.z < zb_nom + 0.4 and abs(n.z) < 0.9:
                mat = "Trim"
            f.material_index = M[mat]
    for ring, sign in ((rings[0], -1), (rings[-1], 1)):
        f = bm.faces.new(ring if sign > 0 else list(reversed(ring)))
        f.material_index = M["Body"]
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))

    for wy in wheel_y:
        for side in (-1, 1):
            add_wheel(bm, side * (W2 - 0.5), y0 + wy, r, 0.95)

    # Lichter, Grill, Spiegel
    front_y, rear_y = y0 + L / 2, y0 - L / 2
    hl_z = keyed(spec["belt"], 0.98) - 0.45
    tl_z = keyed(spec["belt"], 0.02) - 0.35
    for side in (-1, 1):
        add_box(bm, (side * 0.66 * W2, front_y - 0.35, hl_z), (0.3 * W2 * 2 * 0.55, 0.8, 0.55), "Headlight", 0.1)
        add_box(bm, (side * 0.72 * W2, rear_y + 0.35, tl_z), (0.25 * W2 * 2 * 0.55, 0.8, 0.6), "Taillight", 0.1)
        top = spec["top"]
        j = max(k for k, (t, v) in enumerate(top) if v > keyed(spec["belt"], t) + 1.2)
        t_ws = top[min(j + 1, len(top) - 1)][0]
        add_box(bm, (side * (keyed(spec["width"], t_ws) * W2 + 0.3), y0 + (-0.5 + t_ws) * L - 0.6,
                     keyed(spec["belt"], t_ws) + 0.35), (0.7, 0.35, 0.45), "Body", 0.08)
    add_box(bm, (0, front_y - 0.3, hl_z - 0.5), (0.7 * W2, 0.7, 0.75), "Trim", 0.1)
    add_box(bm, (0, front_y - 0.35, keyed(spec["bottom"], 1) + 0.25), (1.6 * W2, 0.8, 0.45), "Trim", 0.1)
    add_box(bm, (0, rear_y + 0.35, keyed(spec["bottom"], 0) + 0.25), (1.6 * W2, 0.8, 0.45), "Trim", 0.1)


def build_trailer(bm, spec):
    tr = spec["trailer"]
    W2 = spec["W"] / 2
    cab_rear = -spec["L"] / 2
    y1 = cab_rear - tr["gap"] + 2.5      # Sattel ragt etwas ueber die Zugmaschine
    y0 = y1 - tr["L"]
    add_box(bm, (0, (y0 + y1) / 2, (tr["H0"] + tr["H1"]) / 2), (W2 * 2, tr["L"], tr["H1"] - tr["H0"]), "Trailer", 0.25)
    add_box(bm, (0, (y0 + y1) / 2, tr["H0"] - 0.5), (W2 * 1.7, tr["L"] - 1, 1.0), "Trim", 0.05)
    add_box(bm, (0, cab_rear - 2.5, 2.4), (W2 * 1.2, 6.0, 1.2), "Trim", 0.05)
    r = spec["wheel_r"]
    for a in tr["axles"]:
        wy = y0 + a * tr["L"]
        for side in (-1, 1):
            add_wheel(bm, side * (W2 - 0.55), wy, r, 1.0)
    for side in (-1, 1):
        add_box(bm, (side * 0.75 * W2, y0 - 0.1, tr["H0"] + 0.4), (1.6, 0.4, 0.7), "Taillight", 0.08)
    for side in (-1, 1):
        add_box(bm, (side * (W2 - 0.1), y0 + tr["L"] * 0.3, tr["H0"] - 0.6), (0.2, tr["L"] * 0.25, 1.2), "Trim")
    return y0


# --------------------------------------------------------------------------
# Blender-Objekte
# --------------------------------------------------------------------------
def material(name):
    mat = bpy.data.materials.get("Auto_" + name) or bpy.data.materials.new("Auto_" + name)
    mat.use_nodes = True
    color, rough, metal = COLORS[name]
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if name in ("Headlight", "Taillight"):
        bsdf.inputs["Emission Color"].default_value = (*color, 1)
        bsdf.inputs["Emission Strength"].default_value = 2.0
    mat.diffuse_color = (*color, 1)
    return mat


def build_car(name, spec, collection):
    bm = bmesh.new()
    if "trailer" in spec:
        # Zugmaschine vorne, Auflieger dahinter -> gesamtes Fahrzeug um Y=0 zentrieren
        tr = spec["trailer"]
        total = spec["L"] + tr["L"] - 2.5 + tr["gap"]
        y_cab = total / 2 - spec["L"] / 2
        loft_body(bm, spec, 0.0)
        build_trailer(bm, spec)
        bmesh.ops.translate(bm, verts=list(bm.verts), vec=(0, y_cab, 0))
    else:
        loft_body(bm, spec)

    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.0005)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for mname in MATERIALS:
        mesh.materials.append(material(mname))
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)

    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.separate(type="MATERIAL")
    bpy.ops.object.mode_set(mode="OBJECT")

    parts = []
    for part in list(collection.objects):
        if part.type != "MESH" or not (part == obj or part.name.startswith(name + ".")):
            continue
        if not part.data.polygons:
            bpy.data.objects.remove(part)
            continue
        mat = part.data.materials[part.data.polygons[0].material_index]
        mname = mat.name.removeprefix("Auto_")
        part.data.materials.clear()
        part.data.materials.append(mat)
        for p in part.data.polygons:
            p.material_index = 0
        part.name = f"{name}_{mname}"
        part.data.name = part.name
        parts.append(part)

    bpy.ops.object.select_all(action="DESELECT")
    for part in parts:
        part.select_set(True)
        bpy.context.view_layer.objects.active = part
        try:
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
        except (AttributeError, RuntimeError):
            pass
        part.select_set(False)
    tris = sum(len(p.data.polygons) for p in parts)
    print(f"{name}: {len(parts)} Teile, ~{tris} Polygone")
    return parts


def main(export_dir=None):
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    coll = bpy.data.collections.get("Autos") or bpy.data.collections.new("Autos")
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)

    all_parts = {}
    for name, spec in CARS.items():
        all_parts[name] = build_car(name, spec, coll)

    if export_dir:
        os.makedirs(os.path.join(export_dir, "autos"), exist_ok=True)
        for name, parts in all_parts.items():
            bpy.ops.object.select_all(action="DESELECT")
            for p in parts:
                p.select_set(True)
            bpy.ops.export_scene.fbx(
                filepath=os.path.join(export_dir, "autos", f"{name}.fbx"),
                use_selection=True, axis_forward="-Z", axis_up="Y",
                bake_space_transform=True, apply_scale_options="FBX_SCALE_UNITS",
                object_types={"MESH"},
            )

    # Zum Anschauen nebeneinander aufstellen
    x = 0.0
    for name, parts in all_parts.items():
        for p in parts:
            p.location.x = x
        x += CARS[name]["W"] + 6

    if export_dir:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(export_dir, "Autos.blend"), compress=True)
        print(f"Exportiert nach {export_dir}")


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    main(argv[argv.index("--export") + 1] if "--export" in argv else None)
