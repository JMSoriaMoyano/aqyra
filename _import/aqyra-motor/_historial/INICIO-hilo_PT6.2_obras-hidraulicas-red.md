# INICIO de hilo — PT 6.2 (Ola 6): nace el **solver de Manning de red** y el subagente `proyectista-de-saneamiento`

Proyecto Estructurando. Ejecuta el **PT 6.2 de la Ola 6**: añadir a la disciplina
`obras-lineales` (v0.2.0, PT 5.2 + 6.1) las **obras hidráulicas de red en lámina libre**
—**colectores de saneamiento**— con el **nacimiento del solver de Manning sobre el grafo de
red** (decisión nº7 "grafo + N solvers"). Es el hilo donde `obras-lineales` **cruza por
primera vez la frontera de red**: usa el núcleo `grafo_red`, **espeja el núcleo** y consume el
**dominio IFC MEP**. Reutiliza el **motor hidráulico de red** de la Ola 4. **Cierra el bloque de
saneamiento de la Ola 6;** el **abastecimiento a presión** (reúso del solver Darcy) queda para el
**PT 6.3**.

**Alcance confirmado con el ICCP (decisiones de la planificación, 22/06/2026):**
- **Alcance = saneamiento primero** (Manning lámina libre). El **abastecimiento a presión**
  (Darcy reutilizado) es el **PT 6.3**, no este hilo.
- **Dos subagentes** en el diseño de la disciplina: **nace `proyectista-de-saneamiento`** (EN 752,
  lámina libre) en el PT 6.2; **`proyectista-de-abastecimiento`** (EN 805, presión) queda
  **reservado para el PT 6.3**.
- **Reutilización del solver Darcy:** **diferida al PT 6.3** (cuando entre el abastecimiento).
  Recomendación pre-registrada: **copiar/espejar `instalaciones/scripts/red/solver_red.py`** dentro
  de `obras-lineales` (el aislamiento de runtime impide importar entre plugins), respetando la
  **decisión nº7** ("el núcleo da topología, **no calcula**; los solvers viven en la disciplina").
- **Espejo del núcleo: SÍ aplica** en el PT 6.2 (primera vez en `obras-lineales`).

**Dónde encaja en la Ola 6 (mapa de la ola, para situar este hilo):**
- **PT 6.1 ✅ — Drenaje (5.2-IC):** hidrología (racional), cunetas (Manning sección simple) y ODT
  (control entrada/salida), **cálculo local por elemento, sin grafo de red, sin espejo de núcleo**
  (`obras-lineales` v0.2.0; gancho `drenaje` del modelo neutro).
- **PT 6.2 (este hilo) — Saneamiento (lámina libre):** **nace el solver de Manning sobre el grafo
  de red**; colectores en árbol que convergen a un vertido; comprobación por tramo (calado/llenado,
  velocidad de autolimpieza/no erosión, pendiente y diámetro mínimos). **Espeja el núcleo**
  (`grafo_red`+`ifc_utils`) y **extiende el dominio IFC MEP a saneamiento** (`iso19650-openbim`).
- **PT 6.3 — Abastecimiento (presión):** reutiliza el **solver Darcy-Weisbach** del motor de red
  (Hardy-Cross para mallas); nace `proyectista-de-abastecimiento` (EN 805); extiende el IFC MEP a
  abastecimiento. *(No es este hilo; déjalo planteado y cierra la Ola 6 ahí.)*

> **Frontera (igual que en PT 4.x/5.x):** la **lectura del IFC MEP y la coherencia de red** viven en
> `iso19650-openbim` (parser físico→**modelo neutro de red** `sistema/nodos/tramos/terminales/fuentes`
> + validación de continuidad); el **cálculo hidráulico** (solver de Manning lámina libre) y la
> **demanda** (caudales de saneamiento) viven en `obras-lineales`, que **consume el JSON neutro de
> red**, no el IFC directamente. Las **cotas de solera/pendiente** son dato de red: si están en el
> Pset/IFC **prevalecen**; si no, las **inyecta el agente** (`[confirmar AN]`).

