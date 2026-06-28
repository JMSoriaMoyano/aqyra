# Texto de inicio — PT 5.1 (Ola 5): soporte georreferenciado IFC 4.3 (IfcAlignment) + GIS

> Copia y pega el bloque siguiente al iniciar el hilo nuevo en el proyecto **Estructurando**.
> Da todo el contexto necesario sin información adicional.

---

Proyecto Estructurando. Ejecuta el **PT 5.1 de la Ola 5**: **abrir el soporte georreferenciado de obra
lineal** — un parser físico→neutro de **alineación** (`ifc_to_model_lineal.py`), su **generador de IFC
4.3 de prueba** (un eje de carretera) y la **validación de alineación/georreferencia**, ampliando
`iso19650-openbim` al esquema **IFC 4.3 (IFC4X3)** y reutilizando del núcleo lo que aplique
(`scripts/nucleo/ifc_utils`) **sin tocarlo**. Es la extensión **C1** que **estrena el dominio
georreferenciado**, análogo a lo que el **PT 4.2** hizo con el dominio IFC MEP antes de nacer
`instalaciones`. Trabaja sin agente de disciplina propio aún (lo crea el PT 5.2); apóyate en el patrón
de parsers ya maduro. **Este PT NO construye la disciplina `obras-lineales`** (trazado 3.1-IC / firmes
6.1-IC) ni calcula nada: solo C1 para obra lineal (leer/validar/escribir IFC 4.3 Alignment + georref +
emitir el **modelo neutro lineal**). **Ojo a la frontera:** la alineación es **referenciación lineal por
PK** (curva paramétrica 1D), **no** un grafo de red; **no** reutiliza `grafo_red` (eso es para
drenaje/obras hidráulicas de la Ola 6). Tampoco hay FEM: trazado y firmes son **geometría + normativa**.

