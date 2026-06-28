# HILO-V2 · Primer corte del pre-proceso — estado y handoff

> **Qué es:** estado del primer corte de V2 (pre-proceso estructural visual) implementado en `publico/`. La IA opera; **JM verifica y firma**.
> **Fecha:** 2026-06-24. **Formato:** Markdown en el repo (§8).
> **VERIFICADO EN WINDOWS (2026-06-24):** `typecheck` limpio (`TYPECHECK_EXIT=0`) y suite en verde con `npx tsc -p tsconfig.check.json` + `npx vitest run` (`pnpm` no estaba en el PATH; los scripts son `tsc`/`vitest` locales). El corte inicial selló **9 suites / 27 tests**; los ajustes de conectividad añaden 4 tests → **31** (validados también en sandbox; se recomienda una pasada final de `vitest`). Revisión visual de JM **HECHA** (Decopak HQ + estructura colgada de cerchas). El sandbox de la IA no podía ejecutar la suite (node_modules de Windows → symlinks pnpm rotos en Linux + disco lleno), por eso la verificación se hizo en la máquina de JM.

## 0. Arreglos de entorno aplicados durante la verificación (no eran bugs de lógica)

Al verificar afloraron **dos bugs latentes del harness/config** que habrían roto igual la suite de V1 (no los introdujo este corte):

1. **Ruta del WASM de web-ifc.** Los 6 tests que usan web-ifc asumían `process.cwd()/node_modules/web-ifc`, que **no existe con pnpm** (web-ifc es dep de `visor`, no se hoistea a la raíz). Arreglado con `publico/visor/test/_wasm.ts` (resuelve el paquete por el resolvedor de Node, `createRequire`) e importado en los 6 tests.
2. **`@types/node` en el typecheck.** `tsconfig.check.json` exigía `"types": ["node"]`, pero `@types/node` no está instalado ni declarado, y el `src` (código de navegador, lib DOM) no lo necesita. Arreglado dejando `"types": []`.
3. **Round-trip diff-able.** `stripStructuralPset` reponía `"\n"` y duplicaba el salto; corregido a `""` para que `strip(append(x)) === x` exactamente (test verde).

---

## 1. Qué hace ahora (DoD §7 del brief)

Sobre Decopak HQ (solo físico, sin dominio de análisis), hablando por la skin Calculista:

- **"ver el analítico" / "idealiza"** → deriva el modelo idealizado (ejes de barra + nudos **con conectividad**) del físico y lo pinta como wireframe cian con los **nudos como puntos** destacados; el físico se atenúa (modo fantasma) para que el analítico se lea. Etiquetado **PROPUESTA revisable** (D-008).
- **"apoyo empotrado aquí"** (con una barra seleccionada) → autora un empotrado en el nudo inferior (pilote/pilar) y pinta el glifo.
- **"añade una sobrecarga de 5 kN/m"** (con una viga seleccionada) → autora una carga distribuida (caso Q, sentido gravedad) y pinta la flecha.
- **"exporta el anejo / las cargas"** → descarga el IFC con el anejo Aqyra escrito; **reabriéndolo, las cargas/apoyos siguen ahí** (round-trip diff-able).
- **"muéstrame todo el modelo"** → restaura el físico (quita el fantasma).

Todo lo autorado/derivado es `state="proposal"` (dos llaves: nunca `verified-signed`).

**Conectividad del idealizado (validada visualmente sobre Decopak HQ y sobre la estructura colgada de cerchas, 2026-06-24):** además de fundir extremos coincidentes (tolerancia D-014, 150 mm), el modelo (a) **parte barras** donde el extremo de otra acomete a su vano (vigueta sobre viga, pilar pasante por planta) y (b) **inserta nudo en cruces interiores** ortogonales y alineados a ejes (tirante vertical × viga de forjado, rejilla de forjado), partiendo ambas. Conservador: las barras **inclinadas** (aspas de cercha/arriostramiento) quedan excluidas, así que no se conectan falsamente.

## 2. Cómo se implementó (decisiones de diseño)

