# Caso MEP-01 — Red PCI (BIE) de prueba · apertura del dominio IFC MEP (PT 4.2, Ola 4, hueco H2)

Primer caso del **dominio MEP**: valida de extremo a extremo el parser físico→neutro de red, el
generador de IFC MEP de prueba y la validación de red, **reutilizando el núcleo transversal**
(`ifc_utils` + `grafo_red`) extraído en el PT 4.1, **sin tocarlo**. No hay cálculo hidráulico (eso
nace después con la disciplina `instalaciones`).

## Red

Grupo de presión (fuente) → T1 (DN100) → Te → {T2 (DN65)→BIE-1, T3 (DN65)→BIE-2, T4 (DN65)→BIE-3}.
Sistema `IfcDistributionSystem` PredefinedType **FIREPROTECTION** (IFC4; en IFC4X3: FIRESUPPRESSION).

## Tubería de extremo a extremo

1. `generate_test_ifc_mep.py` → `red-pci.ifc` (IFC4 en metros; `IfcFlowMovingDevice` + `IfcFlowFitting`
   + 4×`IfcFlowSegment` + 3×`IfcFlowTerminal`, conectados por `IfcDistributionPort` + `IfcRelConnectsPorts`).
2. `ifc_to_model_mep.py red-pci.ifc modelo_neutro_mep.json` → **modelo neutro de red** (C1 §4):
   `unidades` SI, `sistema`, `nodos`, `tramos`, `terminales`, `fuentes`. El grafo lo construye
   `grafo_red.construir_grafo` (mismos snap/troceo T-X que el grafo estructural).
3. `validacion_red.py modelo_neutro_mep.json verificacion_red.json` → **VEREDICTO: CUMPLE**.

## Resultado (verificacion_red.json)

- **5 nodos** (N1 fuente · N2 unión/te · N3-N5 terminales), **4 tramos**, **3 terminales**, **1 fuente**.
- Longitudes: T1=10 m (DN100, montante), T2/T4=5 m, T3=10 m (DN65, ramales). Factor de escala IFC = 1,0.
- **Continuidad**: cobertura 100 % desde la fuente; **sin componentes huérfanas**
  (`filtrar_componentes_desconectadas`, `es_ancla` = nudo fuente); **terminales conectados 3/3**;
  unidades SI coherentes.

## Gancho H3 (no implementado aquí)

El modelo neutro deja prevista la clave `demanda` por terminal y por sistema, para recibir más
adelante caudales/potencias/ocupación (bases de demanda = hueco H3). Este caso **no** calcula demandas.

*Predimensionado/asistencia; a revisar y firmar por técnico competente (Ingeniero de Caminos). NDP `[confirmar AN]`.*
