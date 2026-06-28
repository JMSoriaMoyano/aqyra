# C1 — Contrato IFC / modelo neutro (interoperabilidad)

**Núcleo transversal del ecosistema · PT 1.2 (Ola 1).** Define cómo cualquier disciplina lee y
escribe **IFC** y trabaja sobre un **modelo neutro** común, para reutilizar solver, verificación
y entregables sin reescribir la fontanería. Estado a 22/06/2026.

> Principio: el IFC es el **soporte de intercambio**; el cálculo opera sobre el **modelo neutro**
> (JSON serializable). Un parser por dominio IFC traduce IFC → neutro; el resto del motor no
> conoce IFC.

---

## 1. Vías de entrada IFC (ya implementadas en estructuras)

1. **IFC del dominio de análisis estructural (ortodoxo)** — entidades `IfcStructural*`
   (`IfcStructuralCurveMember`, `IfcStructuralSurfaceMember`, `IfcStructuralPointConnection`,
   `IfcStructuralLinearAction`/`...LoadGroup`, `IfcBoundaryNodeCondition`). Prioridad a las
   entidades estándar; Psets propios `Pset_Estructurando_*` como respaldo. Parser:
   `ifc_to_model.py` (1D) / `ifc_to_model_3d.py` (1D+2D).
2. **IFC físico (BIM real) → analítico** — `IfcBeam`/`IfcColumn`/`IfcWall`/`IfcSlab`/`IfcFooting`/
   `IfcPile` con **geometría** y `IfcMaterial(ProfileSet/LayerSet)`, **sin** entidades de análisis
   ni cargas. Módulo `puente.py`/`puente_analitico/` deriva ejes, secciones, nodos por
   intersección con tolerancia, apoyos e hipótesis de carga. Serie R (R1–R5) cierra esta vía.

Toda disciplina nueva elige su vía (normalmente la **física**, que es la del entregable BIM real)
y produce el **mismo modelo neutro**.

---

## 2. Esquema del modelo neutro (estructuras) — estado actual

Tal como lo emiten los parsers existentes (dict JSON):

```jsonc
{
  "unidades":   { "longitud": "m", "fuerza": "N", "momento": "N*m" },
  "materiales": { "S275JR": { "E":, "G":, "nu":, "rho":, "fy":, "fck":, "fctm": } },
  "secciones":  { "IPE 330": { "A":, "Iy":, "Iz":, "J":, "Wply":, "Wely":, "h":, "Avz":, "clase": } },
  "nodos":      { "N1": { "x":, "y":, "z":, "apoyo": [DX,DY,DZ,RX,RY,RZ] } },
  "barras":     { "B1": { "ni":"N1", "nj":"N2", "seccion":"IPE 330", "material":"S275JR", "tipo": } },
  "superficies":[ { "esquinas":[...], "espesor":, "malla":, "material":, "cargas":[...] } ],
  "cargas":     [ { "caso":, "barra":, "direccion":"GZ", "qz": } ]
}
```

Convenciones invariables:
- **Unidades SI** declaradas en el bloque `unidades` (N, m; el AN trabaja en kN, kN·m, MPa, mm
  en las salidas). Un `factor de unidades` se lee del `IfcUnitAssignment` (R5).
- **Apoyos** como vector booleano de 6 GdL `[DX,DY,DZ,RX,RY,RZ]` (True = coacción).
- **Topología** por nombres de nodo; respaldo por geometría (`IfcEdge`/`IfcVertexPoint`).
- **Perfiles**: prioridad a **catálogo** (`perfiles_db`) sobre cálculo geométrico (lección
  21/06: el geométrico subestima A≈4–5 %, I≈5 %).
- **Cargas — dos colocaciones según dimensión** (el esquema de arriba las muestra juntas, pero
  cada parser usa una): el parser **1D** (`barras/ifc_to_model.py`) emite `cargas` como **lista a
  nivel raíz** (`{caso, barra, direccion, qz}`); el parser **2D** (`laminas/ifc_to_model_3d.py`)
  anida las cargas de superficie **dentro de cada elemento**, en `superficies[].cargas`. Un consumidor
  debe contemplar ambas. (Confirmado: caso 1 trae `cargas` raíz; caso 10, cargas en `superficies`.)

---

## 3. Extensión a otras tipologías estructurales

El esquema ya soporta barras (1D) y superficies (2D). Las nuevas tipologías **extienden** el
modelo neutro sin romperlo:

