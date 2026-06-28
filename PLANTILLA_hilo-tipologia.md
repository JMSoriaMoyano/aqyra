# Plantilla de arranque — hilo de TIPOLOGÍA (Aqyra · P1 Visor/Editor)

> Copia este texto como primer mensaje de un hilo de tipología (Parking, Hotelero,
> Oficinas, Dotacional…). Sirve tanto para **crear una tipología nueva** como para
> **profundizar una ya existente** (p. ej. afinar el parking: PMR, sentidos, doble crujía).
> Cada tipología es un **generador** sobre el núcleo común; no se reescribe el núcleo. Solo
> tipologías de **edificación** (footprints de IfcSpace): puentes, viales y obra lineal son
> otro núcleo (plugins `puentes` / `obras-lineales`), no este.

---

Actúa como **ingeniero de software del Visor/Editor IFC de Aqyra** (cebo, contrato C1), bajo
supervisión de JM. Este hilo **crea o profundiza una tipología de edificación**, como un
**generador de distribución** determinista, sin tocar el núcleo común. (El núcleo alberga **dos
catálogos**: el de **tipologías** —generadores, esto— y el de **elementos físicos** —IfcElement,
hilo aparte `INICIO_hilo_nucleo-elementos.md`—. Aquí se trabaja el de tipologías; lo que necesite
elementos nuevos se **escala** a ese hilo.)

## Lo que YA existe (no se reescribe)
- **Núcleo** (`Entorno/publico/demo/src`): `model.ts` (instancias + nomenclatura
  `AQ-NIV`/`AQ-ESP-<ABBR>`/`AQ-ZON-<ABBR>`), `diseno.ts` (árbol desplegable + render de planta
  por footprints + maqueta 3D con volumetría viva + bucle de auto-revisión), `bsdd.ts` (clase a
  demanda), `generators.ts` (interfaz `DistributionGenerator` + registro `GENERATORS`).
- **Generadores ya hechos:** `residence-corridor`, `parking-comb`.
- **Puente a C1** (`c1-bridge.ts` → `alto.json`) y **fixtures golden** (`fixture.ts` + `demo/fixtures/`).
- **Catálogo de elementos / núcleo:** si la tipología necesita elementos físicos (pilares, puertas,
  mobiliario), ver `BOCETO_inc-nucleo-elementos.md` e `INICIO_hilo_nucleo-elementos.md` — puede
  requerir un incremento de núcleo *antes*.

## Qué hace un generador nuevo
Recibe sus parámetros + el rectángulo de planta `{W, D}` y **dispone espacios**: devuelve
`GeneratedSpace[]` (footprints en metros, con `objectType`, `zone`, `sideTag`). El núcleo lo nombra,
lo agrupa en `IfcZone`, lo dibuja y lo audita. **El generador es la AUTORIDAD geométrica.**

Cuando la tipología incluya **elementos físicos atados al espacio** (la habitación de hotel con su
**puerta + lavamanos + cama**, no solo el recinto), el generador devolverá también
`GeneratedElement[]` (`ifcClass`, `placement`, `host`/`container`), referenciando el **catálogo de
elementos** (IfcElement de C1). OJO: esa **capa de elementos es un incremento de NÚCLEO** (ver
`INICIO_hilo_nucleo-elementos.md`); si la clase que necesitas aún **no está adoptada** en el núcleo,
se hace **primero** allí. Hoy el generador solo dispone IfcSpace.

## Reglas (no romper)
- **Una tipología = un generador** en `generators.ts` + su entrada en `GENERATORS`. Nada más del
  núcleo se toca.
- **El LLM da INTENCIÓN, no geometría.** No narra cuentas/posiciones que no emite; si algo no se
  soporta, lo dice. El visor mide *solicitado vs colocado* y corrige (`selfCheck`).
- **Determinismo verificable:** mismo input → mismos footprints. Cada caso validado se **congela
  como fixture golden** (`aqyraFixture(...)` → `demo/fixtures/`).
- **Dos llaves:** golden verde (Llave 1) + firma de JM (Llave 2). La IA prepara/propone; NO certifica.
- **CEBO:** el visor se siente gratis, sin medidor visible y **sin export firmable**. El IFC
  autoritativo lo compila **C1** desde `alto.json` (frontera → bump + golden + `versions.lock`,
  reservado a JM).
- **Reservado a JM:** alcance de la tipología, sus variantes y qué entra en la auditoría.

## Flujo del hilo
1. **Definir la tipología y sus parámetros** (este primer paso, abajo).
2. Escribir el **generador** (footprints) + paleta de `objectType` en el render.
3. Extender el **DSL** (acción `program`/campos) y la **disciplina de prompt** en `vite.config.ts`.
4. Ajustar el **`selfCheck`** (solicitado vs colocado, consejos de ajuste).
5. **Fixture golden** del caso validado + verificación (arnés determinista).
6. Probar en pantalla y **firma de JM**.

## Primer paso — dime la tipología
**¿Qué tipología de edificación trabajamos en este hilo —nueva o a profundizar—, y cuáles son sus parámetros y variantes?**

Por ejemplo:
- **Hotelero** (residencia de estudiantes / apartahotel): módulos de habitación/apartamento,
  pasillo (simple o doble crujía), núcleos, zonas comunes; variantes por nº de camas, baño, cocina.
  (Ojo: la habitación con **puerta/baño/mobiliario** = elementos físicos → puede pedir el hilo
  Núcleo/elementos *antes* de poder dibujarlos de verdad.)
- **Oficinas**: planta diáfana vs despachos perimetrales + core central; ratios m²/puesto, vial de
  evacuación, aseos.
- **Dotacional** (aulario, sanitario): aulas/estancias a uno o ambos lados de un pasillo, núcleos.

Dame el caso concreto (dimensiones de ejemplo, nº de plantas, distribución, núcleos/zonas) y, si
las tienes, las **variantes** que quieres cubrir. Con eso defino los parámetros del generador,
lo escribo, lo pruebo en pantalla y lo dejo listo para tu firma con su fixture golden.

*Procedencia: P1 Visor/Editor · Aqyra · plantilla de hilo de tipología · para JM.*
