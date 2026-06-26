# INICIO de hilo — Visor IFC v1.1: comparación de versiones

## Rol y contexto

Actúa como ingeniero BIM/desarrollo del ecosistema **Estructurando** (supervisión de Ingeniero de Caminos). Trabajamos el plugin transversal `visor-ifc`, pieza central del trabajo diario, que sirve a las tres disciplinas (estructuras, instalaciones MEP, obras lineales). Consume los contratos del núcleo (C1 modelo neutro/IFC, C3 entregables, C4 resultados) y se enlaza con `bsdd-clasificacion`, `ifc-validate` y `cde-audit` de `iso19650-openbim`. **Frontera firme: el visor lee, anota y edita DATOS; nunca modela geometría.**

## Motor y empaquetado (decisión consolidada)

- **Motor ThatOpen Components / fragments** (geometría teselada + streaming; es el modo "ligero" único, no hay modo "pesado").
- **Empaquetado entregado = app de escritorio Electron, sin servidor externo.** El visor (HTML) corre dentro de una ventana Electron que levanta un **servidor http estático DENTRO del propio proceso** (`127.0.0.1:8731` con fallback). No hay Python ni proceso aparte que un antivirus pueda cerrar. Se decidió tras caerse repetidamente el `python -m http.server 8007` (sospecha: antivirus). Todo en `Estructurando/visor/desktop/`.

## Stack y versiones fijadas (compatibles, NO cambiar de forma aislada)

* `@thatopen/fragments@3.4.5`, `web-ifc@0.0.77`, `three@0.184.0` (peer fragments: three ≥0.182).
* Worker de fragments: blob desde `https://cdn.jsdelivr.net/npm/@thatopen/fragments@3.4.5/dist/Worker/worker.mjs`.
* Importmap mapea `three`, `three/` y `@thatopen/fragments` (esm.sh, `?external=three,web-ifc`) y **`web-ifc` → `https://cdn.jsdelivr.net/npm/web-ifc@0.0.77/web-ifc-api.js`** (glue de NAVEGADOR; el de esm.sh es de Node y NO arranca — ver gotchas).
* App de escritorio: `electron ^31.7.7` + `electron-builder ^24.13.3` (target `nsis` + `portable`).

## Estado de partida: v1.0 CERRADA (build b6) y validada en vivo por el usuario

Entregado en `Estructurando/visor/`:

```
visor/
  visor-ifc-v1.0.html        Visor actual (build b6; entrada de la app de escritorio)
  visor-ifc-v0.9.html … v0.5 versiones previas conservadas
  pipeline.mjs               Conversor IFC -> fragments + índice (Node); su lógica está PORTADA al navegador dentro del HTML
  sw.js / visor.webmanifest  PWA (la app Electron NO los necesita; se conservan)
  icons/                     Iconos (192/512/maskable/180 + visor.ico)
  servir_visor.bat / Abrir Visor IFC.bat / .vbs   Lanzadores http (heredados; el bueno es la app Electron)
  models/
    manifest.json            TODOS los modelos a "load": false  -> el visor ARRANCA VACÍO
    nucleo-lateral / qto-demo / clasif-demo / estructura / mep / lineal / caso-R4 / red-pci / caso-15  (.frag/.props.json)
    cmp-A.{ifc,frag,props.json} / cmp-B.{ifc,frag,props.json}   CASO DE PRUEBA de dos versiones (ya preparado)
    cmp-CASO.md              verdad de terreno del diff A->B (qué cambió, verificado)
  desktop/                   APP DE ESCRITORIO ELECTRON
    main.js                  servidor http en-proceso (127.0.0.1) + BrowserWindow; ROOT=app/ (empaquetado) o ../ (dev)
    package.json             electron + electron-builder (nsis+portable)
    assets/icon.ico
    Construir instalador (1 vez).bat   AUTO-ELEVA a admin (UAC) + npm install + electron-builder -> dist\Visor IFC Setup 1.0.0.exe + portable
    Probar sin construir.bat           npm start (Electron en modo dev, carga el visor de ../)
    LEEME-desktop.md
```

