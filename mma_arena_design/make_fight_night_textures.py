"""Own neutral placeholder graphics for the Fight Night arena (no real brands)."""
import math, os
from PIL import Image, ImageDraw, ImageFont
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fight_night_textures")
B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
def octagon(d, cx, cy, r, w, col):
    pts = [(cx + r * math.cos(math.radians(22.5 + 45 * k)), cy + r * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
    d.line(pts + [pts[0]], fill=col, width=w, joint="curve")
def gradient(w, h, top, bot):
    im = Image.new("RGB", (w, h)); px = im.load()
    for y in range(h):
        t = y / (h - 1); c = tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3))
        for x in range(w): px[x, y] = c
    return im
# event graphic
im = gradient(1600, 900, (10, 14, 40), (30, 10, 55)); d = ImageDraw.Draw(im)
octagon(d, 800, 330, 210, 16, (70, 120, 255)); octagon(d, 800, 330, 170, 6, (150, 90, 255))
d.text((800, 330), "CC", font=ImageFont.truetype(B, 170), fill=(235, 240, 255), anchor="mm")
d.text((800, 640), "CAGE CHAMPIONS", font=ImageFont.truetype(B, 120), fill=(245, 245, 250), anchor="mm")
d.text((800, 760), "MAIN EVENT  ·  PLATZHALTER", font=ImageFont.truetype(R, 48), fill=(140, 170, 255), anchor="mm")
im.save(os.path.join(OUT, "cage_champions_event.png"))
# walkout display: portrait placeholder + fighter name
im = gradient(1600, 900, (8, 12, 30), (20, 8, 40)); d = ImageDraw.Draw(im)
d.rectangle((90, 90, 620, 810), outline=(80, 130, 255), width=8)
d.rectangle((250, 230, 460, 470), fill=(70, 75, 90))               # blocky head
d.rectangle((150, 500, 560, 800), fill=(70, 75, 90))               # shoulders
d.text((360, 150), "PORTRÄT", font=ImageFont.truetype(R, 40), fill=(140, 170, 255), anchor="mm")
d.text((700, 330), "FIGHTER NAME", font=ImageFont.truetype(B, 92), fill=(245, 245, 250), anchor="lm")
d.text((700, 470), "RECORD 0-0-0  ·  PLATZHALTER", font=ImageFont.truetype(R, 50), fill=(150, 175, 255), anchor="lm")
d.text((700, 600), "CAGE CHAMPIONS", font=ImageFont.truetype(B, 60), fill=(160, 110, 255), anchor="lm")
im.save(os.path.join(OUT, "walkout_fighter_display.png"))
print("ok")
