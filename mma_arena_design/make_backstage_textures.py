"""Backstage v01 sign textures (subtle: dark plate, light-grey lettering, thin red bar). -> backstage_textures/*.png"""
import os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "backstage_textures"); os.makedirs(OUT, exist_ok=True)
B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def sign(name, text, arrow=False, w=1024, h=256):
    im = Image.new("RGB", (w, h), (14, 14, 16)); d = ImageDraw.Draw(im)
    d.rectangle((6, 6, w - 7, h - 7), outline=(46, 46, 50), width=4)
    d.rectangle((40, 60, 52, h - 60), fill=(150, 16, 16))                         # thin red accent bar
    f = ImageFont.truetype(B, 112); tw = d.textlength(text, font=f)
    x = 90 if arrow else (w - tw) / 2 + 20
    d.text((x, h / 2), text, font=f, fill=(200, 200, 204), anchor="lm")
    if arrow:                                                                       # straight-ahead arrow (up = walk through)
        ax = w - 150; d.polygon([(ax, 52), (ax + 62, 128), (ax + 24, 128), (ax + 24, 204), (ax - 24, 204), (ax - 24, 128), (ax - 62, 128)], fill=(200, 200, 204))
    im.save(os.path.join(OUT, name))
sign("sign_locker_room.png", "LOCKER ROOM")
sign("sign_arena.png", "ARENA", arrow=True)
print("ok")
