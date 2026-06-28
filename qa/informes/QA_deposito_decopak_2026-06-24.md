# Informe de QA por cálculo — Depósito enterrado Decopak (Rubí)

**Elemento verificado:** depósito enterrado de HA, cajón estanco (Decopak, Rubí, Barcelona)
**Productor (rol build):** agente de cálculo · `calculo/calc_deposito.py` + `resultados.json`
**Verificador (rol QA, dos llaves):** agente de QA independiente · oráculo propio (no re-ejecuta el motor del productor)
**Marco:** `GOBIERNO_QA_Y_VERSIONES.md` §B.2 (tres capas) y §B.5 (procedencia del oráculo) — *quien produce no aprueba*
**Fecha:** 2026-06-24

> **ESTE INFORME NO CERTIFICA NI FIRMA.** La certificación (golden verde + informe QA limpio + **firma humana de JM**, dos llaves) es competencia exclusiva de JM. La QA emite veredicto técnico; no aprueba.

---

## 1. Resumen ejecutivo · VEREDICTO GLOBAL: **CON OBSERVACIONES (verde técnico con condiciones)**

El cálculo del productor es **numéricamente sólido y, donde difiere de mi oráculo, lo hace del lado de la seguridad**. He re-derivado todos los esfuerzos por vías independientes (analítica cerrada, mi propia viga FE Euler-Bernoulli, mi propia **placa 2D FEM** para la losa de cubierta, y mi propia BoEF/Hetényi para el raft). **Ningún caso cae en puerta roja por esfuerzos.** El veredicto no es LIMPIO por tres motivos que dependen de decisiones de JM o de un ajuste de armado, no de un error de cálculo:

- **O-1 (ajustar armado):** el raft incumple levemente estanqueidad (w_k = 0,222 mm > 0,20 mm). Confirmado por mi oráculo. Requiere subir armadura (φ20/175 → w_k=0,179, o φ25/200 → w_k=0,125). **Hasta que no se ajuste, es no-conforme en estanqueidad.**
- **O-2 (gate de JM):** la flotación del vaso vacío sólo es no crítica con el freático documentado (+144,6). Con freático a rasante FS=0,65 < 1 → **flotaría**. Es un gate de proyecto, no un fallo de cálculo.
- **O-3 (gate de JM):** la losa de cubierta de 11,37 m con IAP-11 LM1 es viable pero exige armadura muy pesada (φ25/100, ≈1%). Mi placa 2D **confirma** la viabilidad y que el ancho eficaz 1D del productor es razonable; queda la decisión de esquema (apoyo intermedio / canto) en manos de JM.

El punto que el propio productor marcó como crítico (reparto transversal del tándem por ancho eficaz 1D, "probablemente no conservador") **lo he resuelto con placa 2D independiente y resulta NO ser un problema**: el ancho eficaz real es ~8,45 m frente a los 8,79 m del productor → el productor es ligeramente conservador (~5% en la componente de tándem), no inseguro.

---

## 2. Capa numérica — Tabla por elemento (oráculo independiente)

