"""Pipeline END-TO-END de V3 (paso 5 / DoD, D-021/D-022/D-023).

Cose los cuatro carriles sobre un caso patron: el motor (aqui PyNite como
stand-in de motor-fem) produce `computed` -> la QA independiente reconcilia y pone
la 1.a llave `qa-passed` -> el chequeo EC3 rellena el aprovechamiento y «que no
cumple» -> la firma de JM pone la 2.a llave `verified-signed`. Y la guarda:
NO se puede firmar lo que no ha pasado la QA.
"""
from __future__ import annotations

import os
import sys

_here = os.path.dirname(__file__)
for rel in (("..", "src"), ("..", "..", "puente-calculo", "src"), ("..", "..", "qa-pynite", "src"), ("..", "..", "verificacion-ec", "src")):
    sys.path.insert(0, os.path.join(_here, *rel))

from dataclasses import replace  # noqa: E402

from puente_calculo import contract as c  # noqa: E402
from qa_pynite import run_qa, solve_pynite  # noqa: E402
from verificacion_ec import apply_ec3_checks, critical_members  # noqa: E402
from firma import SigningError, sign_result  # noqa: E402

# IPE300 / S275
SEC = c.SectionRef(profile="IPE300",
                   props=c.SectionProps(A=0.00538, I_strong=8.356e-5, I_weak=6.04e-6, J=2.01e-7),
                   materialProps=c.MaterialProps(E=2.1e8, G=8.08e7, density=78.5, fy_or_fck=2.75e5))
SECTIONS = {"B1": {"A": 0.00538, "fy": 2.75e5, "Wpl_strong": 6.28e-4, "Wpl_weak": 1.25e-4}}


def _cantilever(w: float) -> c.CalcRequest:
    return c.CalcRequest(
        model=c.StructuralModel(
            nodes=[c.Node("N1", 0, 0, 0), c.Node("N2", 4, 0, 0)],
            members=[c.Member(id="B1", kind="beam", nodeStart="N1", nodeEnd="N2", section=SEC)],
            supports=[c.Support(id="S1", nodeId="N1", restraints=c.Restraints(True, True, True, True, True, True))],
            loads=[c.Load(id="L1", kind="distributed", target="B1", value=w, direction="z", case="G")],
        ),
        combinations=[c.Combination("ELU1", "ELU", "ULS", {"G": 1.0}, "G")],
    )


def test_flujo_computed_qapassed_verifiedsigned_con_que_no_cumple():
    req = _cantilever(30.0)  # UDL fuerte -> la mensula NO cumple a flexion

    # 1) MOTOR (stand-in motor-fem) -> computed
    motor = solve_pynite(req, "ELU1")
    assert motor.state == "computed"

    # 2) QA independiente -> 1.a llave qa-passed
    report, elevated = run_qa(req, motor, solver=solve_pynite)
    assert report.verdict == "qa-passed" and elevated is not None
    assert elevated.state == "qa-passed"

    # 3) EC3 -> aprovechamiento + «que no cumple»
    no_cumple = apply_ec3_checks(elevated, SECTIONS)
    assert no_cumple == ["B1"]                      # la mensula no cumple
    assert elevated.members[0].utilization > 1.0
    assert "flexion" in elevated.members[0].governing
    assert critical_members(elevated, 0.9) == ["B1"]

    # 4) FIRMA de JM -> 2.a llave verified-signed (el calculo se certifica;
    #    el «no cumple» es un hallazgo VALIDO y certificado)
    signed, rec = sign_result(elevated, "JM")
    assert signed.state == "verified-signed"
    assert rec.signer == "JM" and rec.combinationId == "ELU1"


def test_no_se_puede_firmar_sin_qa():
    req = _cantilever(10.0)
    motor = solve_pynite(req, "ELU1")              # computed, sin QA
    try:
        sign_result(motor, "JM")
        assert False, "deberia haber fallado: no hay 1.a llave"
    except SigningError:
        pass


def test_qa_fail_bloquea_la_firma():
    req = _cantilever(10.0)
    motor = solve_pynite(req, "ELU1")
    # motor manipulado: reaccion 30% mayor -> qa-fail -> no se eleva nada
    bad = replace(motor, nodes=[replace(n, reaction=replace(n.reaction, fz=n.reaction.fz * 1.3)) if n.reaction else n for n in motor.nodes])
    report, elevated = run_qa(req, bad, solver=solve_pynite)
    assert report.verdict == "qa-fail" and elevated is None   # bloqueo: nada que firmar
    assert report.discrepancies


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
