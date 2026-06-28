# Caso golden DEC-B2 — Cordón del Cajón O SHS 180×8 (compresión + pandeo EC3)

> **Ficha golden** del corpus C6, **valida el contrato C5 v0** (motor-fem / motor de cálculo).
> Golden vN valida C5 vN. **Solo JM** cambia valores esperados o tolerancias (vía PR con traza).

```
id:           DEC-B2
contrato:     C5 v0
proyecto:     Decopak HQ (IFC #40, cordones del Cajón O)
estado:       SEMILLA — pendiente de ratificación JM y de fijar N_Ed con PyNite 3D (P3)
```

## Entrada

```
elemento:     Cordón del Cajón O, SHS 180×8 (S355). A=55,0 cm², i=7,03 cm.
              Cordones continuos L=40,86 m por nivel (Z=5,75/8,833/11,917/15,0);
              L_pandeo = paso de montantes ≈ 3,0 m.
norma:        EC3 6.2.4 (compresión) · 6.3.1 (pandeo curva b) · γ_M0=γ_M1=1,05 · S355
```

## Esperado (valores de referencia del oráculo)

| Magnitud | Esperado (oráculo) | Tolerancia | ¿Cumple? |
|---|---|---|---|
| N_b,Rd (SHS 180×8, L=3,0 m) | 1.595 kN | ±5 % | — |
| λ̄ | 0,559 | — | — |
| χ (curva b) | 0,857 | — | — |
| N_Ed (cordón más solicitado, FEM nodal, un plano) | ≈ 330 kN | ±5 % | build da 409 kN (conservador, +19 %) |
| u = N_Ed/N_b,Rd | 0,21 (QA) / 0,26 (build) | — | ≤ 1,0 → cumple |
| Clasificación SHS 180×8 (S355) | Clase 1 | — | (180−24)/8=19,5 ≤ 26,9 |

## Oráculo

```
oraculo:      FEM nodal 2D propio (rigidez directa, numpy) con nudos reales + EC3 cerrado
fuente:       qa/informes/qa_truss2d_cajonO.py · qa_normativa.py
              informe qa/informes/QA_DEC-B2.md (2026-06-24)
pendiente:    fijar N_Ed con modelo 3D PyNite (P3); la capacidad N_b,Rd ya está verde
```

## Tolerancia

```
N_b,Rd:  ±5 %
N_Ed:    ±5 %
Tolerancias RATIFICADAS por JM 2026-06-26.
```

## Veredicto de referencia

```
responsable:  JM
veredicto:    APTO — N_b,Rd coincide al 0,3 %; demanda del build (409 kN) conservadora
              frente al FEM nodal (≈330 kN). Aprovechamiento holgado (u≈0,2–0,26).
```
