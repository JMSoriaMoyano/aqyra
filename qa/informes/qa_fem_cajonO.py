#!/usr/bin/env python3
"""QA Estructurando 2.0 - Solver FEM nodal independiente del Cajon O.
Metodo directo de rigidez, barras articuladas 3D (solo axil), numpy puro.
Oraculo independiente del build (que uso areas tributarias + equilibrio global).

Pasos:
 1. Lee nudos y conectividad REALES del IFC (qa_cajonO_geom.json).
 2. Ensambla K global (6x6 dof? no: 3 dof/nodo, traslacion). Barra axil 3D.
 3. Aplica apoyos en los nudos del cordon inferior dentro de los muros HA.
 4. Aplica cargas de las hipotesis aprobadas (forjados) en los nudos del cajon.
 5. Verifica modos de solido rigido (K singular sin apoyos) y EQUILIBRIO global.
 6. Resuelve K u = f, recupera AXILES por barra. Reporta picos y reacciones.

NOTA: el modelo articulado puede ser localmente hipostatico en nudos que solo
reciben barras colineales; se trata anadiendo los diafragmas/diagonales reales y,
si hace falta, restringiendo el GdL fuera de plano de nudos de borde (se reporta).
"""
import json, numpy as np

GEOM = '/sessions/practical-dazzling-hopper/mnt/qa/informes/qa_cajonO_geom.json'
d = json.load(open(GEOM))
nodes = np.array(d['nodes'])          # (Nn,3)
bars_raw = d['bars']                  # [g, eid, n0, n1, pname]
Nn = len(nodes)

E = 210e9  # Pa, acero S355

# ---- Areas de seccion SHS (geometria de placas: A=b^2-(b-2t)^2) ----
def shs_area(name):
    # 'SHS 180x8'
    p = name.replace('SHS', '').strip().replace('×', 'x')
    b, t = p.split('x')
    b = float(b) / 1000.0; t = float(t) / 1000.0
    return b * b - (b - 2 * t) ** 2

def shs_props(name):
    p = name.replace('SHS', '').strip().replace('×', 'x')
    b, t = p.split('x'); b = float(b)/1000.; t = float(t)/1000.
    A = b*b - (b-2*t)**2
    I = (b**4 - (b-2*t)**4) / 12.0
    i = (I/A)**0.5
    return A, I, i

# ---- Ensamblaje rigidez axil 3D (3 dof/nodo) ----
ndof = 3 * Nn
K = np.zeros((ndof, ndof))
bars = []
for g, eid, n0, n1, pname in bars_raw:
    if not pname.startswith('SHS'):
        continue
    A = shs_area(pname)
    p0 = nodes[n0]; p1 = nodes[n1]
    L = np.linalg.norm(p1 - p0)
    if L < 1e-6:
        continue
    c = (p1 - p0) / L                  # cosenos directores
    k = E * A / L
    # matriz de rigidez axil 3D: k * [cc^T -cc^T; -cc^T cc^T]
    cc = np.outer(c, c)
    dofs = [3*n0, 3*n0+1, 3*n0+2, 3*n1, 3*n1+1, 3*n1+2]
    ke = np.block([[cc, -cc], [-cc, cc]]) * k
    for a in range(6):
        for b_ in range(6):
            K[dofs[a], dofs[b_]] += ke[a, b_]
    bars.append((g, eid, n0, n1, pname, c, L, A))

print(f"Nudos={Nn}  barras axiles={len(bars)}  ndof={ndof}")

# ---- Modos de solido rigido: K sin apoyos debe tener >= 6 autovalores ~0 ----
# (3 traslaciones + 3 rotaciones de la estructura 3D)
w = np.linalg.eigvalsh(K)
nzero = int(np.sum(np.abs(w) < 1e-3 * np.abs(w).max()))
print(f"Autovalores nulos de K (modos solido rigido + mecanismos) = {nzero}")
print(f"  (esperado >=6 por solido rigido; exceso = mecanismos locales del modelo articulado)")

# ---- Apoyos: nudos del cordon inferior (Z=5.75) dentro de los muros ----
Zbot = 5.75
# NC-Lab: Y in [0,3];  NC-Vest: Y in [24.8, 31.9]
def in_support(p):
    return abs(p[2] - Zbot) < 0.05 and (
        (0.0 <= p[1] <= 3.05) or (24.0 <= p[1] <= 32.0))
sup_nodes = [i for i in range(Nn) if in_support(nodes[i])]
print(f"\nNudos de apoyo (cordon inf en muros): {len(sup_nodes)}")
for i in sup_nodes:
    print('  node', i, np.round(nodes[i], 2))

# fijamos las 3 traslaciones en los nudos de apoyo
fixed = []
for i in sup_nodes:
    fixed += [3*i, 3*i+1, 3*i+2]
fixed = sorted(set(fixed))

