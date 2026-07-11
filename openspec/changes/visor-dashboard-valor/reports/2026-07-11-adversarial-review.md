# Adversarial review · visor-dashboard-valor (E6.1) · 2026-07-11

Revisión crítica contra los guardarraíles del change (§6 del INICIO-hilo + `proposal`/`design`).

1. **¿Cálculo en cliente?** NO. `dashboard.ts` LEE el índice: `modeloVista` pasa `valor_total` **sin
   alterar** (test `no altera ningún valor_total` → `filas.valor === grupos.valor_total` en las 6
   vistas). Lo único que computa es (a) `Σ valor_total` para **verificar** el invariante (lo exige la
   spec: «Σ grupos == suma»), no para re-valorar, y (b) `escala = |valor|/máx` = geometría de la barra.
   No re-mide, no re-valora, no re-proyecta. Sin `three`/`web-ifc` en el módulo.

2. **¿La aceptación reproduce `GOL-PRE-03` desde el engine (no un oráculo propio)?** SÍ. La fixture la
   emite `tools/emitir_proyeccion_visor.py` llamando al engine REAL sobre la medición ANCLADA de
   `GOL-PRE-03`. Comprobado: las `vistas` de coste casan byte a byte con `expected.json`. El test ancla
   por VALOR (grupos/valor/fuente + Σ), no por un md5 propio → un desajuste se corrige re-emitiendo la
   fixture, nunca editando el cliente (verificado: los asserts fallarían si se tocara un valor).

3. **¿Núcleo del visor / `proyectar` / `GOL-PRE-03` intactos?** SÍ. El change es ADITIVO: `dashboard.ts`
   + su test + fixture + emisor (en `tools/`, no en el visor) + exports aditivos en `index.ts` + modo
   `?valor` aditivo en la demo + `DECISIONES` V12. Cero cambios en `viewer`/`ifc-loader`/`selección`/
   `data-state`/skins existentes ni en el motor/esquema/packs. La suite completa (105 tests, 21
   ficheros) sigue verde → sin regresión.

4. **¿La skin certifica?** NO. `ESTADO_PROYECCION = "proposal"`; `isCertified` es `false` (test).
   La UI pinta el chip PROPUESTA vía `dataStateStyle` y la barra de estado («el export firmable llega»).
   El muro de cobro (dos llaves) queda forward.

5. **Modos de fallo cubiertos:** grupo inexistente / residual sin geometría → `guidsDeGrupo` = `[]`
   (test); `máx=0` → `escala=0` sin división por cero; selectores derivados del índice (`ejesDe`/
   `cortesDe`) → sólo combinaciones presentes; determinismo (dos renders idénticos, test).

6. **Honestidad de la fuente:** el chip `fuente` refleja el *fallback* (`ifc`/`criterio`/`regla`/`—`) sin
   ocultarlo; los grupos residuales se muestran. Carbono: invariante Σ (7 117,69 kgCO2e), su golden de
   proyección = forward, documentado.

**Veredicto:** conforme. Sin cálculo en cliente; reproduce `GOL-PRE-03`; núcleo y anclas intactos;
«propone» sin certificar. Llave 1 verde. Llave 2 (merge/firma) = JM. Sin release.
