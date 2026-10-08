"""Gym v02 graphics: wall logo, mat logo, technique posters, round timer, plan board, style sign (own designs, no brands)."""
import math, os
from PIL import Image, ImageDraw, ImageFont
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gym_textures")
B, R = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
F = lambda s, b=True: ImageFont.truetype(B if b else R, s)
CREAM, RED, DARK, BLUE = (236, 232, 224, 255), (196, 32, 32, 255), (24, 24, 28, 255), (40, 90, 200, 255)
def octagon(d, cx, cy, r, w, col, fill=None):
    p = [(cx + r * math.cos(math.radians(22.5 + 45 * k)), cy + r * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
    if fill: d.polygon(p, fill=fill)
    d.line(p + [p[0]], fill=col, width=w)
def fit(d, text, font_px, max_w, bold=True):
    while F(font_px, bold).getlength(text) > max_w: font_px -= 4
    return F(font_px, bold)
# 1) wall logo: emblem + two centred lines, everything inside the canvas
im = Image.new("RGBA", (2400, 640), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
octagon(d, 300, 320, 250, 28, RED, fill=(30, 30, 34, 255)); d.text((300, 320), "CC", font=F(200), fill=CREAM, anchor="mm")
tx0, tx1 = 620, 2340; cx = (tx0 + tx1) / 2
f1 = fit(d, "CAGE CHAMPIONS", 230, tx1 - tx0); d.text((cx, 245), "CAGE CHAMPIONS", font=f1, fill=CREAM, anchor="mm")
d.rectangle((tx0 + 40, 380, tx1 - 40, 392), fill=RED)
f2 = fit(d, "TRAINING  CENTER", 130, tx1 - tx0 - 200); d.text((cx, 495), "TRAINING  CENTER", font=f2, fill=RED, anchor="mm")
im.save(os.path.join(OUT, "wall_logo_v02.png"))
# 2) mat centre logo (transparent)
im = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
octagon(d, 512, 512, 470, 26, (196, 32, 32, 230)); octagon(d, 512, 512, 420, 8, (40, 40, 44, 200))
d.text((512, 470), "CC", font=F(330), fill=(40, 40, 44, 215), anchor="mm")
d.text((512, 720), "CAGE CHAMPIONS", font=F(78), fill=(196, 32, 32, 230), anchor="mm")
im.save(os.path.join(OUT, "mat_logo.png"))
# 3) technique posters: blocky stick figures (own drawings)
def figure(d, x, y, s, col, arm_dx=0.0, kick=False, low=False):
    hy = y + (40 * s if low else 0)
    d.rectangle((x - 18 * s, hy - 120 * s, x + 18 * s, hy - 84 * s), fill=col)                 # head
    d.rectangle((x - 26 * s, hy - 80 * s, x + 26 * s, hy - 10 * s), fill=col)                  # torso
    d.rectangle((x + 26 * s, hy - 74 * s, x + 26 * s + 70 * s * arm_dx + 20 * s, hy - 60 * s), fill=col)   # punching arm
    d.rectangle((x - 46 * s, hy - 74 * s, x - 26 * s, hy - 40 * s), fill=col)                  # guard arm
    d.rectangle((x - 24 * s, hy - 10 * s, x - 6 * s, y + 62 * s), fill=col)
    if kick: d.polygon([(x + 6 * s, hy - 8 * s), (x + 22 * s, hy - 20 * s), (x + 110 * s, hy - 60 * s), (x + 100 * s, hy - 40 * s)], fill=col)
    else: d.rectangle((x + 6 * s, hy - 10 * s, x + 24 * s, y + 62 * s), fill=col)
def poster(name, title, sub, steps):
    im = Image.new("RGB", (600, 850), (22, 22, 26)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 600, 110), fill=(196, 32, 32)); d.text((300, 56), title, font=fit(d, title, 64, 560), fill=(245, 245, 245), anchor="mm")
    for i, (lbl, kw) in enumerate(steps):
        y = 290 + i * 220; d.rectangle((30, y - 150, 570, y + 66), outline=(70, 70, 76), width=3)
        figure(d, 170, y, 1.0, (225, 222, 214), **kw); d.text((320, y - 40), lbl, font=fit(d, lbl, 40, 235), fill=(225, 222, 214), anchor="lm")
    d.text((300, 828), sub, font=F(26, False), fill=(160, 160, 166), anchor="mm"); im.save(os.path.join(OUT, name))
poster("poster_striking.png", "STRIKING", "CAGE CHAMPIONS · TECHNIK 01", [("1  JAB", dict(arm_dx=1.0)), ("2  CROSS", dict(arm_dx=0.6)), ("3  LOW KICK", dict(kick=True))])
poster("poster_defense.png", "DEFENSE", "CAGE CHAMPIONS · TECHNIK 02", [("GUARD", dict(arm_dx=0.0)), ("SLIP", dict(arm_dx=0.2, low=True)), ("SPRAWL", dict(low=True))])
poster("poster_grappling.png", "GRAPPLING", "CAGE CHAMPIONS · TECHNIK 03", [("STANCE", dict()), ("SHOT", dict(low=True, arm_dx=0.8)), ("CLINCH", dict(arm_dx=0.5))])
# 4) round timer face (LED style)
im = Image.new("RGB", (1000, 400), (8, 8, 10)); d = ImageDraw.Draw(im)
d.text((385, 190), "03:00", font=fit(d, "03:00", 230, 690), fill=(230, 40, 35), anchor="mm")
for i, c in enumerate(((40, 200, 70), (230, 170, 30), (230, 40, 35))): d.ellipse((800, 70 + i * 95, 880, 150 + i * 95), fill=c)
d.text((380, 360), "RUNDE 1 / 3", font=F(44), fill=(150, 150, 150), anchor="mm"); im.save(os.path.join(OUT, "round_timer.png"))
# 5) weekly training plan board
im = Image.new("RGB", (1200, 800), (238, 236, 230)); d = ImageDraw.Draw(im)
d.rectangle((0, 0, 1200, 100), fill=(30, 30, 34)); d.text((40, 50), "TRAININGSPLAN · WOCHE", font=F(56), fill=(245, 245, 245), anchor="lm")
d.rectangle((1040, 18, 1180, 82), fill=(196, 32, 32)); d.text((1110, 50), "CC", font=F(48), fill=(245, 245, 245), anchor="mm")
days = ["MO", "DI", "MI", "DO", "FR", "SA"]; rows = [("17:00", ["Boxen", "Grappling", "Kraft", "Sparring", "Technik", "Lauf"]),
        ("18:30", ["Pratzen", "Ringen", "Kondition", "Käfig", "Sandsack", "—"]), ("20:00", ["Dehnen", "BJJ", "Dehnen", "Taktik", "Open Mat", "—"])]
cw = (1200 - 180) / 6
for i, dname in enumerate(days):
    d.text((180 + cw * i + cw / 2, 145), dname, font=F(40), fill=(196, 32, 32), anchor="mm")
for r, (t, items) in enumerate(rows):
    y = 200 + r * 190; d.line((30, y - 10, 1170, y - 10), fill=(180, 178, 172), width=3); d.text((40, y + 80), t, font=F(38), fill=(30, 30, 34), anchor="lm")
    for i, it in enumerate(items):
        d.rounded_rectangle((185 + cw * i, y + 10, 175 + cw * (i + 1), y + 160), 14, fill=(255, 255, 255), outline=(200, 198, 192), width=2)
        d.text((180 + cw * i + cw / 2, y + 85), it, font=fit(d, it, 34, cw - 30), fill=(30, 30, 34), anchor="mm")
im.save(os.path.join(OUT, "plan_board.png"))
# 6) locker room style sign + customisation floor decal
im = Image.new("RGB", (1400, 300), (30, 30, 34)); d = ImageDraw.Draw(im)
d.text((700, 120), "FIGHTER STYLE", font=F(140), fill=(236, 232, 224), anchor="mm"); d.text((700, 245), "LOOK · OUTFIT · HANDSCHUHE", font=F(52), fill=(196, 32, 32), anchor="mm")
im.save(os.path.join(OUT, "sign_fighter_style.png"))
im = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
octagon(d, 512, 512, 480, 40, (196, 32, 32, 255)); octagon(d, 512, 512, 400, 10, (236, 232, 224, 230))
d.text((512, 512), "STYLE", font=F(150), fill=(236, 232, 224, 230), anchor="mm"); im.save(os.path.join(OUT, "style_pad.png"))
print("ok")
