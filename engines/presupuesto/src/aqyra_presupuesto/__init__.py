"""aqyra-presupuesto — engine C5 (presupuesto trazable desde la medición) v0.1.

API del contrato (packages/contracts/C5-presupuesto/contrato.md):

    medir(fuentes) → modelo               # módulo 1: IFC(+Qto) → modelo neutro de medición (D7)
    presupuestar(modelo, criterio, banco, parametros) → presupuesto   # módulos 2–6

El engine PRODUCE el presupuesto; el runner (packages/golden) ANTEPONE su recompute contra el MISMO
`expected` de GOL-PRE-01 (misma costura que cerró C1 en Fase I, C4 en Fase II·h2 y C3 en Fase III·h3
— D9). Determinista: mismo modelo + mismo criterio + mismo banco → mismo presupuesto.

La medición NACE del modelo (D7): `medir` abre el IFC y lee las cantidades de los `Qto` (no adivina
geometría, D_modelo); los huecos se detectan (`IfcRelVoidsElement`) y la magnitud NETA ya los
descuenta. El criterio es un PACK anclado (primitivas finitas seleccionadas por la FORMA del pack,
D8), no un `if`. El catálogo de capítulos (WBS) es un DEFAULT del engine, pack-overridable.
"""
from .escritura import escribir_coste
from .medicion import medir
from .presupuesto import CAPITULOS_DEFAULT, num_a_letra, presupuestar
from .primitivas import PRIMITIVAS
from .proyeccion import CORTES, proyectar, suma_proyeccion

__version__ = "0.7.0"

__all__ = ["medir", "presupuestar", "escribir_coste", "proyectar", "suma_proyeccion", "CORTES",
           "PRIMITIVAS", "CAPITULOS_DEFAULT", "num_a_letra", "__version__"]
