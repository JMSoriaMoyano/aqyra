# Diseño · La proyección (E2.2)

> Cómo se materializa `proyectar` y **qué ratificó JM (D24–D29)**. Regla sagrada heredada
> (C1/C3/C4/C5): añadir claves, nunca cambiar semántica. Un fallo se corrige en el código, jamás
> aflojando una golden. **La proyección es consulta, no cálculo** (N-06): `proyectar` AGRUPA lo que ya
> existe; el reparto 50/50 lo resolvió el parser en E2.1.

## 1 · El modelo mental

El valor vive por **PARTIDA** (`estado_mediciones[]`, agregado de varios objetos vía
`trazabilidad:[guids]`), pero el corte vive por **OBJETO** (`modelo.objetos[].cortes[corte]`). La
proyección reparte el valor de cada partida entre los grupos del corte, pasando por los objetos que la
constituyen. Dos saltos:

```
partida  ──(D26: por magnitud EXACTA)──▶  objeto  ──(D20/D21: fraccion de E2.1)──▶  grupo
 valor_P        share_O = q_O / Σq_O            valor_O               valor_O × fraccion
```

`Σ grupos == Σ partidas` por construcción: `Σ_O share_O = 1` (reparto completo del valor de la partida)
y `Σ fraccion = 1` por eje atribuido (invariante D20). Lo no atribuible cae en **residuales** (D27) para
que el invariante sea EXACTO.

## 2 · D24 · Firma de `proyectar` — recibe el presupuesto **y el modelo**

```python
proyectar(presupuesto: dict, modelo: dict, eje: str, corte: str) -> list[dict]
# -> [ { "grupo", "valor_total", "unidad", "n_partidas", "guids": [...], "fuente" }, ... ]
```

- Recibe **el modelo además del presupuesto**: los `cortes` viven por objeto (E2.1), no en la partida;
  hay que leerlos del modelo. El presupuesto aporta el valor por partida y `traza_cantidades` (D26).
- `corte ∈ {espacial, funcional, uniclass, gubim}`. `eje` = string libre (D17): `coste` o un eje de
  `valores{}`.
- Salida: una fila por grupo, ordenada por **primera aparición** (determinista). `fuente` del grupo =
  la `fuente` de las pertenencias que lo alimentan (`ifc` / `criterio`); si un grupo recibe de ambas,
  gana `criterio` (traza honesta de que hubo *fallback*). `n_partidas` = nº de partidas que aportan al
  grupo; `guids` = objetos que aportan (orden de aparición, sin duplicar).

## 3 · D25 · Cómo se lee el eje

- `eje == "coste"`: el valor de la partida es **`importe`** (canónico, D16); la `unidad` de salida es la
  `moneda` del `resumen` (EUR).
- `eje != "coste"`: el valor es **`valores[eje].total`**; la `unidad` es `valores[eje].unidad`. Una
  partida sin `valores[eje]` en ese run aporta **0** (forward-open; nunca error).
- La `unidad` de salida es **homogénea** dentro de una proyección (todo EUR, o todo kgCO₂e…): el valor
  proyectado es dinero o magnitud del eje, no la unidad de medición (m²/m³) de la partida.

## 4 · D26 · Atribución partida→objeto — **por magnitud EXACTA** (ratificada por JM)

El reparto del valor de una partida entre sus objetos es **proporcional a la magnitud realmente medida
de cada objeto** en esa partida. Como el precio unitario es **uniforme dentro de la partida**, el
reparto de la cantidad es el reparto del valor para **cualquier** eje (coste o no-coste):

```
share_O = cantidad_O / Σ_O cantidad_O        # cantidad_O = contribución del objeto O a la partida
valor_O = valor_partida × share_O
```

- **El engine emite `traza_cantidades`.** El motor ya computa `cantidad_O` por objeto en su bucle
  `obj × pdef → leer-cantidad`; lo publica aditivamente por partida: `traza_cantidades:[{guid, cantidad}]`
  (sólo `origen=modelo`). `proyectar` la lee → **no re-mide** (sigue siendo group-by puro). Un objeto
  aporta a varias partidas con cantidades distintas (muro → fábrica m², enfoscado m²×2caras, pintura
  m²×2caras): cada partida guarda la contribución a ELLA.
- **Por qué EXACTA y no proxy.** El proxy (peso = cantidad del modelo que casa la unidad) coincide con la
  exacta cuando el factor de caras es uniforme en la partida (el caso del criterio v1/v2), pero divergiría
  si dos objetos de una misma partida tuvieran distinto factor/tratamiento de huecos. La exacta lo blinda
  y es honesta con «no recálculo» (lee lo que el motor ya calculó). Coste: una clave aditiva (bump 0.4.0).
- **Degeneración.** Si `Σ cantidad_O == 0` en una partida (no debería), se degrada a equitativa `1/n`
  sobre su `trazabilidad` (evita div/0, conserva Σ).

