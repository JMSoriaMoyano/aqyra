# qa-pynite/ — QA independiente (2.ª llave técnica · ANZUELO · privado · D-023)

Re-cálculo **independiente** del resultado del motor anclado, con **PyNite** (un solver **distinto** del núcleo de `motor-fem` — independencia D-023·C.1). Es la **1.ª llave** de las dos: produce `qa-passed` cuando el resultado reconcilia; la **2.ª llave** es la **firma de JM** (`verified-signed`). La IA prepara la evidencia; **JM firma**.

## Qué hace (D-023)

1. **Gate de equilibrio** (`reconcile.equilibrium_check`) — Σreacciones = Σacciones por eje global (~0,1 %). Si no cierra, el resultado es inconsistente: **qa-fail inmediato**, ni se reconcilia.
2. **Re-cálculo independiente** (`pynite_solver.solve_pynite`) — re-ensambla el modelo **desde el contrato C5** (no reutiliza el solver del adaptador) y resuelve con PyNite (`analyze(sparse=False)`). Convenio D-018: gravedad −Z, ejes por rol (strong→Iz, weak→Iy), **N>0 = tracción** (PyNite reporta el axil con tracción negativa → se niega).
3. **Reconciliación** (`reconcile.reconcile`) — compara motor vs PyNite con tolerancias (D-023·C.2): reacciones/desplazamientos ±2–5 %, esfuerzos/aprovechamientos ±5 %.
4. **Veredicto** (`qa.run_qa`) — `qa-passed` ⇒ eleva el resultado del motor a `state="qa-passed"`; `qa-fail` ⇒ **bloquea** (no eleva nada) y **expone la discrepancia** en el `QAReport` (anulación documentada, D-023·C.4.a).

## Independencia (D-023·C.1)

PyNite ≠ núcleo de `motor-fem`: son solvers distintos (productor ≠ QA). Esta carpeta comparte con el adaptador **solo el contrato** (tipos `puente_calculo.contract`), nunca el solver. Anclado en chequeo independiente **Cat 3** (BS 5975).

## Frontera de gobierno

Esta carpeta **nunca** produce `verified-signed`: solo `qa-passed`. El verde lo acuña la firma de JM. El visor jamás pinta como certificado lo no firmado (D-021).

## Estado

Implementado y verificado en sandbox con PyNite 2.0.2 (caso patrón ménsula: carga −Z → reacción +Z, flecha −Z; reconciliación pass/fail; gate de equilibrio). `motor-fem` no está vendorizado (se ancla del ecosistema): en producción, `run_qa` recibe el `ResultGroup` del motor y lo contrasta con esta QA.
