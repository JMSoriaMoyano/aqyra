"""
Verificacion de la LOSA DE CIMENTACION (raft).

EC7 (geotecnia):
  - Presion del terreno (ELU + peso propio) <= Rd ; sin despegue (p_min >= 0).
  - Asiento diferencial y distorsion angular entre pilares <= limite (1/500) [criterio].
EC2 (hormigon), por metro de ancho y en dos direcciones:
  - Flexion INFERIOR (sagging, vanos) y SUPERIOR (hogging, sobre pilares) -> armado.
  - Punzonamiento (EC2 6.4) en cada pilar segun su posicion; dimensionado si falla.
SI (N, m, Pa).
"""
import sys
import os
import json
import math
import ec2_punz_fis

GC, GS = 1.50, 1.15
FYK = 500e6
FYD = FYK / GS
G_ACC = 9.81
C_NOM = 0.050        # recubrimiento losa de cimentacion (m)
PHI = 0.020          # diametro supuesto (m)
MU_LIM = 0.295
DIST_LIM = 1 / 500   # distorsion angular admisible [criterio/EC7]


def armado(m_Ed, d, fcd, fctm, t, b=1.0):
    m_Ed = abs(m_Ed)
    mu = m_Ed / (b * d ** 2 * fcd) if d > 0 else 9.99
    z = d * (0.5 + math.sqrt(max(0.25 - min(mu, 0.32) / 2, 0.0)))
    As = m_Ed / (z * FYD) if m_Ed > 0 else 0.0
    As_min = max(0.26 * fctm / FYK, 0.0013) * b * d
    As_max = 0.04 * t * b
    As_prov = max(As, As_min)
    return {"m_Ed_kNm_m": m_Ed / 1e3, "mu": mu, "As_cm2_m": As * 1e4,
            "As_min_cm2_m": As_min * 1e4, "As_prov_cm2_m": As_prov * 1e4,
            "ok": bool(mu <= MU_LIM and As_prov <= As_max)}


