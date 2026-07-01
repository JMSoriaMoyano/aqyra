# caso-LIN-03-firmes — selección de sección de firme 6.1-IC

Caso e2e de la disciplina **`obras-lineales`** (PT 5.2, Ola 5), vertical **firmes**.
Sobre el mismo eje (`caso-LIN-01`), a partir de la **acción del tráfico** y la
**explanada**, selecciona la sección del **catálogo de la Norma 6.1-IC** y **rellena el
gancho `firme`** del modelo neutro lineal (que el PT 5.1 dejaba en `None`).

## Cadena de extremo a extremo

```
modelo_neutro_lineal.json
   -> obras-lineales/scripts/firmes/run_all_firme.py  --imd 8000 --pct 12 --calzada-unica --ev2 150
   -> bases (categoría tráfico + explanada) -> catálogo 6.1-IC (sección)
   -> RELLENA  firme + secciones_tipo  ->  modelo_neutro_lineal_firme.json
   -> write-back Pset al IFC (iso19650-openbim:ifc-create) -> eje-resultado.ifc
   -> export GIS de la planta verificada -> eje-verificado.geojson
```

```bash
python3 obras-lineales/scripts/firmes/run_all_firme.py \
        modelo_neutro_lineal.json . --imd 8000 --pct 12 --calzada-unica --ev2 150
```

## Resultado

- Tráfico: IMD 8000 veh/día, 12 % pesados, calzada única → **IMDp ≈ 480** veh.
  pesados/día/carril de proyecto → categoría **T2**.
- Explanada: **Ev2 = 150 MPa** → categoría **E2**.
- Sección del catálogo 6.1-IC: **221** (firme flexible) → **MB 18 cm + ZA 30 cm**
  (espesor total 48 cm). Combinación T2 × E2 permitida; MB ≥ mínimo (18 cm). **CUMPLE**.
- **Gancho `firme` relleno** en `modelo_neutro_lineal_firme.json` (más `secciones_tipo`
  básica). `terreno` queda en `None` (corresponde a drenaje/movimiento de tierras, Ola 6).

## Extras (no bloqueantes)

- **Write-back al IFC** (`eje-resultado.ifc`): `Pset_Estructurando_ResultadoLineal` en el
  `IfcAlignment` con 9 propiedades (trazado + firme). Re-parseado y revalidado **CUMPLE**
  (continuidad 0,0001 m, georref intacta) — la enriquecimiento no rompe el modelo.
  Mapping en `mapping_resultado_lineal.json`.
- **GIS** (`eje-verificado.geojson`): planta densificada (81 vértices) en EPSG:25830.

## Notas

- La **lectura del IFC** es de `iso19650-openbim`; aquí vive la **acción del tráfico (CN-3)**
  y la **selección de catálogo (6.1-IC)**. El **dato del IFC prevalece** sobre los valores
  por defecto. Catálogo, no dimensionado por fatiga.
- Predimensionado/asistencia; NDP **[confirmar AN]** (umbrales de categoría, espesores del
  catálogo, formación de explanada). Revisar y firmar por técnico competente (ICCP).
