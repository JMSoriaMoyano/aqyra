# Plan P1 — Visor/Editor IFC: 4 hitos, golden de aceptación y alcance cerrado

> **Qué es:** el plan de ejecución del proyecto P1 (Visor/Editor IFC de Aqyra, *cebo*,
> contrato **C1**). Recoge el inventario de partida, las decisiones de alcance que cerró
> JM y los 4 hitos con su **golden de aceptación (Llave 1)**. La IA prepara y propone;
> **JM firma (Llave 2)**.
> **Fecha:** 2026-06-26 · Gobernado por `Aqyra-Raiz/PANEL_Ahora-cebo.md` y `INICIO-hilo_P1-visor-editor.md`.

---

## 0. Reglas que este plan no rompe

- El visor es **cebo**: se siente gratis, **sin medidor visible, sin export firmable**. El muro de cobro vive en el anzuelo, nunca aquí.
- *Definition of done* = **dos llaves**: golden verde (Llave 1) + **firma de JM** (Llave 2).
- Un fallo se arregla **en el código**, nunca aflojando la golden. Solo JM toca golden/tolerancias (PR con traza).
- Cambio en la frontera de **C1** = bump → golden → adoptar si verde; anclar en `integracion/versions.lock`. Nunca "latest" ni rama viva.
- Formato abierto en toda frontera.

---

## 1. Inventario de partida (qué ya existe en `publico/visor`, v0.2.0)

| Hito | Estado real del código | Veredicto |
|---|---|---|
| **1 · Base robusta** | Carga IFC4/IFC4.3 (web-ifc), federación (`registry.ts`), selección+Psets, árbol espacial, color/visibilidad por clase, encuadre/órbita (`viewer.ts`, `ifc-loader.ts`). Además ya hay idealizado (`idealize.ts`), estado-de-dato de dos llaves (`data-state.ts`, D-021), write-back diff-able de Psets (`appendStructuralPset`) y saneamiento del eje espacial (`spatial-metric.ts`). ~37 bloques de test. | **Mayoritariamente hecho.** Falta BCF, IDS/bsDD y hardening tablet, y **sembrar su golden** (no existía). |
| **2 · Modo edición** | Mecanismo base existe: `appendStructuralPset`/`stripStructuralPset` (anejo `Pset_AqyraStructural` como líneas STEP, round-trip byte a byte, todo `proposal`). | **Falta UI + alcance ampliado** (ver §2). |
| **3 · Skin Diseño** | **No existe.** Solo `demo/calculista.html` (skin Calculista). | **A construir.** |
| **4 · Auditoría IFC básica** | **No cableada.** `iso19650-openbim/ifc-validate` existe como skill; `openbim/` solo tiene stubs (BCF→F3, IDS→F4). | **A cablear** (ver §2 y golden en §3). |

> Nota de entorno: el toolchain (pnpm store) no es ejecutable en el sandbox de la IA; los tests TS corren en la máquina de JM con `pnpm test`. El **IFC Maestro** sí se generó y verificó con IfcOpenShell.

---

## 2. Alcance cerrado por JM (2026-06-26)

1. **IFC de referencia del golden:** crear desde cero un **IFC Maestro** controlado (el `DepositoDecopakLimpio.ifc` tiene 0 Psets y no sirve por sí solo). **→ Sembrado hoy.**
2. **Edición / write-back (hito 2): ampliada** — Psets **+ geometría/relaciones** (contención espacial, `IfcZone`/`IfcSystem`/`IfcGroup`). Va más allá del `appendStructuralPset` actual; amplía la superficie de C1.
3. **Auditoría básica v0 (hito 4): completa** — 7 reglas: `psets-requeridos`, `nomenclatura`, `clasificacion`, `materiales`, `estructura-espacial`, `estructura-funcional`, `calidad-minima`.
4. **Skin Diseño (hito 3):** lienzo limpio de diseño (árbol + clases + propiedades, **sin jerga de cálculo**).

---

## 3. Los 4 hitos con su golden de aceptación (Llave 1)

Todos los golden cuelgan del **IFC Maestro** (`publico/visor/test/golden/`). Verde = adoptar; firma de JM = liberar.

