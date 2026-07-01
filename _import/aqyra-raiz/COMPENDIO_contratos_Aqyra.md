---
title: "Compendio de contratos — Aqyra"
subtitle: "Copia de los contratos del ecosistema · registro único · 2026-06-27"
---

# Portada y registro único

**Ecosistema Aqyra (AEC · OpenBIM).** Este documento reúne una **copia de los contratos** vigentes, tal como quedaron tras la reconciliación de numeración firmada por JM el **2026-06-27**.

Dos familias:

- **Interfaces C1–C8** — el "enchufe" entre dos piezas (qué entra, qué sale, con qué significado).
- **Convenciones de núcleo CN-*** — convenciones transversales que **no** son interfaces entre piezas.

| Nº | Contrato | Estado | En este compendio |
|---|---|---|---|
| C1 | Parser / IFC / modelo neutro | Firmado | ✔ incluido |
| C2 | Datos (crudo ↔ aprendido) | Borrador | ✔ incluido |
| C3 | *Reservado (libre)* | — | (sin documento) |
| C4 | Red (interfaz del grafo de red) | Pendiente de redactar | (sin documento aún) |
| C5 | Motor-fem (interfaz) | Firmado | ✔ incluido |
| C6 | Corpus golden / recuperación | Propuesto | (es la carpeta `golden/`, no un .md) |
| C7 | Operador IA | Borrador | ✔ incluido |
| C8 | Intercambio CDE | Borrador | ✔ incluido |
| CN-1 | Memoria del despacho | Vigente | ✔ incluido |
| CN-2 | Entregables / documentación | Vigente | ✔ incluido |
| CN-3 | Acciones / bases de cálculo / demanda | Vigente | ✔ incluido |

> Nota: existe además la **especificación de ingeniería** del motor en `Estructurando/Nucleo-transversal/C5_Contrato-motor-FEM.md` (FEM-2, §1–§8), no duplicada aquí; en este compendio se incluye la **interfaz canónica** C5. La IA prepara y propone; la firma es de JM.

\newpage



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


\newpage



# C2 — Contrato de datos: dato crudo del cliente ↔ conocimiento aprendido de Aqyra

**Tipo:** contrato de interfaz / gobierno de datos (SemVer) · **zona protegida** (`contratos-golden/contratos/`)
**Versión:** v0.1.0 (DRAFT, pre-1.0 → interfaz aún inestable) · **Fecha:** 2026-06-26
**Estado:** PROPUESTA — borrador IA, pendiente de firma de JM
**Satisfecho por:** el entorno Aqyra (custodio del dato y del aprendizaje) · **Consumen:** el cliente (dueño del dato crudo) y el operador IA (**C7**, que extrae y consume conocimiento)

> Define **la frontera entre el dato crudo del cliente y el conocimiento que Aqyra puede aprender y retener de él**: qué es de quién, qué puede cruzar de "crudo" a "aprendido", con qué de-identificación, bajo qué consentimiento y con qué derecho de borrado. Es el contrato que sostiene el **foso-conocimiento** sin romper la promesa de apertura. Preparado por la IA; la responsabilidad y la firma son de JM.

> **Numeración:** ocupa **C2** (hueco libre, foundational: C1 mete el dato → C2 gobierna qué se aprende de él). **C3 queda reservado.** Esquema vigente: C1 (parser/IFC) · **C2 (datos)** · C3 *(reservado)* · C4 (red) · C5 (motor-fem) · C6 (corpus golden) · C7 (operador IA) · C8 (intercambio CDE). **Reconciliación 2026-06-27 (firmada por JM):** las convenciones de núcleo heredadas (memoria, documentación) salen del espacio C a la familia **CN-*** (CN-1 memoria, CN-2 documentación), de modo que C3 sigue libre y no hay colisión de C2.

> **La distinción quirúrgica (corazón del contrato).** El **dato crudo** es del **cliente** y es **abierto** —diff-able, exportable, nunca cautivo—. Los **patrones/criterios aprendidos**, una vez **de-identificados**, son de **Aqyra**: ese es el moat. El foso es el **modelo aprendido, no el dato en bruto.** Y la de-identificación no es un adorno: es **lo que hace el foso legalmente sostenible**, porque un patrón que no conserva ninguna traza identificable **sobrevive a un borrado** del dato crudo sin tener que "des-aprenderse".

---

## 1. Propósito y alcance

Establecer la frontera, dentro del entorno Aqyra, entre:

- el **dato crudo** que el cliente aporta o genera (su proyecto: IFC, geometría, propiedades, cantidades, documentos, resultados firmados), del que el cliente es **dueño soberano**, y
- el **conocimiento aprendido** (patrones, criterios, heurísticas, distribuciones) que Aqyra extrae al procesarlo y **retiene de-identificado** para mejorar la asistencia en proyectos futuros (el círculo virtuoso, transversal y capitalizado).

de modo que el aprendizaje **nunca** se haga a costa de la soberanía ni de la apertura del dato del cliente, y que lo retenido **no pueda reconducirse** a un cliente, un proyecto, ni a la cadena de responsabilidad civil de una firma.

**Alcance de v0:** la frontera de aprendizaje sobre los entregables del operador IA (**C7**) y de los motores (C5/C4): qué se puede extraer, qué se debe de-identificar y qué está prohibido retener. La **monetización** del consentimiento (descuento por opt-in, etc.) y la implementación del almacén quedan fuera (capa comercial / ingeniería).

## 2. Principios de diseño (no negociables)

1. **Soberanía del dato crudo.** El dato crudo es del cliente: **exportable** en formato abierto en todo momento, **portable** (no cautivo de Aqyra), y **borrable** a petición. Aqyra es **custodio**, no dueño.
2. **El moat es el aprendido, no el crudo.** Aqyra capitaliza **patrones de-identificados**, nunca el dato bruto. Vender apertura y capitalizar el bruto a la vez sería la contradicción que este contrato existe para impedir.
3. **De-identificación robusta y verificable.** Un patrón solo cruza a "aprendido/retenible" si **no permite reconstruir** ni el cliente, ni el proyecto, ni su geometría/cantidades identificables, ni la cadena de firma/responsabilidad. La robustez se **prueba** (golden anti-re-identificación, §7), no se asume.
4. **Prohibido reutilizar la firma y su responsabilidad civil.** Un cálculo lleva la firma de un colegiado y responsabilidad civil. **Nada** de lo retenido puede atar un patrón a un entregable firmado concreto ni a su autor. La firma es del que la pone, nunca insumo de entrenamiento.
5. **Consentimiento explícito (opt-in, soberanía primero).** Por defecto **no se capitaliza** nada del proyecto de un cliente sin su **consentimiento explícito**. El cliente conserva siempre el dato, su exportación y su borrado, consienta o no. *(El modelo de incentivo —descuento por consentir, opt-in vs opt-out— es decisión comercial, §9.)*
6. **Derecho al olvido sin des-aprender.** El borrado del dato crudo es inmediato y total. Como el patrón retenido **no conserva traza identificable** (principio 3), el borrado **no obliga** a des-aprender — y si un patrón fuese reconducible a lo borrado, **no debió retenerse**.
7. **Trazabilidad y dos llaves.** Toda retención registra su procedencia y su prueba de de-identificación. La IA **propone** retener; la certificación de "este patrón es capitalizable" exige la **segunda llave** (firma de JM). La IA nunca certifica que algo es seguro de retener.
8. **Formato abierto.** El dato y los registros de consentimiento/procedencia viajan como **texto diff-able**; nada propietario en la frontera del dato del cliente.

## 3. Partes y direcciones

| Dirección | Productor | Consumidor |
|---|---|---|
| **Dato crudo → entorno** | El cliente | Aqyra (custodio) — lo procesa, no lo posee |
| **Conocimiento de-identificado → almacén** | Aqyra (vía operador IA, C7) | Aqyra (lo capitaliza para proyectos futuros) |
| **Export / borrado** | Aqyra (custodio) | El cliente (ejerce su soberanía) |

