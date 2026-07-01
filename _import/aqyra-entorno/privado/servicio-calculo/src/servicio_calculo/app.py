"""Núcleo de routing del servicio de cálculo (anzuelo). SIN dependencia de HTTP.

Cada handler toma el `payload` (dict del visor) y devuelve `(status, body)`. Así el
servidor stdlib (`server.py`) es una cáscara fina y los tests ejercitan los handlers
directamente, inyectando productor/solver falsos (no requieren PyNite instalado).

Flujo de las DOS LLAVES (D-021/D-023), una transición por endpoint:
  /solve  -> `computed`        (0 llaves; el motor calculó, NO es verdad)
  /qa     -> `qa-passed`/None  (1.ª llave: QA independiente; None = bloqueo qa-fail)
  /sign   -> `verified-signed` (2.ª llave: firma de JM; exige `qa-passed`)
  /ec3    -> rellena aprovechamiento + «qué no cumple» (no cambia de estado)
El verde SOLO lo acuña /sign. Ningún otro endpoint devuelve `verified-signed`.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Callable, Optional

from firma import SigningError, sign_result
from puente_calculo import contract as c
from qa_pynite import run_qa
from verificacion_ec import apply_ec3_checks, critical_members

from . import producer as prod
from .serialize import (
    result_group_from_dict,
    result_group_to_dict,
    sections_from_model,
)

CRITICAL_THRESHOLD = 0.9  # «al límite»: u > 0,9 (el visor lo resalta)


def _meta(producer_id: str) -> dict[str, Any]:
    """Bandera de gobierno que acompaña a /solve y /qa: ¿provisional?, ¿independiente?"""
    provisional = producer_id == prod.PROVISIONAL_ID
    return {
        "producer": producer_id,
        "provisional": provisional,
        # Independencia de la 2.ª llave (D-023): falsa mientras productor y QA sean
        # el MISMO motor (PyNite). El gate de equilibrio sí es significativo.
        "independent": not provisional,
        "warning": prod.PROVISIONAL_WARNING if provisional else "",
    }


def _summary(rg: c.ResultGroup, not_passing: list[str], at_limit: list[str]) -> dict[str, Any]:
    return {
        "combinationId": rg.combinationId,
        "state": rg.state,
        "atLimit": len(at_limit),
        "atLimitIds": at_limit,
        "notPassing": len(not_passing),
        "notPassingIds": not_passing,
    }


# ── /solve ─────────────────────────────────────────────────────────────────────
def handle_solve(
    payload: dict[str, Any],
    *,
    producer: prod.Producer = prod.default_producer,
    producer_id: str = prod.PROVISIONAL_ID,
) -> tuple[int, dict[str, Any]]:
    """Resuelve el modelo -> grupos `computed` con aprovechamiento EC3 ya relleno."""
    req = c.request_from_dict(payload)
    groups = producer(req)
    sections = sections_from_model(req.model)
    out_groups, summaries = [], []
    for rg in groups:
        not_passing = apply_ec3_checks(rg, sections)  # muta utilization/governing/passes
        at_limit = critical_members(rg, CRITICAL_THRESHOLD)
        out_groups.append(result_group_to_dict(rg))
        summaries.append(_summary(rg, not_passing, at_limit))
    return 200, {"groups": out_groups, "summary": summaries, "meta": _meta(producer_id)}


# ── /ec3 (recomprobación de aprovechamiento sobre un grupo dado) ────────────────
def handle_ec3(payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    req = c.request_from_dict(payload)
    rg = result_group_from_dict(payload["group"])
    sections = sections_from_model(req.model)
    not_passing = apply_ec3_checks(rg, sections)
    at_limit = critical_members(rg, CRITICAL_THRESHOLD)
    return 200, {"group": result_group_to_dict(rg), "summary": _summary(rg, not_passing, at_limit)}


# ── /qa (1.ª llave) ─────────────────────────────────────────────────────────────
def handle_qa(
    payload: dict[str, Any],
    *,
    qa_solver: Optional[Callable[[c.CalcRequest, str], c.ResultGroup]] = None,
    producer_id: str = prod.PROVISIONAL_ID,
) -> tuple[int, dict[str, Any]]:
    """Gate de equilibrio + re-cálculo QA + reconciliación. `qa-passed` o bloqueo.

    El grupo del motor llega de /solve con aprovechamiento EC3 ya relleno, así que
    el re-cálculo QA recibe el MISMO criterio EC3 (mismas `sections`) para que la
    reconciliación del aprovechamiento compare like-con-like (no un falso qa-fail).
    """
    req = c.request_from_dict(payload)
    motor_result = result_group_from_dict(payload["group"])
    sections = sections_from_model(req.model)
    base_solver = qa_solver
    if base_solver is None:  # default real: PyNite (importación perezosa)
        from qa_pynite import solve_pynite
        base_solver = solve_pynite

    def solver_with_ec3(rq: c.CalcRequest, combo_id: str) -> c.ResultGroup:
        g = base_solver(rq, combo_id)  # type: ignore[misc]
        apply_ec3_checks(g, sections)  # mismo criterio EC3 que el motor
        return g

    report, elevated = run_qa(req, motor_result, solver=solver_with_ec3)
    body: dict[str, Any] = {
        "verdict": report.verdict,
        "report": asdict(report),
        "group": result_group_to_dict(elevated) if elevated is not None else None,
        "meta": _meta(producer_id),
    }
    return 200, body


# ── /sign (2.ª llave · única fuente de verified-signed) ─────────────────────────
def handle_sign(payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    signer = payload.get("signer") or payload.get("by")
    if not signer:
        return 400, {"error": "falta 'signer' (la firma identifica a quien acuña la 2.ª llave; la IA no firma)."}
    rg = result_group_from_dict(payload["group"])
    try:
        signed, record = sign_result(rg, signer)
    except SigningError as exc:
        # 409: no se puede firmar lo que no pasó la QA (1.ª llave). Estado preservado.
        return 409, {"error": str(exc), "state": rg.state}
    return 200, {"group": result_group_to_dict(signed), "record": asdict(record)}


# ── /health ─────────────────────────────────────────────────────────────────────
def handle_health() -> tuple[int, dict[str, Any]]:
    try:
        import Pynite  # noqa: F401  (productor/QA provisional)
        pynite = True
    except Exception:  # noqa: BLE001
        pynite = False
    return 200, {"ok": True, "service": "servicio-calculo", "pyniteAvailable": pynite, "meta": _meta(prod.PROVISIONAL_ID)}


#: Tabla (método, ruta) -> handler sin argumentos extra (el servidor pasa el payload).
ROUTES: dict[tuple[str, str], Callable[..., tuple[int, dict[str, Any]]]] = {
    ("POST", "/solve"): handle_solve,
    ("POST", "/ec3"): handle_ec3,
    ("POST", "/qa"): handle_qa,
    ("POST", "/sign"): handle_sign,
}
