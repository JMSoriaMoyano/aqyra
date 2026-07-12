# Golden GOL-PRE-04 - presupuesto con banco de coste REAL BCCA (C5, eje coste)

> Caso NUEVO (patron GOL-PRE-01/GOL-CAR-02). Valora la MISMA medicion anclada de `GOL-PRE-01` con el pack de
> coste REAL `banco/BCCA/v1` (derivado de la Base de Costes de la Construccion de Andalucia -Junta de Andalucia-,
> edicion BCCA2023_V02, CC-BY 3.0) + `criterio/AQ/v1`, modo coste. NO edita `GOL-PRE-01/02/03` (intactas, usan
> `AQ-DEMO`). El coste es traduccion determinista, no calculo: cada precio sale del banco, pero con BCCA es
> DERIVABLE y TRAZABLE a su codigo BCCA (`banco.json>provenance`). Convencion banco+criterio, no verdad fisica.
> Decisiones D49-D52. Registro de licencias: `Aqyra-Negocio/RECONCILIACION_licencias-coste.md`.

## Que ancla (patron GOL-PRE-01; el runner ANTEPONE el recompute del engine)

1. **Identidad** - md5 de las fixtures `entrada/ARQ.ifc`+`EST.ifc` (las MISMAS de `GOL-PRE-01`:
   `0b998513...`/`0d7e7f20...`; la medicion es identica, solo cambia el banco).
2. **Packs** - `criterio/AQ/v1` + `banco/BCCA/v1` anclados en `versions.lock` (`[packs.banco_bcca]`); el runner
   busca el banco por su clave de lock (`banco`/`banco_bc3`/`banco_bcca`). `[packs.banco]=AQ-DEMO/v1` intacto.
3. **Esquema** - el presupuesto conforma `salida-presupuesto.schema.json` SIN tocarlo.
4. **RECOMPUTE** (conda `mcp-bim`, ifcopenshell; y gate CI) - `medir(fixtures, criterio/AQ/v1)` +
   `presupuestar(..., banco=banco/BCCA/v1)` reproduce ESTE expected.
5. **Coherencia interna** - importe = cantidad x precio; precio_unitario == cuadro n1 == banco; n1 == n2
   (Sum componentes + indirectos); PEM = Sum importes = Sum capitulos; GG/BI/base/IVA/PEC segun parametros;
   partidas origen=modelo subset banco (precio == banco) y subset criterio; trazabilidad subset GUIDs del modelo;
   S&S (origen=regla) = 2% del PEM medible.

## Oraculo del eje (calculado a mano y verificado x2)

Precios REALES del `banco/BCCA/v1` (EUR) x cantidades ancladas de `GOL-PRE-01`:

| partida | cantidad | precio BCCA | importe | codigo BCCA de origen |
|---|---|---|---|---|
| CSZ010 | 0,128 m3 | 164,18 | 21,02 | 03HRZ80000 |
| EHS010 | 1,92 m3 | 433,17 | 831,69 | 05HRP80010 |
| EHL010 | 16,20 m3 | 418,01 | 6.771,76 | 05HRL80010 |
| FAB010 | 33,90 m2 | 28,94 | 981,07 | 06LPC80000 |
| REV010 | 67,80 m2 | 12,98 | 880,04 | 10CEE00001 |
| PIN010 | 67,80 m2 | 4,60 | 311,88 | 13IPP90016 |
| PPM010 | 1 ud | 263,29 | 263,29 | 11MPP00151 (m2 hueco x2,10) |
| SYS010 | PA (regla) | 2% PEM medible | 201,22 | - |

**PEM 10.261,97** -> (+13% GG 1.334,06 +6% BI 615,72) base **12.211,75** -> (+21% IVA 2.564,47) **PEC 14.776,22 EUR**.
PEM medible (modelo) = 10.060,75; S&S = 2% = 201,22. Aritmetica cerrada (Sum capitulos = PEM; importe = cantidad x
precio; Sum descomposicion + indirectos = precio del n1; costes_indirectos = 0 porque el precio BCCA declarado =
suma de la descomposicion).

## Regla de oro

Un fallo NO se arregla aflojando esta golden. Si el recompute discrepa, se investiga el ENGINE/emisor, jamas el
oraculo. El presupuesto solo se re-ancla si cambia el DISENO del caso, el criterio o el banco (bump de version +
nuevo hash, decision explicita con JM). `GOL-PRE-01/02/03` INTACTAS (usan `AQ-DEMO`); este caso usa `BCCA`.
