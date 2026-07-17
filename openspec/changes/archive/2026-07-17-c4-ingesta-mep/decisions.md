# Decisiones · c4-ingesta-mep (RATIFICADAS por JM, 2026-07-16)

- **D-MEP-1 · Clases MEP admitidas (v0):** `IfcPipeSegment`, `IfcPipeFitting`, `IfcValve`,
  `IfcCableCarrierSegment`, `IfcCableCarrierFitting`, `IfcFireSuppressionTerminal`, `IfcFlowTerminal`
  como elementos navegables. Los `*Type` son tipos (no elementos). Forward-open: añadir clases = pack/lista, no engine.
- **D-MEP-2 · Mapeo de sistemas:** los `IfcDistributionSystem` → «Estructura funcional» (D-CH-4), por
  `IfcRelAssignsToGroup` + `IfcRelServicesBuildings`, con `PredefinedType`.
- **D-MEP-3 · Métrica espacial:** `elevationMetric` por planta (edificación). `stationMetric` NO aplica.
- **D-MEP-4 · Alcance v0:** elementos + sistemas navegables (desbloquea F5.1). El grafo de red completo
  (puertos/conexiones) = incremento posterior. Baby steps.
- **D-MEP-5 · Fixture/golden:** recorte determinista pequeño (1–2 sistemas) derivado con ifcopenshell,
  anclado por md5; el modelo de 20 MB queda como fuente externa. Golden ancla por conteos+asignaciones.
