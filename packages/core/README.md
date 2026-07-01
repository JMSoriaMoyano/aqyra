# packages/core

Librería compartida, agnóstica al solver, **importada** (no copiada). **Fin del espejo.**

## Qué contiene (0.5)

- **`ifc_utils`** — lectura IFC común: `psets(element)`, `length_scale(ifc)` (factor de unidad a
  metros), `pset_value(...)`, y álgebra homogénea 4×4 (`matmul`/`apply`/`to_list4`/`ident4`).
- **`grafo_red`** — grafo de red genérico: `RegistroNodos` (fusión por tolerancia/snap),
  `punto_en_segmento`, `proyeccion`, `cortes_por_interseccion` (troceo T/X),
  `ordenar_segmento`, `filtrar_componentes_desconectadas`, y
  `construir_grafo(segmentos, tol) → {nodos, tramos, métricas}`. **Devuelve topología, no calcula.**

No habla IFC de dominio, no calcula, no tiene contrato pesado: expone una **interfaz tipada**.

## Procedencia e identidad (byte a byte)

Extraído del núcleo **canónico** `Estructurando/Nucleo-transversal/nucleo`. En los plugins ese
núcleo se **espejaba** byte a byte con una puerta de hash (`verificar_espejo_nucleo.py`), porque
el aislamiento de runtime impedía importarlo. En el monorepo el espejo desaparece: **un paquete,
una versión**. La identidad con el canónico se ancla en `versions.lock` (md5) y la verifica
`tests/test_identidad_nucleo.py` en el CI.

## Tests

```bash
just test-core          # o: uv run pytest packages/core -q
```

- `test_grafo_red.py` — no-regresión de **comportamiento** (snap, troceo T/X, union-find, 4×4).
- `test_identidad_nucleo.py` — no-regresión de **identidad**: los módulos == canónico (md5 LF).

## Pendiente (no es de este paso)

**Retirar el espejo en los 5 plugins aguas arriba** (iso19650-openbim, motor-fem, puentes,
obras-lineales, instalaciones) y hacer que **importen** `aqyra_core`: requiere que los engines
estén en el monorepo (emparentado con la importación de historia, 0.7). Hasta entonces, los
plugins siguen con su espejo; aquí queda el núcleo listo para ser el único origen.

Ver `../../../Aqyra-Raiz/FUNDACION_core_y_gobierno-CI.md`.
