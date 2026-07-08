# Diseño · `valores{}` en la salida de C5 (E1.1)

> Cómo se materializa el cambio y **qué debe ratificar JM** (D16–D18) antes del `opsx:apply`.
> Regla sagrada heredada (C1/C3/C4/C5): **añadir claves, nunca cambiar semántica**. Un fallo se
> corrige en el código, **jamás** aflojando una golden.

## 1 · El delta de esquema (exacto)

En `salida-presupuesto.schema.json`, dentro de `$defs.partida_medida.properties`, se añade:

```jsonc
"valores": {
  "description": "EJE DE VALOR MULTI-EJE (aditivo, forward-open). Mapa id-de-eje -> valor. El eje 'coste' canónico sigue viviendo en precio_unitario/importe; 'valores' abre la partida a otros ejes (carbono, ...) SIN duplicar ni cambiar el coste. Un eje sin banco para esta partida -> su clave ausente, nunca error.",
  "type": "object",
  "additionalProperties": { "$ref": "#/$defs/valor_eje" },
  "propertyNames": { "type": "string", "minLength": 1 },
  "$comment": "clave = id de eje (string libre, convencion: 'coste', 'carbono', 'agua', 'energia_embebida', ...). Enum NO cerrado a proposito (D17): anadir un eje NO debe re-anclar el contrato."
}
```

Y un `$def` nuevo:

```jsonc
"valor_eje": {
  "description": "Valor de UN eje para UNA partida: unitario x cantidad = total, en su unidad, con el banco de origen. 'etapas' desglosa el total por fases del ciclo de vida (EN 15978) cuando el eje lo tenga (p. ej. carbono A1-A3 / A4-A5).",
  "type": "object",
  "required": ["unitario", "total", "unidad"],
  "additionalProperties": true,
  "properties": {
    "unitario": { "type": "number", "$comment": "valor por unidad de medicion (EUR/ud, kgCO2e/ud, ...). Puede ser negativo en ejes que lo admitan (p. ej. captura de carbono); por eso SIN minimum, a diferencia del coste." },
    "total":    { "type": "number", "$comment": "unitario x cantidad de la partida (misma cantidad que la medicion; redondeo del eje)." },
    "unidad":   { "type": "string", "minLength": 1, "$comment": "EUR, kgCO2e, m3(agua), MJ, ... unidad del eje." },
    "banco":    { "type": "string", "$comment": "pack de origen del factor, anclado por hash (p. ej. 'banco/AQ-DEMO/v1', 'banco-carbono/generico/v1'). Recomendado; ausente en ejes 'manual'." },
    "origen":   { "$ref": "#/$defs/origen", "$comment": "REUSA la taxonomia cerrada modelo/regla/manual; por defecto hereda el de la partida." },
    "etapas":   {
      "type": "object",
      "description": "Desglose opcional del total por etapas del ciclo de vida (EN 15978). Claves convencionales: A1A3, A4A5, B, C, D. La suma de las etapas presentes = total (invariante comprobable cuando se declaran).",
      "additionalProperties": { "type": "number" },
      "propertyNames": { "type": "string", "minLength": 1 }
    }
  }
}
```

**Nada más cambia** en el esquema. `precio_unitario`, `importe`, `origen`, `trazabilidad`, cuadros
nº1/nº2 y `resumen` quedan **idénticos**.

## 2 · No-regresión sobre `GOL-PRE-01` (la prueba, no la promesa)

`partida_medida` es `additionalProperties: true` y `valores` **no** se añade a `required`. Por tanto:

- El `expected.json` de `GOL-PRE-01` — cuyas 8 partidas **no** llevan `valores` — **valida** contra el
  esquema extendido **sin editar un solo byte** del `expected`.
- El paso de verificación (ver `tasks.md`) valida programáticamente `expected["presupuesto"]` contra
  el esquema propuesto **antes** y **después** del delta: mismo resultado (conforme). Esa es la Llave 1
  de E1.1.

`GOL-DOC-01` (compositor C7) tampoco se toca: consume el JSON, y `valores` es opcional.

## 3 · Decisiones a ratificar por JM (C5 · D16–D18)

> La IA propone; **JM firma**. Se anclarán en `packages/contracts/C5-presupuesto/DECISIONES.md`
> (continúan D1–D15) al ratificarse, ANTES del `opsx:apply`. Coherentes con D-025 (extensión
> forward-open de C5) del registro del ecosistema.

### D16 · El eje coste **no se duplica**: `valores` es el canal de los ejes NO-coste
El eje coste canónico permanece **exclusivamente** en `precio_unitario` / `importe` (fuente de verdad,
golden intacta). `valores` **no** obliga a contener `coste`; se reserva para los ejes que llegan
después (carbono, agua, …). *Un productor MAY reflejar `valores.coste` como espejo informativo, pero
el golden NO lo exige y el engine (E1.2) NO lo emite por defecto* → así `GOL-PRE-01` sigue byte-
idéntica.
- **Alternativa (a rechazar salvo indicación):** meter también `coste` dentro de `valores` y
  deprecar `precio_unitario`/`importe`. Rompería la golden y la compatibilidad de C7 → **no**.

### D17 · `id de eje` = **string libre** con convención, **no** enum cerrado
La clave de `valores` es un `string` libre (convención: `coste`, `carbono`, `agua`,
`energia_embebida`, …). **No** se cierra en enum: añadir un eje nuevo **no debe re-anclar** el
contrato ni su golden (a diferencia de `origen`, que sí es enum cerrado por ser taxonomía semántica
fija). La convención de nombres reservados se documenta en `contrato.md`.

### D18 · `etapas` (EN 15978) = objeto opcional `clave→número`, invariante Σ etapas = total
El desglose por ciclo de vida es un objeto opcional dentro de cada `valor_eje`, con claves
convencionales `A1A3`, `A4A5`, `B`, `C`, `D` (EN 15978). Cuando se declaran etapas, la suma de las
presentes **debe** igualar `total` (invariante que el engine y el golden de carbono comprobarán en la
Ola 2; en E1.1 solo se fija la **forma**). Se admite un desglose parcial (solo A1A3+A4A5) sin exigir
todo el ciclo.

## 4 · Qué desbloquea (para encuadrar la ratificación)

- **E1.2** — `presupuesto.py` acepta un `banco` cuyo unitario no es € y `parametros.eje`; rellena
  `valores[eje]`. Aceptación: con `eje=coste` y `banco=AQ-DEMO`, salida **byte-idéntica** a hoy.
- **Ola 2 (E3)** — `valores.carbono` + `banco-carbono/generico/v1` + `GOL-CAR-01`, ya sobre esta forma.

## 5 · Riesgos y mitigación

- *Que el esquema extendido invalide alguna golden.* → Mitigado por `additionalProperties:true` +
  `valores` opcional; se **verifica** (no se asume) en el paso de no-regresión.
- *Deriva de nombres de eje.* → Convención documentada en `contrato.md` (D17); el enum queda abierto a
  propósito, la disciplina es de pack/criterio, no de esquema.
- *Etapas incoherentes con el total.* → Invariante Σ etapas = total, exigido por el golden de carbono
  (Ola 2). En E1.1 no hay dato de etapas todavía.