**Cómo se instala (CONFIRMADO funcionando — no reinventarlo):**
1. `desktop/Construir instalador (1 vez).bat` → acepta el **UAC (admin)** → genera `dist\Visor IFC Setup 1.0.0.exe` (instalador NSIS, crea acceso directo «Visor IFC») y `Visor IFC portable.exe`.
2. Ejecutar el `Setup.exe` → instala y crea el acceso directo que abre la app. **Repartible a compañeros.**
3. Para iterar en desarrollo: editar `visor/visor-ifc-v1.0.html` y abrir `desktop/Probar sin construir.bat` (npm start; carga el HTML de `../` sin reconstruir). Al terminar la feature, **reconstruir el instalador**.

**Lo que ya hace la v1.0 (todo a mantener intacto):**
- **Ingesta por arrastre in-browser**: soltar un `.ifc` (o «Abrir IFC…») → `FRAGS.IfcImporter` (web-ifc WASM) lo convierte y el índice se reconstruye con las funciones de `pipeline.mjs` portadas (`SingleThreadedFragmentsModel` síncrono; `Elevation` de plantas, clasificación del STEP, `ifcStrUnescape`). Conserva los bytes IFC. Botón «⬇ caché».
- **Edición de DATOS + export** (web-ifc IfcAPI): «✎ Editar datos» en modelos con IFC fuente → editar `Name`, valores de Pset (texto/número, mutando `NominalValue.value`), añadir propiedad (clonar `IfcPropertySingleValue` + `Handle{type:5}`); export = `SaveModel` → `<id>-editado.ifc` reabrible. QA ligera (puerta de aviso) + delegación a `ifc-validate`.
- **Arranque vacío** + botón **✕ Quitar** por modelo (`removeModel`).
- Heredado v0.6–v0.9.1: federación multi-disciplina; navegación/filtrado (texto, clase, atributo, `Pset ▸ Prop`); aislar/ocultar por elemento/nodo/clase; vista por plantas (cota/planta); sección X/Y/Z global; medición distancia/área; cantidades `Qto_*`; color/leyenda/filtro por clasificación Uniclass/GuBIMClass; incidencias **BCF 2.1** (crear con viewpoint+snapshot, comentar, exportar/importar `.bcfzip`).

## Formato del índice `props.json` (por modelo)

`items{guid→{localId,category,name,attributes,psets,quantities?,classifications?}}`, `localIdToGuid`, `geometryClasses`, `geometryLocalIds`, `countByClass`, `tree` (storeys con `elevation`), `stats`. Los campos `quantities` y `classifications` aparecen solo si el ítem los tiene. **Clave de identidad entre versiones = `GlobalId`.**

## Gotchas confirmados (NO repetir)

