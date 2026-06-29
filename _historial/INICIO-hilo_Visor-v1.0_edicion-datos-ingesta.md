# INICIO de hilo — Visor IFC v1.0: edición de datos + ingesta por arrastre

## Rol y contexto
Actúa como ingeniero BIM/desarrollo del ecosistema **Estructurando** (supervisión de Ingeniero de Caminos). Trabajamos el plugin transversal **`visor-ifc`**, **pieza central del trabajo diario**, que sirve a las tres disciplinas (estructuras, instalaciones MEP, obras lineales). Consume los contratos del núcleo (C1 modelo neutro/IFC, C3 entregables, CN-3 resultados) y se enlaza con `bsdd-clasificacion`, `ifc-validate` y `cde-audit` de `iso19650-openbim`.
**Frontera firme:** el visor lee, anota y **(desde v1.0) edita DATOS**; **nunca modela geometría**. Editar atributos/Psets/clasificaciones y exportar el IFC modificado son operaciones sobre la información del modelo existente: no crean ni mueven geometría.

## Motor (decisión ya tomada y consolidada)
Motor **ThatOpen Components / fragments**. "HTML único" relajado → **app local servida** (sin nube). Roadmap completo en `Visor-IFC_Roadmap_v0.5-v1.3.md` (v1.0 en §4).

### Stack y versiones fijadas (compatibles, NO cambiar de forma aislada)
- `@thatopen/fragments@3.4.5`, `web-ifc@0.0.77`, `three@0.184.0` (peer fragments: three ≥0.182).
- Worker: blob desde `https://cdn.jsdelivr.net/npm/@thatopen/fragments@3.4.5/dist/Worker/worker.mjs`.
- Importmap mapea **`three`, el prefijo `three/`** y `@thatopen/fragments` (esm.sh, `?external=three`). Libs por CDN la 1ª vez.

## Estado de partida: v0.9.1 CERRADA y VALIDADA EN VIVO
Clasificación + BCF + pulido, verificados de punta a punta en navegador real (Chrome, http, puerto 8007) el 22/06/2026 sobre la federación real `nucleo-lateral` + los demos `qto-demo` y `clasif-demo`. Entregado en `Estructurando/visor/`:
```
visor/
  visor-ifc-v0.9.html      Visor actual (cabecera v0.9.1; base de v1.0)
  visor-ifc-v0.8.html / v0.7 / v0.6 / v0.5   versiones previas conservadas
  servir_visor.bat         Sirve por http (PUERTO 8007) y abre /visor-ifc-v0.9.html
  pipeline.mjs             Conversor IFC -> fragments + índice por GlobalId (Node):
                           atributos, psets, quantities (Qto), classifications (parseadas del STEP)
                           y decodificación de escapes IFC (\X2\..\X0\, \X\hh, \S\c) en ifcStrUnescape
  package.json / package-lock.json
  models/
    manifest.json          v0.9: carga nucleo-lateral (real) + qto-demo + clasif-demo; resto load:false
    nucleo-lateral.frag/.props.json     (modelo real, 429 ítems / 410 geom, 7 plantas)
    qto-demo.{ifc,frag,props.json}      (demo con IfcElementQuantity)
    clasif-demo.{ifc,frag,props.json}   (demo con doble clasificación Uniclass + GuBIMClass)
    estructura/mep/lineal, caso-R4/red-pci/caso-15 (.frag/.props.json, load:false)
gubimclass-mapping.json    (raíz) Mapeo IfcClass -> GuBIMClass v1.2 oficial, reutilizable entre hilos
```

**Capacidades acumuladas (mantener intactas):**
- **v0.6** federación: un único `FragmentsModels`, clave `{modelId,localId}`, panel de Modelos, color Original/disciplina/modelo.
- **v0.7** navegación y filtrado: buscar/filtrar toda la federación por texto y por propiedad (`category`, `Disciplina`, atributo, `Pset ▸ Propiedad`); visibilidad granular elemento/nodo/clase; vista por plantas (cota/planta).
- **v0.8** inspección métrica: **sección** X/Y/Z (clipping global), **medición** distancia/área y **lectura de cantidades `Qto_*`**.
- **v0.9 / v0.9.1** anotación: **color/filtro/leyenda por clasificación** (Uniclass/GuBIMClass; bSDD-IFC relegado al detalle del elemento), **incidencias BCF 2.1** (crear con viewpoint+snapshot, editar estado, comentarios, AssignedTo/DueDate/Labels, exportar/importar `.bcfzip`, restaurar cámara/selección/sección con desambiguación por modelo).

