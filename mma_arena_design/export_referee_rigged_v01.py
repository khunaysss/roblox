"""Ringrichter als animierbares Roblox-Modell (v01), Kopie von export_trainer_rigged_v01.py. referee_v02.blend wird nur gelesen.

Ziel: Die Trainer spielen dieselben Animationen wie der Kaempfer (Bones mit gleichen Namen und Hierarchie). Das Trainer-Skelett
hat gleiche Namen, aber eine bis zu 14 Grad andere Ruhehaltung (Unterarme). Deshalb wird jede Bone-Ausrichtung auf die
Ruhehaltung des Kaempfers (Fighter_Rigged_v20.blend) gedreht, das Mesh in dieser Haltung gebacken und als neue Ruhehaltung
gesetzt. Gelenkpositionen (Proportionen, Groesse) bleiben die des Trainers.
Danach: Steuer-Bones entfernen, Meshes nach Material trennen (Roblox: eine Farbe pro MeshPart), Trainer an den Ursprung,
FBX wie beim Kaempfer (export_fighter_rigged_v03.py).
Pruefung: Aktion Fighter_Idle_v08-Ersatz (Fighter_Sig_Tyson aus v20) auf das neue Skelett legen und mit dem Kaempfer
vergleichen (Handschuh-Abstand zum Kopf in der Deckung), Vorschaubild.

Aufruf: blender -b --python export_trainer_rigged_v01.py -- Mike_Tyson
Ausgabe: export/Trainer_<Name>_Rigged_v01.fbx, export/Trainer_<Name>_Rigged_v01_data.luau,
         renders/trainer_<name>_rigged_v01_checks.json, renders/trainer_<name>_rigged_v01_sheet.png
"""
import json, math, os, sys
import bpy, bmesh
from mathutils import Matrix, Vector

NAME = "Referee"
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "referee_v02.blend")
FIGHTER = os.path.join(HERE, "Fighter_Rigged_v20.blend")
FBX = os.path.join(HERE, "export", f"{NAME}_Rigged_v01.fbx")
DATA = os.path.join(HERE, "export", f"{NAME}_Rigged_v01_data.luau")
REP = os.path.join(HERE, "renders", f"{NAME.lower()}_rigged_v01_checks.json")
SHEET = os.path.join(HERE, "renders", f"{NAME.lower()}_rigged_v01_sheet.png")
for p in (FBX, DATA):
    if os.path.exists(p): raise SystemExit(f"Datei existiert bereits, nicht ueberschrieben: {p}")
S = 1 / 0.28

bpy.ops.wm.open_mainfile(filepath=SRC)
D, scene = bpy.data, bpy.context.scene
def upd(): bpy.context.view_layer.update()

# Kaempfer-Ruhehaltung (Armature-Raum) und eine Pruef-Aktion laden
with bpy.data.libraries.load(FIGHTER) as (src, dst):
    dst.objects = ["Fighter_Armature"]; dst.actions = ["Fighter_Sig_Tyson"]
farm = [o for o in dst.objects if o][0]
FREST = {b.name: b.matrix_local.to_3x3().normalized() for b in farm.data.bones}
FHEAD = {b.name: b.head_local.copy() for b in farm.data.bones}
CHECK_ACT = [a for a in dst.actions if a][0]

# nur diesen Trainer behalten
arm = D.objects[NAME + "_Armature"]
meshes = [o for o in arm.children if o.type == "MESH"]
for o in list(D.objects):
    if o != arm and o not in meshes: D.objects.remove(o)
if arm.animation_data: arm.animation_data.action = None
P = arm.pose.bones
for pb in P:
    for c in list(pb.constraints): pb.constraints.remove(c)
    pb.rotation_mode = "QUATERNION"; pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
upd()
DEFORM = [b.name for b in arm.data.bones if b.use_deform]
KEEP = ["Root"] + DEFORM
missing = [n for n in KEEP if n not in FREST]
if missing: raise SystemExit("Bones fehlen im Kaempfer-Skelett: " + ", ".join(missing))
def depth(b): return 0 if b.parent is None else 1 + depth(b.parent)
ORDER = sorted(KEEP, key=lambda n: depth(arm.data.bones[n]))

