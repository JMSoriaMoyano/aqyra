"""aqyra-federacion — service C4 (federación) v0.

API del contrato (packages/contracts/C4-federacion/contrato.md):

    federar(ifcs[], reglas)   → maestro   (manifiesto; IFC derivado = v0.x, D6)
    validar(maestro, ids)     → informe   (QA IDS + reglas de módulo; BCF emitido=false, D8)

Garantía: determinista. El listón de v0 es reproducir el golden C4-FED-01
(manifiesto + informe) dentro de tolerancias.json. Decisiones D6–D10 en
packages/contracts/C4-federacion/DECISIONES.md.
"""
from .federar import federar, federar_fichero
from .qa import validar  # módulo qa.py: 'validar.py' colisiona por NOMBRE con el guardián anti-espejo del engine (8b)

__version__ = "0.1.0"

__all__ = ["federar", "federar_fichero", "validar", "__version__"]
