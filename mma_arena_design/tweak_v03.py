"""v03: tone down red seat backs + dim scoreboard placeholder. Opens v02 (unchanged), saves v03 + low-res preview."""
import os, bpy
HERE = os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "MMA_Arena_Design_v02.blend"))
M = bpy.data.materials
M["M_Seat_Back_Red"].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.11, 0.012, 0.015, 1)  # muted burgundy
M["M_Screen_Placeholder"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.35
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "MMA_Arena_Design_v03.blend"))
s = bpy.context.scene; r = s.render
r.resolution_x, r.resolution_y = 960, 540; s.cycles.samples = 48
s.camera = bpy.data.objects["Cam_01_Overview_Elevated"]
r.filepath = os.path.join(HERE, "renders", "v03_preview_overview.png")
bpy.ops.render.render(write_still=True)
print("done")
