# documentos/presupuesto — DECISIONES (D1–D5)

> El **compositor del Documento de Presupuesto**: convierte la salida AUTORITATIVA de C5
> (`salida-presupuesto` JSON — estado de mediciones + cuadros de precios nº1/nº2 + resumen
> PEM→PEC) en el **documento firmable** con el formato del despacho (Word .docx). Es
> **DETERMINISTA** (formatea datos ya calculados; sin LLM) y es el **primer ladrillo de la capa
> de documentos** que el operador C7 orquestará. OK JM 2026-07-04.

## D1 · Casa y empaquetado — nueva capa `documentos/`
El compositor vive en **`documentos/presupuesto`** (paquete uv `aqyra-documento-presupuesto`),
**no** en `engines/*` (no calcula) ni en `services/*`. Establece la **capa de documentos** como
capa propia del monorepo: es justo lo que C7 orquestará, y el próximo compositor (memoria CTE,
urbanística…) aterriza aquí también.

API: `componer_documento(presupuesto: dict, parametros: dict | None = None) -> Path` (escribe el
`.docx` y devuelve su ruta). Consume el `salida-presupuesto` JSON; **no recalcula nada**.

**Matiz de hermeticidad (importante).** El gate de CI debe ser hermético: solo `python-docx`, sin
el skill en el runner. Por eso el **formato del despacho se implementa dentro del paquete**
(`formato.py`: A4/Arial 11 · tablas 9,5, cabecera azul `#D9E2F3` que se repite en saltos de página,
sin verticales salvo cabecera, total destacado en verde). El skill `memoria-calculo-despacho`
(`scripts/docx_despacho.py`) queda como **especificación de referencia** humana, no como
dependencia de ejecución. El código sigue fino (mapea JSON→secciones); el estilo, replicado in-repo.

## D2 · Formato de salida — `.docx`
`.docx` con el formato del despacho, **revisable por el técnico antes de firmar** (coherente con
«propuesta revisable» de C7). PDF queda como **gancho forward** (render posterior del .docx), no en
v0. **Sin píxeles anclados.**

## D3 · Qué ancla la golden — conformidad por CONTENIDO extraído (no bytes/píxeles)
La golden extrae el **texto y las tablas** del `.docx` (con `python-docx`, **no OCR**) y comprueba:
- las **5 secciones** presentes (carátula · mediciones · nº1 · nº2 · resumen);
- **todas las partidas** del JSON presentes en la tabla de mediciones (por código);
- cada **importe/total** del documento **== JSON (±0,01)** (extraído del .docx, no OCR);
- **Σ capítulos == PEM** y la cadena **PEM→GG→BI→base→IVA→PEC** coherente en el documento;
- el **precio en letra** por partida presente (cuadro nº1).

**Determinismo por CONTENIDO** (patrón 5D, D14 opción b): componer **2×** → **texto/tablas
extraídos idénticos** (fecha y orden fijos). No byte a byte: un `.docx` es un zip con timestamps y
toda la golden del monorepo ancla **contenido, no bytes** (coherente con la nota EOL/docx del hilo).

## D4 · La entrada del golden — el `presupuesto` de `GOL-PRE-01` (sin fixture nueva)
El compositor lee el `presupuesto` de `packages/golden/C5/GOL-PRE-01/expected.json` (ya anclado,
verificado ×2). El caso nuevo **`packages/golden/C5/GOL-DOC-01/`** declara `modo: "documento"` y un
puntero `fuente_presupuesto: "GOL-PRE-01"`; el runner (tercera rama en `run_case_c5`, junto a la de
5D) carga ese presupuesto anclado, compone y verifica la conformidad. **Fuente de verdad única** (el
oráculo); zona anclada del C5 intacta (el `expected` de GOL-PRE-01 se **lee**, no se re-ancla).

## D5 · Relación con C7 y versionado
Queda **DECLARADO**: este compositor es un **entregable determinista que C7 orquestará** — **no es**
el operador C7 (grounding/redacción no-determinista). Versión **0.1.0**; tag firmado
**`documento-presupuesto-v0.1.0`** (Llave 2, firma humana de JM; el CI nunca certifica).

## Zona anclada (frontera dura)
Este paquete solo **AÑADE** `documentos/presupuesto` + el caso `GOL-DOC-01` + edición quirúrgica de
`run_golden.py` / `versions.lock` / `ci.yml` / `[tool.uv.workspace]`. **Nunca** toca el contrato ni
los golden/packs del C5 (GOL-PRE-01/-02 y su `expected`), ni C1/C3/C4, `engines/*`,
`services/federacion`, `packages/core`, `apps/visor`.
