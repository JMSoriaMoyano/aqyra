"""Ensamblado de la peticion al motor + parseo de su respuesta (contrato de binding).

`motor-fem 0.1.0` se consume ANCLADO y NO esta vendorizado en este repo, asi que su
API exacta no se conoce aqui. Este modulo fija el CONTRATO NEUTRO (JSON-able) que el
binding usa: `to_request` serializa el EngineModel a un dict autocontenido y
`from_response` parsea el dict de resultados. Asi la parte dificil (ensamblar el
problema FE completo y mapear la respuesta) queda hecha y TESTEADA; solo el nombre
del *entrypoint* del motor queda por confirmar (ver `engine.MotorFemBinding`).

Forma de la PETICION (lo que el binding pasa al motor):
  { "combo": str,
    "nodes":   [{"id","x","y","z","support":[DX,DY,DZ,RX,RY,RZ]}],            # support: bool, true=restringido
    "members": [{"id","i","j","E","G","A","Iy","Iz","J","rotation",
                 "releases":[Dxi,Dyi,Dzi,Rxi,Ryi,Rzi,Dxj,Dyj,Dzj,Rxj,Ryj,Rzj]}],  # release: bool, true=liberado
    "loads":   [{"kind","target","direction","value","case"}],               # direction: "FX"|"FY"|"FZ" global
    "combos":  [{"name","factors":{caseId: factor}}] }
Forma de la RESPUESTA (lo que el motor debe devolver para `combo`):
  { "members": [{"id","stations":[{"x","axial","Fy","Fz","Mx","My","Mz","dx","dy","dz"}]}],
    "nodes":   [{"id","DX","DY","DZ","RX","RY","RZ","reaction":[FX,FY,FZ,MX,MY,MZ]|null}] }
Convenios (D-018): global Z-up, gravedad -Z; ejes letras del motor (Iy=debil, Iz=fuerte).
El signo del axil se alinea a N>0 traccion en el adaptador (MotorFemPort.axial_tension_positive).
"""
from __future__ import annotations

from typing import Any

from .engine import (
    EngineModel,
    EngineMemberResult,
    EngineNodeResult,
    EngineResult,
    EngineStation,
)


def to_request(model: EngineModel, combo_name: str) -> dict[str, Any]:
    return {
        "combo": combo_name,
        "nodes": [
            {"id": n.id, "x": n.x, "y": n.y, "z": n.z, "support": list(n.support)}
            for n in model.nodes
        ],
        "members": [
            {
                "id": m.id, "i": m.i, "j": m.j,
                "E": m.E, "G": m.G, "A": m.A, "Iy": m.Iy, "Iz": m.Iz, "J": m.J,
                "rotation": m.rotation, "releases": list(m.releases),
            }
            for m in model.members
        ],
        "loads": [
            {"kind": l.kind, "target": l.target, "direction": l.direction, "value": l.value, "case": l.case}
            for l in model.loads
        ],
        "combos": [{"name": cb.name, "factors": dict(cb.factors)} for cb in model.combos],
    }


def from_response(resp: dict[str, Any]) -> EngineResult:
    members = [
        EngineMemberResult(
            id=m["id"],
            stations=[
                EngineStation(
                    x=s["x"], axial=s["axial"], Fy=s["Fy"], Fz=s["Fz"],
                    Mx=s["Mx"], My=s["My"], Mz=s["Mz"], dx=s.get("dx", 0.0), dy=s.get("dy", 0.0), dz=s.get("dz", 0.0),
                )
                for s in m.get("stations", [])
            ],
        )
        for m in resp.get("members", [])
    ]
    nodes = []
    for n in resp.get("nodes", []):
        rx = n.get("reaction")
        reaction = tuple(rx) if rx is not None else None  # type: ignore[assignment]
        nodes.append(
            EngineNodeResult(
                id=n["id"], DX=n["DX"], DY=n["DY"], DZ=n["DZ"], RX=n["RX"], RY=n["RY"], RZ=n["RZ"],
                reaction=reaction,
            )
        )
    return EngineResult(members=members, nodes=nodes)