**Lee primero, en este orden:**
1. `Hoja-de-ruta_Ecosistema-ingenieria.md` — §4 (**capacidad transversal: motor hidráulico de red**;
   el núcleo da topología, no calcula), §5 (disciplina **Obras lineales**: obras hidráulicas
   —saneamiento en lámina libre/Manning, abastecimiento a presión/Darcy; EN 752/EN 805), §6 (Ola 6;
   este hilo es **Ola 6, PT 6.2**; la Ola 6 reutiliza el motor de la Ola 4) y §8 (**decisión nº4**
   núcleo de red espejado + puerta `verificar_espejo_nucleo.py`; **decisión nº7** "grafo + N solvers":
   **aquí nace el solver Manning de red**).
2. `Nucleo-transversal/C1_Contrato-IFC-modelo-neutro.md` — **§4** (modelo neutro de **red** MEP:
   `sistema{tipo,fluido}` / `nodos{x,y,z,tipo}` / `tramos{ni,nj,dn,material,rugosidad,longitud}` /
   `terminales` / `fuentes`; el parser es **agnóstico al sistema**) y **§5bis** (write-back de Psets
   de resultado de red `Pset_Estructurando_ResultadoRed`). Decide cómo encaja el **saneamiento**:
   la **fuente** se invierte (el ancla es el **punto de vertido/outfall**, no una fuente de presión);
   las **cotas de solera** y la **pendiente** por tramo gobiernan el flujo por gravedad.
3. **El patrón a imitar — el motor de red de `instalaciones/`:** `instalaciones/scripts/red/solver_red.py`
   (Darcy-Weisbach + **árbol desde la fuente por BFS** + Hardy-Cross; **reutiliza esa construcción de
   árbol y el reparto de caudales por continuidad** para el solver de Manning), `verificacion_red.py`
   (**balance nodal con signo** + cierre por lazo; replícalo como `verificacion_red_lineal.py`),
   `instalaciones/scripts/nucleo/` (espejo del núcleo) e `ingeniero-de-instalaciones.md` (clasifica/
   enruta por sistema → patrón para el subagente de saneamiento).
4. **Reúso interno de PT 6.1:** `obras-lineales/scripts/drenaje/odt.py` (`geom_circular`,
   calado parcial por Manning, biseccion) y `cuneta.py` (Manning sección simple) — el **solver de
   lámina libre reutiliza esa hidráulica de calado parcial**, ahora **sobre el grafo** en vez de por
   elemento aislado. La **demanda pluvial** puede reutilizar `drenaje/hidrologia.py` (racional 5.2-IC).
5. `iso19650-openbim/scripts/mep/ifc_to_model_mep.py` (parser MEP agnóstico) + `validacion_red.py`
   + `generate_test_ifc_mep.py` — **extiende** el reconocimiento a `IfcDistributionSystem`
   PredefinedType **SEWAGE/STORMWATER/DRAINAGE** (saneamiento); lee **cotas de solera** (Pset si
   está; si no, z de nodos como solera `[confirmar AN]`). El validador sistema-aware ya cubre `Pipe`.
   Caso `Casos-de-uso/caso-MEP-01-red-pci` como referencia de modelo neutro de red.
6. `Nucleo-transversal/verificar_espejo_nucleo.py` (la puerta de integridad del espejo; **ahora SÍ
   aplica**) y `Nucleo-transversal/nucleo/` (canónico del motor) — `obras-lineales` debe espejar
   `grafo_red.py` + `ifc_utils.py` + `test_grafo_red.py` **byte a byte**.
7. `Casos-de-uso/REPOSITORIO-aprendizaje.md` (estructural) y `criterios-obra-lineal.md` (raíz) +
   skill `obras-lineales:criterios-memoria` — añade la sección de **saneamiento/obras hidráulicas**,
   homogénea con trazado/firmes/drenaje. **INC-09** (puerta de empaquetado obligatoria) y el **hazard
   de mount** (ver notas de método; en PT 6.1 truncó plugin.json/README/CHANGELOG/agente/SKILL al
   leerlos por shell → reconstruir desde `Read` en `/tmp`).

**Objetivo y alcance (qué hay que hacer):**
1. **Nace `proyectista-de-saneamiento` (EN 752, lámina libre)** dentro de `obras-lineales`
   (→ **v0.3.0**). El **agente `ingeniero-de-obra-lineal`** amplía su clasificación/enrutado para
   reconocer el encargo de **saneamiento** (red de colectores) y orquestar el flujo (IFC MEP →
   modelo neutro de red [iso19650-openbim] → demanda de saneamiento → solver Manning → verificación →
   write-back → memoria).
