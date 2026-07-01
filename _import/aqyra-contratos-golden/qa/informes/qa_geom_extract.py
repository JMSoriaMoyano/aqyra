#!/usr/bin/env python3
"""QA Estructurando 2.0 - Extractor de geometria real del IFC (numpy puro).
Independiente del build. Resuelve la cadena de placements y las extrusiones
para obtener los nudos REALES (extremos) de cada barra del Cajon O y enlaces.

IFCEXTRUDEDAREASOLID(SweptArea, Position(AXIS2PLACEMENT3D), ExtrudeDir, Depth)
  - Position #pos = (pt, Z(axis), X(refdir))   -> origen y orientacion de la seccion
  - ExtrudeDir en el frame local de Position; mapeado a mundo por la base de Position
  - El solido se coloca ademas por el LocalPlacement del elemento (cadena de relativos)
Nudo inicial = origen de Position transformado por la cadena de placements.
Nudo final   = inicial + Depth * (R_chain @ R_pos @ ExtrudeDir_local)
"""
import re, sys, numpy as np

F = sys.argv[1] if len(sys.argv) > 1 else \
    "/sessions/practical-dazzling-hopper/mnt/Estructurando 2.0/pilotos/decopak-hq/modelo/DEC-PB-EBAN-HQ-Y-BIM-EST-02-EstructuraNucleoLateral-S1-v0.0.ifc"

txt = open(F, encoding='utf-8', errors='replace').read()
data = txt.split('DATA;', 1)[1].split('ENDSEC', 1)[0]
ent = {}
for m in re.finditer(r'#(\d+)\s*=\s*([A-Z0-9]+)\((.*?)\);\s*(?=#\d+\s*=|$)', data, re.S):
    ent[int(m.group(1))] = (m.group(2), m.group(3))

def args(s):
    out = []; d = 0; q = False; cur = ''
    for c in s:
        if c == "'": q = not q
        if not q:
            if c == '(': d += 1
            elif c == ')': d -= 1
        if c == ',' and d == 0 and not q:
            out.append(cur.strip()); cur = ''
        else: cur += c
    out.append(cur.strip()); return out

def ref(a):
    a = a.strip()
    return int(a[1:]) if a.startswith('#') else None

def get_point(idp):
    t, a = ent[idp]
    aa = args(a)
    nums = aa[0].strip()[1:-1]  # (x,y,z)
    return np.array([float(x) for x in nums.split(',')])

def get_dir(idd):
    if idd is None: return None
    t, a = ent[idd]
    aa = args(a)
    nums = aa[0].strip()[1:-1]
    v = np.array([float(x) for x in nums.split(',')])
    return v / np.linalg.norm(v)

def axis2_basis(idp):
    """Return (origin, R) where R columns = [X, Y, Z] world dirs of the placement."""
    t, a = ent[idp]
    aa = args(a)
    o = get_point(ref(aa[0]))
    z = get_dir(ref(aa[1])) if len(aa) > 1 and ref(aa[1]) else np.array([0., 0., 1.])
    x = get_dir(ref(aa[2])) if len(aa) > 2 and ref(aa[2]) else np.array([1., 0., 0.])
    if z is None: z = np.array([0., 0., 1.])
    if x is None: x = np.array([1., 0., 0.])
    # orthonormalize x against z
    x = x - np.dot(x, z) * z
    x = x / np.linalg.norm(x)
    y = np.cross(z, x)
    R = np.column_stack([x, y, z])
    return o, R

def local_placement_transform(idlp):
    """Resolve IFCLOCALPLACEMENT chain -> (origin, R) in world."""
    t, a = ent[idlp]
    aa = args(a)
    parent = ref(aa[0])
    rel = ref(aa[1])  # IFCAXIS2PLACEMENT3D
    o, R = axis2_basis(rel)
    if parent is not None:
        po, pR = local_placement_transform(parent)
        o = po + pR @ o
        R = pR @ R
    return o, R

