# Contrato C4 — federación (N IFC por disciplina → Maestro + QA IDS → BCF)

> **Ficha autoritativa** (6 campos). Fuente: `Aqyra-Raiz/C4_federacion.md §1`
> (las fichas de `Aqyra-Raiz` son la fuente; esta copia es la que rige en el monorepo).
> El **esquema ejecutable** de este contrato son los tres `*.schema.json` de esta carpeta.
> Decisiones de contrato ancladas en `DECISIONES.md` (D1–D5, OK JM 2026-07-02).

## Ficha (6 campos)

**Propósito.** Unir **N IFC por disciplina** en un único **Maestro** coordinado, y
**validarlo** contra los requisitos (**IDS**), emitiendo las incidencias en **BCF**.

**Frontera.** Productor: `services/federacion` (tarea 1.1; aún no existe — contract-first).
Consumidores: **C1** (lee el Maestro), todos los engines y **C7** (trabajan sobre el
Maestro), y la **app/visor** (navega el Maestro y las incidencias BCF).

**Entra.**
- **N IFC por disciplina** (IFC4X3).
- **Reglas de federación** — ver `reglas-federacion.schema.json`: CRS destino (EPSG),
  **punto base DECLARADO por modelo** (ADR: nunca adivinado), disciplina, prioridades y
  política de deduplicación, pack IDS a aplicar.
- **IDS** (pack de requisitos) — `data/packs/ids/<id>/<version>/` (IDS 1.0, buildingSMART).

**Sale.**
- **Maestro**: **manifiesto de federación** (fuente de verdad — ver
  `maestro-manifiesto.schema.json`) + **IFC federado derivado determinista** del manifiesto
  (IFC4X3; lo que navega el visor). D1.
- **Informe de QA** — ver `informe-qa.schema.json`: pass/fail por requisito IDS,
  incidencias con GUIDs, **estados S0–S7** (ISO 19650) por modelo y para el Maestro.
- **Incidencias BCF** — estándar **BCF 3.0** de buildingSMART, **por referencia** (D2:
  no se re-esquematiza; versión fijada aquí y en `versions.lock`).

**Garantía + oráculo.** **Determinista** (mismos IFC + mismas reglas + mismo IDS → mismo
Maestro y mismo informe). Golden = modelos de referencia federados (manifiesto + informe
esperados) y conformidad IDS (pass/fail por requisito, con fallos conocidos adrede).
Oráculo: golden `C4-*` (p. ej. `C4-FED-01`, en `packages/golden/C4/`) — **modo anclado**
(oráculo manual documentado en la ficha) hasta que el service exista (D4).

**Versión.** SemVer; el consumidor ancla `federacion x.y.z` + `IDS vN` + `BCF 3.0` en
`versions.lock` (`[contracts.C4]`).
**Estado: contract-first, sin engine** (schema 0.1.0; service = tarea 1.1).

## API abstracta

```
federar(ifcs[], reglas)   → maestro   (manifiesto + IFC derivado)
validar(maestro, ids)     → {informe, bcf}
```

## Qué NO es (fronteras honestas)

- **No calcula dominios** (C3/C5/C9/C10) ni redacta memorias (C7).
- **Clash geométrico FUERA de C4 v1** (ADR): la QA por IDS cubre "¿está la información y
  bien formada?", no interferencias.
- **No adivina georreferenciación**: si un modelo no la trae, el punto base se **declara**
  en las reglas (input), no se infiere en silencio.
- **No funde ni renombra GUIDs de terceros**: procedencia por disciplina preservada en el
  manifiesto; los elementos no se deduplican (v0.1: solo la estructura espacial se unifica).
- El endurecimiento del parser C1 para IFC sucio es **dependencia** de C4, tarea aparte (1.3).

## Regla de evolución (heredada de C1, sagrada)

*Añadir claves nuevas, nunca cambiar la semántica de las existentes.* Los tres esquemas son
*forward-open*.

---
*La ficha es el diseño; el esquema + la golden son el contrato ejecutable.*
