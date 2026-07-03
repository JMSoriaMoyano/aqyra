"""aqyra-cumplimiento — engine C3 (cumplimiento normativo multi-código) v0.1.

API del contrato (packages/contracts/C3-cumplimiento/contrato.md):

    verificar(maestro, uso, localizacion, pack) → veredicto  (por exigencia + resumen + global)

El engine DA el veredicto; el runner (packages/golden) ANTEPONE su recompute contra el MISMO
`expected` (misma costura que cerró C1 en Fase I y C4 en Fase II·h2 — D9). Determinista: mismo
Maestro + mismo uso/localización + mismo pack → mismo veredicto.

Multi-código HONESTO (D8): el código es un **PACK anclado, no un `if`**. El pack declara, por
exigencia, qué EVALUADOR determinista aplica (`evaluador` + `parametros`); el engine mantiene una
librería FINITA de evaluadores y mapea nombre→función. Cambiar de año/mercado/municipio = cambiar
de pack (nuevas exigencias); un método genuinamente nuevo = un evaluador nuevo (honesto, raro).

Frontera (D7): el engine ABRE el IFC derivado (la vista del Maestro que produce C4) y usa la
procedencia del manifiesto (fuente de verdad, D1 de C4) para atribuir por modelo. NO federa ni
re-ejecuta services/federacion (esa es zona de C4); no adivina uso ni localización (se DECLARAN).
"""
from .cumplimiento import verificar, cargar_maestro
from .evaluadores import EVALUADORES, RESULTADOS

__version__ = "0.1.0"

__all__ = ["verificar", "cargar_maestro", "EVALUADORES", "RESULTADOS", "__version__"]
