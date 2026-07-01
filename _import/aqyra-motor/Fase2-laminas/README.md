# Fase 2 — Motor mixto barras + lámina (losas/muros) IFC → FEM → Eurocódigos

Amplía la Fase 1 con elementos finitos tipo **placa (lámina)** para losas y muros,
sobre un modelo **mixto barras + placa**, con dimensionamiento de la losa según
**EC2**. Caso de prueba elegido: **losa integrada en pórtico** (módulo de edificio).

## Resultado

Módulo de 5 × 5 m y 4 m de altura: 4 pilares HEB 200 y 4 vigas IPE 330 (S275),
con losa de hormigón C30/37 de 20 cm apoyada en las vigas. Cargas: autopeso +
G superpuesta 2 kN/m² + Q de uso 3 kN/m².

- **Elementos placa certificados** contra Timoshenko (losa SS): flecha 2,5 %, momento 0,5 %.
- **Equilibrio global** del modelo mixto: error **0,00 %** (reacción = carga aplicada).
- **EC2 losa**: armado a flexión por dirección (inferior φ10/200 en x, φ10/150 en y;
  superior mínimo), cuantías mín/máx y flecha (24 % de L/300) → **CUMPLE**.
- **EC3 barras**: viga y pilar críticos comprobados (aprovechamiento < 20 %).
- **Punzonamiento (EC2 §6.4)** en pilar de esquina: v_Ed/v_Rd,c = 173 % → la losa de 20 cm
  **requiere armadura de punzonamiento o mayor canto** (la biela v_Rd,max sí cumple).
- **Fisuración (EC2 §7.3)**: wk = 0,30 mm, justo en el límite de 0,30 mm (cumple con 0,40 mm de XC1).
- **Mapas de color** de Mx, My y flecha de la losa + vista 3D del módulo.
- **Memoria de cálculo** Word con todo lo anterior.

## Cómo ejecutar

```bash
python3 scripts/generate_test_ifc_3d.py          # (opcional) regenerar IFC 3D
python3 scripts/run_all.py proyecto-demo         # cadena completa
NODE_PATH=$(npm root -g) node scripts/generate_memoria_fase2.js proyecto-demo
```

Para validar solo los elementos placa: `python3 scripts/plate_validation.py`.

## Arquitectura

| Script | Función |
|---|---|
| `plate_validation.py` | Certifica elementos quad vs Timoshenko (autodiagnóstico) |
| `generate_test_ifc_3d.py` | IFC4: curve members (pórtico) + surface member (losa) |
| `ifc_to_model_3d.py` | IFC → modelo neutro 3D (barras + superficies) |
| `combinaciones.py` | Combinaciones ELU/ELS (EC0, AN España) |
| `solver_3d.py` | FEM mixto: malla la losa, fusiona nodos con vigas, resuelve |
| `verificacion_ec2.py` | Armado EC2 de la losa + EC3 conciso de barras + equilibrio |
| `ec2_punz_fis.py` | Punzonamiento (§6.4) y fisuración (§7.3) de la losa |
| `plots_3d.py` | Mapas de color (Mx, My, flecha) + vista 3D |
| `generate_memoria_fase2.js` | Memoria de cálculo en Word |
| `run_all.py` | Orquestador |

## Convenciones validadas

- Ejes X, Y horizontales; **Z vertical**; gravedad −Z.
- Barras: inercia mayor → slot `Iy`; flexión vertical de vigas → momento `My`, cortante `Fz`.
- Placa: quad MITC4. Momentos por unidad de ancho `[Mx, My, Mxy]`. Con carga
  gravitatoria el momento de campo sale **negativo = sagging (tracción inferior)**.
- Peso propio: PyNite interpreta la densidad como peso específico; el autopeso se
  aplica manualmente como **A·ρ·g** para que el equilibrio cierre exacto.
- Losa mallada compartiendo nodos con las vigas perimetrales (apoyo de borde).

## Limitaciones

Análisis lineal. El punzonamiento se evalúa como transferencia losa-pilar en
esquina (conservador; el modelo apoya la losa en vigas). No se comprueba el
pandeo lateral de vigas ni el detalle de armadura de punzonamiento. El armado es
de predimensionado. **Revisión y firma por técnico competente obligatorias.**

---

## Extensión: losa plana sobre pilares + dimensionamiento a punzonamiento

Subcarpeta `proyecto-losa-plana/`. Variante donde la losa apoya **directamente
sobre pilares** (sin vigas) — aquí el punzonamiento **sí es el mecanismo real**.

Caso: losa C30/37 de 25 cm, 10×10 m (2×2 vanos de 5 m), 9 pilares 350×350 (malla 3×3).

