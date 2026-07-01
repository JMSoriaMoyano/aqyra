# Memoria de cálculo — Tablero losa postesada (caso PUE-02)

**Disciplina `puentes` (Ola 7) · vertical losa postesada · `motor-fem` C5 (FEM-1) +
extensión v0.2.1 (`esfuerzo_lamina`).** Documento de **predimensionado/asistencia**;
debe ser **revisado y firmado por técnico competente (ICCP)**. NDP `[confirmar AN]`.

## 1. Objeto y normativa
Predimensionado de un tablero de **losa postesada** de un vano. Normativa: **IAP-11**
(acciones), **EN 1992-1-1/-2** (EC2, hormigón y postesado §5.10), **EN 1990** (bases
y combinaciones, AN España).

## 2. Datos
- Geometría: luz L = 14.0 m, ancho B = 9.0 m, canto t = 0.70 m. Apoyos simples en
  estribos (líneas). Vigas de borde. Calzada de 2 carriles inset (bordillos).
- Materiales: hormigón fck = 40 MPa (fck(t) = 28 MPa en transferencia), E = 34 GPa.
- Postesado biaxial (P∞, pérdidas simplificadas 18 %): banda en X (vano) con
  drape 0.45 m, distribuido en Y con drape 0.18 m; Ap_x ≈ 8 cm²/m; armadura pasiva
  de fondo As ≈ 13 cm²/m.
- Cargas: g1 (peso propio ρ·g·t), g2 = 3.0 kN/m² (pavimento). LM1 (tándem 2×300/200
  kN + UDL) por carril, **cada eje modelado con dos líneas de rueda** (2.0 m, media
  carga) → barrido móvil.

## 3. Modelo de análisis (C5)
Malla estructurada **14 × 9 de láminas DKMQ** (`motor-fem`), con ρ para el modal. La
**membrana se bloquea** (DX, DY, RZ): la precompresión del postesado se trata
**analíticamente** (σcp = P/t); la placa trabaja a flexión (reparto biaxial + LM1).
El postesado entra como **carga equivalente** hacia arriba (balance de cargas 2D,
`balance_2d`): w_p = w_px + w_py = **20.21 kN/m²**, que equilibra la carga permanente
(20.17 kN/m²) prácticamente al 100 %.

## 4. Cálculo
- **Estático** por casos (G1, G2, P) → momentos de placa Mx (vano) por franja.
- **Cargas móviles / líneas de influencia** (FEM-1, **objetivo `esfuerzo_lamina`**):
  envolventes LM1 de Mx en la franja central de vano.
- **Modal**: frecuencia fundamental **f₁ = 6.43 Hz**.

## 5. Comprobación EC2 (franja crítica de vano `Q_6_4`)
| Comprobación | Aprov. | Estado |
|---|---|---|
| Compresión en transferencia (P0+g1) | 0.196 | CUMPLE |
| Tracción en transferencia (fibra sup) | 0.042 | CUMPLE |
| Compresión en servicio (fibra sup) | 0.248 | CUMPLE |
| Tracción en servicio (fibra inf) | 0.964 | CUMPLE |
| Descompresión cuasipermanente | 0.000 | CUMPLE |
| Flexión ELU de vano (M_Ed=1027 ≤ M_Rd=1062 kNm/m) | 0.967 | CUMPLE |

**Térmica**: en losa de un vano (isostática) el gradiente es libre → momento de
restricción ≈ 0 (se documenta). **Punzonamiento**: N/A (apoyos lineales en estribos).

## 6. Conclusión
**VEREDICTO: CUMPLE** · aprovechamiento máximo **0.967** (gobierna la flexión ELU de
vano, seguida de la tracción en servicio). Predimensionado válido a expensas de la
revisión por técnico competente (ICCP).
