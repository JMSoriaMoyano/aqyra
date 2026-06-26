# Compilador narración → IFC → Visor (Ruta 1)

Genera geometría IFC describiéndola con palabras, sin autoría manual de IFC.

```
 narración (prosa)
      │   skill  narracion-a-spec   (capa SEMÁNTICA: la pone el agente)
      ▼
 <m>.alto.json          spec de alto nivel (macros narración-friendly)
      │   compilar_spec.py          (capa DETERMINISTA: macros + validación)
      ▼
 <m>.spec.json          spec canónico (coordenadas explícitas)
      │   spec_to_ifc.py            (IfcOpenShell, geometría real SweptSolid)
      ▼
 <m>.ifc  ──►  ../visor/pipeline.mjs  ──►  .frag + props.json  ──►  Visor IFC
```

## Piezas
- `SKILL.md` — skill `narracion-a-spec`: cómo mapear prosa → spec de alto nivel.
- `compilar_spec.py` — expansor determinista de macros + validación (esquema + geometría).
- `spec.schema.json` — contrato JSON Schema del spec canónico.
- `spec_to_ifc.py` — generador IFC4 (geometría real).

## Macros del alto nivel
- `niveles: { plantas, altura, base }` → N niveles a cotas base+i·altura (i=0 → Planta Baja).
- `edificios: [ { ancho, largo, luz_max?, seccion_pilar?, espesor_muro?, espesor_forjado?,
  material?, pilares?, muros_perimetrales?, forjados? } ]` → con `luz_max` retícula de
  pilares (incluye interiores); sin él, 4 esquinas. Muros perimetrales + forjados por defecto.
- `reticulas_pilares: [ { nx, ny, sep_x, sep_y, origen, seccion?, material? } ]`.
- `pilares`/`muros`/`losas` canónicos explícitos → pasan tal cual.

Defaults: sección 0,40×0,40 · muro 0,25 · forjado 0,30 · material HA-30. Unidades: metros.

## Ejecutar
```bash
PYTHONPATH=/tmp/pylibs python3 compilar_spec.py  <m>.alto.json  <m>.spec.json
PYTHONPATH=/tmp/pylibs python3 spec_to_ifc.py    <m>.spec.json  <m>.ifc
node ../visor/pipeline.mjs <m>.ifc ../visor/models <m>
# registrar <m> en ../visor/models/manifest.json (herramientas de archivo, no bash)
```

## Ejemplos validados de extremo a extremo
- `edificio-demo`     — 8×5 m, 2 plantas (spec canónico directo). 7 productos, 0 fallos.
- `edificio-oficinas` — narración "18×12, 3 plantas de 3,2 m, pilares HA-30 cada 6 m,
  muros 25 cm, forjados 30 cm" → alto nivel → 24 pilares + 8 muros + 2 forjados.
  34 productos teselan, 0 fallos, BBox 18×12×6,4 m. Cargado en el Visor (`load: true`).

## Próximos pasos
1. Más macros/primitivas: vigas y jácenas, huecos en muro, zapatas bajo pilar, cubierta inclinada.
2. Clasificación/Psets por defecto reusando `bsdd-clasificacion` (Uniclass + GuBIMClass).
3. Validación automática con `ifc-validate` dentro del pipeline.
4. Empaquetar como skill del plugin (hoy es prototipo en carpeta de proyecto).
5. Capa 2: edición paramétrica en vivo en el Visor sobre lo colocado.
