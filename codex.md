---
description: Reglas y directrices de desarrollo de Aqyra — monorepo industrial ACE / OpenBIM. Fuente única de verdad, aplicable a todos los agentes de IA (Claude, Cursor, Codex, Gemini).
alwaysApply: true
---

# Aqyra — estándares de desarrollo (base)

> Este documento es la **fuente única de verdad** del contexto técnico de Aqyra para los
> agentes de IA. `CLAUDE.md`, `AGENTS.md`, `GEMINI.md` y `codex.md` son copias de este
> archivo (en Windows se materializan como copias reales, no symlinks; ver §8). El diseño
> del producto está cerrado aguas arriba (`Aqyra-Raiz`); este árbol lo construye.

## 1. Principios núcleo

- **Spec-Driven Development (SSD)**: cada cambio se define por completo antes de escribir
  código. La documentación (contrato + esquema + golden) es la fuente de verdad; el código
  la implementa, no al revés.
- **Pasos pequeños, de uno en uno**: baby steps. No adelantar más de un paso.
- **La frontera son los contratos**: `packages/contracts/` define qué entra y sale de cada
  capacidad (Cn). No se cruza esa frontera sin PR aprobado.
- **Las dos llaves**: nada es autoritativo sin (Llave 1) golden verde en CI + (Llave 2)
  firma GPG humana de JM. El CI **nunca** certifica (ver §5).
- **TDD por golden y por identidad**: para un contrato, primero el caso de referencia y su
  oráculo (golden); para el núcleo/engine, tests de comportamiento e **identidad byte a byte**
  con el canónico. Un fallo se corrige en el código, nunca aflojando la golden.
- **Solo lo afectado**: el trabajo se acota al subgrafo tocado (`tools/affected.py`).
- **Cambios incrementales y revisables**: preferir modificaciones enfocadas.
- **Cuestionar supuestos** y **detectar patrones repetidos** antes de proponer.

## 2. Idioma

- **Español** para todos los artefactos del proyecto: código (nombres de variables,
  funciones, clases, comentarios, mensajes), documentación, contratos, golden y tickets de
  Jira. El repositorio real es en español (`aqyra_core`, `modelo_neutro`, `federacion`,
  `narracion-ifc`…); mantener esa coherencia.
- Los **tokens técnicos estándar** se dejan en su forma normativa: entidades y Psets IFC
  (`IfcWall`, `Pset_WallCommon`), clases IFC4x3, términos ISO 19650 (CDE, EIR, BEP, LOIN),
  BCF, JSON Schema, GPG, etc.

## 3. Arquitectura del monorepo

Monorepo de doble workspace. **No** hay Nx/Turbo/Bazel en Fase 0: el grafo de "solo lo
afectado" lo calcula `tools/affected.py` y la fachada de build es `just` (`justfile`).

- **Python (uv)** — `pyproject.toml` raíz (`package = false`), `requires-python >=3.10`.
  Miembros del workspace: `packages/core`, `packages/golden`, `packages/packs`,
  `services/federacion` (y `engines/*` según aterrizan). Dev dep: `pytest>=8`.
- **TypeScript (pnpm)** — `pnpm-workspace.yaml` (`apps/*`), `package.json` raíz privado,
  `pnpm@11.9`, Node `>=22`.

Mapa de carpetas:

```
packages/
  core/        aqyra_core — librería núcleo compartida (fin del espejo). Identidad byte a byte.
  contracts/   contratos autoritativos por capacidad: C1-interoperabilidad, C3-cumplimiento,
               C4-federacion (contrato.md + *.schema.json). LA FRONTERA. CODEOWNERS.
  golden/      corpus golden (C1/C3/C4) + runner aqyra-golden + gate (Llave 1). CODEOWNERS.
  packs/       aqyra_packs — loader de conocimiento externo versionado.
engines/
  ifc/         implementación C1 (compilador narración→IFC, catálogo IFC4x3, validación).
services/
  federacion/  service C4 (federación de modelos + QA).
apps/
  visor/       @aqyra/visor — visor OpenBIM (three + web-ifc), Apache-2.0. Ver frontend-standards.
data/packs/    conocimiento externo versionado (anclado por hash).
tools/         orquestador "solo lo afectado" (affected.py) + builders de plugins.
versions.lock  ancla engine + pack + esquema por contrato. CODEOWNERS.
justfile       fachada de build/test/golden.
```

## 4. Contratos y golden (el corazón del vertical)

- Un **contrato** (`packages/contracts/Cn-*/`) = `contrato.md` (ficha autoritativa) +
  uno o más `*.schema.json` (JSON Schema). Es la interfaz estable; el resto del sistema
  depende de él, no de las implementaciones.
- Un contrato se valida con **dos comprobaciones**: (1) esquema JSON Schema bien formado;
  (2) **golden verde** — un caso de referencia + su oráculo; el runner comprueba conformidad
  de esquema y coincidencia con el oráculo (dentro de tolerancia).
- El **runner** es `aqyra-golden` (paquete `packages/golden`): `--schema-only` valida solo
  esquemas; sin flag corre la golden completa. Se invoca por `just schema-check` y `just golden`.
- **Regla de dependencia**: tocar un contrato o el core reejecuta la golde