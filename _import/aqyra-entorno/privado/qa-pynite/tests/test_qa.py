"""Tests de la QA independiente (paso 4, D-023).

A diferencia del adaptador (paso 3, motor falso), aqui hay un solver REAL (PyNite):
se valida la FISICA del convenio D-018 (gravedad -Z -> reaccion +Z, flecha -Z;
N>0 traccion) y la maquina de las dos llaves (equilibrio, reconciliacion, bloqueo).
"""
from __future__ import annotations

import os
import sys
from dataclasses import replace

_here = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(_here, "..", "src"))
sys.path.insert(0, os.path.join(_here, "..", "..", "puente-calculo", "src"))

from puente_calculo import contract as c  # noqa: E402
from qa_pynite import equilibrium_check, reconcile, run_qa, solve_pynite  # noqa: E402


def _sec(A, Is, Iw, J):
    return c.SectionRef(profile="IPE300",
                        props=c.SectionProps(A=A, I_strong=Is, I_weak=Iw, J=J),
                        materialProps=c.MaterialProps(E=2.1e8, G=8.08e7, density=78.5, fy_or_fck=2.75e5))


def _cantilever_x():
    """Mensula HORIZONTAL (X): N1 empotrado -> N2; UDL gravitatoria -Z de 5 kN/m."""
    return c.CalcRequest(
        model=c.StructuralModel(
            nodes=[c.Node("N1", 0, 0, 0), c.Node("N2", 4, 0, 0)],
            members=[c.Member(id="B1", kind="beam", nodeStart="N1", nodeEnd="N2", section=_sec(0.00538, 8.356e-5, 6.04e-6, 2.01e-7))],
            supports=[c.Support(id="S1", nodeId="N1", restraints=c.Restraints(True, True, True, True, True, True))],
            loads=[c.Load(id="L1", kind="distributed", target="B1", value=5.0, direction="z", case="G")],
        ),
        combinations=[c.Combination("ELU1", "ELU", "ULS", {"G": 1.0}, "G")],
    )


def _hanging():
    """Barra colgada: N2 (arriba) empotrado, N1 (abajo) libre con carga -Z -> TRACCION."""
    return c.CalcRequest(
        model=c.StructuralModel(
            nodes=[c.Node("N1", 0, 0, 0), c.Node("N2", 0, 0, 4)],
            members=[c.Member(id="B1", kind="column", nodeStart="N1", nodeEnd="N2", section=_sec(0.00538, 8.356e-5, 6.04e-6, 2.01e-7))],
            supports=[c.Support(id="S2", nodeId="N2", restraints=c.Restraints(True, True, True, True, True, True))],
            loads=[c.Load(id="L1", kind="point", target="N1", value=10.0, direction="z", case="G")],
        ),
        combinations=[c.Combination("ELU1", "ELU", "ULS", {"G": 1.0}, "G")],
    )


def test_fisica_d018_mensula_gravedad_menosZ():
    """D-018: carga -Z -> reaccion +Z y flecha -Z (PyNite real)."""
    rg = solve_pynite(_cantilever_x(), "ELU1")
    n1 = next(n for n in rg.nodes if n.nodeId == "N1")
    assert n1.reaction is not None
    assert abs(n1.reaction.fz - 20.0) < 1e-3   # total = 5 kN/m * 4 m = 20 kN, reaccion +Z
    n2 = next(n for n in rg.nodes if n.nodeId == "N2")
    assert n2.uz < 0                            # la punta baja (flecha -Z)
    nmax = max(abs(s.N) for s in rg.members[0].stations)
    assert nmax < 1e-3                          # mensula transversal: axil ~ 0


def test_fisica_d018_N_positivo_traccion():
    """D-018: barra colgada bajo gravedad -> N>0 (traccion); PyNite reporta -, se niega."""
    rg = solve_pynite(_hanging(), "ELU1")
    nmax = max(s.N for s in rg.members[0].stations)
    assert nmax > 0                              # traccion positiva tras alinear el signo
    assert abs(nmax - 10.0) < 1e-2


def test_equilibrio_gate():
    req = _cantilever_x()
    rg = solve_pynite(req, "ELU1")
    ok, resid = equilibrium_check(req, rg)
    assert ok and resid["FZ"] < 1e-3            # Sum reacciones = Sum acciones

    # rompe el equilibrio: reaccion alterada -> el gate lo detecta
    bad_nodes = [replace(n, reaction=replace(n.reaction, fz=n.reaction.fz * 0.5)) if n.reaction else n for n in rg.nodes]
    bad = replace(rg, nodes=bad_nodes)
    ok2, _ = equilibrium_check(req, bad)
    assert not ok2


def test_reconcile_pass_y_fail():
    req = _cantilever_x()
    motor = solve_pynite(req, "ELU1")            # "motor" (en prod = motor-fem)
    qa = solve_pynite(req, "ELU1")               # QA independiente
    rep = reconcile(req, motor, qa)
    assert rep.verdict == "qa-passed" and rep.equilibrium_ok and not rep.discrepancies

    # motor discrepante (reaccion 20% mayor) -> qa-fail con discrepancia expuesta
    skewed = [replace(n, reaction=replace(n.reaction, fz=n.reaction.fz * 1.2)) if n.reaction else n for n in motor.nodes]
    motor_bad = replace(motor, nodes=skewed)
    rep2 = reconcile(req, motor_bad, qa)
    assert rep2.verdict == "qa-fail" and rep2.discrepancies


def test_run_qa_eleva_o_bloquea():
    req = _cantilever_x()
    motor = solve_pynite(req, "ELU1")
    report, elevated = run_qa(req, motor, solver=solve_pynite)
    assert report.verdict == "qa-passed"
    assert elevated is not None and elevated.state == "qa-passed"   # 1.a llave puesta

    # qa-fail BLOQUEA: no se eleva nada (el visor no puede pintar qa-passed)
    bad = replace(motor, nodes=[replace(n, reaction=replace(n.reaction, fz=n.reaction.fz * 1.3)) if n.reaction else n for n in motor.nodes])
    report2, elevated2 = run_qa(req, bad, solver=solve_pynite)
    assert report2.verdict == "qa-fail" and elevated2 is None


def _run() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    fails = 0
    for t in tests:
        try:
            t()
            print(f"OK   {t.__name__}")
        except AssertionError as e:
            fails += 1
            print(f"FAIL {t.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            fails += 1
            print(f"ERR  {t.__name__}: {e!r}")
    print(f"\n{len(tests) - fails}/{len(tests)} OK")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(_run())
