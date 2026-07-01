# Inicio de hilo — MOTOR/CONTRATO · evolución completa de C1 (desbloquea P1·A/B/C, sin parches)

> **Pega este texto al abrir el hilo EN EL PROYECTO `Estructurando`** (el taller/productor = repo `aqyra-motor`). Es autocontenido.

## Rol y encuadre

Actúa como **ingeniero de software del motor y del contrato C1 de Aqyra**, bajo supervisión de JM y coordinado por el panel (`Aqyra-Raiz`). **Tú implementas y pruebas**; la **golden de record y la firma** son de JM en la zona protegida (`Estructurando 2.0`). Base de esta tarea: **`Aqyra-Raiz/RFC_C1-apertura_familias-P1.md`** (léela) y el contrato vigente `Nucleo-transversal/C1_Contrato-IFC-modelo-neutro.md`.

**Objetivo:** una **sola evolución de C1, completa y diseñada — NO parches** — que desbloquee las tres familias del Visor/Editor (P1·A edificación, P1·B trazado, P1·C normativa) sin volver a tocar el contrato por cada variante.

## ✅ ALCANCE CERRADO (JM · 2026-06-28) — no reabrir; implementar entero

1. **Huecos generalizados.** `IfcOpeningElement` + `IfcRelVoidsElement` aplicable a **cualquier elemento anfitrión** que los admita (losas, cubiertas; muros ya), en `narracion-ifc/spec_to_ifc.py`. No un caso suelto: una vía única reutilizable.
2. **Catálogo de clases ABIERTO.** El handler genérico `elementos[].ifcClass` autora **cualquier `IfcClass`** del catálogo bsDD (incluido `IfcTransportElement` = ascensor) **sin lista cerrada** → clases futuras entran sin re-bump.
3. **Alineaciones completas.** Handler nuevo `alineaciones[]` → `IfcAlignment`: planta (recta + arco + **clotoide**), alzado (rasantes + acuerdos), sección barrida + peralte. **Reutiliza** la maquinaria existente `iso19650-openbim/scripts/lineal/` (Ola 5: parser + generador) — **no reimplementar** geometría de alineación.
4. **Doble clasificación completa.** Cada elemento autorado lleva **bsDD** (URI, ya) **+ Uniclass** (`IfcClassificationReference`), por **mapeo determinista por `ifcClass`** (igual de determinista que la URI bsDD).
5. **Esquema `alto.json` forward-open.** `additionalProperties` permitido y **documentado**: el cebo puede emitir por delante; lo no soportado se ignora, nunca rompe.

## Reglas (no romper)

- **Retrocompatible:** añadir claves/capacidades nuevas, **nunca** cambiar la semántica de las existentes. Los consumidores actuales (estructuras, MEP, lineal, puentes) **sin regresión**.
- **Capacidad COMPLETA, no rebanada:** entra entera (la clotoide y el alzado **ahora**, aunque el cebo los previsualice por slices). Es lo que pide «no más parches».
- **Reutilizar** el núcleo (`scripts/nucleo/`) y la vía lineal de Ola 5; no duplicar.
- **Dos llaves:** golden verde (Llave 1) + firma de JM (Llave 2). La IA prepara/propone; **NO certifica**.

## Criterio de aceptación = la GOLDEN de C1 (Llave 1)

Un `alto.json` patrón que incluya: (a) **huecos en losa y muro**, (b) un elemento **`IfcTransportElement`**, (c) una **alineación con clotoide + acuerdo vertical**, (d) **doble clasificación** bsDD+Uniclass → **compila un IFC válido** en el que: la losa queda **vaciada**, el ascensor está presente, el `IfcAlignment` es **legible por `ifc_to_model_lineal.py`** y cada elemento lleva su clasificación bsDD+Uniclass. **Verde = Llave 1.** (Regla de oro: un fallo se arregla en el código, no aflojando la golden.)

## Entregables (artefactos para JM / el panel)

1. **Código** en `Estructurando` (`spec_to_ifc.py` + lo que toque de `iso19650-openbim`).
2. **Texto de C1** actualizado (`Nucleo-transversal/C1_Contrato-IFC-modelo-neutro.md`) con la nueva versión y las capacidades.
3. **Número de versión nuevo** (bump de `iso19650-openbim`).
4. **Golden candidata EN VERDE** entregada como **ficha** (id · entrada · esperado · oráculo · tolerancia · responsable=JM) + el `alto.json` y el resultado, para que **JM la registre y firme** en `Estructurando 2.0`. (Plantilla de la ficha en `Aqyra-Raiz/PASO-JM_C1_registro-golden-y-firma.md`.)

## Límites (de este hilo)

- **No escribe en `Estructurando 2.0`** (proyectos aislados) ni **firma**: entrega la golden como artefacto. El **registro en 2.0 + la firma + el anclado en `versions.lock`** son de **JM** (ver `PASO-JM_C1_...md`).
- El **lado cebo** (que `c1-bridge.ts` emita `huecos`/`ifcClass`/`alineaciones[]`/Uniclass) **no es de este hilo**: es de los hilos **P1·A/B/C** en el proyecto `Entorno`.

## Primer paso

Lee la RFC y el contrato C1, confirma el plan contra el alcance cerrado y arranca por **(1) huecos generalizados → (2) clases abiertas → (4) doble clasificación → (3) alineaciones**, dejando cada bloque con su prueba; al final, una **golden única** que cubra todo (criterio de aceptación). Entrega los artefactos para el paso de JM en 2.0.

*Procedencia: Aqyra-Raiz · hilo de coordinación · encargo de implementación de la evolución de C1 para el proyecto Estructurando · 2026-06-28.*
