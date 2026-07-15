# Delta de spec · Capacidad `presupuesto` — Emisión `salida-presupuesto` → FIEBDC-3/2024

> Se AÑADE el comportamiento del adaptador de frontera que TRADUCE una `salida-presupuesto` (JSON de C5) a
> un fichero FIEBDC-3/2024 (`.bc3`), y su re-lector para el round-trip. NO cambia ningún esquema de contrato
> (entrada/salida de C5 intactas): la emisión LEE `salida-presupuesto` tal cual. Traducción determinista;
> el único no-determinismo es el sello de fecha del `~V`. Regla forward-open: solo se añade capacidad; nada
> existente cambia de semántica (la ingesta `ingerir_bc3` de E0.1 no se toca).

## ADDED Requirements

### Requirement: La emisión traduce una `salida-presupuesto` a un `.bc3` FIEBDC-3/2024
El adaptador `aqyra_bc3.emitir_bc3(salida)` SHALL leer una `salida-presupuesto` (esquema de salida de C5) y
producir el texto de un fichero FIEBDC-3/2024 (`.bc3`). La traducción SHALL ser **determinista**: la misma
`salida-presupuesto` con el mismo sello de fecha produce el mismo `.bc3` byte a byte. La emisión NO SHALL
recalcular precios ni mediciones (los LEE de la salida) y NO SHALL cambiar ningún esquema de contrato de C5.

#### Scenario: Partida medida → concepto + descomposición + medición
- **GIVEN** una `salida-presupuesto` con una partida `FAB010` (unidad `m2`, `precio_unitario` `31.42`,
  `cantidad` `33.9`) y su `cuadro_precios_2` con dos componentes (mano de obra y material)
- **WHEN** se emite el `.bc3`
- **THEN** el `.bc3` lleva un `~C` de `FAB010` (tipo `0`, precio `31.42`), un `~D` que lo descompone en dos
  conceptos hijo (tipo `1` y `3`) y un `~M` cuya medición total es `33.9`.

### Requirement: El subset emitido v0 es `~V`, `~C`, `~D`, `~M`, `~T`
El adaptador SHALL emitir en v0 los registros `~V` (cabecera + juego de caracteres + sello de fecha), `~C`
(partidas con `tipo 0` y componentes con naturaleza `1`/`2`/`3`), `~D` (descomposiciones), `~M`
(mediciones) y `~T` (texto de pliego mínimo = la descripción de la partida). Las líneas de `~M` SHALL
desglosarse **por objeto** desde `traza_cantidades` (una línea por objeto, con su GUID en el comentario)
cuando la partida la tenga, y SHALL ser una **línea única** con la cantidad total cuando no la tenga.

#### Scenario: Desglose por objeto desde `traza_cantidades`
- **GIVEN** una partida `origen=modelo` con `traza_cantidades` de dos objetos (GUIDs `A` y `B`, cantidades
  `5.4` y `10.8`)
- **WHEN** se emite el `.bc3`
- **THEN** el `~M` de la partida lleva dos líneas de medición con los GUIDs `A` y `B` y sus cantidades, y
  la medición total es `16.2`.

#### Scenario: Línea única cuando no hay traza (p. ej. `origen=regla`)
- **GIVEN** una partida `SYS010` (`origen=regla`, `cantidad` `1`, sin `traza_cantidades`)
- **WHEN** se emite el `.bc3`
- **THEN** el `~M` de la partida es una única línea con la cantidad total `1` y sin GUIDs.

### Requirement: Codificación de salida y sello de fecha
El adaptador SHALL emitir en **UTF-8** por defecto (el `~V` declara `UTF-8`) y SHALL admitir un `charset`
parametrizable (p. ej. `cp1252` → token `ANSI`) para destinos legacy. El sello de fecha del `~V` SHALL ser
un parámetro `fecha` (AAAAMMDD) con un valor por defecto **determinista** (nunca la fecha del sistema), de
modo que sea el único no-determinismo del emisor.

#### Scenario: El sello de fecha es el único no-determinismo
- **GIVEN** una misma `salida-presupuesto`
- **WHEN** se emite dos veces con dos sellos de fecha distintos
- **THEN** toda diferencia entre los dos `.bc3` se explica por la sustitución del sello, y los registros
  `~D`/`~M`/`~T` (que no llevan fecha) son idénticos.

### Requirement: El round-trip conserva los importes (re-lector `leer_bc3_presupuesto`)
El adaptador SHALL proveer `aqyra_bc3.leer_bc3_presupuesto(origen)` que reconstruye el `estado_mediciones`
desde un `.bc3` (cantidad de las `~M`, `precio_unitario` del `~C`, `importe = cantidad × precio_unitario`,
trazabilidad de los GUIDs). El `.bc3` emitido desde una `salida-presupuesto`, REIMPORTADO, SHALL reproducir
cada `importe` con tolerancia **±0,01** y cada `cantidad` con tolerancia **±0,5%** (D3). El anclaje del
golden SHALL ser **semántico** (identidad de importes), NO el `md5` del `.bc3`.

#### Scenario: Round-trip de GOL-PRE-01 con identidad de importes
- **GIVEN** la `salida-presupuesto` ANCLADA de `GOL-PRE-01` (PEM `7 022,53`)
- **WHEN** se emite a `.bc3` y se reimporta con `leer_bc3_presupuesto`
- **THEN** cada `importe` del `estado_mediciones` se reproduce dentro de ±0,01, cada `cantidad` dentro de
  ±0,5%, y la Σ de importes reconstruidos casa con el PEM `7 022,53`
- **AND** `packages/golden` (GOL-PRE-01/02/03, GOL-DOC-01) y los packs anclados permanecen intactos.
