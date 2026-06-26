# Hoja de ruta — Ecosistema de personalizaciones de ingeniería

**Estado a 22/06/2026 · v2.0.** Documento maestro (nivel ecosistema), por encima de las hojas
de ruta de cada plugin. Define la **arquitectura** común, el **empaquetado** y el **orden de
crecimiento** por disciplinas y tipologías. Todo cálculo y entregable es de
**predimensionado/asistencia y debe ser revisado y firmado por técnico competente** (Ingeniero
de Caminos).

> Leyenda de estado: ✅ existe y validado · 🔄 en curso · 🔜 siguiente · ⬜ pendiente.

---

## 0. Punto de partida (lo que ya existe)

| Pieza | Tipo | Estado |
|---|---|---|
| `motor-calculo-estructural` (v0.22.0, agente `ingeniero-estructurista`) | Plugin + agente | ✅ Edificio convencional H y acero, cimentación, contención, multi-elemento, físico→analítico (serie R), **sísmico EC8 + núcleo de pantallas acopladas** |
| `estructuras-eurocodigos` (EC0–EC8 + memorias + criterios) | Plugin de skills | ✅ |
| `cte-documentos-basicos` (DB-SE/SI/SUA/HS/HR/HE + concurrente + memorias) | Plugin de skills | ✅ |
| `iso19650-openbim` (ifc-create, ifc-validate, bsDD, BEP/EIR, LOIN, CDE) | Plugin de skills | ✅ Dominio estructural + **MEP** (v0.4.x, PT 4.2–4.6; **saneamiento lámina libre v0.6.0, PT 6.2**) + **obra lineal IFC 4.3** (v0.5.0, PT 5.1: parser alineación, generador, validación, GIS) |
| `visor-ifc` | Plugin/skill | ✅ |
| `criterios-despacho.md` + programa de aprendizaje (3 docs) + `Nucleo-transversal/` (contratos C1–C3) | Memoria + contratos | ✅ |

**Diagnóstico.** El activo más valioso no es ningún módulo concreto, sino que la experiencia ya
ha producido —sin nombrarlo así— una **arquitectura en capas** correcta. Esta hoja de ruta la
**explicita**, separa lo transversal de lo vertical y permite escalar a nuevas disciplinas
**sin reescribir la fontanería**. La **Ola 1** (consolidar el núcleo + cerrar edificación) está
**cerrada y verificada** (PT 1.6; plugin v0.22.1 tras corregir un truncado de empaquetado en v0.22.0).

---

## 1. Principio rector: transversal vs. vertical

- **Capas transversales (el núcleo):** se construyen una vez y las usan TODAS las disciplinas
  (IFC/BIM, acciones, motor de cálculo, motor hidráulico de red, memoria del despacho,
  entregables). Cada hora invertida aquí se amortiza en todas las disciplinas futuras.
- **Columnas verticales (las disciplinas):** cada disciplina/tipología se monta *encima* del
  núcleo y aporta solo lo suyo: su **normativa** (skills) y su **orquestación** (agente +
  subagentes). No reimplementa el núcleo.

Regla de oro al añadir una disciplina o tipología: *“¿qué de esto es realmente nuevo (normativa,
idealización) y qué ya está en el núcleo (IFC, acciones, hidráulica, memoria, documentación)?”*
— solo se construye lo primero.

---

## 2. Arquitectura: cuándo usar plugin, skill, agente o subagente

- **Skill** = unidad de **conocimiento o procedimiento acotado y reutilizable** (una norma, un
  módulo de comprobación/dimensionado, una plantilla de memoria). Es el ladrillo; casi todo
  empieza siendo skill. Composable y barata de versionar.
- **Subagente** = **especialista en una tipología o subproblema**, con su **propio contexto**.
  Se usa cuando el problema es profundo (evita “ensuciar” el contexto principal) o para
  **paralelizar** (p. ej. *calculista de puentes*, *proyectista de PCI*, *trazado*).
- **Agente de disciplina** = el **“jefe de disciplina”**: clasifica el encargo desde el IFC,
  **enruta** a skills/subagentes, **orquesta** el flujo y **ensambla** el entregable.
  `ingeniero-estructurista` es este patrón; se replica por disciplina.
- **Plugin** = la **frontera de empaquetado y versionado**. Se agrupa por **disciplina**
  (vertical) o por **capacidad transversal** (núcleo); instala y versiona de forma independiente.

**Patrón de agente de disciplina (plantilla reutilizable):**
`clasificar → enrutar → orquestar la receta → verificar (normativa) → visualizar → memoria →
registrar criterios`.

---

## 3. Arquitectura de empaquetado: multi-plugin (no un único plugin)

**Decisión (22/06/2026): el ecosistema es multi-plugin, no un mega-plugin.** El plugin es la
frontera de versionado e instalación, y esas fronteras NO coinciden con “todo junto”:

- **Ritmos distintos:** el motor evoluciona rápido; la normativa (CTE, EC) es estable. Juntos,
  cada corrección del motor obligaría a reversionar lo estable.
- **Instalación a la carta:** quien haga solo obra lineal no necesita el motor de puentes.
- **Contexto del agente:** un agente por disciplina enruta mejor que uno omnisciente saturado.
- **Aislamiento de fallos:** un error empaquetando una disciplina no rompe las demás.

El **pegamento NO es un plugin común, son los contratos** del núcleo (C1–C4, §4) + el patrón de
agente. Así, plugins independientes interoperan sin fusionarse.

### Mapa de plugins (dos niveles)

| Nivel | Plugin | Contenido | Estado |
|---|---|---|---|
| **Transversal (núcleo)** | `iso19650-openbim` | BIM/IFC: crear, validar, bsDD, BEP/EIR, LOIN, CDE + **dominio MEP** (parser red, generador, **validación sistema-aware** Pipe/Cable/Duct, **write-back de Psets de resultado**) + **dominio obra lineal IFC 4.3** (parser de **alineación** físico→modelo neutro lineal por PK, generador IFC4X3, validación continuidad/tangencia/georref, **export GIS GeoJSON**; `scripts/mep`+`scripts/lineal`+`scripts/nucleo` espejado; **MEP de redes incl. saneamiento lámina libre y abastecimiento a presión depósito/bombeo**) | ✅ v0.7.0 (MEP, PT 4.2/4.4/4.5/4.6; obra lineal **Alignment+georref+GIS, PT 5.1**; **saneamiento PT 6.2; abastecimiento PT 6.3**) |
| **Transversal (núcleo)** | `visor-ifc` | Visualización de modelos | ✅ |
| **Transversal (núcleo)** | `motor-fem` | **Motor de elementos finitos propio** (numpy/scipy): librería de elementos (barra · lámina plana · **lámina curva** · **rigidizador** · **cable** · **membrana**), ensamblaje disperso y solvers (estático · modal · pandeo · **no-lineal** · **cargas móviles**); contrato **C5**; *strangler* sobre PyNite. Lo consumen puentes (Ola 7), estructuras singulares (Ola 3) y tensoestructuras | 🔄 Ola 7: PT 7.0 (FEM-0) ✅ v0.1.0; **PT 7.1 (FEM-1) ✅ v0.2.0** (módulo aditivo `fem1.py`: **modal** `eigsh`+masa participante y **cargas móviles/líneas de influencia** por superposición; estático FEM-0 **sin regresión**) |
| **Estructuras** | `motor-calculo-estructural` (+ agente) | Motor IFC→FEM→EC + catálogo de casos + **núcleo transversal** (`scripts/nucleo`) | ✅ v0.23.0 |
| **Puentes** | `puentes` (+ agente) | 1 plugin, agente `ingeniero-de-puentes` + **4 subagentes** (vigas pretensadas, **losa postesada**, **pórtico**, **celosía**); idealización por **emparrillado**, **lámina DKMQ**, **barras+resortes Winkler** y **barras articuladas**; **acciones IAP-11** + **postesado biaxial** (balance de cargas) + **empuje K0** + 2.º orden aprox.; comprobación **EC2/EC3/EC7** (fatiga diferida); **consume `motor-fem` (C5, FEM-1/v0.2.1)** y **Alignment** (C1); `scripts/nucleo` espejado | ✅ v0.2.0 (Ola 7, PT 7.2; `caso-PUE-01..04` CUMPLEN) |
| **Estructuras** | `estructuras-eurocodigos` | Conocimiento normativo EC0–EC8 + memorias | ✅ |
| **Edificación (transversal)** | `cte-documentos-basicos` | DB del CTE (SI/SUA/HS/HR/HE/SE) + concurrente | ✅ |
| **Instalaciones** | `instalaciones` (+ agente) | 1 plugin, subagentes **PCI** ✅ (BIE + **rociadores UNE-EN 12845**) y **eléctricas REBT** ✅ (BT radial: intensidad, sección, caída de tensión) / clima esbozado; **motor hidráulico de red** Darcy-Weisbach **en árbol y malla (Hardy-Cross)** + **solver eléctrico** (mismo grafo) + bases de demanda + **write-back de resultados al IFC** (`scripts/red`+`scripts/pci`+`scripts/electrico`+`scripts/nucleo` espejado) | ✅ v0.3.0 (PCI + REBT; PT 4.3/4.4/4.5) |
| **Obras lineales** | `obras-lineales` (+ agente) | 1 plugin, subagentes **trazado** ✅ (3.1-IC), **firmes** ✅ (6.1-IC), **drenaje** ✅ (5.2-IC: hidrología racional + cunetas Manning + ODT) y **saneamiento** ✅ (EN 752: colectores en lámina libre, **solver de Manning sobre el grafo de red**, PT 6.2); consume el **modelo neutro lineal** y el **modelo neutro de red** de `iso19650-openbim`; trazado/firmes/drenaje **sin grafo**, saneamiento y **abastecimiento sí usan el grafo y espejan el núcleo**; rellena los ganchos `firme`/`secciones_tipo`/`drenaje`/`red`; **abastecimiento ✅ (EN 805, solver Darcy copiado de instalaciones, PT 6.3)** | ✅ v0.4.0 (PT 5.2 + 6.1 + 6.2 + 6.3) |

