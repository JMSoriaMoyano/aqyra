# Tareas · El engine C5 se generaliza a un eje (E1.2)

> Gobernado por `docs/PROCESO_SDD.md`. **EXTIENDE** el engine vivo (forward-open). La golden de coste
> **no se mueve**: cualquier cambio la recomputa idéntica. El contrato C5 está en la frontera
> CODEOWNERS → el merge es firma de JM (Llave 2).

## Paso 0 · Ratificación (BLOQUEA el código) — HECHO
- [x] JM ratifica **D19** (run no-coste = espejo + `valores[eje]` etiquetado; alternativa coste-a-0
      rechazada). OK explícito ANTES del apply (2026-07-08).

## Paso 1 · Rama (primero, tras ratificar)
- [ ] Crear y cambiar a `feat/c5-engine-eje-generalizado` desde `origin/main` (git por `.bat` en el host).

## Paso 2 · Engine (apply) — HECHO en el árbol de trabajo
- [x] `presupuesto.py`: leer `parametros.eje` (default `"coste"`) + `unidad_eje`/`banco_ref`; helper
      `_valor_eje(...)`; guarda `if not es_coste:` en las partidas origen=modelo y origen=regla.
- [x] La rama `eje="coste"` es el código previo **byte a byte** (no emite `valores`).
- [x] Parser de `Qto`, motor económico, cuadros, `resumen`, `escritura.py` y el runner **sin tocar**.

## Paso 3 · No-regresión de la golden (la Llave 1 de E1.2)
- [x] Sandbox (path puro `presupuestar`): `GOL-PRE-01` reproduce PEM 7 022,53 → PEC 10 111,74;
      ninguna partida emite `valores`; `eje="coste"` explícito == default. **Verificado.**
- [ ] En CI, `run_case_c5` (recompute antepuesto) deja `GOL-PRE-01` **verde y byte-idéntica**;
      `GOL-PRE-02` y `GOL-DOC-01` verdes.

## Paso 4 · Test del engine y anclajes
- [x] `tests/test_eje_multieje.py`: coste sin `valores`; `eje=coste`==default; run no-coste rellena
      `valores[eje]` etiquetado (espejo), regla sin banco; mapeo/cantidades intactos entre ejes.
- [x] `pyproject.toml` 0.2.0 → **0.3.0**.
- [x] Anclar **D19** en `DECISIONES.md`; `versions.lock [contracts.C5] engine_version = "0.3.0"` + estado.

## Pasos obligatorios (Llave 1)
- [ ] `adversarial-review c5-engine-eje-generalizado`: engine importa/compila; golden C5 verde; ningún
      `expected` alterado; ninguna clave existente con semántica cambiada.
- [ ] `opsx:archive` → **PR** `feat/c5-engine-eje-generalizado` → `main`; gate verde (Llave 1).
- [ ] **Llave 2 = JM** (merge/firma). **SIN release** en E1.2 (la salida multi-eje se libera con el eje
      carbono, Ola 2).

## Fuera de estas tareas
- Cortes y `proyectar()` (E2) · `banco-carbono`/`GOL-CAR-01` (Ola 2) · ingesta/emisión BC3 (E0).