## 4. Objetos que cruzan la frontera

| # | Objeto | Lado | Régimen |
|---|--------|------|---------|
| D1 | **Dato crudo del proyecto** | del cliente | IFC, geometría, propiedades, cantidades, documentos, resultados firmados. **Soberano, abierto, borrable.** Nunca insumo de entrenamiento sin D4. |
| D2 | **Candidato a patrón** | en la frontera | abstracción extraída al procesar (criterio, heurística, distribución). **Aún no retenible**: pasa por la puerta de de-identificación (§6). |
| D3 | **Conocimiento aprendido de-identificado** | de Aqyra | el patrón ya despojado de toda traza identificable. **Capitalizable**, el moat. |
| D4 | **Registro de consentimiento** | del cliente | opt-in explícito (alcance, fecha, revocable). Sin él, D2 **no** cruza a D3. |
| D5 | **Prueba de de-identificación** | de Aqyra | evidencia de que D3 supera el test anti-re-identificación (§7), atada a la golden. |

**Lista de lo PROHIBIDO retener** (si aparece en D2, no cruza): identidad del cliente o del autor/colegiado; identificadores del proyecto, emplazamiento o catastro; geometría o cantidades que reconstruyan el proyecto; cualquier vínculo a una firma o a su responsabilidad civil; datos personales (RGPD).

## 5. Superficie de API (abstracta)

| Operación | Dirección | Objeto | Nota |
|---|---|---|---|
| `otorgar_consentimiento(cliente, alcance)` / `revocar_consentimiento(id)` | cliente → | D4 | opt-in explícito y revocable; revocar corta futuras retenciones |
| `exportar_datos(proyecto)` | → cliente | D1 | dato crudo en formato abierto, en cualquier momento |
| `borrar_datos(proyecto)` | cliente → | D1 | borrado inmediato y total del crudo |
| `proponer_retencion(candidato)` | operador IA → | D2 → D5 | **propone** retener un patrón; adjunta su prueba de de-identificación |
| `auditar_aprendido(filtro)` | → JM / cliente | D3, D5 | inspecciona qué se ha retenido y su procedencia/prueba |

**Transversal:** mínimo privilegio, **traza de auditoría** de cada retención y cada consentimiento, e **idempotencia** del borrado.

## 6. Máquina de estados y candado de gobierno

- Estados de un candidato a patrón: **CANDIDATO** (D2) → **DE-IDENTIFICADO** (supera el test §7) → **CONSENTIDO** (existe D4 vigente) → **CAPITALIZADO** (retenido en el almacén, D3).
- **Candado de dos llaves:** un candidato solo llega a **CAPITALIZADO** con **prueba de de-identificación verde (golden) + consentimiento vigente + firma de JM**. El operador IA solo `propone_retencion`; **nunca certifica** que un patrón es seguro de capitalizar.
- **Revocación / borrado:** revocar el consentimiento corta futuras retenciones; borrar el crudo es inmediato. Ningún patrón CAPITALIZADO puede quedar atado a un crudo borrado (si lo estuviera, no superó §7 y se purga).

## 7. De-identificación y oráculo (atados a la golden)

El oráculo de C2 **no es numérico ni de conformidad documental** — es de **no-reconducción**. Una golden de C2 somete al conocimiento retenido (D3) a un **intento adversario de re-identificación** y exige que **fracase** en recuperar:

1. **la identidad del cliente** (o del autor/colegiado);
2. **la identidad del proyecto** (nombre, emplazamiento, catastro);
3. **la geometría / cantidades** que reconstruyan el proyecto;
4. **la cadena de firma / responsabilidad civil**.

Si el ataque recupera **cualquiera** de las cuatro ⇒ **rojo**: el patrón **no es retenible**. El fallo más grave es el 4 (reconducir a una firma).

**Procedencia del oráculo:** conjunto de re-identificación **definido y firmado por JM** (mano-JM) sobre proyectos de referencia. Un fallo **no** se arregla relajando el ataque ni el criterio — **solo endureciendo la de-identificación** (mismo espíritu que C5/C7).

> **Golden de v0 a sembrar:** `GOL-DAT-01` — sobre un proyecto de referencia, extraer candidatos a patrón, de-identificarlos y verificar que el ataque de re-identificación fracasa en las cuatro dimensiones. Hasta sembrarla y ratificarla, **C2 v0 no es certificable** (Llave 1 incompleta) y **no se capitaliza nada**.

## 8. Versionado y compatibilidad

- C2 se versiona con SemVer; el consumidor ancla la versión exacta en `versions.lock`.
- **Verde** en la golden anti-re-identificación → se adopta el régimen de retención. **Rojo** → se endurece la de-identificación (regresión) o se cambia el contrato (**MAJOR**).
- Al ser DRAFT pre-1.0 (v0.x), se admiten cambios incompatibles entre minors mientras se estabiliza.

## 9. Puntos abiertos (a cerrar)

1. **Modelo de consentimiento e incentivo** — opt-in (recomendado, soberanía primero) vs opt-out; ¿descuento o contraprestación por consentir? *(decisión comercial — afecta a la tarjeta de precios del roadmap).*
2. **Qué es un "patrón" capitalizable** — taxonomía concreta de D3 (criterios de predimensionado, distribuciones de soluciones, heurísticas de cumplimiento…) y su granularidad.
3. **Técnica de de-identificación** — agregación / k-anonimato / privacidad diferencial / abstracción simbólica; qué se exige para v0.
4. **Encaje legal** — RGPD (datos personales), propiedad intelectual del proyecto, y el deslinde explícito frente a la firma colegiada y su responsabilidad civil. Revisión jurídica antes del primer cliente serio.
5. **Composición con C7** — el operador IA es quien extrae los candidatos; fijar el handoff C7 → C2 (`proponer_retencion`) y que C7 nunca retenga por su cuenta.
6. **Sembrar y ratificar `GOL-DAT-01`** con su conjunto de re-identificación firmado — sin esto, no hay Llave 1.

## 10. Fuera de alcance

- **La implementación del almacén** de conocimiento (base de datos, vectores) — detrás del adaptador.
- **La monetización del consentimiento** (capa comercial).
- **El intercambio con el CDE** (vive en C8) y **la generación de entregables** (vive en C7); C2 solo gobierna qué se aprende y retiene.
- **El modelo de IA concreto** y cómo entrena — detrás del adaptador.

---

### Firma

| Rol | N

\newpage



# C5 — Contrato de interfaz: dominio de análisis ↔ motor-fem

**Tipo:** contrato de interfaz (SemVer) · **zona protegida** (`contratos-golden/contratos/`)
**Versión:** v0.1.0 (DRAFT, pre-1.0 → interfaz aún inestable) · **Fecha:** 2026-06-26
**Rev. 2026-06-26:** cerrados los puntos abiertos 1–3 (JSON Schema canónico · Psets de resultado · alcance lámina). Pendientes 4–6 (ver `C5_puntos_abiertos_4-6.md`).
**Estado:** ✅ **FIRMADO — certificado por las dos llaves.** **Llave 1:** golden 7/7 VERDE (QA, P3 con PyNite 2.0.2). **Llave 2:** firma GPG de JM (EDDSA `8FD1E413A02021DD3E7903CA7D59BA28515E0942`, 2026-06-26 12:53 UTC) sobre `release.manifest.json` (repo `Estructurando/`, firma separada `.asc`), que ancla esta golden y el `sha256` de `motor-fem-v0.1.0.plugin` (`9239c2…866ae`). *Transcrito por la IA 2026-06-26 como reflejo de la firma; la firma criptográfica la posee JM — la IA no certifica.*
**Satisfecho por:** `motor-fem` (productor / taller Estructurando) · **Consumen:** Estructurando 2.0 (QA) y Entorno (producto Aqyra)

> Define **qué entra y qué sale del motor de cálculo** (FEM + verificación por Eurocódigos), **en qué
> formato** y **con qué versión**. Es el contrato que las 6 fichas golden de Decopak HQ validan
> (**golden vN valida C5 vN**). Preparado por la IA; la responsabilidad y la firma son de JM.

