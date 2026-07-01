# Fase 6 — Muros de contención (EC7 + EC2)

Quinto caso del catálogo de cimentaciones/contención de la hoja de ruta v2 (Grupo C:
acoplamiento con geotecnia). Reutiliza el **núcleo**: geotecnia EC7, el **solver de
barras** (el alzado como ménsula vertical) y la biblioteca de verificación EC2.

## Caso: muro de contención en ménsula (T invertida)

Subcarpeta `proyecto-muro-mensula/`. Muro C30/37 de **H = 6,20 m** (alzado 5,50 m +
zapata 0,70 m), zapata **B = 4,00 m** (puntera 1,00 + alzado 0,45 + talón 2,55).
Relleno granular γ = 19 kN/m³, φ = 30°, sobrecarga q = 10 kPa; terreno con resistencia
de cálculo R_d = 350 kPa y rozamiento base φ_b = 30°; empuje pasivo movilizado al 50 %
sobre 0,80 m de tierras en la puntera.

Tres bloques (desacoplados, predimensionado estándar):

**A) Empujes** (activo Rankine/Coulomb + sobrecarga + agua; pasivo en puntera):
- Ka (Rankine) = 0,333 → empuje horizontal característico **142,7 kN/m**.
- Integración numérica vs forma cerrada (0,5·Ka·γ·H² + Ka·q·H): **error 0,21 %**.

**B) Estabilidad EC7 (DA-2*)** [coeficientes NDP a confirmar con el AN España]:
- **Vuelco (EQU):** u = 0,44 — FS característico = 2,99 → OK.
- **Deslizamiento (GEO):** H_d = 196 / R_d = 222 kN → u = 0,88, FS car. = 1,83 → OK.
- **Hundimiento (GEO):** q_Ed = 186 / R_d = 350 kPa → u = 0,53; e = 0,409 m ≤ B/6,
  ancho eficaz de Meyerhof B' = 3,18 m → OK.

**C) Estructura EC2** (por metro de muro):
- **Alzado:** M_Ed(arranque) = 313 kN·m/m → A_s ≈ 19,5 cm²/m; cortante u = 0,79.
  El alzado se resuelve como ménsula vertical con el **solver de barras** (PyNite);
  el momento de base coincide con la solución analítica.
- **Puntera:** M = 85 kN·m/m → A_s ≈ 9,7 cm²/m.
- **Talón:** M = 284 kN·m/m → A_s ≈ 10,4 cm²/m.

Veredicto: **CUMPLE**.

```bash
python3 scripts/generate_test_ifc_muro.py
python3 scripts/run_all_muro.py proyecto-muro-mensula
NODE_PATH=$(npm root -g) node scripts/generate_memoria_muro.js proyecto-muro-mensula
```

## Arquitectura

