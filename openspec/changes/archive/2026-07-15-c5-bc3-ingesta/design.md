# Diseño · Ingesta FIEBDC-3/2024 (`.bc3`) → pack `banco` (E0.1)

> Cómo se materializa y **qué ratificó JM (D30–D33)**. Regla sagrada heredada (C1/C3/C4/C5): la
> interoperabilidad es **traducción determinista**, no cálculo; se reutiliza el esquema de banco tal
> cual (forward-open). El `.bc3` de muestra es PROPIO/sintético (D-026). Verificable ÍNTEGRAMENTE en el
> sandbox (texto puro, sin ifcopenshell).

## 1 · Modelo mental — el mismo esquema de banco, otra fuente

`AQ-DEMO/v1` es un banco escrito a mano; `AQ-BC3-DEMO/v1` es **el mismo esquema** materializado por
**ingesta** de un `.bc3`. Cambiar de fuente = cambiar de pack, no de engine. El adaptador es un
traductor `FIEBDC-3 → banco.json`:

```
muestra.bc3 (ANSI/cp1252)                         banco.json (UTF-8, esquema AQ-DEMO)
  ~V cabecera + juego de caracteres      ─▶  moneda, titulo
  ~C conceptos (codigo/unidad/resumen/precio/tipo) ─▶  partidas[].{codigo,unidad,descripcion} + naturaleza
  ~D descomposiciones (hijo\factor\rend) ─▶  partidas[].componentes[].{tipo,descripcion,unidad,rendimiento,precio,subtotal}
  ~T texto de pliego                     ─▶  (parseado; NO emitido al banco v0 — gancho forward)
                                              costes_indirectos + precio (Σsub + CI, D32)
```

## 2 · Decisión D30 · Casa y API — `engines/bc3` releaseable (mayor recorrido futuro)

**Ratificado (JM, «las de mayor recorrido futuro»).** El adaptador vive en `engines/bc3/` como
**paquete uv `aqyra-bc3`** (espejo estructural de `engines/presupuesto`, D6): `pyproject.toml`
(hatchling, sin dependencias — stdlib pura) + `src/aqyra_bc3/` + `tests/` + miembro de
`[tool.uv.workspace]`. Es el hogar cohesivo para las **dos** direcciones de la frontera:

- `ingerir_bc3(path, *, banco, titulo=None, costes_indirectos_pct="0.03") → dict` (E0.1, este change).
- `emitir_bc3(salida) → .bc3` (E0.2, gancho forward — siguiente change del hilo).

Releaseable (tag `aqyra-bc3-v*` = Llave 2 de JM) cuando la interoperabilidad cierre; **v0 SIN release**
(como `presupuesto` 0.3/0.4). Texto puro → **corre en CI y en el sandbox** (no necesita ifcopenshell,
a diferencia de `engines/presupuesto`).

**Alternativas descartadas por JM (menor recorrido):** `packages/packs` (módulo `aqyra_packs.bc3` — más
mínimo pero mezcla la ingesta con el cargador y no da hogar releaseable a la emisión); `tools/bc3` CLI
(exento de la guardia SDD y **fuera** del pytest de CI → el golden no correría en la Llave 1).

## 3 · Decisión D31 · Subset FIEBDC-3 v0 — `~V/~C/~D/~T`

