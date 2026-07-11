"""aqyra-documento-pliego — capa de documentos C5 (compositor DETERMINISTA del Pliego).

    componer_pliego(presupuesto, criterio, parametros?) -> Path   # JSON salida-presupuesto -> .docx

Consume la salida AUTORITATIVA de C5 (`salida-presupuesto`) + el `criterio` (mapeo partida->sistema) +
un pack de textos de prescripcion, y produce el Pliego de Condiciones Tecnicas firmable con el formato
del despacho. NO recalcula. Determinista (fecha/orden fijos): mismo presupuesto + criterio + textos +
parametros => mismo CONTENIDO extraible. Cierra el trio coste + carbono + prescripcion sobre la misma
medicion. Segundo ladrillo de la capa de documentos que el operador C7 orquestara — NO es el operador C7.
"""
from .compositor import (SEC_CARATULA, SEC_GENERALES, SEC_PARTICULARES, SEC_TRAZA,
                         componer_pliego)

__version__ = "0.1.0"

__all__ = ["componer_pliego", "SEC_CARATULA", "SEC_GENERALES", "SEC_PARTICULARES", "SEC_TRAZA",
           "__version__"]