> `cte-documentos-basicos` es transversal a **toda la edificación** (SI/SUA/HS/HR/HE son más
> arquitectura/instalaciones que estructura), por eso es plugin propio compartido, no dentro de
> estructuras.

### Distribución como suite: marketplace

Para entregar “todo el despacho” de una vez sin fusionar nada, los plugins se agrupan en un
**marketplace** (p. ej. *Despacho de Caminos*): se instalan juntos pero **versionan por
separado**. Es el mecanismo correcto para “un único punto de instalación” — no un mega-plugin.

*(Un plugin único solo tendría sentido en un proyecto diminuto, de un mantenedor, sin
reutilización entre disciplinas; ya estamos muy por encima de eso.)*

### Convención de metadatos del plugin (`description` ≤ 500 caracteres)

El campo `description` del `plugin.json` es **metadato de descubrimiento/selección** (lo que el
usuario y el agente leen para elegir el plugin en el marketplace), **no documentación**. El validador
lo limita a **500 caracteres**. Reglas para que toda disciplina nueva nazca saneada:

- **Descripción corta, estable y paralela entre plugins.** Patrón común:
  *"Disciplina X: entrada IFC (dominio Y), normativa Z; qué dimensiona/comprueba; salida (memoria/IFC)."*
  Tocarla **solo cuando cambie el alcance**, nunca en cada caso/versión.
- **No usarla como changelog.** El historial por versión va en `Casos-de-uso/CHANGELOG-plugin.md`;
  el "qué hace y cómo" en `README.md` y en los contratos C1–C4; las capacidades que **disparan** cada
  pieza, en el `description` de cada **skill/agente** (esos sí guían el enrutado).
- **Descubrimiento por término** → el array **`keywords`** del `plugin.json` (sin ese límite tan
  estricto), no la `description`.
- **Puerta de empaquetado:** `verificar_empaquetado.py` avisa si la `description` supera 500
  caracteres antes de publicar (además de las comprobaciones de truncado/artefactos).

> Antipatrón corregido (PT 4.1): la `description` heredada llegó a ~1.600 caracteres acumulando notas
> de versión → fallaba la validación de instalación y degradaba el enrutado entre disciplinas.

---

## 4. El núcleo transversal y sus contratos

Para que una disciplina nueva “enchufe” sin fricción, el núcleo expone **contratos** estables
(detalle en `Nucleo-transversal/`).

- **C1 — IFC / modelo neutro.** E/S en IFC; el cálculo opera sobre un modelo neutro común.
  Hoy: dominio de **análisis estructural** + **físico→analítico** (serie R). A ampliar:
  **dominio MEP** (`IfcDistributionElement`, `IfcFlowSegment/Fitting/Terminal`, `IfcSystem`,
  `IfcDistributionPort`) para instalaciones y obras hidráulicas; y **IFC 4.3 georreferenciado**
  (`IfcAlignment`, `IfcRoad`, perfil/peralte) + **GIS** para obras lineales. Pieza: `iso19650-openbim`.
- **C2 — Memoria del despacho.** `criterios-<disciplina>.md` (raíz) + memoria por obra +
  programa de aprendizaje (PROGRAMA/REPOSITORIO/CHANGELOG). Una skill `criterios-memoria` por plugin.
- **C3 — Entregables.** Motor de documentos común + **estructura de memoria homogénea** (citas,
  `[confirmar AN]`).
- **C4 — Acciones / bases de cálculo.** EC0/EC1 + DB-SE-AE; en obras lineales se suma la
  **acción del tráfico** (IAP) y, en drenaje, la **hidrología** (caudales de cálculo).

### Capacidad transversal emergente: motor hidráulico de red

Hay un cálculo que **se repite en tres disciplinas**: redes de tuberías/conductos. Conviene
construirlo **una vez** como capacidad compartida (grafo de red + pérdida de carga) y que cada
disciplina aporte solo sus particularidades:

- **Instalaciones — PCI / hidráulicas / clima:** redes a presión (BIE, rociadores, fontanería)
  y conductos de aire.
- **Obras lineales — obras hidráulicas:** colectores en **lámina libre** (Manning) y tuberías a
  presión (abastecimiento).

Misma lógica de **grafo nodos+tramos** que el grafo de nudos estructural (`puente.py`), distinto
solver hidráulico. Nace con las instalaciones (Ola 4) y se reutiliza en obras hidráulicas (Ola 6).

---

## 5. Las disciplinas del ecosistema

Tres disciplinas verticales, cada una con su agente, sobre el mismo núcleo:

### Estructuras — agente `ingeniero-estructurista` ✅
Tipologías: **edificación** ✅ · **edificación singular** · **puentes** · **cimentaciones y
contención**. Soporte: IFC (análisis y físico).

La **edificación singular** (grandes cubiertas, edificios en voladizo, edificios en altura) es la
que **empuja el motor de cálculo** más allá de lo actual: requiere FEM con **elementos de lámina**
(membrana + flexión), **láminas curvas**, **rigidizadores** (stiffeners), y análisis de **2.º
orden global (P-Δ)** y **dinámico** (viento dinámico, EC8 avanzado). Es trabajo de núcleo de
cálculo, no solo de verificación. **Ese núcleo es ahora el plugin transversal `motor-fem`** (Ola 7,
decisión nº8): la edificación singular **consume** sus capacidades (FEM-2 lámina curva+rigidizadores,
FEM-3 no-lineal/P-Δ) en vez de construir un motor propio. Ver `Hoja-de-ruta_Ola7-puentes-y-motor-FEM.md`.

### Instalaciones — agente `ingeniero-de-instalaciones` ✅ (PCI + REBT; v0.3.0, PT 4.3–4.5)
Tipologías/subagentes: **PCI** ✅ (BIE **y rociadores UNE-EN 12845**: solver hidráulico de red
Darcy-Weisbach **en árbol y en malla por Hardy-Cross** + bases de demanda RIPCI/UNE/UNE-EN 12845/DB-SI;
**write-back de Psets de resultado al IFC**) · **eléctricas REBT** ✅ (`proyectista-electrico`: redes de
BT **radiales**; **solver eléctrico** sobre el **mismo grafo** —intensidad, sección por momentos +
intensidad admisible ITC-BT-19, caída de tensión por intensidades; bases de demanda ITC-BT-10/25/44/47;
write-back) · **climáticas** (RITE, DB-HE, esbozado). Soporte: IFC **MEP** (modelo neutro de red de
`iso19650-openbim`). Paradigma: dimensionado de redes + cumplimiento (menos FEM). Nace aquí el **motor
hidráulico de red** (reutilizable en obras hidráulicas, Ola 6); el **solver eléctrico** demuestra que el
grafo del núcleo es agnóstico al solver (otro solver sobre la misma topología).

### Obras lineales — agente `ingeniero-de-obra-lineal` ✅ (trazado + firmes + drenaje; v0.2.0, PT 5.2 + 6.1)
Tipologías/subagentes:
- **Trazado:** ✅ planta (radios, clotoides A∈[R/3,R]), alzado (acuerdos verticales Kv,
  pendientes), visibilidad (Dp), coordinación — **Norma 3.1-IC**. Comprueba la `alineacion` del
  **modelo neutro lineal** frente a la **velocidad de proyecto Vp** → CUMPLE/NO CUMPLE +
  predimensionado (`proyectista-de-trazado`). No rediseña el eje.
