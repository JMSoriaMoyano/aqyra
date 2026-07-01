# Informe de QA por cálculo — DEC-E1

> **QA verificado con FEM nodal numpy independiente + analítico. SIN el oráculo PyNite certificado (no instalable en este entorno) → pendiente de RE-EJECUCIÓN en entorno con PyNite para el cierre definitivo. Pendiente de firma de JM (la IA no certifica).**

- **Caso golden:** DEC-E1 — Encepados de pilotes, modelo de bielas y tirantes (EC2 §6.5)
- **Contrato / golden:** C-E1 v0
- **Fecha de verificación:** 2026-06-24
- **Ejecutado por:** agente de QA (ejecución separada) · **Oráculo:** analítico bielas-tirantes (T=R/tanθ) + EC2 §6.5
- **Versión verificada:** **NO ANCLADA**

> La certificación requiere la firma de JM. La IA no firma.

---

## 1. Trazabilidad

```
input:       Encepado NC-Lab (4 D450, planta 2,40×3,0, h=1,2 m), N_Ed=4.400 kN;
             Encepado NC-Vest (6 D650, planta 3,20×7,0, h=1,5 m), N_Ed=8.300 kN
             (N_Ed del reparto del núcleo, ver §5 y DEC-E2/reacciones)
version:     no anclada
norma:       EC2 §6.5 (modelo de bielas y tirantes), B500S γs=1,15, HA-30
metodo QA:   modelo de bielas derivado independiente: d=h−rec−Ø/2, z=0,9d,
             θ=atan(z/(a/2)), T=R/tanθ, A_s=T/f_yd
resultado:   NC-Lab T=811 kN (18,7 cm²); NC-Vest T=860 kN (19,8 cm²)
oraculo:     analítico EC2 §6.5
comparacion: ver §2
```

## 2. Capa 1 — Numérica (oráculo)

| Magnitud | Valor build | Valor QA (oráculo) | Δ | Tolerancia | ¿Dentro? |
|---|---|---|---|---|---|
| NC-Lab — tirante T | 809 kN | 811 kN | +0,2 % | ±3 % | ☑ |
| NC-Lab — A_s requerida | 18,6 cm² | 18,7 cm² | +0,5 % | (Ø comercial) | ☑ → 6Ø20 (18,8) |
| NC-Lab — θ biela | 53,7° | 53,6° | — | — | ☑ |
| NC-Vest — tirante T | 864 kN | 860 kN | −0,5 % | ±3 % | ☑ |
| NC-Vest — A_s requerida | 19,9 cm² | 19,8 cm² | −0,5 % | (Ø comercial) | ☑ → 7Ø20 (22,0) |
| u_CCT (nudo NC-Lab) | 0,46 | ≈0,46 | — | — | ☑ |

**Verificaciones sin oráculo:** equilibrio del nudo bielas-tirantes (ΣV: R = C·sinθ) ☑ · geometría consistente con canto y separación de pilotes del IFC ☑.

## 3. Capa 2 — Normativa

| Comprobación | Límite | Valor QA | ¿Cumple? |
|---|---|---|---|
| Tirante: A_s ≥ T/f_yd a Ø comercial | — | 6Ø20 (Lab), 7Ø20 (Vest) | ☑ |
| Biela: σ_c ≤ σ_Rd,max=0,6·ν'·f_cd=10,56 MPa | ≤ 10,56 | 2,55 (Lab) / 1,12 (Vest) → u=0,24/0,11 | ☑ |
| Nudo CCT: σ ≤ 0,85·ν'·f_cd=14,96 MPa | ≤ 14,96 | u=0,46 (Lab) / 0,28 (Vest) | ☑ |

## 4. Capa 3 — Regresión

- ¿Promovido a golden congelado? ☐ Sí ☑ Pendiente firma JM (capa numérica y normativa en verde).

## 5. Observaciones / supuestos del build puestos a prueba

- El modelo de bielas se reproduce con exactitud (Δ ≤ 0,5 %). La geometría (canto, separación de pilotes, θ) es coherente con el IFC.
- **Dependencia de S-D1 (reparto de carga al núcleo):** las cargas N_Ed=4.400/8.300 kN proceden del reparto 35/65 del build. Mi **FEM nodal del Cajón O confirmó el reparto ≈35 % NC-Lab / 65 % NC-Vest** (ver DEC-E2 §5 y resumen), así que las cargas de entrada del encepado están bien fundadas. **No obstante**, la carga vertical total del núcleo (≈12.700 kN ELU) la estima el build por áreas tributarias de forjado; QA no recalculó la bajada de cargas completa del edificio (fuera del alcance del Cajón O), por lo que la **magnitud absoluta** de N_Ed queda pendiente de la verificación global con PyNite.

## 6. Veredicto de QA

> **APTO** — el modelo de bielas y tirantes (T, θ, biela, nudo CCT) coincide con el build dentro del ±3 % en ambos encepados; armaduras a Ø comercial correctas. Reserva: la magnitud absoluta de N_Ed depende de la bajada de cargas global (a confirmar con el modelo PyNite del edificio completo); el **reparto** 65/35 sí está verificado.

## 7. Firma (segunda llave — JM)

```
Verificado por QA:   agente QA / run 2026-06-24      fecha: 2026-06-24
Tolerancias fijadas por JM:  ☐
FIRMA JM (técnico competente): ______________  fecha: [   ]   → CERTIFICADO ☐
```

*Scripts QA: `qa/informes/qa_normativa.py` (bielas-tirantes), `qa/informes/qa_truss2d_cajonO.py` (reparto a muros 65/35).*
