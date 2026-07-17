# Golden GOL-MEP-01 — Ingesta MEP al Maestro (F3.1, D-MEP-1..5)

> Primer caso del contrato **CMEP**. Cierra la costura F3.1 del Plan de Cierre:
> el Maestro federado pasa a **reconocer los elementos MEP** y a **mapear sus
> sistemas** («Estructura funcional», D-CH-4). Contract-first: la golden se
> escribió ANTES del engine (modo anclado, falla adrede) y se pone verde cuando
> `engines/ifc/ifc_to_model_mep.py` implementa el reconocimiento.

## Fixture (recorte determinista, D-MEP-5)

`fixtures/mep_min.ifc` — IFC4, anclado por **md5 `8d56937d87cb5b555e99fd3bb07785e2`**
en `versions.lock` (patrón C4-FED-06: el fichero commiteado es el canónico; la
golden verifica CONTENIDO leyéndolo con el engine, no el md5 de una regeneración —
el writer de IfcOpenShell no reproduce bytes idénticos, D-MEP-5). Generado por
`tools/gen_fixture_mep.py` con `time_stamp` de cabecera fijo a 1970. Contiene:

- **10 elementos MEP** de las 7 clases admitidas (D-MEP-1): 3 `IfcPipeSegment`,
  2 `IfcPipeFitting`, 1 `IfcValve`, 1 `IfcFireSuppressionTerminal`,
  1 `IfcFlowTerminal`, 1 `IfcCableCarrierSegment`, 1 `IfcCableCarrierFitting`.
- **2 `IfcDistributionSystem`**: `PCI-agua` (`FIREPROTECTION`, 5 elementos) y
  `Fontaneria` (`DOMESTICCOLDWATER`, 3 elementos), ligados por
  `IfcRelAssignsToGroup` + `IfcRelServicesBuildings` (ambos sirven al edificio `Nave`).
- **2 bandejas** (`IfcCableCarrierSegment`/`Fitting`) **sin sistema a propósito**
  (caso de control: el engine debe reportarlas sin asignar).
- Contención: los 10 en `Planta baja` (`IfcRelContainedInSpatialStructure`), cota `0.0`.

## Oráculo (recompute con el engine real; verificado a mano 2026-07-17)

El runner `run_case_cmep` EJERCITA `ifc_to_model_mep.parsear()` (IFC → modelo neutro,
vista `instalaciones`) y comprueba contra `expected.json`:

1. **Ancla del fixture**: md5 == fila de `versions.lock`.
2. **Recompute**: el engine parsea sin error (modo anclado: sin engine, falla adrede).
3. **Conformidad C1**: el modelo neutro conforma `modelo-neutro.schema.json`
   (vista `instalaciones`, forward-open).
4. **Conteo por CLASE EXACTA**: 7 clases, 10 elementos. **Trampa IFC4**:
   `IfcFireSuppressionTerminal` es subtipo de `IfcFlowTerminal`, así que `by_type`
   los sumaría dos veces → el engine cuenta por `is_a()` exacto → `IfcFlowTerminal = 1`.
5. **Asignación elemento→sistema**: PCI=5, Fontanería=3, **2 sin sistema**.
6. **Sistemas**: 2, con su `PredefinedType` y edificio servido (`Nave`).
7. **Planta**: los 10 en `Planta baja`, cota `0.0 m`.

## Regla de oro

Un fallo NO se arregla aflojando esta golden: se corrige en el engine. La ancla es
por **conteos + asignaciones** (determinismo), no por md5 de la salida del engine.
Ampliar el catálogo de clases MEP (D-MEP-1, forward-open) = añadir a `CLASES_MEP`
del engine + su fila en `expected.json`, no re-diseñar el caso. El grafo de red por
puertos (5.498 `IfcDistributionPort`) queda fuera de v0 (D-MEP-4): incremento
posterior por `aqyra_core.grafo_red`.
