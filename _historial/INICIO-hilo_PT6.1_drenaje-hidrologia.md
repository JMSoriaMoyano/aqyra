# INICIO de hilo — PT 6.1 (Ola 6): nace el vertical `drenaje` (hidrología + Norma 5.2-IC)

Proyecto Estructurando. Ejecuta el **PT 6.1 de la Ola 6**: **arrancar las "obras lineales II"**
añadiendo a la disciplina `obras-lineales` (creada en el PT 5.2) su **tercer subagente**,
**`proyectista-de-drenaje`**, que cubre la **hidrología** (caudales de cálculo) y el **drenaje
superficial y transversal** de la carretera según la **Norma 5.2-IC** (Drenaje superficial). Es el
**análogo, para el agua de lluvia, de lo que trazado/firmes hicieron con la geometría y el firme**:
geometría + normativa + hidrología, **sobre la cuenca georreferenciada** que el PT 5.1 dejó lista
(puente GIS→cuencas, `export_gis.py` → GeoJSON). **Estrena la capacidad transversal CN-3 de
hidrología** (caudales de cálculo) que la hoja de ruta reservó para la Ola 6.

**Dónde encaja en la Ola 6 (mapa de la ola, para situar este hilo):**
- **PT 6.1 (este hilo) — Drenaje (5.2-IC):** hidrología (método racional, IDF), **drenaje
  superficial** (cunetas, capacidad por Manning de **sección simple**) y **obras de drenaje
  transversal (ODT)** (capacidad). Cálculo **local por elemento** (cada cuneta/ODT con su cuenca),
  **sin grafo de red** todavía → **no** espeja el núcleo, igual que trazado/firmes.
- **PT 6.2 — Obras hidráulicas (redes):** colectores de **saneamiento** en **lámina libre**
  (**nace el solver de Manning sobre el grafo de red**, decisión nº7 "grafo + N solvers") y
  **abastecimiento a presión** (reutiliza el solver Darcy-Weisbach del motor de red); pozos,
  depósitos; **EN 752 / EN 805**. Aquí **sí** se espeja el núcleo (`grafo_red`+`ifc_utils`) y se
  extiende el dominio IFC MEP a saneamiento/abastecimiento. *(No es este hilo; déjalo planteado.)*

> **Frontera (igual que en PT 5.2):** la **lectura del IFC y la georreferencia/coherencia** viven en
> `iso19650-openbim` (modelo neutro lineal + `export_gis.py` que produce la planta en GeoJSON, base
> de la cuenca); el **cálculo hidrológico y el dimensionado de cunetas/ODT** viven en
> `obras-lineales`, que **consume el JSON neutro lineal y/o el GeoJSON**, no el IFC directamente. La
> cuenca (área, longitud, pendiente, tiempo de concentración) es **dato hidrológico**: si está en el
> Pset/GIS **prevalece**; si no, lo **inyecta el agente** (`[confirmar AN]`). **No se toca el dominio
> de puentes (Ola 7) ni el motor de red (eso es PT 6.2).**

**Lee primero, en este orden:**
1. `Hoja-de-ruta_Ecosistema-ingenieria.md` — §4 (**capacidad transversal: motor hidráulico de red**
   y **CN-3 — hidrología/caudales de cálculo en obras lineales**), §5 (disciplina **Obras lineales**:
   tipologías **drenaje** —hidrología, drenaje superficial, ODT, 5.2-IC— y **obras hidráulicas**),
   §6 (olas; este hilo es **Ola 6, PT 6.1**; la Ola 6 reutiliza el motor hidráulico de la Ola 4) y
   §8 (**decisión nº4** núcleo de red espejado y **nº7** "grafo + N solvers": el solver Manning de
   lámina libre es de la Ola 6 — **pero el de red es PT 6.2**; este PT 6.1 usa Manning de sección
   simple, local).
