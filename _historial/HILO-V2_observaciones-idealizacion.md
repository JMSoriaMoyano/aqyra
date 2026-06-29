# HILO-V2 · Observaciones e indicaciones sobre la idealización (desde el cálculo)

> **Qué es:** revisión de la **modelización analítica** que el hilo V2 propone, contrastada con los modelos del **cálculo (*Estructurando 2.0*)**, sobre dos casos: **Decopak HQ** (esqueleto de barras + diafragmas + núcleos) y el **Depósito enterrado de Decopak** (cajón de hormigón de muros/losas gruesos). Incluye **tres indicaciones con solicitudes** para el pre-proceso. La IA prepara la evidencia; **JM decide y firma**.
> **Fecha:** 2026-06-24 · **Relación:** `HILO-V2_evidencia-cruzada_calculo.md` (la idealización es la fuente de error) · `HILO-V2_primer-corte_plan.md` (§C derivación, §E proposal revisable).

---

## 1. Proximidad con el modelo del cálculo (contexto)

**Coincide en el esqueleto; se aleja en las superficies.**

- **Coincide:** las **barras de las celosías** (Cajón O / Cercha E / Alma C), los **nudos**, los **apoyos** y los **pilotes** son la misma idealización que la QA resolvió nodalmente (FEM de barras por rigidez directa).
- **Se aleja:** en el cálculo los **forjados** entraron como **carga por áreas tributarias** (líneas de carga sobre barras), no como diafragmas; y los **muros** se comprobaron como **elementos de hormigón a flexocompresión (EC2)**, no como láminas. La QA, además, redujo el Cajón O a un **Vierendeel 2D del alzado desarrollado**.

→ El modelo de V2 es una idealización **FEM más completa** (añade diafragmas y láminas de núcleo). Eso **es bueno**, pero introduce **dos decisiones de idealización** que, mal resueltas, falsean los resultados. Son del tipo que ya marcamos como **fuente de error** (no la lectura del IFC, sino cómo se idealiza).

---

## 2. Indicación A — Carga superficial: el diafragma rectangular «ocupa más» que la planta (trapecio)

**Problema.** Los diafragmas se dibujan como **rectángulos** mayores que la planta real (**trapecio**). Si se asigna una carga superficial q (kN/m²) al diafragma y el solver la integra **sobre el rectángulo**, se aplica F = q·A_rectángulo **> q·A_planta_real → el modelo queda sobrecargado** (más fuerza total que la real).

**Regla.** La carga gravitatoria debe repercutir sobre la **superficie realmente cargada (el trapecio)**, no sobre la extensión dibujada del diafragma. Hay que **no mezclar** los dos papeles del diafragma:
- **rigidez en su plano** (vínculo que reparte acciones horizontales; **no añade peso**), y
- **superficie de transferencia gravitatoria** (aquí manda el **área real**).

**Vías correctas** (cualquiera vale): (a) modelar el diafragma con la **geometría real** (trapecio); (b) usar el rectángulo **solo como diafragma rígido** y aplicar la gravedad aparte sobre el área real / como cargas lineales en vigas de borde; (c) si se carga el rectángulo, **corregir** la presión a q' = q·(A_real/A_rect).

**En el cálculo no apareció** porque se usaron áreas tributarias (la carga salió del área real; p. ej. el Cajón O recibió ~83 kN/m del ancho tributario real).

**Solicitud a V2:**
1. Que `pre` derive el **área de carga de la geometría real de la planta** (trapecio), **no** de la extensión del diafragma.
2. Separar en el modelo de datos el **diafragma-rigidez** (vínculo) de la **superficie-de-carga** (área tributaria real).
3. Que el visor **muestre explícito** «área cargada» vs «extensión del elemento», y exponga la carga total resultante (kN) para que el usuario la valide — coherente con la idealización como **`proposal` revisable**.

---

## 3. Indicación B — Núcleo: una lámina de un plano, pero el núcleo son 4 muros

**Problema.** El núcleo se modela como **una lámina (un plano)**, pero físicamente es una **caja de 4 muros**. Colapsar la caja en un plano **pierde 3 muros, la rigidez torsional de la sección cerrada y la flexión biaxial**. **No se puede armar 4 muros con 1 plano.**

**Cómo se obtiene el armado (y por qué un plano no basta).** De una lámina se obtienen, por metro, los esfuerzos de **membrana** (n_x, n_y, n_xy) y de **placa** (m_x, m_y, m_xy), y de ahí el armado por el **modelo sándwich** (EC2). Pero eso solo arma **ese plano**. Para armar el núcleo real, dos vías:
- **(a) Cuatro láminas** (un plano por muro, formando la caja) → n/m por metro en cada muro → **armado por muro** (sándwich). Es la modelización shell natural de un núcleo.
- **(b) Columna-equivalente** con las propiedades de la **sección cajón** (A, I_x, I_y, **J**, áreas de cortante) → **N-M-V-T por planta** → **repartir** esos esfuerzos a cada pared (flexocompresión + flujo de cortante de Bredt) y armar.