**Lee primero, en este orden:**
1. `Hoja-de-ruta_Ecosistema-ingenieria.md` — §3 (mapa de plugins: `iso19650-openbim` v0.4.3, "ampliar
   **Alignment/GIS** en Ola 5"; convención de `description` ≤ 500), §4 (núcleo y contratos C1, CN-1, CN-2 y CN-3), §4bis
   vía C1 (referencia), §5 (disciplina **Obras lineales** — agente `ingeniero-de-obra-lineal` a crear;
   tipologías trazado/firmes/drenaje/obras hidráulicas; soporte IFC 4.3 Alignment + GIS), §6 (olas; este
   hilo es **Ola 5**; la Ola 6 reutiliza el motor hidráulico de red) y §8 (**decisiones abiertas nº2
   —empaquetado de obras lineales— y nº3 —formato GIS—**, ambas a resolver aquí).
2. `Nucleo-transversal/Verificacion-Ola4.md` — estado de cierre de la Ola 4 (núcleo de red + PCI + REBT),
   el checklist "listo para nueva disciplina" y la abstracción **"grafo de red + N solvers"** (para que
   no confundas el dominio de red con el de alineación: este PT abre un **modelo neutro hermano nuevo**,
   el lineal, no una red).
3. `Nucleo-transversal/C1_Contrato-IFC-modelo-neutro.md` — §3bis (**API del núcleo**:
   `ifc_utils.psets/length_scale/pset_value`; reutilizables para Psets y factor de unidades), §3
   ("**modelos hermanos por tipo de análisis**": añadir claves nuevas sin redefinir las existentes) y
   **§4bis** (Extensión al dominio de obra lineal: entidades **`IfcAlignment`** —horizontal
   rectas/clotoides/curvas; vertical rasante y acuerdos; **`IfcAlignmentCant`** peralte—,
   `IfcRoad`/`IfcRailway` y partes, `IfcCourse`/`IfcPavement`, `IfcEarthworksCut/Fill`, `IfcKerb`;
   **georreferencia `IfcMapConversion` + `IfcProjectedCRS`**; **modelo neutro lineal** propuesto:
   `{ alineacion: {planta[], alzado[], peralte[]}, secciones_tipo, firme, terreno }` por **PK**;
   interoperación GIS GeoJSON/Shapefile).
4. `criterios-despacho.md` (raíz) y `Casos-de-uso/REPOSITORIO-aprendizaje.md` — lecciones **PT 4.2**
   (apertura de un dominio IFC nuevo reutilizando el núcleo sin tocarlo; el parser casa la clase
   **exacta** `el.is_a()`; cuidado con unidades/escala del `IfcUnitAssignment`), **PT 4.6/INC-12** (el
   dato del proyecto que está en el IFC **prevalece**; documenta lo que inyecta el agente), **INC-09**
   (puerta de empaquetado obligatoria) y el **hazard de mount** (método más abajo).
5. **Punto de partida (núcleo, v0.23.0):** `scripts/nucleo/ifc_utils.py` expone `psets`, `length_scale`
   (factor de unidad de longitud del `IfcUnitAssignment`, mm/pie→m) y `pset_value`; está **espejado byte
   a byte** en `iso19650-openbim` e `instalaciones` (puerta `verificar_espejo_nucleo.py`). **No lo
   modifiques** salvo que decidas (y documentes) promover ahí un helper de georreferencia (ver decisión).
   `iso19650-openbim` v0.4.3 ya tiene `scripts/mep/` (parser de red) como **patrón a imitar** para el
   nuevo `scripts/lineal/`.

**Objetivo y alcance (qué hay que hacer):**

1. **Parser `ifc_to_model_lineal.py` (físico→neutro lineal).** Lee **`IfcAlignment`** y sus capas:
   **horizontal** (`IfcAlignmentHorizontal` → segmentos `LINE` / `CIRCULARARC` / `CLOTHOID`, con
   longitud, radio, parámetro A de clotoide, acimut), **vertical** (`IfcAlignmentVertical` → segmentos
   `CONSTANTGRADIENT` / `CIRCULARARC` / `PARABOLICARC`, con pendientes y Kv de acuerdo) y **peralte**
   (`IfcAlignmentCant`). Reconstruye el **perfil por PK** (punto kilométrico = abscisa curvilínea), con
   la **georreferencia** (`IfcMapConversion` + `IfcProjectedCRS`: EPSG, origen E/N, rotación, escala).
   **Reutiliza el núcleo:** `ifc_utils` para Psets y `length_scale`. Emite el **modelo neutro lineal** de
   C1 §4bis (`unidades` SI declaradas, `alineacion`{planta[]/alzado[]/peralte[]}, `georref`, ganchos
   `secciones_tipo`/`firme`/`terreno`), **modelo hermano** del estructural y del de red (mismas
   convenciones de `unidades`, claves nuevas, sin redefinir las existentes).
2. **Generador de IFC 4.3 de prueba** (banco, esquema **IFC4X3**): un eje de carretera simple
   —recta → clotoide → curva circular → clotoide → recta en planta, con uno o dos acuerdos verticales—
   georreferenciado (`IfcProjectedCRS`/`IfcMapConversion`), para validar el parser de extremo a extremo.
3. **Validación de alineación/georreferencia** (arnés propio, análogo al de equilibrio/continuidad de
   red): **continuidad y tangencia** entre segmentos (encadenan sin saltos; PK monótono creciente; radios
   y parámetros de clotoide coherentes con la 3.1-IC como umbral informativo), **georreferencia presente
   y consistente** (CRS, origen), **unidades SI**. Sin cálculo de trazado (eso es la disciplina).
4. **Ampliar `iso19650-openbim` a IFC 4.3 Alignment** (E/S IFC): que `ifc-create`/`ifc-validate`
   **conozcan las entidades de alineación/infra** (crear el eje de prueba; validar
   nomenclatura/Psets/clasificación bsDD + presencia de georreferencia). Si el alcance se hace grande,
   **prioriza el parser + validación (1-3)** y deja `ifc-create/validate` de Alignment como sub-entrega.
5. **Interoperación GIS (gancho, resolviendo la decisión nº3):** exporta la **planta** de la alineación a
   **GeoJSON** (LineString en el CRS proyectado) como puente hacia cartografía/hidrología, o al menos deja
   el hueco y **documenta el formato de intercambio elegido**. No implementes hidrología (es Ola 6).
6. **Gancho a la disciplina (no construir trazado/firmes aquí):** el modelo neutro lineal debe poder
   recibir luego las **secciones tipo**, el **paquete de firme** (categoría de tráfico/explanada, 6.1-IC)
   y el **terreno**; deja las claves previstas pero **no** implementes esos módulos (eso es PT 5.2+).

**Decisiones a resolver y documentar (antes de mover una línea):**
- **Decisión nº3 — formato de intercambio GIS:** ¿**GeoJSON/Shapefile + IFC 4.3** (dos soportes
  complementarios: IFC para el modelo, GIS para cartografía/cuencas) o **IFC 4.3 georreferenciado puro**?
  Propón y justifica; condiciona el gancho GIS (punto 5) y la Ola 6 (drenaje).
- **Decisión nº2 — empaquetado de obras lineales:** confirma **un plugin único `obras-lineales`** con
  subagentes (trazado/firmes/drenaje/hidráulica), análogo a `instalaciones`. **En este PT no nace ese
  plugin** (nace en PT 5.2): el parser/validación de alineación viven en **`iso19650-openbim`** (capa IFC
  transversal, como el MEP), que es el plugin que **reempaquetas** aquí (→ **v0.5.0**).
- **¿Dónde vive la lectura de georreferencia?** Propón si `IfcMapConversion`/`IfcProjectedCRS` se leen en
  el parser lineal (mínima disrupción) o se promueven a un helper del **núcleo** `ifc_utils` (es
  transversal a todo IFC georreferenciado, pero **tocar el núcleo obliga a re-espejar** en los 3 plugins
  y pasar `verificar_espejo_nucleo.py`). Recomendación por defecto: **en el parser lineal** ahora, y
  promover al núcleo solo cuando una segunda disciplina lo necesite.

**Entregable:**
- `iso19650-openbim/scripts/lineal/ifc_to_model_lineal.py` (consume `ifc_utils`, **no** modifica el
  núcleo) + generador de IFC 4.3 de prueba + validación de alineación/georref, con un **micro-test**
  (continuidad/tangencia de segmentos, PK monótono, georref) y un **caso e2e**
  `Casos-de-uso/caso-LIN-01-eje-carretera` que pase de extremo a extremo (IFC 4.3 → modelo neutro lineal
  → validación CUMPLE), con su README y memoria mínima.
- **Actualizar C1** (§4bis: marcar el parser lineal + validación como implementados; añadir el checklist
  de la vía Alignment) y la **hoja de ruta** (estado de la Ola 5; decisiones nº2/nº3 resueltas; mapa de
  plugins `iso19650-openbim` → v0.5.0).
- **Registrar:** lección en `REPOSITORIO-aprendizaje.md` (+ fila/INC si aplica), entrada SemVer en
  `iso19650-openbim/CHANGELOG.md`, y **subir versión + reempaquetar** `iso19650-openbim` → **v0.5.0**.
- **Puertas de calidad obligatorias** (pega su salida en el cierre):
  `PYTHONPATH=/tmp/pylibs python3 Nucleo-transversal/verificar_empaquetado.py
  iso19650-openbim-v0.5.0.plugin --ref iso19650-openbim-v0.4.3.plugin` (**APTO**, exit 0) **y**
  `python3 Nucleo-transversal/verificar_espejo_nucleo.py --canonico
  motor-calculo-estructural-v0.23.0.plugin iso19650-openbim-v0.5.0.plugin` (**ESPEJOS IDÉNTICOS** — si
  no promoviste nada al núcleo, debe seguir idéntico). `description` ≤ 500; `--allow-shrink` solo para
  encogimientos auditados.

**Notas de método (críticas, confirmadas en PT 4.4/4.5/4.6):** las herramientas de fichero
(Read/Write/Edit) son la **fuente de verdad**; el shell del sandbox sirve copias **truncadas/stale** de
ficheros **pre-existentes** (incluidas las **puertas** `.py`, `plugin.json`, `.md` no editados en el
hilo), pero **los ficheros NUEVOS se leen íntegros** y los `.plugin` (ZIP) **extraen íntegros**. Por
tanto: reconstruye el banco en un **`/tmp` nuevo** extrayendo cada `.plugin` con `unzip`; para una puerta
o fichero pre-existente que necesites ejecutar, **léelo con `Read` (íntegro) y reconstrúyelo en `/tmp`**
(verifica con `ast.parse`). Toolchain Python en `/tmp/pylibs` (**ifcopenshell 0.8.5**, soporta **IFC4X3**)
→ ejecuta con `PYTHONPATH=/tmp/pylibs`; el análisis puede superar ~45 s → ejecuta por partes. Clave de
entidad IFC = `entity.id()` (STEP), **NUNCA** `id()` de Python; el parser casa la **clase exacta**
`el.is_a()`. Declara la **unidad de longitud SI explícita** en el generador (`unit.add_si_unit`
LENGTHUNIT sin prefijo; por defecto pone milímetros). El `.plugin` de la raíz puede estar bloqueado →
**construye el ZIP en `/tmp` y cópialo con `cat > destino`**, con **nombre versionado** (no sobrescribas),
excluyendo `__pycache__`/`node_modules`/`*.pyc`. Empaquetado **acumulativo** desde
`iso19650-openbim-v0.4.3.plugin` (la última íntegra). Todo es **predimensionado, a revisar y firmar por
técnico competente** (Ingeniero de Caminos); NDP marcados `[confirmar AN]`.

**Empieza** leyendo los documentos (sobre todo C1 §4bis) y el núcleo (`scripts/nucleo/ifc_utils.py`),
reconstruyendo el banco en `/tmp`, y **proponiendo: (a) la frontera** —qué entidades de `IfcAlignment`
mapeas y cómo reconstruyes el perfil por PK, qué emite el modelo neutro lineal, dónde vive la lectura de
georreferencia—, **(b) la resolución de las decisiones nº2 y nº3**, y **(c) el plugin que reempaquetas**
(`iso19650-openbim` → v0.5.0) — **antes de mover una sola línea**.
