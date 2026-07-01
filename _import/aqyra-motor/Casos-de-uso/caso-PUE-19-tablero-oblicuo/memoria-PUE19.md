# Memoria de cálculo — PUE-19: Tablero oblicuo (esviado)

**Ola 7 · PT 7.5 · FEM-2.** Predimensionado/asistencia. **A revisar y firmar por
técnico competente (ICCP).** NDP: `[confirmar AN]`.

## 1. Objeto y normativa
Tablero oblicuo (esviado) resuelto sobre el peldaño **FEM-2** del motor `motor-fem` v0.3.0
(lámina curva MITC4 + rigidizador con offset rígido + pared delgada de Bredt).
Normativa: **EN 1990/1991 (IAP-11)** para acciones y combinaciones;
**EN 1992 (EC2)** / **EN 1993 (EC3)**.

## 2. Idealización
Malla romboidal de láminas curvas MITC4 que sigue la línea de apoyo esviada (x = y·tan φ); cuadriláteros distorsionados soportados nativamente por MITC4.
Nº de nudos: 221 · nº de elementos: 192.

## 3. Acciones (IAP-11)
Peso propio (g1), carga muerta de pavimento (g2) y sobrecarga de tráfico **LM1**
(tándem + UDL por carril).

## 4. Análisis (motor-fem, FEM-2)
Estático por casos (ELU/ELS) + modal informativo
(primer modo físico f₁ = 5.07 Hz). El motor **no se toca**.

## 5. Comprobaciones

| Comprobación | Ed | Rd | Aprov. | Cumple |
|---|---|---|---|---|
| Flexion losa long. M_Rd (EC2) | 1.22e+06 | 1.29e+06 | 0.949 | ✓ |
| Flexion losa transv. M_Rd (EC2) | 2.62e+05 | 4.02e+05 | 0.652 | ✓ |

- **Esviaje**: 30° · **Concentración esquina obtusa** R_obtusa/R_media = 6.23
- **Reparto transversal** factor = 1.06 · **As_long** = 41.7 cm²/m

## 6. Conclusión
**Veredicto: CUMPLE** · aprovechamiento máximo **0.949**.
La concentración de reacción en la esquina obtusa es el efecto característico del esviaje.

> Documento de predimensionado/asistencia. **A revisar y firmar por técnico competente (ICCP).**
