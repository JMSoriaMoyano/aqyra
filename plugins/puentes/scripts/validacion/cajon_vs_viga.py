"""
Validacion del vertical CAJON (PT 7.4): el modelo de LAMINA PURA vs TEORIA DE
VIGA-CAJON. Un vano simplemente apoyado bajo peso propio: la deflexion de centro
de vano y el momento de seccion (integrado del Nx de las laminas) deben coincidir
con la viga de Euler (5wL^4/384EI, wL^2/8) dentro de la tolerancia de
predimensionado. Confirma que la idealizacion de laminas reproduce el
comportamiento global de viga-cajon (ademas de captar torsion/distorsion/shear
lag, que la viga no ve). SI. Predim.; revisar y firmar (ICCP).
"""
from __future__ import annotations
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "idealizacion"))
import cajon as CJ

G = 9.81


def validar(tol_defl=0.05, tol_M=0.06):
    # box ESBELTO (L/h=25): la deformacion por cortante (~1/L^2) es <2% -> Euler es
    # referencia valida y la coincidencia es estrecha. En vanos cortos el cajon es
    # legitimamente mas flexible que Euler (cortante + shear lag + distorsion, que es
    # lo que FEM-2 capta y la viga de Euler ignora).
    cfg = {"L": 50.0, "n_vanos": 1, "bs": 6.0, "bi": 3.5, "h": 2.0,
           "t_top": 0.25, "t_bot": 0.22, "t_web": 0.35,
           "nx": 32, "nyt": 12, "nyb": 6, "nz": 6,
           "material": {"E": 3.4e10, "nu": 0.2, "rho": 2500.0}}
    M, meta = CJ.construir_cajon(cfg)
    A = meta["props"]["A"]; I = meta["props"]["Iy"]
    CJ.aplicar_peso_propio(M, meta, 2500.0, caso="G")
    res = M.resolver({"G": {"G": 1.0}})["combos"]["G"]
    L = cfg["L"]; h = cfg["h"]; reg = meta["reg"]
    nmid = reg.get((round(L / 2, 4), 0.0, round(-h, 4))) or reg.get(
        (round(L / 2, 4), round(min(meta["ybot"], key=abs), 4), round(-h, 4)))
    w_fem = res["desplazamientos"][nmid][2]
    w_lin = A * 2500.0 * G
    w_beam = -5 * w_lin * L ** 4 / (384 * cfg["material"]["E"] * I)
    M_fem = CJ.momento_seccion(M, res, meta, meta["sec_crit"][0]["ix"])
    M_beam = w_lin * L ** 2 / 8.0
    e_defl = abs(w_fem - w_beam) / abs(w_beam)
    e_M = abs(abs(M_fem) - M_beam) / M_beam
    checks = {"cajon_deflexion_vs_Euler": (w_fem, w_beam, e_defl),
              "cajon_momento_vs_viga": (M_fem, M_beam, e_M)}
    ok = e_defl <= tol_defl and e_M <= tol_M
    return ok, checks


if __name__ == "__main__":
    ok, checks = validar()
    print("=" * 64)
    print("VALIDACION CAJON vs VIGA-CAJON:", "OK" if ok else "FALLO")
    print("=" * 64)
    for k, (c, r, e) in checks.items():
        print("  %-26s calc=%+.5g  ref=%+.5g  err=%.2f%%" % (k, c, r, e * 100))
    sys.exit(0 if ok else 1)
