# Cambio · Selección + Propiedades/Psets + chip de estado de dato (Slice 2)

> Change-id: `visor-seleccion-estado` · Capacidad: `visor` (`apps/visor`, `@aqyra/visor`)
> Procedencia: `Aqyra-Negocio/BRIEF_visor-skins-por-disciplina.md` §3 (pasos 4-5) y §7 (Slice 2)
> + mockup v0.6. Naturaleza: **`apps/` (UI)** propone puro. Gobernado por `docs/frontend-standards.md`
> (TDD, Llave 1) y `CLAUDE.md`. Continúa el hilo de skins (Slice 1 MERGEADO).
> Estado: spec redactada (SSD) · pendiente de ratificar D-SL2-1 (derivación del estado) antes del código.

## Por qué

El Slice 1 vistió el modelo por disciplina. El siguiente gancho de valor OpenBIM es **leer el
elemento**: al seleccionar, ver su clase, su GlobalId, sus **Psets** y — sobre todo — el **estado
del dato** (¿es una propuesta?, ¿lo calculó un motor?, ¿pasó la golden?, ¿está firmado?). El chip
de estado hace visible «dónde vive el foso» sin certificar nada: es el vocabulario de las **dos
llaves** llevado al elemento (D-021). El visor **propone**; la firma la acuña el flujo de firma,
no el visor.

## Qué cambia (Slice 2 · mínimo)

- **Estado de dato por elemento** (`data-state.ts`, función NUEVA `estadoDato`): función **pura**
  que deriva el `DataState` de un elemento a partir de los **nombres de sus Psets**. Regla de
  Slice 2 (propone puro): un elemento con un **Pset de resultado** de un motor (p. ej.
  `Pset_AqyraStructural`, `Pset_*Resultado*`) está `computed`; sin él, `proposal`. Los estados
  `qa-passed` y `verified-signed` **NO** se infieren en el visor (los acuña el flujo de firma,
  D-021) — el visor solo los *mostraría* si el dato ya los trae.
- **Chip de estado** en el panel de Selección: usa `dataStateStyle(estado)` (ya existe) para la
  etiqueta y el color del chip (PROPUESTA / NO VERIFICADO / QA OK·SIN FIRMAR / VERIFICADO), con la
  regla dura de `isCertified` (solo `verified-signed` = verde/certificado).
- **Panel de Selección** (demo): al seleccionar (clic en escena o árbol, resalte ámbar
  `#ff8a3d` ya existente), mostrar clase · GlobalId · **chip de estado** · Psets. Reutiliza
  `IfcLoader.getProperties` y el resalte del `Viewer`.

El núcleo (`estadoDato`) es **puro y determinista** (sin three/web-ifc): unit-testable headless.
El resalte ámbar y la lectura de Psets ya existen en el visor (V6/U1, demo actual); Slice 2 añade
el **estado de dato** y lo cablea al panel.

## Qué NO cambia (fuera de alcance de Slice 2)

- **Panel flotante/arrastrable** (mockup): el panel sigue en la barra lateral; hacerlo flotante y
  draggable es pulido posterior (UX backlog), no Slice 2.
- **Inferir `qa-passed`/`verified-signed`**: el visor no los deduce (D-021·B). Solo los muestra si
  el dato los porta explícitamente (gancho para cuando el CDE/flujo de firma los provea).
- **Estructura funcional / Clasificación bsDD / caja de IA / rail de disciplinas**: slices posteriores.
- No se toca `packages/contracts` ni `packages/golden`.

## Impacto en gobierno — propone puro, sin llaves

`apps/visor` puro. **Golden del visor/`core` intacta** (no lee ni reescribe IFC más allá de la
lectura de Psets ya existente; `data-state` es dominio puro). **No dispara la Llave 2**: el visor
**no** acuña `verified-signed` (D-021 — la regla dura de `isCertified` sigue siendo la única
fuente del verde). PR con `pnpm -r typecheck` + `build` + `test` verdes. `versions.lock` inalterado.

**Definición de hecho:** test headless de `estadoDato` verde · typecheck/build/test de lo afectado
verdes · golden intacta · `apps/visor/DECISIONES.md` con la V-nueva (D-SL2-*) · sin Llave 2.

## Decisión a ratificar antes del código

- **D-SL2-1 — Derivación del estado por elemento.** ¿Se deriva `computed` de la **presencia de un
  Pset de resultado** (propuesta de este cambio), o prefieres otra fuente (una propiedad concreta
  del Pset que porte el estado, o un estado a nivel de modelo)? La spec asume la presencia de Pset
  de resultado; se ajusta si JM decide otra.
