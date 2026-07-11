# Delta de spec · Capacidad `visor` — Dashboard de valor (skin de proyección)

> Se AÑADE una **skin de dashboard de valor** que presenta la vista `proyectar(eje, corte)` del contrato C5
> (E2.2, anclada por `GOL-PRE-03`) sobre el visor. Regla forward-open: sólo se añade una piel/vista; nada
> existente del visor cambia de semántica. La skin es **consulta, no cálculo**: **no** re-mide, **no**
> re-valora, **no** re-proyecta. Gobierna N-06 (proyección = consulta) y N-02 (la vista se siente gratis; el
> muro de cobro es el export firmable).

## ADDED Requirements

### Requirement: La skin consume la proyección precomputada, sin cálculo en cliente
La skin de dashboard SHALL consumir un **índice de proyección precomputado** (la salida de
`proyectar(presupuesto, modelo, eje, corte)` serializada, forma `{eje, corte, suma, grupos[]}` con
`grupos[].{grupo, valor_total, unidad, n_partidas, guids[], fuente}`). La skin NO SHALL ejecutar el engine,
re-medir, re-valorar ni re-proyectar en el cliente. La presentación SHALL ser determinista (mismo índice →
mismas filas y mismo orden).

#### Scenario: La vista lee, no calcula
- **GIVEN** un índice de proyección precomputado con las vistas `(coste, espacial)`, `(coste, funcional)`, `(coste, uniclass)`
- **WHEN** se abre la skin y se selecciona `(coste, espacial)`
- **THEN** la tabla muestra una fila por grupo con `valor_total`/`unidad`/`n_partidas`/`fuente` tal cual del índice
- **AND** la skin no recalcula ningún `valor_total` (los valores son los del índice).

### Requirement: La skin conserva y hace visible el invariante Σ
Para cada vista mostrada, la skin SHALL exponer que `Σ valor_total(grupos) == suma` del eje (±0,01) y SHALL
mostrar los grupos residuales (`(sin geometría)`, `(sin clasificar)`) sin ocultarlos, con su `fuente`.

#### Scenario: Σ visible y grupos residuales presentes
- **GIVEN** la vista `(coste, espacial)` con `suma = 7022.53` que incluye `(sin geometría) = 137.70` (`fuente=regla`)
- **WHEN** se presenta la vista
- **THEN** la pastilla de invariante casa (`Σ grupos == 7022.53`, ±0,01)
- **AND** el grupo `(sin geometría)` aparece en la tabla con `fuente=regla`.

### Requirement: Selección de un grupo resalta sus objetos en 3D
Al seleccionar una fila de la proyección, la skin SHALL resaltar en el maestro 3D exactamente los `guids[]` de
ese grupo (reutilizando la selección del `Viewer`), sin reescribir el modelo ni la geometría.

#### Scenario: Del grupo al objeto
- **GIVEN** una fila de la vista `(coste, espacial)` cuyo grupo lleva `guids = [g1, g2]`
- **WHEN** se selecciona esa fila
- **THEN** el `Viewer` resalta `g1` y `g2` y sólo esos.

### Requirement: La skin reproduce la golden de proyección `GOL-PRE-03`
La aceptación de la skin (E2E TS) SHALL reproducir, a partir de la fixture de proyección, los grupos y
`valor_total` de las vistas `i-planta` (coste·espacial), `ii-uniclass` (coste·uniclass) y `iii-v-funcional`
(coste·funcional) de `GOL-PRE-03`, incluida la `fuente` (`ifc`/`criterio`/`regla`/`—`). Un desajuste SHALL
corregirse en el emisor/engine, NUNCA en el cliente.

#### Scenario: Reproducción del *fallback* del criterio
- **GIVEN** la vista `(coste, funcional)` de la fixture
- **WHEN** la skin la presenta
- **THEN** las filas de los sistemas gruesos del *fallback* llevan `fuente=criterio`, como `GOL-PRE-03.iii-v-funcional`.

### Requirement: La skin es «propone» — no certifica
La skin NO SHALL marcar como certificada (`isCertified`) ninguna proyección. El muro de cobro (export firmable
de la proyección con dos llaves) SHALL quedar como acción diferida (forward), no como estado de la vista.

#### Scenario: La vista no certifica
- **GIVEN** cualquier vista de proyección mostrada
- **WHEN** se consulta el estado de dato de la vista
- **THEN** `isCertified` es `false` (la proyección es consulta; el export firmable llega como acción, no como certificación).
