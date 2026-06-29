INICIO de hilo — PT 7.4 (Ola 7): **FEM-2** (lámina curva + rigidizadores + secciones de
**pared delgada**) en el motor `motor-fem`, y, sobre esa capacidad, el primer vertical avanzado
de la disciplina `puentes`: el **CAJÓN POSTESADO** (tablero de viga-cajón de hormigón, con
**postesado evolutivo**, **fases constructivas** y efectos diferidos), entregado **IFC-driven** con
su caso de aplicación (PUE-17). Proyecto Estructurando. Ejecuta el **PT 7.4**; reanuda la **escalera
FEM** que el PT 7.3.1 dejó en pausa (era un peldaño de lectura, no de motor).

El PT 7.3.1 ya cerró el **lector estructural IFC→idealización** y los 10 casos IFC-driven
(PUE-07…16): `iso19650-openbim` **v0.9.0** (parser estructural C1) + `puentes` **v0.4.0** (adaptador
`scripts/lectura/desde_ifc.py`; los `run_all_*` aceptan un `.ifc`), con el motor **`motor-fem`
v0.2.1 intacto** (sigue **FEM-1**). Con ello, las **6 tipologías** del grupo lineal + subestructura
se calculan de extremo a extremo **arrancando del IFC**. **El hueco que cierra este PT** es que el
motor aún **no sabe** modelar una sección de **pared delgada con torsión/distorsión/alabeo** ni una
**lámina curva** con **rigidizadores**: es el peldaño **FEM-2**, el que habilita el **cajón** (y, de
paso, las **cubiertas laminares** de la Ola 3).

> Todo cálculo y entregable es de **predimensionado/asistencia y debe ser revisado y firmado por
> técnico competente** (Ingeniero de Caminos, Canales y Puertos). Los NDP se marcan `[confirmar AN]`.

---

## Objetivo del hilo (dos entregables encadenados)

1. **Motor `motor-fem` → FEM-2 (capacidad transversal, contrato C5):** añadir, como **módulos
   aditivos** (sin tocar `fem_core`/elementos FEM-0/1, para que la no-regresión sea por
   construcción, igual que FEM-1):
   - **Lámina curva isoparamétrica** (cuadrilátero curvo; membrana + flexión) — para almas y losas
     alabeadas del cajón y para las cubiertas laminares.
   - **Rigidizador** = **barra excéntrica acoplada** a la lámina (offset rígido), para diafragmas,
     almas rigidizadas y la conexión losa-alma.
   - **Sección de pared delgada**: torsión de **Saint-Venant** (J de Bredt para celda cerrada),
     **alabeo/distorsión** (modo de distorsión del cajón) y ***shear lag*** (ancho eficaz de las
     alas). Decidir si se resuelve por **idealización de lámina** (el cajón mallado capta torsión y
     *shear lag* directamente) o por **viga-cajón enriquecida** (barra con GdL de alabeo) — ver
     decisiones.
2. **Disciplina `puentes` → vertical CAJÓN POSTESADO** (nuevo subagente `proyectista-cajon`):
   idealización del cajón (barra+lámina o lámina pura), **postesado evolutivo** + **fases
   constructivas** (voladizos sucesivos / cimbra / dovelas) + **diferidos** (fluencia/retracción,
   redistribución), acciones **IAP-11**, comprobación **EC2** (tensiones por fase, descompresión,
   flexión/cortante/torsión combinados, *shear lag*), **memoria + write-back**. Entregado
   **IFC-driven**: extender el **lector** (parser C1 + adaptador) a la tipología `cajon`, y un
   **caso PUE-17** (cajón postesado de N vanos, IFC4X3 → lector → idealización → FEM-2 → EC2 →
   memoria + write-back).

---

## Contexto — estado de la Ola 7 (para situar el hilo)

