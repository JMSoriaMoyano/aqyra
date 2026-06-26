# Dominio IFC MEP — parser, generador y validación de red (PT 4.2, Ola 4, hueco H2)

Apertura del **dominio MEP** del contrato C1: leer/validar/escribir IFC MEP y emitir el
**modelo neutro de red**. Vive en `iso19650-openbim` (capa IFC transversal del ecosistema) y
**reutiliza el núcleo transversal** (`../nucleo/ifc_utils.py` + `grafo_red.py`, espejado del
canónico en `motor-calculo-estructural`) **sin tocarlo**.

> Devuelve **topología + datos** de la red (nodos+tramos+terminales+fuentes), **no calcula**. El
> solver MEP (hidráulico Darcy/Manning, eléctrico, térmico) lo aporta la disciplina `instalaciones`.

## Módulos

| Archivo | Qué hace |
|---|---|
| `ifc_to_model_mep.py` | Parser físico→neutro de red. `IfcDistributionSystem` + `IfcFlowSegment/Fitting/Terminal/Controller/MovingDevice` + `IfcDistributionPort`/`IfcRelConnectsPorts` → modelo neutro C1 §4. Reutiliza `ifc_utils` (psets/length_scale/pset_value) y `grafo_red.construir_grafo`. |
| `generate_test_ifc_mep.py` | Banco de pruebas: red PCI (fuente → tramos → 3 BIE) con puertos y `IfcRelConnectsPorts`. |
| `validacion_red.py` | Arnés de validación: continuidad (conexo desde fuente), terminales conectados, sin huérfanas (`filtrar_componentes_desconectadas`, `es_ancla`=fuente), unidades SI. **Sin hidráulica.** |
| `test_red_mep.py` | Micro-test autocontenido (sin IFC): unión por puertos, troceo T/X, validación de red. Exit ≠ 0 si falla. |

## Modelo neutro de red (C1 §4)

```jsonc
{
  "unidades":  { "longitud":"m", "caudal":"l/s", "presion":"kPa", "potencia":"W" },
  "sistema":   { "tipo":"FIREPROTECTION", "fluido":, "nombre":, "demanda": null },
  "nodos":     { "N1": { "x":, "y":, "z":, "tipo":"fuente|union|terminal" } },
  "tramos":    { "T1": { "ni":, "nj":, "dn":, "material":, "rugosidad":, "longitud":, ... } },
  "terminales":[ { "id":"BIE-1", "tipo":, "nodo":"N3", "caudal_min":, "presion_min":, "demanda": null } ],
  "fuentes":   [ { "id":"grupo", "nodo":"N1", "presion":, "caudal":, "tipo":"equipo|controlador" } ]
}
```

Es un **modelo hermano** del estructural: mismas convenciones (bloque `unidades` SI, nomenclatura
de nudos del núcleo), claves **nuevas**, sin redefinir las existentes. Gancho **H3**: clave
`demanda` prevista por terminal/sistema (no se calcula aquí).

## Uso

```
python3 generate_test_ifc_mep.py red.ifc
python3 ifc_to_model_mep.py red.ifc modelo_neutro_mep.json
python3 validacion_red.py modelo_neutro_mep.json verificacion_red.json
python3 test_red_mep.py          # micro-test
```

## Nota de esquema

En **IFC4** el sistema PCI usa `PredefinedType=FIREPROTECTION`; en **IFC4X3** el término es
`FIRESUPPRESSION`. El parser es **agnóstico al esquema**: emite el string tal cual venga del modelo.

*Predimensionado/asistencia; a revisar y firmar por técnico competente. NDP `[confirmar AN]`.*

## Saneamiento (PT 6.2, lamina libre)

El parser reconoce los sistemas en **lamina libre** (`PredefinedType` SEWAGE/STORMWATER/
DRAINAGE/WASTEWATER): lee las **cotas de solera** (`Pset_Estructurando_Red.CotaSolera`),
mapea el **VERTIDO/outfall** (`IfcFlowTerminal` OUTLET) como **ancla** en `vertidos[]`
(`tipo:"vertido"`) y anade `habitantes_eq` a los terminales (aporte residual EN 752). El
calculo (solver de **Manning de red**) vive en `obras-lineales` (frontera C1). Generador:
`generate_test_ifc_saneamiento.py`. El parser sigue **agnostico al sistema**.

## Abastecimiento (PT 6.3, presion)

El parser reconoce los sistemas de **abastecimiento a presion** (`PredefinedType`
WATERSUPPLY/DOMESTICCOLDWATER/POTABLEWATER) y la **FUENTE = DEPOSITO**
(`IfcTank`/`IfcFlowStorageDevice`, por **jerarquia `is_a()`**) ademas del grupo de bombeo
(`IfcFlowMovingDevice`). La fuente lleva `tipo:"deposito"|"equipo"|"controlador"` y, en el
deposito, `cota_lamina`/`presion` si el Pset las trae (si no, las inyecta la demanda C4 de
`obras-lineales`). Lee `habitantes_eq` tambien aqui (consumo EN 805). El **ancla de la red
es la FUENTE** (al reves que el vertido del saneamiento). El calculo (solver **Darcy-Weisbach
de red**, copia del de `instalaciones`) vive en `obras-lineales`. Generador:
`generate_test_ifc_abastecimiento.py`; micro-test `test_red_abastecimiento.py`. El parser
sigue **agnostico al sistema**.
