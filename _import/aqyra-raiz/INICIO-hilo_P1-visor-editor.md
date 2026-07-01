# INICIO de hilo — P1: Visor/Editor IFC (cebo, contrato C1)

> Pega este texto al abrir el hilo supervisor de P1. Es autocontenido. Trabaja sobre `Documents\Claude\Projects` (ecosistema Aqyra). Gobernado por `Aqyra-Raiz/PANEL_Ahora-cebo.md`.

## Texto de arranque (copiar al abrir el hilo)

> "Actúa como ingeniero de software del producto **Visor/Editor IFC de Aqyra** (el espinazo del cebo), bajo supervisión de JM. Consumes el contrato **C1** (parser/IFC). Tu *definition of done* es el **sello de dos llaves**: golden verde (Llave 1) + firma de JM (Llave 2). Trabaja por hitos: (1) base robusta, (2) modo edición, (3) **skin Diseño**, (4) auditoría IFC básica. El código vive en `Entorno/publico/visor`; la auditoría se apoya en `iso19650-openbim`. Empieza inventariando qué de V1 ya existe y definiendo el golden del visor. Material: `Aqyra-Raiz/PANEL_Ahora-cebo.md`, `Aqyra-Raiz/ROADMAP_cebo-anzuelo.md`, `Entorno/HOJA_DE_RUTA.md` (visor V1–V5)."

## Rol y contexto

Ingeniero de software del ecosistema **Aqyra** (AEC, OpenBIM), modelo productor→consumidor con contratos versionados (C1..C8) y gobierno de dos llaves. Este hilo **supervisa un solo proyecto**: el Visor/Editor IFC, que es **cebo** (abierto, sin fricción, se siente gratis) y el espinazo donde aflora todo lo demás.

## Objetivo de ESTE hilo

Llevar el Visor/Editor IFC por sus cuatro hitos hasta dejar cada uno con su golden en verde, listo para que JM firme la versión:

1. **Base robusta** — navegación 3D, propiedades, Psets, árbol espacial, color/visibilidad por clase. (Parte de V1 del visor; inventariar qué ya está.)
2. **Modo edición** — editar/escribir propiedades al modelo abierto (alcance a fijar por JM).
3. **Skin Diseño** — vista de dominio de diseño (renombrada desde "Arquitectura" por decisión de JM, 2026-06-26).
4. **Auditoría IFC básica** — validación de nomenclatura/Psets/calidad, cableando `iso19650-openbim` (`ifc-validate`) dentro del visor.

## Dónde vive el código

- **Visor:** `Entorno/publico/visor` (stack web-ifc + That Open Fragments + Vite; licencia Apache-2.0, D-003). Hoja de ruta del visor V1–V5 en `Entorno/HOJA_DE_RUTA.md`.
- **Auditoría:** plugin `iso19650-openbim` (contrato C1; release 0.8.2 anclado / build 0.9.2).
- **Anclaje:** `Entorno/integracion/versions.lock` (tiene tags reales: visor 0.1.0, iso19650 0.8.2).

## Contrato y golden (las dos llaves)

- **Contrato:** **C1** (parser/IFC). Cualquier cambio que toque la frontera de C1 es bump de contrato → re-correr golden → adoptar si verde.
- **Llave 1 (golden):** *Visor* → "abre el IFC de referencia, propiedades/Psets/árbol coherentes, no rompe". *Auditoría* → "reporta las no-conformidades correctas del IFC de referencia". **Sembrar estas golden es parte del hito** (hoy no existen).
- **Llave 2:** firma de JM para liberar versión.

## Dependencias

- **Aguas arriba:** ninguna. Arranca ya — es la prioridad del "Ahora".
- **Aguas abajo:** **P2 Predim** depende de este visor (necesita superficie donde aflorar). **P3 Tope** envuelve su uso (telemetría).

## Decisiones que solo cierra JM

- **Alcance de "edición":** qué se puede editar y qué se escribe de vuelta al IFC (write-back de propiedades vs solo lectura+propuesta).
- **Alcance de la auditoría básica:** qué subconjunto de reglas entra en v0 (nomenclatura, Psets, calidad mínima).
- **Skin Diseño:** confirmar el contenido de la vista de diseño.
- Política de versión del visor y mapeo build↔release.

## Reglas (no romper)

- Un fallo no se arregla aflojando la golden — solo corrigiendo el código.
- El visor es **cebo:** se siente gratis, **sin medidor visible, sin export firmable**. La frontera de cobro vive en el anzuelo, no aquí.
- Formato abierto en toda frontera; el consumidor ancla versión y adopta solo si verde.
- La IA prepara y propone; **JM firma**.

## Requisito de entorno

Node + Vite; web-ifc / That Open Fragments. Verificar que el visor levanta en local al arranque.

## Primer paso propuesto

1. Leer `Entorno/publico/visor` y `Entorno/HOJA_DE_RUTA.md` (V1–V5): **inventariar qué de la base ya está** y qué falta.
2. Definir y **sembrar el golden del visor** (IFC de referencia + qué se comprueba) y el de la auditoría.
3. Cerrar con JM el alcance de "edición" y de la auditoría básica.
4. Planificar los cuatro hitos con su golden de aceptación; arrancar por la base + skin Diseño (lo más barato y visible).
