"""aqyra-federacion — service C4 (federación) v0.5.

API del contrato (packages/contracts/C4-federacion/contrato.md):

    federar(ifcs[], reglas)         → maestro  (manifiesto; fuente de verdad, D1)
    derivar(maestro, base_dir, out) → maestro' (escribe el IFC federado DERIVADO —
                                                D26/D27 — y devuelve el manifiesto con
                                                ifc_derivado {fichero, md5, determinista})
    validar(maestro, ids)           → informe  (QA IDS + reglas de módulo; emitido=false,
                                                D8; + avisos_lectura si hay suciedad
                                                tolerada, D20; + guid-duplicado entre
                                                modelos, D28)
    emitir_bcf(informe, carpeta)    → bcf      (topics BCF 3.0 por incidencia; con
                                                `derivado=` cada viewpoint gana la CÁMARA
                                                determinista — D29; sin él, como en v0)

Lectura ENDURECIDA para IFC sucio (tarea 1.3, D16–D20). Política mantener-separada
IMPLEMENTADA (tarea 1.4, D22). IFC federado derivado + cámara BCF (v0.x, Fase II·h6,
D26–D30): la decisión que D6 aplazó, cerrada — el Maestro por fin se puede ABRIR.

Garantía: determinista. El listón de v0.x es reproducir las golden C4-FED-01
(manifiesto + informe), C4-FED-02 (emisión BCF), C4-FED-03 (IFC sucio), C4-FED-04
(integración mixta), C4-FED-05 (mantener-separada) y C4-FED-06 (derivado por md5
BYTE A BYTE + árbol BCF con cámara) dentro de tolerancias.
Decisiones D6–D30 en packages/contracts/C4-federacion/DECISIONES.md.
"""
from .federar import federar, federar_fichero
from .lectura import LecturaIfcError
from .qa import validar  # módulo qa.py: 'validar.py' colisiona por NOMBRE con el guardián anti-espejo del engine (8b)
from .derivar import derivar, derivar_fichero, camara_para_guids  # módulo derivar.py: sin colisión (comprobado, 8b)
from .bcf import emitir_bcf, empaquetar_bcfzip

__version__ = "0.5.0"

__all__ = ["federar", "federar_fichero", "derivar", "derivar_fichero",
           "camara_para_guids", "validar", "emitir_bcf", "empaquetar_bcfzip",
           "LecturaIfcError", "__version__"]
