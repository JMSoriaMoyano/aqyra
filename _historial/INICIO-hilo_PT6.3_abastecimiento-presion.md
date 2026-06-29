INICIO de hilo — PT 6.3 (Ola 6, **cierre**): nace el subagente `proyectista-de-abastecimiento`
y se **reutiliza el solver Darcy-Weisbach** (red a presión) en `obras-lineales`

Proyecto Estructurando. Ejecuta el **PT 6.3 de la Ola 6**: añadir a la disciplina
`obras-lineales` (v0.3.0, PT 5.2 + 6.1 + 6.2) las **obras hidráulicas de red a PRESIÓN**
—**abastecimiento de agua**— **reutilizando el motor de red Darcy-Weisbach** de la Ola 4
(decisión nº7 "grafo + N solvers"; Hardy-Cross para mallas). Es el **gemelo a presión** del
PT 6.2 (saneamiento en lámina libre): mismo grafo del núcleo (ya espejado en el PT 6.2),
consume el **dominio IFC MEP** ahora extendido a abastecimiento. **Cierra la Ola 6** (obras
lineales II); a partir de aquí el ecosistema apunta a la **Ola 7 (puentes)**.

**Alcance confirmado con el ICCP (decisiones de la planificación, 22/06/2026):**
- **Alcance = abastecimiento a presión** (EN 805, Darcy-Weisbach). El **saneamiento en lámina
  libre** (Manning) ya se cerró en el **PT 6.2** (`proyectista-de-saneamiento`, v0.3.0).
- **Nace `proyectista-de-abastecimiento`** (EN 805, red a presión) en este PT; es el segundo
  subagente de obras hidráulicas, paralelo a `proyectista-de-saneamiento`.
- **Reutilización del solver Darcy:** **ahora sí**. Recomendación pre-registrada (PT 6.2):
  **copiar/espejar `instalaciones/scripts/red/solver_red.py`** (Darcy-Weisbach + árbol por BFS
  desde la fuente + Hardy-Cross en mallas) dentro de `obras-lineales/scripts/red/` (el
  aislamiento de runtime impide importar entre plugins), respetando la **decisión nº7** (el
  núcleo da topología, **no calcula**; los solvers viven en la disciplina). Documenta si es
  copia byte a byte o adaptación; si copias, deja claro el origen y manténlo trazable.
- **Espejo del núcleo: YA aplica** en `obras-lineales` desde el PT 6.2 (`scripts/nucleo/`
  byte a byte). Este PT **no lo toca**; la puerta `verificar_espejo_nucleo.py` debe seguir dando
  **ESPEJOS IDÉNTICOS**.

**Dónde encaja en la Ola 6 (mapa de la ola, para situar este hilo):**
- **PT 6.1 ✅ — Drenaje (5.2-IC):** hidrología (racional), cunetas (Manning sección simple) y ODT
  (control entrada/salida), cálculo local por elemento, **sin grafo de red, sin espejo de núcleo**
  (`obras-lineales` v0.2.0; gancho `drenaje`).
- **PT 6.2 ✅ — Saneamiento (lámina libre):** **nació el solver de Manning sobre el grafo**;
  colectores en árbol que convergen al **vertido**; comprobación por tramo (calado/llenado,
  velocidad de autolimpieza/no erosión, pendiente y diámetro mínimos). **Espejó el núcleo**
  (`grafo_red`+`ifc_utils`) y extendió el dominio IFC MEP a saneamiento (`iso19650-openbim`
  v0.6.0; SEWAGE/STORMWATER/DRAINAGE, cotas de solera, outfall→`vertidos[]`). `obras-lineales`
  v0.3.0; gancho `red`; caso `caso-LIN-05-saneamiento` CUMPLE.
- **PT 6.3 (este hilo) — Abastecimiento (presión):** reutiliza el **solver Darcy-Weisbach** del
  motor de red (Hardy-Cross para mallas); nace `proyectista-de-abastecimiento` (EN 805); extiende
  el IFC MEP a abastecimiento (red a presión: fuente = depósito/bombeo). **Cierra la Ola 6.**

> **Frontera (igual que en PT 4.x/5.x/6.2):** la **lectura del IFC MEP y la coherencia de red**
> viven en `iso19650-openbim` (parser físico→**modelo neutro de red** `sistema/nodos/tramos/
> terminales/fuentes` + validación de continuidad **desde la fuente**); el **cálculo hidráulico**
> (solver Darcy-Weisbach a presión) y la **demanda** (caudales de abastecimiento) viven en
> `obras-lineales`, que **consume el JSON neutro de red**, no el IFC directamente. La **presión de
> la fuente** (depósito por cota / grupo de bombeo) es dato de red: si está en el Pset/IFC
> **prevalece**; si no, la **inyecta el agente** (`[confirmar AN]`).

