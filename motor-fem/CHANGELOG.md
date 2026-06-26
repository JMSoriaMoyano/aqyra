# Changelog — motor-fem

Todas las versiones siguen SemVer. Predimensionado/asistencia; revisar y firmar por técnico
competente (ICCP).

## v0.2.1 — 2026-06-23 · PT 7.2 (Ola 7) · extensión aditiva (sigue en FEM-1)

Extensión **aditiva menor** exigida por la **losa postesada** (lámina DKMQ): el motor **no sube
de peldaño** (sigue en FEM-1), solo amplía el barrido de cargas móviles. C5 §8 (añadir claves,
no cambiar semántica).

### Añadido
- **Objetivo `esfuerzo_lamina`** en `fem1.movil` (vía `_eval_objetivo`): líneas de influencia y
  envolventes LM1 de un **esfuerzo de placa** (`Mx`/`My`/`Mxy`/`Qx`/`Qy`/`Nx`/`Ny`/`Nxy` por
  unidad de ancho) en una lámina DKMQ objetivo. La carga unidad sigue aplicándose como fuerza
  nodal −Z sobre el camino; solo se recupera el esfuerzo de la lámina del `U` resultante.
- **Validación** (`validacion/fem1.py::il_lamina`): losa de una dirección (DKMQ, SS) — la IL del
  barrido móvil coincide con el esfuerzo de placa de un *solve* estático directo (**consistencia
  8.6e-15**) y la IL es **nula en los apoyos** (0.0).

### Sin cambios / no-regresión
- `fem_core.py`, `barra.py`, `lamina.py`, el estático FEM-0 y el resto de FEM-1 (modal + móvil de
  barra/reacción/desplazamiento) **intactos**: arnés FEM-0 (`test_fem_core.py`) y FEM-1 (modal +
  IL viga isostática/continua) **OK** tras la extensión.

## v0.2.0 — 2026-06-23 · PT 7.1 (Ola 7) · peldaño **FEM-1**

Sube el motor al peldaño **FEM-1** (capacidades nuevas, agnósticas a disciplina) **sin tocar**
el estático FEM-0 ni la librería de elementos: todo es **aditivo** (módulo `fem1.py`), de modo
que la no-regresión del *strangler* queda intacta por construcción.

### Añadido
- **Análisis MODAL** (`fem1.modal`): matriz de masas **concentrada** (lumped) — barra
  (ρAL/2 traslación + ρ·Ip·L/2 torsión) y lámina (ρ·área·t/4 por nudo) — más masa de **casos
  gravitatorios** (|Fz|/g) y **masas nodales**. Problema generalizado `Kφ=ω²Mφ` con
  `scipy.sparse.linalg.eigsh` (shift-invert, σ=0). Devuelve frecuencias, periodos, modos y
  **masa participante** por dirección.
- **CARGAS MÓVILES / LÍNEAS DE INFLUENCIA** (`fem1.movil`): barrido de carga unidad sobre un
  **camino** (nodos del modelo) reutilizando la **factorización estática** `splu(Kff)` (N solves
  baratos); **envolventes** de esfuerzos/reacciones por un **tren** (tándem + UDL) combinando las
  líneas de influencia, con **posiciones pésimas**. El núcleo es agnóstico a la normativa.
- **API C5 ampliada** (`resolver.py`): `analisis="modal"` y `"movil"` ya **implementados** (leen
  las claves `masas` y `cargas_moviles` del modelo). Ganchos restantes: `pandeo_lineal`,
  `no_lineal` (FEM-3+).
- **Arnés FEM-1** (`validacion/fem1.py`): modal de viga biapoyada y voladizo vs frecuencias
  cerradas (βₙL); líneas de influencia de viga isostática (reacción y momento) vs solución
  analítica; equilibrio exacto de líneas de influencia en viga continua de 2 vanos.

### Validado
- Modal biapoyada (lumped, ne=20) err < 4e-5; voladizo f1–f3 0.1–0.7 %.
- IL reacción isostática err 3.5e-13; IL momento centro pico = a·b/L exacto; viga continua
  Σ(IL reacciones) = −1 con err 6.3e-13.