> **Numeración:** esquema vigente del ecosistema — C1 (parser/IFC) · C4 (red) · **C5 (motor-fem)** ·
> C6 (corpus golden) · C7 (operador IA) · C8 (intercambio CDE). Ver `C8_intercambio_CDE.md`.

---

## 1. Propósito y alcance

Establecer la frontera entre el **dominio de análisis estructural** (la idealización: barras/láminas,
secciones, materiales, apoyos, acciones y combinaciones) y el **motor-fem**, que la resuelve y verifica,
de modo que:

- el motor reciba un **modelo de análisis** bien definido (derivado del IFC físico y **autorado como
  propuesta** revisable, nunca como verdad cerrada — modelo de dos llaves), y
- devuelva **resultados de cálculo** (deformada, reacciones, esfuerzos N/V/M, análisis modal) y
  **aprovechamientos** frente a los Eurocódigos, en formato abierto y reproducible, listos para el
  write-back a Psets del IFC y para la memoria.

**Alcance de v0 (lo que ejercitan las golden de Decopak HQ):**

| Familia | Análisis | Verificación | Golden |
|---|---|---|---|
| Barra/celosía 2D–3D, estático | reacciones, N/V/M, deformada | EC3 6.2/6.3 (pandeo, clasificación) | DEC-B1, DEC-B2, DEC-B4 |
| Modal | frecuencias propias f₁ | EC5 §7.3 (vibración) | DEC-A1 |
| Flexión/flecha de nervio | M, δ | EC3 6.2.5, EC0 7.4 | DEC-A1 |
| Región D (discontinuidad) | bielas y tirantes | EC2 §6.5 | DEC-E1 |
| Geotecnia de pilote | capacidad | EN 1997 (EC7) | DEC-E2 |
| **Lámina 2D (losas/muros)** | folded-plate, flexión + membrana, esfuerzos m/n/v | EC2 (flexión, fisuración, punzonamiento) | **DEC-S1** |

> **Decisión 2026-06-26 (punto abierto 3):** v0 **incluye la familia lámina** (losas y muros). Es viable
> porque existe oráculo: el FEM folded-plate de QA validado contra Navier (−0,3 %). El shell de PyNite es
> limitado para lámina plegada, así que el oráculo certificado de lámina en v0 es **segundo-FEM + analítico
> cerrado**, no necesariamente PyNite (ver §7 y `C5_puntos_abiertos_4-6.md`).

**Principio rector:** *formato abierto, no binario*. El modelo y los resultados viajan como **texto
diff-able** (STEP/IFC + Psets, o JSON estructurado equivalente); nada propietario en la frontera.

## 2. Principios de diseño (no negociables)

1. **Contrato abstracto, no acoplamiento.** El consumidor depende de *esta interfaz*, no de la
   implementación interna del motor (numpy/PyNite/solver propio). Cambiar el solver por dentro **no** es
   cambio de contrato mientras la frontera y las tolerancias se respeten.
2. **Entrada como propuesta.** La idealización derivada del IFC físico se entrega marcada como
   `proposal` (Pset Aqyra), editable y revisable por un humano; el motor la consume, no la certifica.
3. **SemVer.** `MAJOR.MINOR.PATCH`; **MAJOR** = cambio incompatible de la interfaz (campos de entrada/salida,
   semántica de combinaciones, unidades). El consumidor **ancla** la versión en `versions.lock`; subir es
   deliberado (re-correr golden → adoptar solo si verde).
4. **Golden vN valida C5 vN** (decisión 1 del Gobierno). Las 6 fichas de `golden/` son la suite de
   conformidad de C5 v0.
5. **Dos llaves para certificar.** Un resultado del motor solo es *certificado* con golden verde +
   informe de QA limpio + **firma de JM**. La IA y el motor nunca certifican: producen y proponen.
6. **Reproducibilidad.** Mismo modelo + misma versión de motor ⇒ mismos resultados dentro de tolerancia
   (determinismo); cada salida registra la **procedencia del oráculo** que la valida.

## 3. Partes y direcciones

| Dirección | Productor | Consumidor |
|---|---|---|
| **modelo de análisis → motor-fem** | dominio de análisis (idealización, autorada) | `motor-fem` |
| **resultados → consumidor** | `motor-fem` | QA (2.0) y producto (Entorno) |

## 4. Objetos que cruzan la frontera

| # | Objeto | Dirección | Formato | Semántica |
|---|--------|-----------|---------|-----------|
| I1 | **Modelo de análisis** | → motor | IFC (dominio de análisis) o JSON equivalente | nodos, barras/láminas, secciones, materiales, apoyos |
| I2 | **Acciones y combinaciones** | → motor | Pset Aqyra `proposal` / JSON | cargas (permanente, uso, viento, nieve, sismo ac), coef. γ y ψ, casos, combinaciones ELU/ELS + sísmica |
| I3 | **Parámetros de verificación** | → motor | JSON | norma y Anejo Nacional, γ_M, clase, NDP marcados `[confirmar AN]` |
| O1 | **Deformada y reacciones** | motor → | JSON / Pset | desplazamientos nodales, reacciones de apoyo |
| O2 | **Esfuerzos** | motor → | JSON / Pset | N, V, M por barra/sección (envolventes por combinación) |
| O3 | **Modal** | motor → | JSON | frecuencias propias, periodos, masa participante |
| O4 | **Aprovechamientos** | motor → | JSON / Pset | u = E_d/R_d por comprobación y Eurocódigo, con veredicto CUMPLE/NO CUMPLE |
| O5 | **IFC con write-back** | motor → | IFC (Psets de resultado) | el modelo devuelto con O1–O4 escritos en Psets, texto diff-able |
| O6 | **Trazabilidad** | motor → | JSON / Markdown | versión de motor y de contrato, normas, oráculo de referencia, hipótesis |

> **Fuera de la frontera:** la lógica interna del solver (ensamblaje, condensación, integración) y la
> autoría de la idealización (vive antes de C5, en el parser/operador). C5 solo fija qué cruza.

## 5. Superficie de API (abstracta)

Verbos abstractos; la implementación los mapea a su API/CLI concreta.

| Operación | Dirección | Objeto | Nota |
|---|---|---|---|
| `resolver(modelo, acciones, params)` | → motor | I1–I3 ⇒ O1–O4, O6 | análisis estático + modal + verificación; resultado determinista |
| `escribir_resultados(modelo, resultados)` | motor → | O5 | write-back de Psets al IFC (idempotente, sin sobrescritura silenciosa) |
| `aprovechamientos(resultados)` | motor → | O4 | tabla u por comprobación con veredicto |
| `trazabilidad(run)` | motor → | O6 | versión, normas, oráculo, hipótesis del run |

**Transversal:** unidades **SI explícitas** en la frontera (m, N, Pa, kg; ángulos en grados declarados),
**idempotencia** del write-back y **traza de auditoría** del run.

## 6. Esquema de datos (entrada/salida)

> **Esquema canónico (punto abierto 1, resuelto 2026-06-26):** la representación canónica, **además del
> IFC**, es JSON Schema 2020-12: `schemas/C5_modelo.schema.json` (entrada) y `schemas/C5_resultados.schema.json`
> (salida). El IFC y el JSON son **equivalentes 1:1**; la persistencia en IFC de los resultados se define en
> `C5_psets_resultado.md` (`Pset_AqyraStructuralResult_*`, punto abierto 2, resuelto). El resumen de campos
> mínimos sigue abajo; los schemas mandan en caso de discrepancia.

**Entrada (I1–I3), campos mínimos** — derivados de lo que el cálculo de Decopak necesitó de verdad
(`Entorno/HILO-V2_evidencia-cruzada_calculo.md` D-011):

