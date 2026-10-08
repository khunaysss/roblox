"""Own neutral signage / pinboard graphics for the Training Gym (no real brands)."""
import math, os, random
from PIL import Image, ImageDraw, ImageFont
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gym_textures")
B, R = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
def octagon(d, cx, cy, r, w, col):
    p = [(cx + r * math.cos(math.radians(22.5 + 45 * k)), cy + r * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
    d.line(p + [p[0]], fill=col, width=w)
# painted wall sign (on anthracite wall)
im = Image.new("RGBA", (2400, 600), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
octagon(d, 300, 300, 230, 26, (190, 30, 30, 255)); d.text((300, 300), "CC", font=ImageFont.truetype(B, 190), fill=(235, 232, 225, 255), anchor="mm")
d.text((620, 230), "CAGE CHAMPIONS", font=ImageFont.truetype(B, 210), fill=(235, 232, 225, 255), anchor="lm")
d.text((630, 440), "TRAINING GYM  ·  EST. 2026", font=ImageFont.truetype(B, 96), fill=(190, 30, 30, 255), anchor="lm")
rnd = random.Random(3); px = im.load()
for _ in range(9000):                       # slight paint wear
    x, y = rnd.randrange(2400), rnd.randrange(600)
    if px[x, y][3]: px[x, y] = (px[x, y][0], px[x, y][1], px[x, y][2], rnd.randint(90, 200))
im.save(os.path.join(OUT, "wall_sign.png"))
def paper(w, h, title, lines, accent=(190, 30, 30)):
    im = Image.new("RGB", (w, h), (236, 233, 224)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, 70), fill=accent); d.text((20, 35), title, font=ImageFont.truetype(B, 40), fill=(250, 250, 250), anchor="lm")
    y = 110
    for ln in lines:
        d.text((24, y), ln, font=ImageFont.truetype(R, 28), fill=(40, 40, 45)); y += 46
    return im
paper(560, 760, "TRAININGSPLAN", ["MO  Boxen · Pratzen", "DI  Grappling", "MI  Kraft · Kondition", "DO  Sparring (Käfig)", "FR  Technik", "SA  Lauf 5 km", "SO  Pause", "", "Coach-Notiz:", "Deckung hoch halten!"]).save(os.path.join(OUT, "plan_week.png"))
paper(560, 760, "RUNDEN", ["3 × 3 Min Sandsack", "3 × 2 Min Pratzen", "5 × 1 Min Sprawl", "4 × 10 Kniebeugen", "4 × 8 Bankdrücken", "", "Pause: 1 Min", "", "Ziel: Turnier!"], (40, 40, 48)).save(os.path.join(OUT, "plan_rounds.png"))
im = Image.new("RGB", (600, 850), (18, 18, 22)); d = ImageDraw.Draw(im)
octagon(d, 300, 300, 190, 18, (200, 35, 35)); d.text((300, 300), "CC", font=ImageFont.truetype(B, 150), fill=(240, 240, 240), anchor="mm")
d.text((300, 560), "OPEN", font=ImageFont.truetype(B, 80), fill=(240, 240, 240), anchor="mm")
d.text((300, 650), "TURNIER", font=ImageFont.truetype(B, 80), fill=(200, 35, 35), anchor="mm")
d.text((300, 760), "CAGE CHAMPIONS · SAMSTAG", font=ImageFont.truetype(R, 30), fill=(170, 170, 175), anchor="mm")
im.save(os.path.join(OUT, "poster_tournament.png"))
for name, txt, col in (("sign_umkleide", "UMKLEIDE", (40, 40, 48)), ("sign_ausgang", "AUSGANG", (190, 30, 30))):
    im = Image.new("RGB", (800, 220), col); d = ImageDraw.Draw(im)
    d.text((400, 110), txt, font=ImageFont.truetype(B, 120), fill=(240, 240, 240), anchor="mm"); im.save(os.path.join(OUT, name + ".png"))
print("ok")