| Elemento | Magnitud | Valor productor | Valor oráculo QA | Desv. | Tol. | Veredicto |
|---|---|---|---|---|---|---|
| Muro perimetral 50 | M_base agua (car.) | 54,80 kN·m/m | **54,87** (analítico p₀H²/15 y mi FE) | 0,1% | 2% | ✅ PASA |
| Muro perimetral 50 | R_cabeza agua | 18,92 kN/m | **18,92** (p₀H/10 y mi FE) | 0,0% | 2% | ✅ PASA |
| Muro perimetral 50 | M_base tierras (car.) | 92,60 kN·m/m | **92,72** (mi FE y superposición) | 0,1% | 2% | ✅ PASA |
| Muro perimetral 50 | M_diseño ELU | 125,0 kN·m/m | **125,2** | 0,2% | 2% | ✅ PASA |
| Muro interior 50 | M_base agua dif. | 54,80 kN·m/m | **54,87** | 0,1% | 2% | ✅ PASA |
| Losa cubierta 70 | M_perm (car.) | 307,0 kN·m/m | **307,0** (gL²/8) | 0,0% | 2% | ✅ PASA |
| Losa cubierta 70 | M_UDL (car.) | 145,4 kN·m/m | **145,4** | 0,0% | 2% | ✅ PASA |
| Losa cubierta 70 | M_tándem /m (car.) | 194,1 kN·m/m | **180** (mi placa 2D FEM convergida) | −7,3% | 5%(*) | ⚠️ ver nota |
| Losa cubierta 70 | **M_ULS total** | 923,9 kN·m/m | **902,6** (con tándem 2D) | −2,3% | 5% | ✅ PASA |
| Losa cubierta 70 | Punzonamiento v_Ed | 0,036 MPa | **0,036** (EC2 §6.4, perím. 2d) | 0,0% | 5% | ✅ PASA |
| Losa de fondo (raft) | M_máx (Winkler) | 132,8 kN·m/m | **132,7** (mi BoEF, misma carga) | 0,1% | 5% | ✅ PASA |
| Losa de fondo (raft) | λ (Hetényi) | — | **0,429 1/m** (1/λ=2,33 m) | — | — | (traza) |
| Flotación | FS (freático rasante) | 0,65 | **0,650** (U=γ_w·A·h vs 0,9G) | 0,0% | 1% | ✅ PASA |
| Flotación | U (rasante) | 16.804 kN | **16.804 kN** | 0,0% | 1% | ✅ PASA |

(*) **Nota sobre el tándem (M_tándem/m):** la componente aislada del tándem difiere −7,3% (productor 194,1 conservador; mi placa 2D 180). Por sí sola excedería la tolerancia del 5%, **pero el productor es conservador, no inseguro** (puerta roja sólo aplica si el productor queda *por debajo* del oráculo). Lo decisivo es el **M_ULS total ensamblado = 902,6 (QA) vs 923,9 (productor), desviación −2,3% < 5% → PASA**. El productor sobreestima ligeramente el tándem y por tanto el armado; está del lado seguro.

### Traza del oráculo (qué método usé en cada caso)
- **Muros (perimetral e interior):** (a) solución analítica cerrada de la ménsula apuntalada (*propped cantilever* fixed-base/pinned-top): carga triangular → M_empotramiento = p₀H²/15, R_apoyo = p₀H/10; carga trapezoidal de tierras por superposición uniforme (wL²/8) + triangular (w_tL²/15). (b) **Mi propia viga FE Euler-Bernoulli** (matriz Hermite, vector de carga consistente por Simpson, 300 elementos). Ambas vías coinciden con el productor a <0,2%.
- **Losa de cubierta:** (a) flexión 1D simplemente apoyada (cota conservadora en vano). (b) **Mi propia placa 2D FEM** (elemento rectangular ACM/no conforme de 12 GdL, integración Gauss 4×4, base monómica completa, malla convergida 38×44; tándem como 4 parches de 150 kN; bordes largos simplemente apoyados, cortos libres → unidireccional). Recuperación de M_y (dirección de la luz). Ancho eficaz implícito del tándem = 300·(L/2−0,6)/M_y ≈ 8,45 m. (c) Punzonamiento EC2 §6.4 con perímetro de control a 2d sobre patch 0,40×0,40.
- **Raft:** (a) longitud característica de **Hetényi** λ = (k/4EI)^¼ = 0,429 → 1/λ=2,33 m, λ·L=5,94 (viga relativamente flexible). (b) **Mi propia BoEF FE** (Winkler con matriz consistente). Verificación cruzada con la definición de carga del productor (Pwall=382 kN/m incluyendo p.p. muro + reacción de cubierta perm+UDL+tándem repartido): reproduce M=132,7 a 0,1%.
- **Flotación:** balance estático cerrado U = γ_w·A·h_sub frente a 0,9·G, con G recalculado desde geometría (G=12.133 kN).

---

## 3. Capa normativa

