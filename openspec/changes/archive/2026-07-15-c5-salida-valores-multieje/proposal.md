# Cambio · Eje de valor genérico en la salida de C5 (`valores{}`)

> Change-id: `c5-salida-valores-multieje` · Capacidad: `presupuesto` (contrato `C5-presupuesto`)
> Historia del backlog: **E1.1** (`Aqyra-Negocio/BACKLOG_motor-valoracion_para-Aqyra-Raiz.md` §2·E1) · Ola 1
> Procedencia: handoff negocio → desarrollo (`INICIO-hilo_Aqyra-Raiz_motor-valoracion.md`, 2026-07-08)
> Estado: **PROPUESTA (opsx:propose)** · pendiente de ratificar **D16–D18** con JM antes del `opsx:apply`.
> Tipo: **EXTIENDE** una capacidad viva (C5) — forward-open, no se crea contrato nuevo.

## Por qué

El motor de valoración multi-eje de Aqyra parte de una tesis ya ratificada (D-025 / N-03): un mismo
objeto, medido una vez, vale en varios **ejes** (€, kgCO₂e, …) recorriendo la **misma** tubería
`objeto → Qto → medición → factor de un banco → valor firmable`. El carbono no es un engine nuevo:
es el **mismo** `presupuestar(modelo, criterio, banco, parametros)` con otro `banco` y otro
`parametros.eje`.

Para que eso sea posible sin romper el coste, la **salida** de C5 debe poder llevar **más de un
valor por partida**. Hoy `partida_medida` solo expresa el eje coste (`precio_unitario` / `importe`).
Esta es la primera pieza de la Ola 1: abrir la salida a `valores{}` — un objeto aditivo indexado por
**id de eje** — **sin tocar la semántica** de las claves existentes y **sin mover `GOL-PRE-01`**.

Es el cambio de esquema más pequeño posible que desbloquea E1.2 (engine «banco de un eje») y toda la
Ola 2 (carbono). Contract-first estricto: el esquema y su no-regresión **antes** que una línea de
engine.

## Qué cambia (superficie: `packages/contracts/C5-presupuesto/`)

- **`salida-presupuesto.schema.json`** — se añade al `$defs.partida_medida` una propiedad **opcional**
  `valores`: mapa `id-de-eje → { unitario, total, unidad, banco?, etapas? }`. Nuevo `$def` `valor_eje`.
  - `precio_unitario` / `importe` se **conservan intactos** como el eje `coste` canónico (fuente de
    verdad del eje coste; ver D16).
  - `valores` **no** entra en `required`; una partida sin él es válida (forward-open). Un eje sin
    banco para una partida → su clave **ausente**, nunca error.
- **`contrato.md`** — nota aditiva que documenta `valores{}` y su relación con el eje coste canónico.
- **`DECISIONES.md`** (C5) — se añaden **D16–D18** (numeración propia de C5, continúa D1–D15) una vez
  ratificadas por JM.

Nada más. No se toca el engine, ni el runner, ni los packs, ni las fixtures, ni ningún `expected`.

## Impacto — por qué NO rompe nada (forward-open verificable)

- `partida_medida` ya declara `additionalProperties: true` y `valores` **no** es `required`: el
  `expected.json` de **`GOL-PRE-01`** (que no contiene `valores`) **sigue conformando byte a byte**,
  sin re-anclar (verificado en `tasks.md`, paso de no-regresión).
- El eje coste **no se duplica** en el golden: `precio_unitario`/`importe` siguen siendo la fuente de
  verdad; `valores` es el **canal aditivo** para los ejes que llegan después (carbono en la Ola 2).
- No hay cambio de comportamiento: E1.1 es **solo esquema + documentación**. El engine que **rellena**
  `valores` genéricamente es E1.2 (change aparte), y su criterio de aceptación es **salida byte-
  idéntica** con `banco=AQ-DEMO` y `eje=coste`.

## Fuera de alcance (fronteras honestas)

- **No** se generaliza el engine `presupuesto.py` (`parametros.eje`) — eso es **E1.2**.
- **No** se añade el corte funcional ni `proyectar()` — eso es **E2.1 / E2.2**.
- **No** se crea la familia `banco-carbono` ni `GOL-CAR-01` — eso es la **Ola 2** (E3).
- **No** se toca `GOL-PRE-01` (ni su `expected`, ni sus fixtures, ni su md5).
- **No** se hace `commit` ni release en este hilo: el arranque entrega la **propuesta** para
  ratificación de JM (Llave 2). El git va por `.bat` en el host, nunca desde el desarrollo.
