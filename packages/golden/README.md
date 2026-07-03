# packages/golden — corpus golden (C6) + runner + gate (Llave 1)

La golden **es** el oráculo. El runner valida el esquema de contrato y ejercita cada caso
contra su oráculo, dando VERDE/ROJO reproducible. **Rojo bloquea el merge** (Llave 1,
automática en CI). La **firma GPG de JM** es la Llave 2, humana; el CI **nunca** certifica.

## Estructura

```
packages/golden/
├── src/aqyra_golden/run_golden.py   runner + gate
└── C1/
    └── C1-APERTURA-01/
        ├── caso.alto.json    entrada patrón (lo que emitiría el cebo)
        ├── golden.ifc        IFC4X3 congelado (verdad compilada aguas arriba)
        ├── expected.json     el oráculo (procedencia independiente del runner)
        ├── tolerancias.json  tolerancias + regla de oro
        └── ficha.md          ficha de record
```

## Anatomía de una golden

`caso (entrada) · oráculo (resultado correcto, de procedencia independiente) · tolerancia ·
runner (compara)`. Lo que la hace fiable: el **oráculo no sale del propio código**.

## Correr

```bash
uv run --package aqyra-golden aqyra-golden --golden-dir packages/golden   # golden completa
uv run --package aqyra-golden aqyra-golden --schema-only --golden-dir packages/golden  # solo esquemas
# o, desde la raíz:  just golden   /   just schema-check
```

## Qué comprueba C1-APERTURA-01 (oráculo: conteo de entidades + round-trip)

1. `caso.alto.json` conforma `contracts/C1/alto-spec.schema.json`.
2. Del `golden.ifc` congelado, recomputa y compara con `expected.json`:
   huecos losa=1 / muro=1 · ascensor ELEVATOR=1 · planta LINE·CLOTHOID·CIRCULARARC·CLOTHOID·LINE
   · L=400.000 m · A_clotoide=134.164 · doble clasificación 7/7 · sin_clasif=0.

**Costura (0.5):** cuando `engines/ifc` se importe, se antepone el paso *compile*
(`caso.alto.json` → IFC) al oráculo, contra el **mismo** `expected.json`.

## Qué comprueba GOL-CTE-01 (C3 · cumplimiento, modo ANCLADO — Fase III·h2)

Cumplimiento normativo POR EXIGENCIA sobre el **Maestro federado** del `C4-FED-06` (reutilizado
byte a byte), con el pack `CTE/2019` mínimo. Checklist calculado A MANO y verificado ×2 con
ifcopenshell: E-SUA-ACCESO=**cumple**, E-SI-RF-DECL=**no-cumple** (adrede), E-SI-EVAC y
E-HE1-DEMANDA=**no-verificable**, E-RSCIEI=**no-aplica** → veredicto **no-conforme**. `run_case_c3`
ancla (sin engine): conformidad de los 2 esquemas + identidad por hash (entradas del 06 + derivado
`dcb1e144…` + pack) + coherencia interna (exigencias ⊆ pack, taxonomía cerrada, motivo en cada
no-verificable, resumen == recuento, veredicto agregado, uso/localización, por_modelo). El engine
de 3.3 antepondrá el recompute contra el MISMO `expected`.

## Añadir una golden

Carpeta nueva bajo `C<n>/<ID>/` con `expected.json` (+ `caso.alto.json`, `golden.ifc`,
`tolerancias.json`). El runner la descubre sola. **Un fallo se corrige en el código, nunca
aflojando la golden.**