1. **web-ifc de esm.sh es build de Node** → «not compiled for this environment» en navegador (tanto `IfcImporter` como `IfcAPI.Init()`). Solución: externalizar web-ifc (`?external=three,web-ifc`) + mapear `"web-ifc"` en el importmap a `cdn.jsdelivr.net/npm/web-ifc@0.0.77/web-ifc-api.js` (glue de navegador). `SetWasmPath('https://cdn.jsdelivr.net/npm/web-ifc@0.0.77/', true)`.
2. **CSS**: NO añadir reglas que pisen `#canvas-host{position:absolute;inset:0}` (un `position:relative` lo dejó a altura 0 = lienzo en blanco).
3. **Editar valor de Pset** = mutar `prop.NominalValue.value` (texto y real). NO reemplazar el objeto tipado (rompe `SaveModel` en `toWireType`). **Añadir** propiedad = clonar (`JSON.parse(JSON.stringify(...))`) una `IfcPropertySingleValue` existente, `GetMaxExpressID+1`, fijar `Name`/`NominalValue` planos, `WriteLine`, y empujar `Handle{type:5,value:newId}` a `HasProperties` del Pset.
4. **fragments NO indexa `HasAssociations`** (clasificación) ni reescribe IFC: la clasificación se parsea del texto STEP; la escritura de datos va por **web-ifc**, no por fragments.
5. **getSpatialStructure quirk**: nodos `category`+`localId:null` son GRUPOS de clase; los hijos wrapper son los elementos (normalizado en el pipeline).
6. **API async/sync**: en `FragmentsModels` (navegador) los getters son promesas; en `SingleThreadedFragmentsModel` los síncronos. Cerrar Node con `process.exit(0)`.
7. **Servidor http externo (python) inestable** (se caía repetidamente; sospecha antivirus) → por eso el empaquetado es **Electron con servidor en-proceso**. No volver al python http.server como solución de despacho.
8. **electron-builder** necesita crear **symlinks** al extraer `winCodeSign` → falla sin admin («El cliente no dispone de un privilegio requerido»). Solución confirmada: el `.bat` se **auto-eleva a admin (UAC)** + `set CSC_IDENTITY_AUTO_DISCOVERY=false`. (Alternativa: Modo de desarrollador de Windows.)
9. **Equipo corporativo bloquea Windows Script Host (`.vbs`)** → los lanzadores `.vbs` no abren. El **instalador NSIS** crea un acceso directo que SÍ funciona.
10. **Service Worker (PWA) deja pegada la versión** (un build nuevo no se ve hasta que el SW se actualiza): en desarrollo, desregistrar SW + borrar cachés o subir `CACHE` en `sw.js`. La app Electron evita esto (no usa SW).
11. **Entorno del agente**: las pestañas que controla el Chrome MCP quedan ocultas/throttled → Chrome **congela el rAF** y la selección 3D (`highlight`) se cuelga (CDP timeout); la ingesta y la edición web-ifc NO dependen de rAF y sí funcionan en pestaña oculta → validar lógicas por la **ruta real** (p. ej. `import('web-ifc')`) en vez de los clics. Servir/validar en vivo lo hace el usuario.
12. **Montaje (mount)**: Edit/Write/`cp` grandes dejan truncada la vista de bash (no la del usuario). Patrón fiable: autorar en `/tmp/visorbuildN`, validar (`node --check` del módulo extraído, anclas + aserciones en un build_*.py), copiar y verificar `md5sum` src==dest. Para borrar en el mount: `allow_cowork_file_delete` primero.

## Objetivo de ESTE hilo: v1.1 — Comparación de versiones

Sobre la v1.0, permitir **ver qué cambió entre dos entregas (versiones) de un mismo modelo**, sin tocar geometría:

1. **Cargar dos versiones** del modelo (A = base, B = nueva) — cada una por su `.frag`+`.props.json` o por ingesta de dos IFC — y emparejarlas para comparar.
2. **Diff de DATOS por `GlobalId`**: por elemento, clasificar en **Nuevo** (en B, no en A), **Eliminado** (en A, no en B), **Modificado** (en ambos pero difieren atributos/Psets/clasificaciones) o **Sin cambios**; con el detalle de qué propiedad cambió (antes → después).
3. **Diff de GEOMETRÍA por `GlobalId`**: detectar elementos **desplazados** (comparando centroide/caja de `getBoxes` por encima de un umbral) además de añadidos/eliminados.
4. **Visualización**: colorear por categoría de cambio (nuevo/eliminado/modificado/desplazado/sin cambios) en vista superpuesta (y/o lado a lado); conmutar visibilidad A/B.
5. **Informe de cambios exportable** (tabla en panel + export CSV/JSON; opción de volcar cambios como incidencias BCF); enlace informativo con el control de entregas del CDE (`cde-audit`).

## Criterios de aceptación

