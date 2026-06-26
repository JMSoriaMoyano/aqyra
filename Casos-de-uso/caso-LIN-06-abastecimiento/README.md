# caso-LIN-06-abastecimiento — red de distribución a presión (Darcy-Weisbach de red)

**PT 6.3 (Ola 6 · cierre).** Primer caso de extremo a extremo del **solver Darcy-Weisbach
de red** de `obras-lineales` v0.4.0 (subagente `proyectista-de-abastecimiento`), sobre el
**dominio IFC MEP de abastecimiento** de `iso19650-openbim` v0.7.0. Es el **gemelo a
presión** del `caso-LIN-05-saneamiento` (lámina libre): mismo grafo del núcleo, solver
**reutilizado de `instalaciones`** (decisión nº7 "grafo + N solvers"). **Con este caso se
cierra la Ola 6.**

Todo es **predimensionado/asistencia**: revisar y firmar por técnico competente
(Ingeniero de Caminos). NDP marcados `[confirmar AN]`.

## El caso

Red de **distribución de agua a presión** de una urbanización, alimentada por un
**depósito** (fuente por cota) y con un **anillo** (malla) que reparte el caudal:

```
  DEPÓSITO (lámina z=130 m)
       │  COND-0  Ø200  (aducción)
       ▼
      N0 ───COND-1 Ø125─── N1 (ACO-1, 800 hab-eq)
       │                     │
    COND-4 Ø125           COND-2 Ø125
       │                     │
      N3 ───COND-3 Ø125─── N2 (HIDRANTE-1)
   (ACO-2, 600 hab-eq)
```

El **anillo N0-N1-N2-N3-N0** es una **malla (1 lazo)** que ejercita el **Hardy-Cross**.
La **fuente es el ancla de presión** (al revés que el vertido del saneamiento): el
depósito declara presión relativa **0** en su nudo (a la cota de lámina, 130 m) y la
**carga estática** la genera la propagación por cota del solver (`ρ·g·Δz`).

| Nudo | Cota z (m) | Tipo |
|---|---|---|
| Depósito | 130,0 | **fuente (ancla de presión por cota)** |
| N0 | 100,0 | cabecera (unión) |
| N1 | 98,0 | acometida ACO-1 (800 hab-eq) |
| N2 | 96,0 | **hidrante HIDRANTE-1** (nudo más desfavorable) |
| N3 | 99,0 | acometida ACO-2 (600 hab-eq) |

## Flujo (IFC → cálculo → IFC)

1. **Generar IFC MEP** de abastecimiento — `iso19650-openbim:scripts/mep/generate_test_ifc_abastecimiento.py`
   → `red_abastecimiento.ifc` (`IfcDistributionSystem` PredefinedType **WATERSUPPLY**;
   **depósito** `IfcTank` con `Pset_Estructurando_Red.WaterLevel`; acometidas
   `IfcFlowTerminal` con `HabitantesEq`; **hidrante** `IfcFlowTerminal`; tuberías
   `IfcFlowSegment` con `NominalDiameter`/`Roughness`).
2. **Parsear → modelo neutro de red** — `iso19650-openbim:scripts/mep/ifc_to_model_mep.py`
   → `modelo_red.json` (5 nodos, 5 tramos; el depósito se emite en `fuentes[]`
   `tipo:"deposito"` con `cota_lamina`; sin `vertidos`). El parser es **agnóstico al
   sistema** y reconoce el depósito por **jerarquía `is_a(IfcFlowStorageDevice)`**.
3. **Validar la red** — `iso19650-openbim:scripts/mep/validacion_red.py`
   → `validacion_red_topologia.json` (continuidad **desde la fuente**: cobertura 100 %,
   sin huérfanas) → **CUMPLE**.
4. **Demanda + solver + verificación** — `obras-lineales:scripts/red/run_all_abastecimiento.py`
   → `modelo_red_resuelto.json` (gancho `red`), `resultado_red.json`,
   `verificacion_red_calculo.json`, `mapping_resultado_red.json`. Demanda **EN 805**
   (dotación·hab-eq·punta + **hidrante concurrente**), **solver Darcy-Weisbach** (árbol
   desde la fuente + **Hardy-Cross** en el anillo), comprobación de presión/velocidad/DN.
5. **Write-back al IFC** — `obras-lineales:scripts/red/resultado_red_presion.py` (mapping)
   + `iso19650-openbim:ifc-create:escribir_psets_resultado.py`
   → `red_abastecimiento_resultado.ifc` (`Pset_Estructurando_ResultadoRed`: 8 elementos,
   40 propiedades). Re-parseado y re-validado → **CUMPLE** (continuidad intacta).

## Resultado

**VEREDICTO: CUMPLE.**

- **Demanda (EN 805):** ACO-1 4,63 l/s (800 hab-eq), ACO-2 3,47 l/s (600 hab-eq),
  **HIDRANTE-1 16,70 l/s** (incendio concurrente) → **caudal total 24,80 l/s**
  (dotación 200 l/hab/día, coef. de punta 2,5).
- **Topología:** **malla de 1 lazo**; Hardy-Cross **converge en 6 iteraciones**, residuo
  de cierre de lazo ≈ 0 kPa.
- **Tramos:** aducción COND-0 Ø200 a 0,79 m/s; anillo Ø125 entre **0,65 y 1,03 m/s** —
  todos dentro de la **banda 0,5–2,0 m/s** (anti-estancamiento ↔ anti-golpe de ariete).
- **Presiones:** todas las acometidas/hidrante **≥ 250 kPa**. **Nudo más desfavorable:
  ACO-2**, presión disponible **290,4 kPa** (margen +40,5 kPa). HIDRANTE-1: 313,5 kPa;
  ACO-1: 299,3 kPa.
- **Fuente (depósito por cota):** presión disponible 0 kPa + carga por cota; presión
  requerida −40,5 kPa (la cota cubre la demanda) → **margen +40,5 kPa**. La carga
  estática del depósito (≈ 30–34 m sobre la red) basta sin bombeo.

## NDP a confirmar por el ICCP `[confirmar AN]`

Dotación 200 l/hab/día · coef. de punta 2,5 · caudal de incendio por hidrante 16,7 l/s
(~1000 l/min) · presión dinámica mínima 250 kPa · banda de velocidad 0,5–2,0 m/s · DN
mínimo 80 mm · rugosidad 0,1 mm (fundición dúctil) · modelo de fuente = depósito por cota.

## Frontera

Lectura IFC + coherencia de red en `iso19650-openbim` (`scripts/mep/`); demanda EN 805 +
solver Darcy en `obras-lineales` (`scripts/red/`), que consume el JSON neutro de red. El
**solver `solver_presion.py` es copia byte a byte** del de `instalaciones`
(`scripts/red/solver_red.py`, PT 4.3/4.4). El núcleo (`scripts/nucleo/`) **no se toca**
(espejo idéntico).
