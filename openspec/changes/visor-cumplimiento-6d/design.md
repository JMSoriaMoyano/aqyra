# Diseño · El visor pinta el veredicto de cumplimiento (6D)

> Cómo se implementa `visor-cumplimiento-6d`. Espeja el 5D (C5 write-back D11–D15 + visor h4).

## 1. El Pset de cumplimiento (D-6D-1)

El write-back del cumplimiento es análogo al 5D, pero el modelo de coste 5D tenía una entidad
OpenBIM canónica (`IfcCostSchedule`); el cumplimiento **no** tiene una entidad estándar, así que
se usa un **Property Set** custom con prefijo de marca:

```
Pset_Aqyra_Cumplimiento           (IfcPropertySet, asignado por IfcRelDefinesByProperties)
  Resultado          IfcLabel     ∈ {cumple, no-cumple, no-aplica, no-verificable}   (peor caso)
  Exigencia          IfcLabel     id de la exigencia dominante (la que fija el peor caso)
  DocumentoBasico    IfcLabel     DB-SI / DB-SUA / DB-HE / … / RSCIEI
  Apartado           IfcLabel     referencia (pack+apartado)
  Pack               IfcLabel     "CTE/2019"
  MotivoNoVerificable IfcText     solo si Resultado = no-verificable (D4)
```

Un **Pset por exigencia** adicional (`Pset_Aqyra_Cumplimiento_<EXIG>`) opcional lleva el detalle
por exigencia cuando un elemento cae bajo varias; el `Pset_Aqyra_Cumplimiento` "raíz" lleva el
peor caso agregado que el visor colorea (D-6D-2). En v0 basta el Pset raíz + un detalle mínimo.

Determinismo (como el 5D): orden de escritura estable, sin timestamps salvo los deterministas de
cabecera SPF ya resueltos en el derivado; escribir 2× → bytes idénticos.

## 2. Granularidad: de `por_modelo` a elementos (D-6D-2)

El `veredicto.exigencias[].por_modelo[<modelo>].resultado` da el resultado por **sub-modelo
federado**. El manifiesto del Maestro (C4) mapea `modelo → elementos` (los GlobalIds de cada
sub-modelo dentro del derivado). El write-back:

1. Para cada exigencia, toma `por_modelo` (o el resultado global si no hay desglose).
2. Para cada sub-modelo, atribuye su `resultado` a todos sus elementos.
3. Por elemento, agrega el **peor caso** entre las exigencias que lo tocan:
   `no-cumple` ≻ `no-verificable` ≻ `cumple`; `no-aplica` es neutro (no empeora ni mejora; si
   todas son `no-aplica`, el elemento queda `no-aplica`).

Invariante: todo elemento del derivado recibe exactamente un `Resultado` en el Pset raíz.

## 3. Lectura en el visor (espeja `cost.ts`)

`apps/visor/src/compliance.ts` (puro de datos, sin three.js/WASM en su núcleo testable):

```ts
export type ResultadoCumplimiento = "cumple" | "no-cumple" | "no-aplica" | "no-verificable";
export interface ElementoCumplimiento { globalId: string; resultado: ResultadoCumplimiento;
  exigencia?: string; }
export interface CumplimientoModelo {
  porElemento: Map<string, ElementoCumplimiento>;
  resumen: Record<ResultadoCumplimiento, number>;
}
export function leerCumplimiento(api: IfcAPI, modelID: number): CumplimientoModelo
```

Lee `Pset_Aqyra_Cumplimiento` con web-ifc igual que `cost.ts` lee `IfcCostSchedule`. El viewer
mapea `resultado → color` y pinta con la superficie ya existente (`setColorByClass` no aplica;
se usa un `setColorByElement`/equivalente — si no existe, se añade en la capa de viewer como en
el heatmap 5D). Reversible (`resetColors`).

## 4. Colores (D-6D-4)

`cumple` `#2e9e5b` (verde) · `no-cumple` `#d64545` (rojo) · `no-aplica` `#8a8f98` (gris) ·
`no-verificable` `#e0a43a` (ámbar). Leyenda de 4 entradas con su conteo (`resumen`).

## 5. Golden (D-6D-3)

`run_case` federa+deriva las fixtures con el Maestro del C4-FED-06, verifica (C3, pack CTE/2019,
5 exigencias de GOL-CTE-01), escribe el Pset y ancla:
- **Determinismo**: `escribir_cumplimiento` 2× → bytes idénticos.
- **Semántica**: los `Resultado` del Pset casan con el veredicto de `GOL-CTE-01` proyectado a
  elementos por la regla del peor caso.
Sin aflojar la golden: un fallo se corrige en el código.

## 6. Riesgos / notas

- EOL/CRLF en fixtures del visor: anclar md5 en **LF** (lección Fase IV·h4: `apps/visor/fixtures`
  no tiene `-text`; git normaliza a LF).
- `web-ifc` versión exacta (0.0.68) — no cambiarla.
- Si el viewer aún no tiene color por elemento (solo por clase), se añade la mínima superficie en
  `viewer.ts` reutilizando el mecanismo del heatmap 5D.
