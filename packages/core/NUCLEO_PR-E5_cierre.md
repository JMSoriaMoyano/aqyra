# NÚCLEO · PR-E5 — Cierre: `puentes` re-homed desde el FROZEN v0.6.0 (procedencia invertida)

**Fecha:** 2026-07-02 · **Hilo:** Fase I · hilo 6 · **Decisión:** `NUCLEO_PR-E5_decision.md`
(fuente = FROZEN v0.6.0 + 0.6.0 fiel + ref = el propio frozen). **Sin release.**

## Qué entró

- **`plugins/puentes/`** — descomprimido desde `_import/aqyra-motor/puentes-v0.6.0.plugin`
  (la fuente vívida de 0.6.0; el árbol `_import/aqyra-motor/puentes/` quedó en 0.3.0,
  obsoleto — NO se reescribe, se documenta) **sin `scripts/nucleo/`**: tercer plugin que
  NACE sin copia trackeada del núcleo. **58 ficheros** (62 − 4 del núcleo) byte a byte
  idénticos al frozen; diff = solo la ausencia del núcleo (verificado con md5 por fichero:
  0 diferencias, 0 ficheros extra).
- **`tools/build_plugin_puentes.py`** — patrón obras-lineales (consume
  `tools/_inyectar_nucleo.py`; `SKIP_DIRS=("scripts/nucleo",)`; staging efímero en `/tmp`;
  `--ref` por defecto el frozen v0.6.0). **APTO en local a la primera**: identidad del
  núcleo OK, 46 `.py` sin errores de sintaxis, 11 agentes, **0 encogidos** vs frozen,
  único aviso el esperado (`scripts/nucleo/test_grafo_red.py` ausente vs ref).
- **`.gitignore`** — bloque PR-E5: `plugins/puentes/scripts/nucleo/` (generada en build).
- **`versions.lock [core] estado`** — re-anclado: queda 1 (PR-E6: motor-fem).
- **`packages/core/NUCLEO_PR-E5_decision.md`** — el fork de procedencia resuelto y el
  hallazgo árbol-obsoleto anclado con cifras (41 vs 62; 21 nuevos + 15 evolucionados;
  árbol ⊂ frozen; núcleo == canónico en ambos).

## Qué NO se tocó

- **`ci.yml`** — primer re-home 100% sin wiring: el paso único de builds (PR-E4) recoge
  `build_plugin_puentes.py` por glob (simulado 4/4 APTO en local).
- `_import/` (zona firmada — tampoco para "actualizar" el árbol obsoleto), los guardianes
  (anti-reaparición por nombre cubre `plugins/puentes/` solo), `affected.py`, los anclajes
  md5 de `versions.lock`, `verificar_empaquetado.py`, `tools/_inyectar_nucleo.py`.

## Hallazgo que gobernó el hilo (ver decisión)

Primer caso INVERTIDO de procedencia: en PR-E3/E4 el árbol iba por delante del frozen
(pulido documental); en `puentes` el árbol quedó en 0.3.0 y el frozen v0.6.0 lleva las
olas 0.4→0.6 (4 verticales nuevos: cajón, curvo, mixto, oblicuo + `cli_ifc.py`).
**Precedente anclado:** la procedencia por defecto es el árbol SOLO si árbol ≥ frozen;
si el frozen va por delante, la fuente es el frozen y el árbol se documenta como obsoleto.
`puentes` no contiene ficheros del corte del engine (acoplamiento con `motor-fem` en
runtime): solo aplicó la retirada del núcleo.

## Verificación local (2026-07-02)

- 4/4 builds APTO (simulación del paso único del gate; el glob recoge el builder nuevo).
- Guardianes engine + núcleo simulados por sistema de ficheros (el git del sandbox miente
  contra el mount), excluyendo `build/`, `dist/` y las carpetas generadas gitignoradas:
  VERDES — ni el núcleo ni el corte del engine reaparecen fuera de sus hogares; cero
  ficheros del corte en `plugins/puentes/`.
- Identidad del núcleo verificada en las TRES puntas: frozen == canónico ==
  `versions.lock [core]` (md5 LF `ad06f87d…` / `fe5dfebb…`).
- Lección de entorno nueva: `/tmp` del sandbox se LLENA con los stagings de builds
  sucesivos (`No space left on device` en el 3.er build) — limpiar `/tmp/*-build-*` entre
  builds en las simulaciones locales; en CI no aplica (runner fresco).

## Guion (de `NUCLEO_PR-E2_cierre.md`)

- **PR-E6:** re-home `motor-fem` (el mayor y último; puede necesitar decisión propia —
  con él, Fase I completa el vaciado de espejos). Comprobar ANTES si su árbol también
  quedó por detrás de su frozen (precedente PR-E5).
