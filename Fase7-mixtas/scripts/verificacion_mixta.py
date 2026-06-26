"""
Verificacion de VIGA MIXTA acero-hormigon (EN 1994-1-1, AN Espana).

  - Ancho eficaz b_eff (§5.4.1.2).
  - Momento plastico resistente M_pl,Rd (§6.2.1.2) por MODELO DE FIBRAS (eje neutro
    plastico general: en losa, ala o alma). Conexion total.
  - Conexion a cortante (§6.6): resistencia del perno P_Rd con reduccion kt por chapa
    perpendicular; nº de conectores para conexion total y grado de conexion.
  - Cortante vertical V_pl,Rd (§6.2.2) del alma de acero.
  - Fase de CONSTRUCCION (sin apear): acero solo, M_c,Rd = Wpl·fy/γM0 (nota PLT).
  - Flecha (ELS): acero en construccion + mixta a corto (n0) y largo plazo (nL).

SI (N, m, Pa). γM0=1.0, γv=1.25, γc=1.5 [confirmar AN].
"""
import sys
import os
import json
import math

GM0 = 1.0
GV = 1.25
GC = 1.50
G_ACC = 9.81
LIM_TOTAL, LIM_ACTIVA = 250.0, 350.0   # L/250 total, L/350 sobrecarga [criterio despacho]


def b_eff(L, b0):
    """Ancho eficaz de una viga biapoyada: b_eff = b0 + 2·Le/8 (Le=L)."""
    be = 2 * (L / 8)
    return b0 + be, be


def M_pl_fibras(model, b_eff_m):
    """Momento plastico resistente por fibras (conexion total). Devuelve M_pl,Rd y el PNA."""
    v = model["viga"]; lo = model["losa"]
    mp_s = model["materiales"][v["acero"]]; mp_c = model["materiales"][v["hormigon"]]
    fyd = mp_s["fy"] / GM0
    fcd = mp_c["fck"] / GC
    h = v["h"]; b = v["b"]; tw = v["tw"]; tf = v["tf"]
    hp = lo["hp"]; hc = lo["hc"]
    y_top = h + hp + hc                          # cota superior de la losa (desde base de acero)

    N = 4000
    ys = [(i + 0.5) * y_top / N for i in range(N)]
    dy = y_top / N

    def width_steel(y):
        if 0 <= y < tf or h - tf <= y <= h:
            return b
        if tf <= y < h - tf:
            return tw
        return 0.0

    def fib_force(y, y_na):
        # acero
        ws = width_steel(y)
        if ws > 0:
            s = fyd if y > y_na else -fyd     # compresion (+) arriba del PNA
            return s * ws * dy
        # hormigon de cobertura (solo compresion, solo por encima del PNA)
        if h + hp <= y <= y_top and y > y_na:
            return 0.85 * fcd * b_eff_m * dy
        return 0.0

    # balance axil: buscar y_na con N_net=0 (compresion positiva = traccion)
    def net(y_na):
        return sum(fib_force(y, y_na) for y in ys)

    lo_y, hi_y = 0.0, y_top
    for _ in range(60):
        mid = 0.5 * (lo_y + hi_y)
        # net>0 => demasiada compresion => subir PNA (reduce compresion)
        if net(mid) > 0:
            lo_y = mid
        else:
            hi_y = mid
    y_na = 0.5 * (lo_y + hi_y)
    M = sum(abs(fib_force(y, y_na)) * abs(y - y_na) for y in ys)
    # localizacion del PNA
    if y_na >= h:
        zona = "losa"
    elif y_na >= h - tf:
        zona = "ala superior"
    elif y_na > tf:
        zona = "alma"
    else:
        zona = "ala inferior"
    return M, y_na, zona


