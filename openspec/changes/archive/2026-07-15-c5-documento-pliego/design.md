# Diseño · Compositor de PLIEGO (E4.1) + textos base (E5.3)

> El **cómo**. Decisiones **D1–D7 (numeración propia del documento/pliego, en `documentos/pliego/DECISIONES.md`) a ratificar por JM**. La IA propone; JM firma (dos llaves). Delta de spec del contrato C5 **NULO** (el pliego consume la salida existente; no cambia esquema).

## 0 · Principio rector

Una medición, tres lecturas. El presupuesto la lee como coste; el eje carbono como huella; el **pliego** la lee como **prescripción**. Los tres son *composición determinista* de datos ya autoritativos (patrón C7 / `documento-presupuesto`): el pliego no calcula nada nuevo — toma `estado_mediciones[]` (con `trazabilidad:[guids]`, `cantidad`, `importe`, `valores`), el mapeo partida→sistema del `criterio`, y el texto de prescripción por tipo de unidad, y compone el `.docx` firmable del despacho.

## 1 · Qué YA existe (no se rehace)

- **Patrón de la capa de documentos:** `documentos/presupuesto` (`componer_documento(presupuesto, parametros?) → Path`, determinista, `formato.py` in-repo hermético, golden por contenido `GOL-DOC-01` con rama `modo="documento"` en `run_case_c5`). El pliego es su **espejo**.
- **La medición y sus valores:** `GOL-PRE-01/expected.json` — 8 partidas (`CSZ010, EHS010, EHL010, FAB010, REV010, PIN010, PPM010` + `SYS010` S&S), con `trazabilidad`, `cantidad`, `importe` y capítulos C01–C06. Se **LEE** anclada (D4 del presupuesto), no se re-ancla.
- **El mapeo partida→sistema:** `criterio/AQ/v2` (`reglas_por_clase` = clase→partida; `reglas_sistema` = clase→sistema/Uniclass Ss). El pliego lo usa para ordenar por sistema y para la clave de mapeo del texto base.
- **El gancho `~T`:** `aqyra-bc3.emitir_bc3` emite un `~T` (pliego mínimo = descripción de la partida, D38); en ingesta, `~T` se parsea (bancos reales BEDEC/CYPE llevan el texto por partida). Es la vía por la que un banco REAL aporta la prescripción; AQ-DEMO no la lleva.
- **La forma del pack + anclaje:** `aqyra_packs` (familias en `FAMILIAS`), `content_sha256` + md5, golden de pack, fila en `versions.lock`. `pliego-textos` imita esta forma exacta.

## 2 · Decisiones a ratificar (D1–D7)

### D1 · Casa y API — nuevo paquete `documentos/pliego` (espejo)
`documentos/pliego` (paquete uv **`aqyra-documento-pliego`**), NO en `engines/*` (no calcula) ni `services/*`. API:
`componer_pliego(presupuesto: dict, criterio: dict, parametros: dict | None = None) -> Path` (escribe `.docx`, devuelve ruta). Consume el `salida-presupuesto` JSON + el `criterio` (para el orden por sistema y la clave del texto); **no recalcula**.

**Sub-decisión — `formato.py`:** **(A, recomendada) ESPEJAR** `formato.py` dentro de `documentos/pliego` (copia in-repo). Mantiene hermeticidad, desacopla versiones (el pliego evoluciona su formato sin tocar el presupuesto firmado) y evita una dependencia `documento-pliego → documento-presupuesto` semánticamente rara. · (B) **Importar** de `aqyra-documento-presupuesto` (DRY, pero acopla versiones y crea dependencia entre documentos). · (C) **Extraer** a un `documentos/_formato` común (DRY real, pero refactor que toca el paquete firmado `documentos/presupuesto` — contra guardarraíl). → **Recomendación A** (baby step; con nota "extraer a común si aparece un 3er documento").

### D2 · Formato de salida — `.docx` del despacho
`.docx` revisable antes de firmar; **PDF forward**, **sin píxeles anclados** (espejo de D2 del presupuesto). Carátula con VEREDICTO/estado, condiciones generales, prescripciones particulares por capítulo/sistema, cuadro de trazabilidad. El estilo lo replica `formato.py` in-repo (Arial 11, tablas 9,5, cabecera azul repetida).

### D3 · Contenido del pliego por partida — el trío sobre la partida
Cada partida del pliego lleva: **(1) prescripción** (condiciones de materiales, ejecución, control, criterio de medición y abono — texto base por tipo de unidad); **(2) medición** trazable (`cantidad`, `unidad`, `criterio_aplicado`, GUIDs de `trazabilidad`); **(3) coste** (`importe`, `precio_unitario`); **(4) carbono** (`valores.carbono` con etapas A1A3/A4A5) **forward-open** — si el `presupuesto` fuente trae `valores.carbono`, el pliego lo incluye; si no, ese bloque se omite (nunca error). → **Recomendación:** el cuarteto completo (prescripción + medición + coste + carbono forward-open); es el cierre del trío que persigue la Ola 3.

### D4 · Fuente del texto de prescripción por partida — cadena con *fallback*
Constatado: `AQ-DEMO/v1` **no** lleva texto de prescripción; el `criterio` lleva `nota` de medición (no condiciones técnicas); el `~T` del BC3 lleva solo la descripción (D38). Cadena determinista propuesta (precedencia):
1. **texto del banco** por partida (bancos reales BEDEC/CYPE / `~T` del BC3 ingerido), cuando exista;
2. **pack de textos base** (`pliego-textos/…`) mapeado por **tipo de unidad / clasificación Uniclass Ss** (de `reglas_sistema` del criterio) — la vía de E5.3;
3. **fallback** = descripción de la partida + aviso «prescripción base pendiente de completar».

