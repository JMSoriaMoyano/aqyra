# engines/ifc — implementación de C1 (corte mínimo importado)

Productor del contrato **C1**: compilador (`alto.json` → IFC4X3 con huecos, catálogo abierto,
doble clasificación y alineaciones) y, más adelante, parsers por dominio y write-back. El resto
del motor **nunca** conoce IFC.

**Fase I · hilo 1 — engine importado.** El corte mínimo C1 (compile narración→IFC) se importó
**byte a byte** del canónico `iso19650-openbim 0.10.0` (`_import/aqyra-motor`), con identidad
anclada en `versions.lock [engines.ifc]` y vigilada por `tests/test_identidad_ifc.py` (hash fijo)
y `tests/test_espejo_ifc.py` (vs procedencia). La costura del runner de la golden C1 quedó
**cerrada**: `packages/golden` ya no recomputa desde el IFC congelado, sino que **compila**
`caso.alto.json` con este engine (`compile_c1.py`) y cuenta sobre ese IFC, contra el **mismo**
`expected.json`. La golden `C1-APERTURA-01` sigue **VERDE** con el compile real.

## Layout

- `compile_c1.py` — API pública del engine en el monorepo (`compilar_alto_a_ifc`).
- `narracion-ifc/` — compilador canónico (verbatim): `compilar_spec`, `spec_to_ifc`,
  `clasificacion`, `catalogo_ifc` (+`catalogo-ifc4x3.json`), `alineaciones_ifc`, `validar`,
  `spec.schema.json`.
- `scripts/lineal/generate_test_ifc_lineal.py` — geometría de alineación (`construir_alineacion`),
  verbatim.
- `tests/` — guardianes de identidad y de espejo.
- `ESPEJO_plan-retirada.md` — guardián + plan de retirada de las copias aguas arriba.

Regla de oro: la zona firmada `_import/` **no se reescribe**; el engine se **copia**, no se mueve.
Ver `../../../Aqyra-Raiz/FUNDACION_C1_y_modelo-neutro.md`.