| Tipología | Añade al modelo neutro |
|---|---|
| Pantallas/núcleos + sísmico (EC8) | masas sísmicas, espectro, casos modales, derivas |
| Pretensado (EC2 §5.10) | tendones (trazado, fuerza, pérdidas) como cargas equivalentes |
| Puentes | fases constructivas, ejes/alineación, cargas IAP, fatiga |

Regla: **añadir claves nuevas, nunca cambiar la semántica de las existentes** (retrocompatible,
como `puente.py` endurecido en R5).

---

## 3bis. Utilidades del núcleo como API compartida (PT 4.1, Ola 4 — hueco H1)

Las utilidades de lectura IFC y el **grafo de red nodos+tramos** que estaban embebidos en el lado
de estructuras (`puente_analitico/puente.py`) y **duplicados** en los parsers se han extraído a un
**módulo de núcleo agnóstico al solver**, con API estable, para que cualquier disciplina los reutilice
**sin tocar el núcleo**. Es **canónico** en `scripts/nucleo/` del plugin del motor y se **espeja byte a
byte** a cada plugin que lo consume (`iso19650-openbim` en PT 4.2; `instalaciones` en PT 4.3). El
aislamiento de runtime impide importarlo entre plugins, por lo que el **espejo es la vía** (no un módulo
único importable); su integridad la vela la puerta `Nucleo-transversal/verificar_espejo_nucleo.py`
(hash; FALLA si un espejo diverge). Esto **resuelve la decisión abierta nº4 y cierra INC-10**.

**`ifc_utils.py` — lectura IFC común:**
- `psets(element)` → `{Pset: {Prop: valor}}` (antes duplicado en `puente.py`, `barras/ifc_to_model.py`,
  `laminas/ifc_to_model_3d.py`, etc.; ya centralizado en los tres principales).
- `length_scale(ifc)` → factor de unidad de longitud del `IfcUnitAssignment` a metros (mm→m, pulgada/pie).
- `pset_value(ifc, pset, prop, defecto)` → lector puntual de una propiedad (el Pset es parámetro).
- `matmul`/`apply`/`to_list4`/`ident4` → álgebra homogénea 4×4.

**`grafo_red.py` — grafo de red (origen: el grafo de nudos endurecido en R5):**
- Primitivas: `RegistroNodos` (fusión por tolerancia/snap), `proyeccion`, `punto_en_segmento`,
  `bbox_xy`, `cortes_por_interseccion` (troceo T/X con offset), `ordenar_segmento`,
  `filtrar_componentes_desconectadas` (union-find **genérico** vía predicado `es_ancla`).
- Alto nivel: `construir_grafo(segmentos, tol)` → `{nodos, tramos, métricas}` a partir de segmentos
  genéricos `(p0, p1, payload)`. **Devuelve topología, no calcula.**

> Garantía de no-regresión: `puente.py` quedó como **adaptador fino** que delega en el núcleo;
> R1–R5 reproducen su `modelo_neutro.json` de v0.22.1 **byte a byte** y los casos 1/5/7/10 cumplen.

> **Modelos hermanos por tipo de análisis.** Un análisis con topología distinta puede emitir un
> **modelo neutro propio** (no un superconjunto del gravitatorio) producido por su propio parser,
> siempre que **reutilice las convenciones** (bloque `unidades` SI, nomenclatura) y no redefina la
> semántica de las claves comunes. Ejemplo: el modelo **sísmico** del caso 15 (`solver_nucleo.py`)
> emite `pantallas[]`, `diafragma`, `dinteles`, `ec8`, `nucleo`, `masas` y **no** lleva
> `barras/nodos/superficies` (no los necesita). Salvedad a reconciliar: usa `material` (singular,
> un material de núcleo) en vez de `materiales` (dict) del esquema base — admitir ambos en los
> consumidores o unificar a `materiales` en una próxima revisión.

---

## 4. Extensión al dominio MEP (instalaciones) — plan

Las instalaciones **no** usan el dominio de análisis estructural sino el **dominio MEP** de IFC.
Es el trabajo nuevo de C1 que habilita la **Ola 4** (instalaciones completas: PCI + eléctricas +
climáticas), según la re-secuenciación v2.1 de la hoja de ruta (la Ola 3 es edificación singular).

**Entidades IFC MEP de referencia:**
- Sistemas: `IfcSystem` / `IfcDistributionSystem` (con `PredefinedType`: FIRESUPPRESSION,
  ELECTRICAL, AIRCONDITIONING, etc.).