- **Reparto de reacciones** (ELU): interior 597 kN, borde 176 kN, esquina 61 kN; equilibrio 0,00 %.
- **Punzonamiento EC2 §6.4**: interior **NO cumple** (135 %); borde (83 %) y esquina (53 %) cumplen.
- **Dimensionamiento de la solución** (3 alternativas, reutilizable en el plugin):
  canto mínimo **≥ 320 mm**, o armadura de punzonamiento **≈ 33 cm²/m** (§6.4.5), o **capitel ≈ 701 mm**.
- **Flexión**: vano φ10/150; sobre pilares φ12/100–φ16/150. **Flecha** 12 %. **Fisuración** de vano supera 0,30 mm → reforzar armadura inferior.
- Mapas de Mx (vano y sobre pilares), flecha y **plano de pilares con estado de punzonamiento**.

Ejecutar:

```bash
python3 scripts/generate_test_ifc_flat.py
python3 scripts/run_all_flat.py proyecto-losa-plana
NODE_PATH=$(npm root -g) node scripts/generate_memoria_flat.js proyecto-losa-plana
```

Scripts añadidos: `generate_test_ifc_flat.py`, `solver_flat.py`, `verificacion_flat.py`,
`plots_flat.py`, `generate_memoria_flat.js`, `run_all_flat.py`, y la función
`dimensionar_punzonamiento()` en `ec2_punz_fis.py` (núcleo reutilizable).

---

## Extensión: elemento plano inclinado (cubierta / forjado inclinado)

Subcarpeta `proyecto-cubierta/`. Faldón de hormigón C30/37, 6×5 m, pendiente 20°,
canto 18 cm, simplemente apoyado en los 4 bordes.

- **Mallado en plano inclinado**: se malla en XY y se gira la malla el ángulo del faldón.
- **Cargas de gravedad** repartidas como **cargas nodales verticales** por área real
  (válido en cualquier inclinación, frente a la presión normal).
- **Validación**: invariancia de rotación bajo carga normal (θ=0 vs θ=30°, err 0,8 %)
  y **reducción a θ=0** (membrana ≈ 0); equilibrio vertical **0,00 %**.
- **Resultados**: flexión φ10/300 (Mx 13 kN·m/m), flecha normal 7 % de L/300,
  **membrana de compresión 96 kN/m** hacia los aleros (solo 2,7 % de la capacidad),
  fisuración de vano supera el límite con armadura mínima → reducir separación.
- Mapas de Mx, membrana n_y y flecha normal + vista 3D del faldón.

```bash
python3 scripts/generate_test_ifc_incl.py
python3 scripts/run_all_incl.py proyecto-cubierta
NODE_PATH=$(npm root -g) node scripts/generate_memoria_incl.js proyecto-cubierta
```

Scripts: `generate_test_ifc_incl.py`, `solver_incl.py`, `validate_incl.py`,
`verificacion_incl.py`, `plots_incl.py`, `generate_memoria_incl.js`, `run_all_incl.py`.
Capacidad nueva del núcleo: **mallado/cargas en plano inclinado** y lectura de
**esfuerzos de membrana** (n_x, n_y), reutilizables para cualquier lámina no horizontal.

---

## Extensión: muro de carga (elemento plano vertical)

Subcarpeta `proyecto-muro/`. Muro de hormigón C30/37, 4×3,5 m, espesor 20 cm,
base empotrada y cabeza arriostrada; carga vertical de forjados + viento fuera de plano.

- **Mallado en plano vertical** (XZ); lectura de **membrana vertical** y flexión fuera de plano.
- **Comprobación específica de muro** (lo nuevo): compresión con **esbeltez**
  (EC2 §12.6.5.2 factor Φ + clasificación §5.8.3.1) y **armadura mínima §9.6**.
- **Axil de diseño** = carga vertical total / longitud (evita la singularidad de
  membrana en las esquinas de la base).
- **Resultados**: N_Ed = 1688 kN/m, λ = 61 (esbelto), Φ = 0,67, N_Rd = 2698 kN/m →
  aprovechamiento **63 %**; flexión por viento φ10/300; armadura mínima vertical 4,0 / horizontal 2,0 cm²/m. **CUMPLE**.
- Si no cumpliera, el motor calcula el **espesor mínimo**.

```bash
python3 scripts/generate_test_ifc_muro.py
python3 scripts/run_all_muro.py proyecto-muro
NODE_PATH=$(npm root -g) node scripts/generate_memoria_muro.js proyecto-muro
```

Scripts: `generate_test_ifc_muro.py`, `solver_muro.py`, `ec2_muro.py` (núcleo:
compresión+esbeltez, armadura mínima, espesor mínimo), `verificacion_muro.py`,
`plots_muro.py`, `generate_memoria_muro.js`, `run_all_muro.py`.

> Nota: el muro de carga (compresión dominante) usa el método §12.6.5.2. Un muro de
> sótano (empuje de tierras, flexión dominante) se resuelve como **placa vertical en
> flexión** (cadena de losa) más interacción N-M; el método §12 no aplica a gran excentricidad.

