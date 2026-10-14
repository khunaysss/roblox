"""Cage_Champions_Trainers_v02.blend -> Roblox-Export der sechs Stil-Trainer als stehende Figuren (v01). Die .blend wird nur gelesen.

Jeder Trainer in seiner Kampfhaltung (Frame 1 der Action <Name>_Stance_Idle), mittig auf den Ursprung verschoben (Fuesse z = 0).
Meshes nach Material getrennt (<Objekt>__<Material>), weil Roblox nur eine Farbe pro MeshPart kennt. Gleiches Verfahren wie
export_coach_roblox_v01.py.
Ausgabe: export/Trainers_v01_Roblox.fbx, export/Trainers_v01_data.luau, renders/trainers_roblox_v01_checks.json
Aufruf: blender -b --python export_trainers_roblox_v01.py
"""
import json, os
import bpy, bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Cage_Champions_Trainers_v02.blend")
FBX = os.path.join(HERE, "export", "Trainers_v01_Roblox.fbx")
DATA = os.path.join(HERE, "export", "Trainers_v01_data.luau")
REP = os.path.join(HERE, "renders", "trainers_roblox_v01_checks.json")
for p in (FBX, DATA):
    if os.path.exists(p): raise SystemExit(f"Datei existiert bereits, nicht ueberschrieben: {p}")
S = 1 / 0.28
NAMES = ["Mike_Tyson", "Muhammad_Ali", "Alex_Pereira", "Khabib_Nurmagomedov", "Saenchai", "Charles_Oliveira"]

bpy.ops.wm.open_mainfile(filepath=SRC)
scene = bpy.context.scene

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
                        if fn.type == "TEX_IMAGE" and fn.image and fn.image.pixels:
                            px = fn.image.pixels[:]; n4 = len(px) // 4
                            return [sum(px[i::4][:n4]) / n4 for i in range(3)]
                return list(bc.default_value[:3])
    if m: return list(m.diffuse_color[:3])
    return [0.6, 0.6, 0.6]

for name in NAMES:
    arm = bpy.data.objects[name + "_Armature"]
    arm.animation_data_create()
    arm.animation_data.action = bpy.data.actions[name + "_Stance_Idle"]
    if hasattr(arm.animation_data, "action_slot") and arm.animation_data.action_suitable_slots:
        arm.animation_data.action_slot = arm.animation_data.action_suitable_slots[0]
scene.frame_set(1)
bpy.context.view_layer.update()

dg = bpy.context.evaluated_depsgraph_get()
out_col = bpy.data.collections.new("CC_Export"); scene.collection.children.link(out_col)
data, outs, rep = {}, [], {}
for name in NAMES:
    arm = bpy.data.objects[name + "_Armature"]
    src = [o for o in arm.children if o.type == "MESH"]
    meshes = []
    for o in src:
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), depsgraph=dg)
        me.transform(o.matrix_world); meshes.append((o, me))
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for _, me in meshes:
        for v in me.vertices:
            for i in range(3): lo[i] = min(lo[i], v.co[i]); hi[i] = max(hi[i], v.co[i])
    shift = Matrix.Translation(Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z)))
    colors, tris = {}, 0
    for o, me in meshes:
        me.transform(shift)
        mats = [s.material for s in o.material_slots] or [None]
        used = sorted({p.material_index for p in me.polygons})
        tris += sum(len(p.vertices) - 2 for p in me.polygons)
        for mi in (used if len(used) > 1 else [used[0] if used else 0]):
            bm = bmesh.new(); bm.from_mesh(me)
            if len(used) > 1: bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index != mi], context="FACES")
            if not bm.faces: bm.free(); continue
            mat = mats[mi] if mi < len(mats) else None
            oname = o.name if len(used) <= 1 else f"{o.name}__{mat.name if mat else 'none'}"
            m2 = bpy.data.meshes.new(oname); bm.to_mesh(m2); bm.free()
            ob = bpy.data.objects.new(oname + "_X", m2); out_col.objects.link(ob); outs.append(ob)
            ob.name = oname  # Originalname ist durch das Quellobjekt belegt -> Suffix entfernen geht nur nach Umbenennen der Quelle
            colors[ob.name] = {"rgb": [round(srgb(c) * 255) for c in base_color(mat)], "mat": mat.name if mat else None}
        bpy.data.meshes.remove(me)
    data[name] = {"height": round((hi.z - lo.z) * S, 3), "colors": colors}
    rep[name] = {"height_m": round(hi.z - lo.z, 3), "width_m": round(hi.x - lo.x, 3), "parts": len(colors), "triangles": tris}

bpy.ops.object.select_all(action="DESELECT")
for ob in outs: ob.select_set(True)
bpy.context.view_layer.objects.active = outs[0]
bpy.ops.export_scene.fbx(filepath=FBX, use_selection=True, object_types={"MESH"}, global_scale=1.0, apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_NONE", axis_forward="-Z", axis_up="Y", use_mesh_modifiers=False, mesh_smooth_type="FACE",
    bake_anim=False, path_mode="AUTO")

def lua(v):
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, float): return repr(round(v, 4))
    if isinstance(v, int): return str(v)
    if isinstance(v, str): return '"' + v.replace('"', '\\"') + '"'
    if v is None: return "nil"
    if isinstance(v, list): return "{" + ", ".join(lua(x) for x in v) + "}"
    if isinstance(v, dict): return "{" + ", ".join(f"[{lua(k)}] = {lua(x)}" for k, x in v.items()) + "}"
lines = ["-- Erzeugt von export_trainers_roblox_v01.py aus Cage_Champions_Trainers_v02.blend (Stil-Trainer, Kampfhaltung).", "return {"]
for n in NAMES:
    lines.append(f"\t[{lua(n)}] = {{ height = {data[n]['height']}, colors = {{")
    for k in sorted(data[n]["colors"]): lines.append(f"\t\t[{lua(k)}] = {lua(data[n]['colors'][k])},")
    lines.append("\t} },")
lines.append("}")
open(DATA, "w", encoding="utf-8").write("\n".join(lines) + "\n")
rep["names"] = sorted(o.name for o in outs); rep["fbx_bytes"] = os.path.getsize(FBX)
json.dump(rep, open(REP, "w"), indent=1)
print("REPORT", json.dumps({k: v for k, v in rep.items() if k != "names"}))
print("NAMES", rep["names"][:8])
