# Diseño · Semilla REAL de coste por la vía limpia (E5.1)

> El **cómo**. Decisiones **D49–D52 a ratificar por JM** (continúan D1–D48); se anclarán en
> `packages/contracts/C5-presupuesto/DECISIONES.md`. La IA propone; JM firma. El esquema de spec
> **no cambia** (delta NULO): E5.1 sólo añade un pack de datos + su golden. Espejo de E0.1 (`c5-bc3-ingesta`)
> y E5.2 (`c5-banco-carbono-abierto`).

## 0 · Principio rector

Un motor, un adaptador — y ahora, **dato de coste real y trazable**. E5.1 no añade una línea de motor ni de
adaptador: reemplaza el precio **sintético** del banco de demostración por un precio **derivado** de una base
pública abierta (BCCA). La regla dura: cada precio es convención banco+criterio (estatuto del PEM), **pero no
se inventa** — se deriva de dato abierto real y se documenta su cadena (código BCCA → descomposición →
precio, con su edición/licencia).

## 1 · Qué YA existe (no se rehace)

- **Motor:** `presupuestar(modelo, criterio, banco, parametros)` consume cualquier `banco` con la forma de
  `AQ-DEMO` (D1–D5); `engines/presupuesto` 0.5.0. Un banco nuevo se consume sin tocar el motor.
- **Adaptador:** `engines/bc3.ingerir_bc3(path, *, banco, titulo=None, costes_indirectos_pct="0.03") → dict`
  (0.2.0, D30–D33): lee FIEBDC-3/2024 (`~V/~C/~D/~T`, subset v0), decodifica ANSI→UTF-8, compone
  `precio = Σ subtotales + CI` (Decimal, guarda ±0,01 vs el `~C`). Determinista y texto puro (corre en el
  sandbox). E5.1 lo **usa tal cual**.
- **Forma del pack de coste** (`banco/AQ-DEMO/v1`, `banco/AQ-BC3-DEMO/v1`): por partida
  `{codigo, unidad, descripcion, clasificacion_uniclass, componentes[].{tipo,descripcion,unidad,rendimiento,precio,subtotal}, costes_indirectos, precio}` + cabecera `{banco, titulo, moneda, costes_indirectos_pct}`.
  El pack real **imita esta forma exacta**.
- **Loader + anclaje:** `aqyra_packs` (familia `banco` ya en `FAMILIAS`), `content_sha256` = sha256 del bloque
  `contenido` del `pack.json`; `md5_banco` = md5 de `banco.json`; golden de pack en `test_packs.py`; fila
  `[packs.banco_*]` en `versions.lock`. Doble golden (pack + parser) = patrón `AQ-BC3-DEMO` (D33).
- **Criterio (las 7 partidas y su mapeo):** `criterio/AQ` mapea `IfcWall`→`FAB010`(m²)+`REV010`(m²)+`PIN010`(m²),
  `IfcSlab`→`EHL010`(m³), `IfcColumn`→`EHS010`(m³), `IfcFooting`→`CSZ010`(m³), `IfcDoor`→`PPM010`(ud),
  sin geometría `SYS010` (S&S). **El criterio se reutiliza sin tocar** (el mapeo objeto→partida no cambia entre
  ejes ni entre bancos — tesis del motor multi-eje).
- **Runner:** `run_case_c5` (modo coste). `GOL-PRE-04` reusa este runner (banco_ref → BCCA) sin código nuevo.

## 2 · D49 · Fuente abierta ratificada + atribución (registro)

**Propuesta a ratificación de JM (2026-07-11)** — registro en `Aqyra-Negocio/RECONCILIACION_licencias-coste.md`:

- **BCCA (Junta de Andalucía)** — **CC-BY 3.0** (vía aviso legal del portal; la ficha de la BCCA no fija
  restricción propia y hereda el régimen general). Las 4 preguntas: uso comercial ✅, redistribución en
  producto ✅, obra derivada ✅, atribución = **«Información obtenida del Portal de la Junta de Andalucía»**
  (arrastrada a la obra derivada, sin logotipos/escudos, sin desnaturalizar). **PRIMARIA**.
- **Extremadura (GOBEX)** — licencia **por confirmar**; **SECUNDARIA/contraste, NO anclar sin confirmar**
  (estatuto USLCI del carbono).

**Atribución a arrastrar** (en `provenance`/`fuente` del pack y, cuando proceda, en la salida): «Información
obtenida del Portal de la Junta de Andalucía — BCCA ene-2024 — CC-BY 3.0» + el código BCCA de origen de cada
partida + su edición/URI.

> **Caveat de ratificación:** el aviso legal general del portal habla de «contenidos/textos»; que el dataset
> BC3 caiga sin matices bajo ese CC-BY 3.0 general lo **ratifica JM**. Si JM prefiere confirmación escrita de
> la Consejería, es un paso legal aparte que no bloquea el diseño del pack.

## 3 · D50 · id/version del pack real y `versions.lock` (a ratificar)

`AQ-DEMO/v1` y `AQ-BC3-DEMO/v1` son **INTOCABLES** (los anclan `GOL-PRE-01/02/03` + golden de pack). El pack
real es **NUEVO**.

| Opción | id/version | versions.lock | Nota |
|---|---|---|---|
| **A (recomendada)** | `banco/BCCA/v1` | fila NUEVA `[packs.banco_bcca]` (espejo de `[packs.banco_bc3]`) | banco «adoptable» real con su propia fila; `[packs.banco]=AQ-DEMO/v1` y `[packs.banco_bc3]` intactos. Pointer de producción de coste real = esta fila |
| **B** | `banco/AQ-DEMO/v2` | `[packs.banco]` pasa a `v2` | numeración limpia (v1 demo → v2 real, patrón `criterio` y `banco-carbono`), pero mezcla el banco propio con el derivado de un tercero (BCCA) bajo el mismo id `AQ-DEMO` — menos honesto en la provenance |

