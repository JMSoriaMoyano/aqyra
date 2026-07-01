# HILO-V2 · §6 (D-009…D-012) — FIRMADO + traspaso al hilo de desarrollo

> **✅ ESTADO: FIRMADO por JM el 2026-06-24.** Las cuatro decisiones (D-009…D-012) están inscritas en `DECISIONES.md`. El primer corte de V2 queda **DESBLOQUEADO** (ver §B). Este documento se conserva como evidencia del traspaso.
>
> **Qué fue:** las cuatro decisiones abiertas del brief de V2 (§6.1–§6.4), redactadas en formato `DECISIONES.md`. La IA preparó la evidencia; **JM decidió y firmó**.
> **Fecha:** 2026-06-24 · **Evidencia de respaldo:** `HILO-V2_evidencia-modelo-analitico.md` (inspección de IFC) + `HILO-V2_evidencia-cruzada_calculo.md` (prueba de uso desde el cálculo de Decopak HQ).

---

## A. Cómo firmar (procedimiento)

La firma es **documental**: una decisión queda firmada cuando se inscribe en `DECISIONES.md` con firmante y fecha (patrón de D-001…D-008). No requiere GPG (eso es solo para el sello del release N1.1 del núcleo, D-005). Dos vías equivalentes:

1. **JM directamente:** copiar las entradas de la sección C a `DECISIONES.md`, poner `Fecha de firma` + `Firmante: JM` y marcar `FIRMA: ✅`.
2. **Encargo a la IA:** indicar "firmo D-009…D-012 (o las que apruebes) con fecha de hoy"; la IA traslada las entradas a `DECISIONES.md` con la firma registrada. La decisión la toma JM; la IA solo la inscribe.

Se puede firmar **parcial** (p. ej. cerrar D-010/D-011/D-012 y dejar D-009 en revisión). El arranque de código (§B) solo necesita D-009 y D-012 firmadas; D-010/D-011 afinan el primer write-back.

## B. Traspaso al hilo de desarrollo de V2 (qué se desbloquea al firmar)

- **Antes de firmar:** el primer corte (§4 del brief, §7) **no arranca**. Estado actual: V1 cerrado en F2; los comandos de pre-proceso en la skin Calculista (`publico/demo/src/calculista.ts:324`) aún responden "V2 no disponible".
- **Al firmar D-009 + D-012:** se puede empezar el **mínimo demoable**: derivar ejes del físico → render wireframe del idealizado → autorar **un** apoyo y **una** carga (`DataState=proposal`) → **un** write-back Pset client-side → conectar los comandos reservados de la skin Calculista. Contrato extendido con la sub-API `pre` (SemVer **MINOR**).
- **Requisito de producto que arrastra la evidencia cruzada (no negociable):** la idealización derivada se presenta como **`proposal` revisable por un humano** (preview/diff; luz, apoyos y coacciones editables), nunca como hecho cerrado. Motivo: en el cálculo de Decopak HQ los errores nacieron de la idealización, no de la lectura (forjado CLT NO APTO; longitud de pandeo del montante). Ver `HILO-V2_evidencia-cruzada_calculo.md` §4.
- **Pendiente que NO bloquea §6 pero conviene tener presente:** la verificación estructural que respalda D-009 se hizo en predimensionado **verificado sin el oráculo PyNite** (re-ejecución en entorno con dependencias pendiente, en *Estructurando 2.0*). Esto **no** condiciona las decisiones de producto/arquitectura de §6 — solo la certificación estructural, que va por su carril de dos llaves.

---

## C. Entradas (✅ FIRMADAS 2026-06-24 — ya en `DECISIONES.md`)

> **✅ Trasladadas a `DECISIONES.md` como D-009…D-012, firmadas por JM el 2026-06-24.** Las entradas de abajo se conservan como copia de trabajo; la versión canónica y firmada es la de `DECISIONES.md`.
> **Nota de numeración:** el doc de evidencia del modelo analítico las propuso como D-008…D-011, pero **D-008 ya está ocupado** (ejes/lentes, V1). Numeración corregida y firmada: **D-009…D-012**.

