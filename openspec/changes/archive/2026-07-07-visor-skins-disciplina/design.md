# Diseño técnico · Skins del visor por disciplina (Slice 1)

> Complementa `proposal.md`. Fija la API del módulo `skins.ts`, el mapa canónico provisional de
> color por clase y las decisiones (resueltas y diferidas). Gobernado por `frontend-standards.md`
> (TS 5.5 ESM, módulos pequeños de una responsabilidad, tipado estricto = puerta del CI).

## 1. Módulo nuevo `apps/visor/src/skins.ts` (dominio puro)

Responsabilidad única: **datos de la skin y su derivación** (mapa disciplina→clases, acento,
color categórico por clase, leyenda por intersección). Sin `three`, sin `web-ifc`, sin estado:
funciones puras y deterministas, unit-testables en `vitest` headless.

```ts
/** Disciplinas soportadas en Slice 1 (se ampliará: instalaciones, obras-lineales, puentes). */
export type Disciplina = "diseno" | "estructuras";

/** Definición estática de una skin de disciplina. */
export interface SkinDisciplina {
  readonly id: Disciplina;
  readonly nombre: string;            // "Diseño", "Estructuras" (con tilde, ES)
  readonly acento: string;            // color de acento CSS: "#2f6bed", "#e07a4f"
  readonly clases: readonly string[]; // clases IFC del dominio, forma web-ifc MAYÚSCULAS
}

/** Mapa estático canónico disciplina → skin. Única fuente de verdad de Slice 1. */
export const SKINS: Readonly<Record<Disciplina, SkinDisciplina>>;

/** Color categórico canónico por clase IFC (mapa por TIPO, NO rampa del acento).
 *  Determinista y estable. Clase no mapeada → color de reserva neutro. */
export function colorPorClase(ifcClass: string): { r: number; g: number; b: number };

/** Una entrada de la leyenda de la skin (clase presente en el modelo ∩ dominio). */
export interface EntradaLeyenda {
  readonly ifcClass: string;                        // "IFCWALL"
  readonly count: number;                           // conteo en el modelo
  readonly color: { r: number; g: number; b: number }; // color categórico (0..1)
}

/** Leyenda de la skin = intersección del mapa de dominio con las clases presentes.
 *  `presentes` es la salida de `viewer.classes()`. Orden estable (el del mapa de
 *  dominio, filtrado por presencia). Las clases presentes fuera del dominio se omiten. */
export function leyendaSkin(
  d: Disciplina,
  presentes: ReadonlyArray<{ ifcType: string; count: number }>,
): EntradaLeyenda[];
```

**Colores en 0..1** para encajar con `Viewer.setColorByClass({r,g,b})` sin conversión en el
llamador. El acento va en CSS (`#hex`) porque pinta chrome de UI (pastilla/dock), no mallas.

## 2. Mapa estático disciplina → clases (Slice 1)

Tomado del §4 del brief e intersecado con `ELEMENT_TYPES` de `ifc-loader.ts` (lo que el visor
sabe cargar hoy). Forma web-ifc (MAYÚSCULAS, como devuelve `classes()`):

| Disciplina | Acento | Clases IFC del dominio |
|---|---|---|
| **Diseño** (`diseno`) | `#2f6bed` | `IFCWALL`, `IFCWALLSTANDARDCASE`, `IFCSLAB`, `IFCWINDOW`, `IFCDOOR`, `IFCROOF`, `IFCCOVERING`, `IFCCURTAINWALL` |
| **Estructuras** (`estructuras`) | `#e07a4f` | `IFCCOLUMN`, `IFCBEAM`, `IFCSLAB`, `IFCFOOTING`, `IFCMEMBER`, `IFCPILE`, `IFCPLATE` |

Notas: `IFCSPACE` no está en `ELEMENT_TYPES` (no se carga como malla hoy) → se deja fuera del
mapa de Diseño en Slice 1 y se recupera cuando el árbol funcional/espacios entre (slice
posterior). `IFCSLAB` es compartido (forjado en ambas disciplinas): su color categórico es único;
la pertenencia a una u otra skin la decide el mapa de dominio, no el color.

## 3. Mapa canónico provisional de color por clase (categórico)

Colores distintos por clase, legibles sobre el fondo Pizarra fría `#12151b`. **Provisional**: la
versión definitiva la fija el design system (Ola 3, §6.7). Reserva para clase no mapeada = gris
neutro `(0.55, 0.55, 0.58)` (coherente con el gris de «sin coste» de `viewer.setCostHeatmap`).

