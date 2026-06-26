# Memoria de cálculo — Pila + aparato de apoyo + cimentación (caso PUE-05)

> **Predimensionado/asistencia. Debe ser revisado y firmado por técnico competente
> (Ingeniero de Caminos, Canales y Puertos).** NDP marcados `[confirmar AN]`.

## 1. Objeto y normativa
Predimensionado de una **pila intermedia** de puente de carretera con su **aparato de
apoyo** y su **cimentación**, según EN 1992-1-1 (EC2), EN 1997-1 (EC7) e **IAP-11**
(acciones). La acción sísmica **EN 1998-2 (EC8-2)** queda fuera de este alcance
(gancho diferido a PT sísmico dedicado).

## 2. Idealización (consume motor-fem, contrato C5, FEM-1)
- **Pila = columna** (barra 3D Euler-Bernoulli) en el plano XZ, H = 8 m, discretizada
  en 10 segmentos. Sección rectangular 1,5 × 1,5 m (A = 2,25 m², I = 0,422 m⁴), HA-30.
- **Aparato de apoyo en cabeza** = resorte de 6 GdL (elastomérico zunchado 0,45 × 0,60 m,
  Te = 63 mm): Kh = G·A/Te = 3,86 MN/m, Kv = Ec·A/Te = 2660 MN/m, rigidez a giro
  Ec·I/Te. Transmite las reacciones del tablero como cargas nodales.
- **Base sobre resorte Winkler** (cimentación): kx = 8·10⁸ N/m, kz = 1,5·10⁹ N/m,
  kry = 9·10⁸ N·m/rad. `estabilizar_plano=True` (pila plana XZ).

## 3. Acciones (IAP-11)
Reacciones del tablero en cabeza (modo *dato del caso*): N_G = 4200 kN (permanente),
N_LM1 = 1500 kN (envolvente de tráfico LM1), **frenado/arranque** H = 360 kN, viento
H = 120 kN, térmica H = 150 kN. Peso propio del fuste (ρ·g·A) y viento sobre el fuste
(3 kN/m). Coeficiente del grupo de tráfico **γQ = 1,35** (IAP-11). Combinación ELU:
1,35·G + 1,35·(M+F) + 1,5·ψ₀·(V,T). `[confirmar AN]`

## 4. Cálculo (motor-fem) — esfuerzos de base (ELU)
| Magnitud | Valor |
|---|---|
| Axil N_Ed | 8291 kN |
| Momento M_Ed | 5918 kN·m |
| Cortante V_Ed | 751 kN |
| Frecuencia fundamental f₁ | 4,51 Hz |
| Desplazamiento de cabeza (ELU) | 62,6 mm |

Verificación cruzada: M_base (FEM) = H_cabeza · H coincide con la solución cerrada de
ménsula (error 8·10⁻¹²).

## 5. Comprobación EC2 — fuste (flexo-compresión)
- **2.º orden aproximado**: δ = 1/(1 − N_Ed/N_cr) = **1,016** (N_cr = π²EI/(βH)²,
  β = 2 ménsula). Pila rígida → amplificación despreciable. P-Δ riguroso/pandeo → FEM-3.
- **Flexo-compresión M-N** (sección rectangular, armadura simétrica As = 250 cm²):
  M_Ed,2 / M_Rd → aprov **0,495**; N_Ed ≤ N_Rd,máx. **CUMPLE**.
- **Cortante por bielas** (V_Rd,max + cercos): aprov **0,109**. **CUMPLE**.

## 6. Comprobación EC7 — cimentación (zapata, enrutada)
Zapata 6 × 6 m, canto 1,4 m. Reacción real de base amplificada (N, M, H):
- **Hundimiento** (Meyerhof B' = B − 2e): σ_max = 432 kPa ≤ q_adm = 550 kPa →
  aprov **0,785** (gobierna). e = 0,63 m ≤ B/6 = 1,0 m (sin despegue).
- **Deslizamiento**: H ≤ μ·N. **CUMPLE**.

Alternativas de cimentación disponibles por enrutado: `pilotes` (Rc,d = Rs/γS + Rb/γB
+ reparto de grupo) y `encepado` (biela-tirante). Reutilizan las fórmulas de
`motor-calculo` (cimentaciones / pilotes / bielas-tirantes).

## 7. Conclusión
**VEREDICTO: CUMPLE** · aprovechamiento máximo **0,785** (EC7 hundimiento). El
predimensionado de pila, aparato de apoyo y cimentación es satisfactorio para las
acciones consideradas. Pendiente: comprobación sísmica EC8-2 y revisión del
desplazamiento de cabeza en servicio. **Revisar y firmar por ICCP.**

---
*Registro: 2026-06-23 · pila PUE-05 · run_all_pila · aprov 0,785 · CUMPLE.*
