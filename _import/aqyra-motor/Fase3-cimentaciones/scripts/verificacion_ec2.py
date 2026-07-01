"""
Verificacion EC2 (EN 1992-1-1) de la LOSA + resumen EC3 (EN 1993) de las barras.
Anejo Nacional Espana.

LOSA (por direccion x e y, ancho b = 1 m):
  - Momento de diseno m_Ed (envolvente ELU) de los esfuerzos de placa.
  - mu = m_Ed / (b d^2 fcd);  comprobacion mu <= mu_lim (sin armadura de compresion).
  - As = m_Ed / (z fyd), con z = 0.9 d (brazo simplificado).
  - As,min = max(0.26 fctm/fyk, 0.0013) b d   (EC2 9.2.1.1 / 9.3.1.1)
  - As,max = 0.04 Ac
  - Propuesta de armado (diametro y separacion).
  - Flecha: max |dz| (ELS) frente a L/300 (total) y L/500 (activa) [criterio despacho].

BARRAS: comprobacion EC3 concisa de la viga y el pilar mas solicitados
  (Mc,Rd, Vpl,Rd, Nb,Rd) -- detalle completo en el flujo de la Fase 1.

Incluye autodiagnostico de los elementos placa (Timoshenko).
"""
import sys
import json
import math
import plate_validation
import ec2_punz_fis

# Materiales
GC, GS = 1.50, 1.15
FYK = 500e6          # B500S
FYD = FYK / GS

# Recubrimiento y diametro supuestos
C_NOM = 0.025        # m (clase exposicion XC1, [confirmar por proyecto])
PHI = 0.012          # m (barra supuesta 12 mm)
MU_LIM = 0.295       # limite para armado simple (ductilidad)
LIM_TOTAL, LIM_ACTIVA = 300.0, 500.0


