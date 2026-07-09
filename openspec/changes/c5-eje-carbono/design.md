# Diseño · Eje CARBONO en C5 (E3)

> El **cómo**. Decisiones **D39–D44 ratificadas por JM (2026-07-09)**; se anclan en
> `packages/contracts/C5-presupuesto/DECISIONES.md`. La IA propuso; JM firmó las opciones A/A/A/A.

## 0 · Principio rector

Un motor, varios ejes. El carbono NO es un engine nuevo: es `presupuestar(modelo, criterio, banco,
parametros)` con `parametros.eje="carbono"` y un `banco` = `banco-carbono`. La medición se hace **una vez**
(mismo criterio, mismas cantidades, misma trazabilidad); sólo cambia el factor (kgCO₂e con etapas en vez de
€). Lo único genuinamente nuevo en código es que el motor **emita el desglose por etapas** del ciclo de vida.

## 1 · Qué YA existe (no se rehace)

- `salida-presupuesto.schema.json`: `$def valor_eje` con `etapas` (objeto opcional `clave→número`,
  EN 15978) y `partida_medida.valores` (mapa `id-de-eje → valor_eje`), **opcional/forward-open** (E1.1,
  D16–D18). **La forma de `etapas` ya está fijada; el esquema NO se toca en E3.**
- `presupuesto.py`: `parametros.eje` (default `"coste"`, D19). Con `eje!="coste"` cada partida gana
  `valores[eje] = {unitario, total, unidad, banco, origen}` (etiquetado, espejo de `precio_unitario`/`importe`).
- `proyeccion.py`: `proyectar` lee `valores[eje].total` (D25) → la proyección de carbono es la misma consulta.
- Patrón de pack (`banco/AQ-DEMO/v1`) + loader `aqyra_packs` (familia/hash `content_sha256`) + anclaje en
  `versions.lock` + golden de pack (`packages/packs/tests/test_packs.py`).
- Runner `run_case_c5` con dispatch por `expected.modo` (ramas `5d`/`documento`/`proyeccion`).

## 2 · D39/D40 · Pack `banco-carbono` y reparto de etapas (Opción A ratificada)

**El factor se ancla por CÓDIGO de partida** (la misma junta que el precio en el banco de coste; el mapeo
clase→partida del criterio no cambia entre ejes, D19). Cada partida del `banco-carbono` declara:

```jsonc
{
  "codigo": "EHL010", "unidad": "kgCO2e",
  "descripcion": "Losa/forjado HA-25 — factor de carbono embebido (genérico)",
  "precio": 300.0,                       // factor UNITARIO total (kgCO2e por unidad de medición)
  "etapas": { "A1A3": 287.4, "A4A5": 12.6 },   // factores por etapa POR UNIDAD (EN 15978); Σ = precio
  "componentes": [                       // ver §2.1 — mantiene el cuadro nº2 conforme sin tocar el esquema
    { "tipo": "material", "descripcion": "Factor genérico embebido (A1-A3 + A4-A5)",
      "unidad": "kgCO2e", "rendimiento": 1.0, "precio": 300.0, "subtotal": 300.0 } ],
  "costes_indirectos": 0
}
```

**Reparto en el motor (D40):** `etapa_total = factor_etapa × cantidad` (redondeo 2 dec, `ROUND_HALF_UP`);
la **ÚLTIMA etapa presente (orden canónico A1A3, A4A5, B, C, D) ABSORBE el residuo de redondeo** →
invariante **Σ etapas = total EXACTO** (D18). Guarda de consistencia estilo D32: `Σ factor_etapa` debe casar
(±0,01) con `precio`; si no, aviso auditable, nunca se silencia. Rechazadas (por JM): B (factor total +
reparto por ratio — inventa el reparto) y C (factor por material del componente — es la capa EPD-premium).

**Verificado en el sandbox** (motor real sobre la medición de `GOL-PRE-01`, texto puro, sin ifcopenshell):
las 7 partidas `origen=modelo` emiten `valores.carbono` con `etapas` A1A3/A4A5 y `Σ etapas = total` exacto;
la salida **conforma `salida-presupuesto.schema.json` sin editarlo**.

### 2.1 · Nota de diseño (hallazgo de la verificación) — el cuadro nº2 y `componentes`

El esquema de salida exige `cuadro_precios_2[].componentes` con `minItems: 1`, y el motor emite el cuadro
nº2 para **todo** run (también no-coste). Para que la salida de carbono conforme **sin tocar el esquema**,
cada partida del `banco-carbono` declara **un** `componente` de `tipo:"material"` (el factor embebido como
una línea única). El "cuadro nº2" del carbono muestra así el factor genérico como un material; el desglose
real del ciclo de vida vive en `valores.carbono.etapas`. Alternativa descartada: cambiar el enum `tipo` del
componente para admitir etapas (rompería forward-open del esquema de salida — fuera de E3).