El **plano único** sirve como «muro ancho equivalente» para captar **rigidez lateral / arriostramiento en una dirección** (válido para el reparto global y el sismo en ese plano), **pero no para armar**. En el cálculo se usó la vía (b) a nivel de elemento (cada muro como flexocompresión EC2); salía holgado (u≈0,11) porque gobierna la gravedad.

**Matiz de fase:** el **armado** es post-proceso/cálculo (**V3**, bajo dos llaves), no V2. Pero **la forma de idealizar el núcleo se decide ya en V2** (al derivar el modelo analítico), así que la elección «1 plano vs 4 láminas vs columna-cajón» debe quedar resuelta y expuesta desde el pre-proceso.

**Solicitud a V2:**
1. Que `getStructuralModel()` idealice el núcleo como **4 láminas (caja)** o como **columna de sección cajón equivalente**, **no como un único plano**, cuando el físico tenga el núcleo cerrado.
2. Que la elección de idealización del núcleo sea **explícita, revisable y editable** (`proposal` con preview), no automática y silenciosa.
3. Reservar para **V3** (puente al cálculo) la obtención del armado a partir de los esfuerzos de membrana/placa o de la sección cajón.

---

## 4. Indicación C — Cajones de hormigón grueso (depósito enterrado): la lámina media no cierra el cajón

**Contexto.** En la idealización del **Depósito enterrado de Decopak** (muros 50/20 cm; losas de fondo y superior 60/70 cm) el pre-proceso produjo un modelo **incoherente**: un muro **inclinado** (artefacto al reconstruir el plano medio del `IfcExtrudedAreaSolid`), **planos medios que no conectan** en aristas y encuentros muro-losa (**desfase de media sección**), y la **losa de fondo dibujada mayor que el cajón**. Tal cual, un FEM sobre esa malla da esfuerzos sin sentido.

**Por qué.** La idealización por **superficie media** es buena para elementos **esbeltos** (barras de HQ), pero un depósito es de **muros y losas gruesos** (espesor comparable a la luz): las hipótesis de lámina delgada flojean, los **desfases de plano medio en las uniones importan mucho** y el **auto-cosido** de planos desde los sólidos **distorsiona la geometría**.

**Cómo se resuelve** (igual que en el cálculo: el ingeniero define geometría/apoyos/continuidad; no se cose a ojo):
- **Cerrar el cajón:** continuidad explícita en aristas y encuentros muro-losa (o **offsets rígidos** que recojan el espesor), para que transmita cortante y momento en las esquinas.
- **Si el espesor es grande frente a la luz:** valorar **sólidos** (brick) o el **análisis elástico de placas por panel** (tablas de depósito rectangular o FE de placa con bordes reales) — lo estándar en depósitos de hormigón.
- **Cargas desde el área real** (hidrostática, tierras, tráfico), no del plano sobredimensionado.

**Solicitud a V2** (cuando idealice estructuras de muros/losas — cajones de hormigón): (C1) **cerrar el cajón** conectando los planos en aristas/encuentros (u offsets rígidos); (C2) **avisar si el espesor es grande frente a la luz** (lámina delgada no aplicable → proponer sólido o placa por panel); (C3) **detectar y marcar los artefactos de derivación** (muros torcidos, planos que no conectan) y sacarlo como **propuesta revisable**, nunca como malla cerrada dada por buena.

## 5. Solicitudes resumidas (la IA propone; JM firma)

| # | Solicitud | Dónde encaja |
|---|---|---|
| A1 | Área de carga = geometría real de la planta (trapecio), no el rectángulo del diafragma. | `pre` derivación + modelo de datos |
| A2 | Separar diafragma-rigidez (vínculo) de superficie-de-carga (área tributaria). | modelo de datos / `Pset_AqyraStructural_*` |
| A3 | Mostrar «área cargada» vs «extensión del elemento» y la carga total (kN). | visor / UI proposal |
| B1 | Núcleo como 4 láminas o columna-cajón equivalente, no 1 plano. | `getStructuralModel()` |
| B2 | Idealización del núcleo explícita y editable (`proposal`). | UI proposal/preview |
| B3 | Armado del núcleo (de membrana/placa o sección cajón) → diferido a V3. | puente al cálculo (privado/, V3) |
| C1 | Cerrar el cajón: conectar planos en aristas/encuentros (u offsets rígidos). | `getStructuralModel()` |
| C2 | Avisar si el espesor es grande frente a la luz (lámina delgada no aplicable → sólido/placa por panel). | derivación + UI |
| C3 | Detectar/marcar artefactos (muro torcido, planos sin conectar) como `proposal` revisable. | derivación + UI proposal |

## 6. Gobierno

Ambas son **decisiones de idealización, no de geometría** — el patrón que marcamos como fuente de error (forjado CLT, longitud de pandeo del montante). Por eso deben salir como **propuesta revisable por un humano** (preview/diff), nunca como hecho cerrado, y el **resultado definitivo (esfuerzos y armado) lo confirma la QA con el FEM real** bajo dos llaves. Para **rigidez lateral y reparto global** las simplificaciones (rectángulo rígido, plano equivalente) pueden valer; **para cargar y para armar, no**.

---

*Observaciones preparadas por la IA (equipo de Estructurando 2.0, aportando al hilo V2 de Aqyra) · 2026-06-24 · para revisión y firma de JM. La IA opera; JM decide y firma.*
