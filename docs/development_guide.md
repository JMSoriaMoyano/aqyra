# Guía de desarrollo — Aqyra

Setup y flujo de trabajo real del monorepo. Complementa `docs/base-standards.md`.

## Requisitos

- **Python** ≥ 3.10 y **uv** (gestor del workspace Python).
- **Node** ≥ 22 y **pnpm** 11.9 (workspace TS del visor).
- **just** (fachada de build/test). **git** con **GPG** configurado (ed25519) para firmar
  releases (solo JM firma; ver gobierno).
- Opcional: MCP de **Jira** (para `enrich-us`) y de **Playwright** (E2E de flujos).

## Puesta en marcha

```bash
just sync            # uv sync --all-packages (instala el workspace Python)
pnpm install --frozen-lockfile   # dependencias del visor (respeta el lockfile)
just --list          # ver todas las recetas
```

## Recetas `just` (fachada)

```bash
just schema-check    # valida que los esquemas de contrato son JSON Schema bien formados
just golden          # corre la golden C1 -> VERDE/ROJO (Llave 1)
just test-core       # pytest packages/core (comportamiento + identidad byte a byte)
just test-packs      # pytest packages/packs
just test-engine     # pytest engines/ifc
just test-service    # pytest services/federacion
just check           # puerta completa del CI: esquema + core + packs + engine + service + golden
just affected        # objetivos afectados por el diff contra origin/main
just build           # build de lo afectado
just test            # test de lo afectado
```

El visor se prueba aparte con pnpm: `pnpm -r typecheck`, `pnpm -r build`, `pnpm -r test`
(vitest). En CI todo esto va dentro del job `gate` (Llave 1).

## Flujo de un cambio (SSD sobre OpenSpec 1.5)

```
enrich-us <CLAVE-JIRA>      # refina el ticket (Jira MCP): IFCVIEW-, INFRA-, DEVOPS-, ...
/opsx:propose "idea"        # crea la propuesta + artefactos OpenSpec del cambio
/opsx:apply                 # implementa las tareas de una en una (TDD: golden/tests primero)
adversarial-review          # red-team antes de archivar
/opsx:archive               # archiva el cambio
commit                      # commits enfocados + PR
```

Recomendado: trabajar en un git worktree aislado (skill `using-git-worktrees`).

## Reglas de oro

- La documentación (contrato + esquema + golden) es la fuente de verdad; el código la
  implementa. Ante un cambio nuevo entre `apply` y `archive`, primero actualizar los
  artefactos OpenSpec, luego codificar.
- Un fallo de golden se corrige en el código, nunca aflojando el oráculo.
- No tocar `main` directamente: todo por PR. `packages/contracts/`, `packages/golden/`,
  `versions.lock` y `.github/` requieren aprobación de JM (CODEOWNERS).
- Nada autoritativo sin las **dos llaves**: golden verde (CI) + firma GPG de JM.
- La zona f