# Núcleo — cierre de PR-E2 (Fase I · hilo 3: piloto de la retirada del espejo del núcleo)

**Decisión previa:** `NUCLEO_PR-E2_decision.md` — (A) copia en build · alcance = solo piloto
`iso19650-openbim` · orden E3…E6 = `instalaciones` → `obras-lineales` → `puentes` → `motor-fem`.

## Qué hace este PR

1. **Build extendido al núcleo.** `tools/build_plugin_iso19650.py` genera
   `scripts/nucleo/{ifc_utils,grafo_red}.py` desde `packages/core/src/aqyra_core/` con prueba
   de identidad md5 (LF) contra `versions.lock [core]`; NO APTO si el build no deriva del
   canónico. Verificado en local: `.plugin` 0.10.0 APTO, hashes en el ZIP == anclajes
   (`ad06f87d…`, `fe5dfebb…`). De paso se cerró un hueco del staging: las carpetas de
   `SKIP_DIRS` se saltan ahora con todo su contenido (antes solo se saltaba la carpeta).
2. **Copia trackeada retirada.** `git rm -r plugins/iso19650-openbim/scripts/nucleo/`
   (incluye `README.md` y `test_grafo_red.py` — el mismo conjunto de comprobaciones vive
   portado a pytest en `packages/core/tests/test_grafo_red.py`, verificado por diff) +
   `.gitignore` de la carpeta generada.
3. **Guardián evolucionado.** `engines/ifc/tests/test_no_reaparicion_espejo.py`:
   `test_nucleo_del_plugin_atado_al_canonico` (copia atada, deuda de PR-E1) →
   `test_nucleo_no_reaparece_fuera_de_core` (falla si reaparece `ifc_utils.py`/`grafo_red.py`
   trackeado fuera de `packages/core/` y `_import/`). Misma mecánica que la regla del engine.
4. **Anclado.** `versions.lock [core] estado` re-anclado: espejo retirado del piloto;
   4 plugins pendientes de re-home.

El miembro de referencia queda **100 % limpio**: sin engine (PR-E1) y sin núcleo (PR-E2),
ambos inyectados en build desde sus fuentes únicas. `_import/` intacto.

## Estado del espejo del núcleo tras PR-E2

| Plugin | Copia `scripts/nucleo/` | Situación |
|---|---|---|
| `iso19650-openbim` | **retirada** (generada en build) | re-homed en `plugins/` (PR-E1 + PR-E2) |
| `instalaciones` | frozen en `_import/` | pendiente re-home → **PR-E3** |
| `obras-lineales` | frozen en `_import/` | pendiente re-home → **PR-E4** |
| `puentes` | frozen en `_import/` | pendiente re-home → **PR-E5** |
| `motor-fem` | frozen en `_import/` | pendiente re-home → **PR-E6** |

## Guion PR-E3…E6 (uno por PR, patrón validado por este piloto)

Para cada plugin, en orden `instalaciones` → `obras-lineales` → `puentes` → `motor-fem`:

1. **Re-home:** extraer el árbol del `.plugin` frozen de `_import/` a `plugins/<nombre>/`
   (como PR-E1 hizo con `iso19650-openbim`; `_import/` no se toca).
2. **Builder:** `tools/build_plugin_<nombre>.py` con inyección del núcleo desde
   `packages/core` + identidad vs `versions.lock [core]` + puerta `verificar_empaquetado`
   (con `--ref` al `.plugin` frozen). Factorizar la inyección común si conviene
   (p. ej. `tools/_inyectar_nucleo.py`).
3. **Retirada:** no commitear `scripts/nucleo/` (el re-home entra ya sin la copia);
   `.gitignore` de la carpeta generada.
4. **Guardián:** `test_nucleo_no_reaparece_fuera_de_core` ya cubre `plugins/<nombre>/`
   automáticamente (regla por nombre de fichero, sin lista de plugins). Solo verificar verde.
5. **Cierre:** `versions.lock [core] estado` + wiring `ci.yml` (paso de build del nuevo
   builder) si procede. `motor-fem` al final: el mayor, y dependencia de `puentes` —
   evaluar en PR-E5 si `puentes` necesita adelantar algo de él.

Cuando los 5 consuman el canónico, el estado de `[core]` pasa a "espejo del núcleo
extinguido" y se evalúa el cierre previsto en `engines/ifc/ESPEJO_plan-retirada.md` §3.

*Procedencia: Fase I · hilo 3 · PR-E2. Antecedentes: `ESPEJO_plan-retirada.md`,
`ESPEJO_PR-E1_cierre.md`. La zona firmada `_import/` no se reescribe.*
