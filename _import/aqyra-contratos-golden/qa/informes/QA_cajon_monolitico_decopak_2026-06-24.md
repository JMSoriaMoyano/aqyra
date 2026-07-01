# Informe de QA por cálculo — Depósito enterrado Decopak (Rubí) · **Rev.01 (cajón monolítico)**

**Elemento verificado:** depósito enterrado de HA con **unión rígida muro-losa** (cajón cerrado); cubierta como **placa 2D bidireccional empotrada**.
**Productor (rol build):** `calculo/03_revision_union_rigida.md` · `resultados_v2.json` · `calc_v2_porticocerrado.py` · `calc_v2_placa2d.py` · `calc_v2_diseno.py`
**Verificador (rol QA, dos llaves):** agente de QA independiente · oráculo propio (placa 2D ACM con malla convergida + **resortes rotacionales de borde**, coeficientes analíticos de Timoshenko, pórtico cerrado 1D propio, EC2 propio).
**Marco:** `GOBIERNO_QA_Y_VERSIONES.md` §B.2 (tres capas) y §B.5 (procedencia del oráculo) — *quien produce no aprueba*.
**Fecha:** 2026-06-24 · Re-verificación de la hipótesis de vinculación cambiada por JM.

> **ESTE INFORME NO CERTIFICA NI FIRMA.** La certificación (golden verde + QA limpio + **firma humana de JM**, dos llaves) es competencia exclusiva de JM.

---

## 1. Resumen ejecutivo · VEREDICTO GLOBAL: **ROJO (puerta roja por inconsistencia del modelo)**

El cambio a cajón monolítico es **físicamente correcto y favorable** en concepto, y la mayoría de los armados (apoyo superior, muro base, muro paramento, solera, punzonamiento) son **holgados y se verifican sin problema** por mi oráculo. **Pero el cálculo de la cubierta contiene un error de coherencia de modelo que deja el vano por debajo de la solicitación real, y eso es puerta roja.**

El productor adopta **dos valores de momento que provienen de hipótesis de rigidez incompatibles entre sí**:

- **M_vano = 308 kN·m/m** → tomado de la placa 2D con **bordes perfectamente empotrados** (rigidez de muro = ∞).
- **M_esquina/apoyo = 352 kN·m/m** → tomado del **pórtico 1D con muro flexible** (rigidez real).

Físicamente esto es un **balancín**: a medida que el muro permite girar el borde (y el momento de esquina baja de 510 hacia 352 o menos), **el momento de vano NO se queda en 308: crece**. Mi placa 2D con resortes rotacionales de borde calibrados a la rigidez real del muro (barrida 2EI/H–6EI/H) da **M_vano = 385–459 kN·m/m** en todo el rango, **nunca 308**, mientras la esquina cae a **167–298 kN·m/m**. La suma vano+esquina es aproximadamente invariante (~640–660). El productor se ha quedado con el vano del caso rígido (308) y la esquina del caso flexible (352): **no pueden coexistir**.

Consecuencia sobre el armado de la cubierta (φ20/175 inferior, M_Rd≈452): con el M_vano real (≈412–432) el **aprovechamiento real es 0,91–0,96**, no 0,68. Aún ≤1, pero (a) **anula el margen** que el productor declara, (b) **dispara la fisuración** (w_k de 0,245 a ~0,31–0,35 mm, ya fuera de 0,20 incluso en hipótesis no estanca laxa), y (c) está calculado con un valor de proyecto que **no es seguro de origen**. **La esquina/muro, en cambio, está sobrada** (352 es conservador; el muro φ25/200, M_Rd≈427, resiste incluso los 510 del empotramiento perfecto con util 1,19 — al límite — y holgadamente los 214–352 reales).

**No es un fallo de la física del cajón; es un error de toma de resultados de dos modelos distintos.** Hasta que la cubierta se rearme con un par (vano, esquina) **consistente** procedente de un único modelo, la Rev.01 es **no conforme**.

---

## 2. Capa numérica — Tabla por elemento (oráculo independiente)

