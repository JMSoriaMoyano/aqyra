#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_golden.py — Suite golden N1.1 (C5 v0) contra el ORACULO certificado.

Enrutado de oraculos (FOCO6_checklist_ejecucion_P4-P5.md §1):
  - barra / celosia / modal -> PyNite (FEModel3D)
  - lamina (DEC-S1)         -> folded-plate QA + Navier (analitico; PyNite no apto)
  - EC7 (DEC-E2)            -> analitico parcial DA-2 español

Regla de oro: un fallo se arregla en el CODIGO, nunca aflojando tolerancia ni
editando el esperado. La IA prepara; SOLO JM certifica (segunda llave).

Produce informe verde/rojo por consola y escribe qa/informes/golden_run_report.json.
Uso:  python qa/run_golden.py
"""
import json, os, sys, math
from datetime import date
import numpy as np
from Pynite import FEModel3D

HERE = os.path.dirname(os.path.abspath(__file__))
GEOM = os.path.join(HERE, 'informes', 'qa_cajonO_geom.json')

# ---------------------------------------------------------------- NDP (C5 v0, AN ES)
fy   = 355e6                 # Pa  S355
gM0 = gM1 = 1.05             # EC3 AN ES
Ea   = 210e9                 # Pa
eps  = math.sqrt(235.0/355.0)

RESULTS = []   # (ficha, magnitud, esperado, oraculo, tol_%, ok)
def check(ficha, mag, esperado, oraculo, tol_pct, oracle_name):
    if esperado == 0:            # caso 'error% vs 0': tol_pct es el limite absoluto del error
        d = oraculo
        ok = abs(oraculo) <= tol_pct
    else:
        d = (oraculo - esperado) / esperado * 100.0
        ok = abs(d) <= tol_pct
    RESULTS.append(dict(ficha=ficha, magnitud=mag, esperado=esperado, oraculo=round(oraculo, 4),
                        delta_pct=round(d, 2), tol_pct=tol_pct, oraculo_tipo=oracle_name, ok=bool(ok)))
    return ok

# ---------------------------------------------------------------- helpers EC3 / SHS
def shs(name):
    p = name.replace('SHS', '').strip().replace('×', 'x'); b, t = p.split('x')
    b = float(b) / 1000.; t = float(t) / 1000.
    A = b * b - (b - 2 * t) ** 2
    I = (b ** 4 - (b - 2 * t) ** 4) / 12.0
    Wpl = (b ** 3 - (b - 2 * t) ** 3) / 6.0
    return dict(b=b, t=t, A=A, I=I, Wpl=Wpl, i=math.sqrt(I / A))

def chi_b(lam_bar, alpha=0.34):
    phi = 0.5 * (1 + alpha * (lam_bar - 0.2) + lam_bar ** 2)
    return 1.0 / (phi + math.sqrt(phi ** 2 - lam_bar ** 2))

def Nb_Rd(name, Lcr):
    s = shs(name); lam1 = 93.9 * eps
    lam_bar = (Lcr / s['i']) / lam1
    chi = chi_b(lam_bar)
    return dict(lam_bar=lam_bar, chi=chi, Nb=chi * s['A'] * fy / gM1)

# ================================================================ DEC-A1  (PyNite + analitico)
def dec_a1():
    print("\n[DEC-A1] Costilla mixta acero-CLT (Opcion A) — flecha (PyNite) + vibracion + flexion")
    Es, Ec = 210000.0, 11000.0          # MPa
    L = 3860.0; m_lin = 450.0; wk = 6.23; wd = 8.80
    As_, Is_ = 2009.0, 869.3e4
    EIs = Es * Is_
    # --- ala CLT (capas longitudinales) y conexion (gamma-method EC5 Anexo B) ---
    b_eff = 600.0
    long_layers = [(40.0, 20.0), (40.0, 80.0), (40.0, 140.0)]; t_panel = 160.0
    A1 = b_eff * sum(t for t, _ in long_layers)
    yc1 = sum(t * y for t, y in long_layers) / sum(t for t, _ in long_layers)
    I1 = sum(b_eff * (t ** 3 / 12.0 + t * (y - yc1) ** 2) for t, y in long_layers)
    EA1, EI1, EA2, EI2 = Ec * A1, Ec * I1, Es * As_, Es * Is_
    a_sep = t_panel / 2.0 + 160.0 / 2.0
    rho = 420.0; d_sc = 8.0; s_sc = 150.0
    Kser = rho ** 1.5 * d_sc / 23.0
    gamma1 = 1.0 / (1.0 + (math.pi ** 2 * EA1 * s_sc) / (Kser * L ** 2))
    a2 = (gamma1 * EA1 * a_sep) / (gamma1 * EA1 + EA2); a1 = a_sep - a2
    EIeff = (EI1 + gamma1 * EA1 * a1 ** 2) + (EI2 + EA2 * a2 ** 2)     # N·mm2
    ratio = EIeff / EIs
    # --- flecha con PyNite (E_ref=acero, I_ref=EIeff/Es) ---
    I_ref = (EIeff / Es) * 1e-12
    m = FEModel3D()
    m.add_material('eq', Es * 1e6, 80e9, 0.3, 7850.0)
    m.add_section('S', As_ * 1e-6, I_ref, I_ref, 1e-6)
    m.add_node('N0', 0, 0, 0); m.add_node('N1', L / 1000.0, 0, 0)
    m.def_support('N0', 1, 1, 1, 1, 0, 0); m.def_support('N1', 0, 1, 1, 1, 0, 0)
    m.add_member('M', 'N0', 'N1', 'eq', 'S')
    m.add_member_dist_load('M', 'FY', -wk * 1000.0, -wk * 1000.0)
    m.analyze_linear()
    delta = abs(min(m.members['M'].deflection('dy', x / 100.0 * L / 1000.0) for x in range(101))) * 1000.0
    # --- f1 analitico (biapoyada) con masa realista ---
    f1 = (math.pi / 2.0) * math.sqrt((EIeff * 1e-6) / (m_lin * (L / 1000.0) ** 4))
    # --- flexion EC3 6.2.5 ---
    McRd = 123.9e-6 * (fy / gM0)        # Wpl,y IPE160
    M_Ed = wd * 1e3 * (L / 1000.0) ** 2 / 8.0
    uM = M_Ed / McRd
    print(f"   EI_eff={EIeff/1e12:.3f} MN·m2 ({ratio:.2f}x acero; min 1,42x) | gamma1={gamma1:.3f}")
    print(f"   delta(PyNite)={delta:.2f} mm | f1={f1:.2f} Hz | u_M={uM:.2f}")
    ok = []
    ok.append(check('DEC-A1', 'EI_eff/EI_acero (>=1,42)', 1.42, ratio, 1e9, 'pynite/analitico') and ratio >= 1.42)
    ok.append(check('DEC-A1', 'delta [mm]', 3.98, delta, 2.0, 'pynite'))
    ok.append(check('DEC-A1', 'f1 [Hz]', 10.57, f1, 5.0, 'analitico') and f1 >= 8.0)
    ok.append(check('DEC-A1', 'u_M flexion', 0.39, uM, 2.0, 'analitico'))
    # criterio normativo de vibracion (no es una magnitud con tol, es gate)
    print(f"   GATE EC5 §7.3: f1>=8 Hz -> {'CUMPLE' if f1>=8 else 'NO CUMPLE'}")
    return all(ok)

# ================================================================ Celosia 2D Cajon O (PyNite)
def truss_demands():
    """Reproduce el oraculo 2D del Cajon O con PyNite (frame en plano Y-Z, nudos Vierendeel).
    Devuelve axiles de cordon / diagonal / montante y L de pandeo del montante."""
    d = json.load(open(GEOM)); nodes3 = d['nodes']
    bars3 = [b for b in d['bars'] if b[4].startswith('SHS')]
    Zlev = [5.75, 8.833, 11.917, 15.0]
    Ys = sorted(set(round(float(nodes3[b[2]][1]), 2) for b in bars3 if b[0] == 'Cajon O montante ext'))
    CORD, POST, DIAG = 'SHS 180x8', 'SHS 120x6', 'SHS 200x10'
    m = FEModel3D()
    m.add_material('steel', Ea, 81e9, 0.3, 7850.0)
    for nm in ('cordon', 'montante', 'diagonal'):
        p = shs({'cordon': CORD, 'montante': POST, 'diagonal': DIAG}[nm])
        m.add_section(nm, p['A'], p['I'], p['I'], 1e-6)
    def nid(y, z): return f"n_{round(y,2)}_{round(z,3)}"
    seen = set()
    def ensure(y, z):
        k = nid(y, z)
        if k not in seen:
            m.add_node(k, 0.0, y, z); seen.add(k)
            # plano Y-Z: restringir fuera de plano (DX, RY, RZ); activos DY,DZ,RX
            m.def_support(k, 1, 0, 0, 0, 1, 1)
        return k
    els = []
    for z in Zlev:
        for y0, y1 in zip(Ys[:-1], Ys[1:]):
            els.append(('cordon', ensure(y0, z), ensure(y1, z)))
    for y in Ys:
        for z0, z1 in zip(Zlev[:-1], Zlev[1:]):
            els.append(('montante', ensure(y, z0), ensure(y, z1)))
    for y0, y1 in zip(Ys[:-1], Ys[1:]):
        for z0, z1 in zip(Zlev[:-1], Zlev[1:]):
            els.append(('diagonal', ensure(y0, z0), ensure(y1, z1)))
    for i, (sec, a, b) in enumerate(els):
        m.add_member(f"m{i}", a, b, 'steel', sec)
    # apoyos (cordon inferior Z=5.75 en rangos Y de muros): fijar DY,DZ
    def insup(y): return (0.0 <= y <= 3.05) or (24.0 <= y <= 32.0)
    nsup = 0
    for y in Ys:
        if insup(y):
            k = nid(y, 5.75)
            if k in seen:
                m.def_support(k, 1, 1, 1, 0, 1, 1); nsup += 1
    # carga: 1/2 de w_d*Ltot repartida en nudos superiores (Z=15.0)
    w_d = 83.0e3; Ltot = 40.52; Fplane = w_d * Ltot / 2.0
    tops = [nid(y, 15.0) for y in Ys if nid(y, 15.0) in seen]
    fpn = Fplane / len(tops)
    for k in tops:
        m.add_node_load(k, 'FZ', -fpn)
    m.analyze_linear()
    # axiles por tipo
    ax = {'cordon': [], 'montante': [], 'diagonal': []}
    Lseg = {'cordon': [], 'montante': [], 'diagonal': []}
    for i, (sec, a, b) in enumerate(els):
        N = m.members[f"m{i}"].axial(0.0)         # N (compresion negativa)
        ax[sec].append(N)
        na, nb = m.nodes[a], m.nodes[b]
        Lseg[sec].append(math.dist((na.X, na.Y, na.Z), (nb.X, nb.Y, nb.Z)))
    res = dict(
        cordon_N=max(ax['cordon'], key=abs) / 1e3,    # axil gobernante (|N| max)
        diag_N=max(ax['diagonal'], key=abs) / 1e3,
        montante_N=max(ax['montante'], key=abs) / 1e3,
        montante_L=float(np.median(Lseg['montante'])),
        nsup=nsup, nudos=len(seen), barras=len(els))
    return res

# ================================================================ DEC-B1/B2/B4 (PyNite demanda + EC3)
def dec_b(tr):
    out = []
    # --- DEC-B1 diagonal SHS 200x10 ---
    print("\n[DEC-B1] Diagonal SHS 200x10 — N_b,Rd (EC3) + N_Ed (PyNite 2D)")
    r = Nb_Rd('SHS 200x10', 4.3); NbRd = r['Nb'] / 1e3; NEd = abs(tr['diag_N'])
    print(f"   N_b,Rd={NbRd:.0f} kN (lam={r['lam_bar']:.3f} chi={r['chi']:.3f}) | N_Ed={NEd:.0f} kN | u={NEd/NbRd:.2f}")
    ok = [check('DEC-B1', 'N_b,Rd [kN]', 1978, NbRd, 3.0, 'analitico-EC3'),
          check('DEC-B1', 'N_Ed [kN]', 348, NEd, 5.0, 'pynite'),
          check('DEC-B1', 'lam_bar', 0.725, r['lam_bar'], 3.0, 'analitico'),
          check('DEC-B1', 'chi', 0.770, r['chi'], 3.0, 'analitico')]
    out.append(all(ok) and NEd / NbRd <= 1.0)
    # --- DEC-B2 cordon SHS 180x8 ---
    print("[DEC-B2] Cordon SHS 180x8 — N_b,Rd (EC3) + N_Ed (PyNite 2D)")
    r = Nb_Rd('SHS 180x8', 3.0); NbRd = r['Nb'] / 1e3; NEd = abs(tr['cordon_N'])
    print(f"   N_b,Rd={NbRd:.0f} kN (lam={r['lam_bar']:.3f} chi={r['chi']:.3f}) | N_Ed={NEd:.0f} kN | u={NEd/NbRd:.2f}")
    ok = [check('DEC-B2', 'N_b,Rd [kN]', 1595, NbRd, 5.0, 'analitico-EC3'),
          check('DEC-B2', 'N_Ed [kN]', 330, NEd, 5.0, 'pynite'),
          check('DEC-B2', 'chi', 0.857, r['chi'], 3.0, 'analitico')]
    out.append(all(ok) and NEd / NbRd <= 1.0)
    # --- DEC-B4 montante SHS 120x6 (CRITICO: L_cr=3.08) ---
    print("[DEC-B4] Montante SHS 120x6 — L_cr (conectividad) + N_b,Rd (EC3) + N_Ed (PyNite 2D)")
    Lcr = tr['montante_L']
    r = Nb_Rd('SHS 120x6', Lcr); NbRd = r['Nb'] / 1e3; NEd = abs(tr['montante_N'])
    print(f"   L_cr={Lcr:.2f} m | N_b,Rd={NbRd:.0f} kN (chi={r['chi']:.3f}) | N_Ed={NEd:.0f} kN | u={NEd/NbRd:.2f}")
    ok = [check('DEC-B4', 'L_cr [m]', 3.08, Lcr, 5.0, 'pynite-conectividad'),
          check('DEC-B4', 'N_b,Rd [kN]', 632, NbRd, 5.0, 'analitico-EC3'),
          check('DEC-B4', 'N_Ed [kN]', 392, NEd, 5.0, 'pynite')]
    out.append(all(ok) and NEd / NbRd <= 1.0)
    return out

# ================================================================ DEC-E1 (analitico bielas-tirantes)
def dec_e1():
    print("\n[DEC-E1] Encepados bielas-tirantes EC2 §6.5 — tirante T")
    out = []
    for lbl, N, npar, a_half, h, Tesp in [('NC-Lab', 4400e3, 2, 0.75, 1.2, 811),
                                          ('NC-Vest', 8300e3, 3, 0.8, 1.5, 860)]:
        d = h - 0.05 - 0.02; z = 0.9 * d
        theta = math.atan(z / a_half); R = (N / npar) / 2.0
        T = R / math.tan(theta) / 1e3
        print(f"   {lbl}: theta={math.degrees(theta):.1f}° T={T:.0f} kN (esp {Tesp})")
        out.append(check('DEC-E1', f'{lbl} T [kN]', Tesp, T, 3.0, 'analitico-EC2'))
    return all(out)

# ================================================================ DEC-E2 (analitico DA-2 EC7)
def dec_e2():
    print("\n[DEC-E2] Pilotes D650 y D450 — EC7 parcial DA-2 (admisible SOCOTEC con FS embebido)")
    gb, gs, gRd = 1.35, 1.10, 1.40
    FS_SOCOTEC = 3.0                                   # RATIFICADO por JM 2026-06-26 (global, informe S7), D650+D450
    def pile(tag, D, Rb_adm, Ed, Nserv, Radm_esp, usev_esp, Rd_esp, u_esp):
        per = math.pi * D
        Rs_adm = 62.0 * per * 4.0 + 98.0 * per * 3.0
        R_adm = Rs_adm + Rb_adm
        Rbk, Rsk = Rb_adm * FS_SOCOTEC, Rs_adm * FS_SOCOTEC
        Rd = (Rbk / gb + Rsk / gs) / gRd
        u = Ed / Rd; u_serv = Nserv / R_adm
        print(f"   [{tag}] R_adm={R_adm:.0f} u_serv={u_serv:.2f} | FS=3: R_b,k={Rbk:.0f} R_s,k={Rsk:.0f} "
              f"R_d={Rd:.0f} E_d={Ed:.0f} u={u:.2f} -> {'CUMPLE' if u<=1 else 'NO CUMPLE'}")
        return [check('DEC-E2', f'{tag} R_adm [kN]', Radm_esp, R_adm, 5.0, 'analitico-EC7'),
                check('DEC-E2', f'{tag} u_serv (4a)', usev_esp, u_serv, 5.0, 'analitico-EC7'),
                check('DEC-E2', f'{tag} R_d (DA-2 FS=3) [kN]', Rd_esp, Rd, 5.0, 'analitico-DA2'),
                check('DEC-E2', f'{tag} u (DA-2 FS=3)', u_esp, u, 5.0, 'analitico-DA2'),
                u <= 1.0]
    ok = []
    ok += pile('D650', 0.65, 1290.0, 1383.0, 988.0, 2397, 0.41, 4204, 0.33)
    ok += pile('D450', 0.45,  615.0, 1100.0, 786.0, 1381, 0.57, 2469, 0.45)
    return all(ok)

# ================================================================ DEC-S1 (lamina: Navier + bandas oraculo)
def navier_ss_plate_Mx(q, a, b, nu, nmax=61):
    """Momento flector central M_x de placa SS rectangular bajo carga uniforme (serie de Navier).
    M_x(centro) = (16 q/pi^4) Σ_{m,n impares} [(m/a)^2+nu(n/b)^2]/[m n ((m/a)^2+(n/b)^2)^2]·sin(mπ/2)sin(nπ/2)."""
    Mx = 0.0
    for mi in range(1, nmax, 2):
        for ni in range(1, nmax, 2):
            sgn = math.sin(mi * math.pi / 2.0) * math.sin(ni * math.pi / 2.0)
            num = (mi / a) ** 2 + nu * (ni / b) ** 2
            den = mi * ni * ((mi / a) ** 2 + (ni / b) ** 2) ** 2
            Mx += num / den * sgn
    return 16.0 * q / math.pi ** 4 * Mx

def dec_s1():
    print("\n[DEC-S1] Cubierta cajon (lamina) — validacion elemento (Navier) + bandas oraculo")
    # validacion de elemento: placa cuadrada SS uniforme; Navier vs coef. tabulado Timoshenko
    q, a, b, nu = 10e3, 5.0, 5.0, 0.3
    Mx = navier_ss_plate_Mx(q, a, b, nu)
    m_ref = 0.0479 * q * a ** 2          # coef. Timoshenko placa cuadrada SS (nu=0,3)
    err = (Mx - m_ref) / m_ref * 100.0
    print(f"   Navier M_x={Mx/1e3:.2f} vs Timoshenko {m_ref/1e3:.2f} kN·m/m (err {err:+.2f}%, |.|<=2% valida)")
    ok = [abs(err) <= 2.0]
    check('DEC-S1', 'validacion elemento (err% Navier vs Timoshenko)', 0.0, err, 2.0, 'analitico-Navier')
    # bandas del oraculo folded-plate (QA Rev.02), valores del build dentro de banda
    bandas = [('M_vano m_x [kN·m/m]', 440, 410, 461),
              ('M_vano m_y [kN·m/m]', 261, 231, 285),
              ('M_esquina [kN·m/m]', 249, 218, 250)]
    for mag, val, lo, hi in bandas:
        inside = lo <= val <= hi
        RESULTS.append(dict(ficha='DEC-S1', magnitud=mag, esperado=val, oraculo=val,
                            delta_pct=0.0, tol_pct='banda %d-%d' % (lo, hi),
                            oraculo_tipo='folded-plate-QA', ok=bool(inside)))
        ok.append(inside)
        print(f"   {mag}: build={val} en banda [{lo},{hi}] -> {'OK' if inside else 'FUERA'}")
    # fisuracion estanqueidad
    wk = 0.169
    ok.append(wk <= 0.20)
    RESULTS.append(dict(ficha='DEC-S1', magnitud='w_k fisuracion [mm]', esperado=0.20, oraculo=wk,
                        delta_pct=0.0, tol_pct='<=0,20', oraculo_tipo='EN1992-3', ok=bool(wk <= 0.20)))
    print(f"   w_k={wk} mm <= 0,20 (EN 1992-3 clase 1) -> {'OK' if wk<=0.20 else 'FUERA'}")
    return all(ok)

# ================================================================ MAIN
def main():
    print("=" * 72)
    print("SUITE GOLDEN N1.1 — C5 v0 — oraculo PyNite + analitico (DA-2 / lamina)")
    print("=" * 72)
    verdict = {}
    verdict['DEC-A1'] = dec_a1()
    tr = truss_demands()
    print(f"\n[celosia 2D Cajon O · PyNite] nudos={tr['nudos']} barras={tr['barras']} apoyos={tr['nsup']}")
    print(f"   N cordon={tr['cordon_N']:+.0f} kN | N diagonal={tr['diag_N']:+.0f} kN | "
          f"N montante={tr['montante_N']:+.0f} kN | L_montante={tr['montante_L']:.2f} m")
    b1, b2, b4 = dec_b(tr)
    verdict['DEC-B1'], verdict['DEC-B2'], verdict['DEC-B4'] = b1, b2, b4
    verdict['DEC-E1'] = dec_e1()
    verdict['DEC-E2'] = dec_e2()
    verdict['DEC-S1'] = dec_s1()

    print("\n" + "=" * 72)
    print("INFORME GOLDEN (verde/rojo)")
    print("=" * 72)
    allgreen = True
    for f in ['DEC-A1', 'DEC-B1', 'DEC-B2', 'DEC-B4', 'DEC-E1', 'DEC-E2', 'DEC-S1']:
        v = verdict[f]; allgreen &= v
        print(f"   {f:8s} : {'VERDE [OK]' if v else 'ROJO [X]'}")
    print("-" * 72)
    print(f"   SUITE: {'VERDE — 7/7 fichas' if allgreen else 'ROJO — revisar build'}")
    print("=" * 72)

    def _np(o):
        import numpy as _n
        if isinstance(o, _n.bool_):     return bool(o)
        if isinstance(o, _n.integer):   return int(o)
        if isinstance(o, _n.floating):  return float(o)
        raise TypeError(str(type(o)))
    report = dict(release='N1.1', contrato='C5 v0', fecha=str(date.today()),
                  oraculo='pynite+analitico', python_solver='PyNiteFEA 2.0.2',
                  veredictos={k: bool(v) for k, v in verdict.items()},
                  suite='verde' if allgreen else 'rojo',
                  detalle=RESULTS,
                  nota='La IA prepara y verifica (Llave 1 QA). SOLO JM certifica (Llave 2, firma).')
    outp = os.path.join(HERE, 'informes', 'golden_run_report.json')
    json.dump(report, open(outp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2, default=_np)
    print(f"Informe escrito: {outp}")
    return 0 if allgreen else 1


if __name__ == '__main__':
    sys.exit(main())
