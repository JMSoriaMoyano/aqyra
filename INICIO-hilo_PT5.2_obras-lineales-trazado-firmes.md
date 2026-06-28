# INICIO de hilo — PT 5.2 (Ola 5): nace la disciplina `obras-lineales` (trazado 3.1-IC + firmes 6.1-IC)

Proyecto Estructurando. Ejecuta el **PT 5.2 de la Ola 5**: **crear la disciplina vertical
`obras-lineales`** — su **plugin único** (decisión nº2, ya confirmada), su **agente
`ingeniero-de-obra-lineal`** y los **dos primeros subagentes**, **trazado** (Norma 3.1-IC) y
**firmes** (Norma 6.1-IC), montados **encima del soporte georreferenciado** que abrió el PT 5.1
(`iso19650-openbim` v0.5.0). Es el **análogo lineal de lo que el PT 4.3 hizo con `instalaciones`**:
allí nació la disciplina de instalaciones sobre el dominio IFC MEP; aquí nace la disciplina de obra
lineal sobre el **modelo neutro lineal** (IFC 4.3 Alignment + georref). **Trazado y firmes son
geometría + normativa: NO hay FEM ni solver de red.**

**Ojo a la frontera (igual que `instalaciones`):** la **lectura/validación del IFC** (alineación +
georref) vive en `iso19650-openbim` (parser `scripts/lineal/ifc_to_model_lineal.py`, ya hecho); el
**cálculo de trazado y el dimensionado de firmes** viven en el nuevo plugin `obras-lineales`, que
**consume el modelo neutro lineal** (JSON), no el IFC directamente. **Este PT NO toca el dominio de
drenaje ni las obras hidráulicas** (eso es la **Ola 6**, que reutilizará el motor hidráulico de red);
la alineación sigue siendo **referenciación lineal por PK (curva 1D)**, **no** un grafo de red — **no
uses `grafo_red`**.

**Lee primero, en este orden:**
1. `Hoja-de-ruta_Ecosistema-ingenieria.md` — §2 (heurística plugin/skill/agente/subagente y **patrón
   de agente de disciplina**: clasificar→enrutar→orquestar→verificar→visualizar→memoria→registrar),
   §3 (multi-plugin; convención `description` ≤ 500; **un plugin por disciplina**), §4 (contratos
   C1 + CN-1/CN-2/CN-3; **CN-3 en obra lineal**: acción del tráfico, y para firmes la categoría de tráfico pesado),
   §5 (disciplina **Obras lineales**: agente `ingeniero-de-obra-lineal` a crear; tipologías
   **trazado/firmes**/drenaje/hidráulica — aquí solo las dos primeras), §6 (olas; este hilo es **Ola
   5, PT 5.2**; la Ola 6 hace drenaje/hidráulica) y §8 (**decisión nº2 ya resuelta**: plugin único
   `obras-lineales` con subagentes; déjala documentada como implementada).
2. `Nucleo-transversal/C1_Contrato-IFC-modelo-neutro.md` — **§4bis** (dominio de obra lineal: el
   **modelo neutro lineal** ya implementado en PT 5.1 —`alineacion{planta[]/alzado[]/peralte[]}`,
   `georref`, ganchos `secciones_tipo`/`firme`/`terreno`— y el checklist de la vía Alignment marcado
   ✅) y §6 (checklist C1 para una disciplina nueva). **Este PT RELLENA los ganchos**
   `secciones_tipo`/`firme`/`terreno` que el PT 5.1 dejó previstos (= None).
3. `Nucleo-transversal/CN-1_Convencion-memoria-despacho.md` y `CN-2_Convencion-entregables-documentacion.md` (antes C2/C3, reconciliados 2026-06-27) +
   `plantilla-criterios-disciplina.md` + `plantilla-memoria.md` — cómo nace la **memoria de la
   disciplina** (`criterios-obra-lineal.md` en la raíz + memoria por obra) y la **skill
   `criterios-memoria`** del nuevo plugin, homogénea con la de `instalaciones`/estructuras.
4. **El patrón a imitar — `instalaciones/`** (plugin de disciplina maduro): su `.claude-plugin/
   plugin.json`, `agents/ingeniero-de-instalaciones.md` (clasifica el sistema, enruta al subagente y al
   solver), `agents/proyectista-*.md` (subagentes por vertical), `scripts/<vertical>/` (bases de
   demanda + cálculo + verificación + run_all + write-back) y `skills/criterios-memoria/`. **Replica
   esta estructura** para `obras-lineales` (agente + subagentes `proyectista-de-trazado` y
   `proyectista-de-firmes`; `scripts/trazado/` y `scripts/firmes/`).
5. **Punto de partida (PT 5.1, `iso19650-openbim` v0.5.0):** `iso19650-openbim/scripts/lineal/` —
   `ifc_to_model_lineal.py` (emite el modelo neutro lineal por PK), `validacion_alineacion.py`
   (continuidad/tangencia/georref) y `export_gis.py`. Estúdialos: **tu cálculo de trazado consume su
   salida**. Caso e2e de referencia: `Casos-de-uso/caso-LIN-01-eje-carretera` (modelo neutro lineal +
   GeoJSON ya disponibles). Memoria del hilo: `estructurando-pt51-alignment-gis`.
