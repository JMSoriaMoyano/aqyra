# Boceto de alcance — Incremento de NÚCLEO: catálogo de elementos físicos (IfcElement) vía C1

> Primer salto del núcleo del Visor de "solo estructura espacial" (IfcSpace/IfcZone) a
> "espacial **+ elementos físicos**". No es un hilo de tipología; es un incremento de núcleo
> (afecta a todas las tipologías). Se hace **adoptando el catálogo de C1**, no reinventando IFC.

## 0. Encuadre — dos catálogos, un motor
El núcleo (el motor) es **uno**. Dentro viven **dos catálogos**:
- **Catálogo de tipologías** = los generadores (parking, hotelero…) → **disponen espacios**.
- **Catálogo de elementos** = IfcColumn, IfcWall, IfcDoor, IfcSanitaryTerminal… → los `IfcElement`
  físicos con **identidad**.

Clave (mismo movimiento que con los espacios): la identidad del elemento es **DATO, no código**.
No se escribe un "generador de pilar" y otro de "puerta" (eso es la trampa de plantillas), sino
**UN elemento genérico** `ElementInstance { ifcClass, placement, … }` respaldado por un catálogo.

## 1. El catálogo ya existe — en C1
`narracion-a-ifc/scripts/catalogo_ifc.py` deriva del esquema IFC4X3 **~150 clases concretas de
IfcElement** (11 grupos), cada una con **arquetipo geométrico, PredefinedType, Psets `Pset_*Common`
y URI bsDD** (y `generar_galeria.py` da una galería navegable). **No hay que construir la batería;
hay que adoptarla.** El cebo aporta una **identidad ligera** (clase + colocación + glifo esquemático
+ clasificación) y delega en C1 la geometría real y los Psets. Híbrido: cebo previsualiza, C1 autora.

## 2. Quién coloca los elementos (dos fuentes, un elemento genérico)
- **Sistemas transversales** del edificio: retícula → IfcColumn; envolvente → IfcWall; forjados →
  IfcSlab. Transversales a la tipología (todas los quieren).
- **El generador de tipología**: la habitación de hotel emite su **puerta + lavamanos + cama**; el
  parking **lee la retícula** para no aparcar sobre un pilar. El generador pasa de devolver "solo
  espacios" a devolver **espacios + sus elementos**.

```ts
// la salida del generador se amplía:
interface GeneratedElement {
  ifcClass: string;        // IfcColumn | IfcWall | IfcDoor | IfcSanitaryTerminal | …  (DATO)
  objectType?: string;
  placement: Placement;    // punto | línea | polígono (según arquetipo del catálogo)
  level?: string;
  host?: string;           // anfitrión (la puerta VA EN este muro) — capa relacional
  container?: string;      // contenido en (este lavamanos está EN esta habitación)
}
// GeneratedSpace[]  +  GeneratedElement[]  → el núcleo nombra, dibuja, clasifica y puentea ambos.
```

## 3. La capa de RELACIONES = lo realmente nuevo del núcleo
La identidad de un elemento no es solo clase + posición; incluye **relaciones IFC**:
- **Contención**: todo elemento está *en* un espacio/planta → `IfcRelContainedInSpatialStructure`.
- **Anfitrión**: una puerta/ventana va *dentro de* un muro → hueco (`IfcOpeningElement` +
  `IfcRelVoidsElement`) + relleno (`IfcRelFillsElement`).

La parte **geométrica** de esas relaciones (restar el hueco, encajar la hoja) **ya la resuelve C1**
(`muros[].huecos`). Lo que el núcleo del cebo modela es la **identidad relacional** (`host`,
`container`). Esa capa es la capacidad de núcleo de verdad nueva — y donde se concentra la riqueza.

## 4. Modelo de datos (núcleo)
```ts
interface ElementInstance {
  code: string;            // AQ-PIL-Pnn-xx | AQ-PUE-… | AQ-LAV-…
  ifcClass: string;        // del catálogo (dato)
  objectType?: string;
  placement: Placement;    // punto/línea/polígono (m)
  section?: { w: number; d: number };
  level: string;
  host?: string; container?: string;   // capa relacional
  uriBsdd: string;
}
// StoreyInstance gana `elements: ElementInstance[]`. El árbol gana ramas por ifcClass
// (Elementos · IfcColumn (N), · IfcDoor (N)…). bsDD por clase a demanda ya funciona.
```

