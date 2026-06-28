# Informe de QA por cálculo — Depósito enterrado Decopak (Rubí) · **Rev.02 (cajón monolítico, modelo único)**

**Elemento verificado:** depósito enterrado de HA con **unión rígida muro-losa** (cajón cerrado); cubierta como **placa 2D bidireccional continua** con los muros (modelo único del productor).
**Productor (rol build):** `calculo/03_revision_union_rigida.md` · `calc_v3_placa_consistente.py` (placa 2D ACM + muelle rotacional de borde = rigidez muro) · `calc_v2_porticocerrado.py` · `Memoria_..._Rev02.docx`.
**Verificador (rol QA, dos llaves):** agente de QA independiente. **Oráculo de máximo nivel: lámina 2D COMPLETA del cajón (folded-plate FEM 3D)** — cubierta + 4 muros + solera como placas planas acopladas monolíticamente en sus aristas, solera sobre lecho elástico. Escrito de cero por QA, **sin la aproximación de muelle del productor**.
**Marco:** `GOBIERNO_QA_Y_VERSIONES.md` §B.2 (tres capas), §B.3 (oráculo de mayor nivel) y §B.5 (procedencia del oráculo) — *quien produce no aprueba*.
**Fecha:** 2026-06-24 · Re-verificación de la Rev.02 emitida para cerrar la puerta roja de la Rev.01.

> **ESTE INFORME NO CERTIFICA NI FIRMA.** La certificación (golden verde + QA limpio + **firma humana de JM**, dos llaves) es competencia exclusiva de JM. La QA solo juzga; no edita el código del productor, no afloja tolerancias ni valores esperados.

---

## 1. Resumen ejecutivo · VEREDICTO GLOBAL: **LIMPIO CON OBSERVACIONES (verde con gates)**

La Rev.02 **corrige el defecto que motivó la puerta roja de la Rev.01.** El productor ya no mezcla el vano de la placa empotrada perfecta (308) con la esquina del pórtico flexible (352): ahora **vano y esquina salen del MISMO modelo** (placa con muelle de borde = rigidez del muro), y el par declarado **vano = 440 / esquina = 249** es **internamente coherente** (suma ≈ 689).

He construido el **oráculo más fuerte posible: una lámina 2D completa del cajón monolítico** (5 paneles acoplados en 3D, solera sobre Winkler), que **no necesita ninguna aproximación de muelle** porque el reparto de la esquina lo fija la rigidez real de la caja tridimensional. Resultado:

- **Cubierta VANO ≈ 410–461 kN·m/m** (componente distribuida converge a 280; tándem añade +109…+181 según malla). Mejor estimación robusta: **~420–440.** Productor 440 → **dentro de tolerancia.**
- **Cubierta ESQUINA ≈ 218–250 kN·m/m.** Productor 249 → **dentro de tolerancia.**
- **El equilibrio de la esquina cierra EXACTAMENTE en mi lámina sin muelle:** el momento de cabeza del muro = el momento de esquina de la cubierta en **todas** las mallas (182/182, 232/232, 250/250). Esto confirma físicamente lo que el productor aproximó con un muelle.
- **Suma vano+esquina ≈ 650–711, casi invariante** — exactamente el "balancín" de invariante ~650 que predije en la QA de la Rev.01. El par 440/249 cae sobre esa recta.

**Capa normativa:** todas las comprobaciones verifican con mi EC2 independiente, **utilizaciones ≤ 0,67** y **w_k del vano (φ25/150) = 0,169 mm ≤ 0,20** (reproduzco el 0,169 del productor) — el φ25/150 **resuelve la fisuración que hundió la Rev.01**. Punzonamiento holgado (η 0,08). As,mín cubierta.

**Por qué "con observaciones" y no "limpio a secas":** (a) persiste **sensibilidad de malla del pico bajo el tándem** (artefacto numérico común del elemento de placa ante carga de parche, no error del productor) que sitúa el vano en 410–461; el valor de proyecto 440 es razonable pero **JM debe ser consciente de que el vano puede llegar a ~460** (util sube a 0,53, sigue holgado); (b) gates previos **O-2 (flotación), O-4/O-5 (sismo hidrodinámico, térmica), O-6 (versionado)** siguen **vigentes**; (c) la **estanqueidad de la cubierta (R-2)** sigue siendo decisión de JM, ahora bien cubierta por el φ25/150.

