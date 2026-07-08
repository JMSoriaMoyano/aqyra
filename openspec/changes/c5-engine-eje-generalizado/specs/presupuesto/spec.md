# Delta de spec · Capacidad `presupuesto` — El engine se generaliza a un eje

> Se AÑADE el requisito que codifica el comportamiento del engine cuando `parametros.eje` selecciona
> un eje distinto del coste. Complementa la spec de E1.1 (forma de `valores{}` en la salida). Regla
> forward-open: solo se añaden claves/comportamiento; el eje coste no cambia de semántica.

## ADDED Requirements

### Requirement: El engine valora en el eje pedido sin regresión del coste
`presupuestar(modelo, criterio, banco, parametros)` SHALL aceptar `parametros.eje` (string, default
`"coste"`) y valorar la misma medición en ese eje. El **mapeo clase→partida del criterio** SHALL ser
idéntico entre ejes (se mide una vez). Con `eje == "coste"`, la salida SHALL ser la del contrato C5
previo **byte a byte**: el coste vive en `precio_unitario`/`importe` y **no** se emite `valores`.

#### Scenario: El eje coste por defecto no emite `valores`
- **GIVEN** el modelo, el criterio `AQ/v1` y el banco `AQ-DEMO/v1` de `GOL-PRE-01`
- **WHEN** se llama a `presupuestar(...)` sin `parametros.eje` (o con `eje="coste"`)
- **THEN** ninguna partida del `estado_mediciones` lleva la clave `valores`
- **AND** el resultado es idéntico al `expected` anclado (PEM 7 022,53 → PEC 10 111,74).

#### Scenario: Pedir el eje coste explícito equivale al default
- **GIVEN** las mismas entradas
- **WHEN** se llama con `parametros.eje = "coste"` explícito
- **THEN** el objeto de salida es exactamente igual al del default.

### Requirement: Un eje NO-coste rellena `valores[eje]` etiquetado (espejo)
Con `eje != "coste"`, cada partida SHALL ganar `valores[eje]` con `unitario`, `total` y `unidad` (la
unidad la declara el banco: `unidad_eje`, con *fallback* `moneda`), el `banco` de origen
(`banco.ref`/`banco`; **ausente** cuando `origen == "regla"`) y su `origen`. Los campos requeridos
`precio_unitario`/`importe` SHALL reflejar la magnitud del eje (D19, espejo); la representación
etiquetada autoritativa del eje es `valores[eje]`.

#### Scenario: Partida medida en un eje no-coste
- **GIVEN** un banco que declara `unidad_eje` y `ref` para el eje `carbono`
- **WHEN** se llama con `parametros.eje = "carbono"`
- **THEN** cada partida `origen=modelo` lleva `valores.carbono = { unitario, total, unidad, banco, origen: "modelo" }`
- **AND** `valores.carbono.unitario == precio_unitario` y `valores.carbono.total == importe` (espejo).

#### Scenario: Partida sin geometría en un eje no-coste
- **GIVEN** una partida `origen=regla` (p. ej. S&S por ratio)
- **WHEN** se valora en un eje no-coste
- **THEN** su `valores[eje]` lleva `origen: "regla"` y **no** lleva `banco`.

#### Scenario: El mapeo y las cantidades no cambian entre ejes
- **GIVEN** las mismas entradas valoradas en `coste` y en un eje no-coste
- **WHEN** se comparan los `estado_mediciones`
- **THEN** los pares (código, cantidad, trazabilidad) coinciden exactamente entre ambos ejes.