| Elemento · magnitud | Productor | Oráculo QA | Desv. | Tol. | Veredicto |
|---|---|---|---|---|---|
| Validación placa cuadr. empotrada (centro) | — | FEM 5,29 vs Timoshenko 5,775 (−8%); borde 12,82 vs 12,825 (0,0%) | — | — | (mi FEM converge en borde; centro conservador) |
| Cubierta · **M_esquina/apoyo** (pórtico 1D) | 351,6 | **351,4** (mi pórtico cerrado propio) | 0,1% | 5% | ✅ reproduce el 1D |
| Cubierta · M_apoyo (placa **empotrada perfecta**) | 510 (−509,8) | **510,8** (mi placa 2D + tándem) | 0,2% | 5% | ✅ reproduce la placa |
| Cubierta · M_apoyo unif. solo (placa empotr.) | — | **365** (mi FEM) ≈ **365** (Timoshenko β=0,079) | <1% | 2% | ✅ analítico cerrado |
| **Cubierta · M_esquina REAL** (placa + muro flexible 3–4EI/H) | 352 (adoptado) | **214–249** | — | — | productor **conservador** en esquina |
| **Cubierta · M_VANO REAL** (placa + muro flexible 2–6EI/H) | **308 (adoptado)** | **385–459** (centro 412–432 con 3–4EI/H) | **+25…+49%** | 5% | ❌ **PUERTA ROJA** (productor por debajo) |
| Cubierta · M_vano dir-larga | 182 | (coherente con reparto bidireccional) | — | — | (recae con el vano corto) |
| Muro · base (empotramiento solera) | 92 | **93,1** (mi pórtico cerrado) | 1,2% | 5% | ✅ PASA |
| Muro · cabeza/esquina | 352 | **214–352** (rango, ver arriba) | — | — | ✅ (capacidad sobra) |
| Solera · vano/esquina | 133 | **137,9** (mi pórtico cerrado con lecho elástico) | 3,7% | 5% | ✅ PASA |
| Cubierta · punzonamiento v_Ed | 0,036 MPa (η 0,06) | **0,036 MPa** (EC2 §6.4, rueda 225 kN ULS, u₁ a 2d); η=0,10 | — | 10% | ✅ PASA (mi η algo mayor por γ_Q=1,5 sobre 150 kN) |

**M_Rd verificados (EC2 propio, brazo riguroso x/z):** cubierta φ20/175 → 487 (productor 452, conservador); apoyo φ25/200 → 658 (618); muro φ25/200 → 446 (427); solera φ20/175 → 410 (383). Todos coinciden con el productor dentro de ~7% (el productor usa z=0,9d, conservador). **Las capacidades no son el problema; el problema es la solicitación de vano.**

### Traza del oráculo
- **Placa 2D:** elemento ACM de Kirchhoff (12 GdL) **reimplementado de forma independiente** con **vector de carga consistente** (no lumped como el productor) y **resolución sparse**, malla convergida (32×48 y 40×60, variación <1%). Validado contra Timoshenko (placa cuadrada empotrada: borde 0,0%, centro −8% conservador). **Aportación clave:** introduje **resortes rotacionales en los bordes** = rigidez real del muro (k = α·EI_muro/H, α∈[2,6]), que el modelo del productor (placa empotrada perfecta) NO tiene. Esto es lo que destapa el balancín vano↔esquina.
- **Pórtico cerrado 1D:** mi propia matriz de barra 2D (axil+flexión Hermite), franja 1 m, solera sobre lecho elástico k_s=80.000, tándem como línea equivalente. Reproduce la esquina del productor (351,4 vs 351,6).
- **Analítico:** coeficientes de placa rectangular empotrada de Timoshenko (b/a=1,66 → β_borde=0,079 → 365 uniforme), equilibrio de nudo por rigideces.
- **EC2:** M_Rd con bloque rectangular x=A·f_yd/(0,8·b·f_cd), z=d−0,4x; w_k EN 1992-3; punzonamiento EC2 §6.4 perímetro a 2d.

---

## 3. Capa normativa (utilizaciones y fisuración)

