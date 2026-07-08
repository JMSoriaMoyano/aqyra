# Cambio · Los cortes nacen del IFC (`cortes{espacial,funcional,uniclass,gubim}`)

> Change-id: `c5-cortes-agrupaciones-nativas` · Capacidad: `presupuesto` (contrato `C5-presupuesto`)
> Historia del backlog: **E2.1** (`Aqyra-Negocio/BACKLOG_motor-valoracion_para-Aqyra-Raiz.md` §2·E2) · Ola 1
> Procedencia: handoff negocio → desarrollo (`INICIO-hilo_Aqyra-Raiz_motor-valoracion_E2.md`, 2026-07-08)
> Estado: **PROPUESTA** · decisiones **D20–D23 PENDIENTES de ratificación** por JM (bloquean el código).
> Tipo: **EXTIENDE** una capacidad viva (contrato C5 + parser del engine) — forward-open, no se crea contrato nuevo.
> Gobierna: **D-028 / N-06** (cortes = agrupaciones nativas del IFC; frontera 50/50; criterio como *fallback*).

## Por qué

El objetivo de negocio (N-06) es **valorar rápido una PARTE del modelo** —«el coste de la planta 1»,
«el coste de la zona administrativa», «el coste de los sistemas de climatización»— preguntándola en
lenguaje natural o eligiéndola en la ventana de coste. Una «parte» es siempre una **agrupación que el
modelo ya porta**; el corte es un `group-by` sobre esa agrupación (**consulta, no cálculo**).

E2.1 es la primera de las dos piezas que hacen esto posible: **que cada objeto medido lleve su
atribución a grupos** por los cuatro cortes `cortes{espacial, funcional, uniclass, gubim}`, leídos de
las **agrupaciones nativas del IFC** (D-028), con traza del origen del dato (`fuente ∈ {ifc, criterio}`).
La proyección (`proyectar`) es E2.2, el segundo change de este hilo.

## Qué cambia (superficie)

- **`packages/contracts/C5-presupuesto/entrada-presupuesto.schema.json`** — `objeto_medicion` gana la
  propiedad **opcional** `cortes` (aditiva, forward-open): un objeto con hasta cuatro ejes
  (`espacial`, `funcional`, `uniclass`, `gubim`), cada uno una **lista de pertenencias**
  `[{grupo, fraccion, fuente}]` (D20). Sin agrupación → ausente, nunca error.
- **`engines/presupuesto/src/aqyra_presupuesto/modelo.py`** — nuevos lectores del IFC:
  árbol espacial (incl. IFC 4.3 `IfcFacility`/`IfcFacilityPart`), `IfcSystem` (agrupa elementos),
  `IfcZone`→`IfcSpace`→elemento vía `IfcRelSpaceBoundary` con **reparto de frontera** (D21), y la
  clasificación (Uniclass/GuBIM) que ya lee.
- **`engines/presupuesto/src/aqyra_presupuesto/medicion.py`** — `_objeto_neutro` adjunta `cortes` al
  objeto neutro; el *fallback* del criterio rellena `funcional` cuando no hay agrupación nativa (D22).
- **`data/packs/criterio/AQ/v2/`** — **nueva versión anclada** del pack criterio = `v1` + la tabla
  `reglas_sistema` (clase/uso → sistema grueso) del *fallback* (D22). `v1` y `GOL-PRE-01/02` intactos.
- **`engines/presupuesto/tests/test_cortes.py`** — NUEVO: (1) tests **puros** del reparto 50/50 y del
  fallback (sin ifcopenshell, corren en CI); (2) test de **integración** que construye un IFC4 mínimo
  (árbol + `IfcSystem` + `IfcZone`+espacios+`IfcRelSpaceBoundary`) y verifica los cortes completos, el
  50/50 en un tabique compartido y el fallback (`fuente=criterio`). El caso de referencia del E2.1 es
  un modelo mínimo *self-built*; las **fixtures aumentadas de `GOL-PRE-01`** y la golden de vista
  `GOL-PRE-03` (D23) son de **E2.2**. `GOL-PRE-01` **no se toca**.
- **`packages/packs/tests/test_packs.py`** — tests de `criterio/AQ/v2` (manifiesto + identidad de
  contenido por hash + superset de v1).
- **`packages/contracts/C5-presupuesto/DECISIONES.md`** — se anclan **D20–D23** (continúan D1–D19).
- **`versions.lock`** — `[contracts.C5]` sube `schema_version` (la entrada gana `cortes`). **NO** se
  re-ancla `[packs.criterio]`: sigue en `v1` (lo usa `GOL-PRE-01`); `v2` se ancla por su propio
  `content_sha256` (golden de pack) y el contrato lo **adopta en E2.2** (cuando `GOL-PRE-03` lo referencie).

## Impacto — por qué NO rompe nada

- **Forward-open.** `cortes` es una clave **opcional** nueva en un objeto que ya es
  `additionalProperties: true`; ninguna clave existente cambia de semántica. Un objeto sin agrupación
  no lleva `cortes` (o lleva ejes vacíos) → nunca error. `GOL-PRE-01` es byte-idéntica (su medición no
  mira `cortes`; el eje coste sigue en `precio_unitario`/`importe`).
- **El corte es consulta, no cálculo.** El reparto 50/50 se resuelve **al construir el modelo neutro**
  (atribución, en el parser), no en la proyección (N-06). E2.2 solo suma `valor × fraccion`.
- **La zona anclada no se edita.** El *fallback* llega como **`criterio/AQ/v2` nuevo** (no re-ancla
  `v1`); las fixtures de cortes son **nuevas** (no editan las de `GOL-PRE-01`, md5 `0b998513…`/`0d7e7f20…`).

## Fuera de alcance (fronteras honestas)

- **No** se implementa `proyectar()` ni la golden de vista → eso es **E2.2** (segundo change del hilo).
- **No** se crea la familia `banco-carbono` ni `GOL-CAR-01` → Ola 2 (E3).
- **No** se toca el motor económico, los cuadros, el `resumen`, el write-back 5D (`escritura.py`) ni el
  runner de golden.
- **No** se toca `GOL-PRE-01` (ni su `expected`, ni sus fixtures, ni su md5), ni `GOL-PRE-02`/`GOL-DOC-01`.
- **Sin release** (los cortes son consulta, no un artefacto firmable nuevo). El git va por `.bat` en el
  host; el merge/firma es de JM (Llave 2).
