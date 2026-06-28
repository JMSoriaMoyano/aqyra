# Candidatos a caso golden — Depósito Decopak (propuesta; los aprueba JM)

Cada candidato registra entrada, resultado del productor y **oráculo + tolerancia propuestos**
(GOBIERNO_QA §B.5: todo golden registra la procedencia de su oráculo). **Pendiente de aprobación de JM.**

## G-DEP-01 · Muro a flexión por empuje (ménsula apuntalada)
- **Caso:** franja vertical 1 m, H=4,35 m, empotrada en base + apuntalada en cabeza, empuje
  hidrostático triangular p₀ = 43,5 kPa.
- **Resultado productor:** M_base = 54,80 kN·m/m; reacción cabeza = 18,9 kN/m.
- **Oráculo:** solución cerrada de la ménsula apuntalada → M_base = p₀·H²/15 = **54,88 kN·m/m**;
  R_cabeza = p₀·H/10. Procedencia: **analítica (cerrada)**.
- **Tolerancia propuesta:** 2 % en M. *(auto-chequeo actual: 0,14 %).*

## G-DEP-02 · Losa de cubierta a punzonamiento (rueda IAP-11)
- **Caso:** losa 0,70 m, rueda 150 kN (medio eje tándem), patch 0,40×0,40.
- **Resultado productor:** v_Ed = 0,036 MPa; v_Rd,c = 0,581 MPa → util 0,06.
- **Oráculo:** EC2 §6.4 perímetro de control a 2d; contrastar con PyNite/2.º código en flexión local.
  Procedencia: **normativa + 2.º código FEM (placa)**.
- **Tolerancia:** 5 % en v_Ed.
- ⚠️ Caso prioritario: el reparto transversal del tándem debe verificarse en placa 2D.

## G-DEP-03 · Flotación del vaso vacío (UPL, EC7)
- **Caso:** vaso vacío, freático variable; A_raft = 302,8 m²; peso estabilizador 0,9·G = 10.920 kN.
- **Resultado productor:** freático documentado (+144,6) → U=0 → no crítica. Sensibilidad a rasante:
  U=16.804 kN, FS = 0,65.
- **Oráculo:** balance estático cerrado U = γ_w·A·h_sub vs 0,9·G. Procedencia: **analítica**.
- **Tolerancia:** 1 % en FS. *(El valor de h_sub depende del freático de proyecto → gate de JM.)*

## G-DEP-04 · Raft sobre lecho elástico (Winkler)
- **Caso:** franja transversal, k_s=80.000 kN/m³, cargas de muro + columna de agua.
- **Resultado productor:** M_máx = 132,8 kN·m/m; q_terreno = 65,9 kPa.
- **Oráculo:** viga sobre lecho elástico (solución de Hetényi) o PyNite con resortes; **2.º código FEM**.
- **Tolerancia:** 5 % en M (sensible a k_s → fijar k_s con el geotécnico).
