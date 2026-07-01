import sys; sys.path.insert(0,"/tmp/pylibs")
import numpy as np, json
# ACM con bordes apoyados (w=0) + MUELLE ROTACIONAL = rigidez real del muro
def acm_parts(a,b,D,nu):
    Db=D*np.array([[1,nu,0],[nu,1,0],[0,0,(1-nu)/2]]); gp=[-1/np.sqrt(3),1/np.sqrt(3)]
    def Bmat(xi,eta):
        x=xi*a;y=eta*b
        txx=[0,0,0,2,0,0,6*x,2*y,0,0,6*x*y,0]; tyy=[0,0,0,0,0,2,0,0,2*x,6*y,0,6*x*y]
        txy=[0,0,0,0,1,0,0,2*x,2*y,0,3*x*x,3*y*y]
        return np.array([txx,tyy,[2*t for t in txy]])
    nodes=[(-a,-b),(a,-b),(a,b),(-a,b)]; C=np.zeros((12,12))
    rw=lambda x,y:[1,x,y,x*x,x*y,y*y,x**3,x*x*y,x*y*y,y**3,x**3*y,x*y**3]
    rtx=lambda x,y:[0,0,1,0,x,2*y,0,x*x,2*x*y,3*y*y,x**3,3*x*y*y]
    rty=lambda x,y:[-v for v in [0,1,0,2*x,y,0,3*x*x,2*x*y,y*y,0,3*x*x*y,y**3]]
    for i,(x,y) in enumerate(nodes): C[3*i]=rw(x,y);C[3*i+1]=rtx(x,y);C[3*i+2]=rty(x,y)
    Ci=np.linalg.inv(C); K=np.zeros((12,12))
    for xi in gp:
        for eta in gp:
            B=Bmat(xi,eta)@Ci; K+=(B.T@Db@B)*(a*b)
    return K,Ci,Bmat,Db
def solve(Lx,Ly,nx,ny,t,E,nu,q,patch,krot):
    D=E*t**3/(12*(1-nu**2)); a=Lx/nx/2;b=Ly/ny/2
    Ke,Ci,Bmat,Db=acm_parts(a,b,D,nu); nnx=nx+1;nny=ny+1;nn=nnx*nny;ndof=3*nn
    nid=lambda i,j:j*nnx+i; K=np.zeros((ndof,ndof));F=np.zeros(ndof);elems=[]
    for j in range(ny):
        for i in range(nx):
            n=[nid(i,j),nid(i+1,j),nid(i+1,j+1),nid(i,j+1)];dof=[]
            for nn_ in n: dof+=[3*nn_,3*nn_+1,3*nn_+2]
            for r in range(12):
                for cc in range(12): K[dof[r],dof[cc]]+=Ke[r,cc]
            elems.append((i,j,n,dof))
            qe=q; x0=i*Lx/nx;x1=(i+1)*Lx/nx;y0=j*Ly/ny;y1=(j+1)*Ly/ny
            if patch:
                ox=max(0,min(x1,patch['box'][1])-max(x0,patch['box'][0]))
                oy=max(0,min(y1,patch['box'][3])-max(y0,patch['box'][2]))
                if ox>0 and oy>0: qe+=patch['q']*ox*oy/((x1-x0)*(y1-y0))
            Ae=(Lx/nx)*(Ly/ny)
            for nn_ in n: F[3*nn_]+=-qe*Ae/4
    # BC: w=0 en bordes; muelle rotacional en rotación normal al borde
    le_x=Lx/nx; le_y=Ly/ny
    fixed=set()
    for j in range(nny):
        for i in range(nnx):
            edge=(i==0 or i==nx or j==0 or j==ny); nn_=nid(i,j)
            if edge:
                fixed.add(3*nn_)  # w=0
                if i==0 or i==nx:   # borde muro largo: rot theta_y=-dw/dx -> dof+2
                    K[3*nn_+2,3*nn_+2]+=krot*le_y*(0.5 if (j==0 or j==ny) else 1.0)
                    K[3*nn_+1,3*nn_+1]+=1e12  # libre tangencial? fijar theta tang. para estabilidad
                if j==0 or j==ny:
                    K[3*nn_+1,3*nn_+1]+=krot*le_x*(0.5 if (i==0 or i==nx) else 1.0)
                    if not(i==0 or i==nx): K[3*nn_+2,3*nn_+2]+=1e12
    free=[d for d in range(ndof) if d not in fixed]; U=np.zeros(ndof)
    U[free]=np.linalg.solve(K[np.ix_(free,free)],F[free])
    msum=np.zeros((nn,3));mc=np.zeros(nn);corners=[(-1,-1),(1,-1),(1,1),(-1,1)]
    for (i,j,n,dof) in elems:
        ue=U[dof]
        for k,(xi,eta) in enumerate(corners):
            m=Db@(Bmat(xi,eta)@Ci@ue); msum[n[k]]+=m; mc[n[k]]+=1
    mnod=msum/np.maximum(mc,1)[:,None]
    def mom(x,y):
        i=min(max(int(round(x/(Lx/nx))),0),nx); j=min(max(int(round(y/(Ly/ny))),0),ny)
        return mnod[nid(i,j)]
    return mom
