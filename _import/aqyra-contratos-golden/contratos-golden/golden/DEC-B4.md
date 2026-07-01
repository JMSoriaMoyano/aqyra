# Caso golden DEC-B4 — Montante del Cajón O SHS 120×6 (pandeo según arriostramiento) · CRÍTICO

> **Ficha golden** del corpus C6, **valida el contrato C5 v0** (motor-fem / motor de cálculo).
> Golden vN valida C5 vN. **Solo JM** cambia valores esperados o tolerancias (vía PR con traza).

```
id:           DEC-B4
contrato:     C5 v0
proyecto:     Decopak HQ (IFC #113, montante vertical del Cajón O)
estado:       SEMILLA — pendiente de DECISIÓN DE JM sobre arriostramiento (planos de
              detalle) y de revisar N_Ed del montante en el build
```

## Entrada

```
elemento:     Montante vertical del Cajón O, SHS 120×6 (S355). A=27,4 cm², i=4,61 cm.
              Altura h=9,25 m (Z=5,75→15,0). Nudos REALES en Z=5,75/8,833/11,917/15,0
              (los cordones cruzan el montante y lo dividen en 3 segmentos de ≈3,08 m).
norma:        EC3 6.3.1 (pandeo curva b) · γ_M1=1,05 · S355
```

## Esperado (valores de referencia del oráculo) — veredicto BINARIO según L_cr

| Escenario | L_cr | λ̄ | χ | N_b,Rd | u (build N=250) | u (QA FEM N=392) | Veredicto |
|---|---|---|---|---|---|---|---|
| **Arriostrado por planta** | **3,08 m** | 0,87 | 0,684 | **632 kN** | 0,40 | **0,62** | **CUMPLE** |
| No arriostrado | 9,25 m | 2,60 | 0,130 | 120 kN | 2,08 | 3,26 | NO CUMPLE |

```
clave golden:  L_cr = 3,08 m  (CONFIRMADO por la conectividad real del IFC, no asumido)
               N_b,Rd = 632 kN   (tolerancia ±5 %)
               N_Ed = ≈392 kN (FEM nodal real)  > 250 kN (estimación tributaria del build)
```

## Oráculo

```
oraculo:      FEM nodal 2D propio con conectividad real (determina L_cr por los nudos) + EC3
fuente:       qa/informes/qa_geom_extract.py (nudos/conectividad del montante)
              qa_truss2d_cajonO.py (L_cr y N_Ed nodal) · qa_normativa.py (EC3 ambos escenarios)
              informe qa/informes/QA_DEC-B4.md (2026-06-24)
pendiente:    confirmación de coacción lateral cada 3,08 m en planos de detalle (JM)
```

## Tolerancia

```
N_b,Rd:  ±5 %
N_Ed:    ±5 %   (build debe revisar: 392 kN nodal vs 250 kN tributario, +57 %)
Tolerancias RATIFICADAS por JM 2026-06-26.
```

## Veredicto de referencia y decisión pendiente (DEC-B4)

> **APTO (condicionado).** Con el arriostramiento por planta confirmado por la geometría real
> (L_cr=3,08 m) el montante cumple: u=0,62 con la demanda nodal real, 0,40 con la del build.
> **Decisiones para JM:**
> 1. Confirmar en planos de detalle que las uniones cordón–montante–diagonal–forjado
>    materializan la coacción lateral cada 3,08 m. Si NO se materializa (L_cr=9,25 m): u≥2 → **NO APTO**.
> 2. Devolución a build: revisar N_Ed del montante (FEM nodal ≈392 kN > 250 kN); u real = 0,62, no 0,40.

```
responsable:  JM
veredicto:    APTO (condicionado a decisión de arriostramiento de JM)
```