def member_endpoints(eid):
    """Given element entity id, return (p_start, p_end, depth, profile_name)."""
    t, a = ent[eid]
    aa = args(a)
    lp = ref(aa[5])      # ObjectPlacement (LocalPlacement)
    rep = ref(aa[6])     # ProductDefinitionShape
    o_lp, R_lp = local_placement_transform(lp)
    # find the IFCEXTRUDEDAREASOLID under representation
    t2, a2 = ent[rep]
    reps = args(a2)[2].strip()[1:-1]  # list of shape reps
    solid = None
    for r in reps.split(','):
        r = r.strip()
        if not r.startswith('#'): continue
        tr, ar = ent[int(r[1:])]
        if tr == 'IFCSHAPEREPRESENTATION':
            items = args(ar)[3].strip()[1:-1]
            for it in items.split(','):
                it = it.strip()
                if it.startswith('#'):
                    ti, ai = ent[int(it[1:])]
                    if ti == 'IFCEXTRUDEDAREASOLID':
                        solid = int(it[1:]); break
        if solid: break
    if solid is None:
        return None
    ts, asd = ent[solid]
    sa = args(asd)
    prof = ref(sa[0]); pos = ref(sa[1]); ed = ref(sa[2]); depth = float(sa[3])
    # profile name
    tp, ap = ent[prof]
    pname = args(ap)[1].strip().strip("'")
    o_pos, R_pos = axis2_basis(pos)
    ed_local = get_dir(ed)
    # start point: position origin transformed by local placement
    p0 = o_lp + R_lp @ o_pos
    ed_world = R_lp @ (R_pos @ ed_local)
    p1 = p0 + depth * ed_world
    return p0, p1, depth, pname

# Collect Cajon O members
groups = ['Cajon O cordon ext', 'Cajon O cordon int', 'Cajon O montante ext',
          'Cajon O montante int', 'Cajon O diagonal', 'Cajon O diafragma inf',
          'Cajon O diafragma sup', 'Conexion dintel O', 'Conexion montante']
members = {}
for i, (t, a) in ent.items():
    if t in ('IFCMEMBER', 'IFCBEAM'):
        aa = args(a)
        name = aa[2].strip().strip("'")
        if name in groups:
            members.setdefault(name, []).append(i)

print("=== Conteo por grupo ===")
for g in groups:
    print(f"  {g:24s}: {len(members.get(g,[]))}")

# extract endpoints
allbars = []
for g, ids in members.items():
    for eid in ids:
        r = member_endpoints(eid)
        if r is None: continue
        p0, p1, depth, pname = r
        allbars.append((g, eid, p0, p1, depth, pname))

# Report bounding box and sample geometry per group
print("\n=== Geometria extraida (muestras) ===")
for g in groups:
    bars = [b for b in allbars if b[0] == g]
    if not bars: continue
    Ls = [b[4] for b in bars]
    pname = bars[0][5]
    print(f"\n[{g}]  perfil={pname}  n={len(bars)}  L: min={min(Ls):.3f} max={max(Ls):.3f}")
    for b in bars[:3]:
        print(f"   #{b[1]}: {np.round(b[2],3)} -> {np.round(b[3],3)}  L={b[4]:.3f}")

# Global node set
def keyp(p, tol=1e-3):
    return tuple(np.round(p / tol).astype(int))
nodes = {}
def nid(p):
    k = keyp(p)
    if k not in nodes:
        nodes[k] = (len(nodes), p)
    return nodes[k][0]
conn = []
for g, eid, p0, p1, depth, pname in allbars:
    conn.append((g, eid, nid(p0), nid(p1), pname))

print(f"\n=== Total nudos unicos (Cajon O+enlaces): {len(nodes)}  barras: {len(conn)} ===")
# bounding box
P = np.array([v[1] for v in nodes.values()])
print("BBox X:", P[:,0].min(), P[:,0].max(), " Y:", P[:,1].min(), P[:,1].max(), " Z:", P[:,2].min(), P[:,2].max())

# Save nodes & connectivity for FEM
import json
out = {
    'nodes': [list(map(float, v[1])) for k, v in sorted(nodes.items(), key=lambda x: x[1][0])],
    'bars': [[g, eid, n0, n1, pname] for g, eid, n0, n1, pname in conn],
}
json.dump(out, open('/sessions/practical-dazzling-hopper/mnt/qa/informes/qa_cajonO_geom.json', 'w'))
print("Guardado qa_cajonO_geom.json")
