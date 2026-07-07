# Diseño técnico · Selección + estado de dato (Slice 2)

> Complementa `proposal.md`. Fija la API de `estadoDato`, el cableado al panel y las decisiones.
> Gobernado por `frontend-standards.md` (TS 5.5 ESM estricto, módulos de una responsabilidad).

## 1. `estadoDato` en `src/data-state.ts` (dominio puro)

Extiende el módulo existente `data-state.ts` (que ya define `DataState`, `dataStateStyle`,
`isCertified`, `exportStamp`). Se AÑADE una función pura que deriva el estado de un elemento a
partir de los **nombres de sus Property Sets**:

```ts
/** Patrón de Psets de RESULTADO calculados por un motor del ecosistema (Slice 2). El naming
 *  definitivo se reconcilia en el design system (§6.1 del brief); aquí se aceptan las variantes
 *  vigentes: `Pset_AqyraStructural`, `Pset_*Resultado*` (Estructurando/Aqyra). */
const RESULTADO = /Resultado|AqyraStructural/i;

/**
 * Deriva el `DataState` de un elemento a partir de los NOMBRES de sus Psets (propone puro):
 * - con un Pset de resultado de un motor → `computed` (lo calculó el motor, sin firmar);
 * - sin él → `proposal` (aún es una propuesta).
 * `qa-passed`/`verified-signed` NO se infieren aquí (los acuña el flujo de firma, D-021): si el
 * dato ya los porta, se pasan como `explicito` y esta función los respeta.
 */
export function estadoDato(
  psetNames: readonly string[],
  explicito?: DataState,
): DataState {
  if (explicito) return explicito;
  return psetNames.some((n) => RESULTADO.test(n)) ? "computed" : "proposal";
}
```

Pura, determinista, testable sin WASM. No decide el verde: el verde sigue gobernado por
`isCertified` (solo `verified-signed`).

## 2. Superficie pública (`src/index.ts`)

```ts
export { dataStateStyle, isCertified, exportStamp, stampIfcText, estadoDato } from "./data-state.js";
```

(El resto de exports de `data-state` ya están.)

## 3. Cableado al panel de Selección (demo)

El panel `#props` ya muestra clase · GlobalId · Psets al seleccionar (resalte ámbar `#ff8a3d` ya
existente). Slice 2 añade el **chip de estado** encima de los Psets:

```ts
// en muestraElemento(...), tras leer rec.psets:
const estado = estadoDato(Object.keys(rec.psets));
const st = dataStateStyle(estado);
// chip: st.label con fondo/borde st.color; si !st.certified, marca de "no verificado".
```

El chip se pinta como una pastilla con `st.color` (los colores ya definidos en `STYLES`:
PROPUESTA gris, NO VERIFICADO rojo, QA OK ámbar, VERIFICADO verde). Sólo `verified-signed`
(certificado) va sin marca de agua.

## 4. Decisiones

**Propuestas (a ratificar por JM; se anclarán como V-nueva en `apps/visor/DECISIONES.md`):**

- **D-SL2-1 · Estado derivado de la presencia de Pset de resultado.** `computed` si el elemento
  tiene un Pset de resultado de un motor; `proposal` si no. Es la señal disponible hoy en el
  modelo y respeta D-021 (el visor no acuña `qa-passed`/`verified-signed`). Alternativas: leer una
  propiedad concreta del Pset, o un estado a nivel de modelo — si JM lo prefiere, se ajusta `estadoDato`.
- **D-SL2-2 · Chip en la barra lateral, no flotante.** El panel de Selección permanece en la
  barra; el panel flotante/arrastrable del mockup es pulido posterior (UX backlog), no Slice 2.
- **D-SL2-3 · El visor no acuña el verde.** `isCertified` sigue siendo la única fuente del trato
  «certificado»; `estadoDato` nunca devuelve `verified-signed` por inferencia (solo si viene
  `explicito`). Coherente con D-021·B y con «la IA propone, nunca certifica».

**Diferidas:** panel flotante/draggable, naming canónico de Psets de resultado (§6.1, design
system Ola 3), origen `qa-passed`/`verified-signed` desde el CDE/flujo de firma.

## 5. Riesgos

- **Naming de Psets de resultado no reconciliado (§6.1):** el patrón `RESULTADO` acepta las
  variantes vigentes; cuando se fije el prefijo canónico, se actualiza el patrón (el test ancla el
  comportamiento, no el regex exacto).
- **Falsos `proposal`:** un elemento calculado cuyo Pset no case el patrón saldría `proposal`. Se
  mitiga aceptando las variantes conocidas y dejando el `explicito` como escape.
