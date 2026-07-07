# Cambio · El visor pinta el veredicto de cumplimiento (6D)

> Change-id: `visor-cumplimiento-6d` · Épica Jira: `AQYRAALL-1` (tasks `AQYRAALL-2..5`).
> Capacidades: `engines/cumplimiento` (write-back) + `apps/visor` (`@aqyra/visor`, lectura y
> color) + decisiones de contrato ligeras en `C3-cumplimiento` (Pset, sin esquema nuevo).
> Procedencia: hilo SDD (Aqyra-Raiz), vertical end-to-end pequeña elegida para estrenar el flujo
> opsx sobre el monorepo. Naturaleza: **aditiva** (rama nueva; main/golden/tags intactos).
> Gobierno: dos llaves — Llave 1 (gate verde) + Llave 2 (firma GPG de JM). Estado: **propuesta
> redactada · pendiente de ratificar D-6D-1..4 antes del código.**

## Por qué

El visor ya sabe pintar el **coste 5D** (C5): lee `IfcCostSchedule` del derivado y colorea el
modelo por importe (`apps/visor/src/cost.ts`, Fase IV·h4). El **cumplimiento normativo** (C3) ya
produce un **veredicto por exigencia** (`engines/cumplimiento.verificar()` →
`veredicto-cumplimiento`), pero ese veredicto **no llega al visor**: se queda en un JSON. El
técnico no puede *ver* qué parte del edificio cumple y qué parte no.

Esta vertical cierra ese hueco calcando el patrón, ya probado, del 5D: el engine **escribe** el
resultado de cumplimiento en el modelo derivado como **Pset OpenBIM**, y el visor lo **lee y
colorea** (verde/rojo/gris/ámbar). Es la cuña de adopción de C3 en la superficie del producto —
el "6D" — con riesgo mínimo porque reutiliza contrato+engine+golden de C3 y la arquitectura de
datos del visor.

## Qué cambia

Tres capas finas, aditivas:

1. **Engine (C3)** — `engines/cumplimiento.escribir_cumplimiento(derivado, veredicto) → derivado'`:
   escribe un **Pset de cumplimiento** en los elementos del IFC derivado federado, espejando
   `engines/presupuesto.escribir_coste` (D11–D15 de C5). El engine **abre el derivado, no
   federa** (D7). Determinista: escribir 2× → **bytes idénticos**. `verificar`/`medir` intactos
   (SemVer minor).
2. **Golden** — nuevo caso que ancla el derivado con el Pset escrito, oráculo por **determinismo**
   (escribir 2× = bytes idénticos) + **semántica** (el Pset casa con el veredicto de
   `GOL-CTE-01`). Sin md5 hardcodeado si es frágil por EOL (patrón D14 opción b). Conserva
   íntegros los checks anclados de C3/C4 (más checks, nunca menos).
3. **Visor** — `apps/visor/src/compliance.ts` (módulo NUEVO, puro de datos como `cost.ts`): lee
   el Pset con web-ifc y produce el mapa `porElemento`; el viewer colorea por `resultado`. Demo
   con flag `?6d` (paralela a `?5d`). E2E anclado sobre la fixture del golden.

## Qué NO cambia

- **No se reimplementa C3** ni se federa en el visor. El engine consume el veredicto que
  `verificar()` ya emite.
- **No se amplía la taxonomía** de `resultado` (4 valores cerrados, D4). Forward-open honesto.
- **No se crea un esquema de contrato nuevo**: el Pset es OpenBIM (Property Set estándar), su
  forma se fija por **decisión** en `C3-cumplimiento/DECISIONES.md` (como el 5D usó
  `IfcCostSchedule` canónico + D11–D15, sin esquema propio).
- **No se toca el coste 5D** (`cost.ts`) ni otras zonas del visor. No se toca `packages/golden`
  ni `packages/contracts` firmados existentes (solo se AÑADE).

## Impacto en gobierno — propone puro, sin llaves hasta el cierre

La IA prepara y propone; **no certifica**. El cambio se integra solo con **Llave 1** (gate verde:
golden + typecheck + build + tests) y **Llave 2** (firma GPG de JM en los releases
`cumplimiento-vX.Y.0` y `visor-vX.Y.0`). Zona firmada existente intacta.

## Decisiones a ratificar antes del código (D-6D-1..4)

- **D-6D-1 · Nombre y forma del Pset.** `Pset_Aqyra_Cumplimiento` con propiedades
  `Resultado` (enum de 4), `Exigencia`, `DocumentoBasico`, `Apartado`, `Pack`,
  `MotivoNoVerificable?`. ¿Se ratifica el nombre/propiedades?
- **D-6D-2 · Granularidad.** El veredicto es por exigencia con `por_modelo` (por sub-modelo
  federado), **no por elemento**. Propuesta: atribuir el resultado del sub-modelo a **todos los
  elementos de ese sub-modelo** (vía manifiesto C4). Para varias exigencias sobre el mismo
  elemento: `Resultado` = **peor caso** (`no-cumple` > `no-verificable` > `cumple`; `no-aplica`
  neutro) + un Pset/propiedad por exigencia con el detalle. ¿Se ratifica el "peor caso"?
- **D-6D-3 · Alcance del write-back en v0.** Solo las 5 exigencias del pack `CTE/2019` de
  `GOL-CTE-01`. ¿Correcto para el primer corte?
- **D-6D-4 · Colores del visor.** `cumple`=verde, `no-cumple`=rojo, `no-aplica`=gris,
  `no-verificable`=ámbar. (Decisión de UI, va en `apps/visor/DECISIONES.md`.) ¿Se ratifica?
