# NÚCLEO · PR-E3 — Cierre: `instalaciones` re-homed (primer plugin que nace sin espejo)

**Fecha:** 2026-07-02 · **Hilo:** Fase I · hilo 4 · **Decisión:** `NUCLEO_PR-E3_decision.md`
(0.3.0 fiel + Paso 1c explícito + re-home fiel a la procedencia). **Sin release.**

## Qué entró

- **`plugins/instalaciones/`** — copiado desde `_import/aqyra-motor/instalaciones/`
  (procedencia, NO reescrita) **sin `scripts/nucleo/`**: primer plugin de los 4 pendientes
  que NACE sin copia trackeada del núcleo. Diff vs procedencia = solo la ausencia del
  núcleo (verificado con `diff -rq`).
- **`tools/build_plugin_instalaciones.py`** — patrón del piloto: staging efímero fuera del
  árbol, `SKIP_DIRS=("scripts/nucleo",)`, `_inject_nucleo()` con prueba de identidad md5-LF
  vs `versions.lock [core]`, zip a `dist/plugins/`, puerta `verificar_empaquetado.py
  --ref _import/aqyra-motor/instalaciones-v0.3.0.plugin`. **APTO en local a la primera**:
  identidad OK, 14 `.py` sin errores, 0 encogidos, único aviso el esperado
  (`scripts/nucleo/test_grafo_red.py` ausente vs ref; el `README.md` del núcleo es `.md` y
  no entra al contraste).
- **`ci.yml` Paso 1c** — build de instalaciones como puerta, simétrico al 1b. `affected.py`
  ya mapeaba `plugins/` y `tools/`; sin tocar.
- **`.gitignore`** — bloque PR-E3: `plugins/instalaciones/scripts/nucleo/` (carpeta
  generada).
- **`versions.lock [core] estado`** — re-anclado: piloto + instalaciones limpios; quedan 3.

## Qué NO se tocó

- `_import/` (zona firmada), los guardianes (el anti-reaparición es por nombre y cubre
  `plugins/instalaciones/` solo), el builder del piloto, `affected.py`, `versions.lock`
  anclajes md5.

## Hallazgo auditado (ver decisión)

El árbol de procedencia difiere del frozen v0.3.0 en 15 ficheros: pulido documental
posterior al congelado (C4→CN-3 en textos, docstrings, formato). Verificado por AST:
**lógica ejecutable idéntica en los 12 `.py`** → "0.3.0 fiel" se sostiene; la procedencia
del re-home es el árbol y el frozen queda como ref anti-truncado.

## Factorización diferida (anclada para PR-E4)

La inyección del núcleo está duplicada entre `build_plugin_iso19650.py` y
`build_plugin_instalaciones.py` (~45 líneas). Con el TERCER consumidor (PR-E4,
obras-lineales) se factoriza a **`tools/_inyectar_nucleo.py`** — no se abstrae con n=2,
mismo criterio que el CI (generalizar el paso de builds cuando haya 3+).

## Guion confirmado (de `NUCLEO_PR-E2_cierre.md`)

- **PR-E4:** re-home `obras-lineales` (+ factorizar `_inyectar_nucleo.py` + valorar
  generalizar el paso de builds del CI con n=3).
- **PR-E5:** re-home `puentes`.
- **PR-E6:** re-home `motor-fem` (el mayor; puede necesitar decisión propia).

Cada uno: copiar árbol sin núcleo desde `_import` → builder con inyección e identidad →
wiring CI → gate verde → re-anclar `versions.lock [core] estado`.
