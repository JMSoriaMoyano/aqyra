# Memoria de cálculo — PUE-18: Tablero mixto acero-hormigón

**Ola 7 · PT 7.5 · FEM-2.** Predimensionado/asistencia. **A revisar y firmar por
técnico competente (ICCP).** NDP: `[confirmar AN]`.

## 1. Objeto y normativa
Tablero mixto acero-hormigón resuelto sobre el peldaño **FEM-2** del motor `motor-fem` v0.3.0
(lámina curva MITC4 + rigidizador con offset rígido + pared delgada de Bredt).
Normativa: **EN 1990/1991 (IAP-11)** para acciones y combinaciones;
**EN 1993 (EC3)** clasificación y abolladura EN 1993-1-5, **EN 1994 (EC4)** sección mixta y conexión, **EN 1993-1-9** fatiga.

## 2. Idealización
Losa de hormigón mallada con láminas curvas MITC4; cada viga de acero como ElementoRigidizador con offset rígido bajo la losa (interacción completa). El offset rígido reproduce la acción compuesta validada en placa_rigidizada.
Nº de nudos: 255 · nº de elementos: 288.

## 3. Acciones (IAP-11)
Peso propio (g1), carga muerta de pavimento (g2) y sobrecarga de tráfico **LM1**
(tándem + UDL por carril); modelo de fatiga **FLM3** (camión de 4 ejes de 120 kN).

## 4. Análisis (motor-fem, FEM-2)
Estático por casos (ELU/ELS/FAT) + modal informativo
(primer modo físico f₁ = 2.99 Hz). El motor **no se toca**.

## 5. Comprobaciones

| Comprobación | Ed | Rd | Aprov. | Cumple |
|---|---|---|---|---|
| Flexion mixta M_pl,Rd (EC4) | 2.53e+07 | 4.39e+07 | 0.578 | ✓ |
| Cortante alma Vpl,Rd (EC3) | 4.25e+05 | 1.73e+07 | 0.025 | ✓ |
| Conexion grado eta (EC4 6.6) | 1.32 | 1 | 0.755 | ✓ |
| Fatiga ala inferior (EC3-1-9) | 38.5 | 66.7 | 0.577 | ✓ |

- **Clase de sección**: 2
- **b_eff losa**: 2.50 m · **M_Rd total**: 43.9 MNm · **PNA**: ala superior
- **Conexión** η = 1.32 · **Fatiga** Δσ_E2 = 38.5 ≤ Δσ_Rd = 66.7 MPa

## 6. Conclusión
**Veredicto: CUMPLE** · aprovechamiento máximo **0.755**.
La conexión y la fatiga gobiernan el predimensionado de la sección mixta.

> Documento de predimensionado/asistencia. **A revisar y firmar por técnico competente (ICCP).**
