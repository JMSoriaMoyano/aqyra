#!/usr/bin/env python3
"""QA Estructurando 2.0 - Oraculo 2D del Cajon O (numpy puro, direct stiffness).
Modelo plano Y-Z (alzado desarrollado) de la viga-celosia/Vierendeel del Cajon O,
con los NUDOS REALES del IFC (cotas Z reales 5.75/8.833/11.917/15 = 4 cordones;
posiciones Y reales de los montantes; APOYOS en los rangos Y reales de los muros).

El Cajon O 3D es un cajon de DOS planos verticales (ext x~5.27 e int x~6.47) a 1.2 m;
trabaja como viga de gran canto. Resolvemos UN plano vertical equivalente que toma la
mitad de la carga; el axil de cordon real se reparte ademas entre los 2 planos.

Frame 2D (3 GdL/nudo: uy,uz,rx) -> nudos rigidos (Vierendeel real, SHS soldados).
Verifica: solido rigido (=3), EQUILIBRIO (SFy,SFz,SM), reacciones por muro (S-D1),
axil de cordon (DEC-B2), diagonal (DEC-B1), montante (DEC-B4) y L de pandeo real.
"""
import json, numpy as np

d=json.load(open('/sessions/practical-dazzling-hopper/mnt/qa/informes/qa_cajonO_geom.json'))
nodes3=np.array(d['nodes']); bars3=[b for b in d['bars'] if b[4].startswith('SHS')]
E=210e9; Gsh=81e9

# ---- proyectar a plano Y-Z: usamos UN plano (el exterior). Tomamos las barras cuyo
# nudo medio esta en el plano exterior (montantes ext, cordones ext, diafragmas no -horizontales en X-,
# diagonales del plano ext). Para robustez construimos la celosia 2D a partir de la
# RETICULA real: 4 niveles Z x posiciones Y de montantes. ----
Zlev=[5.75,8.833,11.917,15.0]
# Y de montantes (linea ext): de la extraccion
Ys=sorted(set(round(float(nodes3[b[2]][1]),2) for b in bars3 if b[0]=='Cajon O montante ext'))
print("Niveles Z:",Zlev)
print("Posiciones Y de montantes:",Ys)

# nudos 2D = (Y,Z) en la retícula
node2={}; coords=[]
def nid(y,z):
    k=(round(y,2),round(z,3))
    if k not in node2:
        node2[k]=len(coords); coords.append((y,z))
    return node2[k]
# cordones: por cada nivel Z, barra entre montantes consecutivos
els=[]  # (tipo,perfil,n0,n1)
# perfiles reales
CORD='SHS 180x8'; POST='SHS 120x6'
for z in Zlev:
    for y0,y1 in zip(Ys[:-1],Ys[1:]):
        els.append(('cordon',CORD,nid(y0,z),nid(y1,z)))
# montantes: en cada Y, barra entre niveles Z consecutivos
for y in Ys:
    for z0,z1 in zip(Zlev[:-1],Zlev[1:]):
        els.append(('montante',POST,nid(y,z0),nid(y,z1)))
# diagonales reales del plano: conectan (Y_i,Z_k)->(Y_{i+1},Z_{k+1}) - patron del IFC
# del extracto: #695 (5.27,0,5.75)->(4.88,3,8.833) = (Y0,Z0)->(Y1,Z1). Diagonal ascendente.
# Asignamos diagonal en cada panel (entre montantes y entre niveles)
DIAGP='SHS 200x10'
for (y0,y1) in zip(Ys[:-1],Ys[1:]):
    for (z0,z1) in zip(Zlev[:-1],Zlev[1:]):
        els.append(('diagonal',DIAGP,nid(y0,z0),nid(y1,z1)))

Nn=len(coords); coords=np.array(coords)
print(f"Celosia 2D: nudos={Nn}  barras={len(els)}")

def shs(name):
    p=name.replace('SHS','').strip().replace('×','x'); b,t=p.split('x')
    b=float(b)/1000.; t=float(t)/1000.
    A=b*b-(b-2*t)**2; I=(b**4-(b-2*t)**4)/12.0
    return A,I

def frame2d(p0,p1,A,I):
    dy,dz=p1[0]-p0[0],p1[1]-p0[1]; L=np.hypot(dy,dz); c,s=dy/L,dz/L
    EA=E*A/L; EI=E*I
    k=np.array([
      [EA,0,0,-EA,0,0],
      [0,12*EI/L**3,6*EI/L**2,0,-12*EI/L**3,6*EI/L**2],
      [0,6*EI/L**2,4*EI/L,0,-6*EI/L**2,2*EI/L],
      [-EA,0,0,EA,0,0],
      [0,-12*EI/L**3,-6*EI/L**2,0,12*EI/L**3,-6*EI/L**2],
      [0,6*EI/L**2,2*EI/L,0,-6*EI/L**2,4*EI/L]])
    T=np.array([
      [c,s,0,0,0,0],[-s,c,0,0,0,0],[0,0,1,0,0,0],
      [0,0,0,c,s,0],[0,0,0,-s,c,0],[0,0,0,0,0,1]])
    return T.T@k@T,(c,s),L

