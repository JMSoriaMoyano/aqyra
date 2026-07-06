# Roadmap · Skins del visor por disciplina

> Nota de secuencia del hilo «visor · skins por disciplina». No es normativa de contrato; ordena
> los slices y deja anotadas las ratificaciones de JM. La spec del Slice 1 vive en este mismo
> cambio (`proposal.md` / `design.md` / `specs/visor/spec.md`).

## Ratificaciones de JM (2026-07-06)

- **D-SK-2 · RATIFICADA.** Color por clase = **mapa categórico** por tipo IFC, separado del
  acento de disciplina (no rampa). Prevalece sobre la redacción «rampa» del §7 del brief.
- **D-SK-4 · RATIFICADA.** Alcance de Slice 1 = **Diseño + Estructuras** (las de modelo de
  edificio ya soportadas por `ELEMENT_TYPES`).
- D-SK-1 (clases = mapa estático ∩ presentes) y D-SK-3 (`skins.ts` dominio puro) quedan como en
  `design.md`; se anclarán como V-nuevas en `apps/visor/DECISIONES.md` en la fase de código.

## Cómo se elabora una skin nueva (patrón)

Cada disciplina nueva es **aditiva** sobre `apps/visor/src/skins.ts`: ampliar `type Disciplina`,
añadir su entrada en `SKINS` (acento + lista de clases del dominio) y los colores categóricos de
sus clases nuevas. Es dato puro, unit-testable headless, y entra por su **propio cambio OpenSpec**
con tests-first y las dos llaves (propone puro → sin Llave 2), igual que el Slice 1. La parte de
datos de una skin cuesta horas; **lo que fija el calendario es la capacidad de ingesta que el
visor necesita antes** de poder cargar y colorear las clases de ese dominio.

## Secuencia y dependencias

| Slice | Disciplinas / superficie | Prerrequisito que marca el «cuándo» |
|---|---|---|
| **1** (este) | Diseño + Estructuras · acento + color categórico + leyenda | ninguno (clases en `ELEMENT_TYPES`) |
| **2** | Panel Selección + Propiedades/Psets + chip de estado | ninguno nuevo (reutiliza `ifc-loader`/`data-state`) |
| **3** | Instalaciones (MEP) | **ampliar la ingesta**: `ELEMENT_TYPES` hoy NO carga `IfcFlowSegment`/`IfcFlowFitting`/`IfcFlowTerminal`/`IfcFlowController` bajo `IfcDistributionSystem` |
| **4** | Obras lineales + Puentes | **cerrar `stationMetric` (PK)** —hoy lanza `Error(INFRA)` en `spatial-metric.ts`— y la carga de `IfcAlignment`; entretanto, árbol por contenedor provisional |

**Eje transversal (paralelo, no bloqueante del re-vestido):** el **dock de herramientas que
invoca el engine** de cada disciplina (`motor-fem`, `instalaciones`, `obras-lineales`, `puentes`)
y trae resultados como Psets + estado de dato. El re-vestido es UX; el cálculo vive en los
engines (§6.2 del brief). Si al cablearlo se define un **contrato de invocación visor↔engine**,
*ese* pasa a **contract-first** (ficha de contrato + golden con oráculo + CODEOWNERS): gobierno
más pesado que la skin, fuera del alcance de estos slices.

## En una frase

Las skins nuevas se **elaboran** ampliando el mapa de `skins.ts`; el **cuándo** lo fija que el
visor sepa cargar y colorear las clases de cada dominio (MEP para Slice 3; PK/`IfcAlignment` para
Slice 4).
