# -*- coding: utf-8 -*-
"""aqyra-documento-export — capa TRANSVERSAL de export firmable (el muro de cobro).

Nucleo generico (descriptor + manifiesto + sellado + firma) + consumidores por tipo de artefacto. El
PRIMARIO es CONTRACTUAL: `presupuesto-obra` (presupuesto por partidas + cuadros + medicion + BC3). La
`proyeccion-valor` queda como export de gestion. Dos llaves: integridad en el gate (Llave 1) + firma
GPG de JM en el release (Llave 2).
"""
from __future__ import annotations

from .export import componer_export, consumidor_de, NOMBRE_MANIFIESTO
from .manifiesto import construir_manifiesto, serializar, integridad, hash_canonico
from .firma import estado_firmable, es_certificado, firmar_detached
from . import presupuesto_doc, pliego_doc, proyeccion

__all__ = [
    "componer_export", "consumidor_de", "construir_manifiesto", "serializar", "integridad",
    "hash_canonico", "estado_firmable", "es_certificado", "firmar_detached", "NOMBRE_MANIFIESTO",
    "presupuesto_doc", "pliego_doc", "proyeccion",
]
__version__ = "0.1.0"