6. `criterios-despacho.md` (raíz) y `Casos-de-uso/REPOSITORIO-aprendizaje.md` — lección **PT 5.1**
   (apertura del dominio lineal; frontera PK 1D ≠ grafo de red; hazard de mount), lección **PT 4.3**
   (nacimiento de una disciplina sobre un modelo neutro; frontera lectura IFC ↔ demanda/cálculo de la
   disciplina), **INC-09** (puerta de empaquetado obligatoria) y el **hazard de mount** (método abajo).

**Objetivo y alcance (qué hay que hacer):**
1. **Nace el plugin `obras-lineales` (v0.1.0).** `.claude-plugin/plugin.json` (`description` ≤ 500,
   paralela a las demás; `keywords` para descubrimiento), `README.md`, `CHANGELOG.md` y la skill
   `criterios-memoria` (C2/C3). Agente **`ingeniero-de-obra-lineal`**: a partir de un IFC 4.3 (o del
   modelo neutro lineal ya extraído) **clasifica** el encargo (¿trazado?, ¿firmes?, ¿ambos?),
   **enruta** al subagente, **orquesta** el flujo (IFC → modelo neutro lineal [de `iso19650-openbim`]
   → comprobación/dimensionado → verificación normativa → memoria) y **ensambla** el entregable.
2. **Subagente `proyectista-de-trazado` (Norma 3.1-IC).** Sobre la `alineacion` del modelo neutro
   lineal, comprueba el **trazado en planta y alzado** para una **velocidad de proyecto Vp**
   (parámetro de proyecto, `[confirmar AN]`): radios mínimos en planta vs Vp, **parámetro A y longitud
   de clotoide** (límites de la 3.1-IC), **acuerdos verticales** (Kv mínimo convexo/cóncavo vs Vp),
   **pendientes máximas/mínimas**, **coordinación planta-alzado**, y **distancias de visibilidad**
   (parada/adelantamiento) como comprobación informativa. `scripts/trazado/` con un módulo de
   comprobación + verificación + `run_all_trazado.py` + micro-test. **No rediseña el eje**: comprueba
   y reporta CUMPLE/NO CUMPLE + propuestas (predimensionado).
3. **Subagente `proyectista-de-firmes` (Norma 6.1-IC).** A partir de la **categoría de tráfico pesado**
   (de la IMDp/IMD y % de pesados — dato de proyecto que inyecta el agente, `[confirmar AN]`) y de la
   **categoría de explanada** (E1/E2/E3 según CBR/formación), selecciona la **sección de firme** del
   **catálogo de la 6.1-IC** (paquete de capas: mezclas bituminosas / firmes semirrígidos / etc.),
   y **rellena el gancho `firme`** del modelo neutro lineal (`{categoria_trafico, explanada,
   paquete[]}`). `scripts/firmes/` con bases (categoría tráfico/explanada) + selección de sección +
   verificación + `run_all_firme.py` + micro-test. (6.3-IC de rehabilitación queda fuera de este PT.)
4. **Rellenar los ganchos del modelo neutro lineal.** El PT 5.1 dejó `secciones_tipo`, `firme` y
   `terreno` = None; este PT los **rellena** (al menos `firme` y, si procede, una `seccion_tipo`
   básica), **sin redefinir** las claves existentes (retrocompatible, modelo hermano).
5. **Caso(s) e2e.** Reutiliza/crea un eje (puedes partir de `caso-LIN-01`): **`caso-LIN-02-trazado`**
   (3.1-IC: planta/alzado/visibilidad para una Vp → CUMPLE/NO CUMPLE razonado) y
   **`caso-LIN-03-firmes`** (6.1-IC: categoría de tráfico + explanada → sección de firme → `firme`
   relleno), cada uno con su README y memoria. Si el alcance se hace grande, **prioriza trazado** y
   deja firmes como sub-entrega.
6. **(Opcional, si entra) write-back / visual.** Enriquecer el IFC con un Pset de resultado de obra
   lineal (vía `iso19650-openbim:ifc-create`, como hace `instalaciones`) y/o exportar a GIS la planta
   ya verificada. No bloqueante.

**Decisiones a resolver y documentar (antes de mover una línea):**
- **¿`obras-lineales` necesita espejar el núcleo `scripts/nucleo/`?** Recomendación por defecto:
  **NO** — trabaja sobre el **modelo neutro lineal (JSON)** que produce `iso19650-openbim`, igual que
  `instalaciones` trabaja sobre el modelo neutro de red; **no** usa `grafo_red` ni, en principio,
  `ifc_utils` (la lectura IFC ya la hace `iso19650-openbim`). Si finalmente lees IFC directamente o
  escribes Psets, decide si espejas `ifc_utils` (entonces pasa `verificar_espejo_nucleo.py`) o lo
  invocas vía la skill de `iso19650-openbim`. **Justifica y documenta.**