- Elementos: `IfcDistributionElement` → `IfcFlowSegment` (tubo/conducto/cable bandeja),
  `IfcFlowFitting` (codo/te), `IfcFlowTerminal` (BIE, rociador, difusor, luminaria, enchufe),
  `IfcFlowController`, `IfcFlowMovingDevice` (bomba/ventilador), `IfcEnergyConversionDevice`.
- Conectividad: `IfcDistributionPort` + `IfcRelConnectsPorts` → **grafo de red** (análogo al
  grafo de nudos estructural, reutilizable conceptualmente).
- Propiedades: Psets estándar `Pset_*` (p. ej. `Pset_PipeSegmentTypeCommon`) y cantidades `Qto_*`.

**Modelo neutro MEP (propuesta, mismo patrón que el estructural):**

```jsonc
{
  "unidades":  { "longitud":"m", "caudal":"l/s", "presion":"kPa", "potencia":"W" },
  "sistema":   { "tipo":"FIRESUPPRESSION", "fluido":"agua" },
  "nodos":     { "ND1": { "x":, "y":, "z":, "tipo":"terminal|union|fuente" } },
  "tramos":    { "T1": { "ni":, "nj":, "dn":, "material":, "rugosidad":, "longitud": } },
  "terminales":[ { "id":"BIE-1", "tipo":"BIE25", "caudal_min":, "presion_min": } ],
  "fuentes":   [ { "id":"grupo", "presion":, "caudal": } ]
}
```

- **Grafo de red** (nodos+tramos) reutiliza la lógica de **construcción de grafo por puertos/
  intersección** ya madura en el lado estructural, **ya extraída al núcleo** (`scripts/nucleo/
  grafo_red.py`, PT 4.1): `construir_grafo(segmentos, tol)` se alimenta desde
  `IfcDistributionPort`/`IfcRelConnectsPorts` con `es_ancla` = nudo fuente.
- **Cálculo MEP** ≠ FEM: dimensionado **hidráulico** (pérdida de carga Darcy-Weisbach/Hazen-
  Williams), **eléctrico** (caída de tensión, intensidades), **térmico** (cargas, caudales de
  aire). Cada disciplina aporta su solver de red; el núcleo aporta el grafo, las unidades y la
  E/S IFC. **Implementado (PT 4.3):** el **solver hidráulico a presión** (Darcy-Weisbach) vive en
  el plugin `instalaciones` (`scripts/red/solver_red.py`), consumiendo este modelo neutro; la clave
  `demanda` (H3) la rellena `instalaciones/scripts/pci/bases_demanda.py` (frontera C1 lectura ↔ CN-3
  demanda ↔ cálculo de la disciplina).

**Tareas de la extensión MEP (Ola 4) — ✅ IMPLEMENTADO (PT 4.2, hueco H2; plugin
`iso19650-openbim` v0.4.0):**
1. ✅ Parser `ifc_to_model_mep.py` (físico→neutro de red) reutilizando el **núcleo**
   (`ifc_utils.psets`/`length_scale`/`pset_value` y `grafo_red.construir_grafo`), **sin tocarlo**. El
   núcleo (H1) ya estaba extraído; esta tarea era H2. Lee `IfcDistributionSystem` +
   `IfcFlowSegment/Fitting/Terminal/Controller/MovingDevice` + `IfcDistributionPort`/
   `IfcRelConnectsPorts` (respaldo geométrico) y emite el modelo neutro de red de abajo. Vive en
   `iso19650-openbim/scripts/mep/` (la capa IFC transversal), con el núcleo **espejado** en
   `iso19650-openbim/scripts/nucleo/` (avance de la decisión nº4: el canónico sigue en el motor).
2. ✅ Generador de IFC MEP de prueba `generate_test_ifc_mep.py` (red PCI: fuente → 4 tramos → 3 BIE).
3. ✅ Validación de red `validacion_red.py` (continuidad conexa desde fuente, terminales conectados,
   sin componentes huérfanas vía `grafo_red.filtrar_componentes_desconectadas` con `es_ancla`=fuente,
   unidades SI) — análoga al arnés de equilibrio. Micro-test `test_red_mep.py` + caso e2e
   `Casos-de-uso/caso-MEP-01-red-pci` (CUMPLE, cobertura 100 %). **Sin cálculo hidráulico** (el solver
   Darcy/Manning lo aporta después la disciplina `instalaciones`).

> **Gancho H3 dejado listo (no implementado aquí):** el modelo neutro de red deja la clave `demanda`
> prevista por **terminal** y por **sistema**, para recibir más adelante caudales/potencias/ocupación
> (bases de demanda = hueco H3). El parser **no** calcula demandas.

