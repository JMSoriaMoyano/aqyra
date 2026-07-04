# UX_BACKLOG — el visor abierto (demo y experiencia de usuario)

> **Qué es:** el embalse de fricciones y mejoras de experiencia del visor, capturadas EN EL
> MOMENTO en que se sienten (por JM o por Claude). Anotar cuesta cero; implementar espera
> al **hilo de experiencia** correspondiente.
>
> **Dónde vive (regla 6, cumplida):** este fichero se MUDÓ de `_operativo/UX_BACKLOG_visor.md`
> (gitignored) a `apps/visor/UX_BACKLOG.md` en el PR del primer hilo de UX (Fase III·h4, lote 1)
> y desde entonces VIAJA CON EL PAQUETE (trackeado). Para capturar: «apunta al backlog: …» en
> cualquier hilo, o edita la tabla a mano.
>
> **Reglas de proceso (acordadas 2026-07-03):**
> 1. **Captura continua** — cualquier hilo, cualquier momento; una línea + severidad.
> 2. **Ejecución por lotes** — hilos de UX dedicados; nunca goteo de mini-PRs.
> 3. **Momento** — en las fronteras de fase SI el backlog lo justifica (>8-10 entradas o
>    cualquier `bloquea`); si está flaco, se acumula para la siguiente frontera.
> 4. **Excepción inmediata** — solo lo que ROMPE la demo (precedente: fix wasm PR #23).
> 5. **Frontera dura** — una mejora de UX nunca toca la zona anclada (fixtures, E2E,
>    contratos, golden). Si lo exige, deja de ser mejora: es decisión (D/V) con JM.
> 6. Mudanza CUMPLIDA (ver arriba): trackeado en `apps/visor/UX_BACKLOG.md`.
>
> **Severidades:** `bloquea` (impide usar/enseñar la demo) · `molesta` (fricción real en
> cada uso) · `mejora` (estaría bien). Estado: `abierta` · `en-hilo-X` · `hecha (PR #n)`.

| # | Fecha | Sev. | Observación | Origen | Estado |
|---|-------|------|-------------|--------|--------|
| 1 | 2026-07-03 | molesta | El resaltado de Components del topic BCF (emissive sobre material gris claro) apenas se distingue: al aplicar la cámara D29 no queda obvio QUÉ elementos señala el topic. Valorar color de acento + atenuar el resto (ghost). | Claude, demo 3.1 | hecha (PR #26) |
| 2 | 2026-07-03 | molesta | El árbol espacial no pliega/despliega ni hace scroll-to ni selección al clicar un nodo: con dos ramas ya es largo; con un modelo real será inusable. | Claude, demo 3.1 | hecha (PR #26) |
| 3 | 2026-07-03 | mejora | El panel «Selección» al clicar un elemento solo muestra tipo/GlobalId/expressId — el loader ya sabe leer Psets (`getProperties`): mostrarlos (es el gancho de valor OpenBIM). | Claude, demo 3.1 | hecha (PR #26) |
| 4 | 2026-07-03 | mejora | Tras aplicar la cámara D29 no hay botón «vista general» para volver a encuadrar el modelo completo (hay que orbitar a mano desde un primer plano). | Claude, demo 3.1 | hecha (PR #26) |
| 5 | 2026-07-03 | mejora | Los topics sin viewpoint (R4-GEORREF) no dan feedback visual en la escena al seleccionarlos — al menos indicar «topic a nivel de proyecto, sin cámara» en el panel. | Claude, demo 3.1 | hecha (PR #26) |
| 6 | 2026-07-03 | mejora | Coordenadas EPSG absolutas (~4.6M) en float32 de three.js: riesgo de jitter/precisión visual con modelos grandes — valorar re-base local de la escena (restar el punto base) manteniendo las coordenadas reales en el dato. | Claude, hallazgo 3.1 | abierta (diferida — decisión V6/U1: NO entra en el lote; toca la transformación de coordenadas, roza precisión/E2E) |
| 7 | 2026-07-03 | molesta | El fondo del visor debe ser OSCURO, como había sido hasta ahora (el histórico del cebo); en la demo 3.1 la escena sale sobre fondo claro/por defecto. | JM, demo 3.1 | hecha (PR #26) |
| 8 | 2026-07-03 | molesta | El modelo debería ocupar TODA la pantalla disponible, no el recuadro que ocupa ahora: el canvas queda como una caja fija arriba-izquierda y el resto del viewport se desperdicia (mirar mount/resize del Viewer: el renderer no sigue el tamaño real del contenedor #escena). | JM, demo 3.1 | hecha (PR #26) |
| 9 | 2026-07-03 | molesta | Al clicar un elemento del árbol de estructura espacial debería verse REFLEJADO en el modelo (resaltado/zoom al elemento); hoy el árbol es solo texto pasivo — es la mitad que le falta a la entrada #2 (árbol → escena, además de plegado). | JM, demo 3.1 | hecha (PR #26) |

## Cómo añadir una entrada

Dime «apunta al backlog: …» en cualquier hilo, o edita la tabla a mano. Formato libre;
lo único obligatorio es la severidad y no perder la observación.
