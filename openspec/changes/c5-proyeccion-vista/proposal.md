# Cambio · La proyección (`proyectar(presupuesto, modelo, eje, corte)`)

> Change-id: `c5-proyeccion-vista` · Capacidad: `presupuesto` (contrato `C5-presupuesto`)
> Historia del backlog: **E2.2** (`Aqyra-Negocio/BACKLOG_motor-valoracion_para-Aqyra-Raiz.md` §2·E2) · Ola 1
> Procedencia: handoff negocio → desarrollo (`INICIO-hilo_Aqyra-Raiz_motor-valoracion_E2.2.md`, 2026-07-08)
> Estado: **PROPUESTA** · decisiones **D24–D29 RATIFICADAS** por JM (2026-07-08); ancladas en `DECISIONES.md`.
> Tipo: **NUEVO comportamiento** sobre una capacidad viva (engine C5) + **EXTIENDE** la salida (aditivo, forward-open) — no se crea contrato nuevo.
> Cierra la primera de las dos piezas de E2 junto a **E2.1** (`c5-cortes-agrupaciones-nativas`, ya en `main`, PR #50): E2.1 dejó los `cortes` en el modelo; E2.2 los **agrega**.

## Por qué

E2.1 dejó a cada objeto medido su atribución a grupos (`cortes{espacial,funcional,uniclass,gubim}`,
lista de pertenencias `{grupo, fraccion, fuente}`). Falta la **consulta** que responde «¿cuánto vale la
planta 1?», «¿cuánto la zona administrativa?», «¿cuánto los sistemas de clima?»: un **group-by
determinista**, sin recálculo, que reparte el valor que ya existe entre los grupos del corte pedido.
Con esto queda entregado el «valor a tiempo real por clasificación» —ya vendible sobre el eje coste,
sin esperar al carbono (Ola 2)— porque los cortes ya están en el modelo y esta pieza los suma.

## Qué cambia (superficie)

- **`engines/presupuesto/src/aqyra_presupuesto/proyeccion.py`** — NUEVO. `proyectar(presupuesto, modelo,
  eje, corte) → [{grupo, valor_total, unidad, n_partidas, guids[], fuente}]`. **Group-by puro**: no
  re-mide, no re-valora; suma `valor_partida × (cantidad_objeto / Σcantidad) × fraccion` (D24–D27).
- **`engines/presupuesto/src/aqyra_presupuesto/presupuesto.py`** — **aditivo (D26 EXACTA)**: cada partida
  `origen=modelo` gana `traza_cantidades: [{guid, cantidad}]` (la contribución de cantidad de cada objeto
  a esa partida, que el motor ya computa en su bucle). Habilita el reparto por magnitud EXACTA sin que
  `proyectar` re-mida. `GOL-PRE-01` sigue verde: el recompute compara sólo claves nombradas.
- **`packages/contracts/C5-presupuesto/salida-presupuesto.schema.json`** — `partida_medida` gana
  `traza_cantidades` (opcional, aditivo) + `$defs.traza_cantidad`. Forward-open.
- **`packages/golden/C5/GOL-PRE-03/`** — NUEVA golden de **vista** (patrón `GOL-PRE-02`, modo `proyeccion`):
  las CINCO vistas (por planta, por `IfcFacilityPart` 4.3, por `IfcSystem`, por `IfcZone` 50/50, y
  *fallback* criterio) + el invariante `Σ proyección == Σ estado_mediciones`. Fixtures **aumentadas** de
  `GOL-PRE-01` (ARQ/EST + `IfcSystem`+`IfcZone`+espacios+`IfcRelSpaceBoundary`+árbol 4.3, md5 propios).
- **`packages/golden/src/aqyra_golden/run_golden.py`** — `run_case_c5` gana la rama `modo == "proyeccion"`
  (`_run_c5_proyeccion`): mide con `criterio/AQ/v2`, presupuesta, proyecta las 5 vistas y ancla por
  **DETERMINISMO + SEMÁNTICA + INVARIANTE** (D28, patrón D14 — sin md5 de salida hardcodeado).
- **`engines/presupuesto/tests/test_proyeccion.py`** — NUEVO: tests **puros** (sandbox, sin ifcopenshell)
  del invariante Σ, del reparto por magnitud EXACTA y de los residuales (D27).
- **`packages/golden/C5/GOL-PRE-03/gen_fixtures.py`** — generador determinista de las fixtures aumentadas
  (corre en el conda `mcp-bim` de JM; el sandbox no trae ifcopenshell). Sella los md5 que ancla el caso.
- **`packages/contracts/C5-presupuesto/DECISIONES.md`** — se anclan **D24–D29** (continúan D1–D23).
- **`engines/presupuesto/pyproject.toml`** + **`versions.lock [contracts.C5]`** — `engine_version` 0.3.0 → **0.4.0**.

## Impacto — por qué NO rompe nada

- **Forward-open.** `traza_cantidades` es una clave **opcional** nueva en un objeto `additionalProperties:
  true`; ninguna clave existente cambia de semántica. `GOL-PRE-01`/`GOL-PRE-02`/`GOL-DOC-01` intactas
  (el recompute compara claves nombradas; la clave nueva es invisible para ellos).
- **La proyección es consulta, no cálculo.** `proyectar` **agrupa** lo que ya existe; el reparto 50/50 ya
  lo resolvió el parser (E2.1). Invariante `Σ == total` por construcción (D27 conserva Σ con residuales).
- **La zona anclada no se edita.** `GOL-PRE-03` es un **caso NUEVO** (no toca `GOL-PRE-01`); usa
  `criterio/AQ/v2` (ya anclado por su `content_sha256` en E2.1) y `banco/AQ-DEMO/v1`. `[packs.criterio]`
  sigue en `v1` (lo usa `GOL-PRE-01`); la rama `proyeccion` ancla `v2` por su golden de pack.

## Fuera de alcance (fronteras honestas)

- **No** se toca el motor económico (importe/PEM…PEC), los cuadros, el `resumen`, el parser de cortes de
  E2.1 ni el runner base (solo se AÑADE la rama `proyeccion`).
- **No** se crea la familia `banco-carbono` ni `GOL-CAR-01` → Ola 2 (E3). El eje carbono no se adelanta.
- **No** se implementa ingesta/emisión BC3 (E0.1/E0.2) → changes/PRs siguientes del mismo hilo.
- **No** se toca `GOL-PRE-01` (ni su `expected`, ni sus fixtures, ni sus md5 `0b998513…`/`0d7e7f20…`).
- **Sin release** (la proyección es consulta, no un artefacto firmable nuevo; salvo que JM decida). El git
  va por `.bat` en el host; el merge/firma es de JM (Llave 2).
