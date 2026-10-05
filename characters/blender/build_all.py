"""Baut alle Figuren: python3 build_all.py [Tier ...] [--only Key] [--res N]
Ausgabe: characters/export/<Tier>/<Key>.fbx, characters/preview/<Tier>/<Key>.png
"""
import os, sys, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import avatar_lib as L
from roster import TIERS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    args = sys.argv[1:]
    only = args[args.index("--only") + 1] if "--only" in args else None
    res = int(args[args.index("--res") + 1]) if "--res" in args else 420
    tiers = [a for a in args if a in TIERS] or list(TIERS)
    for t in tiers:
        os.makedirs(os.path.join(ROOT, "export", t), exist_ok=True)
        os.makedirs(os.path.join(ROOT, "preview", t), exist_ok=True)
        for key, fn in TIERS[t]:
            if only and only != key:
                continue
            try:
                L.reset(key.split("_", 1)[1])
                fn()
                L.tier_fx(t)
                L.export(os.path.join(ROOT, "export", t, key + ".fbx"))
                L.render(os.path.join(ROOT, "preview", t, key + ".png"), tier=t, res=res, samples=16)
                print("DONE", t, key, flush=True)
            except Exception:
                print("FAIL", t, key, flush=True)
                traceback.print_exc()

if __name__ == "__main__":
    main()