**Lee primero, en este orden:**
1. `Hoja-de-ruta_Ecosistema-ingenieria.md` — §4 (**capacidad transversal: motor hidráulico de red**;
   el núcleo da topología, no calcula), §5 (disciplina **Obras lineales**: obras hidráulicas
   —saneamiento lámina libre/Manning ✅, **abastecimiento a presión/Darcy** ⬅ este hilo; EN 752/
   EN 805), §6 (Ola 6; este hilo es **Ola 6, PT 6.3**, el que **cierra la ola**) y §8 (**decisión
   nº4** núcleo espejado; **decisión nº7** "grafo + N solvers": aquí se **reutiliza el solver
   Darcy** como N-ésimo solver sobre el mismo grafo).
2. **El patrón a reutilizar — el solver Darcy de `instalaciones`:**
   `instalaciones/scripts/red/solver_red.py` (**Darcy-Weisbach**, fricción Swamee-Jain; **árbol
   desde la fuente por BFS** con `es_ancla`=fuente; **Hardy-Cross** para mallas; propagación de
   presiones desde la fuente con cota; comprobación de terminales por presión dinámica mínima) y
   `instalaciones/scripts/red/verificacion_red.py` (**balance nodal con signo** + cierre por lazo
   + presiones/velocidades). **Cópialos/espéjalos** a `obras-lineales/scripts/red/` (p. ej.
   `solver_presion.py` + `verificacion_red_presion.py`) o reúsalos adaptando nombres. Mira también
   `instalaciones/scripts/pci/bases_demanda.py` (patrón de bases de demanda) y
   `instalaciones/scripts/red/resultado_ifc.py` (write-back `Pset_Estructurando_ResultadoRed`).
3. **El gemelo recién hecho — el saneamiento del PT 6.2:**
   `obras-lineales/scripts/red/solver_lamina_libre.py`, `bases_saneamiento.py`,
   `verificacion_red_lineal.py`, `run_all_obras_hidraulicas.py`, `resultado_red_lineal.py`,
   `test_obras_hidraulicas.py` y el agente `agents/ingeniero-de-obra-lineal.md` +
   `agents/proyectista-de-saneamiento.md` — **imita su estructura** (homogeneidad entre los dos
   verticales de obras hidráulicas). Caso `Casos-de-uso/caso-LIN-05-saneamiento` como referencia
   de e2e y memoria.
4. `Nucleo-transversal/C1_Contrato-IFC-modelo-neutro.md` — **§4** (modelo neutro de **red** MEP,
   agnóstico al sistema), **§4ter** (saneamiento: outfall/cotas de solera; **aquí añade el espejo:
   abastecimiento a presión, fuente = depósito/bombeo**) y **§5bis** (write-back de Psets de
   resultado de red `Pset_Estructurando_ResultadoRed`). Decide cómo encaja el **abastecimiento**:
   la **fuente** vuelve a ser un **ancla de presión** (al revés que el vertido del saneamiento):
   depósito con carga por cota o grupo de bombeo con presión.
5. `iso19650-openbim/scripts/mep/ifc_to_model_mep.py` (parser MEP agnóstico) + `validacion_red.py`
   + `generate_test_ifc_mep.py`/`generate_test_ifc_saneamiento.py` — **extiende** el reconocimiento
   a sistemas de abastecimiento (`IfcDistributionSystem` PredefinedType **WATERSUPPLY /
   DOMESTICCOLDWATER / POTABLEWATER**, según esquema) y a la **fuente = depósito**
   (`IfcFlowStorageDevice`/`IfcTank`, presión por cota) además del grupo de bombeo
   (`IfcFlowMovingDevice`, ya soportado). Lee **presión/cota de la fuente** del Pset si está. El
   validador ya ancla en `fuentes` (red a presión); el ancla del abastecimiento es la **fuente**,
   no el vertido.
6. `Nucleo-transversal/verificar_espejo_nucleo.py` y `verificar_empaquetado.py` (las puertas) +
   `Nucleo-transversal/nucleo/` (canónico del motor). El espejo de `obras-lineales` **ya existe**
   (PT 6.2): este PT debe mantenerlo **idéntico**.
7. `criterios-obra-lineal.md` (raíz) + skill `obras-lineales:criterios-memoria` — añade la sección
   de **abastecimiento (EN 805, red a presión)**, homogénea con saneamiento. Nota de método: el
   **hazard de mount** (el shell trunca la lectura de ficheros de texto **pre-existentes**; los
   **nuevos** de la sesión y los **ZIP** se leen íntegros; **no se puede borrar por shell** salvo
   tras `allow_cowork_file_delete`).

