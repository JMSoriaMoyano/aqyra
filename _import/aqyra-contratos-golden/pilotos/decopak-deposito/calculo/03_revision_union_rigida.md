# 03 · Revisión — unión rígida muro-losa: cajón monolítico y cubierta como placa 2D

**Decopak · depósito enterrado** · Rev. sobre `02_acciones_y_calculo.md` · 2026-06-24
**Estado: PROPUESTA pendiente de verificación QA + firma de JM.**

> **Histórico de la revisión.** Una primera versión (Rev.01) tomó el momento de **vano** de la placa
> con bordes perfectamente empotrados (308) y el de **esquina** del pórtico con muro flexible (352).
> La **QA independiente lo marcó ROJO**: son dos modelos de rigidez incompatibles (un balancín — si
> la esquina baja a ~250 por la flexibilidad del muro, el vano sube). Esta Rev.02 lo corrige con un
> **único modelo consistente** (placa 2D con muelles rotacionales de borde = rigidez real del muro).

## Motivo del cambio (instrucción de JM)

La vinculación de la cubierta pasa de **bi-apoyada** a **unión rígida (monolítica)** muro-losa. El
conjunto solera–muros–cubierta trabaja como **cajón cerrado** y la cubierta es una **placa 2D
bidireccional** continua con los muros, igual que la solera.

## Modelo único consistente (Rev.02)

**Placa 2D de Kirchhoff (FEM ACM)** del panel de cubierta (10,87 × 18,0 m), con los bordes apoyados
en los muros mediante **muelles rotacionales** de rigidez `k = 4·E·I_muro/H_muro` (la rigidez real
del muro empotrado en la solera), tándem IAP-11 repartido en huella. Un único modelo → el par
vano/apoyo es coherente. *Acotación de sensibilidad* barriendo la rigidez del muro:

| Rigidez de borde | Vano m_x | Vano m_y | Apoyo m_x |
|---|---|---|---|
| k = 2·EI/H (muro flexible) | +487 | +287 | −167 |
| **k = 4·EI/H (nominal)** | **+440** | **+261** | **−249** |
| k = 6·EI/H (muro rígido) | +413 | +245 | −298 |

El pórtico cerrado transversal (modelo auxiliar) confirma el equilibrio en la esquina
(M_cubierta = M_muro). El FEM de placa se validó contra Timoshenko (placa empotrada): error 0,2 %.

## Efecto de la unión rígida (cubierta) — valores consistentes

| Magnitud | Bi-apoyada | **Cajón monolítico (consistente)** | |
|---|---|---|---|
| Momento de **vano** (tracción inf.) | 923,9 | **440** kN·m/m (m_x) · 261 (m_y) | ↓ 52 % |
| Momento de **apoyo/esquina** (tracción sup.) | 0 | **249** kN·m/m (rango 167–298) | nuevo → armado superior |
| Momento de **cabeza de muro** | 0 | **249** kN·m/m (= esquina, continuidad) | nuevo → armado exterior |

> Nota: la reducción del vano es menor que la que sugería la Rev.01 (308): la flexibilidad real del
> muro relaja la esquina **y** sube el vano. Aun así, la unión rígida sigue siendo favorable frente a
> la bi-apoyada (923,9 → 440).

## Armado y comprobaciones (Rev.02, modelo único)

| Elemento · comprobación | M_Ed (kN·m/m) | Armado | M_Rd | η | w_k | Veredicto |
|---|---|---|---|---|---|---|
| Cubierta · **vano inferior** (dir. corta) | 440 | **φ25/150 (32,7)** | 823 | 0,53 | **0,169** | CUMPLE |
| Cubierta · vano inferior (dir. larga) | 261 | φ20/200 (15,7) | 382 | 0,68 | — | CUMPLE |
| Cubierta · **apoyo superior** sobre muros | 249–298 | φ20/150 (20,9) | 526 | 0,57 | — | CUMPLE |
| Muro · **cabeza/esquina** (cara exterior) | 249–298 | φ25/200 (24,5) | 427 | 0,70 | 0,128 | CUMPLE |
| Muro · base (empotr. en solera) | 92 | φ20/200 (15,7) | 274 | 0,34 | — | CUMPLE |
| Muro · paramento (agua/tierras) | 95 | φ20/200 (15,7) | 274 | 0,35 | 0,144 | CUMPLE |
| Solera (raft) · vano y esquina | 133 | φ20/175 (18,0) | 383 | 0,35 | 0,179 | CUMPLE |
| Cubierta · punzonamiento (rueda 150 kN) | — | — | — | 0,06 | — | CUMPLE |

**Aprovechamiento máximo: 0,70** (cabeza del muro). Todos los elementos ≤ 1.

> **Vano de cubierta — fisuración (gate G4):** el armado inferior se dimensiona a **φ25/150** porque
> la cara inferior de la cubierta puede estar en contacto con el agua (Clase 1, w_k ≤ 0,20 → 0,169 ✅).
> Si se confirma **resguardo de lámina libre** (cara no mojada, exposición XC, w_k ≤ 0,30), bastaría
> **φ20/150** (util 0,83, w_k 0,30). Decisión de JM.

## Lectura del cambio

La unión rígida es **favorable**: el armado inferior de la cubierta baja de φ25/100 (bi-apoyada) a
φ25/150–φ20/150, el reparto bidireccional alivia el vano y el aprovechamiento máximo baja a 0,70. El
coste es **armadura superior nueva sobre los muros (φ20/150)** y **mayor armadura en la cara exterior
de la cabeza de los muros (φ25/200)**.

## Trazabilidad y QA

Scripts: `calc_v3_placa_consistente.py` (placa 2D con muelle rotacional = rigidez muro, modelo único),
`calc_v2_porticocerrado.py` (pórtico cerrado auxiliar), `calc_v2_placa2d.py` (placa empotrada, cota
superior). La **QA independiente** verificó el cajón y marcó ROJO la incoherencia de la Rev.01
(`qa/informes/QA_cajon_monolitico_decopak_2026-06-24.md`); esta Rev.02 **incorpora su corrección**
(modelo único, par vano/apoyo consistente). **Debe re-verificarse la Rev.02** antes de la firma.
Candidato golden **G-DEP-05**: «cubierta como placa 2D con rigidez de muro real».
