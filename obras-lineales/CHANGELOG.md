# CHANGELOG — obras-lineales

Todas las versiones son de **predimensionado/asistencia**; revisar y firmar por tecnico
competente (Ingeniero de Caminos). NDP marcados `[confirmar AN]`.

## v0.4.0 — 2026-06-22 (PT 6.3, Ola 6 · CIERRE)

**Nace el subagente `proyectista-de-abastecimiento` (EN 805) y se REUTILIZA el solver
Darcy-Weisbach de la Ola 4.** Es el **gemelo a presion** del saneamiento (PT 6.2): mismo
**grafo del nucleo** (espejo **sin cambios**) y, en vez del Manning, el **solver Darcy
copiado byte a byte** de `instalaciones` (decision nº7 "grafo + N solvers"; el aislamiento
de runtime impide importar entre plugins -> la copia es la via). **Cierra la Ola 6.**

### Agente / subagente
- `agents/proyectista-de-abastecimiento.md` — **nuevo** subagente (EN 805, red a presion).
- `agents/ingeniero-de-obra-lineal.md` — clasificacion/enrutado ampliados a
  **abastecimiento**, nuevo ejemplo y receta orquestada (IFC MEP -> modelo neutro de red
  -> demanda EN 805 -> solver Darcy -> verificacion -> gancho `red` -> write-back -> memoria).

### Abastecimiento (EN 805) — `scripts/red/` (stdlib pura)
- `solver_presion.py`: **COPIA BYTE A BYTE** del `solver_red.py` de `instalaciones`
  (Darcy-Weisbach, Swamee-Jain; **arbol desde la fuente** + Hardy-Cross en mallas;
  **propagacion de presion con cota**; comprobacion de terminales por presion dinamica
  minima). Solo se anade un banner de procedencia.
- `bases_abastecimiento.py`: **demanda EN 805** = dotacion x hab-eq x coef. de punta
  (+ **hidrante concurrente**, por defecto). Fija la **fuente**: deposito por cota
  (presion 0 + carga rho*g*dz) o bombeo (presion declarada). El dato del IFC prevalece.
- `verificacion_red_presion.py` (balance nodal + presiones/velocidades),
  `run_all_abastecimiento.py` (gancho `red` EN 805 + v_min/DN_min),
  `resultado_red_presion.py` (write-back `Pset_Estructurando_ResultadoRed`),
  `test_abastecimiento.py` **17/17** (deposito por cota + arbol + malla + negativos).

### Nucleo espejado (SIN CAMBIOS)
- `scripts/nucleo/` identico al canonico. `verificar_espejo_nucleo.py` -> ESPEJOS IDENTICOS.

### Caso e2e
- `Casos-de-uso/caso-LIN-06-abastecimiento`: WATERSUPPLY (deposito + anillo) -> demanda
  EN 805 -> solver Darcy -> **CUMPLE** (24,8 l/s; v 0,65–1,03 m/s; Hardy-Cross 6 iter;
  presiones >= 250 kPa; nudo desfavorable ACO-2 margen +40,5 kPa). Write-back re-validado.
  Depende de `iso19650-openbim` **v0.7.0**.

### Decisiones (confirmadas por el ICCP)
- Copia byte a byte del solver; fuente = deposito por cota (bombeo soportado); hidrante
  concurrente por defecto; comprobaciones EN 805 (v 0,5–2,0 m/s, p_min 250 kPa, DN_min)
  `[confirmar AN]`. Puerta **APTO** (`--ref` v0.3.0) + **ESPEJOS IDENTICOS**. Cierra la Ola 6.

## v0.3.0 — 2026-06-22 (PT 6.2, Ola 6)

**Nace el subagente `proyectista-de-saneamiento` (EN 752) y el SOLVER DE MANNING DE RED
en lamina libre.** Es la **primera vez que `obras-lineales` cruza la frontera de red**:
usa el **grafo del nucleo** (decision nº7 "grafo + N solvers"), **espeja el nucleo** y
consume el **dominio IFC MEP** de saneamiento. Reutiliza el **motor de red** de la Ola 4
(construccion del arbol + reparto por continuidad + Hardy-Cross) con fisica de **lamina
libre** (Manning) en vez de Darcy a presion. **Cierra el bloque de saneamiento de la
Ola 6**; el abastecimiento a presion (EN 805, Darcy) queda para el **PT 6.3**.