- **FEM-0 sin regresión**: analítico/NAFEMS/oráculo/casos 1–15 idénticos a v0.1.0.

### Decisiones (confirmadas con el ICCP, 23/06/2026)
- Masas del modal: **concentradas (lumped)**; rotaciones de flexión sin masa (clásico).
- Cargas móviles: **barrido directo** + envolvente por líneas de influencia.
- IAP-11 **no** vive en el núcleo (es normativa de `puentes`); el tren llega en magnitudes.

## v0.1.0 — 2026-06-23 · PT 7.0 (Ola 7) · peldaño **FEM-0**

Nace el **motor de elementos finitos propio y transversal** del ecosistema (núcleo
`numpy`/`scipy`), con estrategia *strangler* sobre PyNite (oráculo de validación, cero
regresión).

### Añadido
- **Librería de elementos** (`scripts/elementos/`):
  - `barra.py`: barra 3D de 12 GdL. Rigidez local **Euler-Bernoulli** (reproduce
    `Pynite.Member3D._k_unc`) con **conmutador Timoshenko** (Φ, áreas de cortante) por
    defecto desactivado; terna local idéntica a PyNite (vertical/horizontal/inclinada +
    rotación); **liberaciones de extremo** por condensación estática; **FER** de cargas de
    barra (uniforme/lineal/puntual/axial/**térmica** axil y gradiente).
  - `lamina.py`: cuadrilátero **DKMQ** (flexión+cortante Mindlin, Katili) + **membrana** con
    GdL de **drilling** (1/1000, Bathe) — reproduce `Pynite.Quad3D`. Esfuerzos por unidad de
    ancho `[Nx,Ny,Nxy,Mx,My,Mxy,Qx,Qy]`.
- **Ensamblador + solver** (`fem_core.py`): matriz de rigidez **dispersa** (tripletes
  COO/`scipy.sparse`), apoyos y **resortes**, solver **estático lineal** (`spsolve`),
  recuperación de esfuerzos y **reacciones**, comprobación de **equilibrio** (ΣF ≈ 0).
  Multi-caso resuelto una vez; combinaciones por **superposición**.
- **Mallador** (`mallador.py`): `desde_modelo_neutro` (modelo neutro C1 → malla FEM C5) y
  **adaptador espejo** `desde_pynite` (replica un `FEModel3D` en el núcleo propio: pieza
  clave del *strangler*).
- **API estable (contrato C5)** (`resolver.py`): `resolver(modelo, analisis="estatico_lineal",
  combos)`. Ganchos reservados: `modal`, `pandeo_lineal`, `no_lineal`, `movil`.
- **Arnés de validación** (`scripts/validacion/`): `analitico.py` (viga/voladizo/axil/torsión
  EB + placa Timoshenko), `oraculo_pynite.py` (pórtico + placa vs PyNite), `nafems.py` (patch
  test de membrana + placa SS), `no_regresion.py` (casos 1–15) + `test_fem_core.py`.
- **Núcleo transversal espejado** (`scripts/nucleo/`): `ifc_utils.py`, `grafo_red.py`,
  `test_grafo_red.py`, `README.md` — **byte a byte** del canónico (puerta
  `verificar_espejo_nucleo.py`).
- **Contrato C5** (`Nucleo-transversal/C5_Contrato-motor-FEM.md`).

### Validado (sin regresión)
- Barra `k` vs PyNite ≈ 2e-10; lámina `K` vs PyNite ≈ 1e-16.
- Analítico (EB) exacto; placa vs Timoshenko 1–2.5 % (< 5 %); patch test de membrana 5.6e-16.
- Oráculo PyNite: pórtico (despl 2e-17, reac 3e-11, esf 4e-11), placa (despl/M exactos).
- No-regresión `resultados.json`: caso-01 (barra) 4e-11; caso-03 (placa real, 2646 GdL) Rz
  pilar 0.0, M rel 1.3e-11.

### Decisiones (confirmadas con el ICCP)
- Barra **EB + conmutador Timoshenko** (el oráculo PyNite es EB → cero regresión).
- **Mallador en `motor-fem`** (junto al núcleo).
- C5: **estático lineal + ganchos reservados** (modal/pandeo/no-lineal/móvil para FEM-1+).
