"""Fighter_Casual_v11 - v10 + weichere Koerperform (gleiche Proportionen, gleiches Rig, gleiche Gewichte).

Fighter_Casual_v10.blend wird geoeffnet und NICHT veraendert.
Fighter_Body, Fighter_Gloves, Fighter_Shorts:
  - schmale Fasen an Kanten > 35 Grad (2 Segmente, Gewichte werden beim Anwenden interpoliert) -> Lichtkanten an Schultern, Brust, Bauch, Kinn
  - weiche, gewichtete Normalen (flache grosse Flaechen bleiben flach, Kanten runden sich im Licht) statt hart schattierter Flaechen
Fighter_Body: neue, nicht ueberlappende UVs (Smart UV Project) fuer spaetere Normal-/Roughness-Texturen.
Export: export/Fighter_Body_v11.fbx (Armatur + 3 Teile, gleiche Einstellungen wie export_hands_v01.py, Normalen mit exportiert).
Pruefung: renders/fighter_v11_checks.json
Aufruf: blender -b --python build_fighter_v11.py
"""
import bpy, bmesh, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Casual_v10.blend"), os.path.join(HERE, "Fighter_Casual_v11.blend")
FBX = os.path.join(HERE, "export", "Fighter_Body_v11.fbx")
if os.path.exists(OUT): raise SystemExit("Fighter_Casual_v11.blend existiert - nicht ueberschrieben")
bpy.ops.wm.open_mainfile(filepath=SRC)
D = bpy.data
arm = D.objects["Fighter_Armature"]
PARTS = ["Fighter_Body", "Fighter_Gloves", "Fighter_Shorts"]
check = {}

def uv_area(me):
    bm = bmesh.new(); bm.from_mesh(me)
    l = bm.loops.layers.uv.active
    a = 0.0
    if l:
        for f in bm.faces:
            co = [lp[l].uv for lp in f.loops]
            s = 0.0
            for i in range(len(co)): s += co[i].x * co[(i + 1) % len(co)].y - co[(i + 1) % len(co)].x * co[i].y
            a += abs(s) / 2
    bm.free(); return round(a, 3)

for n in PARTS:
    o = D.objects[n]
    me = o.data
    before = {"verts": len(me.vertices), "faces": len(me.polygons), "groups": len(o.vertex_groups)}
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    # Fase zuerst (vor der Armatur), dann anwenden
    bev = o.modifiers.new("CC_Bevel", "BEVEL")
    bev.limit_method = "ANGLE"; bev.angle_limit = 0.61; bev.width = 0.012; bev.segments = 2
    bev.harden_normals = False; bev.use_clamp_overlap = True
    while o.modifiers[0] != bev: bpy.ops.object.modifier_move_up(modifier=bev.name)
    bpy.ops.object.modifier_apply(modifier=bev.name)
    # entartete Mini-Flaechen der Fase entfernen (sonst NaN-UVs)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-5)
    bm.to_mesh(me); bm.free(); me.update()
    for p in me.polygons: p.use_smooth = True
    wn = o.modifiers.new("CC_WeightedNormal", "WEIGHTED_NORMAL")
    wn.keep_sharp = True; wn.mode = "FACE_AREA"; wn.weight = 80
    while o.modifiers[0] != wn: bpy.ops.object.modifier_move_up(modifier=wn.name)
    bpy.ops.object.modifier_apply(modifier=wn.name)
    if n == "Fighter_Body":
        uvl = me.uv_layers.new(name="CC_UV_Clean")
        me.uv_layers.active = uvl
        bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.01)
        bpy.ops.object.mode_set(mode="OBJECT")
        fixed = 0
        for d in uvl.data:
            if d.uv.x != d.uv.x or d.uv.y != d.uv.y: d.uv = (0.0, 0.0); fixed += 1
        check["uv_nan_fixed"] = fixed
        # saubere UV als erste Ebene (Roblox nutzt die erste)
        for old in [l for l in me.uv_layers if l.name != "CC_UV_Clean"]: me.uv_layers.remove(old)
    check[n] = {"before": before, "after": {"verts": len(me.vertices), "faces": len(me.polygons), "groups": len(o.vertex_groups)},
                "uv_area": uv_area(me) if me.uv_layers else None, "armature_mod": any(m.type == "ARMATURE" for m in o.modifiers)}

bpy.ops.wm.save_as_mainfile(filepath=OUT)
bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
for n in PARTS: D.objects[n].select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.fbx(filepath=FBX, use_selection=True, object_types={"ARMATURE", "MESH"}, global_scale=1.0,
                         apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE", axis_forward="-Z", axis_up="Y",
                         add_leaf_bones=False, primary_bone_axis="Y", secondary_bone_axis="X", use_armature_deform_only=False,
                         armature_nodetype="NULL", use_mesh_modifiers=False, mesh_smooth_type="OFF", use_tspace=True, bake_anim=False)
check["fbx_bytes"] = os.path.getsize(FBX)
json.dump(check, open(os.path.join(HERE, "renders", "fighter_v11_checks.json"), "w"), indent=1)
print("CHECK", json.dumps(check))
