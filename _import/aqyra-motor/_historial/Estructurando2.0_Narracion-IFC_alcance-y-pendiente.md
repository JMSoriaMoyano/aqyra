# Estructurando 2.0 — Hilo «Compilador narración → IFC»

**Estado a 2026-06-23 · Entregable principal: `iso19650-openbim-v0.8.2.plugin` (APTO, a instalar)**

Este hilo construye, de forma incremental y verificada, la capacidad de **crear modelos IFC con geometría real describiéndolos en lenguaje natural**, integrándola en el ecosistema BIM del proyecto (visor IFC, plugin OpenBIM, bsDD). Lo que sigue resume el alcance cubierto y el trabajo pendiente para continuar en un hilo nuevo.

---

## 1. Punto de partida y decisión de arquitectura

Se planteó cómo generar geometría IFC «narrando al prompt». Tras un análisis coste/beneficio de tres rutas (generador server-side, MCP sobre el visor, STEP directo por el LLM), se eligió la **Ruta 1**: un compilador determinista alimentado por el lenguaje, que reutiliza el pipeline del visor ya existente.

El compilador se diseñó en **dos capas con frontera limpia**:

- **Capa semántica** (lenguaje → intención): el agente, guiado por la skill, traduce la prosa a un *spec de alto nivel*.
- **Capa determinista** (intención → geometría): `compilar_spec.py` expande macros a coordenadas y valida; `spec_to_ifc.py` genera el IFC con IfcOpenShell.

```
prosa → <m>.alto.json → compilar_spec.py → <m>.spec.json → spec_to_ifc.py → <m>.ifc
      → visor/pipeline.mjs → .frag + props → Visor IFC
```

---

## 2. Alcance cubierto

### 2.1 Núcleo del compilador
- **Spec paramétrico canónico** con su contrato **JSON Schema** (`spec.schema.json`), todo en metros.
- **Expansor determinista** (`compilar_spec.py`): macros de edificio (retícula anisótropa `luz_max_x`/`luz_max_y`, niveles por nº de plantas), retícula de pilares, y validación de esquema + geométrica.
- **Generador** (`spec_to_ifc.py`): IFC4/IFC4X3 con geometría real (extrusiones), estructura espacial completa.

### 2.2 Primitivas con geometría realista
- **Pilares**: rectangulares o circulares.
- **Muros** con **huecos reales**: `IfcOpeningElement` + `IfcRelVoidsElement` que **restan** del muro (verificado por volumen), con puerta/ventana rellenando vía `IfcRelFillsElement`.
- **Forjados**: macizo, nervado (unidireccional de nervios), reticular (waffle) y **unidireccional con bovedillas** (las bovedillas como `IfcBuildingElementPart`, coloreables aparte).
- **Vigas / miembros**: perfil en **I** (doble T), tabla IPE/HEB.
- **Zapatas**: pad + pedestal.
- **Puertas / ventanas**: marco + hoja / vidrio.
- **Rampas**: rectas, en tijera (scissor) y **peldañeadas**.
- **Escaleras**: peldañeado, **meseta**, **giro en U**, **zanca**.

### 2.3 Catálogo bsDD (cobertura del estándar)
- `catalogo_ifc.py` **deriva del esquema IFC4X3** las **~150 clases concretas de `IfcElement`** (los 11 grupos: constructivo, distribución, conjunto, componente, característico, mobiliario, geográfico, geotécnico, transporte, virtual, civil + `IfcVehicle`).
- Cada elemento se instancia con: arquetipo geométrico, **`PredefinedType`** del esquema, **Psets `Pset_*Common`** estándar (plantillas de IfcOpenShell) y la **URI del diccionario IFC de bsDD** como `IfcClassificationReference`.
- `generar_galeria.py` produce un IFC con una instancia de cada clase (catálogo navegable); `construir_catalogo.py` vuelca la tabla completa a `catalogo-ifc4x3.json`.
- Primitiva genérica **`elementos`** en el flujo de narración: «pon una viga / zapata / puerta…».

### 2.4 Validación integrada (doble modo)
- `validar.py`, cableado en `spec_to_ifc.py`:
  - **Informe** (por defecto): lista ERROR / AVISO / INFO, no bloquea.
  - **Puerta** (`--estricto`): falla si hay ERROR duro (esquema, unidad SI, contexto geométrico, GlobalId duplicado, `RelVoids`/`RelFills` íntegros, representación no vacía).
- Las primitivas nativas añaden sus `Pset_*Common` → **modelos sin avisos**.

