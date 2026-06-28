"""Tests del adaptador C5 (paso 3, D-019).

Verifican el MOAT (traduccion D-018/D-020) y el MAPEO de resultados con un MOTOR
FALSO: `motor-fem` se consume anclado y no se vendoriza, asi que la FISICA la
comprueba el motor real (o la QA PyNite del paso 4); aqui se comprueba que el
adaptador TRADUCE y MAPEA con el convenio correcto (ejes por rol, N>0 traccion,
releases true=liberado, gravedad -Z, combos, estado computed, write-back).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from puente_calculo import contract as c  # noqa: E402
from puente_calculo.adapter import solve_request  # noqa: E402
from puente_calculo.engine import (  # noqa: E402
    EngineModel,
    EngineMemberResult,
    EngineNodeResult,
    EngineResult,
    EngineStation,
)
from puente_calculo.translate import to_engine_model  # noqa: E402
from puente_calculo.writeback import append_to_ifc  # noqa: E402


class FakeMotor:
    """Motor falso: registra el EngineModel recibido (para auditar la traduccion)
    y devuelve un EngineResult canonico (axil traccion+ , reaccion +Z)."""

    axial_tension_positive = True

    def __init__(self, tension_positive: bool = True) -> None:
        self.axial_tension_positive = tension_positive
        self.last_model: EngineModel | None = None
        self.last_combo: str | None = None

    def solve(self, model: EngineModel, combo_name: str) -> EngineResult:
        self.last_model = model
        self.last_combo = combo_name
        return EngineResult(
            members=[
                EngineMemberResult(
                    id="B1",
                    stations=[
                        EngineStation(x=0.0, axial=10.0, Fy=3.0, Fz=0.0, Mx=0.0, My=0.0, Mz=-8.0, dx=0.0, dy=0.0, dz=0.0),
                        EngineStation(x=4.0, axial=10.0, Fy=-3.0, Fz=0.0, Mx=0.0, My=0.0, Mz=0.0, dx=0.0, dy=-0.012, dz=0.0),
                    ],
                )
            ],
            nodes=[EngineNodeResult(id="N1", DX=0, DY=0, DZ=0, RX=0, RY=0, RZ=0, reaction=(0, 0, 12.5, 0, 0, 0))],
        )


def _mensula() -> c.CalcRequest:
    """Mensula: N1 empotrado (z=0) -> N2 (z=4), carga distribuida vertical."""
    model = c.StructuralModel(
        nodes=[c.Node("N1", 0, 0, 0), c.Node("N2", 0, 0, 4)],
        members=[
            c.Member(
                id="B1", kind="column", nodeStart="N1", nodeEnd="N2",
                section=c.SectionRef(
                    profile="IPE300",
                    props=c.SectionProps(A=0.00538, I_strong=8.356e-5, I_weak=6.04e-6, J=2.01e-7),
                    materialProps=c.MaterialProps(E=2.1e8, G=8.08e7, density=78.5, fy_or_fck=2.75e5),
                ),
            )
        ],
        supports=[c.Support(id="S1", nodeId="N1", restraints=c.Restraints(True, True, True, True, True, True))],
        loads=[c.Load(id="L1", kind="distributed", target="B1", value=5.0, direction="z", case="G")],
    )
    return c.CalcRequest(model=model, combinations=[c.Combination("ELU1", "ELU", "ULS", {"G": 1.35, "Q": 1.5}, "1.35G+1.5Q")])


def test_traduccion_seccion_por_rol_y_apoyo():
    em = to_engine_model(_mensula())
    m = em.members[0]
    assert m.Iz == 8.356e-5  # strong -> Iz (D-018)
    assert m.Iy == 6.04e-6   # weak -> Iy
    assert m.E == 2.1e8
    n1 = next(n for n in em.nodes if n.id == "N1")
    assert n1.support == (True, True, True, True, True, True)  # empotrado (true=restringido)


def test_gravedad_menos_z_y_combos():
    em = to_engine_model(_mensula())
    ld = em.loads[0]
    assert ld.direction == "FZ" and ld.value == -5.0  # gravedad -Z (D-018)
    assert em.combos[0].factors == {"G": 1.35, "Q": 1.5}  # mapa, no texto


def test_releases_biarticulada_mapea_a_motor():
    req = _mensula()
    rotula = c.MemberEndRelease(mStrong=True, mWeak=True)  # libera los dos flectores
    req.model.members[0].releases = c.MemberReleases(i=rotula, j=rotula)
    em = to_engine_model(req)
    rel = em.members[0].releases
    # orden Dxi,Dyi,Dzi,Rxi,Ryi(<-mWeak),Rzi(<-mStrong), Dxj..Rzj
    assert rel == (False, False, False, False, True, True, False, False, False, False, True, True)


def test_mapeo_resultado_N_positivo_traccion_y_estado_computed():
    motor = FakeMotor(tension_positive=True)
    groups = solve_request(_mensula(), motor)
    assert len(groups) == 1
    rg = groups[0]
    assert rg.state == "computed"  # 0 llaves: nunca certificado
    assert rg.combinationId == "ELU1"
    st0 = rg.members[0].stations[0]
    assert st0.N == 10.0          # N>0 = traccion (D-018), pasa intacto
    assert st0.V_strong == 3.0    # rol fuerte <- Fy
    assert st0.M_strong == -8.0   # rol fuerte <- Mz
    assert rg.nodes[0].reaction.fz == 12.5  # reaccion +Z bajo gravedad -Z


def test_alineacion_de_signo_axil_si_motor_es_compresion_positiva():
    motor = FakeMotor(tension_positive=False)  # motor reporta compresion+
    rg = solve_request(_mensula(), motor)[0]
    assert rg.members[0].stations[0].N == -10.0  # el adaptador NIEGA -> N>0 traccion


def test_carga_por_area_reparte_a_bordes():
    req = _mensula()
    req.model.members.append(
        c.Member(
            id="E1", kind="beam", nodeStart="N1", nodeEnd="N2",
            section=c.SectionRef(
                profile="IPE200",
                props=c.SectionProps(A=0.00285, I_strong=1.943e-5, I_weak=1.42e-6, J=6.98e-8),
                materialProps=c.MaterialProps(E=2.1e8, G=8.08e7, density=78.5, fy_or_fck=2.75e5),
            ),
        )
    )
    req.model.surfaces.append(
        c.Surface(id="S5", kind="diaphragm", area=10.0,
                  areaLoad=c.SurfaceAreaLoad(q=5.0, case="Q", distributeTo="edges"),
                  edgeMembers=["E1"])
    )
    em = to_engine_model(req)
    edge = [l for l in em.loads if l.target == "E1"]
    assert edge and edge[0].direction == "FZ"
    # total = q*area = 50 kN sobre L=4 m -> w = -12.5 kN/m (gravedad)
    assert abs(edge[0].value - (-12.5)) < 1e-9


def test_writeback_estampa_no_verificado_y_alinea_a_resultgroup():
    rg = solve_request(_mensula(), FakeMotor())[0]
    ifc = "ISO-10303-21;\nDATA;\n#1=IFCPROJECT();\nENDSEC;\n"
    out = append_to_ifc(ifc, rg, model_name="decopak")
    assert "AQYRA-RESULTGROUP" in out and "AQYRA-REACTION" in out
    assert "NO VERIFICADO" in out  # computed -> estampado (guarda de exportacion)
    assert out.index("AQYRA-RESULTGROUP") > out.index("DATA;")  # tras DATA;
    rg.state = "verified-signed"
    signed = append_to_ifc(ifc, rg)
    assert "NO VERIFICADO" not in signed


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
