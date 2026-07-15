# Cambio · Ingesta FIEBDC-3/2024 (`.bc3`) → pack `banco` (E0.1)

> Change-id: `c5-bc3-ingesta` · Capacidad: `presupuesto` (contrato `C5-presupuesto`) · frontera C1/C5
> Historia del backlog: **E0.1** (`Aqyra-Negocio/BACKLOG_motor-valoracion_para-Aqyra-Raiz.md` §2·E0) · Ola 1
> Procedencia: handoff negocio → desarrollo (`INICIO-hilo_Aqyra-Raiz_motor-valoracion_E0-BC3.md`, 2026-07-08)
> Estado: **PROPUESTA** · decisiones **D30–D33 ratificadas** por JM (2026-07-08, «las de mayor recorrido futuro»).
> Tipo: **NUEVO** adaptador de frontera (no toca esquema de contrato: reutiliza el esquema de banco).
> Gobierna: **D-026 / N-04** (política de datos 3+2; el `.bc3` de muestra es PROPIO; redistribuir bases
> públicas espera a la verificación de licencia por JM).

## Por qué

El presupuesto de Aqyra debe **entrar y salir** en el formato del despacho y de la licitación pública
española, **FIEBDC-3/2024** (`.bc3`) — «OpenBIM, sin cautividad»: un banco real (BCCA, Extremadura o
el del cliente) entra como **pack anclado**, y el presupuesto sale a Presto/Arquímedes/TCQ y a la mesa
de contratación. E0.1 es la primera de las dos piezas: la **ingesta** de un banco `.bc3` → pack `banco`
con el **mismo esquema** que `AQ-DEMO`. La emisión (`salida-presupuesto` → `.bc3`) es E0.2, el siguiente
change de este hilo.

La interoperabilidad es **traducción determinista, no cálculo**: el mismo `.bc3` produce el mismo
`banco.json` byte a byte, anclable por hash.

## Qué cambia (superficie)

- **`engines/bc3/`** — **paquete uv NUEVO** `aqyra-bc3` (releaseable; v0 SIN release), texto puro
  (stdlib, sin ifcopenshell → corre en CI y en el sandbox). `aqyra_bc3.ingerir_bc3(path) → banco.json`
  (esquema AQ-DEMO). Subset FIEBDC-3 v0 `~V/~C/~D/~T` (D31); precio compuesto Σsub+CI con guarda (D32).
  CLI `aqyra-bc3 ingerir …`.
- **`data/packs/banco/AQ-BC3-DEMO/v1/`** — pack de muestra NUEVO: `banco.json` (ingerido), `pack.json`
  (manifiesto), `golden/expected.json` (`content_sha256`) y `fuente/muestra.bc3` (el `.bc3` PROPIO/
  sintético, D-026, provenance auditable). `[packs.banco]=AQ-DEMO/v1` **intacto**.
- **`engines/bc3/tests/test_bc3.py`** — golden del **parser**: `ingerir_bc3(fuente/muestra.bc3)`
  **reproduce** el `banco.json` anclado (determinismo 2×, transcodificación ANSI→UTF-8, naturaleza de
  componentes, precio compuesto, guarda de consistencia). Corre en CI (texto puro).
- **`packages/packs/tests/test_packs.py`** — golden **de pack** de `banco/AQ-BC3-DEMO/v1` (manifiesto
  válido + versión anclada `banco_bc3` + identidad por `content_sha256` + `md5(banco.json)` +
  `md5(muestra.bc3)`), patrón de los demás packs anclados.
- **`versions.lock`** — sección NUEVA `[packs.banco_bc3]` (id `AQ-BC3-DEMO`, familia `banco`, `v1`).
  **NO** re-mueve `[packs.banco]` (sigue en `AQ-DEMO/v1`).
- **`pyproject.toml`** (raíz) — `engines/bc3` como miembro de `[tool.uv.workspace]`.
- **`.github/workflows/ci.yml`** — `engines/bc3` añadido al `pytest` del Paso 1 (Llave 1).
- **`packages/contracts/C5-presupuesto/DECISIONES.md`** — se anclan **D30–D33** (continúan D1–D29).
- **`packages/contracts/C5-presupuesto/contrato.md`** — nota en «Frontera»: el `banco_ref` puede
  materializarse por ingesta BC3 (`engines/bc3`); aditivo, no cambia la semántica del contrato.

## Impacto — por qué NO rompe nada

- **No toca ningún esquema de contrato** (ni entrada ni salida de C5): la ingesta produce un pack
  `banco` con el esquema ya existente. `schema_version` de C5 **no se mueve**.
- **La zona anclada no se edita.** El banco de muestra es un pack **NUEVO** bajo su propia ruta; el
  golden de coste `GOL-PRE-01/02/03`, el `GOL-DOC-01`, los packs `criterio/AQ/v1`+`v2` y
  `banco/AQ-DEMO/v1` quedan **intactos** (identidad por hash preservada).
- **Traducción determinista.** El `banco.json` se reproduce del `.bc3` con el adaptador (golden del
  parser) → no hay drift silencioso; el pack se ancla por `content_sha256` + `md5`.
- **D-026.** El `.bc3` de muestra es **PROPIO/sintético**: no redistribuye ninguna base pública ni
  licenciada. Las semillas reales (BCCA/Extremadura, E5.1) usan este MISMO adaptador, tras la
  verificación de licencia por JM.

## Fuera de alcance (fronteras honestas)

- **No** se implementa la emisión `salida-presupuesto` → `.bc3` → eso es **E0.2** (siguiente change).
- **No** se ingieren bases públicas reales (BCCA/Extremadura) → **E5.1**, tras la verificación de
  licencia por JM (D-026).
- **No** se lee el `~M` (mediciones) ni el `%CI` del propio BC3 en v0 (ganchos forward: E0.2 y refino).
- **No** se toca el engine `engines/presupuesto`, el motor económico, los cuadros ni el runner de golden.
- **Sin release** (la ingesta es interop, no un artefacto firmable nuevo; el tag de `aqyra-bc3` = Llave 2
  cuando JM lo decida, probablemente al cerrar E0.2). El git va por `.bat` en el host; el merge/firma es
  de JM (Llave 2).
