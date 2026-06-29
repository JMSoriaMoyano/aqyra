# HILO-V2 · Primer corte — contrato `pre` (hecho) + plan del mínimo demoable

> **Qué es:** el primer entregable de desarrollo de V2, dejado **preparado** tras la firma de §6 (D-009…D-012). Contiene (A) la **extensión de contrato ya aplicada** y (B) el **plan del mínimo demoable** para implementarla. La IA opera; **JM firma**.
> **Fecha:** 2026-06-24 · **Base:** brief `HILO-V2_brief_preproceso.md` (§4 primer corte, §5 DoD) + evidencia `HILO-V2_evidencia-cruzada_calculo.md`.

---

## A. Contrato `pre` — YA APLICADO (superficie + stubs, estilo F0)

Cambio **aditivo (SemVer MINOR)**, espejando el patrón `bcf`/`ids`: superficie declarada y stubs; la implementación es el primer corte. Ficheros tocados en `publico/`:

| Fichero | Cambio |
|---|---|
| `openbim/src/index.ts` | Tipos del pre-proceso (`StructuralModel`, `StructuralNode`, `StructuralMember`, `SectionRef`, `Support`, `Restraints`, `Load`, `LoadCase`, `Combination`, `PreDataState`), interfaz **`PreApi`** y **`PreAdapter`** (lecturas → vacío; derivación/mutaciones → `throw later(...)`). |
| `embed/src/contract.ts` | Importa/re-exporta los tipos `pre`; añade `readonly pre: PreApi` a `AqyraViewer`. |
| `embed/src/element.ts` | Cablea `readonly pre: PreApi = new PreAdapter()` en `<aqyra-viewer>`. |

**Superficie de `PreApi`** (solo lectura del contrato; las mutaciones autoran entradas `proposal`):

```ts
getStructuralModel(): Promise<StructuralModel>;   // derivado del físico (D-009) o leído si la entrada trae dominio de análisis
listSupports(): Support[];   setSupport(nodeId, restraints): Support;
listLoads(): Load[];         addLoad(load): string;   removeLoad(id): void;
listLoadCases(): LoadCase[]; listCombinations(): Combination[];
```

> **Verificación pendiente (entorno de dev):** el `tsc` de este sandbox malinterpreta los UTF-8 del mount y da errores espurios en ficheros no tocados, así que **no se pudo type-checkear aquí**. El cambio es aditivo y mecánico (mismo molde que `bcf`/`ids`); **correr `pnpm typecheck && pnpm test` (12/12) en el entorno de dev** antes de dar por verde. El **bump MINOR de `@aqyra/embed`** se aplica al cerrar el primer corte, no ahora.

## B. Mínimo demoable (DoD §5) — pasos

El objetivo: cargar Decopak HQ y, hablando, ver la estructura idealizada + un apoyo + una carga, y que **una** edición persista al IFC. Cinco pasos:

1. **Derivar + visualizar el idealizado.** Implementar `getStructuralModel()` en `PreAdapter`: del físico de Decopak HQ, derivar **ejes de barra** y **nudos**; pintar el wireframe sobre el modelo. Sección desde `…ProfileDef`, clasificación por `PredefinedType`.
2. **Apoyos.** `listSupports()/setSupport()`: render de glifos de apoyo; autorar **un** empotrado (p. ej. base de pilote/zapata).
3. **Una carga.** `addLoad()`: autorar **una** carga (distribuida en una viga o puntual en un nudo) por menú contextual o barra de comandos; render como glifo de flecha con valor; `state="proposal"`.
4. **Un write-back.** Persistir esa carga/apoyo como **Pset Aqyra** en el IFC, **client-side con web-ifc** (D-010); reabrir → sigue ahí (texto diff-able).
5. **Superficie.** Conectar los comandos ya reservados en la skin Calculista (`publico/demo/src/calculista.ts:324`, regex `carga|sobrecarga|apoyo|empotr|barra|nudo|analitic|hipotesis`) para que **despachen** a `pre` en vez de avisar "V2 no disponible".

## C. Cómo derivar el modelo analítico (D-009)

- **Eje de barra:** no hay representación `'Axis'` en el IFC del caso guía → reconstruir del `IfcExtrudedAreaSolid` (colocación + dirección·profundidad de extrusión). Es el punto con miga (lo demuestra el hilo de cálculo).
- **Nudos y conectividad:** agrupar extremos coincidentes (con tolerancia) → grafo de nudos. **Resolver la conectividad REAL** (no áreas tributarias): es lo que en el cálculo distinguió el FEM nodal del predimensionado, y lo que reveló la longitud de pandeo real del montante.
- **Sección/material:** del `…ProfileDef` y `IfcRelAssociatesMaterial`.
- **Diseño enchufable:** estrategia de idealización por tipología, al estilo de `SpatialMetric` (`publico/visor/src/spatial-metric.ts`) — edificación primero; obra lineal después.

## D. Modelo de datos `Pset_AqyraStructural_*` (D-011)

Campos mínimos (de lo que necesitó el cálculo de Decopak HQ): **apoyos** (nodeId + 6 coacciones), **cargas** (tipo punt./distrib., objetivo, valor, dirección, caso), **casos** (naturaleza: permanente/uso/viento/nieve/sismo/térmica), **combinaciones** (estado límite + expresión, incl. sísmica con `ac`), y **coeficientes** γ/ψ. Todo en `state=proposal`. Emisión nativa `IfcStructuralLoad*` diferida a ≈V3.

## E. Requisito no negociable (de la evidencia cruzada §4)

La idealización derivada se presenta como **`proposal` revisable por un humano** — preview/diff; **luz, apoyos y coacciones editables** —, nunca como hecho cerrado. Razón: en el cálculo de Decopak HQ los errores nacieron de la idealización (forjado CLT NO APTO; longitud de pandeo del montante), no de leer la geometría. Coherente con D-008 (lo derivado es `proposal` con preview + aprobación) y con las dos llaves.

## F. Frontera cebo/anzuelo

`pre` (leer/derivar geometría, autorar, write-back) es **mecánica → cebo (`publico/`)**. El **criterio** —qué cargas/combinaciones tocan según norma/corpus— es **anzuelo (`privado/`)** y se enciende con el copiloto en **V4**; el puente al motor de cálculo (post-proceso) es **V3**. En V2 el NL sigue siendo el stub de reglas.

## G. Tests a añadir (verde antes de cerrar)

- `pre` declarada en el contrato y cableada (no rompe los 12 tests existentes).
- `getStructuralModel()` sobre Decopak HQ devuelve nudos/miembros coherentes con el inventario (231 `IfcMember`, 160 `IfcBeam`, …).
- `addLoad` + write-back: reabrir el IFC y recuperar el Pset (round-trip diff-able).
- `DataState` de todo lo autorado = `proposal`.

## H. Pendientes / decisiones que pueden surgir (para JM)

1. Tolerancia de coincidencia de nudos al construir el grafo (afecta a la conectividad).
2. Convenio de unidades y signos de cargas en el Pset.
3. Confirmar el bump de versión de `@aqyra/embed` (MINOR) al cerrar el corte.
4. (Recordatorio) re-ejecutar la QA del cálculo con PyNite en entorno certificado — carril de *Estructurando 2.0*, no bloquea V2.

---

*Procedencia: primer corte de V2 · proyecto Aqyra · contrato `pre` aplicado + plan · IA · 2026-06-24. Pendiente de `pnpm typecheck && pnpm test` en el entorno de dev y de la implementación de los pasos B. La IA opera; JM firma.*