- **PT 7.0 ✅** `motor-fem` v0.1.0 (FEM-0: barra EB + lámina DKMQ, *strangler* vs PyNite).
  **PT 7.1 ✅** `puentes` v0.1.0 + **FEM-1** (modal + cargas móviles/líneas de influencia).
  **PT 7.2 ✅** `puentes` v0.2.0 (losa postesada DKMQ, pórtico, celosía) + `motor-fem` v0.2.1.
  **PT 7.3 ✅** `puentes` v0.3.0 (pila + apoyo + cimentación, estribo) — motor sin tocar.
  **PT 7.3.1 ✅** lector estructural IFC + 10 casos: `iso19650` v0.9.0 + `puentes` v0.4.0.
- **Escalera FEM:** FEM-0 ✅ · FEM-1 ✅ · **FEM-2 🔜 (este PT)** · FEM-3 (arco/pandeo) · FEM-4
  (cable/membrana, atirantado) · FEM-5 (dinámica avanzada, horizonte).
- El **oráculo PyNite** es **EB en barras** y **DKMQ en placas** (no Timoshenko/MITC4): la
  no-regresión de FEM-0/1 se valida contra él. **FEM-2 no tiene oráculo en PyNite** (no hay lámina
  curva ni pared delgada) → se valida con **benchmarks NAFEMS** y **teoría de viga-cajón** (ver
  plan de validación).

---

## Lo que YA existe y se reutiliza (clave para acotar el alcance)

- **`motor-fem` v0.2.1** (`scripts/`): `fem_core.py` (ensamblaje disperso COO + estático lineal +
  resortes), `elementos/barra.py` (EB + conmutador Timoshenko), `elementos/` lámina **DKMQ**,
  `mallador.py` (`desde_modelo_neutro`, `desde_pynite` espejo), `fem1.py` (modal + móvil,
  **aditivo**). **FEM-2 imita este patrón aditivo:** nuevos `elementos/lamina_curva.py`,
  `elementos/rigidizador.py` y `fem2.py` (pared delgada / ensamblaje con offset), **sin tocar**
  `fem_core` ni los elementos existentes. Contrato **C5** (`C5_Contrato-motor-FEM.md`): el modelo de
  análisis admite `tipo: barra|lamina|lamina_curva|rigidizador|cable|membrana` (la clave ya está
  prevista) + `laminados`/offsets.
- **`puentes` v0.4.0**: `idealizacion/losa_lamina.py` (malla DKMQ — patrón para mallar el cajón por
  láminas), `pretensado/inyeccion_pretensado.py` + `comprobacion/ec2_*` (tensiones, descompresión),
  `acciones/iap11.py`, `comun/resultado_ifc_puente.py` (write-back), `scripts/lectura/desde_ifc.py`
  (adaptador por tipología — **se extiende** con `cajon`).
- **Lector estructural (PT 7.3.1)** `iso19650` v0.9.0 `scripts/estructural/ifc_to_model_estructural.py`:
  ya lee **geometría extruida real** incluido **`IfcArbitraryProfileDefWithVoids`** (cajón con
  huecos → A/Iy/Iz exactos del polígono + J de pared delgada por Bredt). **El cajón ya se lee**; lo
  nuevo es **mallarlo por láminas** y resolver pared delgada en el FEM.
- **`motor-calculo`**: `pretensado/balance_2d.py`, `pretensado/ec2_pretensado.py` (tensiones de
  fibra, §5.10) — reutilizables por fórmula (recordar el **stub de PyNite** o copia byte-fiel para
  los módulos que lo importan a nivel de módulo).

