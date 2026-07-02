"""aqyra-federacion — service C4 (federación) v0.2.

API del contrato (packages/contracts/C4-federacion/contrato.md):

    federar(ifcs[], reglas)      → maestro  (manifiesto; IFC derivado = v0.x, D6)
    validar(maestro, ids)        → informe  (QA IDS + reglas de módulo; emitido=false, D8)
    emitir_bcf(informe, carpeta) → bcf      (topics BCF 3.0 por incidencia; el informe
                                             devuelto refleja emitido=true — D11: paso
                                             SEPARADO, validar() queda intacta)

Garantía: determinista. El listón de v0 es reproducir las golden C4-FED-01
(manifiesto + informe) y C4-FED-02 (emisión BCF) dentro de tolerancias.
Decisiones D6–D15 en packages/contracts/C4-federacion/DECISIONES.md.
"""
from .federar import federar, federar_fichero
from .qa import validar  # módulo qa.py: 'validar.py' colisiona por NOMBRE con el guardián anti-espejo del engine (8b)
from .bcf import emitir_bcf, empaquetar_bcfzip

__version__ = "0.2.0"

__all__ = ["federar", "federar_fichero", "validar", "emitir_bcf",
           "empaquetar_bcfzip", "__version__"]
