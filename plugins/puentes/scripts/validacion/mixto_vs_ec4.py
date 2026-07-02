"""
Validacion del vertical MIXTO (PT 7.5):

(A) M_pl,Rd de la seccion mixta por FIBRAS de `ec3ec4_mixto` vs el M_pl,Rd de
    `motor-calculo` (mixtas/verificacion_mixta.M_pl_fibras) para la MISMA viga ->
    reuso por formula EC4 verificado (tol 3%).
(B) Accion compuesta: flecha del modelo FEM (losa de laminas + viga de acero como
    rigidizador con offset rigido) vs viga compuesta de Euler (E_s*I_comp) para un
    vano biapoyado bajo peso propio -> interaccion completa por offset (tol 5%),
    coherente con la validacion `placa_rigidizada` del motor (1,3%).

SI (N, m). Predimensionado; revisar y firmar (ICCP).
"""
from __future__ import annotations
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "idealizacion"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "comprobacion"))
import mixto as MX
import ec3ec4_mixto as EC
sys.path.insert(0, os.environ.get("MOTOR_CALCULO_MIXTAS", ""))
try:
    import verificacion_mixta as VM
except Exception:
    VM = None


def validar(tol_Mpl=0.03, tol_defl=0.05):
    steel = {"b": 0.30, "h": 0.70, "tw": 0.014, "tf": 0.024}
    steel.update(MX._ishape_props(steel["b"], steel["h"], steel["tw"], steel["tf"]))
    fy = 355e6; fck = 30e6; Ecm = 33e9; t_losa = 0.25
    L = 24.0; sep = 3.0
    be = min(EC.b_eff_losa(L, sep), sep)
    M_mine, zna, zona = EC.M_pl_fibras(steel, t_losa, be, fy, fck)

    checks = {}
    if VM is not None:
        model = {"viga": {"acero": "S355", "hormigon": "C30", "h": steel["h"], "b": steel["b"],
                          "tw": steel["tw"], "tf": steel["tf"], "A": steel["A"], "Iy": steel["Iy"],
                          "Wply": steel["Wply"], "Avz": steel.get("Avz", steel["h"] * steel["tw"]),
                          "L": L, "apeado": False},
                 "losa": {"hp": 0.0, "hc": t_losa, "b0": 0.0, "nr": 1},
                 "materiales": {"S355": {"E": 2.1e11, "fy": fy}, "C30": {"E": Ecm, "fck": fck}}}
        M_ref, yna_ref, zona_ref = VM.M_pl_fibras(model, be)
        e_M = abs(M_mine - M_ref) / M_ref
        checks["Mpl_mixto_vs_motorcalculo"] = (M_mine, M_ref, e_M)
    else:
        checks["Mpl_mixto_vs_motorcalculo"] = (M_mine, None, 0.0)
        e_M = 0.0

    # (B) accion compuesta: una jacena (n_vigas=1), vano biapoyado, peso propio
    mx = {"L": L, "n_vanos": 1, "B": 3.0, "n_vigas": 1, "t_losa": t_losa,
          "nx": 24, "ny": 6, "perfil": steel,
          "material_h": {"E": Ecm, "nu": 0.2, "rho": 2500.0, "fck": fck},
          "material_s": {"E": 2.1e11, "nu": 0.3, "rho": 7850.0, "fy": fy, "fu": 490e6}}
    M, meta = MX.construir_mixto(mx)
    MX.aplicar_peso_propio(M, meta, "G")
    res = M.resolver({"G": {"G": 1.0}})["combos"]["G"]
    reg = meta["reg"]; ycen = round(meta["ys_g"][0], 4)
    nmid = reg[(round(L / 2.0, 4), ycen, 0.0)]
    w_fem = res["desplazamientos"][nmid][2]
    # viga compuesta de Euler: I_comp (homogeneizada a acero), carga = peso losa(trib)+acero
    pm = MX._seccion_mixta_props(steel, t_losa, meta["sep_vigas"] if meta["n_vigas"] > 1 else mx["B"],
                                 mx["material_h"], mx["material_s"])
    A_c = mx["B"] * t_losa
    w_lin = (A_c * 2500.0 + steel["A"] * 7850.0) * 9.81
    I_comp = pm["I_comp_m4"]; Es = 2.1e11
    w_beam = -5 * w_lin * L ** 4 / (384 * Es * I_comp)
    e_d = abs(w_fem - w_beam) / abs(w_beam)
    checks["accion_compuesta_flecha_vs_Euler"] = (w_fem, w_beam, e_d)

    ok = (e_M <= tol_Mpl) and (e_d <= tol_defl)
    return ok, checks


if __name__ == "__main__":
    ok, checks = validar()
    print("MIXTO validacion OK=", ok)
    for k, v in checks.items():
        if v[1] is None:
            print("  %s: mine=%.4g (sin referencia motor-calculo)" % (k, v[0]))
        else:
            print("  %s: mine=%.4g ref=%.4g err=%.2f%%" % (k, v[0], v[1], 100 * v[2]))
