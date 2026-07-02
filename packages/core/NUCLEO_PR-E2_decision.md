# Núcleo — decisión PR-E2 (Fase I · hilo 3: retirada del espejo del núcleo)

**Fecha:** 2026-07-02 · **Decisor:** JM · **Contexto:** con el núcleo canónico en
`packages/core/src/aqyra_core/` (`ifc_utils.py` + `grafo_red.py`, anclados en
`versions.lock [core]`) y el patrón de *consumo por build* probado en el engine (PR-E1),
queda retirar las copias duplicadas de `scripts/nucleo/` que viven en 5 plugins.

## Decisión 1 — Modo de consumo: **(A) copia en build desde `packages/core`**

El empaquetado de cada plugin genera `scripts/nucleo/{ifc_utils,grafo_red}.py` copiando
desde `packages/core/src/aqyra_core/`, con **prueba de identidad** md5 (LF) contra
`versions.lock [core]`. La carpeta generada queda **gitignored**: ninguna copia trackeada.

*Por qué no (B) `import aqyra_core`:* los scripts de los skills corren **standalone** en el
sandbox del plugin, sin site-packages garantizado → riesgo de runtime; y el `.plugin`
tendría que empaquetar el paquete de todos modos. (A) reutiliza el patrón ya probado en
PR-E1: mismo builder, mismo guardián, misma puerta `verificar_empaquetado`.

## Decisión 2 — Alcance de PR-E2: **solo el piloto `iso19650-openbim`**

PR-E2 retira la copia trackeada de `plugins/iso19650-openbim/scripts/nucleo/` y deja el
miembro de referencia **100 % limpio**: sin engine (PR-E1) y sin núcleo (este PR), ambos
inyectados en build desde sus canónicos. Los otros 4 plugins (`motor-fem`,
`obras-lineales`, `instalaciones`, `puentes`) **no están en el monorepo** (solo `.plugin`
frozen en `_import/`): su retirada exige re-home previo y entra por PR incremental.

Nota: `scripts/nucleo/README.md` y `test_grafo_red.py` del plugin se retiran con la
carpeta — el test es el mismo conjunto de comprobaciones ya portado a pytest en
`packages/core/tests/test_grafo_red.py` (verificado por diff); el `.plugin` no los
necesita en runtime.

## Decisión 3 — Orden de re-home (PR-E3…E6)

**`instalaciones` → `obras-lineales` → `puentes` → `motor-fem`** — de menor a mayor
complejidad estimada: valida el re-home con los plugins más contenidos y deja
`motor-fem` (el mayor, y dependencia de `puentes`) para el final, con el patrón rodado.
Cada PR: re-home a `plugins/<nombre>/` + builder con inyección de núcleo + retirada de
la copia + guardián verde.

## Definición de hecho de PR-E2

1. `tools/build_plugin_iso19650.py` genera `scripts/nucleo/` desde `packages/core` con
   identidad vs `versions.lock [core]`; `.plugin` APTO por la puerta.
2. Ninguna copia del núcleo trackeada bajo `plugins/` (`git rm` + `.gitignore`).
3. Guardián `test_no_reaparicion_espejo.py` evolucionado: falla si reaparece copia
   trackeada de `ifc_utils.py`/`grafo_red.py` fuera de `packages/core/` y `_import/`.
4. `versions.lock [core] estado` re-anclado; nota de cierre con guion PR-E3…E6.

*La zona firmada `_import/` no se toca. Plan base: `engines/ifc/ESPEJO_plan-retirada.md`;
antecedente: `engines/ifc/ESPEJO_PR-E1_cierre.md`.*
