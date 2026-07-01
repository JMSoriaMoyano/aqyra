# Caso golden DEC-E1 — Encepados de pilotes, bielas y tirantes (EC2 §6.5)

> **Ficha golden** del corpus C6, **valida el contrato C5 v0** (motor-fem / motor de cálculo).
> Golden vN valida C5 vN. **Solo JM** cambia valores esperados o tolerancias (vía PR con traza).

```
id:           DEC-E1
contrato:     C5 v0
proyecto:     Decopak HQ (encepados NC-Lab y NC-Vest)
estado:       SEMILLA — pendiente de ratificación JM; magnitud absoluta de N_Ed sujeta
              a la bajada de cargas global (a confirmar con PyNite, P3). El reparto 65/35
              SÍ está verificado por el FEM nodal.
```

## Entrada

```
elemento:     Encepado NC-Lab — 4 pilotes D450, planta 2,40×3,0 m, canto h=1,2 m. N_Ed=4.400 kN
              Encepado NC-Vest — 6 pilotes D650, planta 3,20×7,0 m, canto h=1,5 m. N_Ed=8.300 kN
              (N_Ed del reparto 35/65 del núcleo; ver DEC-E2 §5)
norma:        EC2 §6.5 (modelo de bielas y tirantes) · B500S γ_s=1,15 · HA-30
metodo:       d=h−rec−Ø/2 · z=0,9d · θ=atan(z/(a/2)) · T=R/tanθ · A_s=T/f_yd
```

## Esperado (valores de referencia del oráculo)

| Magnitud | Esperado (oráculo) | Tolerancia | Armado a Ø comercial |
|---|---|---|---|
| NC-Lab — tirante T | 811 kN | ±3 % | A_s=18,7 cm² → 6Ø20 (18,8) |
| NC-Lab — θ biela | 53,6° | — | — |
| NC-Lab — u_CCT (nudo) | ≈0,46 | — | ≤ 1,0 → cumple |
| NC-Vest — tirante T | 860 kN | ±3 % | A_s=19,8 cm² → 7Ø20 (22,0) |
| Biela σ_c ≤ σ_Rd,max=10,56 MPa | 2,55 (Lab) / 1,12 (Vest) | — | u=0,24/0,11 → cumple |
| Nudo CCT σ ≤ 0,85·ν'·f_cd=14,96 MPa | u=0,46 (Lab) / 0,28 (Vest) | — | cumple |

## Oráculo

```
oraculo:      analítico bielas-tirantes (EC2 §6.5) derivado independiente
fuente:       qa/informes/qa_normativa.py (bielas-tirantes)
              qa_truss2d_cajonO.py (reparto a muros 65/35)
              informe qa/informes/QA_DEC-E1.md (2026-06-24)
pendiente:    magnitud absoluta de N_Ed depende de la bajada de cargas global (PyNite, P3)
```

## Tolerancia

```
T (tirante):  ±3 %
A_s:          a Ø comercial
Tolerancias RATIFICADAS por JM 2026-06-26.
```

## Veredicto de referencia

```
responsable:  JM
veredicto:    APTO — modelo de bielas y tirantes coincide con el build dentro del ±3 % en
              ambos encepados; armaduras a Ø comercial correctas. Reserva: magnitud absoluta
              de N_Ed sujeta a la bajada de cargas global del edificio (PyNite).
```
