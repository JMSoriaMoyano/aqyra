#!/usr/bin/env python3
"""QA Estructurando 2.0 - Solver FEM de PORTICO 3D del Cajon O (numpy puro).
Oraculo INDEPENDIENTE del build. Euler-Bernoulli 3D, 6 GdL/nudo (rigido en nudos).
El Cajon O es una celosia/VIERENDEEL de SHS soldados -> nudos transmiten momento.

CLAVE de idealizacion: en el IFC los cordones son UNA barra continua de 40.86 m por
nivel; los montantes y diagonales solo tocan sus extremos. Para construir la celosia
REAL hay que SUBDIVIDIR cada barra en los puntos donde otra barra la intersecta
(nudos de la celosia). Eso hacemos aqui (split por proyeccion de nudos sobre barras).

Verifica modos de solido rigido (=6), EQUILIBRIO (SF,SM), y extrae AXILES reales.
"""
import json, numpy as np
from collections import defaultdict

GEOM='/sessions/practical-dazzling-hopper/mnt/qa/informes/qa_cajonO_geom.json'
d=json.load(open(GEOM))
nodes0=[np.array(p) for p in d['nodes']]
bars_raw=[b for b in d['bars'] if b[4].startswith('SHS')]
E=210e9; Gsh=81e9

# ---- nodo global con tolerancia ----
TOL=1e-3
nodes=[]; nkey={}
def getnid(p):
    k=tuple(np.round(np.array(p)/TOL).astype(int))
    if k in nkey: return nkey[k]
    nkey[k]=len(nodes); nodes.append(np.array(p,float)); return nkey[k]

# barras iniciales con coords
segs=[]
for g,eid,n0,n1,pname in bars_raw:
    p0=nodes0[n0]; p1=nodes0[n1]
    segs.append([g,eid,pname,p0.copy(),p1.copy()])

# todos los nudos existentes (extremos)
allpts=[]
for s in segs:
    allpts.append(s[3]); allpts.append(s[4])

# ---- subdividir cada barra en los puntos (de otros nudos) que caen sobre ella ----
def split_bar(g,eid,pname,p0,p1,pts):
    L=np.linalg.norm(p1-p0)
    u=(p1-p0)/L
    ts=[0.0,1.0]
    for q in pts:
        d=q-p0
        t=np.dot(d,u)/L
        if 1e-4<t<1-1e-4:
            perp=d-np.dot(d,u)*u
            if np.linalg.norm(perp)<5e-3:   # 5 mm de la barra -> intersecta
                ts.append(t)
    ts=sorted(set(round(t,6) for t in ts))
    out=[]
    for a,b in zip(ts[:-1],ts[1:]):
        pa=p0+a*L*u; pb=p0+b*L*u
        out.append((g,eid,pname,pa,pb))
    return out

# para eficiencia agrupamos puntos candidatos (todos los extremos)
P=np.array(allpts)
newsegs=[]
for g,eid,pname,p0,p1 in segs:
    # candidatos: puntos en bounding box de la barra
    lo=np.minimum(p0,p1)-0.01; hi=np.maximum(p0,p1)+0.01
    mask=np.all((P>=lo)&(P<=hi),axis=1)
    cand=P[mask]
    newsegs+=split_bar(g,eid,pname,p0,p1,cand)

# ensamblar nudos
bars=[]
for g,eid,pname,p0,p1 in newsegs:
    n0=getnid(p0); n1=getnid(p1)
    if n0!=n1: bars.append((g,eid,pname,n0,n1))
Nn=len(nodes)
nodes=np.array(nodes)
print(f"Tras subdividir: nudos={Nn}  barras={len(bars)}")

# connectivity check
deg=defaultdict(int); adj=defaultdict(set)
for g,eid,p,n0,n1 in bars:
    deg[n0]+=1; deg[n1]+=1; adj[n0].add(n1); adj[n1].add(n0)