### 2.5 Empaquetado permanente
- Todo el compilador es la skill **`narracion-a-ifc`** dentro del plugin **`iso19650-openbim` v0.8.2**, junto a `ifc-create`, `bsdd-clasificacion` e `ifc-validate`, que reutiliza.
- Pasa la puerta de empaquetado (`verificar_empaquetado.py`): núcleo transversal espejado **intacto** (md5), sin truncados, `description` dentro de límite.

---

## 3. Entregables de este hilo

- **`iso19650-openbim-v0.8.2.plugin`** (raíz del proyecto) — versión a instalar.
- Carpeta **`narracion-ifc/`**: `compilar_spec.py`, `spec_to_ifc.py`, `catalogo_ifc.py`, `construir_catalogo.py`, `generar_galeria.py`, `validar.py`, `spec.schema.json`, `catalogo-ifc4x3.json`, `SKILL.md`, `LEEME.md` y los specs/IFC de demostración.
- Modelos demo registrados en el **visor** (`visor/models/manifest.json`): `edificio-demo`, `edificio-oficinas`, `parking` (4 plantas 25×150 con rampas en tijera), `familias`, `galeria`, `demo-v05` (hueco real + reticular + escalera), `demo-v06` (unidireccional + escalera en U + rampa peldañeada).

---

## 4. Pendiente de trabajo

### 4.1 Capa 2 — edición paramétrica en vivo en el visor (siguiente gran bloque)
Convertir el visor de mirador a **editor paramétrico**: que el modelo recuerde su spec y se pueda modificar sobre lo que se ve. Quedó **explicada y con el primer corte por decidir**:

- **C — Round-trip del spec (cimiento):** enlazar modelo↔spec y montar cambio → regenerar → recargar en caliente preservando vista. Habilita a las otras dos.
- **A — Panel de propiedades editable:** seleccionar y editar parámetros del elemento (lo más tangible; geometría depende de C).
- **B — Edición narrada en contexto:** órdenes sobre el modelo abierto («sube los pilares a 4 m»), mutando el spec (lo más potente; semántica más difícil).

> **Decisión abierta clave:** dónde se ejecuta la regeneración. El visor es HTML offline (web-ifc) y el generador es Python/IfcOpenShell → o un **proceso local** que sirva de backend, o que el **agente** haga de backend en Cowork. Esto se resuelve dentro de C.

Recomendación registrada: **C + gancho mínimo demostrable**, luego A, luego B.

### 4.2 Mejoras menores del generador
- Encadenar `ifc-validate` para auditoría de **dominio** (continuidad de red MEP, alineación/georref en obra lineal) cuando el modelo lo tenga.
- Geometría real de más familias: cubierta inclinada, forjado reticular con casetones (recuperables/perdidos), muro multicapa.
- `PredefinedType` por defecto «típico» por clase (hoy toma el primer valor válido del enum).

### 4.3 Operativa
- **Reinstalar `iso19650-openbim` v0.8.2** en Cowork para que la skill quede activa en cualquier hilo.

---

## 5. Notas técnicas y *hazards* del entorno (para el próximo hilo)

- **Toolchain:** IfcOpenShell 0.8.5 + jsonschema. Tras reinicio del sandbox, `/tmp` se vacía y `/tmp/pylibs` puede quedar parcial/read-only → reinstalar en `/var/tmp/pylibs` y usar `PYTHONPATH=/var/tmp/pylibs:/tmp/pylibs`.
- **`/tmp` es un tmpfs pequeño:** pip y `verificar_empaquetado.py` (extrae a temporal) fallan con *No space left on device* → usar `TMPDIR=/var/tmp/...`.
- **Bug de IfcOpenShell:** `geom.settings().set("use-world-coords", True)` devuelve coordenadas basura en extrusiones rectangulares → verificar con verts locales + `sh.transformation.matrix`. **No afecta al entregable** (el visor usa web-ifc, que lee el STEP directamente).
- **Mount:** el shell puede leer/escribir copias **truncadas** de ficheros del montaje (markdown y `manifest.json` incluidos) → editar esos ficheros **solo con herramientas de fichero**, y empaquetar construyendo el ZIP en `/tmp` y copiando con `cat >`.
- **Empaquetado:** plugin instalado read-only (copiar a `/tmp` + `chmod`); no sobrescribir el `.plugin` (nombre versionado); `description` del `plugin.json` **≤ 500 caracteres** o la instalación lo rechaza; **no tocar `scripts/nucleo/`** (espejo byte a byte).