| Script | Función |
|---|---|
| `generate_test_ifc_muro.py` | IFC4: alzado (surface member) + geometría + terreno + cargas en Psets |
| `solver_muro.py` | Empujes activo/pasivo (Rankine/Coulomb + agua), pesos, y **alzado como ménsula** (solver de barras) |
| `verificacion_muro.py` | EC7 vuelco/deslizamiento/hundimiento (B' Meyerhof) + EC2 alzado/puntera/talón |
| `plots_muro.py` | Sección, diagrama de empujes, presión bajo zapata, M(z) del alzado |
| `generate_memoria_muro.js` | Memoria de cálculo en Word |
| `run_all_muro.py` | Orquestador |
| `combinaciones.py` | Combinaciones EC0 (compartido con el núcleo) |

## Capacidades del modelo

- **Empuje activo** Rankine (β configurable) o **Coulomb** (con rozamiento muro-terreno
  δ → componente vertical del empuje).
- **Sobrecarga** uniforme en coronación (caso variable Q).
- **Nivel freático**: empuje hidrostático + peso efectivo del suelo sumergido (γ').
  Verificado: empuje de agua integrado = forma cerrada (0,5·γ_w·h_w²) con error nulo.
  Con freático alto el deslizamiento pasa a **REVISAR** (comportamiento correcto).
- **Empuje pasivo** movilizable en la puntera (fracción reductora) en el deslizamiento.

## Convenciones y decisiones

- X horizontal (0 = puntera), Z vertical; z hacia abajo desde coronación para empujes.
- Enfoque **DA-2*** (γ sobre efectos de acciones y sobre resistencias). Vuelco como EQU.
- Plano virtual de Rankine vertical en el extremo del talón; el peso de tierras sobre el
  talón actúa como estabilizador.
- Predimensionado: estados desacoplados; parámetros del terreno del estudio geotécnico.

---

## Caso 2: pantalla de contención anclada

Subcarpeta `proyecto-pantalla-anclada/`. Pantalla de hormigón C30/37 de **0,60 m** para
una **excavación de 7,0 m** con **empotramiento de 4,5 m** (L = 11,5 m) y **una fila de
anclas** (profundidad 1,5 m, inclinación 25°, separación 2,0 m; bulbo Ø200 mm, τ = 200 kPa).

Idealización (reutiliza el **solver de barras** y el modelo de **viga sobre muelles** del
pilote): el empuje activo del trasdós es la carga, el terreno delante del empotramiento son
**muelles horizontales** (balasto kh) que movilizan el pasivo, y el **ancla es un apoyo
horizontal** cuya reacción es la fuerza de anclaje.

- **Empotramiento (EC7, apoyo libre):** FoS del pasivo = **1,78 ≥ 1,5** → OK (M_pasivo/M_activo
  respecto al ancla). Con 3,0 m de empotramiento el FoS bajaba a 1,10 (REVISAR): el modelo
  detecta correctamente el empotramiento insuficiente.
- **Ancla:** se dimensiona por la **envolvente** de dos métodos —muelles (FE) = 138 kN/m y
  **apoyo libre = 183 kN/m** (gobierna)—. F_ancla = **403 kN** (sep. 2,0 m), **L_bulbo ≥ 6,4 m**,
  L_libre ≥ 6,9 m, **L_total ≥ 13,3 m**.
- **Fuste (EC2):** M_Ed = 251 kN·m/m → A_s ≈ 11,2 cm²/m; cortante u = 0,58.

Veredicto: **CUMPLE**. Equilibrio horizontal del modelo FE = **0,00 %**; validación cruzada
del empuje activo y del FoS con cálculo analítico independiente (FoS 1,79 vs 1,78; Ea 457,1 kN/m).

```bash
python3 scripts/generate_test_ifc_pantalla.py
python3 scripts/run_all_pantalla.py proyecto-pantalla-anclada
NODE_PATH=$(npm root -g) node scripts/generate_memoria_pantalla.js proyecto-pantalla-anclada
```

| Script | Función |
|---|---|
| `generate_test_ifc_pantalla.py` | IFC4: pantalla (curve member) + ancla + terreno + sobrecarga |
| `solver_pantalla.py` | Empujes activo/pasivo + viga sobre muelles con el ancla como apoyo (reusa coef. del muro y solver del pilote) |
| `verificacion_pantalla.py` | Empotramiento (free-earth) + ancla/bulbo (envolvente FE/apoyo libre) + fuste EC2 |
| `plots_pantalla.py` | Esquema, empujes activo/pasivo, M(z) del fuste, deformada |
| `generate_memoria_pantalla.js` | Memoria de cálculo en Word |
| `run_all_pantalla.py` | Orquestador |

**Decisiones clave de la pantalla:** el modelo de muelles (subgrade reaction) da la flecha y
el M(z) del fuste; el método de **apoyo libre** (free-earth) fija el FoS del empotramiento y,
por seguridad, la **fuerza del ancla se diseña con la envolvente** de ambos (el FE reparte más
pasivo en cabeza y subestima el ancla).

## Limitaciones / siguiente paso

Análisis lineal. El muro ménsula no incluye **sismo** (Mononobe-Okabe, EC8-5). La pantalla es
de **una fila de anclas**, sin **fases de excavación**, agua diferencial entre caras ni
pretensado del ancla; el pasivo no se acota en el modelo de muelles (lo fija el FoS de apoyo
libre). Extensiones naturales: **varias filas de anclas / fases constructivas**, y **sismo**.
**Todo es predimensionado: revisión y firma por técnico competente.**
