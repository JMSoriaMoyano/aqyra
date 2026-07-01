"""Espejo Python del contrato C5 (publico/openbim/src/index.ts).

Son los MISMOS tipos que el visor serializa (entrada) y consume (salida); aqui
en dataclasses para el adaptador privado. Mantener sincronizado con el contrato
publico (SemVer; MAJOR = rotura). Unidades SI del proyecto: m, kN; frame Z-up,
gravedad -Z (D-018). Ejes locales por ROL (axis/strong/weak), nunca por letra.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

# Estados de dato (D-021): las dos llaves. El adaptador SOLO produce "computed".
DataState = str  # "proposal" | "computed" | "qa-passed" | "verified-signed"


# ── Entrada ───────────────────────────────────────────────────────────────────
@dataclass
class Node:
    id: str
    x: float
    y: float
    z: float


@dataclass
class SectionProps:
    A: float
    I_strong: float
    I_weak: float
    J: float
    Av_strong: Optional[float] = None
    Av_weak: Optional[float] = None
    # Modulos resistentes (m3) para EC3 (D-022); opcionales.
    Wel_strong: Optional[float] = None
    Wpl_strong: Optional[float] = None
    Wel_weak: Optional[float] = None
    Wpl_weak: Optional[float] = None


@dataclass
class MaterialProps:
    E: float
    G: float
    density: float
    fy_or_fck: float


@dataclass
class SectionRef:
    profile: str = ""
    material: Optional[str] = None
    props: Optional[SectionProps] = None
    materialProps: Optional[MaterialProps] = None


@dataclass
class MemberEndRelease:
    axial: bool = False
    vStrong: bool = False
    vWeak: bool = False
    torsion: bool = False
    mStrong: bool = False
    mWeak: bool = False


@dataclass
class MemberReleases:
    i: Optional[MemberEndRelease] = None
    j: Optional[MemberEndRelease] = None


@dataclass
class Member:
    id: str
    kind: str
    nodeStart: str
    nodeEnd: str
    section: Optional[SectionRef] = None
    releases: Optional[MemberReleases] = None
    ifcGlobalId: Optional[str] = None


@dataclass
class Restraints:
    ux: bool
    uy: bool
    uz: bool
    rx: bool
    ry: bool
    rz: bool


@dataclass
class Support:
    id: str
    nodeId: str
    restraints: Restraints
    state: DataState = "proposal"


@dataclass
class Load:
    id: str
    kind: str  # "point" | "distributed"
    target: str  # nodeId (point) o memberId (distributed)
    value: float
    direction: str = "z"  # "x" | "y" | "z" (gravedad por defecto = -Z, D-018)
    case: Optional[str] = None
    state: DataState = "proposal"


@dataclass
class SurfaceAreaLoad:
    q: float
    case: Optional[str] = None
    distributeTo: str = "edges"  # "edges" | "nodes"


@dataclass
class Surface:
    id: str
    kind: str
    ifcType: str = ""
    outline: list[list[float]] = field(default_factory=list)
    area: Optional[float] = None
    areaLoad: Optional[SurfaceAreaLoad] = None
    # nudos/barras de borde para repartir la carga por area (si el visor los aporta)
    edgeMembers: list[str] = field(default_factory=list)
    edgeNodes: list[str] = field(default_factory=list)


@dataclass
class Combination:
    id: str
    name: str
    limitState: str  # "ULS" | "SLS" | "seismic"
    terms: dict[str, float] = field(default_factory=dict)  # {caseId: factor}
    expression: str = ""


@dataclass
class StructuralModel:
    nodes: list[Node] = field(default_factory=list)
    members: list[Member] = field(default_factory=list)
    surfaces: list[Surface] = field(default_factory=list)
    supports: list[Support] = field(default_factory=list)
    loads: list[Load] = field(default_factory=list)
    state: DataState = "proposal"


@dataclass
class CalcRequest:
    model: StructuralModel
    combinations: list[Combination] = field(default_factory=list)


# ── Salida (esquema de resultados, D-019·B.3) ──────────────────────────────────
@dataclass
class MemberStation:
    x: float
    N: float  # axil (kN); N>0 = traccion (D-018)
    V_strong: float
    V_weak: float
    M_strong: float
    M_weak: float
    T: float
    dx: float
    dy: float
    dz: float


@dataclass
class MemberResult:
    memberId: str
    stations: list[MemberStation]
    utilization: float = 0.0  # comprobacion EC3 = paso 5/D-022; aqui 0 si no hay checker
    governing: Optional[str] = None
    passes: bool = True


@dataclass
class NodeReaction:
    fx: float
    fy: float
    fz: float
    mx: float
    my: float
    mz: float


@dataclass
class NodeResult:
    nodeId: str
    ux: float
    uy: float
    uz: float
    rx: float
    ry: float
    rz: float
    reaction: Optional[NodeReaction] = None


@dataclass
class SurfaceResult:
    surfaceId: str
    membrane: dict[str, float]
    plate: dict[str, float]


@dataclass
class ResultGroup:
    id: str
    combinationId: str
    state: DataState  # nace "computed"
    members: list[MemberResult] = field(default_factory=list)
    nodes: list[NodeResult] = field(default_factory=list)
    surfaces: list[SurfaceResult] = field(default_factory=list)


# ── Parsers from_dict (el JSON que serializa el visor) ─────────────────────────
def _release(d: Optional[dict[str, Any]]) -> Optional[MemberEndRelease]:
    if not d:
        return None
    return MemberEndRelease(
        axial=bool(d.get("axial")), vStrong=bool(d.get("vStrong")), vWeak=bool(d.get("vWeak")),
        torsion=bool(d.get("torsion")), mStrong=bool(d.get("mStrong")), mWeak=bool(d.get("mWeak")),
    )


def _section(d: Optional[dict[str, Any]]) -> Optional[SectionRef]:
    if not d:
        return None
    p = d.get("props")
    m = d.get("materialProps")
    return SectionRef(
        profile=d.get("profile", ""),
        material=d.get("material"),
        props=SectionProps(
            A=p["A"], I_strong=p["I_strong"], I_weak=p["I_weak"], J=p["J"],
            Av_strong=p.get("Av_strong"), Av_weak=p.get("Av_weak"),
            Wel_strong=p.get("Wel_strong"), Wpl_strong=p.get("Wpl_strong"),
            Wel_weak=p.get("Wel_weak"), Wpl_weak=p.get("Wpl_weak"),
        ) if p else None,
        materialProps=MaterialProps(E=m["E"], G=m["G"], density=m["density"], fy_or_fck=m["fy_or_fck"]) if m else None,
    )


def model_from_dict(d: dict[str, Any]) -> StructuralModel:
    return StructuralModel(
        nodes=[Node(n["id"], n["x"], n["y"], n["z"]) for n in d.get("nodes", [])],
        members=[
            Member(
                id=m["id"], kind=m.get("kind", "member"), nodeStart=m["nodeStart"], nodeEnd=m["nodeEnd"],
                section=_section(m.get("section")),
                releases=MemberReleases(i=_release((m.get("releases") or {}).get("i")), j=_release((m.get("releases") or {}).get("j")))
                if m.get("releases") else None,
                ifcGlobalId=m.get("ifcGlobalId"),
            )
            for m in d.get("members", [])
        ],
        surfaces=[
            Surface(
                id=s["id"], kind=s.get("kind", "diaphragm"), ifcType=s.get("ifcType", ""),
                outline=s.get("outline", []), area=s.get("area"),
                areaLoad=SurfaceAreaLoad(q=s["areaLoad"]["q"], case=s["areaLoad"].get("case"), distributeTo=s["areaLoad"].get("distributeTo", "edges"))
                if s.get("areaLoad") else None,
                edgeMembers=s.get("edgeMembers", []), edgeNodes=s.get("edgeNodes", []),
            )
            for s in d.get("surfaces", [])
        ],
        supports=[
            Support(id=s["id"], nodeId=s["nodeId"], restraints=Restraints(**s["restraints"]), state=s.get("state", "proposal"))
            for s in d.get("supports", [])
        ],
        loads=[
            Load(id=l["id"], kind=l["kind"], target=l["target"], value=l["value"],
                 direction=l.get("direction", "z"), case=l.get("case"), state=l.get("state", "proposal"))
            for l in d.get("loads", [])
        ],
        state=d.get("state", "proposal"),
    )


def request_from_dict(d: dict[str, Any]) -> CalcRequest:
    return CalcRequest(
        model=model_from_dict(d.get("model", d)),
        combinations=[
            Combination(id=c["id"], name=c.get("name", c["id"]), limitState=c.get("limitState", "ULS"),
                        terms=dict(c.get("terms", {})), expression=c.get("expression", ""))
            for c in d.get("combinations", [])
        ],
    )
