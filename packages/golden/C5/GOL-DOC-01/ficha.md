# Golden GOL-DOC-01 — conformidad del Documento de Presupuesto (capa de documentos, C5)

> El primer caso de la **capa de documentos**. Hace **ENTREGABLE** lo que GOL-PRE-01 hizo
> presupuestable: el `salida-presupuesto` JSON (autoritativo de C5) → el **Documento de Presupuesto
> firmable** (.docx del despacho). El compositor `documentos/presupuesto.componer_documento` es
> **DETERMINISTA** (formatea; sin LLM) — es el primer ladrillo que el operador **C7 orquestará**
> (no es el operador C7).

## Entrada (D4 — sin fixture nueva)
El compositor lee el `presupuesto` de **`GOL-PRE-01/expected.json`** (ya anclado, verificado ×2):
8 partidas → cuadro nº1 (en letra) + nº2 (descompuesto) + resumen **PEM 7 022,53 → PEC 10 111,74**.
`fuente_presupuesto: "GOL-PRE-01"` en el `expected` de este caso apunta a esa fuente; la zona
anclada del C5 se **lee**, no se re-ancla.

## Qué ancla (conformidad por CONTENIDO — D3; NO bytes ni píxeles)
El runner (`run_case_c5`, rama `modo="documento"`) compone el `.docx`, extrae **texto + tablas** con
`python-docx` (no OCR) y comprueba:

1. el `presupuesto` fuente **conforma** `salida-presupuesto.schema.json`;
2. el compositor **genera** el `.docx` (existe, no vacío);
3. las **5 secciones** presentes (carátula · mediciones · nº1 · nº2 · resumen);
4. las **8 partidas** en la tabla de mediciones, con **importe == JSON (±0,01)**;
5. **Σ capítulos == PEM** y cada **importe de capítulo == JSON**;
6. cadena **PEM → GG → BI → base → IVA → PEC** presente y **== JSON (±0,01)**;
7. **precio en letra** por partida (cuadro nº1) presente;
8. **DETERMINISMO**: componer **2×** ⇒ **texto/tablas extraídos idénticos** (fecha/orden fijos).

## Regla de oro
Un fallo NO se arregla aflojando esta golden ni el formato. Se investiga en el **compositor**
(`documentos/presupuesto`). El documento solo cambia si cambia el `presupuesto` fuente (GOL-PRE-01,
zona anclada — decisión explícita con JM) o el diseño del formato (bump de versión del compositor).