```
nodos:         id, x, y, z
barras:        id, nodo_i, nodo_j, seccion, material, liberaciones
laminas:       id, nodos[], espesor, material            (cuando aplique)
secciones:     id, tipo (IPE/SHS/…), A, I_y, I_z, …  o paramétrica
materiales:    id, E, G, ρ, f_y/f_ck, γ_M
apoyos:        nodo, tipo (empotrado/articulado/resorte), rigideces
acciones:      caso, tipo (permanente/uso·categoría/viento/nieve/sismo·ac), valor
combinaciones: id, tipo (ELU/ELS/sísmica), {caso: (γ, ψ)}
verificacion:  norma, anejo_nacional, NDP[]  (marcados [confirmar AN])
```

**Salida (O1–O4), campos mínimos:**

```
desplazamientos: nodo, ux, uy, uz, rx, ry, rz
reacciones:      nodo, Fx, Fy, Fz, Mx, My, Mz
esfuerzos:       barra/sección, combinación, N, Vy, Vz, Mt, My, Mz   (+ envolvente)
modal:           modo, f [Hz], T [s], masa_participante
aprovechamiento: id, comprobación, norma§, E_d, R_d, u=E_d/R_d, veredicto
```

## 7. Tolerancias y oráculo (atadas a la golden)

- Las **tolerancias por magnitud** las fija cada ficha golden de `golden/` y **las ratifica JM**; no son
  parte editable del motor. Referencia v0: capacidades EC3 ±3–5 %, esfuerzos ±5 %, frecuencias ±5 %,
  tirantes EC2 ±3 %, capacidades EC7 ±5 %.
- Cada resultado declara su **oráculo de referencia**: analítico / segundo código FEM / **PyNite** / MMS /
  mano firmada por JM. El oráculo certificado de v0 es **PyNite** (pendiente de re-ejecución, P3).
- Un fallo de conformidad **no** se resuelve aflojando tolerancia ni editando el esperado — solo
  corrigiendo el motor.

## 8. Versionado y compatibilidad

- C5 se versiona con SemVer; el consumidor ancla la versión exacta en `versions.lock` (`nucleo: motor-fem`).
- **Verde** en la suite golden de C5 → se adopta. **Rojo** → regresión (la corrige el productor) o cambio
  de contrato (**MAJOR**: se adapta el consumidor y se revalida, con aprobación de JM).
- Al ser DRAFT pre-1.0 (v0.x) se admiten cambios incompatibles entre minors mientras se estabiliza.
- **Mapeo build↔release (pendiente, decisión JM):** el `version` del `plugin.json` (build interno del
  taller) es un espacio distinto del tag de release anclado. Hoy se ancla `motor-fem 0.1.0` (tag N1.1).
  Fijar qué build del taller se publica como qué tag es parte del cierre de N1.1 (FOCO6 §2).

## 9. Puntos abiertos

**Resueltos 2026-06-26 (decisión JM):**

1. ✅ **Esquema canónico** — JSON Schema 2020-12 (`schemas/C5_modelo.schema.json`, `schemas/C5_resultados.schema.json`) **además del** IFC; equivalentes 1:1.
2. ✅ **Psets de resultado** — `Pset_AqyraStructuralResult_*` definidos en `C5_psets_resultado.md`, espejo del schema de resultados.
3. ✅ **Alcance v0 incluye lámina** (losas/muros) — golden DEC-S1; oráculo segundo-FEM + analítico (no depende de PyNite).

**Resueltos 2026-06-26 (decisión JM, detalle en `C5_puntos_abiertos_4-6.md`):**

4. ✅ **Formato EC7 = parcial DA-2 español** (opción 4b). Acciones A1, resistencias R2; pilotes γ_b=1,35,
   γ_s=1,10, γ_t=1,25, γ_Rd=1,40 (`C5_NDP_anejo_nacional_ES.md` §6). El admisible SOCOTEC se conserva como
   traza. Afecta a O4 y a DEC-E2 (re-baseline pendiente de R_b,k/R_s,k).
5. ✅ **Sismo diferido de N1.1** (opción 5a) con justificación de baja sismicidad (ac≈0,046 g). El modal
   espectral con torsión (5c) se abre como **minor posterior** (C5 v0.x → v0.(x+1)) con su propia golden.
   EC8 queda `confirmar_AN`.
6. ✅ **NDP del Anejo Nacional español** fijados (opción 6c) en `C5_NDP_anejo_nacional_ES.md`: confirmados
   los que usan las 7 golden; `confirmar_AN` los de sismo (EC8) y los dependientes de emplazamiento.

**Sin puntos abiertos de redacción.** Restan acciones de ejecución: ratificación JM de la tabla NDP y de las
7 fichas, re-baseline de DEC-E2 en DA-2, corrección de DEC-A1 (Opción A) y re-ejecución con PyNite (P3).

## 10. Fuera de alcance

- La autoría de la idealización (derivar ejes/apoyos/cargas del físico): vive **antes** de C5.
- La certificación de resultados: vive en el gobierno de dos llaves, no en el motor.
- La memoria de cálculo como documento: la produce la skill de memoria a partir de O1–O6.

---

### Firma

| Rol | Nombre | Estado |
|---|---|---|
| Prepara (IA) | equipo IA Estructurando 2.0 | Borrador 2026-06-26 |
| Aprueba/firma | **JM** | ☐ Pendiente |

> Borrador para discusión. Predimensionado/interfaz a revisar por técnico competente. La firma de JM lo
> eleva a C5 v0 ratificado, al que quedan atadas las 6 fichas golden de Decopak HQ.


\newpage



# C7 — Contrato de interfaz: encargo ↔ operador IA

**Tipo:** contrato de interfaz (SemVer) · **zona protegida** (`contratos-golden/contratos/`)
**Versión:** v0.1.0 (DRAFT, pre-1.0 → interfaz aún inestable) · **Fecha:** 2026-06-26
**Estado:** PROPUESTA — borrador IA, pendiente de firma de JM
**Satisfecho por:** el **operador IA** (orquestador de entregables del entorno Aqyra) · **Consumen:** el producto Aqyra y, a través de él, el usuario (despacho / autónomo)

> Define **qué entra y qué sale del operador IA**: el componente que recibe un **encargo** (petición de un entregable + el modelo abierto + el alcance), **orquesta los motores** (C1 parser/IFC, C4 red, C5 motor-fem) y las **skills de normativa**, y **produce el entregable como propuesta revisable**, con veredicto, trazabilidad y fundamentación. Preparado por la IA; la responsabilidad y la firma son de JM.

> **Numeración:** esquema vigente del ecosistema — C1 (parser/IFC) · C4 (red) · C5 (motor-fem) · C6 (corpus golden) · **C7 (operador IA)** · C8 (intercambio CDE). Ver `C8_intercambio_CDE.md`.

> **La diferencia capital con C5.** El motor-fem (C5) es **determinista**: misma entrada + misma versión ⇒ misma salida dentro de tolerancia. El operador IA **no lo es**. Por eso C7 **no** promete reproducibilidad numérica; la sustituye por cuatro garantías: **(1) propuesta nunca certificación · (2) trazabilidad total · (3) fundamentación obligatoria (cero invención) · (4) conformidad estructural** verificable contra una golden de tipo distinto (completitud + grounding, no número).

---

## 1. Propósito y alcance

Establecer la frontera entre el **encargo** —la petición de un entregable de proyecto sobre un modelo abierto— y el **operador IA**, que lo resuelve orquestando los motores y las skills, de modo que:

- el operador reciba un **encargo bien definido** (tipo de entregable, modelo IFC, uso del edificio, alcance/fase, requisitos y datos confirmados), y
- devuelva un **entregable propuesto** (memoria / justificación / validación) con **veredicto** por exigencia, **trazabilidad** completa y **mapa de fundamentación**, en formato abierto y marcado como `proposal` (modelo de dos llaves).

**Alcance de v0 (lo que ejercita la golden de C7):** el operador de **documentación de cumplimiento**, concretamente la **memoria CTE + justificación urbanística** — el primer entregable firmable del roadmap (cuña autónomo), por ser máxima disposición a pagar y menor coste de construcción (usa las skills de CTE/normativa y C1; no requiere C5). Otras salidas (memoria de cálculo vía C5, predimensionado, presupuesto, validación municipal) son **ganchos para vN**, no parte de v0.

