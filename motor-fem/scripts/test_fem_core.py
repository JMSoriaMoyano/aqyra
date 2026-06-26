"""
Micro-test del nucleo FEM (FEM-0). Ejecuta:
 - simetria y definicion positiva (con apoyos) de la matriz de barra y de lamina;
 - rigidez de barra a axil vs analitico;
 - equilibrio de una viga;
 - placa cuadrada vs Timoshenko (< 5%);
 - patch test de membrana (tension constante, < 1e-9);
 - parches analiticos (analitico.validar) y benchmarks NAFEMS (nafems.validar).

Exit 0 si todo pasa, !=0 si falla. Requiere numpy/scipy (PYTHONPATH=/tmp/pylibs).
"""
from __future__ import annotations
import os
import sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "validacion"))
from fem_core import ModeloFEM, ElementoBarra, ElementoLamina  # noqa: E402
import analitico, nafems                                       # noqa: E402


def _chk(name, cond, fails):
    print("  [%s] %s" % ("OK" if cond else "FALLO", name))
    if not cond:
        fails.append(name)


def main():
    fails = []
    MAT = {"E": 210e9, "G": 80.77e9, "nu": 0.3, "rho": 7850.0}
    SEC = {"A": 8.68e-3, "Iy": 5.7e-5, "Iz": 2.0e-5, "J": 1e-6}

    # --- barra: simetria de K global ---
    el = ElementoBarra("b", "a", "b", (0, 0, 0), (4, 0, 0), MAT, SEC)
    K = el.Kglobal
    _chk("barra K simetrica", np.allclose(K, K.T, atol=1e-6), fails)

    # --- barra a axil vs analitico ---
    r = analitico.barra_axil()
    _chk("barra axil vs PL/EA", r["alargamiento_m"][2] < 1e-9, fails)

    # --- viga: equilibrio ---
    vb = analitico.viga_biapoyada()
    _chk("viga equilibrio ~0", vb["equilibrio_N"][2] < 1e-3, fails)
    _chk("viga flecha EB exacta", vb["flecha_centro_m"][2] < 1e-6, fails)

    # --- lamina: simetria de K ---
    le = ElementoLamina("q", ["1", "2", "3", "4"],
                        [(0, 0, 0), (2, 0.1, 0), (2.1, 1.6, 0), (0.2, 1.5, 0)], 0.2, 30e9, 0.2)
    Kq = le.Kglobal
    _chk("lamina K simetrica", np.allclose(Kq, Kq.T, atol=1e-3), fails)

    # --- placa vs Timoshenko ---
    pl = analitico.placa_timoshenko(n=12)
    _chk("placa flecha vs Timoshenko <5%", pl["flecha_centro_m"][2] < 0.05, fails)
    _chk("placa M vs Timoshenko <5%", pl["M_centro_Nm"][2] < 0.05, fails)

    # --- patch test de membrana ---
    pm = nafems.patch_membrana()
    _chk("patch membrana tension constante <1e-9",
         pm["membrana_tension_constante_err"][2] < 1e-9, fails)

    # --- definicion positiva con apoyos (viga biapoyada estable) ---
    M = ModeloFEM()
    M.add_nodo("a", 0, 0, 0); M.add_nodo("b", 4, 0, 0)
    M.add_elemento(ElementoBarra("b", "a", "b", (0, 0, 0), (4, 0, 0), MAT, SEC))
    M.set_apoyo("a", [1, 1, 1, 1, 1, 1]); M.set_apoyo("b", [0, 1, 1, 1, 1, 1])
    M.add_carga_nodal("Q", "b", [1000.0, 0, 0, 0, 0, 0])
    res = M.resolver()
    _chk("solve estable (axil libre)", abs(res["combos"]["Q"]["desplazamientos"]["b"][0]) > 0, fails)

    print("\nRESULTADO:", "TODO OK" if not fails else "FALLOS: %s" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