- **`~V`** — cabecera y **juego de caracteres**. FIEBDC-3 suele venir en **ANSI (Windows-1252)**; el
  parser lee el token del `~V` (`ANSI`→cp1252 por defecto, `850`/`437`, `UTF-8`, `ISO-8859-1`),
  decodifica y **normaliza a UTF-8** en el pack. Separadores: campo `|`, subcampo `\`, decimal `.`.
- **`~C`** — conceptos: `codigo`, `unidad`, `resumen`→`descripcion`, `precio`, `tipo`. El campo `tipo`
  mapea la **naturaleza** del componente: `1`→`mano_obra`, `2`→`maquinaria`, `3`→`material`,
  `0`/vacío→partida (la que lleva `~D`).
- **`~D`** — descomposiciones: por cada partida, tripletes `hijo \ factor \ rendimiento` → `componentes`
  (con `rendimiento = factor × rendimiento` efectivo y `subtotal`).
- **`~T`** — texto de pliego: **se parsea** pero **no se emite** al banco v0 (el esquema de banco no lo
  lleva; gancho forward para E4-pliego y E0.2). No se añade clave nueva al banco (forward-open).
- **`~M`** (mediciones) — **fuera de v0**: pertenece a un presupuesto/obra, no a un banco de precios; es
  del flujo de E0.2 (emisión/round-trip). Se ignora si aparece.

## 4 · Decisión D32 · Precio de partida y costes indirectos

- `subtotal = precio_hijo × factor × rendimiento` (**Decimal**, `ROUND_HALF_UP`, 2 decimales — dinero
  sin float).
- `costes_indirectos = Σ subtotales × costes_indirectos_pct`; `precio = Σ subtotales + costes_indirectos`.
- `costes_indirectos_pct` **v0 = 3%** (parámetro; **gancho forward** para leerlo de los coeficientes del
  propio BC3, que varían entre emisores — se difiere para no abrir superficie de parser en v0).
- **Guarda de consistencia:** el precio compuesto debe casar (**±0,01**) con el precio declarado en el
  `~C`; si no, se registra un aviso auditable (`_avisos_ingesta`) — **no se silencia** (espíritu de D7,
  la guarda de huecos). La muestra es consistente → sin avisos.

**Alternativas descartadas (por JM):** tomar el precio del `~C` literal y dejar el CI como residuo
(rompe la homogeneidad de `costes_indirectos_pct` global del banco); leer el `%CI` del BC3 ya en v0
(superficie heterogénea, mejor gancho forward).

## 5 · Decisión D33 · Anclaje del pack de muestra

- Pack **`banco/AQ-BC3-DEMO/v1`** bajo su propia ruta, con `fuente/muestra.bc3` como **provenance**
  auditable (el `.bc3` PROPIO/sintético que lo produce, D-026).
- Sección NUEVA **`[packs.banco_bc3]`** en `versions.lock` (espejo de `[packs.banco]`); el golden de pack
  verifica `version_anclada(LOCK,'banco_bc3') == v1`. `[packs.banco]=AQ-DEMO/v1` **intacto**.
- **Doble golden** (dos costuras que impiden el drift):
  1. Golden **de pack** (`packages/packs/tests/test_packs.py`): `content_sha256` del bloque `contenido`
     + `md5(banco.json)` + `md5(muestra.bc3)` (patrón `banco/AQ-DEMO`/`criterio/AQ/v2`).
  2. Golden **del parser** (`engines/bc3/tests/test_bc3.py`): `ingerir_bc3(fuente/muestra.bc3)` reproduce
     el `banco.json` anclado byte a byte (determinismo del adaptador). Un fallo se corrige en el
     **código**, jamás editando el banco anclado.

**Alternativa descartada (por JM):** anclar solo por el golden de pack sin fila en `versions.lock` (como
`criterio/AQ/v2`) — menos recorrido: un banco «adoptable» encaja mejor con su fila propia.

## 6 · Verificación (dos llaves)

- **Sandbox (texto puro):** TODO el golden de E0.1 corre en el sandbox (parser + golden de pack), sin
  ifcopenshell. Anclas verificadas: `md5(banco.json)`, `md5(muestra.bc3)`, `content_sha256`.
- **Local (conda `mcp-bim`):** solo si se quiere el bucle de golden COMPLETO junto a los otros contratos;
  E0.1 no lo necesita (no toca ifcopenshell).
- **Llave 1:** gate verde en CI (`pytest packages/packs engines/bc3` verde; `GOL-PRE-01/02/03`,
  `GOL-DOC-01`, packs anclados **intactos**). **Llave 2:** merge/firma de JM. **Sin release.**

## 7 · Qué desbloquea

- **E0.2** — emisión `salida-presupuesto` → `.bc3` (mismo paquete `engines/bc3`), con golden de
  round-trip por identidad de importes (D3: importes ±0,01; cantidades ±0,5%).
- **E5.1** — semilla de coste real (BCCA/Extremadura) por el MISMO adaptador, tras la verificación de
  licencia por JM (D-026).
