# Cambio · Skin del visor · Dashboard de valor (mostrador B — E6.1)

> Change-id: `visor-dashboard-valor` · Capacidad: `visor` (`apps/visor`) — consume la vista `proyectar`
> del contrato **C5-presupuesto** (E2.2, anclada por `GOL-PRE-03`).
> Historia del backlog: **E6.1** (`Aqyra-Negocio/BACKLOG_motor-valoracion_para-Aqyra-Raiz.md` §2·E6.1, §3 Ola 4).
> Procedencia: handoff negocio → desarrollo (`INICIO-hilo_Aqyra-Raiz_motor-valoracion_Ola4-dashboard.md`,
> 2026-07-11) + `BRIEF_contrato_motor-valoracion-multieje.md` §2.3 (la vista de proyección = el «a tiempo
> real») + `BRIEF_visor-skins-por-disciplina.md` (forma de skin).
> Naturaleza: **vertical TS del visor** (`apps/`) — su Llave 1 es el gate de tests TS (Vitest). **NO** es
> contract-first: consume una capacidad ya anclada (`proyectar`, `GOL-PRE-03`); no crea contrato nuevo.
> Estado: spec redactada (SSD) · decisiones **D-DV-1..D-DV-5 a ratificar** antes del código.
> Gobierna: **N-07/D-e** (el dashboard es la Ola 4), **N-06** (la proyección es consulta, no cálculo),
> **N-02** (el corte se siente gratis; el muro de cobro es el export firmable).

## Por qué

La Ola 1 dejó `proyectar(presupuesto, modelo, eje, corte)` anclada (E2.2, `GOL-PRE-03`): un *group-by*
determinista que agrega el **valor por eje** (coste, carbono) y **por corte** (espacial, funcional, Uniclass,
GuBIM) sobre la MISMA medición, ligado al objeto (GUIDs). Es el motor del «a tiempo real por clasificación»
del brief (§2.3). Lo que falta es el **mostrador B**: exponer esa vista al **validador/operador** como una
piel interactiva del visor.

E6.1 es esa piel: sobre el shell del visor abierto, una skin que **presenta** la proyección —tabla + gráfica,
comparar por eje y por corte, seleccionar un grupo y **resaltar sus GUIDs en 3D**—. Es una **VISTA, no un
cálculo**: el cliente **no recalcula**; reproduce los totales de la golden. Encaja como una skin más
(`apps/visor`, espejo de Diseño/Estructuras/Instalaciones/Auditoría/cumplimiento 6D). Cuenta la tesis del
producto: **agregar y comparar valor se siente gratis**; el **muro de cobro** sigue en el **export firmable**
(dos llaves), que en v0 queda como gancho forward.

## Qué cambia (superficie)

Vertical TS acotado (`apps/visor`), espejo de las skins ya construidas:

- **UI de la piel** (`apps/visor`, acento propio del dashboard): panel de **proyección de valor** con
  selector de **eje** (Coste / Carbono) × selector de **corte** (Espacial / Funcional / Uniclass), una
  **tabla** de grupos (`grupo · valor_total · unidad · nº partidas · fuente`) y una **gráfica de barras** de
  la proyección; al seleccionar un grupo, **resaltado de sus GUIDs** en el maestro 3D (reutiliza la selección
  del `Viewer`); pastilla de **invariante Σ** (la suma de grupos == total del eje) y chip de **fuente**
  (`ifc`/`criterio`/`regla`/`—`, traza honesta del *fallback*).
- **Lógica pura de presentación** (`apps/visor/src/dashboard.ts`, NUEVO): consume el **JSON de proyección
  precomputado** (forma de `proyectar`, D-DV-3) y produce el modelo de vista (filas ordenadas, escala de la
  gráfica, Σ, unidades). Sin three/web-ifc → testeable headless (patrón `skins.ts`, `cost.ts`, `data-state.ts`).
- **Fixtures de proyección** (`apps/visor/test/fixtures/` o `apps/visor/fixtures/`, NUEVO): el/los JSON de
  proyección de la muestra (emitidos por el engine, patrón derivado/BCF: el visor los **lee**, no los calcula),
  para el test de aceptación que reproduce `GOL-PRE-03`.
- **Registro de la skin** (`registry.ts`/`skins.ts` si aplica) + **demo** (`demo/main.ts`) para exhibirla.
- **`apps/visor/DECISIONES.md`** — nueva entrada **V** con **D-DV-1..D-DV-5**.

## Qué NO cambia / fuera de alcance

- **El motor no se toca.** `proyectar` (E2.2) y su golden `GOL-PRE-03` están **anclados**; el dashboard los
  **consume**. No hay golden nuevo de engine.
- **Sin cálculo en cliente.** La skin **no** re-mide ni re-valora ni re-proyecta: lee el JSON de proyección
  precomputado. Si algún total no casa con `GOL-PRE-03`, el fallo se corrige en el emisor/engine, **no** en el
  cliente.
- **El export firmable NO entra en v0.** El muro de cobro (export de la proyección con dos llaves) es **gancho
  forward**. La vista es «propone», no certifica (chip `data-state`, regla `isCertified`).
- **Comparar dos ofertas** (dos presupuestos lado a lado) = **post-v0** (D-DV-2): v0 compara ejes y cortes de
  UNA medición.
- **El eje/corte GuBIM y cortes avanzados**: v0 expone Espacial + Funcional + Uniclass (los de `GOL-PRE-03`);
  GuBIM = forward.
- **El design system definitivo** (hex/tono): semilla en este change; lo fija el design system (Ola 3).
- No se toca el eje coste/carbono, ni los packs, ni el pliego, ni el esquema, ni las golden ancladas.

## Impacto en gobierno — «propone» (no dispara ninguna llave en v0)

- **La skin es «propone»:** presenta, agrega, compara, resalta. **No dispara ninguna de las dos llaves.** La
  proyección que muestra ya está firmada aguas arriba (`GOL-PRE-03`, Llave 1 + merge de JM).
- **El muro de cobro (dos llaves) vive en el export firmable**, que queda **fuera de v0** (gancho forward). La
  barra de estado y el chip `data-state` dejan claro «la IA/el motor proyecta · el técnico firma el export».
- **Naturaleza `apps/` (revisión normal, Llave 1 del visor):** la UI, la lógica de presentación y el test E2E.
  No toca `packages/contracts` ni `packages/golden` (no es contract-first: `proyectar` ya está anclada).

**Definición de hecho.** `pnpm -r typecheck` + `pnpm -r build` + `pnpm -r test` (Vitest) VERDE en lo afectado
del visor; **golden del visor/`core` intacta** (skins/selección/`data-state` sin regresión); el test de
aceptación reproduce los totales/grupos de `GOL-PRE-03`. El loop TS corre en la **máquina de JM**
(pnpm/symlinks no van por el mount). Merge/firma = JM (Llave 2).
