#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cálculo del depósito enterrado de Decopak (Rubí). PROPUESTA pendiente de QA + firma JM.
Eurocódigos + AN España + EN 1992-3 (depósitos). numpy puro.
Unidades: kN, m, kPa(=kN/m2), MPa(=MN/m2). Momentos kN·m/m (por metro de ancho).
"""
import numpy as np, json

R = {}  # resultados

# ============================================================ MATERIALES
fck=30.0; gC=1.5; fcd=fck/gC                       # 20.0 MPa
fcm=fck+8; fctm=0.30*fck**(2/3); fctk05=0.7*fctm
Ecm=22000*(fcm/10)**0.3                            # MPa
fyk=500.0; gS=1.15; fyd=fyk/gS; Es=200000.0
alphae=Es/Ecm
R['materiales']=dict(fck=fck,fcd=round(fcd,2),fctm=round(fctm,3),fctk05=round(fctk05,3),
                     Ecm=round(Ecm,0),fyd=round(fyd,1),alphae=round(alphae,2))

# ============================================================ GEOMETRÍA (del IFC)
H   = 4.35     # altura muro / calado max agua
Ht  = 4.95     # altura tierras retenidas (147.00 -> rasante 151.95)
LT  = 11.37    # luz transversal c/c muros largos (losa cubierta)
tw  = 0.50     # muros 50 cm
tf  = 0.60     # losa fondo
tr60= 0.60; tr70=0.70   # losas cubierta
A_raft=302.78
A_base_grande=18.0*10.0  # compartimento grande lleno

# ============================================================ ACCIONES (caract.)
g_h2o=10.0     # kN/m3 (brief)
g_w  =25.0     # hormigón
g_s  =20.0     # terreno
phi=30.0; K0=1-np.sin(np.radians(phi)); Ka=np.tan(np.radians(45-phi/2))**2
q_sob=20.0     # sobrecarga trasdós (tráfico pesado adyacente) -> conservador
R['acciones']=dict(K0=round(K0,3),Ka=round(Ka,3),phi=phi,q_sobrecarga=q_sob,
                   gamma_agua=g_h2o,gamma_terreno=g_s)

# ============================================================ BEAM FE (Euler-Bernoulli)
def beam_fe(L,EI,n,w_func,bc):
    """ viga 1D, n elementos. w_func(x)->kN/m (transversal). bc: dict node->(w?,th?) fijar 0.
        devuelve x, M(x) [kN·m], V(x), reacciones."""
    ndof=2*(n+1); K=np.zeros((ndof,ndof)); F=np.zeros(ndof)
    le=L/n
    ke=EI/le**3*np.array([[12,6*le,-12,6*le],
                          [6*le,4*le**2,-6*le,2*le**2],
                          [-12,-6*le,12,-6*le],
                          [6*le,2*le**2,-6*le,4*le**2]])
    for e in range(n):
        x0=e*le; xc=x0+le/2; w=w_func(xc)   # carga uniforme por elemento (valor en centro)
        fe=w*le*np.array([1/2, le/12, 1/2, -le/12])
        dofs=[2*e,2*e+1,2*e+2,2*e+3]
        for i in range(4):
            F[dofs[i]]+=fe[i]
            for j in range(4): K[dofs[i],dofs[j]]+=ke[i,j]
    fixed=[]
    for node,(fw,fth) in bc.items():
        if fw: fixed.append(2*node)
        if fth: fixed.append(2*node+1)
    free=[d for d in range(ndof) if d not in fixed]
    U=np.zeros(ndof)
    U[free]=np.linalg.solve(K[np.ix_(free,free)],F[free])
    Rr=K@U-F
    # momentos por elemento en nodos
    xs=[]; Ms=[]; Vs=[]
    for e in range(n):
        x0=e*le; ue=U[[2*e,2*e+1,2*e+2,2*e+3]]
        # M = EI*d2w; usar funciones de forma en extremos
        for xi in (0.0,1.0):
            B=np.array([(12*xi-6)/le**2,(6*xi-4)/le,(-12*xi+6)/le**2,(6*xi-2)/le])  # d2N
            M=EI*B@ue
            xs.append(x0+xi*le); Ms.append(M)
    react={n_:Rr[2*n_] for n_ in bc}
    return np.array(xs),np.array(Ms),react

# ============================================================ EC2 DESIGN HELPERS
def As_flexion(Med, d, b=1.0):
    """ As (cm2/m) por flexión simple rectangular. Med kN·m, d m, b m."""
    Med=abs(Med)*1e-3  # MN·m
    mu=Med/(b*d**2*fcd)
    if mu>0.295: mu=0.295
    z=d*(0.5+np.sqrt(0.25-mu/1.0)) if mu<0.295 else 0.85*d
    z=min(z,0.95*d)
    As=Med/(z*fyd)      # m2
    return As*1e4, z    # cm2/m, z(m)

def As_min_fis(h,d,b=1.0,k=0.65,kc=0.4,fct=None,sigs=400.0):
    """ As,min control de fisuración EN1992 7.3.2 (tracción por flexión). cm2/m """
    fct=fct or fctm
    Act=b*h/2.0
    Asmin=kc*k*fct*Act/sigs   # m2 (sigs en MPa, fct en MPa, Act m2 -> MN/ (MPa)=m2*?)
    # kc*k*fct[MN/m2]*Act[m2]/sigs[MN/m2] = m2
    return Asmin*1e4

def VRdc(d,As,b=1.0):
    """ cortante sin armadura EC2 6.2.2, kN """
    d_mm=d*1000
    k=min(1+np.sqrt(200/d_mm),2.0)
    rho=min(As*1e-4/(b*d),0.02)
    vmin=0.035*k**1.5*np.sqrt(fck)
    vRd=max(0.18/gC*k*(100*rho*fck)**(1/3),vmin)  # MPa
    return vRd*b*d*1e3  # kN

def crack_w(M_sls,h,d,As_cm2,c,phi_bar,b=1.0,kt=0.4):
    """ ancho de fisura EN1992 7.3.4. M_sls kN·m/m. devuelve wk(mm), sigma_s(MPa)."""
    As=As_cm2*1e-4
    rho=As/(b*d)
    # eje neutro fisurado
    kk=alphae*rho
    xi=(-kk+np.sqrt(kk**2+2*kk))  # x/d
    x=xi*d
    z=d-x/3
    sigs=abs(M_sls)*1e-3/(As*z)   # MPa
    hc_eff=min(2.5*(h-d),(h-x)/3,h/2)
    Aceff=b*hc_eff
    rho_eff=As/Aceff
    sr=3.4*c+0.8*0.5*0.425*(phi_bar*1e-3)/rho_eff   # m
    eps=(sigs-kt*(fctm/rho_eff)*(1+alphae*rho_eff))/Es
    eps=max(eps,0.6*sigs/Es)
    wk=sr*eps*1000  # mm
    return wk, sigs, x

def bars(area_target_cm2, phi_mm, smax=200):
    """ separación necesaria para un diámetro; devuelve (s_mm, As_prov_cm2)."""
    a1=np.pi*(phi_mm/2)**2/100  # cm2
    s=int(a1/area_target_cm2*1000)  # mm para 1 m
    s=min(s,smax); s=(s//25)*25
    if s<75: s=75
    Asp=a1*1000/s
    return s,Asp

# ============================================================ 1) MURO PERIMETRAL LARGO 50cm
EI_w=Ecm*1e3*1.0*tw**3/12  # kN·m2/m  (E MPa->kN/m2 *1e3)
n=30
# Caso A: tanque vacío + tierras + sobrecarga (empuje INWARD). presión z desde base.
def p_earth(z):  # z desde base (0) a H(top wall). prof bajo rasante = (Ht - z)
    prof=Ht-z
    return K0*g_s*prof + K0*q_sob
def p_water(z):  # agua llena, triangular: 0 en top, max en base
    return g_h2o*(H-z)
xs,MsA,reA=beam_fe(H,EI_w,n,p_earth,{0:(1,1),n:(1,0)})   # base empotrada, top apoyado
xs,MsB,reB=beam_fe(H,EI_w,n,p_water,{0:(1,1),n:(1,0)})
M_base_E=MsA[0]; M_span_E=np.max(np.abs(MsA[1:-3]))
M_base_W=MsB[0]; M_span_W=np.max(np.abs(MsB[1:-3]))
# envolvente diseño (valor absoluto en base y vano)
Mb_uls=1.35*abs(M_base_E)  # tierras permanente desfav (GEO)
Mw_uls=1.5*abs(M_base_W)   # agua variable
# diseño base (cara): mayor de ambos
d_w=tw-0.045-0.010
Mb_design=max(Mb_uls,Mw_uls)
As_b,_=As_flexion(Mb_design,d_w)
Asmin_w=As_min_fis(tw,d_w)
As_b=max(As_b,Asmin_w)
sb,Asb_prov=bars(As_b,20)
V_b=max(abs(reA[0]),abs(reB[0]))*1.5
VR=VRdc(d_w,Asb_prov)
# SLS fisura cara agua (caract, agua llena): M_base_W (1.0)
wk_w,sig_w,_=crack_w(abs(M_base_W),tw,d_w,Asb_prov,0.045,20)
R['muro_perimetral_50']=dict(
  EI=round(EI_w,0),d=round(d_w,3),
  M_base_tierras=round(M_base_E,1),M_vano_tierras=round(M_span_E,1),
  M_base_agua=round(M_base_W,1),M_vano_agua=round(M_span_W,1),
  M_diseno_ULS=round(Mb_design,1),As_req=round(As_b,2),Asmin=round(Asmin_w,2),
  armado=f"phi20/{sb}",As_prov=round(Asb_prov,2),
  V_ULS=round(V_b,1),VRdc=round(VR,1),util_cortante=round(V_b/VR,2),
  wk_cara_agua=round(wk_w,3),sigma_s=round(sig_w,1),lim_wk=0.20,
  util_flexion=round(Mb_design/(Asb_prov*1e-4*fyd*0.9*d_w*1e3),2))

# ============================================================ 2) MURO INTERIOR 50cm (agua diferencial)
def p_dif(z): return g_h2o*(H-z)
xs,MsI,reI=beam_fe(H,EI_w,n,p_dif,{0:(1,1),n:(1,0)})
M_base_I=MsI[0]; Mi_uls=1.5*abs(M_base_I)
As_i,_=As_flexion(Mi_uls,d_w); As_i=max(As_i,Asmin_w)
si,Asi=bars(As_i,20)
wk_i,sig_i,_=crack_w(abs(M_base_I),tw,d_w,Asi,0.045,20)
R['muro_interior_50']=dict(M_base=round(M_base_I,1),M_ULS=round(Mi_uls,1),
  As_req=round(As_i,2),armado=f"phi20/{si}",As_prov=round(Asi,2),
  wk=round(wk_i,3),util_flexion=round(Mi_uls/(Asi*1e-4*fyd*0.9*d_w*1e3),2))

# ============================================================ 3) LOSA CUBIERTA unidireccional 11.37 m, IAP-11 LM1
# cargas permanentes
g_self=tr70*g_w           # 17.5 (banda 70)
g_fin=1.5                 # impermeab/acabados
g_perm=g_self+g_fin
# LM1 carril 1: UDL 9 kN/m2; tándem 2 ejes 300 kN (alpha=1, AN España)
q_udl=9.0
Q_axle=300.0; Q_tandem=2*Q_axle  # 600 kN
# dispersión rueda 0.40 a través de 0.70 -> 1.10 m; b_eff (losa unidir, carga central) = patch+L/2
patch=0.40+tr70
beff_wheel=patch+LT/2
beff_tandem=min(2.0+beff_wheel, 10.0)   # 2 ruedas a 2.0 m, limitado por ancho
q_tandem_line=Q_tandem/beff_tandem      # kN por metro de ancho, concentrado long.
# momentos (simplemente apoyada, conservador para vano)
M_perm=g_perm*LT**2/8
M_udl =q_udl*LT**2/8
M_tand=q_tandem_line*LT/4
M_sls=M_perm+M_udl+M_tand
M_uls=1.35*M_perm+1.5*(M_udl+M_tand)
d_r=tr70-0.045-0.012
# capacidad con armado pesado phi25/100 (doble capa) como tentativa
As_try,_=As_flexion(M_uls,d_r);
sr,Asr=bars(As_try,25,smax=100)
MRd=Asr*1e-4*fyd*0.9*d_r*1e3
# punzonamiento rueda 150 kN, losa 70
def punz(P,d,u1_mult=1.0):
    P=P*1.5  # ULS
    d_mm=d*1000; k=min(1+np.sqrt(200/d_mm),2.0)
    rho=0.01
    vRdc=max(0.18/gC*k*(100*rho*fck)**(1/3),0.035*k**1.5*np.sqrt(fck))
    # perímetro de control a 2d de patch 0.40x0.40
    a=0.40
    u1=4*a+2*np.pi*2*d
    vEd=P/(u1*d)*1e-3  # MPa
    return vEd,vRdc,u1
vEd,vRdc_p,u1=punz(150.0,d_r)
R['losa_cubierta_70']=dict(L=LT,g_perm=round(g_perm,1),
  beff_tandem=round(beff_tandem,2),q_tandem_line=round(q_tandem_line,1),
  M_perm=round(M_perm,1),M_udl=round(M_udl,1),M_tandem=round(M_tand,1),
  M_ULS=round(M_uls,1),M_SLS=round(M_sls,1),d=round(d_r,3),
  armado_tentativo=f"phi25/{sr} (2 capas posible)",As_prov=round(Asr,2),MRd=round(MRd,1),
  util_flexion=round(M_uls/MRd,2),
  punz_vEd=round(vEd,3),punz_vRdc=round(vRdc_p,3),util_punz=round(vEd/vRdc_p,2),
  M_solo_permanente_ULS=round(1.35*M_perm,1),
  util_solo_permanente=round(1.35*M_perm/MRd,2))

# ============================================================ 4) LOSA DE FONDO (raft) — viga sobre lecho elástico (Winkler)
W_losa_fondo=A_raft*tf*g_w
W_agua=A_base_grande*g_h2o*H
L_muros=2*21.5+2*10.0+10.4
W_muros=L_muros*tw*H*g_w
W_cub=(193.78*tr60+39.65*tr70)*g_w
W_tot=W_losa_fondo+W_agua+W_muros+W_cub
q_terreno=W_tot/A_raft
# Apoyo en UG3 arenisca (roca blanda, PL>80 kg/cm2): q_adm alta y subgrade muy rígido
q_adm_UG3=800.0          # kPa, conservador para arenisca
ks=80000.0               # kN/m3 módulo de balasto (roca blanda, rígido)
# Franja transversal de 1 m sobre lecho elástico:
Lraft=13.84              # ancho real del raft (bbox transversal)
xw1=(Lraft-LT)/2; xw2=xw1+LT    # posición de los dos muros largos
def boef_raft(n=120):
    EIf=Ecm*1e3*1.0*tf**3/12
    le=Lraft/n; ndof=2*(n+1)
    K=np.zeros((ndof,ndof)); F=np.zeros(ndof)
    ke=EIf/le**3*np.array([[12,6*le,-12,6*le],[6*le,4*le**2,-6*le,2*le**2],
                           [-12,-6*le,12,-6*le],[6*le,2*le**2,-6*le,4*le**2]])
    # rigidez de muelle (Winkler) repartida (matriz de masa consistente *ks)
    kg=ks*le/420*np.array([[156,22*le,54,-13*le],[22*le,4*le**2,13*le,-3*le**2],
                           [54,13*le,156,-22*le],[-13*le,-3*le**2,-22*le,4*le**2]])
    for e in range(n):
        dofs=[2*e,2*e+1,2*e+2,2*e+3]
        x0=e*le; xc=x0+le/2
        # carga hacia abajo: peso losa (15) + agua si dentro del vaso (entre muros)
        w=tf*g_w
        if xw1<=xc<=xw2: w+=g_h2o*H        # columna de agua compartimento lleno
        fe=w*le*np.array([1/2,le/12,1/2,-le/12])
        for i in range(4):
            F[dofs[i]]+=fe[i]
            for j in range(4):
                K[dofs[i],dofs[j]]+=ke[i,j]+kg[i,j]
    # cargas de muro (línea) en nodos más próximos a xw1,xw2: peso muro + reacción cubierta
    Pwall=tw*H*g_w + (g_perm*LT/2 + (q_udl+q_tandem_line)*LT/4)  # kN/m (perm + variable simplif.)
    for xw in (xw1,xw2):
        nod=int(round(xw/le)); F[2*nod]+=Pwall
    U=np.linalg.solve(K,F)
    # momentos
    Ms=[]; xs=[]
    for e in range(n):
        ue=U[[2*e,2*e+1,2*e+2,2*e+3]]
        for xi in (0.0,1.0):
            B=np.array([(12*xi-6)/le**2,(6*xi-4)/le,(-12*xi+6)/le**2,(6*xi-2)/le])
            xs.append(e*le+xi*le); Ms.append(EIf*B@ue)
    return np.array(xs),np.array(Ms),Pwall,U
xs_r,Ms_r,Pwall,Ur=boef_raft()
M_raft=np.max(np.abs(Ms_r))
M_raft_uls=1.35*M_raft
d_f=tf-0.045-0.010
As_f,_=As_flexion(M_raft_uls,d_f); Asmin_f=As_min_fis(tf,d_f); As_f=max(As_f,Asmin_f)
sf,Asf=bars(As_f,20)
wk_f,sig_f,_=crack_w(M_raft,tf,d_f,Asf,0.045,20)
R['losa_fondo']=dict(modelo="viga sobre lecho elástico (Winkler), ks=80000 kN/m3 (UG3 arenisca)",
  W_total=round(W_tot,0),q_terreno_medio=round(q_terreno,1),
  q_adm_UG3=q_adm_UG3,util_portante=round(q_terreno/q_adm_UG3,2),
  P_muro_linea=round(Pwall,1),M_raft=round(M_raft,1),M_ULS=round(M_raft_uls,1),d=round(d_f,3),
  As_req=round(As_f,2),Asmin=round(Asmin_f,2),armado=f"phi20/{sf}",As_prov=round(Asf,2),
  wk=round(wk_f,3),util_flexion=round(M_raft_uls/(Asf*1e-4*fyd*0.9*d_f*1e3),2))

# ============================================================ 5) FLOTACION (vaso vacio, freatico documentado +144.6)
z_base=146.40; z_wt=144.60
h_sub=max(0.0, z_wt - z_base)
U=g_h2o*A_raft*h_sub
W_estab=0.9*(W_losa_fondo+W_muros+W_cub)
FS=W_estab/U if U>0 else float('inf')
h_sub_cons=151.95-z_base
U_cons=g_h2o*A_raft*h_sub_cons
FS_cons=W_estab/U_cons
R['flotacion']=dict(freatico_documentado=z_wt,base=z_base,h_sumergida=round(h_sub,2),
  U_documentado=round(U,0),W_estab_09G=round(W_estab,0),
  FS_documentado=("inf (sin subpresion)" if U==0 else round(FS,2)),
  caso_conservador_rasante=dict(h_sub=round(h_sub_cons,2),U=round(U_cons,0),FS=round(FS_cons,2)),
  nota="Con freatico documentado la base queda sobre el agua -> flotacion NO critica.")

# ============================================================ VERIFICACION (oraculo analitico)
p0=g_h2o*H
M_emp_teor=p0*H**2/15
R_top_teor=p0*H/10
R['verificacion']=dict(
  caso="muro agua triangular, mensula apuntalada (fixed-pinned)",
  M_base_FE=round(abs(M_base_W),2),M_base_analitico=round(M_emp_teor,2),
  error_pct=round(abs(abs(M_base_W)-M_emp_teor)/M_emp_teor*100 if M_emp_teor else 0,3),
  R_top_analitico=round(R_top_teor,2))

def _conv(o):
    if isinstance(o,dict): return {k:_conv(v) for k,v in o.items()}
    if isinstance(o,(list,tuple)): return [_conv(v) for v in o]
    if isinstance(o,(np.floating,)): return float(o)
    if isinstance(o,(np.integer,)): return int(o)
    return o
R=_conv(R)
with open("/tmp/resultados.json","w") as fh:
    json.dump(R,fh,indent=2,ensure_ascii=False)
print(json.dumps(R,indent=2,ensure_ascii=False))
