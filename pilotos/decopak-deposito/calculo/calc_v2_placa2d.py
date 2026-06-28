# -*- coding: utf-8 -*-
"""Placa de Kirchhoff, elemento rectangular ACM (12 GdL). numpy puro.
Valida con placa cuadrada empotrada (Timoshenko) y calcula la cubierta del depósito."""
import sys; sys.path.insert(0,"/tmp/pylibs")
import numpy as np, json

def acm_K_and_B(a,b,D,nu):
    """Rigidez 12x12 del elemento ACM (lados 2a x 2b) y func. para momentos.
       a,b = SEMI-lados. Integración Gauss 2x2."""
    Db=D*np.array([[1,nu,0],[nu,1,0],[0,0,(1-nu)/2]])
    gp=[-1/np.sqrt(3),1/np.sqrt(3)]; K=np.zeros((12,12))
    # nodos: (-a,-b),(a,-b),(a,b),(-a,b); dof por nodo w,θx=dw/dy,θy=-dw/dx (conv. estándar ACM)
    def Bmat(xi,eta):
        x=xi*a; y=eta*b
        # polinomio: 1,x,y,x2,xy,y2,x3,x2y,xy2,y3,x3y,xy3
        # curvaturas: -[w,xx ; w,yy ; 2w,xy]
        # derivadas segundas de cada término
        terms_xx=[0,0,0,2,0,0,6*x,2*y,0,0,6*x*y,0]
        terms_yy=[0,0,0,0,0,2,0,0,2*x,6*y,0,6*x*y]
        terms_xy=[0,0,0,0,1,0,0,2*x,2*y,0,3*x*x,3*y*y]
        return np.array([terms_xx,terms_yy,[2*t for t in terms_xy]])
    # matriz C que relaciona coef. polinomio con GdL nodales
    nodes=[(-a,-b),(a,-b),(a,b),(-a,b)]
    C=np.zeros((12,12))
    def row_w(x,y): return [1,x,y,x*x,x*y,y*y,x**3,x*x*y,x*y*y,y**3,x**3*y,x*y**3]
    def row_tx(x,y): # dw/dy
        return [0,0,1,0,x,2*y,0,x*x,2*x*y,3*y*y,x**3,3*x*y*y]
    def row_ty(x,y): # -dw/dx
        return [-v for v in [0,1,0,2*x,y,0,3*x*x,2*x*y,y*y,0,3*x*x*y,y**3]]
    for i,(x,y) in enumerate(nodes):
        C[3*i]=row_w(x,y); C[3*i+1]=row_tx(x,y); C[3*i+2]=row_ty(x,y)
    Cinv=np.linalg.inv(C)
    for xi in gp:
        for eta in gp:
            B=Bmat(xi,eta)@Cinv   # 3x12 (curv en GdL)
            K+=(B.T@Db@B)*(a*b)   # jac=a*b, peso 1
    return K,Cinv,Bmat

def solve_plate(Lx,Ly,nx,ny,t,E,nu,q_unif,patch=None,bc='clamp'):
    D=E*t**3/(12*(1-nu**2))
    a=Lx/nx/2; b=Ly/ny/2
    Ke,Cinv,Bmat=acm_K_and_B(a,b,D,nu)
    nnx=nx+1; nny=ny+1; nn=nnx*nny; ndof=3*nn
    def nid(i,j): return j*nnx+i
    K=np.zeros((ndof,ndof)); F=np.zeros(ndof)
    elems=[]
    for j in range(ny):
        for i in range(nx):
            n=[nid(i,j),nid(i+1,j),nid(i+1,j+1),nid(i,j+1)]
            dof=[]
            for nn_ in n: dof+= [3*nn_,3*nn_+1,3*nn_+2]
            for r in range(12):
                for c in range(12): K[dof[r],dof[c]]+=Ke[r,c]
            elems.append((i,j,n,dof))
            # carga uniforme -> nodal (consistente simplificada: reparto a 4 nodos w)
            qe=q_unif
            if patch:
                x0=i*Lx/nx; x1=(i+1)*Lx/nx; y0=j*Ly/ny; y1=(j+1)*Ly/ny
                px0,px1,py0,py1=patch['box']
                ox=max(0,min(x1,px1)-max(x0,px0)); oy=max(0,min(y1,py1)-max(y0,py0))
                if ox>0 and oy>0:
                    qe=qe+patch['q']*(ox*oy)/((x1-x0)*(y1-y0))
            Ae=(Lx/nx)*(Ly/ny)
            for nn_ in n: F[3*nn_]+= -qe*Ae/4.0   # w hacia abajo (-)
    # BC
    fixed=set()
    for j in range(nny):
        for i in range(nnx):
            edge=(i==0 or i==nx or j==0 or j==ny)
            if edge:
                nn_=nid(i,j)
                if bc=='clamp': fixed.update([3*nn_,3*nn_+1,3*nn_+2])
                else: fixed.add(3*nn_)  # simple: solo w=0
    free=[d for d in range(ndof) if d not in fixed]
    U=np.zeros(ndof)
    U[free]=np.linalg.solve(K[np.ix_(free,free)],F[free])
    # momentos: evaluar en las 4 esquinas de cada elemento y promediar por nodo
    Db=D*np.array([[1,nu,0],[nu,1,0],[0,0,(1-nu)/2]])
    msum=np.zeros((nn,3)); mcnt=np.zeros(nn)
    corners=[(-1,-1),(1,-1),(1,1),(-1,1)]
    for (i,j,n,dof) in elems:
        ue=U[dof]
        for k,(xi,eta) in enumerate(corners):
            m=Db@(Bmat(xi,eta)@Cinv@ue)
            msum[n[k]]+=m; mcnt[n[k]]+=1
    mnod=msum/np.maximum(mcnt,1)[:,None]
    def mom_at(x,y):
        i=int(round(x/(Lx/nx))); j=int(round(y/(Ly/ny)))
        i=min(max(i,0),nx); j=min(max(j,0),ny)
        return mnod[nid(i,j)]
    recs=[]
    for j in range(nny):
        for i in range(nnx):
            recs.append((i*Lx/nx,j*Ly/ny,*mnod[nid(i,j)]))
    return U,recs,D,mom_at

