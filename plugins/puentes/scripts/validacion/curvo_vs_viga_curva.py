"""
Validacion del vertical CURVO (PT 7.5) frente a la teoria de VIGA CURVA
(flexo-torsion acoplada):

(A) FLEXION: el momento de seccion del cajon curvo coincide con el de la viga
    recta de la misma longitud desarrollada (w*S^2/8) -> la malla curva capta la
    flexion global (tol predim 8%); y es consistente con el caso casi-recto
    (R grande), donde la torsion se anula.
(B) TORSION ACOPLADA: bajo carga vertical aparece un par torsor T que (i) crece al
    DISMINUIR el radio segun la ley de acoplamiento dT/ds=M/R -> T*R ~ const
    (T(R)/T(2R)~2, tol 15%), y (ii) tiende a CERO en el tablero recto (R->inf).
    Se reporta ademas la estimacion estatica de viga curva T~w*S^3/(24R) (cota
    inferior: ignora la redistribucion por GJ/EI y el brazo del apoyo).

SI (N, m). Predimensionado; revisar y firmar por tecnico competente (ICCP).
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "idealizacion"))
import curvo as CV

G = 9.81


def _run(R, S=40.0):
    cfg = {"R": R, "L": S, "bs": 7.0, "bi": 4.0, "h": 2.2, "t_top": 0.25, "t_bot": 0.22,
           "t_web": 0.40, "nx": 24, "nyt": 6, "nyb": 3, "nz": 3,
           "material": {"E": 3.4e10, "nu": 0.2, "rho": 2500.0, "fck": 40e6}}
    M, meta = CV.construir_curvo(cfg)
    CV.aplicar_peso_propio(M, meta, "G")
    est = M.resolver({"G": {"G": 1.0}})["combos"]["G"]
    ix = meta["sec_crit"][0]["ix"]
    Mfem = abs(CV.momento_seccion(M, est, meta, ix))
    T = CV.torsion_apoyo(est, meta)["T_apoyo_Nm"]
    w = meta["props"]["A"] * 2500.0 * G
    return Mfem, T, w, S


def validar(tol_flex=0.08, tol_ley=0.15):
    checks = {}
    M150, T150, w, S = _run(150.0)
    M300, T300, _, _ = _run(300.0)
    Mrec, Trec, _, _ = _run(1.0e6)            # casi recto
    # (A) flexion vs viga recta
    M_th = w * S ** 2 / 8.0
    e_flex = abs(M150 - M_th) / M_th
    checks["flexion_box_curvo_vs_viga"] = (M150, M_th, e_flex)
    # consistencia M curvo vs casi-recto
    e_cons = abs(M150 - Mrec) / Mrec
    checks["flexion_curvo_vs_recto"] = (M150, Mrec, e_cons)
    # (B) ley de acoplamiento T*R ~ const  => T150/T300 ~ 2
    ratio = T150 / T300 if T300 else 0.0
    e_ley = abs(ratio - 2.0) / 2.0
    checks["torsion_ley_1_sobre_R (T150/T300~2)"] = (ratio, 2.0, e_ley)
    # torsion -> 0 en recto
    rel_recto = Trec / Mrec if Mrec else 0.0
    checks["torsion_recto_T_sobre_M (~0)"] = (rel_recto, 0.0, rel_recto)
    # informativo: estimacion estatica de viga curva
    T_est = w * S ** 3 / (24.0 * 150.0)
    checks["[info] T_fem vs w S^3/24R"] = (T150, T_est, abs(T150 - T_est) / T_est)

    ok = (e_flex <= tol_flex) and (e_cons <= 0.03) and (e_ley <= tol_ley) and (rel_recto < 0.02)
    return ok, checks


if __name__ == "__main__":
    ok, checks = validar()
    print("CURVO validacion OK=", ok)
    for k, v in checks.items():
        print("  %s: fem=%.4g ref=%.4g err=%.1f%%" % (k, v[0], v[1], 100 * v[2]))
