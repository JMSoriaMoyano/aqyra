#!/usr/bin/env python3
"""compile_c1.py — API pública del engine C1 (narración→IFC) en el monorepo.

Encapsula la cadena del canónico importado (byte a byte bajo `narracion-ifc/`,
identidad anclada en `versions.lock` y vigilada por `test_identidad_ifc`) para que
el runner de la golden y el CI la invoquen sin conocer el layout interno:

    alto.json (dict)  --compilar_spec.compilar-->  spec canónico
    spec canónico     --spec_to_ifc.generar------>  IFC4X3 (fichero)

Este fichero NO forma parte de la zona de identidad: es la superficie estable del
engine dentro del monorepo. Los ficheros importados (compilar_spec.py, spec_to_ifc.py,
clasificacion.py, catalogo_ifc.py, catalogo-ifc4x3.json, alineaciones_ifc.py, validar.py,
spec.schema.json y scripts/lineal/generate_test_ifc_lineal.py) se mantienen verbatim.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_NARRACION = _HERE / "narracion-ifc"  # módulos flat del compilador


def _ensure_import_path() -> None:
    """Pone el directorio del compilador en sys.path (imports flat: `import clasificacion`).
    `alineaciones_ifc` descubre `../scripts/lineal` por su cuenta relativo a su __file__."""
    p = str(_NARRACION)
    if p not in sys.path:
        sys.path.insert(0, p)


def compilar_alto_a_ifc(alto: dict, out_path) -> tuple:
    """Compila un `alto.json` (dict) a un IFC4X3 escrito en `out_path`.

    Devuelve (model, counts) tal cual los entrega `spec_to_ifc.generar`.
    Requiere ifcopenshell (perezoso: no se importa hasta aquí)."""
    _ensure_import_path()
    import compilar_spec  # noqa: E402  (import diferido tras fijar sys.path)
    import spec_to_ifc    # noqa: E402
    canon = compilar_spec.compilar(alto)
    return spec_to_ifc.generar(canon, str(out_path))
