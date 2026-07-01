# Memoria de instalaciones — Caso REBT-01: instalación eléctrica de vivienda

> Predimensionado/asistencia. **Debe ser revisado y firmado por técnico competente
> (Ingeniero de Caminos).** Los valores no determinados (NDP) se marcan `[confirmar AN]`.
> Disciplina `instalaciones`, vertical eléctrico (REBT), PT 4.5 (Ola 4).

## 1. Objeto y alcance

Dimensionado y comprobación de la instalación eléctrica interior de una **vivienda**
con **grado de electrificación elevada** (REBT, ITC-BT-25), de extremo a extremo:
modelo IFC MEP (sistema `ELECTRICAL`) → modelo neutro de red → bases de demanda →
solver de red eléctrica → verificación → escritura de resultados al IFC. Se comprueban
las **caídas de tensión** y las **intensidades admisibles** de cada circuito.

## 2. Normativa y referencias

- **REBT** (RD 842/2002) y sus Instrucciones Técnicas Complementarias.
- **ITC-BT-10** — previsión de cargas; grado de electrificación.
- **ITC-BT-25** — número de circuitos y características (vivienda): C1–C12.
- **ITC-BT-19** — caídas de tensión admisibles e intensidades admisibles de los
  conductores.
- **ITC-BT-44/-47** — receptores (alumbrado y motores), cuando aplica.

Todos los valores normativos por defecto se consideran **NDP `[confirmar AN]`**; el
dato del proyecto (IFC) prevalece sobre el valor por defecto.

## 3. Descripción de la red

Red **radial (en árbol)** alimentada desde el **cuadro general de la vivienda**
(fuente / ancla). Topología leída del IFC por el parser MEP de `iso19650-openbim`
(agnóstico al tipo de sistema): **9 nodos, 8 tramos, 8 terminales, 1 fuente**. Cada
terminal representa un **circuito** (C1, C2, C3, C4, C5, C8, C9, C12).

Conductores de **cobre**, aislamiento **PVC** `[confirmar AN]`. Conductividad
γ = 56 m/Ω·mm² (Cu, 20 °C) `[confirmar AN]`. Tensión monofásica **230 V**.

## 4. Bases de demanda (slot CN-3)

Modo **vivienda** (ITC-BT-25). Potencia de cálculo por circuito = P_prevista · Fu · Fs
(factores de utilización y simultaneidad de la tabla de la ITC-BT-25 `[confirmar AN]`).
Grado de electrificación **elevada** (potencia mínima prevista 9 200 W, ITC-BT-10).

**Potencia prevista total: 18 705,8 W.**

| Circuito | Uso | P cálculo (W) | cos φ | S mín. norm. (mm²) |
|---|---|---|---|---|
| C1 — Iluminación | alumbrado | 1 552,5 | 0,90 | 1,5 |
| C2 — Tomas uso general | fuerza | 368,0 | 0,95 | 2,5 |
| C3 — Cocina/horno | fuerza | 2 025,0 | 0,95 | 6,0 |
| C4 — Lavadora/lavavajillas/termo | fuerza | 1 707,8 | 0,95 | 4,0 |
| C5 — Tomas baño y cocina | fuerza | 690,0 | 0,95 | 2,5 |
| C8 — Calefacción | fuerza | 5 750,0 | 0,95 | 6,0 |
| C9 — Aire acondicionado | fuerza | 5 750,0 | 0,95 | 6,0 |
| C12 — Adicional | fuerza | 862,5 | 0,95 | 2,5 |

## 5. Método de cálculo

- **Intensidad por tramo:** I = P / (U · cos φ) (monofásico).
- **Propuesta de sección:** método de momentos sobre catálogo normalizado, limitada
  por la **intensidad admisible** (ITC-BT-19, Cu, PVC, 2 conductores cargados) y por la
  **sección mínima** normativa del circuito.
- **Caída de tensión (comprobación vinculante):** método de las intensidades,
  ΔU = 2·L·I·cos φ / (γ·S), **acumulada** desde el cuadro por la rama. Si la caída
  acumulada supera el límite (**3 % alumbrado / 5 % fuerza**, ITC-BT-19), el solver
  **sube la sección** del tramo gobernante hasta cumplir.
- **Topología radial:** propagación por árbol (se reutiliza la del solver hidráulico
  del plugin); no se requiere reparto hiperestático (Hardy-Cross).

## 6. Resultados y comprobaciones

**Veredicto: CUMPLE.** Balance de potencias **0,0000 %** (continuidad). Caída de
tensión máxima **1,098 %** (circuito gobernante **C8 — Calefacción**), muy por debajo
del límite. Intensidades dentro del admisible en todos los tramos.

| Circuito | Fases | I (A) | S (mm²) | I adm. (A) | ΔU acum. (%) | Límite (%) | Cumple |
|---|---|---|---|---|---|---|---|
| C1 — Iluminación | mono | 7,50 | 1,5 | 15 | 1,048 | 3 | ✔ |
| C2 — Tomas uso general | mono | 1,68 | 2,5 | 21 | 0,149 | 5 | ✔ |
| C3 — Cocina/horno | mono | 9,27 | 6,0 | 36 | 0,342 | 5 | ✔ |
| C4 — Lavadora/termo | mono | 7,82 | 4,0 | 27 | 0,432 | 5 | ✔ |
| C5 — Tomas baño/cocina | mono | 3,16 | 2,5 | 21 | 0,316 | 5 | ✔ |
| C8 — Calefacción | mono | 26,32 | 6,0 | 36 | 1,098 | 5 | ✔ |
| C9 — Aire acondicionado | mono | 26,32 | 6,0 | 36 | 1,098 | 5 | ✔ |
| C12 — Adicional | mono | 3,95 | 2,5 | 21 | 0,395 | 5 | ✔ |

**Write-back al IFC:** se escriben los Psets `Pset_Estructurando_ResultadoRed` (sección,
intensidad, caída de tensión, potencia por tramo; potencia, tensión, caída acumulada y
veredicto por terminal) — **8 elementos enriquecidos**. Validación de red con
`iso19650-openbim:ifc-validate`: **APTO** (continuidad 100 %, 0 incidencias; el validador
exige `Pset_CableSegmentTypeCommon` por ser sistema ELECTRICAL).

## 7. Conclusiones y observaciones

La instalación, con las secciones propuestas (mínimas normativas de la ITC-BT-25 en
todos los circuitos), cumple holgadamente las caídas de tensión y las intensidades
admisibles. El circuito gobernante en caída de tensión es la calefacción (C8). Todos
los NDP marcados `[confirmar AN]` (γ, aislamiento, factores Fu/Fs, intensidades
admisibles de tabla) deben ser confirmados por el técnico. **Predimensionado a revisar
y firmar por técnico competente (Ingeniero de Caminos).**

---

*Registro de comprobación — 2026-06-22 · sistema ELECTRICAL (vivienda, electrificación
elevada) · solver eléctrico radial (intensidades + momentos) · γ=56, PVC, 230 V ·
resultado CUMPLE (balance 0,0 %, ΔU máx 1,098 %) · Psets de resultado escritos al IFC
(APTO).*