# 1) jede Bone auf die Kaempfer-Ausrichtung drehen (Position bleibt), von der Wurzel nach aussen
before = {}
for n in ORDER:
    pb = P[n]
    before[n] = pb.matrix.to_3x3().normalized().to_quaternion().rotation_difference(FREST[n].to_quaternion()).angle
    head = pb.matrix.translation.copy()
    pb.matrix = Matrix.Translation(head) @ FREST[n].to_4x4()
    upd()

# 2) Meshes in dieser Haltung backen, Haltung als neue Ruhehaltung setzen
bpy.ops.object.select_all(action="DESELECT")
for o in meshes:
    bpy.context.view_layer.objects.active = o
    mod = next(m for m in o.modifiers if m.type == "ARMATURE")
    # andere Modifier (z. B. Bevel) vorher anwenden, damit die Reihenfolge stimmt
    for m in list(o.modifiers):
        if m.type != "ARMATURE" and o.modifiers.find(m.name) < o.modifiers.find(mod.name):
            bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    for m in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="POSE"); bpy.ops.pose.select_all(action="SELECT"); bpy.ops.pose.armature_apply(selected=False)
bpy.ops.object.mode_set(mode="OBJECT")

# 3) Steuer-Bones entfernen, normale Vererbung
bpy.ops.object.mode_set(mode="EDIT")
eb = arm.data.edit_bones
for b in [b for b in eb if b.name not in KEEP]: eb.remove(b)
for b in eb: b.use_inherit_rotation = True; b.use_connect = False
bpy.ops.object.mode_set(mode="OBJECT")
after = {b.name: b.matrix_local.to_3x3().normalized().to_quaternion().rotation_difference(FREST[b.name].to_quaternion()).angle for b in arm.data.bones}

# 4) Armature-Modifier wieder anlegen, Meshes nach Material trennen
for o in meshes:
    m = o.modifiers.new("Armature", "ARMATURE"); m.object = arm
parts = []
for o in meshes:
    bpy.ops.object.select_all(action="DESELECT"); o.select_set(True); bpy.context.view_layer.objects.active = o
    if len({p.material_index for p in o.data.polygons}) > 1:
        bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.separate(type="MATERIAL"); bpy.ops.object.mode_set(mode="OBJECT")
    parts += [x for x in bpy.context.selected_objects if x.type == "MESH"]
parts = list({p.name: p for p in parts}.values())
for p in parts:
    mat = p.material_slots[0].material if p.material_slots else None
    p.name = f"{NAME}__{mat.name.replace(NAME + '_', '') if mat else 'Part'}"

# 5) an den Ursprung: Fuesse auf z = 0, Mitte x/y = 0
off = arm.matrix_world.translation.copy()
lo = min((p.matrix_world @ Vector(c)).z for p in parts for c in p.bound_box)
arm.location = arm.location - Vector((off.x, off.y, 0)) - Vector((0, 0, lo)); upd()

# Farben je Teil (sRGB 0..255)
def srgb(c): return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
def base_color(m):
    if m and m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                bc = n.inputs["Base Color"]
                if bc.is_linked:
                    fn = bc.links[0].from_node
                    if fn.type == "RGB": return list(fn.outputs[0].default_value[:3])
                    if fn.type == "VALTORGB":
                        els = fn.color_ramp.elements; return [sum(e.color[i] for e in els) / len(els) for i in range(3)]
                    if fn.type == "TEX_IMAGE" and fn.image and fn.image.pixels:
                        px = fn.image.pixels[:]; n4 = len(px) // 4; return [sum(px[i::4][:n4]) / n4 for i in range(3)]
                return list(bc.default_value[:3])
    return list(m.diffuse_color[:3]) if m else [0.6, 0.6, 0.6]
colors = {p.name: [round(srgb(c) * 255) for c in base_color(p.material_slots[0].material if p.material_slots else None)] for p in parts}

# 6) Pruefung: Kaempfer-Aktion auf das neue Skelett, Handschuhe zur Deckung
arm.animation_data_create(); arm.animation_data.action = CHECK_ACT
if hasattr(arm.animation_data, "action_slot") and arm.animation_data.action_suitable_slots:
    arm.animation_data.action_slot = arm.animation_data.action_suitable_slots[0]
