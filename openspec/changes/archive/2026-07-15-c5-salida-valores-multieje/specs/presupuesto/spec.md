# Delta de spec · Capacidad `presupuesto` — Eje de valor multi-eje en la salida

> Primera especificación formal de la capacidad `presupuesto` (contrato C5): se AÑADE el requisito
> que codifica el eje de valor genérico `valores{}` en la salida. (No hay baseline previa en
> `openspec/specs/presupuesto/`.) Regla forward-open: solo se añaden claves; ninguna existente cambia
> de semántica.

## ADDED Requirements

### Requirement: Eje de valor genérico en la partida medida
La salida de `presupuestar()` SHALL admitir, por cada partida del estado de mediciones, un objeto
**opcional** `valores` indexado por **id de eje** (string libre), donde cada eje aporta su valor
`unitario`, su `total`, su `unidad` y, opcionalmente, el `banco` de origen y un desglose por `etapas`
del ciclo de vida. El eje **coste** canónico SHALL permanecer en `precio_unitario` / `importe`, sin
duplicarse ni alterarse; `valores` es aditivo y su ausencia es válida.

#### Scenario: Una partida sin `valores` sigue siendo válida
- **GIVEN** una salida de presupuesto conforme al contrato C5 previo (p. ej. `GOL-PRE-01`)
- **WHEN** se valida contra el esquema extendido con `valores{}`
- **THEN** la partida **sin** la clave `valores` conforma sin error
- **AND** su `precio_unitario`/`importe` (eje coste) no cambian de semántica ni de valor.

#### Scenario: Una partida declara un eje adicional
- **GIVEN** una partida con `valores.carbono = { unitario, total, unidad: "kgCO2e", banco }`
- **WHEN** se valida contra el esquema extendido
- **THEN** el eje `carbono` conforma como `valor_eje`
- **AND** el eje `coste` sigue expresado en `precio_unitario`/`importe` (no en `valores`).

#### Scenario: Un eje sin factor para la partida omite su clave (nunca error)
- **GIVEN** un banco que no cubre la clase de una partida para el eje pedido
- **WHEN** se compone la salida
- **THEN** la clave de ese eje **no aparece** en `valores` para esa partida
- **AND** la salida sigue siendo conforme (forward-open: ausencia, no error).

### Requirement: Id de eje abierto y desglose por etapas EN 15978
El id de eje SHALL ser un `string` libre (convención `coste`, `carbono`, `agua`, `energia_embebida`,
…) **sin** enum cerrado, de modo que añadir un eje no re-ancle el contrato. Cuando un `valor_eje`
declare `etapas`, estas SHALL ser un objeto `clave→número` con claves convencionales de EN 15978
(`A1A3`, `A4A5`, `B`, `C`, `D`), y la suma de las etapas presentes SHALL igualar el `total` del eje.

#### Scenario: Añadir un eje nuevo no re-ancla el contrato
- **GIVEN** el esquema con la clave de `valores` como string libre
- **WHEN** un pack introduce el eje `agua`
- **THEN** `valores.agua` conforma sin modificar el esquema ni re-anclar el contrato.

#### Scenario: El desglose por etapas suma el total del eje
- **GIVEN** un `valor_eje` con `total` y `etapas = { A1A3, A4A5 }`
- **WHEN** se comprueba la coherencia del eje
- **THEN** `A1A3 + A4A5` es igual a `total` (invariante; desglose parcial admitido).

### Requirement: No-regresión del eje coste anclado
La extensión `valores{}` SHALL preservar byte a byte el oráculo de coste anclado (`GOL-PRE-01`): su
`expected` no se edita y su recomputación permanece idéntica.

#### Scenario: La golden de coste permanece intacta
- **GIVEN** el `expected.json` anclado de `GOL-PRE-01` (sin `valores`)
- **WHEN** se aplica el esquema extendido y se re-ejecuta el runner C5
- **THEN** `GOL-PRE-01` queda **verde y byte-idéntica** (PEM 7 022,53 → PEC 10 111,74)
- **AND** ningún `expected` ni md5 de fixture se modifica.
