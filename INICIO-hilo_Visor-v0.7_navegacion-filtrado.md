# INICIO de hilo — Visor IFC v0.7 (navegación y filtrado avanzados)

> Pega este texto al abrir el hilo nuevo. Es autocontenido.

## Rol y contexto

Actúa como ingeniero BIM/desarrollo del ecosistema **Estructurando** (supervisión de Ingeniero de Caminos). Trabajamos el plugin transversal **`visor-ifc`**, **pieza central del trabajo diario**, que sirve a las tres disciplinas (estructuras, instalaciones MEP, obras lineales). Consume los contratos del núcleo (C1 modelo neutro/IFC, C3 entregables, CN-3 resultados) y se enlaza con `bsdd-clasificacion`, `ifc-validate` y `cde-audit` de `iso19650-openbim`.

**Frontera firme:** el visor lee, anota y (desde v1.0) edita DATOS; **nunca modela geometría**.

## Motor (decisión ya tomada y consolidada)

Motor **ThatOpen Components / fragments**. "HTML único" relajado → **app local servida** (sin nube). Roadmap completo en `Visor-IFC_Roadmap_v0.5-v1.3.md` (v0.7 en §3).

### Stack y versiones fijadas (compatibles, NO cambiar de forma aislada)
- `@thatopen/fragments@3.4.5`, `web-ifc@0.0.77`, `three@0.184.0` (peer fragments: three ≥0.182).
- Worker: blob desde `https://cdn.jsdelivr.net/npm/@thatopen/fragments@3.4.5/dist/Worker/worker.mjs`.
- Importmap mapea **`three`, el prefijo `three/`** y `@thatopen/fragments` (esm.sh, `?external=three`). Libs por CDN la 1ª vez.

## Estado de partida: v0.6 CERRADA y VALIDADA EN VIVO

Federación multi-disciplina verificada de punta a punta en navegador real (Chrome, http) el 22/06/2026. Entregada en `Estructurando/visor/`:

```
visor/
  visor-ifc-v0.6.html      Visor (federación N modelos; libs desde CDN la 1ª vez)
  visor-ifc-v0.5.html      Visor v0.5 (base de paridad, conservado)
  servir_visor.bat         Sirve por http y abre /visor-ifc-v0.6.html
  pipeline.mjs             Conversor IFC -> fragments + índice por GlobalId (Node)
  package.json             Dependencias fijadas del conversor
  instalar_dependencias.bat / convertir_ifc.bat
  models/
    manifest.json          v0.6: objeto {version, georef, disciplinas{}, models[]}
    estructura.frag/.props.json   mep.frag/.props.json   lineal.frag/.props.json
    (+ caso-R4 / red-pci / caso-15 de v0.5, con load:false)
```

Fuentes de los modelos de prueba en `Casos-de-uso/caso-FED-01-federacion-multidisciplina/` (`gen_federacion.py` + estructura/mep/lineal .ifc + README).

**Arquitectura v0.6 (mantener):**
- **Pre-conversión** (igual que v0.5): el pipeline genera por modelo `caso.frag` + `caso.props.json` (índice por **GlobalId**: `items{guid→{localId,category,name,attributes,psets}}`, `localIdToGuid`, `geometryClasses`, `geometryLocalIds`, `countByClass`, `tree` normalizado).
- **Federación:** un único `FragmentsModels` con varios `load(bytes,{modelId})`. Mapa `LOADED: modelId → {entry,index,object,classToLocalIds,geomIds,color,disc,visible,isolated}`.
- **Selección con clave compuesta `{modelId,localId}`** (evita colisión de localId entre modelos). `onPick` hace `raycast` a cada modelo visible y toma el de **menor distancia**.
- `manifest.json` es objeto v0.6 con `disciplinas{label,color}`, `georef` (EPSG:25830) y `models[]` con `disciplina`/`load` (compat. con el array plano de v0.5).
- UI: pestañas **Modelos / Árbol / Clases** + panel de propiedades. Panel de Modelos: visibilidad, **aislar**, encuadre por modelo. Selector global de color **Original / Por disciplina / Por modelo** (`applyColorMode` re-aplica el highlight tras recolorear). Árbol y Clases **agrupados por modelo**.

**Validado (criterios v0.6):** tres modelos de distinta disciplina (estructura 13 geom, MEP 5, lineal 5; 65 ítems / 23 con geometría) cargados, **alineados** por coordenadas compartidas (mismo WCS + `IfcMapConversion` EPSG:25830 idéntico); capas conmutables (visibilidad / aislar / color por modelo y disciplina); selección por clic que identifica disciplina+modelo en propiedades; encuadre conjunto y por modelo; servido por http, sin errores de consola.

