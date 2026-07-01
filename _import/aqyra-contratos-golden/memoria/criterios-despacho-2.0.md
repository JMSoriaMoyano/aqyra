# Criterios de despacho — Estructurando 2.0

> Memoria entre hilos del proyecto de industrialización. Lo que debe persistir entre sesiones: gobierno, roles, decisiones y convenciones. Se actualiza cuando se cierra una decisión o cambia un contrato.

**Versión** 1.0 · **Inicializada** 2026-06-23 · **Mantiene:** equipo IA · **Aprueba:** JM

---

## Naturaleza del proyecto

Estructurando 2.0 **industrializa** el ecosistema de agentes de ingeniería y lanza el **wedge** BIM/cumplimiento. Modelo dual: **Estructurando = productor** (publica versiones del núcleo); **Estructurando 2.0 = consumidor** (las usa ancladas en `versions.lock`) e industrializa. Una sola fuente de verdad: 2.0 nunca bifurca el núcleo de forma permanente.

## Reparto de roles (firme)

- **JM (humano):** Dirección · Negocio/Comercial · Ing. Núcleo FEM. **Responsable y firmante.**
- **IA (ecosistema Claude):** Ing. BIM-IFC · Producto (PM) · QA/Verificación · desarrollo de código. **Opera; JM aprueba.**

Regla operativa permanente: **la IA nunca firma ni certifica.** Prepara la evidencia para que JM firme. En tareas «IA opera · JM aprueba», el entregable se marca como *propuesta pendiente de firma de JM*.

## Gobierno de QA (resumen operativo)

- **QA independiente:** el agente que produce el cálculo NO es el que lo verifica. Run de QA separado, con su propio oráculo y contexto.
- **Tres capas de verificación:** numérica (oráculo), normativa (reglas de código), regresión (suite golden congelada en CI).
- **Certificación de dos llaves:** un resultado se certifica solo con (a) golden verde + (b) Informe de QA limpio + (c) **firma de JM** registrada. Es el peldaño N4 (trazable).
- **Anti-gaming:** un fallo de QA se resuelve arreglando el código, NUNCA aflojando tolerancia ni editando el valor esperado. Golden y tolerancias en zona protegida; cambiarlas exige PR aprobado por JM.

## Gobierno de versiones (resumen operativo)

- Se versionan los **contratos** (C1, C4, C5…) con SemVer. MAJOR = cambia un contrato (incompatible).
- 2.0 consume **versiones ancladas** (`versions.lock`), nunca «latest» ni la rama viva.
- Subir de versión es deliberado: bump del pin → re-correr suite golden → adoptar solo si verde.

## Decisiones de gobierno (estado)

1. Golden/contratos en zona protegida, propiedad de QA/JM, atados a la versión de contrato (golden vN valida contrato vN). — **Ratificada**
2. Jerarquía de oráculos (PyNite por defecto; analítico / 2.º código FEM / MMS donde PyNite no llegue). — **Abierta**, se resuelve caso a caso. JM elige el oráculo y fija la tolerancia.
3. Solo JM cambia tolerancias y valores golden, vía PR. — **Ratificada**

## Giro estratégico (sesión de brainstorm con JM, 2026-06-23)

> Documento fundacional: `TESIS_PRODUCTO.md`. Reemplaza el enfoque «visor + checklist».

- **El wedge es crear el modelo desde lenguaje natural**, no un visor con checklist (archivado). Cálculo, firma, obra y mantenimiento son bonus tracks que cuelgan de la misma semilla IFC viva.
- **Señuelo vs foso:** el modelado por lenguaje natural es table stakes (copiable). El **foso** es el corpus de casos golden **verificados y recuperables por OIR/AIR/PIR**. Lo escaso que se vende es la **confianza verificada**, que se acuña caso a caso (QA dos llaves + firma JM), no se scrapea.
- **Unidad de valor (átomo):** «respuesta verificada a un requisito de información, en una fase», no «el proyecto».
- **Archivo vs flywheel:** el valor no es acumular casos sino **recuperarlos y reaplicarlos** vía una capa de indexado por OIR (aún no existe). Pruebas de que gira: el caso N+1 cuesta menos que el N; lo produce alguien que no es JM.
- **QA = fábrica del foso:** cada certificación de dos llaves mina un activo defendible.
- **Decopak HQ** es la prueba E2E (IFC semilla nacido de lenguaje natural; voladizos → forjado CLT ligero, S355, EC3).

## Decisiones operativas del Sprint 0 (2026-06-23)

- **A2.1 — Unidad de medida del ROI:** se miden las CUATRO unidades como baseline: (1) comprobación por elemento, (2) memoria de cálculo, (3) QA/validación de IFC, (4) justificación CTE. **Métrica estrella nueva:** coste marginal decreciente del caso N+1 vs N (prueba del flywheel). Fuente: Decopak HQ y Terres Cavades.
- **B1.1 / B1.2 — reescritas (v2):** wedge = modelo desde lenguaje natural sobre corpus golden; las v1 (visor+checklist) están en `producto-wedge/PRD/_archivo/`.
- **Sprint 0 reencuadrado:** propuesta en `SPRINT_0_REENCUADRE_PROPUESTA.md` (no sobrescribe el canónico; pendiente firma JM). Prioridad: foso (capa golden/recuperación por OIR) sobre el motor de lenguaje natural.
- **Formato de entregables:** **solo Markdown** en el repo (decisión de JM, 2026-06-23). Nada de copias .docx para los documentos estratégicos/PRD salvo que JM lo pida explícitamente para un entregable concreto.

## Pilotos → tracks

| Piloto | Tipo | Track | Aporta |
|---|---|---|---|
| Decopak HQ | interno | A · uso interno | casos golden + baseline ROI |
| Terres Cavades | interno | A · uso interno | casos golden + baseline ROI |
| Can Cabassa | externo | B · wedge | validación del PRD + LOI |

## Convenciones

- Documentos vivos en Markdown dentro de la carpeta correspondiente del repo; copia .docx cuando requiera firma.
- Antes de cada tarea: leer los README de las carpetas implicadas.
- Toda métrica de ROI se captura desde el primer cálculo de los pilotos (medir antes de tocar nada).
