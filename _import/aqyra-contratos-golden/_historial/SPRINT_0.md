# Sprint 0 — Arranque  (≈ M1, 2–3 semanas)

**Objetivo:** montar los rieles mínimos, instrumentar la medición *antes* de tocar los pilotos, sembrar el PRD del wedge y fijar el oráculo de referencia. **Salida del Sprint 0** = poder ejecutar los pilotos de extremo a extremo en M2, con medición de ROI y QA en marcha.

**Convención de responsable:** `JM` = decide/ejecuta (roles humanos). `IA (rol)` = opera. Donde la IA opera y JM aprueba, se indica `IA opera · JM aprueba` (la IA prepara la evidencia; la responsabilidad y la firma son de JM).

## Tareas del Sprint 0

| ID | Tarea | Track | Responsable | Criterio de aceptación (DoD) | Depende |
|----|-------|-------|-------------|------------------------------|---------|
| **GOV-1** | Diseño de QA independiente | N | JM | ✅ Cerrado en `GOBIERNO_QA_Y_VERSIONES.md` (3 capas, dos llaves, anti-gaming). | — |
| **GOV-2** | Contrato de versiones entre proyectos | N | JM | ✅ Cerrado en `GOBIERNO_QA_Y_VERSIONES.md` (SemVer de contratos, productor/consumidor, pin). | — |
| **N1.1** | Consolidar monorepo y control de versiones | N | JM (Núcleo) · IA (código) | Repo único estructurado; esquema de tags/SemVer documentado; **primer tag del núcleo publicado** y reflejado en `versions.lock`. | GOV-2 |
| **N3.1** | KPIs de fase y umbrales del gate | N | JM | Cuadro de KPIs y criterios de salida de Fase 0 escritos y aprobados (base: `metricas/`). | — |
| **N3.2** | Tablero de seguimiento del backlog | N | IA (PM) · JM aprueba | `Backlog_Fase0_operativo.xlsx` en uso y enlazado; estados actualizándose. | N3.1 |
| **A2.1** | Definir métricas de ROI (horas/entregable, retrabajo) | A | IA (PM) · JM aprueba | Cuadro de métricas y método de medición aprobado por JM. | — |
| **A2.2** | Instrumentar el registro de tiempos | A | IA (PM) | Plantilla/herramienta de registro lista y probada en un caso real. | A2.1 |
| **B1.1** | Delimitar alcance funcional del wedge | B | IA (PM) · JM (Negocio) | Lista de funcionalidades del MVP (Visor + ISO 19650 + CTE) en `producto-wedge/PRD/`. | — |
| **B1.2** | Definir la frontera con el cálculo | B | IA (PM) · JM aprueba | Documento de frontera: qué **no** hace el wedge (sin firma estructural). | B1.1 |
| **N2.2** | Fijar el oráculo numérico de referencia | N | JM (Núcleo) · IA (QA) | PyNite fijado como espejo por defecto; criterio de jerarquía documentado (remite a Gobierno §B.3). | — |

> **Dos victorias de salida:** GOV-1 y GOV-2 ya están cerradas — el Sprint 0 arranca con el gobierno hecho.

## Definición de «Sprint 0 terminado»

- [ ] Monorepo consolidado con **primer tag del núcleo publicado** y anclado en `versions.lock`.
- [ ] Métricas de ROI **definidas e instrumentadas** (listas para capturar baseline desde el primer cálculo de los pilotos).
- [ ] **Alcance y frontera** del wedge escritos en `producto-wedge/PRD/`.
- [ ] **Oráculo de referencia** fijado (PyNite por defecto + criterio de jerarquía).
- [ ] **Tablero** en uso, conectado al backlog.
- [ ] Gobierno de QA y versiones cerrado (✅ hecho).

→ Habilita el **M2**: ejecutar Decopak HQ y Terres Cavades de extremo a extremo (A1.2), formalizar los primeros casos golden (N2.1) y preparar el pitch de Can Cabassa (B3.2).

## Notas de gobierno aplicables ya

- **QA independiente:** el agente que genera el cálculo no es el que lo verifica. Run de QA separado, con su oráculo.
- **Dos llaves:** un resultado solo se «certifica» con golden verde + informe de QA limpio + **firma de JM**.
- **Versiones:** 2.0 consume **versiones ancladas** del núcleo; nunca la rama viva. Subir de versión = re-correr golden y adoptar solo si verde.
