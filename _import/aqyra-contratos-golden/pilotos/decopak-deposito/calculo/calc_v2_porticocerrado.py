# -*- coding: utf-8 -*-
import sys; sys.path.insert(0,"/tmp/pylibs")
import numpy as np, json
Ecm=32837e3
B=11.37; Hc=4.95; tf=0.60; tw=0.50; tr=0.70
g_w=25.0; g_h2o=10.0; g_s=20.0; K0=0.5; q_sob=20.0; hw=4.35; ks=80000.0
def sec(t): return dict(EA=Ecm*t, EI=Ecm*t**3/12.0)
SEC={'raft':sec(tf),'wall':sec(tw),'roof':sec(tr)}
ne=20
def lin(p,q,n): return [(p[0]+(q[0]-p[0])*i/n,p[1]+(q[1]-p[1])*i/n) for i in range(n+1)]
A=(0,0);Bn=(B,0);C=(B,Hc);D=(0,Hc)
coords=[]; elems=[]
def addnode(p):
    for i,c in enumerate(coords):
        if abs(c[0]-p[0])<1e-6 and abs(c[1]-p[1])<1e-6: return i
    coords.append(p); return len(coords)-1
for stype,p,q in [('raft',A,Bn),('wall',Bn,C),('roof',C,D),('wall',D,A)]:
    pts=lin(p,q,ne)
    for i in range(ne): elems.append((addnode(pts[i]),addnode(pts[i+1]),stype))
N=len(coords); ndof=3*N
def kloc(EA,EI,L):
    k=np.zeros((6,6)); k[0,0]=k[3,3]=EA/L; k[0,3]=k[3,0]=-EA/L
    a=EI/L**3; kb=a*np.array([[12,6*L,-12,6*L],[6*L,4*L*L,-6*L,2*L*L],[-12,-6*L,12,-6*L],[6*L,2*L*L,-6*L,4*L*L]])
    for ii,iv in enumerate([1,2,4,5]):
        for jj,jv in enumerate([1,2,4,5]): k[iv,jv]=kb[ii,jj]
    return k
def T(c,s):
    t=np.array([[c,s,0],[-s,c,0],[0,0,1]]); TT=np.zeros((6,6)); TT[:3,:3]=t; TT[3:,3:]=t; return TT
def lf_builder(vase_full,traffic,char=False):
    gG=gQ=gW=gGr=1.0
    if not char: gG=1.35;gQ=1.5;gW=1.5;gGr=1.35
    def lf(stype,xc):
        fx=fz=0.0
        if stype=='roof':
            perm=tr*g_w+1.5; q=perm*gGr+(9.0*gQ if traffic else 0.0); fz=-q
        elif stype=='raft':
            q=tf*g_w*gGr+(g_h2o*hw*gW if vase_full else 0.0); fz=-q
        elif stype=='wall':
            z=xc[1]; pw=(g_h2o*max(0.0,hw-z)) if vase_full else 0.0
            prof_t=(Hc+0.30-z); pe=K0*g_s*max(0.0,prof_t)+K0*q_sob
            indir=1.0 if xc[0]<B/2 else -1.0
            fx=(gG*pe)*indir+(gW*pw)*(-indir)
        return fx,fz
    return lf
def run(vase_full,traffic,char=False,tandem=False):
    lf=lf_builder(vase_full,traffic,char)
    K=np.zeros((ndof,ndof)); Fv=np.zeros(ndof); store=[]
    for (n1,n2,stype) in elems:
        p1=np.array(coords[n1]); p2=np.array(coords[n2]); L=np.linalg.norm(p2-p1)
        c=(p2[0]-p1[0])/L; s=(p2[1]-p1[1])/L; Sx=SEC[stype]
        ke=kloc(Sx['EA'],Sx['EI'],L); Te=T(c,s); Kg=Te.T@ke@Te
        fx,fz=lf(stype,(p1+p2)/2); wl=fx*(-s)+fz*c; al=fx*c+fz*s
        feL=np.array([al*L/2,wl*L/2,wl*L*L/12,al*L/2,wl*L/2,-wl*L*L/12])
        fe=Te.T@feL; dof=[3*n1,3*n1+1,3*n1+2,3*n2,3*n2+1,3*n2+2]
        for i in range(6):
            Fv[dof[i]]+=fe[i]
            for j in range(6): K[dof[i],dof[j]]+=Kg[i,j]
        store.append((dof,ke,Te,feL,p1,p2,stype))
    le=B/ne
    for i,cc in enumerate(coords):
        if abs(cc[1])<1e-6:
            K[3*i+1,3*i+1]+=ks*(le if 1e-6<cc[0]<B-1e-6 else le/2)
    K[3*addnode((B/2,0)),3*addnode((B/2,0))]+=1e9
    if tandem:
        Ptd=68.3*(1.0 if char else 1.5); Fv[3*addnode((B/2,Hc))+1]+=-Ptd
    U=np.linalg.solve(K,Fv)
    # recuperación: fuerzas de extremo = ke@ul - feL ; momentos = comp 2 y 5
    out={'roof':[], 'wall':[], 'raft':[]}
    for (dof,ke,Te,feL,p1,p2,stype) in store:
        ul=Te@U[dof]; fend=ke@ul-feL
        M1=-fend[2]; M2=fend[5]
        out[stype].append((p1,p2,M1,M2))
    return out,U
def env(out):
    r={}
    for st,lst in out.items():
        Ms=[]; 
        for (p1,p2,M1,M2) in lst: Ms+=[M1,M2]
        r[st]=dict(Mmin=round(min(Ms),1),Mmax=round(max(Ms),1))
    return r
# validación: corner equilibrium roof vs wall en C=(B,Hc)
o,_=run(True,True,tandem=True)
def at_node(out,node):
    vals=[]
    for st,lst in out.items():
        for (p1,p2,M1,M2) in lst:
            if np.allclose(p1,node): vals.append((st,'i',round(M1,1)))
            if np.allclose(p2,node): vals.append((st,'j',round(M2,1)))
    return vals
print("Equilibrio esquina C (roof+wall):", at_node(o,(B,Hc)))
for name,(vf,tr_,td) in {"FULL+traffic":(True,True,True),"EMPTY+traffic":(False,True,True),"FULL no-traffic":(True,False,False)}.items():
    o,_=run(vf,tr_,tandem=td); print(name, json.dumps(env(o),ensure_ascii=False))

print("\n--- DIAGNÓSTICO momentos por nodo (combo EMPTY+traffic+tandem) ---")
o,_=run(False,True,tandem=True)
def along(out,stype,axis,coord_const,nconst_idx):
    pts=[]
    for (p1,p2,M1,M2) in out[stype]:
        pts.append((p1,M1)); pts.append((p2,M2))
    # ordenar por la coordenada que varía
    pts=sorted(pts,key=lambda t:(t[0][axis]))
    return pts
roof=along(o,'roof',0,None,None)
print("ROOF M a lo largo (x, M):")
seen=set()
for p,M in roof:
    key=round(p[0],2)
    if key in seen: continue
    seen.add(key)
    if abs(p[0]-round(p[0]))<0.06 or p[0] in (0,B):
        print("  x=%.2f  M=%.1f"%(p[0],M))
wall=along(o,'wall',1,None,None)
print("WALL M a lo largo (z, M) [una cara]:")
seen=set()
for p,M in wall:
    if abs(p[0]-B)>0.01: continue
    key=round(p[1],2)
    if key in seen: continue
    seen.add(key)
    if abs(p[1]-round(p[1]*2)/2)<0.06:
        print("  z=%.2f  M=%.1f"%(p[1],M))
