# caso-LIN-05-saneamiento — red de colectores residuales (lámina libre, Manning de red)

**PT 6.2 (Ola 6).** Primer caso de extremo a extremo del **solver de Manning de red**
de `obras-lineales` v0.3.0, sobre el **dominio IFC MEP de saneamiento** de
`iso19650-openbim` v0.6.0. Es la primera vez que la disciplina de obra lineal **cruza la
frontera de red** (usa el grafo del núcleo; decisión nº7 "grafo + N solvers").

Todo es **predimensionado/asistencia**: revisar y firmar por técnico competente
(Ingeniero de Caminos). NDP marcados `[confirmar AN]`.

## El caso

Red **separativa de aguas residuales** de una urbanización: tres acometidas de sector
que convergen, por gravedad, a un **vertido** (outfall). Las **cotas de solera** de los
nudos gobiernan la pendiente.

```
  ACO-1 (P1, 2600 hab-eq) --COL-1 Ø315--\
                                          POZO-P3 --COL-3 Ø400--\
  ACO-2 (P2, 2600 hab-eq) --COL-2 Ø315--/                        VERTIDO (outfall)
  ACO-3 (P4, 1700 hab-eq) --------------COL-4 Ø315--------------/
```

| Nudo | Cota de solera (m) | Tipo |
|---|---|---|
| P1, P2 | 100,50 | acometida |
| P4 | 100,20 | acometida |
| P3 | 100,00 | pozo (unión) |
| V | 99,50 | **vertido (ancla)** |

## Flujo (IFC → cálculo → IFC)

1. **Generar IFC MEP** de saneamiento — `iso19650-openbim:scripts/mep/generate_test_ifc_saneamiento.py`
   → `red_saneamiento.ifc` (`IfcDistributionSystem` PredefinedType **SEWAGE**;
   acometidas `IfcFlowTerminal` con `Pset_Estructurando_Red.CotaSolera`/`HabitantesEq`;
   pozo `IfcDistributionChamberElement`; **vertido** `IfcFlowTerminal` PredefinedType
   **OUTLET**; colectores `IfcFlowSegment`).
2. **Parsear → modelo neutro de red** — `iso19650-openbim:scripts/mep/ifc_to_model_mep.py`
   → `modelo_red.json` (5 nodos con `cota_solera`; el OUTLET se emite en `vertidos[]`
   `tipo:"vertido"`; 3 acometidas con `habitantes_eq`).
3. **Validar topología** — `validacion_red.py` → `validacion_red_topologia.json`
   (**CUMPLE**: continuidad 100 % hacia el vertido).
4. **Calcular** — `obras-lineales:scripts/red/run_all_obras_hidraulicas.py`:
   demanda de aguas residuales (EN 752) → **solver de Manning de red** (árbol desde el
   vertido) → verificación → `resultado_red.json`, `verificacion_red_calculo.json`,
   `modelo_red_resuelto.json` (gancho `red`), `mapping_resultado_red.json`.
5. **Write-back** — `iso19650-openbim:ifc-create:escribir_psets_resultado.py`
   → `red_saneamiento_resultado.ifc` (5 elementos enriquecidos con
   `Pset_Estructurando_ResultadoRed`). Re-parseado y re-validado **CUMPLE** (round-trip).

## Demanda de aguas residuales (EN 752) `[confirmar AN]`

Dotación 200 l/hab/día · coef. de retorno 0,80 · coef. de punta 2,5
→ 0,00463 l/s por habitante-eq.

| Acometida | hab-eq | Caudal punta (l/s) |
|---|---|---|
| ACO-1 | 2600 | 12,04 |
| ACO-2 | 2600 | 12,04 |
| ACO-3 | 1700 | 7,87 |
| **Total vertido** | | **31,94** |

## Resultado del solver (Manning, lámina libre)

| Colector | DN (mm) | Q (l/s) | J (m/m) | calado y (m) | llenado | v (m/s) | régimen |
|---|---|---|---|---|---|---|---|
| COL-1 | 315 | 12,04 | 0,0071 | 0,077 | 24,4 % | 0,82 | supercrítico |
| COL-2 | 315 | 12,04 | 0,0071 | 0,077 | 24,4 % | 0,82 | supercrítico |
| COL-3 | 400 | 24,07 | 0,0100 | 0,092 | 23,0 % | 1,11 | supercrítico |
| COL-4 | 315 | 7,87 | 0,0130 | 0,053 | 17,0 % | 0,90 | supercrítico |

**Continuidad:** COL-3 = COL-1 + COL-2 = 24,07 l/s; el vertido recoge 31,94 l/s
(residuo nodal 0,0 %).

## Veredicto: **CUMPLE**

Todos los colectores: **grado de llenado ≤ 24,4 %** (< 0,75 NDP), **velocidad
0,82–1,11 m/s** (en banda autolimpieza 0,6 ↔ no erosión 5,0 m/s NDP), **pendiente > 0**
(desagüe por gravedad) y **DN ≥ 300 mm**.

## Archivos

| Archivo | Contenido |
|---|---|
| `red_saneamiento.ifc` | IFC MEP de saneamiento de entrada (SEWAGE) |
| `modelo_red.json` | modelo neutro de red (parser MEP) |
| `validacion_red_topologia.json` | validación de continuidad hacia el vertido |
| `resultado_red.json` | resultado del solver de Manning por tramo |
| `verificacion_red_calculo.json` | verificación (balance nodal + comprobaciones) |
| `modelo_red_resuelto.json` | modelo con el gancho `red` (resumen) |
| `mapping_resultado_red.json` | mapping del write-back (`Pset_Estructurando_ResultadoRed`) |
| `red_saneamiento_resultado.ifc` | IFC enriquecido con los resultados (round-trip CUMPLE) |
| `memoria-saneamiento.md` | memoria de cálculo |

> El **abastecimiento a presión** (EN 805, Darcy/Hardy-Cross) es del **PT 6.3** y cierra
> la Ola 6; no forma parte de este caso.