### Hito 1 — Base robusta
- **Golden:** abrir el IFC Maestro y comprobar contra `ifc-maestro.golden.json` que **esquema** (IFC4), **inventario** (6 muros / 2 losas / 3 pilares / 2 vigas / 2 puertas / 1 ventana = 23 IfcProduct), **Psets**, **árbol espacial** (2 plantas + 3 espacios) y **clases** salen coherentes y estables, y que **no rompe**.
- **DoD:** golden verde + smoke real adicional con `DepositoDecopakLimpio.ifc` (carga sin romper).

### Hito 2 — Modo edición (ampliada)
- **Golden:** sobre el IFC Maestro, una edición de Pset y una edición de relación (re-contención espacial / asignación a zona) **persisten** con write-back diff-able, marcadas `proposal`, con preview+aprobación y deshacer; el original se preserva (`strip(append(x)) === x`).
- **DoD:** golden verde de write-back ampliado; ninguna salida sale firmable (cebo).

### Hito 3 — Skin Diseño
- **Golden:** la vista Diseño carga el IFC Maestro y expone navegación + árbol espacial + clases (color/visibilidad/aislar) + propiedades, **sin** elementos de cálculo; smoke de render estable.
- **DoD:** golden verde + revisión visual de JM de la pantalla.

### Hito 4 — Auditoría IFC básica (completa)
- **Golden:** correr las 7 reglas sobre el IFC Maestro y reportar **exactamente** las 7 no-conformidades sembradas del manifiesto (ni una más, ni una menos):

| Regla | Defecto sembrado (elemento) |
|---|---|
| psets-requeridos | `AQ-PUE-INT-P01-01` (puerta sin FireRating) |
| nomenclatura | `tabique provisional` |
| clasificacion | `AQ-PIL-EST-P01-01` (sin clasificar) |
| materiales | `AQ-VIG-EST-P01-01` (sin material) |
| estructura-espacial | `AQ-MUR-INT-P01-02` (huérfano) |
| estructura-funcional | `AQ-ESP-P01-01` (Dormitorio sin zona) |
| calidad-minima | `AQ-PIL-EST-P00-02` (geometría vacía) |

- **DoD:** golden verde cableando `iso19650-openbim/ifc-validate`; el auditor en producto coincide con el oráculo `audit-rules.py` sobre el Maestro.

---

## 4. Sembrado en este corte (2026-06-26)

En `publico/visor/test/golden/`:
- `generate-ifc-maestro.py` — generador reproducible (IfcOpenShell).
- `ifc-maestro.ifc` — el IFC Maestro (IFC4, 23 IfcProduct), verificado.
- `ifc-maestro.golden.json` — manifiesto (verdad conforme + 7 defectos sembrados).
- `audit-rules.py` — auditor de referencia (oráculo v0 de las 7 reglas).
- `README.md` — corpus golden documentado.

---

## 5. Siguientes pasos (tras la firma de JM)

1. Cablear el **golden del visor base** (test TS con web-ifc node) que compara contra el manifiesto → cerrar Llave 1 del hito 1.
2. Cablear el **golden de la auditoría** (TS sobre `iso19650-openbim/ifc-validate`) que iguala al oráculo.
3. Arrancar **hito 3 (skin Diseño)** en paralelo (barato y visible).
4. Diseñar el **write-back ampliado** del hito 2 (Psets + relaciones) con su golden.
5. Anclar versión y golden en `integracion/versions.lock` al liberar.

---

## 6. Decisiones abiertas / a confirmar por JM

- **Patrón de nomenclatura definitivo** (hoy propuesto `AQ-<TIPO>-<ZONA>-<NIVEL>-<NN>` para elementos físicos).
- **Lista de Psets requeridos por clase** (hoy v0: `IfcDoor`→`FireRating`); ¿se amplía vía IDS?
- ¿Añadir **Decopak HQ federado** como golden de escala cuando esté montado?
- Política de versión del visor y mapeo build↔release.

---

## 7. Sello de dos llaves

- **Llave 1 (golden):** sembrada esta iteración (IFC Maestro + manifiesto + oráculo). Tests TS verdes pendientes del siguiente corte.
- **Llave 2 (firma de JM):** ___________________________  ·  fecha: __________

> *Procedencia: plan P1 · proyecto Aqyra · IA (Ing. software Visor/Editor) · 2026-06-26 · para revisión, ajuste y firma de JM.*
