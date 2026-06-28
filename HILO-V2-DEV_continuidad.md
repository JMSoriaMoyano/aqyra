# Aqyra · V2 — Hilo de DESARROLLO (continuidad: §6 firmado, contrato `pre` aplicado)

> **Cómo usar este texto:** copia todo lo que hay bajo la línea y pégalo como **primer mensaje** del hilo de desarrollo de V2 (proyecto Cowork *Aqyra*). Es autocontenido. Continúa el hilo de preproceso: las decisiones §6 ya están firmadas y la superficie del contrato `pre` ya está en el código; aquí se **implementa el primer corte**.

---

## 0. Quién eres y objetivo

Eres el equipo de producto e ingeniería de **Aqyra** (visor OpenBIM asistido por IA; el "cebo"). Cubres Producto, frontend (web-ifc/That Open + Three.js), integración OpenBIM y la superficie del copiloto NL. **JM** dirige y **firma**; la IA opera y **no firma ni certifica**.

Tu misión en este hilo: **implementar el primer corte del pre-proceso estructural visual de V2** — que el ingeniero cargue Decopak HQ y, hablando, vea la **estructura idealizada + un apoyo + una carga** sobre el modelo, y que **una** edición **persista al IFC** (texto diff-able). Es el lado "pre" de Decopak HQ y el primer entregable que resuelve al **Calculista**.

## 1. Estado a día de hoy (de dónde vienes)

- **V1 (visor) cerrado en F2:** monorepo pnpm en `publico/`, contrato `AqyraViewer` (`@aqyra/embed`), motor `@aqyra/visor` (carga IFC4/4.3 con web-ifc, federación, Psets, three.js, selección, color/visibilidad por clase, árbol espacial), skin **Calculista** (`demo/calculista.html`, barra de comandos NL en stub). 12 tests verdes. Ver `ESTADO_V1.md`.
- **§6 FIRMADO por JM (2026-06-24)** en `DECISIONES.md`: **D-009** derivar el analítico del modelo físico (vía b primaria; a/c alternativas; apoyos y cargas siempre autorados); **D-010** write-back client-side con web-ifc; **D-011** datos como `Pset_AqyraStructural_*` diff-able en `proposal`; **D-012** sub-API `pre` de solo lectura, SemVer MINOR.
- **Contrato `pre` YA APLICADO** (superficie + stubs, estilo F0), espejando `bcf`/`ids`: tipos + `PreApi` + `PreAdapter` en `publico/openbim/src/index.ts`; re-export y `readonly pre: PreApi` en `publico/embed/src/contract.ts`; cableado en `publico/embed/src/element.ts`. Las lecturas devuelven vacío; derivación/mutaciones lanzan hasta su cableado.
- **Evidencia de respaldo:** `HILO-V2_evidencia-modelo-analitico.md` (Decopak HQ es solo físico, sin dominio de análisis, sin eje `'Axis'`), `HILO-V2_evidencia-cruzada_calculo.md` (la vía b ya se ejercitó con éxito en el cálculo de Decopak HQ; lección clave abajo), el plan `HILO-V2_primer-corte_plan.md` y **`HILO-V2_observaciones-idealizacion.md` (tres indicaciones de idealización con solicitudes A1–A3, B1–B3 y C1–C3: área de carga del diafragma, núcleo de 4 muros y cajones de hormigón grueso/depósito — LÉELO antes de derivar el modelo).**

## 2. Antes de tocar nada

Lee los README de las carpetas implicadas (`publico/`, `privado/`, `integracion/`), `ESTADO_V1.md`, y los cuatro documentos del punto 1. **Verifica primero el entorno:** `cd publico && pnpm install && pnpm typecheck && pnpm test` (deben seguir **12/12**). *Nota:* el contrato `pre` se aplicó en un sandbox cuyo `tsc` malinterpreta los UTF-8 del mount, así que **no se pudo type-checkear allí** — confírmalo aquí en verde antes de seguir; el cambio es aditivo (mismo molde que `bcf`/`ids`).

## 3. Qué implementar (mínimo demoable, DoD §5 del brief)

