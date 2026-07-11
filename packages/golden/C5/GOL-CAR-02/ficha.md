# GOL-CAR-02 · Golden de valoracion CARBONO con banco REAL — E5.2 (Ola 2)

> Caso **NUEVO** (patron `GOL-CAR-01`), modo `carbono`. Valora la MISMA medicion de `GOL-PRE-01` en el
> **eje carbono** con el pack `banco-carbono/generico/v2` (**REAL**, factores DERIVADOS de fuentes con
> licencia ABIERTA ratificadas: ADEME Licence Ouverte 2.0, ProBas dl-de/by-2.0, UK GHG OGL v3.0). NO edita
> `GOL-CAR-01` (sintetico v1) ni `GOL-PRE-01/02/03`/`GOL-DOC-01` (intactas). El carbono es **traduccion
> determinista, no calculo**: cada kgCO2e sale del factor del banco-carbono anclado, pero **DERIVABLE y
> TRAZABLE** a su fuente abierta (banco.json>provenance). Convencion banco+criterio, no verdad fisica.
> Decisiones D45-D48. Registro de licencias: `Aqyra-Negocio/RECONCILIACION_licencias-carbono.md`.

## Que ancla (D48 — patron D14/D28/D44, sin md5 de salida)

1. **Identidad** — md5 de las fixtures `entrada/ARQ.ifc`+`EST.ifc` (las de `GOL-CAR-01`/`GOL-PRE-03`,
   `19a272a5...`/`f1d25192...`).
2. **Packs** — `criterio/AQ/v2` (mide igual que v1) + `banco-carbono/generico/v2` (`content_sha256` +
   `md5_banco` anclados en `test_packs.py` y `versions.lock [packs.banco_carbono]=v2`). `[packs.criterio]`
   sigue en v1; `banco-carbono/generico/v1` INTACTO (lo ancla `GOL-CAR-01`).
3. **Esquema** — el presupuesto de carbono **conforma `salida-presupuesto.schema.json` SIN tocarlo**.
4. **RECOMPUTE** (conda `mcp-bim`, ifcopenshell) — `medir(fixtures, criterio/AQ/v2)` +
   `presupuestar(..., banco=banco-carbono/generico/v2, eje="carbono")`.
5. **SEMANTICA carbono** — por partida `origen=modelo`: `valores.carbono` con `unitario x cantidad = total`,
   `unidad=kgCO2e`, `banco=banco-carbono/generico/v2`, `etapas` A1A3/A4A5 y **Sum etapas = total** (D18). S&S
   (`origen=regla`): etiquetado, sin etapas. Resumen del eje == Sum totales.
6. **DETERMINISMO + INVARIANTE** — `proyectar(..., "carbono", corte)` 2x = misma salida; los grupos del corte
   == la vista de coste homologa (el corte no depende del eje); `Sum proyeccion == PEM del eje`.

## Oraculo del eje (calculado a mano y verificado x2)

Factores del `banco-carbono/generico/v2` (kgCO2e/ud, A1A3 + A4A5) x cantidades ancladas de `GOL-PRE-01`:

| partida | cantidad | factor | total kgCO2e | A1A3 | A4A5 |
|---|---|---|---|---|---|
| CSZ010 | 0,128 m3 | 268,64 | 34,39 | 33,04 | 1,35 |
| EHS010 | 1,92 m3 | 362,87 | 696,71 | 675,65 | 21,06 |
| EHL010 | 16,20 m3 | 306,33 | 4 962,55 | 4 789,04 | 173,51 |
| FAB010 | 33,90 m2 | 26,30 | 891,57 | 872,25 | 19,32 |
| REV010 | 67,80 m2 | 5,33 | 361,37 | 352,56 | 8,81 |
| PIN010 | 67,80 m2 | 0,45 | 30,51 | 30,51 | 0,00 |
| PPM010 | 1 ud | 1,03 | 1,03 | 0,92 | 0,11 |
| SYS010 | PA (regla) | — | 139,56 | (sin etapas) | |

**PEM del eje = 7 117,69 kgCO2e** (Sum modelo 6 978,13 + S&S 2% 139,56). Proyeccion espacial: Nivel 00
731,10 · Planta Baja 2 938,66 · Nivel 01 3 308,37 · (sin geometria) 139,56 · **Sum = 7 117,69** (invariante).

Factores DERIVADOS (banco.json>provenance): hormigon 0,088 (ADEME 20719) · acero reciclado 0,938 (ADEME 26730)
· ladrillo 0,20 (ProBas2 f472c5b1) · cemento 0,866 (ADEME 20723) -> mortero 0,173 · pintura 1,51 (ADEME 24255,
proxy) · madera 0,0367 (ADEME 20721, neto biogenico; PPM010 a refinar en v3/epd) · transporte A4 0,086 kgCO2e/
t.km x 50 km (UK GHG, OGL).

## Como se genera / verifica (dos llaves)

- **Sandbox (texto puro):** `pytest packages/packs/tests/test_packs.py` (golden de pack v2 + v1 intacto) +
  conformidad de esquema del pack.
- **Local (conda `mcp-bim`, ifcopenshell):** `run_golden` de `C5` -> `GOL-CAR-02` verde y `GOL-CAR-01` +
  `GOL-PRE-01/02/03` + `GOL-DOC-01` byte-identicas/intactas.
- **Llave 1:** gate verde en CI. **Llave 2:** merge/firma de JM. **Sin release** (salvo decision de JM).

*Regla de oro: un fallo se corrige en el engine, jamas aflojando el check. El oraculo del carbono es
consistencia + no-regresion + invariante + TRAZABILIDAD a fuente abierta, no verdad fisica.*