# ---- Cargas: hipotesis aprobadas (doc 02). Forjados cassette -> nudos sup ----
# Carga ELU forjado oficinas: 6.60 kN/m2 ; vuelo medio ~6.3 m por planta ;
# 4 plantas cuelgan del cajon. Distribuimos la carga descendente del forjado en
# los nudos del cordon SUPERIOR (Z=15) y niveles intermedios donde apoyan plantas.
# Carga lineal total sobre el cajon (build): q ~ 83 kN/m sobre L=40.52 m.
# Repartimos por nudos de cada nivel proporcional a su area tributaria longitudinal.
w_d = 83.0e3   # N/m (envolvente build, incluye 4 plantas + PP acero)
Ltot = 40.52
Ftot = w_d * Ltot
# nudos receptores: todos los del plano exterior (x~5.27) y los niveles de planta
# Para reparto fisico: las plantas estan a Z=5.75,8.833,11.917,15 -> cargamos los
# 4 niveles del cordon EXTERIOR (x~5.27) por igual (cada planta su area).
recv = [i for i in range(Nn) if abs(nodes[i][0]-5.27) < 0.05]
# excluir nudos de apoyo de recibir carga puntual concentrada (igual da, se reparte)
# carga vertical (-Z) por nudo
f = np.zeros(ndof)
if recv:
    fpn = Ftot / len(recv)
    for i in recv:
        f[3*i+2] -= fpn
print(f"\nCarga total aplicada Ftot = {Ftot/1e3:.0f} kN en {len(recv)} nudos (cordon ext, todos los niveles)")

# ---- Reduccion y resolucion ----
free = [i for i in range(ndof) if i not in set(fixed)]
Kff = K[np.ix_(free, free)]
ff = f[free]
# regularizacion minima para mecanismos locales fuera de plano (se reporta)
# detectar dof con rigidez nula en diagonal
diag = np.diag(Kff)
nrigid = int(np.sum(diag < 1e-6))
if nrigid:
    print(f"  AVISO: {nrigid} GdL libres con rigidez ~0 (mecanismo articulado local).")
    print("         Se les anade un muelle debil 1e-3*k_medio para estabilizar y se reporta.")
    kreg = 1e-3 * np.median(diag[diag > 0])
    for j in range(len(free)):
        if diag[j] < 1e-6:
            Kff[j, j] += kreg

u_free = np.linalg.solve(Kff, ff)
u = np.zeros(ndof)
u[free] = u_free

# ---- Axiles por barra ----
results = []
for (g, eid, n0, n1, pname, c, L, A) in bars:
    d0 = u[3*n0:3*n0+3]; d1 = u[3*n1:3*n1+3]
    elong = np.dot(d1 - d0, c)
    N = E * A / L * elong          # N (+traccion, -compresion)
    results.append((g, eid, pname, N, L, A))

# ---- Verificacion de EQUILIBRIO global: sum(reacciones) = sum(cargas) ----
R = K @ u - f                       # reacciones en GdL fijos (resto ~0)
Rz = sum(R[3*i+2] for i in sup_nodes)
print(f"\n=== EQUILIBRIO GLOBAL ===")
print(f"  Suma cargas verticales aplicadas = {-f.reshape(-1,3)[:,2].sum()/1e3:.1f} kN (hacia abajo)")
print(f"  Suma reacciones verticales       = {Rz/1e3:.1f} kN (hacia arriba)")
print(f"  Residuo SF_z = {(Rz + f.reshape(-1,3)[:,2].sum())/1e3:.3e} kN  (debe ~0)")
# reaccion por muro
Rlab = sum(R[3*i+2] for i in sup_nodes if nodes[i][1] <= 3.05)
Rvest = sum(R[3*i+2] for i in sup_nodes if nodes[i][1] >= 24.0)
print(f"  Reaccion NC-Lab (Y<=3)  = {Rlab/1e3:.0f} kN  ({100*Rlab/Rz:.0f} %)")
print(f"  Reaccion NC-Vest (Y>=24)= {Rvest/1e3:.0f} kN  ({100*Rvest/Rz:.0f} %)")

# ---- Picos de axil por grupo ----
print(f"\n=== AXILES MAXIMOS por grupo (FEM nodal independiente) ===")
from collections import defaultdict
byg = defaultdict(list)
for r in results: byg[r[0]].append(r)
for g in ['Cajon O cordon ext','Cajon O cordon int','Cajon O diagonal',
          'Cajon O montante ext','Cajon O montante int']:
    rs = byg.get(g, [])
    if not rs: continue
    Ns = [r[3] for r in rs]
    nmax = max(rs, key=lambda r: abs(r[3]))
    print(f"  [{g}] perfil(es)={sorted(set(r[2] for r in rs))}")
    print(f"      N_max_traccion = {max(Ns)/1e3:+.0f} kN | N_max_compresion = {min(Ns)/1e3:+.0f} kN")
    print(f"      barra mas solicitada #{nmax[1]} ({nmax[2]}) N={nmax[3]/1e3:+.0f} kN L={nmax[4]:.2f} m")

# montante critico: el de mayor compresion + su L_segmento real
mont = [r for r in results if 'montante' in r[0]]
if mont:
    mc = min(mont, key=lambda r: r[3])
    print(f"\n=== DEC-B4 MONTANTE ===")
    print(f"  Montante mas comprimido: #{mc[1]} {mc[2]} N={mc[3]/1e3:+.0f} kN  L_barra={mc[4]:.2f} m")

# guardar
json.dump({'axiles': [[r[0], r[1], r[2], r[3]/1e3, r[4]] for r in results],
           'Rlab_kN': Rlab/1e3, 'Rvest_kN': Rvest/1e3, 'Rtot_kN': Rz/1e3},
          open('/sessions/practical-dazzling-hopper/mnt/qa/informes/qa_cajonO_axiles.json', 'w'))
print("\nGuardado qa_cajonO_axiles.json")
