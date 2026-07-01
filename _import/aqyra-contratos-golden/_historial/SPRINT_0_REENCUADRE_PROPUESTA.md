# Sprint 0 — Propuesta de reencuadre alrededor del foso

**Estado:** PROPUESTA — pendiente de firma de JM · **Fecha** 2026-06-23 · **Versión** 1.0
**No sobrescribe** el `SPRINT_0.md` canónico. Es una propuesta de reordenación a la luz de `TESIS_PRODUCTO.md`. Si JM la aprueba, se promueve al canónico.

> Preparado por la IA (PM). El gobierno manda: la IA propone, JM firma.

---

## 1. Qué cambia y por qué

El Sprint 0 canónico instrumenta la medición y siembra un wedge de «visor + checklist». La tesis lo reencuadra: **el wedge es crear el modelo desde lenguaje natural, y el foso es el corpus golden verificado y recuperable por OIR.** El Sprint 0 debe, por tanto, sembrar el **foso**, no la capa de documentación.

Lo que **se mantiene** (sigue siendo correcto): el gobierno de QA y versiones (GOV-1, GOV-2 ✅), el monorepo y el primer tag (N1.1), el oráculo de referencia (N2.2), las métricas de ROI (A2.1, con métrica estrella nueva) y el tablero (N3.2).

Lo que **se reencuadra:** las tareas del Track B y la prioridad del esfuerzo.

## 2. Las tres preguntas que el Sprint 0 debe dejar resueltas

1. **¿Cuál es la unidad de caso golden?** → «respuesta verificada a un OIR/AIR/PIR, en una fase». Hay que fijar su esquema (qué campos, qué metadatos, cómo registra la procedencia del oráculo y la firma).
2. **¿Cómo se recupera y reaplica?** → diseño de la capa de indexado · recuperación · reaplicación keyed a requisitos de información. Es la pieza nueva y el grueso del valor.
3. **¿Se reproduce sin JM?** → Decopak HQ como prueba E2E de que la semilla→modelo→verificación funciona con alguien que no es JM.

## 3. Backlog reencuadrado del Sprint 0

| ID | Tarea | Cambio | DoD |
|----|-------|--------|-----|
| GOV-1 / GOV-2 | Gobierno de QA y versiones | Sin cambio (✅ cerrado) | Ya hecho |
| N1.1 | Monorepo + primer tag del núcleo | Sin cambio | Tag publicado y anclado en `versions.lock` |
| N2.2 | Oráculo de referencia | Sin cambio | PyNite por defecto + jerarquía documentada |
| **F1.1** *(nueva)* | **Esquema de la unidad de caso golden** | Define el átomo: respuesta verificada a un OIR, en una fase; campos, metadatos, procedencia del oráculo, firma | Esquema escrito y aprobado por JM |
| **F1.2** *(nueva)* | **Diseño de la capa de recuperación/reaplicación por OIR** | Cómo se indexa, se busca y se reaplica un golden ante un nuevo OIR | Diseño (no implementación) aprobado por JM |
| **B1.1 / B1.2** | Alcance y frontera del wedge | **Reescritas** (v2): modelo desde lenguaje natural sobre corpus golden | En `producto-wedge/PRD/` (hecho, pendiente firma) |
| **B2.1** *(reencuadrada)* | Decopak HQ como prueba E2E | El IFC semilla existente se lleva de semilla → modelo calculable → caso golden verificado | 1 caso golden Decopak HQ acuñado por dos llaves |
| A2.1 | Métricas de ROI | **Métrica estrella nueva:** coste marginal del caso N+1 vs N (prueba del flywheel) | Cuadro aprobado por JM (hecho, pendiente firma) |
| A2.2 | Instrumentar registro de tiempos | Sin cambio | Plantilla probada en un caso real |
| N3.1 | KPIs del gate de fase | Añadir KPI «coste marginal decreciente del caso N+1» | Cuadro de KPIs aprobado |
| N3.2 | Tablero de seguimiento | Sin cambio | Backlog enlazado y actualizándose |

## 4. Prioridad del esfuerzo (la trampa a evitar)

> **Vigilar:** sobreinvertir en el motor de lenguaje natural (vistoso, demoable, **copiable**) e infrainvertir en F1.1/F1.2 (aburrido, **defendible**). Orden de prioridad:

1. **F1.1 + F1.2** — la capa golden/recuperación por OIR (el foso). No existe ni en Estructurando.
2. **B2.1 (Decopak HQ)** — la prueba E2E que valida unidad + recuperación + acuñación.
3. El motor lenguaje natural → IFC (`narracion-a-ifc`) — table stakes; lo justo para que funcione.

## 5. Definición de «Sprint 0 reencuadrado terminado»

- [ ] Monorepo con primer tag anclado (N1.1) y oráculo fijado (N2.2).
- [ ] **Unidad de caso golden definida** (F1.1) y **capa de recuperación por OIR diseñada** (F1.2).
- [ ] Alcance y frontera del wedge v2 escritos (B1.1/B1.2) ✅.
- [ ] **Un caso golden de Decopak HQ acuñado** por dos llaves (B2.1) — prueba de que la semilla se industrializa.
- [ ] Métricas de ROI con la métrica de flywheel (A2.1) e instrumentadas (A2.2).
- [ ] Tablero en uso (N3.2). Gobierno cerrado (✅).

→ Habilita el M2: reaplicar el golden de Decopak HQ a un segundo caso y **medir si el N+1 cuesta menos** (primera evidencia del foso girando).

---

### Firma

| Rol | Nombre | Estado |
|---|---|---|
| Prepara (IA · PM) | equipo IA Estructurando 2.0 | Entregado 2026-06-23 |
| Aprueba/firma | **JM** | ☐ Pendiente |
