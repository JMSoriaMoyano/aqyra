# 02 · Bases de acciones, combinaciones y cálculo por elemento

**Depósito enterrado de Decopak (Rubí)** · Eurocódigos + AN España + **EN 1992-3** (depósitos)
**Estado: PROPUESTA pendiente de verificación QA independiente + firma de JM.** · 2026-06-24
Motor de cálculo: `calc_deposito.py` (FE viga Euler-Bernoulli + viga sobre lecho elástico, numpy).
Resultados completos: `resultados.json`.

> **Decisiones de JM (2026-06-24) incorporadas:** (1) tráfico de cubierta = **IAP-11 LM1 completo**;
> (2) cubierta = **losa unidireccional luz c/c 11,37 m** sobre los dos muros largos;
> (3) flotación con **freático documentado (+144,6)**.

---

## 1. Materiales y bases (EC2 / AN España)

| Parámetro | Valor |
|---|---|
| Hormigón HA-30 | f_ck = 30 · f_cd = 20,0 MPa · f_ctm = 2,90 MPa · E_cm = 32,8 GPa |
| Acero B500S | f_yk = 500 · f_yd = 434,8 MPa · E_s = 200 GPa |
| Recubrimiento | c_nom = 45 mm (caras agua/tierra) |
| Estanqueidad EN 1992-3 | Clase 1 → **w_k,máx = 0,20 mm** (caras en contacto con agua) |

## 2. Acciones características

| Acción | Valor | Norma / criterio |
|---|---|---|
| Peso propio hormigón | γ = 25 kN/m³ | EC1-1-1 |
| **Agua** (depósito lleno) | γ_w = **10 kN/m³**, calado h_w = 4,35 m → p_base = 43,5 kPa | brief JM / EN 1991-4 |
| **Empuje de tierras (reposo)** | K₀ = 1−sen φ' = **0,50** (φ'=30°). p_base = K₀·γ_s·H_t = 49,5 kPa | EC7 (estructura enterrada arriostrada) |
| Sobrecarga en trasdós | q = 20 kPa → K₀·q = 10 kPa (tráfico pesado adyacente) | EC7 / conservador |
| **Tráfico cubierta IAP-11 LM1** | carril 1: tándem 2×300 kN (α=1) + UDL 9 kN/m² | IAP-11 (decisión JM) |
| Terreno | γ_s = 20 kN/m³, φ' = 30° (UG1/relleno) | geotecnia HQ + criterio |
| **Sismo** | a_c = 0,046 g (a_b=0,04g, S=1,1509, C=1,4386) | SOCOTEC HQ — ver §8 |

## 3. Combinaciones (EC0 / AN España)

- **ELU (STR/GEO):** 1,35·G + 1,5·Q_lead + 1,5·ψ₀·Q_acomp. Empuje de tierras como permanente
  desfavorable (γ=1,35); agua y tráfico como variables (γ=1,5).
- **ELS (estanqueidad/fisuración):** combinación **característica** (γ=1,0), depósito lleno, para
  el control de fisura w_k en caras en contacto con agua (EN 1992-3, Clase 1).
- **Flotación (UPL, EC7):** acción desestabilizadora (subpresión) γ=1,0 frente a estabilizadora
  (peso propio) γ_G,stb = 0,9. Ver §7.
- **Casos pésimos de servicio:** (a) **vaso lleno + tierras + tráfico**; (b) **vaso vacío + tierras**
  (empuje no compensado, cara interior); (c) **prueba de estanqueidad: lleno sin relleno** (cara exterior).

---

## 4. Muros perimetrales de contención (50 cm)

Franja vertical de 1 m, **empotrada en la losa de fondo y apuntalada en la losa de cubierta**
(ménsula apuntalada). Acción reversible → armado en **ambas caras**. d = 0,445 m (φ20).

