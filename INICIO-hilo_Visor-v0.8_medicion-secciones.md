# INICIO de hilo — Visor IFC v0.8 (medición y secciones)

> Pega este texto al abrir el hilo nuevo. Es autocontenido.

## Rol y contexto

Actúa como ingeniero BIM/desarrollo del ecosistema **Estructurando** (supervisión de Ingeniero de Caminos). Trabajamos el plugin transversal **`visor-ifc`**, **pieza central del trabajo diario**, que sirve a las tres disciplinas (estructuras, instalaciones MEP, obras lineales). Consume los contratos del núcleo (C1 modelo neutro/IFC, C3 entregables, C4 resultados) y se enlaza con `bsdd-clasificacion`, `ifc-validate` y `cde-audit` de `iso19650-openbim`.

**Frontera firme:** el visor lee, anota y (desde v1.0) edita DATOS; **nunca modela geometría**. Medir y cortar son operaciones de inspección sobre la geometría existente: no la modifican.

## Motor (decisión ya tomada y consolidada)

Motor **ThatOpen Components / fragments**. "HTML único" relajado → **app local servida** (sin nube). Roadmap completo en `Visor-IFC_Roadmap_v0.5-v1.3.md` (v0.8 en §3).

### Stack y versiones fijadas (compatibles, NO cambiar de forma aislada)
- `@thatopen/fragments@3.4.5`, `web-ifc@0.0.77`, `three@0.184.0` (peer fragments: three ≥0.182).
- Worker: blob desde `https://cdn.jsdelivr.net/npm/@thatopen/fragments@3.4.5/dist/Worker/worker.mjs`.
- Importmap mapea **`three`, el prefijo `three/`** y `@thatopen/fragments` (esm.sh, `?external=three`). Libs por CDN la 1ª vez.

## Estado de partida: v0.7 CERRADA y VALIDADA EN VIVO

Navegación y filtrado avanzados, verificados de punta a punta en navegador real (Chrome, http, puerto 8007) el 22/06/2026, **incluido un modelo real del usuario** (`nucleo-lateral`: estructura de núcleo lateral, IFC4, 429 ítems / 410 con geometría, 7 plantas reales -1.5→+15.0 m). Entregado en `Estructurando/visor/`:

```
visor/
  visor-ifc-v0.7.html      Visor (navegación + filtrado; libs desde CDN la 1ª vez)
  visor-ifc-v0.6.html      Visor v0.6 (federación, conservado)
  visor-ifc-v0.5.html      Visor v0.5 (paridad, conservado)
  servir_visor.bat         Sirve por http (PUERTO 8007) y abre /visor-ifc-v0.7.html
  pipeline.mjs             Conversor IFC -> fragments + índice por GlobalId (Node)
  package.json             Dependencias fijadas del conversor
  instalar_dependencias.bat / convertir_ifc.bat
  models/
    manifest.json          v0.7: {version, georef, disciplinas{}, models[]}; activo nucleo-lateral, demos a load:false
    nucleo-lateral.frag/.props.json   (modelo real del usuario)
    estructura/mep/lineal .frag/.props.json (demos federación v0.6, load:false)
    (+ caso-R4 / red-pci / caso-15 de v0.5, load:false)
```

**Capacidades de v0.7 (mantener intactas):**
- **Buscar/filtrar** toda la federación: texto libre (nombre/clase/atributos/valores de Pset) + propiedad (`category`, `Disciplina`, atributo, o `Pset ▸ Propiedad`) con operador igual/contiene. Índice de campos/valores **construido en el navegador al cargar** (no en el pipeline). Resultados etiquetados por disciplina/modelo; acciones en un clic sobre el conjunto: **Aislar · Colorear · Ocultar**; clic en resultado = seleccionar + encuadrar.
- **Visibilidad granular** vía `M.object.setVisible(localIds,bool)`: por elemento (panel de propiedades), por nodo/subárbol del árbol y por clase (botones contextuales `◎ aislar / ⦸ ocultar / ◉ mostrar` al hover). `isolatePairs(pairs)` oculta todo y muestra solo los pares. **Mostrar todo** global (cabecera + tecla **G**).
- **Vista por plantas con doble modo**: *Por cota* (agrupa los `IfcBuildingStorey` de distintas disciplinas que comparten elevación) y *Por planta* (cada storey con su modelo). Aísla el nivel en un clic, con cotas.
- Federación v0.6: un único `FragmentsModels`, clave compuesta `{modelId,localId}`, panel de Modelos (visibilidad/aislar/encuadre), color Original/Por disciplina/Por modelo, árbol y clases por modelo.

**Fix de pipeline incorporado en v0.7:** el `IfcImporter` de fragments **pierde el atributo `Elevation` de los `IfcBuildingStorey`**. `pipeline.mjs` lo recupera del IFC fuente por `GlobalId` (regex sobre el texto) y lo reinyecta en `items[guid].attributes.Elevation` y como campo `elevation` en los nodos de planta del `tree`. Patrón reutilizable para otros atributos/cantidades que el importador descarte.

**Formato del índice `props.json` (por modelo):** `items{guid→{localId,category,name,attributes,psets}}`, `localIdToGuid`, `geometryClasses`, `geometryLocalIds`, `countByClass`, `tree` normalizado (storeys con `elevation`), `stats`.

