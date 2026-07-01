"""
Verificacion de ZAPATA AISLADA: EC7 (geotecnia) + EC2 (hormigon).

EC7:
  - Tension del terreno: p_max (ELU) <= Rd (resistencia de calculo)
  - Excentricidad: e = M/N <= B/6 (sin despegue) ; p_min >= 0
EC2:
  - Flexion: momento en la CARA del pilar (seccion critica) integrando la presion
    del terreno -> armadura inferior (dos direcciones)
  - Punzonamiento (§6.4): V_Ed neto (axil del pilar menos presion dentro del
    perimetro de control) -> comprobacion y, si procede, dimensionamiento
  - Cortante (§6.2.2): a un canto d de la cara del pilar
SI (N, m).
"""
import sys
import json
import math
import numpy as np
import ec2_punz_fis
from ec2_punz_fis import _vRdc
from verificacion_ec2 import armado_direccion, _to_native

GC = 1.50
C_NOM = 0.050     # recubrimiento de zapata (m)
PHI = 0.016


def _momento_cara(presion, info, direccion):
    """Momento por metro de ancho en la cara del pilar integrando la presion del suelo."""
    xp, yp, c, B = info["xp"], info["yp"], info["c_pilar"], info["B"]
    # area tributaria por nodo (malla regular -> aprox por numero de nodos en rejilla)
    # estimamos trib por nodo = (B/ (n-1))^2 con n nodos por lado
    n_side = round(math.sqrt(len(presion)))
    da = (B / (n_side - 1)) ** 2 if n_side > 1 else B * B
    if direccion == "x":
        face = xp + c / 2
        M = sum(p["p"] * da * (p["x"] - face) for p in presion if p["x"] > face)
    else:
        face = yp + c / 2
        M = sum(p["p"] * da * (p["y"] - face) for p in presion if p["y"] > face)
    return abs(M) / B   # por metro de ancho


def verificar(model, results):
    info = results["info"]
    mp = model["materiales"][info["material"]]
    fck = mp["fck"]; fctm = mp["fctm"]; fcd = fck / GC
    t = info["espesor"]; B = info["B"]; c = info["c_pilar"]; Rd = info["Rd"]
    d = t - C_NOM - PHI
    area = info["area"]

    out = {"info": info, "equilibrio": results["equilibrio"]}

    # --- EC7: tension del terreno y excentricidad (ELU) ---
    pres = results["zapata"]["ELU"]["presion"]
    p_vals = [p["p"] for p in pres]
    p_max = max(p_vals); p_min = min(p_vals)
    # excentricidad equivalente a partir de p_max,p_min (distribucion lineal)
    p_med = sum(p_vals) / len(p_vals)
    out["geotecnia"] = {
        "p_max_kPa": p_max / 1e3, "p_min_kPa": p_min / 1e3, "p_med_kPa": p_med / 1e3,
        "Rd_kPa": Rd / 1e3, "u_Rd": p_max / Rd, "ok_Rd": p_max <= Rd,
        "ok_sin_despegue": p_min >= -1e-6,
    }

    # --- EC2 flexion: momento en cara del pilar ---
    Mx_face = _momento_cara(pres, info, "x")
    My_face = _momento_cara(pres, info, "y")
    out["flexion"] = {
        "x": armado_direccion(Mx_face, d, fcd, fctm, t),
        "y": armado_direccion(My_face, d, fcd, fctm, t),
        "d_mm": d * 1e3,
    }
    As_med = math.sqrt(out["flexion"]["x"]["As_prov_cm2_m"] * 1e-4 *
                       out["flexion"]["y"]["As_prov_cm2_m"] * 1e-4)
    rho_l = As_med / d

    # --- EC2 punzonamiento (V_Ed neto) ---
    N_ELU = results["equilibrio"]["aplicada_ELU_kN"] * 1e3
    A_within = c * c + 4 * c * (2 * d) + math.pi * (2 * d) ** 2   # area dentro de u1
    V_net = N_ELU - p_med * A_within
    out["punzonamiento"] = ec2_punz_fis.punzonamiento(V_net, c, c, d, fck, rho_l, posicion="interior")
    out["punzonamiento"]["V_Ed_neto_kN"] = V_net / 1e3
    if not out["punzonamiento"]["ok"]:
        out["punzonamiento"]["dimensionado"] = ec2_punz_fis.dimensionar_punzonamiento(
            V_net, c, c, t, C_NOM, PHI, fck, As_med, posicion="interior")

    # --- EC2 cortante (a d de la cara) ---
    face = info["xp"] + c / 2 + d
    n_side = round(math.sqrt(len(pres)))
    da = (B / (n_side - 1)) ** 2 if n_side > 1 else B * B
    V_1way = sum(p["p"] * da for p in pres if p["x"] > face) / B    # por metro
    vRdc, kk = _vRdc(d, fck, rho_l)
    out["cortante"] = {"V_Ed_kN_m": V_1way / 1e3, "vRdc_MPa": vRdc / 1e6,
                       "VRdc_kN_m": vRdc * d / 1e3, "u": V_1way / (vRdc * d),
                       "ok": V_1way <= vRdc * d}

    geo_ok = out["geotecnia"]["ok_Rd"] and out["geotecnia"]["ok_sin_despegue"]
    est_ok = (out["flexion"]["x"]["ok"] and out["flexion"]["y"]["ok"]
              and out["punzonamiento"]["ok"] and out["cortante"]["ok"])
    out["veredicto"] = "CUMPLE" if (geo_ok and est_ok) else "REVISAR"
    return _to_native(out)


