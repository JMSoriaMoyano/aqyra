# engines/presupuesto — engine C5 (presupuesto trazable desde la medición)

Engine VIVO del contrato **C5** (Fase IV·h2, D6–D10). Hace **presupuestable** el modelo que el visor
hizo abrible (C1) y el cumplimiento hizo juzgable (C3): **medición trazable → precios descompuestos →
PEM/PEC firmable**. La medición **nace del modelo** (los `Qto`), no se teclea.

## API

```python
from aqyra_presupuesto import medir, presupuestar

modelo = medir([{ "id": "ARQ", "disciplina": "ARQ", "path": "ARQ.ifc", "fichero": "ARQ.ifc" }, ...])
presupuesto = presupuestar(modelo, criterio, banco, parametros)
```

- `medir(fuentes) → modelo` — **módulo 1 (parser, D7)**: abre el IFC(+`Qto`) y produce el modelo neutro
  de medición (`salida` conforma `entrada-presupuesto.schema.json`). Lee `Qto` (no adivina geometría,
  D_modelo); detecta huecos (`IfcRelVoidsElement`) y la magnitud **neta** ya los descuenta (D7).
- `presupuestar(modelo, criterio, banco, parametros) → presupuesto` — **módulos 2–6**: mapeo a
  partida(s) por el criterio (un objeto → varias partidas), motor económico (medición × precio del
  banco → PEM → GG/BI → base → IVA → PEC), justificación de mediciones (trazabilidad a GUIDs) y de
  precios (cuadros nº1/nº2), y partidas sin geometría (S&S por ratio, D5). Conforma
  `salida-presupuesto.schema.json`.

## Diseño (D6–D10)

- **Primitivas finitas (D8):** `leer-cantidad` y `partida-por-ratio` en `primitivas.py`. El **criterio
  es la tabla de verdad** ("el código es un PACK anclado, no un `if`"); la primitiva se elige por la
  **forma** del criterio anclado (`reglas_por_clase` → `leer-cantidad`; `reglas_sin_geometria` →
  `partida-por-ratio`), no por un campo explícito (el pack no lo lleva y no se re-ancla).
- **Catálogo de capítulos (WBS):** DEFAULT del engine (`CAPITULOS_DEFAULT`), **pack-overridable**
  (forward-open), como `CLASES_ESTRUCTURALES` en el engine C3.
- **Determinista:** mismo modelo + mismo criterio + mismo banco → mismo presupuesto.

## Costura y golden (D9)

El runner `packages/golden` (`run_case_c5`) **antepone** el recompute (`medir` + `presupuestar` sobre
las fixtures con `Qto`) contra el MISMO `expected` de `GOL-PRE-01` (PEM 7 022,53 → PEC 10 111,74),
conservando íntegros los 17 checks anclados del 4.1. Un fallo se investiga en el engine, jamás en el
oráculo (contract-first).

## Release (D10)

Paquete uv `aqyra-presupuesto` (SemVer). Primer tag firmado: `presupuesto-v0.1.0` (Llave 2 = firma
humana de JM; el CI nunca certifica).
