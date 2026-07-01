# iso19650-openbim — miembro del monorepo (re-homed, PR-E1)

Este plugin se **construye desde el monorepo** consumiendo el compilador narración→IFC como
**fuente única** de `engines/ifc`. No lleva copia embebida del engine: su copia se **genera en
build**. Fase I · hilo 2 (retirada del espejo del engine). Ver `engines/ifc/ESPEJO_PR-E1_decision.md`.

## Cómo se construye

```
python3 tools/build_plugin_iso19650.py
```

Produce `dist/plugins/iso19650-openbim-<version>.plugin` y pasa la puerta de empaquetado
(`tools/verificar_empaquetado.py`): plugin.json válido (semver, description ≤500), `ast.parse` de
todo `.py`, salto de línea final, sin artefactos, y contraste anti-truncado vs el 0.9.2 frozen.

El build **prueba** que cada fichero de engine inyectado es byte a byte idéntico a su anclaje md5
en `versions.lock [engines.ifc.md5]`: si el build no deriva del canónico, falla.

## Qué se COMMITEA y qué se GENERA

**Commiteado (fuente del miembro):** `.claude-plugin/plugin.json`, `README.md`, `CHANGELOG.md`,
las 6 skills (bep-eir, bsdd-clasificacion, cde-audit, ifc-create, ifc-validate, loin-matrix),
`skills/narracion-a-ifc/SKILL.md`, `skills/narracion-a-ifc/_aux/` (auxiliares NO-engine:
`construir_catalogo.py`, `generar_galeria.py`), `scripts/{estructural,mep}/`, el resto de
`scripts/lineal/` y `scripts/nucleo/`.

**Generado en build (gitignored, NUNCA commiteado):**

| Destino en el `.plugin` | Fuente única |
|---|---|
| `skills/narracion-a-ifc/scripts/*.py` + `.json` (compilador) | `engines/ifc/narracion-ifc/*` (8 ficheros del corte) + `_aux/*` |
| `scripts/lineal/generate_test_ifc_lineal.py` | `engines/ifc/scripts/lineal/` |

## Guardián

`engines/ifc/tests/test_no_reaparicion_espejo.py` (en el gate, paso `pytest engines/ifc`) falla si
un fichero del corte del engine reaparece **trackeado** fuera de `engines/ifc`, y ata la copia de
`scripts/nucleo/` al canónico `packages/core` (deuda de PR-E2…E5).

## Deuda conocida

`scripts/nucleo/{ifc_utils,grafo_red}.py` es todavía una copia del núcleo (espejo de core), fuera
del alcance de PR-E1. Se retira en PR-E2…E5 aplicando este mismo patrón de consumo por build desde
`packages/core`. Hasta entonces, queda atada byte a byte al canónico por el guardián.