if __name__ == "__main__":
    mp_ = sys.argv[1] if len(sys.argv) > 1 else "proyecto-zapata/modelo_neutro.json"
    rp_ = sys.argv[2] if len(sys.argv) > 2 else "proyecto-zapata/resultados.json"
    op_ = sys.argv[3] if len(sys.argv) > 3 else "proyecto-zapata/verificacion.json"
    model = json.load(open(mp_, encoding="utf-8"))
    results = json.load(open(rp_, encoding="utf-8"))
    out = verificar(model, results)
    json.dump(out, open(op_, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    g = out["geotecnia"]
    print(f"ZAPATA B={out['info']['B']} t={out['info']['espesor']}  -> {out['veredicto']}")
    print(f"  EC7 terreno: p_max={g['p_max_kPa']:.0f} kPa / Rd={g['Rd_kPa']:.0f} kPa ({g['u_Rd']*100:.0f}%)  "
          f"{'OK' if g['ok_Rd'] else 'NO'}  sin despegue: {'si' if g['ok_sin_despegue'] else 'NO'}")
    fx, fy = out["flexion"]["x"], out["flexion"]["y"]
    print(f"  EC2 flexion (cara pilar): Mx={fx['m_Ed_kNm_m']:.1f} -> {fx['armado']}  "
          f"My={fy['m_Ed_kNm_m']:.1f} -> {fy['armado']}  (d={out['flexion']['d_mm']:.0f}mm)")
    pz = out["punzonamiento"]
    print(f"  EC2 punzonamiento: V_Ed,neto={pz['V_Ed_neto_kN']:.0f} kN  vEd/vRdc={pz['u_vRdc']*100:.0f}%  "
          f"{'OK' if pz['ok'] else 'NO -> dimensionar'}")
    cv = out["cortante"]
    print(f"  EC2 cortante (a d): V_Ed={cv['V_Ed_kN_m']:.0f} kN/m  VRdc={cv['VRdc_kN_m']:.0f} kN/m "
          f"({cv['u']*100:.0f}%)  {'OK' if cv['ok'] else 'NO'}")
    print(f"  EQUILIBRIO: error {out['equilibrio']['error_pct']:.2f}%")
