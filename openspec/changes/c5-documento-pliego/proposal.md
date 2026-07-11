# Cambio · Compositor de PLIEGO de condiciones técnicas — `documentos/pliego` (E4.1) + textos base (E5.3)

> Change-id: `c5-documento-pliego` · Capa: `documentos/` (operada por C7) · Consume: contrato `C5-presupuesto`
> Historia del backlog: **E4.1** + **E5.3** (`Aqyra-Negocio/BACKLOG_motor-valoracion_para-Aqyra-Raiz.md` §2·E4, §2·E5.3, §3 Ola 3)
> Procedencia: handoff negocio → desarrollo (`INICIO-hilo_Aqyra-Raiz_motor-valoracion_Ola3-pliego.md`, 2026-07-11), continuación tras el cierre de la Ola 2 · CARBONO (E3 PR #54 + E5.2 PR #55, `main` 2d12505).
> Estado: **PROPUESTA** · decisiones **D1–D7 (del documento/pliego) a ratificar** por JM.
> Tipo: **NUEVO documento, patrón conocido** — segundo compositor de la capa `documentos/`, espejo de `documentos/presupuesto`. **CONSUME** la salida C5 (medición + `valores`); **NO** toca contrato, esquema, motor ni golden existentes.
> Gobierna: **D5 (§«el pliego como consumidor tipo C7» del BRIEF)**, **N-07/D-e** (orden de olas: coste → carbono → **PLIEGO** → dashboard), **N-04/D-026** (política de datos 3+2: la ingesta/redistribución de cada fuente pública queda supeditada a la verificación de su licencia por JM — se aplica a los textos base E5.3).

## Por qué

El motor de valoración ya produce, sobre la MISMA medición trazable al objeto, el **coste** (`valores.coste`/`precio_unitario`·`importe`, Ola 1) y el **carbono** (`valores.carbono` con etapas A1A3/A4A5, Ola 2). Falta la tercera pata del trío: la **prescripción** — el pliego de condiciones técnicas que dice *cómo* debe ser y ejecutarse cada partida, ligado al objeto y firmable.

E4.1 construye ese cierre como **documento**, no como eje de valor: un `componer_pliego(presupuesto, criterio, parametros) → .docx` **determinista, sin LLM**, que —igual que `componer_documento` hizo con el presupuesto— **COMPONE** salidas autoritativas ya calculadas (no recalcula) en el pliego del despacho, trazable partida→objeto. Cierra el trío **coste + carbono + prescripción** sobre una sola medición.

E5.3 alimenta la prescripción con **texto base**: en v0, una **semilla PROPIA** de Aqyra (como `banco/AQ-DEMO/v1` sembró el coste y `banco-carbono/generico/v1` sembró el carbono), para NO bloquear E4.1 en la puerta de licencia; el texto normativo **REAL** (PG-3/PG-4 del Ministerio de Transportes y los Documentos Básicos del CTE del BOE) entra por la **vía limpia** — registro de licencias tipo `RECONCILIACION`, ratificado por JM (N-04) — como adición posterior.

## Qué cambia (superficie)

- **`documentos/pliego/`** (NUEVO) — paquete uv `aqyra-documento-pliego` 0.1.0, espejo de `documentos/presupuesto`: `componer_pliego(presupuesto, criterio, parametros?) → Path`. `compositor.py` (mapea JSON→secciones del pliego), `formato.py` (formato del despacho, in-repo/hermético), `cli.py`, `__init__.py`, `tests/`. Determinista, sin LLM. **No recalcula.**
- **`data/packs/pliego-textos/AQ-DEMO/v1/`** (NUEVO, si D5=A) — semilla **PROPIA** de textos de prescripción por tipo de unidad/partida (7 partidas de `GOL-PRE-01`), Aqyra-authored, marcada **demo**. `textos.json` + `pack.json` + `golden/expected.json` (`content_sha256` + md5). Nueva familia `pliego-textos` en el enum de `pack.schema.json` (aditivo, patrón `banco-carbono`).
- **`packages/golden/C5/GOL-PLI-01/`** (NUEVO) — caso de la capa de documentos: `expected.json` (`modo:"pliego"`, `fuente_presupuesto:"GOL-PRE-01"`), `ficha.md`, `tolerancias.json`. Conformidad por **CONTENIDO extraído** (python-docx, NO bytes/píxeles), patrón `GOL-DOC-01`.
- **`packages/golden/src/aqyra_golden/run_golden.py`** — rama de modo `pliego` bajo `run_case_c5` (dispatch `expected.modo=="pliego"`, patrón de las ramas `documento`/`carbono`). Sin runner nuevo en `CASE_RUNNERS`.
- **`versions.lock`** — fila nueva `[documentos.pliego]` (espejo de `[documentos.presupuesto]`) + `[packs.pliego_textos]` (si D5=A). `[documentos.presupuesto]` y todos los packs/goldens anclados **intactos**.
- **`documentos/pliego/DECISIONES.md`** (NUEVO) — se anclan **D1–D7** del documento/pliego.
- **`Aqyra-Negocio/RECONCILIACION_licencias-pliego.md`** (NUEVO, negocio) — registro de la verificación de licencia de PG-3/PG-4 y CTE DB (E5.3 REAL), patrón `RECONCILIACION_licencias-carbono.md`. **Condición suspensiva** para anclar cualquier texto normativo real.

## Impacto — por qué NO rompe nada (forward-open verificable)

- **El motor no se toca.** `engines/presupuesto` 0.5.0 y el esquema de salida C5 quedan intactos: el pliego LEE `estado_mediciones[]` + `valores` y no escribe en la salida.
- **El eje coste y el eje carbono, intactos.** `GOL-PRE-01/02/03`, `GOL-CAR-01/02` y `GOL-DOC-01` byte-idénticas; packs `criterio/AQ/v1`+`v2`, `banco/AQ-DEMO/v1`, `banco/AQ-BC3-DEMO/v1`, `banco-carbono/generico/v1`+`v2` intactos por hash.
- **La capa de documentos crece por adición.** `documentos/presupuesto` 0.1.0 (firmado) no se toca: el pliego **espeja** su `formato.py` (no lo importa), como el presupuesto espejó el skill `memoria-calculo-despacho` (hermeticidad + desacoplo de versiones).
- **El pliego es traducción determinista.** Mismo `presupuesto` + mismo `criterio` + mismo pack de textos + mismos `parametros` → mismo CONTENIDO extraíble. Sin LLM en el gate.
- **La puerta de licencia protege lo público.** E5.3 real (PG-3/CTE) **no** se ancla hasta que JM verifique y ratifique su licencia (N-04). E4.1 avanza con la semilla PROPIA, sin depender de esa puerta.

## Fuera de alcance (fronteras honestas)

- **No** se reempaqueta PG-3/PG-4 ni CTE DB sin verificar su licencia de redistribución (N-04); en v0 la prescripción es una semilla PROPIA de Aqyra.
- **No** se toca el eje coste, el eje carbono, sus packs/goldens, el esquema de salida C5, ni el motor.
- **No** se importa `documentos/presupuesto` (paquete firmado); su `formato.py` se **espeja**.
- **No** entra el dashboard (E6, Ola 4) ni el write-back del pliego al IFC.
- **Sin release** salvo que JM lo decida. Git por `.bat` en el host; merge/firma = JM (Llave 2).