| Entregable | Motores/skills que orquesta | Golden v0 |
|---|---|---|
| **Memoria CTE** (DB-SI/SUA/HS/HR/HE/SE aplicables al uso) | C1 (parser) + skills `cte-documentos-basicos` | **GOL-CTE-01** *(a sembrar)* |
| **Justificación urbanística** | C1 + planeamiento aplicable (E3) | **GOL-URB-01** *(a sembrar)* |
| *(gancho vN)* Memoria de cálculo | C7 invoca **C5** y empaqueta su O1–O4 | — |
| *(gancho vN)* Predim / validación municipal | C5/C4 (predim) · C1+IDS (validación) | — |

## 2. Principios de diseño (no negociables)

1. **Contrato abstracto, no acoplamiento.** El consumidor depende de *esta interfaz*, no del modelo de IA ni de la arquitectura de agentes que haya detrás. Cambiar el modelo o los agentes por dentro **no** es cambio de contrato mientras la frontera y las garantías se respeten.
2. **Propuesta, no verdad.** Toda salida nace marcada `proposal`. La IA **produce y propone; nunca certifica.** La certificación exige la **segunda llave** (firma de JM), gobernada fuera de la API (§6).
3. **No determinista ⇒ trazable y fundamentado.** Sustituye al determinismo de C5. La "reproducibilidad" de C7 es **auditabilidad**: cada salida lleva su traza completa y su mapa de fundamentación, de modo que un humano pueda verificar *cómo* y *de dónde* salió cada afirmación.
4. **Fundamentación obligatoria — cero invención.** Ninguna afirmación sin fuente verificable (artículo de normativa vigente, resultado de C5/C4, propiedad del modelo). Lo que no tiene fuente **se marca `[confirmar]`, no se rellena.** Inventar un dato o citar una norma inexistente es un fallo de contrato.
5. **Humano en el bucle.** El operador **pide confirmación** de las hipótesis críticas (idealización, NDP, zona climática, ocupación, datos faltantes) antes de producir; nunca las asume en silencio.
6. **Formato abierto.** Entregable, veredicto, traza y grounding viajan como **texto diff-able** (Markdown / JSON); nada propietario en la frontera.
7. **SemVer.** `MAJOR.MINOR.PATCH`; **MAJOR** = cambio incompatible de la interfaz (campos del encargo/entregable, semántica del veredicto, esquema del grounding). El consumidor **ancla** la versión en `versions.lock`; subir es deliberado (re-correr golden → adoptar si verde). **Golden vN valida C7 vN.**

## 3. Partes y direcciones

| Dirección | Productor | Consumidor |
|---|---|---|
| **Encargo → operador** | El producto / usuario | El operador IA |
| **Operador → entregable** | El operador IA | El producto / usuario (y, opcional, el CDE vía C8) |

## 4. Objetos que cruzan la frontera

**Entrada (encargo → operador):**

| # | Objeto | Formato / estándar | Semántica |
|---|--------|--------------------|-----------|
| E1 | **Encargo** | JSON | tipo de entregable, uso del edificio, alcance/fase (Básico/Ejecución), banda de PEM |
| E2 | **Modelo abierto** | IFC (vía **C1**) | geometría, espacios, propiedades, clasificación |
| E3 | **Requisitos y contexto** | JSON / IDS / EIR-PIR (vía **C8** O4/O6) | normativa aplicable según uso, planeamiento urbanístico, parámetros, NDP |
| E4 | **Hipótesis y datos confirmados** | JSON | los que fija el humano (zona climática, ocupación, sectores de incendio…) |

**Salida (operador → entregable):**

| # | Objeto | Formato / estándar | Semántica |
|---|--------|--------------------|-----------|
| S1 | **Entregable propuesto** | Markdown / PDF, marcado `proposal` | la memoria / justificación redactada |
| S2 | **Veredicto por exigencia** | JSON / Markdown | CUMPLE / NO CUMPLE / CUMPLE CON OBSERVACIONES, con los huecos `[confirmar]` |
| S3 | **Trazabilidad** | JSON / Markdown | skills y motores usados + sus versiones, hipótesis asumidas, versión de C7 |
| S4 | **Mapa de fundamentación (grounding)** | JSON | cada afirmación ↔ su fuente (artículo, resultado C5/C4, propiedad del modelo) |
| S5 | **Write-back** *(opcional)* | IFC (vía **C1**, Psets) / doc al CDE (**C8** O7) | resultados/propiedades escritos al modelo o publicados |

## 5. Superficie de API (abstracta)

Verbos abstractos; el adaptador los mapea a la implementación concreta (agentes/skills).

| Operación | Dirección | Objeto | Nota |
|---|---|---|---|
| `solicitar_entregable(encargo, modelo, requisitos)` | encargo → operador | E1–E3 → S1–S4 | produce el borrador propuesto con su traza y grounding |
| `listar_huecos(entregable_id)` | operador → | S2 | devuelve los `[confirmar]` que faltan por fijar |
| `confirmar_hipotesis(entregable_id, valores)` | encargo → operador | E4 | el humano fija datos/hipótesis marcados `[confirmar]`; regenera lo afectado |
| `revisar(entregable_id)` | operador → | S3, S4 | entrega traza + mapa de fundamentación para auditoría |
| `proponer_certificacion(entregable_id)` | operador → | — | **propone** pasar a certificado; la 2ª llave la gobierna §6, no la API |

**Transversal:** **mínimo privilegio**, **traza de auditoría** de cada generación (qué versión de qué skill/motor, qué fuentes), e **idempotencia** del write-back.

## 6. Máquina de estados y candado de gobierno

- Estados del entregable: **BORRADOR** (`proposal`) → **REVISADO** (un humano validó hipótesis y grounding) → **CERTIFICADO** (dos llaves) → **PUBLICADO** (al CDE, vía C8).
- **Candado de dos llaves** (mismo principio que C5/C8 §6): la transición a **CERTIFICADO** exige **golden verde + revisión de grounding limpia + firma de JM**. El operador IA solo produce **BORRADOR** y puede `proponer_certificacion`; **nunca certifica**.
- Ningún hueco `[confirmar]` puede quedar abierto en un entregable que se propone a certificación: o se confirma (E4) o se declara explícitamente como no aplicable.

## 7. Oráculo y conformidad (atados a la golden)

El oráculo de C7 **no es numérico** (a diferencia de C5). Es de **conformidad estructural + fundamentación**. Una golden de C7 fija, para un proyecto de referencia, cuatro comprobaciones:

1. **Cobertura** — el entregable cubre **todas** las exigencias aplicables al uso (CTE: DB-SI/SUA/HS/HR/HE/SE + normativa concurrente; urbanística: todos los parámetros del planeamiento). Falta una exigencia aplicable ⇒ rojo.
2. **Citación** — cada justificación cita un **artículo real, vigente y aplicable** al caso. Cita inexistente, derogada o inaplicable ⇒ rojo.
3. **Veredicto** — el CUMPLE / NO CUMPLE / observaciones por exigencia **coincide** con el checklist de referencia.
4. **Grounding** — **0 afirmaciones sin fuente**; los huecos correctamente marcados `[confirmar]`. Una afirmación inventada ⇒ rojo (el fallo más grave).

**Procedencia del oráculo:** checklist de cumplimiento de referencia **revisado y firmado por JM** (mano-JM), apoyado en la skill `cte-documentos-basicos:checklist-cumplimiento`. Un fallo de conformidad **no** se arregla relajando el checklist ni editando el esperado — **solo corrigiendo el operador** (mismo espíritu que C5).

> **Golden de v0 a sembrar:** `GOL-CTE-01` (memoria CTE de un proyecto de referencia — p. ej. Decopak) y `GOL-URB-01` (justificación urbanística). Cada una con su checklist firmado como oráculo. Hasta sembrarlas y ratificarlas, **C7 v0 no es certificable** (Llave 1 incompleta).

