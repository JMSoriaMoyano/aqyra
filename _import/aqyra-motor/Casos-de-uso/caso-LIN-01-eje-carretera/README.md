# Caso LIN-01 — Eje de carretera (IFC 4.3 → modelo neutro lineal → validación)

Primer caso del **dominio georreferenciado de obra lineal** (PT 5.1, Ola 5). Estrena la vía
**IFC 4.3 Alignment + GIS** del contrato C1 (§4bis), análogo a lo que `caso-MEP-01-red-pci` hizo
con el dominio MEP. **No calcula trazado ni firmes** (eso es la disciplina `obras-lineales`,
PT 5.2+): solo lee, reconstruye el perfil por PK, valida coherencia geométrica/georreferencia y
exporta a GIS.

## Geometría del eje (banco de pruebas)

| | Tramo | Tipo | Longitud | Parámetro |
|---|---|---|---|---|
| **Planta** | S1 | LINE | 100 m | recta |
| | S2 | CLOTHOID | 60 m | R: ∞→300, A=134,16 |
| | S3 | CIRCULARARC | 80 m | R=300 m (izq.) |
| | S4 | CLOTHOID | 60 m | R: 300→∞, A=134,16 |
| | S5 | LINE | 100 m | recta |
| **Alzado** | V1 | CONSTANTGRADIENT | 150 m | i=+2,0 %, cota 100,000 |
| | V2 | PARABOLICARC | 100 m | +2,0 %→−3,0 %, Kv=2000 |
| | V3 | CONSTANTGRADIENT | 150 m | i=−3,0 % |
| **Peralte** | 5 segmentos | bombeo 0→+7 % en clotoides, 7 % en curva | | LINEARTRANSITION/CONSTANTCANT |

**Longitud total 400 m (PK 0+000 → 0+400).** Georreferencia: `IfcProjectedCRS` EPSG:25830
(ETRS89 / UTM 30N) + `IfcMapConversion` (origen E=337.000 N=4.610.000 H=700, sin rotación, escala 1,0).

## Flujo e2e

```
PYTHONPATH=/tmp/pylibs python3 scripts/lineal/generate_test_ifc_lineal.py eje-carretera.ifc
PYTHONPATH=/tmp/pylibs python3 scripts/lineal/ifc_to_model_lineal.py eje-carretera.ifc modelo_neutro_lineal.json
python3 scripts/lineal/validacion_alineacion.py modelo_neutro_lineal.json verificacion_alineacion.json
python3 scripts/lineal/export_gis.py modelo_neutro_lineal.json eje-carretera.geojson
```

## Resultado

**VEREDICTO: CUMPLE.** Continuidad máxima 0,0001 m, tangencia máxima 0,0 rad (umbrales 0,05 m /
1·10⁻³ rad); cotas y pendientes encadenan; georreferencia presente y consistente; unidades SI.
A/R de clotoide dentro de 3.1-IC (informativo). Exportación GIS: `eje-carretera.geojson`
(LineString, 81 vértices, EPSG:25830).

## Ficheros

- `eje-carretera.ifc` — IFC 4.3 (IFC4X3) del eje georreferenciado.
- `modelo_neutro_lineal.json` — modelo neutro lineal emitido por el parser (C1 §4bis).
- `verificacion_alineacion.json` — informe de validación (CUMPLE).
- `eje-carretera.geojson` — planta en el CRS proyectado (puente a GIS/hidrología, Ola 6).
- `memoria-lineal.md` — memoria mínima del caso.

*Predimensionado/asistencia; a revisar y firmar por técnico competente (Ingeniero de Caminos).*