### Agente / subagente
- `agents/proyectista-de-saneamiento.md` — **nuevo** subagente (EN 752, lamina libre).
- `agents/ingeniero-de-obra-lineal.md` — clasificacion/enrutado ampliados a
  **saneamiento** (red de colectores), nuevo ejemplo y receta orquestada (IFC MEP ->
  modelo neutro de red -> demanda residual -> solver de Manning -> verificacion ->
  gancho `red` -> write-back -> memoria).

### Saneamiento (EN 752) — `scripts/red/` (stdlib pura, reusa `drenaje/odt.py`)
- `solver_lamina_libre.py`: **solver de Manning sobre el grafo**. Orienta la red como
  **arbol desde el VERTIDO** (outfall = ancla), reparte el caudal por **continuidad
  aguas arriba** y resuelve el **calado normal en seccion parcialmente llena**
  (`Q=(1/n)·A·R^(2/3)·J^(1/2)`, J de las **cotas de solera**) reutilizando
  `odt.geom_circular`. **Mallas cableadas**: el arbol es el caso de 0 lazos; con cuerdas
  se activa un **Hardy-Cross de lamina libre** (cierre por h_f de Manning). Comprueba por
  tramo **grado de llenado** (<=0,75), **velocidad** (0,6–5,0 m/s), **pendiente** (>0) y
  **DN minimo** (300 mm). Reporta el regimen (Froude). NDP `[confirmar AN]`.
- `bases_saneamiento.py`: **demanda de aguas residuales** (EN 752) = dotacion x
  habitantes-eq x coef. de punta x coef. de retorno (+ infiltracion); el `caudal_min`
  del IFC prevalece. Regimen separativo; gancho `aplicar_pluviales` (red unitaria,
  reusa la hidrologia 5.2-IC) documentado. NDP `[confirmar AN]`.
- `verificacion_red_lineal.py`: **balance nodal con signo** (continuidad **hacia el
  vertido**, invertida respecto a la red a presion) + cierre por lazo + comprobaciones
  por tramo. `run_all_obras_hidraulicas.py` (CLI) rellena el gancho **`red`** del modelo.
  `resultado_red_lineal.py`: write-back `Pset_Estructurando_ResultadoRed`. Micro-test
  `test_obras_hidraulicas.py` **16/16** (positivo + 4 negativos + malla).

### Nucleo espejado (NUEVO en obras-lineales)
- `scripts/nucleo/` = `grafo_red.py` + `ifc_utils.py` + `test_grafo_red.py` (+ README),
  **espejados byte a byte** desde el motor canonico (v0.23.0). Puerta
  `verificar_espejo_nucleo.py` -> **ESPEJOS IDENTICOS**.

### Gancho C1 §4
- Clave **nueva** `red` = `{norma:"EN 752", regimen, metodo, veredicto, caudal_total_
  vertido_l_s, velocidad_pico_m_s, llenado_pico_pct, topologia}` (retrocompatible).
  `terreno` sigue en `None`.

### Caso e2e
- `Casos-de-uso/caso-LIN-05-saneamiento`: red de colectores residuales (IFC MEP SEWAGE)
  -> modelo neutro de red -> demanda EN 752 -> solver de Manning -> calado/velocidad/
  llenado por tramo -> **CUMPLE** (caudal vertido 31,9 l/s; v 0,82–1,11 m/s; llenado
  17–24 %). Write-back del Pset de resultado de red. Depende de `iso19650-openbim`
  **v0.6.0** (parser/validacion/generador MEP de saneamiento).