| Esfuerzo / comprobación | Valor | Veredicto |
|---|---|---|
| M en base, caso tierras+sobrecarga (car.) | 92,6 kN·m/m | — |
| M en base, caso agua llena (car.) | 54,8 kN·m/m | — |
| **M de diseño ELU** (env. = máx[1,35·tierras; 1,5·agua]) | **125,0 kN·m/m** | — |
| A_s requerida (flexión) / A_s,mín (fisur.) | 6,80 / 4,71 cm²/m | — |
| **Armado propuesto** (cada cara) | **φ20/200 (15,71 cm²/m)** | — |
| Aprovechamiento a flexión | **0,46** | ✅ |
| Cortante V_Ed / V_Rd,c | 178,8 / 195,9 kN | **0,91** ⚠️ ajustado |
| **Fisuración cara agua** w_k (σ_s=83,6 MPa) | **0,113 mm** ≤ 0,20 | ✅ estanco |

> Nota: el cortante queda al 91 %; conviene confirmar con la QA (canto/armado de la base). El armado
> a flexión está holgado porque lo gobiernan el cortante y la fisuración, no el momento.

## 5. Muro interior de compartimentación (50 cm)

Empuje **diferencial de agua** (compartimento grande lleno, pequeño vacío). Franja apuntalada.

| | Valor | Veredicto |
|---|---|---|
| M en base (agua, car.) | 54,8 kN·m/m | — |
| M ELU (1,5·) | 82,2 kN·m/m | — |
| Armado | φ20/200 (ambas caras) | — |
| Aprovechamiento flexión / w_k | 0,30 / 0,113 mm | ✅ |

## 6. Losas

### 6.1 Losa de cubierta (70 cm, transitable) — IAP-11 LM1, **unidireccional 11,37 m**

Permanente g = 19,0 kPa (p.p. 17,5 + acabados 1,5). Tándem repartido en b_eff = 8,79 m
(dispersión rueda 0,40+0,70 + 2 ruedas a 2,0 m) → 68,3 kN/m. Simplemente apoyada (conservador en vano).

| Componente del momento (car.) | M (kN·m/m) |
|---|---|
| Permanente | 307,0 |
| UDL LM1 (9 kPa) | 145,4 |
| Tándem LM1 (600 kN) | 194,1 |
| **M_ELU** | **923,9** |

| Comprobación | Valor | Veredicto |
|---|---|---|
| **Armado necesario** (inferior) | **φ25/100 ≈ 49,1 cm²/m** (≈ 1,0 % — pesado) | — |
| M_Rd con ese armado | 1.235 kN·m/m | — |
| **Aprovechamiento a flexión** | **0,75** | ✅ (con armado pesado) |
| Punzonamiento rueda 150 kN: v_Ed / v_Rd,c | 0,036 / 0,581 MPa | **0,06** ✅ |
| (Referencia: solo permanente, ELU) | 414,5 kN·m/m → util 0,34 | — |

> ⚠️ **Hallazgo:** una losa unidireccional de 11,37 m con **IAP-11 LM1 completo** es viable a flexión
> con el canto de 0,70 m **pero exige armadura muy pesada (~φ25/100, ≈1 %)**. Recomendación a JM:
> valorar (a) **reducir la luz** con un apoyo intermedio / viga, (b) **aumentar canto**, o
> (c) revisar si IAP-11 LM1 es el modelo adecuado frente a un vehículo pesado de explanada. La QA
> debe rehacer esta losa con **placa 2D (FEM)**, ya que el método de ancho eficaz aquí es aproximado.

### 6.2 Losa de fondo (raft) — viga sobre lecho elástico (Winkler)

Apoyo en **UG3 (arenisca, roca blanda)** a +146,40; k_s = 80.000 kN/m³. Carga: p.p. + columna de
agua (43,5 kPa) en el vaso + cargas de muro (382 kN/m). d = 0,545 m.

