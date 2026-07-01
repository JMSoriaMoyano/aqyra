# data/packs — conocimiento externo versionado (0.6)

Un **pack** es una unidad versionada de conocimiento externo que un engine consume; **no es
código**. Cambiar de mercado, localidad o año = cambiar de pack, no de engine. Todo pack se
ancla en `../../versions.lock` y trae su **golden de pack**.

## Ruta y manifiesto

```
data/packs/<familia>/<id>/<version>/
├── pack.json     manifiesto (valida contra pack.schema.json)
└── golden/
    └── expected.json   golden de pack (identidad del contenido por hash)
```

El manifiesto (`pack.schema.json`): `id · familia · version · fuente · vigencia · metadatos ·
contenido`. El **hash del bloque `contenido`** es la identidad de la golden: actualizar un pack
sin bump de versión + nuevo hash **rompe el test** → no hay drift silencioso.

## Las cuatro familias

| Familia | Contenido | Lo consume | Ejemplos |
|---|---|---|---|
| **codigos** | coeficientes/curvas/fórmulas de dimensionamiento | C9 · C10 · C11+ | EC-ES · ACI 318 · AISC 360 · ASCE 7 · NFPA |
| **normativa** | reglas de cumplimiento + referencias de artículo | C3 | CTE (DB-*) · RITE · REBT · RSCIEI · RIPCI · urbanística |
| **banco** | partidas descompuestas + mapeo clasificación→partida | C5 | BEDEC/ITeC · PREOC · base del despacho |
| **ids** | Psets/clasif/valores exigidos | C4 · C7 | IDS del proyecto · plantillas EIR |

## Estado (Fase 0)

Esqueleto con un pack de ejemplo: **`codigos/EC-ES/2021`** (subconjunto mínimo de coeficientes
estándar, para probar el mecanismo). Cargador: `packages/packs` (`aqyra_packs`). Anclado en
`versions.lock` `[packs.codigo]`. El resto de familias, vacías hasta que un engine las consuma.

**Costura:** la golden de pack de Fase 0 es identidad de contenido por hash; cuando exista el
engine, se sustituye por el resultado de un **proyecto de referencia** bajo ese pack (así,
actualizar el banco o el año del código no desplaza los resultados en silencio).

Ver `../../../Aqyra-Raiz/FUNDACION_C6_golden_y_packs.md`.