> **Esquema vs implementación (nota de esquema):** en **IFC4** el sistema PCI usa
> `PredefinedType=FIREPROTECTION`; en **IFC4X3** el término es `FIRESUPPRESSION`. El parser es
> **agnóstico al esquema** (emite el string tal cual). El banco de pruebas debe declarar la unidad de
> longitud SI explícita (`unit.add_si_unit` LENGTHUNIT sin prefijo): `unit.assign_unit` por defecto
> pone milímetros, que el parser respetaría literalmente (lección del caso MEP-01).

### 4ter. Extensión a saneamiento — lámina libre por gravedad (PT 6.2, Ola 6)

El **mismo modelo neutro de red** del §4 sirve para las **obras hidráulicas de saneamiento**
(colectores en **lámina libre**), con dos particularidades propias del flujo por gravedad. El
parser sigue siendo **agnóstico al sistema** (`iso19650-openbim` v0.6.0); el **cálculo** (solver
de Manning de red) vive en `obras-lineales`, que consume el JSON neutro (frontera C1 ↔ cálculo).

- **Sistemas:** `IfcDistributionSystem` PredefinedType **SEWAGE / STORMWATER / DRAINAGE /
  WASTEWATER** (el parser emite el string tal cual). Colectores `IfcFlowSegment`; pozos de
  registro `IfcDistributionChamberElement`/`IfcFlowFitting` (nudos de unión).
- **Fuente invertida → vertido (outfall):** en saneamiento el **ancla de la red es el VERTIDO**,
  no una fuente de presión. El parser reconoce el outfall (`IfcFlowTerminal` PredefinedType
  **OUTLET**, o por nombre) y lo emite en una clave **nueva `vertidos[]`** =
  `[{id, nodo, tipo:"vertido"}]`, marcando su nodo con `tipo:"vertido"`. El solver orienta el
  árbol **desde el vertido** (`grafo_red` con `es_ancla`=outfall) y reparte el caudal por
  continuidad **aguas arriba**. La validación de red admite anclar en **fuentes** (presión) o en
  **vertidos** (gravedad).
- **Cotas de solera (dato de red que gobierna la pendiente):** la pendiente del flujo por
  gravedad la fijan las **cotas de solera (invert)** de los nudos. Si están en el Pset/IFC
  (`Pset_Estructurando_Red.CotaSolera` por nudo) **prevalecen**; si no, se toma la **z del nodo
  como solera** `[confirmar AN]`. El parser las emite como `nodos[*].cota_solera`. Los terminales
  de saneamiento llevan `habitantes_eq` (aporte residual, EN 752).
- **Retrocompatibilidad:** son **claves nuevas** (`vertidos`, `cota_solera`, `habitantes_eq`); el
  resto del esquema no cambia. PCI/REBT **sin regresión** (la clave aditiva `vertidos:[]` queda
  vacía). El **write-back** reutiliza el mismo `Pset_Estructurando_ResultadoRed` (por colector:
  DN, caudal, velocidad, calado, llenado, pendiente, régimen, sentido; por vertido: caudal total).

### 4quater. Extensión a abastecimiento — red a presión (PT 6.3, Ola 6 · cierre)

El **mismo modelo neutro de red** del §4 sirve para las **obras hidráulicas de abastecimiento**
(distribución de agua **a presión**), gemelo a presión del saneamiento (§4ter). El parser sigue
siendo **agnóstico al sistema** (`iso19650-openbim` v0.7.0); el **cálculo** (solver Darcy-Weisbach
de red) vive en `obras-lineales` y es **copia byte a byte** del de `instalaciones` (motor de red de
la Ola 4; decisión nº7 "grafo + N solvers").

- **Sistemas:** `IfcDistributionSystem` PredefinedType **WATERSUPPLY / DOMESTICCOLDWATER /
  POTABLEWATER** (el parser emite el string tal cual). Tuberías `IfcFlowSegment`; nudos de unión
  `IfcFlowFitting`.
