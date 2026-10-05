"""Erstellt pro Stufe ein Uebersichtsbild preview/<Tier>_sheet.png"""
import glob, os, sys
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tiers = sys.argv[1:] or sorted(os.listdir(os.path.join(ROOT, "preview")))
for t in tiers:
    d = os.path.join(ROOT, "preview", t)
    if not os.path.isdir(d):
        continue
    fs = sorted(glob.glob(os.path.join(d, "*.png")))
    if not fs:
        continue
    W = Image.open(fs[0]).size[0]
    cols = min(5, len(fs)); rows = (len(fs) + cols - 1) // cols
    sh = Image.new("RGB", (W * cols, W * rows), (20, 20, 24)); dr = ImageDraw.Draw(sh)
    for i, f in enumerate(fs):
        x, y = (i % cols) * W, (i // cols) * W
        sh.paste(Image.open(f).convert("RGB"), (x, y))
        dr.rectangle([x, y, x + 210, y + 26], fill=(15, 15, 18))
        dr.text((x + 8, y + 7), os.path.basename(f)[:-4], fill=(255, 255, 255))
    sh.save(os.path.join(ROOT, "preview", f"{t}_sheet.png"))
    print("sheet", t)
