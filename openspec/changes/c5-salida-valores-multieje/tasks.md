# Tareas · `valores{}` en la salida de C5 (E1.1)

> Gobernado por `docs/PROCESO_SDD.md` y `docs/openspec-tasks-mandatory-steps.md`. Contract-first:
> esquema + no-regresión de la golden **antes** que cualquier engine. **Baby steps, solo lo afectado.**
> El contrato C5 está en la frontera CODEOWNERS → el merge es firma de JM (Llave 2).

## Paso 0 · Ratificación (BLOQUEA el código)
- [ ] JM ratifica **D16** (coste no se duplica; `valores` = ejes no-coste), **D17** (id de eje = string
      libre, no enum) y **D18** (`etapas` opcional, Σ etapas = total). OK explícito ANTES del apply.

## Paso 1 · Rama (primero, tras ratificar)
- [ ] Crear y cambiar a `feat/c5-salida-valores-multieje` desde `origin/main` (git por `.bat` en el host).

## Paso 2 · Delta de esquema (apply)
- [ ] Añadir `$defs.valor_eje` y la propiedad opcional `valores` a `$defs.partida_medida` en
      `packages/contracts/C5-presupuesto/salida-presupuesto.schema.json` (ver `design.md §1`; el
      esquema completo propuesto está en `proposed/salida-presupuesto.schema.json` de este change).
- [ ] `precio_unitario`/`importe`/`origen`/`trazabilidad`/cuadros/`resumen` **sin tocar**.

## Paso 3 · No-regresión de la golden (la Llave 1 de E1.1)
- [ ] Validar `packages/golden/C5/GOL-PRE-01/expected.json` (`expected["presupuesto"]`) contra el
      esquema extendido: **conforme, sin editar el expected** (ni su md5 de fixtures).
- [ ] Re-ejecutar el runner de C5 afectado (`tools/affected.py` → golden C5): `GOL-PRE-01` **verde y
      byte-idéntica**; `GOL-DOC-01` (C7) verde.

## Paso 4 · Documentación del contrato
- [ ] Nota aditiva en `contrato.md`: `valores{}`, relación con el eje coste canónico (D16), convención
      de nombres de eje (D17), `etapas` EN 15978 (D18).
- [ ] Anclar **D16–D18** en `packages/contracts/C5-presupuesto/DECISIONES.md` (continúan D1–D15).

## Pasos obligatorios (Llave 1)
- [ ] `adversarial-review c5-salida-valores-multieje`: esquema válido (JSON Schema draft 2020-12),
      golden C5 verde, ningún `expected` alterado, ninguna clave existente con semántica cambiada.
- [ ] `versions.lock`: sin cambio de hash del contrato salvo el propio esquema (E1.1 no crea packs).
- [ ] `opsx:archive` → **PR** `feat/c5-salida-valores-multieje` → `main`; gate verde (Llave 1).
- [ ] **Llave 2 = JM** (merge/firma). Sin release en E1.1 (la salida multi-eje se libera con el engine).

## Fuera de estas tareas
- Engine `parametros.eje` (E1.2) · cortes y `proyectar()` (E2) · `banco-carbono`/`GOL-CAR-01` (Ola 2).
