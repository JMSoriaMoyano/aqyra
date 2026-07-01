"""Write-back de resultados al IFC, alineado a IfcStructuralResultGroup.

Persiste los resultados como anejo DIFF-ABLE (mecanismo *append* de D-013),
mapeado al StructuralAnalysisDomain: `IfcStructuralResultGroup` agrupa los
resultados (`ResultGroupFor` -> modelo de analisis) y las reacciones de apoyo son
`IfcStructuralReaction`. Cada bloque lleva su ESTADO (D-021): mientras no sea
`verified-signed`, sale ESTAMPADO «NO VERIFICADO» (guarda de exportacion, D-021.C.2).
Es texto STEP-comment + lineas clave=valor: legible y diff-able; la emision nativa
de entidades IFC queda como refinamiento (la forma ya espeja el estandar).
"""
from __future__ import annotations

from . import contract as c


def _stamp(state: str) -> str:
    if state == "verified-signed":
        return ""
    return f" [NO VERIFICADO · estado={state} · sin firma de JM]"


def result_group_to_ifc_text(rg: c.ResultGroup, *, model_name: str = "modelo") -> str:
    """Devuelve el bloque de anejo (texto) a *append* en la seccion DATA del IFC."""
    lines: list[str] = []
    lines.append("/* ====== AQYRA · IfcStructuralResultGroup (anejo diff-able) ====== */")
    lines.append(f"/* modelo={model_name} · combinacion={rg.combinationId} · estado={rg.state}{_stamp(rg.state)} */")
    lines.append(f"AQYRA-RESULTGROUP;id={rg.id};combination={rg.combinationId};state={rg.state};theory=FIRST_ORDER")
    for m in rg.members:
        # esfuerzos extremos por barra (signos D-018: N>0 traccion)
        nmax = max((s.N for s in m.stations), default=0.0)
        nmin = min((s.N for s in m.stations), default=0.0)
        msmax = max((abs(s.M_strong) for s in m.stations), default=0.0)
        lines.append(
            f"AQYRA-MEMBERRESULT;member={m.memberId};N_max={nmax:.4g};N_min={nmin:.4g};"
            f"M_strong_max={msmax:.4g};util={m.utilization:.4g};passes={int(m.passes)}"
        )
    for n in rg.nodes:
        if n.reaction is not None:
            r = n.reaction
            # IfcStructuralReaction: reaccion en el apoyo (componentes globales)
            lines.append(
                f"AQYRA-REACTION;node={n.nodeId};FX={r.fx:.4g};FY={r.fy:.4g};FZ={r.fz:.4g};"
                f"MX={r.mx:.4g};MY={r.my:.4g};MZ={r.mz:.4g};state={rg.state}"
            )
    lines.append("/* ====== fin AQYRA ResultGroup ====== */")
    return "\n".join(lines) + "\n"


def append_to_ifc(ifc_text: str, rg: c.ResultGroup, *, model_name: str = "modelo") -> str:
    """Inserta el anejo de resultados tras `DATA;` (diff-able, no rompe el parseo)."""
    block = "\n" + result_group_to_ifc_text(rg, model_name=model_name)
    i = ifc_text.find("DATA;")
    if i == -1:
        return ifc_text + block
    cut = i + len("DATA;")
    return ifc_text[:cut] + block + ifc_text[cut:]