**Formato del índice `props.json` (por modelo):** `items{guid→{localId,category,name,attributes,psets,quantities?,classifications?}}`, `localIdToGuid`, `geometryClasses`, `geometryLocalIds`, `countByClass`, `tree` (storeys con `elevation`), `stats`. Los campos `quantities` y `classifications` aparecen solo si el ítem los tiene.

### Gotchas confirmados (NO repetir)
1. **El worker NO arranca desde `file://`** → servir siempre por http con `servir_visor.bat` (puerto 8007).
2. **`getSpatialStructure()` quirk:** nodos `category`+`localId:null` son GRUPOS de clase; los hijos wrapper son los elementos. Normalizado en el pipeline.
3. **`raycast(mouse,dom)`** espera `clientX/clientY` crudos; el hit devuelve `localId`, `distance` y `point`.
4. **API async/sync:** en `FragmentsModels` (navegador) los getters son promesas; en `SingleThreadedFragmentsModel` (Node) son síncronos. Cerrar Node con `process.exit(0)`.
5. **Sección = clipping GLOBAL** (`renderer.clippingPlanes`), no per-material.
6. **fragments NO indexa `HasAssociations`** (clasificación) ni reescribe IFC: es formato de *visualización*. Las clasificaciones se parsean del **texto STEP** (`IfcRelAssociatesClassification → IfcClassificationReference → ReferencedSource`), decodificando escapes IFC. **Implicación clave para v1.0:** la *escritura* de datos al IFC NO puede ir por fragments → habrá que usar **web-ifc (IfcAPI)** o parcheo STEP (ver retos técnicos).
7. **Truncado al escribir en carpeta montada:** Edit/Write/`cp` grandes dejan truncada la *vista de bash* (no la del usuario). Patrón fiable: **autorar en sandbox `/tmp/visorbuildN`, validar (`node --check`, anclas + aserciones), copiar y verificar `md5sum` src==dest**; reescribir HTML grande con `build_*.py` (anclas + aserciones) y `manifest.json` por heredoc.
8. **CDN bloqueado desde el sandbox** → no se valida headless; la validación en vivo corre en la máquina del usuario (lanzar `.bat` por **Ejecutar**; Chrome es tier *read* → inspeccionar con el **Chrome MCP**; `<select>` nativo no cambia por teclado de forma fiable → disparar `change` por JS; estado módulo-scoped → leer por DOM; `zoom` puede dar CDP timeout → `get_page_text`).
9. **`file_upload` del Chrome MCP** solo admite carpetas conectadas (la carpeta del proyecto), no Downloads; el diálogo nativo de Chrome no es clicable (tier *read*).

## Objetivo de ESTE hilo: v1.0 — edición de datos + ingesta por arrastre + entregable estable
Sobre la v0.9.1, convertir el visor en la **primera versión "de despacho"** (uso diario), sin tocar geometría:

1. **Ingesta in-browser por arrastre.** Arrastrar/soltar un `.ifc` sobre el visor y convertirlo **en el navegador** con el mismo `IfcImporter` (web-ifc WASM), **reutilizando la lógica de `pipeline.mjs`** (recuperación de `Elevation` de storeys, parseo de clasificación del STEP y `ifcStrUnescape`). Sin paso de conversión externo. Con **cacheado** del `.frag`+`.props.json` para reaperturas instantáneas (alcance del caché a decidir, ver más abajo).
2. **Edición de DATOS + exportación del IFC.** Editar atributos, **Property Sets** y **clasificaciones** del elemento seleccionado y **exportar el IFC modificado** (reabrible en otra herramienta). Refrescar la vista/índice tras editar. Respeta la frontera "datos sí, geometría no".
3. **QA antes de exportar.** Integración con **`ifc-validate`** (comprobación de nomenclatura, Psets requeridos, clasificación, calidad) como puerta previa a la exportación.
4. **Documentación de uso y empaquetado estable.** Primera versión "de despacho".

### Criterios de aceptación
- **Editar un Pset, validar y exportar un IFC correcto que reabre en otra herramienta** (p. ej. BIMvision/Revit/usBIM o re-importado en el propio visor) conservando el cambio.
- **Abrir un `.ifc` por arrastre** sin paso de conversión externo, con la federación operativa (navegación, clasificación, medición, BCF) sobre el modelo recién ingerido.
- Sin pérdida de rendimiento ni errores de consola; **capacidades v0.5–v0.9.1 intactas**.
- **Frontera:** no mueve ni crea geometría.

