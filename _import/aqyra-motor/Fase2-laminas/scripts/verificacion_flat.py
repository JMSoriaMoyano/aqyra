"""
Verificacion EC2 de la LOSA PLANA sobre pilares:
  - Flexion (armadura inferior de vano y superior sobre pilares) + cuantias
  - Flecha (ELS) frente a L/300 y L/500
  - PUNZONAMIENTO (EC2 6.4) en cada tipo de pilar (interior/borde/esquina)
      y, si no cumple, DIMENSIONAMIENTO de la solucion (canto / armadura / capitel)
  - FISURACION (EC2 7.3) en vano (cuasipermanente)

Incluye autodiagnostico de los elementos placa (Timoshenko).
"""
import sys
import json
import math
import plate_validation
import ec2_punz_fis
from verificacion_ec2 import armado_direccion, _to_native

GC, GS = 1.50, 1.15
FYK = 500e6
C_NOM = 0.030    # recubrimiento (m)
PHI = 0.016      # diametro supuesto (m)
LIM_TOTAL, LIM_ACTIVA = 300.0, 500.0


def _pctl(vals, q):
    v = sorted(vals)
    if not v:
        return 0.0
    i = min(len(v) - 1, max(0, int(q * (len(v) - 1))))
    return v[i]


def verificar(model, results):
    info = results["info"]
    mp = model["materiales"][info["material"]]
    fck = mp["fck"]; fctm = mp["fctm"]; Ecm = mp["E"]; fcd = fck / GC
    t = info["espesor"]
    d_x = t - C_NOM - PHI / 2
    d_y = t - C_NOM - PHI - PHI / 2

    out = {"autodiagnostico_placa": None, "losa": {}, "punzonamiento": {},
           "fisuracion": {}, "equilibrio": results["equilibrio"]}
    okp, chk = plate_validation.validar()
    out["autodiagnostico_placa"] = {"valido": okp, "checks": chk}

    quads = results["losa"]["ELU"]["quads"]
    # sagging (vano, traccion inferior) = max(-M); hogging (pilares, superior) = max(+M)
    # el hogging se acota con percentil 97 para evitar la singularidad sobre el pilar
    mx_sag = max(max((-q["Mx"] for q in quads), default=0.0), 0.0)
    my_sag = max(max((-q["My"] for q in quads), default=0.0), 0.0)
    mx_hog = max(_pctl([q["Mx"] for q in quads if q["Mx"] > 0], 0.97), 0.0)
    my_hog = max(_pctl([q["My"] for q in quads if q["My"] > 0], 0.97), 0.0)

    losa = {"t": t, "d_x_mm": d_x * 1e3, "d_y_mm": d_y * 1e3, "fck_MPa": fck / 1e6,
            "recubrimiento_mm": C_NOM * 1e3, "phi_mm": PHI * 1e3}
    losa["x_inferior"] = armado_direccion(mx_sag, d_x, fcd, fctm, t)
    losa["y_inferior"] = armado_direccion(my_sag, d_y, fcd, fctm, t)
    losa["x_superior"] = armado_direccion(mx_hog, d_x, fcd, fctm, t)
    losa["y_superior"] = armado_direccion(my_hog, d_y, fcd, fctm, t)

    # flecha (vano = separacion entre pilares)
    span = info["W"] / 2 if info["W"] == info["H"] else min(info["W"], info["H"])
    f_tot = max((abs(p["dz"]) for p in results["losa"]["ELS_car"]["deformada"]), default=0.0)
    f_act = max((abs(p["dz"]) for p in results["losa"]["ELS_act"]["deformada"]), default=0.0)
    losa["flecha"] = {"L_m": span, "f_total_mm": f_tot * 1e3, "lim_total_mm": span / LIM_TOTAL * 1e3,
                      "u_total": f_tot / (span / LIM_TOTAL), "ok_total": f_tot <= span / LIM_TOTAL,
                      "f_activa_mm": f_act * 1e3, "lim_activa_mm": span / LIM_ACTIVA * 1e3,
                      "u_activa": f_act / (span / LIM_ACTIVA), "ok_activa": f_act <= span / LIM_ACTIVA}
    out["losa"] = losa

    # cuantia de traccion para punzonamiento (armadura superior sobre pilares)
    As_x = losa["x_superior"]["As_prov_cm2_m"] * 1e-4
    As_y = losa["y_superior"]["As_prov_cm2_m"] * 1e-4
    As_med = math.sqrt(As_x * As_y)
    d_med = (d_x + d_y) / 2
    rho_l = math.sqrt((As_x / d_x) * (As_y / d_y))

    # punzonamiento por tipo de pilar (toma el mas cargado de cada tipo)
    for pos in ("interior", "edge", "corner"):
        cols = [p for p in results["pilares"].values() if p["posicion"] == pos]
        if not cols:
            continue
        p = max(cols, key=lambda c: abs(c["Rz"]["ELU"]))
        V = abs(p["Rz"]["ELU"]); lado = p["lado"]
        chkp = ec2_punz_fis.punzonamiento(V, lado, lado, d_med, fck, rho_l, posicion=pos)
        entry = {"check": chkp, "V_Ed_kN": V / 1e3, "lado_mm": lado * 1e3}
        if not chkp["ok"]:
            entry["dimensionado"] = ec2_punz_fis.dimensionar_punzonamiento(
                V, lado, lado, t, C_NOM, PHI, fck, As_med, posicion=pos)
        out["punzonamiento"][pos] = entry

    # fisuracion en vano (cuasipermanente), direccion gobernante
    qcp = results["losa"]["ELS_cp"]["quads"]
    mx_cp = max(max((-q["Mx"] for q in qcp), default=0.0), 0.0)
    my_cp = max(max((-q["My"] for q in qcp), default=0.0), 0.0)
    if my_cp >= mx_cp:
        M_cp, As_d, d_d = my_cp, losa["y_inferior"]["As_prov_cm2_m"] * 1e-4, d_y
    else:
        M_cp, As_d, d_d = mx_cp, losa["x_inferior"]["As_prov_cm2_m"] * 1e-4, d_x
    out["fisuracion"] = ec2_punz_fis.fisuracion(M_cp, As_d, d_d, t, C_NOM, PHI, fctm, Ecm)

    return _to_native(out)