| Comprobación | Límite / criterio | Valor QA | Veredicto |
|---|---|---|---|
| Materiales (f_cd, f_ctm, E_cm, f_yd, α_e) | EC2 / AN España | f_cd=20,0 · f_ctm=2,90 · E_cm=32.837 · f_yd=434,8 · α_e=6,09 | ✅ correctos |
| Muro: aprovechamiento flexión | ≤ 1 | 0,46 | ✅ |
| Muro: **cortante V_Ed/V_Rd,c** | ≤ 1 | **0,82** (V_Ed=160,9 con γ=1,35) | ✅ (ver D-1) |
| Muro: A_s,mín fisuración EN1992-3 | — | 4,71 cm²/m (coincide) | ✅ |
| Muro: **w_k cara agua** | ≤ 0,20 mm | **0,113 mm** (σ_s=83,6) | ✅ estanco |
| Muro interior: flexión / w_k | ≤1 / ≤0,20 | 0,30 / 0,113 mm | ✅ |
| Losa cubierta: flexión | ≤ 1 | 0,72 (M_ULS 2D / M_Rd φ25/100) | ✅ |
| Losa cubierta: A_s requerida | — | **≈37–38 cm²/m** (φ25/100=49,1 provee) | ✅ holgada |
| Losa cubierta: **punzonamiento** | ≤ 1 | 0,06 | ✅ amplísimo |
| Raft: flexión | ≤ 1 | 0,54 | ✅ |
| Raft: portante UG3 | q/q_adm | 0,08 | ✅ |
| Raft: **w_k** | ≤ 0,20 mm | **0,222 mm** | ❌ **NO CUMPLE** (ver O-1) |
| Flotación: FS (freático documentado) | — | sin subpresión → no crítica | ✅ condicional (ver O-2) |
| Flotación: FS (freático rasante) | ≥ 1,0 (UPL EC7) | **0,65** | ❌ flotaría si sube freático |
| Recubrimiento c_nom | 45 mm clase XC4/XD | adoptado | ✅ adecuado depósito |

**Observación normativa importante (D-2):** el productor reporta "A_s requerida (inferior) = φ25/100 ≈ 49,1 cm²/m" para la losa de cubierta. Esa cifra es el área **provista**, no la requerida. La A_s **requerida a flexión** es ≈ 37–38 cm²/m por mi oráculo; φ25/100 la cubre con holgura. No afecta a la seguridad (queda del lado seguro), pero la etiqueta conviene aclararla.

---

## 4. Discrepancias frente al productor (todas explicadas)

- **D-1 · Cortante del muro (productor conservador).** El productor calcula V_Ed = 178,8 kN aplicando **γ=1,5 a la reacción de tierras** (`V_b = max(reA,reB)·1,5`). Como el empuje de tierras es acción **permanente desfavorable**, el coeficiente correcto en STR/GEO es **γ=1,35** → V_Ed = 160,9 kN. El aprovechamiento real es **0,82**, no 0,91. El productor está del lado de la seguridad; el "⚠️ ajustado al 91%" es pesimista. **No es puerta roja; es conservador.** Recomiendo corregir el coeficiente en una futura revisión del motor para no penalizar innecesariamente el canto/armado.
- **D-2 · Etiqueta de A_s de la losa de cubierta.** Ver §3: "49,1 cm²/m necesaria" es en realidad la provista; la necesaria es ~37–38. Sin impacto en seguridad.
- **D-3 · Tándem repartido (productor conservador).** Ancho eficaz 8,79 m (productor) vs 8,45 m (mi placa 2D). Neto: M_ULS total del productor (923,9) es 2,3% superior al mío (902,6). Conservador.

**Ninguna discrepancia deja al productor por debajo del oráculo.** No hay puerta roja por esfuerzos.

---

## 5. Observaciones / gates que dependen de JM