> **Hueco real a construir:** los **elementos FEM-2** (lámina curva + rigidizador + pared delgada) y
> el **vertical cajón** (idealización por láminas + postesado evolutivo/fases/diferidos + EC2 con
> torsión/distorsión/*shear lag*). El lector, el postesado, las acciones IAP-11 y el write-back **ya
> existen** y solo se extienden a la tipología `cajon`.

---

## Frontera (contratos del núcleo) — respétala

- **C5 (`motor-fem`):** **crece** con los elementos FEM-2 (aditivos). Es su sitio natural. No conoce
  normativa ni tipologías.
- **C1 (`iso19650-openbim`):** el parser estructural **clasifica** el cajón (ya lee la sección con
  huecos); a lo sumo añade metadatos de tipología `cajon` (clave aditiva). Lectura/escritura IFC.
- **`puentes`:** crece con el **vertical cajón** (idealización + EC2 + fases) y la **extensión del
  adaptador** `desde_ifc` a `cajon`. Reusa idealización de lámina, pretensado, IAP-11 y write-back.
- **`motor-calculo`:** no se migra; se **reutilizan** sus fórmulas de pretensado/EC2 por PYTHONPATH.

---

## Decisiones a resolver y documentar (antes de mover una línea)

- **Idealización del cajón: ¿lámina pura o viga-cajón enriquecida?** Recomendado: **lámina pura**
  (mallar tableros/almas con lámina curva + rigidizadores) — capta torsión, distorsión y *shear lag*
  por geometría, coherente con FEM-2 y reutilizable por la Ola 3; la viga-cajón con GdL de alabeo
  queda como alternativa ligera. `[confirmar AN]`
- **Lámina curva: formulación.** Cuadrilátero isoparamétrico de 4 nodos con membrana (*drilling*) +
  flexión (Mindlin/MITC4) vs DKMQ curvo. Recomendado: **MITC4 con corrección de bloqueo por cortante**
  (estándar NAFEMS) y *drilling* a 1/1000 (coherente con DKMQ de FEM-0). `[confirmar AN]`
- **Rigidizador: acoplamiento.** Barra excéntrica con **offset rígido** (transformación de GdL del
  nodo de la barra al plano medio de la lámina) vs nodos coincidentes con *link* rígido. Recomendado:
  **offset rígido** (matriz de transformación), sin nodos extra. `[confirmar AN]`
- **Pared delgada / torsión:** ¿J de Bredt + modo de distorsión analítico, o que la malla de lámina
  lo capte íntegro? Recomendado: **la malla lo capta** (torsión y *shear lag* directos); reportar el
  *shear lag* como **ancho eficaz** comparado con la teoría. `[confirmar AN]`
- **Fases constructivas y diferidos:** ¿voladizos sucesivos (dovelas) con tesado evolutivo + estado
  de cargas permanentes por fase, o un único estado en servicio con pérdidas diferidas? Recomendado:
  **fases simplificadas** (construcción vs servicio) + diferidos por coeficientes EC2 (fluencia φ,
  retracción), dejando el tesado dovela-a-dovela como gancho. `[confirmar AN]`
- **Validación de FEM-2 sin oráculo PyNite:** **benchmarks NAFEMS** (lámina curva: *Scordelis-Lo
  roof*, *pinched cylinder*, *hemispherical shell*) + **placa rigidizada** + **cajón vs teoría de
  viga-cajón** (torsión de Bredt, *shear lag* por ancho eficaz). Tolerancias: NAFEMS dentro del
  **±2–5 %** de la referencia publicada `[confirmar AN]`; no-regresión FEM-0/1 **exacta** (los
  elementos nuevos no alteran los existentes).

---

## El caso de aplicación (PUE-17), IFC-driven

`caso-PUE-17-cajon-postesado`: **generar IFC4X3** del cajón (sección de viga-cajón por
`IfcArbitraryProfileDefWithVoids`, eje por **Alignment**, N vanos) → **lector** (ya lo lee; clasificar
tipología `cajon`) → **idealización por láminas + rigidizadores** → **postesado evolutivo + fases** →
`motor-fem` **FEM-2** (estático + envolventes LM1 + modal) → **EC2** (tensiones por fase,
descompresión, flexión/cortante/**torsión** combinados, *shear lag*) → **memoria + write-back al IFC**.
Carpeta con el conjunto estándar IFC-driven (ver `Casos-de-uso/INDICE-PUE.md` y la plantilla
`caso-PUE-05-pila-cimentacion/README-IFC-driven.md`), y fila nueva en `INDICE-PUE.md`. Opcional: un
**benchmark de cubierta laminar** (Scordelis-Lo) como semilla de la **Ola 3** (spin-off de FEM-2).

---

## Lee primero, en este orden

1. `Hoja-de-ruta_Ola7-puentes-y-motor-FEM.md` — **§2 (escalera FEM, FEM-2)**, **§4 (tipologías:
   cajón)**, la **tabla de PTs (7.4)**, **§7 (conexión Ola 3)** y el **registro v1.5** (cierre
   PT 7.3.1).
2. `Nucleo-transversal/C5_Contrato-motor-FEM.md` — el modelo de análisis FEM y cómo **añadir
   elementos** (lámina curva / rigidizador) y GdL sin romper FEM-0/1.
3. **`motor-fem` v0.2.1** (`scripts/`): `fem_core.py`, `elementos/` (barra + DKMQ), `mallador.py`,
   `fem1.py` (patrón de **módulo aditivo**) y `scripts/validacion/` (cómo se validan los peldaños).
4. **`puentes` v0.4.0** (`scripts/`): `idealizacion/losa_lamina.py` (mallado DKMQ),
   `pretensado/inyeccion_pretensado.py`, `comprobacion/ec2_losa.py`/`ec2_tablero.py`,
   `acciones/iap11.py`, `comun/resultado_ifc_puente.py`, **`scripts/lectura/desde_ifc.py`**
   (adaptador a extender) y `run_all_*` (flujo a imitar para `run_all_cajon`).
5. **`iso19650-openbim` v0.9.0**: `scripts/estructural/ifc_to_model_estructural.py` (lee la sección
   de cajón con huecos) y `scripts/lineal/ifc_to_model_lineal.py` (eje por Alignment).
6. `criterios-despacho.md` — lecciones PT 7.0–7.3.1 (oráculo EB/DKMQ, módulo aditivo de FEM-1,
   geometría extruida real, IFC4X3, stub de PyNite, hazard de mount).

---

## Entregable

- **`motor-fem` vX.Y (.plugin)**: FEM-2 — `elementos/lamina_curva.py` + `elementos/rigidizador.py` +
  `fem2.py` (pared delgada / offset), **aditivos**; `fem_core` y elementos FEM-0/1 **sin tocar**.
  Benchmarks NAFEMS + cajón vs viga-cajón en `scripts/validacion/`. Núcleo espejado intacto.
- **`puentes` v0.5.0 (.plugin)**: vertical **cajón** (`idealizacion/cajon.py`,
  `comprobacion/ec2_cajon.py`, `run_all_cajon.py`), subagente `proyectista-cajon`, extensión de
  `desde_ifc.py` a la tipología `cajon`. Idealización de lámina/pretensado/IAP-11/write-back reusados.
- **`iso19650-openbim` vX.Y (.plugin)** si procede (metadatos de tipología `cajon`; clave aditiva).
- **`caso-PUE-17-cajon-postesado`** documentado (IFC + lectura + FEM-2 + EC2 + memoria + write-back)
  + fila en `Casos-de-uso/INDICE-PUE.md`. Opcional: benchmark Scordelis-Lo (semilla Ola 3).
- **Actualizar**: hoja de ruta Ola 7 (PT 7.4 ✅ → PT 7.5 🔜), C5 (elementos nuevos),
  `criterios-despacho.md` (lección FEM-2) y la memoria del proyecto.
- **Puertas de calidad obligatorias** (pega su salida en el cierre):
  `TMPDIR=/tmp HOME=/tmp PYTHONPATH=/tmp/pylibs python3 Nucleo-transversal/verificar_empaquetado.py <plugin>.plugin --ref <previo>.plugin`
  (**APTO**, `description` ≤500) para `motor-fem` vX.Y, `puentes` v0.5.0 e `iso19650` vX.Y, **y**
  `verificar_espejo_nucleo.py --canonico <motor-calculo>.plugin <plugin>.plugin` (**ESPEJOS
  IDÉNTICOS**), **y** los **benchmarks NAFEMS** (lámina curva dentro de tolerancia) + la
  **no-regresión exacta de FEM-0/1** + el **caso PUE-17 e2e**.

---

## Notas de método (críticas, confirmadas en PT 4.x–7.3.1)

- **Entorno / ifcopenshell:** `/tmp/pylibs` puede quedar **read-only** de una sesión previa →
  instala `ifcopenshell` en target limpio `pip install --no-cache-dir --target=/tmp/ifclib ifcopenshell`
  (v0.8.5; trae numpy/shapely/lark) y ejecuta con `PYTHONPATH=/tmp/ifclib:/tmp/pylibs`. numpy/scipy en
  `/tmp/pylibs`. Exporta siempre **`TMPDIR=/tmp HOME=/tmp PIP_NO_CACHE_DIR=1 MPLCONFIGDIR=/tmp/mplcache`**.
- **Hazard de mount:** los ficheros **editados con Edit** se leen **truncados** desde el shell; los
  creados con **Write** se leen íntegros. **Desarrolla y testea en `/tmp`**; **reconstruye el
  `.plugin` y los verificadores en `/tmp`** desde el contenido íntegro; `cp /tmp→workspace` escribe
  bytes correctos (verifícalo por tamaño exacto). `plugin.json` vive en `.claude-plugin/` (carpeta
  oculta: `glob('**')` la salta; usa ruta explícita). Excluye `__pycache__`/`*.pyc` al empaquetar.
- **Disco `/sessions`** puede estar al **100 %**: que las extracciones caigan en `/tmp` (`TMPDIR=/tmp`).
- **PyNite no está en el sandbox**: `motor-calculo` lo importa a nivel de módulo en varios solvers →
  para reutilizar sus **fórmulas/parsers** basta un **stub de `Pynite`** (`class FEModel3D: raise`)
  en el PYTHONPATH, o copia byte-fiel de la parte usada. **FEM-2 no tiene oráculo PyNite** → validar
  con **NAFEMS** y teoría de viga-cajón, no contra PyNite.
- **IFC de puentes = IFC4X3 SIEMPRE** (`IfcBearing`/`IfcAlignment`/`IfcBridge` no existen en IFC4;
  `IfcStructuralProfileProperties` se eliminó tras IFC2X3). El cajón se modela con
  `IfcArbitraryProfileDefWithVoids`; el lector ya extrae A/Iy/Iz exactos + J de pared delgada.
- **Reutiliza, no reescribas:** elementos/ensamblaje de `motor-fem` (no toques FEM-0/1), lector
  C1 + adaptador `desde_ifc`, idealización de lámina + pretensado + IAP-11 + write-back de `puentes`.
  La regla de oro: *"¿qué es realmente nuevo (lámina curva + rigidizador + pared delgada en el motor;
  idealización del cajón + fases + EC2 con torsión en la disciplina) y qué ya está?"* — solo se
  construye lo primero.
- Todo es **predimensionado, a revisar y firmar por técnico competente** (ICCP); NDP `[confirmar AN]`.

**Empieza** leyendo los documentos (hoja de ruta §2/§4 + tabla 7.4 + §7 + registro v1.5, **C5**, el
motor `motor-fem` v0.2.1 —patrón de módulo aditivo y validación—, el plugin `puentes` v0.4.0
—idealización de lámina, pretensado, EC2, adaptador `desde_ifc`— y el lector de `iso19650` v0.9.0
—lectura del cajón con huecos—), y **proponiendo, antes de mover una línea: (a)** la **arquitectura de
FEM-2** (lámina curva + rigidizador + pared delgada como módulos aditivos sobre C5) y su esquema en el
modelo de análisis; **(b)** la **idealización del cajón** (lámina pura vs viga-cajón enriquecida; cómo
se mallan tableros/almas/diafragmas y se inyecta el postesado evolutivo por fases); **(c)** el **plan
de validación** (benchmarks NAFEMS + cajón vs teoría de viga-cajón + no-regresión exacta de FEM-0/1) y
el **caso PUE-17** con tolerancias.