seen=set();comps=0
for s in range(Nn):
    if s in seen or deg[s]==0: continue
    comps+=1; st=[s]
    while st:
        x=st.pop()
        if x in seen: continue
        seen.add(x); st+=list(adj[x])
print(f"componentes conexas={comps}  nudos grado1={sum(1 for i in range(Nn) if deg[i]==1)}")

def shs_props(name):
    p=name.replace('SHS','').strip().replace('×','x'); b,t=p.split('x')
    b=float(b)/1000.; t=float(t)/1000.
    A=b*b-(b-2*t)**2; I=(b**4-(b-2*t)**4)/12.0
    bm=b-t; Am=bm*bm; J=Am*Am*t/bm
    return A,I,I,J

def beam3d(p0,p1,A,Iy,Iz,J):
    L=np.linalg.norm(p1-p0); x=(p1-p0)/L
    ref=np.array([1.,0.,0.]) if abs(x[2])>0.99 else np.array([0.,0.,1.])
    y=np.cross(ref,x); y/=np.linalg.norm(y); z=np.cross(x,y)
    R=np.vstack([x,y,z]); T=np.zeros((12,12))
    for i in range(4): T[3*i:3*i+3,3*i:3*i+3]=R
    EA=E*A/L; GJ=Gsh*J/L; k=np.zeros((12,12))
    k[0,0]=k[6,6]=EA; k[0,6]=k[6,0]=-EA
    k[3,3]=k[9,9]=GJ; k[3,9]=k[9,3]=-GJ
    for (idx,EI) in [([1,5,7,11],E*Iz),([2,4,8,10],E*Iy)]:
        a=12*EI/L**3; bb=6*EI/L**2; c=4*EI/L; e=2*EI/L
        if idx[0]==1:
            kb=np.array([[a,bb,-a,bb],[bb,c,-bb,e],[-a,-bb,a,-bb],[bb,e,-bb,c]])
        else:
            kb=np.array([[a,-bb,-a,-bb],[-bb,c,bb,e],[-a,bb,a,bb],[-bb,e,bb,c]])
        for ii,I in enumerate(idx):
            for jj,Jd in enumerate(idx): k[I,Jd]+=kb[ii,jj]
    return T.T@k@T,x,L

ndof=6*Nn; K=np.zeros((ndof,ndof)); barel=[]
for g,eid,pname,n0,n1 in bars:
    A,Iy,Iz,J=shs_props(pname)
    kg,xax,L=beam3d(nodes[n0],nodes[n1],A,Iy,Iz,J)
    dofs=list(range(6*n0,6*n0+6))+list(range(6*n1,6*n1+6))
    K[np.ix_(dofs,dofs)]+=kg
    barel.append((g,eid,pname,n0,n1,xax,L,A))

# rigid body modes (only if connected single component)
if comps==1:
    w=np.linalg.eigvalsh(K)
    nz=int(np.sum(np.abs(w)<1e-6*np.abs(w).max()))
    print(f"Modos solido rigido K libre = {nz} (esperado 6)")

Zbot=5.75
def insup(p): return abs(p[2]-Zbot)<0.05 and((0.0<=p[1]<=3.05)or(24.0<=p[1]<=32.0))
sup=[i for i in range(Nn) if insup(nodes[i])]
fixed=[]
for i in sup: fixed+=list(range(6*i,6*i+3))
fixed=sorted(set(fixed))
print(f"Apoyos: {len(sup)} nudos")

top=[i for i in range(Nn) if abs(nodes[i][2]-15.0)<0.05]
w_d=83.0e3; Ftot=w_d*40.52
f=np.zeros(ndof); fpn=Ftot/len(top)
for i in top: f[6*i+2]-=fpn
print(f"Carga Ftot={Ftot/1e3:.0f} kN en {len(top)} nudos cordon superior")

