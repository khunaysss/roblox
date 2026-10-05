"""Gegenprobe: liest die erzeugten Luau-Daten, baut sie wie Roblox nach (in Blender) und rendert."""
import os, sys, re, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "characters", "blender"))
import bpy
from mathutils import Matrix, Vector
import avatar_lib as L
from avatar_lib import M, S

C = Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0)))
ROW = re.compile(r'\{"([^"]*)","([BCS])",([^}]*)\}')

def parse_rows(text):
    out = []
    for m in ROW.finditer(text):
        name, kind, rest = m.group(1), m.group(2), m.group(3)
        parts = rest.split(",")
        nums = [float(x) for x in parts[:15]]
        hexc = parts[15].strip('"'); mcode = int(parts[16])
        out.append((name, kind, nums, hexc, mcode))
    return out

def build(rows, scale):
    for name, kind, n, hexc, mcode in rows:
        size = Vector(n[0:3]); pos = Vector(n[3:6])
        Rr = Matrix((n[6:9], n[9:12], n[12:15]))      # Roblox-Rotation (Zeilen)
        Rb = C.transposed() @ Rr                       # Spalten = Part-Achsen in Blender
        pb = C.transposed() @ pos / scale
        sz = size / scale
        if kind == "C":
            bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1, vertices=20)
            o = bpy.context.object
            # Zylinderachse (lokal Z) -> Part-X; Groesse X = Laenge
            local = Matrix(((0, 1, 0), (0, 0, 1), (1, 0, 0))).transposed()
            o.matrix_world = Matrix.Translation(pb) @ (Rb @ Matrix(((0, 0, 1), (1, 0, 0), (0, 1, 0)))).to_4x4() @ Matrix.Diagonal((sz.y, sz.z, sz.x, 1))
        elif kind == "S":
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, segments=16, ring_count=10)
            o = bpy.context.object
            o.matrix_world = Matrix.Translation(pb) @ Rb.to_4x4() @ Matrix.Diagonal((sz.x, sz.y, sz.z, 1))
        else:
            bpy.ops.mesh.primitive_cube_add(size=1)
            o = bpy.context.object
            o.matrix_world = Matrix.Translation(pb) @ Rb.to_4x4() @ Matrix.Diagonal((sz.x, sz.y, sz.z, 1))
        o.data.materials.append(M(hexc, emit=4 if mcode == 1 else 0, metal=1.0 if mcode == 2 else 0.0, rough=0.3))
        o.parent = S.root
        S.objs.append(o)

if __name__ == "__main__":
    lua, fig, scale, out, tier = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4], sys.argv[5]
    text = open(lua).read()
    if fig != "-":
        i = text.index('{"' + fig + '", "')
        j = text.index("}},", i)
        text = text[i:j]
    rows = parse_rows(text)
    L.reset("verify")
    build(rows, scale)
    L.render(out, tier=tier, res=420, samples=12)
    print("rows", len(rows))
