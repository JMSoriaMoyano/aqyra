INICIO de hilo — PT 7.5 (Ola 7): **TABLEROS AVANZADOS** sobre **FEM-2** — tableros
**metálicos y mixtos** (lámina rigidizada + conectores, **abolladura** y **fatiga**), tableros
**oblicuos** (esviaje) y tableros **curvos** (mallado sobre el **Alignment** curvo, torsión).
Tres verticales nuevos de la disciplina `puentes` apoyados en la capacidad **FEM-2** que el
PT 7.4 ya entregó (lámina curva MITC4 + rigidizador con offset + pared delgada), entregados
**IFC-driven** con sus casos de aplicación (PUE-18, PUE-19, PUE-20). Proyecto Estructurando.
Ejecuta el **PT 7.5**. La **escalera FEM permanece en FEM-2**: este PT, como el 7.3, es de
**disciplina, no de motor** — `motor-fem` v0.3.0 se reutiliza tal cual (lámina curva +
rigidizador + offset rígido + Bredt/shear lag ya bastan); solo se añade idealización +
comprobación EC3/EC4 + extensión del lector.

> Todo cálculo y entregable es de **predimensionado/asistencia y debe ser revisado y firmado por
> técnico competente** (Ingeniero de Caminos, Canales y Puertos). Los NDP se marcan `[confirmar AN]`.

---

## Objetivo del hilo (tres verticales encadenados sobre FEM-2)

1. **Tableros metálicos y mixtos** (subagente `proyectista-mixto`): tablero **bijácena/multijácena
   de acero** o **cajón metálico** (chapas con **rigidizadores longitudinales/transversales**) y
   **mixto acero-hormigón** (losa de hormigón conectada a las vigas de acero). Idealización por
   lámina rigidizada (FEM-2); la **losa mixta** = láminas de hormigón + **viga de acero como
   rigidizador con offset rígido** (interacción completa — es exactamente la acción compuesta ya
   validada en `placa_rigidizada`). Comprobación **EC3** (resistencia de secciones de clase 1-4,
   **abolladura de paneles** EN 1993-1-5 por **ancho eficaz**) + **EC4** (conexión, **conectores**,
   resistencia de la sección mixta — reúso de `motor-calculo` mixtas). **Fatiga** EN 1993-1-9
   (categoría de detalle, Δσ) — ver decisiones.
2. **Tableros oblicuos** (subagente `proyectista-oblicuo`): tablero (losa o emparrillado/lámina) con
   **esviaje** — los apoyos no son perpendiculares al eje. Idealización por **malla que sigue la
   línea de apoyo oblicua** (la lámina curva MITC4 ya admite cuadriláteros distorsionados);
   **reparto transversal 2D** y líneas de influencia 2D bajo LM1; concentración de reacciones en
   la esquina obtusa (efecto de esviaje). Comprobación **EC2** (losa) o **EC3** (metálico).
3. **Tableros curvos** (subagente `proyectista-curvo`): tablero con **planta curva** sobre el eje del
   **IfcAlignment** (Ola 5). Idealización mallando las láminas **siguiendo la curvatura** (la lámina
   curva las representa nativamente); **torsión acoplada a la flexión** (la curvatura genera torsión
   bajo carga vertical). Comprobación **EC2/EC3** con la **torsión** como protagonista (Bredt si es
   cajón; alabeo si es abierto). Reúso del **parser de Alignment** (`iso19650` lineal, Ola 5) para
   el eje y de la **pared delgada** del motor (Bredt/distorsión).

Cada vertical: **idealización** (reúso de lámina curva + rigidizador) + **acciones IAP-11** + `motor-fem`
**FEM-2** (estático + envolventes LM1 + modal) + **comprobación EC** + **memoria + write-back**.
Entregados **IFC-driven**: extensión del **lector** (parser C1 + adaptador `desde_ifc`) a las
tipologías `mixto`/`oblicuo`/`curvo`, y los **casos PUE-18/19/20**.

---

## Contexto — estado de la Ola 7 (para situar el hilo)

- **PT 7.0 ✅** `motor-fem` v0.1.0 (FEM-0). **PT 7.1 ✅** `puentes` v0.1.0 + FEM-1.
  **PT 7.2 ✅** `puentes` v0.2.0 (losa postesada, pórtico, celosía) + `motor-fem` v0.2.1.
  **PT 7.3 ✅** `puentes` v0.3.0 (pila + apoyo + cimentación, estribo) — **motor sin tocar**.
  **PT 7.3.1 ✅** lector estructural IFC + 10 casos: `iso19650` v0.9.0 + `puentes` v0.4.0.
  **PT 7.4 ✅** **FEM-2** + **cajón postesado**: `motor-fem` **v0.3.0** (lámina curva MITC4 +
  rigidizador offset + pared delgada Bredt/shear lag, NAFEMS ±5%), `puentes` **v0.5.0** (cajón por
  lámina pura, EC2 fases/torsión/shear-lag, `caso-PUE-17` CUMPLE), `iso19650` **v0.9.1** (tipología
  `cajon`).