## 5. Primer slice mínimo — IfcColumn de una retícula
Aterrizar el patrón con UNA clase, la más transversal y de mayor apalancamiento:
- **Sistema transversal** `buildGrid({origen, sep_x, sep_y, sección}, {W,D}) → IfcColumn[]`
  (nudos dentro de W×D, determinista → golden + fixture).
- Modelo + render (puntos en planta + verticales en la caja 3D) + rama del árbol + detalle (sección
  + bsDD) + acción `columns` en el DSL.
- **Puente C1**: mapear a `reticulas_pilares` / `elementos` — primitivos que C1 **ya tiene** → la
  frontera es MENOR que la de `espacios` (no hay primitivo nuevo; golden sobre la salida de C1).
- Sin muros, sin forjados, sin acoplamiento todavía. Muros/forjados/carpintería = **clones de este
  molde** (misma `ElementInstance`, otra `ifcClass`, otro arquetipo del catálogo).

## 6. Acoplamiento (elementos ↔ espacios) — por fases
- **Fase A (este incremento):** modelar + dibujar + clasificar + puentear columnas. El generador de
  parking las **ignora** (pueden solaparse).
- **Fase B (después):** el generador **lee** la retícula y recorta plazas en los nudos. "El generador
  lee el núcleo" es la señal de acoplamiento real, y va medido aparte.

## 7. Coste (es núcleo, no un fichero)
`model.ts` (ElementInstance + elements en plantas + buildGrid + nomenclatura), `diseno.ts` (render
de columnas + ramas del árbol + acción), `vite.config.ts` (acción `columns` + prompt), `c1-bridge.ts`
(`reticulas_pilares`/`elementos`), `fixture.ts` (snapshot con elementos). ~5 ficheros del espinazo.

## 8. Verificación / golden
- Arnés de `buildGrid` (nudos correctos, nomenclatura única).
- Fixture del caso (retícula 8×8 en 120×24) → snapshot con recuento de columnas.
- Golden de C1: el `alto.json` con `reticulas_pilares` compila columnas válidas (lo corre JM).

## 9. Decisiones reservadas a JM — ✅ DECIDIDAS (JM, 2026-06-28)

> **Write-back de coordinación (2026-06-28):** JM cerró las 6 en el hilo de P1; la IA las transcribe aquí desde lo ya implementado en `Entorno/publico/demo/src/model.ts`. La IA transcribe, JM decidió.

1. **Clases del primer slice → solo `IfcColumn`** (1ª opción).
2. **Identidad relacional (`host`/`container`) → DIFERIDA** (después del slice de columnas).
3. **Retícula → a nivel de EDIFICIO, con el pilar repitiéndose por planta** — corrección de JM: NO "una columna = un objeto" único; el pilar se REPITE por planta. Reflejado en `model.ts` (l.86).
4. **Acoplamiento columnas↔plazas → Fase B** (no en este incremento).
5. **Defaults → sección 0,40×0,40, HA-30** (confirmados). `DEFAULT_SECTION` en `model.ts`.
6. **Ejes → lógicos (cada columna lleva su cruce de ejes) SIN emitir `IfcGrid` propio.** Reflejado en `model.ts` (l.84).

Estado: cerradas las 6 y, según el panel (28-jun), el slice de **columnas + forjados (IfcSlab) está FIRMADO** (golden 13/13, dos llaves ✔). En cola: parking en peine (`parking.golden` 7/7).

<details><summary>Preguntas originales (traza)</summary>

- ¿Solo IfcColumn primero (recomendado) o más clases del catálogo de golpe?
- ¿Identidad relacional (`host`/`container`) ya en este slice, o tras IfcColumn (que no necesita host)?
- ¿Retícula a nivel de edificio (columnas que pasan plantas) o por planta? (rec.: edificio.)
- ¿Acoplamiento columnas↔plazas en este incremento o en Fase B? (rec.: Fase B.)
- Defaults de sección/material (0,40×0,40, HA-30 de C1) — confirmar.
- ¿IfcGrid de ejes (A/B/C · 1/2/3) ligado a las columnas, o columnas sueltas por sep_x/sep_y?
</details>

*Procedencia: P1 Visor/Editor · Aqyra · boceto de incremento de núcleo (catálogo de elementos) · para dimensionar y firmar (JM).*
