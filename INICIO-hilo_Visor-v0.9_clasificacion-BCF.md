# INICIO de hilo — Visor IFC v0.9: clasificación y BCF

## Rol y contexto
Actúa como ingeniero BIM/desarrollo del ecosistema **Estructurando** (supervisión de Ingeniero de Caminos). Trabajamos el plugin transversal **`visor-ifc`**, **pieza central del trabajo diario**, que sirve a las tres disciplinas (estructuras, instalaciones MEP, obras lineales). Consume los contratos del núcleo (C1 modelo neutro/IFC, C3 entregables, C4 resultados) y se enlaza con `bsdd-clasificacion`, `ifc-validate` y `cde-audit` de `iso19650-openbim`.
**Frontera firme:** el visor lee, anota y (desde v1.0) edita DATOS; **nunca modela geometría**. Anotar, clasificar y crear incidencias son operaciones sobre la información del modelo existente: no crean ni mueven geometría.

## Motor (decisión ya tomada y consolidada)
Motor **ThatOpen Components / fragments**. "HTML único" relajado → **app local servida** (sin nube). Roadmap completo en `Visor-IFC_Roadmap_v0.5-v1.3.md` (v0.9 en §4).

### Stack y versiones fijadas (compatibles, NO cambiar de forma aislada)
- `@thatopen/fragments@3.4.5`, `web-ifc@0.0.77`, `three@0.184.0` (peer fragments: three ≥0.182).
- Worker: blob desde `https://cdn.jsdelivr.net/npm/@thatopen/fragments@3.4.5/dist/Worker/worker.mjs`.
- Importmap mapea **`three`, el prefijo `three/`** y `@thatopen/fragments` (esm.sh, `?external=three`). Libs por CDN la 1ª vez.

## Estado de partida: v0.8 CERRADA y VALIDADA EN VIVO
Medición y secciones, verificadas de punta a punta en navegador real (Chrome, http, puerto 8007) el 22/06/2026, sobre la federación real `nucleo-lateral` + el demo `qto-demo`. Entregado en `Estructurando/visor/`:
```
visor/
  visor-ifc-v0.8.html      Visor (sección + medición + lectura Qto; base de v0.9)
  visor-ifc-v0.7.html      v0.7 (navegación + filtrado, conservado)
  visor-ifc-v0.6.html / v0.5.html   versiones previas conservadas
  servir_visor.bat         Sirve por http (PUERTO 8007) y abre /visor-ifc-v0.8.html
  pipeline.mjs             Conversor IFC -> fragments + índice por GlobalId (Node); ahora también lee Quantities (Qto)
  package.json / package-lock.json
  models/
    manifest.json          v0.8: carga nucleo-lateral (real) + qto-demo; resto load:false
    nucleo-lateral.frag/.props.json     (modelo real del usuario, 429 ítems / 410 geom, 7 plantas)
    qto-demo.{ifc,frag,props.json}      (demo con IfcElementQuantity inyectado sobre estructura.ifc)
    estructura/mep/lineal, caso-R4/red-pci/caso-15 (.frag/.props.json, load:false)
```

**Capacidades acumuladas (mantener intactas):**
- **v0.6** federación: un único `FragmentsModels`, clave compuesta `{modelId,localId}`, panel de Modelos, color Original/Por disciplina/Por modelo.
- **v0.7** navegación y filtrado: buscar/filtrar toda la federación por texto y por propiedad (`category`, `Disciplina`, atributo, `Pset ▸ Propiedad`); índice de campos/valores construido en el navegador; acciones Aislar/Colorear/Ocultar; visibilidad granular elemento/nodo/clase; vista por plantas (cota/planta).
- **v0.8** inspección métrica: **sección** X/Y/Z sobre toda la federación (clipping global `renderer.clippingPlanes`, con offset/invertir/limpiar), **medición** de distancia y área (con el `point` del `raycast`, etiquetas HTML proyectadas), y **lectura de cantidades `Qto_*`** del elemento seleccionado.

**Formato del índice `props.json` (por modelo):** `items{guid→{localId,category,name,attributes,psets,quantities?}}`, `localIdToGuid`, `geometryClasses`, `geometryLocalIds`, `countByClass`, `tree` (storeys con `elevation`), `stats`. El campo `quantities` (v0.8) sólo aparece si el ítem tiene `IfcElementQuantity`.

### Gotchas confirmados (NO repetir)
1. **El worker NO arranca desde `file://`** → servir siempre por http con `servir_visor.bat` (puerto 8007).
2. **`getSpatialStructure()` quirk:** nodos `category`+`localId:null` son GRUPOS de clase; los hijos wrapper (`category:null`,`localId:N`) son los elementos. Normalizado en el pipeline.
3. **`raycast(mouse,dom)`** espera `clientX/clientY` crudos; el hit devuelve `localId`, `distance` y `point` (usado en medición).
4. **API async/sync:** en `FragmentsModels` (navegador) los getters son promesas; en `SingleThreadedFragmentsModel` (Node) son síncronos. Cerrar Node con `process.exit(0)`.
5. **Sección = clipping GLOBAL** (`renderer.clippingPlanes`), no per-material: corta todos los modelos del `FragmentsModels` compartido sin tocar materiales internos de fragments. Patrón a reutilizar si v0.9 necesita aislar/recortar para una vista BCF.
6. **Truncado al escribir en carpeta montada:** Edit/Write/`cp` grandes pueden dejar truncada la *vista de bash* (no la del usuario). Patrón fiable: **autorar en sandbox `/tmp/visorbuildN` con heredoc, validar ahí (`node --check`, anclas + aserciones `count==1` para el HTML), copiar y verificar `md5sum` src==dest**; reescribir `manifest.json` por heredoc si el Edit lo trunca.
7. **Entorno sandbox:** el pipeline corre con node v22 reusando `node_modules` del visor (symlink); `web-ifc` wasm local (no necesita CDN); `ifcopenshell` en `/tmp/pylibs` (`sys.path.insert`). **CDN bloqueado desde el sandbox** → no se valida headless; la validación en vivo corre en la máquina del usuario (lanzar `.bat` vía diálogo **Ejecutar** con grant "Explorador de archivos"; Chrome es tier *read* → inspeccionar con el **Chrome MCP**, `get_page_text` si el zoom da `CDP timeout`).

