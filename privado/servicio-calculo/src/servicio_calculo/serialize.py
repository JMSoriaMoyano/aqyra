"""(De)serialización entre el contrato C5 (dataclasses) y el JSON del visor.

La SALIDA usa `dataclasses.asdict`: los nombres de campo de `puente_calculo.contract`
son el ESPEJO del contrato TS público (`publico/openbim`), así que el JSON producido
encaja campo a campo con el tipo `ResultGroup` que `viewer.showResultGroup` consume.
La ENTRADA reusa los parsers del contrato (`request_from_dict`) y añade el parseo del
`ResultGroup` que el cliente devuelve a /qa y /sign (no existía: solo había de entrada).
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from puente_calculo import contract as c


# ── Salida ─────────────────────────────────────────────────────────────────────
def result_group_to_dict(rg: c.ResultGroup) -> dict[str, Any]:
    return asdict(rg)


# ── Entrada (el grupo que el visor devuelve para elevar de estado) ─────────────
def _station(d: dict[str, Any]) -> c.MemberStation:
    return c.MemberStation(
        x=d["x"], N=d["N"], V_strong=d["V_strong"], V_weak=d["V_weak"],
        M_strong=d["M_strong"], M_weak=d["M_weak"], T=d["T"],
        dx=d.get("dx", 0.0), dy=d.get("dy", 0.0), dz=d.get("dz", 0.0),
    )


def _member(d: dict[str, Any]) -> c.MemberResult:
    return c.MemberResult(
        memberId=d["memberId"],
        stations=[_station(s) for s in d.get("stations", [])],
        utilization=d.get("utilization", 0.0),
        governing=d.get("governing"),
        passes=d.get("passes", True),
    )


def _node(d: dict[str, Any]) -> c.NodeResult:
    r = d.get("reaction")
    reaction = None
    if r is not None:
        reaction = c.NodeReaction(fx=r["fx"], fy=r["fy"], fz=r["fz"], mx=r["mx"], my=r["my"], mz=r["mz"])
    return c.NodeResult(
        nodeId=d["nodeId"], ux=d.get("ux", 0.0), uy=d.get("uy", 0.0), uz=d.get("uz", 0.0),
        rx=d.get("rx", 0.0), ry=d.get("ry", 0.0), rz=d.get("rz", 0.0), reaction=reaction,
    )


def result_group_from_dict(d: dict[str, Any]) -> c.ResultGroup:
    return c.ResultGroup(
        id=d["id"], combinationId=d["combinationId"], state=d.get("state", "computed"),
        members=[_member(m) for m in d.get("members", [])],
        nodes=[_node(n) for n in d.get("nodes", [])],
        surfaces=[],  # superficies: write-back diferido (fuera de alcance del hilo)
    )


# ── Secciones para EC3 (derivadas del modelo: A, fy y módulos resistentes) ─────
def sections_from_model(model: c.StructuralModel) -> dict[str, dict[str, Any]]:
    """{memberId: {A, fy, Wpl_strong, Wpl_weak, Wel_strong, Wel_weak}} a partir de
    `member.section.props` y `materialProps.fy_or_fck`. Solo barras con datos."""
    out: dict[str, dict[str, Any]] = {}
    for m in model.members:
        sec = m.section
        if not sec or not sec.props or not sec.materialProps:
            continue
        p = sec.props
        out[m.id] = {
            "A": p.A, "fy": sec.materialProps.fy_or_fck,
            "Wpl_strong": p.Wpl_strong, "Wel_strong": p.Wel_strong,
            "Wpl_weak": p.Wpl_weak, "Wel_weak": p.Wel_weak,
        }
    return out