- **Escalera FEM:** FEM-0 ✅ · FEM-1 ✅ · **FEM-2 ✅** · FEM-3 (arco/pandeo) · FEM-4
  (cable/membrana, atirantado) · FEM-5 (dinámica avanzada). **Este PT NO sube de peldaño**: agota
  la capacidad FEM-2 ya entregada en tres tipologías más.
- El **oráculo PyNite** es EB+DKMQ. **FEM-2 no tiene oráculo PyNite** → la **abolladura por
  autovalores** (pandeo) **no se aborda aquí** (es FEM-3): la abolladura se resuelve por **EC3-1-5
  (ancho eficaz)**, que es un **check normativo**, no un cálculo de autovalores.

---

## Lo que YA existe y se reutiliza (clave para acotar el alcance)

- **`motor-fem` v0.3.0 (FEM-2)** — **se reutiliza ÍNTEGRO, sin tocar** (no-regresión por
  construcción, como en PT 7.3): `elementos/lamina_curva.py` (`LaminaCurvaMITC4`),
  `elementos/rigidizador.py` (`ElementoRigidizador`, **offset rígido = acción compuesta**),
  `fem2.py` (`ElementoLaminaCurva` + `bredt_J`/`shear_lag_beff`/`indicador_distorsion`), `fem1.py`
  (modal + móvil, objetivo `esfuerzo_lamina`), `fem_core.py` (ensamblaje + estático).
  **El rigidizador con offset YA es el conector de interacción completa** de la sección mixta (lo
  validó `placa_rigidizada`: sección T compuesta vs Euler 1,3 %).
- **`puentes` v0.5.0** — patrones directos a imitar: `idealizacion/cajon.py` (**malla de láminas
  curvas + rigidizadores, nudos fundidos por coordenada, recuperación de momento de sección**),
  `comprobacion/ec2_cajon.py` (fibras del FEM + Bredt + shear lag), `run_all_cajon.py` (flujo e2e,
  acepta `.ifc`, modal informativo), `acciones/iap11.py`, `comun/resultado_ifc_puente.py`
  (write-back), `lectura/desde_ifc.py` (adaptador por tipología — **se extiende**),
  `lectura/gen_cases.py` (builders IFC4X3 — **se extiende**), `validacion/cajon_vs_viga.py`.
- **`motor-calculo-estructural`** (por PYTHONPATH, **reúso por fórmula**): **mixtas EC4**
  (`scripts/mixtas`, `run_all_mixta`: M_Rd con grado de conexión, **conectores**, cortante, flecha
  por fases construcción/mixta), **acero EC3** (clasificación de secciones, resistencia, pandeo;
  skill `acero-ec3`), **EN 1993-1-5** abolladura por ancho eficaz. Recordar el **stub de PyNite** o
  copia byte-fiel de las partes puras (los solvers importan PyNite a nivel de módulo).
- **`iso19650-openbim` v0.9.1**: `scripts/estructural/ifc_to_model_estructural.py` (lee secciones de
  acero `IfcIShapeProfileDef` y cajón con huecos; clasifica tipologías) y
  `scripts/lineal/ifc_to_model_lineal.py` (**eje por `IfcAlignment`, planta/alzado por PK** — clave
  para el tablero **curvo**).

> **Hueco real a construir:** la **idealización** de cada tablero (lámina rigidizada metálica;
> losa+viga mixta por offset; malla oblicua; malla sobre eje curvo) y su **comprobación**
> (EC3 abolladura/fatiga, EC4 conexión, reparto oblicuo, torsión en curvo). El motor, el lector, el
> postesado, IAP-11 y el write-back **ya existen** y solo se extienden.

---

## Frontera (contratos del núcleo) — respétala

- **C5 (`motor-fem`):** **NO cambia** (FEM-2 ya cubre lámina curva + rigidizador + offset + pared
  delgada). Excepción única: si se decide **interacción parcial** (deslizamiento conector), sería un
  elemento de conexión **aditivo** (gancho FEM-2.x) — ver decisiones; recomendado **dejarlo fuera**.
