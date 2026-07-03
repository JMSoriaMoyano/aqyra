# Golden GOL-CTE-01 — cumplimiento CTE sobre el Maestro federado (C3, contract-first)

> El primer caso del contrato **C3** (cumplimiento normativo multi-código). Hace **JUZGABLE** el
> Maestro que 3.1 hizo abrible: veredicto **por exigencia** + checklist. **Modo ANCLADO**
> (contract-first, D5): el checklist esperado es el **oráculo FIRMADO** (cubierto por el tag GPG
> del cierre); el engine `engines/cumplimiento` llega en 3.3 y **antepondrá** el recompute contra
> este MISMO expected (costura C1/C4).

## Entradas (RE-USADAS byte a byte del C4-FED-06 — patrón D14/D21: cero entradas de diseño nuevas)

- `entrada/ARQ.ifc` — congelado del 06 (md5 `653a359154112146d82ca02de0fde2ee`). ARQ: 2 muros,
  1 losa, 1 puerta, 1 ascensor (`Ascensor-01`, ELEVATOR). Plantas `Planta Baja` / `Planta 1`.
- `entrada/EST.ifc` — congelado del 06 (md5 `b84cb79c4a7cf4b560148340bc8dc305`). EST: 4 pilares,
  2 zapatas, 1 losa. Plantas `Nivel 00` / `Nivel 01`.
- `reglas.json` — copia de las reglas de federación del 06: el Maestro (manifiesto + derivado
  `dcb1e14460f3556107ce35d6dade16c3`) es **regenerable** con `services/federacion` 0.5.0. La
  verificación C3 se hace **sobre el Maestro** (D2), no sobre un IFC suelto.

## Entrada del contrato (`entrada.json`)

`modelo` = **maestro-federado** (reglas + derivado como vista + procedencia ARQ/EST). `uso` =
**Residencial Vivienda** y `localizacion` = **Jaén (zona climática C4)**, ambos **DECLARADOS**
(ADR: nunca inferidos del IFC). `pack_normativo` = **CTE/2019**.

## Oráculo (checklist calculado A MANO, verificado ×2 — 2026-07-03)

Con `ifcopenshell 0.8.5` sobre los modelos congelados (md5 comprobados antes de leer), el
checklist ejercita los **cuatro estados** del veredicto:

| exigencia | DB / apartado | resultado | cómo se derivó del Maestro |
|---|---|---|---|
| `E-SUA-ACCESO` | DB-SUA 9 §1.1.2 | **cumple** | `IfcTransportElement 'Ascensor-01'` PredefinedType=ELEVATOR presente |
| `E-SI-RF-DECL` | DB-SI SI6 Tabla 3.1 | **no-cumple** (adrede) | **0 de 10** elementos estructurales con `FireRating` (ARQ 3=2 muros+1 losa; EST 7=4 pilares+2 zapatas+1 losa) |
| `E-SI-EVAC` | DB-SI SI3 | **no-verificable** | requiere motor de evacuación (ocupación + recorridos) |
| `E-HE1-DEMANDA` | DB-HE HE1 | **no-verificable** | requiere motor térmico (demanda por zona climática C4) |
| `E-RSCIEI` | RSCIEI RD 2267/2004 | **no-aplica** | uso Residencial Vivienda (no industrial) |

**Resumen:** total 5 → cumple 1 · no-cumple 1 · no-aplica 1 · no-verificable 2.
**Veredicto agregado:** `no-conforme` (regla D4: hay ≥1 `no-cumple`).

**Doble verificación:** dos lecturas independientes con ifcopenshell (inspección de clases/Psets
y recuento estructural + `FireRating`) dieron los mismos números (10 estructurales, 0 con
`FireRating`); el ascensor ELEVATOR está presente. Los md5 de entrada coinciden con los
congelados del 06.

## Qué ancla el modo ANCLADO (runner `run_case_c3`, más checks que hoy — D10)

Conformidad de los **2 esquemas** (entrada + veredicto); **identidad por hash** (entradas del 06 +
derivado `dcb1e144…`); **coherencia interna** (exigencias del veredicto ⊆ pack CTE; taxonomía
**cerrada** de resultados; `motivo` presente en cada `no-verificable`; `resumen` == recuento
real; **veredicto agregado** según la regla D4; `uso`/`localizacion` coherentes entrada↔veredicto;
modelos de `por_modelo` ⊆ modelos de la entrada; pack anclado en `versions.lock [packs.normativa]`).

## Regla de oro

Un fallo NO se arregla aflojando esta golden. El checklist solo se re-ancla si cambia el DISEÑO
del caso (decisión explícita con JM). Las entradas son las CONGELADAS del 06: cambiarlas es
cambiar el caso. Cuando el engine de 3.3 exista, **reproducirá este expected** — si discrepa, se
investiga el engine, jamás el oráculo.