Para `GOL-PLI-01` (sobre `AQ-DEMO`, sin texto de banco) la fuente efectiva es el **pack de textos base** (paso 2), dejando `AQ-DEMO/v1` intacto. → **Recomendación:** cadena (e) mezcla con *fallback*, en ese orden.

### D5 · Textos base (E5.3) — semilla PROPIA ahora, texto REAL por la vía limpia
Como el coste (`AQ-DEMO` propio) y el carbono (`generico/v1` sintético → `v2` real), la prescripción arranca con una **semilla PROPIA** para no bloquear E4.1 en la puerta de licencia, y el texto normativo REAL entra después, verificado.

| Opción | Semilla v0 (golden) | Texto REAL (posterior) | Licencia |
|---|---|---|---|
| **A (recomendada)** | `pliego-textos/AQ-DEMO/v1` — texto PROPIO de Aqyra por partida/tipo de unidad, marcado **demo** | `pliego-textos/<PG-3\|CTE-DB>/vN` (adición posterior) | E4.1 **no** depende de licencia; E5.3 real espera verificación N-04 (registro `RECONCILIACION_licencias-pliego.md`) |
| **B** | ninguna; E4.1 se bloquea hasta verificar PG-3/CTE | PG-3/CTE directo | E4.1 bloqueada por la puerta de licencia |

**Recomendación A** — desacopla el compositor (E4.1) de la puerta de licencia (E5.3 real), igual que la Ola 1/2. **Puerta de licencia (N-04):** PG-3/PG-4 (Min. Transportes) y CTE DB (BOE) son públicos, pero *público ≠ ingestable*: su redistribución **dentro de un pack de Aqyra** requiere verificar sus condiciones de uso (las 4 preguntas del patrón E5.2) y ratificación de JM ANTES de anclar. PG-3 = obra civil (carreteras); CTE DB = edificación (natural para las 7 partidas de la golden). **Mapeo** por tipo de unidad / Uniclass Ss / disciplina.

### D6 · Golden `GOL-PLI-01` — por CONTENIDO (patrón `GOL-DOC-01`)
Runner: rama **`modo="pliego"`** bajo `run_case_c5` (dispatch `expected.modo=="pliego"`, patrón `documento`/`carbono`), **sin runner nuevo** en `CASE_RUNNERS`. Entrada: el `presupuesto` de **`GOL-PRE-01`** (se LEE anclado, D4 presupuesto) + `criterio/AQ/v2` + el pack `pliego-textos/AQ-DEMO/v1`. El runner compone el `.docx`, extrae **texto + tablas** con `python-docx` (NO OCR) y comprueba:
1. el `presupuesto` fuente **conforma** `salida-presupuesto.schema.json`;
2. el compositor **genera** el `.docx` (existe, no vacío);
3. las **secciones** presentes (carátula · condiciones generales · prescripciones particulares · trazabilidad);
4. las **8 partidas** presentes, cada una con su **prescripción** (texto base no vacío), su **medición** (`cantidad` == JSON ±tol) y su **coste** (`importe` == JSON ±0,01);
5. **trazabilidad**: los GUIDs de cada partida presentes en el pliego (partida→objeto);
6. **carbono forward-open**: si el `presupuesto` trae `valores.carbono`, sus etapas presentes; si no, ausencia sin error;
7. **DETERMINISMO**: componer **2×** ⇒ texto/tablas extraídos idénticos (fecha/orden fijos).

**Nota de ejecución:** como `GOL-DOC-01`, la golden **LEE** el presupuesto anclado (no pasa por `medir()`), así que la composición y el chequeo de contenido se **unit-testean en el sandbox** (texto puro); solo el runner completo `run_golden.py` (torn-read del mount) se verifica en el conda `mcp-bim` de JM antes del PR.

### D7 · Anclaje
`[documentos.pliego]` en `versions.lock` (espejo de `[documentos.presupuesto]`). Pack `pliego-textos/AQ-DEMO/v1` anclado por `content_sha256` + md5 en `versions.lock [packs.pliego_textos]` y su golden de pack en `test_packs.py`. Nueva familia `pliego-textos` en `pack.schema.json` (aditivo). Versión `aqyra-documento-pliego` **0.1.0**; tag firmado **`documento-pliego-v0.1.0`** (Llave 2) — **sin release salvo decisión de JM**.

## 3 · Estructura del `.docx` (corte mínimo que reproduce `GOL-PLI-01`)

0. **Carátula** — proyecto, objeto, fecha (inyectable), nota de documento determinista revisable/firmable.
1. **Condiciones generales** — cláusulas generales del pliego (del texto base: normativa aplicable, control de calidad, recepción). En v0, de la semilla PROPIA.
2. **Prescripciones técnicas particulares** — por capítulo/sistema (orden del `criterio`): por partida, ficha con **prescripción + medición (cantidad, criterio, GUIDs) + coste + carbono (forward-open)**.
3. **Trazabilidad** — tabla partida → GUIDs del modelo (la joya: el pliego ligado al objeto).

## 4 · Versionado y no-regresión

- **Sin bump** de `engines/*` ni del esquema C5 (no se tocan). `documentos/presupuesto` 0.1.0 intacto (se espeja, no se importa).
- **Sin release** (Llave 2 espera decisión de JM).
- El compositor + el chequeo de contenido + el golden de pack se unit-testean en el **sandbox** (texto puro). El recompute del runner completo (`GOL-PLI-01` + no-regresión de `GOL-PRE-01/02/03`, `GOL-DOC-01`, `GOL-CAR-01/02` byte-idénticas) corre en el conda `mcp-bim` local de JM antes del PR.
