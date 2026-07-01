INICIO de hilo — PT 7.0 (Ola 7, **arranque**): nace el plugin transversal **`motor-fem`**
y el peldaño **FEM-0** (núcleo lineal propio), con **estrategia *strangler* sobre PyNite**

Proyecto Estructurando. Ejecuta el **PT 7.0 de la Ola 7 (puentes)**: **NACE el motor de
elementos finitos propio** como **capacidad transversal** en un plugin nuevo `motor-fem`
(núcleo numpy/scipy), el cimiento sobre el que se construirán todas las tipologías de
puente (Ola 7), las estructuras singulares / cubiertas laminares (Ola 3) y, en su
horizonte no-lineal, las tensoestructuras. Este PT **no entrega ninguna tipología de
puente todavía**: entrega el **motor** (peldaño FEM-0) y el **contrato C5**, validados y
sin regresión. Es el equivalente, para el cálculo, de lo que el PT 4.1 fue para el grafo
de red.

**Alcance confirmado con el ICCP (decisiones de la planificación, 23/06/2026):**
- **Motor FEM = plugin transversal `motor-fem`** (núcleo propio numpy/scipy), NO dentro de
  `motor-calculo-estructural`. Capacidad compartida por puentes, singular y tensoestructuras.
- **Estrategia *strangler* sobre PyNite:** PyNite (motor actual: barras + lámina plana
  MITC4) se mantiene como **oráculo de validación** mientras se construye el núcleo propio
  en paralelo; **cero regresión** en los casos 1–15; PyNite se **deprecia por fases**.
- **Secuencia de tipologías por madurez del FEM** (no toca este PT, pero lo orienta):
  lineales → avanzadas → no-lineales.
- **Acciones IAP-11** (carretera) — tampoco toca este PT (entra en PT 7.1); aquí solo se
  construye el **motor**.

**Dónde encaja en la Ola 7 (mapa de la ola, para situar este hilo):**
- **PT 7.0 (este hilo) — Cimiento del motor FEM (FEM-0):** nace `motor-fem`; núcleo lineal
  propio (barra 3D + lámina plana), ensamblaje disperso, **estático lineal**, apoyos/
  resortes; **strangler** vs PyNite; **contrato C5**; arnés de validación (analítico +
  oráculo PyNite + primeros NAFEMS); **casos 1–15 sin regresión**.
- **PT 7.1 — Disciplina `puentes` + IAP-11 + cargas móviles (FEM-1):** nace el plugin
  `puentes`; primer vertical (vigas pretensadas). **Depende de este PT.**
- **PT 7.2…7.7 —** resto de tipologías por madurez (ver hoja de ruta dedicada).

> **Frontera (contratos del núcleo):** la **lectura/escritura IFC y el modelo neutro
> estructural** viven en `iso19650-openbim` (C1) y no se tocan. El **cálculo FEM** (mallado,
> ensamblaje, solver) vive en `motor-fem` (contrato **C5**, nuevo), que **consume el modelo
> neutro estructural** (C1 §2) y devuelve esfuerzos/desplazamientos/modos. `motor-calculo-
> estructural` pasa a ser **consumidor** del núcleo (sus verticales llaman al núcleo en vez
> de a PyNite, **sin cambiar su normativa**), pero **en este PT no se migra todavía**: el
> núcleo propio se construye y se valida **en paralelo** (strangler); la migración de los
> verticales es de PTs posteriores. PyNite es **solo oráculo de test**, no se invoca en
> producción del núcleo nuevo.

**Lee primero, en este orden:**
1. `Hoja-de-ruta_Ola7-puentes-y-motor-FEM.md` — **§1–§3** (principio rector motor
   transversal + verticales; arquitectura de `motor-fem`; **escalera de capacidades FEM-0…
   FEM-5**, este hilo es **FEM-0**), **§8** (contrato **C5**: modelo de análisis FEM + API
   del solver + arnés de validación NAFEMS) y **§10** (decisiones abiertas que tocan a este
   PT: ubicación del mallador; `puentes` como plugin propio —no en este hilo—).
