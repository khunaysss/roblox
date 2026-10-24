"""Pruefung (nur lesen): Ueberlagerung Eck-Trainer <-> sitzender Kaempfer in der Rundenpause, je Aufstellungswinkel.

Fighter_Casual_v10.blend wird geoeffnet und NICHT gespeichert. Aufstellung wie CC_Corner (Roblox) und build_corner_anims_v01.py:
Kaempfer am Ursprung (Blick -Y), Trainer PLACE_C = 0,95 m vor ihm. Zusaetzlich wird der Trainer um eine senkrechte Achse durch den
Mund des Kaempfers (Trinkphase) um theta gedreht: Flasche bleibt am Mund, der Koerper rueckt seitlich von den Knien weg.
Messwert je theta: Anzahl sich schneidender Dreieckspaare (BVH-Overlap) Trainer-Koerper vs. Kaempfer-Koerper ueber alle Frames
(ohne Flasche; Hand-Mund-Kontakt bleibt erlaubt) und Abstand Flaschenhand-Mund in der Trinkphase.
Aufruf: blender -b --python check_corner_overlap_v01.py  ->  renders/corner_overlap_v01_checks.json
"""
import bpy, json, math, os
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "Fighter_Casual_v10.blend"))
D, scene = bpy.data, bpy.context.scene
arm = D.objects["Fighter_Armature"]
N = 168
PLACE_C = Matrix.Translation((0, -0.95, 0)) @ Matrix.Rotation(math.pi, 4, "Z")

def assign(a, act):
    a.animation_data_create(); a.animation_data.action = act
    ad = a.animation_data
    if act and hasattr(ad, "action_slot") and ad.action_suitable_slots: ad.action_slot = ad.action_suitable_slots[0]

arm2 = arm.copy(); arm2.data = arm.data; scene.collection.objects.link(arm2)
kids1 = [o for o in D.objects if o.parent == arm and o.type == "MESH" and not o.hide_render]
kids2 = []
for o in kids1:
    o2 = o.copy(); o2.parent = arm2; scene.collection.objects.link(o2); kids2.append(o2)
    for m in o2.modifiers:
        if m.type == "ARMATURE": m.object = arm2
assign(arm, D.actions["Fighter_CornerRest"]); assign(arm2, D.actions["Coach_CornerTalk"])
dg = bpy.context.evaluated_depsgraph_get()

def mouth_world():
    pb = arm.pose.bones["Head"]; b = arm.data.bones["Head"]
    off = b.matrix_local.inverted() @ Vector((0, -0.13, b.head_local.z + 0.07))
    return arm.matrix_world @ pb.matrix @ off

def bvh(objs):
    verts, polys = [], []
    for o in objs:
        ev = o.evaluated_get(dg); me = ev.to_mesh(); mw = o.matrix_world
        base = len(verts); verts += [mw @ v.co for v in me.vertices]
        polys += [[base + i for i in p.vertices] for p in me.polygons]
        ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys)

scene.frame_set(62); dg.update(); M = mouth_world()
axis = Vector((M.x, M.y, 0))
names = sorted({o.name for o in kids1})
res = {"mouth_axis_m": [round(axis.x, 3), round(axis.y, 3)], "meshes": names, "theta": {}}
for th in (0, 20, -20, 30, -30, 40, -40):
    R = Matrix.Translation(axis) @ Matrix.Rotation(math.radians(th), 4, "Z") @ Matrix.Translation(-axis)
    arm2.matrix_world = arm.matrix_world @ R @ PLACE_C
    pairs, worst, hand = 0, (0, 0), []
    for f in range(1, N + 1, 3):
        scene.frame_set(f); dg.update()
        n = len(bvh(kids1).overlap(bvh(kids2)))
        pairs += n
        if n > worst[1]: worst = (f, n)
        if 52 <= f <= 76:
            hr = arm2.matrix_world @ arm2.pose.bones["RightHand"].matrix.translation
            hand.append((hr - mouth_world()).length)
    res["theta"][th] = {"overlap_pairs_sum": pairs, "worst_frame": worst[0], "worst_pairs": worst[1],
                        "hand_mouth_m_drink": [round(min(hand), 3), round(max(hand), 3)]}
    print("THETA", th, res["theta"][th])
json.dump(res, open(os.path.join(HERE, "renders", "corner_overlap_v01_checks.json"), "w"), indent=1)
print("CHECK", json.dumps(res))
