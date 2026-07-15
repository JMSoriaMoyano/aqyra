# Delta de spec · Capacidad `presupuesto` — Eje CARBONO (E3)

> AÑADE los requisitos del eje **carbono** sobre la capacidad `presupuesto` (contrato C5). El esquema de
> SALIDA **no cambia** (`valores.carbono` + `etapas` ya caben, E1.1/D16–D18); el delta es de comportamiento
> del motor (emitir `etapas`), una familia de pack nueva (`banco-carbono`) y una golden nueva
> (`GOL-CAR-01`). Regla forward-open: sólo se añaden claves/familias; ninguna existente cambia de semántica.

## ADDED Requirements

### Requirement: El motor emite el desglose por etapas de un eje no-coste
Cuando `parametros.eje != "coste"` y el `banco` declara, por partida, factores por etapa del ciclo de vida,
`presupuestar()` SHALL emitir `valores[eje].etapas` (objeto `clave→número`, EN 15978) tal que la suma de las
etapas presentes sea **exactamente** igual a `valores[eje].total`. El reparto SHALL ser determinista: la
última etapa presente (orden canónico `A1A3`, `A4A5`, `B`, `C`, `D`) absorbe el residuo de redondeo. El eje
`coste` (default) SHALL seguir sin emitir `valores` (no-regresión de `GOL-PRE-01`).

#### Scenario: Cada partida origen=modelo del eje carbono lleva etapas que suman el total
- **GIVEN** un `banco-carbono` con factores por etapa `A1A3`/`A4A5` por partida
- **WHEN** se presupuesta la medición de `GOL-PRE-01` con `eje="carbono"`
- **THEN** cada partida `origen=modelo` tiene `valores.carbono.etapas = { A1A3, A4A5 }`
- **AND** `A1A3 + A4A5` es exactamente igual a `valores.carbono.total` (invariante D18)
- **AND** `valores.carbono.total` es igual a `importe` (espejo D19) y `valores.carbono.unidad = "kgCO2e"`.

#### Scenario: Una partida sin factor de banco no lleva etapas
- **GIVEN** una partida `origen=regla` (p. ej. Seguridad y Salud por ratio), sin respaldo en el banco
- **WHEN** se presupuesta con `eje="carbono"`
- **THEN** la partida lleva `valores.carbono` etiquetado (sin `banco`) **y sin** `etapas` (forward-open).

#### Scenario: El run de coste no cambia
- **GIVEN** `eje="coste"` (default) con el banco de coste `AQ-DEMO`
- **WHEN** se presupuesta la medición de `GOL-PRE-01`
- **THEN** ninguna partida emite `valores` y el resumen es PEM 7 022,53 → PEC 10 111,74 (byte-idéntico).

### Requirement: Familia de pack `banco-carbono`
El manifiesto de pack SHALL admitir la familia **`banco-carbono`** (aditiva al enum
`codigos/normativa/banco/criterio/ids`). Un pack `banco-carbono/<fuente>/vN` SHALL declarar, por código de
partida, un factor unitario en `kgCO2e` y su desglose por etapas (EN 15978), anclado por `content_sha256`
en `versions.lock [packs.banco_carbono]` con su golden de pack.

#### Scenario: El pack banco-carbono se carga y ancla como los demás
- **GIVEN** `data/packs/banco-carbono/generico/v1/pack.json`
- **WHEN** el loader `aqyra_packs` valida el manifiesto y calcula su `content_sha256`
- **THEN** el manifiesto conforma `pack.schema.json` con `familia = "banco-carbono"`
- **AND** su hash casa con el golden de pack anclado (identidad de contenido).

### Requirement: Golden GOL-CAR-01 (valoración carbono anclada)
La capacidad SHALL anclar un caso `GOL-CAR-01` que valora la MISMA medición de `GOL-PRE-01` en el eje
carbono, anclado por DETERMINISMO + SEMÁNTICA + INVARIANTE (no por md5 de salida): `valores.carbono` por
partida (con etapas y Σ etapas = total), un resumen del eje, y una proyección de carbono por un corte con
`Σ proyección == Σ valores.carbono`. `GOL-PRE-01/02/03` y `GOL-DOC-01` SHALL permanecer byte-idénticas.

#### Scenario: La proyección de carbono conserva el total
- **GIVEN** el presupuesto de carbono de `GOL-CAR-01` sobre las fixtures aumentadas de `GOL-PRE-03`
- **WHEN** se proyecta `proyectar(pres, modelo, "carbono", corte)`
- **THEN** la suma de los grupos es igual a la suma de `valores.carbono` del estado de mediciones (±0,01)
- **AND** los grupos del corte coinciden con los de la vista de coste homóloga (el corte no depende del eje).

#### Scenario: La golden de coste no se re-ancla
- **GIVEN** la incorporación del caso `GOL-CAR-01`
- **WHEN** se ejecuta el runner del contrato C5
- **THEN** `GOL-PRE-01/02/03` y `GOL-DOC-01` quedan byte-idénticas (E3 sólo AÑADE `GOL-CAR-01`).