- **C1 (`iso19650-openbim`):** el parser **clasifica** las tipologías `mixto`/`oblicuo`/`curvo`
  (claves aditivas: ángulo de esviaje, perfil de acero, referencia al Alignment); lee la geometría
  metálica (perfiles I/cajón) y el eje curvo. Lectura/escritura IFC.
- **`puentes`:** crece con los **tres verticales** + la **extensión del adaptador** `desde_ifc` y de
  `gen_cases`. Reúso de lámina/rigidizador, IAP-11, EC4/EC3 de `motor-calculo`, y write-back.
- **`motor-calculo`:** no se migra; se **reutilizan** sus fórmulas de mixtas/EC3 por PYTHONPATH.

---

## Decisiones a resolver y documentar (antes de mover una línea)

- **Sección mixta: ¿interacción completa por offset, o parcial con conector?** Recomendado:
  **interacción completa** modelando la viga de acero como **rigidizador con offset rígido** bajo la
  losa de láminas (ya validado como acción compuesta); la **comprobación de conectores** (nº, paso,
  P_Rd) se hereda de **EC4** (`motor-calculo` mixtas) por fórmula. La interacción parcial (slip) queda
  como **gancho** (requeriría un elemento de conexión nuevo). `[confirmar AN]`
- **Abolladura de paneles metálicos: ¿EC3-1-5 ancho eficaz, o pandeo por autovalores?** Recomendado:
  **EN 1993-1-5 (ancho/área eficaz)** — coherente con FEM-2 lineal y con la práctica de
  predimensionado; el **pandeo por autovalores** (sensibilidad a imperfecciones) se difiere a **FEM-3**.
  `[confirmar AN]`
- **Fatiga (EN 1993-1-9): ¿check de Δσ o gancho diferido?** Recomendado: **check básico** —
  carrera de tensiones Δσ del **modelo de fatiga FLM3** en el detalle crítico vs **Δσ_C/γ_Mf** por
  **categoría de detalle**; sin daño acumulado (Palmgren-Miner) ni espectro completo, que quedan como
  gancho. (En celosía la fatiga se dejó como gancho; aquí se da un peldaño más.) `[confirmar AN]`
- **Tablero oblicuo: ¿malla romboidal (sigue el esviaje) o malla ortogonal con borde oblicuo?**
  Recomendado: **malla que sigue la línea de apoyo oblicua** (cuadriláteros distorsionados que la
  lámina MITC4 ya soporta), reportando la **concentración de reacción en la esquina obtusa** y el
  **reparto transversal**. `[confirmar AN]`
- **Tablero curvo: ¿reusar el Alignment de Ola 5 o parametrizar la curva?** Recomendado: **reusar el
  `IfcAlignment`** (parser lineal `iso19650`) para el eje en planta y **mallar las láminas siguiendo
  la directriz curva**; la **torsión** (acoplada a la flexión por la curvatura) se comprueba por
  **Bredt** (cajón) o se reporta el **alabeo** (sección abierta). `[confirmar AN]`
- **¿Sube el motor?** Recomendado: **`motor-fem` v0.3.0 INTACTO** (como en PT 7.3). Solo si se acepta
  interacción parcial entraría una extensión aditiva. `[confirmar AN]`
- **Validación sin oráculo PyNite:** **EC4 vs `motor-calculo` mixtas** (ya validado), **acción
  compuesta** (`placa_rigidizada` ya OK), **abolladura EC3-1-5** vs ejemplo de catálogo/SteelConstruct,
  **reparto oblicuo** vs malla ortogonal fina o solución de losa esviada, **torsión del curvo** vs
  **teoría de viga curva** (flexo-torsión acoplada). Tolerancias: NAFEMS/predim **±2–5 %**
  `[confirmar AN]`; no-regresión FEM-0/1/2 **exacta** (el motor no se toca).

---

## Los casos de aplicación (PUE-18/19/20), IFC-driven

- `caso-PUE-18-tablero-mixto`: **generar IFC4X3** (vigas de acero `IfcIShapeProfileDef` o cajón
  metálico + losa de hormigón `IfcSlab`; Psets de conexión/rigidizadores) → **lector** (tipología
  `mixto`) → idealización (losa de láminas + vigas como rigidizador offset) → FEM-2 → **EC3+EC4**
  (abolladura ancho eficaz, conectores, sección mixta, fatiga básica) → memoria + write-back.
- `caso-PUE-19-tablero-oblicuo`: tablero (losa o lámina) con **esviaje α** (Pset) → lector
  (tipología `oblicuo`) → **malla oblicua** → FEM-2 (LM1 2D) → **EC2/EC3** + reparto y reacción de
  esquina obtusa → memoria + write-back.
