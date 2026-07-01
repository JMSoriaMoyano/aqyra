"""
Verificacion EC3 (EN 1993-1-1) con Anejo Nacional Espana, nivel Fase 1 (barras).

Comprobaciones por barra (envolvente ELU):
  - Resistencia a flexion:   Mc,Rd = Wpl,y * fy / gM0           (Clase 1/2)
  - Resistencia a cortante:  Vpl,Rd = Avz * fy / (sqrt(3)*gM0)
  - Resistencia axil:        Nc,Rd = A * fy / gM0
  - Pandeo por flexion (pilares): Nb,Rd = chi * A * fy / gM1   (curva 'b', eje fuerte, Lcr=L)
  - Interaccion N+M (lineal, conservadora): N/NcRd + M/McRd <= 1
Comprobaciones de servicio (ELS):
  - Flecha total  <= L/300  (ELS caracteristica)
  - Flecha activa <= L/500  (ELS, proxy variable)

Incluye AUTODIAGNOSTICO: valida el solver contra la solucion cerrada de una
viga biapoyada (M=qL^2/8, V=qL/2, f=5qL^4/384EI) antes de dar resultados.
"""
import sys
import json
import math


def _to_native(o):
    """Convierte tipos numpy a nativos de Python para serializacion JSON."""
    if isinstance(o, dict):
        return {k: _to_native(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_to_native(v) for v in o]
    if hasattr(o, "item"):
        try:
            return o.item()
        except Exception:
            return o
    return o

GM0 = 1.00
GM1 = 1.00
LIM_TOTAL = 300.0   # L/300
LIM_ACTIVA = 500.0  # L/500


# ---------------------------------------------------------------------------
# Autodiagnostico del solver (certificado de correccion)
# ---------------------------------------------------------------------------
def autodiagnostico():
    from Pynite import FEModel3D
    L, q = 6.0, 20e3
    E, G, nu = 210e9, 80.77e9, 0.3
    A, Imaj, Imin, J = 6.261e-3, 1.177e-4, 7.881e-6, 2.815e-7
    m = FEModel3D()
    m.add_material("S", E, G, nu, 7850.0)
    m.add_section("S", A, Imin, Imaj, J)          # Iz = mayor
    m.add_node("A", 0, 0, 0); m.add_node("B", L, 0, 0)
    m.def_support("A", True, True, True, True, True, False)
    m.def_support("B", False, True, True, True, True, False)
    m.add_member("V", "A", "B", "S", "S")
    m.add_member_dist_load("V", "FY", -q, -q, case="Q")
    m.add_load_combo("c", {"Q": 1.0})
    m.analyze_linear()
    mb = m.members["V"]
    M = -mb.min_moment("Mz", "c")
    V = mb.max_shear("Fy", "c")
    fmid = -mb.min_deflection("dy", "c")
    M_t, V_t, f_t = q * L**2 / 8, q * L / 2, 5 * q * L**4 / (384 * E * Imaj)
    checks = {
        "M (kN·m)": (M / 1e3, M_t / 1e3, abs(M - M_t) / M_t),
        "V (kN)": (V / 1e3, V_t / 1e3, abs(V - V_t) / V_t),
        "flecha (mm)": (fmid * 1e3, f_t * 1e3, abs(fmid - f_t) / f_t),
    }
    ok = all(err < 0.01 for _, _, err in checks.values())
    return ok, checks


# ---------------------------------------------------------------------------
def verificar(model, results):
    fy_mat = {name: mp["fy"] for name, mp in model["materiales"].items()}
    out = {"autodiagnostico": None, "barras": {}}

    ok, checks = autodiagnostico()
    out["autodiagnostico"] = {"valido": ok, "checks": checks}

    for bid, b in model["barras"].items():
        sec = model["secciones"][b["seccion"]]
        fy = fy_mat[b["material"]]
        A, Wpl, Avz = sec["A"], sec["Wply"], sec["Avz"]
        Imaj = sec["Iy"]  # eje fuerte
        L = results["longitudes"][bid]
        elu = results["barras"][bid]["ELU"]

        N_Ed = max(abs(elu["N_i"]), abs(elu["N_j"]))
        V_Ed = max(abs(elu["V_max"]), abs(elu["V_min"]))
        M_Ed = max(abs(elu["M_max"]), abs(elu["M_min"]))
        compresion = (elu["N_i"] < 0) or (elu["N_j"] < 0)

        # Resistencias de seccion
        Mc_Rd = Wpl * fy / GM0
        Vpl_Rd = Avz * fy / (math.sqrt(3) * GM0)
        Nc_Rd = A * fy / GM0

        # Pandeo por flexion (eje fuerte, Lcr=L, curva b)
        eps = math.sqrt(235e6 / fy)
        lam1 = 93.9 * eps
        i_maj = math.sqrt(Imaj / A)
        lam_bar = (L / i_maj) / lam1
        alpha = 0.34  # curva b
        phi = 0.5 * (1 + alpha * (lam_bar - 0.2) + lam_bar**2)
        chi = 1.0 / (phi + math.sqrt(phi**2 - lam_bar**2)) if phi > 0 else 1.0
        chi = min(chi, 1.0)
        Nb_Rd = chi * A * fy / GM1

        u_M = M_Ed / Mc_Rd
        u_V = V_Ed / Vpl_Rd
        u_N = N_Ed / Nc_Rd
        u_buck = (N_Ed / Nb_Rd) if compresion else 0.0
        u_NM = u_N + u_M  # interaccion lineal conservadora

        # Servicio: flechas
        f_total = abs(min(results["barras"][bid]["ELS_car"]["defl"]))
        f_activa = abs(min(results["barras"][bid]["ELS_act"]["defl"]))
        lim_total = L / LIM_TOTAL
        lim_activa = L / LIM_ACTIVA
        u_ftot = f_total / lim_total
        u_fact = f_activa / lim_activa

        comprob = {
            "Flexion Mc,Rd": {"Ed": M_Ed, "Rd": Mc_Rd, "u": u_M, "ok": u_M <= 1.0,
                              "art": "EC3 6.2.5"},
            "Cortante Vpl,Rd": {"Ed": V_Ed, "Rd": Vpl_Rd, "u": u_V, "ok": u_V <= 1.0,
                                "art": "EC3 6.2.6"},
            "Axil Nc,Rd": {"Ed": N_Ed, "Rd": Nc_Rd, "u": u_N, "ok": u_N <= 1.0,
                           "art": "EC3 6.2.4"},
            "Interaccion N+M": {"Ed": None, "Rd": None, "u": u_NM, "ok": u_NM <= 1.0,
                                "art": "EC3 6.2.1 (lineal, conservadora)"},
        }
        if compresion:
            comprob["Pandeo Nb,Rd"] = {"Ed": N_Ed, "Rd": Nb_Rd, "u": u_buck,
                                       "ok": u_buck <= 1.0, "art": "EC3 6.3.1",
                                       "lambda_bar": lam_bar, "chi": chi}
        comprob["Flecha total L/300"] = {"Ed": f_total, "Rd": lim_total, "u": u_ftot,
                                         "ok": u_ftot <= 1.0, "art": "EC0 7.4 / criterio despacho"}
        comprob["Flecha activa L/500"] = {"Ed": f_activa, "Rd": lim_activa, "u": u_fact,
                                          "ok": u_fact <= 1.0, "art": "criterio despacho"}

        u_max = max(c["u"] for c in comprob.values())
        out["barras"][bid] = {
            "seccion": b["seccion"], "material": b["material"], "tipo": b["tipo"],
            "L": L, "fy": fy, "compresion": compresion,
            "comprobaciones": comprob, "aprovechamiento_max": u_max,
            "veredicto": "CUMPLE" if u_max <= 1.0 else "NO CUMPLE",
        }
    return _to_native(out)


if __name__ == "__main__":
    model_path = sys.argv[1] if len(sys.argv) > 1 else "proyecto-demo/modelo_neutro.json"
    res_path = sys.argv[2] if len(sys.argv) > 2 else "proyecto-demo/resultados.json"
    out_path = sys.argv[3] if len(sys.argv) > 3 else "proyecto-demo/verificacion.json"
    with open(model_path, encoding="utf-8") as fh:
        model = json.load(fh)
    with open(res_path, encoding="utf-8") as fh:
        results = json.load(fh)
    out = verificar(model, results)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)

    ad = out["autodiagnostico"]
    print("AUTODIAGNOSTICO solver:", "OK" if ad["valido"] else "FALLO")
    for k, (val, teor, err) in ad["checks"].items():
        print(f"   {k}: calc={val:.3f}  teor={teor:.3f}  err={err*100:.3f}%")
    print("\n=== VERIFICACION EC3 (envolvente ELU/ELS) ===")
    for bid, r in out["barras"].items():
        print(f"\n {bid} ({r['tipo']}, {r['seccion']}, {r['material']})  ->  "
              f"{r['veredicto']}  (aprov. max {r['aprovechamiento_max']*100:.1f}%)")
        for nombre, c in r["comprobaciones"].items():
            print(f"    {nombre:22s} u={c['u']*100:6.1f}%  {'OK' if c['ok'] else 'NO'}  [{c['art']}]")
