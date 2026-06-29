# HILO-V3 · D-021 — Estado de dato en el visor (las dos llaves, visibles) — FIRMADO

> **✅ ESTADO: FIRMADO por JM el 2026-06-25 con C.1.a + C.2.** C.1.a = 4 estados (`proposal`/`computed`/`qa-passed`/`verified-signed`); C.2 = guarda de exportación (toda salida no firmada estampa «NO VERIFICADO»). Inscrita en `DECISIONES.md` como **D-021**. Este documento se conserva como evidencia. La IA preparó la evidencia; **JM decidió y firmó**.
> **Propuesta original de la IA** (Producto / BIM-IFC) con evidencia. **La IA prepara la evidencia; JM decide y firma.**
> **Qué resuelve:** cómo el visor **representa y hace cumplir** el estado de un resultado — de propuesta a verificado-firmado — para que **nunca** se pueda presentar como certificado lo que no lo está. Es la materialización en pantalla del gobierno de **dos llaves**.
> **Independiente del motor:** todo en `publico/` (cebo). No espera a C5; lo consume cuando llegue.
> **Fecha:** 2026-06-25.

---

## A. Por qué hace falta D-021 (el riesgo concreto)

Un resultado del motor —una deformada, un aprovechamiento de 0,95, un mapa de colores— **parece una respuesta**. Sin una señal inequívoca, un usuario puede capturar la pantalla y tratarlo como cálculo certificado, cuando aún no ha pasado QA ni lleva firma. Ese es justo el fallo que el gobierno prohíbe: «el visor **nunca** pinta como `verified-signed` lo no firmado».

Hoy el contrato ya reserva `DataState = "proposal" | "verified-signed"` (`embed/src/contract.ts`, desde V1) y la skin Calculista tiene un **cartel persistente sin ✕** (rojo, solo se retira al resolver el modelado). D-021 **eleva ese mecanismo** del modelado de V2 al **estado de los resultados** de V3 y lo convierte en regla dura.

**Anclaje de estándar (verificado).** ISO 19650 ya define el ciclo: códigos **S** (WIP/Compartido, **no contractual**) → tras el sign-off formal, códigos **A/B** (**Publicado, contractual**). Las **dos llaves de Aqyra son ese sign-off**. Alineamos el estado de dato con esos códigos para hablar el mismo idioma que el **CDE Aqyra** (skill `cde-audit`, estados S0–S7), no una taxonomía paralela.

---

## B. Propuesta (lo que se firma)

### B.1 · Modelo de estados (las dos llaves, explícitas)
Se extiende `DataState` de binario a un conjunto que refleja **cuántas llaves** lleva el dato:

| Estado | Significado | Llaves | ISO 19650 |
|---|---|---|---|
| `proposal` | Input autorado/derivado (modelo, cargas, apoyos, uniones, idealización). Editable. | — | WIP / S0 |
| `computed` | El motor produjo el resultado, **sin verificar**. Es un cálculo, no una verdad. | **0** | WIP / S0 |
| `qa-passed` | **1.ª llave:** QA independiente (PyNite) reconcilia dentro de tolerancia; **a falta de firma**. | **1** | Compartido / S3 (revisión, antesala del sign-off) |
| `verified-signed` | **2.ª llave:** JM firma. Contractual. | **2** | Publicado / A |

`proposal` y `verified-signed` ya existen en el contrato; se añaden **`computed`** y **`qa-passed`** (cambio de contrato **MINOR**; `PreDataState` de `openbim` espeja).

### B.2 · Regla visual BINARIA en la frontera de confianza
Aunque haya cuatro estados para la **auditoría**, en pantalla la frontera es **una y solo una**: **solo `verified-signed` recibe el tratamiento «certificado»** (limpio, verde, sin marca). **Todo lo demás se ve provisional**, sin ambigüedad. Un resultado `computed` no puede parecerse a uno firmado.

### B.3 · Lenguaje visual (canvas-first, D-007)
- **Chip de estado persistente** del layer de resultado activo (esquina/cabecera), color + etiqueta:
  - `proposal` — neutro/gris · «PROPUESTA»
  - `computed` — **rojo** · «NO VERIFICADO»
  - `qa-passed` — **ámbar** · «QA OK · SIN FIRMAR»
  - `verified-signed` — **verde** · «VERIFICADO · firma JM»
- **Marca de agua / trama** sobre los overlays de resultado mientras NO estén `verified-signed` (diagonal «NO VERIFICADO»): el render «limpio» se reserva al firmado.
- **Leyenda** estado→color siempre accesible (coherente con el listado de clases de la skin).
- **Cartel persistente** (reutiliza `warnBanner`, rojo, sin ✕) cuando hay resultados `computed` a la vista.

### B.4 · Enforcement (lo que hace la regla *dura*, no solo estética)
- El tratamiento «certificado» (verde/limpio) está **condicionado a `state==="verified-signed"`** en el render. Ese estado **solo lo puede acuñar el flujo de firma** (QA + firma, en `privado/`): el camino de render público **nunca** lo produce. → Aunque un bug del cebo intente pintar algo como verificado, no puede: el verde solo nace del *write-back* firmado.
- **Guarda de exportación:** cualquier exportación (imagen, PDF/informe, BCF) de un resultado no firmado **estampa la marca de estado**, para que no circule como certificado fuera de la pantalla.
- **Transición `→ verified-signed`**: solo vía QA (PyNite, D-023) + firma de JM (`privado/`). El visor **muestra** el estado; no lo **mina**.

