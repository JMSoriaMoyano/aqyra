# Cambio · Ingesta MEP al Maestro federado (C4/C1) — instalaciones navegables

> Change-id: `c4-ingesta-mep` · Capacidad: C1 (modelo neutro) + C4 (federación) · **contract-first**.
> Plan de Cierre **F3.1** (habilitador). Desbloquea el skin de Instalaciones del visor (F5.1) y las
> disciplinas atenuadas del rail. Dos llaves. Decisiones D-MEP-1..D-MEP-5 **RATIFICADAS por JM (2026-07-16)**.

## Por qué
El pipeline actual (engines/ifc, services/federacion, visor) reconoce elementos de edificación pero
**no enumera las clases MEP** (`IfcFlow*`/`IfcPipe*`/`IfcCableCarrier*`/`IfcValve`/`IfcFireSuppressionTerminal`),
así que un modelo de instalaciones entra pero sus elementos no se ven ni sus **sistemas** aparecen. La
arquitectura ya está preparada: `packages/core/grafo_red.py` (red por `IfcDistributionPort`/
`IfcRelConnectsPorts`) y `ifc_utils.py` anticipan `ifc_to_model_mep.py`. Este cambio cierra esa costura.

## Modelo de referencia (fuente externa, NO entra al repo)
`MEP Nave industrial.ifc` (aportado por JM) · **IFC4** (Revit ReferenceView V1.2) · 20,3 MB ·
**17 `IfcDistributionSystem`** (PCI + fontanería + bandejas eléctricas) · clases físicas presentes:
`IfcPipeSegment/Fitting`, `IfcValve`, `IfcCableCarrierSegment/Fitting`, `IfcFireSuppressionTerminal`,
`IfcFlowTerminal` · red de **5.498 `IfcDistributionPort`** con **2.464 `IfcRelConnectsPorts`** /
**2.866 `IfcRelNests`** · sistemas ligados por `IfcRelAssignsToGroup` (17) + `IfcRelServicesBuildings` (17).

## Qué cambia (alcance v0, D-MEP-4 acotado)
1. **Reconocer las clases MEP** (D-MEP-1) como elementos navegables del modelo neutro: `IfcPipeSegment`,
   `IfcPipeFitting`, `IfcValve`, `IfcCableCarrierSegment`, `IfcCableCarrierFitting`,
   `IfcFireSuppressionTerminal`, `IfcFlowTerminal` (los `*Type` son tipos, no elementos).
2. **Mapear los sistemas** (D-MEP-2): cada `IfcDistributionSystem` (17) → «Estructura funcional» del
   visor (D-CH-4), vía `IfcRelAssignsToGroup` (sistema→elementos) + `IfcRelServicesBuildings`
   (sistema→edificio), con su `PredefinedType`.
3. **Métrica espacial** (D-MEP-3): `elevationMetric` por planta (edificación). `stationMetric`/
   `IfcAlignment` NO aplica (es de obra lineal).
4. **Salida:** los elementos MEP aparecen en el árbol/contadores por clase del visor y los 17 sistemas
   en la sección funcional. **v0 NO construye el grafo de red completo** (puertos/conexiones): eso es
   incremento posterior por `grafo_red` para alimentar el motor de instalaciones.

## Qué NO cambia / fuera de alcance
- **El grafo de red por puertos** (5.498 puertos) — incremento posterior (motor de instalaciones).
- **La zona anclada** (fixtures de edificación, E2E, cámara D29, golden C4/C3) intacta.
- **stationMetric / IfcAlignment** — obras lineales, otro epic.
- El modelo de 20 MB **no entra al repo**; el golden usa un **recorte determinista** (D-MEP-5).

## Golden (D-MEP-5)
Fixture = **recorte determinista pequeño** (1–2 `IfcDistributionSystem`) derivado del modelo real con
`tools/derivar_fixture_mep.py` (ifcopenshell, conda `mcp-bim` de JM), anclado por **md5** en
`versions.lock`. Golden `GOL-MEP-01`: sobre el recorte, comprobar (a) nº de elementos MEP por clase
reconocidos, (b) los sistemas y su asignación elemento→sistema, (c) la métrica de planta. Ancla por
determinismo (conteos + asignaciones), no por md5 de salida.

## Alcance de ESTA entrega (acotado con JM 2026-07-17)
Esta entrega es el **núcleo contract-first C1** (lo que da la autoridad de las dos llaves — la golden):
esquema del modelo neutro (clave `instalaciones`, forward-open) + golden `GOL-MEP-01` + engine
`engines/ifc/ifc_to_model_mep.py` + ancla del fixture en `versions.lock`. Con esto el Maestro ya
**reconoce** los elementos MEP y **mapea** sus sistemas en el modelo neutro.

**Diferido a baby-steps siguientes** (por la regla de zona anclada, no por alcance del diseño):
- **Federación `estructura_funcional`** en el manifiesto C4: el runner C4 (`_diffs`) rechaza claves
  inesperadas → añadirla rompería los 6 golden C4-FED anclados. Entra en su propio change con su
  golden C4 MEP (o emitida sólo-si-hay-sistemas + caso nuevo).
- **Visor** (enumeración MEP + poblar «Estructura funcional»): es el consumo aguas abajo — el
  **skin de Instalaciones es F5.1**, que este change DESBLOQUEA.

## Gobierno — dos llaves
Toca C1/C4 (zona con guardián + contrato) → **change SDD obligatorio** (este) + golden anclada ANTES
del engine + adversarial-review + PR (Llave 1) → **Llave 2 (merge/firma JM)**.