if __name__ == "__main__":
    mp_ = sys.argv[1] if len(sys.argv) > 1 else "proyecto-losa-plana/modelo_neutro.json"
    rp_ = sys.argv[2] if len(sys.argv) > 2 else "proyecto-losa-plana/resultados.json"
    op_ = sys.argv[3] if len(sys.argv) > 3 else "proyecto-losa-plana/verificacion.json"
    model = json.load(open(mp_, encoding="utf-8"))
    results = json.load(open(rp_, encoding="utf-8"))
    out = verificar(model, results)
    json.dump(out, open(op_, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    print("PLACA:", "OK" if out["autodiagnostico_placa"]["valido"] else "FALLO")
    L = out["losa"]
    print(f"\nLOSA t={L['t']*1e3:.0f}mm  d_x={L['d_x_mm']:.0f} d_y={L['d_y_mm']:.0f}mm")
    for k in ("x_inferior", "y_inferior", "x_superior", "y_superior"):
        a = L[k]
        print(f"  {k:11s}: m={a['m_Ed_kNm_m']:6.1f}  As={a['As_dim_cm2_m']:5.2f} cm²/m -> {a['armado']}")
    fl = L["flecha"]
    print(f"  flecha total {fl['f_total_mm']:.2f}/{fl['lim_total_mm']:.1f}mm ({fl['u_total']*100:.0f}%)")
    print("\nPUNZONAMIENTO:")
    for pos, e in out["punzonamiento"].items():
        c = e["check"]
        print(f"  {pos:8s} V_Ed={e['V_Ed_kN']:6.1f} kN  vEd/vRdc={c['u_vRdc']*100:5.0f}%  "
              f"{'OK' if c['ok'] else 'NO -> dimensionar'}")
        if "dimensionado" in e:
            d = e["dimensionado"]
            print(f"           -> canto min={d['canto_minimo']['h_min_mm']}mm  "
                  f"armadura Asw/sr={d['armadura']['asw_sr_cm2_m']:.1f} cm²/m  "
                  f"capitel={d['capitel']['lado_capitel_mm']}mm")
    fi = out["fisuracion"]
    print(f"\nFISURACION vano: wk={fi['wk_mm']:.3f}mm wmax={fi['wmax_mm']:.2f} ({fi['u']*100:.0f}%)  "
          f"{'OK' if fi['ok'] else 'NO'}")
    eq = out["equilibrio"]
    print(f"EQUILIBRIO ELU error={eq['error_pct']:.2f}%")
