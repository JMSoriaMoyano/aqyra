"""Servicio de cálculo LOCAL (anzuelo · D-019·C.4). Envuelve el pipeline privado
(produce -> QA -> EC3 -> firma) en endpoints HTTP que el post-proceso del visor llama.
El visor (cebo) sigue sin servidor para VER; solo el POST llama aquí.
"""
from __future__ import annotations

from .app import handle_ec3, handle_health, handle_qa, handle_sign, handle_solve
from .producer import (
    PROVISIONAL_ID,
    PROVISIONAL_WARNING,
    Producer,
    default_producer,
    motorfem_producer,
    pynite_producer,
)
from .server import serve

__all__ = [
    "handle_solve",
    "handle_qa",
    "handle_sign",
    "handle_ec3",
    "handle_health",
    "serve",
    "Producer",
    "default_producer",
    "pynite_producer",
    "motorfem_producer",
    "PROVISIONAL_ID",
    "PROVISIONAL_WARNING",
]
