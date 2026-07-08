# GOL-PRE-03 · Golden de vista (proyección) — E2.2

> Caso **NUEVO** (patrón `GOL-PRE-02`), modo `proyeccion`. Ancla la consulta `proyectar(eje, corte)`
> (D24–D29): el «valor a tiempo real por clasificación». NO edita `GOL-PRE-01`/`GOL-PRE-02` (intactas).
> La proyección es **consulta, no cálculo**: `proyectar` AGRUPA lo que ya existe.

## Qué ancla (D28 — patrón D14, sin md5 de salida)

1. **Identidad** — md5 de las fixtures **aumentadas** `entrada/ARQ.ifc`+`EST.ifc` (nuevas; las de
   `GOL-PRE-01`, `0b998513…`/`0d7e7f20…`, quedan intactas).
2. **Pack** — `criterio/AQ/v2` anclado por su `content_sha256` (`079c28e9…`, golden de pack de E2.1);
   `banco/AQ-DEMO/v1`. `[packs.criterio]` sigue en `v1` (lo usa `GOL-PRE-01`).
3. **Presupuesto** — reproduce el PEM/PEC de referencia (la geometría medida no cambia al aumentar las
   agrupaciones): PEM 7 022,53 → PEC 10 111,74 EUR.
4. **DETERMINISMO** — `proyectar` 2× por vista → misma salida.
5. **INVARIANTE** — `Σ valor_total == Σ estado_mediciones` del eje (== PEM en coste), ±0,01.
6. **SEMÁNTICA (las 5 vistas)** — `expected.vistas[]` (grupos, `valor_total`, `fuente`) casan con la
   proyección recomputada.

## Las cinco vistas (acceptance E2.2)

Cinco **aspectos** de la acceptance, cubiertos por **3 proyecciones distintas** (el runner recomputa
`proyectar` una vez por `(eje, corte)` y comprueba los grupos/valores/fuente):

| proyección | eje | corte | aspectos que cubre |
|---|---|---|---|
| `i-planta` | coste | espacial | (i) por planta (árbol espacial; `fuente=ifc`) |
| `ii-uniclass` | coste | uniclass | (ii) por clasificación Uniclass — **sustituye a ii-facility 4.3** (ver **Nota 4.3**) |
| `iii-v-funcional` | coste | funcional | (iii) `IfcSystem` (`fuente=ifc`) + (iv) `IfcZone` **50/50** del tabique (fraccionario; Σ zonas == total) + (v) *fallback* del criterio (`fuente=criterio`), TODOS en una proyección |

El eje `funcional` es uno por objeto (prioridad `IfcSystem` > `IfcZone` > *fallback*): en **una**
proyección funcional conviven grupos `ifc` (system), `ifc` fraccionarios (zona 50/50) y `criterio`
(fallback) — así iii/iv/v se comprueban juntos.

## Fixtures aumentadas (D29)

`gen_fixtures.py` (conda `mcp-bim`) parte de las de `GOL-PRE-01` y les inyecta de forma **determinista**:
`IfcSystem` (agrupa parte de la estructura), `IfcZone`+`IfcSpace`+`IfcRelSpaceBoundary` (un tabique entre
dos zonas → 50/50), dejando otros objetos **sin** agrupación (para la vista *fallback*). Escribe las
fixtures con **md5 propios** y **hornea** `entrada.json`+`expected.json` (invariante + las 5 vistas).

**Nota 4.3 (`ii-facility`).** Las fixtures de `GOL-PRE-01` son **IFC4**; `IfcFacility`/`IfcFacilityPart`
son entidades **IFC4X3**. La vista `ii-facility` se materializa generando las fixtures aumentadas en
**IFC4X3** con un `IfcFacilityPart` en la ruta espacial (opción por defecto de `gen_fixtures.py`), o —si
JM lo prefiere para v0— se colapsa con `i-planta` y el nodo 4.3 queda como gancho forward. **Punto a
ratificar en el bucle local** (candidato a D30).

## Cómo se genera / verifica (dos llaves)

- **Local (conda `mcp-bim`):** `GEN_gol-pre-03.bat` → `gen_fixtures.py` (fixtures + `entrada.json` +
  `expected.json`); luego `pytest engines/presupuesto` + `run_golden` de `C5` (todas verdes).
- **Llave 1:** gate verde en CI (`GOL-PRE-01/02`/`GOL-DOC-01` byte-idénticas; `GOL-PRE-03` verde).
- **Llave 2:** merge/firma de JM. **Sin release** (la proyección es consulta).

*Regla de oro: un fallo se corrige en el engine (`proyeccion.py`/`presupuesto.py`), jamás aflojando el
check. El oráculo de las vistas es consistencia + no-regresión + invariante, no verdad física.*
