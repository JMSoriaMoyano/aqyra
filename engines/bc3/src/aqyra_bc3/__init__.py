# -*- coding: utf-8 -*-
"""aqyra_bc3 — adaptador de interoperabilidad FIEBDC-3/2024 (.bc3) <-> Aqyra.

Capacidad de frontera (C1/C5), traducción DETERMINISTA en las dos direcciones:
- E0.1 (ingesta):  `ingerir_bc3(path) -> banco.json` (pack `banco`, esquema AQ-DEMO).
- E0.2 (emisión):  `emitir_bc3(salida) -> .bc3`  (gancho forward — siguiente change del hilo).

Texto puro (stdlib): corre en el sandbox y en CI sin ifcopenshell. Releaseable
(tag = Llave 2 de JM) cuando la interoperabilidad cierre; v0 SIN release.
"""
from .bc3 import ingerir_bc3, serializar_banco, NATURALEZA, CHARSETS

__version__ = "0.1.0"

__all__ = ["ingerir_bc3", "serializar_banco", "NATURALEZA", "CHARSETS", "__version__"]