2. `Nucleo-transversal/C1_Contrato-IFC-modelo-neutro.md` — **§4bis** (modelo neutro lineal: el
   gancho **`terreno` quedó en `None`** y se reservó para drenaje/movimiento de tierras; aquí decides
   si **añades un gancho `drenaje`** —caudales, cunetas, ODT— como clave nueva retrocompatible) y
   **§4** (modelo neutro de **red** MEP + `export_gis`/GeoJSON como puente a cuencas; relevante para
   el PT 6.2, ojéalo).
3. `criterios-obra-lineal.md` (raíz) + la skill `obras-lineales:criterios-memoria` + las plantillas
   `Nucleo-transversal/plantilla-criterios-disciplina.md` y `plantilla-memoria.md` — cómo crece la
   memoria de la disciplina (añade la sección de **hidrología/drenaje**, homogénea con trazado/firmes).
4. **El patrón a imitar — el propio `obras-lineales/` (PT 5.2)** y, para el cálculo hidráulico, el
   **motor de red de `instalaciones/`**: `obras-lineales/agents/ingeniero-de-obra-lineal.md`
   (clasifica trazado/firmes → **añade drenaje**), `agents/proyectista-de-trazado.md` y
   `proyectista-de-firmes.md` (estructura de subagente), `scripts/trazado/` y `scripts/firmes/`
   (bases→cálculo→verificación→run_all→micro-test). **Replica esa estructura** en
   `scripts/drenaje/` y crea `agents/proyectista-de-drenaje.md`. Mira también
   `instalaciones/scripts/red/solver_red.py` (Darcy/Hardy-Cross) **solo como referencia** del estilo
   del solver hidráulico — el Manning de **red** será el PT 6.2.
5. **Punto de partida georreferenciado (PT 5.1):** `iso19650-openbim/scripts/lineal/export_gis.py`
   (planta → GeoJSON LineString en CRS proyectado) y el caso `Casos-de-uso/caso-LIN-01-eje-carretera`
   (`eje-carretera.geojson`, `modelo_neutro_lineal.json`). La **cuenca** de cada tramo se apoya en
   esta planta/GeoJSON. Casos de obra lineal ya disponibles: `caso-LIN-02-trazado`,
   `caso-LIN-03-firmes`.
6. `Casos-de-uso/REPOSITORIO-aprendizaje.md` — lección **PT 5.2** (nacimiento de la disciplina sobre
   el modelo neutro; frontera lectura IFC ↔ cálculo; "el dato del IFC prevalece"; **sin espejo de
   núcleo** cuando el cálculo es local), lección **PT 5.1** (puente GIS/cuencas), **INC-09** (puerta
   de empaquetado obligatoria) y el **hazard de mount** (método abajo; en PT 5.2 golpeó a
   `plugin.json` recién editado).

**Objetivo y alcance (qué hay que hacer):**
1. **Nace el subagente `proyectista-de-drenaje` (Norma 5.2-IC)** dentro de `obras-lineales`
   (→ **v0.2.0**). El **agente `ingeniero-de-obra-lineal`** amplía su clasificación/enrutado para
   reconocer el encargo de **drenaje** (además de trazado/firmes) y orquestar el flujo
   (modelo neutro lineal + cuenca [GeoJSON/datos] → hidrología → capacidad de cuneta/ODT →
   verificación → memoria).
2. **Hidrología (CN-3 — caudales de cálculo).** `scripts/drenaje/hidrologia.py`: **método racional**
   de la 5.2-IC (`Q = C · I(T,tc) · A / 3.6`, con coeficiente de escorrentía C, intensidad de la
   **curva IDF** para el periodo de retorno T y el tiempo de concentración tc, área de cuenca A),
   tiempo de concentración (p. ej. Témez `tc = 0.3·(L/J^0.25)^0.76`), y **periodos de retorno por
   tipo de elemento** (drenaje de plataforma, ODT…) — todos NDP **[confirmar AN]**. La **cuenca**
   (A, L, J) se toma del GIS/Pset si está (**prevalece**) o se inyecta.
3. **Drenaje superficial — cunetas.** `scripts/drenaje/cuneta.py`: **capacidad por Manning de
   sección simple** (triangular/trapezoidal) en lámina libre (`Q = (1/n)·A·R^(2/3)·J^(1/2)`),
   calado normal, resguardo, velocidad (autolimpieza/erosión) → **CUMPLE/NO CUMPLE** vs el caudal de
   cálculo. (Sección simple, **sin grafo de red**.)
