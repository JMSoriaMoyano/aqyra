# Golden GOL-PRE-02 — el coste vuelve al modelo (write-back 5D, C5 Fase IV·h3)

> El segundo caso del contrato **C5**: hace **5D** el modelo que `GOL-PRE-01` hizo presupuestable.
> El coste (partida e importe) vuelve al IFC con el **modelo de coste nativo de OpenBIM** (D12):
> `IfcCostSchedule` + `IfcCostItem` asignados a los elementos. Auditable hasta el elemento.

## Flujo (runner `run_case_c5`, rama 5D)

1. **Federar + derivar** las fixtures con `Qto` (`reglas.json`, patrón C4-FED-06) → derivado (el Maestro
   que abre el visor). El engine ABRE el derivado, no federa (D7).
2. **Medir + presupuestar** (reutiliza el engine del 4.2) → presupuesto (reproduce `GOL-PRE-01`).
3. **`escribir_coste(presupuesto, derivado, salida)`** → IFC 5D con:
   `IfcCostSchedule` (BUDGET) → `IfcRelNests` → `IfcCostItem` por capítulo → por partida
   (`IfcCostValue`=importe, `CostQuantities`=cantidad) + `IfcRelAssignsToControl` a los elementos con
   GUID ∈ trazabilidad + `IfcCostItem` resumen (PEM…PEC) + `IfcMonetaryUnit` EUR.

## Qué ancla (D14, opción b — sin md5 hardcodeado)

- **DETERMINISMO:** escribir el 5D **dos veces** produce **bytes idénticos** (cabecera SPF con firma
  fija sin versión + `time_stamp` constante + GUIDs `uuid5`, patrón `derivar`).
- **SEMÁNTICA:** el cost schedule **casa con el presupuesto** — un `IfcCostItem` por partida con
  `IfcCostValue`=importe y `CostQuantities`=cantidad; `IfcRelAssignsToControl` → GUIDs ⊆ trazabilidad;
  Σ importes de partida = PEM; el item resumen lleva PEM/GG/BI/base/IVA/PEC; `IfcMonetaryUnit`=EUR.

## Regla de oro

Un fallo NO se arregla aflojando el check: se investiga el ENGINE (`escritura.py`). El presupuesto y
sus fixtures/derivado son los del 4.1/2.6 — **`GOL-PRE-01` y la zona anclada quedan intactos**.
