# Caso 14 — Viga pretensada hiperestática (continua, 2 vanos) · EC2 §5.10

> Cuarto peldaño de la **segunda tanda** (Dirección 1). **Continúa la tipología de
> pretensado y la lleva a estructuras hiperestáticas.** Plugin de partida:
> `motor-calculo-estructural` **v0.19.0** (acumulativo); el caso toma **0.20.0**.

## 1. Encargo

Calcular y verificar, por **predimensionado** según EN 1992‑1‑1 (EC2) §5.10 con
Anejo Nacional España, una **viga postesada continua de dos vanos** de un
forjado/estructura de aparcamiento, a partir del **IFC ortodoxo** `caso-14.ifc`,
con el agente `ingeniero-estructurista`. El salto respecto al caso 12 (viga
postesada **isostática**) y al caso 13 (losa plana postesada) es la
**hiperestaticidad**: aparecen los **momentos hiperestáticos (secundarios) de
pretensado**, la **línea de presiones** y la **concordancia**, la posibilidad de
**redistribución** (§5.5) y el **ELU con el momento secundario** como acción
(γ_P = 1,0).

## 2. El modelo (sintético, realista)

- **Hormigón C40/50**: fck = 40 MPa, fcd = 26,67 MPa, fctm = 3,5 MPa,
  Ecm = 35 GPa, fck(t) = 32 MPa (transferencia).
- **Sección rectangular** b = 0,50 × h = 1,30 m (misma que el caso 12).
  A = 0,6500 m², I = 0,09154 m⁴, W = 0,14083 m³, c = 0,65 m.
- **Dos vanos** de L = 20,0 m (total 40 m, L/h ≈ 15,4), **3 apoyos**: dos extremos
  articulados y uno central (introduce la hiperestaticidad). 1 grado de
  hiperestatismo (la reacción/momento del apoyo central).
- **Pretensado postesado adherente**, tendón **14 × Y1860S7 0,6"** (Ap = 150
  mm²/cordón → **Ap = 2.100 mm²**), **trazado parabólico continuo por vano**:
  e = 0 en los apoyos extremos (anclaje en c.d.g.), **e = +0,30 m** (hacia abajo)
  en centro de vano y **e = −0,30 m** (hacia arriba) sobre el apoyo central, con
  curvaturas inversas y punto de inflexión junto al apoyo central.
  *(El enunciado original sugería e ≈ ±0,50 m; se **refina a ±0,30 m** para que el
  balance equilibre la permanente con residual ~0; con ±0,50 el drape sería 0,75 y
  el pretensado sobre‑equilibraría la permanente.)*
- **Cargas** (vía ortodoxa): peso propio **g0 = A·25 = 16,25 kN/m** (lo añade el
  solver), carga muerta **g2 = 5,0 kN/m**, sobrecarga **q = 12,0 kN/m** (ψ₂ = 0,3).
- Geometría/apoyos/cargas por entidades ortodoxas (`IfcStructuralCurveMember`,
  `IfcStructuralPointConnection` + `IfcBoundaryNodeCondition`,
  `IfcStructuralCurveAction` + `IfcStructuralLoadGroup`); datos del pretensado
  (P/σp0/σp,∞, Ap, trazado por vano, drape, μ/k, penetración de cuña, relajación)
  en `Pset_Estructurando_Pretensado` del curve member. NDP marcados `[confirmar AN]`.

## 3. Trabajo (la tipología de pretensado en estructuras hiperestáticas)

1. **Reutiliza** la biblioteca `pretensado/` EC2 §5.10 del caso 12 (cargas
   equivalentes, pérdidas, tensiones por fibra, ELU por fibras) y el solver de
   barras para la **viga continua**. Orquestador nuevo
   `run_all_pretensado_continua.py`.
2. **Cargas equivalentes en la viga continua**: w_p hacia arriba en los vanos +
   fuerza de desvío hacia abajo sobre el apoyo central + momentos de anclaje →
   aplicar a la continua (FEM) y obtener **M_p,tot(x)**. Calcular **M₁(x) = P·e(x)**
   y **M_sec = M_p,tot − M₁**. Validar que M_sec es **lineal y nula en los
   extremos**. Contraste por el **método de las fuerzas** (1 incógnita
   hiperestática) ≈ FEM.
3. **Línea de presiones y concordancia**: e_p(x) = M_p,tot/P = e(x) + M_sec/P;
   comprobar si el tendón es concordante (M_sec ≈ 0) y cuantificar la desviación.
4. **Verificación**: tensiones por fibra (transferencia/servicio) **con M_sec**;
   **ELU de flexión por fibras** con el **momento secundario como acción
   (γ_P = 1,0)** en centro de vano (sagging) y apoyo central (hogging);
   **redistribución §5.5** (opcional, con control de x/d); fisuración §7.3 y flecha.
5. **Validación**: balance (w_p equilibra la permanente, residual ~0); M_sec
   lineal y nula en extremos; FEM vs método de las fuerzas (Δ ≈ 0);
   M_p,tot = M₁ + M_sec; σp,∞ ≈ 0,60·fpk, σp0 ≈ 0,72·fpk; tensiones dentro de
   límites; ELU M_Rd ≥ M_Ed (con secundario); equilibrio global ~0 %. Contraste
   cargas equivalentes vs fuerza+excentricidad.

## 4. Chequeo de mano (orden de magnitud)

- **Esfuerzos externos** (continua de 2 vanos, UDL; apoyo central M = −w·L²/8,
  vano M ≈ +9·w·L²/128 a 0,375·L): ELS cuasipermanente w = 21,25 + 0,3·12 = 24,85
  → M_apoyo ≈ −1.242 kN·m, M_vano ≈ +699. ELS rara w = 33,25 → −1.662 / +935.
  **ELU** w = 1,35·21,25 + 1,5·12 = 46,69 → **M_apoyo ≈ −2.334**, M_vano ≈ +1.313.
- **Balance**: w_p = 8·P·a/L² con a = 0,45 m y P_m,∞ = 2.344 kN (14×Y1860S7,
  σp,∞ = 0,60·fpk = 1.116 MPa) → **w_p ≈ 21,1 kN/m** ≈ permanente (residual ~0).
- **Momentos de pretensado (LO NUEVO)**: M₁ = P·e (primario, isostático),
  M_p,tot (cargas equivalentes en la continua, FEM/método de fuerzas), **M_sec =
  M_p,tot − M₁** lineal, nula en extremos, máxima sobre el apoyo central (algunos
  cientos de kN·m, sagging → alivia el hogging de cálculo allí).
- **ELU con secundario (§5.10.8)**: M_Ed = γ_G·M_g + γ_Q·M_q + 1,0·M_sec; M_Rd por
  fibras con activo a f_pd (+ pasivo).

## 5. Entregables

`caso-14.ifc`, `validacion-IFC.txt`, `modelo_neutro.json`,
`verificacion_pretensado_continua.json`, memoria(s) Word y diagramas (alzado con
trazado del tendón, cargas equivalentes, leyes **M₁ / M_p,tot / M_sec**
superpuestas, **línea de presiones**, M/V de servicio y ELU, interacción por
sección crítica, tensiones por fibra, flecha). Código fuente en `_codigo/`.

> Resultado de **predimensionado**, a revisar y firmar por técnico competente.
> NDP del Anejo Nacional España marcados `[confirmar AN]`.