* Cargar dos versiones de un modelo, ejecutar la comparación y obtener la **lista de cambios** (añadidos/eliminados/modificados/desplazados) y el **coloreado** correspondiente en 3D, en un clic.
* El diff de datos por `GlobalId` detecta correctamente un Pset/atributo modificado (antes→después) sobre un caso de prueba con dos versiones controladas.
* Exportar el informe de cambios (CSV/JSON) reabrible fuera del visor.
* Sin pérdida de rendimiento ni errores de consola; capacidades v0.5–v1.0 intactas; frontera "datos sí, geometría no" (la comparación LEE geometría para el diff, no la modifica).
* Entregado dentro de la app de escritorio Electron (rehacer el instalador con la feature).

## Retos técnicos clave (anticipar al planificar)

* **Emparejado de versiones**: cómo designa el usuario A vs B (panel «Comparar» que elige dos modelos cargados). Mismo `GlobalId` en A y B = mismo elemento (es el supuesto de "dos versiones del mismo modelo"); el `localId` difiere por modelo → indexar por `GlobalId`.
* **Diff de datos**: recorrer `items` de A y B (ya en memoria), comparar `attributes`/`psets`/`quantities`/`classifications`; producir por elemento `{estado, cambios:[{ruta, antes, despues}]}`. Cuidado con orden/normalización de valores.
* **Diff de geometría**: obtener centroide/caja por `GlobalId` con `M.object.getBoxes([localId])` (async) en A y B; "desplazado" si la distancia entre centros supera un umbral configurable. Diff de malla completa = fuera de alcance (proxy por caja/centroide).
* **Coloreado y visibilidad** por categoría sobre la escena compartida (`setColor`/`highlight` por modelo); conmutar A/B y filtrar por estado.
* **Rendimiento** para modelos grandes (miles de elementos): el diff de datos es barato; el de geometría implica N llamadas async a `getBoxes` → agrupar/await en lote.
* **Colisión de `GlobalId`** entre A y B: aquí es deseada (mismo elemento). Pero ojo a cargar A y B en la misma federación (la selección por `GlobalId` puede resolver al primero) → marcar cada modelo como versión y resolver por `{modelId, GlobalId}`.
* **Empaquetado**: tras la feature, reconstruir el instalador (`Construir instalador (1 vez).bat`). Recordar bumpear el **build bN** en la cabecera del HTML para confirmar versión cargada.

## Decisiones a tomar al inicio (con recomendación)

1. **Emparejado A/B**: ¿panel «Comparar» que selecciona dos modelos ya cargados (recomendado), o un flujo «abrir base + comparar con…» por arrastre?
2. **Profundidad del diff de geometría**: ¿centroide/caja por `GlobalId` con umbral (recomendado, factible) o solo presencia (añadido/eliminado) en v1.1 y desplazamiento en v1.1.x?
3. **Visualización**: ¿superpuesta con colores de diff (recomendado) o lado a lado con doble vista (más trabajo, a v1.1.x)?
4. **Clave de emparejado**: ¿`GlobalId` (recomendado, contrato del núcleo) y dejar el emparejado difuso de elementos renombrados para más adelante?
5. **Salida del informe**: ¿tabla en panel + export **CSV/JSON** (recomendado) y/o generar **incidencias BCF** por cambio?

## Decisiones ya tomadas (no reabrir salvo que el usuario lo pida)

* Edición/lectura de DATOS, nunca geometría (frontera firme). La comparación lee geometría para el diff; no la altera.
* Motor fragments para geometría; datos por web-ifc/STEP.
* **Empaquetado = app de escritorio Electron con servidor en-proceso**; instalación por `Construir instalador (1 vez).bat` (auto-eleva UAC) → `Setup.exe`. No volver al servidor python externo.
* GuBIMClass: tabla oficial v1.2 (`gubimclass-mapping.json` en la raíz); ampliar, no inventar.
* Pendiente de v1.0.x (no es objeto de v1.1 salvo que se priorice): **offline pleno** (vendor local de three/fragments/web-ifc + importmap a rutas locales, clave para tablet en obra), modo «solo datos», firma de código.

