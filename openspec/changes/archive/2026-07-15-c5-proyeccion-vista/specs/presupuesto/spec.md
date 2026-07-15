# Delta de spec · Capacidad `presupuesto` — La proyección

> Se AÑADE `proyectar(...)` (group-by determinista sobre los `cortes` de E2.1 + el valor de cada partida)
> y la clave aditiva `traza_cantidades` (desglose por objeto). Complementa E1.1/E1.2 (`valores{}` +
> `parametros.eje`) y E2.1 (`cortes`). Regla forward-open: solo se añaden claves/comportamiento; nada
> existente cambia de semántica. La proyección es **consulta, no cálculo**. Gobierna N-06.

## ADDED Requirements

### Requirement: El motor publica la contribución por objeto de cada partida (`traza_cantidades`)
El motor (`presupuestar(...)`) SHALL adjuntar a cada partida `origen=modelo` la clave opcional
`traza_cantidades`: la lista `{guid, cantidad}` de la contribución de cada objeto a la cantidad de esa
partida. La suma de `cantidad` de `traza_cantidades` SHALL igualar la `cantidad` de la partida. Las
partidas `origen=regla` (sin geometría) NO SHALL llevar `traza_cantidades`. La adición SHALL ser aditiva:
`GOL-PRE-01`/`GOL-PRE-02`/`GOL-DOC-01` permanecen verdes (el recompute compara claves nombradas).

#### Scenario: Dos muros a la misma partida
- **GIVEN** dos muros `M-Fachada` (15,90 m²) y `M-Interior` (18,00 m²) que mapean a `FAB010`
- **WHEN** se presupuesta
- **THEN** `FAB010.traza_cantidades = [{guid:M-Fachada, cantidad:15.90}, {guid:M-Interior, cantidad:18.00}]`
- **AND** su suma (33,90) == `FAB010.cantidad`.

#### Scenario: Partida sin geometría no lleva desglose
- **GIVEN** la partida `SYS010` (Seguridad y Salud, `origen=regla`, `trazabilidad: []`)
- **WHEN** se presupuesta
- **THEN** `SYS010` NO lleva `traza_cantidades`.

### Requirement: `proyectar` agrupa el valor por eje y corte sin recálculo
`proyectar(presupuesto, modelo, eje, corte)` SHALL devolver una lista `{grupo, valor_total, unidad,
n_partidas, guids[], fuente}`, agregando el valor de cada partida por los grupos del `corte` pedido. El
valor de una partida SHALL ser `importe` cuando `eje == "coste"` (D16) y `valores[eje].total` en otro
caso (0 si ausente). `proyectar` NO SHALL re-medir ni re-valorar (group-by determinista). La salida SHALL
ser determinista (mismo orden y valores en ejecuciones repetidas).

#### Scenario: Proyección del coste por planta
- **GIVEN** un presupuesto y un modelo cuyos objetos llevan `cortes.espacial`
- **WHEN** `proyectar(presupuesto, modelo, "coste", "espacial")`
- **THEN** cada fila lleva el `importe` agregado de las partidas de esa planta, con `unidad = "EUR"`.

### Requirement: Atribución partida→objeto por magnitud EXACTA
`proyectar` SHALL repartir el valor de una partida entre los objetos de su `trazabilidad` en proporción a
su contribución de cantidad (`traza_cantidades`): `share_O = cantidad_O / Σ cantidad_O`. De cada objeto a
sus grupos, SHALL multiplicar por la `fraccion` de `cortes[corte]` (resuelta por el parser en E2.1,
incluido el reparto 50/50). Si `Σ cantidad_O == 0`, SHALL degradar a reparto equitativo `1/n`.

#### Scenario: Reparto por tamaño, no por cabezas
- **GIVEN** `FAB010` (importe I) con `M-Fachada` (15,90 m²) en la Planta-01 y `M-Interior` (18,00 m²) en la Planta-02
- **WHEN** `proyectar(..., "coste", "espacial")`
- **THEN** la Planta-01 recibe `I × 15,90/33,90` y la Planta-02 `I × 18,00/33,90` (no `I/2` cada una).

#### Scenario: `IfcZone` con reparto 50/50 (atribución fraccionaria)
- **GIVEN** un tabique con `cortes.funcional = [{grupo:Aulas,fraccion:0.5},{grupo:Admin,fraccion:0.5}]`
- **WHEN** `proyectar(..., "coste", "funcional")`
- **THEN** su valor de objeto se reparte 50 % a `Aulas` y 50 % a `Admin`
- **AND** `Σ` por zonas del eje `funcional` == total del presupuesto.

### Requirement: La proyección conserva el total (invariante Σ) con residuales
Para cada `(eje, corte)`, `Σ valor_total` de la proyección SHALL igualar `Σ` del `estado_mediciones` en
ese eje (±redondeo declarado). El valor no atribuible a un grupo real SHALL caer en un grupo residual
determinista: una partida `origen=regla` (sin `trazabilidad`) en `"(sin geometría)"` (`fuente="regla"`);
un objeto sin el eje de corte pedido en `"(sin clasificar)"` (`fuente="—"`).

#### Scenario: Σ proyección == Σ estado de mediciones
- **GIVEN** un presupuesto con PEM P (incluida S&S `origen=regla`)
- **WHEN** se proyecta por cualquier `(eje, corte)`
- **THEN** `Σ valor_total` (grupos reales + residuales) == P (±`importe_abs`).

#### Scenario: Partida sin geometría al residual
- **GIVEN** `SYS010` (`origen=regla`, sin `trazabilidad`)
- **WHEN** se proyecta el coste por cualquier corte
- **THEN** su importe entero aparece en el grupo `"(sin geometría)"` con `fuente="regla"`.

### Requirement: *Fallback* del criterio visible en la proyección
Cuando el corte `funcional` de un objeto proviene del *fallback* del criterio (`fuente="criterio"`, D22),
la fila de proyección de ese grupo SHALL declarar `fuente="criterio"`. Un grupo alimentado por
pertenencias `ifc` y `criterio` SHALL declarar `fuente="criterio"` (traza honesta del *fallback*).

#### Scenario: Vista funcional por *fallback*
- **GIVEN** objetos sin `IfcSystem`/`IfcZone` cuyo `cortes.funcional` sale de `reglas_sistema` (`criterio/AQ/v2`)
- **WHEN** `proyectar(..., "coste", "funcional")`
- **THEN** las filas de esos sistemas gruesos llevan `fuente="criterio"`.
