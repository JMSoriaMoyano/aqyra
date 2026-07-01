"""Tests del contrato de binding al motor (paso b): ensamblado y parseo.

Verifica `to_request`/`from_response` (la parte testeable del binding a motor-fem;
el solve real depende del entrypoint del paquete anclado). Tambien ejercita el
binding COMPLETO inyectando un `motor_fem` falso en sys.modules.
"""
from __future__ import annotations

import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from puente_calculo.engine import EngineCombo, EngineLoad, EngineMember, EngineModel, EngineNode  # noqa: E402
from puente_calculo.motor_request import from_response, to_request  # noqa: E402


def _model() -> EngineModel:
    return EngineModel(
        nodes=[EngineNode("N1", 0, 0, 0, support=(True, True, True, True, True, True)),
               EngineNode("N2", 4, 0, 0)],
        members=[EngineMember("B1", "N1", "N2", E=2.1e8, G=8.08e7, A=0.00538, Iy=6.04e-6, Iz=8.356e-5, J=2.01e-7,
                              releases=(False, False, False, False, True, True) + (False,) * 6)],
        loads=[EngineLoad("member_dist", "B1", "FZ", -5.0, "G")],
        combos=[EngineCombo("ELU1", {"G": 1.35, "Q": 1.5})],
    )


def test_to_request_serializa_el_problema_completo():
    req = to_request(_model(), "ELU1")
    assert req["combo"] == "ELU1"
    assert req["nodes"][0]["support"] == [True, True, True, True, True, True]
    m = req["members"][0]
    assert m["Iz"] == 8.356e-5 and m["Iy"] == 6.04e-6           # ejes letras del motor
    assert m["releases"][4] is True and m["releases"][5] is True  # Ryi,Rzi liberados (rotula i)
    assert req["loads"][0]["direction"] == "FZ" and req["loads"][0]["value"] == -5.0  # gravedad -Z
    assert req["combos"][0]["factors"] == {"G": 1.35, "Q": 1.5}


def test_from_response_mapea_esfuerzos_y_reacciones():
    resp = {
        "members": [{"id": "B1", "stations": [
            {"x": 0.0, "axial": -10.0, "Fy": 3.0, "Fz": 0.0, "Mx": 0.0, "My": 0.0, "Mz": -8.0, "dx": 0, "dy": 0, "dz": 0},
        ]}],
        "nodes": [{"id": "N1", "DX": 0, "DY": 0, "DZ": 0, "RX": 0, "RY": 0, "RZ": 0, "reaction": [0, 0, 20.0, 0, 0, 0]},
                  {"id": "N2", "DX": 0, "DY": 0, "DZ": -0.01, "RX": 0, "RY": 0, "RZ": 0, "reaction": None}],
    }
    er = from_response(resp)
    assert er.members[0].stations[0].axial == -10.0   # axil nativo del motor (lo niega el adaptador)
    assert er.nodes[0].reaction == (0, 0, 20.0, 0, 0, 0)
    assert er.nodes[1].reaction is None and er.nodes[1].DZ == -0.01


def test_binding_completo_con_motor_falso_inyectado():
    """Inyecta un `motor_fem` falso en sys.modules y ejercita MotorFemBinding entero."""
    fake = types.ModuleType("motor_fem")

    def solve(request):  # firma: dict -> dict
        # "resuelve" devolviendo una reaccion que equilibra la carga del request
        return {
            "members": [{"id": m["id"], "stations": [
                {"x": 0.0, "axial": -1.0, "Fy": 0.0, "Fz": 0.0, "Mx": 0.0, "My": 0.0, "Mz": 0.0, "dx": 0, "dy": 0, "dz": 0}]}
                for m in request["members"]],
            "nodes": [{"id": n["id"], "DX": 0, "DY": 0, "DZ": 0, "RX": 0, "RY": 0, "RZ": 0,
                       "reaction": [0, 0, 20.0, 0, 0, 0] if any(n["support"]) else None} for n in request["nodes"]],
        }

    fake.solve = solve  # type: ignore[attr-defined]
    sys.modules["motor_fem"] = fake
    try:
        from puente_calculo.engine import MotorFemBinding
        binding = MotorFemBinding(entrypoint="solve")
        er = binding.solve(_model(), "ELU1")
        assert er.members[0].stations[0].axial == -1.0
        assert er.nodes[0].reaction == (0, 0, 20.0, 0, 0, 0)
    finally:
        del sys.modules["motor_fem"]


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
