"""Acceso al Maestro federado para el engine C3 (D7).

Abre el IFC derivado (la vista del Maestro, D26/D30 de C4) y reconstruye la PROCEDENCIA por
modelo desde el manifiesto (fuente de verdad, D1 de C4): el derivado FUNDE los modelos en un solo
IFC preservando los GUIDs (dedup=nunca, D28), pero no marca de qué modelo vino cada elemento; el
manifiesto sí lo declara. Este módulo no reimplementa federación: solo lee los GUIDs de las
fuentes declaradas para poder repartir el veredicto `por_modelo`.
"""
from __future__ import annotations

from pathlib import Path

import ifcopenshell
import ifcopenshell.util.element as _ue


def abrir(path) -> "ifcopenshell.file":
    """Abre un IFC (el derivado o una fuente)."""
    return ifcopenshell.open(str(path))


def psets(elemento) -> dict:
    """Property sets de un elemento como {Pset: {prop: valor}} (robusto ante entidades rotas)."""
    try:
        return _ue.get_psets(elemento) or {}
    except Exception:  # noqa: BLE001 — entidad corrupta: sin psets legibles
        return {}


def guid_de(entidad):
    """GlobalId de una entidad o None si no es legible."""
    try:
        return entidad.GlobalId
    except Exception:  # noqa: BLE001
        return None


def guid_a_modelo(manifiesto: dict, base_dir) -> dict:
    """{GlobalId → id de modelo} leyendo las fuentes declaradas en el manifiesto (D1).

    El derivado preserva los GUIDs (D28); esto recupera la procedencia que el derivado funde.
    Si un GUID aparece en más de un modelo (duplicado entre disciplinas, D28), gana el PRIMERO
    declarado en el manifiesto (determinista por el orden de `modelos`).
    """
    base_dir = Path(base_dir)
    mapa: dict[str, str] = {}
    for m in manifiesto.get("modelos", []):
        ruta = base_dir / m["fichero_origen"]
        fuente = ifcopenshell.open(str(ruta))
        for prod in fuente.by_type("IfcProduct"):
            g = guid_de(prod)
            if g is not None:
                mapa.setdefault(g, m["id"])
    return mapa