2. **Solver de Manning de red (el titular).** `scripts/red/solver_lamina_libre.py`: sobre el **grafo
   del núcleo**, orienta la red como **árbol desde el vertido** (reusa `_arbol_desde_fuente` del
   solver Darcy, con `es_ancla`=outfall), reparte el caudal por **continuidad aguas abajo** y, por
   tramo, resuelve el **calado normal en sección parcialmente llena** (circular/ovoide) por **Manning**
   (`Q=(1/n)·A·R^(2/3)·J^(1/2)`, J de las cotas de solera) **reutilizando `odt.geom_circular`**.
   Comprueba por tramo: **velocidad** (autolimpieza ↔ no erosión), **grado de llenado** (≤0,75 NDP),
   **pendiente** y **diámetro mínimos**. NDP `[confirmar AN]`.
3. **Demanda de saneamiento (CN-3, EN 752).** `scripts/red/bases_saneamiento.py`: caudales de **aguas
   residuales** (dotación · hab-eq · coef. de punta) y/o **pluviales** (reúso de la hidrología
   racional 5.2-IC del PT 6.1 → escorrentía a la red). Define el régimen (separativo/unitario). NDP.
4. **Verificación + run_all + micro-test.** `verificacion_red_lineal.py` (balance nodal con signo +
   velocidades/llenado, análogo a `verificacion_red`), `run_all_obras_hidraulicas.py` (CLI: IFC MEP
   → modelo neutro de red → demanda → solver → veredicto + JSON; rellena un gancho de resultado) y
   `test_obras_hidraulicas.py` (positivo + negativos: tramo sin pendiente, velocidad baja, llenado
   excesivo, diámetro insuficiente).
5. **Espejo del núcleo (NUEVO en obras-lineales).** `scripts/nucleo/` = `grafo_red.py` + `ifc_utils.py`
   + `test_grafo_red.py` espejados **byte a byte** desde el motor canónico. La puerta
   `verificar_espejo_nucleo.py` debe dar **ESPEJOS IDÉNTICOS**.
6. **Extensión IFC MEP a saneamiento** (`iso19650-openbim`, C1 §4 → **minor bump**): parser reconoce
   SEWAGE/STORMWATER/DRAINAGE y lee cotas de solera/pendiente; generador de IFC MEP de saneamiento de
   prueba; validación de red (continuidad hacia el vertido). Reúsa el parser agnóstico (no lo redefine).
7. **Caso e2e** `Casos-de-uso/caso-LIN-05-saneamiento`: red de colectores (IFC MEP SEWAGE) → modelo
   neutro de red → caudales → **solver Manning lámina libre** → calado/velocidad/llenado por tramo →
   veredicto **CUMPLE/NO CUMPLE razonado**, con README y memoria. Write-back del Pset de resultado
   (no bloqueante).

**Decisiones a resolver y documentar (antes de mover una línea):**
- **Origen de las cotas de solera/pendiente** (gobiernan el flujo por gravedad): del **Pset/IFC** si
  está (prevalece); si no, **z de nodos como solera**, inyección del agente `[confirmar AN]`.
- **Demanda de saneamiento:** ¿**residuales**, **pluviales** o ambas (unitario)? Define cuál cubre el
  caso e2e. EN 752; coef. de punta y dotaciones NDP `[confirmar AN]`.
- **Modelo de la "fuente" invertida:** en saneamiento el **ancla del árbol es el vertido (outfall)**,
  no una fuente de presión; documenta cómo se mapea al `es_ancla` del `grafo_red` y al `tipo` de nodo.
- **Sección de los colectores:** circular por defecto (reúso `odt.geom_circular`); deja gancho para
  ovoide/marco. NDP.
- **Frontera con PT 6.3:** deja explícito que el **abastecimiento a presión** (Darcy/Hardy-Cross,
  EN 805, `proyectista-de-abastecimiento`) y la **reutilización/copia del solver Darcy** son del PT 6.3.