- **Fuente = ancla de presión (al revés que el VERTIDO del saneamiento):** el ancla de la red es la
  **FUENTE**. El parser la reconoce en `fuentes[]` (`tipo:"deposito"|"equipo"|"controlador"`):
  - **Depósito** (`IfcTank`/`IfcFlowStorageDevice`, reconocido por **jerarquía `is_a()`**) → fuente
    **por cota**: lámina de agua libre → la demanda inyecta `presion=0` y la **carga estática** nace
    de la propagación por cota del solver (`ρ·g·Δz`). El parser lee `cota_lamina` del Pset si está.
  - **Grupo de bombeo** (`IfcFlowMovingDevice`, ya soportado) → presión declarada.
  - La **presión de la fuente** (`fuentes[*].presion`) del Pset **prevalece**; si no, la inyecta la
    demanda (CN-3) según el tipo de fuente. El validador ya ancla en `fuentes` (sin cambios).
- **Demanda (CN-3, EN 805):** caudal punta = dotación·hab-eq·coef. de punta (el parser lee
  `habitantes_eq` también para abastecimiento) + **hipótesis de incendio** (caudal de hidrante
  concurrente). Vive en `obras-lineales/scripts/red/bases_abastecimiento.py`.
- **Retrocompatibilidad:** son **claves ya existentes** (`fuentes`, `red`); el resto del esquema no
  cambia. PCI/REBT/saneamiento **sin regresión** (el depósito solo se reconoce como fuente nueva; el
  parser para SEWAGE/FIREPROTECTION/ELECTRICAL es idéntico). El **write-back** reutiliza el mismo
  `Pset_Estructurando_ResultadoRed` (por tramo: DN, caudal, velocidad, pérdida, sentido; por
  terminal: presión disponible/mín/margen/cumple).

> **Cierre de la Ola 6:** con el abastecimiento, las obras hidráulicas de obra lineal quedan
> completas (saneamiento por gravedad/Manning + abastecimiento a presión/Darcy) y la **Ola 6 queda
> CERRADA**. El siguiente foco del ecosistema es la **Ola 7 (puentes)**.

---

## 4bis. Extensión al dominio de obra lineal (IFC 4.3 + GIS)

Las obras lineales (trazado, firmes, drenaje, obras hidráulicas) son **georreferenciadas** y se
apoyan en **IFC 4.3**. Es el trabajo de C1 que habilita la Ola 5.

**Entidades IFC 4.3 de referencia:**
- **Alineación:** `IfcAlignment` (horizontal: rectas/clotoides/curvas; vertical: rasante y
  acuerdos; peralte/cant) — la "directriz" del proyecto lineal.
- **Espaciales infra:** `IfcRoad`/`IfcRailway` y sus partes (`IfcRoadPart`…), `IfcFacility`.
- **Elementos:** `IfcCourse`/`IfcPavement` (firmes), `IfcEarthworksCut/Fill`, `IfcKerb`,
  obras de drenaje como elementos MEP de saneamiento (ver dominio MEP, §4).
- **Georreferencia:** `IfcMapConversion` + `IfcProjectedCRS` (sistema de coordenadas).

**Modelo neutro lineal (propuesta):** un perfil paramétrico por **PK (punto kilométrico)** sobre
la alineación: `{ alineacion: {planta[], alzado[], peralte[]}, secciones_tipo: {...}, firme:
{categoria_trafico, explanada, paquete[]}, terreno: {...} }`. Interopera con **GIS** (GeoJSON/
Shapefile) para hidrología de cuencas y cartografía.

> El **drenaje** y las **obras hidráulicas** reutilizan el modelo neutro MEP (§4) + el motor
> hidráulico de red; la diferencia es **lámina libre** (Manning) vs **presión**.

**Tareas de la extensión lineal (Ola 5) — ✅ IMPLEMENTADO (PT 5.1; plugin `iso19650-openbim`
v0.5.0):**
1. ✅ Parser `scripts/lineal/ifc_to_model_lineal.py` (físico→neutro lineal) reutilizando el **núcleo**
   (`ifc_utils.length_scale`/`psets`) **sin tocarlo**. Lee `IfcAlignment` → capas
   `IfcAlignmentHorizontal/Vertical/Cant` (`IsNestedBy`) → `IfcAlignmentSegment.DesignParameters`
   (segmentos `LINE`/`CIRCULARARC`/`CLOTHOID`; `CONSTANTGRADIENT`/`PARABOLICARC`; peralte) +
   georreferencia (`IfcMapConversion`/`IfcProjectedCRS`). Reconstruye el perfil por **PK** y emite
   `alineacion{planta[]/alzado[]/peralte[]}` + `georref` + ganchos `secciones_tipo`/`firme`/`terreno`
   (None). **Modelo hermano nuevo, no una red** (referenciación lineal 1D → **no** usa `grafo_red`).