### Decisiones
- **Cotas de solera**: dato del Pset/IFC si esta (prevalece); si no, **z del nodo**
  `[confirmar AN]`. **Fuente invertida**: el ancla del arbol es el **vertido** (outfall),
  `tipo:"vertido"` en `vertidos[]`. **Seccion**: circular por defecto (gancho
  ovoide/marco). **Demanda**: aguas **residuales** (separativo) en el caso base.
- Puerta **APTO** (`verificar_empaquetado.py`, `--ref` v0.2.0) y **ESPEJOS IDENTICOS**
  (`verificar_espejo_nucleo.py`, canonico el motor).

## v0.2.0 — 2026-06-22 (PT 6.1, Ola 6)

**Nace el subagente `proyectista-de-drenaje` (Norma 5.2-IC, Drenaje superficial)** — el
analogo, para el agua de lluvia, de lo que trazado/firmes hicieron con la geometria y el
firme. Estrena la capacidad transversal **C4 de hidrologia** (caudales de calculo).

### Agente
- `agents/ingeniero-de-obra-lineal.md` — clasificacion/enrutado ampliados a **drenaje**
  (ademas de trazado/firmes), nuevo ejemplo y receta orquestada (cuenca/GeoJSON ->
  hidrologia -> capacidad de cuneta/ODT -> verificacion -> gancho `drenaje` -> memoria).
- `agents/proyectista-de-drenaje.md` — subagente Norma **5.2-IC** (hidrologia + cunetas + ODT).

### Drenaje (5.2-IC) — `scripts/drenaje/` (stdlib pura)
- `hidrologia.py`: **metodo racional modificado** (cuencas pequenas) — tiempo de
  concentracion de **Temez**, intensidad de la **curva IDF 5.2-IC** (`Id=Pd/24`, ley
  `It/Id`), coef. de **escorrentia** por umbral Po, coef. de **uniformidad Kt**, factor
  reductor areal **KA**, `Q=C·I·A·Kt/3.6`; periodos de retorno por tipo de elemento. NDP
  `[confirmar AN]`.
- `cuneta.py`: capacidad por **Manning de seccion simple** (triangular/trapezoidal),
  calado normal por biseccion, **resguardo** y **velocidad** (autolimpieza/erosion) ->
  CUMPLE/NO CUMPLE vs el caudal de calculo.
- `odt.py`: capacidad de **obra de drenaje transversal** (tubo circular/marco) por
  **control de entrada/salida** (gobierna el menor), **dimension minima** y velocidad ->
  vs el caudal de la cuenca vertiente.
- `verificacion_drenaje.py` (recuento + veredicto + informe) · `run_all_drenaje.py` (CLI:
  modelo + `--datos` -> caudales -> cunetas/ODT -> veredicto + JSON; rellena el gancho
  `drenaje`) · `test_drenaje.py` (micro-test 13/13: positivos + negativos de cuneta/ODT).

### Gancho del modelo neutro (C1 §4bis)
- Clave **nueva** `drenaje = {cuencas[], cunetas[], odt[]}` (retrocompatible; solo se
  **anaden** claves, no se redefinen las existentes). `terreno` **sigue en `None`**
  (geotecnia/movimiento de tierras).

### Caso e2e
- `caso-LIN-04-drenaje`: eje de `caso-LIN-01` -> cuenca de plataforma (T=25) -> caudal
  racional -> **cuneta CUMPLE**; cuenca vertiente -> **ODT** -> veredicto razonado.

### Decisiones
- **Sin espejo de nucleo (igual que trazado/firmes):** cuneta/ODT son **Manning de
  seccion simple, calculo LOCAL por elemento** sobre el JSON neutro; no hay topologia de
  red ni lectura IFC -> `verificar_espejo_nucleo.py` **no aplica**. El **grafo_red +
  espejo + IFC MEP de saneamiento** entran en el **PT 6.2** (colectores).
- **El dato del GIS/Pset prevalece** para la cuenca (A/L/J) y la lluvia (Pd, I1/Id, Po) y
  el periodo de retorno T; si falta, lo inyecta el agente (`[confirmar AN]`).
- **Hidrologia: metodo racional modificado 5.2-IC** (predimensionado; gancho para
  hidrogramas si hiciera falta).

