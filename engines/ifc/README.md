# engines/ifc — implementación de C1 (esqueleto)

Productor del contrato **C1**: parsers por dominio (IFC → modelo neutro), compilador
(`alto.json` → IFC4X3 con doble clasificación) y write-back (resultados → Psets por GUID).
El resto del motor **nunca** conoce IFC.

**Esqueleto en Fase 0.** La implementación firmada vive aguas arriba como
`iso19650-openbim 0.10.0`. Se **importa** aquí en **0.5** (junto con la extracción de `core`).
Cuando aterrice, el runner de la golden C1 antepone el paso *compile* (`alto.json` → IFC) al
oráculo, contra el **mismo** `expected.json` que ya usa el vertical de Fase 0.

Ver `../../../Aqyra-Raiz/FUNDACION_C1_y_modelo-neutro.md`.
