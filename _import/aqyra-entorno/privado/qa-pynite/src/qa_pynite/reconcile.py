"""Equilibrio + reconciliacion con tolerancias (D-023). PURO (sin PyNite).

Dos comprobaciones:
  1. GATE de equilibrio: Sum(reacciones) = Sum(acciones) por eje global (~0,1%).
     Si no cierra, ni se reconcilia: qa-fail inmediato (el resultado es inconsistente).
  2. RECONCILIACION motor vs QA (PyNite independiente) dentro de tolerancia:
     reacciones/desplazamientos +-2..5 %, esfuerzos/aprovechamientos +-5 %.
Veredicto: qa-passed solo si equilibrio OK y todo reconcilia; si no, qa-fail con
la discrepancia EXPUESTA (anulacion documentada, D-023.C.4.a).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from puente_calculo import contract as c

# Tolerancias por defecto (D-023.C.2). Relativas salvo el equilibrio.
TOL_EQUILIBRIUM = 1e-3   # ~0,1 %
TOL_REACTION = 0.05      # +-5 % (banda 2..5 %)
TOL_DISPLACEMENT = 0.05  # +-5 %
TOL_FORCE = 0.05         # +-5 % esfuerzos/aprovechamientos


@dataclass
class QAReport:
    verdict: str  # "qa-passed" | "qa-fail"
    equilibrium_ok: bool
    discrepancies: list[str] = field(default_factory=list)
    detail: dict[str, object] = field(default_factory=dict)


def _length(model: c.StructuralModel, member_id: str) -> float:
    nb = {n.id: n for n in model.nodes}
    m = next((x for x in model.members if x.id == member_id), None)
    if not m or m.nodeStart not in nb or m.nodeEnd not in nb:
        return 0.0
    a, b = nb[m.nodeStart], nb[m.nodeEnd]
    return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2) ** 0.5


def applied_totals(req: c.CalcRequest, combo_id: str) -> dict[str, float]:
    """Resultante de las ACCIONES aplicadas (FX,FY,FZ) para una combinacion.
    Gravedad -Z (eje z -> FZ negativa). Factor por caso de la combinacion."""
    combo = next((cb for cb in req.combinations if cb.id == combo_id), None)
    factors = combo.terms if combo and combo.terms else {}
    tot = {"FX": 0.0, "FY": 0.0, "FZ": 0.0}

    def axis(direction: str, value: float) -> tuple[str, float]:
        d = (direction or "z").lower()
        if d == "x":
            return "FX", value
        if d == "y":
            return "FY", value
        return "FZ", -value

    for ld in req.model.loads:
        f = factors.get(ld.case or "G", 1.0 if not factors else 0.0)
        if f == 0.0:
            continue
        ax, val = axis(ld.direction, ld.value)
        mag = val * (_length(req.model, ld.target) if ld.kind == "distributed" else 1.0)
        tot[ax] += mag * f
    for s in req.model.surfaces:
        al = s.areaLoad
        if not al:
            continue
        f = factors.get(al.case or "Q", 1.0 if not factors else 0.0)
        tot["FZ"] += -(al.q * (s.area or 0.0)) * f
    return tot


def reaction_totals(result: c.ResultGroup) -> dict[str, float]:
    tot = {"FX": 0.0, "FY": 0.0, "FZ": 0.0}
    for n in result.nodes:
        if n.reaction is not None:
            tot["FX"] += n.reaction.fx
            tot["FY"] += n.reaction.fy
            tot["FZ"] += n.reaction.fz
    return tot


def equilibrium_check(req: c.CalcRequest, result: c.ResultGroup, tol: float = TOL_EQUILIBRIUM) -> tuple[bool, dict[str, float]]:
    """Sum(acciones) + Sum(reacciones) ~ 0 por eje. Devuelve (ok, residuos rel.)."""
    applied = applied_totals(req, result.combinationId)
    reactions = reaction_totals(result)
    resid: dict[str, float] = {}
    ok = True
    for ax in ("FX", "FY", "FZ"):
        scale = max(abs(applied[ax]), abs(reactions[ax]), 1.0)
        r = abs(applied[ax] + reactions[ax]) / scale  # reaccion equilibra la accion
        resid[ax] = r
        if r > tol:
            ok = False
    return ok, resid


def _rel(a: float, b: float) -> float:
    return abs(a - b) / max(abs(a), abs(b), 1e-9)


def reconcile(
    req: c.CalcRequest,
    motor: c.ResultGroup,
    qa: c.ResultGroup,
    *,
    tol_reaction: float = TOL_REACTION,
    tol_displacement: float = TOL_DISPLACEMENT,
    tol_force: float = TOL_FORCE,
    tol_equilibrium: float = TOL_EQUILIBRIUM,
) -> QAReport:
    discr: list[str] = []

    # 1) GATE de equilibrio sobre el resultado del MOTOR.
    eq_ok, resid = equilibrium_check(req, motor, tol_equilibrium)
    if not eq_ok:
        discr.append(f"equilibrio: residuos {resid} > {tol_equilibrium} (Sum reacciones != Sum acciones)")

    # 2) Reacciones por nudo (motor vs QA independiente).
    qa_react = {n.nodeId: n.reaction for n in qa.nodes if n.reaction}
    for n in motor.nodes:
        if n.reaction is None:
            continue
        q = qa_react.get(n.nodeId)
        if q is None:
            discr.append(f"reaccion {n.nodeId}: la QA no la tiene")
            continue
        for comp in ("fx", "fy", "fz", "mx", "my", "mz"):
            mv, qv = getattr(n.reaction, comp), getattr(q, comp)
            if _rel(mv, qv) > tol_reaction and max(abs(mv), abs(qv)) > 1e-6:
                discr.append(f"reaccion {n.nodeId}.{comp}: motor={mv:.4g} qa={qv:.4g} ({_rel(mv, qv) * 100:.1f}% > {tol_reaction * 100:.0f}%)")

    # 3) Desplazamientos nodales.
    qa_disp = {n.nodeId: n for n in qa.nodes}
    for n in motor.nodes:
        q = qa_disp.get(n.nodeId)
        if not q:
            continue
        for comp in ("ux", "uy", "uz", "rx", "ry", "rz"):
            mv, qv = getattr(n, comp), getattr(q, comp)
            if _rel(mv, qv) > tol_displacement and max(abs(mv), abs(qv)) > 1e-9:
                discr.append(f"desplaz {n.nodeId}.{comp}: motor={mv:.4g} qa={qv:.4g} ({_rel(mv, qv) * 100:.1f}%)")

    # 4) Esfuerzos por barra (extremos N y M_strong) y aprovechamiento.
    qa_mem = {m.memberId: m for m in qa.members}
    for m in motor.members:
        q = qa_mem.get(m.memberId)
        if not q or not m.stations or not q.stations:
            continue
        mN = max(abs(s.N) for s in m.stations)
        qN = max(abs(s.N) for s in q.stations)
        if _rel(mN, qN) > tol_force and max(mN, qN) > 1e-6:
            discr.append(f"axil {m.memberId}: |N|max motor={mN:.4g} qa={qN:.4g} ({_rel(mN, qN) * 100:.1f}%)")
        mM = max(abs(s.M_strong) for s in m.stations)
        qM = max(abs(s.M_strong) for s in q.stations)
        if _rel(mM, qM) > tol_force and max(mM, qM) > 1e-6:
            discr.append(f"flector {m.memberId}: |M_strong|max motor={mM:.4g} qa={qM:.4g} ({_rel(mM, qM) * 100:.1f}%)")
        if _rel(m.utilization, q.utilization) > tol_force and max(m.utilization, q.utilization) > 1e-6:
            discr.append(f"aprov {m.memberId}: motor={m.utilization:.4g} qa={q.utilization:.4g}")

    verdict = "qa-passed" if (eq_ok and not discr) else "qa-fail"
    return QAReport(verdict=verdict, equilibrium_ok=eq_ok, discrepancies=discr, detail={"equilibrium_residual": resid})
