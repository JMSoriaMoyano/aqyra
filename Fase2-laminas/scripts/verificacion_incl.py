"""
Verificacion EC2 del ELEMENTO PLANO INCLINADO (cubierta / forjado inclinado):
  - Flexion (armadura inferior por direccion) + cuantias
  - Flecha normal al faldon (ELS) frente a L/300 y L/500
  - Esfuerzos de MEMBRANA (n_x, n_y): comprobacion a compresion del hormigon
  - Fisuracion (EC2 7.3) en vano
Incluye validacion del plano inclinado (invariancia de rotacion + equilibrio).
"""
import sys
import json
import math
import validate_incl
from verificacion_ec2 import armado_direccion, _to_native
import ec2_punz_fis

GC = 1.50
C_NOM = 0.025
PHI = 0.012
LIM_TOTAL, LIM_ACTIVA = 300.0, 500.0


def verificar(model, results):
    info = results["info"]
    mp = model["materiales"][info["material"]]
    fck = mp["fck"]; fctm = mp["fctm"]; Ecm = mp["E"]; fcd = fck / GC
    t = info["espesor"]
    d_x = t - C_NOM - PHI / 2
    d_y = t - C_NOM - PHI - PHI / 2

    out = {"validacion": None, "losa": {}, "membrana": {}, "fisuracion": {},
           "equilibrio": results["equilibrio"], "info": info}
    vr = validate_incl.validar()
    out["validacion"] = {"invariancia_rotacion": vr,
                         "equilibrio_pct": results["equilibrio"]["error_pct"]}

    quads = results["losa"]["ELU"]["quads"]
    mx_sag = max(max((-q["Mx"] for q in quads), default=0.0), 0.0)
    my_sag = max(max((-q["My"] for q in quads), default=0.0), 0.0)
    losa = {"t": t, "d_x_mm": d_x * 1e3, "d_y_mm": d_y * 1e3, "fck_MPa": fck / 1e6,
            "recubrimiento_mm": C_NOM * 1e3, "phi_mm": PHI * 1e3}
    losa["x_inferior"] = armado_direccion(mx_sag, d_x, fcd, fctm, t)
    losa["y_inferior"] = armado_direccion(my_sag, d_y, fcd, fctm, t)

    # flecha normal al faldon (vano = Lu)
    span = info["Lu"]
    f_tot = max((abs(p["dn"]) for p in results["losa"]["ELS_car"]["deformada"]), default=0.0)
    f_act = max((abs(p["dn"]) for p in results["losa"]["ELS_act"]["deformada"]), default=0.0)
    losa["flecha"] = {"L_m": span, "f_total_mm": f_tot * 1e3, "lim_total_mm": span / LIM_TOTAL * 1e3,
                      "u_total": f_tot / (span / LIM_TOTAL), "ok_total": f_tot <= span / LIM_TOTAL,
                      "f_activa_mm": f_act * 1e3, "lim_activa_mm": span / LIM_ACTIVA * 1e3,
                      "u_activa": f_act / (span / LIM_ACTIVA), "ok_activa": f_act <= span / LIM_ACTIVA}
    out["losa"] = losa

    # membrana (compresion del hormigon, por metro de ancho)
    nx = min(q["nx"] for q in quads); ny = min(q["ny"] for q in quads)  # mas negativos (compresion)
    nx_t = max(q["nx"] for q in quads); ny_t = max(q["ny"] for q in quads)
    n_comp = min(nx, ny)            # compresion gobernante (N/m)
    n_trac = max(nx_t, ny_t)        # traccion gobernante (N/m)
    nRd_comp = fcd * t * 1.0        # capacidad a compresion bruta (N/m)
    out["membrana"] = {
        "n_comp_kN_m": n_comp / 1e3, "n_trac_kN_m": n_trac / 1e3,
        "nRd_comp_kN_m": nRd_comp / 1e3, "u_comp": abs(n_comp) / nRd_comp,
        "ok_comp": abs(n_comp) <= nRd_comp,
        "nota": "compresion de membrana del faldon (empuje a aleros); interaccion N-M conservadora aparte",
    }

    # fisuracion en vano (cuasipermanente)
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
    mp_ = sys.argv[1] if len(sys.argv) > 1 else "proyecto-cubierta/modelo_neutro.json"
    rp_ = sys.argv[2] if len(sys.argv) > 2 else "proyecto-cubierta/resultados.json"
    op_ = sys.argv[3] if len(sys.argv) > 3 else "proyecto-cubierta/verificacion.json"
    model = json.load(open(mp_, encoding="utf-8"))
    results = json.load(open(rp_, encoding="utf-8"))
    out = verificar(model, results)
    json.dump(out, open(op_, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    v = out["validacion"]
    print("VALIDACION: invariancia", "OK" if v["invariancia_rotacion"]["ok"] else "NO",
          f"(err {v['invariancia_rotacion']['err_Mx']*100:.2f}%)  equil {v['equilibrio_pct']:.2f}%")
    L = out["losa"]
    print(f"\nCUBIERTA t={L['t']*1e3:.0f}mm  angulo={out['info']['angulo']}deg")
    for k in ("x_inferior", "y_inferior"):
        a = L[k]
        print(f"  {k:11s}: m={a['m_Ed_kNm_m']:5.1f}  As={a['As_dim_cm2_m']:5.2f} cm²/m -> {a['armado']}")
    fl = L["flecha"]
    print(f"  flecha normal {fl['f_total_mm']:.2f}/{fl['lim_total_mm']:.1f}mm ({fl['u_total']*100:.0f}%)")
    me = out["membrana"]
    print(f"  membrana: comp={me['n_comp_kN_m']:.1f} kN/m (uRd={me['u_comp']*100:.1f}%)  trac={me['n_trac_kN_m']:.1f} kN/m")
    fi = out["fisuracion"]
    print(f"  fisuracion wk={fi['wk_mm']:.3f}mm ({fi['u']*100:.0f}%)  {'OK' if fi['ok'] else 'NO'}")