**Objetivo y alcance (qué hay que hacer):**
1. **Nace `proyectista-de-abastecimiento` (EN 805, presión)** dentro de `obras-lineales`
   (→ **v0.4.0**). El **agente `ingeniero-de-obra-lineal`** amplía su clasificación/enrutado para
   reconocer el encargo de **abastecimiento** (red a presión) y orquestar el flujo (IFC MEP →
   modelo neutro de red [iso19650-openbim] → demanda de abastecimiento → solver Darcy →
   verificación → write-back → memoria).
2. **Solver Darcy-Weisbach a presión (reúso).** `scripts/red/solver_presion.py` (copia/espejo de
   `instalaciones/scripts/red/solver_red.py`): sobre el **grafo del núcleo**, orienta la red como
   **árbol desde la fuente** (`es_ancla`=depósito/bombeo), reparte el caudal por **continuidad
   aguas abajo**, resuelve la **pérdida de carga Darcy-Weisbach** por tramo y **propaga presiones
   desde la fuente con cota**; **Hardy-Cross** para mallas. Comprueba por tramo: **velocidad**
   (mín. anti-estancamiento ↔ máx. anti-golpe de ariete/erosión, p. ej. 0,5–2,0 m/s NDP), **presión
   mínima** en acometidas/hidrantes (p. ej. ≥ 250 kPa NDP) y **DN mínimo**. NDP `[confirmar AN]`.
3. **Demanda de abastecimiento (CN-3, EN 805).** `scripts/red/bases_abastecimiento.py`: caudal punta
   por **dotación · habitantes-eq · coef. de punta/simultaneidad** (y, si procede, caudal de
   incendio/hidrante como hipótesis concurrente). Define el tipo de fuente (depósito por cota /
   bombeo). NDP `[confirmar AN]`.
4. **Verificación + run_all + micro-test.** `verificacion_red_presion.py` (balance nodal con signo
   + presiones/velocidades, análogo a `instalaciones/verificacion_red.py`),
   ampliación de `run_all_obras_hidraulicas.py` (o `run_all_abastecimiento.py`: IFC MEP → modelo
   neutro de red → demanda → solver → veredicto + JSON; rellena el gancho de resultado `red`) y
   `test_abastecimiento.py` (positivo + negativos: presión insuficiente en el nudo más
   desfavorable, velocidad excesiva, malla que no cierra, DN insuficiente).
5. **Espejo del núcleo (SIN CAMBIOS).** `scripts/nucleo/` permanece **idéntico** al canónico del
   motor (no se toca en este PT). La puerta `verificar_espejo_nucleo.py` debe dar **ESPEJOS
   IDÉNTICOS**.
6. **Extensión IFC MEP a abastecimiento** (`iso19650-openbim`, C1 §4 → **minor bump v0.7.0**):
   parser reconoce los sistemas de abastecimiento (WATERSUPPLY/DOMESTICCOLDWATER/POTABLEWATER) y
   la **fuente = depósito** (`IfcFlowStorageDevice`/`IfcTank`, presión por cota) además del bombeo;
   generador de IFC MEP de abastecimiento de prueba; validación de red (continuidad **desde la
   fuente**). Reúsa el parser agnóstico (no lo redefine); PCI/REBT/saneamiento **sin regresión**.
7. **Caso e2e** `Casos-de-uso/caso-LIN-06-abastecimiento`: red de distribución a presión (IFC MEP
   WATERSUPPLY, fuente = depósito por cota o bombeo) → modelo neutro de red → caudales → **solver
   Darcy-Weisbach** → presión/velocidad por tramo y en el nudo más desfavorable → veredicto
   **CUMPLE/NO CUMPLE razonado**, con README y memoria. Write-back del Pset de resultado (no
   bloqueante). **Recomendado: incluir una malla** para ejercitar el Hardy-Cross.

**Decisiones a resolver y documentar (antes de mover una línea):**
- **Reúso del solver Darcy:** ¿**copia byte a byte** de `instalaciones/scripts/red/solver_red.py`
  (renombrado) o **adaptación**? Documenta la elección y la trazabilidad al original (decisión nº7).
- **Modelo de la fuente:** **depósito por cota** (presión = ρ·g·Δz desde la lámina de agua) vs
  **grupo de bombeo** (presión declarada). ¿Cuál cubre el caso e2e? EN 805. `[confirmar AN]`.
- **Demanda de abastecimiento:** caudal punta por simultaneidad; ¿se considera la **hipótesis de
  incendio** (hidrante) concurrente? Dotaciones y coef. de punta NDP `[confirmar AN]`.
- **Comprobaciones:** presión mínima en acometidas/hidrantes; banda de velocidad (anti-estancamiento
  ↔ anti-ariete); DN mínimo. NDP `[confirmar AN]`.
- **Frontera de cierre de la Ola 6:** deja explícito que con el abastecimiento **la Ola 6 queda
  cerrada**; el siguiente foco del ecosistema es la **Ola 7 (puentes)**, integrador del núcleo
  maduro + Alignment/infra.

