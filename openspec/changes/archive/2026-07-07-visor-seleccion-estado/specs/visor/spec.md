# Delta de spec · Capacidad `visor` — Selección + estado de dato (Slice 2)

> Se AÑADEN los requisitos del estado de dato por elemento y su chip en el panel de Selección.
> Superficie `apps/visor` propone puro: no dispara las llaves; el visor NO acuña el estado
> certificado. Reutiliza el resalte ámbar y la lectura de Psets ya existentes.

## ADDED Requirements

### Requirement: Estado de dato derivado por elemento
El visor SHALL derivar el `DataState` de un elemento a partir de los **nombres de sus Property
Sets**: un elemento con un Pset de **resultado** de un motor SHALL ser `computed`; sin él,
`proposal`. El visor NO SHALL inferir `qa-passed` ni `verified-signed` (los acuña el flujo de
firma, D-021); si el dato porta un estado explícito, `estadoDato` SHALL respetarlo.

#### Scenario: Elemento con Pset de resultado es «computed»
- **GIVEN** un elemento cuyos Psets incluyen `Pset_AqyraStructural`
- **WHEN** se calcula `estadoDato(nombresDePsets)`
- **THEN** el estado es `computed`.

#### Scenario: Elemento sin Pset de resultado es «proposal»
- **GIVEN** un elemento cuyos Psets son solo `Pset_WallCommon`
- **WHEN** se calcula `estadoDato(nombresDePsets)`
- **THEN** el estado es `proposal`.

#### Scenario: El visor no inventa el estado certificado
- **GIVEN** cualquier conjunto de nombres de Psets sin estado explícito
- **WHEN** se calcula `estadoDato(...)`
- **THEN** el resultado NUNCA es `verified-signed` por inferencia
- **AND** un estado `explicito` provisto por el dato se devuelve tal cual.

### Requirement: Chip de estado en el panel de Selección
Al seleccionar un elemento, el visor SHALL mostrar en el panel de Selección su clase, su GlobalId,
sus Psets y un **chip de estado** con la etiqueta y el color de `dataStateStyle(estado)`. El trato
«certificado» (verde/limpio) SHALL condicionarse a `isCertified` (solo `verified-signed`); los
estados no firmados SHALL mostrarse con su marca (no verde).

#### Scenario: El chip refleja el estilo del estado
- **GIVEN** un elemento cuyo estado derivado es `computed`
- **WHEN** se pinta el panel de Selección
- **THEN** el chip muestra la etiqueta y el color de `dataStateStyle("computed")` (NO VERIFICADO, rojo)
- **AND** NO recibe el trato certificado (`isCertified("computed")` es falso).

#### Scenario: La selección conserva el resalte ámbar
- **GIVEN** un elemento seleccionado (clic en escena o en el árbol)
- **WHEN** se aplica el resalte de selección
- **THEN** el elemento se resalta en ámbar `#ff8a3d` (color de selección existente del visor)
- **AND** el panel muestra su clase, GlobalId, chip de estado y Psets.
