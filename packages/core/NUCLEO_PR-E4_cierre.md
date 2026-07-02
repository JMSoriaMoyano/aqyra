# NÚCLEO · PR-E4 — Cierre: `obras-lineales` re-homed + inyección factorizada (deuda pagada)

**Fecha:** 2026-07-02 · **Hilo:** Fase I · hilo 5 · **Decisión:** `NUCLEO_PR-E4_decision.md`
(0.4.0 fiel + factorización completa + paso único de builds). **Sin release.**

## Qué entró

- **`tools/_inyectar_nucleo.py`** — fuente única de la inyección del núcleo (`md5_lf`,
  `core_anchors`, `inject_nucleo`), nacida con el tercer consumidor (deuda anclada en
  `NUCLEO_PR-E3_cierre.md` pagada). Los TRES builders la consumen; la duplicación
  (~45 líneas × 3) muere de golpe.
- **Migración de `build_plugin_iso19650.py` y `build_plugin_instalaciones.py`** —
  no-regresión probada: los `.plugin` resultantes son idénticos a nivel de CONTENIDO
  pre/post migración (hash md5 del conjunto de entradas: iso `1429f881…` 50 ficheros,
  instalaciones `554dea5b…` 21 ficheros — iguales antes y después).
- **`plugins/obras-lineales/`** — copiado desde `_import/aqyra-motor/obras-lineales/`
  (procedencia, NO reescrita) **sin `scripts/nucleo/`**: segundo plugin que NACE sin copia
  trackeada del núcleo. 40 ficheros byte a byte idénticos a la procedencia; diff = solo la
  ausencia del núcleo (verificado con `diff -rq` + md5 por fichero).
- **`tools/build_plugin_obras_lineales.py`** — patrón instalaciones (el más simple, sin
  engine) consumiendo `_inyectar_nucleo`. **APTO en local a la primera**: identidad OK,
  32 `.py` sin errores, 0 encogidos vs frozen v0.4.0, único aviso el esperado
  (`scripts/nucleo/test_grafo_red.py` ausente vs ref).
- **`ci.yml` — paso ÚNICO de builds** (sustituye a 1b y 1c): bucle sobre todos los
  `tools/build_plugin_*.py` (el glob no captura `_inyectar_nucleo.py` ni
  `verificar_empaquetado.py`). Un plugin nuevo deja de tocar `ci.yml`: PR-E5 y E6 solo
  añaden su builder.
- **`.gitignore`** — bloque PR-E4: `plugins/obras-lineales/scripts/nucleo/` (generada).
- **`versions.lock [core] estado`** — re-anclado: quedan 2 (puentes → motor-fem).

## Qué NO se tocó

- `_import/` (zona firmada), los guardianes (anti-reaparición por nombre cubre
  `plugins/obras-lineales/` solo), `affected.py`, los anclajes md5 de `versions.lock`,
  `verificar_empaquetado.py`.

## Hallazgo auditado (ver decisión)

El árbol de procedencia difiere del frozen v0.4.0 en 14 ficheros (9 documentales + 5
`.py`). Verificado con el comparador AST (docstrings ELIMINADOS): **lógica ejecutable
idéntica en los 5 `.py`** → "0.4.0 fiel" se sostiene; mismo precedente que PR-E3.

## Verificación local (2026-07-02)

- 3/3 builds APTO (simulación del paso único del gate).
- Guardianes engine + núcleo simulados por sistema de ficheros (el git del sandbox miente
  contra el mount): VERDES con las exenciones y gitignore aplicados. Ojo: `build/` (staging
  antiguo, gitignored) contiene copias NO trackeadas — invisibles para el guardián real.
- Lección de entorno reconfirmada y AMPLIADA: el torn-read del mount afecta a `Edit` sobre
  ficheros existentes Y puede persistir minutos incluso tras un `Write` completo (vista
  del sandbox con null bytes mientras el host está limpio). Mitigación usada: ejecutar la
  copia limpia desde `/tmp` con `compile(src, ruta_real)` + `__file__` inyectado — el
  producto se verifica igual; el gate corre sobre el checkout de git (host limpio).

## Guion (de `NUCLEO_PR-E2_cierre.md`)

- **PR-E5:** re-home `puentes` (builder = patrón obras-lineales; `ci.yml` ya no se toca).
- **PR-E6:** re-home `motor-fem` (el mayor; puede necesitar decisión propia).