### D-009 · §6.1 — Fuente del modelo analítico
- **Fecha de firma:** ____ · **Firmante:** JM · **FIRMA: ☐ pendiente**
- **Decisión (propuesta):** **derivar el idealizado del modelo físico (b)** como vía primaria (ejes desde la trayectoria de extrusión de `IfcBeam`/`IfcColumn`/`IfcMember`, sección desde `…ProfileDef`, clasificación por `PredefinedType`); **leer `IfcStructuralAnalysisModel` (a)** si el IFC de entrada lo trae; **consumir el analítico del núcleo (c)** como puente aguas abajo. Apoyos y cargas **siempre autorados** en Aqyra (no vienen en la entrada).
- **Evidencia:** `HILO-V2_evidencia-modelo-analitico.md` §2 (Decopak HQ sin dominio de análisis); `HILO-V2_evidencia-cruzada_calculo.md` §3 (vía (b) **ejercitada con éxito**: la QA reconstruyó nudos y conectividad reales para el FEM nodal).
- **Acciones que dispara:** el primer corte deriva el eje del `IfcExtrudedAreaSolid` (no hay `'Axis'`); la derivación se diseña **enchufable** (estilo `SpatialMetric`) por tipología; la idealización sale como `proposal` revisable.

### D-010 · §6.2 — Dónde regenera / write-back
- **Fecha de firma:** ____ · **Firmante:** JM · **FIRMA: ☐ pendiente**
- **Decisión (propuesta):** persistir cargas/apoyos **client-side con web-ifc** (texto diff-able), honrando D-002 ("sin servidor"); **reservar** un backend Python/IfcOpenShell solo si la regeneración paramétrica completa lo exige más adelante.
- **Evidencia:** D-002 + write-back de web-ifc probado en V1; `HILO-V2_evidencia-cruzada_calculo.md` §3 (IFC tratado como texto STEP diff-able en el cálculo).
- **Acciones que dispara:** el write-back del primer corte es client-side; queda como residual la opción backend para Capa 2·C íntegra.

### D-011 · §6.3 — Modelo de datos de cargas/combinaciones
- **Fecha de firma:** ____ · **Firmante:** JM · **FIRMA: ☐ pendiente**
- **Decisión (propuesta):** representar apoyos, cargas, casos y combinaciones como **Pset Aqyra `Pset_AqyraStructural_*`** *diff-able* en estado `proposal`, sin depender de entidades `IfcStructuralLoad*` nativas; **diferir a ≈V3** la emisión nativa para interoperar con el motor.
- **Evidencia:** entradas sin cargas/apoyos (§2 doc hermano); `HILO-V2_evidencia-cruzada_calculo.md` §3 (campos mínimos que necesitó el cálculo: acciones —incl. sismo ac—, γ/ψ, apoyos, casos, combinaciones ELU/ELS+sísmica).
- **Acciones que dispara:** diseñar el esquema del Pset con esa lista de campos mínima.

### D-012 · §6.4 — Extensión del contrato `AqyraViewer`
- **Fecha de firma:** ____ · **Firmante:** JM · **FIRMA: ☐ pendiente**
- **Decisión (propuesta):** añadir una sub-API **`pre`** de solo lectura (espejando `bcf`/`ids`), datos en `proposal`, versionada **SemVer MINOR**: `getStructuralModel()`, `listSupports()/setSupport()`, `listLoads()/addLoad()/removeLoad()`, `listLoadCases()/listCombinations()`.
- **Evidencia:** patrón `bcf`/`ids` y `DataState` ya en `publico/embed/src/contract.ts`; `HILO-V2_evidencia-cruzada_calculo.md` §3 (qué debe exponer `getStructuralModel`: miembros con eje y sección, nudos, apoyos, materiales).
- **Acciones que dispara:** extender `contract.ts` (MINOR), implementar la sub-API en el primer corte, conectar la skin Calculista.

---

*Procedencia: para-firma de §6 · proyecto Aqyra, hilo V2 · evidencia preparada por la IA · 2026-06-24. Tras la firma (total o parcial), trasladar las entradas a `DECISIONES.md` y arrancar el primer corte. La IA opera; JM firma.*
