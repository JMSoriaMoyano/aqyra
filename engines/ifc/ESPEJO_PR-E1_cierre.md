# PR-E1 · Cierre — espejo del engine retirado + guion PR-E2…E5

**Fase I · hilo 2.** Estado al cerrar el trabajo local (pendiente de merge por PR con gate verde).
Base `main` `7a25c98`. La zona firmada `_import/` no se tocó.

## Qué queda hecho (DoD por tarea)

1. **Fork resuelto** (`ESPEJO_PR-E1_decision.md`): modelo **C** (piloto), alcance **solo engine**,
   publicación **firmada desde el monorepo**, consumo **por copia en build**.
2. **Fuente localizada**: no había copia viva editable; el empotramiento solo existía en el
   `.plugin` ZIP (0.9.2 frozen) y en el 0.10.0 nunca empaquetado. Re-home = crear miembro nuevo.
3. **Re-home**: `plugins/iso19650-openbim/` (0.10.0) construye consumiendo `engines/ifc`; el
   compilador NO se commitea (se genera en build). `tools/build_plugin_iso19650.py` prueba
   identidad byte a byte vs `versions.lock` y sale **APTO** por la puerta de empaquetado.
4. **Guardián** `engines/ifc/tests/test_no_reaparicion_espejo.py` en el gate (paso `pytest
   engines/ifc`): falla si el corte del engine reaparece trackeado fuera de `engines/ifc`, y ata
   la copia de núcleo del plugin al canónico `packages/core`.
5. **Anclado** en `versions.lock` (`[engines.ifc] estado`, `[core] estado`).

Wiring del gate: `ci.yml` Paso 1b (build APTO en cada PR), `affected.py` (`plugins/`→`ifc`),
`justfile` intacto (el guardián entra por `test-engine`).

## Verificación (sandbox)

- `pytest engines/ifc`: 10 passed (identidad + espejo intactos). El guardián hace *skip* en el
  sandbox por índice de git corrupto en el mount; con `git ls-files` simulado, **ambos tests
  pasan**. `packages/core` requiere `uv sync` (no rehecho en sandbox; verde en CI).
- Build del plugin: **APTO para distribuir** (494/500 desc., 31 módulos, 0 sintaxis, identidad
  engine OK; 3 encogimientos 0.9.2→0.10.0 auditados en `--allow-shrink`).

La verdad la sella el **gate en checkout limpio** (el mount da torn-reads e índice corrupto).

## Publicación (Llave 2, JM)

Tras merge con gate verde: `python tools/build_plugin_iso19650.py` produce el `.plugin` 0.10.0;
el release se hace por **tag firmado** `vX.Y.Z` (release.yml verifica golden verde + firma GPG).
El `.plugin` 0.9.2 en `_import` queda frozen.

## Guion del siguiente hilo — PR-E2…E5 (espejo del núcleo)

Mismo patrón, un plugin por PR: que `motor-fem`, `obras-lineales`, `instalaciones`, `puentes` (y
el propio `iso19650-openbim`) consuman `packages/core` en vez de su `scripts/nucleo/` propio,
**generando** la copia en build desde `packages/core` (igual que el engine desde `engines/ifc`).
El guardián ya ata las copias al canónico; al retirarlas, se sustituye la atadura por la ausencia.
Cierre del núcleo cuando ninguna build embeba copia: `test_identidad_nucleo` queda como única
garantía y se re-ancla `[core] estado`.
