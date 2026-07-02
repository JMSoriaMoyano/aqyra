# NÚCLEO · PR-E6 — Cierre: `motor-fem` re-homed desde el FROZEN v0.3.0 — VACIADO DE ESPEJOS COMPLETO (Fase I)

**Fecha:** 2026-07-02 · **Hilo:** Fase I · hilo 6 (continuación) · **Decisión:**
`NUCLEO_PR-E6_decision.md` (fuente = FROZEN v0.3.0 + 0.3.0 fiel + ref = el propio frozen).
**Sin release.** Con este PR, el guion de `NUCLEO_PR-E2_cierre.md` queda COMPLETO:
los 5 plugins del monorepo nacen sin copia trackeada del núcleo.

## Qué entró

- **`plugins/motor-fem/`** — descomprimido desde `_import/aqyra-motor/motor-fem-v0.3.0.plugin`
  **sin `scripts/nucleo/`**: **19 ficheros** (23 − 4) byte a byte idénticos al frozen
  (verificado por md5: 0 diferencias, 0 extra).
- **`tools/build_plugin_motor_fem.py`** — patrón obras-lineales/puentes (consume
  `_inyectar_nucleo`; `--ref` por defecto el frozen v0.3.0). **APTO a la primera**:
  18 `.py` sin errores, **0 encogidos**, único aviso el esperado (`test_grafo_red.py`).
- **`.gitignore`** — bloque PR-E6: `plugins/motor-fem/scripts/nucleo/`.
- **`versions.lock [core] estado`** — re-anclado: **VACIADO DE ESPEJOS COMPLETO (Fase I)**.
- **`packages/core/NUCLEO_PR-E6_decision.md`** — hallazgo y decisiones ancladas.

## Qué NO se tocó

- **`ci.yml`** (paso único recoge el 5.º builder por glob: 5/5 APTO simulado en local),
  `_import/`, guardianes, `affected.py`, anclajes md5, `verificar_empaquetado.py`,
  `_inyectar_nucleo.py`.

## Hallazgo (ver decisión)

Segundo caso invertido consecutivo (precedente PR-E5 aplicado tal cual): árbol 0.2.1
(19 ficheros) vs frozen v0.3.0 (23 = 0.2.1 + FEM-2: lámina curva MITC4, rigidizador,
fem2, NAFEMS). Matiz nuevo: el árbol lleva un **refactor cosmético** en 5 ficheros
(imports muertos, temporales inline, variable muerta) verificado **sin cambio de
comportamiento** (AST canónico + inspección) — se documenta y no se conserva. Nada
funcional existe solo en el árbol; núcleo == canónico en ambos; sin ficheros del corte
del engine. FEM-2 es lo que consumen los verticales cajón/curvo/mixto/oblicuo de
`puentes` en runtime.

## Verificación local (2026-07-02)

- 5/5 builds APTO (simulación del paso único del gate).
- Guardianes engine + núcleo simulados por FS (excluyendo `build/`, `dist/` y las 5
  carpetas generadas gitignoradas): VERDES.
- Identidad del núcleo en las tres puntas: frozen == canónico == `versions.lock [core]`.

## Fase I — estado final del guion

- PR-E1 (engine, piloto) ✅ · PR-E2 (núcleo, piloto) ✅ · PR-E3 (instalaciones) ✅ ·
  PR-E4 (obras-lineales + factorización + paso único) ✅ · PR-E5 (puentes, frozen) ✅ ·
  **PR-E6 (motor-fem, frozen) ✅ — vaciado completo.**
- Regla de procedencia consolidada: árbol solo si árbol ≥ frozen; si el frozen va por
  delante, la fuente es el frozen y el árbol se documenta sin reescribir `_import/`.