ndof=3*Nn; K=np.zeros((ndof,ndof)); elinfo=[]
for typ,pf,n0,n1 in els:
    A,I=shs(pf); kg,cs,L=frame2d(coords[n0],coords[n1],A,I)
    dofs=[3*n0,3*n0+1,3*n0+2,3*n1,3*n1+1,3*n1+2]
    K[np.ix_(dofs,dofs)]+=kg
    elinfo.append((typ,pf,n0,n1,cs,L,A))

# rigid body modes
w=np.linalg.eigvalsh(K)
nz=int(np.sum(np.abs(w)<1e-6*np.abs(w).max()))
print(f"Modos solido rigido (K libre) = {nz}  (esperado 3 en 2D)")

# apoyos: cordon inferior (Z=5.75) en rangos Y de los muros
def insup(y): return (0.0<=y<=3.05) or (24.0<=y<=32.0)
sup=[node2[(round(y,2),5.75)] for y in Ys if insup(y) and (round(y,2),5.75) in node2]
print(f"Apoyos (Z=5.75 en muros): {len(sup)} nudos -> Y={[coords[i][0] for i in sup]}")
fixed=[]
for i in sup: fixed+=[3*i,3*i+1]   # apoyo articulado: uy,uz fijos
fixed=sorted(set(fixed))

# carga: la mitad de Ftot (un plano). build Ftot total ~83 kN/m *40.52
w_d=83.0e3; Ltot=40.52; Ftot=w_d*Ltot; Fplane=Ftot/2.0
top=[node2[(round(y,2),15.0)] for y in Ys]
f=np.zeros(ndof); fpn=Fplane/len(top)
for i in top: f[3*i+1]-=fpn
print(f"Carga plano = {Fplane/1e3:.0f} kN (1/2 de {Ftot/1e3:.0f}) en {len(top)} nudos sup")

free=[i for i in range(ndof) if i not in set(fixed)]
u=np.zeros(ndof); u[free]=np.linalg.solve(K[np.ix_(free,free)],f[free])

# axiles
res=[]
for (typ,pf,n0,n1,cs,L,A) in elinfo:
    c,s=cs
    d0=u[3*n0:3*n0+2]; d1=u[3*n1:3*n1+2]
    elong=(d1[0]-d0[0])*c+(d1[1]-d0[1])*s
    res.append((typ,pf,E*A/L*elong,L,n0,n1))

R=K@u-f
Rz=sum(R[3*i+1] for i in sup)
Rlab=sum(R[3*i+1] for i in sup if coords[i][0]<=3.05)
Rvest=sum(R[3*i+1] for i in sup if coords[i][0]>=24.0)
print(f"\n=== EQUILIBRIO (un plano) ===")
print(f"  carga={-f[1::3].sum()/1e3:.0f} kN  reaccion={Rz/1e3:.0f} kN  residuo Fz={(Rz+f[1::3].sum())/1e3:.2e}")
print(f"  SFy={(K@u-f)[0::3].sum()/1e3:.2e} kN (debe ~0)")
print(f"  Reaccion NC-Lab(Y<=3)={Rlab/1e3:.0f} kN ({100*Rlab/Rz:.0f}%)  NC-Vest(Y>=24)={Rvest/1e3:.0f} kN ({100*Rvest/Rz:.0f}%)")
# en total (2 planos) las reacciones se duplican:
print(f"  -> TOTAL 2 planos: Lab={2*Rlab/1e3:.0f} kN, Vest={2*Rvest/1e3:.0f} kN; build asumio 65/35")

# axil cordon (un plano). El axil de cordon real del cajon = reparto entre 2 planos
cor=[r for r in res if r[0]=='cordon']; cc=max(cor,key=lambda r:abs(r[2]))
dia=[r for r in res if r[0]=='diagonal']; dc=min(dia,key=lambda r:r[2])
mon=[r for r in res if r[0]=='montante']; mc=min(mon,key=lambda r:r[2])
print(f"\n=== AXILES (oraculo 2D, un plano) ===")
print(f"  CORDON  N_max={cc[2]/1e3:+.0f} kN (tracc {max(r[2] for r in cor)/1e3:+.0f} / compr {min(r[2] for r in cor)/1e3:+.0f}) L_seg={cc[3]:.2f}")
print(f"  DIAGONAL N_compr_max={dc[2]/1e3:+.0f} kN  L={dc[3]:.2f} m  ({dc[1]})")
print(f"  MONTANTE N_compr_max={mc[2]/1e3:+.0f} kN  L_segmento={mc[3]:.2f} m  ({mc[1]})")
print(f"  (cordon real del cajon ~ por plano; comparar con build N_Ed cordon=409, diag=778, montante=250)")

json.dump({'plano_Rlab':Rlab/1e3,'plano_Rvest':Rvest/1e3,
           'tot_Rlab':2*Rlab/1e3,'tot_Rvest':2*Rvest/1e3,
           'cordon_N':cc[2]/1e3,'diag_N':dc[2]/1e3,'diag_L':dc[3],
           'montante_N':mc[2]/1e3,'montante_L':mc[3],'rbm':nz},
          open('/sessions/practical-dazzling-hopper/mnt/qa/informes/qa_truss2d_axiles.json','w'))
print("\nGuardado qa_truss2d_axiles.json")