| Clase IFC | Hex (semilla) |
|---|---|
| IFCWALL / IFCWALLSTANDARDCASE | `#c9d1d9` |
| IFCSLAB | `#8b9dc3` |
| IFCWINDOW | `#5bc8e6` |
| IFCDOOR | `#d9a05b` |
| IFCROOF | `#b05be6` |
| IFCCOVERING | `#7e8aa2` |
| IFCCURTAINWALL | `#5be6c8` |
| IFCCOLUMN | `#e0574f` |
| IFCBEAM | `#e0a24f` |
| IFCFOOTING | `#9e6b3f` |
| IFCMEMBER | `#e0d24f` |
| IFCPILE | `#a24f2a` |
| IFCPLATE | `#c0c04f` |
| (no mapeada) | gris `#8c8c95` |

El mapa vive en `skins.ts` como tabla de datos; el test ancla el contrato (determinismo + reserva
+ distinción), no cada hex, para que el design system pueda re-teñir sin romper la spec.

## 4. Cableado al `Viewer` (fino, reutiliza lo existente)

La skin **no añade parámetros a la ingesta**. La aplicación de la skin es una operación de
presentación sobre un modelo ya cargado, componiendo funciones puras con la API pública:

```ts
// pseudocódigo del cableado (demo / capa de UI; no en skins.ts)
const leyenda = leyendaSkin(disciplina, viewer.classes());
for (const e of leyenda) viewer.setColorByClass(e.ifcClass, e.color); // color categórico
// acento -> CSS var de la pastilla/dock: SKINS[disciplina].acento
```

`resetColors()` (ya existe) revierte al color web-ifc. Conmutar de disciplina = `resetColors()` +
recomputar leyenda + re-pintar. Toggle de visibilidad por clase = `setVisibilityByClass` con la
clase de la leyenda. Nada de esto recalcula geometría ni toca el modelo neutro.

## 5. Superficie pública (`src/index.ts`)

Se añaden a los `exports` del paquete (parte de la API del visor):

```ts
export { SKINS, colorPorClase, leyendaSkin } from "./skins.js";
export type { Disciplina, SkinDisciplina, EntradaLeyenda } from "./skins.js";
```

## 6. Decisiones

**Resueltas en este slice** (a ratificar por JM; se anotarán como V-nuevas en
`apps/visor/DECISIONES.md`):

- **D-SK-1 · Fuente de clases = mapa estático ∩ presentes.** La lista por disciplina es un mapa
  estático de dominio, intersecado con `viewer.classes()` del modelo. Resuelve §6.3 con la
  recomendación del propio mockup (no derivar solo del modelo, no listar clases del dominio
  ausentes).
- **D-SK-2 · Color por clase = categórico, no rampa.** Mapa por tipo IFC, separado del acento.
  Resuelve §6.7 y prevalece sobre la redacción «rampa» del §7 (que queda como texto heredado del
  mockup). El acento tiñe chrome de UI; las mallas se tiñen por clase.
- **D-SK-3 · `skins.ts` es dominio puro.** Sin three/web-ifc; el cableado al `Viewer` vive en la
  capa de UI/demo. Mantiene el núcleo unit-testable headless y la responsabilidad única.
- **D-SK-4 · Alcance Slice 1 = Diseño + Estructuras.** Las dos disciplinas de modelo de edificio
  ya soportadas por `ELEMENT_TYPES`. El `type Disciplina` se amplía en slices posteriores.

**Diferidas (no se tocan aquí):** naming de Psets (§6.1), invocación al engine desde el dock
(§6.2), tono de fondo token único (§6.6), mapa de color definitivo del design system (§6.7),
clasificación bsDD (§6.8), idealización como overlay conmutable (§6.5), árbol por PK/
`stationMetric` (§6.4).

## 7. Riesgos y mitigación

- **Deriva de color con el design system (Ola 3):** el test ancla el contrato (determinismo +
  reserva), no los hex; re-teñir no rompe la spec. La tabla de hex es semilla, no compromiso.
- **`IFCSLAB` compartido entre disciplinas:** su color es único por clase; la pertenencia la
  decide el mapa de dominio. Sin ambigüedad en el pintado.
- **Clases presentes fuera del dominio:** `leyendaSkin` las omite (no las pinta ni lista). El
  resto del modelo conserva su color web-ifc hasta que se elija otra skin.
