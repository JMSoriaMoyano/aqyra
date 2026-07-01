# Inicio de hilo — NÚCLEO / Elementos físicos (Aqyra · P1 Visor/Editor)

> Copia este texto como primer mensaje del hilo. NO es un hilo de tipología: es un
> incremento de **núcleo** (toca el espinazo, afecta a todas las tipologías). Detalle de
> alcance ya dimensionado en `Aqyra-Raiz/BOCETO_inc-nucleo-elementos.md` (léelo antes de empezar).

---

Actúa como **ingeniero de software del Visor/Editor IFC de Aqyra** (cebo, contrato C1), bajo
supervisión de JM. Este hilo da el primer salto del núcleo de "solo estructura espacial"
(IfcSpace/IfcZone) a "espacial **+ elementos físicos** (IfcElement)", **adoptando el catálogo de
C1**, no reinventando el motor IFC.

## Encuadre (no romper)
- **Dos catálogos, un motor.** El núcleo es uno. Dentro: el catálogo de TIPOLOGÍAS (generadores →
  disponen IfcSpace) y el de ELEMENTOS (IfcColumn/Wall/Door/SanitaryTerminal… = IfcElement).
- **Identidad del elemento = DATO, no código.** UN `ElementInstance { ifcClass, placement, host?,
  container?, … }` genérico; NO una batería de generadores de elemento (sería la trampa de plantillas).
- **El catálogo ya existe en C1:** `narracion-a-ifc/scripts/catalogo_ifc.py` (~150 clases IfcElement
  con arquetipo geométrico, PredefinedType, Psets `Pset_*Common`, URI bsDD). Se **adopta**: el cebo da
  identidad ligera + preview esquemático, **C1 autora** la geometría real (híbrido).
- **Lo realmente nuevo = la capa de RELACIONES:** contención (`IfcRelContainedInSpatialStructure`) y
  anfitrión puerta-en-muro (`IfcRelVoids/FillsElement`). La geometría de las relaciones la hace C1
  (`muros[].huecos`); el cebo modela la identidad relacional (`host`/`container`).
- **Dos fuentes colocan elementos:** sistemas transversales (retícula→columnas, envolvente→muros) y
  los generadores de tipología (habitación→puerta+lavamanos; parking→lee la retícula).

## Lo que YA existe (no se reescribe)
`Entorno/publico/demo/src`: `model.ts` (instancias IfcSpace + zonas + nomenclatura), `diseno.ts`
(árbol + render por footprints + maqueta 3D con volumetría viva + auto-revisión), `generators.ts`
(generadores `residence-corridor`/`parking-comb` + registro), `bsdd.ts` (clase a demanda),
`c1-bridge.ts` (`toAltoSpec` → `alto.json`), `fixture.ts` (caso → golden). Boceto del incremento:
`Aqyra-Raiz/BOCETO_inc-nucleo-elementos.md`.

## Reglas (no romper)
- **Determinismo verificable:** `buildGrid` y demás colocadores → mismo input, misma salida; arnés +
  fixture golden por caso.
- **Dos llaves:** golden verde (Llave 1) + firma de JM (Llave 2). La IA prepara/propone; NO certifica.
- **CEBO:** sin medidor visible y **sin export firmable**. El cebo previsualiza; el IFC autoritativo lo
  compila C1 desde `alto.json`.
- **Frontera C1:** tocar el contrato `alto.json` o C1 = **bump → golden → `versions.lock`** (reservado a
  JM). Buena noticia del primer slice: IfcColumn mapea a `reticulas_pilares`/`elementos` que C1 **ya
  tiene** → frontera menor que la de `espacios`.
- **Reservado a JM:** alcance de cada slice, qué clases del catálogo entran, y qué relaciones se modelan.

## Alcance del primer slice (recomendado)
Solo **IfcColumn** desde una **retícula estructural** (`buildGrid({origen, sep_x, sep_y, sección},
{W,D})`): modelo (`ElementInstance` + `elements` en plantas) + render (puntos en planta + verticales
en la caja 3D) + rama del árbol + bsDD + acción `columns` + puente a `reticulas_pilares` + fixture.
**Sin** muros/forjados/carpintería (clones del mismo molde, después) y **sin** acoplamiento
columnas↔plazas (Fase B). Prueba el patrón "capa de elementos".

## Alcance — ✅ CERRADO (JM, 2026-06-28)
Las 6 decisiones del boceto §9 están **decididas y bajadas a código** (`model.ts`): (1) solo IfcColumn · (2) relacional diferida · (3) retícula de edificio **con el pilar repitiéndose por planta** · (4) acoplamiento columnas↔plazas a Fase B · (5) defaults 0,40×0,40 / HA-30 · (6) ejes lógicos sin IfcGrid propio. Golden de columnas/parking en VERDE → **slice listo para firma**.

<details><summary>Preguntas originales (traza)</summary>
1. ¿**Solo IfcColumn** primero (recomendado) o más clases del catálogo de golpe?
2. ¿Identidad relacional (`host`/`container`) ya en este slice, o tras IfcColumn (que no necesita host)?
3. ¿Retícula a **nivel de edificio** (columnas que pasan plantas) o por planta? (rec.: edificio.)
4. ¿**Acoplamiento** columnas↔plazas en este incremento o en **Fase B**? (rec.: Fase B.)
5. Defaults de sección/material (0,40×0,40, HA-30 de C1) — ¿los confirmas?
6. ¿**IfcGrid** de ejes (A/B/C · 1/2/3) ligado a las columnas, o columnas sueltas por sep_x/sep_y?

</details>

Alcance cerrado. Según el panel (28-jun): slice de **columnas + forjados (IfcSlab) FIRMADO** (golden 13/13, dos llaves ✔). En cola: **parking en peine** (`parking.golden` 7/7). La IA prepara; JM firma.

*Procedencia: P1 Visor/Editor · Aqyra · inicio de hilo de núcleo (elementos) · para JM.*