- **Firmes:** ✅ categoría de tráfico pesado (IMDp), explanada (E1/E2/E3), **selección de sección del
  catálogo** — **Norma 6.1-IC** (6.3-IC rehabilitación fuera de alcance); rellena el gancho `firme`
  del modelo neutro (`proyectista-de-firmes`). Catálogo, no dimensionado por fatiga.
- **Drenaje:** ✅ hidrología (cuencas, método racional modificado, IDF, coef. de
  escorrentía), drenaje superficial (cunetas por Manning de sección simple) y obras de
  drenaje transversal (ODT por control de entrada/salida) — **Norma 5.2-IC** (PT 6.1).
  Rellena el gancho `drenaje` del modelo neutro. **Cálculo local por elemento, sin grafo
  de red** (`proyectista-de-drenaje`).
- **Obras hidráulicas (tuberías y colectores):** **saneamiento** ✅ (lámina libre, Manning;
  EN 752, PT 6.2: **nace el solver Manning sobre el grafo y se espeja el núcleo**; colectores
  en árbol que convergen al vertido + mallas cableadas por Hardy-Cross) y **abastecimiento** ✅
  (a presión; EN 805, **PT 6.3**: **reutiliza —copia byte a byte— el solver Darcy** de
  `instalaciones`; árbol desde la fuente —depósito por cota/bombeo— + Hardy-Cross en mallas;
  hidrante concurrente); pozos, depósitos. **Con el abastecimiento se cierra la Ola 6.**

Soporte: **IFC 4.3 (`IfcAlignment`) + GIS** (los proyectos de infraestructura son
georreferenciados).

---

## 6. Las olas (orden de crecimiento, de menor a mayor complejidad)

Dentro de cada ola, los casos escalan: **comprobar un elemento → dimensionar/optimizar →
proyecto completo con memoria + IFC**.

| Ola | Foco | Disciplina | Por qué aquí | Estado |
|---|---|---|---|---|
| **1** | Consolidar núcleo (contratos C1–C4) + cerrar **edificación** (incl. sísmico EC8 + núcleo) | Núcleo + Estructuras | Máxima reutilización, mínimo riesgo | ✅ Cerrada (PT 1.6 verificado; plugin **v0.22.1**) |
| **2** | **Cimentaciones y contención** como módulo transversal limpio | Estructuras | Lo comparten edificación, puentes y obra civil | 🔜 |
| **3** | **Edificación singular** (grandes cubiertas, voladizos, altura): FEM con **láminas / láminas curvas / rigidizadores**, **2.º orden (P-Δ)** y **dinámico** | Estructuras | Continúa la disciplina madura; **pasa a CONSUMIR `motor-fem`** (no construye motor propio): cubiertas laminares = vertical directo sobre **FEM-2/FEM-3**. Reactivable como spin-off en paralelo a PT 7.4/7.6 | ⬜ (replanteada como consumidora del motor FEM) |
| **4** | **Instalaciones** completas: **PCI + eléctricas (REBT) + climáticas (RITE/HE)** — nace el **motor hidráulico de red** + dominio **IFC MEP** | Instalaciones | Lanza la disciplina entera de una vez; la normativa de PCI ya existe | 🔄 En curso: **PT 4.1 (H1) ✅** núcleo de red; **PT 4.2 (H2) ✅** dominio IFC MEP (`iso19650-openbim` v0.4.0); **PT 4.3 (H3) ✅** nace `instalaciones` v0.1.0 (agente `ingeniero-de-instalaciones` + subagente PCI + **solver hidráulico de red Darcy-Weisbach** + bases de demanda). **PT 4.4 ✅** `instalaciones` v0.2.0: **rociadores UNE-EN 12845** (densidad×área, OH1 e2e), **motor de red con MALLAS (Hardy-Cross)** y **write-back de Psets de resultado al IFC** (`iso19650-openbim` v0.4.1). **PT 4.5 ✅** segundo vertical **eléctricas (REBT)**: `instalaciones` v0.3.0 (subagente `proyectista-electrico` + **solver eléctrico** sobre el mismo grafo —intensidad, sección, caída de tensión— + bases de demanda ITC-BT-10/25/44/47 + write-back) e `iso19650-openbim` v0.4.2 (**validador sistema-aware** Pipe/Cable/Duct; parser intacto). Casos `caso-REBT-01-vivienda` y `caso-REBT-02-terciario` CUMPLE/APTO. **PT 4.6 ✅** verificación/consolidación de la Ola 4 (`Verificacion-Ola4.md`): contratos C1–C4 coherentes, modelo neutro agnóstico al sistema, regresión micro-test 3/3 + 5 casos e2e (**PCI sin regresión tras REBT**), puertas **APTO** + **ESPEJOS IDÉNTICOS**, sin defecto de empaquetado; INC-12 (reproducibilidad rociadores) e INC-13 (feeder mono+tri) menores. **H1/H2/H3 ✅; PCI completo (BIE+rociadores) + REBT ✅ — Ola 4 CERRADA en lo verificado.** **Clima (RITE) → sub-ola 4.x (PT 4.7)**, hueco pre-aprovisionado (parser agnóstico + validador `AIRCONDITIONING→Duct` + patrón demanda/subagente). |
| **5** | **Obras lineales I:** núcleo **IFC 4.3 Alignment + GIS** y arranque por **trazado** y **firmes** | Obras lineales | Estrena el soporte georreferenciado; trazado/firmes son geometría+normativa (sin FEM) | 🔄 En curso: **PT 5.1 ✅** soporte georreferenciado (extensión C1 §4bis en `iso19650-openbim` v0.5.0: parser de alineación físico→modelo neutro lineal por PK, generador IFC4X3, validación continuidad/tangencia/georref, export GIS GeoJSON; caso `caso-LIN-01-eje-carretera` CUMPLE; decisiones nº2/nº3 resueltas). **PT 5.2 ✅** nace la disciplina `obras-lineales` v0.1.0 (agente `ingeniero-de-obra-lineal` + subagentes **trazado 3.1-IC** y **firmes 6.1-IC**; `scripts/trazado`+`scripts/firmes`, stdlib pura; rellena los ganchos `firme`/`secciones_tipo`; write-back `Pset_Estructurando_ResultadoLineal` + GIS; casos `caso-LIN-02-trazado` CUMPLE y `caso-LIN-03-firmes` sección 221; puerta **APTO**, sin espejo de núcleo). **Olas 5 (trazado+firmes) ✅; pendiente Ola 6 (drenaje/hidráulica).** |
| **6** | **Obras lineales II:** **drenaje** (hidrología + 5.2-IC) y **obras hidráulicas** (colectores/tuberías) | Obras lineales | Reutiliza el **motor hidráulico de red** de la Ola 4 | ✅ **CERRADA** (PT 6.3): **PT 6.1 ✅** nace el subagente **`proyectista-de-drenaje`** (`obras-lineales` v0.2.0): hidrología por método racional modificado 5.2-IC (tc Témez, IDF, coef. escorrentía), capacidad de **cunetas** (Manning de sección simple) y **ODT** (control de entrada/salida); rellena el gancho **`drenaje`** del modelo neutro; caso `caso-LIN-04-drenaje` CUMPLE; **sin espejo de núcleo** (cálculo local, sin grafo de red); puerta **APTO**. Estrena la **capacidad transversal C4 de hidrología**. **PT 6.2 ✅** nace el subagente **`proyectista-de-saneamiento`** (`obras-lineales` v0.3.0) y el **solver de Manning sobre el grafo**: colectores en lámina libre en árbol que convergen al **vertido** (outfall = ancla; mallas cableadas por Hardy-Cross de lámina libre), comprobando calado/velocidad/grado de llenado/pendiente/DN; **espeja el núcleo** (`verificar_espejo_nucleo.py` ESPEJOS IDÉNTICOS) y extiende el dominio **IFC MEP a saneamiento** (`iso19650-openbim` v0.6.0: SEWAGE/STORMWATER/DRAINAGE, cotas de solera, vertido). Reutiliza el **motor de red de la Ola 4** (árbol + continuidad + Hardy-Cross) con física de lámina libre. Caso `caso-LIN-05-saneamiento` CUMPLE; puertas **APTO** + **ESPEJOS IDÉNTICOS**. **PT 6.3 ✅** nace `proyectista-de-abastecimiento` (EN 805, red a presión): **copia byte a byte del solver Darcy** de `instalaciones` a `obras-lineales/scripts/red/solver_presion.py` (decisión nº7), árbol desde la **fuente** (depósito por cota/bombeo) + Hardy-Cross en mallas, demanda EN 805 + **hidrante concurrente**, comprobación velocidad 0,5–2,0 m/s / presión ≥250 kPa / DN_min; `iso19650-openbim` v0.7.0 extiende el IFC MEP a abastecimiento (WATERSUPPLY/DOMESTICCOLDWATER; **fuente = depósito `IfcTank`** por jerarquía `is_a`). Caso `caso-LIN-06-abastecimiento` CUMPLE (depósito por cota + anillo Hardy-Cross). **Ola 6 CERRADA; siguiente foco Ola 7 (puentes).** |
| **7** | **Puentes** (remate integrador) + **nuevo motor FEM transversal** | Estructuras | El núcleo maduro + el Alignment/infra de obras lineales convergen; **nace `motor-fem`** (capacidad transversal: lámina curva, rigidizadores, no-lineal) | 🔄 **Arranca (planificada)**: hoja de ruta dedicada `Hoja-de-ruta_Ola7-puentes-y-motor-FEM.md` (decisión nº8). Motor FEM transversal (`motor-fem`, núcleo numpy/scipy) con **estrategia *strangler* sobre PyNite**, escalera FEM-0…FEM-5; tipologías por madurez (vigas pretensadas → losa → pórtico → celosía → pilas/estribos → cajón → metálico/mixto → oblicuo → curvo → arco → atirantado); acciones **IAP-11** + cargas móviles + fases constructivas/diferidos; consume **Alignment** (Ola 5) y el **pretensado** ✅. **PT 7.0 (FEM-0) ✅ `motor-fem` v0.1.0**; **PT 7.1 (FEM-1) ✅**: `motor-fem` v0.2.0 (modal + cargas móviles/líneas de influencia) + nace la disciplina **`puentes` v0.1.0** (vigas pretensadas e2e `caso-PUE-01` CUMPLE). **PT 7.2 🔜** (losa postesada, pórtico, celosía). |

