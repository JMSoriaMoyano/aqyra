"""Firma de JM (2.a llave). Unica fuente de verified-signed (D-021/D-023)."""
from __future__ import annotations

from .sign import SignatureRecord, SigningError, sign_result

__all__ = ["sign_result", "SignatureRecord", "SigningError"]
