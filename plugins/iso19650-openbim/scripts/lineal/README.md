# Dominio IFC 4.3 obra lineal — parser, generador y validación de alineación (PT 5.1, Ola 5)

Apertura del **dominio georreferenciado** del contrato C1 (§4bis): leer/validar/escribir IFC 4.3
de **alineación** y emitir el **modelo neutro lineal**. Vive en `iso19650-openbim` (capa IFC
transversal del ecosistema), junto al dominio MEP (`../mep/`), y **reutiliza el núcleo transversal**
(`../nucleo/ifc_utils.py`, espejado del canónico en `motor-calculo-estructural`) **sin tocarlo**.

> **Frontera de dominio (crítica).** La alineación es **referenciación lineal por PK** (curva
> paramétrica 1D), **no** un grafo de red: por eso este dominio **no** usa `grafo_red` (eso es para
> drenaje/obras hidráulicas, Ola 6). Devuelve **geometría paramétrica + georreferencia**, **no
> calcula** trazado (3.1-IC) ni firmes (6.1-IC): eso lo aporta la disciplina `obras-lineales` (PT 5.2+).

## Módulos

| Archivo | Qué hace |
|---|---|
| `ifc_to_model_lineal.py` | Parser físico→neutro lineal. `IfcAlignment` → `IsNestedBy` → `IfcAlignmentHorizontal/Vertical/Cant` → `IfcAlignmentSegment.DesignParameters` (`IfcAlignment{Horizontal,Vertical,Cant}Segment`) + georref (`IfcMapConversion`/`IfcProjectedCRS`) → modelo neutro C1 §4bis. Reutiliza `ifc_utils` (psets/length_scale). |
| `generate_test_ifc_lineal.py` | Banco de pruebas: eje de carretera recta→clotoide→curva→clotoide→recta + 2 acuerdos verticales + peralte, georreferenciado (EPSG:25830). Esquema **IFC4X3**, unidad SI de longitud explícita. |
| `validacion_alineacion.py` | Arnés de validación: PK monótono/contiguo, **continuidad + tangencia** (integrando cada segmento), continuidad de cotas/pendientes en alzado, georref presente, unidades SI; radios/A de clotoide frente a 3.1-IC (informativo). **Sin cálculo de trazado.** |
| `export_gis.py` | Export de la **planta** a **GeoJSON** (`LineString`) en el CRS proyectado (decisión nº3: GeoJSON + IFC 4.3). Densifica integrando cada segmento. |
| `test_lineal.py` | Micro-test e2e: genera→parsea→valida (positivo) + 3 casos negativos (salto, PK no contiguo, sin georref). Exit ≠ 0 si falla. |

## Modelo neutro lineal (C1 §4bis)

```jsonc
{
  "unidades":   { "longitud":"m", "angulo":"rad", "pendiente":"m/m" },
  "georref":    { "epsg":, "map_projection":, "origen_e":, "origen_n":, "altura":,
                  "rotacion_rad":, "escala":, "datum_vertical": },
  "alineacion": {
    "planta":  [ { "pk_ini":, "tipo":"LINE|CIRCULARARC|CLOTHOID", "longitud":,
                   "x_ini":, "y_ini":, "acimut_ini_rad":, "radio_ini":, "radio_fin":, "A_clotoide": } ],
    "alzado":  [ { "pk_ini":, "tipo":"CONSTANTGRADIENT|PARABOLICARC|CIRCULARARC",
                   "longitud_h":, "cota_ini":, "pendiente_ini":, "pendiente_fin":, "kv": } ],
    "peralte": [ { "pk_ini":, "tipo":, "peralte_ini_pct":, "peralte_fin_pct":, "cant_ini_m":, "cant_fin_m": } ]
  },
  "pk_inicio":, "pk_fin":, "longitud_total":,
  "secciones_tipo": null, "firme": null, "terreno": null   // ganchos a obras-lineales (PT 5.2+)
}
```

Es un **modelo hermano** del estructural y del de red: mismas convenciones (bloque `unidades` SI),
claves **nuevas**, sin redefinir las existentes. El radio sigue el convenio IFC (0 = recta = radio
infinito → `null` en el neutro; signo + = giro a izquierda).

## Uso

```
PYTHONPATH=/tmp/pylibs python3 generate_test_ifc_lineal.py eje.ifc
PYTHONPATH=/tmp/pylibs python3 ifc_to_model_lineal.py eje.ifc modelo_neutro_lineal.json
python3 validacion_alineacion.py modelo_neutro_lineal.json verificacion_alineacion.json
python3 export_gis.py modelo_neutro_lineal.json eje.geojson
PYTHONPATH=/tmp/pylibs python3 test_lineal.py          # micro-test
```

## Nota de esquema

`IfcAlignment` y su jerarquía son propias de **IFC 4.3 (IFC4X3)**. El banco declara la unidad de
longitud SI explícita (`unit.add_si_unit` LENGTHUNIT sin prefijo): `unit.assign_unit` por defecto
pone milímetros, que el parser respetaría literalmente (lección del caso MEP-01).

*Predimensionado/asistencia; a revisar y firmar por técnico competente (Ingeniero de Caminos). NDP `[confirmar AN]`.*
