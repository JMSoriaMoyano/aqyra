"""
Validacion del vertical OBLICUO (PT 7.5):

(A) Caso RECTO (esviaje=0): la malla romboidal degenera en ortogonal y el tablero
    se comporta como losa unidireccional biapoyada -> el momento de la franja
    central Mx debe coincidir con la teoria de viga w*L^2/8 (por metro) y la
    concentracion en esquina ~1 (reparto uniforme). Referencia "malla ortogonal".
(B) Caso ESVIADO (esviaje>0): debe aparecer la CONCENTRACION de reaccion en la
    esquina OBTUSA (>1) -> el efecto de esviaje queda capturado.

Tol viga 5%. SI (N, m). Predimensionado; revisar y firmar (ICCP).
"""
from __future__ import annotations
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "idealizacion"))
import oblicuo as OB

G = 9.81


def _resolver(esviaje, L=16.0, B=8.0, t=0.6, q2=0.0):
    obl = {"L": L, "B": B, "esviaje_deg": esviaje, "t": t, "nx": 20, "ny": 12,
           "material": {"E": 3.3e10, "nu": 0.2, "rho": 2500.0, "fck": 35e6, "fyk": 500e6}}
    M, meta = OB.construir_oblicuo(obl)
    OB.aplicar_peso_propio(M, meta, "G")
    if q2:
        OB.aplicar_carga_muerta(M, meta, q2, "G")
    est = M.resolver({"G": {"G": 1.0}})["combos"]["G"]
    mx = OB.momentos_franja(est, meta, "Mx")
    reac = OB.reacciones_esquinas(est, meta)
    return obl, meta, mx, reac, t


def validar(tol_viga=0.05):
    checks = {}
    # (A) recto: Mx franja vs w L^2/8
    obl, meta, mx, reac, t = _resolver(0.0)
    w = obl["material"]["rho"] * G * t                  # N/m2 (peso propio)
    M_viga = w * obl["L"] ** 2 / 8.0                    # Nm/m
    e = abs(mx["M_max_Nm_m"] - M_viga) / M_viga
    checks["recto_Mx_franja_vs_viga"] = (mx["M_max_Nm_m"], M_viga, e)
    checks["recto_concentracion_esquina"] = (reac["concentracion_obtusa"], 1.0,
                                             abs(reac["concentracion_obtusa"] - 1.0))
    # (B) esviado 35deg: concentracion obtusa > 1
    _, _, mx2, reac2, _ = _resolver(35.0)
    checks["esviado_concentracion_obtusa"] = (reac2["concentracion_obtusa"], ">1.0",
                                              reac2["concentracion_obtusa"])
    ok = (e <= tol_viga) and (reac["concentracion_obtusa"] < 2.0) \
        and (reac2["concentracion_obtusa"] > reac["concentracion_obtusa"])
    return ok, checks


if __name__ == "__main__":
    ok, checks = validar()
    print("OBLICUO validacion OK=", ok)
    for k, v in checks.items():
        if isinstance(v[1], str):
            print("  %s: valor=%.3f (esperado %s)" % (k, v[0], v[1]))
        else:
            print("  %s: fem=%.4g ref=%.4g err=%.2f%%" % (k, v[0], v[1], 100 * v[2]))