> Lógica de dependencias: la Ola 4 crea el **motor hidráulico** que la Ola 6 reutiliza; la Ola 5
> crea el **soporte Alignment/GIS** que el puente (Ola 7) aprovecha. Estructuras avanza seguida
> (olas 1–3), luego instalaciones (4) y obras lineales (5–6); puentes cierra como integrador.

> **Ola 4 cerrada en lo verificado (PT 4.6 ✅, `Nucleo-transversal/Verificacion-Ola4.md`):** núcleo de red
> + PCI (BIE + rociadores) + REBT, con contratos C1–C4 coherentes, regresión limpia y puertas en verde.
> **Próximos pasos (🔜):** (a) **PT 4.7 — clima/RITE** (sub-ola 4.x): solver de conductos de aire + cargas
> térmicas + demanda RITE/DB-HE, sobre el hueco ya pre-aprovisionado (parser MEP agnóstico, validador
> `AIRCONDITIONING→Duct`, patrón demanda/subagente); ejecutable sin bloquear la Ola 5. (b) **Ola 5 — obras
> lineales I** (IFC 4.3 Alignment + GIS; trazado/firmes), independiente de la Ola 4. **Arranca por `PT 5.1`**
> (soporte georreferenciado IFC 4.3 `IfcAlignment` + GIS, la extensión C1 que estrena el dominio
> georreferenciado y resuelve las decisiones abiertas nº2 —empaquetado— y nº3 —formato GIS—); texto de inicio
> en `INICIO-hilo_PT5.1_alignment-gis.md`.

---

## 7. Ola 1 en detalle — paquetes de trabajo

> Objetivo: dejar el **núcleo reutilizable y documentado** (C1–C4) y **cerrar la edificación**.

| PT | Paquete | Resultado |
|---|---|---|
| 1.1 | Formalizar la arquitectura (este documento) | ✅ `Hoja-de-ruta_Ecosistema-ingenieria.md` |
| 1.2 | Contrato IFC / modelo neutro + plan MEP/Alignment | ✅ `Nucleo-transversal/C1_…` |
| 1.3 | Contrato memoria-despacho + plantilla de criterios | ✅ `C2_…` + `plantilla-criterios-disciplina.md` |
| 1.4 | Contrato entregables + plantilla de memoria | ✅ `C3_…` + `plantilla-memoria.md` |
| 1.5 | Cerrar edificación: sísmico EC8 + **núcleo de pantallas acopladas** + sísmico integrado en `run_all_edificio` | ✅ caso 15, plugin **v0.22.0** |
| 1.6 | Verificación de Ola 1: coherencia contratos/plugins + checklist “listo para nueva disciplina” | ✅ `Nucleo-transversal/Verificacion-Ola1.md` (contratos coherentes; empaquetado corregido **v0.22.1**; backlog Ola 4 H1–H7) |

**Definición de “hecho” de la Ola 1:** un plugin de disciplina nuevo puede (a) leer/escribir IFC
(C1), (b) aprender entre hilos (C2), (c) emitir memoria homogénea (C3), (d) tomar acciones (C4)
— sin tocar el núcleo. Y la edificación queda cubierta de extremo a extremo.

---

## 8. Decisiones abiertas (a confirmar por el Ingeniero de Caminos)

1. **Empaquetado de instalaciones:** ✅ *Decidido: un plugin único `instalaciones` con subagentes.*
2. **Empaquetado de obras lineales:** ✅ *Resuelto (PT 5.1) e **IMPLEMENTADO (PT 5.2)**: **un plugin
   único `obras-lineales`** (v0.1.0) con subagentes (trazado/firmes ✅; drenaje/hidráulica en Ola 6),
   análogo a `instalaciones`. El parser/validación de alineación viven en `iso19650-openbim` (capa IFC
   transversal), como el MEP; el cálculo de trazado/firmes en `obras-lineales`. **Sin espejo de núcleo**
   (no lee IFC ni usa `grafo_red`): trabaja sobre el modelo neutro lineal (JSON).*
3. **Soporte GIS:** ✅ *Resuelto (PT 5.1): **GeoJSON + IFC 4.3** (dos soportes complementarios) — IFC =
   modelo de ingeniería (alineación paramétrica completa); GeoJSON (LineString en CRS proyectado) =
   puente a cartografía/cuencas para la Ola 6. Implementado `export_gis.py`; Shapefile queda como opción
   futura documentada (evita dependencia binaria). La georreferencia se lee en el parser lineal; se
   promoverá al núcleo solo cuando una 2ª disciplina georreferenciada la necesite.*
4. **Motor hidráulico de red:** ✅ *Resuelto del todo (PT 4.1 v0.23.0 + PT 4.3 v0.1.0).* El **grafo
   de red** y las utilidades IFC viven en un **módulo de núcleo agnóstico al solver** (`scripts/nucleo/`:
   `ifc_utils` + `grafo_red`), **canónico** en el motor y **espejado byte a byte** a cada plugin que lo
   consume (`iso19650-openbim`, `instalaciones`). **Patrón de espejo adoptado** (no un módulo único
   importable): el aislamiento de runtime impide importar entre plugins, así que el espejo es la única
   vía; se vela su integridad con la puerta `Nucleo-transversal/verificar_espejo_nucleo.py` (hash, FALLA
   si un espejo diverge). Esto cierra **INC-10**. El **motor hidráulico** nació en PT 4.3: el *solver*
   (Darcy-Weisbach en `instalaciones`; Manning en obras hidráulicas, Ola 6) que cada disciplina añade
   sobre ese grafo común (el núcleo da topología, no calcula).
5. **Marketplace:** ¿crear ya el marketplace *Despacho de Caminos* para distribuir la suite?
6. **Cierre de la Ola 4 y ubicación de RITE:** ✅ *Propuesto y adoptado (PT 4.6): cerrar la Ola 4 "en lo
   verificado" (núcleo de red + PCI + REBT) y llevar **clima/RITE** a una **sub-ola 4.x (PT 4.7)**.* RITE es
   un vertical nuevo (física nueva: conductos de aire, cargas térmicas, demanda RITE/DB-HE), no una tarea de
   verificación; su hueco está pre-aprovisionado (parser MEP agnóstico, validador `AIRCONDITIONING→Duct`,
   patrón demanda/subagente), así que entra como 4.x sin bloquear la Ola 5. *[confirmar por el ICCP]*
7. **Abstracción transversal del cálculo de redes:** ✅ *Confirmada (PT 4.6): "grafo de red (topología, del
   núcleo) + N solvers (física por disciplina)".* Hoy: solver **hidráulico** (Darcy-Weisbach, árbol +
   Hardy-Cross) y solver **eléctrico** (propagación por árbol, mismo grafo). La **Ola 6** añadirá un solver
   **Manning** (lámina libre) y el **clima** uno de **conductos de aire**, todos sobre el mismo grafo. El
   núcleo da topología y E/S IFC; **no calcula**. **Matiz (PT 6.1):** el **drenaje local**
