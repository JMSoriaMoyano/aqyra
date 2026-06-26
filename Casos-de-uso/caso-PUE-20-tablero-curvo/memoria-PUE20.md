# Memoria de cálculo — PUE-20: Tablero curvo en planta

**Ola 7 · PT 7.5 · FEM-2.** Predimensionado/asistencia. **A revisar y firmar por
técnico competente (ICCP).** NDP: `[confirmar AN]`.

## 1. Objeto y normativa
Tablero curvo en planta resuelto sobre el peldaño **FEM-2** del motor `motor-fem` v0.3.0
(lámina curva MITC4 + rigidizador con offset rígido + pared delgada de Bredt).
Normativa: **EN 1990/1991 (IAP-11)** para acciones y combinaciones;
**EN 1992 (EC2)** / **EN 1993 (EC3)**.

## 2. Idealización
Malla de láminas curvas MITC4 siguiendo la directriz del eje (arco de radio R / IfcAlignment de Ola 5); sección cajón levantada en la terna {tangente, normal radial, vertical} por estación de arco.
Nº de nudos: 285 · nº de elementos: 272.

## 3. Acciones (IAP-11)
Peso propio (g1), carga muerta de pavimento (g2) y sobrecarga de tráfico **LM1**
(tándem + UDL por carril).

## 4. Análisis (motor-fem, FEM-2)
Estático por casos (ELU/ELS) + modal informativo
(primer modo físico f₁ = 2.70 Hz). El motor **no se toca**.

## 5. Comprobaciones

| Comprobación | Ed | Rd | Aprov. | Cumple |
|---|---|---|---|---|
| Flexion compresion sup. (EC2) | 1.25e+07 | 2.7e+07 | 0.462 | ✓ |
| Flexion armado fondo As/As_max (EC2) | 654 | 2.07e+03 | 0.316 | ✓ |
| Cortante+Torsion Bredt (EC2 6.3) | 4.91e+06 | 7.38e+06 | 0.666 | ✓ |

- **Radio** R = 200 m · **T/M** = 0.141 · **T_apoyo** = 8490 kNm (acoplamiento por curvatura)
- **J de Bredt** = 8.8476 m⁴ · τ_total = 4.91 ≤ τ_Rd = 7.38 MPa

## 6. Conclusión
**Veredicto: CUMPLE** · aprovechamiento máximo **0.666**.
La torsión, acoplada a la flexión por la curvatura (dT/ds = M/R), es protagonista del dimensionado.

> Documento de predimensionado/asistencia. **A revisar y firmar por técnico competente (ICCP).**
