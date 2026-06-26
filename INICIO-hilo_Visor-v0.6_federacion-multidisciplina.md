# INICIO de hilo — Visor IFC v0.6 (federación multi-disciplina a escala)

> Pega este texto al abrir el hilo nuevo. Es autocontenido.

## Rol y contexto

Actúa como ingeniero BIM/desarrollo del ecosistema **Estructurando** (supervisión de Ingeniero de Caminos). Trabajamos el plugin transversal **`visor-ifc`**, **pieza central del trabajo diario**, que sirve a las tres disciplinas (estructuras, instalaciones MEP, obras lineales). Consume los contratos del núcleo (C1 modelo neutro/IFC, C3 entregables, C4 resultados) y se enlaza con `bsdd-clasificacion`, `ifc-validate` y `cde-audit` de `iso19650-openbim`.

**Frontera firme:** el visor lee, anota y (desde v1.0) edita DATOS; **nunca modela geometría**.

## Motor (decisión ya tomada y consolidada)

Motor **ThatOpen Components / fragments**. Se relajó el "HTML único" → **app local servida** (sin nube). Roadmap completo en `Visor-IFC_Roadmap_v0.5-v1.3.md`.

### Stack y versiones fijadas (compatibles, NO cambiar de forma aislada)
- `@thatopen/fragments@3.4.5`, `web-ifc@0.0.77`, `three@0.184.0` (peer fragments: three ≥0.182).
- Worker: blob desde `https://cdn.jsdelivr.net/npm/@thatopen/fragments@3.4.5/dist/Worker/worker.mjs`.
- Importmap mapea **`three`, el prefijo `three/`** y `@thatopen/fragments` (esm.sh, `?external=three`). Libs por CDN la 1ª vez.

## Estado de partida: v0.5 CERRADA y VALIDADA EN VIVO

Paridad funcional con la v0.4, verificada de punta a punta en navegador real (Chrome, http). Entregada en `Estructurando/visor/`:

```
visor/
  visor-ifc-v0.5.html      Visor (1 archivo; libs desde CDN la 1ª vez)
  servir_visor.bat         Sirve por http y abre el visor (abre /visor-ifc-v0.5.html)
  pipeline.mjs             Conversor IFC -> fragments + índice por GlobalId (Node)
  package.json             Dependencias fijadas del conversor
  instalar_dependencias.bat / convertir_ifc.bat
  models/
    manifest.json          Lista de modelos del selector
    caso-R4.frag/.props.json   red-pci.frag/.props.json   caso-15.frag/.props.json
```

**Arquitectura (mantener):** *pre-conversión*. El pipeline (Node/sandbox) genera por modelo `caso.frag` (geometría ligera) + `caso.props.json` (índice por **GlobalId**: `items{guid→{localId,category,name,attributes,psets}}`, `localIdToGuid`, `geometryClasses`, `geometryLocalIds`, `countByClass`, `tree` normalizado). El visor carga esos ficheros **por http** y las libs/worker de CDN.

**Validado (los 6 criterios v0.5):** render y navegación (caso-R4: pórtico+losa+muro+zapata), selección por clic con resaltado azul, panel propiedades/Psets por GlobalId, árbol espacial navegable, color y visibilidad por clase IFC, selector multi-modelo, y degradación correcta cuando el IFC no trae geometría teselada (red-pci y caso-15: árbol+datos, vista 3D vacía). Sin errores de consola.

