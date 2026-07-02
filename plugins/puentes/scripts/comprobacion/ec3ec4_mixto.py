"""
Comprobacion EC3 + EC4 de un tablero MIXTO acero-hormigon (PT 7.5, Ola 7).

- Clasificacion de la seccion de acero (clase 1-4, EN 1993-1-1 Tabla 5.2).
- Abolladura de paneles por ANCHO/AREA EFICAZ (EN 1993-1-5 §4.4) si la seccion
  es clase 4 (decision PT 7.5: ancho eficaz, NO autovalores -> eso es FEM-3).
- Resistencia a flexion de la seccion mixta (M_pl,Rd por fibras, conexion total,
  EN 1994-1-1 §6.2.1.2) y cortante (alma de acero, Vpl,Rd).
- CONEXION (conectores tipo perno, EN 1994-1-1 §6.6): P_Rd, fuerza de rasante
  Nc, numero de conectores Nf y grado de conexion eta.  [reuso por formula de
  motor-calculo `mixtas/verificacion_mixta`]
- FATIGA basica (EN 1993-1-9): carrera de tensiones Delta_sigma en el ala inferior
  bajo el modelo de fatiga FLM3 vs Delta_sigma_C/gamma_Mf por categoria de detalle
  (sin dano acumulado Palmgren-Miner ni espectro completo -> gancho diferido).

SI (N, m). Predimensionado/asistencia; revisar y firmar por tecnico competente (ICCP).
"""
from __future__ import annotations
import math

GM0 = 1.0      # EC3 resistencia de seccion
GM1 = 1.0      # EC3 inestabilidad
GMf = 1.35     # EC3-1-9 fatiga (consecuencia alta, baja inspeccion) [confirmar AN]
GV = 1.25      # conectores
GC = 1.50      # hormigon


def clasificar_seccion(steel, fy, psi_web=-1.0):
    """Clasifica el perfil en I (alma en flexion, ala en compresion). Devuelve
    clase global (max de alma y ala) y detalle. EN 1993-1-1 Tabla 5.2."""
    eps = math.sqrt(235e6 / fy)
    b = steel.get("b"); h = steel.get("h"); tw = steel.get("tw"); tf = steel.get("tf")
    r = steel.get("r", 0.0)
    if None in (b, h, tw, tf):
        return {"clase": 3, "clase_ala": 3, "clase_alma": 3, "eps": eps,
                "nota": "geometria de placas no disponible; clase 3 por defecto"}
    # ala comprimida (voladizo): c = (b - tw)/2 - r
    c_f = (b - tw) / 2.0 - r
    rat_f = c_f / tf
    if rat_f <= 9 * eps:
        cl_f = 1
    elif rat_f <= 10 * eps:
        cl_f = 2
    elif rat_f <= 14 * eps:
        cl_f = 3
    else:
        cl_f = 4
    # alma en flexion (interna): c = h - 2tf - 2r
    c_w = h - 2 * tf - 2 * r
    rat_w = c_w / tw
    if rat_w <= 72 * eps:
        cl_w = 1
    elif rat_w <= 83 * eps:
        cl_w = 2
    elif rat_w <= 124 * eps:
        cl_w = 3
    else:
        cl_w = 4
    return {"clase": max(cl_f, cl_w), "clase_ala": cl_f, "clase_alma": cl_w,
            "c_ala_tf": rat_f, "c_alma_tw": rat_w, "eps": eps}


def ancho_eficaz_placa(b, t, fy, ksigma=4.0, interno=True, psi=1.0):
    """Factor de reduccion rho por abolladura de placa (EN 1993-1-5 §4.4) y ancho
    eficaz b_eff = rho*b. interno=panel apoyado en dos bordes (ksigma~4 unif.);
    outstand (voladizo) ksigma~0.43. Predimensionado."""
    eps = math.sqrt(235e6 / fy)
    lam_p = (b / t) / (28.4 * eps * math.sqrt(ksigma))
    if interno:
        if lam_p <= 0.673:
            rho = 1.0
        else:
            rho = (lam_p - 0.055 * (3 + psi)) / lam_p ** 2
    else:  # outstand
        if lam_p <= 0.748:
            rho = 1.0
        else:
            rho = (lam_p - 0.188) / lam_p ** 2
    rho = max(0.0, min(1.0, rho))
    return {"lambda_p": lam_p, "rho": rho, "b_eff_m": rho * b, "ksigma": ksigma}


def b_eff_losa(L, sep, b0=0.0):
    """Ancho eficaz de la losa por viga (EC4 §5.4.1.2): b_eff = b0 + 2*min(L/8,sep/2)."""
    bei = min(L / 8.0, sep / 2.0)
    return b0 + 2.0 * bei