### B.5 · Alcance de D-021 (y lo que queda fuera)
- **Dentro:** la **representación** y el **enforcement** del estado en el visor; el modelo de estados; el mapeo a ISO 19650; la guarda de exportación.
- **Fuera (otras decisiones):** el **mecanismo de QA** (PyNite) → D-023; la **mecánica de firma** y el puente que acuña `verified-signed` → `privado/` (D-019 contrato C5). D-021 define los estados y cómo se ven/aplican; **no** los produce.

---

## C. Puntos abiertos para JM

**C.1 · Granularidad de estados.**
- **C.1.a (recomendada) — 4 estados** (`proposal`/`computed`/`qa-passed`/`verified-signed`). Hace **legibles las dos llaves** (se ve qué falta: QA o firma) y casa con ISO 19650 (S0/S3/A). La frontera visual sigue siendo binaria (B.2).
- **C.1.b — binario** (`proposal`/`verified-signed`): `computed` y `qa-passed` caen en `proposal`. Más simple en el contrato, pero **funde «aún dibujo cargas» con «el FEM dio 0,95 sin verificar»** bajo la misma etiqueta — peor para la auditoría y el aviso.

**C.2 · Guarda de exportación (B.4).** ¿Estampar la marca de estado en TODA exportación no firmada (recomendado **sí**: cierra la fuga fuera de pantalla) o solo avisar en pantalla?

El resto (regla binaria de confianza, enforcement por `verified-signed` como única fuente del verde) no tiene alternativa razonable: es el núcleo del gobierno.

---

## D. Entrada lista para `DECISIONES.md` (al firmar)

### D-021 · Estado de dato en el visor (dos llaves visibles) (V3)
- **Fecha de firma:** ____ · **Firmante:** JM · **FIRMA: ☐ pendiente**
- **Decisión:** el visor representa el estado de cada dato con un **modelo que refleja las dos llaves** —`proposal` (input) / `computed` (motor, 0 llaves) / `qa-passed` (1.ª llave: QA PyNite) / `verified-signed` (2.ª llave: firma JM)— mapeado a ISO 19650 (S0 / S0 / S3 / A) para alinear con el CDE Aqyra. **Regla visual binaria:** solo `verified-signed` recibe el tratamiento «certificado» (verde/limpio); todo lo demás se ve provisional (chip de estado + marca de agua «NO VERIFICADO»). **Enforcement:** el verde está condicionado a `state==="verified-signed"`, estado que **solo acuña el flujo de firma de `privado/`** — el render público nunca lo produce; **guarda de exportación** que estampa la marca en cualquier salida no firmada. Cambio de contrato **MINOR** (añade `computed`/`qa-passed` a `DataState`; `PreDataState` espeja).
- **Bifurcaciones firmadas por JM:** [C.1 granularidad: 4 estados / binario] · [C.2 guarda de exportación: sí / solo pantalla].
- **Evidencia:** ISO 19650 — códigos S (WIP/Compartido, no contractual) vs A/B (Publicado, contractual tras sign-off); S3 = revisión, antesala del sign-off (verificado 2026-06-25); contrato V2 — `DataState` ya reserva `proposal`/`verified-signed` (`embed/src/contract.ts`); skin Calculista — `warnBanner` persistente sin ✕ (`demo/src/calculista.ts`). Detalle en `HILO-V3_para-firma_D-021-estado-dato.md`.
- **Acciones que dispara:** (1) extender `DataState`/`PreDataState` con `computed`/`qa-passed` + bump MINOR de `@aqyra/embed`; (2) chip de estado + marca de agua + leyenda en el visor/skin, con el verde gated a `verified-signed`; (3) guarda de exportación (imagen/PDF/BCF) que estampa estado; (4) mapeo estado↔ISO 19650 compartido con `cde-audit`; (5) test: un layer `computed` NUNCA renderiza con estilo certificado; solo el *write-back* firmado vira a verde.

---

## Fuentes

- **ISO 19650 — códigos de estado/idoneidad:** S0 (WIP, no compartir fuera de autoría), S1/S2/S3 (Compartido; S3 = revisión y comentario, antesala del sign-off formal), A/B (Publicado, contractual tras aprobación), CR (as-built). BS EN ISO 19650-2 Annex A (consultado 2026-06-25): [Understanding Status Codes — Man and Machine](https://www.manandmachine.co.uk/understanding-status-codes-bs-en-iso-19650-2-national-annex-a/) · [Container Information States ISO 19650 — BibLus](https://biblus.accasoftware.com/en/container-information-states-iso-19650-wip-shared-published-archived/) · [UK BIM Framework — Guidance Part C (CDE)](https://www.ukbimframework.org/wp-content/uploads/2021/02/Guidance-Part-C_Facilitating-the-common-data-environment-workflow-and-technical-solutions_Edition-1.pdf)
- **Estado interno:** `publico/embed/src/contract.ts` (`DataState` reservado desde V1), `publico/demo/src/calculista.ts` (`warnBanner` persistente), `privado/README.md` (regla de dos llaves), skill `cde-audit` (estados S0–S7 del CDE Aqyra) — repo Aqyra, 2026-06-25.

---

*Para-firma de D-021 · proyecto Aqyra, hilo V3 · evidencia preparada por la IA · 2026-06-25. Tras la firma, trasladar §D a `DECISIONES.md`. La IA opera; JM firma.*