4. **Drenaje transversal — ODT.** `scripts/drenaje/odt.py`: **capacidad de una obra de drenaje
   transversal** (tubo/marco) por control de entrada/salida (criterio simplificado, lámina libre o
   en carga) → comprobación frente al caudal de la cuenca vertiente; dimensión mínima y velocidad.
5. **Verificación + run_all + micro-test.** `verificacion_drenaje.py` (recuento + veredicto, análogo
   a `verificacion_trazado`), `run_all_drenaje.py` (CLI: modelo + cuenca/periodo → caudal → cuneta/ODT
   → veredicto + JSON) y `test_drenaje.py` (micro-test positivo + negativos).
6. **Gancho del modelo neutro.** Decide y documenta: **añadir** la clave **`drenaje`**
   (`{cuencas[], cunetas[], odt[], caudales}`) al modelo neutro lineal (clave **nueva**,
   retrocompatible; **no** redefinir las existentes), dejando claro su relación con el `terreno`
   reservado. Rellénala como hicieron firmes con `firme`.
7. **Caso(s) e2e.** `Casos-de-uso/caso-LIN-04-drenaje`: a partir del eje de `caso-LIN-01`/su GeoJSON,
   una cuenca de plataforma → caudal de cálculo (racional, T=25 [confirmar AN]) → **cuneta** que
   cumple, y una **ODT** para una cuenca vertiente → veredicto **CUMPLE/NO CUMPLE razonado**, con
   README y memoria. (Si el alcance se agranda, **prioriza la cuneta + hidrología** y deja la ODT como
   sub-entrega.)
8. **(Opcional, no bloqueante)** write-back de un Pset de resultado de drenaje al IFC
   (`Pset_Estructurando_ResultadoLineal` ampliado o uno nuevo) vía `iso19650-openbim:ifc-create`, y/o
   export GIS de las cuencas. No bloqueante.

**Decisiones a resolver y documentar (antes de mover una línea):**
- **¿`obras-lineales` necesita ya espejar el núcleo `scripts/nucleo/`?** Recomendación por defecto:
  **NO en PT 6.1** — la cuneta/ODT son **Manning de sección simple**, cálculo **local por elemento**
  (como trazado/firmes), sobre el JSON neutro lineal; no hay topología de red. El **grafo_red + el
  espejo + el dominio IFC de saneamiento entran en PT 6.2** (colectores). **Justifícalo y déjalo
  escrito** (si finalmente lees IFC de red o resuelves una red, entonces espejas y pasa
  `verificar_espejo_nucleo.py`).
- **Origen de la cuenca (lección INC-12 / "el dato del IFC prevalece").** ¿De dónde salen **A, L, J**
  de la cuenca y el **periodo de retorno T**? Propón: del **GIS/Pset** si están (prevalecen); si no,
  los **inyecta el agente** y se documentan `[confirmar AN]`. Define la **fuente de la IDF**
  (curva regional / `Máx. lluvia diaria en la España peninsular` o IDF de proyecto) como NDP.
- **Hidrología — método.** Recomendación: **método racional 5.2-IC** (con tc de Témez y C de la 5.2-IC)
  como base de predimensionado; deja gancho para hidrogramas si hiciera falta. `[confirmar AN]`.
- **Gancho `drenaje` vs `terreno`.** Decide si el resultado de drenaje va a una clave nueva `drenaje`
  (recomendado) y qué relación guarda con el `terreno` reservado (que seguirá para
  geotecnia/movimiento de tierras). **No redefinas** claves existentes.
- **Frontera con PT 6.2.** Deja explícito que las **redes de colectores/abastecimiento** (grafo +
  Manning/Darcy + IFC MEP de saneamiento) son del PT 6.2; este PT 6.1 es drenaje **local**.