2. ✅ Generador `scripts/lineal/generate_test_ifc_lineal.py` (IFC4X3: eje recta→clotoide→curva→
   clotoide→recta, 2 acuerdos verticales, peralte, georreferenciado EPSG:25830).
3. ✅ Validación `scripts/lineal/validacion_alineacion.py` (PK monótono/contiguo, **continuidad y
   tangencia** por integración de segmentos, continuidad de cotas/pendientes en alzado, georref
   presente, SI; radios/clotoides vs 3.1-IC informativo) + micro-test `test_lineal.py` (positivo + 3
   negativos) + caso e2e `Casos-de-uso/caso-LIN-01-eje-carretera` (CUMPLE). **Sin cálculo de trazado.**
4. ✅ Interoperación **GIS**: `scripts/lineal/export_gis.py` (planta → GeoJSON LineString en CRS
   proyectado). **Decisión nº3 resuelta: GeoJSON + IFC 4.3** (dos soportes complementarios).
5. ✅ `ifc-create`/`ifc-validate` ampliadas a Alignment (`checks-lineal.py`: alineación + georref +
   continuidad; SKILL.md de ambas con el dominio de obra lineal).

> **Dónde vive la georreferencia (decisión PT 5.1):** en el **parser lineal**, no en el núcleo
> (mínima disrupción; `verificar_espejo_nucleo.py` sigue idéntico). Se promoverá a `ifc_utils` solo
> cuando una **segunda** disciplina georreferenciada lo necesite (obligaría a re-espejar en los 3 plugins).

**Estado de la vía Alignment frente al checklist (§6) — PT 5.1, `iso19650-openbim` v0.5.0:**

- [x] **Vía de entrada** definida: **obra lineal IFC 4.3** (`IfcAlignment` + capas + georref).
- [x] El parser `ifc_to_model_lineal.py` produce el **modelo neutro lineal** con `unidades` SI declaradas.
- [x] **Reutiliza el núcleo** (`ifc_utils.length_scale`/`psets`) **sin tocarlo** (espejo idéntico).
- [x] **Extiende** el esquema con claves nuevas (`alineacion`, `georref`, `secciones_tipo`, `firme`,
  `terreno`) sin alterar las existentes (modelo hermano del estructural y del de red).
- [x] **Generador de IFC 4.3 de prueba** + **validación** (PK/continuidad/tangencia/georref) — arnés propio.
- [x] **Escribe/valida** vía `ifc-create`/`ifc-validate` ampliadas a Alignment (`checks-lineal.py`).
  **Write-back de resultados de obra lineal: ✅ (PT 5.2** — la disciplina `obras-lineales` construye
  el mapping `Pset_Estructurando_ResultadoLineal` —trazado: Vp/veredicto; firme: código de sección,
  categoría de tráfico/explanada, espesor— en `scripts/comun/resultado_ifc_lineal.py` y lo vuelca con
  el escritor genérico de `iso19650-openbim`; ver §5bis).

> **Ganchos `secciones_tipo`/`firme`/`terreno` (PT 5.2, plugin `obras-lineales` v0.1.0):** el PT 5.1
> los dejó previstos como `None`; la disciplina de obra lineal los **rellena** sin redefinir las claves
> existentes (modelo hermano retrocompatible): **`firme`** = `{categoria_trafico, explanada,
> codigo_seccion, tipo_firme, paquete[], espesor_total_cm, imdp, ev2}` (selección del catálogo 6.1-IC,
> `scripts/firmes/seleccion_firme.py`) y **`secciones_tipo`** = plataforma básica (calzada/arcenes,
> peralte máx). El trazado (3.1-IC) no toca el modelo: comprueba la `alineacion` frente a la Vp y emite
> veredicto.

> **Gancho `drenaje` (clave NUEVA, PT 6.1, plugin `obras-lineales` v0.2.0):** el drenaje añade una
> **clave nueva retrocompatible** `drenaje` = `{norma:"5.2-IC", metodo_hidrologico, cuencas[], cunetas[],
> odt[]}` (no redefine ninguna existente). La rellena `scripts/drenaje/run_all_drenaje.py` con la
> **hidrología** (método racional modificado 5.2-IC: tc de Témez, IDF, coef. de escorrentía → caudal de
> cálculo por cuenca) y la **capacidad** de cunetas (Manning de sección simple) y ODT (control de
> entrada/salida). **`terreno` sigue en `None`** (corresponde a **geotecnia/movimiento de tierras**, no
> al drenaje): el gancho de drenaje y el de terreno son **independientes**. Cálculo **LOCAL por elemento,
> sin `grafo_red`** (no espeja el núcleo, igual que trazado/firmes); el **motor de red** (colectores en
> lámina libre + abastecimiento a presión, grafo + Manning/Darcy + IFC MEP de saneamiento) es del
> **PT 6.2** (obras hidráulicas), donde **sí** se espejará el núcleo y se extenderá el dominio IFC MEP.
> El write-back añade el resumen de drenaje al `Pset_Estructurando_ResultadoLineal` del `IfcAlignment`.

