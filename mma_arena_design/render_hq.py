"""High-quality review renders of MMA_Arena_Design_v01.blend (the .blend itself is not modified).

Run:  python render_hq.py
Output: renders/hq/<camera>.png  (1920x1080, Cycles, 384 samples, denoised)
"""
import os
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "MMA_Arena_Design_v01.blend"))
out = os.path.join(HERE, "renders", "hq")
os.makedirs(out, exist_ok=True)

scene = bpy.context.scene
r = scene.render
r.resolution_x, r.resolution_y, r.resolution_percentage = 1920, 1080, 100
cy = scene.cycles
cy.device = "CPU"
cy.samples = 384
cy.use_adaptive_sampling = True
cy.adaptive_threshold = 0.004
cy.use_denoising = True
cy.denoiser = "OPENIMAGEDENOISE"
cy.max_bounces = 10
cy.diffuse_bounces = 4
cy.glossy_bounces = 4
cy.transparent_max_bounces = 24
r.film_transparent = False

for cam in sorted((o for o in bpy.data.collections["Review_Cameras"].objects if o.type == "CAMERA"), key=lambda o: o.name):
    scene.camera = cam
    r.filepath = os.path.join(out, cam.name + ".png")
    bpy.ops.render.render(write_still=True)
    print("rendered", r.filepath, flush=True)