| Comprobación | Límite | Valor QA | Veredicto |
|---|---|---|---|
| **Cubierta vano · flexión con M real** | ≤1 | **0,85–0,96** (M_Ed real 412–432 / M_Rd 452–487), NO 0,68 | ⚠️ ≤1 pero **sin margen y mal fundado** |
| Cubierta apoyo superior · flexión | ≤1 | 0,54–0,57 (sobra; M real ≤352) | ✅ |
| Muro cabeza/esquina · flexión | ≤1 | 0,50–0,82 (M real 214–352) | ✅ (a 510 daría 1,19; pero 510 es el límite no físico) |
| Muro base · flexión | ≤1 | 0,34 | ✅ |
| Solera · flexión | ≤1 | 0,35 | ✅ |
| Punzonamiento rueda | ≤1 | 0,10 | ✅ |
| **w_k cubierta vano** (si se exige Clase 1) | ≤0,20 mm | productor 0,245 **ya > 0,20**; con M_vano real → **~0,31–0,35 mm** | ❌ si la cubierta es estanca |
| w_k muro paramento (agua/tierras) | ≤0,20 mm | 0,128–0,144 | ✅ estanco |
| w_k solera | ≤0,20 mm | 0,179 (φ20/175, resuelve el O-1 de la QA previa) | ✅ estanco |

**Sobre la estanqueidad de la cubierta:** el productor la marca condicional (resguardo de lámina libre). De acuerdo en que la cara superior de la cubierta no está en contacto permanente con el líquido; **pero ya con M=308 su w_k=0,245 > 0,20**, y con el M de vano real sube a ~0,31–0,35. Si JM exige Clase 1 también en cubierta, φ20/175 **no vale** (haría falta φ20/150 o más). Aunque no se exija estanqueidad en cubierta, una fisura de ~0,3 mm en cara inferior bajo combinación característica es un indicador más de que el armado de vano está infradimensionado para el momento real.

---

## 4. Foco: el momento de esquina cubierta-muro (núcleo del cambio)

Barrido de mi placa 2D con resorte de borde = rigidez del muro (franja, EI_muro=342.052):

| Hipótesis de borde | M_vano (kN·m/m) | M_esquina (kN·m/m) |
|---|---|---|
| Empotramiento **perfecto** (placa2d del productor) | ~280–308 | **510** |
| Muro 6EI/H (rígido) | 385 | 298 |
| Muro **4EI/H** (realista, base empotrada) | **412** | **249** |
| Muro **3EI/H** (realista, base semi-rígida) | **432** | **214** |
| Muro 2EI/H (flexible) | 459 | 167 |
| Pórtico 1D del productor | (artefacto local) | 352 |
| **Productor (proyecto)** | **308** | **352** |

**Lectura:** el valor de proyecto de la esquina (352) es **conservador y seguro** (la esquina real es 214–298; el muro φ25/200 con M_Rd=427 lo cubre con util 0,50–0,70). **El error está en el otro extremo del balancín:** el vano de 308 corresponde a una esquina de 510, no a 352. Un par consistente sería, p. ej., **vano ≈ 412 / esquina ≈ 249** (muro 4EI/H) — y entonces el armado de vano φ20/175 queda al 0,91 y con w_k fuera de 0,20.

El productor afirma que la esquina está "acotada 352–510". **Correcto, y elige bien el extremo seguro (352) para la esquina/muro.** Lo que no hizo fue propagar esa misma elección al vano: si la esquina relaja a 352, el vano sube por encima de 308. **La cota inferior segura del vano es ~385 (caso más rígido), no 308.**

---

## 5. Discrepancias frente al productor

- **D-1 (PUERTA ROJA) · Par vano/esquina incoherente.** M_vano=308 (placa empotrada) y M_esquina=352 (pórtico flexible) proceden de rigideces de muro distintas e incompatibles. El vano real es 385–459. **El armado inferior de la cubierta (φ20/175) está dimensionado para 308 y queda por debajo de la solicitación real.** Re-derivado por mi placa 2D con resortes de borde.
- **D-2 · Esquina conservadora (no bloqueante).** 352 sobreestima la esquina real (214–298). Favorable; el muro sobra. No es error de seguridad.
- **D-3 · w_k de cubierta ya > 0,20 con M=308 (0,245).** Con el M real sube a ~0,31–0,35. Bloqueante solo si JM exige Clase 1 en cubierta; indicador de infradimensionado en todo caso.
- **D-4 · Validación del productor con error del 8% en centro.** Su propia placa2d declara "error 8% en centro" frente a Timoshenko y **lo subestima** (FEM 5,31 < Timoshenko 5,775). Su malla ACM lumped infravalora el momento de centro; el vano real es aún algo mayor que su FEM. Refuerza D-1.
- **D-5 · Punzonamiento η 0,06 vs 0,10.** Diferencia por factor de carga (yo aplico γ_Q=1,5 sobre la rueda de 150 kN → 225 kN ULS). Ambos holgadísimos; no bloqueante.

