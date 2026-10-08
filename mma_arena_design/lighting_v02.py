"""v02: lighting / exposure pass only. Opens v01 (unchanged), saves MMA_Arena_Design_v02.blend.
Run: python lighting_v02.py  -> also writes a low-res preview renders/v02_preview_overview.png
"""
import os
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "MMA_Arena_Design_v01.blend"))
D = bpy.data

# less overexposure on the canvas
D.lights["Key_Area_OverCage"].energy = 1000
D.lights["Key_Area_OverCage"].size = 8
for i in range(1, 5):
    l = D.lights[f"Key_Spot_{i}"]
    l.energy = 1400
    l.spot_blend = 0.7
# brighter, neutral surroundings
for i in range(1, 5):
    D.lights[f"Fill_Stands_{i}"].energy = 1100
    D.lights[f"Fill_Stands_{i}"].color = (1.0, 0.98, 0.95)
amb = D.lights.new("Ambient_Ceiling_Soft", "AREA")
amb.energy, amb.size, amb.color = 2500, 22, (1.0, 0.98, 0.96)
o = D.objects.new("Ambient_Ceiling_Soft", amb)
o.location = (0, 0, 9.0)
D.collections["Presentation_Lights"].objects.link(o)
# red accents: fewer and weaker
for n in ("Accent_Red_Rim_NE", "Accent_Red_Rim_NW"):
    D.objects[n].hide_render = True
D.lights["Accent_Red_Walkway"].energy = 120
D.lights["Accent_Red_Tunnel"].energy = 120
D.materials["M_Red_LED"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 2.5
# softer tone mapping
s = bpy.context.scene
s.view_settings.look = "AgX - Base Contrast"
s.view_settings.exposure = 0.0

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "MMA_Arena_Design_v02.blend"))

# single low-res preview
r = s.render
r.resolution_x, r.resolution_y = 960, 540
s.cycles.samples = 48
s.camera = D.objects["Cam_01_Overview_Elevated"]
r.filepath = os.path.join(HERE, "renders", "v02_preview_overview.png")
bpy.ops.render.render(write_still=True)
print("done")
