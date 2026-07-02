# NÚCLEO · PR-E4 — Decisión: re-home de `obras-lineales` + factorización `_inyectar_nucleo.py`

**Fecha:** 2026-07-02 · **Decisor:** JM · **Contexto:** Fase I · hilo 5. Guion anclado en
`NUCLEO_PR-E2_cierre.md` (PR-E3…E6) y deuda anclada en `NUCLEO_PR-E3_cierre.md`
(la inyección del núcleo se factoriza con el TERCER consumidor: este PR).

## Decisión (fork resuelto antes de tocar código)

1. **Versión: 0.4.0 fiel.** El `.plugin` resultante es funcionalmente idéntico al frozen
   `_import/aqyra-motor/obras-lineales-v0.4.0.plugin` — solo cambia CÓMO se construye
   (núcleo inyectado en build desde `packages/core` en vez de copia trackeada). El semver
   se mueve cuando cambie el producto, no el empaquetado. **Sin release en este PR.**
2. **Factorización completa.** `tools/_inyectar_nucleo.py` nace en este PR (con `_md5_lf`,
   `_core_anchors` e `_inject_nucleo`) y migran TAMBIÉN los dos builders existentes
   (`build_plugin_iso19650.py`, `build_plugin_instalaciones.py`): la puerta de cada build
   y el gate protegen la migración, y la duplicación (~45 líneas × 3) muere de golpe.
   **Prueba de no-regresión:** los tres builds siguen APTO en local y el CONTENIDO de los
   `.plugin` de iso19650 e instalaciones es idéntico pre/post migración (la factorización
   no cambia el producto).
3. **Wiring CI: paso único de builds.** Los Pasos 1b y 1c de `ci.yml` se sustituyen por un
   paso único que ejecuta todos los `tools/build_plugin_*.py` — criterio anclado en PR-E3
   (generalizar con n=3). Un plugin nuevo deja de tocar `ci.yml`.
4. **Re-home fiel byte a byte.** Se copia desde la procedencia `_import/aqyra-motor/
   obras-lineales/` sin ajuste alguno; lo único que NO entra es `scripts/nucleo/` (el
   plugin nace limpio; la carpeta se genera en build). Cualquier evolución del contenido,
   en PR aparte: este PR solo cambia DÓNDE vive y CÓMO se construye.

## Verificación de partida (2026-07-02)

- Identidad del núcleo confirmada: `_import/aqyra-motor/obras-lineales/scripts/nucleo/
  {ifc_utils,grafo_red}.py` md5 LF `ad06f87d…` / `fe5dfebb…` == `packages/core/src/
  aqyra_core/` == `versions.lock [core]`. La retirada no pierde nada.
- Árbol de procedencia: 44 ficheros (sin `__pycache__`); frozen v0.4.0: 44 ficheros.
  Mismo conjunto de rutas en ambos. Diferencia esperada del nuevo `.plugin`: pierde
  `scripts/nucleo/{test_grafo_red.py,README.md}` (artefactos de desarrollo del núcleo).
  En la puerta `verificar_empaquetado.py --ref`, la ausencia es AVISO (no bloqueo) y el
  contraste solo mira `.py` → único aviso esperado: `test_grafo_red.py`.
- **Hallazgo (auditado, mismo precedente que PR-E3):** el árbol NO es byte a byte el
  frozen: 14 ficheros difieren (9 documentales — CHANGELOG, README, 6 agents, SKILL — y
  5 `.py`: `drenaje/hidrologia.py`, `firmes/bases_firme.py`, `red/bases_abastecimiento.py`,
  `red/bases_saneamiento.py`, `red/solver_presion.py`). Verificado con el comparador AST
  (docstrings ELIMINADOS, no vaciados): **lógica ejecutable IDÉNTICA en los 5 `.py`** —
  todo el diff es pulido documental posterior al congelado. La procedencia del re-home es
  el ÁRBOL (fuente viva, por guion del hilo); el frozen queda solo como `--ref`
  anti-truncado. "0.4.0 fiel" se sostiene: funcionalmente idéntico.
- Guardián `test_nucleo_no_reaparece_fuera_de_core` es por nombre de fichero: cubre
  `plugins/obras-lineales/` automáticamente, sin tocarlo. `affected.py` ya mapea
  `plugins/` y `tools/`.
- Consumo en runtime: los scripts del plugin cargan el núcleo por `sys.path` hacia
  `../nucleo` (`import ifc_utils` / `import grafo_red`); la carpeta generada en build basta.

## Consecuencias

- `plugins/obras-lineales/` entra a `plugins/` sin copia trackeada del núcleo (segundo de
  los 3 pendientes). `versions.lock [core] estado` pasa a "obras-lineales re-homed; quedan
  2 (puentes, motor-fem)".
- Builder nuevo `tools/build_plugin_obras_lineales.py` y los dos existentes consumen
  `tools/_inyectar_nucleo.py`: la inyección del núcleo tiene UNA implementación.
- `ci.yml` queda con un paso de builds generalizado; PR-E5 y PR-E6 no tocarán `ci.yml`.
- La zona firmada `_import/` NO se reescribe: el re-home es COPIA desde procedencia.
