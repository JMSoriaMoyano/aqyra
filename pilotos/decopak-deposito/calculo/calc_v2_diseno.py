import sys; sys.path.insert(0,"/tmp/pylibs")
import numpy as np, json
fck=30; fcd=20e3; fctm=2.896; Ecm=32837e3; Es=200e6; ae=Es/Ecm; fyd=434.8e3
def MRd(As,d): return As*1e-4*fyd*0.9*d            # kN·m/m (As cm2/m)
def wk(M,h,d,As,c=0.045,phi=0.020):
    A=As*1e-4; rho=A/d; kk=ae*rho; x=(-kk+np.sqrt(kk**2+2*kk))*d; z=d-x/3
    sig=abs(M)/(A*z); hc=min(2.5*(h-d),(h-x)/3,h/2); re=A/hc
    sr=3.4*c+0.8*0.5*0.425*phi/re
    eps=max((sig-0.4*(fctm*1e3)/re*(1+ae*re))/Es,0.6*sig/Es)
    return sr*eps*1000, sig/1e3
def Asbar(phi_mm,s_mm): return np.pi*(phi_mm/2)**2/100*(1000/s_mm)  # cm2/m

elems=[]
# (nombre, M_Ed kN·m/m, h, d, phi, s, fisura?, M_serv)
defs=[
 ("Cubierta · vano (inferior) — dir corta",308,0.70,0.643,20,175,True,210),
 ("Cubierta · vano (inferior) — dir larga",182,0.70,0.623,16,200,False,None),
 ("Cubierta · apoyo sobre muros (superior)",352,0.70,0.643,25,200,False,None),
 ("Muro · cabeza/esquina (cara exterior)",352,0.50,0.445,25,200,True,128),
 ("Muro · base (empotramiento en solera)",92,0.50,0.445,20,200,False,None),
 ("Muro · paramento (agua/tierras, vano)",95,0.50,0.445,20,200,True,70),
 ("Solera (raft) · vano y esquina",133,0.60,0.545,20,175,True,133),
]
rows=[]
for (nm,M,h,d,phi,s,fis,Ms) in defs:
    As=Asbar(phi,s); mr=MRd(As,d); util=abs(M)/mr
    w=("-",)
    if fis and Ms: 
        ww,sg=wk(Ms,h,d,As); w=(round(ww,3),round(sg,0))
    rows.append(dict(elem=nm,M_Ed=M,armado=f"phi{phi}/{s} ({As:.1f} cm2/m)",
       MRd=round(mr,0),util=round(util,2),wk=(w[0] if fis else "-")))
# punzonamiento (sin cambio)
print(json.dumps(rows,indent=2,ensure_ascii=False))
json.dump(rows,open('/tmp/diseno_v2.json','w'),indent=2,ensure_ascii=False)
print("\nMax util =",max(r['util'] for r in rows))
