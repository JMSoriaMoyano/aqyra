# Contrato C3 — cumplimiento normativo (multi-código) sobre el Maestro federado

> **Ficha autoritativa** (6 campos). Fuente: `Aqyra-Raiz/PLAN_reestructuracion_industrializacion.md §2`
> (fila C3). El **esquema ejecutable** de este contrato son los dos `*.schema.json` de esta
> carpeta. Decisiones de contrato ancladas en `DECISIONES.md` (D1–D5, OK JM 2026-07-03).

## Ficha (6 campos)

**Propósito.** Emitir un **veredicto de cumplimiento normativo POR EXIGENCIA** (+ checklist)
sobre un modelo, para un **uso** y una **localización** dados, aplicando **packs normativos**
(CTE/RITE/urbanística…). **Multi-código por diseño:** el código es un **PACK anclado, no un
`if`** — cambiar de año/mercado/municipio = cambiar de pack, no de engine.

**Frontera.** Productor: `engines/cumplimiento` (tarea 3.3; **aún no existe** — contract-first).
Consumidores: **C7** (orquesta el cumplimiento y redacta la memoria/anexo) y el producto. El
**anexo contra incendios** ilustra la composición del PLAN: C3 (DB-SI/RSCIEI) + C10 (hidráulica
de BIE/rociadores) + C7 (redacta) — ningún engine solo.

**Entra.** Ver `entrada-cumplimiento.schema.json`:
- **modelo** = el **Maestro federado** (lo que produce C4): manifiesto + `base_dir`, con el
  **IFC derivado como vista** (D26/D30 de C4). C3 consume lo que C4 produce (dependencias §1).
- **uso** — uso característico DECLARADO (ADR: nunca adivinado del IFC).
- **localizacion** — país/CCAA/provincia/municipio/zona climática, DECLARADA.
- **pack_normativo** — `data/packs/normativa/<id>/<version>/` (p. ej. `CTE/2019`).

**Sale.** Ver `veredicto-cumplimiento.schema.json`:
- **veredicto POR EXIGENCIA**: `{id, exigencia, documento_basico, referencia (pack+apartado),
  resultado ∈ {cumple, no-cumple, no-aplica, no-verificable}, motivo_no_verificable?, evidencia?,
  por_modelo?}`.
- **resumen** agregado (conteo por resultado) + **veredicto** global
  (`conforme` / `conforme-con-reservas` / `no-conforme`).

**Garantía + oráculo.** **Determinista** (mismo modelo + mismo uso/localización + mismo pack →
mismo veredicto). El **checklist esperado** de la golden es el oráculo, **FIRMADO por pack**:
vive en la golden y queda cubierto por el tag GPG del cierre (Llave 2), como los expected de C4.
Oráculo: golden `GOL-CTE-01` (en `packages/golden/C3/`) — **modo ANCLADO** (checklist calculado
a mano y verificado ×2 contra el Maestro del C4-FED-06) hasta que el engine exista (3.3).

**Versión.** SemVer; el consumidor ancla `cumplimiento x.y.z` + `pack normativa vN` en
`versions.lock` (`[contracts.C3]` + `[packs.normativa]`).
**Estado: contract-first** (esquema 0.1.0 + pack `CTE/2019` mínimo + `GOL-CTE-01` anclada; el
engine `engines/cumplimiento` llega en la tarea 3.3).

## API abstracta

```
verificar(modelo_maestro, uso, localizacion, pack_normativo) → veredicto  (por exigencia + resumen)
```

## Qué NO es (fronteras honestas)

- **No calcula dominios** (evacuación, demanda energética, hidráulica…): eso son motores
  (C9/C10). Lo que un motor debe cerrar se declara **`no-verificable`** con su **motivo** (D4) —
  forward-open: el engine futuro lo convierte en `cumple`/`no-cumple` sin cambiar el esquema.
- **No adivina uso ni localización**: se DECLARAN en la entrada (ADR heredado de C4).
- **No re-esquematiza el código**: el CTE (u otro) es un **pack** versionado de `data/`, no
  lógica cableada. Multi-código = multi-pack.
- **No federa** (eso es C4) ni redacta la memoria (eso es C7).

## Regla de evolución (heredada de C1/C4, sagrada)

*Añadir claves nuevas, nunca cambiar la semántica de las existentes.* Los dos esquemas son
*forward-open*. La taxonomía de `resultado` es un enum **cerrado** de 4 valores (D4): un engine
futuro reclasifica dentro del mismo enum, no lo amplía.

---
*La ficha es el diseño; el esquema + la golden son el contrato ejecutable.*
