"""Tattoo / pattern decals for the six trainers (simplified stylised drawings, transparent PNG)."""
import math, os, random
from PIL import Image, ImageDraw, ImageFont
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trainers_textures")
INK = (28, 24, 24, 215)
def new(w=512, h=512): im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); return im, ImageDraw.Draw(im)
# Tyson: tribal face tattoo (left temple/eye)
im, d = new(256, 256)
for i in range(4):
    d.arc((30 + i * 18, 20 + i * 10, 220 - i * 10, 230 - i * 12), 200 + i * 15, 320 + i * 10, fill=INK, width=14 - i * 2)
d.line((60, 200, 120, 150, 150, 70), fill=INK, width=12); im.save(os.path.join(OUT, "tyson_face_tattoo.png"))
# Pereira: two round chest pieces + sleeve
for name, seed in (("pereira_chest_L", 1), ("pereira_chest_R", 2)):
    im, d = new(); r = random.Random(seed)
    d.ellipse((90, 90, 422, 422), outline=INK, width=10); d.ellipse((150, 150, 362, 362), outline=INK, width=6)
    for k in range(12):
        a = 2 * math.pi * k / 12; d.line((256 + 110 * math.cos(a), 256 + 110 * math.sin(a), 256 + 160 * math.cos(a), 256 + 160 * math.sin(a)), fill=INK, width=8)
    d.rectangle((216, 196, 296, 300), outline=INK, width=8); d.rectangle((236, 225, 248, 240), fill=INK); d.rectangle((264, 225, 276, 240), fill=INK)
    im.save(os.path.join(OUT, name + ".png"))
def sleeve(name, seed, dense):
    im, d = new(256, 512); r = random.Random(seed)
    for _ in range(dense):
        x, y, s = r.randint(10, 220), r.randint(10, 480), r.randint(25, 70)
        k = r.randint(0, 2)
        if k == 0: d.ellipse((x, y, x + s, y + s), outline=INK, width=6)
        elif k == 1: d.polygon([(x, y + s), (x + s / 2, y), (x + s, y + s)], outline=INK, width=6)
        else: d.arc((x, y, x + s, y + s * 1.4), 20, 300, fill=INK, width=7)
    im.save(os.path.join(OUT, name + ".png"))
sleeve("pereira_sleeve", 3, 14); sleeve("oliveira_sleeve", 4, 18)
# Oliveira: portrait sketch + script name
im, d = new(512, 512)
d.rectangle((60, 90, 230, 330), outline=INK, width=8); d.ellipse((95, 120, 195, 250), outline=INK, width=8)
d.line((120, 175, 140, 175), fill=INK, width=6); d.line((150, 175, 170, 175), fill=INK, width=6); d.line((130, 215, 160, 215), fill=INK, width=5)
d.text((380, 200), "Oliveira", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 64), fill=INK, anchor="mm")
im.save(os.path.join(OUT, "oliveira_chest.png"))
# Khabib: light chest hair
im, d = new(); r = random.Random(7)
for _ in range(260):
    x, y = r.gauss(256, 70), r.gauss(230, 60); a = r.uniform(-1, 1)
    d.line((x, y, x + 10 * math.sin(a), y + 12), fill=(40, 28, 20, 110), width=3)
im.save(os.path.join(OUT, "khabib_chest_hair.png"))
# Khabib shorts: dark angular pattern
im, d = new(256, 256)
for i in range(4): d.polygon([(20 + i * 50, 250), (60 + i * 50, 10), (80 + i * 50, 10), (40 + i * 50, 250)], fill=(10, 10, 12, 170))
im.save(os.path.join(OUT, "khabib_shorts_pattern.png"))
# Pereira / Oliveira: gold side accents
im, d = new(256, 256)
d.polygon([(150, 250), (230, 20), (250, 20), (175, 250)], fill=(205, 160, 60, 255)); d.polygon([(190, 250), (250, 90), (256, 90), (210, 250)], fill=(205, 160, 60, 255))
im.save(os.path.join(OUT, "gold_accent.png"))
# Saenchai: gold ornament for Muay Thai shorts
im, d = new(512, 512); G = (215, 170, 60, 255)
for cx, cy, s in ((256, 260, 1.0),):
    for k in range(3):
        d.arc((cx - 180 * s + k * 40, cy - 120 + k * 30, cx + 60 - k * 20, cy + 120 - k * 30), 90, 360, fill=G, width=22 - k * 5)
    d.arc((cx - 40, cy - 60, cx + 180, cy + 160), 180, 450, fill=G, width=20)
    d.ellipse((cx + 60, cy - 30, cx + 110, cy + 20), outline=G, width=12)
im.save(os.path.join(OUT, "saenchai_ornament.png"))
print("ok")