free=[i for i in range(ndof) if i not in set(fixed)]
Kff=K[np.ix_(free,free)]; ff=f[free]
# si quedan dof rotacionales sueltos (grado1) -> muelle debil reportado
diag=np.diag(Kff).copy(); nweak=int(np.sum(diag<1e-3))
if nweak:
    kreg=1e-6*np.median(diag[diag>1])
    for j in range(len(free)):
        if diag[j]<1e-3: Kff[j,j]+=kreg
    print(f"  (regularizados {nweak} GdL rotacionales de extremos libres con muelle 1e-6; no afectan axiles de cordones/diagonales)")
u=np.zeros(ndof); u[free]=np.linalg.solve(Kff,ff)

results=[]
for (g,eid,pname,n0,n1,xax,L,A) in barel:
    elong=np.dot(u[6*n1:6*n1+3]-u[6*n0:6*n0+3],xax)
    results.append((g,eid,pname,E*A/L*elong,L,A,n0,n1))

R=K@u-f
Rz=sum(R[6*i+2] for i in sup)
Rlab=sum(R[6*i+2] for i in sup if nodes[i][1]<=3.05)
Rvest=sum(R[6*i+2] for i in sup if nodes[i][1]>=24.0)
print(f"\n=== EQUILIBRIO GLOBAL ===")
print(f"  carga total={-f[2::6].sum()/1e3:.0f} kN  reaccion total={Rz/1e3:.0f} kN  residuo={(Rz+f[2::6].sum())/1e3:.2e}")
print(f"  NC-Lab  = {Rlab/1e3:.0f} kN ({100*Rlab/Rz:.0f}%)   NC-Vest = {Rvest/1e3:.0f} kN ({100*Rvest/Rz:.0f}%)")
print(f"  >>> Build asumio reparto 65/35 Vest/Lab (S-D1)")

print(f"\n=== AXILES por grupo (FRAME 3D nudos reales) ===")
byg=defaultdict(list)
for r in results: byg[r[0]].append(r)
for g in ['Cajon O cordon ext','Cajon O cordon int','Cajon O diagonal','Cajon O montante ext','Cajon O montante int']:
    rs=byg.get(g,[]);
    if not rs: continue
    Ns=[r[3] for r in rs]; nmax=max(rs,key=lambda r:abs(r[3]))
    print(f"  [{g}] perfiles={sorted(set(r[2] for r in rs))}")
    print(f"     N_tracc_max={max(Ns)/1e3:+.0f}  N_compr_max={min(Ns)/1e3:+.0f} kN | critica #{nmax[1]} {nmax[2]} N={nmax[3]/1e3:+.0f} kN L={nmax[4]:.2f}")

diag_=[r for r in results if r[0]=='Cajon O diagonal']; dc=min(diag_,key=lambda r:r[3])
cor=[r for r in results if 'cordon' in r[0]]; cc=max(cor,key=lambda r:abs(r[3]))
print(f"\nDEC-B4 montante mas comprimido: #{mc[1]} {mc[2]} N={mc[3]/1e3:+.0f} kN L_segmento={mc[4]:.2f} m")
print(f"DEC-B1 diagonal mas comprimida: #{dc[1]} {dc[2]} N={dc[3]/1e3:+.0f} kN L={dc[4]:.2f} m")
print(f"DEC-B2 cordon mas solicitado:   #{cc[1]} {cc[2]} N={cc[3]/1e3:+.0f} kN L_seg={cc[4]:.2f} m")

json.dump({'Rlab_kN':Rlab/1e3,'Rvest_kN':Rvest/1e3,'Rtot_kN':Rz/1e3,'comps':comps,
           'montante_Ncrit_kN':mc[3]/1e3,'montante_Lseg_m':mc[4],
           'diagonal_Ncrit_kN':dc[3]/1e3,'diagonal_perfil':dc[2],
           'cordon_Ncrit_kN':cc[3]/1e3},
          open('/sessions/practical-dazzling-hopper/mnt/qa/informes/qa_cajonO_frame_axiles.json','w'))
print("\nGuardado qa_cajonO_frame_axiles.json")