## 8. Versionado y compatibilidad

- C7 se versiona con SemVer; el consumidor ancla la versión exacta en `versions.lock`.
- **Verde** en la golden de conformidad → se adopta. **Rojo** → regresión (la corrige el operador) o cambio de contrato (**MAJOR**: se adapta el adaptador y se revalida).
- Al ser DRAFT pre-1.0 (v0.x), se admiten cambios incompatibles entre minors mientras se estabiliza la frontera.

## 9. Puntos abiertos (a cerrar)

1. **Catálogo de entregables de v0** — ¿solo memoria CTE + urbanística, o se incluye ya validación municipal (gancho del Mostrador B)? *Propuesta: solo CTE + urbanística; lo demás a vN.*
2. **Esquema JSON** del encargo (E1), del veredicto (S2) y del mapa de grounding (S4) — `schemas/C7_*.schema.json`, en paralelo a los de C5.
3. **Handoff C7 → C5/C4** cuando el entregable incluye cálculo: cómo invoca el operador al motor y empaqueta su O1–O4 en la memoria (define la composición de contratos).
4. **Fuente de la normativa urbanística** (planeamiento municipal): ¿de dónde se carga el articulado aplicable? (IDS del CDE / carga manual / base de datos del despacho).
5. **Política de citación verificable** — ¿se exige cita literal con referencia fechada de cada artículo? ¿qué versión de cada DB del CTE se ancla (igual que los NDP de C5)?
6. **Sembrar y ratificar `GOL-CTE-01` / `GOL-URB-01`** con su checklist firmado — sin esto, no hay Llave 1.

## 10. Fuera de alcance

- **El cálculo numérico** (vive en C5) y **la resolución de redes** (C4): C7 los **orquesta**, no los reimplementa.
- **La certificación** de los entregables: vive en el gobierno de dos llaves, no en la API.
- **El modelo de IA concreto y la implementación de agentes/skills:** quedan detrás del adaptador.
- **El cobro / la licencia** (capa comercial) y **el tope de uso justo** (guardarraíl operativo): no son parte de esta interfaz.

---

### Firma

| Rol | Nombre | Estado |
|---|---|---|
| Prepara (IA) | equipo IA Estructurando 2.0 / Aqyra | Entregado 2026-06-26 |
| Aprueba/firma | **JM** | ☐ Pendiente |


\newpage



# C8 — Contrato de interfaz: Nuestro entorno ↔ CDE

**Tipo:** contrato de interfaz (SemVer) · **zona protegida** (`contratos-golden/contratos/`)
**Versión:** v0.1.0 (DRAFT, pre-1.0 → interfaz aún inestable) · **Fecha:** 2026-06-23
**Estado:** PROPUESTA — pendiente de (a) alineación con el equipo del CDE y (b) firma de JM
**Co-propiedad:** equipo Estructurando 2.0 / proyecto Entorno · equipo del CDE (producto en paralelo)

> **Nota de numeración (reconciliación 2026-06-23):** este contrato se redactó primero como «C6», pero el esquema de contratos del ecosistema ya reserva **C6 = corpus golden / recuperación por OIR** y **C7 = operador IA** (ver `entorno/integracion/versions.lock`). Para evitar colisión, el intercambio con el CDE pasa a **C8**. Esquema vigente: C1 (parser/IFC), C2 (datos), C3 *(reservado)*, C4 (red), C5 (motor-fem), C6 (corpus), C7 (operador IA), **C8 (intercambio CDE)**. **Reconciliación 2026-06-27 (firmada por JM):** las convenciones de núcleo heredadas pasan a la familia **CN-*** (CN-1 memoria, CN-2 documentación), fuera del espacio C.

> Define **qué cruza la frontera** entre nuestro entorno y el CDE, **en qué formato**, **en qué dirección** y **con qué versión**. Sigue el modelo productor/consumidor de `GOBIERNO_QA_Y_VERSIONES.md` (§A). Preparado por la IA; la responsabilidad y la firma son de JM.

---

## 1. Propósito y alcance

Establecer el intercambio **bidireccional** entre nuestro entorno abierto (basado en IFC) y el CDE que desarrolla el equipo en paralelo, de modo que:

- los entregables de **misión 1** (pre/post de cálculo: IFC con resultados escritos de vuelta) y de **misión 2** (QA del IFC: incidencias) **se publiquen** en el CDE, y
- el CDE **sirva** a nuestro entorno los modelos, los requisitos de información (EIR/PIR) y el contexto de estados/incidencias.

**Principio rector:** la frontera se apoya en **estándares openBIM** (IFC, BCF, IDS) y en el modelo de estados **ISO 19650**; la API es **fina**, y por debajo viajan artefactos estándar. Mismo lema del proyecto: *formato abierto, no binario*, aplicado a la integración.

## 2. Principios de diseño (no negociables)

1. **Contrato abstracto, no acoplamiento.** Su CDE es *una* implementación detrás de un **adaptador**; no *la* dependencia. Si su API cambia, lo absorbe el adaptador (regla §A.3/A.4 del Gobierno).
2. **Estándares por debajo.** Modelo en **IFC**; incidencias en **BCF**; requisitos en **IDS**; estados y metadatos en **ISO 19650**. Solo se inventa lo imprescindible.
3. **SemVer.** `MAJOR.MINOR.PATCH`; **MAJOR** = cambio incompatible de la interfaz. El consumidor **ancla** la versión en `versions.lock`; subir es deliberado (re-correr golden → adoptar si verde).
4. **Golden vN valida C8 vN** (decisión 1 del Gobierno).
5. **Dos llaves para publicar resultados certificados.** Un entregable solo transiciona a estado *Publicado/certificado* con golden verde + informe de QA limpio + **firma de JM**. La IA nunca certifica.

## 3. Partes y direcciones

| Dirección | Productor | Consumidor |
|---|---|---|
| **Entorno → CDE** | Nuestro entorno | El CDE |
| **CDE → Entorno** | El CDE | Nuestro entorno |

## 4. Objetos que cruzan la frontera

| # | Objeto | Dirección | Formato / estándar | Semántica |
|---|--------|-----------|--------------------|-----------|
| O1 | **Modelo de información** | CDE → Entorno | **IFC** (IFC4; IFC4.3 si infra) | El CDE entrega el modelo a procesar (cálculo/QA). |
| O2 | **Modelo con write-back** | Entorno → CDE | **IFC** (Psets de resultado) | Devolvemos el IFC con resultados de cálculo/comprobaciones escritos en Psets. |
| O3 | **Incidencias / QA** | bidireccional | **BCF** (2.1 / 3.0, vía BCF-API) | Misión 2 publica issues de QA como BCF; recibimos su estado/resolución. |
| O4 | **Requisitos validables** | CDE → Entorno | **IDS** | Requisitos de información comprobables sobre el modelo. |
| O5 | **Metadatos de contenedor y estado** | bidireccional | **ISO 19650** (código de estado/suitability, revisión, clasificación) | Estado del contenedor (WIP→Compartido→Publicado→Archivado), revisión, idoneidad. |
| O6 | **Requisitos de información** | CDE → Entorno | Estructurado (EIR/PIR; JSON/doc a definir) | Qué debe entregar el proyecto; alimenta a los copilotos. |
| O7 | **Entregables documentales** | Entorno → CDE | Markdown / PDF | Memoria de cálculo, informe de QA (acompañan al IFC). |

> **Fuera de la frontera:** los candidatos a golden y la evidencia interna de QA viven en `contratos-golden/` y `qa/`, **no** se publican al CDE salvo decisión expresa.

## 5. Superficie de API (abstracta)

Verbos abstractos; el adaptador los mapea a la API concreta del CDE.

