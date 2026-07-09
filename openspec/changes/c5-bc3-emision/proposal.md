# Cambio · Emisión `salida-presupuesto` → FIEBDC-3/2024 (`.bc3`) + round-trip (E0.2)

> Change-id: `c5-bc3-emision` · Capacidad: `presupuesto` (contrato `C5-presupuesto`) · frontera C1/C5
> Historia del backlog: **E0.2** (`Aqyra-Negocio/BACKLOG_motor-valoracion_para-Aqyra-Raiz.md` §2·E0) · **cierra la Ola 1**
> Procedencia: handoff negocio → desarrollo (`INICIO-hilo_Aqyra-Raiz_motor-valoracion_E0.2-BC3-emision.md`, 2026-07-09)
> Estado: **PROPUESTA** · decisiones **D34–D38 ratificadas** por JM (2026-07-09).
> Tipo: **ADITIVO** sobre el adaptador de frontera de E0.1 (`engines/bc3`). NO toca esquema de contrato: la emisión **LEE** `salida-presupuesto` tal cual.
> Gobierna: **D-026 / N-04** (política de datos 3+2; no se redistribuye ninguna base pública).

## Por qué

E0.1 abrió la **ingesta** (`.bc3` → pack `banco`). E0.2 abre la **emisión**, la dirección inversa:
el presupuesto de Aqyra **sale** a FIEBDC-3/2024 (`.bc3`) para entrar en el flujo del despacho y de la
licitación pública española — Presto/Arquímedes/TCQ y la mesa de contratación. Con las dos direcciones,
«OpenBIM, sin cautividad» es real en ambos sentidos y **la Ola 1 (coste conectado) queda cerrada**.

La interoperabilidad es **traducción determinista, no cálculo**: la misma `salida-presupuesto` produce el
mismo `.bc3` salvo el **sello de fecha** del `~V` (parametrizable). La emisión no inventa precios ni
mediciones: consume la salida como el compositor C7 consume la salida para el `.docx`.

## Qué cambia (superficie)

- **`engines/bc3/`** (paquete existente `aqyra-bc3`, sube a **0.2.0**) — texto puro (stdlib, sin
  ifcopenshell → corre en CI y en el sandbox). Se AÑADE:
  - `emitir_bc3(salida, *, fecha=None, charset="utf-8", …) → str`: `salida-presupuesto` → texto `.bc3`
    (`~V/~C/~D/~M/~T`, D35/D38). Determinista salvo el sello de fecha del `~V` (D36).
  - `leer_bc3_presupuesto(origen) → {estado_mediciones}`: re-lector del round-trip (D34), reconstruye
    `estado_mediciones` (cantidad de las `~M`, precio del `~C`, `importe = cantidad × precio_unitario`,
    trazabilidad de los GUIDs). Simétrico de `emitir_bc3`; reusable por E5/importación.
  - CLI `aqyra-bc3 emitir <salida.json> [--salida .bc3] [--charset] [--fecha]`.
- **`engines/bc3/tests/test_emision.py`** — golden de **ROUND-TRIP** (la Llave 1 de E0.2): el `.bc3`
  emitido desde la `salida-presupuesto` ANCLADA de `GOL-PRE-01`, REIMPORTADO, reproduce el
  `estado_mediciones` con **identidad de importes** (±0,01) y cantidades (±0,5%, D3). Anclaje **semántico**
  (D37), NO por md5 del `.bc3` (lleva sello de fecha). + determinismo, subset, charset, desglose por objeto.
- **`engines/bc3/README.md`** — documenta la emisión y el round-trip.
- **`packages/contracts/C5-presupuesto/DECISIONES.md`** — se anclan **D34–D38** (continúan D1–D33).
- **`packages/contracts/C5-presupuesto/contrato.md`** — nota en «Frontera»: la `salida-presupuesto` puede
  emitirse a `.bc3` (`engines/bc3.emitir_bc3`); aditivo, no cambia la semántica.

## Impacto — por qué NO rompe nada

- **No toca ningún esquema de contrato** (ni entrada ni salida de C5): la emisión **LEE**
  `salida-presupuesto`. `schema_version` de C5 **no se mueve**.
- **La zona anclada no se edita.** `GOL-PRE-01/02/03`, `GOL-DOC-01`, los packs `criterio/AQ/v1`+`v2`,
  `banco/AQ-DEMO/v1` y `banco/AQ-BC3-DEMO/v1` quedan **intactos** (identidad por hash preservada). El golden
  de round-trip **consume** `GOL-PRE-01` como entrada; **no** lo re-ancla → `packages/golden` intacto.
- **`ingerir_bc3` no se toca** (E0.2 es aditivo): `emitir_bc3`/`leer_bc3_presupuesto` son nuevos.
- **Traducción determinista.** Misma salida + mismo sello → mismos bytes; el round-trip conserva los
  importes (patrón semántico, como D14/D28).

## Fuera de alcance (fronteras honestas)

- **No** se siembran bases públicas reales (BCCA/Extremadura) → **E5.1**, tras la verificación de licencia
  por JM (D-026).
- **No** se emite el banco-carbono ni `GOL-CAR-01` (Ola 2), ni el pliego como documento firmable (E4-pliego:
  el `~T` de v0 es el mínimo desde la descripción), ni el dashboard (E6).
- **No** se lee el `%CI` del propio BC3 (gancho forward, como en la ingesta).
- **Sin release** salvo que JM lo decida (si al cerrar la interop se libera `aqyra-bc3`, su tag
  `aqyra-bc3-v*` = Llave 2 de JM). El git va por `.bat` en el host; el merge/firma es de JM (Llave 2).
