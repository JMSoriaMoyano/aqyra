# HILO-V2 · Evidencia cruzada — qué validó el hilo de cálculo (Estructurando 2.0) para §6

> **Qué es:** evidencia de respaldo para las decisiones abiertas §6.1–§6.4 del brief de V2, aportada desde el **hilo de cálculo estructural de Decopak HQ** (proyecto *Estructurando 2.0*), donde se hizo a mano el pre-proceso que Aqyra V2 va a industrializar. **La IA prepara la evidencia; JM decide y firma.**
> **Fecha:** 2026-06-24 · **Formato:** Markdown en el repo (§8). **Verificado** = ejercitado/medido en el hilo de cálculo; **[I]** = inferido.
> **Relación con `HILO-V2_evidencia-modelo-analitico.md`:** aquel inspeccionó los IFC *antes de escribir código*; este aporta la **prueba de uso**: el mismo modelo recorrido de extremo a extremo por un cálculo real.

---

## 0. Aviso de numeración (corregir antes de firmar)

El documento de evidencia del modelo analítico propone registrar estas decisiones como **D-008…D-011**, pero en `DECISIONES.md` el **D-008 ya está ocupado** (arquitectura de ejes/lentes + higiene BIM, V1). Para no cruzar trazas, esta nota usa la numeración corregida **D-009 (§6.1) · D-010 (§6.2) · D-011 (§6.3) · D-012 (§6.4)**. Ajustar el documento hermano al trasladar a `DECISIONES.md`.

## 1. De dónde sale esta evidencia

En *Estructurando 2.0* se calculó la estructura completa de Decopak HQ a partir del **mismo IFC** que usa Aqyra (`…HQ-Y-BIM-EST-02-…-S1-v0.0.ifc`). El flujo fue: validar el IFC → autorar hipótesis de acciones (aprobadas por JM) → derivar el modelo de análisis del físico → calcular (build) → **verificar con QA independiente**. Ese recorrido **es el pre-proceso de V2 hecho a mano**, así que sirve de banco de pruebas de las decisiones §6.

Artefactos (repo *Estructurando 2.0*, `pilotos/decopak-hq/calculo/` y `qa/informes/`): validación `01`, hipótesis `02`, geotecnia `04`, cálculos `05–07`, memoria `10`, e informes de QA `QA_DEC-*` + `QA_RESUMEN`.

## 2. El hecho compartido (verificado, coincide con §2 del doc hermano)

El IFC de Decopak HQ es **físico, sin dominio de análisis**: ni miembros analíticos, ni apoyos, ni cargas, ni eje de barra explícito. En el hilo de cálculo se constató lo mismo desde el otro lado: la validación `01` lo marcó como **«semilla» (geometría + materiales + estructura espacial)**, sin Psets de elemento ni acciones. → Todo el dominio de análisis hubo que **derivarlo y autorarlo**. Es exactamente la situación que §6 debe resolver.

## 3. Validación cruzada por decisión

### D-009 · §6.1 — Fuente del modelo analítico → **(b) derivar del físico: VALIDADA en uso**
- **Verificado:** el cálculo se hizo derivando el idealizado del modelo físico. El *build* obtuvo longitudes de barra desde los `IfcCartesianPoint`/placements y secciones desde los `…ProfileDef`. La **QA fue la prueba limpia**: reconstruyó los **nudos y la conectividad reales** de la geometría para montar un FEM nodal por rigidez directa (3 modos de sólido rígido exactos, equilibrio con residuo ~1e-12) — es decir, derivó el analítico del físico y lo resolvió.
- **Consecuencia para §6.1:** la vía (b) **no es solo viable, ya se ejercitó con éxito** sobre el caso guía. Confirma la recomendación de (b) como vía primaria. La vía (a) —leer `IfcStructuralAnalysisModel`— sigue sin aplicar al caso guía (CoordinationView no lo trae). 
- **Matiz [I] útil para Aqyra:** reconstruir el **eje** desde el `IfcExtrudedAreaSolid` (no hay `'Axis'`) y la **conectividad de nudos** es la parte con miga; el *build* lo hizo tosco (áreas tributarias + Vierendeel 2D) y solo la QA lo hizo nodal. El `pre` debe apuntar a la derivación nodal real, no a la aproximación global.

### D-010 · §6.2 — Write-back → **client-side con web-ifc: coherente (sin contraprueba)**
- **Verificado:** el IFC es **texto STEP diff-able**; en el hilo de cálculo se leyó y se manipuló como texto sin binario. El write-back de resultados/Psets es, por tanto, un diff de texto — coherente con D-010 y con D-002 ("sin servidor").
- **Límite honesto:** el hilo de cálculo **no ejercitó** el write-back en navegador (corrió en Python por restricciones de entorno), así que **no aporta contraprueba de web-ifc**; eso ya quedó probado en V1. No hay evidencia en contra.

