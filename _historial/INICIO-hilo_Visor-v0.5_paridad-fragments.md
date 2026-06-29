# INICIO de hilo — Visor IFC v0.5 (paridad funcional sobre ThatOpen/fragments)

> Pega este texto al abrir el hilo nuevo. Es autocontenido.

## Rol y contexto

Actúa como ingeniero BIM/desarrollo del ecosistema **Estructurando** (supervisión de Ingeniero de Caminos). Trabajamos el plugin transversal **`visor-ifc`**, que se ha redefinido como **pieza central del trabajo diario** y sirve a las tres disciplinas (estructuras, instalaciones MEP, obras lineales). Consume los contratos del núcleo (C1 modelo neutro/IFC, C3 entregables, CN-3 resultados) y se enlaza con `bsdd-clasificacion`, `ifc-validate` y `cde-audit` de `iso19650-openbim`.

**Frontera firme:** el visor lee, anota y (desde v1.0) edita DATOS; **nunca modela geometría**.

## Decisión de motor (ya tomada)

El motor pasa de web-ifc directo a **ThatOpen Components / fragments**. Se relaja el "HTML único autocontenido" → **app local servida/empaquetada** (sin nube). Roadmap completo en `Visor-IFC_Roadmap_v0.5-v1.3.md`.

## Estado: PoC v0.5 CERRADA con éxito

Validado de punta a punta en navegador real (doc `Visor-IFC_PoC-ThatOpen_resultado.md`):

- Conversión `IFC → fragments` con `IfcImporter.process({bytes})` (Node, sandbox), en estructura y MEP.
- Del `.frag` se recuperan geometría, categorías, nombres, **GlobalId**, Psets y árbol espacial.
- **Render confirmado** sirviendo por http: caso-R4 (pórtico + losa) se dibuja y navega.

### Stack y versiones fijadas (compatibles)
- `@thatopen/fragments@3.4.5`, `web-ifc@0.0.77`, `three@0.184.0` (peer fragments: three ≥0.182).
- Worker: `dist/Worker/worker.mjs` cargado como blob URL.
- Importmap: mapear **`three` y el prefijo `three/`** (fragments importa subrutas `three/examples/jsm/...`).

### Gotchas confirmados (no repetir)
1. **El worker NO arranca desde `file://`** (Chrome lo bloquea) → `load()` se cuelga sin error. Hay que **servir por http** (lanzador `servir_visor.bat` → `python -m http.server`) o empaquetar como app local servida.
2. En `FragmentsModels` (multihilo) `getCategories()` / `getItemsWithGeometry()` son **asíncronos** (promesas); en `SingleThreadedFragmentsModel` son síncronos.

## Objetivo de ESTE hilo: paridad funcional v0.5 sobre fragments

Reescribir el visor sobre fragments hasta igualar la v0.4, como **app local servida**:

1. **Pipeline** `IFC → fragments + índice de propiedades por GlobalId` como utilidad del plugin (Node/sandbox), con selector directo/ligero por tamaño.
2. **Selección** de elementos (clic) con resaltado.
3. **Panel de propiedades + Property Sets** del elemento seleccionado.
4. **Árbol de estructura espacial** (Proyecto/Emplazamiento/Edificio/Planta/elementos) navegable.
5. **Color y visibilidad por clase IFC**.
6. **Empaquetado/arranque local** (servidor o app) que evite `file://`; actualizar el lanzador.

### Criterios de aceptación
- Abre un modelo pesado con fluidez; selección muestra propiedades/Psets correctas por GlobalId; árbol y filtros por clase operativos; sin errores en consola; servido por http/app (no `file://`).

## Archivos de referencia (raíz del proyecto)
- `Visor-IFC_Roadmap_v0.5-v1.3.md` — plan de versiones.
- `Visor-IFC_PoC-ThatOpen_resultado.md` — resultado de la PoC y detalles técnicos.
- `visor-poc-thatopen.html` — visor PoC funcionando (base de partida).
- `servir_visor.bat` — lanzador del servidor local.
- Modelos de prueba en `Casos-de-uso/` (p. ej. `caso-R4`, `caso-15`, `caso-MEP-01-red-pci`).

## Primer paso propuesto
Partir de `visor-poc-thatopen.html`, separar el pipeline de conversión del visor, y añadir **selección + panel de propiedades/Psets** leyendo por GlobalId. Validar abriendo por http antes de seguir.