def M_pl_fibras(steel, t_losa, b_eff, fy, fck, n_fib=2000):
    """Momento plastico resistente de la seccion mixta por FIBRAS (conexion total,
    EN 1994-1-1 §6.2.1.2). Losa de hormigon ARRIBA (cobertura t_losa), perfil I
    debajo. Solo compresion en el hormigon. Devuelve (M_pl_Rd, zeta_PNA, zona)."""
    fyd = fy / GM0; fcd = 0.85 * fck / GC
    b = steel["b"]; h = steel["h"]; tw = steel["tw"]; tf = steel["tf"]
    H = t_losa + h
    dz = H / n_fib
    zs = [(i + 0.5) * dz for i in range(n_fib)]   # zeta desde la cara superior de la losa

    def w_steel(z):
        zeta = z - t_losa                          # desde la cara superior del acero
        if zeta < 0:
            return 0.0
        if 0 <= zeta < tf or h - tf <= zeta <= h:
            return b
        if tf <= zeta < h - tf:
            return tw
        return 0.0

    def fib(z, zna):
        ws = w_steel(z)
        if ws > 0:
            s = fyd if z > zna else -fyd           # compresion arriba del PNA
            return s * ws * dz
        if 0 <= z <= t_losa and z < zna:           # hormigon comprimido (arriba del PNA)
            return -fcd * b_eff * dz               # compresion negativa (mismo signo abajo del eje)
        return 0.0

    # convencion: compresion = positiva arriba del PNA para el acero; el hormigon
    # solo comprime cuando esta por encima del PNA. Balance: sum(fuerzas)=0.
    def net(zna):
        tot = 0.0
        for z in zs:
            ws = w_steel(z)
            if ws > 0:
                tot += (fyd if z < zna else -fyd) * ws * dz   # arriba(z<zna)=compresion
            elif z < zna:
                tot += fcd * b_eff * dz                        # hormigon comprimido
        return tot

    loz, hiz = 0.0, H
    for _ in range(60):
        mid = 0.5 * (loz + hiz)
        if net(mid) > 0:        # demasiada compresion -> subir PNA (menos area comprimida)
            hiz = mid
        else:
            loz = mid
    zna = 0.5 * (loz + hiz)
    M = 0.0
    for z in zs:
        ws = w_steel(z)
        if ws > 0:
            f = fyd * ws * dz
        elif z < zna:
            f = fcd * b_eff * dz
        else:
            f = 0.0
        M += f * abs(z - zna)
    if zna <= t_losa:
        zona = "losa"
    elif zna <= t_losa + tf:
        zona = "ala superior"
    elif zna < t_losa + h - tf:
        zona = "alma"
    else:
        zona = "ala inferior"
    return M, zna, zona


def conexion(steel, t_losa, b_eff, fy, fck, Ecm, conector, L):
    """Conexion por pernos (EN 1994-1-1 §6.6). Espejo por formula de
    verificacion_mixta.conexion (losa maciza, sin chapa)."""
    d = conector["d"]; hsc = conector["hsc"]; fu = conector["fu"]
    sep = conector["sep_long"]; nfila = conector.get("n_fila", 1)
    alpha = 1.0 if hsc / d >= 4 else 0.2 * (hsc / d + 1)
    PRd1 = 0.8 * fu * (math.pi * d ** 2 / 4) / GV
    PRd2 = 0.29 * alpha * d ** 2 * math.sqrt(fck * Ecm) / GV
    PRd = min(PRd1, PRd2)
    Na = steel["A"] * fy / GM0
    Fcf = 0.85 * fck / GC * b_eff * t_losa
    Nc = min(Na, Fcf)
    Nf = Nc / PRd
    n_disp = nfila * (L / 2.0) / sep
    eta = n_disp / Nf if Nf > 0 else 0.0
    eta_min = max(1 - (355e6 / fy) * (0.75 - 0.03 * min(L, 25.0)), 0.4)
    return {"PRd1_kN": PRd1 / 1e3, "PRd2_kN": PRd2 / 1e3, "PRd_kN": PRd / 1e3,
            "Na_kN": Na / 1e3, "Fcf_kN": Fcf / 1e3, "Nc_kN": Nc / 1e3,
            "Nf_media_luz": Nf, "n_disp_media_luz": n_disp, "grado_eta": eta,
            "eta_min": eta_min, "ok": bool(eta >= max(eta_min, 1.0) or eta >= 1.0)}


