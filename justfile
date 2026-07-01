# Aqyra — fachada de orquestación (Fase 0)
# Requiere: uv (paquetes Python) + pnpm (visor TS). El grafo de "solo lo afectado"
# lo calcula tools/affected.py. No hay Nx/Turbo/Bazel en Fase 0 (se añade si el grafo crece,
# sin tocar esta fachada).

set shell := ["bash", "-uc"]

# rama base para el cálculo de "afectado"
base := "origin/main"

# recipe por defecto: enseña la ayuda
default:
    @just --list

# instala/actualiza el workspace Python (todos los miembros)
sync:
    uv sync --all-packages

# valida que los esquemas de contrato son JSON Schema bien formados (paso 1 de validación)
schema-check:
    uv run --package aqyra-golden aqyra-golden --schema-only --golden-dir packages/golden

# corre la golden (Llave 1) — el corazón del vertical C1
golden:
    uv run --package aqyra-golden aqyra-golden --golden-dir packages/golden

# tests del núcleo (comportamiento + identidad byte a byte con el canónico)
test-core:
    uv run pytest packages/core -q

# tests de packs (manifiesto + versión anclada + golden de pack por hash)
test-packs:
    uv run pytest packages/packs -q

# puerta completa que exige el CI: esquema válido + tests de core/packs + golden verde
check: schema-check test-core test-packs golden

# lista los objetivos afectados por el diff contra {{base}}
affected base=base:
    uv run python tools/affected.py --base {{base}}

# build de lo afectado (Fase 0: sync del workspace + build del visor si está tocado)
build base=base:
    uv sync --all-packages
    uv run python tools/affected.py --base {{base}} --run build

# test de lo afectado (Fase 0: la golden es el test)
test base=base:
    uv sync --all-packages
    uv run python tools/affected.py --base {{base}} --run test