def conexion(model, b_eff_m):
    v = model["viga"]; lo = model["losa"]; co = model["conectores"]
    mp_s = model["materiales"][v["acero"]]; mp_c = model["materiales"][v["hormigon"]]
    d = co["d"]; hsc = co["hsc"]; fu = co["fu"]; Ecm = mp_c["E"]; fck = mp_c["fck"]
    alpha = 1.0 if hsc / d >= 4 else 0.2 * (hsc / d + 1)
    PRd1 = 0.8 * fu * (math.pi * d ** 2 / 4) / GV
    PRd2 = 0.29 * alpha * d ** 2 * math.sqrt(fck * Ecm) / GV
    PRd_solid = min(PRd1, PRd2)
    # reduccion por chapa perpendicular (§6.6.4.2)
    nr = lo["nr"]; b0 = lo["b0"]; hp = lo["hp"]
    kt = (0.7 / math.sqrt(nr)) * (b0 / hp) * (hsc / hp - 1)
    kt_max = 0.85 if nr == 1 else 0.70           # tabla 6.2 (perno a traves de chapa) [confirmar]
    kt = min(kt, kt_max)
    PRd = kt * PRd_solid
    # fuerza de rasante longitudinal (conexion total) = compresion mixta Nc
    Na = v["A"] * mp_s["fy"] / GM0
    Fcf = 0.85 * fck / GC * b_eff_m * lo["hc"]
    Nc = min(Na, Fcf)
    Nf = Nc / PRd                                 # conectores para conexion total (media luz)
    n_prov = (v["L"] / 2) / co["sep_long"]        # conectores dispuestos en media luz
    eta = n_prov / Nf
    # grado minimo (§6.6.1.2) para perfil con alas iguales, L<=25 m
    Le = v["L"]
    eta_min = max(1 - (355e6 / mp_s["fy"]) * (0.75 - 0.03 * Le), 0.4)
    return {"PRd1_kN": PRd1 / 1e3, "PRd2_kN": PRd2 / 1e3, "kt": kt, "PRd_kN": PRd / 1e3,
            "Na_kN": Na / 1e3, "Fcf_kN": Fcf / 1e3, "Nc_kN": Nc / 1e3,
            "Nf_total": Nf, "n_disp_media_luz": n_prov, "grado_eta": eta,
            "eta_min": eta_min, "conexion_total": bool(eta >= 1.0),
            "ok": bool(eta >= min(1.0, eta_min) and eta >= eta_min)}


def I_compuesta(model, b_eff_m, n):
    """Inercia de la seccion mixta homogeneizada (coef. de equivalencia n)."""
    v = model["viga"]; lo = model["losa"]
    A_s = v["A"]; I_s = v["Iy"]; h = v["h"]
    y_s = h / 2
    hc = lo["hc"]; hp = lo["hp"]
    A_c = b_eff_m * hc / n
    y_c = h + hp + hc / 2
    y_na = (A_s * y_s + A_c * y_c) / (A_s + A_c)
    I = I_s + A_s * (y_na - y_s) ** 2 + (b_eff_m * hc ** 3 / 12) / n + A_c * (y_c - y_na) ** 2
    return I, y_na


def flecha(model, results, b_eff_m):
    v = model["viga"]; L = v["L"]
    mp_s = model["materiales"][v["acero"]]; mp_c = model["materiales"][v["hormigon"]]
    Ea = mp_s["E"]; Ecm = mp_c["E"]
    n0 = Ea / Ecm
    nL = Ea / (Ecm / 3.0)                          # largo plazo (fluencia, modulo eficaz ~Ecm/3)
    w = results["cargas_kN_m"]
    w_constr = (w["w_steel"] + w["w_losa"]) * 1e3  # acero solo (sin apear)
    w_g2 = w["w_g2"] * 1e3
    w_q = w["w_q"] * 1e3

    def d5(wq, E, I):
        return 5 * wq * L ** 4 / (384 * E * I)

    I_s = v["Iy"]
    I_short, _ = I_compuesta(model, b_eff_m, n0)
    I_long, _ = I_compuesta(model, b_eff_m, nL)
    d_constr = 0.0 if v["apeado"] else d5(w_constr, Ea, I_s)
    d_g2 = d5(w_g2, Ea, I_long)                    # carga muerta permanente -> largo plazo
    d_q = d5(w_q, Ea, I_short)                     # sobrecarga -> corto plazo
    d_total = d_constr + d_g2 + d_q
    return {"n0": n0, "nL": nL, "I_acero_cm4": I_s * 1e8,
            "I_corto_cm4": I_short * 1e8, "I_largo_cm4": I_long * 1e8,
            "d_construccion_mm": d_constr * 1e3, "d_muertas_mm": d_g2 * 1e3, "d_uso_mm": d_q * 1e3,
            "d_total_mm": d_total * 1e3, "lim_total_mm": L / LIM_TOTAL * 1e3,
            "u_total": d_total / (L / LIM_TOTAL), "ok_total": bool(d_total <= L / LIM_TOTAL),
            "d_activa_mm": d_q * 1e3, "lim_activa_mm": L / LIM_ACTIVA * 1e3,
            "u_activa": d_q / (L / LIM_ACTIVA), "ok_activa": bool(d_q <= L / LIM_ACTIVA)}