## 3 · D41 · Convención del eje (marco por precedente, confirmado por JM)

`id="carbono"` (string libre, D17), `unidad="kgCO2e"`, etapas mínimas `A1A3` (producto) + `A4A5`
(construcción) con Σ etapas = total (D18). Se ancla en `C5/DECISIONES.md` (numeración propia, continúa
D1–D38). **El esquema de SALIDA C5 no cambia.** El delta del contrato es sólo el enum de familia del
`pack.schema.json` (E3.2) + `DECISIONES.md`/`contrato.md`.

## 4 · D42 · Trazabilidad del origen del factor (`epd`/`generico`) — DIFERIDA

No se añade clave en v0. El campo `banco` de cada `valores.carbono` ya dice `banco-carbono/generico/v1` (y
dirá `.../epd/vN` cuando exista el pack premium), así que el origen del factor **ya es trazable sin tocar el
esquema de salida**. La clave dedicada `origen_factor` se materializa cuando el motor mezcle EPD+genérico
(N-05, capa premium posterior). Mantiene el esquema de salida intacto en E3.

## 5 · D43 · Runner (rama de modo bajo `run_case_c5`)

Nueva rama `expected.modo == "carbono"` → `_run_c5_carbono(...)`, igual que `5d`/`documento`/`proyeccion`.
El contrato sigue siendo `"C5"` en `CASE_RUNNERS` (sin entrada nueva). El runner:
1. Conformidad del esquema de salida (el carbono conforma sin editar el esquema).
2. Identidad por md5 de las fixtures aumentadas (`entradas_md5`) — las de `GOL-PRE-03` (D44).
3. `criterio/AQ/v2` anclado por su `content_sha256`; `banco-carbono/generico/v1` anclado por su
   `content_sha256` + md5 del `banco.json`.
4. **RECOMPUTE** (conda `mcp-bim`, ifcopenshell): `medir(fixtures, criterio_v2)` + `presupuestar(...,
   banco=banco-carbono, eje="carbono")`.
5. **SEMÁNTICA carbono:** por cada partida `origen=modelo`, `valores.carbono` con `unitario × cantidad =
   total`, `unidad=kgCO2e`, `banco=banco-carbono/generico/v1`, `etapas` A1A3/A4A5 y **Σ etapas = total**
   (±`importe_abs`). Resumen del eje == Σ totales. S&S (`origen=regla`): etiquetado, sin etapas.
6. **PROYECCIÓN + INVARIANTE:** `proyectar(pres, modelo, "carbono", corte)` 2× determinista; grupos == los
   del corte (mismos que la vista coste homóloga de `GOL-PRE-03`, porque el corte no depende del eje);
   `Σ proyección == Σ valores.carbono` (±`importe_abs`).

## 6 · D44 · Anclaje de `GOL-CAR-01` (fixtures aumentadas de `GOL-PRE-03` + `criterio/AQ/v2`)

`GOL-CAR-01` valora la MISMA medición anclada de `GOL-PRE-01` en carbono. Reusa las **fixtures aumentadas**
de `GOL-PRE-03` (misma medición + cortes `IfcSystem`/`IfcZone`/árbol 4.3 inyectados, md5 ya anclados en
E2.2) y `criterio/AQ/v2` → valoración carbono por partida + etapas **y** proyección de carbono **real** por
un corte. `GOL-PRE-01/02/03` quedan **byte-idénticas** (E3 sólo AÑADE el caso).

**Modo anclado (D14/D28, sin md5 de salida hardcodeado):** el sandbox no corre ifcopenshell → el recompute
del golden corre en el conda `mcp-bim` de JM (como E1.2/E2.1/E2.2/GOL-PRE-03). Anclaje por
DETERMINISMO + SEMÁNTICA + INVARIANTE (§5). El **oráculo del eje carbono** (factores del banco-carbono +
cantidades de la medición) se calcula a mano y se verifica ×2; los factores del `banco-carbono/generico/v1`
son la fuente del kgCO₂e (convención, no verdad física). Un fallo se investiga en el ENGINE, jamás aflojando
el check.

## 7 · Versionado y no-regresión

- `engines/presupuesto` 0.4.0 → **0.5.0** (aditivo; coste intacto). `versions.lock [contracts.C5]`
  `engine_version = "0.5.0"`; `banco-carbono` en fila nueva `[packs.banco_carbono]`.
- **Sin release** (la Llave 2 del carbono espera a que JM lo decida, probablemente al cerrar la Ola 2).
- El recompute del golden **no** corre en el sandbox (ifcopenshell) → se verifica en conda `mcp-bim` local
  antes del PR; en el sandbox se unit-testea la lógica de etapas/invariante (Decimal, texto puro) y la
  conformidad de esquemas.