**Entregable:**
- Plugin **`obras-lineales` v0.3.0**: `agents/proyectista-de-saneamiento.md` + agente
  `ingeniero-de-obra-lineal.md` ampliado (clasifica/enruta saneamiento); `scripts/red/`
  (`solver_lamina_libre.py` + `bases_saneamiento.py` + `verificacion_red_lineal.py` +
  `run_all_obras_hidraulicas.py` + `test_obras_hidraulicas.py`); **`scripts/nucleo/` espejado**;
  `README.md` + `CHANGELOG.md` + `.claude-plugin/plugin.json` (`description` ≤ 500, actualizada al
  alcance saneamiento) y skill `criterios-memoria` retocada.
- `iso19650-openbim` **minor** (parser/validación/generador MEP de saneamiento).
- `criterios-obra-lineal.md` (raíz) ampliado con **saneamiento (EN 752), Manning lámina libre y
  criterios de red**.
- Caso e2e `Casos-de-uso/caso-LIN-05-saneamiento` con README y memoria.
- **Actualizar**: C1 §4 (saneamiento; outfall; cotas de solera), la **hoja de ruta** (Ola 6: **PT 6.2 ✅**;
  fila de `obras-lineales` a v0.3.0; registro de versiones; **PT 6.3 abastecimiento** como pendiente
  que cierra la Ola 6), `REPOSITORIO`/`criterios` (lección + INC si aplica) y los `CHANGELOG.md`.
- **Puertas de calidad obligatorias** (pega su salida en el cierre):
  `PYTHONPATH=/tmp/pylibs python3 Nucleo-transversal/verificar_empaquetado.py
  obras-lineales-v0.3.0.plugin --ref obras-lineales-v0.2.0.plugin` (**APTO**, exit 0; `description`
  ≤ 500) **y** `verificar_espejo_nucleo.py` (**ESPEJOS IDÉNTICOS** — esta vez **sí aplica**, canónico
  el motor). Si se reempaqueta `iso19650-openbim`, su puerta también **APTO** + espejo idéntico.

**Notas de método (críticas, confirmadas en PT 4.x/5.x/6.1):** las herramientas de fichero
(Read/Write/Edit) son la **fuente de verdad**; el shell del sandbox sirve copias **truncadas/stale**
de ficheros **pre-existentes o recién editados** (en PT 6.1 truncó `plugin.json`, `README.md`,
`CHANGELOG.md`, el agente y la SKILL al leerlos por shell), pero **los ficheros NUEVOS se leen
íntegros** y los `.plugin` (ZIP) **extraen íntegros**. Por tanto: para empaquetar, **reconstruye el
`.plugin` en `/tmp`** tomando los ficheros sin cambios del **ZIP v0.2.0** (íntegro), los nuevos
íntegros y los editados **reconstruidos desde `Read`** (verifica con `ast.parse` + salto de línea
final + `json.load`). El **espejo del núcleo debe ser byte-idéntico** al canónico: cópialo desde
`Nucleo-transversal/nucleo/` leído con `Read` y verifica con `verificar_espejo_nucleo.py`. Toolchain
Python en `/tmp/pylibs` (**ifcopenshell 0.8.5**, IFC4X3) → ejecuta con `PYTHONPATH=/tmp/pylibs`; el
cálculo hidráulico debe ser **stdlib pura** (como el solver Darcy de `instalaciones`). El `.plugin` de
la raíz puede estar bloqueado → **construye el ZIP en `/tmp` y cópialo con `cat > destino`**, con
**nombre versionado** (no sobrescribas), excluyendo `__pycache__`/`node_modules`/`*.pyc`. Todo es
**predimensionado, a revisar y firmar por técnico competente** (Ingeniero de Caminos); NDP marcados
`[confirmar AN]`.

**Empieza** leyendo los documentos (sobre todo el **motor de red de `instalaciones/`** como patrón
del solver y del arnés, **C1 §4** del modelo neutro de red, el **espejo del núcleo** y el **reúso de
la hidráulica de calado parcial del PT 6.1**), y **proponiendo: (a) la estructura del subagente
`proyectista-de-saneamiento` y de `scripts/red`** (qué calcula el solver de Manning sobre el grafo,
cómo orienta el árbol desde el vertido, cómo comprueba calado/velocidad/llenado, cómo rellena el
gancho de resultado), **(b) la resolución de las decisiones** (cotas de solera; demanda residual/
pluvial; fuente invertida/outfall; sección de colector; frontera con PT 6.3) y **(c) la extensión IFC
MEP de saneamiento** en `iso19650-openbim` — **antes de mover una sola línea**.
