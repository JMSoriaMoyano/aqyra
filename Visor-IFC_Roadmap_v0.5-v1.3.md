# Visor IFC — Roadmap como herramienta central (v0.5 → v1.3)

**Plugin:** `visor-ifc` (transversal del marketplace "Despacho de Caminos")
**Estado de partida:** v0.4 — web-ifc + Three.js, HTML autocontenido, lanzador Python.
**Fecha del plan:** 22 de junio de 2026
**Sustituye a:** `Visor-IFC_Roadmap_v0.5-v1.0.md` (ampliado tras decidir que el visor es pieza central y las capacidades avanzadas quedan comprometidas).

---

## 0. Decisión de fondo: cambio de motor

Al ser el visor una **pieza central del trabajo diario** y comprometerse las capacidades avanzadas (federación a escala, comparación de versiones, coloreado por resultados de cálculo), el motor actual (web-ifc directo en un único HTML) se queda corto en rendimiento. Por tanto:

- **Se adopta ThatOpen Components (fragments) como motor.** Aporta de serie streaming, federación multi-modelo, cortes, mediciones y BCF, con rendimiento de producción.
- **Se relaja el principio "un solo HTML autocontenido"** → pasa a **aplicación local empaquetada** (bundle estático: `index.html` + assets, abrible en local, sin nube). El lanzador Python actual evoluciona para servir/abrir el bundle.
- **Se conserva el modo ligero por diseño:** los fragments son el formato teselado ligero; IfcOpenShell/ThatOpen convierten `IFC → fragments + propiedades` en el sandbox.

Esta es la única decisión arquitectónica grande del plan; el resto son incrementos sobre esta base.

---

## 1. Principios de diseño (no negociables)

1. **Herramienta transversal**, plugin propio, nunca acoplada al plugin de Estructuras. Sirve a estructuras, instalaciones MEP y obras lineales.
2. **Consume los contratos del núcleo** (C1 modelo neutro/IFC, CN-2 entregables, CN-3 acciones/resultados); no duplica cálculo ni validación.
3. **El visor lee, anota y, desde v1.0, edita datos; nunca modela geometría.** Frontera firme con la autoría (Blender/Bonsai, Revit).
4. **Local y sin nube:** todo el procesamiento ocurre en el equipo / sandbox. Privacidad de los proyectos.
5. **Una mejora por versión, validada y anotada con fecha.** Versiones de dependencias fijadas y compatibles.
6. **Rendimiento fluido como criterio de aceptación** de cada versión.

---

## 2. Fundación (v0.5–v0.6): motor y federación

### v0.5 — Migración a ThatOpen Components (fragments)
**Objetivo:** sustituir el motor y abrir modelos pesados con fluidez.

- Pipeline en sandbox: `IFC → fragments` (geometría) + índice de propiedades/Psets por `GlobalId`.
- Reescritura del visor sobre ThatOpen Components: navegación 3D, selección, propiedades/Psets, árbol espacial, color/visibilidad por clase (paridad funcional con v0.4).
- Empaquetado como bundle local; lanzador Python actualizado.
- **Aceptación:** un modelo grande de referencia navega fluido y mantiene toda la funcionalidad de v0.4.

### v0.6 — Federación multi-disciplina a escala
**Objetivo:** ver y gestionar varias disciplinas a la vez.

- Carga simultánea de varios modelos (estructuras / MEP / lineales) con coordenadas compartidas.
- Panel de modelos: visibilidad, aislar y color **por modelo y disciplina**.
- Encuadre conjunto y por modelo; gestión de origen/georreferencia.
- **Aceptación:** tres modelos de distinta disciplina alineados, con capas conmutables sin pérdida de rendimiento.