## 5. Salida IFC (escritura) y validación

- **Escritura**: enriquecer el IFC con resultados (Psets de resultado: aprovechamientos,
  armado, DN dimensionado) y/o generar IFC de análisis. Apoyo en `iso19650-openbim:ifc-create`.
- **Validación**: `iso19650-openbim:ifc-validate` (nomenclatura, Psets, clasificación bsDD,
  Uniclass/GuBIMClass) + arnés propio de equilibrio/continuidad.
- **Visualización**: `visor-ifc`.

### 5bis. Write-back de Psets de resultado de red (PT 4.4, Ola 4)

Cierra el ciclo **IFC → cálculo → IFC** para el dominio MEP. La frontera (decisión PT 4.4,
**opción a**): la **mecánica** de escritura IFC es de la capa transversal (`iso19650-openbim`); la
**semántica** (qué Pset y qué propiedades) la fija la disciplina (`instalaciones`); la **orquestación**
la hace el agente de disciplina (el aislamiento de runtime impide importar entre plugins, así que la
disciplina no llama al escritor por `import` sino invocando la skill).

- **Escritor genérico** (`iso19650-openbim:ifc-create:references/escribir_psets_resultado.py`): lee un
  **mapping JSON** `{ "elementos": { "<Name|GlobalId>": { "<Pset>": { "<Prop>": valor } } } }` y vuelca
  los Psets al IFC con `ifcopenshell.api` (localiza el elemento por **Name** y, si no, por **GlobalId**;
  tipa el valor). Es **agnóstico** a disciplina y esquema.
- **Semántica de red** (`instalaciones:red/resultado_ifc.py`, stdlib): construye el mapping de
  `Pset_Estructurando_ResultadoRed` — por **tramo** (IfcFlowSegment): `DN_dimensionado_mm`, `Caudal_l_s`,
  `Velocidad_m_s`, `Perdida_carga_kPa`, `Sentido_flujo`; por **terminal** (IfcFlowTerminal): `Caudal_l_s`,
  `Presion_disponible_kPa`, `Presion_min_kPa`, `Margen_kPa`, `Cumple`. La clave de cada tramo es su
  `elemento` (Name del IfcFlowSegment del modelo neutro); la de cada terminal, su `id`.
- **Validación**: `iso19650-openbim:ifc-validate` (`checks-mep.py`) **reconoce** el Pset de resultado y
  comprueba que la **continuidad de red** sigue cumpliendo tras el enriquecimiento.

> Estado: ✅ implementado y verificado en `caso-PCI-02-rociadores-malla` (22 elementos enriquecidos,
> continuidad 100 %, APTO). Reutilizable por eléctricas/clima y por obras hidráulicas (Ola 6).

> **Reúso por el vertical eléctrico (PT 4.5).** Las instalaciones **eléctricas (REBT)** consumen el
> **mismo modelo neutro de red** (el parser `ifc_to_model_mep.py` es **agnóstico al tipo de sistema**:
> emite `sistema ELECTRICAL`/`nodos`/`tramos`/`terminales`/`fuentes` igual que en PCI; **no se extendió
> el parser** —la sección/material del conductor nace en la capa de demanda de `instalaciones`, no en C1).
> El **write-back** usa el mismo `Pset_Estructurando_ResultadoRed` con propiedades eléctricas (sección,
> intensidad, caída de tensión, potencia). La **validación** (`checks-mep.py`) pasó a ser **sistema-aware**
> (PT 4.5, `iso19650-openbim` v0.4.2): el Pset de segmento requerido depende de `sistema.tipo`
> (`Pset_PipeSegmentTypeCommon` hidráulico, `Pset_CableSegmentTypeCommon` ELECTRICAL,
> `Pset_DuctSegmentTypeCommon` aire). Verificado en `caso-REBT-01-vivienda` y `caso-REBT-02-terciario`.

---

## 6. Checklist de cumplimiento del contrato C1 (para una disciplina nueva)

