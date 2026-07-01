# Índice de casos de uso de puentes (PUE)

Casos de la disciplina `puentes` (Ola 7). Los **PUE-01…06** son paramétricos
(`entrada_caso.json` tecleado; PT 7.1–7.3). Los **PUE-07…16** son **IFC-driven**
(PT 7.3.1) y **PUE-17** es el primer **avanzado** (PT 7.4, cajón postesado sobre FEM-2):
arrancan de un IFC4X3, lo leen con el lector estructural
(`ifc_to_model_estructural.py` en C1 + `desde_ifc.py` en puentes) y recorren
idealización → motor-fem → IAP-11 → comprobación EC → memoria + write-back al IFC.

> Todo es predimensionado/asistencia; debe ser revisado y firmado por técnico
> competente (ICCP). NDP marcados [confirmar AN].

## Paramétricos (PT 7.1–7.3) — referencia de round-trip

| # | Tipología | Veredicto | Aprov. máx |
|---|---|---|---|
| PUE-01 | Vigas pretensadas (emparrillado) | CUMPLE | 0,813 |
| PUE-02 | Losa postesada (lámina DKMQ) | CUMPLE | 0,967 |
| PUE-03 | Pórtico (marco) | CUMPLE | 0,644 |
| PUE-04 | Celosía | CUMPLE | 0,985 |
| PUE-05 | Pila + apoyo + cimentación | CUMPLE | 0,785 |
| PUE-06 | Estribo (Ka activo) | CUMPLE | 0,971 |

## IFC-driven (PT 7.3.1) — los 10 casos

Orden por reuso creciente: (1) cimentación/estribo → (2) pila+apoyo → (3) tablero →
(4) integrado. Cada caso: `caso-PUE-NN.ifc` (entrada) · `entrada_caso_desde_ifc.json`
(reconstruido por el lector) · `resultado.json` · `mapping_resultado_ifc.json` ·
`PUE-NN-resultados.ifc` (write-back) · `memoria-PUE-NN.md` · `README.md`.

| # | Caso | Vertical(es) | Veredicto | Aprov. máx | Demuestra |
|---|---|---|---|---|---|
| PUE-07 | Paso superior vigas artesa | vigas pretensadas | CUMPLE | 0,807 | lector tablero + sección artesa (cajón con huecos) |
| PUE-08 | Losa postesada ancha de un vano | losa postesada | CUMPLE | 0,999 | lector lámina + objetivo esfuerzo_lamina |
| PUE-09 | Marco de paso inferior | pórtico | CUMPLE | 0,738 | lector marco + empuje K0 + resortes |
| PUE-10 | Pasarela peatonal en celosía | celosía | CUMPLE | 0,584 | lector celosía + modal (confort) |
| PUE-11 | Pila alta esbelta sobre 4 pilotes | pila + pilotes | CUMPLE | 0,893 | lector pila + reuso parser pilotes (2.º orden) |
| PUE-12 | Pila sobre encepado de 2 pilotes | pila + encepado | CUMPLE | 0,563 | lector pila + reuso biela-tirante (encepado) |
| PUE-13 | Estribo cerrado integral | estribo | CUMPLE | 0,912 | reuso muro + selector K0 (reposo) |
| PUE-14 | Estribo abierto alto, gran sobrecarga | estribo | CUMPLE | 0,999 | reuso muro + Ka activo + sobrecarga |
| PUE-15 | Puente completo integrado | todos (acoplado) | CUMPLE | 0,836 | cadena tablero→apoyo→pila/estribo→cimentación en un IFC |
| PUE-16 | Rediseño (NO CUMPLE → CUMPLE) | estribo | v1 **NO CUMPLE** 3,164 → v2 **CUMPLE** 0,971 | la herramienta detecta el fallo y guía el ajuste |

## Avanzados (PT 7.4–7.5) — FEM-2

| # | Caso | Vertical(es) | Veredicto | Aprov. máx | Demuestra |
|---|---|---|---|---|---|
| PUE-17 | Cajón postesado de 3 vanos | cajón (lámina pura) | CUMPLE | 0,754 | **FEM-2**: lámina curva MITC4 + diafragmas-rigidizadores; postesado evolutivo por fases; EC2 con cortante+torsión de Bredt y *shear lag*; lector tipología `cajon` |
| PUE-18 | Tablero mixto acero-hormigón (4 jácenas) | mixto (lámina rigidizada) | CUMPLE | 0,755 | **FEM-2**: losa de láminas + viga de acero como **rigidizador offset** (interacción completa); **EC3** clase 1-4 + abolladura **EN 1993-1-5**, **EC4** M_pl mixto + conexión, **fatiga EN 1993-1-9** (FLM3); lector tipología `mixto` |
| PUE-19 | Tablero oblicuo, esviaje 30° | oblicuo (malla romboidal) | CUMPLE | 0,949 | **FEM-2**: malla que sigue la línea de apoyo esviada; **reparto 2D** + **concentración en la esquina obtusa** (×6,2); EC2 armado de losa; lector tipología `oblicuo` |
| PUE-20 | Tablero curvo en planta, R = 200 m | curvo (lámina sobre Alignment) | CUMPLE | 0,666 | **FEM-2**: malla sobre la directriz curva; **torsión acoplada** a la flexión (`dT/ds=M/R`) por **Bredt**; EC2 con torsión protagonista; lector tipología `curvo` |

## Validación del lector — round-trip paramétrico ↔ IFC

Las 6 tipologías reproducen el resultado del caso paramétrico equivalente al
regenerar el IFC y releerlo (arnés `roundtrip_all`):

| Tipología | Dif. relativa | Tipología | Dif. relativa |
|---|---|---|---|
| Vigas pretensadas | 0,0 | Celosía | 0,0 |
| Losa postesada | 0,0 | Pila | 3,6 × 10⁻⁷ |
| Pórtico | 1,1 × 10⁻⁶ | Estribo | 0,0 |

Máximo 1,1 × 10⁻⁶, muy dentro de las tolerancias (geometría 1 × 10⁻⁶; aprovechamientos
1 × 10⁻³). La plantilla de documentación IFC-driven está en
`caso-PUE-05-pila-cimentacion/README-IFC-driven.md`.

## Decisión de sección bajo "geometría extruida real"

Las dimensiones y A, Iy, Iz se leen de la geometría extruida real (rectángulo/círculo
exactos; cajón/artesa por `IfcArbitraryProfileDefWithVoids` con A, Iy, Iz exactos del
polígono). La constante de torsión J se deriva de la geometría (pared delgada), por lo
que puede diferir ~% de un J abstracto; gobierna torsión, no flexión. Los datos NO
geométricos (fck, pretensado, rigideces de suelo/apoyo, reacciones, q_adm) viajan en
`Pset_Estructurando_*`.