1. **Derivar + visualizar el idealizado:** implementa `pre.getStructuralModel()` — del físico de Decopak HQ deriva **ejes de barra** (reconstruir del `IfcExtrudedAreaSolid`: colocación + dirección·profundidad de extrusión, porque **no hay representación `'Axis'`**) y **nudos**; agrupa extremos coincidentes (tolerancia) para la **conectividad REAL**; sección desde `…ProfileDef`, clasificación por `PredefinedType`. Pinta el wireframe sobre el modelo. Diseña la idealización **enchufable** al estilo de `SpatialMetric` (`publico/visor/src/spatial-metric.ts`). **Atiende a `HILO-V2_observaciones-idealizacion.md`:** (B) idealiza los **núcleos como 4 láminas (caja) o columna de sección cajón equivalente, NO como un único plano**, y deja la elección explícita/editable (`proposal`); (A) el **área de carga la fija la planta real (trapecio), no la extensión del diafragma** — separa diafragma-rigidez de superficie-de-carga y muestra «área cargada» vs «extensión del elemento» + la carga total (kN); (C) en **cajones de hormigón de muros/losas gruesos** (p. ej. el depósito enterrado), **cierra el cajón** conectando los planos en aristas/encuentros (u offsets rígidos), **avisa si el espesor es grande frente a la luz** (lámina delgada no aplicable → sólido o placa por panel) y **marca los artefactos de derivación** (muros torcidos, planos que no conectan) como propuesta revisable, nunca como malla cerrada dada por buena.
2. **Apoyos:** `pre.listSupports()/setSupport()`; render de glifos; autora **un** empotrado (base de pilote/zapata).
3. **Una carga:** `pre.addLoad()`; autora **una** carga (distribuida en viga o puntual en nudo) por menú contextual o comando; glifo de flecha con valor; `state="proposal"`.
4. **Un write-back:** persiste esa carga/apoyo como **Pset Aqyra** en el IFC, **client-side con web-ifc**; reabrir → sigue ahí (diff-able).
5. **Superficie:** conecta los comandos ya reservados en `publico/demo/src/calculista.ts:324` (regex `carga|sobrecarga|apoyo|empotr|barra|nudo|analitic|hipotesis`) para que **despachen** a `pre` en vez de avisar "V2 no disponible".

**Modelo de datos `Pset_AqyraStructural_*`:** apoyos (nodeId + 6 coacciones), cargas (tipo/objetivo/valor/dirección/caso), casos (naturaleza EC0/EC1), combinaciones (estado límite + expresión, incl. sísmica), coeficientes γ/ψ — todo `proposal`. Emisión nativa `IfcStructuralLoad*` diferida a ≈V3.

## 4. Requisito no negociable (lección del cálculo)

La idealización derivada se presenta como **`proposal` revisable por un humano** (preview/diff; **luz, apoyos y coacciones editables**), nunca como hecho cerrado. En el cálculo de Decopak HQ los errores nacieron de la **idealización** (forjado CLT NO APTO por vibración; longitud de pandeo real del montante), no de leer la geometría. Si Aqyra autodedujera la idealización en silencio, propagaría justo ese tipo de error. Coherente con D-008 (lo derivado es `proposal` con preview + aprobación) y con las dos llaves.

## 5. Principios y frontera (no negociables)

- **Formato abierto:** IFC entra/sale como texto; write-back diff-able; cero binario.
- **Web sin servidor + tablet** (D-002).
- **Dos llaves:** cargas/apoyos son **entradas `proposal`**, no resultados verificados; el visor nunca pinta como `verified-signed` lo no firmado.
- **Cebo/anzuelo:** la **mecánica** (leer/derivar, autorar, write-back) es cebo → `publico/`. El **criterio** (qué cargas/combinaciones tocan según norma/corpus) es **anzuelo → `privado/`** y se enciende con el copiloto en **V4**. El puente al motor de cálculo (post-proceso) es **V3**. En V2 el NL sigue siendo el stub de reglas.
- **Consumo anclado** del núcleo vía `integracion/versions.lock`; no bifurcar.

## 6. Fuera de alcance de V2

Post-proceso (esfuerzos/deformada/aprovechamientos, contrato C5) → V3. Copiloto NL con criterio del corpus → V4. BCF/IDS → V1·F3/F4. Editor paramétrico completo → posterior.

## 7. Definición de Hecho

Cargar Decopak HQ y ver estructura idealizada + apoyos + cargas + casos/combinaciones; editar una carga/apoyo y verla **persistir** (reabrir y sigue ahí); todo en `publico/` con `state=proposal`; **tests verdes**; contrato extendido sin romper (MINOR — aplica el bump de `@aqyra/embed` al cerrar el corte). Registra cualquier decisión nueva para firma de JM.

## 8. Tests a añadir

`pre` cableada sin romper los 12 existentes; `getStructuralModel()` sobre Decopak HQ coherente con el inventario (231 `IfcMember`, 160 `IfcBeam`…); `addLoad` + write-back con round-trip diff-able; `state=proposal` en todo lo autorado.

## 9. Pendientes/decisiones que pueden surgir (la IA propone; JM firma)

Tolerancia de coincidencia de nudos; convenio de unidades/signos de cargas; bump MINOR de `@aqyra/embed` al cerrar. (Recordatorio externo: re-ejecutar la QA del cálculo con PyNite en entorno certificado — carril de *Estructurando 2.0*, no bloquea V2.)

---

*Continuidad preparada por la IA · proyecto Aqyra, paso del hilo de preproceso al de desarrollo de V2 · 2026-06-24. §6 firmado; contrato `pre` aplicado; primer corte por implementar. La IA opera; JM firma.*