2. **El motor actual a espejar/validar (PyNite) — la fuente de verdad de FEM-0:**
   `motor-calculo-estructural` (v0.23.0, dentro del `.plugin`):
   `scripts/barras/solver.py` (barras 3D con PyNite `FEModel3D`),
   `scripts/laminas/solver_flat.py` y `scripts/laminas/solver_3d.py` (mixto barras + placa
   **MITC4**; esfuerzos de placa `[Mx, My, Mxy]`),
   `scripts/laminas/plate_validation.py` (**certificación de la placa vs Timoshenko** — el
   patrón analítico ya existe, reúsalo),
   `scripts/barras/combinaciones.py` (combinaciones ELU/ELS). El **núcleo propio FEM-0 debe
   reproducir estos resultados** dentro de tolerancia.
3. `Nucleo-transversal/C1_Contrato-IFC-modelo-neutro.md` — **§2** (esquema del **modelo
   neutro estructural**: `unidades`/`materiales`/`secciones`/`nodos`/`barras`/`superficies`/
   `cargas`; apoyos como vector de 6 GdL; las **dos colocaciones de cargas** 1D raíz vs 2D
   en `superficies[].cargas`) y **§3** (cómo extender el esquema sin romperlo). El **modelo
   de análisis FEM (C5)** extiende este modelo neutro con `mallas`/`elementos`/`laminados`/
   apoyos-resorte/cargas-móviles.
4. Casos de referencia para la **no-regresión** (oráculo): `Casos-de-uso/caso-01`…`caso-15`
   (pórtico acero, forjado losa+vigas, losa plana, cubierta inclinada, soporte-zapata,
   mixto, muros, losa de cimentación, cimentación profunda, edificio integrado, pantalla
   sísmica EC8, vigas/losas postesadas, núcleo sísmico). Cada uno tiene su `modelo_neutro.
   json` y su `resultados.json`/`verificacion.json` — el núcleo propio debe **reproducirlos**.
5. `Nucleo-transversal/verificar_espejo_nucleo.py` y `verificar_empaquetado.py` (las
   puertas) + `Nucleo-transversal/nucleo/` (canónico del grafo+ifc_utils, a espejar también
   en `motor-fem`). `criterios-despacho.md` (raíz) + la skill `criterios-memoria` del motor.

**Objetivo y alcance (qué hay que hacer):**
1. **Nace el plugin `motor-fem` (v0.1.0)**: `.claude-plugin/plugin.json` (`description`
   ≤500), `README.md`, `CHANGELOG.md`, `scripts/` (el núcleo FEM) y `scripts/nucleo/`
   **espejado byte a byte** del motor canónico (la puerta `verificar_espejo_nucleo.py`
   debe dar **ESPEJOS IDÉNTICOS**). Sin agente todavía (es núcleo, no disciplina; el agente
   de puentes nace en PT 7.1).
2. **Contrato C5 — modelo de análisis FEM + API del solver.** Documenta en
   `Nucleo-transversal/C5_Contrato-motor-FEM.md`: (a) el **modelo de análisis** (extiende
   C1 §2 con `mallas`/`elementos` —tipo `barra|lamina`—, `laminados`, apoyos con **resortes**,
   `casos`/`combinaciones`, `cargas`; solo **añade** claves, retrocompatible); (b) la **API**
   `resolver(modelo, analisis="estatico_lineal")` → esfuerzos/desplazamientos/reacciones;
   (c) el **arnés de validación** (puerta de calidad del núcleo).
3. **Librería de elementos FEM-0** (`scripts/elementos/` o similar, numpy):
   - **Barra 3D** (Timoshenko, 6 GdL/nudo): matriz de rigidez local, transformación a
     globales, cargas de barra (puntual/uniforme/térmica), liberaciones de extremo.
   - **Lámina plana cuadrilátera** (membrana con **DOF de drilling** + flexión **Mindlin-
     Reissner tipo MITC4**, para casar con la placa actual): esfuerzos por unidad de ancho
     `[Nx, Ny, Nxy, Mx, My, Mxy]` + cortantes. Triángulo como degeneración/respaldo.
