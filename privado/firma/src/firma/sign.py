"""Firma de JM — la 2.a LLAVE (D-021/D-023). UNICA fuente de `verified-signed`.

Regla inviolable: SOLO se puede firmar un resultado que YA tiene la 1.a llave
(`qa-passed`, QA independiente). La firma lo eleva a `verified-signed` (contractual).
El visor pinta el verde SOLO con este estado; el render publico nunca lo acuña.
La IA opera; **JM firma** — esta funcion representa esa accion de gobierno.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone

from puente_calculo import contract as c


class SigningError(RuntimeError):
    """Se intento firmar algo que no ha pasado la QA (1.a llave)."""


@dataclass
class SignatureRecord:
    signer: str
    timestamp: str  # ISO-8601 UTC
    combinationId: str
    resultGroupId: str


def sign_result(rg: c.ResultGroup, signer: str, *, timestamp: str | None = None) -> tuple[c.ResultGroup, SignatureRecord]:
    """Eleva un resultado `qa-passed` a `verified-signed`. Falla si no esta `qa-passed`."""
    if rg.state != "qa-passed":
        raise SigningError(
            f"no se puede firmar un resultado en estado '{rg.state}': se requiere 'qa-passed' "
            "(1.a llave, QA independiente) antes de la firma de JM (2.a llave)."
        )
    ts = timestamp or datetime.now(timezone.utc).isoformat()
    signed = replace(rg, state="verified-signed")
    record = SignatureRecord(signer=signer, timestamp=ts, combinationId=rg.combinationId, resultGroupId=rg.id)
    return signed, record
