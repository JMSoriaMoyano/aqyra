# Espejo del engine C1 — guardián activo + plan de retirada

**Fase I · hilo 1.** Decisión (JM): *guardián de identidad ya; retirada por PR incremental en
hilo aparte.* Este documento fija qué es el espejo, cómo se protege ahora y cómo se retira
después. La zona firmada `_import/` **no se reescribe**.

## Qué es el espejo

Con el engine canónico ya único en `engines/ifc` (corte mínimo C1 importado del canónico
`iso19650-openbim 0.10.0`), las copias del motor que sobreviven aguas arriba son el *espejo*:

| Copia (empaquetada en `_import/aqyra-motor/*.plugin`) | Qué duplica | Versión embebida |
|---|---|---|
| `iso19650-openbim-v0.9.2.plugin` → `skills/narracion-a-ifc/scripts/` + `scripts/lineal/` | **compilador narración→IFC** (este engine) | **0.9.2** (pre-apertura P1) |
| `motor-fem-v0.3.0.plugin` → `scripts/nucleo/` | núcleo (`ifc_utils`, `grafo_red`) | — |
| `obras-lineales-v0.4.0.plugin` → `scripts/nucleo/` | núcleo | — |
| `instalaciones-v0.3.0.plugin` → `scripts/nucleo/` | núcleo | — |
| `puentes-v0.6.0.plugin` → `scripts/nucleo/` | núcleo | — |

Dos espejos distintos:

1. **Espejo del engine** (este hilo): el compilador vive dentro del plugin `iso19650-openbim`.
   Además está **desincronizado**: el `.plugin` empaquetado es **0.9.2** (sin huecos
   generalizados, catálogo abierto ni doble clasificación), mientras el canónico del monorepo
   es **0.10.0**. Retirar = que el plugin consuma `engines/ifc` en vez de llevar su propia copia.
2. **Espejo del núcleo** (0.5): `ifc_utils`/`grafo_red` duplicados en 5 plugins. Ya trazado en
   `versions.lock [core]` (`estado = "…retirada del espejo aguas arriba = pendiente"`). Fuera del
   alcance de este hilo; se retira con el núcleo, no con el engine.

## Guardián activo (ya en el gate)

Dos tests en `engines/ifc/tests/`, ejecutados por el gate (`pytest engines/ifc`, Paso 1 del CI y
`just check`):

- **`test_identidad_ifc`** — ancla los 9 ficheros del corte mínimo a hashes fijos (md5 LF)
  vetados contra el 0.10.0. Nadie edita el engine sin re-ancla consciente.
- **`test_espejo_ifc`** — compara byte a byte `engines/ifc` con su **procedencia** en
  `_import/aqyra-motor` (el 0.10.0 importado). Mientras el espejo viva, canónico y origen no
  divergen en silencio.

Invariante: **el árbol firmado == el árbol verde**. Un cambio en el engine que no pase por su
golden de comportamiento (`C1-APERTURA-01`) o rompa la procedencia, pone el gate en rojo.

## Plan de retirada (hilo aparte, por PR incremental)

La retirada **no** toca `_import/` (frozen). Ocurre aguas arriba, en cómo se construyen los
plugins, y se hace un plugin por PR para acotar el radio de impacto:

1. **PR-E1 · unificar la fuente.** Que la build del plugin `iso19650-openbim` tome el compilador
   de `engines/ifc` (submódulo/consumo del paquete) en lugar de `skills/narracion-a-ifc/scripts/`.
   Subir el plugin de 0.9.2 → 0.10.0 en el mismo movimiento (recupera la capacidad de apertura P1).
2. **PR-E2..E5 · núcleo** (coordinado con la retirada del espejo de core 0.5): que
   `motor-fem`, `obras-lineales`, `instalaciones`, `puentes` consuman el núcleo compartido en vez
   de `scripts/nucleo/` propio. Uno por PR.
3. **Cierre.** Cuando ninguna build embeba copia, el guardián `test_espejo_ifc` deja de tener
   procedencia que comparar (se auto-omite) y se sustituye por la sola identidad. Se re-ancla el
   estado en `versions.lock`.

Definición de hecho de la retirada: cada plugin construye consumiendo la fuente única; su golden
sigue verde; ninguna copia del engine/núcleo fuera de `engines/ifc` (+ core) y de `_import/`.
