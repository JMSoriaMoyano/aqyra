# Criterios de despacho - Obra lineal (carreteras)

> Capa transversal de memoria (se acumula entre todos los proyectos de obra lineal).
> Las skills del plugin `obras-lineales` LEEN este archivo al iniciar: mantener formato y ubicación estables.
> Todo resultado derivado debe ser **revisado y firmado por técnico competente** (Ingeniero de Caminos).
>
> **Formato de las memorias:** seguir `formato-memoria-calculo.md` (raíz) y la plantilla
> Word `Plantilla_Memoria_Calculo.docx`, comunes a todas las disciplinas.

## Normativa
- Anejo Nacional / normativa por defecto: **España**.
- **Trazado:** **Norma 3.1-IC** (Trazado, Orden FOM/273/2016) — radios mínimos, clotoides,
  acuerdos verticales (Kv), pendientes, visibilidad (parada/adelantamiento), coordinación.
- **Firmes:** **Norma 6.1-IC** (Secciones de firme) — categoría de tráfico pesado, categoría
  de explanada, catálogo de secciones. 6.3-IC (rehabilitación) fuera de alcance por ahora.
- **Drenaje:** **Norma 5.2-IC** (Drenaje superficial) — hidrología (método racional
  modificado), drenaje de plataforma/márgenes (cunetas) y obras de drenaje transversal (ODT).
- **Saneamiento (PT 6.2):** **EN 752** — redes de colectores en **lámina libre** (Manning) por
  gravedad hasta el vertido. Solver de Manning sobre el **grafo de red** del núcleo.
- **Abastecimiento (PT 6.3):** **EN 805** — redes de distribución **a presión** (Darcy-Weisbach +
  Hardy-Cross en mallas) desde una **fuente** (depósito por cota o bombeo). Solver Darcy sobre el
  **grafo de red** del núcleo (**copia del de `instalaciones`**, decisión nº7). **Cierra la Ola 6.**
- **Soporte IFC/coherencia geométrica:** `iso19650-openbim` v0.7.0 (PT 5.1: IFC 4.3 `IfcAlignment`
  + georreferencia, modelo neutro lineal por PK, validación, export GIS; **PT 6.2: IFC MEP de
  saneamiento** —SEWAGE/STORMWATER/DRAINAGE, cotas de solera, vertido—; **PT 6.3: IFC MEP de
  abastecimiento** —WATERSUPPLY/DOMESTICCOLDWATER, fuente = depósito `IfcTank`/bombeo—).

## Materiales / componentes habituales
- Firme flexible: **mezcla bituminosa (MB)** sobre **zahorra artificial (ZA)**.
- Firme semirrígido (tráfico alto T00/T0): MB sobre **suelocemento (SC)**.
- Explanada: categorías **E1 (Ev2 ≥ 60 MPa) / E2 (≥ 120) / E3 (≥ 300)** [confirmar AN].
- Drenaje: cunetas **triangulares/trapezoidales** (tierra n≈0,025; hormigón n≈0,015);
  ODT en **tubo circular** o **marco** de hormigón (n≈0,013). Dimensión mínima de ODT
  ~1,80 m por conservación/limpieza [confirmar AN].

## Coeficientes y criterios
- **Velocidad de proyecto Vp** = parámetro de proyecto que gobierna TODOS los umbrales de
  trazado (radio mínimo, Kv, pendiente máx, Dp). El **dato del IFC prevalece**; si falta, lo
  inyecta el agente. [confirmar AN].
- **Trazado (3.1-IC):** radio mínimo por Vp (peralte ~7 %); clotoide **A ∈ [R/3, R]** y longitud
  mínima por variación de aceleración centrífuga (J=0,5 m/s³); Kv mínimo convexo
  `Dp²/(2(√h1+√h2)²)` (h1=1,10, h2=0,20 m) y cóncavo `Dp²/(2(h_faros+Dp·tanβ))` (h_faros=0,50 m,
  β=1°); distancia de parada `Dp = Vp·tp/3,6 + Vp²/(254(fl±i))` (tp=2 s); pendiente máx por Vp,
  mínima 0,5 % (drenaje). Todos NDP [confirmar AN] en `scripts/trazado/parametros_3_1_IC.py`.