- `caso-PUE-20-tablero-curvo`: tablero **curvo** sobre `IfcAlignment` (radio R) → lector (tipología
  `curvo`, eje de Ola 5) → **malla sobre la directriz curva** → FEM-2 (**torsión** acoplada) →
  **EC2/EC3** + Bredt → memoria + write-back.

Carpetas con el conjunto estándar IFC-driven (ver `Casos-de-uso/INDICE-PUE.md` y la plantilla
`caso-PUE-05-pila-cimentacion/README-IFC-driven.md`), y filas nuevas en `INDICE-PUE.md` (sección
**Avanzados — FEM-2**, junto a PUE-17).

---

## Lee primero, en este orden

1. `Hoja-de-ruta_Ola7-puentes-y-motor-FEM.md` — **§3 (escalera FEM, FEM-2 ya hecho)**, **§4
   (tipologías: metálicos/mixtos, oblicuos, curvos)**, la **tabla de PTs (7.5)**, **§7 (conexión
   Ola 3)** y el **registro v1.6** (cierre PT 7.4).
2. `Nucleo-transversal/C5_Contrato-motor-FEM.md` — **§4 (librería de elementos: lámina curva +
   rigidizador, ya disponibles)** y **§8 (FEM-2 ✅)** — confirmar que **no hace falta tocar el motor**.
3. **`puentes` v0.5.0** (`scripts/`): `idealizacion/cajon.py` (**el patrón de mallado por láminas +
   rigidizadores a imitar**), `comprobacion/ec2_cajon.py`, `run_all_cajon.py`, `acciones/iap11.py`,
   `comun/resultado_ifc_puente.py`, `lectura/desde_ifc.py` y `lectura/gen_cases.py` (**adaptador y
   generador a extender**), `validacion/cajon_vs_viga.py`.
4. **`motor-calculo-estructural`**: `scripts/mixtas` (`run_all_mixta`, EC4: conexión, conectores,
   fases) y la skill/lógica de **acero EC3** + **EN 1993-1-5** (abolladura por ancho eficaz). Recordar
   el **stub de PyNite**.
5. **`iso19650-openbim` v0.9.1**: `scripts/estructural/ifc_to_model_estructural.py` (perfiles de acero
   y clasificación de tipología) y `scripts/lineal/ifc_to_model_lineal.py` (**eje por Alignment** para
   el curvo).
6. `criterios-despacho.md` — lecciones PT 7.0–7.4 (oráculo EB/DKMQ; **drilling = 1/1000 de la
   flexión**; offset rígido = acción compuesta; lámina pura; facetas planas y doble curvatura;
   **hazard de mount que corrompe**, fuente de verdad = `.plugin`/Read; stub de PyNite; geometría
   extruida real).

---

## Entregable

- **`puentes` v0.6.0 (.plugin)**: tres verticales — `idealizacion/{mixto,oblicuo,curvo}.py`,
  `comprobacion/{ec3ec4_mixto,ec_oblicuo,ec_curvo}.py`, `run_all_{mixto,oblicuo,curvo}.py`, subagentes
  `proyectista-mixto`/`proyectista-oblicuo`/`proyectista-curvo`, extensión de `desde_ifc.py` y
  `gen_cases.py`, validaciones en `scripts/validacion/`. Lámina/rigidizador/IAP-11/write-back reusados.
- **`iso19650-openbim` vX.Y (.plugin)**: clasificación de `mixto`/`oblicuo`/`curvo` (claves aditivas:
  esviaje, perfil de acero, ref. Alignment).
- **`motor-fem` v0.3.0 — SIN CAMBIOS** (se distribuye igual; demostrar no-regresión FEM-0/1/2).
- **`caso-PUE-18-tablero-mixto`, `caso-PUE-19-tablero-oblicuo`, `caso-PUE-20-tablero-curvo`**
  documentados (IFC + lectura + FEM-2 + EC + memoria + write-back) + filas en `INDICE-PUE.md`.
- **Actualizar**: hoja de ruta Ola 7 (PT 7.5 ✅ → PT 7.6 🔜), `criterios-despacho.md` (lección
  PT 7.5) y la memoria del proyecto.
