"""Adaptador del contrato C5 (anzuelo). Superficie publica del paquete."""
from __future__ import annotations

from . import contract
from .adapter import map_result, solve_json, solve_request
from .engine import (
    EngineMember,
    EngineMemberResult,
    EngineModel,
    EngineNode,
    EngineNodeResult,
    EngineResult,
    EngineStation,
    MotorFemBinding,
    MotorFemPort,
)
from .motor_request import from_response, to_request
from .translate import to_engine_model
from .writeback import append_to_ifc, result_group_to_ifc_text

__all__ = [
    "contract",
    "solve_request",
    "solve_json",
    "map_result",
    "to_engine_model",
    "to_request",
    "from_response",
    "EngineModel",
    "EngineNode",
    "EngineMember",
    "EngineResult",
    "EngineNodeResult",
    "EngineMemberResult",
    "EngineStation",
    "MotorFemPort",
    "MotorFemBinding",
    "append_to_ifc",
    "result_group_to_ifc_text",
]
