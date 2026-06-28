# Evidencia para QA — Depósito enterrado Decopak

**Rol de este hilo:** *build* (produce el cálculo). **La verificación la hace un agente de QA en
ejecución separada, con su propio oráculo.** Aquí se prepara la evidencia; **no se certifica**.
Certificación = golden verde + informe QA limpio + **firma de JM** (dos llaves, GOBIERNO_QA §B.5).

## 1. Trazabilidad (entrada → versión → norma → resultado → oráculo)

| Campo | Valor |
|---|---|
| **Entrada** | `modelo/DepositoDecopakEnterrado.ifc` (IFC2X3, Revit 2026, vista coordinación) |
| **Lectura** | `ifcopenshell 0.8.5` (parser IFC2X3); geometría en coord. de mundo |
| **Versión núcleo/plugins** | `versions.lock` → **`0.0.0` (NO ANCLADA)** — motor-fem, motor-calculo, estructuras-eurocodigos, iso19650-openbim. Cálculo hecho con motor propio `calc_deposito.py` (numpy), NO con el núcleo versionado. |
| **Norma** | EC0/EC1 (AN España), EC2, EC7, **EN 1992-3** (depósitos), IAP-11 (tráfico), EC8 (sismo, pendiente) |
| **Resultado** | `calculo/resultados.json` + `calculo/02_acciones_y_calculo.md` |
| **Oráculo (auto-chequeo)** | fórmula cerrada ménsula apuntalada p₀H²/15: error 0,14 % vs FE. **Insuficiente como QA**. |
| **Reproducibilidad** | `calculo/calc_deposito.py` (entradas y modelo explícitos en el script) |

## 2. Qué debe verificar la QA (capas B.2 del gobierno)

1. **Numérica (oráculo independiente — PyNite por defecto):**
   - Muros: viga apuntalada bajo empuje trapezoidal/triangular (M_base, M_vano, reacciones).
   - **Losa de cubierta: rehacer con placa 2D / emparrillado** (el ancho eficaz del tándem aquí es
     aproximado y probablemente NO conservador en reparto transversal). **Punto crítico de QA.**
   - Raft: viga/placa sobre lecho elástico (k_s); contrastar M con PyNite (DKMQ + resortes).
2. **Normativa:** recubrimientos, A_s,mín, aprovechamientos ≤ 1, **w_k ≤ 0,20 mm** (EN 1992-3),
   cortante y punzonamiento EC2, FS de flotación EC7.
3. **Regresión:** congelar los casos de §3 como golden si JM los aprueba.

## 3. Supuestos que requieren confirmación de JM (gates abiertos)

| # | Supuesto adoptado | Impacto si cambia |
|---|---|---|
| S1 | Cota implantación base = **+146,40** (del IFC) | empujes, freático, portante, flotación |
| S2 | **Freático documentado** (+144,6, bajo la base) → flotación no crítica | si sube, vaso vacío flota (FS=0,65) |
| S3 | HA-30 / B500S, c_nom=45, estanqueidad Clase 1 (w_k≤0,20) | armado y fisuración |
| S4 | K₀=0,50 (reposo), γ_s=20, φ'=30°, q_trasdós=20 kPa | empuje de muros |
| S5 | Cubierta **unidireccional 11,37 m**, IAP-11 LM1 (decisión JM) | armado pesado (~φ25/100); revisar esquema |
| S6 | Muros "20 cm" = muretes/recrecido superior (no compartimentación) | función real a confirmar en modelo |
| S7 | Sismo (EC8-4 hidrodinámico) pendiente de incluir | combinación accidental |

## 4. Límites declarados del cálculo del productor

- Motor propio simplificado (FE de barra 1D + Winkler 1D); **no es FEM 2D de placa**. La losa de
  cubierta y el raft deben verificarse con placa 2D en la QA.
- Reparto transversal del tándem por ancho eficaz (aproximado).
- Térmica/retracción tratada cualitativamente (no se cuantifica la coacción).
- Sismo no incluido numéricamente.
