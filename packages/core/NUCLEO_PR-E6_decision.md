# NÚCLEO · PR-E6 — Decisión: re-home de `motor-fem` desde el FROZEN v0.3.0 (precedente PR-E5 aplicado)

**Fecha:** 2026-07-02 · **Decisor:** JM · **Contexto:** Fase I · hilo 6 (continuación).
Último re-home del guion `NUCLEO_PR-E2_cierre.md`: con este PR, **Fase I completa el
vaciado de espejos** (0 pendientes).

## Hallazgo (verificado 2026-07-02, comprobación previa exigida por el cierre de PR-E5)

Mismo patrón invertido que `puentes`, con un matiz nuevo:

- **Árbol `_import/aqyra-motor/motor-fem/`**: `plugin.json` declara **0.2.1**; 19 ficheros.
  Es el producto v0.2.1 **salvo 5 ficheros** (`plugin.json`, `fem1.py`, `fem_core.py`,
  `mallador.py`, `validacion/fem1.py`) con **refactor COSMÉTICO** posterior: imports
  muertos eliminados (`lil_matrix`/`csr_matrix`), import local subido a cabecera
  (`coo_matrix`), temporales inline (`rr/cc`, `E/nu`), variable muerta (`full`) y pulido
  documental. Verificado por AST canónico + inspección: **sin cambio de comportamiento**.
- **Frozen `motor-fem-v0.3.0.plugin`**: **23 ficheros** = 0.2.1 + la ola **FEM-2**
  (`elementos/lamina_curva.py` MITC4, `elementos/rigidizador.py`, `fem2.py`,
  `validacion/nafems2.py`), con FEM-0/1 **intactos byte a byte** respecto a v0.2.1
  (capa aditiva, C5 §8).
- **Nada funcional existe solo en el árbol.** El refactor cosmético se documenta aquí y
  NO se conserva (la zona firmada no se reescribe; cualquier rescate del pulido, en PR
  aparte sobre `plugins/motor-fem/` si algún día interesa).
- **Núcleo**: `scripts/nucleo/{ifc_utils,grafo_red}.py` == canónico == `versions.lock
  [core]` (md5 LF) **tanto en árbol como en frozen**.
- **Sin ficheros del corte del engine** ni en árbol ni en frozen.
- FEM-2 es lo que consumen en runtime los verticales cajón/curvo/mixto/oblicuo de
  `puentes` (PR-E5): re-homar el árbol rompería ese acoplamiento.

## Decisión

1. **Fuente: el FROZEN `motor-fem-v0.3.0.plugin`** (regla de PR-E5: árbol solo si
   árbol ≥ frozen; aquí el frozen va por delante). 23 − 4 = **19 ficheros** a
   `plugins/motor-fem/` **sin** `scripts/nucleo/`.
2. **Versión: 0.3.0 fiel.** Solo cambia cómo se construye. **Sin release.**
3. **Ref del contraste: el MISMO frozen v0.3.0.** Único aviso esperado:
   `scripts/nucleo/test_grafo_red.py` ausente; **0 encogidos**.
4. **Builder** `tools/build_plugin_motor_fem.py` = patrón obras-lineales/puentes
   (consume `_inyectar_nucleo`; `SKIP_DIRS=("scripts/nucleo",)`).
5. **Wiring CI: NINGUNO** (paso único de builds; serán 5/5).

## Consecuencias

- `versions.lock [core] estado` pasa a **"vaciado de espejos COMPLETO (Fase I)"** —
  0 plugins con copia trackeada del núcleo; guardián anti-reaparición vigila a los 5.
- `.gitignore`: bloque PR-E6 (`plugins/motor-fem/scripts/nucleo/`).
- La zona firmada `_import/` NO se reescribe: el árbol 0.2.1+refactor queda como record.