P = arm.pose.bones
for pb in P: pb.rotation_mode = "XYZ"          # Kaempfer-Aktionen sind als Euler-Winkel gekeyt
chk = {"rest_angle_before_deg_max": round(max(before.values()) * 57.2958, 2), "rest_angle_after_deg_max": round(max(after.values()) * 57.2958, 3),
       "parts": len(parts), "bones": len(arm.data.bones), "height_m": None, "frames": {}}
hi = 0
for f in (1, 10, 17, 30):
    scene.frame_set(f); upd()
    h = (arm.matrix_world @ P["Head"].head); lh = arm.matrix_world @ P["LeftHand"].head; rh = arm.matrix_world @ P["RightHand"].head
    chk["frames"][f] = {"hand_L_to_head_m": round((lh - h).length, 3), "hand_R_to_head_m": round((rh - h).length, 3)}
scene.frame_set(1); upd()
chk["height_m"] = round(max((p.matrix_world @ Vector(c)).z for p in parts for c in p.bound_box), 3)

# Vorschau: 4 Frames der Pruef-Aktion
import numpy as np
scene.render.engine = "BLENDER_WORKBENCH"; scene.render.resolution_x = 300; scene.render.resolution_y = 420
scene.display.shading.color_type = "MATERIAL"
cd = D.cameras.new("Cam"); cd.type = "ORTHO"; cd.ortho_scale = 2.4
cam = D.objects.new("Cam", cd); scene.collection.objects.link(cam); scene.camera = cam
cam.location = (2.2, -2.2, 1.0); cam.rotation_euler = (math.radians(90), 0, math.radians(45))
tiles = []; tmp = os.path.join(HERE, "renders", "_referee_tmp.png")
for f in (1, 10, 17, 30):
    scene.frame_set(f); scene.render.filepath = tmp; bpy.ops.render.render(write_still=True)
    img = D.images.load(tmp); tiles.append(np.array(img.pixels[:], dtype=np.float32).reshape(420, 300, 4)); D.images.remove(img)
os.remove(tmp)
sheet = np.concatenate(tiles, axis=1)
im = D.images.new("sheet", sheet.shape[1], sheet.shape[0], alpha=True); im.pixels = sheet.ravel()
im.filepath_raw = SHEET; im.file_format = "PNG"; im.save()
scene.camera = None; D.objects.remove(cam)

# 7) Export in Ruhehaltung (ohne Animation)
arm.animation_data.action = None
for pb in P: pb.location = (0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
upd()
bpy.ops.object.select_all(action="DESELECT")
for o in [arm] + parts: o.select_set(True)
bpy.context.view_layer.objects.active = arm
arm.name = NAME + "_Rig"
bpy.ops.export_scene.fbx(filepath=FBX, use_selection=True, object_types={"ARMATURE", "MESH"}, apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_NONE", global_scale=1.0, axis_forward="-Z", axis_up="Y", use_mesh_modifiers=True,
    mesh_smooth_type="FACE", use_tspace=False, add_leaf_bones=False, primary_bone_axis="Y", secondary_bone_axis="X",
    use_armature_deform_only=False, armature_nodetype="NULL", bake_anim=False, path_mode="AUTO")
def lua(v):
    if isinstance(v, list): return "{" + ", ".join(str(x) for x in v) + "}"
    return '"' + str(v) + '"'
lines = [f"-- Erzeugt von export_referee_rigged_v01.py ({NAME}, Skelett auf Kaempfer-Ruhehaltung ausgerichtet).", "return {",
         f"\tname = \"{NAME}\", height = {round(chk['height_m'] * S, 3)},", "\tcolors = {"]
for n in sorted(colors): lines.append(f"\t\t[\"{n}\"] = {lua(colors[n])},")
lines += ["\t},", "}"]
open(DATA, "w", encoding="utf-8").write("\n".join(lines) + "\n")
chk["fbx_bytes"] = os.path.getsize(FBX); chk["part_names"] = sorted(colors)
json.dump(chk, open(REP, "w"), indent=1)
print("CHECK", json.dumps({k: v for k, v in chk.items() if k != "part_names"}))
