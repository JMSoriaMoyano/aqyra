# Delta de spec · Capacidad `presupuesto` — Los cortes nacen del IFC

> Se AÑADE el comportamiento del parser que atribuye cada objeto medido a los cuatro cortes
> (`espacial`, `funcional`, `uniclass`, `gubim`) a partir de las agrupaciones nativas del IFC, con
> `fuente` y reparto de frontera. Complementa E1.1/E1.2 (`valores{}` + `parametros.eje`). Regla
> forward-open: solo se añaden claves/comportamiento; nada existente cambia de semántica. Gobierna N-06.

## ADDED Requirements

### Requirement: El parser atribuye cada objeto a los cortes nativos del IFC
El parser de medición (`medir(...)`) SHALL leer las agrupaciones nativas del modelo y adjuntar a cada
objeto medido `cortes` (opcional): `espacial` (árbol `IfcSpatialStructure`, incl. IFC 4.3
`IfcFacility`/`IfcFacilityPart`), `funcional` (`IfcSystem` y/o `IfcZone`), `uniclass` y `gubim`
(clasificación por objeto). Cada eje SHALL ser una **lista de pertenencias** `{grupo, fraccion, fuente}`
con `fuente ∈ {ifc, criterio}`. Un objeto sin agrupación para un eje SHALL omitir ese eje (nunca error).

#### Scenario: Corte espacial directo desde el árbol
- **GIVEN** un elemento contenido en `IfcBuildingStorey "Planta-01"` vía `IfcRelContainedInSpatialStructure`
- **WHEN** se mide el modelo
- **THEN** el objeto lleva `cortes.espacial = [{ grupo: "…/Planta-01", fraccion: 1.0, fuente: "ifc" }]`.

#### Scenario: Corte funcional desde `IfcSystem`
- **GIVEN** un elemento asignado a un `IfcSystem "Sys/Clima/AireP1"` (`IfcRelAssignsToGroup`)
- **WHEN** se mide el modelo
- **THEN** el objeto lleva una pertenencia `{ grupo: "Sys/Clima/AireP1", fraccion: 1.0, fuente: "ifc" }` en `cortes.funcional`.

#### Scenario: Corte de clasificación (Uniclass/GuBIM)
- **GIVEN** un elemento con código Uniclass `Ss_25_11_16`
- **WHEN** se mide el modelo
- **THEN** el objeto lleva `cortes.uniclass = [{ grupo: "Ss_25_11_16", fraccion: 1.0, fuente: "ifc" }]`.

### Requirement: Atribución espacio→elemento con reparto de frontera 50/50
Para el corte funcional por `IfcZone`, el parser SHALL atribuir cada elemento a los espacios que delimita
vía `IfcRelSpaceBoundary`, con `fraccion = 1/N` para los `N` espacios distintos que delimita, agregada
por zona. La suma de `fraccion` de un objeto atribuido SHALL ser `1.0` por eje. El reparto SHALL
resolverse al construir el modelo neutro (no en la proyección).

#### Scenario: Tabique compartido entre dos zonas (50/50)
- **GIVEN** un tabique que delimita el espacio `E-101` (zona `Aulas`) y el espacio `E-102` (zona `Admin`)
- **WHEN** se mide el modelo
- **THEN** su `cortes.funcional` contiene `{ grupo: "Aulas", fraccion: 0.5, fuente: "ifc" }` y `{ grupo: "Admin", fraccion: 0.5, fuente: "ifc" }`
- **AND** la suma de fracciones del eje `funcional` es `1.0`.

#### Scenario: Elemento interior a un único espacio (100 %)
- **GIVEN** un elemento cuya única frontera es el espacio `E-101` (zona `Aulas`)
- **WHEN** se mide el modelo
- **THEN** su `cortes.funcional` contiene una sola pertenencia `{ grupo: "Aulas", fraccion: 1.0, fuente: "ifc" }`.

### Requirement: *Fallback* del criterio cuando no hay agrupación funcional nativa
Cuando el modelo no declara `IfcSystem` ni `IfcZone`/espacios para un elemento, el parser SHALL derivar
`cortes.funcional` de la tabla `reglas_sistema` del pack criterio (clase/uso → sistema grueso) con
`fuente = "criterio"`. El *fallback* NO SHALL inventar cortes espaciales ni de zona ausentes.

#### Scenario: Muro sin sistema ni zona → funcional por criterio
- **GIVEN** un `IfcWall` exterior sin `IfcSystem` ni frontera de espacio, y un criterio con `reglas_sistema` (`IfcWall` exterior → "Envolvente")
- **WHEN** se mide el modelo
- **THEN** su `cortes.funcional = [{ grupo: "Envolvente", fraccion: 1.0, fuente: "criterio" }]`.

### Requirement: Los cortes no alteran la medición ni el coste
La adición de `cortes` SHALL ser aditiva: la medición, el mapeo clase→partida, el `estado_mediciones`,
los cuadros y el `resumen` (PEM→PEC) SHALL ser idénticos a los de antes de E2.1. `GOL-PRE-01` SHALL
permanecer verde y byte-idéntica (su `expected` sin editar).

#### Scenario: La golden de coste no se mueve
- **GIVEN** las fixtures + criterio `AQ/v1` + banco `AQ-DEMO/v1` de `GOL-PRE-01`
- **WHEN** se recomputa con el parser que ya adjunta `cortes`
- **THEN** el `estado_mediciones` semántico == `expected` (PEM 7 022,53 → PEC 10 111,74), sin regresión.