(cunetas/ODT) usa **Manning de sección simple por elemento**, **sin grafo** — no es un
solver de red; el **solver Manning sobre el grafo** (colectores en lámina libre) **nació en
el PT 6.2 ✅** (obras hidráulicas de saneamiento, `obras-lineales` v0.3.0), donde el plugin
**ya espeja el núcleo** (ESPEJOS IDÉNTICOS). El **abastecimiento a presión** (Darcy, **PT 6.3 ✅**,
`obras-lineales` v0.4.0) **reutiliza —copia byte a byte— el solver Darcy** de `instalaciones`
sobre el mismo grafo (N-ésimo solver; **cierra la Ola 6**). Solo queda el **clima** (conductos de
aire) como solver pendiente sobre el mismo grafo (sub-ola 4.x).
8. **Motor de cálculo FEM (Ola 7):** ✅ *Decidido (23/06/2026): nuevo **motor FEM transversal** en un
   plugin propio `motor-fem`* (núcleo numpy/scipy), análogo al motor hidráulico de red — capacidad que
   comparten **puentes**, **estructuras singulares** (cubiertas laminares) y **tensoestructuras**.
   **Estrategia *strangler* sobre PyNite** (oráculo de validación; deprecación por fases, cero
   regresión en casos 1–15). Crece por una **escalera de capacidades FEM-0…FEM-5** (lineal → cargas
   móviles/modal → lámina curva+rigidizadores → no-lineal/pandeo → cables/membranas+form-finding →
   dinámica en el tiempo). Tipologías de puente **por madurez del FEM**; acciones **IAP-11** (carretera;
   ferrocarril IAPF futuro). La **Ola 3 (singular) pasa a consumir `motor-fem`** (no construye motor
   propio). Contrato nuevo **C5** (modelo de análisis FEM + API del solver + arnés de validación
   NAFEMS). Detalle en `Hoja-de-ruta_Ola7-puentes-y-motor-FEM.md`. *Abiertas:* ubicación del mallador,
   `puentes` como plugin propio (recomendado), alcance de FEM-5 y de tensoestructuras (horizonte),
   modelo de pérdidas diferidas. *[confirmar por el ICCP]*

---

## Registro de versiones

- **v3.7 (23/06/2026):** **Ola 7 PT 7.3 CERRADO** — `puentes` sube a **v0.3.0**
  (subestructura) con dos verticales nuevos (2 subagentes): **pila + aparato de apoyo +
  cimentación** (columna barra 3D + aparato de apoyo como **resorte de 6 GdL** + base
  Winkler; EC2 fuste flexo-compresión M-N + 2.º orden aprox. + cortante por bielas;
  **EC7 cimentación enrutada** zapata/pilotes/encepado reutilizando `motor-calculo`;
  EC8-2 diferida) y **estribo** (muro con cargas de tablero; empuje activo Ka / reposo
  K0; reusa `verificacion_muro` EC7/EC2 + fuste por motor-fem; frenado en estabilidad
  global). El motor **`motor-fem` v0.2.1 NO se toca** (sigue FEM-1). Casos `PUE-05/06`
  CUMPLEN; puertas **APTO** + espejo **IDÉNTICO** + **sin regresión** de PUE-01..04.
  **Siguiente: PT 7.4** (cajón postesado, FEM-2). Detalle en
  `Hoja-de-ruta_Ola7-puentes-y-motor-FEM.md` (v1.4).
- **v3.6 (23/06/2026):** **Ola 7 PT 7.2 CERRADO** — `puentes` **v0.2.0** completa el grupo
  lineal con tres verticales nuevos (3 subagentes): **losa postesada** (lámina DKMQ + postesado
  biaxial por balance de cargas + envolventes LM1 por objetivo de lámina; EC2), **pórtico**
  (barras + resortes Winkler + empuje K0 + 2.º orden aprox.; EC2/EC7) y **celosía** (barras
  articuladas; EC3 con fatiga diferida). El motor sube a **`motor-fem` v0.2.1** (extensión
  aditiva `esfuerzo_lamina`, sigue en FEM-1). Casos `PUE-02/03/04` CUMPLEN; puertas APTO +
  espejo IDÉNTICO + arnés FEM sin regresión. **Siguiente: PT 7.3** (subestructura). Detalle en
  `Hoja-de-ruta_Ola7-puentes-y-motor-FEM.md` (v1.3).
- **v3.5 (23/06/2026):** **Arranca la Ola 7 (puentes) y se planifica el nuevo MOTOR FEM
  transversal** (decisión nº8). Documento dedicado `Hoja-de-ruta_Ola7-puentes-y-motor-FEM.md`:
  nace (planificado) el plugin **`motor-fem`** (núcleo numpy/scipy: barra · lámina plana · **lámina
  curva** · **rigidizador** · **cable** · **membrana**; solvers estático/modal/pandeo/**no-lineal**/
  **cargas móviles**), con **estrategia *strangler* sobre PyNite** y una **escalera de capacidades
  FEM-0…FEM-5**. La disciplina **`puentes`** (plugin propio recomendado, agente `ingeniero-de-puentes`)
  aborda las tipologías **por madurez del FEM**: vigas pretensadas → losa postesada → pórtico →
  celosía → pilas/estribos/cimentaciones → cajón → metálico/mixto → oblicuo → curvo → arco →
  atirantado. Transversales: **acciones IAP-11** + **líneas de influencia/cargas móviles** + **fases
  constructivas y efectos diferidos** (extiende el pretensado ✅) + geometría **Alignment** (Ola 5).
  Plan **PT 7.0–7.8**; contrato **C5** (modelo de análisis FEM + API + arnés NAFEMS). **La Ola 3
  (estructuras singulares) se replantea como consumidora de `motor-fem`** (cubiertas laminares =
  vertical sobre FEM-2/FEM-3); el horizonte **tensoestructuras** se habilita con FEM-4 (cables/
  membranas + form-finding). Sin reempaquetado (fase de planificación). **Confirmadas 4 decisiones de
  arquitectura con el ICCP** (motor transversal, strangler, secuencia por madurez, IAP-11).
- **v3.4 (22/06/2026):** **PT 6.3 (Ola 6 · CIERRE) — nace el abastecimiento a presión (EN 805) y
  se REUTILIZA el solver Darcy de la Ola 4**. `obras-lineales` → **v0.4.0**: nuevo subagente
  **`proyectista-de-abastecimiento`** (EN 805, red a presión) y el agente `ingeniero-de-obra-lineal`
  amplía su clasificación/enrutado a **abastecimiento**. Es el **gemelo a presión** del saneamiento
  (PT 6.2): mismo **grafo del núcleo** (espejo idéntico, **sin cambios**) y, en vez del Manning, el
  **solver Darcy-Weisbach copiado byte a byte** de `instalaciones` (decisión nº7 "grafo + N solvers";
  el aislamiento de runtime impide importar entre plugins → la copia es la vía). `scripts/red/`
  (**stdlib pura**): `solver_presion.py` (**copia** del `solver_red.py` de instalaciones: árbol
  **desde la fuente** + Hardy-Cross en mallas; Darcy-Weisbach/Swamee-Jain; **propagación de presión
  con cota**), `bases_abastecimiento.py` (**demanda EN 805**: dotación·hab-eq·punta + **hidrante
  concurrente**; fija la **fuente** depósito por cota/bombeo), `verificacion_red_presion.py` (balance
  nodal + presiones/velocidades), `run_all_abastecimiento.py` (gancho **`red`**; añade v_min/DN_min de
  abastecimiento), `resultado_red_presion.py` (write-back `Pset_Estructurando_ResultadoRed`) y
  `test_abastecimiento.py` (**17/17**: depósito por cota + árbol + malla + negativos presión/velocidad/
  DN + bases). **`iso19650-openbim` → v0.7.0**: el parser MEP reconoce **WATERSUPPLY/DOMESTICCOLDWATER/
  POTABLEWATER** y la **fuente = depósito** (`IfcTank`/`IfcFlowStorageDevice` por **jerarquía `is_a`**,
  no string exacto) además del bombeo; lee `cota_lamina`/presión de la fuente y `habitantes_eq` también
  en abastecimiento; generador `generate_test_ifc_abastecimiento.py` (depósito + anillo); micro-test
  `test_red_abastecimiento.py`; validación **sin cambios** (ya anclaba en `fuentes`). PCI/REBT/
  saneamiento **sin regresión** (`test_red_mep.py` TODO OK). **Decisiones (todas confirmadas por el
  ICCP):** **copia byte a byte** del solver Darcy (trazabilidad, cero regresión); **fuente = depósito
  por cota** (presión 0 + carga `ρ·g·Δz`) en el caso e2e, con **bombeo** soportado; **hidrante
  concurrente** incluido por defecto; comprobaciones **EN 805** (v 0,5–2,0 m/s, p_min 250 kPa, DN_min)
  `[confirmar AN]`. **Gancho C1 §4quater:** abastecimiento sobre el mismo modelo neutro de red (fuente =
  ancla de presión, al revés que el vertido). Caso e2e `caso-LIN-06-abastecimiento` (IFC MEP WATERSUPPLY,
  depósito lámina 130 m + anillo → modelo neutro → demanda EN 805 → **solver Darcy** → **CUMPLE**:
  caudal 24,8 l/s, v 0,65–1,03 m/s, Hardy-Cross 6 iter residuo ≈0, presiones ≥250 kPa, nudo más
  desfavorable ACO-2 margen +40,5 kPa; write-back 8 elem/40 props re-validado CUMPLE). Puertas **APTO**
  (`verificar_empaquetado.py`, `--ref` v0.3.0/v0.6.0) y **ESPEJOS IDÉNTICOS** (`verificar_espejo_nucleo.py`,
  canónico el motor). **Reempaquetados:** `obras-lineales` v0.4.0 e `iso19650-openbim` v0.7.0 (motor
  v0.23.0 e `instalaciones` v0.3.0 siguen vigentes). **Ola 6 CERRADA; siguiente foco Ola 7 (puentes).**
