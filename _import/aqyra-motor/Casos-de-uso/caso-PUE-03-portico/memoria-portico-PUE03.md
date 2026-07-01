# Memoria de cálculo — Pórtico de paso (caso PUE-03)

**Disciplina `puentes` (Ola 7) · vertical pórtico · `motor-fem` C5 (FEM-1).** Documento
de **predimensionado/asistencia**; debe ser **revisado y firmado por técnico competente
(ICCP)**. NDP `[confirmar AN]`.

## 1. Objeto y normativa
Predimensionado de un **pórtico (marco) de paso** monolítico. Normativa: **IAP-11**
(acciones), **EN 1992-1-1** (EC2, hormigón), **EN 1997-1** (EC7, cimentación),
**EN 1990** (combinaciones, AN España).

## 2. Datos
- Geometría: luz L = 10.0 m, altura H = 6.0 m, ancho 10.0 m. Dintel h = 0.90 m,
  pilas h = 0.80 m. Nudos esquina **monolíticos** (rígidos).
- Materiales: hormigón fck = 30 MPa, E = 33 GPa.
- Suelo (cimentación): zapatas corridas B = 2.5 m, Lf = 10 m; resortes Winkler
  kx = 6.0·10⁸, kz = 1.25·10⁹, kry = 6.5·10⁸ N/m; q_adm = 300 kPa, μ = 0.5.
- Relleno: φ = 30° → **K0 = 1 − sin φ = 0.500** (empuje al reposo, marco enterrado),
  γ = 19 kN/m³.
- Cargas: peso propio + g2 = 60 kN/m (relleno/pavimento sobre dintel); LM1 (2 carriles)
  sobre el camino del dintel; empuje de tierras triangular sobre las pilas.

## 3. Modelo de análisis (C5)
**Marco plano XZ** de barras (dintel ne=10, pilas np=6) con la **base sobre resortes**
(Winkler kx/kz/kry) — no apoyos rígidos. `estabilizar_plano=True`. El empuje de
tierras se aplica por segmento de pila como carga uniforme global (presión media ×
ancho); resultante por pila ≈ 1710 kN.

## 4. Cálculo
- **Estático** por casos (G permanentes, E empuje) y **envolventes LM1** sobre el
  dintel y la base de las pilas. **Modal**: f₁ = **4.04 Hz**.
- **2.º orden** (pilas): amplificación aproximada δ = 1/(1 − N_Ed/N_cr) = **1.005**
  (despreciable; pila rígida). P-Δ completo → FEM-3.

## 5. Comprobación EC2 + EC7
| Elemento / comprobación | Aprov. | Estado |
|---|---|---|
| Dintel — flexión ELU | 0.119 | CUMPLE |
| Dintel — cortante por bielas (V_Rd,max) | 0.129 | CUMPLE |
| Pila — flexión con 2.º orden | 0.066 | CUMPLE |
| Cimentación EC7 — hundimiento (σ_max=193 ≤ q_adm=300 kPa) | 0.644 | CUMPLE |
| Cimentación EC7 — deslizamiento | 0.436 | CUMPLE |

**Nota deslizamiento**: en un marco cerrado, los empujes de las dos pilas se
**equilibran a través del dintel**; el deslizamiento se gobierna por la **reacción
horizontal real de la base** (kx·dx), no por el empuje total de una pila.

## 6. Conclusión
**VEREDICTO: CUMPLE** · aprovechamiento máximo **0.644** (gobierna el hundimiento de
la cimentación, EC7). Predimensionado válido a expensas de la revisión por técnico
competente (ICCP).