| Operación | Dirección | Objeto | Nota |
|---|---|---|---|
| `obtener_modelo(id, rev)` | CDE → Entorno | O1 | Descarga el IFC de un contenedor/revisión. |
| `publicar_modelo(id, ifc, meta)` | Entorno → CDE | O2, O5 | Sube IFC con write-back + metadatos; **no** publica como certificado por sí solo (ver §6). |
| `listar_incidencias(filtro)` | CDE → Entorno | O3 | Lee issues (BCF). |
| `publicar_incidencia(bcf)` / `actualizar_incidencia(id)` | Entorno → CDE | O3 | Empuja/actualiza issues de QA. |
| `leer_requisitos(proyecto)` | CDE → Entorno | O4, O6 | Obtiene IDS y EIR/PIR. |
| `leer_estado(id)` / `proponer_transicion(id, estado)` | bidireccional | O5 | Lee o **propone** cambio de estado (la transición a Publicado la gobierna §6). |
| `adjuntar_documento(id, doc)` | Entorno → CDE | O7 | Sube memoria/informe. |

**Transversal:** autenticación (mecanismo a confirmar con el equipo del CDE), **mínimo privilegio**, **idempotencia** en las escrituras y **traza de auditoría** (exigida por ISO 19650).

## 6. Máquina de estados y candado de gobierno

- Las transiciones siguen ISO 19650: **WIP → Compartido → Publicado → Archivado**.
- **Candado:** la transición a **Publicado/certificado** de un resultado de cálculo **requiere las dos llaves** (golden verde + informe de QA limpio + **firma de JM**). Nuestro entorno solo puede `proponer_transicion`; la publicación certificada la ratifica el proceso de gobierno, no la API.
- No se publica sobre un contenedor ya Publicado sin nueva revisión (sin sobrescritura silenciosa).

## 7. Versionado y compatibilidad

- C8 se versiona con SemVer; el consumidor ancla la versión exacta en `versions.lock` (entrada `cde-interfaz` + la versión del producto CDE cuando se ratifique).
- **Verde** en la suite golden de interfaz → se adopta. **Rojo** → regresión (la corrige el productor) o cambio de contrato (**MAJOR**: se adapta el adaptador y se revalida).
- Al ser DRAFT pre-1.0 (v0.x), se admiten cambios incompatibles entre minors mientras se estabiliza con el equipo del CDE.

## 8. Puntos abiertos (a cerrar con el equipo del CDE)

1. **Versión de IFC** soportada por el CDE (IFC4 vs IFC4.3) y perfil/MVD.
2. **Versión de BCF** (2.1 vs 3.0) y si exponen **BCF-API** (REST) o solo BCFzip.
3. **Soporte de IDS** para requisitos validables.
4. **Mecanismo de autenticación** y modelo de permisos (quién puede transicionar estados).
5. **Esquema de O6** (EIR/PIR): formato estructurado concreto (JSON Schema a acordar).
6. **Códigos de estado/idoneidad** exactos que usa su CDE (mapeo a ISO 19650 S0–S7).
7. **Hosting/despliegue** (cloud / on-prem) e implicaciones de la auditoría.

## 9. Fuera de alcance

- Construir un CDE (lo hace el equipo en paralelo).
- La lógica interna del CDE (permisos, almacenamiento) más allá de lo que cruza la frontera.
- La certificación de resultados (vive en el gobierno de dos llaves, no en la API).

---

### Firma



\newpage



# CN-1 — Convención de memoria del despacho (aprendizaje entre hilos)

> **Reconciliación de numeración (2026-06-27, firmada por JM).** Este contrato era **«C2 — memoria del despacho»**. Para evitar la colisión con el **C2 canónico = datos**, se traslada a la familia **CN- (Convenciones de Núcleo)**, que agrupa las convenciones transversales que no son interfaces entre piezas. Sucede a `C2_Contrato-memoria-despacho.md` (ahora puntero). Esquema vigente: interfaces **C1–C8** · convenciones de núcleo **CN-1 (memoria)**, **CN-2 (entregables/documentación)**.

**Núcleo transversal · PT 1.3 (Ola 1).** Generaliza el mecanismo de memoria ya probado en
estructuras para que **toda disciplina aprenda entre hilos** con el mismo formato y ubicación
estable. Estado a 22/06/2026 (numeración actualizada 2026-06-27).

> Las skills `criterios-memoria` de cada plugin **leen estos archivos al iniciar**: el formato y
> la ubicación deben mantenerse estables.

---

## 1. Dos niveles de memoria

1. **Criterios del despacho (entre proyectos):** un archivo por disciplina en la **raíz** de la
   carpeta de trabajo. Acumula decisiones que se repiten en todos los proyectos (materiales por
   defecto, Anejo Nacional, coeficientes, criterios de diseño, lecciones aprendidas).
   - `criterios-despacho.md` — estructuras *(ya existe)*
   - `criterios-instalaciones.md` — instalaciones *(a crear en Ola 4)*
   - `criterios-<disciplina>.md` — patrón general
2. **Memoria del proyecto (por obra):** una `memoria-<disciplina>.md` en la **subcarpeta** de
   cada proyecto, con las decisiones e hipótesis específicas y el registro de comprobaciones.

A esto se añade el **programa de aprendizaje** (3 docs en `Casos-de-uso/`): `PROGRAMA`,
`REPOSITORIO`, `CHANGELOG` — mecanismo de crecimiento del plugin.

---

## 2. Árbol de carpetas de proyecto (convención reutilizable)

```
<Carpeta-de-trabajo>/
├── criterios-<disciplina>.md          # criterios del despacho (transversal, entre proyectos)
├── Casos-de-uso/
│   ├── PROGRAMA-aprendizaje.md         # escalera de casos + protocolo (DoD)
│   ├── REPOSITORIO-aprendizaje.md      # lecciones, backlog de incidencias, métricas
│   └── CHANGELOG-plugin.md             # versiones del plugin (SemVer)
└── <Proyecto-X>/
    ├── memoria-<disciplina>.md         # memoria de la obra (decisiones, hipótesis, registro)
    ├── modelo.ifc                      # soporte IFC
    └── _resultados/                    # salidas (diagramas, memoria Word, JSON neutro)
```

---

## 3. Plantilla de `criterios-<disciplina>.md`

> Plantilla lista para copiar también en `plantilla-criterios-disciplina.md` (esta carpeta).

```markdown
# Criterios de despacho - <Disciplina>

> Capa transversal de memoria (se acumula entre todos los proyectos).
> Las skills del plugin `<plugin>` LEEN este archivo al iniciar: mantener formato y ubicación.
> Todo resultado derivado debe ser **revisado y firmado por técnico competente**.

## Normativa
- Anejo Nacional / reglamento por defecto: **España**
- Normas de referencia: <listar>

## Materiales / componentes habituales
- <p. ej. Hormigón C30/37; o, en instalaciones, tubería/cable/conducto por defecto>

## Coeficientes y criterios
- <coeficientes parciales, límites de servicio, criterios de diseño> [confirmar AN/Reglamento]

## Lecciones aprendidas (crece hilo a hilo)
- [AAAA-MM-DD] <lección> / <razón> / <referencia normativa>. [caso N]

## Formato de memoria
- Una memoria por obra en su subcarpeta; citar siempre el artículo aplicado.
- Marcar **[confirmar AN]** los valores NDP no verificados.
- Registro de comprobaciones fechado (AAAA-MM-DD): elemento / skill / parámetros / resultado / decisión.
- Unidades SI.
```

---

## 4. Reglas del contrato CN-1

- **Ubicación estable:** criterios en la raíz; memoria en la subcarpeta del proyecto.
- **Formato estable:** secciones fijas (Normativa, Materiales, Coeficientes, Lecciones, Formato).
- **Entradas fechadas:** toda lección y comprobación lleva fecha `AAAA-MM-DD` y, si aplica, el
  caso de uso que la originó.
- **Trazabilidad normativa:** citar artículo; marcar **[confirmar AN]** los NDP.
- **Una skill `criterios-memoria` por plugin** inicializa y mantiene estos archivos.

## 5. Checklist de cumplimiento (disciplina nueva)

