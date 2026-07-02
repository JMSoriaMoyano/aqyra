"""aqyra-federacion — service C4 (federación) v0.4.

API del contrato (packages/contracts/C4-federacion/contrato.md):

    federar(ifcs[], reglas)      → maestro  (manifiesto; IFC derivado = v0.x, D6)
    validar(maestro, ids)        → informe  (QA IDS + reglas de módulo; emitido=false, D8;
                                             + `avisos_lectura` si hay suciedad tolerada, D20)
    emitir_bcf(informe, carpeta) → bcf      (topics BCF 3.0 por incidencia; el informe
                                             devuelto refleja emitido=true — D11: paso
                                             SEPARADO, validar() queda intacta)

Lectura ENDURECIDA para IFC sucio (tarea 1.3, D16–D20): suciedad tolerable →
degradación DECLARADA (avisos_lectura); bloqueante → LecturaIfcError con diagnóstico.
Política de estructura espacial `mantener-separada` IMPLEMENTADA (tarea 1.4, D22):
nodos por modelo sin fundir — antes se ecoaba sin aplicarse (bug corregido en 0.4.0).

Garantía: determinista. El listón de v0 es reproducir las golden C4-FED-01
(manifiesto + informe), C4-FED-02 (emisión BCF), C4-FED-03 (IFC sucio, camino
feliz-degradado), C4-FED-04 (integración mixta: avisos + emisión juntos, D21/D23)
y C4-FED-05 (mantener-separada, D22) dentro de tolerancias.
Decisiones D6–D25 en packages/contracts/C4-federacion/DECISIONES.md.
"""
from .federar import federar, federar_fichero
from .lectura import LecturaIfcError
from .qa import validar  # módulo qa.py: 'validar.py' colisiona por NOMBRE con el guardián anti-espejo del engine (8b)
from .bcf import emitir_bcf, empaquetar_bcfzip

__version__ = "0.4.0"

__all__ = ["federar", "federar_fichero", "validar", "emitir_bcf",
           "empaquetar_bcfzip", "LecturaIfcError", "__version__"]
