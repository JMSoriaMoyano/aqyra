"""
Verificacion del PILOTE:
  - EC7: capacidad axil  N_Ed <= Rc,d
  - Lateral: flecha en cabeza <= limite de servicio
  - EC2: seccion circular bajo N + M (flexo-compresion); armadura minima EN 1536
SI (N, m, Pa).
"""
import sys
import json
import math
from combinaciones import GAMMA_G_SUP, GAMMA_Q_SUP

GC, GS = 1.50, 1.15
FYK = 500e6
FYD = FYK / GS
LIM_CABEZA = 0.010   # flecha de cabeza admisible (m) [criterio de servicio]


def verificar(model, results):
    p = model["pilote"]; mp = model["materiales"][p["material"]]
    D = p["D"]; fck = mp["fck"]; fcd = fck / GC
    Ac = math.pi * D ** 2 / 4
    cargas = model["cargas"]

    out = {"info": results["info"], "equilibrio": results["equilibrio"]}

    # --- EC7 axil ---
    N_Ed = GAMMA_G_SUP * cargas.get("G", {}).get("N", 0) + GAMMA_Q_SUP * cargas.get("Q", {}).get("N", 0)
    Rcd = results["capacidad_axil"]["Rc_d_kN"] * 1e3
    out["axil_ec7"] = {"N_Ed_kN": N_Ed / 1e3, "Rc_d_kN": Rcd / 1e3,
                       "Rs_k_kN": results["capacidad_axil"]["Rs_k_kN"],
                       "Rb_k_kN": results["capacidad_axil"]["Rb_k_kN"],
                       "u": N_Ed / Rcd, "ok": bool(N_Ed <= Rcd)}

    # --- lateral: flecha cabeza (ELS) y M de calculo (ELU) ---
    defl_els = results["pilote"].get("ELS_car", results["pilote"]["ELU"])["deformada"]
    dx_head = abs(defl_els[0]["dx"])
    M_Ed = max(abs(pt["M"]) for pt in results["pilote"]["ELU"]["esfuerzos"])
    V_Ed = max(abs(pt["V"]) for pt in results["pilote"]["ELU"]["esfuerzos"])
    out["lateral"] = {"flecha_cabeza_mm": dx_head * 1e3, "lim_mm": LIM_CABEZA * 1e3,
                      "u": dx_head / LIM_CABEZA, "ok": bool(dx_head <= LIM_CABEZA),
                      "M_Ed_kNm": M_Ed / 1e3, "V_Ed_kN": V_Ed / 1e3}

    # --- EC2 seccion circular bajo N + M ---
    e = M_Ed / N_Ed if N_Ed > 0 else 0.0
    # armadura minima de pilote (EN 1536): >= 0.5% Ac (para Ac <= 0.5 m2)
    As_min = 0.005 * Ac
    # capacidad a compresion (squash, conservadora con interaccion para e/D pequeno)
    N_Rd = Ac * fcd + As_min * FYD
    # comprobacion simplificada de flexo-compresion: usar diagrama aproximado
    # M_Rd aprox con brazo 0.8D y armadura traccionada As_min/2 (mitad de barras)
    z_arm = 0.8 * D
    M_Rd = (As_min / 2) * FYD * z_arm + N_Ed * (D / 2 - 0.1 * D)  # contribucion del axil
    out["seccion_ec2"] = {
        "Ac_m2": Ac, "e_mm": e * 1e3, "e_sobre_D": e / D,
        "As_min_cm2": As_min * 1e4, "N_Rd_kN": N_Rd / 1e3, "u_N": N_Ed / N_Rd,
        "M_Rd_kNm": M_Rd / 1e3, "u_M": M_Ed / M_Rd if M_Rd > 0 else 9.99,
        "ok_N": bool(N_Ed <= N_Rd), "ok_M": bool(M_Ed <= M_Rd),
    }

    oks = [out["axil_ec7"]["ok"], out["lateral"]["ok"],
           out["seccion_ec2"]["ok_N"], out["seccion_ec2"]["ok_M"]]
    out["veredicto"] = "CUMPLE" if all(oks) else "REVISAR"
    return out


if __name__ == "__main__":
    mp_ = sys.argv[1] if len(sys.argv) > 1 else "proyecto-pilote/modelo_neutro.json"
    rp_ = sys.argv[2] if len(sys.argv) > 2 else "proyecto-pilote/resultados.json"
    op_ = sys.argv[3] if len(sys.argv) > 3 else "proyecto-pilote/verificacion.json"
    model = json.load(open(mp_, encoding="utf-8"))
    results = json.load(open(rp_, encoding="utf-8"))
    out = verificar(model, results)
    json.dump(out, open(op_, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    a = out["axil_ec7"]; lt = out["lateral"]; s = out["seccion_ec2"]
    print(f"PILOTE Ø{out['info']['D']} L={out['info']['L']}  -> {out['veredicto']}")
    print(f"  EC7 axil: N_Ed={a['N_Ed_kN']:.0f} kN / Rc,d={a['Rc_d_kN']:.0f} kN ({a['u']*100:.0f}%)  {'OK' if a['ok'] else 'NO'}")
    print(f"  lateral: M_Ed={lt['M_Ed_kNm']:.0f} kN·m  V_Ed={lt['V_Ed_kN']:.0f} kN  "
          f"flecha cabeza {lt['flecha_cabeza_mm']:.1f}/{lt['lim_mm']:.0f} mm ({lt['u']*100:.0f}%)  {'OK' if lt['ok'] else 'NO'}")
    print(f"  EC2 seccion: e/D={s['e_sobre_D']:.2f}  As,min={s['As_min_cm2']:.1f} cm²  "
          f"u_N={s['u_N']*100:.0f}%  u_M={s['u_M']*100:.0f}%")