### Gotchas confirmados (NO repetir)
1. **El worker NO arranca desde `file://`** → servir por http (`servir_visor.bat`). Si el server sirve la **RAÍZ** del proyecto, la URL del bundle es `/visor/visor-ifc-v0.6.html` (y puede haber un server v0.5 ya ocupando el puerto 8000).
2. **`getSpatialStructure()` quirk:** nodos con `category` y `localId:null` son GRUPOS de clase; sus hijos wrapper (`category:null`,`localId:N`) son los elementos reales; un grupo puede tener varios. Normalizar con `elementsOf(catGroup)` recursivo.
3. **`raycast(mouse,dom):`** `screenToCast` resta el bounding rect internamente → pasar `mouse` con **clientX/clientY crudos**.
4. **API async/sync:** en `FragmentsModels` (worker) getCategories/getItemsWithGeometry/getItemsData/getSpatialStructure son **promesas**; en `SingleThreadedFragmentsModel` (Node) son síncronas. Cerrar el proceso Node con `process.exit(0)`.
5. **Geometría que tesela:** sólo renderiza si el IFC trae Body `IfcExtrudedAreaSolid` (u otra rep. con malla). `IfcFlowSegment` sin Body NO renderiza (por eso red-pci v0.5 salía vacío). Para MEP/lineal, generar tuberías/conductos como sólidos extruidos (perfil circular/rectangular).
6. **`IfcPipeSegment` (IFC4)** no admite `GRAVITYSEGMENT` → usar `CULVERT` / `RIGIDSEGMENT`.
7. **Truncado de cola al escribir en carpeta montada:** Write/Edit grandes pueden perder ~20–30 bytes finales (SyntaxError "Unexpected token '<'"). **Tras cada escritura grande, verificar el tail** (`tail`/grep de `</script>`/`</html>`); un `<!-- fin -->` final sirve de buffer.
8. **Entorno sandbox:** `ifcopenshell` ya está en `/tmp/pylibs` (reusar; instalar llena el disco). `/tmp/visorbuild_5` tiene el `node_modules` del pipeline pero es **read-only** → crear dir nuevo y `ln -s` a su `node_modules`. **CDN (esm.sh/jsdelivr) bloqueados desde el sandbox** → no se puede validar headless aquí; la validación en vivo corre en la máquina del usuario (lanzar `.bat` vía diálogo **Ejecutar**, que necesita grant "Explorador de archivos"; Chrome es tier *read* → inspeccionar/capturar con el **Chrome MCP** `computer`, no con clics de escritorio).

## Objetivo de ESTE hilo: v0.7 — navegación y filtrado avanzados

Sobre la federación v0.6, dar al usuario control fino para encontrar y aislar lo que le interesa:

1. **Aislar/ocultar granular** por **elemento** (selección) y por **nodo del árbol** (un subárbol o una clase), no sólo por modelo. Botones aislar/ocultar/mostrar contextuales y un "mostrar todo" global.
2. **Búsqueda y filtro por propiedad o Pset** sobre toda la federación: p. ej. `FireRating = EI120`, `Disciplina = MEP`, `category = IFCCOLUMN`, o texto en nombre/atributo. El resultado se **lista** (con su modelo/disciplina) y se puede **aislar/colorear en un clic**.
3. **Vista por plantas** (una cada vez) usando `IfcBuildingStorey`/Elevation del `tree`, con cotas de nivel; conmutar planta visible. (Coordinar con que cada modelo trae sus propias plantas.)

### Criterios de aceptación
- **Filtrar por una propiedad/Pset y aislar el resultado en un clic**, identificando a qué modelo/disciplina pertenece cada elemento encontrado; aislar/ocultar granular por elemento y por nodo del árbol; vista por plantas operativa; servido por http, sin pérdida de rendimiento ni errores en consola.

## Archivos de referencia (raíz del proyecto)
- `Visor-IFC_Roadmap_v0.5-v1.3.md` — plan de versiones (v0.7 en §3; v0.6 marcada CERRADA en §2).
- `Estructurando/visor/` — bundle v0.6 funcionando (base de partida): `visor-ifc-v0.6.html`, `pipeline.mjs`, `models/`.
- `Casos-de-uso/caso-FED-01-federacion-multidisciplina/` — los 3 IFC co-localizados + `gen_federacion.py` (para regenerar/ampliar modelos de prueba).
- `INICIO-hilo_Visor-v0.6_federacion-multidisciplina.md` y memorias `[[estructurando-visor-v0.6-federacion]]`, `[[estructurando-visor-v0.5-pipeline]]` — detalles técnicos y gotchas.

## Primer paso propuesto
1. Comprobar si el **índice `props.json`** ya basta para filtrar (atributos + psets por GlobalId ya están). Si falta algo para "buscar por propiedad" (p. ej. un índice invertido propiedad→[guids]), **ampliar el pipeline** sin romper el formato v0.6.
2. Añadir un **buscador/filtro** en la UI (campo + selector de propiedad/valor) que recorra `LOADED` y devuelva resultados `{modelId,localId}`; acciones sobre el resultado: **aislar**, **colorear**, **ocultar**, listar.
3. Añadir **aislar/ocultar contextual** en el árbol (por nodo/subárbol y por clase) y sobre la selección actual; "mostrar todo" global.
4. Añadir **vista por plantas** a partir de las `IfcBuildingStorey` del `tree` de cada modelo (selector de planta + cota).
5. Validar por http en navegador antes de seguir; subir a **v0.7** y anotar fecha y resultado en el roadmap y en memoria.

<!-- fin -->