def comprobar(mixto, esfuerzos, props_mixta):
    """mixto: dict con 'material_s'{fy,fu,E}, 'material_h'{fck,E,fctm?}, 'conector'{...},
       'fatiga'{detalle_MPa,lambda?,phi?}, 'n_vigas','L','sep_vigas','t_losa'.
    esfuerzos: {'M_Ed_Nm','V_Ed_N','M_fat_Nm'(rango de fatiga, por toda la seccion)}.
    props_mixta: salida de _seccion_mixta_props + 'steel'."""
    ms = mixto["material_s"]; mh = mixto["material_h"]
    fy = ms["fy"]; fu = ms.get("fu", 1.25 * fy); fck = mh["fck"]; Ecm = mh["E"]
    steel = props_mixta["steel"]; t_losa = mixto["t_losa"]
    L = mixto["L"]; sep = mixto["sep_vigas"]; ng = int(mixto["n_vigas"])

    # 1) clasificacion
    cl = clasificar_seccion(steel, fy)
    # 2) ancho eficaz de losa por viga y abolladura de placas si clase 4
    be = b_eff_losa(L, sep)
    be = min(be, sep)
    abolladura = None
    if cl["clase"] == 4 and all(k in steel for k in ("b", "h", "tw", "tf")):
        c_ala = (steel["b"] - steel["tw"]) / 2.0
        ab_f = ancho_eficaz_placa(c_ala, steel["tf"], fy, ksigma=0.43, interno=False)
        ab_w = ancho_eficaz_placa(steel["h"] - 2 * steel["tf"], steel["tw"], fy, ksigma=23.9, interno=True, psi=-1.0)
        abolladura = {"ala": ab_f, "alma": ab_w}

    # 3) flexion: M_pl,Rd por viga (con su b_eff) -> total
    M_pl, zna, zona = M_pl_fibras(steel, t_losa, be, fy, fck)
    M_Rd_tot = ng * M_pl
    M_Ed = esfuerzos["M_Ed_Nm"]
    u_flex = M_Ed / M_Rd_tot if M_Rd_tot > 0 else 9.99

    # 4) cortante (alma de acero) Vpl,Rd
    Avz = steel.get("Avz", steel["h"] * steel["tw"])
    Vpl = ng * Avz * fy / (math.sqrt(3) * GM0)
    V_Ed = esfuerzos.get("V_Ed_N", 0.0)
    u_cort = V_Ed / Vpl if Vpl > 0 else 0.0

    # 5) conexion
    conn = None
    if mixto.get("conector"):
        conn = conexion(steel, t_losa, be, fy, fck, Ecm, mixto["conector"], L)

    # 6) fatiga basica EN 1993-1-9
    fat = None
    if esfuerzos.get("M_fat_Nm") and mixto.get("fatiga"):
        I_c = props_mixta["I_comp_m4"]; c_inf = props_mixta["c_acero_inf"]
        dsig = esfuerzos["M_fat_Nm"] * c_inf / I_c            # rango en el ala inferior
        lam = mixto["fatiga"].get("lambda", 1.0); phi = mixto["fatiga"].get("phi", 1.0)
        dsig_E2 = lam * phi * dsig
        dsig_C = mixto["fatiga"]["detalle_MPa"] * 1e6
        dsig_Rd = dsig_C / GMf
        u_fat = dsig_E2 / dsig_Rd if dsig_Rd > 0 else 9.99
        fat = {"delta_sigma_MPa": dsig / 1e6, "delta_sigma_E2_MPa": dsig_E2 / 1e6,
               "delta_sigma_C_MPa": dsig_C / 1e6, "delta_sigma_Rd_MPa": dsig_Rd / 1e6,
               "u_fatiga": u_fat, "lambda": lam, "phi": phi,
               "nota": "check basico FLM3; sin Palmgren-Miner (gancho diferido)"}

    checks = [
        {"nombre": "Flexion mixta M_pl,Rd (EC4)", "valor": M_Ed, "limite": M_Rd_tot,
         "aprov": u_flex, "cumple": bool(u_flex <= 1.0)},
        {"nombre": "Cortante alma Vpl,Rd (EC3)", "valor": V_Ed, "limite": Vpl,
         "aprov": u_cort, "cumple": bool(u_cort <= 1.0)},
    ]
    if conn is not None:
        checks.append({"nombre": "Conexion grado eta (EC4 6.6)", "valor": conn["grado_eta"],
                       "limite": 1.0, "aprov": (conn["eta_min"] / conn["grado_eta"] if conn["grado_eta"] else 9.99),
                       "cumple": conn["ok"]})
    if fat is not None:
        checks.append({"nombre": "Fatiga ala inferior (EC3-1-9)", "valor": fat["delta_sigma_E2_MPa"],
                       "limite": fat["delta_sigma_Rd_MPa"], "aprov": fat["u_fatiga"],
                       "cumple": bool(fat["u_fatiga"] <= 1.0)})

    aprov = max(c["aprov"] for c in checks)
    veredicto = "CUMPLE" if all(c["cumple"] for c in checks) else "NO CUMPLE"
    return {"checks": checks, "veredicto": veredicto, "aprovechamiento_max": aprov,
            "clasificacion": cl, "b_eff_losa_m": be, "abolladura_EN1993_1_5": abolladura,
            "M_pl_Rd_viga_Nm": M_pl, "M_Rd_total_Nm": M_Rd_tot, "PNA_zona": zona,
            "Vpl_Rd_N": Vpl, "conexion": conn, "fatiga": fat}