### D-011 · §6.3 — Datos de cargas/apoyos → **Pset propio diff-able + autoría: VALIDADO el principio**
- **Verificado:** como el IFC **no trae cargas ni apoyos**, en el cálculo se **autoraron** (hipótesis de acciones `02`, apoyos de pilote/muro) y se trataron como **entradas propuestas pendientes de firma**, no como verdad. Es justo el modelo de D-011 (Pset Aqyra `proposal`) y del principio nº 3 (dos llaves).
- **Aporte para el modelo de datos:** lo que de verdad necesitó el cálculo y que el `Pset_AqyraStructural_*` debería poder representar: **acciones** (permanente, sobrecarga por categoría de uso, viento, nieve, **sismo** con ac), **coeficientes** γ y ψ, **apoyos** (empotrado/articulado/resorte), **casos** y **combinaciones** ELU/ELS + sísmica. Sirve como lista de campos mínima para diseñar el Pset.

### D-012 · §6.4 — Sub-API `pre` → **encaje confirmado + forma sugerida**
- **Verificado (de la superficie de código):** `pre` espeja el patrón `bcf`/`ids` del contrato `AqyraViewer` y el `DataState=proposal` ya está reservado — encaje limpio, MINOR.
- **Aporte:** el `getStructuralModel()` debe exponer lo que el cálculo consumió: **miembros idealizados con su eje y sección, nudos, apoyos, materiales**; y `listLoads/Cases/Combinations` lo de D-011. La derivación debería ser **enchufable** al estilo de `SpatialMetric` (`publico/visor/src/spatial-metric.ts`): una "estrategia de idealización" por tipología (edificación / obra lineal), no una sola heurística.

## 4. La lección crítica para el primer corte (§4): **la idealización es la fuente de error, no la lectura**

El hilo de cálculo lo demuestra con datos:

| Hallazgo de la QA | Qué enseña a V2 |
|---|---|
| **DEC-A1 (forjado CLT) NO APTO.** El *build* erró flecha (2,6 → **9,87 mm**) y frecuencia (8,5 → **~6–7 Hz**): el forjado **incumple vibración f₁≥8 Hz (EC5)**. | El error **no** estuvo en leer la geometría, sino en **cómo se idealizó/calculó** el elemento. Una autoderivación silenciosa lo habría propagado. |
| **DEC-B4 (montante).** Su seguridad depende de la **longitud de pandeo real** (3,08 m arriostrado vs 9,25 m no): u pasa de 0,40 a 2,1. La QA lo resolvió **leyendo los nudos reales**, no asumiendo. | La idealización (¿qué barra está coaccionada en qué nudo?) **cambia el veredicto**. Debe ser explícita y trazable. |
| **S-A2.** La costilla del cassette se reinterpretó de ménsula de 6,55 m a nervio biapoyado de 3,86 m. | Decidir **qué luz/condición de apoyo** toma cada elemento es una **decisión de ingeniería**, no un dato del IFC. |

**Requisito de producto que se deriva (propuesta para §4):** en V2, la **idealización derivada del físico debe presentarse como `proposal` revisable por un humano** (preview/diff, posibilidad de corregir luz, apoyos y coacciones), nunca como un hecho cerrado. Es coherente con el gobierno de dos llaves y con D-008 (lo que la IA deriva es `proposal` con preview + aprobación). El "mínimo demoable" del §4 (derivar ejes → autorar un apoyo y una carga → un write-back Pset) está bien planteado **siempre que la idealización quede editable y marcada como propuesta**.

## 5. Síntesis para la firma

| Decisión (renum.) | Propuesta del doc hermano | Aporte de esta evidencia |
|---|---|---|
| D-009 §6.1 | derivar del físico (b) primaria | **Validada en uso** (build + QA nodal sobre el caso guía) |
| D-010 §6.2 | write-back client-side web-ifc | Coherente (IFC texto diff-able); sin contraprueba, ya probado en V1 |
| D-011 §6.3 | Pset Aqyra `proposal` diff-able | **Principio validado** (cargas/apoyos autorados); lista de campos mínima aportada |
| D-012 §6.4 | sub-API `pre` read-only, MINOR | Encaje confirmado; forma sugerida + derivación enchufable (estilo `SpatialMetric`) |

Ninguna de estas decisiones es de la IA: **las cierra y firma JM**. Esta nota solo aporta la evidencia de uso.

## 6. Fuentes

- Hilo de cálculo Decopak HQ (*Estructurando 2.0*): `pilotos/decopak-hq/calculo/01,02,04,05–07,10` e `qa/informes/QA_DEC-A1/B4/…` + `QA_RESUMEN` (medido 2026-06-24).
- IFC común: `pilotos/decopak-hq/modelo/DEC-PB-EBAN-HQ-Y-BIM-EST-02-EstructuraNucleoLateral-S1-v0.0.ifc`.
- Doc hermano: `HILO-V2_evidencia-modelo-analitico.md` (§2 hallazgo, §3 propuestas §6).
- Superficie de código citada: `publico/embed/src/contract.ts` (`AqyraViewer`, `DataState`, `bcf`/`ids`); `publico/visor/src/spatial-metric.ts` (métrica enchufable); `publico/demo/src/calculista.ts:324` (comandos pre reservados).

---

*Evidencia preparada por la IA (equipo técnico de Estructurando 2.0, aportando al hilo V2 de Aqyra) · 2026-06-24 · para la firma de §6 por JM. La IA opera; JM decide y firma.*
