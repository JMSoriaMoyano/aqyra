"""Aprovechamiento EC3 (acero) — CRITERIO normativo = ANZUELO (privado · D-022).

Comprobacion de seccion EN 1993-1-1 §6.2 (Anejo Nacional espanol, gamma_M0=1.05):
  Npl,Rd = A*fy/gamma_M0 ; Mc,Rd = Wpl*fy/gamma_M0 (clase 1/2; Wel si no hay Wpl).
  Interaccion LINEAL conservadora (§6.2.1(7)): u = |N|/Npl,Rd + |My|/Mcy,Rd + |Mz|/Mcz,Rd.
Es el SUELO de V3 (verificacion + «que no cumple»); el armado EC2 y el pandeo de
barra (§6.3) son incrementos posteriores. En produccion, el `Ec3CheckPort` se
cablea a la skill anclada `estructuras-eurocodigos 0.1.0` (versions.lock); aqui
una implementacion de referencia, testeable, con la misma interfaz.

Unidades SI del proyecto: N en kN, M en kN·m, A en m², W en m³, fy en kN/m².
"""
from __future__ import annotations

from typing import Optional, Protocol

GAMMA_M0 = 1.05  # Anejo Nacional espanol para EN 1993-1-1


def ec3_section_utilization(
    *,
    N: float,
    M_strong: float,
    M_weak: float = 0.0,
    A: float,
    fy: float,
    Wpl_strong: Optional[float] = None,
    Wel_strong: Optional[float] = None,
    Wpl_weak: Optional[float] = None,
    Wel_weak: Optional[float] = None,
    gamma_M0: float = GAMMA_M0,
) -> tuple[float, str, bool]:
    """Aprovechamiento de seccion EC3 §6.2. Devuelve (u, gobernante, cumple)."""
    terms: list[tuple[str, float]] = []
    npl = A * fy / gamma_M0
    if npl > 0:
        terms.append(("axil" + (" (traccion)" if N >= 0 else " (compresion)"), abs(N) / npl))
    Ws = Wpl_strong if Wpl_strong else Wel_strong
    if Ws:
        terms.append(("flexion eje fuerte", abs(M_strong) / (Ws * fy / gamma_M0)))
    Ww = Wpl_weak if Wpl_weak else Wel_weak
    if Ww:
        terms.append(("flexion eje debil", abs(M_weak) / (Ww * fy / gamma_M0)))
    if not terms:
        return 0.0, "sin datos (faltan A·fy/W)", True
    u = sum(t for _, t in terms)  # interaccion lineal conservadora
    governing = max(terms, key=lambda x: x[1])[0]
    return u, governing, u <= 1.0


class Ec3CheckPort(Protocol):
    """Puerto de comprobacion EC3. En produccion: skill `estructuras-eurocodigos`."""

    def utilization(self, *, N: float, M_strong: float, M_weak: float, A: float, fy: float,
                    Wpl_strong: Optional[float], Wpl_weak: Optional[float]) -> tuple[float, str, bool]:
        ...


class SimpleEc3Check:
    """Implementacion de referencia (seccion §6.2). Reemplazable por la skill anclada."""

    def __init__(self, gamma_M0: float = GAMMA_M0) -> None:
        self.gamma_M0 = gamma_M0

    def utilization(self, *, N, M_strong, M_weak, A, fy, Wpl_strong, Wpl_weak):
        return ec3_section_utilization(
            N=N, M_strong=M_strong, M_weak=M_weak, A=A, fy=fy,
            Wpl_strong=Wpl_strong, Wpl_weak=Wpl_weak, gamma_M0=self.gamma_M0,
        )


def _section_data(member, sections: dict) -> Optional[dict]:
    """Extrae {A, fy, Wpl_strong, Wpl_weak, Wel_*} para una barra. Tolerante: lee de
    `sections[memberId]` (dict) o del contrato via getattr (sin acoplar a su version)."""
    s = sections.get(member.memberId)
    if s is not None:
        return s
    return None


def apply_ec3_checks(result_group, sections: dict, *, checker: Optional[Ec3CheckPort] = None) -> list[str]:
    """Rellena utilization/governing/passes de cada MemberResult (peor estacion) y
    devuelve la lista «QUE NO CUMPLE» (memberId con u>1). Muta el result_group.

    `sections`: {memberId: {"A":..,"fy":..,"Wpl_strong":..,"Wpl_weak":..,"Wel_strong":..,"Wel_weak":..}}.
    """
    chk = checker or SimpleEc3Check()
    no_cumple: list[str] = []
    for m in result_group.members:
        sd = _section_data(m, sections)
        if sd is None or not m.stations:
            continue
        worst_u, worst_gov, worst_pass = 0.0, "—", True
        for st in m.stations:
            u, gov, ok = chk.utilization(
                N=st.N, M_strong=st.M_strong, M_weak=st.M_weak,
                A=sd["A"], fy=sd["fy"],
                Wpl_strong=sd.get("Wpl_strong") or sd.get("Wel_strong"),
                Wpl_weak=sd.get("Wpl_weak") or sd.get("Wel_weak"),
            )
            if u > worst_u:
                worst_u, worst_gov, worst_pass = u, gov, ok
        m.utilization = worst_u
        m.governing = worst_gov
        m.passes = worst_pass
        if not worst_pass:
            no_cumple.append(m.memberId)
    return no_cumple


def critical_members(result_group, threshold: float = 0.9) -> list[str]:
    """Elementos «al limite» (u > umbral): los que el visor resalta."""
    return [m.memberId for m in result_group.members if m.utilization > threshold]
