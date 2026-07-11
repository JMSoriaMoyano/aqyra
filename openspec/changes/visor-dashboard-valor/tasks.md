# Tareas · Skin del visor · Dashboard de valor (E6.1) — `visor-dashboard-valor`

> Gobernado por `docs/frontend-standards.md` (visor `apps/`, TDD, Llave 1) y `docs/PROCESO_SDD.md`. Naturaleza
> **vertical TS** (`apps/`): va por revisión normal (Llave 1 = gate de tests TS). **NO** es contract-first:
> consume `proyectar` (E2.2), ya anclada por `GOL-PRE-03`. Zona intocable: motor (`engines/presupuesto`),
> `proyectar`/`GOL-PRE-03`, esquema C5, packs, y el **núcleo del visor** (`viewer`, `ifc-loader`, selección,
> `data-state`, skins existentes — golden del visor intacta). Baby steps; solo lo afectado. El loop TS corre en
> la máquina de JM (pnpm/symlinks no van por el mount).

## Paso 0 · Ratificación (BLOQUEA el código)
- [x] JM ratifica **D-DV-1** (casa: skin del visor vs app aparte). Recomendación: **skin del visor**.
- [x] JM ratifica **D-DV-2** (alcance v0: ejes {coste, carbono} × cortes {espacial, funcional, uniclass};
      tabla + gráfica; selección→GUIDs; comparar dos ofertas = post-v0). Recomendación: como se lista.
- [x] JM ratifica **D-DV-3** (fuente de datos: JSON de proyección **precomputado** vs service en vivo).
      Recomendación: **precomputado** (patrón derivado/BCF, sin cálculo en cliente).
- [x] JM ratifica **D-DV-4** (aceptación: E2E TS reproduce los totales/grupos de `GOL-PRE-03`; sin golden nuevo
      de engine). Recomendación: como se lista.
- [x] JM ratifica **D-DV-5** (muro de cobro: v0 sólo vista; export firmable = forward). Recomendación: como se
      lista.
- [x] Anclar **D-DV-1..D-DV-5** en `apps/visor/DECISIONES.md` (nueva entrada V). — en este PR

## Paso 1 · Rama (primero, tras ratificar) — host
- [x] Crear y cambiar a `feat/visor-dashboard-valor` desde `origin/main` (git por `.bat` en el host).

## Paso 2 · Tests-first (TDD «red») — Vitest headless
- [x] `apps/visor/test/dashboard.test.ts`: red sobre `dashboard.ts` (aún inexistente) — invariante Σ por vista,
      semántica de grupos vs `GOL-PRE-03` (i-planta / ii-uniclass / iii-v-funcional), determinismo de la
      presentación, selección→GUIDs, regla `isCertified` (la vista nunca certifica). Ver `tests-first-draft.md`.
- [x] Fixture de proyección: anclar el/los JSON de proyección de la muestra (índice `{(eje,corte)→grupos}`),
      **emitido del engine** (no escrito a mano), que reproduce `GOL-PRE-03`. Registrar su md5.

## Paso 3 · Emisor del JSON de proyección (determinista, junto al engine) — apply
- [x] Un emisor mínimo (Python, `engines/presupuesto` o `tools/`) que llama a `proyectar` por cada `(eje,corte)`
      de v0 y vuelca el índice de proyección (forma de `GOL-PRE-03.expected` + `n_partidas`/`guids`/`unidad`).
      Determinista; **no** vive en el visor. Verificable en el sandbox / conda `mcp-bim` (según pase por
      `medir()`). Congela la **fixture** del visor.

## Paso 4 · Lógica de presentación pura — apply
- [x] `apps/visor/src/dashboard.ts` (NUEVO, puro, sin three/web-ifc — patrón `skins.ts`/`cost.ts`): consume el
      índice de proyección → modelo de vista (filas ordenadas, Σ, escala de barras, unidad, chip de fuente).
      Selección de grupo → lista de `guids[]`. Verde los tests del Paso 2.
- [x] Exportar los tipos/ut’s en `src/index.ts` (recorte del corte, patrón V1).

## Paso 5 · UI de la piel + demo — apply
- [x] UI de la skin (`apps/visor`): panel de valor (selectores eje×corte, tabla, gráfica de barras, pastilla Σ,
      chip de fuente) + cableado de la **selección → resaltado de GUIDs** en el `Viewer` (reutiliza la selección
      existente; no reescribe geometría).
- [x] Registro de la skin (`registry.ts`/`skins.ts` si aplica) + `demo/main.ts` para exhibirla sobre el
      federado de la demo. Barra de estado «se siente gratis · el export firmable llega».

## Paso 6 · Anclaje de decisiones — apply
- [x] `apps/visor/DECISIONES.md`: nueva entrada **V** con **D-DV-1..D-DV-5** + referencia al backlog E6.1 y a
      `GOL-PRE-03`/`c5-proyeccion-vista`.

## Pasos obligatorios (Llave 1)
- [x] **apps/ (Llave 1):** en la máquina de JM — `pnpm -r typecheck` + `pnpm -r build` + `pnpm -r test`
      (Vitest) VERDE; **golden del visor/`core` intacta** (skins, selección, `data-state`, `federado-e2e` sin
      cambios). Reporte en `specs/visor-dashboard-valor/reports/AAAA-MM-DD-unit-test.md`.
- [x] `adversarial-review visor-dashboard-valor`: sin cálculo en cliente (el visor lee la fixture, no re-mide);
      la aceptación reproduce `GOL-PRE-03`; el núcleo del visor y `proyectar`/`GOL-PRE-03` intactos.
- [x] `opsx:archive` → **PR** `feat/visor-dashboard-valor` → `main`; gate verde (Llave 1).
- [x] **Llave 2 = JM** (merge/firma). **SIN release** (la vista es consulta; el export firmable = forward).

## Fuera de estas tareas
- Export firmable de la proyección (dos llaves, muro de cobro) = forward · comparar dos ofertas/presupuestos =
  post-v0 · cortes GuBIM/avanzados = forward · tocar `proyectar`/`GOL-PRE-03`/el motor/el esquema/los packs ·
  tocar el núcleo del visor o las skins existentes (salvo el registro aditivo de la nueva skin) · el banco de
  coste real (E5.1, change hermano `c5-banco-coste-abierto`).
