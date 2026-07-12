# Golden GOL-PRE-05 - presupuesto con banco de coste REAL BCCA NATIVO (C5, eje coste)

> Caso NUEVO (patron GOL-PRE-04). Valora la MISMA medicion anclada de `GOL-PRE-01` con el pack de coste
> REAL NATIVO `banco/BCCA-nativo/v1` (unidades de obra BCCA con su CODIGO NATIVO -sin alias del criterio-,
> derivadas de la Base de Costes de la Construccion de Andalucia, CC-BY 3.0) + `criterio/AQ/v3` (corte
> NATIVO de 4 clases), modo coste. NO edita `GOL-PRE-01/02/03/04` (intactas). E5.1b es el forward nativo
> de E5.1/D51: el precio deja de ser "alias del criterio" (FAB010) y pasa a ser "la unidad de obra BCCA
> nativa" (06LPC80000), trazable a su codigo real sin capa de traduccion. Decisiones D53-D55.
> La PUERTA queda FUERA (D54): su unidad nativa BCCA (11MPP00151) es m2 de hueco y el modelo neutro
> anclado no expone el area del hueco (mide conteo + area de hoja 1,845). Registro de licencias:
> `Aqyra-Negocio/RECONCILIACION_licencias-coste.md`.

## Que ancla (patron GOL-PRE-04; el runner ANTEPONE el recompute del engine)

1. **Identidad** - md5 de las fixtures `entrada/ARQ.ifc`+`EST.ifc` (las MISMAS de `GOL-PRE-01/04`:
   `0b998513...`/`0d7e7f20...`; la medicion es identica para las 4 clases, cambian los codigos y el banco).
2. **Packs** - `criterio/AQ/v3` (anclado por su `content_sha256`; `[packs.criterio]` NO se mueve de v1) +
   `banco/BCCA-nativo/v1` (anclado en `versions.lock [packs.banco_bcca_nativo]`, clave NUEVA). La semilla
   `BCCA/v1` bajo `[packs.banco_bcca]` queda INTACTA (la ancla GOL-PRE-04).
3. **Esquema** - el presupuesto conforma `salida-presupuesto.schema.json` SIN tocarlo.
4. **RECOMPUTE** (conda `mcp-bim`, ifcopenshell; y gate CI) - `medir(fixtures, criterio/AQ/v3)` +
   `presupuestar(..., banco=banco/BCCA-nativo/v1)` reproduce ESTE expected.
5. **Coherencia interna** - importe = cantidad x precio; precio_unitario == cuadro n1 == banco; n1 == n2
   (Sum componentes + indirectos); PEM = Sum importes = Sum capitulos; GG/BI/base/IVA/PEC segun parametros;
   partidas origen=modelo subset banco (precio == banco) y subset criterio; trazabilidad subset GUIDs del
   modelo; S&S (origen=regla) = 2% del PEM medible. La PUERTA (11MPP00151) esta AUSENTE (D54).

## Oraculo del eje (calculado a mano y verificado x2; coincide con el recompute del engine)

Precios REALES del `banco/BCCA-nativo/v1` (EUR) x cantidades ancladas de `GOL-PRE-01`:

| partida (codigo BCCA nativo) | cap | cantidad | precio | importe |
|---|---|---|---|---|
| 03HRZ80000 (zapata HA-25) | C01 | 0,128 m3 | 164,18 | 21,02 |
| 05HRP80010 (pilar HA-25) | C02 | 1,92 m3 | 433,17 | 831,69 |
| 05HRL80010 (losa HA-25) | C02 | 16,20 m3 | 418,01 | 6.771,76 |
| 06LPC80000 (fabrica 1/2 pie) | C03 | 33,90 m2 | 28,94 | 981,07 |
| 10CEE00001 (enfoscado) | C04 | 67,80 m2 | 12,98 | 880,04 |
| 13IPP90016 (pintura plastica) | C04 | 67,80 m2 | 4,60 | 311,88 |
| SYS010 (S&S, regla) | C06 | PA | 2% PEM medible | 195,95 |

PEM medible (modelo) = 9.797,46; S&S = 2% = 195,95.
**PEM 9.993,41** -> (+13% GG 1.299,14 +6% BI 599,60) base **11.892,15** -> (+21% IVA 2.497,35) **PEC 14.389,50 EUR**.
Aritmetica cerrada (Sum capitulos = PEM; importe = cantidad x precio; Sum descomposicion + indirectos =
precio del n1; costes_indirectos = 0 porque el precio BCCA declarado = suma de la descomposicion).

## Regla de oro

Un fallo NO se arregla aflojando esta golden. Si el recompute discrepa, se investiga el ENGINE/emisor,
jamas el oraculo. El presupuesto solo se re-ancla si cambia el DISENO del caso, el criterio o el banco
(bump de version + nuevo hash, decision explicita con JM). `GOL-PRE-01/02/03/04` INTACTAS. La puerta y la
base BCCA completa son forward (D54/D53), no un fallo de este caso.