- **Derivación (D-009).** El físico de Decopak HQ **no trae** `'Axis'`; el eje de cada barra se deriva por **PCA de la geometría teselada** (eigenvector dominante = eje largo del miembro). Estrategia **enchufable** (`IdealizationStrategy`, estilo `SpatialMetric`): `pcaAxisStrategy` por defecto. Solo barras (beam/column/member/pile); losas/muros se omiten (su idealización 2D llega después).
- **Conectividad (D-014).** Tres niveles: fundir extremos coincidentes (tolerancia 150 mm, filtro de eje nulo desacoplado), `splitAtIntersections` (extremo de una barra sobre el vano de otra) y `connectCrossings` (cruce interior de dos barras alineadas a ejes y ortogonales). Las inclinadas se excluyen → no conecta aspas. Flags para desactivar cada uno.
- **Visualización del overlay.** El idealizado, los nudos (puntos blancos de 5 px, tamaño fijo en pantalla) y los glifos de apoyo/carga se dibujan **siempre por encima** (`depthTest:false` + `renderOrder`); el físico se **atenúa** (`ghostPhysical`) al mostrar el analítico y se restaura con "muéstrame todo".
- **Write-back (D-010) — por APPEND de texto, no `SaveModel`.** El anejo Aqyra se **añade** como líneas STEP al final del bloque DATA del IFC original, dejando el resto intacto → **diff mínimo y reversible** (`stripStructuralPset` restaura el original byte a byte). `SaveModel` reescribe todo el fichero (diff enorme), por eso **no** se usa aquí. Sigue siendo client-side y sin servidor (D-002).
- **Modelo de datos (D-011).** Apoyos/cargas/casos/combinaciones se serializan a `Pset_AqyraStructural` como `IfcPropertySingleValue` con valor `clave=valor;…` (diff-able). Emisión nativa `IfcStructuralLoad*` diferida a ≈V3.
- **Contrato (D-012).** La sub-API `pre` ya declarada se cablea vía un `StructuralProvider` inyectado desde el Web Component (mantiene `openbim` desacoplado de `visor`). Bump **MINOR**: `@aqyra/embed` 0.1.0 → **0.2.0**.
- **Frontera cebo/anzuelo.** Toda la mecánica (derivar, autorar, persistir) es **cebo** (`publico/`). El **criterio** (qué cargas/combinaciones tocan por norma) **no** está aquí: las combinaciones se exponen como **expresión genérica editable** (`1.35·G+1.50·Q`), y la selección normativa queda para el copiloto (anzuelo, V4).

## 3. Ficheros tocados (`publico/`)

| Acción | Fichero |
|---|---|
| NUEVO | `visor/src/idealize.ts` — derivación PCA + clustering + clasificación + `splitAtIntersections` + `connectCrossings` (puro) |
| EDIT | `visor/src/ifc-loader.ts` — `deriveStructural`, `readStructuralPset`, `appendStructuralPset`/`stripStructuralPset`, `AQYRA_PSET` |
| EDIT | `visor/src/viewer.ts` — capa overlay: `setIdealization`/`setNodeGlyphs`/`setSupportGlyphs`/`setLoadGlyphs`/`ghostPhysical`/`clearOverlay` (dibujo por encima) |
| EDIT | `visor/src/index.ts` — exports nuevos |
| EDIT | `openbim/src/index.ts` — `StructuralProvider` + `PreAdapter` funcional (autorado `proposal` + serialización) |
| EDIT | `embed/src/element.ts` — proveedor inyectado, texto fuente por modelo, helpers de pre + render de nudos/glifos + export |
| EDIT | `embed/package.json` — 0.1.0 → 0.2.0 (MINOR) |
| EDIT | `demo/src/calculista.ts` — dispatch real de los comandos de pre (antes "V2 no disponible") |
| NUEVO | `visor/test/_wasm.ts` (resolución del WASM) · `visor/test/idealize.test.ts` (9) · `visor/test/pre-structural.test.ts` (4) · `openbim/test/pre.test.ts` (5) |

Suite: **9 suites · 31 tests** (12 de V1 + 19 nuevos).

## 4. Decisiones nuevas — FIRMADAS por JM (`DECISIONES.md`, 2026-06-24)

- **D-013 · Write-back por append STEP** (vs `SaveModel`): añadir el anejo al final de DATA, original intacto (diff-able, reversible, idempotente). *Residual:* confirmar que web-ifc reparsea comentarios STEP `/* */`.
- **D-014 · Tolerancia de coincidencia de nudos**: 20 mm por defecto, configurable. *Residual (no bloquea):* afinar a la vista de Decopak HQ real.
- **D-015 · Convenio de unidades/signos de carga (provisional)**: kN / kN·m⁻¹ positivos, sentido por `direction`, gravitatoria = `y` hacia −Y. *Residual:* confirmar el convenio de signos antes de conectar el motor (V3, C5).

## 5. Verificación

1. **Tests/typecheck (Windows, 2026-06-24):** `npx tsc -p tsconfig.check.json` → `TYPECHECK_EXIT=0`; `npx vitest run` → verde. El corte inicial dio **27 tests**; los **4 tests añadidos** de conectividad (T-split, no-split, tirante×forjado, aspa no-conecta) llevan la suite a **31** y se validaron además con comprobaciones de lógica pura en sandbox (Node). *Recomendado:* una pasada final de `npx vitest run` para sellar las 31 en verde.
2. **Revisión visual (JM) — HECHA ✅:** validado en navegador sobre **Decopak HQ** y sobre la **estructura colgada de cerchas**; la idealización con conectividad (tirantes conectando a forjados, rejilla viga-vigueta, aspas sin conectar) se confirmó correcta.

**Límites conocidos (siguiente incremento):** (a) la conexión de cruce asume tirantes/vigas **alineados a ejes globales** (zonas giradas en planta no se detectan aún); (b) **vigas no rectas** (en L/quebradas) se reducen a un eje recto → se ven "dobladas" (requiere derivar polilínea); (c) **muros/losas** sin analítico (lámina/diafragma) y **uniones sin tipificar** (rígida/articulada) — ver D-014.

---

*Estado preparado por la IA (PM / Ing. BIM-IFC) · Aqyra V2 primer corte · 2026-06-24 · para verificación y firma de JM.*
