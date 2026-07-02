# NÚCLEO · PR-E3 — Decisión: re-home de `instalaciones` (primer plugin sin espejo de serie)

**Fecha:** 2026-07-02 · **Decisor:** JM · **Contexto:** Fase I · hilo 4. Guion anclado en
`NUCLEO_PR-E2_cierre.md` (PR-E3…E6: instalaciones → obras-lineales → puentes → motor-fem).

## Decisión (fork resuelto antes de tocar código)

1. **Versión: 0.3.0 fiel.** El `.plugin` resultante es funcionalmente idéntico al frozen
   `_import/aqyra-motor/instalaciones-v0.3.0.plugin` — solo cambia CÓMO se construye
   (núcleo inyectado en build desde `packages/core` en vez de copia trackeada). El semver
   se mueve cuando cambie el producto, no el empaquetado. **Sin release en este PR.**
2. **Wiring CI: Paso 1c explícito** en `ci.yml`, simétrico al Paso 1b del piloto.
   Generalizar a "todos los `tools/build_plugin_*.py`" cuando haya 3+ builders — no se
   abstrae con n=2.
3. **Re-home fiel byte a byte.** Se copia desde la procedencia `_import/aqyra-motor/
   instalaciones/` sin ajuste alguno a agentes/skills; lo único que NO entra es
   `scripts/nucleo/` (el plugin nace limpio; la carpeta se genera en build). Cualquier
   evolución del contenido, en PR aparte: este PR solo cambia DÓNDE vive y CÓMO se
   construye.

## Verificación de partida (2026-07-02)

- Identidad del núcleo confirmada en ambos sentidos: `_import/.../scripts/nucleo/
  {ifc_utils,grafo_red}.py` md5 LF `ad06f87d…` / `fe5dfebb…` == `packages/core/src/
  aqyra_core/` == `versions.lock [core]`. La retirada no pierde nada.
- Frozen v0.3.0: 23 ficheros. Diferencia esperada del nuevo `.plugin`: pierde
  `scripts/nucleo/{test_grafo_red.py,README.md}` (artefactos de desarrollo). En la puerta
  `verificar_empaquetado.py --ref`, la ausencia es AVISO (no bloqueo) y el contraste solo
  mira `.py` → único aviso esperado: `test_grafo_red.py`.
- **Hallazgo (auditado):** el árbol `_import/aqyra-motor/instalaciones/` NO es byte a byte
  el frozen: 15 ficheros difieren. Verificado por AST (docstrings eliminados): la lógica
  ejecutable es IDÉNTICA en los 12 `.py`; todo el diff es pulido documental posterior al
  congelado (renombrado C4→CN-3 en textos, docstrings/comentarios añadidos, dicts
  reformateados) también en .md/.json (keywords reordenadas+ampliadas, CHANGELOG ampliado).
  La procedencia del re-home es el ÁRBOL (fuente viva, por guion del hilo); el frozen queda
  solo como --ref anti-truncado (0 encogidos: la evolución solo crece). "0.3.0 fiel" se
  sostiene: funcionalmente idéntico.
- Guardián `test_nucleo_no_reaparece_fuera_de_core` es por nombre de fichero: cubre
  `plugins/instalaciones/` automáticamente, sin tocarlo.

## Consecuencias

- `plugins/instalaciones/` entra a `plugins/` sin copia trackeada del núcleo (primero de
  los 4 pendientes). `versions.lock [core] estado` pasa a "instalaciones re-homed; quedan
  3 (obras-lineales, puentes, motor-fem)".
- Builder nuevo `tools/build_plugin_instalaciones.py` (patrón del piloto: staging efímero,
  inyección con prueba de identidad, zip, puerta `--ref` frozen). Si el copy-paste de la
  inyección supera ~40 líneas, se factoriza a `tools/_inyectar_nucleo.py`.
- La zona firmada `_import/` NO se reescribe: el re-home es COPIA desde procedencia.