## Retos técnicos clave (anticipar al planificar)
- **Escritura de IFC en el navegador.** fragments no escribe IFC. Caminos: (a) **web-ifc `IfcAPI`** en el navegador — `OpenModel(bytes)`, modificar propiedades/Psets/clasificaciones por la API y `ExportFileAsIFC()`/`SaveModel()`; mantiene un modelo web-ifc en memoria en paralelo al de fragments (offline si el WASM va embebido). (b) **Parcheo STEP** para ediciones simples de Pset (frágil; reusa el tokenizador del pipeline). Recomendado: **(a) web-ifc IfcAPI** como motor de lectura+escritura de datos; fragments sigue siendo solo geometría/render.
- **Reconversión tras editar.** Tras escribir datos, regenerar el índice `props.json` (y si procede el `.frag`) reusando las funciones puras del pipeline portadas al navegador, para que la vista refleje el cambio sin recargar.
- **Caché a disco.** Un HTML servido no escribe en disco arbitrario. Opciones: **File System Access API** (`showDirectoryPicker`) sobre la carpeta del proyecto (con permiso), o descarga manual del `.frag`+`.props.json`. El auto-cacheo "junto al IFC" pleno encaja con la **app local empaquetada**.
- **QA sin Python en el navegador.** `ifc-validate` es Python/IfcOpenShell. En el navegador caben **comprobaciones ligeras en JS** (Psets requeridos, nomenclatura, clasificación presente) como puerta previa; la validación completa se delega a la skill `ifc-validate` sobre el IFC exportado.

## Decisiones a tomar al inicio (con recomendación)
1. **Motor de escritura de datos:** ¿web-ifc IfcAPI (recomendado) o parcheo STEP? 
2. **Alcance del caché de ingesta:** ¿File System Access API sobre la carpeta del proyecto, o descarga manual del `.frag`/`.props.json` ahora y auto-cacheo pleno en la app empaquetada?
3. **QA pre-export:** ¿comprobaciones ligeras en JS dentro del visor + delegar la validación completa a `ifc-validate`, o exigir pasar `ifc-validate` antes de habilitar exportar?
4. **Empaquetado "de despacho":** ¿WASM de web-ifc y libs **embebidos/offline** ya en v1.0, o seguir con CDN la 1ª vez y dejar el empaquetado offline como v1.0.x?
5. **Secuencia del hilo:** ¿ingesta por arrastre primero (desbloquea abrir cualquier IFC) y luego edición+export, con checkpoint de validación en vivo entre medias?

## Decisiones ya tomadas (no reabrir salvo que el usuario lo pida)
- **Edición de DATOS, nunca geometría** (frontera firme del visor).
- **App local servida** (sin nube); "HTML único" relajado.
- **fragments solo para geometría/visualización**; los datos editables van por web-ifc/STEP, no por fragments.
- GuBIMClass: usar la **tabla oficial v1.2** (`gubimclass-mapping.json` en la raíz); ampliarla, no inventar códigos.

## Archivos de referencia (raíz del proyecto)
- `Visor-IFC_Roadmap_v0.5-v1.3.md` — plan de versiones (v1.0 en §4; v0.5–v0.9.1 marcadas CERRADAS).
- `Estructurando/visor/` — bundle v0.9.1 funcionando (base de partida): `visor-ifc-v0.9.html`, `pipeline.mjs`, `models/` (incl. `clasif-demo`).
- `gubimclass-mapping.json` — mapeo IfcClass → GuBIMClass v1.2 oficial.
- Memorias `[[estructurando-visor-v0.9-clasificacion-bcf]]`, `[[estructurando-visor-v0.8-medicion-seccion]]`, `[[estructurando-visor-v0.7-navegacion]]`, `[[estructurando-visor-v0.6-federacion]]`, `[[estructurando-visor-v0.5-pipeline]]` — detalles técnicos y gotchas.
- Skills enlazables: `iso19650-openbim:ifc-validate` (QA), `iso19650-openbim:bsdd-clasificacion`, `iso19650-openbim:ifc-create`, `iso19650-openbim:cde-audit`.

## Primer paso propuesto
1. Confirmar las **decisiones de inicio** (motor de escritura, caché, QA, empaquetado, secuencia).
2. **Prueba de concepto de ingesta por arrastre:** zona drop → `IfcImporter` (web-ifc WASM) en el navegador → `.frag` en memoria + índice con las funciones del pipeline portadas (Elevation + clasificación + `ifcStrUnescape`); cargar el modelo en la federación viva. Validar con un `.ifc` real por http.
3. **Prueba de concepto de edición+export:** abrir el IFC con **web-ifc IfcAPI**, editar un Pset del elemento seleccionado, **exportar el IFC** y demostrar que reabre conservando el cambio (en otra herramienta y/o reimportado). Puerta de QA ligera previa.
4. Integrar ambas en el visor, refrescar índice/vista tras editar, **validar en vivo** (sobre `nucleo-lateral`/demos y un IFC arrastrado), subir a **v1.0**, marcar CERRADA en el roadmap con fecha y resultado, y actualizar memoria. Documentar uso y preparar el empaquetado "de despacho".
