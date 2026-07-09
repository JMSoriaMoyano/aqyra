# Diseño · Emisión `salida-presupuesto` → FIEBDC-3/2024 (`.bc3`) + round-trip (E0.2)

> Cómo se materializa y **qué ratificó JM (D34–D38)**. Regla sagrada heredada (C1/C3/C4/C5): la
> interoperabilidad es **traducción determinista**, no cálculo; la emisión LEE `salida-presupuesto`
> tal cual (forward-open, patrón consumidor de C7). Verificable ÍNTEGRAMENTE en el sandbox (texto puro,
> sin ifcopenshell).

## 1 · Modelo mental — la dirección inversa de E0.1

E0.1 tradujo `~C/~D` (un banco) → `banco.json`. E0.2 traduce una `salida-presupuesto` (un presupuesto
medido) → `~V/~C/~D/~M/~T`. La novedad frente a la ingesta es el **`~M` (mediciones)**, que la ingesta
dejó fuera de v0 precisamente porque pertenece a un presupuesto, no a un banco:

```
salida-presupuesto (JSON de C5)                    presupuesto.bc3 (FIEBDC-3/2024)
  estado_mediciones[].{codigo,unidad,descripcion,precio_unitario} ─▶ ~C partida (tipo 0)
  cuadro_precios_2[].componentes[]                 ─▶ ~C hijo (tipo 1/2/3) + ~D (hijo\factor\rend)
  estado_mediciones[].{cantidad, traza_cantidades} ─▶ ~M (líneas de medición, por objeto o total)
  estado_mediciones[].descripcion                  ─▶ ~T (pliego mínimo, D38)
                                                        ~V (cabecera + charset + sello de fecha, D36)
```

Cierre del bucle (`leer_bc3_presupuesto`): `~C/~D/~M` → `estado_mediciones` (cantidad de las `~M`,
precio del `~C`, `importe = cantidad × precio_unitario`). La identidad de importes es el oráculo.

## 2 · Decisión D34 · API y re-lector — `emitir_bc3` + `leer_bc3_presupuesto` en `aqyra_bc3`

**Ratificado (JM).** La API vive en el paquete existente `engines/bc3` (D30), aditiva:
- `emitir_bc3(salida, *, fecha=None, charset="utf-8", programa="AQYRA", autor="Aqyra", titulo=None) → str`
  — devuelve el texto `.bc3` canónico (simétrico de `serializar_banco`, que devuelve `str`); el CLI lo
  escribe con el `charset`.
- `leer_bc3_presupuesto(origen) → {"estado_mediciones": [...]}` — el re-lector del round-trip vive **en el
  paquete** (no en el test): es una capacidad reutilizable (la lectura de un presupuesto `.bc3` con `~M` la
  reusan E5/importación futura) y da simetría a la frontera. **Rechazada por JM (menor recorrido):** que el
  re-lector sea una función privada del test.

## 3 · Decisión D35 · Subset EMITIDO v0 y líneas de `~M` — desglose por objeto

Subset emitido: **`~V`** (cabecera + charset + sello de fecha), **`~C`** (partidas `tipo 0` + componentes
del cuadro nº2 con su naturaleza `1/2/3`; el hijo se codifica `⟨codigo⟩.⟨n⟩`, determinista), **`~D`**
(descomposiciones: `hijo\factor(=1)\rendimiento`, de modo que `precio_hijo × 1 × rendimiento = subtotal`),
**`~M`** y **`~T`** (§D38).

**Líneas de `~M` (ratificado JM):** **desglose por objeto** desde `traza_cantidades` — una línea de
medición por objeto con su cantidad y el **GUID en el comentario** (preserva la trazabilidad, la joya); y
**línea única** con la cantidad total cuando la partida no tiene `traza_cantidades` (p. ej. `origen=regla`
como S&S, o las partidas de `GOL-PRE-01`, que llevan `trazabilidad` pero no `traza_cantidades`). El total
del `~M` = Σ de las líneas. **Rechazada por JM:** una sola línea con la cantidad total siempre (pierde el
desglose por objeto/GUID). Formato de la línea de detalle: grupos de 5 subcampos
`comentario(GUID)\N\longitud\latitud\altura`, con la medición = `N` (dims vacías).