**Entregable:**
- Plugin **`obras-lineales` v0.2.0**: `agents/proyectista-de-drenaje.md` + agente
  `ingeniero-de-obra-lineal.md` ampliado (clasifica/enrutar drenaje); `scripts/drenaje/`
  (`hidrologia.py` + `cuneta.py` + `odt.py` + `verificacion_drenaje.py` + `run_all_drenaje.py` +
  `test_drenaje.py`); `README.md` + `CHANGELOG.md` + `.claude-plugin/plugin.json` (`description`
  ≤ 500, actualizada al alcance drenaje) y, si procede, la skill `criterios-memoria` retocada.
- `criterios-obra-lineal.md` (raíz) ampliado con **Normativa 5.2-IC, hidrología y criterios de
  drenaje**.
- Caso e2e `Casos-de-uso/caso-LIN-04-drenaje` (cuenca → caudal → cuneta/ODT → veredicto) con README y
  memoria.
- **Actualizar**: C1 (gancho `drenaje` si se añade; relación con `terreno`), la **hoja de ruta**
  (Ola 6: **PT 6.1 ✅**; fila de `obras-lineales` a v0.2.0; entrada en el registro de versiones; mapa
  de la Ola 6 con PT 6.2 pendiente), `REPOSITORIO-aprendizaje.md` (lección + INC si aplica) y el
  `CHANGELOG.md` del plugin.
- **Puertas de calidad obligatorias** (pega su salida en el cierre):
  `PYTHONPATH=/tmp/pylibs python3 Nucleo-transversal/verificar_empaquetado.py
  obras-lineales-v0.2.0.plugin --ref obras-lineales-v0.1.0.plugin` (**APTO**, exit 0; `description`
  ≤ 500). Si **no** espejas el núcleo (recomendado), `verificar_espejo_nucleo.py` **no aplica**
  (decláralo); si lo espejas, pásalo (**ESPEJOS IDÉNTICOS**).

**Notas de método (críticas, confirmadas en PT 4.x/5.x):** las herramientas de fichero
(Read/Write/Edit) son la **fuente de verdad**; el shell del sandbox sirve copias **truncadas/stale**
de ficheros **pre-existentes** o **recién editados** (en PT 5.2 le ocurrió a `plugin.json` editado),
pero **los ficheros NUEVOS se leen íntegros** y los `.plugin` (ZIP) **extraen íntegros**. Por tanto:
para una puerta o fichero pre-existente que necesites ejecutar, **léelo con `Read` (íntegro) y
reconstrúyelo en `/tmp`** (verifica con `ast.parse`); autora los `.py` nuevos directamente o por
**heredoc en `/tmp`**, **prueba y empaqueta desde `/tmp`**, y persiste a la carpeta verificando con
`Read`. Toolchain Python en `/tmp/pylibs` (**ifcopenshell 0.8.5**, IFC4X3) → ejecuta con
`PYTHONPATH=/tmp/pylibs`; el cálculo de drenaje debe ser **stdlib pura** (como trazado/firmes). El
`.plugin` de la raíz puede estar bloqueado → **construye el ZIP en `/tmp` y cópialo con `cat >
destino`**, con **nombre versionado** (no sobrescribas), excluyendo `__pycache__`/`node_modules`/
`*.pyc`. Todo es **predimensionado, a revisar y firmar por técnico competente** (Ingeniero de
Caminos); NDP marcados `[confirmar AN]`.

**Empieza** leyendo los documentos (sobre todo el patrón `obras-lineales/` del PT 5.2, C1 §4bis y el
puente GIS/cuencas del PT 5.1), y **proponiendo: (a) la estructura del subagente y de
`scripts/drenaje`** (qué calcula la hidrología 5.2-IC, cómo dimensiona/comprueba cunetas y ODT por
Manning, cómo y dónde rellenas el gancho del modelo neutro), **(b) la resolución de las decisiones**
(espejo del núcleo sí/no en 6.1; origen de la cuenca y del periodo de retorno; método hidrológico;
gancho `drenaje` vs `terreno`; frontera con PT 6.2), y **(c) el alcance del hilo** (hidrología +
cunetas + ODT, o hidrología + cunetas primero y ODT como sub-entrega) — **antes de mover una sola
línea**.
