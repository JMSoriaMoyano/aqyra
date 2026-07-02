# NÚCLEO · PR-E5 — Decisión: re-home de `puentes` desde el FROZEN v0.6.0 (fuente en disputa resuelta)

**Fecha:** 2026-07-02 · **Decisor:** JM · **Contexto:** Fase I · hilo 6. Guion anclado en
`NUCLEO_PR-E2_cierre.md` (PR-E3…E6) y cierre previo `NUCLEO_PR-E4_cierre.md`. Primer caso
en que la fuente del re-home estaba EN DISPUTA: árbol de procedencia obsoleto vs frozen.

## Hallazgo que gobierna la decisión (verificado 2026-07-02)

En PR-E3/E4 el árbol de `_import` iba POR DELANTE del frozen (pulido documental posterior
al congelado; lógica idéntica). En `puentes` es AL REVÉS — el árbol quedó obsoleto:

- **Árbol `_import/aqyra-motor/puentes/`**: `plugin.json` declara **0.3.0**; **41 ficheros**
  (6 verticales: vigas pretensadas, losa postesada, pórtico, celosía, pilas-apoyos, estribos).
- **Frozen `_import/aqyra-motor/puentes-v0.6.0.plugin`**: **62 ficheros**, `plugin.json`
  **0.6.0**. Contiene TODO el árbol y además las olas 0.4→0.6: **21 ficheros nuevos**
  (4 verticales completos: cajón, curvo, mixto, oblicuo — agente + idealización +
  comprobación + run_all + validación contra caso de contraste — y `scripts/lectura/
  cli_ifc.py`) y **15 comunes evolucionados** (plugin.json, CHANGELOG, README, agente
  ingeniero, lectura/write-back, los 6 run_all).
- **Nada existe solo en el árbol** (árbol ⊂ frozen). El subtree del 0.7 capturó el working
  tree de la reorg (29-jun), pero los `.plugin` v0.4–v0.6 se congelaron después SIN
  actualizar el árbol fuente.
- **Núcleo**: `scripts/nucleo/{ifc_utils,grafo_red}.py` md5 LF `ad06f87d…`/`fe5dfebb…` ==
  canónico `packages/core/src/aqyra_core/` == `versions.lock [core]` **tanto en árbol como
  en frozen** — la retirada no pierde nada, gane quien gane la disputa.

Consecuencia: re-homar el árbol = perder 3 versiones publicadas. "La procedencia es el
árbol" (PR-E3/E4) presuponía árbol ≥ frozen; aquí no se cumple.

## Decisión (fork resuelto antes de tocar código)

1. **Fuente del re-home: el FROZEN `puentes-v0.6.0.plugin`.** Es el producto más reciente
   y completo (la fuente vívida de 0.6.0). Se descomprime a `plugins/puentes/` **sin**
   `scripts/nucleo/`. El árbol 0.3.0 queda documentado aquí como OBSOLETO y **no se toca**:
   la zona firmada `_import/` no se reescribe ni para "actualizarla" — se documenta.
2. **Versión: 0.6.0 fiel.** El `.plugin` resultante es funcionalmente idéntico al frozen —
   solo cambia CÓMO se construye (núcleo inyectado en build desde `packages/core`). El
   semver se mueve cuando cambie el producto, no el empaquetado. **Sin release en este PR.**
3. **Ref del contraste: el MISMO frozen v0.6.0.** Diferencia esperada del nuevo `.plugin`:
   solo la ausencia de `scripts/nucleo/{test_grafo_red.py,README.md}` (artefactos de
   desarrollo del núcleo; `ifc_utils.py` y `grafo_red.py` se regeneran en build). En la
   puerta `verificar_empaquetado.py --ref`, la ausencia de un `.py` es AVISO (no bloqueo)
   → único aviso esperado: `test_grafo_red.py`; **0 encogidos**.
4. **Re-home fiel byte a byte desde el frozen.** 62 − 4 = **58 ficheros** entran a
   `plugins/puentes/`; cualquier evolución del contenido, en PR aparte: este PR solo cambia
   DÓNDE vive y CÓMO se construye.
5. **Wiring CI: NINGUNO.** El paso único de builds (PR-E4) ejecuta todos los
   `tools/build_plugin_*.py`: el builder nuevo entra al gate solo.

## Consecuencias

- `plugins/puentes/` entra a `plugins/` sin copia trackeada del núcleo (tercero de los 3
  pendientes de PR-E2). `versions.lock [core] estado` pasa a "queda 1 (motor-fem, PR-E6)".
- Builder nuevo `tools/build_plugin_puentes.py` = patrón obras-lineales (consume
  `tools/_inyectar_nucleo.py`; `SKIP_DIRS=("scripts/nucleo",)`; staging efímero; `--ref`
  por defecto el frozen v0.6.0 — el CI ejecuta los builders sin argumentos).
- `.gitignore`: bloque PR-E5 (`plugins/puentes/scripts/nucleo/`). Guardián anti-reaparición
  por NOMBRE cubre `plugins/puentes/` automáticamente; `affected.py` ya mapea `plugins/`
  y `tools/`.
- `puentes` no contiene ficheros del corte del engine (acoplamiento con `motor-fem` en
  runtime, no por copia): solo aplica la retirada del núcleo.
- **Precedente para PR-E6 y futuros re-homes:** la procedencia por defecto es el árbol
  SOLO si árbol ≥ frozen; si el frozen va por delante, la fuente es el frozen y el árbol
  se documenta como obsoleto sin reescribir la zona firmada.