- **Firmes (6.1-IC):** categoría de tráfico por **IMDp** (vehículos pesados/día en el carril de
  proyecto; en calzada única reparto 50 % por sentido); categoría de explanada por Ev2 (o CBR);
  **selección por catálogo** (no dimensionado por fatiga). Combinaciones T00/T0/T1 × E1 **no
  permitidas** (mejorar explanada). El **dato del IFC prevalece**. NDP [confirmar AN].
- **Drenaje (5.2-IC):** hidrología por el **método racional modificado** — tiempo de
  concentración de **Témez** `tc=0,3·(L/J^0,25)^0,76` [h]; intensidad de la **curva IDF**
  `I=Id·(I1/Id)^[(28^0,1−tc^0,1)/(28^0,1−1)]` con `Id=Pd/24`; **coef. de escorrentía** por
  umbral `Po` (`C=(Pd'/Po−1)(Pd'/Po+23)/(Pd'/Po+11)²`, `Pd'=Pd·KA`); **coef. de uniformidad**
  `Kt=1+tc^1,25/(tc^1,25+14)`; caudal `Q=C·I·A·Kt/3,6` [m³/s]. **Periodos de retorno** por
  tipo de elemento (plataforma/cuneta T≈25, ODT T≈100). **Cunetas** por **Manning de sección
  simple** (capacidad con resguardo + velocidad autolimpieza/erosión); **ODT** por **control de
  entrada/salida** (gobierna el menor) + dimensión mínima. La **cuenca** (A, L, J), la **lluvia
  de proyecto** (Pd, I1/Id, Po) y **T** son **dato del GIS/Pset si existen** (prevalecen); si no,
  los inyecta el agente. Todos NDP [confirmar AN]. **Cálculo LOCAL por elemento, sin grafo de red.**
- **Saneamiento (5.2-IC/EN 752, PT 6.2):** colectores en **lámina libre** por **Manning** sobre el
  **grafo de red**. **Demanda** de aguas residuales (EN 752) = dotación·hab-eq·coef. retorno·coef.
  punta (+ infiltración); dotación 200 l/hab·día, retorno 0,80, punta 2,5 NDP [confirmar AN]. **Solver**
  (`scripts/red/solver_lamina_libre.py`): árbol **desde el vertido** (outfall = ancla; el caudal de un
  tramo es la demanda acumulada aguas arriba), **calado normal** en sección parcialmente llena
  `Q=(1/n)·A·R^(2/3)·J^(1/2)` (J de las **cotas de solera**, reúsa `odt.geom_circular`); **mallas
  cableadas** (Hardy-Cross de lámina libre, cierre por h_f de Manning). Comprobaciones por tramo
  [confirmar AN]: **grado de llenado ≤ 0,75**, **velocidad** [0,6; 5,0] m/s (autolimpieza↔no erosión),
  **pendiente > 0**, **DN ≥ 300 mm**; n de Manning por material (hormigón 0,013, PVC 0,009). Las
  **cotas de solera** son **dato del IFC si existen** (`Pset_Estructurando_Red.CotaSolera`); si no, z
  del nodo [confirmar AN].
- **Abastecimiento (EN 805, PT 6.3):** red **a presión** por **Darcy-Weisbach** sobre el **grafo de
  red**. **Demanda** = dotación·hab-eq·coef. punta (+ **hidrante** concurrente, incluido por defecto);
  dotación 200 l/hab·día, punta 2,5, caudal de incendio 16,7 l/s NDP [confirmar AN]. **Solver**
  (`scripts/red/solver_presion.py`, **copia byte a byte** del de `instalaciones`): árbol **desde la
  fuente** (depósito/bombeo = ancla; el caudal de un tramo es la demanda acumulada aguas abajo),
  pérdida Darcy-Weisbach (Swamee-Jain), **propagación de presión con cota**; **mallas** por Hardy-Cross.
  **Fuente:** depósito por cota → presión 0 + carga `ρ·g·Δz`; bombeo → presión declarada. El dato del
  IFC prevalece (`fuentes[*].presion`). Comprobaciones por tramo [confirmar AN]: **velocidad** [0,5; 2,0]
  m/s (anti-estancamiento↔anti-ariete), **presión dinámica mínima** ≥ 250 kPa en acometidas/hidrantes,
  **DN ≥ DN_min** (80 mm); rugosidad por material (fundición 0,1 mm).