4. **Ensamblador + solver** (`scripts/fem_core.py`): ensamblaje **disperso**
   (`scipy.sparse`), aplicación de apoyos (incl. **resortes**) y cargas, **solver estático
   lineal** (`scipy.sparse.linalg.spsolve`), recuperación de esfuerzos y **reacciones**;
   comprobación de **equilibrio** (ΣF, ΣM ≈ 0) como cierre interno.
5. **Mallador** (`scripts/mallador.py`): del **modelo neutro estructural** (C1 §2) a la
   **malla FEM** (barras → elementos barra; `superficies` → malla de láminas, reutilizando
   la convención de `add_rectangle_mesh` del solver actual; nodos compartidos viga-losa-
   pilar por tolerancia). **Decisión abierta:** ¿el mallador vive en `motor-fem` o como
   adaptador en `motor-calculo-estructural`? (recomendado: en `motor-fem`).
6. **Arnés de validación (la pieza clave del strangler)** `scripts/validacion/`:
   - **Parches analíticos**: viga (flecha/esfuerzos cerrados), **placa Timoshenko**
     (reúsa/portea `plate_validation.py`), barra a torsión/axil.
   - **Oráculo PyNite**: ejecuta el mismo modelo con PyNite y con el núcleo propio y
     contrasta esfuerzos/desplazamientos dentro de **tolerancia documentada** `[confirmar
     AN]`. PyNite vive en otro plugin (aislamiento de runtime) → el contraste se hace **en
     desarrollo/test** (no en producción), p. ej. desde un script de validación que importa
     ambos, o contra los `resultados.json` de referencia.
   - **Benchmarks NAFEMS** (primeros): al menos un *patch test* de membrana y uno de placa.
   - **No-regresión casos 1–15**: re-resolver con el núcleo propio y contrastar contra los
     `resultados.json`/`verificacion.json` de referencia. **Veredicto: SIN REGRESIÓN.**
7. **Micro-test** `scripts/test_fem_core.py` (rigidez de barra vs analítico; equilibrio;
   simetría/positividad de K; placa vs Timoshenko; un patch test).

**Decisiones a resolver y documentar (antes de mover una línea):**
- **Formulación de elementos:** barra **Timoshenko vs Euler-Bernoulli** (recomendado
  Timoshenko, casa mejor con PyNite y con vigas cortas); lámina **MITC4** (para reproducir
  la placa actual) vs DKQ; tratamiento del **DOF de drilling** (rigidez ficticia de
  Allman/penalti) para acoplar membrana+flexión en 6 GdL/nudo (necesario para vigas+losa
  coplanares y para el futuro acoplamiento con rigidizadores). `[confirmar AN]`.
- **Solver disperso:** `spsolve` directo (suficiente para predimensionado) vs iterativo
  (CG/AMG) — recomendado directo ahora, gancho para iterativo. `[confirmar AN]`.
- **Tolerancia del strangler:** qué desviación relativa se admite entre núcleo propio y
  PyNite/analítico (p. ej. 1e-3 en desplazamientos, 1e-2 en esfuerzos de placa). `[confirmar AN]`.
- **Ubicación del mallador** (en `motor-fem` recomendado) y **alcance del contrato C5**
  (qué claves del modelo de análisis se fijan ya y cuáles se dejan como gancho para FEM-1+:
  `cargas_moviles`, `modos`, `no_lineal`).
- **Convención de ejes y de esfuerzos**: respetar las del motor actual (X,Y horizontales,
  Z vertical, gravedad −Z; barras `Iy`=inercia mayor; placa `[Mx,My,Mxy]` por unidad de
  ancho) para que la no-regresión sea directa.

