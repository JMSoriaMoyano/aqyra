# Aqyra · Cierre de V2 (pre-proceso) y arranque de V3 (post-proceso)

> **Cómo usar este texto:** pégalo como **primer mensaje** del nuevo hilo (proyecto Cowork *Aqyra*). Es autocontenido: resume lo hecho en V2, lo que queda pendiente, y en qué consiste V3. La IA opera; **JM decide y firma**.
> **Fecha:** 2026-06-25.

---

## 0. Quién eres
Eres el equipo de producto e ingeniería de **Aqyra** (visor OpenBIM asistido por IA; el "cebo"): Producto, frontend (web-ifc/That Open + Three.js), integración OpenBIM y la superficie del copiloto NL. **JM** dirige y **firma**; la IA opera y **no firma ni certifica**. Consumo **anclado** del núcleo vía `integracion/versions.lock`; no se bifurca. Frontera **cebo (`publico/`) / anzuelo (`privado/`)**. Dos llaves: lo derivado/autorado es `proposal`; el visor nunca pinta como `verified-signed` lo no firmado.

## 1. Qué se hizo en V2 (pre-proceso estructural visual) — IMPLEMENTADO

Todo en `publico/` (cebo), todo en estado `proposal`, revisable por humano (lección D-008: los errores nacen de la **idealización**).

**Derivación del modelo analítico** (`visor/src/idealize.ts`, enchufable estilo `SpatialMetric`):
- **Barras:** ejes por **PCA** de la geometría teselada (Decopak HQ no trae `'Axis'`); clasificación por `PredefinedType`; nudos por clustering con **tolerancia** (D-014, 150 mm).
- **Conectividad:** `splitAtIntersections` (parte una barra donde acomete el extremo de otra: vigueta→viga, pilar pasante) y `connectCrossings` (cruce interior ortogonal alineado a ejes: tirante×forjado, rejilla). Conservador: excluye aspas inclinadas.
- **Superficies** (losas/muros): plano por PCA, **contorno y área REAL** (envolvente convexa, no el rectángulo — Indicación A), idealización **diafragma/lámina seleccionable** (D-016); malla shell por rejilla.
- **Calidad/idealización** (Indicación C): detección **GRUESO** (t/luz>0,1 → lámina delgada no aplica), **TORCIDO** + **verticalización** de muros (un muro es vertical; si el plano PCA sale ladeado se endereza), **no-plano** (caja/núcleo → no colapsar a un plano, Indicación B).
- **Núcleos:** (a) **columna-cajón equivalente** (`deriveCores`) con propiedades de **sección hueca** (A, Ix, Iy = exterior−interior) + **J de Bredt**; (b) **detección de grupo-núcleo** por adyacencia de esquinas (caja cerrada / U abierta); (c) **4 láminas cosidas** (`buildCoreShell`: malla unificada que comparte los nudos de esquina → caja conectada).

**Autorado + write-back** (`openbim/src/index.ts` `PreApi`/`PreAdapter`):
- Apoyos (`setSupport`, empotrado), cargas (`addLoad`, distribuida/puntual), casos (G/Q) y una combinación ELU genérica editable.
- **Write-back diff-able (D-010/D-011):** `appendStructuralPset` añade el anejo `Pset_AqyraStructural` como **líneas STEP al final del DATA** (sin re-serializar; mínimo diff, idempotente, reversible con `stripStructuralPset`). Round-trip verificado.

**Superficie (skin Calculista, `demo/calculista.html`):** barra de comandos NL (stub de reglas) que despacha a `pre` — "ver el analítico", "apoyo empotrado", "sobrecarga de N kN/m", "muros como lámina / forjados como diafragma", "columna-cajón", "4 láminas", "exporta las cargas". Render: wireframe idealizado (cian), nudos (puntos), apoyos/cargas (glifos), superficies (diafragma verde / lámina naranja / no-plano rojo / grueso rosa / torcido rojo / núcleo teal-ámbar), físico en **fantasma**. UX: cartel de aviso **persistente** (sin ✕, se retira al resolver el modelado), **etiquetas por núcleo clicables y cerrables**, ✕ en menú contextual.

**Contrato:** sub-API `pre` cableada vía `StructuralProvider` (mantiene `openbim` desacoplado de `visor`). Bump SemVer MINOR `@aqyra/embed` → **0.4.0**.