- [ ] Define su **vía de entrada** IFC (dominio de análisis / físico / MEP).
- [ ] Su parser produce el **modelo neutro** con `unidades` declaradas y SI.
- [ ] Reutiliza utilidades del núcleo `scripts/nucleo/` (`ifc_utils.psets`/`length_scale`/
  `pset_value`, `grafo_red.construir_grafo`) y `perfiles_db`/DN. **Disponible desde PT 4.1 (v0.23.0).**
- [ ] **Extiende** el esquema con claves nuevas, sin alterar las existentes (retrocompatible).
- [ ] Dispone de **generador de IFC de prueba** y de **validación** (equilibrio/continuidad).
- [ ] Escribe resultados de vuelta vía `ifc-create` y valida con `ifc-validate`.

**Estado de la vía MEP frente al checklist (PT 4.2 — `iso19650-openbim` v0.4.0):**

- [x] **Vía de entrada** definida: **MEP físico** (`IfcDistributionSystem` + `IfcFlow*` + puertos).
- [x] El parser `ifc_to_model_mep.py` produce el **modelo neutro de red** con `unidades` SI declaradas.
- [x] **Reutiliza el núcleo** (`ifc_utils.psets`/`length_scale`/`pset_value`, `grafo_red.construir_grafo`,
  `filtrar_componentes_desconectadas`) **sin tocarlo** (núcleo espejado en el plugin).
- [x] **Extiende** el esquema con claves nuevas (`sistema`, `tramos`, `terminales`, `fuentes`,
  `demanda`) sin alterar las existentes (modelo hermano del estructural).
- [x] **Generador de IFC MEP de prueba** (`generate_test_ifc_mep.py`) y **validación de red**
  (`validacion_red.py`: continuidad/terminales/huérfanas/SI) — análogo al arnés de equilibrio.
- [x] **Escribe/valida** vía `ifc-create`/`ifc-validate` ampliadas a MEP (`checks-mep.py`: nomenclatura,
  Psets `Pset_*`, puertos y continuidad de red). **Psets de resultado de red: ✅ (PT 4.4** — escritor
  genérico `escribir_psets_resultado.py` + semántica en `instalaciones`; ver §5bis).

> Todo resultado es de predimensionado/asistencia y debe ser **revisado y firmado por técnico
> competente**.

---

## §4quinquies. Modelo neutro ESTRUCTURAL de puente (clave aditiva — Ola 7, PT 7.3.1)

`iso19650-openbim` v0.9.0 añade `scripts/estructural/ifc_to_model_estructural.py`: un parser hermano
del lineal y del MEP que produce el **modelo neutro estructural de puente** a partir de un IFC4X3
físico. Es **aditivo y retrocompatible** (no toca `nodos/barras/superficies/unidades`); emite su
propia clave de esquema `"esquema": "estructural_puente"` con:

- `tipologia` (vigas_pretensadas | losa_postesada | portico | celosia | pila | estribo | puente_completo),
- `elementos[]` (cada `IfcElement` clasificado: `rol`, `clase_ifc`, `geom` {pi, pj, L, orient},
  `seccion` {A, Iy, Iz, J, …}, `material`, `psets`),
- `asociaciones[]` (pila↔cimentación, pila↔apoyo por proximidad), `apoyos[]`, `alineacion_ref`
  (reusa el parser de Alignment si hay `IfcAlignment`), y `metricas`.

**Geometría extruida REAL** (decisión PT 7.3.1): dimensiones y A/Iy/Iz/J se leen del
`IfcExtrudedAreaSolid` + perfil (rectángulo/círculo/I exactos; `IfcArbitraryProfileDefWithVoids` para
cajón/artesa, con A/Iy/Iz exactos del polígono y J de pared delgada). Lo **no geométrico** (fck, P0 de
pretensado, rigideces de suelo/apoyo, reacciones, q_adm) viaja en `Pset_Estructurando_*`. **Hallazgos
de esquema:** el dominio de puentes exige **IFC4X3** (`IfcBearing`/`IfcAlignment`/`IfcBridge` no
existen en IFC4) y **`IfcStructuralProfileProperties` se eliminó tras IFC2X3** (por eso las constantes
de sección se derivan de la forma, no de una entidad de perfil estructural). La capa de **idealización**
(modelo neutro estructural → `entrada_caso` por tipología) vive en `puentes` v0.4.0
(`scripts/lectura/desde_ifc.py`), no en C1.

> Todo resultado es de predimensionado/asistencia y debe ser **revisado y firmado por técnico
> competente (ICCP)**.