---

## 2. Descripción del oráculo QA · lámina 2D completa del cajón (validada)

**Modelo (escrito de cero, independiente):** FEM de lámina plegada en 3D. Cada panel se malla con un **elemento quad plano de 24 GdL** = **flexión (placa Kirchhoff ACM 12 GdL)** + **membrana (Q4 bilineal, 8 GdL)** + rigidez de drilling ficticia para estabilidad (1e-3·E·t·A). Ensamblaje en ejes globales con la matriz de rotación de cada panel; **nodos de arista comunes FUSIONADOS → unión monolítica real** (no un muelle). Solera sobre **resortes verticales de Winkler** (k_s = 80.000 kN/m³, área tributaria por nodo) + resortes horizontales blandos para coartar el sólido rígido. Cargas: cubierta (perm. mayorada + UDL LM1 + tándem 600 kN en huella 3,1×2,3 como parche), solera (p.p. + columna de agua), muros (empuje neto ELU = 1,35·tierras_reposo − 1,5·agua). 5 paneles, 1.018–2.274 nodos según malla.

**Validación del elemento (capa de confianza):**
- **Placa rectangular simplemente apoyada bajo carga uniforme vs. serie cerrada de Navier:** mi FEM **M_x −0,3 %, M_y −0,3 %**. El elemento de flexión es correcto (mejora respecto al "−8 % en centro" que el propio productor reconocía en su validación, por usar yo recuperación consistente en esquinas, no carga lumped en el centro).
- **Equilibrio de esquina (auto-consistencia de la lámina):** momento de cabeza de muro = momento de esquina de cubierta en cada malla (coincidencia exacta) → la caja cierra el nudo sin muelle.
- **Convergencia (componente distribuida, sin tándem):** vano 280 / esquina 182 **idéntico** en mallas 14×18×8, 16×22×10, 20×28×12 (variación <0,5 %). La única dispersión proviene del **pico del tándem** (carga de parche), inevitable con elemento de placa; por eso reporto el vano como rango 410–461 y no un valor único.

**Diferencias de formulación con el productor:** el productor usa una **placa 2D aislada con muelle rotacional de borde k=4·EI_muro/H** (modelo reducido correcto). Yo uso la **caja 3D completa acoplada**, que **deriva la rigidez de borde por sí sola** (no la copio). Que ambos coincidan dentro de tolerancia valida que su calibración del muelle (k≈4EI/H) representa bien la rigidez real de la caja.

---

## 3. Capa numérica — Tabla por elemento (oráculo lámina completa + EC2 propio)

| Magnitud | Productor (Rev.02) | Oráculo QA (lámina completa) | Desv. | Tol. | Veredicto |
|---|---|---|---|---|---|
| Validación placa SS uniforme (Mx, My) | — | FEM vs Navier: −0,3 % / −0,3 % | <1% | 2% | ✅ elemento validado |
| Cubierta · componente distribuida (vano) | — | **280** (convergido <0,5%, 3 mallas) | — | — | ✅ estable |
| **Cubierta · M_VANO m_x** (total ELU) | **440** | **410–461** (mejor est. ~420–440) | dentro | 10% | ✅ |
| Cubierta · M_vano m_y (dir. larga) | 261 | **231–285** | dentro | 10% | ✅ |
| **Cubierta · M_ESQUINA/apoyo** | **249** | **218–250** | dentro | 10% | ✅ |
| **Equilibrio esquina = cabeza muro** | =249 (continuidad) | **coincide exacto** (250/250, 232/232, 182/182) | 0% | — | ✅ cierre del nudo |
| Suma vano+esquina (invariante "balancín") | 689 | **650–711** | dentro | — | ✅ confirma física previa |
| Muro · base | 92 | (orden 57–92 en lámina, gob. caso vaso vacío) | — | 10% | ✅ holgado |
| Solera · vano/esquina | 133 | (lámina sobre Winkler, flecta poco; −55 a 133) | — | 10% | ✅ holgado |
| Cubierta · punzonamiento v_Ed | 0,036 MPa (η0,06) | **0,036 MPa**, η **0,08** (Q_ELU 225 kN, u₁ a 2d) | — | 10% | ✅ (mi η>productor por γ_Q=1,5) |

