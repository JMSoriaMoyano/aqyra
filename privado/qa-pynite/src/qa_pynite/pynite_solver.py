"""Re-calculo INDEPENDIENTE con PyNite (2.a llave tecnica · D-023).

Carril de QA: re-implementa el ensamblado desde el contrato C5 y resuelve con
PyNite, un solver DISTINTO del nucleo de `motor-fem` (independencia D-023.C.1).
Comparte el CONTRATO (tipos) con el adaptador, NO el solver. Convenio D-018:
frame Z-up, gravedad -Z, ejes por rol (strong->Iz, weak->Iy), N>0 = traccion.

PyNite reporta el axil con TRACCION NEGATIVA (verificado 2.0.2): se NIEGA para
cumplir N>0 traccion. Se usa `analyze(sparse=False)` (solver numpy).
"""
from __future__ import annotations

from puente_calculo import contract as c

# Mapeo de cargas global (gravedad -Z, D-018), independiente del adaptador.
def _global_dir(direction: str, value: float) -> tuple[str, float]:
    d = (direction or "z").lower()
    if d == "x":
        return "FX", value
    if d == "y":
        return "FY", value
    return "FZ", -value  # gravedad por defecto


# releases por rol -> orden PyNite Dxi,Dyi,Dzi,Rxi,Ryi,Rzi,...:
# axial->Dx, vStrong->Dy, vWeak->Dz, torsion->Rx, mStrong->Rz, mWeak->Ry.
def _end(e: c.MemberEndRelease | None) -> tuple[bool, bool, bool, bool, bool, bool]:
    if e is None:
        return (False,) * 6
    return (e.axial, e.vStrong, e.vWeak, e.torsion, e.mWeak, e.mStrong)


def solve_pynite(req: c.CalcRequest, combo_id: str, *, n_stations: int = 5) -> c.ResultGroup:
    from Pynite import FEModel3D

    model = req.model
    fe = FEModel3D()
    for n in model.nodes:
        fe.add_node(n.id, n.x, n.y, n.z)
    for s in model.supports:
        r = s.restraints
        fe.def_support(s.nodeId, r.ux, r.uy, r.uz, r.rx, r.ry, r.rz)  # true=restringido (directo)

    length: dict[str, float] = {}
    node_by_id = {n.id: n for n in model.nodes}
    for m in model.members:
        sec = m.section
        if not sec or not sec.props or not sec.materialProps:
            raise ValueError(f"barra {m.id}: faltan props/material numericos para la QA.")
        p, mat = sec.props, sec.materialProps
        nu = mat.E / (2.0 * mat.G) - 1.0  # nu = E/(2G) - 1
        matname = f"mat_{m.id}"
        secname = f"sec_{m.id}"
        fe.add_material(matname, mat.E, mat.G, nu, mat.density, mat.fy_or_fck)
        fe.add_section(secname, p.A, p.I_weak, p.I_strong, p.J)  # Iy=weak, Iz=strong (D-018)
        fe.add_member(m.id, m.nodeStart, m.nodeEnd, matname, secname)
        if m.releases:
            rel = _end(m.releases.i) + _end(m.releases.j)
            fe.def_releases(m.id, *rel)  # true=liberado (directo)
        a, b = node_by_id[m.nodeStart], node_by_id[m.nodeEnd]
        length[m.id] = ((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2) ** 0.5

    cases: set[str] = set()
    for ld in model.loads:
        direction, val = _global_dir(ld.direction, ld.value)
        case = ld.case or "G"
        cases.add(case)
        if ld.kind == "point":
            fe.add_node_load(ld.target, direction, val, case=case)
        else:
            fe.add_member_dist_load(ld.target, direction, val, val, case=case)

    # carga por area -> reparto a bordes/nudos (independiente del adaptador)
    for s in model.surfaces:
        al = s.areaLoad
        if not al:
            continue
        area = s.area or 0.0
        total = al.q * area
        case = al.case or "Q"
        cases.add(case)
        if al.distributeTo == "nodes" and s.edgeNodes:
            per = total / len(s.edgeNodes)
            for nid in s.edgeNodes:
                fe.add_node_load(nid, "FZ", -per, case=case)
        elif s.edgeMembers:
            tot_len = sum(length.get(mid, 0.0) for mid in s.edgeMembers) or 1.0
            w = total / tot_len
            for mid in s.edgeMembers:
                fe.add_member_dist_load(mid, "FZ", -w, -w, case=case)

    combo = next((cb for cb in req.combinations if cb.id == combo_id), None)
    factors = dict(combo.terms) if combo and combo.terms else {ca: 1.0 for ca in (cases or {"G"})}
    fe.add_load_combo(combo_id, factors)
    fe.analyze(sparse=False)

    members: list[c.MemberResult] = []
    for m in model.members:
        mem = fe.members[m.id]
        L = length[m.id]
        stations: list[c.MemberStation] = []
        for k in range(n_stations):
            x = L * k / (n_stations - 1) if n_stations > 1 else 0.0
            stations.append(
                c.MemberStation(
                    x=x,
                    N=-mem.axial(x, combo_id),          # PyNite traccion negativa -> N>0 traccion (D-018)
                    V_strong=mem.shear("Fy", x, combo_id),
                    V_weak=mem.shear("Fz", x, combo_id),
                    M_strong=mem.moment("Mz", x, combo_id),
                    M_weak=mem.moment("My", x, combo_id),
                    T=mem.torque(x, combo_id),
                    dx=0.0,
                    dy=mem.deflection("dy", x, combo_id),
                    dz=mem.deflection("dz", x, combo_id),
                )
            )
        members.append(c.MemberResult(memberId=m.id, stations=stations, utilization=0.0, passes=True))

    supported = {s.nodeId for s in model.supports}
    nodes: list[c.NodeResult] = []
    for n in model.nodes:
        nd = fe.nodes[n.id]
        reaction = None
        if n.id in supported:
            reaction = c.NodeReaction(
                fx=nd.RxnFX[combo_id], fy=nd.RxnFY[combo_id], fz=nd.RxnFZ[combo_id],
                mx=nd.RxnMX[combo_id], my=nd.RxnMY[combo_id], mz=nd.RxnMZ[combo_id],
            )
        nodes.append(
            c.NodeResult(
                nodeId=n.id,
                ux=nd.DX[combo_id], uy=nd.DY[combo_id], uz=nd.DZ[combo_id],
                rx=nd.RX[combo_id], ry=nd.RY[combo_id], rz=nd.RZ[combo_id],
                reaction=reaction,
            )
        )

    return c.ResultGroup(id=f"QA-{combo_id}", combinationId=combo_id, state="computed", members=members, nodes=nodes, surfaces=[])
