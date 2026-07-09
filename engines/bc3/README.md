# engines/bc3 — adaptador FIEBDC-3/2024 (.bc3) ↔ Aqyra

Capacidad de **frontera** (C1/C5): interoperabilidad con el formato del despacho y de la
licitación pública española, **FIEBDC-3/2024** (`.bc3`). «OpenBIM, sin cautividad»: un banco real
(o del cliente) entra como pack anclado, y el presupuesto de Aqyra sale a Presto/Arquímedes/TCQ.

Traducción **determinista** (no cálculo): el mismo `.bc3` produce el mismo `banco.json` byte a byte.

## Direcciones

- **E0.1 · ingesta** (v0, este paquete): `ingerir_bc3(path) → banco.json` — materializa un pack
  `banco/<id>/vN` con el **mismo esquema** que `data/packs/banco/AQ-DEMO/v1`.
- **E0.2 · emisión** (siguiente change del hilo): `emitir_bc3(salida) → .bc3` — exporta el
  `salida-presupuesto` (C5) a FIEBDC-3 (mediciones + cuadros + textos), con golden de round-trip.

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
```

## Golden y dos llaves

- Golden del **parser** (`tests/test_bc3.py`): `ingerir_bc3(fuente/muestra.bc3)` **reproduce** el
  `banco.json` anclado (determinismo + transcodificación + guarda). Texto puro → corre en CI.
- Golden **de pack** (`packages/packs/tests/test_packs.py`): identidad del pack por `content_sha256`
  + `md5(banco.json)` + `md5(muestra.bc3)`.
- El `.bc3` de muestra es **PROPIO/sintético** (D-026): no deriva de ninguna base pública ni
  licenciada. **Llave 1** = gate verde; **Llave 2** = firma/merge de JM. v0 **SIN release**.