> **CERRADA — 22/06/2026. Validada en vivo por http (Chrome).** Entregada en `Estructurando/visor/visor-ifc-v0.6.html`. Un único `FragmentsModels` con tres `load({modelId})`: estructura (13 geom), MEP (5), obra lineal (5), 65 ítems / 23 con geometría, generados co-localizados (mismo WCS + `IfcMapConversion` EPSG:25830 idéntico). Comprobado: render y alineación de las tres disciplinas en la misma escena; panel de Modelos con visibilidad / **aislar** / encuadre por modelo; **color por disciplina** simultáneo (estructura azul, MEP naranja, lineal verde) y por modelo; selección por clic que identifica disciplina+modelo en el panel de propiedades (clave `GlobalId`, sin colisión de `localId` entre modelos); encuadre conjunto y por modelo; sin errores de consola. Generador de modelos: `outputs/gen_federacion.py`. Gotcha nuevo: si el server http sirve la RAÍZ del proyecto, la URL es `/visor/visor-ifc-v0.6.html`.

---

## 3. Inspección (v0.7–v0.8)

### v0.7 — Navegación y filtrado avanzados
- Aislar/ocultar granular por elemento y por nodo del árbol.
- Búsqueda y filtro por propiedad o Pset (p. ej. `FireRating = EI120`).
- Vista por plantas (una cada vez) y cotas de nivel.
- **Aceptación:** filtrar por propiedad y aislar el resultado en un clic.

> **CERRADA — 22/06/2026. Validada en vivo por http (Chrome, puerto 8007).** Entregada en `Estructurando/visor/visor-ifc-v0.7.html` (manifest a v0.7; `servir_visor.bat` abre el puerto 8007). Sobre la federación v0.6 se añaden cinco capacidades: (1) **Buscar/filtrar** toda la federación por texto libre, `category`, `Disciplina`, atributo o `Pset ▸ Propiedad` (igual/contiene), con índice de campos/valores construido en el navegador al cargar — resultados etiquetados por disciplina/modelo y acciones en un clic **Aislar · Colorear · Ocultar**; (2) **visibilidad granular** por elemento (panel de propiedades), por **nodo/subárbol y clase** (botones contextuales ◎ aislar / ⦸ ocultar / ◉ mostrar al pasar el ratón); (3) **Mostrar todo** global (cabecera + tecla G); (4) **vista por plantas con doble modo**: *Por cota* (agrupa los `IfcBuildingStorey` de las 3 disciplinas que comparten nivel) y *Por planta* (cada storey por separado con su modelo), aislando el nivel en un clic; (5) **cotas reales** en árbol y plantas. Comprobado en vivo: filtro de texto "pilar" → 4 resultados (Estructura·COLUMN) → **Aislar** deja solo los 4 pilares con encuadre; *Por cota* → nivel **+0.00 m** agrupa Planta Baja + Instalaciones + Plataforma (14 elem., 3 disciplinas) y lo aísla; acciones contextuales del árbol operativas; "Mostrar todo" restaura; **sin errores de consola**. **Corrección de pipeline (sin romper formato v0.6):** el `IfcImporter` perdía `Elevation` de los `IfcBuildingStorey`; ahora `pipeline.mjs` la recupera del IFC fuente por `GlobalId` y la inyecta en el índice y en los nodos del árbol (regenerados estructura/mep/lineal `.props.json`). Gotcha nuevo: abrir el HTML por **doble clic (`file://`)** falla (`manifest.json: Failed to fetch`) — usar siempre `servir_visor.bat` (http).

