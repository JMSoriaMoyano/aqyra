# Visor IFC — Plan de versiones v0.5 → v1.0

**Plugin:** `visor-ifc` (transversal del marketplace "Despacho de Caminos")
**Estado de partida:** v0.4 — web-ifc + Three.js, HTML autocontenido, lanzador Python (`abrir_ifc.py` / `Abrir_IFC.bat`).
**Fecha del plan:** 22 de junio de 2026

---

## 1. Principios de diseño (no negociables)

1. **Herramienta transversal, no de estructuras.** El visor sirve a las tres disciplinas (estructuras, instalaciones MEP, obras lineales) y se distribuye como plugin propio, nunca acoplado al plugin de Estructuras.
2. **Consume los contratos del núcleo.** Lee el modelo neutro / IFC (C1) y los entregables (C3); no duplica lógica de cálculo ni de validación.
3. **El visor lee y anota; no modela geometría.** La frontera con las herramientas de autoría (Blender/Bonsai, Revit) se mantiene siempre: edición de *datos* sí, edición de *geometría* no.
4. **Cada versión = una mejora pequeña, sólida y validada**, anotada con fecha. Compatibilidad de versiones de three/web-ifc fijada y verificada.
5. **Experiencia de usuario fluida** como criterio de aceptación de cada versión, no como añadido.

---

## 2. Eje de evolución: dos modos de carga

El plan se apoya en **dos modos** que conviven:

- **Modo directo (web-ifc):** la página lee el `.ifc`. Cómodo para modelos pequeños/medios y para revisión rápida. Es lo actual.
- **Modo ligero (glTF/glb + JSON de propiedades):** IfcOpenShell pre-tesela el IFC en el sandbox; el visor carga geometría ligera + propiedades por `GlobalId`. Es la base de la buena UX con modelos pesados y de la federación multi-disciplina.

El modo ligero (v0.5) es la palanca técnica que habilita casi todo lo demás.

---

## 3. Plan por versiones

### v0.5 — Modo ligero (glTF) y selector de modo
**Objetivo:** que un modelo pesado abra fluido.

- Pipeline en sandbox: `IFC → glTF/glb` (geometría teselada) + `JSON` de propiedades/Psets indexado por `GlobalId`.
- El visor detecta y carga el paquete ligero; conserva selección, propiedades y árbol espacial leyendo el JSON.
- Selector automático: directo para modelos pequeños, ligero para grandes (umbral por tamaño/nº de elementos).
- **Criterio de aceptación:** un modelo grande de referencia abre y navega con fluidez; las propiedades siguen disponibles al seleccionar.

### v0.6 — Federación multi-disciplina
**Objetivo:** ver varias disciplinas a la vez.

- Carga de varios modelos simultáneos (estructuras / MEP / lineales).
- Panel de modelos: visibilidad, aislar y color **por modelo y por disciplina**, además del color por clase ya existente.
- Encuadre conjunto y por modelo; gestión de origen/coordenadas compartidas.
- **Criterio de aceptación:** dos o tres modelos de distinta disciplina alineados, con encendido/apagado por capa.

### v0.7 — Navegación y filtrado avanzados
**Objetivo:** encontrar y aislar lo que importa.

- Aislar/ocultar **granular** por elemento y por nodo del árbol (no solo por clase).
- Búsqueda y filtro por propiedad o por Pset (p. ej. todos los elementos con `FireRating = EI120`).
- Vista por plantas (mostrar una planta cada vez) y cotas de nivel.
- **Criterio de aceptación:** filtrar por una propiedad y aislar el resultado en un clic.

### v0.8 — Medición y secciones
**Objetivo:** inspección métrica.

- Planos de sección (cortes) interactivos.
- Mediciones: distancia, área; lectura de cantidades (`Qto_*`) si existen.
- **Criterio de aceptación:** medir una distancia y aplicar un corte sobre un modelo federado.

### v0.9 — Color por clasificación + comentarios/BCF (anotación)
**Objetivo:** dar el salto de "ver" a "anotar".

- Color por clasificación Uniclass / GuBIMClass leyendo `IfcClassificationReference` (enlace con la skill `bsdd-clasificacion`).
- Comentarios e incidencias estilo **BCF**: crear, situar en 3D, listar y **exportar BCF**.
- **Criterio de aceptación:** crear una incidencia sobre un elemento y exportarla en BCF reabrible.

### v1.0 — Capa de edición de datos + entregable estable
**Objetivo:** primera versión "de despacho".

- Edición de **datos** del IFC con web-ifc: propiedades, Psets y clasificaciones; **exportar el IFC modificado**.
- Integración con `ifc-validate`: avisos de calidad sobre lo editado antes de exportar.
- Empaquetado y documentación de uso estable; lanzador como software preferente del `.ifc` consolidado.
- **Criterio de aceptación:** editar un Pset, validar y exportar un IFC correcto que reabre en otra herramienta.
- **Frontera explícita:** v1.0 **no** mueve ni crea geometría. Eso queda fuera del alcance del visor.

---

## 4. Horizonte post-1.0 (no comprometido)

- **Migración a ThatOpen Components (fragments)** solo si el visor pasa a ser pieza central de trabajo diario: federación y streaming nativos, mejor rendimiento, a cambio de abandonar el "único HTML autocontenido".
- Comparación de versiones de un mismo modelo (diff geométrico/de datos).
- Vínculo con resultados de cálculo (esfuerzos/armado de Estructuras, presiones/caudales de Instalaciones) coloreando el modelo por resultado — vía contratos del núcleo.

---

## 5. Criterios de evolución

- **Prioridad por uso real**, no por completitud: si una candidata no se usa en proyectos vivos, baja en la cola.
- **Una mejora por versión**, validada abriendo el visor; si no se puede probar el render aquí, se entrega marcada como "versión vigente a validar" y se itera con el feedback (errores de consola).
- **Compatibilidad fijada:** no cambiar versiones de three/web-ifc de forma aislada.
- **Cada versión se anota** en el `roadmap.md` de la skill con fecha y resultado.

---

## 6. Dónde se desarrolla

Dentro del **ecosistema Estructurando** (misma memoria, mismo núcleo, mismo marketplace) pero como **plugin independiente `visor-ifc`**. No se integra en el plugin de Estructuras. Consume C1 (modelo neutro/IFC) y C3 (entregables); se enlaza con las skills `bsdd-clasificacion` e `ifc-validate` del plugin `iso19650-openbim`.
