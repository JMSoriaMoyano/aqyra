# Memoria de cálculo — Abastecimiento de agua a presión (EN 805)

**Obra:** red de distribución de agua de la urbanización (caso-LIN-06).
**Disciplina:** obras lineales — obras hidráulicas de abastecimiento.
**Norma:** UNE-EN 805 (abastecimiento de agua: tuberías, accesorios, válvulas).
**Método:** pérdida de carga **Darcy-Weisbach** (fricción por Swamee-Jain) sobre el
**grafo de red**; reparto por continuidad en árbol desde la fuente y **Hardy-Cross** en
mallas. Solver `obras-lineales:scripts/red/solver_presion.py` (copia del motor de red de
`instalaciones`, PT 4.3/4.4).

> Documento de **predimensionado/asistencia**. Debe ser **revisado y firmado por técnico
> competente (Ingeniero de Caminos, Canales y Puertos)**. Los valores marcados
> `[confirmar AN]` son parámetros normativos/criterio del despacho a confirmar.

## 1. Objeto y alcance

Comprobación hidráulica de una red de distribución a presión alimentada por un
**depósito** (fuente por cota), con un **anillo** (malla) de reparto. Se verifica, para
la hipótesis de demanda punta con **incendio concurrente** (un hidrante), que en todo
tramo la **velocidad** está en la banda admisible y que en toda acometida/hidrante la
**presión dinámica** supera el mínimo exigido, y que la **fuente** tiene carga suficiente.

## 2. Datos de partida

- **Fuente:** depósito con lámina de agua a cota **130,0 m**; presión relativa 0 en su
  nudo; la carga estática nace de la diferencia de cota con la red (`ρ·g·Δz`).
- **Red:** aducción Ø200 (fundición dúctil) del depósito a la cabecera; **anillo Ø125**
  entre cabecera, dos acometidas y un hidrante (cotas 96–100 m).
- **Demanda (EN 805):** ACO-1 800 hab-eq, ACO-2 600 hab-eq; HIDRANTE-1 caudal de
  incendio. Dotación **200 l/hab/día** `[confirmar AN]`, coef. de punta **2,5**
  `[confirmar AN]`, caudal de hidrante **16,7 l/s** (~1000 l/min) `[confirmar AN]`.

## 3. Hipótesis y criterios `[confirmar AN]`

| Parámetro | Valor | Origen |
|---|---|---|
| Dotación | 200 l/hab/día | criterio del despacho / ordenanza |
| Coef. de punta | 2,5 | criterio del despacho |
| Caudal de incendio (hidrante) | 16,7 l/s | criterio / RIPCI |
| Presión dinámica mínima | 250 kPa | EN 805 / ordenanza |
| Banda de velocidad | 0,5 – 2,0 m/s | anti-estancamiento ↔ anti-golpe de ariete |
| DN mínimo | 80 mm | catálogo de red |
| Rugosidad absoluta | 0,1 mm | fundición dúctil revestida |
| Fluido | agua 20 °C (ρ=998 kg/m³, ν=1,01·10⁻⁶ m²/s) | — |

## 4. Caudales de cálculo

Caudal medio por acometida `Q_medio = dotación · hab-eq / 86400`; caudal punta
`Q_punta = Q_medio · 2,5`. El hidrante aporta el caudal de incendio como **hipótesis
concurrente** (sin consumo doméstico propio).

| Aporte | hab-eq | Q consumo (l/s) | Q incendio (l/s) | Q total (l/s) |
|---|---|---|---|---|
| ACO-1 | 800 | 4,63 | — | 4,63 |
| ACO-2 | 600 | 3,47 | — | 3,47 |
| HIDRANTE-1 | — | — | 16,70 | 16,70 |
| **Total** | | | | **24,80** |

## 5. Cálculo hidráulico (Darcy-Weisbach de red)

El solver orienta la red como **árbol desde la fuente** (depósito), reparte el caudal por
continuidad aguas abajo y, en el **anillo**, resuelve el reparto hiperestático por
**Hardy-Cross** (corrección por lazo, n=2). La presión se propaga desde la fuente con la
cota geométrica.

- **Topología:** malla de **1 lazo**; Hardy-Cross **converge en 6 iteraciones**, residuo
  de cierre de lazo ≈ 0 kPa (2.ª ley de Kirchhoff hidráulica satisfecha).
- **Balance de caudales:** continuidad nodal cerrada (residuo ≈ 0 %).

| Tramo | DN (mm) | Q (l/s) | v (m/s) | Δp (kPa) |
|---|---|---|---|---|
| COND-0 (aducción) | 200 | 24,80 | 0,79 | 1,09 |
| COND-1 | 125 | 12,64 | 1,03 | 12,87 |
| COND-2 | 125 | 8,01 | 0,65 | 5,42 |
| COND-3 | 125 | 8,69 | 0,71 | 6,33 |
| COND-4 | 125 | 12,16 | 0,99 | 11,97 |

Todas las velocidades en la banda **0,5–2,0 m/s** (sin estancamiento ni riesgo de golpe
de ariete/erosión).

## 6. Comprobación de presiones

| Punto | p disponible (kPa) | p mínima (kPa) | Margen (kPa) | Cumple |
|---|---|---|---|---|
| ACO-1 | 299,3 | 250 | +49,3 | ✔ |
| **ACO-2 (más desfavorable)** | **290,4** | 250 | **+40,5** | ✔ |
| HIDRANTE-1 | 313,5 | 250 | +63,5 | ✔ |

**Fuente (depósito por cota):** presión requerida −40,5 kPa (la carga por cota cubre la
demanda) → margen **+40,5 kPa**. **No se requiere bombeo**: la cota del depósito (≈ 30–34 m
sobre la red) basta para garantizar el mínimo en el nudo más desfavorable.

## 7. Conclusión

**La red CUMPLE** la comprobación de abastecimiento a presión (EN 805) para la hipótesis
de demanda punta con incendio concurrente: velocidades en banda, presión ≥ 250 kPa en
todas las acometidas y el hidrante, y carga de fuente suficiente desde el depósito por
cota, con la malla resuelta por Hardy-Cross. Los resultados se han volcado al IFC
(`Pset_Estructurando_ResultadoRed`) y la red enriquecida re-valida su continuidad.

> **Predimensionado.** A revisar y firmar por técnico competente (ICCP). Confirmar los
> NDP de la tabla del §3 con el Anejo Nacional / criterio del despacho / ordenanza
> municipal.
