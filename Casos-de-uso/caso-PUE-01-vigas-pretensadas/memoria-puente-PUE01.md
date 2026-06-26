# Memoria de cálculo — Tablero de vigas pretensadas (caso-PUE-01)

**Disciplina:** puentes (Ola 7, PT 7.1) · **Núcleo:** motor-fem v0.2.0 (C5, FEM-1) ·
**Fecha:** 23/06/2026

> **Predimensionado/asistencia.** Este documento NO sustituye al proyecto. Debe ser
> **revisado y firmado por técnico competente (Ingeniero de Caminos, Canales y Puertos)**.
> Los valores marcados `[confirmar AN]` son parámetros de Anejo Nacional a fijar por el proyectista.

## 1. Objeto y normativa

Predimensionado de un tablero de **vigas pretensadas** de carretera por **emparrillado
(grillage)**, con acciones de **IAP-11** (modelo de carga LM1, térmica, viento),
pretensado según **EC2 §5.10** (EN 1992-1-1) y comprobación según **EC2 / EC2-2** con
Anejo Nacional español. El cálculo de esfuerzos y envolventes de tráfico se realiza con
el motor de elementos finitos propio `motor-fem` (peldaño FEM-1: estático + líneas de
influencia/cargas móviles + modal).

## 2. Geometría y materiales

| Concepto | Valor |
|---|---|
| Luz (isostática) | L = 25.0 m |
| Nº de vigas / separación | 4 / 2.50 m |
| Ancho de tablero | 8.75 m (2 carriles virtuales de 3 m) |
| Riostras | estribos + centro de vano |
| Sección de viga (doble-T + losa) | A = 0.70 m², I = 0.22 m⁴, h = 1.50 m, c_sup = 0.70 m, c_inf = 0.80 m, b_w = 0.24 m |
| Hormigón | HP-45: fck = 45 MPa, fck(t) = 32 MPa, Ecm = 34 GPa, ρ = 2500 kg/m³ |
| Acero activo | fpk = 1860 MPa, Ep = 195 GPa, Ap = 42 cm²/viga |

**Idealización (emparrillado barra+barra):** cada viga se discretiza en 20 barras
longitudinales sobre el eje; las riostras (barras transversales) reparten la carga
entre vigas. Apoyos isostáticos en estribos (un estribo fijo longitudinal, el otro
deslizante). El tablero horizontal flecta fuera de plano → estabilización de plano
desactivada; la estabilidad la dan los apoyos.

## 3. Acciones (IAP-11)

- **Permanentes:** peso propio g1 = 17.17 kN/m·viga (ρ·A·g) + carga muerta g2 = 6.56 kN/m·viga
  (pavimento 3 kN/m² repartido).
- **LM1 (tráfico):** carriles virtuales de 3 m. Carril 1 (αQ·Q1k = 300 kN/eje, tándem de
  2 ejes a 1.2 m + UDL αq·q1k·3 m = 27 kN/m); carril 2 (200 kN/eje + 7.5 kN/m). Asignados a
  las vigas bajo cada carril. El tren se barre por **líneas de influencia** (motor-fem,
  41 posiciones) → envolventes y posiciones pésimas.
- **Térmica:** componente uniforme ΔT = 15 °C (axil) + gradiente vertical ΔT = 10 °C; α = 1·10⁻⁵.
- **Viento:** empuje transversal 3 kN/m (básico).
- **Combinaciones:** ELU (6.10) y ELS característica/frecuente/cuasipermanente con ψ de
  IAP-11 (gr1a) `[confirmar AN]`.

## 4. Pretensado (EC2 §5.10) — cargas equivalentes y pérdidas

Tendón parabólico, e_centro = 0.55 m, e_apoyo = 0. Carga equivalente de balance
**w_p = 8·P∞·e/L² = 28.9 kN/m** (hacia arriba), inyectada como caso `P`.

| Pérdida | Valor (MPa) |
|---|---|
| Rozamiento | 42.0 |
| Penetración de cuña | 46.8 |
| Acortamiento elástico | 28.1 |
| Relajación | 0.3 |
| Diferidas (fluencia+retracción+relaj., ec. 5.46) | 145.4 |

σp0 = 1238 MPa (0.67·fpk) → σp∞ = 976 MPa. **Pérdidas totales 21.2 %**
(P₀ = 5200 kN → **P∞ = 4098 kN**). Pérdidas diferidas por método **simplificado por
coeficientes** (decisión nº5); gancho dejado para integración paso a paso.

## 5. Esfuerzos (motor-fem FEM-1) y comprobación EC2

Envolventes por viga (M en centro de vano, V en apoyo). Viga crítica = **viga 2**.

| Viga | M_perm | M_LM1,máx | M_Ed (ELU) | M_Rd | V_Ed (ELU) | V_Rd,máx | Aprov. | Veredicto |
|---|---|---|---|---|---|---|---|---|
| 0 | 1854 | 1363 | 4343 | 8254 | 546 | 1774 | 0.67 | CUMPLE |
| 1 | 1854 | 2558 | 5956 | 8254 | 1106 | 1774 | 0.72 | CUMPLE |
| **2** | **1854** | **2558** | **5956** | **8254** | **1441** | **1774** | **0.81** | **CUMPLE** |
| 3 | 1854 | 2168 | 5429 | 8254 | 633 | 1774 | 0.67 | CUMPLE |

(M en kN·m, V en kN.)

**Tensiones (viga crítica, MPa; compresión negativa):**

| Situación | Fibra superior | Fibra inferior | Límite |
|---|---|---|---|
| Transferencia (P₀ + g1) | −2.60 | −12.95 | comp. ≤ 0.6·fck(t) = −19.2 |
| Servicio (P∞ + g + LM1) | −12.72 | +1.99 | tracción ≤ fctm = 3.8 |

- **Flexión ELU:** M_Ed = 5956 ≤ M_Rd = 8254 kN·m (aprov. 0.72). ✔
- **Cortante ELU (bielas):** V_Ed = 1441 ≤ V_Rd,máx = 1774 kN (aprov. 0.81). Requiere
  armadura transversal (cercos) dimensionada por el modelo de bielas (θ = 21.8°). ✔
- **Tensiones en vacío y servicio:** dentro de límites; **descompresión** verificada en
  cuasipermanente. ✔
- **Fisuración:** sin tracción en cuasipermanente. ✔

## 6. Análisis dinámico (modal)

Frecuencias propias (masa concentrada, peso propio + cuasipermanente):
**f₁ = 2.24 Hz**, f₂ = 3.34 Hz, f₃ = 3.53 Hz. La frecuencia fundamental se sitúa en el
rango a contrastar frente a los criterios de confort dinámico (informativo) `[confirmar AN]`.

## 7. Conclusión

El tablero **CUMPLE** en predimensionado con un aprovechamiento máximo de **0.81**
(gobierna el cortante). Resultado de asistencia: **revisar y firmar por técnico
competente (ICCP)** antes de cualquier uso en proyecto.