**Recomendación: A** — la fuente es un tercero (BCCA), no el despacho; merece su **propio id** (`BCCA`) y su
**propia fila** en el lock, igual que `AQ-BC3-DEMO` tuvo `[packs.banco_bc3]`. Deja los demo intactos por hash y
el pointer de coste real explícito. (El motor elige el banco por `banco_ref` del caso, no por el pointer del
lock, así que añadir la fila no rompe ninguna golden anclada.)

## 4 · D51 · Alcance de la ingesta y encaje con el criterio (a ratificar) — el corazón de E5.1

El problema real: el **criterio** mapea clases IFC → **códigos de partida propios** (`FAB010…PPM010`); la base
**BCCA** trae ≈6.600 precios con **códigos nativos BCCA** distintos. Para que la **muestra presupuestable**
corra con el criterio existente hay que resolver ese encaje.

| Opción | Qué se ancla en v0 | Encaje con el criterio | Fidelidad al dato |
|---|---|---|---|
| **A (recomendada)** | las **7 partidas del criterio** (`FAB010…PPM010`), cada una con el **precio y descomposición REALES de la partida BCCA equivalente**, materializadas por `ingerir_bc3` de un **`.bc3` semilla** (subconjunto de 7 unidades, recodificadas a los 7 códigos del criterio) + `provenance` con el **código BCCA de origen** | `criterio/AQ` **sin tocar**; la muestra usa el modelo de `GOL-PRE-01` | Alta: precio/descomposición reales de BCCA; el código del criterio es un **alias** documentado en `provenance` (derivación por Aqyra, vía limpia — igual que el carbono derivó factores) |
| **B** | la **base BCCA completa** con códigos NATIVOS | exige `criterio/AQ/v3` que mapee clases IFC → códigos BCCA nativos (toca el criterio → su propia golden) | Máxima, pero abre superficie (criterio nuevo + golden) — **gancho forward**, no v0 |

**Recomendación: A** — mantiene el criterio intacto, el delta de spec NULO y el patrón de la vía limpia
(dato real, derivación documentada). El `.bc3` semilla es **provenance auditable** (como `fuente/muestra.bc3`
de `AQ-BC3-DEMO`): se ingiere de forma determinista y el `provenance` de cada partida enlaza al código BCCA de
origen y su descomposición real. La **base completa con criterio nativo** queda como forward hook explícito.

Cada partida lleva un bloque **`provenance`** (aditivo; el motor sólo lee `codigo/unidad/componentes/precio`,
así que `provenance` es documentación inerte para el engine):

```jsonc
"provenance": {
  "fuente": "BCCA — Base de Costes de la Construcción de Andalucía (Junta de Andalucía), ene-2024",
  "licencia": "CC-BY 3.0",
  "atribucion": "Información obtenida del Portal de la Junta de Andalucía",
  "codigo_bcca": "<código nativo BCCA de la unidad de obra equivalente>",
  "unidad": "m2",
  "ref": "<edición/URI del dato>",
  "nota": "Precio y descomposición reales de la partida BCCA; recodificada al código del criterio (FAB010) por Aqyra (vía limpia) para reutilizar criterio/AQ sin tocarlo."
}
```

> Los **valores numéricos concretos** (precios/descomposiciones BCCA por partida) se fijan en `opsx:apply`,
> consultando la BCCA ratificada partida a partida; este diseño fija el **método y la estructura**, no los
> números.

## 5 · D52 · Golden (a ratificar)

| Opción | Qué ancla | Recompute |
|---|---|---|
| **A (recomendada)** | golden de pack (identidad de contenido: `content_sha256` + md5(banco.json) + md5(.bc3)) **+** `GOL-PRE-04` = valora la medición de `GOL-PRE-01` con el pack REAL BCCA por `run_case_c5` (modo coste); oráculo del **PEM real** a mano ×2 (determinismo + no-regresión + invariante, patrón `GOL-CAR-02`) | `GOL-PRE-04` pasa por `medir()` → **recompute en el conda `mcp-bim` de JM** (ifcopenshell), NO en el sandbox |
| **B** | sólo golden de pack (identidad de contenido) + golden del parser (`ingerir_bc3` reproduce `banco.json`) | todo en el sandbox (texto puro) |

**Recomendación: A** — cierra el eje coste real con una golden que **usa** el pack BCCA end-to-end (no sólo su
hash), igual que `GOL-CAR-02` cerró el carbono real. `GOL-PRE-01/02/03` quedan **intactas** (usan `AQ-DEMO`).
Nuevo oráculo (PEM BCCA) calculado a mano y verificado ×2 en el apply. El golden del parser + golden de pack
corren en el sandbox; sólo `GOL-PRE-04` necesita el conda local.

## 6 · Versionado y no-regresión

- **Sin bump de engine ni de adaptador** (no se tocan). `versions.lock [packs.banco_bcca]` según D50.
- **Sin release** (Llave 2 del coste real espera decisión de JM).
- El golden de pack (hash/md5), el golden del parser (`ingerir_bc3`) y la aritmética de la descomposición se
  unit-testean en el **sandbox** (texto puro). Si D52 = A, el recompute de `GOL-PRE-04` (pasa por
  `medir()`/ifcopenshell) corre en el conda `mcp-bim` local de JM antes del PR — como `GOL-PRE-03`/`GOL-CAR-02`.
  `GOL-PRE-01/02/03`, `GOL-CAR-01/02`, `GOL-DOC-01`, `GOL-PLI-01` byte-idénticas/intactas.
