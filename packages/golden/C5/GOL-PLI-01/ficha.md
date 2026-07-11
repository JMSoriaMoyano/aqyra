# Golden GOL-PLI-01 — conformidad del Pliego de Condiciones Técnicas (capa de documentos, C5)

> El segundo caso de la **capa de documentos** (tras GOL-DOC-01). Cierra el trío **coste + carbono +
> prescripción** sobre la misma medición: toma el `salida-presupuesto` JSON (autoritativo de C5), el
> criterio (mapeo partida→sistema) y el texto de prescripción, y emite el **Pliego de Condiciones
> Técnicas firmable** (.docx del despacho). El compositor `documentos/pliego.componer_pliego` es
> **DETERMINISTA** (formatea; sin LLM) — es el segundo ladrillo que el operador **C7 orquestará** (no
> es el operador C7).

## Entrada (D6 — sin fixture nueva)
El compositor lee el `presupuesto` de **`GOL-PRE-01/expected.json`** (ya anclado, verificado ×2): 8
partidas (7 medibles + S&S), PEM 7 022,53 → PEC 10 111,74. `fuente_presupuesto: "GOL-PRE-01"` apunta a
esa fuente; la zona anclada del C5 se **lee**, no se re-ancla. Añade `criterio: "AQ/v2"` (mapeo
partida→clase→sistema) y `pack_textos: "pliego-textos/AQ-DEMO/v1"` (texto de prescripción PROPIO, demo).

## Qué ancla (conformidad por CONTENIDO — patrón GOL-DOC-01/D3; NO bytes ni píxeles)
El runner (`run_case_c5`, rama `modo="pliego"`) compone el `.docx`, extrae **texto + tablas** con
`python-docx` (no OCR) y comprueba:

1. el `presupuesto` fuente **conforma** `salida-presupuesto.schema.json`;
2. el compositor **genera** el `.docx` (existe, no vacío);
3. las **secciones** presentes (carátula · condiciones generales · prescripciones particulares · cuadro de trazabilidad);
4. las **8 partidas** presentes, cada una con su **prescripción** (texto base no vacío, sin caer al *fallback*);
5. **medición**: cantidad de cada partida **== JSON (±0,001)**;
6. **coste**: importe de cada partida **== JSON (±0,01)**;
7. **trazabilidad**: los **GUIDs** de cada partida origen=modelo presentes en el pliego;
8. **carbono forward-open**: si el `presupuesto` trae `valores.carbono`, sus etapas presentes; si no, ausencia **sin error**;
9. **DETERMINISMO**: componer **2×** ⇒ **texto/tablas extraídos idénticos** (fecha/orden fijos).

## Regla de oro
Un fallo NO se arregla aflojando esta golden ni el formato. Se investiga en el **compositor**
(`documentos/pliego`). El pliego solo cambia si cambia el `presupuesto` fuente (GOL-PRE-01, zona
anclada — decisión explícita con JM), el criterio, el pack de textos (anclado por hash) o el diseño
del formato (bump de versión del compositor).