### Puertas
- `verificar_empaquetado.py obras-lineales-v0.2.0.plugin --ref obras-lineales-v0.1.0.plugin`
  -> APTO; `description` 483/500. Espejo de nucleo: **no aplica** (sin `scripts/nucleo/`).

## v0.1.0 — 2026-06-22 (PT 5.2, Ola 5)

**Nace la disciplina `obras-lineales`** sobre el soporte georreferenciado del PT 5.1
(`iso19650-openbim` v0.5.0). Analogo lineal de lo que el PT 4.3 hizo con `instalaciones`.

### Agente y subagentes
- `agents/ingeniero-de-obra-lineal.md` — clasifica (trazado/firmes/ambos), enruta,
  orquesta (IFC -> modelo neutro lineal [iso19650-openbim] -> comprobacion/seleccion ->
  verificacion -> relleno de ganchos -> memoria) y ensambla el entregable.
- `agents/proyectista-de-trazado.md` — subagente Norma **3.1-IC**.
- `agents/proyectista-de-firmes.md` — subagente Norma **6.1-IC**.

### Trazado (3.1-IC) — `scripts/trazado/`
- `parametros_3_1_IC.py`: tablas/formulas por velocidad de proyecto Vp (radio minimo,
  pendiente maxima, distancia de parada Dp, Kv minimo convexo/concavo, limites de
  clotoide). NDP `[confirmar AN]`.
- `comprobacion_trazado.py`: comprueba planta (radio, A y longitud de clotoide), alzado
  (Kv de acuerdos, pendientes), coordinacion planta-alzado y visibilidad -> CUMPLE/NO
  CUMPLE por elemento con propuesta de predimensionado.
- `verificacion_trazado.py` (recuento + veredicto + informe) · `run_all_trazado.py` (CLI)
  · `test_trazado.py` (micro-test 7/7).

### Firmes (6.1-IC) — `scripts/firmes/`
- `bases_firme.py`: categoria de trafico pesado (IMDp, o IMD + %pesados) y de explanada
  (Ev2 o CBR). NDP `[confirmar AN]`.
- `catalogo_6_1_IC.py`: catalogo literal de secciones (firme flexible MB/zahorra y
  semirrigido MB/suelocemento) por combinacion permitida trafico x explanada.
- `seleccion_firme.py`: selecciona la seccion y **rellena los ganchos** `firme` y
  `secciones_tipo` del modelo neutro lineal (solo añade claves; retrocompatible).
- `verificacion_firme.py` (combinacion permitida + espesores) · `run_all_firme.py` (CLI)
  · `test_firme.py` (micro-test 7/7).

### Comun y memoria
- `scripts/comun/resultado_ifc_lineal.py`: semantica del Pset
  `Pset_Estructurando_ResultadoLineal` para el write-back (la mecanica IFC es de
  `iso19650-openbim:ifc-create`).
- `skills/criterios-memoria/SKILL.md`: memoria de la disciplina (C2/C3).

### Casos e2e
- `caso-LIN-02-trazado`: eje de `caso-LIN-01` -> trazado 3.1-IC a Vp=60 -> **CUMPLE**
  (NO CUMPLE a Vp=100, sensibilidad documentada).
- `caso-LIN-03-firmes`: IMD 8000 / 12% pesados / calzada unica / Ev2 150 -> T2 x E2 ->
  seccion **221** (MB 18 + ZA 30) -> gancho `firme` relleno -> **CUMPLE**.

### Decisiones
- **Sin espejo de nucleo** (no se lee IFC ni se usa `grafo_red`; se trabaja sobre el JSON
  neutro): la puerta `verificar_espejo_nucleo.py` no aplica.
- **El dato del IFC prevalece** para Vp e IMDp/explanada (patron INC-12).
- **Firmes por catalogo** (6.1-IC), no dimensionado parametrico por fatiga.

### Puertas
- `verificar_empaquetado.py obras-lineales-v0.1.0.plugin` -> APTO; `description` <= 500.
