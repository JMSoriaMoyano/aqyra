"""aqyra_core — núcleo compartido, agnóstico al solver (extraído en 0.5).

Fin del espejo: en `Estructurando` estos módulos se copiaban byte a byte en cada plugin
(iso19650-openbim, motor-fem, puentes, obras-lineales, instalaciones) con una puerta de hash,
porque el aislamiento de runtime del sandbox de plugins impedía importarlos. En el monorepo son
un **paquete importado** versionado: un solo sitio, una sola versión.

- `ifc_utils`: lectura IFC común (psets, length_scale, pset_value) + álgebra homogénea 4×4.
- `grafo_red`: grafo de red genérico (fusión por tolerancia, troceo T/X, componentes conexas,
  `construir_grafo`). Devuelve topología, no calcula.

Los módulos se conservan **byte a byte** respecto al núcleo canónico de `Nucleo-transversal`
(ver `versions.lock` y `tests/test_identidad_nucleo.py`). La regla del espejo (identidad) se
sustituye aquí por la identidad del paquete con su canónico.
"""

from . import grafo_red, ifc_utils
from .grafo_red import (
    RegistroNodos,
    bbox_xy,
    construir_grafo,
    cortes_por_interseccion,
    filtrar_componentes_desconectadas,
    ordenar_segmento,
    proyeccion,
    punto_en_segmento,
)
from .ifc_utils import (
    apply,
    ident4,
    length_scale,
    matmul,
    pset_value,
    psets,
    to_list4,
)

__version__ = "0.1.0"

__all__ = [
    "grafo_red", "ifc_utils",
    # grafo_red
    "RegistroNodos", "bbox_xy", "construir_grafo", "cortes_por_interseccion",
    "filtrar_componentes_desconectadas", "ordenar_segmento", "proyeccion", "punto_en_segmento",
    # ifc_utils
    "apply", "ident4", "length_scale", "matmul", "pset_value", "psets", "to_list4",
]