### v0.8 — Medición y secciones — **CERRADA 22/06/2026**
- Planos de sección (cortes) interactivos: plano X/Y/Z sobre **toda la federación** vía `renderer.clippingPlanes` (global; corta todos los modelos del `FragmentsModels` compartido), con eje, offset (slider con cota en m), **Invertir** y **Limpiar cortes**.
- Mediciones: **distancia** (polilínea clic-clic, etiqueta por tramo + total `Σ`) y **área** (polígono, Newell; etiqueta `A` + perímetro), tomando el `point` del `raycast` de fragments; etiquetas HTML proyectadas (capa `#labels`), **Terminar** (Enter) y **Limpiar medidas**.
- Lectura de cantidades `Qto_*`: `pipeline.mjs` ampliado para leer `IfcElementQuantity.Quantities` (Length/Area/Volume/Weight/Count) → nuevo campo `quantities` por ítem (formato v0.7 intacto); el panel muestra la sección **CANTIDADES (QTO)** con unidades (m, m², m³).
- **Aceptación cumplida:** validado en vivo por http (8007) sobre federación real `nucleo-lateral` + demo `qto-demo`: corte en Z (lectura −19.98 m), distancia 16.730 m, área 61.188 m²/perímetro 34.581 m, y Qto de `IFCSLAB` (NetArea 36 m², NetVolume 9 m³). Sin errores en consola. Ningún IFC del proyecto traía `IfcElementQuantity`, por lo que la ruta Qto se demuestra con `qto-demo` (cantidades inyectadas sobre `estructura.ifc`).
- **Entregado:** `visor-ifc-v0.8.html`, `pipeline.mjs` (ampliado), `models/qto-demo.{ifc,frag,props.json}`, `manifest.json` v0.8 (carga `nucleo-lateral` + `qto-demo`), `servir_visor.bat` (abre v0.8).

---

## 4. Anotación y datos (v0.9–v1.0)

### v0.9 — Clasificación y BCF — **CERRADA 22/06/2026**
- Color por clasificación Uniclass / GuBIMClass (`IfcClassificationReference`), enlazado con la skill `bsdd-clasificacion`.
- Comentarios e incidencias **BCF**: crear, situar en 3D, listar y exportar/importar BCF.
- **Aceptación:** crear una incidencia y exportarla en BCF reabrible.