## 4 · Decisión D36 · Codificación de salida y sello de fecha

- **Charset de salida = UTF-8 por defecto** (FIEBDC-3/2024 lo admite; sin pérdida de acentos), el `~V`
  declara `UTF-8`. **Parametrizable a ANSI/cp1252** (`--charset cp1252` → token `ANSI`) para destinos
  legacy que lo exijan. **Rechazada por JM:** ANSI por defecto.
- **Sello de fecha del `~V` = parámetro `fecha` (AAAAMMDD)**, por defecto una **constante determinista
  documentada** (`_FECHA_DEFAULT`), **nunca** `date.today()` (rompería la reproducibilidad y no existe en
  el sandbox). Es el **único no-determinismo** del emisor: la misma salida + el mismo `fecha` → los mismos
  bytes. El sello también sella la fecha de precio de cada `~C` (comportamiento FIEBDC); toda diferencia
  entre dos emisiones se explica por sustitución del sello (comprobado en el golden).

## 5 · Decisión D37 · Anclaje del golden de round-trip — identidad de importes (semántico)

El golden vive como **pytest en `engines/bc3/tests/test_emision.py`** (texto puro → CI + sandbox) que
**consume** la `salida-presupuesto` ANCLADA de `GOL-PRE-01` (`expected.json → presupuesto`; se LEE, no se
recalcula — D4). Ancla **SEMÁNTICA**, NO `md5` del `.bc3` (lleva sello de fecha): el `.bc3` emitido,
REIMPORTADO por `leer_bc3_presupuesto`, reproduce cada `importe` (**±0,01**) y `cantidad` (**±0,5%**, D3) del
`estado_mediciones`, y la Σ de importes casa con el **PEM 7 022,53**. Patrón semántico heredado (D14/D28).
`packages/golden` **no se toca** (GOL-PRE-01 se consume, no se re-ancla). **Rechazada:** anclar por md5 del
`.bc3` (el sello de fecha lo haría inestable).

## 6 · Decisión D38 · Pliego `~T` en v0 — mínimo desde la descripción

**Ratificado (JM).** Se emite un `~T` por partida con **su descripción** como pliego mínimo. La
`salida-presupuesto` v0 no porta un pliego estructurado; el `~T` mínimo deja el `.bc3` más completo para el
receptor y es el **gancho** natural para **E4-pliego** (cuando el pliego real entre en la salida o se
resuelva del banco/criterio, el `~T` se enriquece). El re-lector **ignora** el `~T` para los importes (no
afecta al round-trip). **Rechazada por JM:** no emitir `~T` en v0.

## 7 · Verificación (dos llaves)

- **Sandbox (texto puro):** TODO el golden de E0.2 corre en el sandbox junto al de E0.1 (`pytest
  engines/bc3` = **16 passed**: 8 ingesta + 8 emisión). Round-trip verificado contra `GOL-PRE-01`
  (importes exactos, PEM 7 022,53).
- **Llave 1:** gate verde en CI (`engines/bc3` ya está en el `pytest` de `ci.yml` desde E0.1; el nuevo
  `test_emision.py` corre solo). `GOL-PRE-01/02/03`, `GOL-DOC-01` y todos los packs anclados **intactos**.
- **Llave 2:** merge/firma de JM. **Sin release** (salvo decisión de JM al cerrar la interop).

## 8 · Qué cierra / desbloquea

- **Cierra la Ola 1** (coste conectado: E0.1 + E0.2 + E1.1 + E1.2 + E2.1 + E2.2).
- **E5.1** — semilla de coste real (BCCA/Extremadura) por el MISMO adaptador (ingesta), tras licencia (D-026).
- **E4-pliego** — el `~T` mínimo es el gancho para el pliego firmable.
