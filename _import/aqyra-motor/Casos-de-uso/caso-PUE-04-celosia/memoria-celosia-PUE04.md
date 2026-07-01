# Memoria de cálculo — Celosía de acero (caso PUE-04)

**Disciplina `puentes` (Ola 7) · vertical celosía · `motor-fem` C5 (FEM-1).** Documento
de **predimensionado/asistencia**; debe ser **revisado y firmado por técnico competente
(ICCP)**. NDP `[confirmar AN]`.

## 1. Objeto y normativa
Predimensionado de una **celosía de acero** (tipo Pratt) de tablero inferior. Normativa:
**IAP-11** (acciones), **EN 1993-1-1** (EC3, acero: tracción y pandeo de barras),
**EN 1993-1-9** (fatiga — diferida), **EN 1990** (combinaciones, AN España).

## 2. Datos
- Geometría: luz L = 40.0 m, canto h = 5.0 m, **8 paneles** (panel 5.0 m). Cordones
  inferior (tablero) y superior, montantes y diagonales Pratt.
- Material: acero **S355** (fy = 355 MPa, E = 210 GPa, ρ = 7850 kg/m³).
- Secciones: cordones A = 220 cm²; diagonales A = 120 cm²; montantes A = 115 cm²
  (extremos dimensionados para la reacción de apoyo).
- Cargas: permanente del tablero g = 42 kN/m (incluye peso propio simplificado de la
  celosía) en los nudos del cordón inferior; LM1 (2 carriles) sobre el cordón inferior.

## 3. Modelo de análisis (C5)
Celosía plana XZ de **barras articuladas** (`tipo:"articulado"` → solo axil).
Modelo 2D puro: `estabilizar_plano=True` + se coacciona **RY** en todos los nudos
(las barras articuladas dejarían RY singular). Apoyos isostáticos en los extremos del
cordón inferior.

## 4. Cálculo
- **Estático** (G) → axiles por barra. **Cargas móviles / líneas de influencia**
  (FEM-1): **envolventes del axil** (N) de cordones, diagonales y montantes por paso
  del tren LM1. **Modal**: f₁ = **2.64 Hz**.
- Axiles de diseño (ELU): cordón inferior centro ≈ **+6343 kN** (tracción); cordón
  superior centro ≈ **−6750 kN** (compresión); diagonal de apoyo ≈ **+4198 kN**.

## 5. Comprobación EC3 (barra crítica `D_0`)
| Comprobación | Valor | Estado |
|---|---|---|
| Tracción N_t,Rd = A·fy/γM0 (diagonal de apoyo D_0) | aprov 0.985 | CUMPLE |
| Compresión + pandeo N_b,Rd = χ·A·fy/γM1 (curva b) | aprov < 0.99 | CUMPLE |
| Uniones (resistencia completa de barra) | — | CUMPLE |
| **Fatiga (EN 1993-1-9)** | **gancho diferido** | pendiente PT fatiga |

## 6. Conclusión
**VEREDICTO: CUMPLE** · aprovechamiento máximo **0.985** (gobierna la diagonal de
apoyo en tracción). La **fatiga** (LM3 + categorías de detalle + daño Palmgren-Miner)
queda como gancho diferido a un PT específico. Predimensionado válido a expensas de la
revisión por técnico competente (ICCP).