def verificar(model, results):
    v = model["viga"]; lo = model["losa"]
    mp_s = model["materiales"][v["acero"]]
    fy = mp_s["fy"]; L = v["L"]
    beff, be = b_eff(L, lo["b0"])

    out = {"info": results["info"], "b_eff_m": beff}

    # Conexion a cortante (define el grado de conexion)
    out["conexion"] = conexion(model, beff)
    eta = out["conexion"]["grado_eta"]

    # M_pl,Rd conexion total (fibras) y M_Rd de diseno (interpolacion si conexion parcial)
    Mpl, y_na, zona = M_pl_fibras(model, beff)
    Ma = v["Wply"] * fy / GM0                       # M_a,pl,Rd: acero solo
    if eta >= 1.0:
        M_Rd = Mpl; conexion_tipo = "total"
    else:
        # interpolacion lineal (EC4 §6.2.1.3): M_Rd = Ma + eta·(Mpl - Ma)
        M_Rd = Ma + eta * (Mpl - Ma); conexion_tipo = "parcial"
    M_Ed = results["mixta"]["ELU"]["M_max"]
    out["flexion_mixta"] = {"M_pl_Rd_total_kNm": Mpl / 1e3, "M_a_Rd_kNm": Ma / 1e3,
                            "M_Rd_kNm": M_Rd / 1e3, "M_Ed_kNm": M_Ed / 1e3,
                            "PNA_desde_base_mm": y_na * 1e3, "PNA_zona": zona,
                            "grado_conexion": eta, "tipo_conexion": conexion_tipo,
                            "u": M_Ed / M_Rd, "ok": bool(M_Ed <= M_Rd)}

    # Cortante vertical
    Vpl = v["Avz"] * fy / (math.sqrt(3) * GM0)
    V_Ed = results["mixta"]["ELU"]["V_max"]
    out["cortante"] = {"Vpl_Rd_kN": Vpl / 1e3, "V_Ed_kN": V_Ed / 1e3,
                       "u": V_Ed / Vpl, "ok": bool(V_Ed <= Vpl)}

    # Fase de construccion (acero solo)
    Mc_Rd = v["Wply"] * fy / GM0
    M_Ed_c = results["construccion"]["ELU"]["M_max"]
    out["construccion"] = {"Mc_Rd_kNm": Mc_Rd / 1e3, "M_Ed_kNm": M_Ed_c / 1e3,
                           "u": M_Ed_c / Mc_Rd, "ok": bool(M_Ed_c <= Mc_Rd),
                           "nota": "verificar pandeo lateral (PLT) si el ala comprimida no esta arriostrada por la chapa"}

    # Flecha
    out["flecha"] = flecha(model, results, beff)

    oks = [out["flexion_mixta"]["ok"], out["cortante"]["ok"], out["conexion"]["ok"],
           out["construccion"]["ok"], out["flecha"]["ok_total"], out["flecha"]["ok_activa"]]
    out["veredicto"] = "CUMPLE" if all(oks) else "REVISAR"
    return out


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    proj = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "proyecto-viga-mixta")
    model = json.load(open(os.path.join(proj, "modelo_neutro.json"), encoding="utf-8"))
    results = json.load(open(os.path.join(proj, "resultados.json"), encoding="utf-8"))
    out = verificar(model, results)
    json.dump(out, open(os.path.join(proj, "verificacion.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    fm = out["flexion_mixta"]; cv = out["cortante"]; cx = out["conexion"]; cc = out["construccion"]; fl = out["flecha"]
    print("VIGA MIXTA %s -> %s  (b_eff=%.2f m)" % (out["info"]["perfil"], out["veredicto"], out["b_eff_m"]))
    print("  FLEXION mixta (%s): M_Ed=%.0f / M_Rd=%.0f kNm (%.0f%%)  [M_pl,total=%.0f, M_a=%.0f]  PNA %s a %.0f mm  %s"
          % (fm["tipo_conexion"], fm["M_Ed_kNm"], fm["M_Rd_kNm"], fm["u"] * 100, fm["M_pl_Rd_total_kNm"],
             fm["M_a_Rd_kNm"], fm["PNA_zona"], fm["PNA_desde_base_mm"], "OK" if fm["ok"] else "NO"))
    print("  CORTANTE: V_Ed=%.0f / Vpl,Rd=%.0f kN (%.0f%%)  %s" % (
        cv["V_Ed_kN"], cv["Vpl_Rd_kN"], cv["u"] * 100, "OK" if cv["ok"] else "NO"))
    print("  CONEXION: PRd=%.1f kN/perno (kt=%.2f)  Nc=%.0f kN  N_f=%.1f  n_disp=%.1f  grado=%.2f (min %.2f)  %s" % (
        cx["PRd_kN"], cx["kt"], cx["Nc_kN"], cx["Nf_total"], cx["n_disp_media_luz"], cx["grado_eta"],
        cx["eta_min"], "OK" if cx["ok"] else "NO"))
    print("  CONSTRUCCION: M_Ed=%.0f / Mc,Rd=%.0f kNm (%.0f%%)  %s" % (
        cc["M_Ed_kNm"], cc["Mc_Rd_kNm"], cc["u"] * 100, "OK" if cc["ok"] else "NO"))
    print("  FLECHA: total=%.1f/%.1f mm (%.0f%%)  uso=%.1f/%.1f mm (%.0f%%)  [n0=%.1f nL=%.1f]" % (
        fl["d_total_mm"], fl["lim_total_mm"], fl["u_total"] * 100, fl["d_activa_mm"],
        fl["lim_activa_mm"], fl["u_activa"] * 100, fl["n0"], fl["nL"]))