**Entregable:**
- Plugin **`motor-fem` v0.1.0** (FEM-0): `scripts/` (núcleo: elementos barra+lámina,
  `fem_core`, `mallador`, `validacion`, `test_fem_core`), `scripts/nucleo/` **espejado**,
  `README.md` + `CHANGELOG.md` + `.claude-plugin/plugin.json` (`description` ≤500).
- `Nucleo-transversal/C5_Contrato-motor-FEM.md` (modelo de análisis FEM + API + arnés).
- **Informe de strangler** (en `Casos-de-uso/` o en el README): contraste núcleo propio vs
  PyNite/analítico + **no-regresión casos 1–15** con la tolerancia documentada.
- **Actualizar**: la hoja de ruta dedicada (PT 7.0 ✅ → PT 7.1 🔜; estado de FEM-0), la hoja
  de ruta maestra (fila `motor-fem` y Ola 7; registro de versiones), `criterios` (lección +
  INC si aplica) y el `CHANGELOG.md` del plugin.
- **Puertas de calidad obligatorias** (pega su salida en el cierre):
  `PYTHONPATH=/tmp/pylibs python3 Nucleo-transversal/verificar_empaquetado.py
  motor-fem-v0.1.0.plugin` (**APTO**, exit 0; `description` ≤500) **y**
  `verificar_espejo_nucleo.py --canonico <motor>.plugin motor-fem-v0.1.0.plugin`
  (**ESPEJOS IDÉNTICOS**) **y** el **arnés de validación** (analítico + oráculo PyNite +
  NAFEMS + **casos 1–15 SIN REGRESIÓN**).

**Notas de método (críticas, confirmadas en PT 4.x/5.x/6.x):** las herramientas de fichero
(Read/Write/Edit) son la **fuente de verdad**; el **shell del sandbox trunca la lectura** de
ficheros de texto **pre-existentes** del mount **aunque se reescriban** (en PT 6.3:
`plugin.json` se leyó truncado a 66 líneas; el parser editado a 451), pero **los ficheros
NUEVOS de la sesión se leen íntegros** y los `.plugin` (ZIP) **extraen íntegros**. Por tanto:
para empaquetar, **reconstruye el `.plugin` en `/tmp`** (ficheros nuevos copiados del
workspace + pre-existentes editados **parcheados con Python** desde el ZIP base íntegro +
`verificar_empaquetado.py` reconstruido desde `Read`). El **espejo del núcleo** se copia del
ZIP del motor (canónico) y se verifica con `verificar_espejo_nucleo.py`. **Toolchain ya
disponible en `/tmp/pylibs`: numpy 2.2.6, scipy 1.15.3, PyNite 2.0.2, ifcopenshell 0.8.5** →
ejecuta con `PYTHONPATH=/tmp/pylibs`. A diferencia de los solvers hidráulicos (stdlib pura),
el **núcleo FEM usa numpy/scipy** (no es stdlib). El `.plugin` de la raíz: **construye el ZIP
en `/tmp` y cópialo con `cat > destino`/`cp`**, con **nombre versionado** (no sobrescribas),
excluyendo `__pycache__`/`*.pyc`. Todo es **predimensionado, a revisar y firmar por técnico
competente** (Ingeniero de Caminos); NDP marcados `[confirmar AN]`.

**Empieza** leyendo los documentos (sobre todo la **hoja de ruta dedicada §3/§8**, los
**solvers PyNite actuales** —`barras/solver.py`, `laminas/solver_flat.py`/`solver_3d.py`,
`plate_validation.py`— como referencia a reproducir, **C1 §2/§3** del modelo neutro y el
**espejo del núcleo**), y **proponiendo, antes de mover una sola línea: (a)** la estructura
del plugin `motor-fem` y el **esquema del modelo de análisis FEM (C5)** (qué claves añade al
modelo neutro, API del solver); **(b)** las **formulaciones de elemento** (barra Timoshenko,
lámina MITC4 con drilling) y el **ensamblador/solver disperso**; y **(c)** el **plan de
strangler/validación** (parches analíticos + oráculo PyNite + NAFEMS + no-regresión de los
casos 1–15, con la tolerancia propuesta).