## Objetivo de ESTE hilo: v0.9 — clasificación y BCF
Sobre la v0.8, dar herramientas de **anotación y clasificación** (sin tocar geometría):

1. **Color por clasificación.** Colorear y filtrar la federación por **Uniclass / GuBIMClass** (`IfcClassificationReference` vía `IfcRelAssociatesClassification`), con leyenda por código/sistema. Enlazar con la skill **`bsdd-clasificacion`** de `iso19650-openbim` (doble clasificación Uniclass + GuBIMClass).
   - **OJO — primer punto a comprobar:** el `pipeline.mjs` actual extrae atributos, `psets` (de `IsDefinedBy`) y `quantities`, pero **probablemente NO captura las clasificaciones**, que llegan por `HasAssociations → IfcRelAssociatesClassification → RelatingClassification` (distinto de `IsDefinedBy`). Habrá que **ampliar `pipeline.mjs`** para leer `HasAssociations`/clasificación y añadir un campo nuevo (p. ej. `classifications`) sin romper el formato v0.8 — mismo patrón que se siguió con `quantities` en v0.8.

2. **Comentarios e incidencias BCF.** Crear una incidencia, **situarla en 3D** (viewpoint: posición/orientación de cámara + componentes seleccionados por `GlobalId` + planos de sección activos + snapshot opcional), listarlas, y **exportar/importar BCF** (BCF-XML / `.bcfzip`). Es anotación de datos: respeta la frontera "datos sí, geometría no".

### Criterios de aceptación
- **Crear una incidencia y exportarla en BCF reabrible:** sobre la federación servida por http, crear una incidencia con título/comentario y un viewpoint (cámara + elementos seleccionados), exportarla a `.bcfzip` conforme al estándar, y demostrar que reabre (reimportar en el propio visor y/o en una herramienta BCF externa) recuperando la vista y los componentes.
- **Color por clasificación** de la federación con leyenda y filtro; si el modelo real no trae `IfcClassificationReference`, demostrar la ruta con un modelo clasificado (p. ej. enriquecer un caso con `bsdd-clasificacion`, como se hizo con `qto-demo` para las cantidades).
- Sin pérdida de rendimiento ni errores en consola; capacidades v0.5–v0.8 intactas.

## Archivos de referencia (raíz del proyecto)
- `Visor-IFC_Roadmap_v0.5-v1.3.md` — plan de versiones (v0.9 en §4; v0.5–v0.8 marcadas CERRADAS).
- `Estructurando/visor/` — bundle v0.8 funcionando (base de partida): `visor-ifc-v0.8.html`, `pipeline.mjs`, `models/` (incl. `nucleo-lateral` y `qto-demo`).
- Memorias `[[estructurando-visor-v0.8-medicion-seccion]]`, `[[estructurando-visor-v0.7-navegacion]]`, `[[estructurando-visor-v0.6-federacion]]`, `[[estructurando-visor-v0.5-pipeline]]` — detalles técnicos y gotchas.
- Skills enlazables: `iso19650-openbim:bsdd-clasificacion` (clasificación Uniclass/GuBIMClass + URI bsDD), `iso19650-openbim:ifc-validate`, `iso19650-openbim:cde-audit`.

## Decisiones ya tomadas (no reabrir salvo que el usuario lo pida)
- **Abrir IFC por arrastrar/soltar (ingesta in-browser)** y **edición + exportación de datos** se consolidan en **v1.0**, no en v0.9 (la app local empaquetada llevará web-ifc embebido y permitirá cachear `.frag`+`.props.json` junto al IFC). Anotado en roadmap §4.
- **BCF antes que edición de IFC:** v0.9 anota/clasifica (lectura + ficheros BCF aparte); la escritura de datos al propio IFC es de v1.0.

## Primer paso propuesto
1. Revisar el visor v0.8 y confirmar puntos de enganche: cómo colorear/filtrar por un campo nuevo (reutilizar la maquinaria de `applyColorMode`/filtros de v0.7) y cómo capturar el estado de cámara + selección + planos de sección para un viewpoint BCF.
2. Comprobar en un `props.json` si hay clasificaciones; si no, **ampliar `pipeline.mjs`** para leer `IfcRelAssociatesClassification` (campo `classifications`, formato v0.8 intacto) y regenerar los índices afectados. Preparar un modelo clasificado de demo con `bsdd-clasificacion` si el real no trae clasificación.
3. Implementar **color + filtro por clasificación** con leyenda; luego el **modelo de incidencias BCF** (crear, viewpoint, listar) y por último **exportar/importar `.bcfzip`**.
4. Validar por http en navegador (sobre `nucleo-lateral` + demo) antes de seguir; subir a **v0.9**, marcar CERRADA en el roadmap con fecha y resultado, y actualizar memoria.
