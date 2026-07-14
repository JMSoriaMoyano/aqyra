# Cambio · Operador de ENTREGA C7 v0 — el paquete contractual firmable (presupuesto + pliego)

> Change-id: `c7-entrega-v0` · Capas: `packages/contracts/C7-entrega` (NUEVO) + `services/entrega` (NUEVO) + `packages/golden/C7` (NUEVO) · anclaje (`versions.lock`, `pyproject`, `ci.yml`)
> Historia: forward de la Ola 5 (export firmable A+B+C mergeados, `main` HEAD `fa0f086`). Los compositores/raíl de export ya anticiparon a C7 («el operador C7 orquestará la ENTREGA — NO es el operador C7»).
> Estado: **APPLY** · decisiones **D-C7-1..6 RATIFICADAS por JM 2026-07-13**.
> Tipo: **operador NUEVO contract-first** (ficha + 2 esquemas ANTES del módulo, patrón C4/C5). Solo AÑADE; no toca el núcleo de export ni los compositores ni los motores.

## Por qué

La maquinaria de sellar+firmar UN entregable existe y está probada 3× (`documentos/export.componer_export`
+ consumidores `presupuesto-obra`/`pliego-obra`). Falta el **operador que orquesta un PAQUETE de
entregables como una unidad**, con un manifiesto de entrega maestro. C7 v0 lo cierra: convierte «sellar
un entregable» en «orquestar una entrega», de forma **determinista** (sin LLM), envolviendo el raíl que
ya existe y añadiendo el roll-up que ata los N bundles al mismo Maestro.

## Qué cambia (superficie) — todo AÑADE

- **`packages/contracts/C7-entrega/`** (NUEVO) — `contrato.md` (ficha 6 campos, reconciliada con
  `Aqyra-Raiz/C7_operador.md`) + `solicitud-entrega.schema.json` + `manifiesto-entrega.schema.json`
  (forward-open, JSON Schema 2020-12) + `DECISIONES.md` (D-C7-1..6).
- **`services/entrega/`** (NUEVO, uv `aqyra-entrega`, hermano de `services/federacion`) —
  `entrega.py` (`componer_entrega(solicitud, parametros?)`: valida, itera los entregables llamando a
  `componer_export`, ensambla el `manifiesto-entrega` con roll-up) + `manifiesto_entrega.py` (construir +
  serializar determinista + integridad + roll-up `paquete_sha256`) + `__init__.py` + `cli.py` +
  `pyproject.toml` (dep `aqyra-documento-export`) + `tests/test_entrega.py`. **No reimplementa
  sellado/firma: los reúsa.**
- **`packages/golden/C7/GOL-EN-01/`** (NUEVO) — `entrada.json` (la solicitud presupuesto+pliego) +
  `expected.json` + `ficha.md` + `tolerancias.json`.
- **`packages/golden/src/aqyra_golden/run_golden.py`** — `run_case_c7` + `CASE_RUNNERS["C7"]` (+ helper
  `_resolver_artefacto_ref`). Los 2 esquemas de C7 entran solos en el Paso 1 (glob `C*/*.schema.json`);
  el caso entra solo en el Paso 2 (glob `C*/` con `expected.json`).
- **Anclaje** — `versions.lock [contracts.C7]`+`[services.entrega]`; `pyproject [tool.uv.workspace]`
  (+`services/entrega`); `ci.yml` (pytest +`services/entrega`).

## Impacto — por qué NO rompe nada (verificado en local, sin ifcopenshell)

- **No-regresión** `GOL-EXP-01` (presupuesto), `GOL-EXP-03` (pliego), `GOL-PLI-01`: el raíl de export y
  los compositores **no cambian** su comportamiento; C7 los ENVUELVE.
- **Contract-first / forward-open**: 2 esquemas nuevos + service nuevo + golden nuevo; nada existente
  cambia de semántica.
- **Consulta, no cálculo**: el operador LEE los artefactos anclados + envuelve `componer_export`; no
  re-mide, no re-valora, no re-renderiza. Determinista puro (sin LLM).

## Fuera de alcance (forward)

Nuevos consumidores (memoria de cumplimiento C3, memoria de cálculo C9/C10, informe de coordinación C4,
carbono); colocación en el CDE por estado ISO 19650 S0–S7 (C8); `maestro_ref` explícito; orquestación por
matriz LOIN/hito; re-entrega ante cambio de modelo; firma cualificada/PAdES del cliente. **Sin release
nuevo** por defecto (D-C7-6); Llave 2 (merge/firma `entrega-v0.1.0`) = JM.
