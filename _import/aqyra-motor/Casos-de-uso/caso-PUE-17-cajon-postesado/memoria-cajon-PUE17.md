# Memoria de cálculo — Tablero de viga-cajón postesado (PUE-17)

> **Predimensionado/asistencia. A revisar y firmar por técnico competente (Ingeniero de
> Caminos, Canales y Puertos).** Valores de determinación nacional sin verificar: `[confirmar AN]`.

## 1. Objeto y normativa

Predimensionado de un tablero de **viga-cajón de hormigón postesado** de 3 vanos continuos,
calculado por **elementos finitos de lámina** (motor `motor-fem`, peldaño FEM-2) arrancando de
un modelo **IFC4X3**. Normativa de referencia: **EN 1990/1991** (acciones y combinaciones,
tren de cargas **IAP-11 / LM1**), **EN 1992-1-1 y EN 1992-2** (hormigón estructural y puentes,
§5.10 pretensado, §6.3 torsión, §5.3.2 ancho eficaz), Anejo Nacional de España.

## 2. Geometría y materiales

Cajón unicelular trapezoidal: ancho de losa superior **11,0 m**, de losa inferior **6,0 m**,
canto **2,5 m**; espesores losa superior **0,30 m**, losa inferior **0,25 m**, almas
inclinadas **0,45 m**. Luz **3 × 40 m**. Hormigón **HP-40** (f_ck = 40 MPa, E = 35 GPa,
ν = 0,2, ρ = 2500 kg/m³); f_ck en transferencia 28 MPa `[confirmar AN]`.

Propiedades de la sección por pared delgada (con las que se idealiza el cajón): A = 7,98 m²,
I_y = 8,56 m⁴, c_sup = 0,97 m, c_inf = 1,53 m, área de la celda media A_m = 17,91 m²,
J de Bredt = 17,76 m⁴. La geometría extruida real del IFC (`IfcArbitraryProfileDefWithVoids`)
da el área bruta del polígono (6,43 m²); la diferencia es la propia de la idealización de
pared delgada y se documenta como cross-check.

## 3. Idealización (lámina pura, FEM-2)

El cajón se malla con **láminas curvas cuadriláteras MITC4** (membrana + flexión Mindlin con
cortante transversal asumido, libre de bloqueo) en las cuatro paredes, con los **diafragmas de
apoyo como rigidizadores** (barra excéntrica acoplada por offset rígido). 555 nudos, 540
elementos. Apoyos simples sobre la losa inferior en estribos y pilas. La idealización de lámina
capta **torsión, distorsión y *shear lag* por geometría**; se validó contra la teoría de
viga-cajón (deflexión vs Euler 0,77 %, momento de sección 5,3 %).

## 4. Acciones y postesado

- **Permanentes**: peso propio g1 (peso de las láminas) y carga muerta g2 = 3,0 kN/m².
- **Sobrecarga de tráfico**: **LM1** (IAP-11), tándem 2 × 300 kN por carril + UDL 9 kN/m²,
  3 carriles, resuelto por **líneas de influencia** (objetivo `esfuerzo_lamina` sobre los
  paneles de fibra del FEM).
- **Postesado** por **balance de cargas** (EC2 §5.10): P0 = 70 000 kN, pérdidas 18 %
  (modelo simplificado por porcentaje `[confirmar AN]`) → P∞ = 57 400 kN; carga equivalente
  ascendente w_p = 8·P∞·f/L² = 315,7 kN/m (f = 1,1 m). La precompresión σ_cp = −P/A se trata
  analíticamente; la fase de transferencia escala el postesado por P0/P∞.

Coeficientes: γ_G = 1,35; γ_Q = 1,50; γ_P = 1,0; ψ-LM1 según IAP-11 `[confirmar AN]`.

## 5. Comprobaciones EC2 (sección crítica: vano 2)

| Comprobación | Valor | Límite | Aprov. | Veredicto |
|---|---|---|---|---|
| Construcción — compresión inferior | −12,67 MPa | −0,6·f_ck(t) = −16,8 MPa | 0,754 | CUMPLE |
| Construcción — tracción superior | 0 | f_ctm = 3,51 MPa | 0,000 | CUMPLE |
| Servicio — compresión superior | −7,91 MPa | −0,6·f_ck = −24,0 MPa | 0,330 | CUMPLE |
| Servicio — tracción inferior | 0 | f_ctm | 0,000 | CUMPLE |
| Descompresión (cuasiperm.) | −8,47 MPa | 0 | 0,000 | CUMPLE |
| Flexión ELU | M_Ed = 55 224 kN·m | M_Rd = 166 232 kN·m | 0,332 | CUMPLE |
| Cortante + torsión (interacción V/T) | 0,532 | 1,0 | 0,532 | CUMPLE |

*Shear lag*: ancho eficaz del ala b_eff/b = 0,84 (EN 1992-1-1 §5.3.2). Frecuencia fundamental
f₁ = 3,14 Hz (informativa). La sección permanece en **compresión** en servicio, con amplio
margen frente a descompresión.

## 6. Conclusión

El tablero de cajón postesado de 3 × 40 m **CUMPLE** en predimensionado, con
**aprovechamiento máximo 0,754** gobernado por la **compresión de la fibra inferior en la fase
de construcción/transferencia**. El resto de comprobaciones presentan amplio margen.

> Este documento es un **predimensionado de asistencia** y **debe ser revisado y firmado por
> técnico competente (ICCP)** antes de cualquier uso. Verificar los NDP marcados `[confirmar AN]`
> (límites de tensión, pérdidas diferidas, ángulo de bielas, ψ de combinación) frente al Anejo
> Nacional aplicable.