# ---------------- VALIDACIÓN: placa cuadrada empotrada, carga uniforme ----------------
E=32837e3; nu=0.2
L=5.0; t=0.2; q=10.0
U,recs,D,mom_at=solve_plate(L,L,24,24,t,E,nu,q,bc='clamp')
Mc=mom_at(L/2,L/2)[0]
Me=mom_at(0,L/2)[0]
print("VALIDACIÓN placa empotrada cuadrada (malla 24x24):")
print("  M_centro FEM=%.4f  Timoshenko=%.4f  err=%.1f%%"%(Mc,0.0231*q*L**2,abs(Mc-0.0231*q*L**2)/(0.0231*q*L**2)*100))
print("  M_borde  FEM=%.4f  Timoshenko=%.4f  err=%.1f%%"%(Me,-0.0513*q*L**2,abs(Me+0.0513*q*L**2)/(0.0513*q*L**2)*100))

# ================= CUBIERTA DEL DEPÓSITO: placa 2D empotrada (unión rígida) =================
# Panel del compartimento grande: luz corta (entre caras muros) x luz larga
Lx=11.37-0.50   # 10.87 m (corta, transversal)
Ly=18.0         # larga
t=0.70; nu=0.2
# cargas ULS (por m2): permanente + UDL LM1 ; tándem como patch central
gperm=t*25.0+1.5            # 19.0 (canto 0.70) -> 0.70*25+1.5=19.0
q_uls_unif=1.35*gperm+1.5*9.0
# tándem 600 kN ULS=900; patch central ~2.3(long)x3.1(transv) -> ajusto a malla
pbox=(Lx/2-1.55, Lx/2+1.55, Ly/2-1.15, Ly/2+1.15)  # ~3.1 x 2.3 m
patch={'box':pbox,'q':1.5*600.0/(3.1*2.3)}
U,recs,D,mom_at=solve_plate(Lx,Ly,28,40,t,E,nu,q_uls_unif,patch=patch,bc='clamp')
mc=mom_at(Lx/2,Ly/2)       # centro (vano, + tracción inferior)
mex=mom_at(0,Ly/2)         # borde muro largo (apoyo, - tracción superior) -> mx
mey=mom_at(Lx/2,0)         # borde testero
# máximos globales en el campo
mx_all=[r[2] for r in recs]; my_all=[r[3] for r in recs]
res=dict(
  panel=f"{Lx:.2f} x {Ly:.2f} m (empotrada 4 bordes)",
  q_uls_unif=round(q_uls_unif,1), patch_q=round(patch['q'],1),
  M_vano_centro_mx=round(mc[0],1), M_vano_centro_my=round(mc[1],1),
  M_apoyo_muro_largo_mx=round(mex[0],1), M_apoyo_testero_my=round(mey[1],1),
  Mx_max_campo=round(max(mx_all),1), Mx_min_campo=round(min(mx_all),1),
  My_max_campo=round(max(my_all),1), My_min_campo=round(min(my_all),1))
print("\nCUBIERTA (placa 2D empotrada):")
print(json.dumps(res,indent=2,ensure_ascii=False))
import pickle
pickle.dump({'recs':recs,'Lx':Lx,'Ly':Ly,'res':res},open('/tmp/plate_roof.pkl','wb'))
