# aqyra — monorepo industrial (Fase 0)

Monorepo de Aqyra (industria ACE / OpenBIM). Este árbol es el **andamiaje** de la Fase 0:
esqueleto + el vertical de prueba **C1 → golden → CI**, que valida la tubería entera con el
mínimo material.

> Base documental (fuente, no se reinventa aquí): `../Aqyra-Raiz/` —
> `MANUAL_arquitectura_Aqyra.docx`, `PLAN_reestructuracion_industrializacion.docx`,
> `ADRs_decisiones-arquitectura.md`, `CONTRATOS_estado-validacion-ubicacion.md` y las fichas
> de fundación (C1, C6+packs, core+CI).

## Estructura

```
aqyra/
├── packages/
│   ├── core/          librería compartida (fin del espejo) — esqueleto, se llena en 0.5
│   ├── contracts/     contratos autoritativos (ficha + esquema), anclados en versions.lock
│   │   └── C1-interoperabilidad/   ← formalizado en este hilo
│   └── golden/        corpus golden (C6) + runner + gate (Llave 1)
│       └── C1/C1-APERTURA-01/      ← golden importada (firmada aguas arriba)
├── engines/           implementaciones (engines/ifc = C1 impl, se importa en 0.5)
├── services/          C4 federación, C7 operador (fases posteriores)
├── apps/              visor TS (pnpm)
├── data/packs/        conocimiento externo versionado (esqueleto, se llena en 0.6)
├── tools/             orquestador "solo lo afectado"
├── versions.lock      ancla engine + pack por contrato
├── justfile           fachada de build/test/golden
├── pyproject.toml     workspace uv (Python)
└── pnpm-workspace.yaml workspace pnpm (TS)
```

## Cómo se valida un contrato (las dos llaves)

1. **Esquema válido** (JSON Schema bien formado).
2. **Golden verde:** un caso de referencia + su oráculo; el runner comprueba conformidad de
   esquema y coincidencia con el oráculo (dentro de tolerancia).
3. **CI corre la golden** en cada PR → **Llave 1** (automática). PR rojo bloquea el merge.
4. **Adopción:** bump → anclar en `versions.lock` → **firma GPG de JM** → **Llave 2** (humana).
   El CI **nunca** certifica.

`packages/contracts/` y `packages/golden/` están protegidos por **CODEOWNERS**: cambios por PR.

## Uso rápido

```bash
just sync           # instala el workspace Python (uv)
just schema-check   # valida que los esquemas de contrato son JSON Schema bien formados
just golden         # corre la golden C1 → VERDE/ROJO (Llave 1)
just check          # esquema + golden (lo que exige el CI)
just affected       # lista los objetivos afectados por el diff contra origin/main
```

## Estado de la Fase 0

- **0.1** esqueleto + workspace + orquestador — hecho.
- **0.2** esquema de C1 (modelo neutro + alto-spec) formalizado, anclado — hecho.
- **0.3** golden C1 (`C1-APERTURA-01`) importada + runner — hecho.
- **0.4** CI (golden + typecheck) + CODEOWNERS + firma en release — hecho.
- **0.5** `packages/core` (extraer núcleo, retirar espejo) — hecho.
- **0.6** `data/packs` (packs versionados) — hecho.
- **0.7** importar historia git de los 4 repos preservando firmas — **hecho** (la última).

**Fase 0 COMPLETA (0.1–0.7).** Cimientos cerrados.

## Historia importada (0.7)

La historia completa de los 4 repos aguas arriba está bajo `_import/<repo>`, importada con
`git subtree add` (**conserva los SHA**, así que los objetos firmados siguen intactos y sus
tags GPG verifican en el monorepo). Los 4 repos originales quedan archivados read-only; la
zona firmada **no se reescribe**. Procedencia y tags firmados: ver `versions.lock` §`[historia]`.

| Repo origen | Prefijo | Tags firmados |
|---|---|---|
| `aqyra-motor` (`Estructurando`) | `_import/aqyra-motor` | 4 |
| `aqyra-entorno` (`Entorno`) | `_import/aqyra-entorno` | 3 |
| `aqyra-contratos-golden` (`Estructurando 2.0`) | `_import/aqyra-contratos-golden` | 1 |
| `aqyra-raiz` (`Aqyra-Raiz`) | `_import/aqyra-raiz` | 0 |

*Fase 0 = cimientos. El diseño está cerrado (ver `Aqyra-Raiz`); este árbol lo construye.*