| Ref | Observación | Tipo | Acción |
|---|---|---|---|
| **O-1** | Raft w_k=0,222 > 0,20 mm (confirmado por QA). | No conforme (estanqueidad) | **Subir armado raft a φ20/175 (w_k=0,179) o φ25/200 (w_k=0,125).** Re-verificar tras el cambio. |
| **O-2** | Flotación segura sólo con freático +144,6; con freático a rasante FS=0,65. | Gate de proyecto (geotecnia) | JM: confirmar freático máximo en el punto real de implantación (+146,40, 5,6 m bajo HQ). Si puede ascender → prever talón/lastre/anclajes o válvula antisubpresión. |
| **O-3** | Losa 11,37 m con LM1 exige ≈1% de armadura (φ25/100). Viabilidad confirmada por placa 2D. | Decisión de esquema | JM: valorar apoyo intermedio/viga, mayor canto, o idoneidad de LM1 frente a vehículo de explanada. |
| **O-4** | Sismo (EC8-4 hidrodinámico Housner + Mononobe-Okabe) **no cuantificado**. a_c=0,046g bajo. | Gate diferido | JM: confirmar que se acepta como no crítico o exigir combinación accidental. |
| **O-5** | Coacción térmica/retracción (calor de hidratación) tratada sólo cualitativamente. | Gate diferido (estanqueidad) | JM: exigir cuantificación EN 1992-3 §7 + plan de hormigonado/juntas. |
| **O-6** | `versions.lock = 0.0.0` (versión NO anclada); cálculo con motor propio, no con el núcleo versionado. | Trazabilidad/gobierno | JM: anclar versión antes de congelar golden (GOBIERNO §B.5). |
| **O-7** | D-1 (γ=1,5 en cortante de tierras) — corregir a 1,35 en el motor. | Mejora (conservador) | No bloqueante. |

---

## 6. Revisión de candidatos a golden (capa de regresión)

| Caso | Oráculo / tolerancia | Reproducible | Recomendación a JM |
|---|---|---|---|
| **G-DEP-01** Muro ménsula apuntalada | Analítico cerrado p₀H²/15; tol 2%. **Verificado por QA: 0,1%.** | Sí | ✅ **CONGELAR.** Oráculo y tolerancia correctos. Oráculo de doble vía (cerrado + mi FE). |
| **G-DEP-02** Losa punzonamiento + reparto tándem | EC2 §6.4 + placa 2D; tol 5%. **QA: punz 0,0%; tándem verificado por mi placa 2D (M_ULS −2,3%).** | Sí | ✅ **CONGELAR**, fijando el oráculo del reparto a "placa 2D, M_ULS total" (no a la componente aislada de tándem, que es más sensible). Era el caso marcado prioritario y queda resuelto. |
| **G-DEP-03** Flotación UPL | Balance cerrado; tol 1%. **QA: 0,0%.** | Sí | ✅ **CONGELAR el método.** El valor numérico (FS) queda condicionado al freático de proyecto (gate O-2): congelar la *fórmula y el caso conservador a rasante*, no un FS "verde" hasta cerrar O-2. |
| **G-DEP-04** Raft Winkler | Hetényi / BoEF; tol 5%. **QA: 0,1% con misma definición de carga.** | Sí, con matiz | ⚠️ **CONGELAR con cautela.** Reproducible, pero el M es muy sensible (a) al módulo de balasto k_s (fijar con el geotécnico) y (b) a **cómo se modela la carga de muro** (el productor inyecta la reacción de cubierta incl. tándem como línea concentrada; cambiar esa hipótesis cambia M ±50%). Documentar la definición exacta de carga en el oráculo del golden. |

---

## 7. Conclusión de la QA

- **Veredicto técnico global: CON OBSERVACIONES.** El cálculo es correcto en esfuerzos (todas las desviaciones < tolerancia y, donde difieren, el productor es conservador). No hay errores que comprometan la seguridad.
- **Bloqueantes antes de firma:** O-1 (ajustar armado del raft por estanqueidad) y cierre del gate O-2 (freático/flotación).
- **G-DEP-01, 02, 03 (método) y 04 (con cautela)** son aptos para congelar como golden tras las decisiones de JM.

**La QA no certifica ni firma.** Este informe se eleva a JM, que decide sobre los gates O-1…O-7 y, en su caso, firma (dos llaves, GOBIERNO §B.5).

*— Agente de QA independiente, Estructurando 2.0 · 2026-06-24*
