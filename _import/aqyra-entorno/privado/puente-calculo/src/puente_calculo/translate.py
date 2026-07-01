"""Traduccion modelo C5 (publico, por ROL) -> EngineModel (letras del motor).

EL MOAT (D-018/D-020). Reglas que NUNCA salen del anzuelo:
  - Ejes por ROL: strong -> z (Iz), weak -> y (Iy). Nunca se pasa la letra cruda.
  - Releases (true=liberado) -> def_releases del motor, mapeo por rol:
        axial->Dx, vStrong->Dy, vWeak->Dz, torsion->Rx, mStrong->Rz, mWeak->Ry.
  - Apoyos (true=restringido) -> def_support (DX..RZ), directo.
  - Gravedad -Z global: una carga vertical (eje "z") se aplica como FZ NEGATIVA.
  - Combinaciones {caso: factor} -> combos del motor (no se parsea texto).
  - Carga por area q (kN/m2) -> repartida a vigas de borde / nudos por area real.
"""
from __future__ import annotations

import math

from . import contract as c
from .engine import EngineCombo, EngineLoad, EngineMember, EngineModel, EngineNode


def _global_load(direction: str, value: float) -> tuple[str, float]:
    """Convenio D-018 (Z-up, gravedad -Z): el eje 'z' es vertical y una carga
    autorada en 'z' actua HACIA ABAJO (FZ negativa). 'x'/'y' en +eje global."""
    d = (direction or "z").lower()
    if d == "x":
        return "FX", value
    if d == "y":
        return "FY", value
    return "FZ", -value  # gravedad por defecto


# Orden def_releases del motor: Dxi,Dyi,Dzi,Rxi,Ryi,Rzi, Dxj,Dyj,Dzj,Rxj,Ryj,Rzj.
# Mapeo por ROL (D-018): Dx<-axial, Dy<-vStrong, Dz<-vWeak, Rx<-torsion, Ry<-mWeak, Rz<-mStrong.
def _end_releases(e: c.MemberEndRelease | None) -> tuple[bool, bool, bool, bool, bool, bool]:
    if e is None:
        return (False, False, False, False, False, False)
    return (e.axial, e.vStrong, e.vWeak, e.torsion, e.mWeak, e.mStrong)


def _member_releases(r: c.MemberReleases | None) -> tuple[bool, ...]:
    if r is None:
        return (False,) * 12
    return _end_releases(r.i) + _end_releases(r.j)


def _length(a: c.Node, b: c.Node) -> float:
    return math.dist((a.x, a.y, a.z), (b.x, b.y, b.z))


def to_engine_model(req: c.CalcRequest) -> EngineModel:
    model = req.model
    node_by_id = {n.id: n for n in model.nodes}
    support_by_node = {s.nodeId: s.restraints for s in model.supports}

    # Nudos + apoyos (true=restringido -> def_support, directo).
    nodes: list[EngineNode] = []
    for n in model.nodes:
        r = support_by_node.get(n.id)
        sup = (r.ux, r.uy, r.uz, r.rx, r.ry, r.rz) if r else (False,) * 6
        nodes.append(EngineNode(id=n.id, x=n.x, y=n.y, z=n.z, support=sup))

    # Barras: seccion/material numericos por ROL (strong->Iz, weak->Iy) + releases.
    members: list[EngineMember] = []
    for m in model.members:
        sec = m.section
        props = sec.props if sec else None
        mat = sec.materialProps if sec else None
        if props is None or mat is None:
            # Sin numeros no se puede ensamblar: lo resuelve el lado Aqyra (D-019.C.1.a).
            raise ValueError(
                f"barra {m.id}: faltan props/material numericos (resolverlos en Aqyra antes de C5)."
            )
        members.append(
            EngineMember(
                id=m.id, i=m.nodeStart, j=m.nodeEnd,
                E=mat.E, G=mat.G, A=props.A,
                Iy=props.I_weak, Iz=props.I_strong, J=props.J,
                rotation=0.0,
                releases=_member_releases(m.releases),
            )
        )

    # Cargas explicitas (nudo/barra), gravedad -Z.
    loads: list[EngineLoad] = []
    for ld in model.loads:
        direction, val = _global_load(ld.direction, ld.value)
        kind = "node" if ld.kind == "point" else "member_dist"
        loads.append(EngineLoad(kind=kind, target=ld.target, direction=direction, value=val, case=ld.case or "G"))

    # Carga por area q (kN/m2) -> reparto a bordes/nudos por area real (D-019.C.3.a).
    for s in model.surfaces:
        al = s.areaLoad
        if al is None:
            continue
        area = s.area if s.area is not None else _polygon_area(s.outline)
        total = al.q * area  # kN
        case = al.case or "Q"
        if al.distributeTo == "nodes" and s.edgeNodes:
            per = total / len(s.edgeNodes)
            for nid in s.edgeNodes:
                loads.append(EngineLoad(kind="node", target=nid, direction="FZ", value=-per, case=case))
        elif s.edgeMembers:
            # UDL por metro que conserva la carga total: w * sum(L) = total.
            lengths = []
            for mid in s.edgeMembers:
                mm = next((x for x in model.members if x.id == mid), None)
                if mm and mm.nodeStart in node_by_id and mm.nodeEnd in node_by_id:
                    lengths.append(_length(node_by_id[mm.nodeStart], node_by_id[mm.nodeEnd]))
                else:
                    lengths.append(0.0)
            tot_len = sum(lengths) or 1.0
            w = total / tot_len  # kN/m
            for mid in s.edgeMembers:
                loads.append(EngineLoad(kind="member_dist", target=mid, direction="FZ", value=-w, case=case))
        # si no hay bordes declarados, el reparto tributario geometrico fino queda
        # como refinamiento (el visor aporta edgeMembers/edgeNodes).

    # Combinaciones {caso: factor} -> combos (sin parsear texto).
    combos = [EngineCombo(name=cb.id, factors=dict(cb.terms)) for cb in req.combinations]

    return EngineModel(nodes=nodes, members=members, loads=loads, combos=combos)


def _polygon_area(outline: list[list[float]]) -> float:
    """Area de un poligono 3D plano (formula de Newell / norma del area vectorial)."""
    if len(outline) < 3:
        return 0.0
    nx = ny = nz = 0.0
    n = len(outline)
    for k in range(n):
        a = outline[k]
        b = outline[(k + 1) % n]
        nx += a[1] * b[2] - a[2] * b[1]
        ny += a[2] * b[0] - a[0] * b[2]
        nz += a[0] * b[1] - a[1] * b[0]
    return 0.5 * math.sqrt(nx * nx + ny * ny + nz * nz)
