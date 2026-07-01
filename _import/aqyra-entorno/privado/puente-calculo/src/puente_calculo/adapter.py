"""Adaptador C5: orquesta serializado -> traduccion -> solve -> mapeo con estado.

Produce SOLO `computed` (0 llaves, D-021): el motor calculo, sin verificar. El
paso a `qa-passed` (PyNite, D-023) y a `verified-signed` (firma de JM) es de los
otros carriles. El mapeo de salida vuelve del lenguaje de LETRAS del motor al
esquema PUBLICO por ROL (D-018) y alinea N>0 = traccion.
"""
from __future__ import annotations

from typing import Any

from . import contract as c
from .engine import EngineResult, MotorFemPort
from .translate import to_engine_model


def _map_member(er, axial_tension_positive: bool) -> c.MemberResult:
    stations: list[c.MemberStation] = []
    for st in er.stations:
        n = st.axial if axial_tension_positive else -st.axial  # D-018: N>0 traccion
        stations.append(
            c.MemberStation(
                x=st.x, N=n,
                V_strong=st.Fy, V_weak=st.Fz,   # rol fuerte<-Fy, debil<-Fz (D-018)
                M_strong=st.Mz, M_weak=st.My,   # rol fuerte<-Mz, debil<-My
                T=st.Mx,
                dx=st.dx, dy=st.dy, dz=st.dz,
            )
        )
    # Aprovechamiento EC3 = paso 5/D-022 (checker aparte); aqui solo esfuerzos.
    return c.MemberResult(memberId=er.id, stations=stations, utilization=0.0, governing=None, passes=True)


def _map_node(nr) -> c.NodeResult:
    reaction = None
    if nr.reaction is not None:
        fx, fy, fz, mx, my, mz = nr.reaction
        reaction = c.NodeReaction(fx=fx, fy=fy, fz=fz, mx=mx, my=my, mz=mz)
    return c.NodeResult(nodeId=nr.id, ux=nr.DX, uy=nr.DY, uz=nr.DZ, rx=nr.RX, ry=nr.RY, rz=nr.RZ, reaction=reaction)


def map_result(combination_id: str, er: EngineResult, axial_tension_positive: bool) -> c.ResultGroup:
    return c.ResultGroup(
        id=f"RG-{combination_id}",
        combinationId=combination_id,
        state="computed",  # nace sin llaves (D-021); el visor NUNCA lo pinta verde
        members=[_map_member(m, axial_tension_positive) for m in er.members],
        nodes=[_map_node(n) for n in er.nodes],
        surfaces=[],
    )


def solve_request(req: c.CalcRequest, motor: MotorFemPort) -> list[c.ResultGroup]:
    """Resuelve cada combinacion con el motor y devuelve los grupos `computed`."""
    engine_model = to_engine_model(req)
    groups: list[c.ResultGroup] = []
    combos = req.combinations or [c.Combination(id="ELU1", name="ELU", limitState="ULS", terms={})]
    for cb in combos:
        er = motor.solve(engine_model, cb.id)
        groups.append(map_result(cb.id, er, motor.axial_tension_positive))
    return groups


def solve_json(payload: dict[str, Any], motor: MotorFemPort) -> list[c.ResultGroup]:
    """Punto de entrada del servicio: JSON del visor -> grupos de resultado."""
    return solve_request(c.request_from_dict(payload), motor)