- **v3.3 (22/06/2026):** **PT 6.2 (Ola 6) — nace el solver de Manning de red (saneamiento, lámina
  libre)**. `obras-lineales` → **v0.3.0**: nuevo subagente **`proyectista-de-saneamiento`** (EN 752) y
  el agente `ingeniero-de-obra-lineal` amplía su clasificación/enrutado a **saneamiento**. Es la
  **primera vez que `obras-lineales` cruza la frontera de red**: usa el **grafo del núcleo** (decisión
  nº7 "grafo + N solvers"), **espeja el núcleo** (`scripts/nucleo/` = `grafo_red`+`ifc_utils`+
  `test_grafo_red`, byte a byte del motor) y consume el **dominio IFC MEP** de saneamiento. `scripts/red/`
  (**stdlib pura**, reúsa `drenaje/odt.py`): `solver_lamina_libre.py` (**Manning sobre el grafo**: árbol
  **desde el vertido**/outfall + reparto por continuidad aguas arriba + **Hardy-Cross de lámina libre**
  en mallas; calado normal en sección parcialmente llena; comprueba llenado≤0,75, velocidad 0,6–5,0 m/s,
  pendiente>0, DN≥300), `bases_saneamiento.py` (**demanda residual EN 752**: dotación·hab-eq·punta·
  retorno), `verificacion_red_lineal.py` (balance nodal con signo **hacia el vertido** + cierre por lazo
  + comprobaciones por tramo), `run_all_obras_hidraulicas.py` (rellena el gancho **`red`**),
  `resultado_red_lineal.py` (write-back `Pset_Estructurando_ResultadoRed`) y `test_obras_hidraulicas.py`
  (**16/16**: positivo + 4 negativos + malla). **`iso19650-openbim` → v0.6.0**: el parser MEP reconoce
  **SEWAGE/STORMWATER/DRAINAGE**, lee **cotas de solera** y mapea el **vertido** (`OUTLET`) en
  `vertidos[]` (`tipo:"vertido"`); validación anclada en fuentes **o** vertidos; generador
  `generate_test_ifc_saneamiento.py`; micro-test ampliado (PCI/REBT **sin regresión**, clave aditiva
  `vertidos:[]`). **Gancho C1 §4ter:** clave nueva **`red`** (resumen) + `vertidos`/`cota_solera`/
  `habitantes_eq` (retrocompatibles). Caso e2e `caso-LIN-05-saneamiento` (IFC MEP SEWAGE → modelo neutro
  de red → demanda EN 752 → **solver Manning** → calado/velocidad/llenado por tramo → **CUMPLE**, caudal
  vertido 31,9 l/s, v 0,82–1,11 m/s, llenado 17–24 %; write-back re-validado CUMPLE). **Decisiones:**
  **cotas de solera** dato del IFC si está (prevalece), si no z del nodo `[confirmar AN]`; **fuente
  invertida = vertido** (outfall = ancla del árbol); **sección circular** (gancho ovoide/marco);
  **demanda residual** (separativo) en el caso base; **mallas cableadas** (decisión del ICCP). Puertas
  **APTO** (`verificar_empaquetado.py`, `--ref` v0.2.0; `description` 489/500) y **ESPEJOS IDÉNTICOS**
  (`verificar_espejo_nucleo.py`, canónico el motor) — esta vez **sí aplica** en `obras-lineales`.
  **Reempaquetados:** `obras-lineales` v0.3.0 e `iso19650-openbim` v0.6.0 (motor v0.23.0 e
  `instalaciones` v0.3.0 siguen vigentes). **🔜 PT 6.3:** abastecimiento a presión (EN 805, Darcy/
  Hardy-Cross, `proyectista-de-abastecimiento`); **cierra la Ola 6**.
- **v3.2 (22/06/2026):** **arranca la Ola 6 (obras lineales II) con el PT 6.1 — drenaje (5.2-IC)**.
  Nace el **tercer subagente** de `obras-lineales`, **`proyectista-de-drenaje`** (plugin → **v0.2.0**),
  el análogo —para el agua de lluvia— de lo que trazado/firmes hicieron con la geometría y el firme.
  **Estrena la capacidad transversal C4 de hidrología** (caudales de cálculo). El agente
  `ingeniero-de-obra-lineal` amplía su clasificación/enrutado a **drenaje** (además de trazado/firmes).
  `scripts/drenaje/` (**stdlib pura**): `hidrologia.py` (**método racional modificado 5.2-IC**: tc de
  Témez, intensidad de la **curva IDF**, coef. de **escorrentía** por umbral Po, coef. de uniformidad
  Kt, factor reductor areal KA, `Q=C·I·A·Kt/3.6`; periodos de retorno por tipo de elemento),
  `cuneta.py` (capacidad por **Manning de sección simple** triangular/trapezoidal, calado normal por
  bisección, resguardo, velocidad autolimpieza/erosión), `odt.py` (capacidad de **ODT** tubo/marco por
  **control de entrada/salida**, dimensión mínima, velocidad), `verificacion_drenaje.py` +
  `run_all_drenaje.py` (CLI `--datos` → rellena el gancho `drenaje`) + `test_drenaje.py` (**13/13**).
  **Gancho C1 §4bis:** clave **nueva** `drenaje` = `{cuencas[], cunetas[], odt[]}` (retrocompatible;
  `terreno` sigue en `None`, es geotecnia/movimiento de tierras). **Write-back** ampliado
  (`Pset_Estructurando_ResultadoLineal` con resumen de drenaje) + GIS. Caso e2e `caso-LIN-04-drenaje`
  (cuenca de plataforma T=25 → cuneta **CUMPLE**; cuenca vertiente 0,85 km² → ODT Ø1,80 **CUMPLE**,
  control de entrada; IFC enriquecido re-parseado **CUMPLE**, georref intacta). **Decisiones:** **sin
  espejo de núcleo** (cunetas/ODT son **Manning de sección simple, cálculo local por elemento**, sin
  topología de red → `verificar_espejo_nucleo.py` **no aplica**; el grafo_red + espejo + IFC MEP de
  saneamiento son del **PT 6.2**); **el dato del GIS/Pset prevalece** para la cuenca (A/L/J) y la lluvia
  (Pd, I1/Id, Po) y T; **hidrología por método racional modificado**. Puerta **APTO**
  (`verificar_empaquetado.py`, `--ref` v0.1.0; `description` 483/500). **Único nuevo empaquetado:**
  `obras-lineales` v0.2.0 (iso19650-openbim v0.5.0, motor v0.23.0 e instalaciones v0.3.0 siguen
  vigentes). **🔜 PT 6.2:** obras hidráulicas de red (colectores lámina libre + abastecimiento a
  presión; nace el solver Manning sobre el grafo y se espeja el núcleo).
