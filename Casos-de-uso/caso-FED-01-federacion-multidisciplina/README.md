# caso-FED-01 — Federación multi-disciplina (Visor v0.6)

Tres IFC **co-localizados** que comparten el mismo sistema de coordenadas mundo
(WCS en 0,0,0) y la **misma georreferencia** (`IfcProjectedCRS` EPSG:25830 +
`IfcMapConversion` idéntico). Todos llevan geometría Body (`IfcExtrudedAreaSolid`)
por lo que teselan en web-ifc/fragments.

- `estructura.ifc` — edificio: 4 pilares HEB240 + 4 zapatas + 4 vigas + forjado losa.
- `mep.ifc` — instalaciones: bajante + ramales PCI + montante + conducto de clima.
- `lineal.ifc` — viario anexo: firme + bordillo + colector enterrado + 2 pozos.

El edificio ocupa X[0..6] Y[0..5]; el vial va en X negativo (paralelo), de modo
que al federar los tres modelos solapan correctamente en la misma escena.

## Reproducir
    python gen_federacion.py .            # genera los 3 .ifc
    # luego, con el pipeline del visor:
    node pipeline.mjs estructura.ifc models estructura
    node pipeline.mjs mep.ifc        models mep
    node pipeline.mjs lineal.ifc     models lineal

Validado en vivo (22/06/2026) en `visor/visor-ifc-v0.6.html`: 65 ítems, 23 con
geometría; render, alineación, panel de modelos (visibilidad/aislar/color por
modelo y disciplina), selección con identificación de disciplina+modelo.