## 5 · D27 · Conservación de Σ — residuales deterministas

Para que `Σ proyección == Σ estado_mediciones` sea **EXACTO** (salvo redondeo declarado), nada se pierde:

- **Partida sin `trazabilidad`** (`origen=regla`, p. ej. S&S `SYS010` al 2 %): su valor entero va al grupo
  **`"(sin geometría)"`**, `fuente = "regla"`. No tiene objetos → no tiene corte.
- **Objeto sin el eje de corte pedido** (o GUID ausente del modelo): su parte va al grupo
  **`"(sin clasificar)"`**, `fuente = "—"`.

Los residuales son grupos como cualquier otro en la salida (auditables). El invariante los incluye.

## 6 · D28 · Anclaje de `GOL-PRE-03` — DETERMINISMO + SEMÁNTICA + INVARIANTE (patrón D14)

El sandbox no corre ifcopenshell → **no** se pre-calcula un md5 de salida. `_run_c5_proyeccion` ancla así
(patrón `GOL-PRE-02`/D14, sin md5 hardcodeado):

1. **Identidad** por md5 de las fixtures aumentadas (anclado en `entradas_md5`).
2. **DETERMINISMO**: `proyectar` 2× sobre la misma entrada → **misma salida** (list igual).
3. **INVARIANTE**: para cada `(eje, corte)` de las vistas, `Σ valor_total == Σ estado_mediciones[eje]`
   (±`importe_abs`).
4. **SEMÁNTICA**: las CINCO vistas del `expected` casan con la proyección recomputada —
   (i) por planta (`espacial`), (ii) por `IfcFacilityPart` 4.3 (`espacial`), (iii) por `IfcSystem`
   (`funcional`), (iv) por `IfcZone` con **atribución fraccionaria** 50/50 (`funcional`; Σ por zonas ==
   total), (v) *fallback* criterio (`funcional`, `fuente=criterio`) — grupos, `valor_total`, `fuente`.

Un fallo se investiga en el ENGINE (`proyeccion.py`/`presupuesto.py`), jamás aflojando el check.

## 7 · D29 · Fixtures aumentadas + `criterio/AQ/v2`

- **Fixtures.** `gen_fixtures.py` (conda `mcp-bim`) lee `GOL-PRE-01/entrada/ARQ.ifc`+`EST.ifc` y les
  **inyecta**, de forma determinista: un **árbol 4.3** (`IfcFacility`/`IfcFacilityPart` sobre el árbol
  existente), `IfcSpace`+`IfcRelSpaceBoundary` (para el 50/50 de un tabique entre dos zonas), `IfcZone`
  (2 zonas) e `IfcSystem` (p. ej. clima). Escribe `GOL-PRE-03/entrada/ARQ.ifc`+`EST.ifc` con **md5
  propios**; las ancladas de `GOL-PRE-01` (`0b998513…`/`0d7e7f20…`) quedan **intactas** (mismo precedente
  que la inyección de `Qto`, D_modelo).
- **Criterio.** `GOL-PRE-03` usa `criterio/AQ/v2` (v1 + `reglas_sistema`, D22) para la vista *fallback*
  (objetos sin `IfcSystem`/`IfcZone` → `funcional` por criterio). `criterio/AQ/v1` intacto; `GOL-PRE-01`
  sigue en v1. La rama `proyeccion` ancla v2 por su `content_sha256` (`079c28e9…`, golden de pack de E2.1),
  no por `[packs.criterio]` (que sigue en v1).
- **Golden.** `GOL-PRE-03` es un **caso NUEVO** (patrón `GOL-PRE-02`), nunca editando `GOL-PRE-01`.

## 8 · Verificación (dos llaves)

- **Sandbox (path puro):** `proyectar` sobre un presupuesto + modelo **sintéticos** (sin IFC) — invariante
  Σ, reparto por magnitud EXACTA, residuales, determinismo. `test_proyeccion.py`.
- **Local (conda `mcp-bim`):** `gen_fixtures.py` genera las fixtures aumentadas (ifcopenshell); el
  oráculo funcional de `GOL-PRE-03` se computa de esas fixtures y `_run_c5_proyeccion` cierra la costura.
- **Llave 1:** gate verde en CI (`GOL-PRE-01/02`/`GOL-DOC-01` byte-idénticas; `GOL-PRE-03` verde; tests
  del engine verdes). **Llave 2:** merge/firma de JM. **Sin release.**

## 9 · Qué desbloquea

- **E0.1/E0.2** (ingesta/emisión BC3) — siguientes changes del hilo, cierran la Ola 1.
- **E6** (dashboard, Ola 4): la vista `proyectar(eje, corte)` como producto; la `fuente` viaja para
  mostrar si el corte nace del modelo o de una convención (residual N-06).