- **Espejo de núcleo (desde PT 6.2):** trazado/firmes/drenaje trabajan sobre el **modelo neutro lineal
  (JSON)**, no usan `grafo_red` (cálculo local); pero **saneamiento y abastecimiento SÍ usan el grafo de
  red** y por tanto el plugin **espeja `scripts/nucleo/`** byte a byte (`verificar_espejo_nucleo.py`
  **aplica** → ESPEJOS IDÉNTICOS). Con el **abastecimiento a presión** (EN 805, Darcy, PT 6.3) **se
  cierra la Ola 6**; el siguiente foco es la **Ola 7 (puentes)**.

## Lecciones aprendidas (crece hilo a hilo)
- [2026-06-22] **Nace la disciplina sobre el modelo neutro lineal** (PT 5.2, análogo a `instalaciones`
  en PT 4.3): la lectura/coherencia del IFC vive en `iso19650-openbim`; el **cálculo de trazado
  (3.1-IC) y la selección de firme (6.1-IC)** viven en `obras-lineales`, que consume el JSON neutro.
  Frontera limpia: geometría/coherencia ↔ cumplimiento normativo. [casos LIN-02/LIN-03]
- [2026-06-22] **Vp es el parámetro gobernante del trazado**: el mismo eje CUMPLE a Vp=60 y NO
  CUMPLE a Vp=100 (radio, clotoides por confort, Kv del acuerdo convexo). La herramienta **no
  rediseña**: reporta CUMPLE/NO CUMPLE + propuesta de predimensionado. [caso LIN-02]
- [2026-06-22] **Frontera con iso19650 (validación vs cumplimiento)**: `validacion_alineacion.py`
  (PT 5.1) comprueba **coherencia geométrica** y deja el 3.1-IC como **aviso informativo** (A∈[R/3,R]);
  el **veredicto normativo vs Vp** es de `obras-lineales`. No duplicar. [caso LIN-02]
- [2026-06-22] **Relleno de ganchos del modelo neutro** (C1 §4bis): firmes rellena `firme`
  (sección de catálogo) y una `secciones_tipo` básica; **solo se añaden claves**, nunca se redefine
  la semántica de las existentes (modelo hermano retrocompatible). `terreno` queda para la Ola 6. [caso LIN-03]
- [2026-06-22] **El dato del IFC prevalece** también aquí (patrón INC-12): Vp (trazado) e
  IMDp/explanada (firmes) del Pset si están; si no, inyección del agente documentada `[confirmar AN]`. [LIN-02/03]
- [2026-06-22] **Firmes por catálogo, no por fatiga** (decisión PT 5.2): la 6.1-IC manda secciones de
  catálogo; el plugin selecciona, no rehace el dimensionado mecanicista. [caso LIN-03]
- [2026-06-22] **Write-back reutiliza la mecánica de iso19650** (`escribir_psets_resultado.py`):
  `Pset_Estructurando_ResultadoLineal` en el `IfcAlignment`; el IFC enriquecido re-parsea y revalida
  CUMPLE (no rompe el modelo). [caso LIN-03]
- [2026-06-22] **Nace el drenaje (PT 6.1, 5.2-IC) como tercer subagente** — el análogo, para el agua,
  de trazado/firmes: hidrología (caudal de cálculo) + capacidad de cunetas (Manning) y ODT (control
  entrada/salida). **Estrena la capacidad transversal C4 de hidrología.** [caso LIN-04]
- [2026-06-22] **El drenaje local NO espeja el núcleo** (igual que trazado/firmes): cuneta/ODT son
  Manning de **sección simple**, cálculo local por elemento sobre el JSON neutro; no hay topología de
  red. El **grafo_red + espejo + IFC MEP de saneamiento** son del **PT 6.2** (colectores). [caso LIN-04]
- [2026-06-22] **Gancho `drenaje` ≠ `terreno`**: el drenaje añade la clave **nueva** `drenaje`
  (caudales/cunetas/ODT, retrocompatible); `terreno` se reserva para **geotecnia/movimiento de tierras**
  y sigue en `None`. Solo se añaden claves, nunca se redefinen las existentes (C1 §4bis). [caso LIN-04]