### Gotchas confirmados (NO repetir)
1. **El worker NO arranca desde `file://`** → servir por http (servir_visor.bat). Ojo: si se sirve la RAÍZ del proyecto, la URL del bundle es `/visor/visor-ifc-v0.5.html`.
2. **getSpatialStructure() quirk:** nodos con `category` y `localId:null` son GRUPOS de clase; sus hijos wrapper (`category:null`,`localId:N`) son los elementos reales, y un grupo puede tener varios. Normalizar con `elementsOf(catGroup)` recursivo.
3. **raycast(mouse,dom):** `screenToCast` resta el bounding rect internamente → pasar `mouse` con **clientX/clientY crudos** (no restar el rect).
4. **API async/sync:** en `FragmentsModels` (worker) getCategories/getItemsWithGeometry/getItemsData/getSpatialStructure son **promesas**; en `SingleThreadedFragmentsModel` (Node) son síncronas. Cerrar el proceso Node con `process.exit(0)`.
5. **npm/build:** instalar y construir en `/tmp/<dir>` (NO en carpeta montada: da EPERM); copiar solo assets.
6. **Truncado de cola al escribir en carpeta montada:** Write/Edit grandes pueden perder ~20–30 bytes finales (en v0.5 se comió `</script></body></html>` → SyntaxError "Unexpected token '<'", módulo sin ejecutar y sin error en consola). **Tras cada escritura grande, verificar el tail** (`tail`, grep de `</script>`/`</html>`) y reparar; un `<!-- fin -->` final sirve de buffer.

## Objetivo de ESTE hilo: v0.6 — federación multi-disciplina a escala

Ver y gestionar varias disciplinas a la vez sobre el motor fragments:

1. **Carga simultánea** de varios modelos (estructuras / MEP / lineales) en la misma escena, con **coordenadas compartidas** (alineación por origen/georreferencia; revisar `getCRS()` / `getCoordinates()` de fragments y los Psets de georreferencia del IFC).
2. **Panel de modelos:** por cada modelo cargado → visibilidad, **aislar**, y **color por modelo y por disciplina**; recuento y estado.
3. **Encuadre** conjunto (todos) y por modelo; gestión de origen/georreferencia cuando los orígenes difieren.
4. Mantener selección/propiedades/árbol/clases de v0.5, ahora **por modelo** (el GlobalId sigue siendo la clave; cuidar colisiones de localId entre modelos usando el `modelId`).

### Criterios de aceptación
- Tres modelos de distinta disciplina cargados y **alineados**, con capas conmutables (visibilidad/aislar/color por modelo y disciplina) **sin pérdida de rendimiento**; selección y propiedades correctas identificando a qué modelo pertenece cada elemento; servido por http, sin errores en consola.

## Archivos de referencia (raíz del proyecto)
- `Visor-IFC_Roadmap_v0.5-v1.3.md` — plan de versiones (v0.6 en §2).
- `Estructurando/visor/` — bundle v0.5 funcionando (base de partida): `visor-ifc-v0.5.html`, `pipeline.mjs`, `models/`.
- `INICIO-hilo_Visor-v0.5_paridad-fragments.md` y memoria `[[estructurando-visor-v0.5-pipeline]]` — detalles técnicos y gotchas.
- Modelos de prueba en `Casos-de-uso/` (estructura: `caso-R4`, `caso-15`; MEP: `caso-MEP-01-red-pci`, `caso-PCI-*`, `caso-REBT-*`). Para federación conviene generar/usar modelos que compartan emplazamiento.

## Primer paso propuesto
1. Extender `models/manifest.json` con metadatos por modelo: **`disciplina`** (estructura/MEP/lineal) y, si procede, **origen/georreferencia**.
2. Reescribir la carga del visor para sostener **N modelos a la vez** (un `FragmentsModels` con varios `load(...,{modelId})`; mapa `modelId → {object, index}`), evitando colisiones de localId entre modelos.
3. Añadir el **panel de modelos** (visibilidad / aislar / color por modelo y disciplina) junto a las pestañas Árbol/Clases.
4. Cargar a la vez **caso-R4 (estructura) + red-pci (MEP)** y validar alineación por coordenadas compartidas; encuadre conjunto y por modelo.
5. Validar por http en navegador antes de seguir; subir a **v0.6** y anotar fecha y resultado en `references/roadmap.md` de la skill.
