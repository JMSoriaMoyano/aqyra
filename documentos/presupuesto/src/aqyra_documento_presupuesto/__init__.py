"""aqyra-documento-presupuesto — capa de documentos C5 (compositor DETERMINISTA).

    componer_documento(presupuesto, parametros?) -> Path      # JSON salida-presupuesto -> .docx

Consume la salida AUTORITATIVA de C5 (`salida-presupuesto`) y produce el Documento de Presupuesto
firmable con el formato del despacho. NO recalcula. Determinista (fecha/orden fijos): mismo
presupuesto + mismos parametros => mismo CONTENIDO extraíble. Primer ladrillo de la capa de
documentos que el operador C7 orquestará — NO es el operador C7.
"""
from .compositor import (SEC_CARATULA, SEC_CP1, SEC_CP2, SEC_MEDICIONES, SEC_RESUMEN,
                         componer_documento)

__version__ = "0.1.0"

__all__ = ["componer_documento", "SEC_CARATULA", "SEC_MEDICIONES", "SEC_CP1", "SEC_CP2",
           "SEC_RESUMEN", "__version__"]
