"""Puerto al motor de calculo anclado + modelo/result neutros del motor.

El adaptador consume `motor-fem 0.1.0` ANCLADO (../../integracion/versions.lock)
a traves de `MotorFemPort` (puerto): no lo bifurca. El `EngineModel`/`EngineResult`
hablan la convencion de LETRAS del motor/PyNite (Iy=debil, Iz=fuerte; Dxi..Rzj;
FX/FY/FZ); `translate.py` produce el EngineModel y `adapter.py` mapea el
EngineResult de vuelta al esquema PUBLICO por ROL (D-018), alineando N>0 traccion.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


# ── Entrada del motor (letras PyNite) ──────────────────────────────────────────
@dataclass
class EngineNode:
    id: str
    x: float
    y: float
    z: float
    # apoyo: GdL RESTRINGIDO (True=coaccionado) — convenio def_support de PyNite.
    support: tuple[bool, bool, bool, bool, bool, bool] = (False,) * 6  # DX,DY,DZ,RX,RY,RZ


@dataclass
class EngineMember:
    id: str
    i: str
    j: str
    E: float
    G: float
    A: float
    Iy: float  # inercia eje DEBIL (PyNite y)
    Iz: float  # inercia eje FUERTE (PyNite z)
    J: float
    rotation: float = 0.0  # orientacion de seccion (grados) que ancla que eje es el fuerte
    # releases: GdL LIBERADO (True=liberado) en orden Dxi,Dyi,Dzi,Rxi,Ryi,Rzi, Dxj..Rzj.
    releases: tuple[bool, ...] = (False,) * 12


@dataclass
class EngineLoad:
    kind: str  # "node" | "member_dist" | "member_point"
    target: str
    direction: str  # "FX" | "FY" | "FZ" (global)
    value: float  # con signo global (gravedad ya viene como FZ negativa)
    case: str


@dataclass
class EngineCombo:
    name: str
    factors: dict[str, float]  # {caseId: factor}


@dataclass
class EngineModel:
    nodes: list[EngineNode] = field(default_factory=list)
    members: list[EngineMember] = field(default_factory=list)
    loads: list[EngineLoad] = field(default_factory=list)
    combos: list[EngineCombo] = field(default_factory=list)


# ── Salida del motor (letras PyNite) ───────────────────────────────────────────
@dataclass
class EngineStation:
    x: float
    axial: float  # con su signo nativo del motor (ver MotorFemPort.axial_tension_positive)
    Fy: float
    Fz: float
    Mx: float
    My: float
    Mz: float
    dx: float
    dy: float
    dz: float


@dataclass
class EngineMemberResult:
    id: str
    stations: list[EngineStation]


@dataclass
class EngineNodeResult:
    id: str
    DX: float
    DY: float
    DZ: float
    RX: float
    RY: float
    RZ: float
    # reaccion (FX,FY,FZ,MX,MY,MZ) solo en nudos con apoyo, o None.
    reaction: tuple[float, float, float, float, float, float] | None = None


@dataclass
class EngineResult:
    members: list[EngineMemberResult] = field(default_factory=list)
    nodes: list[EngineNodeResult] = field(default_factory=list)


class MotorFemPort(Protocol):
    """Puerto del motor. Implementaciones: `MotorFemBinding` (motor-fem anclado) y
    `FakeMotor` (test)."""

    #: True si el motor reporta el axil con TRACCION positiva (D-018 N>0 traccion).
    #: Si False, el adaptador NEGA el axil para cumplir el convenio del contrato.
    axial_tension_positive: bool

    def solve(self, model: EngineModel, combo_name: str) -> EngineResult:
        ...


class MotorFemBinding:
    """Binding al `motor-fem 0.1.0` ANCLADO. Se consume, no se bifurca.

    El ENSAMBLADO de la peticion y el PARSEO de la respuesta estan completos y
    testeados (`motor_request.to_request`/`from_response`, contrato neutro JSON-able).
    Lo unico que depende de la API real del motor (no vendorizado en este repo) es el
    NOMBRE del *entrypoint*: por defecto `motor_fem.<entrypoint>(request) -> response`
    con `entrypoint="solve"`. Si la firma real difiere, se ajusta SOLO ese punto.
    No se finge calculo: si el motor no esta o no expone el entrypoint, falla claro.
    """

    #: PyNite/motor-fem suelen reportar el axil con traccion negativa; el adaptador
    #: usa este flag para alinear a N>0 traccion (D-018). Confirmar con motor-fem.
    axial_tension_positive = False

    def __init__(self, *, entrypoint: str = "solve") -> None:
        self.entrypoint = entrypoint
        try:
            import motor_fem  # type: ignore  # noqa: F401
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "motor-fem 0.1.0 no esta instalado: anclalo desde integracion/versions.lock "
                "en el entorno de calculo. El visor (cebo) sigue sin servidor para VER; "
                "solo el POST llama a este servicio (D-019.C.4)."
            ) from exc
        self._motor = motor_fem
        if not hasattr(self._motor, entrypoint):
            raise RuntimeError(
                f"motor-fem no expone el entrypoint '{entrypoint}'. Ajusta `entrypoint=` al "
                "nombre real de su funcion de resolucion. Contrato peticion/respuesta en "
                "motor_request.py (forma neutra JSON-able)."
            )

    def solve(self, model: EngineModel, combo_name: str) -> EngineResult:
        from .motor_request import from_response, to_request

        request = to_request(model, combo_name)
        response = getattr(self._motor, self.entrypoint)(request)
        if not isinstance(response, dict):
            raise TypeError(
                f"motor-fem.{self.entrypoint} devolvio {type(response).__name__}; se esperaba el "
                "dict de respuesta (ver contrato en motor_request.py)."
            )
        return from_response(response)