- **v3.1 (22/06/2026):** **nace la disciplina `obras-lineales` (PT 5.2, Ola 5)** sobre el soporte
  georreferenciado del PT 5.1 — análogo lineal de lo que el PT 4.3 hizo con `instalaciones` sobre el
  modelo neutro de red. **Plugin `obras-lineales` v0.1.0**: agente `ingeniero-de-obra-lineal`
  (clasifica trazado/firmes/ambos → enruta → orquesta → verifica → memoria) + subagentes
  `proyectista-de-trazado` (**3.1-IC**) y `proyectista-de-firmes` (**6.1-IC**). `scripts/trazado/`
  (parámetros por Vp + comprobación planta/alzado/visibilidad/coordinación + verificación + run_all +
  micro-test 7/7) y `scripts/firmes/` (bases IMDp/explanada + catálogo + selección que **rellena los
  ganchos** `firme`/`secciones_tipo` + verificación + run_all + micro-test 7/7), **stdlib pura**;
  `scripts/comun/resultado_ifc_lineal.py` (semántica `Pset_Estructurando_ResultadoLineal`); skill
  `criterios-memoria` + `criterios-obra-lineal.md` (raíz). **Frontera:** lectura/coherencia IFC en
  `iso19650-openbim`; cálculo de trazado/firmes en `obras-lineales` (consume el JSON neutro lineal).
  **Decisiones:** **sin espejo de núcleo** (no lee IFC ni usa `grafo_red`; `verificar_espejo_nucleo.py`
  no aplica), **el dato del IFC prevalece** (Vp, IMDp/explanada), **firmes por catálogo** (no fatiga).
  Casos e2e: `caso-LIN-02-trazado` (Vp=60 → **CUMPLE**; Vp=100 → NO CUMPLE, sensibilidad) y
  `caso-LIN-03-firmes` (IMDp 480 → T2, Ev2 150 → E2 → sección **221** MB18+ZA30; gancho `firme`
  relleno; **write-back** al IFC re-validado CUMPLE + **GeoJSON**). **Ganchos C1 §4bis rellenados**
  (`firme`, `secciones_tipo`; `terreno` queda para Ola 6). **Decisión nº2 implementada.** Puerta
  **APTO** (`verificar_empaquetado.py`, `description` 478/500; sin `--ref` por ser v0.1.0; espejo de
  núcleo no aplica). **Único nuevo empaquetado:** `obras-lineales` v0.1.0 (iso19650-openbim v0.5.0,
  motor v0.23.0 e instalaciones v0.3.0 siguen vigentes). **🔜 Ola 6:** drenaje (5.2-IC) + obras
  hidráulicas (reutilizan el motor hidráulico de red de la Ola 4).
- **v3.0 (22/06/2026):** **arranca la Ola 5 (obras lineales I)** con el **PT 5.1** — apertura del
  **dominio georreferenciado** (extensión C1 §4bis), análogo a lo que el PT 4.2 hizo con el dominio IFC
  MEP. `iso19650-openbim` → **v0.5.0**: nuevo `scripts/lineal/` (parser `ifc_to_model_lineal.py`
  físico→**modelo neutro lineal** por **PK** desde `IfcAlignment` + capas horizontal/vertical/peralte +
  georref `IfcMapConversion`/`IfcProjectedCRS`; generador IFC4X3 `generate_test_ifc_lineal.py`;
  validación `validacion_alineacion.py` de continuidad/tangencia/PK/georref con integrador de curvatura;
  `export_gis.py` planta→GeoJSON; micro-test positivo+3 negativos), y `ifc-create`/`ifc-validate`
  ampliadas a Alignment (`checks-lineal.py` + SKILL.md). **El núcleo NO se toca** (reutiliza `ifc_utils`;
  espejo md5-idéntico) — la **alineación es referenciación lineal por PK (curva 1D), NO un grafo de red**
  (no usa `grafo_red`, reservado a drenaje/hidráulica de la Ola 6). Caso e2e
  `caso-LIN-01-eje-carretera` (IFC 4.3 → neutro lineal → validación **CUMPLE** → GeoJSON; continuidad
  0,0001 m / tangencia 0,0 rad). **Decisiones resueltas: nº2** (plugin único `obras-lineales`, nace en
  PT 5.2; el parser/validación viven en `iso19650-openbim`) y **nº3** (GIS = **GeoJSON + IFC 4.3**;
  georref leída en el parser lineal). Puertas: **APTO** (`verificar_empaquetado.py`, `--ref` v0.4.3;
  `description` 457/500) y **ESPEJOS IDÉNTICOS** (`verificar_espejo_nucleo.py`, canónico motor v0.23.0).
  **Único reempaquetado:** `iso19650-openbim` v0.5.0 (motor v0.23.0 e `instalaciones` v0.3.0 siguen
  vigentes). **🔜 PT 5.2:** nace la disciplina `obras-lineales` (trazado 3.1-IC / firmes 6.1-IC).
- **v2.9 (22/06/2026):** **INC-12 resuelto** (cola del PT 4.6) → `iso19650-openbim` **v0.4.3**. El **parser MEP**
  `ifc_to_model_mep.py` lee `sistema.clase_riesgo` de `Pset_Estructurando_SistemaPCI.ClaseRiesgo` (o
  `Pset_Estructurando_Red`) del `IfcDistributionSystem` cuando existe; si no, queda `None` y la inyecta el
  agente (respaldo) — el **dato del IFC prevalece**, como con caudal/presión de terminal. El generador
  `generate_test_ifc_rociadores.py` escribe ese Pset (`ClaseRiesgo=OH1`). Con esto la **red de rociadores
  PCI-02 es reproducible sin inyección manual** (req 58,9/margen 241,1 kPa; resultado 0 mismatches/282 claves;
  write-back IFC re-parseado **CUMPLE**, `clase_riesgo` round-trip OH1). **Sin regresión** (BIE/REBT →
  `clase_riesgo=None`, idéntico); **núcleo e `instalaciones` intactos** (el dispatcher ya enrutaba por
  `clase_riesgo`). Puertas **APTO** (`--ref` v0.4.2) + **ESPEJOS IDÉNTICOS**; `description` 434/500. Caso
  PCI-02 regenerado coherente. **Único reempaquetado:** `iso19650-openbim` v0.4.3 (motor v0.23.0 e
  `instalaciones` v0.3.0 siguen vigentes).
- **v2.8 (22/06/2026):** cerrado el **PT 4.6** (verificación y consolidación de la **Ola 4**, análogo al
  PT 1.6 sobre la Ola 1). Entregable `Nucleo-transversal/Verificacion-Ola4.md`. **Veredicto: Ola 4
  CERRABLE ✅ en lo verificado (núcleo de red + PCI + REBT), sin reempaquetar.** Comprobado: (1) **contratos
  C1–C4 coherentes** — el **modelo neutro de red es agnóstico al sistema** (mismo esquema y `unidades` para
  `FIREPROTECTION` y `ELECTRICAL`, solo cambia `sistema.tipo`; la sección del conductor nace en demanda, no
  en el parser, que quedó intacto), write-back con el mismo `Pset_Estructurando_ResultadoRed` y validación
  **sistema-aware** (Pipe/Cable/Duct, con `AIRCONDITIONING→Duct` ya cableado); (2) **regresión** micro-test
  3/3 (grafo, solver de red árbol+mallas, solver eléctrico) y **5 casos e2e** (MEP-01, PCI-01, PCI-02,
  REBT-01, REBT-02) re-ejecutados desde `/tmp` y contrastados contra su JSON de referencia → **PCI sin
  regresión tras REBT** (PCI-01 fuente 600/352,9 kPa; PCI-02 300/58,9 kPa, balance 0,0 %, cierre lazo
  3·10⁻⁶) y **REBT CUMPLE** (REBT-01 ΔU 1,098 %; REBT-02 ΔU 3,318 %; balances 0,0 %); (3) **puertas APTO**
  (`verificar_empaquetado.py`: iso19650 v0.4.2 vs v0.4.1, instalaciones v0.3.0 vs v0.2.0; `description`
  434/481/460 ≤500) y **ESPEJOS IDÉNTICOS** (núcleo **md5-idéntico** en los 3 plugins); (4) **sin defecto de
  empaquetado** (0 truncados, 0 artefactos; **sin divergencia real workspace↔`.plugin`** —los diff de `.py`
  por shell eran el hazard de mount, desmentido con la herramienta `Read`—; el `.md` no sincronizado de
  PT 4.5 **no recurre**, CHANGELOGs al día). **Incidencias:** abierta **INC-12** (P3, la red de rociadores
  PCI-02 necesita la inyección de `sistema.clase_riesgo`=OH1, un dato de proyecto del agente, para no caer a
  demanda BIE; con la inyección reproduce exacto → **no es regresión**); registrada **INC-13** (aproximación
  feeder mono+tri = trifásico equilibrado, ya `[confirmar AN]`). **Decisiones (nº6 y nº7, ver §8):**
  **cerrar la Ola 4 en lo verificado (PCI+REBT) y llevar RITE a una sub-ola 4.x (PT 4.7)**; y **confirmada la
  abstracción "grafo de red + N solvers"** (hidráulico Darcy-Weisbach + eléctrico sobre el mismo grafo; la
  Ola 6 añadirá Manning lámina libre y el clima el de conductos). **No se reempaqueta ningún plugin.**