> El par (440, 249) del productor **cae dentro de la banda de mi lámina completa** en las tres mallas y sobre la recta de suma invariante. La Rev.01 ponía el vano en 308 (fuera de banda, puerta roja); la Rev.02 lo sube a 440, **dentro de banda.** Hallazgo de la Rev.01 **resuelto.**

**M_Rd verificados (EC2 propio, bloque rectangular x=A·f_yd/0,8·b·f_cd, z=d−0,4x):** todos ≥ los del productor (uso brazo riguroso; el productor usa z=0,9d conservador): cubierta vano φ25/150 → **864** (prod. 823); muro φ25/200 → **446** (prod. 427); apoyo φ20/150 → **571**; solera φ20/175 → **410** (prod. 383). Las capacidades no son el problema.

---

## 4. Capa normativa (utilizaciones y fisuración) — oráculo QA

| Comprobación | Límite | Valor QA | Veredicto |
|---|---|---|---|
| **Cubierta vano · flexión** φ25/150 | ≤1 | **0,51** (M 440) / **0,53** (M 461 pésimo) | ✅ holgado |
| **Cubierta vano · w_k** (EN 1992-3, M_serv 307) | ≤0,20 mm | **0,169 mm** (σs 157 MPa) — reproduce el 0,169 del productor | ✅ **resuelve R-2 de Rev.01** |
| Cubierta vano dir-larga φ20/200 · flexión | ≤1 | 0,60 (261) / 0,66 (285) | ✅ |
| Cubierta apoyo sup φ20/150 · flexión | ≤1 | 0,44–0,52 | ✅ |
| **Muro cabeza/esquina φ25/200 · flexión** | ≤1 | **0,56** (249/250) – **0,67** (298) | ✅ cubre la esquina |
| Muro cabeza · w_k cara ext | ≤0,20 mm | ~0,198 mm | ✅ al límite |
| Muro base φ20/200 · flexión / w_k | ≤1 / ≤0,20 | 0,31 / 0,167 | ✅ |
| Solera φ20/175 · flexión / w_k | ≤1 / ≤0,20 | 0,32 / 0,133 | ✅ |
| Punzonamiento rueda | ≤1 | 0,08 | ✅ |
| As,mín (cubierta/muro/solera) | EC2 9.x | 9,7 / 6,7 / 8,2 cm²/m exigida; armados muy por encima | ✅ |

**Aprovechamiento máximo por mi oráculo: 0,67** (cabeza de muro a 298). Coherente con el 0,70 del productor (que toma el extremo rígido 298 del rango). **Todos ≤ 1.**

---

## 5. Punzonamiento (EC2 §6.4)

Rueda 150 kN → **Q_ELU = 225 kN** (γ_Q=1,5). Perímetro de control u₁ a 2d (d=0,643): u₁=9,68 m. **v_Ed = 0,036 MPa**, **v_Rd,c = 0,464 MPa** → **η = 0,08.** El productor declara 0,06 (sin γ_Q sobre la rueda). Ambos **holgadísimos**; la diferencia es solo el factor de carga. No bloqueante.

---

## 6. Discrepancias y observaciones frente al productor

- **D-0 (RESUELTO) · La incoherencia de modelo de la Rev.01 está corregida.** Vano y esquina ya proceden de un único modelo. Mi lámina completa **independiente** confirma el par (440/249) dentro de tolerancia del 10 % y reproduce el cierre exacto del nudo esquina↔cabeza de muro. **La puerta roja de la Rev.01 queda cerrada.**
- **O-A (observación, no bloqueante) · Sensibilidad del pico del tándem.** Mi vano oscila 410–461 según dónde caiga la huella del tándem respecto a la malla (artefacto del elemento de placa ante carga de parche, también presente en el modelo del productor). El proyecto 440 es razonable; el armado φ25/150 cubre incluso 461 (util 0,53). Recomiendo a JM **mantener φ25/150** (no bajar a φ20/150) precisamente por este margen y por la fisuración.
- **O-B · w_k cabeza de muro 0,198 mm, al límite de 0,20.** El φ25/200 cumple por poco en la cara exterior bajo combinación característica. Aceptable, pero sin holgura; vigilar si JM endurece la clase de estanqueidad de los muros.
- **D-C · Punzonamiento η 0,06 vs 0,08** (factor de carga sobre la rueda). Ambos holgados. No bloqueante.

