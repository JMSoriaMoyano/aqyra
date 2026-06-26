"""
Predimensionado de la zapata: ejecuta la cadena run_all_zapata y, si el
hundimiento por area eficaz (EC7) supera R_d, AMPLIA la zapata cuadrada (centrada
en el pilar) al minimo lado que cumple, con un unico solve de confirmacion
(dimensionamiento analitico del lado + comprobacion FE). Mantiene picos como
envolvente y deja constancia del lado de modelo y del adoptado.

Uso: python3 run_zapata_predim.py <proj> <ifc>
"""
import sys
import os
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import solver_zapata
import verificacion_zapata
import plots_zapata

GAMMA_C = 25000.0  # N/m3
GG, GQ = 1.35, 1.50


def _Bmin(NGk, NQk, MGk, MQk, t, Rd, B0):
    """Lado cuadrado minimo (centrado, excentricidad en un eje) con sigma_ef<=Rd."""
    def sigma(B):
        Nd = GG * (NGk + GAMMA_C * B * B * t) + GQ * NQk
        Md = GG * MGk + GQ * MQk
        e = Md / Nd if Nd else 0.0
        Lef = B - 2.0 * e
        if Lef <= 0:
            return float("inf"), Nd, e
        return Nd / (B * Lef), Nd, e
    lo, hi = max(B0, 0.5), 6.0
    s_hi, _, _ = sigma(hi)
    if s_hi > Rd:
        return None
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        s, _, _ = sigma(mid)
        if s > Rd:
            lo = mid
        else:
            hi = mid
    import math
    return math.ceil(hi / 0.05) * 0.05


def _sigma_ef_analitico(NGk, NQk, MGk, MQk, B, t, Rd):
    Nd = GG * (NGk + GAMMA_C * B * B * t) + GQ * NQk
    Md = GG * MGk + GQ * MQk
    e = Md / Nd if Nd else 0.0
    Lef = B - 2.0 * e
    s = Nd / (B * Lef) if Lef > 0 else float("inf")
    return s, Nd, e


def run(proj, ifc):
    os.makedirs(proj, exist_ok=True)
    model = solver_zapata.parse_auto(ifc)
    z = model["zapata"]
    B0 = z["B"]
    # cargas caracteristicas de cabeza (N, N*m)
    NGk = NQk = MGk = MQk = 0.0
    for c in z["cargas"]:
        N = abs(c["N"]); M = abs(c.get("Mx", 0.0))
        if str(c["caso"]).upper().startswith("Q"):
            NQk += N; MQk += M
        else:
            NGk += N; MGk += M
    Rd = z["Rd"]
    # 1) PRE-CHEQUEO ANALITICO del hundimiento por area eficaz con el lado de
    #    modelo (evita un solve FE extra; el solver es lento en sandbox).
    s0, Nd0, e0 = _sigma_ef_analitico(NGk, NQk, MGk, MQk, B0, z["espesor"], Rd)
    predim = {"B_modelo_m": B0, "L_modelo_m": z["L"], "ampliada": False,
              "sigma_ef_modelo_analitico_kPa": round(s0 / 1000.0, 1),
              "u_Rd_modelo_analitico": round(s0 / Rd, 3)}
    if s0 > Rd:
        Bmin = _Bmin(NGk, NQk, MGk, MQk, z["espesor"], Rd, B0)
        if Bmin and Bmin > B0:
            z["B"] = z["L"] = Bmin
            z["x0"] = z["xp"] - Bmin / 2.0
            z["y0"] = z["yp"] - Bmin / 2.0
            predim.update({"ampliada": True, "B_adoptado_m": Bmin, "L_adoptado_m": Bmin,
                           "motivo": "hundimiento area eficaz > R_d con %.2f m (u_analitico=%.2f)" % (B0, s0 / Rd)})
    # 2) UN solo solve FE de confirmacion con el lado adoptado
    _, res = solver_zapata.solve(model)
    out = verificacion_zapata.verificar(model, res)
    out["predimensionado_zapata"] = predim
    json.dump(model, open(os.path.join(proj, "modelo_neutro.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    json.dump(res, open(os.path.join(proj, "resultados.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    json.dump(out, open(os.path.join(proj, "verificacion.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    g = out["geotecnia"]
    print("[zapata] via=%s B=%.2f%s  sigma_ef %.0f/%.0f kPa (%.0f%%)  punz %.0f%%  cort %.0f%%  fis %.0f%%  -> %s" % (
        model.get("via"), model["zapata"]["B"], " (ampliada de %.2f)" % B0 if predim["ampliada"] else "",
        g["sigma_ef_kPa"], g["Rd_kPa"], g["u_Rd"] * 100, out["punzonamiento"]["u_vRdc"] * 100,
        out.get("cortante", {}).get("u", 0) * 100, out["fisuracion"]["u"] * 100, out["veredicto"]))
    for f in plots_zapata.generar(res, out, proj):
        pass
    return out


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