> **CERRADA — 22/06/2026. Validada en vivo por http (Chrome, puerto 8007)** sobre la federación `nucleo-lateral` + `qto-demo` + el nuevo `clasif-demo`. Entregada en `Estructurando/visor/visor-ifc-v0.9.html` (manifest a v0.9). Dos bloques:
> **(1) Clasificación.** El `pipeline.mjs` no capturaba clasificaciones (ThatOpen fragments **no indexa** `HasAssociations`, solo `ContainedInStructure`/`IsDefinedBy`); se resolvió **parseando el texto STEP** del IFC (`IfcRelAssociatesClassification → IfcClassificationReference → ReferencedSource`) y mapeando por `GlobalId`, con nuevo campo `items[guid].classifications=[{system,code,name,location}]` (formato v0.8 intacto). Modelo demo `clasif-demo` enriquecido con `bsdd-clasificacion` (Uniclass 2015 real desde la API bsDD: Pr_20_85_08 vigas, Pr_20_85_16 pilares, Pr_20_85_13_32 zapatas, Ss_30_12 forjado; + bSDD-IFC URI + GuBIMClass ilustrativo). En el visor: pestaña **Clasif.** con selector de sistema, leyenda por código (color/cuenta/aislar/ocultar), modo de color **«Por clasificación»** en cabecera (elementos sin clasificar en gris neutro), integración en **Buscar** (`Clasif · <sistema>`) y sección **Clasificación** en la ficha de propiedades (sistema, código, denominación, URI). Comprobado en vivo: leyenda Uniclass de 4 códigos, coloreo del modelo demo, ficha con triple clasificación (bSDD-IFC / Ss_30_12 / EE.30.10).
> **(2) BCF.** Modelo interno de incidencias **3.0-ready**, export **BCF 2.1** conforme (`bcf.version`, `<guid>/markup.bcf`, `viewpoint.bcfv`, `snapshot.png`) con **zip propio** (CRC32, método STORE) e import (STORE + deflate vía `DecompressionStream`). Viewpoint = cámara (posición/dirección/up/fov) + selección por `GlobalId` + planos de sección + **snapshot PNG real** (`preserveDrawingBuffer`). Comprobado: round-trip headless (el `unzip` estándar lee el `.bcfzip`; `markup.bcf`/`viewpoint.bcfv` XML bien formados; PNG binario intacto) **y en vivo** (crear incidencia con snapshot+componente; «Ir a la vista» restaura cámara/selección/visibilidad; **reimportar** un `.bcfzip` estándar recupera la incidencia y su viewpoint). **Sin errores de consola; capacidades v0.5–v0.8 intactas.**
> **Gotchas nuevos:** fragments no expone `HasAssociations` por `getItemsData` → parsear clasificación del STEP; el diálogo nativo de «abrir fichero» pertenece a Chrome (tier *read*) y no es clicable → importar con `file_upload` del Chrome MCP (solo carpetas conectadas) o por arrastre (v1.0); GlobalId puede colisionar si se cargan dos modelos derivados del mismo IFC (aquí `qto-demo`/`clasif-demo`) → la selección BCF por `GlobalId` resuelve al primero. Sample BCF: `visor/import-test.bcfzip`.
>
> **GuBIMClass oficial (22/06/2026).** Sustituidos los códigos ilustrativos por la tabla **GuBIMClass v1.2 ES** aportada por el usuario: Zapatas `20.10.10.20`, Pilares `20.20.10.10`, Jácenas `20.20.20.20`, Forjados `20.20.20.10`. Mapeo reutilizable en `Estructurando/gubimclass-mapping.json`. Fix de `pipeline.mjs`: el parser STEP ahora decodifica los escapes de cadena IFC (`\X2\..\X0\`, `\X\hh`, `\S\c`) — antes "Jácenas" se leía como `J\X2\00E1\X0\cenas`.
>
> **Pulido v0.9.1 (22/06/2026, validado en vivo).** (1) **bSDD-IFC relegado:** la entidad IFC se oculta del selector/leyenda de **Clasif.** y de **Buscar** (queda solo en la ficha del elemento); sistemas «reales» = Uniclass/GuBIMClass (`isRealClassif`/`uiClassifSystems`). (2) **Sincronización del panel Sección al restaurar un viewpoint:** `syncSectionUIFromPlane()` refleja toggle On/Off, eje X/Y/Z y offset del plano BCF (validado: On · Z · −19.98 m). (3) **Gestión de incidencias BCF:** etiquetas (`Labels`), `AssignedTo`, `DueDate`, **cambio de estado** y **añadir comentarios** desde la tarjeta; emitidos/leídos en `markup.bcf`. (4) **Desambiguación de selección por modelo:** el componente BCF lleva `AuthoringToolId=modelId`; al restaurar resuelve al modelo correcto aun con GlobalId colisionando (validado: restaura `clasif-demo`, no `qto-demo`). Sin errores de consola.

### v1.0 — Edición de datos + entregable estable
- Edición de **datos** del IFC (propiedades, Psets, clasificaciones) y exportación del IFC modificado.
- Integración con `ifc-validate`: control de calidad antes de exportar.
- **Abrir IFC directamente (ingesta in-browser):** arrastrar/soltar un `.ifc`, convertirlo en el navegador con el mismo `IfcImporter` (web-ifc WASM) y reusar la lógica de `pipeline.mjs` (incluida la recuperación de `Elevation`), con **cacheado automático del `.frag`+`.props.json` a disco** para reaperturas instantáneas. (Decidido 22/06/2026: técnicamente factible ya como v0.7.1 drag&drop, pero se consolida aquí porque la app local empaquetada lleva web-ifc embebido —offline— y permite escribir el caché junto al IFC.)
- Documentación de uso y empaquetado estable. Primera versión "de despacho".
- **Aceptación:** editar un Pset, validar y exportar un IFC correcto que reabre en otra herramienta; abrir un `.ifc` por arrastre sin paso de conversión externo.
- **Frontera:** no mueve ni crea geometría.

> **CERRADA — 22/06/2026 (build b6). Validada en vivo por el usuario; entregada como app de escritorio Electron instalable.** Entregada en `Estructurando/visor/visor-ifc-v1.0.html`. Tres bloques:
> **(1) Ingesta por arrastre (in-browser).** Zona drop a nivel de ventana + botón «Abrir IFC…». El `.ifc` se convierte en el navegador con `FRAGS.IfcImporter` (web-ifc WASM) y el índice `props.json` se reconstruye con las funciones de `pipeline.mjs` **portadas al navegador** (`SingleThreadedFragmentsModel` síncrono; storey `Elevation`, clasificación del STEP, `ifcStrUnescape`) y se añade a la federación viva. Conserva los bytes IFC para edición/export. Botón «⬇ caché» (File System Access o descarga del `.frag`+`.props.json`). **Validado en vivo:** `clasif-demo.ifc` → IFC→fragments ~1,2 s, 29 ítems, 13 con geometría, 13 clasificados, render confirmado por muestreo de píxeles, 0 errores de consola; regresión en Node del índice portado idéntica a `pipeline.mjs` (13/13 cantidades, 13/13 clasificaciones).
> **(2) Edición de DATOS + export (web-ifc IfcAPI).** Panel «✎ Editar datos» (solo en modelos con IFC fuente): editar `Name`, editar valores de Pset (texto/número, mutando `NominalValue.value`), añadir propiedad (clonar `IfcPropertySingleValue`, `Handle{type:5}` a `HasProperties`). Export = `SaveModel` → `<id>-editado.ifc`. **Validado en vivo por la ruta real de la página** (`import('web-ifc')` vía importmap → glue de navegador de jsDelivr): editar Pset (texto+real)+`Name`+añadir-propiedad → `SaveModel` (IFC `ISO-10303-21` válido) → reapertura **conserva los cambios**. Falta solo accionar los botones DOM en vivo (la pestaña del agente queda de fondo y Chrome congela el rAF de la selección 3D; las funciones que invocan ya están probadas).
> **(3) QA ligera + delegación.** Botón «Validar (QA)»: Psets de proyecto, `Name`, clasificación presente, valores vacíos (puerta de aviso, no bloquea). Validación completa delegada a la skill `ifc-validate` sobre el IFC exportado.
> **Decisiones de inicio (confirmadas por el usuario):** motor de escritura = **web-ifc IfcAPI**; secuencia = ingesta→edición; QA = JS ligero + delegar; empaquetado = mínimo viable (CDN 1ª vez + caché FSA/descarga), **offline pleno aplazado a v1.0.x**.
> **Gotcha decisivo (nuevo):** el build de **web-ifc de esm.sh es de entorno Node** (su glue de Emscripten lanza «not compiled for this environment» en navegador). Solución: **externalizar web-ifc** del bundle de fragments (`?external=three,web-ifc`) y mapear `"web-ifc"` en el importmap al **glue de navegador de jsDelivr** (`web-ifc-api.js`). Otros: la regla CSS `#canvas-host{position:relative}` pisaba el `position:absolute;inset:0` original → lienzo a altura 0 (eliminada); las pestañas del Chrome MCP quedan ocultas/throttled y congelan rAF (la ingesta/edición web-ifc no dependen de rAF, la selección sí); `<meta no-store>` para evitar servir copias cacheadas pre-fix; build b3 sello visible en cabecera.
>
> **Editor confirmado por el usuario en vivo (build b4):** seleccionar elemento de un modelo arrastrado → «✎ Editar datos» → cambiar valor → exportar, OK. **build b6:** arranca **vacío** (`manifest.json` todos `load:false`) + botón **✕ Quitar** por modelo (`removeModel`: scene.remove + dispose + `fragments.disposeModel` + `CloseModel` web-ifc + rebuild de paneles) + estado vacío.
>
> **Empaquetado entregado = app de escritorio Electron (sin servidor externo).** Tras caerse repetidamente el servidor `python -m http.server 8007` (sospecha: antivirus matando python), el usuario eligió **Electron**. En `Estructurando/visor/desktop/`: `main.js` (servidor http **dentro del proceso Electron**, 127.0.0.1:8731 con fallback; `ROOT=app/` empaquetado o `../` en dev; BrowserWindow sin menú; `shell.openExternal` para URIs; bloquea path traversal — VALIDADO en Node), `package.json` (`electron-builder --win nsis portable`). **Método de instalación CONFIRMADO funcionando:** `desktop/Construir instalador (1 vez).bat` **se auto-eleva a admin (UAC)** — imprescindible porque electron-builder crea symlinks al extraer winCodeSign (`CSC_IDENTITY_AUTO_DISCOVERY=false`) — y genera `dist/Visor IFC Setup 1.0.0.exe` (instalador NSIS, acceso directo «Visor IFC») + `Visor IFC portable.exe`. El usuario lo generó e instaló OK; repartible a compañeros. Gotchas: icono vía `.vbs` NO abre (equipo corporativo bloquea Windows Script Host) → el instalador es la vía buena; SmartScreen avisa la 1ª vez (exe sin firmar). **PWA (build b5) descartada como empaquetado** (su SW dejaba pegada la versión y seguía necesitando servidor); el visor mantiene el `sw.js`/manifest pero la app Electron no los necesita.
>
> **Pendiente para v1.0.x:** offline pleno (descargar three/fragments/web-ifc a `app/vendor/` y reescribir el importmap a rutas locales → cero dependencia de CDN, clave para tablet en obra); modo «solo datos» opcional; firma de código para quitar SmartScreen.

---

## 5. Capacidades avanzadas comprometidas (v1.1–v1.3)

### v1.1 — Comparación de versiones
**Objetivo:** ver qué cambió entre dos entregas de un modelo.

- Diff de **datos** (propiedades/Psets) y de **geometría** (elementos añadidos / eliminados / desplazados) por `GlobalId`.
- Vista lado a lado o superpuesta con código de color (nuevo/modificado/eliminado).
- Informe de cambios exportable; enlace con el control de entregas del CDE (`cde-audit`).
- **Aceptación:** comparar dos versiones de un modelo y listar/colorear los cambios.

> **ENTREGADA — 23/06/2026 (build b7). Validación lógica determinista APTA; pendiente validación en vivo del usuario en la app Electron.** Entregada en `Estructurando/visor/visor-ifc-v1.1.html` (la app de escritorio ya apunta a v1.1). Decisiones de inicio del usuario: emparejado por **panel «Comparar»** sobre modelos cargados; diff de geometría por **centroide/caja con umbral**; vista **lado a lado**; informe **tabla + CSV/JSON + volcado a incidencias BCF**; clave de emparejado = `GlobalId`. Nueva pestaña **Comparar**: selección de A (base) y B (nueva) de entre los modelos del manifest/cargados (carga bajo demanda; botón «Caso de prueba» carga cmp-A/cmp-B), umbral de desplazamiento configurable (0,05 m por defecto).
> **(1) Diff de DATOS por `GlobalId`** (recorre `items` de A y B en memoria; aplana atributos/Psets/cantidades/clasificaciones; filtra a elementos con GlobalId real, ignorando las `IfcPropertySingleValue` keyed `local:`): clasifica **Nuevo / Eliminado / Modificado / Sin cambios** con detalle antes→después por propiedad.
> **(2) Diff de GEOMETRÍA por `GlobalId`**: centro de `M.object.getBoxes([localId])` por elemento en A y B; «Desplazado» si la distancia supera el umbral (con el vector centroide antes→después y Δ en el informe).
> **(3) Visualización**: coloreado por estado sobre la escena compartida (nuevo verde, eliminado rojo, modificado naranja, desplazado azul, sin cambios gris) + **vista lado a lado** (doble render con `setScissor`/`setViewport` compartiendo cámara: A a la izquierda, B a la derecha; oculta el resto de la federación mientras dura) + conmutar visibilidad A/B + «Quitar colores».
> **(4) Informe**: resumen con chips-filtro por estado, lista clic-a-encuadrar (reusa `selectItem`), export **CSV** (BOM + escape) y **JSON** reabribles, y **volcado a incidencias BCF 2.1** (una por cambio, reusando `captureViewpoint`/`TOPICS`/`exportBcf` de v0.9; selección por `{ifcGuid, model:B}`).
> **Validación determinista (Node, sin navegador):** sobre el caso de prueba cmp-A/cmp-B, el diff de datos del **código ya integrado** (extraído del HTML y ejecutado en vm) reproduce la verdad de terreno: 1 nuevo (Viga_3), 1 eliminado (Viga_4), 1 modificado (Forjado_cubierta: `Canto_m` 0.25→0.30 y `Material` C30/37→C35/45); el diff de geometría por centroide detecta **solo** Pilar_2 desplazado exactamente **2,000 m**. Módulo del HTML pasa `node --check`; copia al mount verificada por `md5sum`.
> **Empaquetado:** `desktop/main.js` carga `visor-ifc-v1.1.html`; `package.json` a **1.1.0** (artefacto `Visor IFC Setup 1.1.0.exe`); el `.bat` de construcción copia la v1.1 a `app/`. **Reconstruir el instalador con `Construir instalador (1 vez).bat`** tras validar en vivo.
> **Pendiente:** validación en vivo del usuario (coloreado y lado a lado en 3D — no validables en la pestaña throttled del agente, gotcha rAF) y reconstrucción del instalador.

### v1.2 — Coloreado por resultados de cálculo
**Objetivo:** unir el visor con los motores de cálculo del ecosistema.

- Lectura de resultados vía contrato del núcleo (CN-3): esfuerzos/armado/ratios de Estructuras; presiones/caudales/DN de Instalaciones.
- Mapa de color por resultado sobre el modelo (degradado y leyenda), por elemento.
- Filtro por umbral (p. ej. resaltar elementos con ratio > 1,0 o presión < requerida).
- **Aceptación:** colorear un modelo estructural por ratio de aprovechamiento y un modelo MEP por presión disponible.

> **ENTREGADA — 23/06/2026 (build b8). Validación lógica determinista APTA; pendiente validación en vivo del usuario.** Entregada en `Estructurando/visor/visor-ifc-v1.2.html` (la app de escritorio ya apunta a v1.2; `package.json` 1.2.0). Decisiones del usuario: leer resultados **del IFC y además importar JSON** (contrato CN-3 externo), escala **gradiente continuo + umbral**, demos **estructural y MEP**. Nueva pestaña **Resultados**: selector de **magnitud** (cualquier propiedad numérica de Psets/cantidades de la federación; las `*Resultado*` se ordenan primero), **gradiente** verde→amarillo→rojo con **leyenda** (barra + min/max + marca de umbral + nº de críticos), **umbral** configurable con **invertir escala** (bajo = crítico, p.ej. presión) y **aislar críticos**, e **importar JSON** de resultados (`{results:{GlobalId:{magnitud:valor}}}`) que casa por GlobalId y añade magnitudes `… (JSON)`. Lee directamente el índice `props.json` (sin tocar el pipeline); colorea por `setColor` agrupando en 21 buckets por modelo.
> **Datos demo (no requieren motor de cálculo):** `models/res-estr` (estructura: `Pset_Estructurando_Resultado.Aprovechamiento`, 13 elem, min 0,33 / max 1,12 → **2 críticos ≥1,0**: Pilar_3 1,12 y Viga_4 1,05) y `models/res-mep` (MEP: `Pset_Estructurando_ResultadoRed.Presion_bar/Velocidad_m_s/DN_mm`, 5 elem; presión invertida umbral 2,0 → **2 críticos**), más `models/res-estr-resultados-sismo.json` para probar la importación JSON (Aprov_sismo). Ambos en el manifest con `load:false`; geometría reutilizada de clasif-demo/mep (no cargar la pareja origen simultáneamente).
> **Validación determinista (Node):** el `resScan` ya integrado (extraído del HTML, ejecutado en vm con un LOADED simulado) detecta las 6 magnitudes con las `*Resultado*` primero y los 2 críticos ≥1,0; módulo pasa `node --check`; copia al mount verificada por `md5sum`.
> **VALIDADA EN VIVO 23/06/2026 (build b8→b9):** demo en la app de escritorio — coloreo de `res-estr` por Aprovechamiento (gradiente verde→rojo, leyenda 0,33→1,12), umbral 1,0 → 2 sobre umbral, «aislar críticos» dejó solo Pilar_3 y Viga_4; selector con las 6 magnitudes. **Pulido v1.2.1 (build b9):** (1) pestañas en dos filas (`flex-wrap`) — con 9 pestañas «Resultados» quedaba recortada/tapada por la tarjeta de Sección; (2) **cargador de modelos del manifest** en el panel Modelos (los `load:false` ya no dependen de Comparar). Validado en vivo. **Pendiente:** reconstruir el instalador para llevar la v1.2 a la app instalada.

### v1.3 — Colaboración y flujo de trabajo
**Objetivo:** integrar el visor en el día a día del despacho.

- Estados de revisión y aprobación sobre las incidencias BCF.
- Vínculo con el CDE (Aqyra/ISO 19650): abrir el modelo publicado, registrar estado S0–S7.
- Vistas guardadas y "puntos de vista" compartibles entre el equipo.
- **Aceptación:** abrir un entregable del CDE, anotar, cambiar de estado y compartir una vista.

---

## 6. Resumen de secuencia

| Versión | Tema | Hito |
|--------|------|------|
| v0.5 | Motor ThatOpen (fragments) | Modelos pesados fluidos, paridad v0.4 |
| v0.6 | Federación multi-disciplina | Varios modelos a la vez — **CERRADA 22/06/2026** |
| v0.7 | Navegación / filtrado | Aislar y buscar por propiedad — **CERRADA 22/06/2026** |
| v0.8 | Medición y secciones | Cortes y medidas — **CERRADA 22/06/2026** |
| v0.9 | Clasificación + BCF | Anotación e incidencias |
| v1.0 | Edición de datos + ingesta por arrastre | Exportar IFC editado (de despacho) — **ENTREGADA 22/06/2026 (build b3)** |
| v1.1 | Comparación de versiones | Diff datos + geometría |
| v1.2 | Coloreado por resultados | Unión con motores de cálculo (CN-3) |
| v1.3 | Colaboración / CDE | Flujo ISO 19650 |

---

## 7. Criterios de evolución

- **Prioridad por uso real en proyectos vivos.** Las versiones de fundación (v0.5–v0.6) son habilitadoras y van primero; el resto se reordena según necesidad.
- **Una mejora por versión**, validada al abrir el visor; si no se puede probar el render aquí, se entrega "a validar" y se itera con el feedback (consola).
- **Compatibilidad de dependencias fijada** (ThatOpen Components / three / web-ifc).
- **Cada versión se anota** en el `roadmap.md` de la skill con fecha y resultado.

---

## 8. Riesgos y notas

- **Migración a ThatOpen (v0.5)** es el mayor esfuerzo y bloquea al resto; conviene una prueba de concepto temprana con un modelo real antes de comprometer la reescritura completa.
- **Bundle vs. único HTML:** se pierde la portabilidad de "un archivo", a cambio de rendimiento de producción. El lanzador Python mantiene el doble clic sobre `.ifc`.
- **Contrato CN-3 (resultados):** v1.2 depende de que los motores de cálculo expongan resultados por `GlobalId` de forma estable; coordinar con la evolución del núcleo.

---

## 9. Dónde se desarrolla

Dentro del **ecosistema Estructurando** (misma memoria, mismo núcleo, mismo marketplace) como **plugin independiente `visor-ifc`**. Consume C1, CN-2 y CN-3; se enlaza con `bsdd-clasificacion`, `ifc-validate` y `cde-audit` del plugin `iso19650-openbim`.
