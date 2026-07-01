"""Tests del aprovechamiento EC3 (paso 5, D-022). Nucleo puro (sin contrato)."""
from __future__ import annotations

import os
import sys
from types import SimpleNamespace as NS

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from verificacion_ec import apply_ec3_checks, critical_members, ec3_section_utilization  # noqa: E402

# IPE300, S275: A=0.00538 m2, Wpl_strong=6.28e-4 m3, fy=2.75e5 kN/m2, gamma_M0=1.05
A, FY, WPL = 0.00538, 2.75e5, 6.28e-4
NPL = A * FY / 1.05          # ~ 1409 kN
MCRD = WPL * FY / 1.05       # ~ 164 kN·m


def test_axil_puro_traccion():
    u, gov, ok = ec3_section_utilization(N=NPL, M_strong=0, A=A, fy=FY, Wpl_strong=WPL)
    assert abs(u - 1.0) < 1e-6 and ok          # N = Npl,Rd -> u=1, cumple (limite)
    assert "axil" in gov and "traccion" in gov


def test_flexion_pura_eje_fuerte():
    u, gov, ok = ec3_section_utilization(N=0, M_strong=MCRD, A=A, fy=FY, Wpl_strong=WPL)
    assert abs(u - 1.0) < 1e-6 and "fuerte" in gov


def test_interaccion_N_mas_M_supera_la_unidad():
    u, gov, ok = ec3_section_utilization(N=0.6 * NPL, M_strong=0.6 * MCRD, A=A, fy=FY, Wpl_strong=WPL)
    assert abs(u - 1.2) < 1e-6 and not ok       # 0.6+0.6 = 1.2 > 1 -> NO cumple
    assert gov in ("axil (traccion)", "flexion eje fuerte")


def test_usa_Wel_si_no_hay_Wpl():
    wel = 5.57e-4
    u, _, _ = ec3_section_utilization(N=0, M_strong=MCRD, A=A, fy=FY, Wel_strong=wel)
    assert u > 1.0  # con Wel (<Wpl) el aprovechamiento es mayor


def test_apply_rellena_y_lista_que_no_cumple():
    # dos barras: B1 holgada, B2 sobrecargada
    rg = NS(members=[
        NS(memberId="B1", stations=[NS(N=0.2 * NPL, M_strong=0.2 * MCRD, M_weak=0.0)], utilization=0.0, governing=None, passes=True),
        NS(memberId="B2", stations=[NS(N=0.0, M_strong=1.3 * MCRD, M_weak=0.0)], utilization=0.0, governing=None, passes=True),
    ])
    sections = {
        "B1": {"A": A, "fy": FY, "Wpl_strong": WPL, "Wpl_weak": 6.0e-5},
        "B2": {"A": A, "fy": FY, "Wpl_strong": WPL, "Wpl_weak": 6.0e-5},
    }
    no_cumple = apply_ec3_checks(rg, sections)
    assert rg.members[0].passes and not rg.members[0].memberId in no_cumple
    assert abs(rg.members[0].utilization - 0.4) < 1e-6
    assert no_cumple == ["B2"] and not rg.members[1].passes
    assert abs(rg.members[1].utilization - 1.3) < 1e-6
    assert critical_members(rg, 0.9) == ["B2"]  # solo B2 supera 0.9


def _run() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    fails = 0
    for t in tests:
        try:
            t(); print(f"OK   {t.__name__}")
        except AssertionError as e:
            fails += 1; print(f"FAIL {t.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            fails += 1; print(f"ERR  {t.__name__}: {e!r}")
    print(f"\n{len(tests) - fails}/{len(tests)} OK")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(_run())
