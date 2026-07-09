# Delta de spec · Capacidad `presupuesto` — Ingesta FIEBDC-3/2024 → pack `banco`

> Se AÑADE el comportamiento del adaptador de frontera que TRADUCE un `.bc3` (FIEBDC-3/2024) a un pack
> `banco` con el esquema existente (AQ-DEMO). NO cambia ningún esquema de contrato (entrada/salida de C5
> intactas): es una FUENTE nueva de packs `banco`. Traducción determinista; el `.bc3` de muestra es
> PROPIO/sintético (D-026). Regla forward-open: solo se añade capacidad; nada existente cambia de semántica.

## ADDED Requirements

### Requirement: La ingesta traduce un `.bc3` a un pack `banco` con el esquema existente
El adaptador `aqyra_bc3.ingerir_bc3(path)` SHALL leer un fichero FIEBDC-3/2024 (`.bc3`) y producir un
`banco.json` con el **mismo esquema** que `data/packs/banco/AQ-DEMO/v1` (`{banco, titulo, moneda,
costes_indirectos_pct, partidas:[{codigo, unidad, descripcion, clasificacion_uniclass, componentes:
[{tipo, descripcion, unidad, rendimiento, precio, subtotal}], costes_indirectos, precio}]}`). La
traducción SHALL ser **determinista**: el mismo `.bc3` produce el mismo `banco.json` byte a byte. La
ingesta NO SHALL cambiar ningún esquema de contrato de C5.

#### Scenario: Concepto simple → partida con componentes
- **GIVEN** un `~C` de partida `FAB010` (tipo `0`, precio `31.42`) con un `~D` que lo descompone en
  `MO001` (tipo `1`, 24.00, rend 0.40), `MO002` (tipo `1`, 20.00, rend 0.42) y `MT001` (tipo `3`, 12.50, rend 1.00)
- **WHEN** se ingiere el `.bc3`
- **THEN** el banco lleva la partida `FAB010` con tres `componentes` de `tipo` `mano_obra`, `mano_obra`
  y `material`, `subtotal` `9.60`, `8.40` y `12.50`, `costes_indirectos` `0.92` y `precio` `31.42`.

### Requirement: El subset v0 lee `~V`, `~C`, `~D`, `~T`
El adaptador SHALL soportar en v0 los registros `~V` (cabecera + juego de caracteres), `~C` (conceptos:
código, unidad, resumen→descripción, precio, tipo→naturaleza), `~D` (descomposiciones) y `~T` (texto de
pliego). El `~T` SHALL parsearse pero NO emitirse al banco v0. El `~M` (mediciones) SHALL ignorarse en
v0 (es del flujo de emisión E0.2). La naturaleza SHALL mapear `1`→`mano_obra`, `2`→`maquinaria`,
`3`→`material`.

#### Scenario: Transcodificación del juego de caracteres a UTF-8
- **GIVEN** un `.bc3` codificado en ANSI (Windows-1252) con `~V` que declara `ANSI` y descripciones con acentos
- **WHEN** se ingiere el `.bc3`
- **THEN** el `banco.json` sale en UTF-8 con los acentos intactos (p. ej. «Fábrica», «hormigón»).

### Requirement: Precio compuesto con costes indirectos y guarda de consistencia
El adaptador SHALL calcular `subtotal = precio_hijo × factor × rendimiento` (Decimal, HALF_UP, 2
decimales), `costes_indirectos = Σ subtotales × costes_indirectos_pct` (v0 = 3%) y `precio = Σ
subtotales + costes_indirectos`. Si el precio compuesto NO casa (±0,01) con el precio declarado en el
`~C`, el adaptador SHALL registrar un aviso auditable (`_avisos_ingesta`) y NO SHALL silenciarlo.

#### Scenario: Precio del `~C` incoherente con la descomposición → aviso
- **GIVEN** un `~C` de partida cuyo precio declarado difiere en más de 0,01 del Σ subtotales + CI
- **WHEN** se ingiere el `.bc3`
- **THEN** el banco resultante incluye `_avisos_ingesta` con el código de la partida afectada.

### Requirement: El pack de muestra se ancla y no mueve la zona anclada
El pack `banco/AQ-BC3-DEMO/v1` SHALL anclarse por su `content_sha256` (golden de pack) y por el
`md5(banco.json)` + `md5(muestra.bc3)` del manifiesto; su versión SHALL anclarse en `versions.lock`
bajo `[packs.banco_bc3]`. El pack `banco/AQ-DEMO/v1` (`[packs.banco]`), los packs `criterio/AQ/v1`+`v2`
y las golden `GOL-PRE-01/02/03` y `GOL-DOC-01` SHALL permanecer intactos.

#### Scenario: El banco anclado se reproduce desde su `.bc3`
- **GIVEN** el `.bc3` de muestra `fuente/muestra.bc3` (PROPIO/sintético) y el `banco.json` anclado
- **WHEN** se ejecuta `ingerir_bc3(fuente/muestra.bc3)`
- **THEN** el `banco.json` reproducido es idéntico byte a byte al anclado (determinismo del adaptador)
- **AND** `content_sha256`, `md5(banco.json)` y `md5(muestra.bc3)` casan con el golden y el manifiesto.