- **v2.7 (22/06/2026):** cerrado el **PT 4.5** (segundo vertical de instalaciones: **eléctricas, REBT**).
  Nace el **solver de red eléctrica** sobre el **mismo grafo de red** (otro solver sobre la misma
  topología; BT radial → reutiliza la propagación por árbol del solver hidráulico, sin Hardy-Cross):
  `instalaciones/scripts/electrico/` — `bases_demanda_electrica.py` (C4: ITC-BT-10 previsión, ITC-BT-25
  circuitos vivienda C1–C12, ITC-BT-44/-47 receptores; dispatcher vivienda/receptores),
  `solver_electrico.py` (intensidad I=P/(U·cosφ) mono / P/(√3·U·cosφ) tri; **sección propuesta por
  momentos + intensidad admisible** ITC-BT-19; **caída de tensión por intensidades** ΔU=2·L·I·cosφ/(γ·S)
  mono / √3·L·I·cosφ/(γ·S) tri, acumulada + redimensionado), `verificacion_electrico.py` (balance de
  potencias + ΔU ≤ límite 3 %/5 % + I ≤ admisible), `resultado_ifc_electrico.py` (write-back) y
  `run_all_electrico.py`; micro-test 14/14. **Subagente `proyectista-electrico`** + agente
  `ingeniero-de-instalaciones` enruta ELECTRICAL → REBT. **Decisiones:** método **híbrido** (momentos
  para proponer + intensidades para verificar); la **sección del conductor nace en la disciplina**
  (no en el parser → `iso19650` parser **intacto**); **topología radial** confirmada. **INC-11:** el
  validador MEP no era sistema-aware → se hizo dependiente de `sistema.tipo` (Pipe/Cable/Duct), única
  causa para reempaquetar `iso19650-openbim` → **v0.4.2** (validador; parser sin tocar). Casos e2e
  `caso-REBT-01-vivienda` (8 circuitos, ΔU máx 1,098 %) y `caso-REBT-02-terciario` (mono/tri, ΔU máx
  3,318 %): IFC ELECTRICAL → demanda → solver → verificación **CUMPLE** (balance 0,0 %) → Psets de
  resultado al IFC, validado **APTO**; memorias md+docx. **Reempaquetados:** `instalaciones` → **v0.3.0**
  e `iso19650-openbim` → **v0.4.2**, ambos **APTO** y **ESPEJOS IDÉNTICOS** del núcleo (canónico motor
  v0.23.0). **Ola 4: PCI completo (BIE+rociadores) + REBT ✅; pendiente clima (RITE).**
- **v2.6 (22/06/2026):** cerrado el **PT 4.4** (completa el motor hidráulico de red y el vertical PCI).
  **Tres frentes:** (1) **solver de mallas** — `instalaciones/scripts/red/solver_red.py` resuelve el
  reparto hiperestático por **Hardy-Cross** (ciclos fundamentales = cuerdas del árbol generador;
  continuidad en nudos + pérdida nula por lazo, n=2); el árbol es el caso de 0 lazos (**sin regresión**:
  PCI-01 byte a byte); arnés `verificacion_red.py` con **balance nodal con signo** + **cierre por lazo**;
  micro-test de malla 1 lazo (50/50) y 2 lazos. (2) **Rociadores UNE-EN 12845** — `pci/bases_demanda.py`
  por **densidad×área de operación** (LH/OH1-4/HHP), n=⌈A_op/A_cob⌉, K (Q=K·√p), dispatcher BIE/rociadores.
  (3) **Write-back IFC→cálculo→IFC** (decisión: opción **a**) — escritor genérico en `iso19650-openbim`
  (`ifc-create:escribir_psets_resultado.py`) + semántica `Pset_Estructurando_ResultadoRed` en
  `instalaciones` (`red/resultado_ifc.py`); `ifc-validate` reconoce el Pset. Caso e2e
  **`caso-PCI-02-rociadores-malla`** (IFC mallado 3 lazos → demanda OH1 → Hardy-Cross → verificación
  **CUMPLE**, balance 0,0 %, cierre lazo 5·10⁻⁶ kPa → Psets escritos al IFC, validado APTO) + memoria
  md+docx. **Reempaquetados:** `instalaciones` → **v0.2.0** e `iso19650-openbim` → **v0.4.1**, ambos
  **APTO** (`verificar_empaquetado.py`) y **ESPEJOS IDÉNTICOS** del núcleo (`verificar_espejo_nucleo.py`,
  canónico motor v0.23.0). **Ola 4: PCI completo (BIE+rociadores); motor de red con árbol y malla.**
- **v2.5 (22/06/2026):** cerrado el **PT 4.3** (hueco **H3** + motor de cálculo): **nace la disciplina
  `instalaciones`** (plugin **v0.1.0**) con el agente `ingeniero-de-instalaciones` y el subagente
  `proyectista-pci`. Nace el **motor hidráulico de red** (capacidad transversal): `scripts/red/
  solver_red.py` (**Darcy-Weisbach**, fricción Swamee-Jain; reparto de caudales en árbol; propagación de
  presiones desde la fuente con cota; comprobación de BIE) + `scripts/red/verificacion_red.py` (balance de
  caudales ≈0 % y presiones) + micro-test. **Bases de demanda** `scripts/pci/bases_demanda.py` (H3, slot
  C4 no estructural: simultaneidad/caudal/presión de BIE según RIPCI/UNE/DB-SI, `[confirmar AN]`). Caso
  e2e `caso-PCI-01-bie-presion` (IFC→parser MEP PT 4.2→demanda→solver→verificación **CUMPLE**, balance
  0,0 %, fuente 600 vs 352,9 kPa req) + memoria (md+docx). **Frontera confirmada:** lectura IFC MEP en
  `iso19650-openbim`; demanda+cálculo en `instalaciones`. **Decisión nº4 cerrada (INC-10):** núcleo
  **canónico en el motor, espejado byte a byte** a `iso19650-openbim` e `instalaciones`; puerta de
  integridad `verificar_espejo_nucleo.py`. Solo se empaqueta `instalaciones` (motor e iso19650 intactos).
  **Ola 4: H1/H2/H3 ✅.**
- **v2.4 (22/06/2026):** cerrado el **PT 4.2** (hueco **H2**): abierto el **dominio IFC MEP** en
  `iso19650-openbim` → **v0.4.0**. Parser físico→modelo neutro de **red** (`scripts/mep/
  ifc_to_model_mep.py`), generador de IFC MEP de prueba y **validación de red** (continuidad/
  terminales/huérfanas/SI), reutilizando el **núcleo** (`ifc_utils`+`grafo_red`) **sin tocarlo**;
  `ifc-create`/`ifc-validate` ampliadas a MEP. Caso e2e `caso-MEP-01-red-pci` (CUMPLE). El **núcleo se
  espejó** al plugin `iso19650-openbim/scripts/nucleo/` (canónico sigue en el motor) — primer paso del
  espejado previsto en la **decisión nº4**. Sin solver hidráulico (nace con `instalaciones`); gancho
  **H3** (clave `demanda`) listo, no implementado. Pendientes de la Ola 4: **H3** y el solver de red.
- **v2.3 (22/06/2026):** marcada la **Ola 4 como siguiente**, arrancando por **PT 4.1** (hueco H1:
  extraer al núcleo el grafo de red + utilidades IFC; resuelve la decisión abierta nº4). Texto de
  inicio en `INICIO-hilo_PT4.1_grafo-red-nucleo.md`.
- **v2.2 (22/06/2026):** cerrado el **PT 1.6** (verificación de la Ola 1). Contratos C1–C4 coherentes
  con la implementación y edificación cumplida de extremo a extremo (casos 10 y 15). Detectado y
  **corregido** un defecto de empaquetado (8 módulos truncados en el `.plugin` **v0.22.0** →
  reempaquetado **v0.22.1** íntegro). Backlog de la Ola 4 registrado (H1 extraer grafo+utilidades de
  red al núcleo, H2 ampliar IFC a MEP, H3 bases de demanda, H4–H7 menores). Entregable:
  `Nucleo-transversal/Verificacion-Ola1.md`. **Ola 1 cerrada.**
- **v2.1 (22/06/2026):** re-secuenciadas las olas 3 y 4 a petición del Ingeniero de Caminos:
  **Ola 3 = Edificación singular** (empuja el motor de cálculo a FEM de láminas/láminas curvas/
  rigidizadores + 2.º orden y dinámico) y **Ola 4 = Instalaciones completas** (PCI + eléctricas +
  climáticas, donde nace el motor hidráulico de red). Estructuras avanza seguida (olas 1–3).
- **v2.0 (22/06/2026):** incorporada **Obras lineales** como tercera disciplina (trazado,
  firmes, drenaje, obras hidráulicas; soporte IFC 4.3 Alignment + GIS). Añadida la **arquitectura
  de empaquetado** (multi-plugin, mapa de plugins, marketplace) y la **capacidad transversal de
  motor hidráulico de red**. Olas re-secuenciadas a **1–7** (obras lineales en 5–6, puentes como
  remate en 7). Reflejado el cierre de la Ola 1 / PT 1.5 (plugin v0.22.0).
- **v1.0 (22/06/2026):** primera versión. Arquitectura en planos, heurística
  plugin/skill/agente/subagente, contratos C1–C4 del núcleo y olas 1–5 (+ horizonte de obra lineal).