| Comprobación | Valor | Veredicto |
|---|---|---|
| Carga total / presión media al terreno | 19.963 kN / **65,9 kPa** | — |
| Portante: q / q_adm (UG3) | 65,9 / ~800 kPa | **0,08** ✅ amplio |
| M máx (Winkler) / M_ELU | 132,8 / 179,2 kN·m/m | — |
| Armado | φ20/200 (ambas caras) | — |
| Aprovechamiento flexión | **0,54** | ✅ |
| Fisuración w_k | **0,222 mm** | ⚠️ ligeramente > 0,20 |

> El raft sobre roca flecta poco (la reacción sigue a la carga). w_k = 0,222 mm supera levemente el
> límite de estanqueidad 0,20 mm: **subir a φ20/175 (17,95 cm²/m) o φ25/200** deja w_k < 0,20.

## 7. Flotación (vaso vacío) — EC7 UPL

| Caso | h sumergida | Subpresión U | Peso estab. (0,9·G) | FS / veredicto |
|---|---|---|---|---|
| **Freático documentado (+144,6)** | 0 (base +146,40 sobre el agua) | 0 | 10.920 kN | **sin subpresión → NO crítica** ✅ |
| *Sensibilidad: freático a rasante (+151,95)* | 5,55 m | 16.804 kN | 10.920 kN | FS = 0,65 → **flotaría** ⚠️ |

> Con el dato del informe SOCOTEC la base queda **1,8 m por encima** del freático máximo → la flotación
> **no gobierna**. **⚠️ Pero la cota de implantación del depósito (+146,40) es 5,6 m más baja que la de
> HQ (+152,00); el freático local debe confirmarse en este punto.** Si pudiera ascender (lluvia,
> rotura de servicios), el vaso vacío flotaría (FS<1): convendría prever **losa de fondo con talón/zarpa,
> lastre o anclajes**, o una **válvula antisubpresión**. Decisión de JM.

## 8. Sismo y estanqueidad (notas)

- **Sismo (EC8 / NCSE):** a_c = 0,046 g (emplazamiento HQ). Para un cajón enterrado y rígido, el sismo
  rara vez gobierna frente a agua+tierras, pero debe comprobarse el **empuje hidrodinámico** (Housner,
  EC8-4) en los muros del vaso lleno y el incremento de empuje de tierras sísmico (Mononobe-Okabe).
  **Propuesta:** incluirlo como combinación accidental en la verificación QA; previsiblemente no crítico.
- **Estanqueidad (EN 1992-3):** w_k ≤ 0,20 mm cumplido en muros (0,113) y casi en el raft (0,222 → ajustar).
  Controlar además **fisuración por coacción térmica/retracción** (calor de hidratación, juntas Sika
  Waterbar ya previstas en el modelo) con armadura mínima de piel y plan de hormigonado.

---

## 9. Resumen de aprovechamientos (PROPUESTA · pendiente QA + firma)

| Elemento | Comprobación crítica | Aprov. | Veredicto |
|---|---|---|---|
| Muro perimetral 50 | cortante en base | 0,91 | ✅ (ajustado) |
| Muro perimetral 50 | flexión / fisura | 0,46 / 0,113 mm | ✅ |
| Muro interior 50 | flexión / fisura | 0,30 / 0,113 mm | ✅ |
| Losa cubierta 70 | flexión (LM1, φ25/100) | 0,75 | ✅ (armado pesado) |
| Losa cubierta 70 | punzonamiento | 0,06 | ✅ |
| Losa de fondo | flexión | 0,54 | ✅ |
| Losa de fondo | fisuración | 0,222 mm | ⚠️ ajustar armado |
| Flotación (documentado) | UPL | — | ✅ no crítica |

**Verificación interna (oráculo analítico):** el FE del muro apuntalado bajo empuje triangular da
M_base = 54,80 kN·m/m frente a la fórmula cerrada p₀·H²/15 = 54,88 → **error 0,14 %** (FE validado).
Esto es auto-chequeo del productor; **no sustituye la QA independiente de dos llaves.**