def _to_native(o):
    if isinstance(o, dict):
        return {k: _to_native(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_to_native(v) for v in o]
    return o.item() if hasattr(o, "item") else o


def propon_armado(As_req):
    """Devuelve (phi_mm, sep_mm, As_prov_mm2) cubriendo As_req [m2/m]."""
    As_req_mm2 = As_req * 1e6  # mm2/m
    for phi in (10, 12, 16, 20):
        a1 = math.pi * (phi / 2) ** 2  # area de 1 barra mm2
        for sep in (300, 250, 200, 150, 125, 100):
            As_prov = a1 * 1000 / sep
            if As_prov >= As_req_mm2:
                return phi, sep, As_prov
    return 20, 100, math.pi * 100 * 1000 / 100


def armado_direccion(m_Ed, d, fcd, fctm, t):
    """Calcula armadura para un momento m_Ed [N·m/m] en una direccion."""
    b = 1.0
    mu = m_Ed / (b * d**2 * fcd)
    z = 0.9 * d
    As = m_Ed / (z * FYD)                       # m2/m
    As_min = max(0.26 * fctm / FYK, 0.0013) * b * d
    As_max = 0.04 * t * b
    As_dim = max(As, As_min)
    phi, sep, As_prov = propon_armado(As_dim)
    return {
        "m_Ed_kNm_m": m_Ed / 1e3, "mu": mu, "mu_ok": mu <= MU_LIM,
        "As_req_cm2_m": As * 1e4, "As_min_cm2_m": As_min * 1e4,
        "As_max_cm2_m": As_max * 1e4, "As_dim_cm2_m": As_dim * 1e4,
        "armado": f"φ{phi}/{sep}", "As_prov_cm2_m": As_prov / 100,
        "ok": As_dim <= As_max and mu <= MU_LIM,
    }


def verificar(model, results):
    info = results["info"]
    surf = model["superficies"][0]
    matc = model["materiales"][surf["material"]]
    fck = matc["fck"]; fctm = matc["fctm"]; fcd = fck / GC
    t = info["espesor"]
    d_x = t - C_NOM - PHI / 2          # capa exterior
    d_y = t - C_NOM - PHI - PHI / 2    # capa interior

    out = {"autodiagnostico_placa": None, "losa": {}, "barras": {},
           "equilibrio": results["equilibrio"]}

    ok_p, checks_p = plate_validation.validar()
    out["autodiagnostico_placa"] = {"valido": ok_p, "checks": checks_p}

    # --- momentos de placa (envolvente ELU) ---
    quads = results["losa"]["ELU"]["quads"]
    # Convencion PyNite: con carga gravitatoria (-Z) la flexion de campo sale
    # NEGATIVA y corresponde a SAGGING (traccion en cara INFERIOR). Se separan:
    #   sagging (inferior) = max(-M, 0)   ;   hogging (superior) = max(+M, 0)
    mx_sag = max((-q["Mx"] for q in quads), default=0.0); mx_sag = max(mx_sag, 0.0)
    mx_hog = max((q["Mx"] for q in quads), default=0.0); mx_hog = max(mx_hog, 0.0)
    my_sag = max((-q["My"] for q in quads), default=0.0); my_sag = max(my_sag, 0.0)
    my_hog = max((q["My"] for q in quads), default=0.0); my_hog = max(my_hog, 0.0)

    losa = {"t": t, "d_x_mm": d_x * 1e3, "d_y_mm": d_y * 1e3,
            "fck_MPa": fck / 1e6, "fcd_MPa": fcd / 1e6, "fyd_MPa": FYD / 1e6,
            "recubrimiento_mm": C_NOM * 1e3, "phi_mm": PHI * 1e3}
    losa["x_inferior"] = armado_direccion(mx_sag, d_x, fcd, fctm, t)
    losa["x_superior"] = armado_direccion(mx_hog, d_x, fcd, fctm, t)
    losa["y_inferior"] = armado_direccion(my_sag, d_y, fcd, fctm, t)
    losa["y_superior"] = armado_direccion(my_hog, d_y, fcd, fctm, t)

    # --- flecha ---
    L = min(info["W"], info["H"])
    f_total = max((abs(p["dz"]) for p in results["losa"]["ELS_car"]["deformada"]), default=0.0)
    f_activa = max((abs(p["dz"]) for p in results["losa"]["ELS_act"]["deformada"]), default=0.0)
    losa["flecha"] = {
        "L_m": L, "f_total_mm": f_total * 1e3, "lim_total_mm": L / LIM_TOTAL * 1e3,
        "u_total": f_total / (L / LIM_TOTAL), "ok_total": f_total <= L / LIM_TOTAL,
        "f_activa_mm": f_activa * 1e3, "lim_activa_mm": L / LIM_ACTIVA * 1e3,
        "u_activa": f_activa / (L / LIM_ACTIVA), "ok_activa": f_activa <= L / LIM_ACTIVA,
    }
    losa_ok = all(losa[k]["ok"] for k in ("x_inferior", "x_superior", "y_inferior", "y_superior")) \
        and losa["flecha"]["ok_total"] and losa["flecha"]["ok_activa"]
    losa["veredicto"] = "CUMPLE" if losa_ok else "NO CUMPLE"
    out["losa"] = losa

    # --- PUNZONAMIENTO (EC2 6.4) en pilar de esquina mas cargado ---
    # Hipotesis: se evalua la transferencia de carga losa->pilar en la esquina
    # (representativa de losa-pilar / nudo); el modelo apoya la losa en vigas.
    Ncol = max(abs(results["barras"][p]["ELU"]["N"]) for p in info["pilares"])
    c_col = model["secciones"][info["sec_pilar"]]["h"]  # lado ~ canto HEB (m)
    d_med = (d_x + d_y) / 2
    As_x = losa["x_inferior"]["As_prov_cm2_m"] * 1e-4  # cm2/m -> m2/m
    As_y = losa["y_inferior"]["As_prov_cm2_m"] * 1e-4
    rho_x = As_x / (1.0 * d_x); rho_y = As_y / (1.0 * d_y)
    rho_l = math.sqrt(rho_x * rho_y)
    out["punzonamiento"] = ec2_punz_fis.punzonamiento(
        Ncol, c_col, c_col, d_med, fck, rho_l, posicion="corner")

    # --- FISURACION (EC2 7.3) en la direccion mas solicitada (cuasipermanente) ---
    quads_cp = results["losa"]["ELS_cp"]["quads"]
    mx_cp = max((-q["Mx"] for q in quads_cp), default=0.0)
    my_cp = max((-q["My"] for q in quads_cp), default=0.0)
    Ecm = matc["E"]
    # direccion gobernante: la de mayor momento cuasipermanente
    if my_cp >= mx_cp:
        M_cp, As_d, d_d = my_cp, As_y, d_y
    else:
        M_cp, As_d, d_d = mx_cp, As_x, d_x
    out["fisuracion"] = ec2_punz_fis.fisuracion(
        M_cp, As_d, d_d, t, C_NOM, PHI, fctm, Ecm)

    # --- EC3 concisa de barras (viga y pilar mas solicitados) ---
    GM0 = 1.0
    secs = model["secciones"]
    fy = next(mp["fy"] for mp in model["materiales"].values() if mp.get("fy"))

    def ec3_barra(bid, sec, momento, cortante, axil):
        Wpl = sec["Wply"]; Avz = sec["Avz"]; A = sec["A"]
        Mc = Wpl * fy / GM0; Vpl = Avz * fy / (math.sqrt(3) * GM0); Nc = A * fy / GM0
        return {"M_Ed_kNm": momento / 1e3, "Mc_Rd_kNm": Mc / 1e3, "u_M": momento / Mc,
                "V_Ed_kN": cortante / 1e3, "Vpl_Rd_kN": Vpl / 1e3, "u_V": cortante / Vpl,
                "N_Ed_kN": axil / 1e3, "Nc_Rd_kN": Nc / 1e3, "u_N": abs(axil) / Nc,
                "u_max": max(momento / Mc, cortante / Vpl, abs(axil) / Nc),
                "seccion": None}

    # viga mas solicitada (max |My|)
    vig = max(info["vigas"], key=lambda b: max(abs(results["barras"][b]["ELU"]["My_max"]),
                                               abs(results["barras"][b]["ELU"]["My_min"])))
    rv = results["barras"][vig]["ELU"]
    M_v = max(abs(rv["My_max"]), abs(rv["My_min"]))
    V_v = max(abs(rv["Vz_max"]), abs(rv["Vz_min"]))
    ev = ec3_barra(vig, secs[info["sec_viga"]], M_v, V_v, abs(rv["N"]))
    ev["seccion"] = info["sec_viga"]; ev["id"] = vig
    out["barras"]["viga_critica"] = ev

    # pilar mas solicitado (max |N|)
    pil = max(info["pilares"], key=lambda b: abs(results["barras"][b]["ELU"]["N"]))
    rp = results["barras"][pil]["ELU"]
    M_p = max(abs(rp["My_max"]), abs(rp["My_min"]), abs(rp["Mz_max"]), abs(rp["Mz_min"]))
    V_p = max(abs(rp["Vz_max"]), abs(rp["Vz_min"]), abs(rp["Vy_max"]), abs(rp["Vy_min"]))
    ep = ec3_barra(pil, secs[info["sec_pilar"]], M_p, V_p, abs(rp["N"]))
    ep["seccion"] = info["sec_pilar"]; ep["id"] = pil
    out["barras"]["pilar_critico"] = ep

    return _to_native(out)


if __name__ == "__main__":
    mp = sys.argv[1] if len(sys.argv) > 1 else "proyecto-demo/modelo_neutro.json"
    rp = sys.argv[2] if len(sys.argv) > 2 else "proyecto-demo/resultados.json"
    op = sys.argv[3] if len(sys.argv) > 3 else "proyecto-demo/verificacion.json"
    model = json.load(open(mp, encoding="utf-8"))
    results = json.load(open(rp, encoding="utf-8"))
    out = verificar(model, results)
    json.dump(out, open(op, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    ad = out["autodiagnostico_placa"]
    print("AUTODIAGNOSTICO PLACA:", "OK" if ad["valido"] else "FALLO")
    L = out["losa"]
    print(f"\nLOSA t={L['t']*1e3:.0f}mm  d_x={L['d_x_mm']:.0f}  d_y={L['d_y_mm']:.0f}mm  "
          f"fck={L['fck_MPa']:.0f}  ->  {L['veredicto']}")
    for k in ("x_inferior", "x_superior", "y_inferior", "y_superior"):
        a = L[k]
        print(f"  {k:11s}: m={a['m_Ed_kNm_m']:6.1f} kN·m/m  As={a['As_dim_cm2_m']:5.2f} cm²/m  "
              f"-> {a['armado']} ({a['As_prov_cm2_m']:.2f})  mu={a['mu']:.3f}  {'OK' if a['ok'] else 'NO'}")
    fl = L["flecha"]
    print(f"  flecha total {fl['f_total_mm']:.2f}/{fl['lim_total_mm']:.1f}mm "
          f"({fl['u_total']*100:.0f}%)  activa {fl['f_activa_mm']:.2f}/{fl['lim_activa_mm']:.1f}mm "
          f"({fl['u_activa']*100:.0f}%)")
    print("\nBARRAS (EC3):")
    for k, b in out["barras"].items():
        print(f"  {k} [{b['id']} {b['seccion']}]: u_M={b['u_M']*100:.0f}% u_V={b['u_V']*100:.0f}% "
              f"u_N={b['u_N']*100:.0f}%  aprov={b['u_max']*100:.0f}%")
    pz = out["punzonamiento"]
    print(f"\nPUNZONAMIENTO (esquina, V_Ed={pz['V_Ed_kN']:.1f} kN): "
          f"vEd={pz['vEd_u1_MPa']:.3f} vRdc={pz['vRdc_MPa']:.3f} MPa  "
          f"u={pz['u_vRdc']*100:.0f}%  -> {'OK' if pz['ok'] else 'REQUIERE ARMADURA/canto'}")
    fi = out["fisuracion"]
    print(f"FISURACION (cuasiperm.): wk={fi['wk_mm']:.3f} mm  wmax={fi['wmax_mm']:.2f} mm  "
          f"u={fi['u']*100:.0f}%  sigma_s={fi['sigma_s_MPa']:.0f} MPa  -> {'OK' if fi['ok'] else 'NO'}")
    eq = out["equilibrio"]
    print(f"\nEQUILIBRIO ELU: aplicada={eq['aplicada_total_ELU_kN']:.1f} kN  "
          f"reaccion={eq['reaccion_ELU_kN']:.1f} kN  error={eq['error_pct']:.2f}%")
