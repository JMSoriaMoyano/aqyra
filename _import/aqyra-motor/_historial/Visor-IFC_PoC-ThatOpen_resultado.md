# PoC v0.5 — Motor ThatOpen (fragments): resultado

**Fecha:** 22 de junio de 2026
**Objetivo:** de-riesgar el cambio de motor del visor (web-ifc directo → ThatOpen Components / fragments) antes de comprometer la reescritura completa de la v0.5.

## Entorno

- Node 22 en el sandbox; `@thatopen/fragments@3.4.5` + `web-ifc@0.0.77`.
- Conversión `IFC → fragments` con la clase `IfcImporter` (web-ifc WASM en local).
- Lectura/inspección con `SingleThreadedFragmentsModel` (sin worker, en Node).

## Resultado de la conversión (IFC → .frag)

| Modelo | Disciplina | IFC | Fragments | Tiempo |
|--------|-----------|-----|-----------|--------|
| caso-R4 | Estructura (edificio físico) | 17.7 KB | 7.6 KB | 0.16–0.55 s |
| caso-15 | Estructura (núcleo sísmico) | 21.4 KB | 4.2 KB | 0.37 s |
| caso-10 | Estructura (edificio integrado) | 20.1 KB | 3.3 KB | 0.30 s |
| red-pci | Instalaciones MEP (PCI) | 10.2 KB | 2.6 KB | 0.31 s |

Conversión correcta en las **tres situaciones** (estructura y MEP). El formato fragments **reduce el tamaño** (~2,5–6×), que es justo lo que habilita la "versión ligera" y la federación multi-disciplina.

## Datos recuperados del .frag (caso-R4)

Del fragments se leen, sin volver al IFC:

- **Geometría:** 8 elementos con geometría.
- **Clases IFC:** IFCBEAM, IFCCOLUMN, IFCFOOTING, IFCSLAB, IFCWALL (+ entidades de material, Psets, unidades…).
- **Atributos por elemento:** nombre y **GlobalId** (p. ej. `IFCBEAM | Portico_Dintel | 1AdnCGwv59Mhf5YpHnUnII`).
- **Property Sets** (IFCPROPERTYSET / IFCPROPERTYSINGLEVALUE).
- **Estructura espacial:** raíz IFCPROJECT → … → IFCBUILDINGSTOREY.

Es decir, el `.frag` conserva **todo lo que el visor necesita** (geometría + propiedades + árbol + GUID), y el indexado por `GlobalId` —clave para el coloreado por resultados de la v1.2— está disponible.

## Visor mínimo

`visor-poc-thatopen.html`: visor autocontenido (modelo caso-R4 embebido en base64) que carga los fragments con ThatOpen + Three.js. Navegación 3D, encuadre automático, rejilla/ejes y panel con clases y nº de elementos.

- Requiere **conexión a internet** la primera vez (carga three, @thatopen/fragments y el worker desde CDN). En producción se empaquetará en local.

### Incidencia detectada y resuelta (1ª apertura: se quedaba en "Inicializando…")

La primera versión del visor se congelaba al cargar. Diagnóstico (verificado en navegador con las herramientas de depuración):

- **Causa:** el `importmap` solo mapeaba el especificador `three`, pero `@thatopen/fragments` importa internamente subrutas `three/examples/jsm/...` (Line2, LineMaterial, etc.). Al no estar mapeado el prefijo `three/`, fallaba la resolución de módulos y el script se abortaba en silencio.
- **Fix:** añadir al importmap `"three/": "https://esm.sh/three@0.184.0/"`.
- **Verificado en navegador:** con el importmap corregido cargan three 184, OrbitControls, `@thatopen/fragments` (FragmentsModels) y el worker (HTTP 200); `fragments.load()` del modelo resuelve sin error.
- **Render:** el motor de fragments hace *streaming* de geometría bajo demanda de cámara/viewport, por lo que solo se dibuja en una ventana real con bucle de render (no en pruebas headless).

### 2ª incidencia confirmada: el worker no arranca desde `file://`

Al abrir el visor como archivo local (`file://`), todo carga (three, OrbitControls, fragments, WebGL, descarga del worker) pero `fragments.load()` **no resuelve**: el *worker* de fragments no llega a arrancar. Confirmado con un vigilante de 8 s en el propio visor.

- **Causa:** Chrome bloquea la ejecución de Web Workers en páginas servidas con el esquema `file://` (origen opaco). No es un fallo del visor ni de ThatOpen.
- **Implicación de diseño (refuerza la v0.5):** el visor **debe servirse por http** (o empaquetarse como app local con su propio servidor), no abrirse como archivo suelto. Esto valida la decisión del roadmap de pasar de "HTML `file://` autocontenido" a **app local empaquetada**.
- **Solución para validar la PoC:** servir la carpeta (`python -m http.server 8000`, o el lanzador `servir_visor.bat`) y abrir `http://localhost:8000/visor-poc-thatopen.html`.

### Render CONFIRMADO (22-jun-2026, http://localhost:8000)

Servido por http, el visor **dibuja el modelo correctamente**: pórtico (pilares + dintel) y losa del caso-R4 visibles, navegación 3D operativa. Registro en pantalla: `✓ three 184` → `✓ OrbitControls` → `✓ @thatopen/fragments` → `✓ WebGL` → `✓ worker descargado (3177 KB)` → `✓ modelo cargado en escena` → `✓ render OK`; panel: "Modelo cargado ✓ — caso-R4 (8 elementos)", clases IFCBEAM/IFCCOLUMN/IFCFOOTING/IFCSLAB/IFCWALL. Consola sin errores.

Detalle menor corregido: en el modo multihilo de `FragmentsModels`, `getCategories()`/`getItemsWithGeometry()` devuelven promesas (no arrays como en `SingleThreadedFragmentsModel`); hay que tratarlas como asíncronas.

**La PoC de la v0.5 queda CERRADA con éxito.** Camino validado de punta a punta: IFC → fragments → carga → render + propiedades/clases, en navegador real.

## Conclusión

La cadena completa **IFC → fragments → lectura de geometría y propiedades** funciona y es rápida, en estructura y en MEP. El riesgo técnico de la v0.5 queda **acotado**: el camino es viable.

**Recomendación:** comprometer la reescritura de la v0.5 sobre ThatOpen, con dos verificaciones pendientes antes de cerrarla:
1. Validar el **render** abriendo el visor PoC (confirmar que se dibuja el modelo).
2. Probar la conversión con un **modelo grande real** (los casos aquí son ligeros) para medir tiempos y memoria a escala.

## Siguientes pasos

- Abrir `visor-poc-thatopen.html` y confirmar el render (reportar errores de consola si los hay).
- Si OK: empaquetar el pipeline `IFC → fragments` como utilidad del plugin y dar paridad funcional con la v0.4 (selección + panel de propiedades + árbol + color/visibilidad por clase) ya sobre fragments.