def verificar(model, results):
    info = results["info"]
    mp = model["materiales"][info["material"]]
    fck = mp["fck"]; fctm = mp["fctm"]; fcd = fck / GC
    t = info["espesor"]; BX = info["BX"]; LY = info["LY"]; ks = info["ks"]; Rd = info["Rd"]
    rho_c = mp["rho"]
    d_x = t - C_NOM - PHI / 2
    d_y = t - C_NOM - PHI - PHI / 2
    d_med = (d_x + d_y) / 2

    out = {"info": info, "equilibrio": results["equilibrio"]}

    # --- EC7: presion del terreno (ELU) + peso propio ---
    pres = [p["p"] for p in results["losa"]["ELU"]["presion"]]
    pp_self = GC / GC * 0.0  # (placeholder)
    pp_self = 1.35 * t * rho_c * G_ACC      # peso propio mayorado (Pa)
    p_max = max(pres) + pp_self
    p_min = min(pres) + pp_self
    out["geotecnia"] = {
        "p_max_kPa": p_max / 1e3, "p_min_kPa": p_min / 1e3, "Rd_kPa": Rd / 1e3,
        "peso_propio_kPa": pp_self / 1e3, "u_Rd": p_max / Rd,
        "ok_Rd": bool(p_max <= Rd), "ok_sin_despegue": bool(p_min >= -1e-6)}

    # --- EC7: asiento diferencial / distorsion angular ---
    # distorsion = asiento_dif / separacion minima entre pilares
    xs = sorted(set(round(p["x"], 3) for p in info["pilares"]))
    ys = sorted(set(round(p["y"], 3) for p in info["pilares"]))
    sep_min = min([xs[i + 1] - xs[i] for i in range(len(xs) - 1)] +
                  [ys[i + 1] - ys[i] for i in range(len(ys) - 1)] + [1e9])
    dist = (info["asiento_dif_mm"] / 1e3) / sep_min if sep_min > 0 else 0.0
    out["asientos"] = {
        "asiento_max_mm": info["asiento_max_mm"], "asiento_min_mm": info["asiento_min_mm"],
        "asiento_dif_mm": info["asiento_dif_mm"], "sep_min_m": sep_min,
        "distorsion": dist, "distorsion_lim": DIST_LIM,
        "ok": bool(dist <= DIST_LIM)}

    # --- EC2 flexion: sagging (inferior) y hogging (superior), x e y ---
    # El pico bajo el pilar (carga puntual) es una SINGULARIDAD: se toma el momento
    # de diseno en la SECCION CRITICA (fuera de la huella + ~0.5 d del pilar).
    quads = results["losa"]["ELU"]["quads"]

    def fuera_pilar(q):
        for pil in info["pilares"]:
            r = pil["lado"] / 2 + 0.5 * d_med
            if abs(q["x"] - pil["x"]) <= r and abs(q["y"] - pil["y"]) <= r:
                return False
        return True

    qd = [q for q in quads if fuera_pilar(q)] or quads
    mx_sag = max([-q["Mx"] for q in qd] + [0.0])
    mx_hog = max([q["Mx"] for q in qd] + [0.0])
    my_sag = max([-q["My"] for q in qd] + [0.0])
    my_hog = max([q["My"] for q in qd] + [0.0])
    out["flexion"] = {
        "d_x_mm": d_x * 1e3, "d_y_mm": d_y * 1e3,
        "x_inferior": armado(mx_sag, d_x, fcd, fctm, t),
        "x_superior": armado(mx_hog, d_x, fcd, fctm, t),
        "y_inferior": armado(my_sag, d_y, fcd, fctm, t),
        "y_superior": armado(my_hog, d_y, fcd, fctm, t)}
    # cuantia de traccion superior (gobierna punzonamiento sobre pilares)
    As_x = out["flexion"]["x_superior"]["As_prov_cm2_m"] * 1e-4
    As_y = out["flexion"]["y_superior"]["As_prov_cm2_m"] * 1e-4
    rho_l = math.sqrt((As_x / d_x) * (As_y / d_y))

    # --- EC2 punzonamiento por pilar ---
    punz = []
    p_med_field = (results["equilibrio"]["reaccion_suelo_ELU_kN"] * 1e3) / info["area"]  # presion media ELU
    for pil in info["pilares"]:
        c = pil["lado"]; pos = pil["pos"]
        N_ELU = 1.35 * pil["N_G_kN"] * 1e3 + 1.5 * pil["N_Q_kN"] * 1e3
        # descuento de la presion del terreno dentro del perimetro de control u1
        p_local = pil.get("p_local_ELU_kPa", p_med_field / 1e3) * 1e3
        A_within = c * c + 4 * c * (2 * d_med) + math.pi * (2 * d_med) ** 2
        V_net = N_ELU - p_local * A_within
        pz = ec2_punz_fis.punzonamiento(V_net, c, c, d_med, fck, rho_l, posicion=pos)
        pz["pilar"] = {"x": pil["x"], "y": pil["y"], "pos": pos,
                       "N_ELU_kN": N_ELU / 1e3, "V_net_kN": V_net / 1e3}
        if not pz["ok"]:
            pz["dimensionado"] = ec2_punz_fis.dimensionar_punzonamiento(
                V_net, c, c, t, C_NOM, PHI, fck, math.sqrt(As_x * As_y), posicion=pos)
        punz.append(pz)
    out["punzonamiento"] = punz
    out["punz_critico"] = max(punz, key=lambda r: r["u_vRdc"])

    geo_ok = out["geotecnia"]["ok_Rd"] and out["geotecnia"]["ok_sin_despegue"] and out["asientos"]["ok"]
    flex_ok = all(out["flexion"][k]["ok"] for k in ("x_inferior", "x_superior", "y_inferior", "y_superior"))
    punz_ok = all(pz["ok_vRdmax"] for pz in punz)   # u0 (biela) no superable; vRdc se puede armar
    out["veredicto"] = "CUMPLE" if (geo_ok and flex_ok and punz_ok) else "REVISAR"
    return out


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    proj = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "proyecto-losa-cimentacion")
    model = json.load(open(os.path.join(proj, "modelo_neutro.json"), encoding="utf-8"))
    results = json.load(open(os.path.join(proj, "resultados.json"), encoding="utf-8"))
    out = verificar(model, results)
    json.dump(out, open(os.path.join(proj, "verificacion.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)

    g = out["geotecnia"]; a = out["asientos"]; fx = out["flexion"]; pc = out["punz_critico"]
    print("LOSA DE CIMENTACION -> %s" % out["veredicto"])
    print("  EC7 presion: p=[%.0f, %.0f] kPa (Rd=%.0f, +pp=%.0f)  u=%.2f  %s  despegue:%s"
          % (g["p_min_kPa"], g["p_max_kPa"], g["Rd_kPa"], g["peso_propio_kPa"], g["u_Rd"],
             "OK" if g["ok_Rd"] else "NO", "no" if g["ok_sin_despegue"] else "SI"))
    print("  EC7 asientos: max=%.2f min=%.2f dif=%.2f mm  distorsion=1/%.0f (lim 1/%.0f)  %s"
          % (a["asiento_max_mm"], a["asiento_min_mm"], a["asiento_dif_mm"],
             1 / a["distorsion"] if a["distorsion"] > 0 else 9999, 1 / a["distorsion_lim"],
             "OK" if a["ok"] else "NO"))
    print("  EC2 flexion (d_x=%.0f d_y=%.0f mm):" % (fx["d_x_mm"], fx["d_y_mm"]))
    for k in ("x_inferior", "x_superior", "y_inferior", "y_superior"):
        aa = fx[k]
        print("     %-11s m=%6.0f kNm/m  As=%5.1f cm2/m  %s" % (
            k, aa["m_Ed_kNm_m"], aa["As_prov_cm2_m"], "OK" if aa["ok"] else "NO"))
    print("  EC2 punzonamiento critico (%s, V_net=%.0f kN): vEd/vRdc=%.0f%%  vEd/vRdmax=%.0f%%  %s" % (
        pc["pilar"]["pos"], pc["pilar"]["V_net_kN"], pc["u_vRdc"] * 100, pc["u_vRdmax"] * 100,
        "OK" if pc["ok"] else ("ARMAR" if pc["ok_vRdmax"] else "NO (biela)")))
