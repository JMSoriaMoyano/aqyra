"""Orquestacion de la QA (1.a llave · D-023).

run_qa: gate de equilibrio -> re-calculo INDEPENDIENTE con PyNite -> reconciliacion.
- qa-passed: devuelve el resultado del motor ELEVADO a state="qa-passed" (1.a llave
  puesta; falta la firma de JM para verified-signed).
- qa-fail: BLOQUEA (devuelve None como resultado elevado): el visor NO puede pintar
  qa-passed ni certificado. La discrepancia queda EXPUESTA en el QAReport (anulacion
  documentada, D-023.C.4.a). La IA opera; JM firma. El verde solo lo acuna la firma.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Callable

from puente_calculo import contract as c

from .pynite_solver import solve_pynite
from .reconcile import QAReport, reconcile

Solver = Callable[[c.CalcRequest, str], c.ResultGroup]


def run_qa(
    req: c.CalcRequest,
    motor_result: c.ResultGroup,
    *,
    solver: Solver = solve_pynite,
) -> tuple[QAReport, c.ResultGroup | None]:
    """Devuelve (report, resultado_elevado_o_None). None = bloqueo (qa-fail)."""
    qa_result = solver(req, motor_result.combinationId)
    report = reconcile(req, motor_result, qa_result)
    if report.verdict == "qa-passed":
        return report, replace(motor_result, state="qa-passed")
    return report, None  # bloqueo: nunca se eleva un resultado discrepante
