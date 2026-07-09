# -*- coding: utf-8 -*-
"""aqyra_bc3 — adaptador de interoperabilidad FIEBDC-3/2024 (.bc3) <-> Aqyra.

Capacidad de frontera (C1/C5), traducción DETERMINISTA en las dos direcciones:
- E0.1 (ingesta):  `ingerir_bc3(path) -> banco.json` (pack `banco`, esquema AQ-DEMO).
- E0.2 (emisión):  `emitir_bc3(salida) -> .bc3` (FIEBDC-3/2024) + `leer_bc3_presupuesto`
                   (re-lector del round-trip: .bc3 -> estado_mediciones).

Con E0.2 cierra la Ola 1: el presupuesto ENTRA y SALE del formato del despacho y de
la licitación pública. Texto puro (stdlib): corre en el sandbox y en CI sin
ifcopenshell. Releaseable (tag = Llave 2 de JM) cuando la interoperabilidad cierre;
v0 SIN release.
"""
from .bc3 import (
    ingerir_bc3, serializar_banco, emitir_bc3, leer_bc3_presupuesto,
    NATURALEZA, CHARSETS,
)

__version__ = "0.2.0"

__all__ = [
    "ingerir_bc3", "serializar_banco", "emitir_bc3", "leer_bc3_presupuesto",
    "NATURALEZA", "CHARSETS", "__version__",
]
