"""main_coach_v03.blend -> Roblox-Export Haupttrainer als stehende Figur (v01). Die .blend wird nur gelesen, nicht gespeichert.

Zweck: Haupttrainer fuer den Einstieg (Begruessung im Gym, Tipps am Kaefigrand). Keine Kampfanimationen (anderes Skelett als der
Kaempfer), deshalb eine feste, entspannte Standhaltung: Haende per IK-Steuerung neben die Oberschenkel.
Ohne Pratzen, Bauchpolster und Riemen (Trainer steht nur und spricht).

Ausgabe:
  export/Main_Coach_v01_Roblox.fbx   Meshes in Weltkoordinaten (cm, -Z vorne, Y oben), nach Material getrennt (<Objekt>__<Material>),
                                     weil Roblox nur eine Farbe pro MeshPart kennt
  export/Main_Coach_v01_data.luau    colors (Mesh -> Farbe/Material), height (Studs), foot (Fusshoehe)
  renders/coach_roblox_v01_checks.json
Aufruf: blender -b --python export_coach_roblox_v01.py
"""
import json, os
import bpy, bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "main_coach_v03.blend")
FBX = os.path.join(HERE, "export", "Main_Coach_v01_Roblox.fbx")
DATA = os.path.join(HERE, "export", "Main_Coach_v01_data.luau")
REP = os.path.join(HERE, "renders", "coach_roblox_v01_checks.json")
for p in (FBX, DATA):
    if os.path.exists(p):
        raise SystemExit(f"Datei existiert bereits, nicht ueberschrieben: {p}")
S = 1 / 0.28
SKIP = ("Focus_Mitt", "Belly_Pad")

bpy.ops.wm.open_mainfile(filepath=SRC)
scene = bpy.context.scene
arm = bpy.data.objects["Main_Coach_Armature"]

# Standhaltung: IK-Haende neben die Oberschenkel (Schulter ~1,43 m, Arm ~0,56 m), Ellbogen nach hinten
def place(bone, world):
    pb = arm.pose.bones[bone]
    m = pb.matrix.copy()
    m.translation = arm.matrix_world.inverted() @ Vector(world)
    pb.matrix = m
    bpy.context.view_layer.update()
place("CTRL_IK_Hand_L", (0.36, 0.0, 0.90))
place("CTRL_IK_Hand_R", (-0.36, 0.0, 0.90))
place("CTRL_Pole_Elbow_L", (0.45, 0.45, 1.15))
place("CTRL_Pole_Elbow_R", (-0.45, 0.45, 1.15))
bpy.context.view_layer.update()
hl = arm.matrix_world @ arm.pose.bones["LeftHand"].head
hr = arm.matrix_world @ arm.pose.bones["RightHand"].head

def srgb(c): return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
def base_color(m):
    if m and m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                bc = n.inputs["Base Color"]
                if bc.is_linked:
                    for l in bc.links:
                        fn = l.from_node
                        if fn.type == "RGB": return list(fn.outputs[0].default_value[:3])
                        if fn.type == "VALTORGB":
                            els = fn.color_ramp.elements
                            return [sum(e.color[i] for e in els) / len(els) for i in range(3)]
                return list(bc.default_value[:3])
    if m: return list(m.diffuse_color[:3])
    return [0.6, 0.6, 0.6]

src = [o for o in arm.children if o.type == "MESH" and not any(s in o.name for s in SKIP)]
dg = bpy.context.evaluated_depsgraph_get()
out_col = bpy.data.collections.new("CC_Export"); scene.collection.children.link(out_col)
colors, outs, tris = {}, [], 0
lo, hi = Vector((1e9, 1e9, 1e9)), Vector((-1e9, -1e9, -1e9))
for o in src:
    oname = o.name
    o.name = oname + "__SRC"
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), depsgraph=dg)
    me.transform(o.matrix_world)
    for v in me.vertices:
        for i in range(3): lo[i] = min(lo[i], v.co[i]); hi[i] = max(hi[i], v.co[i])
    mats = [s.material for s in o.material_slots] or [None]
    used = sorted({p.material_index for p in me.polygons})
    tris += sum(len(p.vertices) - 2 for p in me.polygons)
    for mi in (used if len(used) > 1 else [used[0] if used else 0]):
        bm = bmesh.new(); bm.from_mesh(me)
        if len(used) > 1: bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index != mi], context="FACES")
        if not bm.faces: bm.free(); continue
        m2 = bpy.data.meshes.new(oname); bm.to_mesh(m2); bm.free()
        mat = mats[mi] if mi < len(mats) else None
        name = oname if len(used) <= 1 else f"{oname}__{mat.name if mat else 'none'}"
        ob = bpy.data.objects.new(name, m2); out_col.objects.link(ob); outs.append(ob)
        colors[ob.name] = {"rgb": [round(srgb(c) * 255) for c in base_color(mat)], "mat": mat.name if mat else None}
    bpy.data.meshes.remove(me)

bpy.ops.object.select_all(action="DESELECT")
for ob in outs: ob.select_set(True)
bpy.context.view_layer.objects.active = outs[0]
bpy.ops.export_scene.fbx(filepath=FBX, use_selection=True, object_types={"MESH"}, global_scale=1.0, apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_NONE", axis_forward="-Z", axis_up="Y", use_mesh_modifiers=False, mesh_smooth_type="FACE",
    bake_anim=False, path_mode="AUTO")

def lua(v):
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, (int, float)): return repr(round(v, 4)) if isinstance(v, float) else str(v)
    if isinstance(v, str): return '"' + v.replace('"', '\\"') + '"'
    if v is None: return "nil"
    if isinstance(v, list): return "{" + ", ".join(lua(x) for x in v) + "}"
    if isinstance(v, dict): return "{" + ", ".join(f"[{lua(k)}] = {lua(x)}" for k, x in v.items()) + "}"
height = (hi.z - lo.z) * S
lines = ["-- Erzeugt von export_coach_roblox_v01.py aus main_coach_v03.blend (Haupttrainer, Standhaltung).", "return {",
         f"\theight = {round(height, 3)}, foot = {round(lo.z * S, 3)},", "\tcolors = {"]
for n in sorted(colors): lines.append(f"\t\t[{lua(n)}] = {lua(colors[n])},")
lines += ["\t},", "}"]
open(DATA, "w", encoding="utf-8").write("\n".join(lines) + "\n")
rep = {"source": "main_coach_v03.blend (nur gelesen)", "meshes": len(outs), "triangles": tris, "height_m": round(hi.z - lo.z, 3),
       "width_m": round(hi.x - lo.x, 3), "depth_m": round(hi.y - lo.y, 3), "hand_L": [round(x, 3) for x in hl], "hand_R": [round(x, 3) for x in hr],
       "fbx_bytes": os.path.getsize(FBX)}
json.dump(rep, open(REP, "w"), indent=1)
print("REPORT", json.dumps(rep))
