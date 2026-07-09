# engines/bc3 — adaptador FIEBDC-3/2024 (.bc3) ↔ Aqyra

Capacidad de **frontera** (C1/C5): interoperabilidad con el formato del despacho y de la
licitación pública española, **FIEBDC-3/2024** (`.bc3`). «OpenBIM, sin cautividad»: un banco real
(o del cliente) entra como pack anclado, y el presupuesto de Aqyra sale a Presto/Arquímedes/TCQ.

Traducción **determinista** (no cálculo): el mismo `.bc3` produce el mismo `banco.json` byte a byte, y
la misma `salida-presupuesto` produce el mismo `.bc3` (salvo el sello de fecha del `~V`).

## Direcciones

- **E0.1 · ingesta**: `ingerir_bc3(path) → banco.json` — materializa un pack `banco/<id>/vN` con el
  **mismo esquema** que `data/packs/banco/AQ-DEMO/v1`.
- **E0.2 · emisión**: `emitir_bc3(salida) → .bc3` — exporta la `salida-presupuesto` (C5) a
  FIEBDC-3/2024 (`~V/~C/~D/~M/~T`), y `leer_bc3_presupuesto(origen) → {estado_mediciones}` la re-lee
  (round-trip). Con E0.2 cierra la Ola 1: el presupuesto **entra y sale** del formato del despacho.

## Emisión y round-trip (E0.2 · D34–D38)

- `emitir_bc3(salida, *, fecha=None, charset="utf-8", …)` — subset emitido `~V/~C/~D/~M/~T`. Las
  **mediciones `~M`** se desglosan **por objeto** desde `traza_cantidades` (el GUID en el comentario), o
  una línea única con la cantidad total cuando no hay traza (p. ej. `origen=regla`). Salida en **UTF-8**
  por defecto (parametrizable a ANSI/cp1252). El **sello de fecha** del `~V` es el único no-determinismo
  (parámetro `fecha`, valor por defecto determinista — nunca `date.today()`). El `~T` es un pliego mínimo
  (la descripción de la partida; gancho E4-pliego).
- `leer_bc3_presupuesto(origen)` — reconstruye `estado_mediciones` (cantidad de las `~M`, precio del
  `~C`, `importe = cantidad × precio_unitario`, trazabilidad de GUIDs). NO recalcula el precio.
- **Golden de round-trip** (`tests/test_emision.py`): consume la `salida-presupuesto` ANCLADA de
  `GOL-PRE-01`, emite → re-lee → **identidad de importes** (±0,01) + cantidades (±0,5%), PEM 7 022,53.
  Ancla **semántica**, NO `md5` del `.bc3` (lleva sello de fecha). Texto puro → corre en CI y sandbox.

## Subset FIEBDC-3 v0 (D31)

`~V` (cabecera + juego de caracteres) · `~C` (conceptos: código/unidad/resumen→descripción/precio/
tipo→naturaleza MO·maquinaria·material) · `~D` (descomposiciones → componentes con rendimiento y
subtotal) · `~T` (texto de pliego: se parsea; **no** se emite al banco v0 — gancho forward E4/E0.2).
`~M` (mediciones) es de E0.2. Codificación: se detecta del `~V` (ANSI/cp1252 por defecto, 850/437,
UTF-8, ISO-8859-1) y se normaliza a **UTF-8**; separador de campo `|`, subcampo `\`, decimal `.`.

## Precio y costes indirectos (D32)

`subtotal = precio_hijo × factor × rendimiento` (Decimal, HALF_UP, 2 decimales);
`precio_partida = Σ subtotales + costes_indirectos` con `costes_indirectos_pct` v0 = 3% (parámetro;
gancho forward para leerlo de los coeficientes del BC3). **Guarda de consistencia**: el precio
compuesto debe casar (±0,01) con el precio declarado en el `~C`; si no, aviso auditable
(`_avisos_ingesta`), nunca se silencia.

## CLI

```
aqyra-bc3 ingerir data/packs/banco/AQ-BC3-DEMO/v1/fuente/muestra.bc3 --banco AQ-BC3-DEMO/v1
aqyra-bc3 emitir  packages/golden/C5/GOL-PRE-01/expected.json --salida presupuesto.bc3 [--charset cp1252] [--fecha 20260709]
```

## Golden y dos llaves

- Golden del **parser** (`tests/test_bc3.py`): `ingerir_bc3(fuente/muestra.bc3)` **reproduce** el
  `banco.json` anclado (determinismo + transcodificación + guarda). Texto puro → corre en CI.
- Golden **de pack** (`packages/packs/tests/test_packs.py`): identidad del pack por `content_sha256`
  + `md5(banco.json)` + `md5(muestra.bc3)`.
- El `.bc3` de muestra es **PROPIO/sintético** (D-026): no deriva de ninguna base pública ni
  licenciada. **Llave 1** = gate verde; **Llave 2** = firma/merge de JM. v0 **SIN release**.