### Gotchas confirmados (NO repetir)
1. **El worker NO arranca desde `file://`** (doble clic → `No se pudo leer models/manifest.json: Failed to fetch`). **Servir siempre por http** con `servir_visor.bat` (puerto 8007). El visor ya avisa en consola.
2. **`getSpatialStructure()` quirk:** nodos con `category` y `localId:null` son GRUPOS de clase; sus hijos wrapper (`category:null`,`localId:N`) son los elementos reales. Normalizar con `elementsOf(catGroup)` recursivo (ya hecho en el pipeline).
3. **`raycast(mouse,dom)`:** `screenToCast` resta el bounding rect internamente → pasar `mouse` con **clientX/clientY crudos**. El hit devuelve `localId`, `distance` y `point` (útil para medición).
4. **API async/sync:** en `FragmentsModels` (worker, navegador) getCategories/getItemsWithGeometry/getItemsData/getSpatialStructure/getBoxes son **promesas**; en `SingleThreadedFragmentsModel` (Node) son síncronas. Cerrar el proceso Node con `process.exit(0)`.
5. **Geometría que tesela:** sólo renderiza si el IFC trae Body con malla (`IfcExtrudedAreaSolid`, etc.). Elementos sin Body NO renderizan (cargan como datos).
6. **Truncado al escribir en carpeta montada:** Write/Edit grandes (HTML del visor, `manifest.json`, incluso `cp` desde `/tmp`) pueden truncar la cola. Patrón fiable: **autorar en sandbox `/tmp/visorbuildX` con heredoc `'EOF'`, `node --check` del script de módulo, copiar y verificar bytes src==dest**; reescribir `manifest.json` por heredoc si el Edit lo trunca; `<!-- fin -->` final de buffer. El **mount de bash va con retardo** respecto a la herramienta Read (autoritativa): verificar contra Read, no solo `wc`/`tail`.
7. **Entorno sandbox:** el pipeline corre con node v22 reusando `node_modules` de `/tmp/visorbuild_5` (symlink). `ifcopenshell` ya está en `/tmp/pylibs`. **CDN (esm.sh/jsdelivr) bloqueados desde el sandbox** → no se valida headless; la validación en vivo corre en la máquina del usuario (lanzar `.bat` vía diálogo **Ejecutar** con grant "Explorador de archivos"; Chrome es tier *read* → inspeccionar/capturar con el **Chrome MCP** `computer`, no con clics de escritorio).

## Objetivo de ESTE hilo: v0.8 — medición y secciones

Sobre la v0.7, dar herramientas de inspección métrica y de corte:

1. **Planos de sección (cortes) interactivos.** Uno o varios planos de recorte que cortan la federación (todos los modelos a la vez), con control de posición/orientación (ejes X/Y/Z y, si procede, plano arbitrario), activar/desactivar y "limpiar cortes". Implementación previsible vía **clipping planes de three** (`renderer.localClippingEnabled=true`, `THREE.Plane`) aplicados al material de los fragments; coordinar con que es un `FragmentsModels` compartido.
2. **Mediciones.** Distancia entre dos puntos (clic-clic) y área (polígono), tomando los puntos del `point` que devuelve el `raycast` de fragments; cotas/etiquetas en pantalla y total acumulado; "limpiar medidas".
3. **Lectura de cantidades `Qto_*`** del elemento seleccionado (longitud, área, volumen). **OJO:** comprobar primero si el pipeline las captura — las cantidades viven en `IfcElementQuantity` → `Quantities` (`IfcQuantityLength/Area/Volume`), distinto de `IfcPropertySet` → `HasProperties` que sí extrae hoy. Probablemente haya que **ampliar `pipeline.mjs`** para leer `Quantities` sin romper el formato v0.7.

### Criterios de aceptación
- **Medir y cortar sobre un modelo federado**, servido por http, sin pérdida de rendimiento ni errores en consola: un plano de sección que corta toda la federación con control y limpieza; medición de distancia y de área con valores correctos sobre el modelo real `nucleo-lateral`; lectura de `Qto_*` del elemento seleccionado (o, si el modelo no las trae, demostrar la ruta con un modelo/elemento que sí).

## Archivos de referencia (raíz del proyecto)
- `Visor-IFC_Roadmap_v0.5-v1.3.md` — plan de versiones (v0.8 en §3; v0.6 y v0.7 marcadas CERRADAS).
- `Estructurando/visor/` — bundle v0.7 funcionando (base de partida): `visor-ifc-v0.7.html`, `pipeline.mjs`, `models/` (incl. `nucleo-lateral`).
- `INICIO-hilo_Visor-v0.7_navegacion-filtrado.md` y memorias `[[estructurando-visor-v0.7-navegacion]]`, `[[estructurando-visor-v0.6-federacion]]`, `[[estructurando-visor-v0.5-pipeline]]` — detalles técnicos y gotchas.

## Decisión pendiente ya tomada (no reabrir salvo que el usuario lo pida)
- **Abrir IFC directamente (ingesta in-browser por arrastrar/soltar):** factible ya en navegador (mismo `IfcImporter` + lógica de `pipeline.mjs` portada, incl. recuperación de `Elevation`), pero **consolidado en v1.0** (no v0.7.1) para llevar web-ifc embebido (offline) y **cachear el `.frag`+`.props.json` a disco** junto al IFC. Anotado en roadmap §4.

## Primer paso propuesto
1. Revisar el visor v0.7 y confirmar el punto de enganche para clipping planes (material de fragments, `renderer.localClippingEnabled`) y para capturar `point` del `raycast`.
2. Comprobar en un `props.json` si hay `Qto_*`/cantidades; si no, ampliar `pipeline.mjs` para leer `IfcElementQuantity.Quantities` y regenerar índices afectados (formato v0.7 intacto).
3. Implementar **un** plano de sección por eje con control de offset y "limpiar"; luego **medición de distancia**; luego área y `Qto_*`.
4. Validar por http en navegador (sobre `nucleo-lateral`) antes de seguir; subir a **v0.8**, marcar CERRADA en el roadmap con fecha y resultado, y actualizar memoria.

<!-- fin -->
