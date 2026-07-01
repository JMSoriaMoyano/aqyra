# Informe de QA por cálculo — DEC-B2

> **QA verificado con FEM nodal numpy independiente + analítico. SIN el oráculo PyNite certificado (no instalable en este entorno) → pendiente de RE-EJECUCIÓN en entorno con PyNite para el cierre definitivo. Pendiente de firma de JM (la IA no certifica).**

- **Caso golden:** DEC-B2 — Cordón del Cajón O SHS 180×8 (flexo-axil EC3)
- **Contrato / golden:** C-B2 v0
- **Fecha de verificación:** 2026-06-24
- **Ejecutado por:** agente de QA (ejecución separada) · **Oráculo:** FEM nodal 2D propio (numpy) + EC3 6.2/6.3
- **Versión verificada:** **NO ANCLADA**

> La certificación requiere la firma de JM. La IA no firma.

---

## 1. Trazabilidad

```
input:       IFC #40 SHS 180×8 (A=55,0 cm², i=7,03 cm); cordones L=40,86 m por nivel,
             4 niveles Z=5,75/8,833/11,917/15; L_pandeo=paso de montantes ≈3,0 m
version:     no anclada
norma:       EC3 6.2.4 (compresión), 6.3.1 (pandeo curva b), γM0=γM1=1,05; S355
metodo QA:   FEM nodal 2D (rigidez directa) con nudos reales + EC3 cerrado independiente
resultado:   N_c,Rd=1.861 kN; N_b,Rd=1.595 kN; N_Ed,QA≈330 kN (un plano); u_QA≈0,21
oraculo:     FEM propio + EC3; equilibrio y sólido rígido verificados
comparacion: ver §2
```

## 2. Capa 1 — Numérica (oráculo)

| Magnitud | Valor build | Valor QA (oráculo) | Δ | Tolerancia | ¿Dentro? |
|---|---|---|---|---|---|
| N_b,Rd (SHS 180×8, L=3,0 m) | 1.600 kN | 1.595 kN | −0,3 % | ±5 % | ☑ |
| λ̄ | 0,56 | 0,559 | −0,2 % | — | ☑ |
| χ | 0,86 | 0,857 | −0,3 % | — | ☑ |
| N_Ed (cordón) | 409 kN | ≈330 kN (FEM nodal, un plano) | −19 % | ±5 % | ☒ (build conservador) |
| u = N_Ed/N_b,Rd | 0,26 | 0,21 (QA) / 0,26 (build) | — | — | ambos ✔ |

**Verificaciones sin oráculo:** equilibrio ΣF (residuo 1,6e-12 kN) ☑ · sólido rígido = 3 ☑ · convergencia n/a.

> **Reparto de axiles (§S-D1).** El build calcula N_cordón = M_global/(z·n_planos) con la viga-celosía biapoyada equivalente (L=27 m + voladizos), z=9,25 m, 2 planos → 409 kN. Mi FEM nodal da ≈330 kN en el cordón más solicitado (por plano). El build es **conservador** (+19 %). La capacidad N_b,Rd coincide al 0,3 %.

## 3. Capa 2 — Normativa

| Comprobación | Límite | Valor QA | ¿Cumple? |
|---|---|---|---|
| Clasificación SHS 180×8 (S355) | Clase 1 | Clase 1 ((180−24)/8=19,5 ≤ 26,9) | ☑ |
| Compresión + pandeo u ≤ 1,0 | ≤ 1,0 | 0,21 (QA) / 0,26 (build) | ☑ |

## 4. Capa 3 — Regresión

- ¿Promovido a golden congelado? ☐ Sí ☑ Pendiente (verde; fijar N_Ed con PyNite 3D).

## 5. Observaciones / supuestos del build puestos a prueba

- **Idealización de viga-celosía validada:** el reparto del par mecánico (cordones a ±N, brazo z=canto) es consistente con el FEM. El build queda del lado de la seguridad en la demanda.
- El cordón es **continuo de 40,86 m por nivel** en el IFC; la celosía solo se materializa al subdividirlo en los nudos de montantes/diagonales — QA lo hizo (subdivisión por intersección) para resolver la celosía con conectividad real.

## 6. Veredicto de QA

> **APTO** — N_b,Rd coincide al 0,3 % (dentro de ±5 %); la demanda del build (409 kN) es conservadora frente al FEM nodal (≈330 kN). Aprovechamiento holgado (u≈0,2–0,26).

## 7. Firma (segunda llave — JM)

```
Verificado por QA:   agente QA / run 2026-06-24      fecha: 2026-06-24
Tolerancias fijadas por JM:  ☐
FIRMA JM (técnico competente): ______________  fecha: [   ]   → CERTIFICADO ☐
```

*Scripts QA: `qa/informes/qa_truss2d_cajonO.py`, `qa/informes/qa_normativa.py`.*