A diferencia de la Rev.01, **ninguna discrepancia deja al productor por debajo de la solicitación real fuera de tolerancia.** El par crítico (vano/esquina) está ahora del lado correcto.

---

## 7. Gates para JM (vigentes / nuevos)

| Ref | Observación | Tipo | Acción |
|---|---|---|---|
| **R-1 (Rev.01)** | Par vano/esquina incoherente, vano 308 infra. | **CERRADO** | Rev.02 lo corrige (440/249, modelo único). Verificado por lámina completa independiente. ✅ |
| **R-2 (Rev.01)** | w_k cubierta vano > 0,20. | **CERRADO** | φ25/150 → w_k 0,169 ≤ 0,20. ✅ (mientras se mantenga φ25/150 si la cara inferior puede mojarse). |
| O-A (nuevo) | Vano sensible al tándem (410–461). | Observación | Mantener φ25/150; no bajar armado de vano. |
| O-B (nuevo) | w_k cabeza muro 0,198 al límite. | Observación | Aceptable; vigilar si cambia clase de estanqueidad. |
| O-2 (previa) | Flotación UPL con freático a rasante FS=0,65. | **Gate vigente** | JM: confirmar freático de proyecto; el cambio de vinculación no afecta a la flotación. |
| O-4/O-5 (previas) | Sismo hidrodinámico (EC8-4) y coacción térmica/retracción no cuantificados. | **Gates diferidos vigentes** | Sin cambio. |
| O-6 (previa) | `versions.lock=0.0.0`; motor propio no versionado. | Trazabilidad | Anclar versión antes de congelar golden. |

---

## 8. Regresión / golden

- **G-DEP-05 · "Cubierta de cajón monolítico — par vano/esquina consistente".** **Se puede congelar en VERDE** con el oráculo de esta QA: **lámina 2D completa del cajón** (folded-plate, validada contra Navier −0,3 % y con cierre exacto del nudo esquina↔muro). Caso golden: par (vano, esquina) del MISMO modelo, suma invariante ~650–690. Tolerancia **2 %** para la componente distribuida (convergida) y **10 %** para el total con tándem (por el pico de parche). Este golden captura el fallo de la Rev.01 (vano 308 quedaría fuera de banda) y valida la Rev.02 (440 dentro). **Anclar versión del motor (O-6) antes de marcar el golden verde.**
- **G-DEP-02 (punzonamiento + reparto tándem):** vigente; fijar γ_Q=1,5 sobre la rueda en el oráculo (η 0,08).
- **G-DEP-01/03/04 (muro ménsula, flotación, raft):** vigentes; la vinculación rígida no los invalida.

---

## 9. Conclusión

- **Veredicto técnico global: LIMPIO CON OBSERVACIONES (verde con gates).** La Rev.02 corrige la incoherencia de modelo de la Rev.01. Mi **lámina 2D completa del cajón** —oráculo de máximo nivel, sin aproximación de muelle— confirma de forma totalmente acoplada el par **vano ≈ 410–461 / esquina ≈ 218–250**, dentro de tolerancia del par de proyecto **440 / 249**, con cierre exacto del equilibrio de esquina y suma invariante ~650–690.
- **Capa normativa correcta:** utilizaciones ≤ 0,67, **w_k vano 0,169 ≤ 0,20** (φ25/150 resuelve la fisuración), w_k muros ≤ límite, punzonamiento η 0,08, As,mín cumplida.
- **Para firma de JM:** la Rev.02 es **técnicamente conforme y puede elevarse a firma**, condicionada a las observaciones O-A (mantener φ25/150), O-B (w_k muro al límite) y a los **gates vigentes O-2 (flotación/freático), O-4/O-5 (sismo, térmica) y O-6 (versionado)**, que son **independientes de este cálculo de cajón** y deben resolverse en paralelo. **G-DEP-05 se puede congelar en verde** con el oráculo de lámina completa, tras anclar la versión del motor.

**La QA no certifica ni firma.** Se eleva a JM, que decide sobre los gates y, en su caso, firma (dos llaves, GOBIERNO §B.5).

*— Agente de QA independiente, Estructurando 2.0 · 2026-06-24*