- [ ] Tiene `criterios-<disciplina>.md` en la raíz con las 5 secciones.
- [ ] Tiene `Casos-de-uso/` con PROGRAMA + REPOSITORIO + CHANGELOG.
- [ ] Cada proyecto tiene su `memoria-<disciplina>.md` en subcarpeta.
- [ ] Su skill `criterios-memoria` lee/escribe estos archivos al iniciar.


\newpage



# CN-2 — Convención de entregables y documentación

> **Reconciliación de numeración (2026-06-27, firmada por JM).** Este contrato era **«C3 — entregables y memoria»**. Para mantener **C3 reservado** en el esquema canónico, se traslada a la familia **CN- (Convenciones de Núcleo)**. Sucede a `C3_Contrato-entregables-memoria.md` (ahora puntero). Esquema vigente: interfaces **C1–C8** · convenciones de núcleo **CN-1 (memoria)**, **CN-2 (entregables/documentación)**.

**Núcleo transversal · PT 1.4 (Ola 1).** Define una **estructura de memoria homogénea** para
todas las disciplinas, de modo que las skills de memoria (`memoria-calculo`, `memoria-cte`,
futura `memoria-instalaciones`…) compartan formato, citas y trazabilidad. Estado a 22/06/2026
(numeración actualizada 2026-06-27).

> Motor de documentos común: skills `docx`/`pdf`/`pptx`/`xlsx`. La estructura de contenido es la
> que se fija aquí; el formato de salida (Word/PDF) lo aporta la skill correspondiente.

---

## 1. Estructura común de memoria (todas las disciplinas)

Toda memoria sigue el mismo esqueleto, con los apartados específicos de cada disciplina dentro:

1. **Datos del proyecto** — emplazamiento, uso/tipología, Anejo Nacional, condicionantes
   (exposición/durabilidad, zona sísmica, zona climática, etc. según disciplina).
2. **Normativa aplicada** — normas y artículos de referencia.
3. **Materiales / componentes adoptados** — con sus parámetros característicos.
4. **Acciones e hipótesis / bases de cálculo** — cargas y combinaciones (bases de cálculo
   compartidas), o caudales/potencias/ocupación en instalaciones.
5. **Comprobaciones por elemento / sistema** — el cuerpo técnico: para cada elemento, el
   modelo, el cálculo, la cláusula normativa y el **aprovechamiento/resultado**.
6. **Registro de comprobaciones (fechado)** — trazabilidad: `AAAA-MM-DD` / elemento / skill /
   parámetros / resultado / decisión.
7. **Conclusiones** — síntesis y advertencias.

---

## 2. Reglas invariables (todas las disciplinas)

- **Citar siempre** el artículo de la norma aplicada (p. ej. *EN 1992-1-1 §6.4.4*; *RIPCI*;
  *REBT ITC-BT-19*).
- Marcar **[confirmar AN]** todo valor NDP (parámetro de determinación nacional) o de
  reglamento no verificado.
- **Unidades SI** coherentes y declaradas (kN, kN·m, MPa, mm en estructuras; l/s, kPa, kW, A en
  instalaciones).
- **Predimensionado/asistencia:** toda memoria incluye la advertencia de **revisión y firma por
  técnico competente**.
- **Una memoria por obra** en su subcarpeta (no mezclar proyectos); hereda los criterios
  transversales de `criterios-<disciplina>.md` (convención **CN-1**).
- **Registro fechado** de cada comprobación, enlazable al caso de uso que la originó.

---

## 3. Encaje con las skills de memoria existentes

- `estructuras-eurocodigos:memoria-calculo` y `motor-calculo-estructural` (memoria Word) →
  memoria de cálculo estructural.
- `cte-documentos-basicos:memoria-cte` → justificación de cumplimiento del CTE.
- Futuro `instalaciones:memoria-instalaciones` → mismo esqueleto, apartados MEP.

Todas reutilizan el motor de documentos (`docx`/`pdf`) y la **plantilla** común
(`plantilla-memoria.md`, esta carpeta).

> **Fuente canónica = `plantilla-memoria.md`** (los 7 apartados de §1). Toda disciplina nueva parte
> de ella. **Alineación pendiente (H4):** la skill `estructuras-eurocodigos:memoria-calculo` documenta
> hoy una estructura distinta ("Objeto y alcance" en vez de "Datos del proyecto", "Modelo estructural"
> separado y **sin** el apartado "Registro de comprobaciones (fechado)"). El generador del motor
> `sismico/generate_memoria_nucleo.py` (caso 15) **sí** sigue este esqueleto. Ajustar la skill al de
> §1 — cambio en el plugin `estructuras-eurocodigos` (Settings > Capabilities), no en este contrato.

## 4. Checklist de cumplimiento (disciplina nueva)

- [ ] Su memoria sigue el esqueleto de 7 apartados.
- [ ] Cita artículos y marca **[confirmar AN]** los NDP.
- [ ] Incluye registro fechado y advertencia de revisión/firma.
- [ ] Una memoria por obra, hereda criterios del despacho (CN-1).
- [ ] Reutiliza el motor de documentos común para la salida Word/PDF.


\newpage



# CN-3 — Convención de acciones / bases de cálculo / bases de demanda

> **Reconciliación de numeración (2026-06-27, firmada por JM).** Lo que el ecosistema venía rotulando «C4 — acciones / bases de cálculo / bases de demanda» **no es una interfaz entre piezas, es una convención de entrada compartida**; por el criterio de nomenclatura (interfaces C1–C8 · convenciones de núcleo CN-*) pasa a **CN-3**. El número **C4 canónico queda libre para "red"** (la interfaz del grafo de red, aún sin documento de contrato). Se ejecutó un barrido de las referencias «C4 = acciones/demanda» en las disciplinas, renombrándolas a CN-3 (sin tocar EC4, MITC4, C40/50 ni etiquetas de pieza).

**Núcleo transversal.** Define la **capa de entrada común** a cualquier disciplina: las acciones y bases de cálculo de las que parte el dimensionado. Estado a 2026-06-27.

> Principio: es **dato de entrada**, no cálculo. El grafo/modelo de red (interfaz **C4 = red**) y los solvers consumen esta convención; aquí solo se fija **qué cargas/demandas entran y cómo se expresan**.

---

## 1. Alcance (las tres formas de la misma convención)

- **Estructuras:** acciones y combinaciones EC0/EC1 + DB-SE-AE (permanentes, sobrecargas de uso, viento, nieve, térmicas, sísmica). Implementa: skill `estructuras-eurocodigos:bases-acciones`.
- **Instalaciones (MEP):** bases de demanda (caudales, potencias, ocupación, simultaneidad). Implementa: `instalaciones/scripts/.../bases_demanda.py` (gancho `demanda` del modelo neutro de red, C1 §4).
- **Obra lineal:** acción del tráfico (categoría de tráfico pesado para firmes), hidrología (caudales de cálculo 5.2-IC), demanda residual/abastecimiento (EN 752 / EN 805). Implementa: `obras-lineales/scripts/.../bases_*.py`.

## 2. Reglas

- **Es entrada, no interfaz de pieza:** se expresa como datos (acciones/combinaciones, demandas) que alimentan el modelo de red (C4) y los solvers.
- **Trazabilidad normativa:** citar la norma (EC0/EC1, DB-SE-AE, RIPCI/UNE, 5.2-IC, EN 752/805); marcar **[confirmar AN]** los NDP.
- **Unidades SI** declaradas.
- **Frontera:** C1 lee el IFC y da el modelo neutro/red; **CN-3** rellena las acciones/demandas; el solver de la disciplina calcula. (En el contrato C1 esta frontera aparece como «C1 lectura ↔ CN-3 demanda ↔ cálculo».)

## 3. Relación con los demás contratos

- **C1** (parser/IFC) entrega el modelo neutro y el grafo de red; deja el gancho `demanda` para CN-3.
- **C4** (red) es la **interfaz** del grafo de red (nodos/tramos) — distinta de esta convención de entrada.
- **C5** (motor-fem) consume las acciones estructurales de CN-3 para el cálculo FEM.


\newpage

