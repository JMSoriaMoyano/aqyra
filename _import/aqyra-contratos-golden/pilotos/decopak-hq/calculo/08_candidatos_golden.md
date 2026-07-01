# Decopak HQ — Candidatos a caso golden (para QA + aprobación JM)

> **PROPUESTA — pendiente de verificación QA independiente y firma de JM. Versión de núcleo no anclada (versions.lock=0.0.0).**

- **Rol:** build. Las fichas proponen **oráculo y tolerancia**; los **aprueba JM** (`contratos-golden/`). La QA los ejecuta con su propio oráculo independiente.
- Cada golden registra **procedencia de oráculo y tolerancia**. Origen: plan de cálculo `03` §5.

---

## DEC-A1 — Costilla cassette IPE 160 (flexión + vibración)

| Campo | Valor |
|---|---|
| Caso | Nervio IPE 160 del cassette CLT; flexión ELU y frecuencia propia |
| Entrada | IFC #1857 (IPE 160), L=3,86 m (nervio), w_d=8,80 kN/m; w_k=6,23 kN/m |
| Oráculo | **Analítico cerrado**: M=wL²/8, δ=5wL⁴/384EI, f₁=(π/2)√(EI/mL⁴) + EC5 §7.3 |
| Resultado build | u_M=0,39; δ=2,6 mm; f₁=8,5 Hz (u_vib≈0,94) |
| Tolerancia sugerida | ±2 % en M y δ (analítico vs FEM); ±5 % en f₁ (sensible a masa/rigidez) |
| Por qué | Corazón del caso (voladizo ligero CLT); vibración es el ELS gobernante |
| Riesgo | Modelo de voladizo (ménsula 6,55 vs nervio 3,86) — **decisión de modelo, ver 05 §S-A2** |

## DEC-B1 — Diagonal del Cajón O a compresión (pandeo EC3)

| Campo | Valor |
|---|---|
| Caso | Diagonal SHS 200×10, L=4,3 m, compresión con pandeo (curva b) |
| Entrada | IFC #746 (SHS 200×10); N_Ed=778 kN |
| Oráculo | **Euler/EC3 6.3.1** cerrado (χ curva b) + **PyNite** (celosía articulada) |
| Resultado build | λ̄=0,73; χ=0,78; N_b,Rd=2.004 kN; **u=0,39** |
| Tolerancia | ±3 % en N_b,Rd; ±5 % en N_Ed (depende del reparto de la celosía) |
| Por qué | Barra crítica de cortante de la celosía; pandeo es la comprobación gobernante |

## DEC-B2 — Cordón del Cajón O a flexo-axil (EC3)

| Campo | Valor |
|---|---|
| Caso | Cordón SHS 180×8, axil del par mecánico de la viga-celosía |
| Entrada | IFC #40 (SHS 180×8); N_Ed=409 kN (vano), L_pandeo=3,0 m |
| Oráculo | **PyNite** (celosía con nudos reales) + EC3 6.2/6.3 |
| Resultado build | N_b,Rd=1.600 kN; **u=0,26** |
| Tolerancia | ±5 % (reparto del voladizo entre cordones) |
| Por qué | Reparto del voladizo; valida la idealización de viga-celosía |

## DEC-B4 — Montante del Cajón O (HALLAZGO de arriostramiento)

| Campo | Valor |
|---|---|
| Caso | Montante SHS 120×6, h=9,25 m; pandeo según longitud arriostrada |
| Entrada | IFC #113 (SHS 120×6); N_Ed=250 kN |
| Oráculo | EC3 6.3.1 con L_cr=3,08 m (arriostrado) **vs** L_cr=9,25 m (no arriostrado) |
| Resultado build | arriostrado **u=0,40 ✔** ; no arriostrado **u=2,1 ❌** |
| Tolerancia | binaria (cumple/no) según hipótesis de arriostramiento |
| Por qué | **Punto crítico de decisión:** la seguridad depende del arriostramiento real (ver 06 §S-B1) |

## DEC-E1 — Encepado de pilotes (bielas y tirantes, EC2 §6.5)

| Campo | Valor |
|---|---|
| Caso | Encepado NC-Vest (6 D650) y NC-Lab (4 D450); celosía de bielas-tirantes |
| Entrada | IFC #3686/#3699 (encepados), #3703.. (pilotes); N_Ed=8.300 / 4.400 kN |
| Oráculo | **Analítico (modelo de bielas)**: T=R/tanθ, C=R/sinθ + EC2 §6.5 (biela/nudo) |
| Resultado build | NC-Lab: T=809 kN (18,6 cm²), u_biela=0,24, u_CCT=0,46; NC-Vest: T=864 kN (19,9 cm²) |
| Tolerancia | ±3 % en T/C (geometría); cuantía As redondeada a Ø comercial |
| Por qué | Región D de cimentación; comprobación de referencia EC2 §6.5 |

## DEC-E2 — Pilote D650 (capacidad + asiento, EC7)

| Campo | Valor |
|---|---|
| Caso | Pilote perforado D650, punta UG3 + fuste UG2/UG3 |
| Entrada | IFC #3703 (D650, L=7 m); doc 04 SOCOTEC (punta 1.290 kN, fuste UG2 62/UG3 98 kPa) |
| Oráculo | **Analítico EC7** (R = R_punta + R_fuste; FS aplicado) |
| Resultado build | R_adm≈2.396 kN; N_servicio=988 kN; **u=0,41** |
| Tolerancia | ±5 % (promedio de zona por empotramiento <6D) |
| Por qué | Geotecnia; valida el camino de cargas hasta el terreno |

---

**Resumen:** 6 candidatos (DEC-A1, B1, B2, B4, E1, E2). DEC-B4 se añade a los del plan 03 por ser el **punto de decisión crítico** (arriostramiento del montante). Todos a aprobar por JM con su oráculo y tolerancia antes de promover a CI.

---
**Aviso:** PREDIMENSIONADO. Pendiente de verificación QA independiente + firma de JM.
