# Caso golden DEC-B1 — Diagonal del Cajón O SHS 200×10 (pandeo EC3)

> **Ficha golden** del corpus C6, **valida el contrato C5 v0** (motor-fem / motor de cálculo).
> Golden vN valida C5 vN. **Solo JM** cambia valores esperados o tolerancias (vía PR con traza).

```
id:           DEC-B1
contrato:     C5 v0
proyecto:     Decopak HQ (diagonales "Cajon O diagonal")
estado:       SEMILLA — pendiente de ratificación JM, de identificar el perfil real
              de la diagonal crítica, y de fijar N_Ed con PyNite 3D (P3)
```

## Entrada

```
elemento:     Diagonal del Cajón O, SHS 200×10 (S355), L = 4,3 m
              [AVISO: el IFC tiene 7 perfiles de diagonal — SHS 250×16/250×12/200×10/
               160×8/150×8/120×6/300×16. La ficha verifica SHS 200×10; JM/build deben
               identificar el perfil y la posición de la diagonal CRÍTICA real → DEC-B1.]
norma:        EC3 6.3.1 (pandeo por flexión, curva b, α=0,34) · γ_M1 = 1,05 · S355
```

## Esperado (valores de referencia del oráculo)

| Magnitud | Esperado (oráculo) | Tolerancia | ¿Cumple? |
|---|---|---|---|
| N_b,Rd (SHS 200×10, L=4,3 m) | 1.978 kN | ±3 % | — |
| λ̄ | 0,725 | — | — |
| χ (curva b) | 0,770 | — | — |
| N_Ed (diagonal crítica, FEM nodal, un plano) | ≈ 348 kN | ±5 % | build da 778 kN (conservador) |
| u = N_Ed/N_b,Rd | 0,18 (QA) / 0,39 (build) | — | ≤ 1,0 → cumple |
| Clasificación SHS 200×10 (S355) | Clase 1 | — | (b−3t)/t=17 ≤ 33ε=26,9 |

## Oráculo

```
oraculo:      FEM nodal 2D propio (rigidez directa, numpy) sobre nudos REALES del IFC
              (celosía 2D Vierendeel, 64 nudos, 153 barras) + EC3 6.3.1 cerrado
fuente:       qa/informes/qa_geom_extract.py · qa_truss2d_cajonO.py · qa_normativa.py
              informe qa/informes/QA_DEC-B1.md (2026-06-24)
pendiente:    fijar N_Ed con modelo 3D PyNite (P3); la capacidad N_b,Rd ya está verde
```

## Tolerancia

```
N_b,Rd:  ±3 %
N_Ed:    ±5 %
Tolerancias RATIFICADAS por JM 2026-06-26.
```

## Veredicto de referencia

```
responsable:  JM
veredicto:    APTO (condicionado) — N_b,Rd coincide al 1,3 %; demanda del build conservadora.
              Condición: identificar el perfil real de la diagonal crítica antes de congelar.
```