- [2026-06-22] **La cuenca y la lluvia son dato hidrológico del GIS/Pset** (patrón "el dato del IFC
  prevalece"): A/L/J de la cuenca, Pd/I1Id/Po de la lluvia de proyecto y el periodo de retorno T del
  GIS/estudio pluviométrico si existen; si no, inyección del agente documentada `[confirmar AN]`. [LIN-04]
- [2026-06-22] **Nace el saneamiento (PT 6.2, EN 752) y el SOLVER DE MANNING DE RED** — la disciplina
  **cruza por primera vez la frontera de red**: usa el `grafo_red` del núcleo (espejado byte a byte) y
  consume el IFC MEP de saneamiento. Reutiliza el **motor de red de la Ola 4** (árbol + continuidad +
  Hardy-Cross) con física de **lámina libre** (Manning) en vez de Darcy. [caso LIN-05]
- [2026-06-22] **Fuente invertida = vertido (outfall)**: en saneamiento el ancla del árbol es el
  **vertido**, no una fuente de presión. El parser lo emite en `vertidos[]` (`tipo:"vertido"`) y el
  solver orienta el árbol desde él; el caudal de un tramo es la demanda acumulada **aguas arriba**
  (continuidad invertida respecto a la red a presión). [caso LIN-05]
- [2026-06-22] **Las cotas de solera gobiernan el flujo por gravedad** (dato del IFC, patrón INC-12):
  `J = (solera_aguas_arriba − solera_aguas_abajo)/L`. Si falta el Pset, z del nodo como solera
  `[confirmar AN]`. Si `J ≤ 0` el tramo no desagua (contrapendiente) → NO CUMPLE. [caso LIN-05]
- [2026-06-22] **El saneamiento SÍ espeja el núcleo** (al revés que trazado/firmes/drenaje): al usar el
  grafo de red, `verificar_espejo_nucleo.py` **aplica** y debe dar ESPEJOS IDÉNTICOS. Gancho **nuevo**
  `red` (resumen del veredicto/caudal vertido), retrocompatible; `terreno` sigue en `None`. [caso LIN-05]
- [2026-06-22] **Nace el abastecimiento (PT 6.3, EN 805) REUTILIZANDO el solver Darcy de la Ola 4** — el
  motor hidráulico de red de `instalaciones` (`solver_red.py`) se **copia byte a byte** a
  `obras-lineales/scripts/red/solver_presion.py` (el aislamiento de runtime impide importar entre
  plugins; decisión nº7 "grafo + N solvers"). El solver ya modelaba la **fuente como ancla de presión
  con cota**, así que el **depósito por cota** encaja sin tocar la física: presión 0 en el nudo de lámina
  + propagación `ρ·g·Δz`. **Cierra la Ola 6.** [caso LIN-06]
- [2026-06-22] **Fuente = ancla (al revés que el vertido del saneamiento)**: en abastecimiento el árbol
  se orienta **desde la fuente** y el caudal de cada tramo es la demanda acumulada **aguas abajo**
  (continuidad normal, no invertida). El parser reconoce el **depósito** (`IfcTank`) por **jerarquía
  `is_a(IfcFlowStorageDevice)`**, no por string exacto. [caso LIN-06]
- [2026-06-22] **Hipótesis de incendio (hidrante) concurrente** incluida por defecto en la demanda de
  abastecimiento (decisión del ICCP): el hidrante aporta su caudal de incendio (sin consumo doméstico) y
  exige la presión mínima. Banda de velocidad **0,5–2,0 m/s** (anti-estancamiento↔anti-ariete), distinta
  de la del saneamiento. NDP [confirmar AN]. [caso LIN-06]

## Formato de memoria
- Una memoria por obra, en su subcarpeta.
- Citar siempre la norma y el apartado (3.1-IC / 6.1-IC / 5.2-IC / EN 752 saneamiento / EN 805 abastecimiento).
- Marcar como **[confirmar AN]** los valores NDP no verificados.
- Registro de comprobaciones fechado (AAAA-MM-DD): encargo / datos / parámetros / resultado
  (Vp y veredicto de trazado; IMDp, explanada, código de sección de firme; cuenca, periodo de
  retorno, caudal de cálculo y veredicto de cuneta/ODT en drenaje) / decisión.
- Unidades SI (longitud m, velocidad km/h, pendiente %; caudal m³/s; PK en m).
