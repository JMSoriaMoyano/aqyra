# Paso 5 · Unit tests + estado — visor-cumplimiento-6d (2026-07-07)

Verificación mecánica de los pasos obligatorios. Toolchain del host (no hay uv/pytest/just en el
PATH de JM): engine con runner standalone (python conda `mcp-bim`), visor con el `node_modules` local.
El gate (GitHub Actions, uv+pytest+pnpm) es la verificación de referencia (Llave 1).

## Engine C3 + golden 6D (Python)

- **Runner standalone del golden** (`_operativo/run_6d_golden.py`, despacho real `run_case_c3`):
  `GOL-CTE-01` (22 checks) + `GOL-CTE-6D-01` (14 checks) → **VERDE**. n_elementos=13 (todos
  `no-cumple`, E-SI-RF-DECL domina), determinismo md5 raw `d9b68d468ee8…`.
- **Gate CI** (ci.yml Paso 1 pytest de `engines/cumplimiento` + Paso 3 golden completo): **VERDE**
  (run 28878912633, 55 s) tras el fix de colisión de basename `test_escritura.py`
  (→ `test_escritura_cumplimiento.py`, commit `e0a0b3d`).

## Visor 6D (TypeScript)

- **Local host** (`CHECK_visor.bat`): `tsc -p tsconfig.check.json` (typecheck, incl. `demo`) rc=0;
  `tsc -p tsconfig.json` (build) rc=0; `vitest run` **92/92** (20 ficheros) rc=0. Nuevos:
  `compliance.test.ts` (6) + `cumplimiento-6d-e2e.test.ts` (2).
- **Gate CI** (ci.yml Paso 5 pnpm build+typecheck+test): **VERDE** (run 28882354507, 52 s).

## Nota curl/Playwright de los pasos obligatorios

**N/A**: no hay endpoint HTTP nuevo (engine de librería + visor estático). La verificación
equivalente es el runner de golden (engine) y el E2E vitest anclado (visor), ejecutados por el agente
y confirmados por el gate.

## Hallazgos

1. El check de conteos del golden 6D debía restringir la proyección a los `IfcElement` ESCRITOS
   (`guid_a_modelo` mapea todo `IfcProduct`, incl. estructura espacial; el engine escribe solo en
   `IfcElement`). Corregido en el runner, no en el engine.
2. `test_escritura.py` colisionaba de basename con `engines/presupuesto` en el pytest del CI
   (convención del repo = basenames únicos, sin `__init__.py`). Renombrado.
3. El loader del visor enumera solo elementos RENDERABLES (`ELEMENT_TYPES`): colorea 11 de los 13
   (no enumera `IfcTransportElement` ni `IfcOpeningElement`). El lector de datos ve los 13. El E2E
   ancla `colorPorExpress.size == m.elements.length`, no 13.