**Decisiones firmadas (en `DECISIONES.md`):** D-009..D-012 (§6), **D-013** write-back por append, **D-014** tolerancia de nudos + partido + cruces, **D-015** unidades/signos (provisional), **D-016** superficies diafragma/lámina, **D-017** correcciones desde el cálculo (A área real, B núcleo no-plano + columna-cajón + grupos + 4 láminas, C grueso + torcido/verticalización).

**Verificación:** typecheck limpio y **38 tests verdes** confirmados en Windows (9 suites). Los tests añadidos DESPUÉS (grueso, torcido, verticalización, cosido de 4 láminas, columna-cajón hueca, grupos) están **validados con lógica pura en sandbox** pero **pendientes de re-sellar** con `npm run typecheck; npm test` (el sandbox no ejecuta pnpm: node_modules instalado en Windows). Arreglos de entorno aplicados: ruta del WASM por `require.resolve` (`visor/test/_wasm.ts`), `@types/node` fuera del typecheck, lanzador `INICIAR_VISOR_npm.bat`.

## 2. Pendiente de V2 (la IA propone; JM firma)

1. **Tipificación de uniones (rígido/articulado)** — la 2.ª mitad de la "terna" que quedó aplazada y **no implementada**: nudos rígidos por defecto, liberar extremos a articulado, editable; representar releases en el Pset.
2. **4 láminas para EST-02** (núcleo en **un** `IfcWall` hueco): falta **partir ese elemento en caras** por clustering de triángulos/normales → exige llevar la **topología de malla** (triángulos+normales) a la derivación (refactor del flujo de datos). Hoy solo se cubre EST-01 (núcleo autorado por caras).
3. **Carga por área (Indicación A2):** aplicar q sobre el área real → cargas en vigas de borde; separar formalmente **diafragma-rigidez** de **superficie-de-carga**.
4. **Afinado de umbrales:** tolerancia de nudos (D-014), planar/grueso/torcido, posible sobre-marcado de "no-plano" tras verticalizar.
5. **Re-sellar tests** en Windows (los añadidos tras los 38 verdes) y **convenio de signos** definitivo antes del puente al motor (D-015).
6. **Cierre de producto:** consolidar DoD/demo, gate legal de publicación de `publico/` (D-003), sello del release N1.1 del núcleo.

## 3. En qué consiste V3 (post-proceso bajo dos llaves)

V3 conecta el modelo `proposal` de V2 con el **cálculo** y devuelve resultados **verificados y firmados**.

- **Puente al motor de cálculo (contrato C5, `motor-fem`):** vive en `privado/` (anzuelo), consumido **anclado**. Consume el modelo analítico (barras, nudos, apoyos, cargas, casos/combinaciones, superficies, núcleos, releases) y **ensambla y resuelve el FEM**: cose las mallas shell (las 4 láminas → sección cerrada real), resuelve la columna-cajón, aplica releases/área de carga/combinaciones (ELU/ELS + sísmica).
- **Resultados sobre el modelo:** **esfuerzos (N/V/M), deformada, aprovechamientos**, y el "qué no cumple", pintados en el visor con su **estado de dato**.
- **Dos llaves:** los resultados se muestran como `verified-signed` **solo** tras QA independiente + **firma de JM**; el visor nunca pinta como verificado lo no firmado.
- **Armado:** del núcleo (de esfuerzos de membrana/placa de las láminas o de la sección cajón) y de elementos, en entorno certificado; **re-ejecución de la QA con PyNite** (carril *Estructurando 2.0*).
- **Fuera de V3:** copiloto NL con **criterio del corpus** (qué cargas/combinaciones tocan por norma) → **V4**; BCF/IDS → V1·F3/F4.

## 4. Reglas de trabajo (heredadas)
- Antes de cada tarea, **leer los README** de las carpetas implicadas (`publico/`, `privado/`, `integracion/`) y los `HILO-V2_*` + `DECISIONES.md`.
- **Search-first** para estándares (IFC structural, EC0/EC1/EC2, Bredt…); citar fuente y fecha; distinguir verificado de inferido.
- **Formato:** Markdown en el repo; sin `.docx` salvo petición.
- Todo resultado de cálculo, **bajo dos llaves**. La IA prepara la evidencia; **JM firma**.

---

*Cierre de V2 y arranque de V3 · proyecto Aqyra · IA (PM / Ing. BIM-IFC) · 2026-06-25 · para lanzar el hilo de V3.*
