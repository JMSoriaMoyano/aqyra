# GOL-CAR-01 · Golden de valoracion CARBONO — E3.3 (Ola 2)

> Caso **NUEVO** (patron `GOL-PRE-03`), modo `carbono`. Valora la MISMA medicion de `GOL-PRE-01` en el
> **eje carbono** con el pack `banco-carbono/generico/v1` (PROPIO/sintetico, D-026). NO edita
> `GOL-PRE-01`/`GOL-PRE-02`/`GOL-PRE-03`/`GOL-DOC-01` (intactas). El carbono es **traduccion determinista,
> no calculo**: el kgCO2e sale del factor del banco-carbono anclado (convencion banco+criterio, no verdad
> fisica, estatuto del PEM). Decisiones D39-D44.

## Que ancla (D44 — patron D14/D28, sin md5 de salida)

1. **Identidad** — md5 de las fixtures **aumentadas** `entrada/ARQ.ifc`+`EST.ifc` (las de `GOL-PRE-03`,
   `19a272a5…`/`f1d25192…`; reusadas por D44). Las de `GOL-PRE-01` (`0b998513…`/`0d7e7f20…`) intactas.
2. **Packs** — `criterio/AQ/v2` (`content_sha256 079c28e9…`, mide igual que v1) + `banco-carbono/generico/v1`
   (`content_sha256 44d0cd3f…` + `md5_banco 47fb4787…`). `[packs.criterio]` sigue en v1; el banco-carbono
   se ancla por su fila `[packs.banco_carbono]`.
3. **Esquema** — el presupuesto de carbono **conforma `salida-presupuesto.schema.json` SIN tocarlo**
   (`valores.carbono` + `etapas` ya caben, E1.1/D16-D18).
4. **RECOMPUTE** (conda `mcp-bim`, ifcopenshell) — `medir(fixtures, criterio/AQ/v2)` +
   `presupuestar(..., banco=banco-carbono/generico/v1, eje="carbono")`.
5. **SEMANTICA carbono** — por partida `origen=modelo`: `valores.carbono` con `unitario × cantidad = total`,
   `unidad=kgCO2e`, `banco=banco-carbono/generico/v1`, `etapas` A1A3/A4A5 y **Σ etapas = total** (D18). S&S
   (`origen=regla`): etiquetado, sin etapas. Resumen del eje == Σ totales.
6. **DETERMINISMO + INVARIANTE** — `proyectar(..., "carbono", corte)` 2× = misma salida; los grupos del
   corte == la vista de coste homologa (el corte no depende del eje); `Σ proyeccion == PEM del eje`.

## Oraculo del eje (calculado a mano y verificado x2)

Factores del `banco-carbono/generico/v1` (kgCO2e/ud, A1A3 + A4A5) x cantidades ancladas de `GOL-PRE-01`:

| partida | cantidad | factor | total kgCO2e | A1A3 | A4A5 |
|---|---|---|---|---|---|
| CSZ010 | 0,128 m3 | 245,0 | 31,36 | 29,82 | 1,54 |
| EHS010 | 1,92 m3 | 312,5 | 600,00 | 574,08 | 25,92 |
| EHL010 | 16,20 m3 | 300,0 | 4 860,00 | 4 655,88 | 204,12 |
| FAB010 | 33,90 m2 | 46,3 | 1 569,57 | 1 427,19 | 142,38 |
| REV010 | 67,80 m2 | 8,75 | 593,25 | 535,62 | 57,63 |
| PIN010 | 67,80 m2 | 2,4 | 162,72 | 145,77 | 16,95 |
| PPM010 | 1 ud | 58,0 | 58,00 | 54,00 | 4,00 |
| SYS010 | PA (regla) | — | 157,50 | (sin etapas) | |

**PEM del eje = 8 032,40 kgCO2e** (Σ modelo 7 874,90 + S&S 2% 157,50). Proyeccion espacial: Nivel 00
631,36 · Planta Baja 4 003,54 · Nivel 01 3 240,00 · (sin geometria) 157,50 · **Σ = 8 032,40** (invariante).

## Como se genera / verifica (dos llaves)

- **Local (conda `mcp-bim`):** `pytest engines/presupuesto` (incl. `test_carbono.py`, texto puro) +
  `run_golden` de `C5` → `GOL-CAR-01` verde y `GOL-PRE-01/02/03` + `GOL-DOC-01` byte-identicas.
- **Llave 1:** gate verde en CI. **Llave 2:** merge/firma de JM. **Sin release** (salvo decision de JM).

*Regla de oro: un fallo se corrige en el engine (`presupuesto.py`), jamas aflojando el check. El oraculo
del carbono es consistencia + no-regresion + invariante, no verdad fisica.*