- **Datos de proyecto vs IFC (lección INC-12).** ¿De dónde salen **Vp** (trazado) y **categoría de
  tráfico/explanada** (firmes)? Propón: si están en un Pset del IFC, **prevalecen**; si no, los
  **inyecta el agente** y se documentan. Mantén el patrón "el dato del IFC prevalece".
- **Frontera trazado ↔ disciplina estructural (puentes, Ola 7).** Deja claro que el eje/alineación que
  produce esta disciplina es el que el **puente** (Ola 7) reutilizará; no construyas nada de puentes.
- **Catálogo de firmes:** ¿catálogo literal de la 6.1-IC (tablas de secciones por categoría de
  tráfico × explanada) o un dimensionado paramétrico? Recomendación: **catálogo** (es lo que manda la
  norma), con las secciones como datos; `[confirmar AN]`.

**Entregable:**
- Plugin **`obras-lineales` v0.1.0**: `agents/ingeniero-de-obra-lineal.md` +
  `agents/proyectista-de-trazado.md` + `agents/proyectista-de-firmes.md`; `scripts/trazado/` y
  `scripts/firmes/` (comprobación/dimensionado + verificación + run_all + micro-test); skill
  `criterios-memoria`; `README.md` + `CHANGELOG.md` + `.claude-plugin/plugin.json`.
- `criterios-obra-lineal.md` (raíz) inicializado (C2).
- Caso(s) e2e `Casos-de-uso/caso-LIN-02-trazado` (y `caso-LIN-03-firmes` si entra) que pasen de
  extremo a extremo (modelo neutro lineal → comprobación 3.1-IC / sección 6.1-IC → veredicto), con
  README y memoria.
- **Actualizar**: C1 §4bis (marcar los ganchos `firme`/`secciones_tipo` como rellenados por la
  disciplina), la **hoja de ruta** (Ola 5: PT 5.2 ✅; mapa de plugins + fila de `obras-lineales`;
  decisión nº2 implementada; entrada en el registro de versiones), `REPOSITORIO-aprendizaje.md`
  (lección + INC si aplica) y el `CHANGELOG.md` del nuevo plugin.
- **Puertas de calidad obligatorias** (pega su salida en el cierre):
  `PYTHONPATH=/tmp/pylibs python3 Nucleo-transversal/verificar_empaquetado.py
  obras-lineales-v0.1.0.plugin` (**APTO**, exit 0; sin `--ref` por ser v0.1.0, o `--ref` si haces una
  baseline). Si decides espejar el núcleo:
  `python3 Nucleo-transversal/verificar_espejo_nucleo.py --canonico
  motor-calculo-estructural-v0.23.0.plugin obras-lineales-v0.1.0.plugin` (**ESPEJOS IDÉNTICOS**). Si
  **no** espejas, no aplica esta segunda puerta (decláralo). `description` ≤ 500.

**Notas de método (críticas, confirmadas en PT 4.x/5.1):** las herramientas de fichero
(Read/Write/Edit) son la **fuente de verdad**; el shell del sandbox sirve copias **truncadas/stale**
de ficheros **pre-existentes** (incluidas las **puertas** `.py`, `plugin.json`, `.md` no editados en
el hilo), pero **los ficheros NUEVOS se leen íntegros** y los `.plugin` (ZIP) **extraen íntegros**.
Por tanto: para una puerta o fichero pre-existente que necesites ejecutar, **léelo con `Read`
(íntegro) y reconstrúyelo en `/tmp`** (verifica con `ast.parse`); autora los `.py` nuevos por
**heredoc en `/tmp`**, **prueba y empaqueta desde `/tmp`**, y persiste a la carpeta con `cp /tmp →
mount` **verificando con `Read`**. Toolchain Python en `/tmp/pylibs` (**ifcopenshell 0.8.5**, soporta
**IFC4X3**) → ejecuta con `PYTHONPATH=/tmp/pylibs`; trabaja por partes (el análisis puede superar ~45
s). El `.plugin` de la raíz puede estar bloqueado → **construye el ZIP en `/tmp` y cópialo con `cat >
destino`**, con **nombre versionado** (no sobrescribas), excluyendo `__pycache__`/`node_modules`/
`*.pyc`. Todo es **predimensionado, a revisar y firmar por técnico competente** (Ingeniero de
Caminos); NDP marcados `[confirmar AN]`.

**Empieza** leyendo los documentos (sobre todo el patrón `instalaciones/` y C1 §4bis) y el modelo
neutro lineal del PT 5.1, y **proponiendo: (a) la estructura del plugin** (agente + subagentes +
`scripts/trazado/firmes`; qué comprueba trazado de la 3.1-IC y qué selecciona firmes de la 6.1-IC;
cómo rellenas los ganchos del modelo neutro lineal), **(b) la resolución de las decisiones** (espejo
del núcleo sí/no; origen de Vp y categoría de tráfico/explanada; catálogo de firmes), y **(c) el
alcance del hilo** (trazado completo + firmes, o trazado primero y firmes como sub-entrega) — **antes
de mover una sola línea**.
