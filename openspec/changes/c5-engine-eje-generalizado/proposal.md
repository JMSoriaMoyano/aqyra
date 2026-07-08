# Cambio · El engine C5 se generaliza a un eje (`parametros.eje`)

> Change-id: `c5-engine-eje-generalizado` · Capacidad: `presupuesto` (contrato `C5-presupuesto`)
> Historia del backlog: **E1.2** (`Aqyra-Negocio/BACKLOG_motor-valoracion_para-Aqyra-Raiz.md` §2·E1) · Ola 1
> Procedencia: handoff negocio → desarrollo (`INICIO-hilo_Aqyra-Raiz_motor-valoracion_E1.2.md`, 2026-07-08)
> Estado: **PROPUESTA + APLICADA** · **D19 RATIFICADA** por JM antes del código (2026-07-08).
> Tipo: **EXTIENDE** una capacidad viva (engine C5) — forward-open, no se crea contrato nuevo.

## Por qué

E1.1 abrió la **forma** de la salida a `valores{}` (D16–D18). E1.2 la hace **viva**: el motor
`presupuestar(...)` deja de saber solo de € y acepta un `banco` cuyo valor unitario es de **cualquier
eje** (kgCO₂e, agua, energía embebida, …), seleccionado por `parametros.eje` (default `"coste"`).

Es la segunda pieza de la Ola 1 y el habilitador directo de la Ola 2 (carbono): en cuanto exista un
`banco-carbono`, la huella se calcula con **este mismo engine** y otro `banco`, sin código nuevo. El
mapeo objeto→partida del **criterio no cambia entre ejes** (es el 80 % del valor, se reutiliza tal
cual): se mide una vez y se valora en el eje pedido.

## Qué cambia (superficie: `engines/presupuesto/`)

- **`src/aqyra_presupuesto/presupuesto.py`** — `presupuestar(...)` gana la lectura de
  `parametros.eje` (default `"coste"`) y un helper `_valor_eje(...)`:
  - `eje == "coste"`: la rama es el **código C5 previo byte a byte** (no emite `valores`).
  - `eje != "coste"`: cada partida gana `valores[eje]` etiquetado (unidad del banco, banco de origen,
    origen), con `precio_unitario`/`importe` reflejando la magnitud del eje (D19, espejo).
- **`tests/test_eje_multieje.py`** — NUEVO: fija la no-regresión del coste (eje default no emite
  `valores`, `eje=coste` explícito == default) y la forma del run no-coste (valores etiquetado,
  espejo, mapeo/cantidades intactos entre ejes).
- **`pyproject.toml`** — bump `0.2.0 → 0.3.0` (aditivo).
- **`packages/contracts/C5-presupuesto/DECISIONES.md`** — se ancla **D19** (continúa D1–D18).
- **`versions.lock [contracts.C5]`** — `engine_version = "0.3.0"` + estado.

## Impacto — por qué NO rompe nada (verificado, no prometido)

- El eje `coste` (default) es la **rama intacta**: `if not es_coste:` guarda toda la novedad, de modo
  que con `banco=AQ-DEMO` y `eje=coste` la salida es **byte-idéntica** a hoy. Verificado en el sandbox
  (path puro `presupuestar`): `GOL-PRE-01` reproduce PEM **7 022,53** → PEC **10 111,74**, sin
  `valores` en ninguna partida, y `eje="coste"` explícito devuelve exactamente el mismo objeto que el
  default. `GOL-PRE-01` / `GOL-PRE-02` / `GOL-DOC-01` no se tocan.
- El run no-coste conforma el esquema (verificado estructuralmente contra `$defs.valor_eje`).

## Fuera de alcance (fronteras honestas)

- **No** se añaden cortes ni `proyectar()` — eso es **E2.1 / E2.2**.
- **No** se crea la familia `banco-carbono` ni `GOL-CAR-01` — eso es la **Ola 2** (E3).
- **No** se toca el parser de `Qto` (`medicion.py`/`modelo.py`), el motor económico, el write-back 5D
  (`escritura.py`) ni el runner de golden.
- **No** se toca `GOL-PRE-01` (ni su `expected`, ni sus fixtures, ni su md5).
- **Sin release** en E1.2: la salida multi-eje se libera con el eje carbono (Ola 2) o cuando lo
  decida JM (Llave 2). El git va por `.bat` en el host, nunca desde el desarrollo.