**A diferencia de la QA previa (donde todas las discrepancias dejaban al productor del lado seguro), aquí D-1 deja al productor POR DEBAJO del oráculo en el vano de cubierta → puerta roja.**

---

## 6. Gates y observaciones para JM

| Ref | Observación | Tipo | Acción |
|---|---|---|---|
| **R-1** | Cubierta: par (vano, esquina) incoherente; vano real 385–459, no 308. φ20/175 infra-dimensionado (util real 0,91–0,96). | **Bloqueante (rojo)** | Rehacer la cubierta con **un único modelo** (placa 2D con rigidez de muro real, o lámina completa del cajón) y rearmar el vano con el par consistente (p.ej. vano≈412 → revisar a φ20/150 o φ25/200 inferior). Re-verificar. |
| **R-2** | w_k cubierta vano = 0,245 (M=308) → ~0,31–0,35 (M real). | Bloqueante si Clase 1 en cubierta; observación en todo caso | JM: decidir si la cubierta es paramento estanco. Si sí, denso de armadura. Si no, el w_k confirma de todos modos R-1. |
| O-1 (previa) | Solera w_k: con φ20/175 → 0,179 ≤ 0,20. | **Resuelto** | La Rev.01 sube la solera a φ20/175; cierra el O-1 de la QA anterior. ✅ |
| O-2 (previa) | Flotación UPL con freático a rasante FS=0,65. | Gate vigente | **Sigue vigente** — el cambio de vinculación no afecta a la flotación. JM: confirmar freático. |
| O-4/O-5 (previas) | Sismo hidrodinámico (EC8-4) y coacción térmica/retracción no cuantificados. | Gates diferidos vigentes | Sin cambio. |
| O-6 (previa) | `versions.lock=0.0.0`; motor propio no versionado. | Trazabilidad | Sin cambio. |

---

## 7. Regresión / golden

- **G-DEP-05 (nuevo) · "Cubierta como placa 2D empotrada — par vano/esquina consistente".** Oráculo: **placa 2D con resortes rotacionales de borde calibrados a la rigidez del muro** + cota analítica de Timoshenko para el caso uniforme empotrado (β_borde=0,079 → 365). Tolerancia 5% (placa+tándem), 2% (uniforme analítico). **NO congelar en verde hasta resolver R-1:** el caso golden debe fijar que vano y esquina salen del MISMO modelo, no de dos. Este golden, bien planteado, captura exactamente el fallo detectado.
- **G-DEP-01/03/04 (previos):** siguen vigentes (muro ménsula apuntalada, flotación, raft) — la vinculación rígida no los invalida.
- **G-DEP-02 (punzonamiento + reparto tándem):** vigente; mi η=0,10 (γ_Q=1,5) vs 0,06; fijar el factor de carga en el oráculo del golden.

---

## 8. Conclusión

- **Veredicto técnico global: ROJO.** No por la física del cajón (que es correcta y favorable), sino por una **incoherencia de modelo en la cubierta** que deja el armado de vano por debajo de la solicitación real (vano real 385–459 vs 308 de proyecto; util real 0,91–0,96; w_k ~0,3 mm).
- **El resto del cajón está bien:** apoyo superior, muro (esquina sobrada, el 352 es conservador), base de muro, solera (cierra el O-1 previo) y punzonamiento se verifican holgados por mi oráculo independiente.
- **Bloqueante antes de firma (R-1):** rearmar la cubierta con un par (vano, esquina) consistente de un único modelo y re-verificar. Resolver R-2 (estanqueidad de cubierta) según decisión de JM. Gates previos O-2/O-4/O-5/O-6 siguen vigentes.

**La QA no certifica ni firma.** Se eleva a JM, que decide sobre R-1, R-2 y los gates y, en su caso, firma (dos llaves, GOBIERNO §B.5).

*— Agente de QA independiente, Estructurando 2.0 · 2026-06-24*