- **Puertas de calidad obligatorias** (pega su salida en el cierre):
  `TMPDIR=/tmp HOME=/tmp PYTHONPATH=/tmp/pylibs python3 Nucleo-transversal/verificar_empaquetado.py <plugin>.plugin --ref <previo>.plugin`
  (**APTO**, `description` ≤500) para `puentes` v0.6.0 e `iso19650` vX.Y, **y**
  `verificar_espejo_nucleo.py --canonico <motor-calculo>.plugin <plugin>.plugin` (**ESPEJOS
  IDÉNTICOS**), **y** la **no-regresión FEM-0/1/2** (el motor no se toca) + los **casos PUE-18/19/20 e2e**.

---

## Notas de método (críticas, confirmadas en PT 4.x–7.4)

- **Entorno / ifcopenshell:** `/tmp/pylibs` puede quedar **read-only** de una sesión previa →
  instala `ifcopenshell` en target limpio `pip install --no-cache-dir --target=/tmp/ifclib ifcopenshell`
  (v0.8.5) y ejecuta con `PYTHONPATH=/tmp/ifclib:/tmp/pylibs`. Exporta siempre
  **`TMPDIR=/tmp HOME=/tmp PIP_NO_CACHE_DIR=1 MPLCONFIGDIR=/tmp/mplcache`**.
- **Hazard de mount (agravado en PT 7.4):** los ficheros **editados con Edit** se leen **corruptos**
  (no solo truncados) desde el shell — `diff` los da "idénticos" porque ambos mount-reads se corrompen
  igual. **Fuente de verdad: el `.plugin` (zip, unzip fiable) o el Read del agente**, NO el bash-read
  del workspace. **Desarrolla y empaqueta en `/tmp`**; los loose dirs pueden estar en versiones
  viejas → **canónico = el `.plugin` de mayor versión**. `plugin.json` vive en `.claude-plugin/`;
  excluye `__pycache__`/`*.pyc` al empaquetar; verifica el `cp /tmp→workspace` por tamaño exacto.
- **Disco `/sessions`** puede estar al 100 % → extracciones a `/tmp` (`TMPDIR=/tmp`).
- **PyNite no está en el sandbox**: para reutilizar fórmulas de `motor-calculo` (mixtas/EC3) basta un
  **stub de `Pynite`** en el PYTHONPATH o **copia byte-fiel** de la parte pura. **FEM-2 no tiene
  oráculo PyNite** → validar con **EC4/EC3 del motor-calculo + acción compuesta + EC3-1-5 + teoría de
  viga curva**.
- **IFC de puentes = IFC4X3 SIEMPRE** (`IfcBearing`/`IfcAlignment`/`IfcBridge` no existen en IFC4;
  `IfcStructuralProfileProperties` se eliminó tras IFC2X3). Acero por `IfcIShapeProfileDef`; cajón
  metálico por `IfcArbitraryProfileDefWithVoids`; eje curvo por `IfcAlignment` (Ola 5).
- **Reutiliza, no reescribas:** el **rigidizador con offset YA es la acción compuesta** (no inventes
  un conector si vas a interacción completa); la lámina curva YA admite quads distorsionados (oblicuo)
  y curvos (curvo); el lector y el write-back YA están. La regla de oro: *"¿qué es realmente nuevo
  (idealización mixta/oblicua/curva + EC3/EC4/abolladura/fatiga/torsión) y qué ya está?"* — solo se
  construye lo primero. **El motor NO se toca** (es un PT de disciplina, como el 7.3).
- Todo es **predimensionado, a revisar y firmar por técnico competente** (ICCP); NDP `[confirmar AN]`.

**Empieza** leyendo los documentos (hoja de ruta §3/§4 + tabla 7.5 + §7 + registro v1.6, **C5 §4/§8**,
el plugin `puentes` v0.5.0 —`cajon.py` como patrón de mallado por láminas/rigidizadores, EC2, adaptador
`desde_ifc`, `gen_cases`—, las **mixtas/EC3 de `motor-calculo`** y el **lector de Alignment de
`iso19650`**), y **proponiendo, antes de mover una línea: (a)** la **idealización de cada tablero**
(mixto = losa de láminas + viga de acero como rigidizador offset, interacción completa; oblicuo = malla
sobre la línea de apoyo esviada; curvo = malla sobre el Alignment, torsión acoplada) confirmando que
**el motor no se toca**; **(b)** el **alcance normativo** (EC4 conexión/conectores por reúso, EC3-1-5
abolladura por ancho eficaz, fatiga EN 1993-1-9 ¿check Δσ o gancho?, EC2 oblicuo, torsión Bredt/alabeo
curvo); **(c)** el **plan de validación** (EC4 vs motor-calculo + acción compuesta + EC3-1-5 + reparto
oblicuo vs malla fina + torsión curvo vs viga curva) y los **casos PUE-18/19/20** con tolerancias.
