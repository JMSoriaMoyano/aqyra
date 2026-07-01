#!/usr/bin/env python3
"""QA Estructurando 2.0 - Capa NORMATIVA independiente (numpy puro).
Recalcula desde cero las comprobaciones EC de los 6 casos golden, con formulas
derivadas (no copiadas del build). Oraculos:
 - DEC-A1 CLT/nervio: M=wL2/8, d=5wL4/384EI, f1=(pi/2)sqrt(EI/mL4) + EC5
 - DEC-B1/B2/B4 acero: EC3 6.3.1 pandeo curva b (chi), N_b,Rd; con L reales del FEM 2D
 - DEC-E1 encepado: EC2 6.5 bielas-tirantes T=R/tan(theta)
 - DEC-E2 pilote: EC7 R=R_punta+R_fuste
"""
import numpy as np
fy=355e6; gM0=1.05; gM1=1.05; Ea=210e9
eps=np.sqrt(235/355)
def shs(name):
    p=name.replace('SHS','').strip().replace('×','x'); b,t=p.split('x')
    b=float(b)/1000.; t=float(t)/1000.
    A=b*b-(b-2*t)**2; I=(b**4-(b-2*t)**4)/12.0; Wpl=(b**3-(b-2*t)**3)/6.0
    i=np.sqrt(I/A); return dict(b=b,t=t,A=A,I=I,Wpl=Wpl,i=i)
def chi_b(lam_bar,alpha=0.34):
    phi=0.5*(1+alpha*(lam_bar-0.2)+lam_bar**2)
    return 1/(phi+np.sqrt(phi**2-lam_bar**2))
def Nb_Rd(name,Lcr):
    s=shs(name); lam1=93.9*eps
    lam_bar=(Lcr/s['i'])/lam1
    chi=chi_b(lam_bar)
    Nb=chi*s['A']*fy/gM1
    return dict(A=s['A'],i=s['i'],lam_bar=lam_bar,chi=chi,Nb=Nb,Nc=s['A']*fy/gM0)

print("="*70)
print("DEC-B1 Diagonal SHS 200x10 (pandeo EC3 6.3.1)")
r=Nb_Rd('SHS 200x10',4.3)   # L diagonal build 4.3 m
print(f"  A={r['A']*1e4:.1f} cm2 i={r['i']*100:.2f} cm lam_bar={r['lam_bar']:.3f} chi={r['chi']:.3f}")
print(f"  N_b,Rd={r['Nb']/1e3:.0f} kN  (build 2004)  | N_Ed build=778, QA FEM 2D~348")
print(f"  u_build=778/{r['Nb']/1e3:.0f}={778/(r['Nb']/1e3):.2f}  | u_QA(FEM N=348)={348/(r['Nb']/1e3):.2f}")

print("="*70)
print("DEC-B2 Cordon SHS 180x8 (pandeo+axil)")
r=Nb_Rd('SHS 180x8',3.0)
print(f"  A={r['A']*1e4:.1f} cm2 i={r['i']*100:.2f} cm lam_bar={r['lam_bar']:.3f} chi={r['chi']:.3f}")
print(f"  N_c,Rd={r['Nc']/1e3:.0f} kN  N_b,Rd={r['Nb']/1e3:.0f} kN (build 1600) | N_Ed build=409, QA~330")
print(f"  u_build=409/{r['Nb']/1e3:.0f}={409/(r['Nb']/1e3):.2f} | u_QA(330)={330/(r['Nb']/1e3):.2f}")

print("="*70)
print("DEC-B4 Montante SHS 120x6 (CRITICO arriostramiento)")
for Lcr,lbl in [(3.08,'arriostrado L=3.08'),(9.25,'NO arriostrado L=9.25')]:
    r=Nb_Rd('SHS 120x6',Lcr)
    NEd_build=250; NEd_qa=392
    print(f"  [{lbl}] lam_bar={r['lam_bar']:.2f} chi={r['chi']:.3f} N_b,Rd={r['Nb']/1e3:.0f} kN")
    print(f"      u(build N=250)={NEd_build/(r['Nb']/1e3):.2f} | u(QA FEM N=392)={NEd_qa/(r['Nb']/1e3):.2f}")

print("="*70)
print("DEC-A1 Costilla IPE160 nervio biapoyado + vibracion")
# IPE160 catalogo
A=20.09e-4; Iy=869.3e-8; Wply=123.9e-6
fyd=fy/gM0; McRd=Wply*fyd
L=3.86; wd=8.80e3; wk=6.23e3
M=wd*L**2/8; delta=5*wk*L**4/(384*Ea*Iy)
print(f"  M_Ed={M/1e3:.1f} kNm  M_c,Rd={McRd/1e3:.1f} kNm  u_M={M/McRd:.2f} (build 0.39)")
print(f"  delta={delta*1000:.2f} mm  L/300={L/0.3:.1f}mm  u={delta/(L/300):.2f} (build 2.6mm)")
# vibracion: f1=(pi/2)sqrt(EI/(m L^4)), m masa lineal cuasiperm
m=4.41e3/9.81   # kg/m (g+psi2 q sobre 1.3 ancho) build usa 346 kg/m
f1=(np.pi/2)*np.sqrt(Ea*Iy/(m*L**4))
print(f"  m={m:.0f} kg/m  f1={f1:.2f} Hz (build 8.5 Hz, criterio >=8)")

print("="*70)
print("DEC-E1 Encepado bielas-tirantes EC2 6.5")
for lbl,N,npar,a_half,h,Dp in [('NC-Lab(4D450)',4400e3,2,0.75,1.2,0.45),('NC-Vest(6D650)',8300e3,3,0.8,1.5,0.65)]:
    d=h-0.05-0.02; z=0.9*d
    theta=np.arctan(z/a_half)
    R=(N/npar)/2
    T=R/np.tan(theta); C=R/np.sin(theta)
    As=T/(500e6/1.15)
    print(f"  {lbl}: R_par={N/npar/1e3:.0f} R_pil={R/1e3:.0f} theta={np.degrees(theta):.1f} T={T/1e3:.0f} kN As={As*1e4:.1f} cm2")
print("  build: NC-Lab T=809, NC-Vest T=864")

print("="*70)
print("DEC-E2 Pilote D650 EC7")
for D,lbl,qp,fUG2,fUG3 in [(0.65,'D650',3.88e6,62e3,98e3),(0.45,'D450',3.88e6,62e3,98e3)]:
    Ap=np.pi*D**2/4; per=np.pi*D
    Rp=qp*Ap; Rf=fUG2*per*4+fUG3*per*3
    Radm=Rp+Rf
    print(f"  {lbl}: A_punta={Ap:.3f} R_punta={Rp/1e3:.0f} R_fuste={Rf/1e3:.0f} R_adm={Radm/1e3:.0f} kN")
print("  build: D650 R_adm~2396 (con promedio de zona, punta reducida a 1290); D450 R_adm~1380")
# con punta reducida promedio de zona (build usa 1290 para D650)
for D,lbl,Rp_red,fUG2,fUG3 in [(0.65,'D650',1290e3,62e3,98e3),(0.45,'D450',615e3,62e3,98e3)]:
    per=np.pi*D; Rf=fUG2*per*4+fUG3*per*3; Radm=Rp_red+Rf
    print(f"  {lbl} (punta promedio zona {Rp_red/1e3:.0f}): R_fuste={Rf/1e3:.0f} R_adm={Radm/1e3:.0f} kN")
print("  N_serv D650=988 -> u=988/Radm ; D450=786")