E=32837e3;nu=0.2; Lx=10.87;Ly=18.0;t=0.70
q=1.35*(t*25+1.5)+1.5*9.0
patch={'box':(Lx/2-1.55,Lx/2+1.55,Ly/2-1.15,Ly/2+1.15),'q':1.5*600/(3.1*2.3)}
EIw=E*0.5**3/12; Hw=4.95
print("Momentos cubierta (placa 2D + muelle rotacional = rigidez muro):")
for beta in [2,4,6]:
    krot=beta*EIw/Hw
    mom=solve(Lx,Ly,28,40,t,E,nu,q,patch,krot)
    mc=mom(Lx/2,Ly/2); me=mom(0,Ly/2)
    print(f"  k={beta}EI/H: vano mx=+{mc[0]:.0f}  my=+{mc[1]:.0f} | apoyo mx={me[0]:.0f}")

# --- momento de servicio (combinación característica) para fisuración del vano ---
qc=(t*25+1.5)+9.0
patchc={'box':patch['box'],'q':600/(3.1*2.3)}
mom_c=solve(Lx,Ly,28,40,t,E,nu,qc,patchc,4*EIw/Hw)
Mserv=mom_c(Lx/2,Ly/2)[0]
print("\nM_servicio vano (caract.) mx=+%.0f"%Mserv)
# diseño/fisura bottom
fctm=2.896;Es=200e6;ae=Es/32837e3;fyd=434.8e3
def wk(M,h,d,As,c=0.045,phi=0.020):
    A=As*1e-4;rho=A/d;kk=ae*rho;x=(-kk+np.sqrt(kk**2+2*kk))*d;z=d-x/3
    sig=abs(M)/(A*z);hc=min(2.5*(h-d),(h-x)/3,h/2);re=A/hc
    sr=3.4*c+0.8*0.5*0.425*phi/re;eps=max((sig-0.4*(fctm*1e3)/re*(1+ae*re))/Es,0.6*sig/Es)
    return sr*eps*1000,sig/1e3
def MRd(As,d):return As*1e-4*fyd*0.9*d
d_r=0.643
for arm,phi,s in [("phi20/150",20,150),("phi20/125",20,125),("phi25/150",25,150)]:
    As=np.pi*(phi/2)**2/100*(1000/s)
    w,_=wk(Mserv,0.70,d_r,As,phi=phi/1000)
    print("  vano inf %s = %.1f cm2/m | MRd=%.0f util_ULS(440)=%.2f | wk=%.3f"%(arm,As,MRd(As,d_r),440/MRd(As,d_r),w))