## Archivos de referencia (raíz del proyecto)

* `Visor-IFC_Roadmap_v0.5-v1.3.md` — plan de versiones (v1.0 CERRADA en §4; v1.1 en §5).
* `Estructurando/visor/` — bundle v1.0 funcionando; `desktop/` = app Electron + instalador.
* `gubimclass-mapping.json` — mapeo IfcClass → GuBIMClass v1.2 oficial.
* Memorias `[[estructurando-visor-v1.0-edicion-ingesta]]` (incluye método de instalación Electron, build b6, todos los gotchas), `[[estructurando-visor-v0.9-clasificacion-bcf]]`, `[[estructurando-visor-v0.8-medicion-seccion]]`, `[[estructurando-visor-v0.7-navegacion]]`, `[[estructurando-visor-v0.6-federacion]]`, `[[estructurando-visor-v0.5-pipeline]]`, `[[visor-ifc-roadmap]]`.
* Skills enlazables: `iso19650-openbim:cde-audit` (entregas/estados S0–S7), `iso19650-openbim:ifc-validate`, `iso19650-openbim:bsdd-clasificacion`.

## Caso de prueba (YA PREPARADO — no hay que generarlo)

Dejado listo en este hilo, en `Estructurando/visor/models/` (detalle en `models/cmp-CASO.md`):

- **cmp-A** (`cmp-A.{ifc,frag,props.json}`) — versión base, **sin Viga_3**.
- **cmp-B** (`cmp-B.{ifc,frag,props.json}`) — **sin Viga_4**, **Pilar_2 desplazado +2 m en X**, **Pset del forjado modificado**.
- En el `manifest.json` con `"load": false` (se cargan a propósito para comparar). 28 ítems / 12 con geometría cada una; comparten `GlobalId`.

**Verdad de terreno del diff A → B (verificada en Node):**

| Estado | Elemento | GlobalId | Detalle |
|--------|----------|----------|---------|
| Nuevo | Viga_3 | `1f_5YTfGjBdgzh32$3k$QP` | solo en B |
| Eliminado | Viga_4 | `1pbVB1idHDGQ5Db8F5_NVy` | solo en A |
| Modificado | Forjado_cubierta (IfcSlab) | `0NOtbTXaHB1vP4gniGSf4w` | `Canto_m` 0.25→0.30 ; `Material` 'C30/37'→'C35/45' |
| Desplazado | Pilar_2 (IfcColumn) | `0A7IMBbTD91PrLqjhr$r0e` | placement +2 m X; solo visible por geometría (`getBoxes`), no en `props.json` |
| Sin cambios | resto | — | idénticos |

Con esto, el diff de datos se valida por `props.json` (regresión en Node, ya comprobada) y el de geometría por el `.frag` (desplazamiento de Pilar_2).

## Primer paso propuesto

1. Confirmar las decisiones de inicio (emparejado A/B, profundidad del diff de geometría, visualización, clave, salida del informe).
2. **PoC del diff de datos por `GlobalId`** sobre cmp-A/cmp-B (Nuevo/Eliminado/Modificado con detalle antes→después), contrastándolo con la verdad de terreno de arriba.
3. **PoC del diff de geometría** (centroide/caja por `GlobalId` con `getBoxes`, umbral de desplazamiento) → debe detectar Pilar_2 desplazado y nada más.
4. Integrar en el visor: panel «Comparar» (elegir A base y B nueva), coloreado por estado (nuevo/eliminado/modificado/desplazado/sin cambios), informe exportable (CSV/JSON); bumpear **build bN** en la cabecera del HTML.
5. Validar en vivo con el usuario (app Electron, vía `Probar sin construir.bat`); **reconstruir el instalador** (`Construir instalador (1 vez).bat`); marcar v1.1 en el roadmap con fecha y resultado; actualizar memoria.
