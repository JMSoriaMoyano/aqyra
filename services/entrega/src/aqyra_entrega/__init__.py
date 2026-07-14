# -*- coding: utf-8 -*-
"""aqyra-entrega — operador C7: orquestador DETERMINISTA de la ENTREGA de entregables firmables.

Envuelve documentos/export.componer_export sobre cada entregable de una `solicitud-entrega` y emite
UN `manifiesto-entrega` maestro con roll-up. La IA propone la solicitud (fuera); C7 la valida y la
ejecuta reproducible; JM firma (dos llaves). NO certifica.
"""
from __future__ import annotations

from .entrega import (
    componer_entrega,
    sha_por_bundle,
    NOMBRE_MANIFIESTO_ENTREGA,
    NOMBRE_MANIFIESTO_BUNDLE,
)
from . import manifiesto_entrega

__all__ = [
    "componer_entrega",
    "sha_por_bundle",
    "manifiesto_entrega",
    "NOMBRE_MANIFIESTO_ENTREGA",
    "NOMBRE_MANIFIESTO_BUNDLE",
]

__version__ = "0.1.0"
