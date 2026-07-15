# Diseño · El engine C5 se generaliza a un eje (E1.2)

> Cómo se materializa y qué ratificó JM (**D19**) antes del código. Regla sagrada heredada
> (C1/C3/C4/C5): **añadir claves, nunca cambiar semántica**. Un fallo se corrige en el código,
> **jamás** aflojando una golden.

## 1 · El delta de engine (exacto)

En `presupuestar(modelo, criterio, banco, parametros)`:

```python
eje = str(parametros.get("eje", "coste"))
es_coste = eje == "coste"
unidad_eje = banco.get("unidad_eje") or banco.get("moneda") or parametros.get("moneda", "EUR")
banco_ref  = banco.get("ref") or banco.get("banco")
```

En los dos sitios donde se construye una partida (origen=modelo y origen=regla), tras armar el `dict`
`p` **idéntico al de hoy**, se añade una única guarda:

```python
if not es_coste:                       # el eje coste (default) NO entra aquí → rama intacta
    p["valores"] = {eje: _valor_eje(unitario, total, unidad_eje, banco_ref, origen)}
```

- **origen=modelo:** `unitario = precio` (del banco), `total = importe` (`mul2(cantidad, precio)`),
  `banco_ref` presente, `origen="modelo"`.
- **origen=regla (S&S):** `unitario = total = importe`, **sin** banco (`banco_ref=None`),
  `origen="regla"`.

`_valor_eje(...)` devuelve `{"unitario", "total", "unidad"[, "banco"], "origen"}`, que conforma
`$defs.valor_eje` (E1.1). **Nada más cambia**: catálogo, medición, motor económico, cuadros y
`resumen` quedan idénticos.

## 2 · No-regresión sobre `GOL-PRE-01` (la prueba, no la promesa)

Como toda la novedad vive tras `if not es_coste:`, con `eje="coste"` (default) el objeto de salida es
el del C5 previo **byte a byte**. Verificado en el sandbox por el path puro `presupuestar` (sin IFC),
alimentado con `entrada.json.modelo` + packs `criterio/AQ/v1` + `banco/AQ-DEMO/v1`:

- `estado_mediciones` semántico == `expected["presupuesto"]`; PEM **7 022,53** → PEC **10 111,74**.
- **ninguna** partida emite `valores`.
- `eje="coste"` explícito devuelve **exactamente** el mismo objeto que el default.

El runner C5 (`run_case_c5`, recompute antepuesto, D9) sigue verde sin editar `expected`.
`GOL-PRE-02` (5D) y `GOL-DOC-01` (C7) no dependen de `parametros.eje` (default coste) → intactos.

## 3 · Decisión ratificada por JM (C5 · D19)

> La IA propuso; **JM ratificó** (2026-07-08). Anclada en
> `packages/contracts/C5-presupuesto/DECISIONES.md` (continúa D16–D18).

### D19 · Un run con eje NO-coste: **espejo + `valores[eje]` etiquetado**
El esquema exige `precio_unitario`/`importe` (required, `minimum: 0`), pero D16 no cubrió el caso
«este run no tiene coste». Resolución ratificada: en un run `eje != "coste"`, esos campos **reflejan
la magnitud del eje** (espejo) y la **verdad etiquetada** (con `unidad` + `banco`) vive en
`valores[eje]`; el `resumen` totaliza el eje. En el run de coste (default) esos campos son coste y no
hay `valores` (D16 intacto).
- **Alternativa rechazada:** `precio_unitario=0`/`importe=0` en el run no-coste (D16 literal). Se
  descarta por dar un `resumen` en cero y romper la simetría con el presupuesto de coste; el espejo es
  más útil (resumen del eje) y de un **solo camino de código** (mínimo riesgo para `GOL-PRE-01`).

## 4 · De dónde salen la unidad y el banco del eje (forward-open)

El **banco** declara su propio eje: `unidad_eje` (p. ej. `"kgCO2e"`) y `ref` (id anclado, p. ej.
`"banco-carbono/generico/v1"`). El banco de coste `AQ-DEMO` **no** los declara (usa `moneda="EUR"` y
`banco="AQ-DEMO/v1"`), y como el run de coste no emite `valores`, **no se re-ancla** ese pack. Un
banco de carbono (Ola 2) los declarará; es aditivo.

## 5 · Qué desbloquea

- **Ola 2 (E3)** — `banco-carbono/generico/v1` + `GOL-CAR-01`: la huella se calcula con **este mismo
  engine** (otro banco, `eje="carbono"`), sobre la forma que E1.1 abrió y E1.2 rellena.
- La composición multi-eje final (coste canónico + `valores.carbono`) se resuelve superponiendo el
  run de coste y el run del eje por código/GUID (paso posterior; fuera de E1.2).

## 6 · Riesgos y mitigación

- *Tocar sin querer la rama de coste.* → La novedad está aislada tras `if not es_coste:`; verificada
  la identidad byte a byte del default (§2).
- *Deriva de la unidad/ref del eje.* → Las declara el banco (anclado por hash); el engine solo las
  refleja. `GOL-CAR-01` (Ola 2) fijará el número del eje.