**Entregable:**
- Plugin **`obras-lineales` v0.4.0**: `agents/proyectista-de-abastecimiento.md` + agente
  `ingeniero-de-obra-lineal.md` ampliado (clasifica/enruta abastecimiento); `scripts/red/`
  (`solver_presion.py` + `bases_abastecimiento.py` + `verificacion_red_presion.py` +
  `run_all`/`test_abastecimiento.py` + write-back); `scripts/nucleo/` **sin cambios**;
  `README.md` + `CHANGELOG.md` + `.claude-plugin/plugin.json` (`description` ≤ 500, actualizada al
  alcance abastecimiento) y skill `criterios-memoria` retocada.
- `iso19650-openbim` **minor v0.7.0** (parser/validación/generador MEP de abastecimiento).
- `criterios-obra-lineal.md` (raíz) ampliado con **abastecimiento (EN 805), Darcy a presión y
  criterios de red**.
- Caso e2e `Casos-de-uso/caso-LIN-06-abastecimiento` con README y memoria.
- **Actualizar**: C1 §4ter (abastecimiento; fuente = depósito/bombeo), la **hoja de ruta** (Ola 6:
  **PT 6.3 ✅ → Ola 6 CERRADA**; fila de `obras-lineales` a v0.4.0; registro de versiones; marcar
  la **Ola 7 puentes** como siguiente), `criterios` (lección + INC si aplica) y los `CHANGELOG.md`.
- **Puertas de calidad obligatorias** (pega su salida en el cierre):
  `PYTHONPATH=/tmp/pylibs python3 Nucleo-transversal/verificar_empaquetado.py
  obras-lineales-v0.4.0.plugin --ref obras-lineales-v0.3.0.plugin` (**APTO**, exit 0; `description`
  ≤ 500) **y** `verificar_espejo_nucleo.py` (**ESPEJOS IDÉNTICOS**, canónico el motor). Si se
  reempaqueta `iso19650-openbim`, su puerta también **APTO** + espejo idéntico.

**Notas de método (críticas, confirmadas en PT 4.x/5.x/6.x):** las herramientas de fichero
(Read/Write/Edit) son la **fuente de verdad**; el shell del sandbox **trunca la lectura** de
ficheros de texto **pre-existentes o recién editados** del mount (en PT 6.2: `solver_red.py` real
22.810 B → shell 15.209 B; `verificar_empaquetado.py` no parseaba por shell), pero **los ficheros
NUEVOS de la sesión se leen íntegros** y los `.plugin` (ZIP) **extraen íntegros**. Por tanto: para
empaquetar, **reconstruye el `.plugin` en `/tmp`** tomando los ficheros sin cambios del **ZIP
v0.3.0** (íntegro), los nuevos íntegros y los editados; **reconstruye `verificar_empaquetado.py` en
`/tmp` desde `Read`** para poder ejecutarlo. El **espejo del núcleo** ya es byte-idéntico: cópialo
desde el ZIP v0.3.0 o del motor y verifica con `verificar_espejo_nucleo.py`. Toolchain Python en
`/tmp/pylibs` (**ifcopenshell 0.8.5**, IFC4/IFC4X3) → ejecuta con `PYTHONPATH=/tmp/pylibs`; el
cálculo hidráulico debe ser **stdlib pura** (como el solver Darcy de `instalaciones` y el Manning
del PT 6.2). El `.plugin` de la raíz: **construye el ZIP en `/tmp` y cópialo con `cat > destino`**,
con **nombre versionado** (no sobrescribas), excluyendo `__pycache__`/`node_modules`/`*.pyc`. El
mount **no permite borrar por shell** salvo tras `allow_cowork_file_delete`. Todo es
**predimensionado, a revisar y firmar por técnico competente** (Ingeniero de Caminos); NDP marcados
`[confirmar AN]`.

**Empieza** leyendo los documentos (sobre todo el **solver Darcy de `instalaciones`** como patrón a
copiar/espejar, el **gemelo de saneamiento del PT 6.2** para imitar la estructura, **C1 §4/§4ter/
§5bis** del modelo neutro de red y el **espejo del núcleo** ya existente), y **proponiendo: (a) la
estructura del subagente `proyectista-de-abastecimiento` y de `scripts/red`** (cómo reúsas el solver
Darcy, cómo orienta el árbol desde la fuente/depósito, cómo comprueba presión/velocidad, cómo rellena
el gancho de resultado), **(b) la resolución de las decisiones** (copia vs adaptación del solver;
fuente depósito/bombeo; demanda y concurrencia de incendio; comprobaciones; cierre de la Ola 6) y
**(c) la extensión IFC MEP de abastecimiento** en `iso19650-openbim` — **antes de mover una sola
línea**.
