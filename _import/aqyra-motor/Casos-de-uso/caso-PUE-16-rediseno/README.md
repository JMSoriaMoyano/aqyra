# PUE-16 — Rediseño (NO CUMPLE → CUMPLE)

Caso de **valor iterativo** IFC-driven (PT 7.3.1): un estribo con **geometria
insuficiente** que el lector+calculo detectan como **NO CUMPLE**, y su **rediseño**
(base ensanchada) que pasa a **CUMPLE**. Demuestra que la herramienta detecta el fallo
y guia el ajuste. **Predim.; revisar y firmar (ICCP).**

## Iteracion
- **v1 (insuficiente)** `PUE-16-v1.ifc`: base estrecha (puntera 1,0 / talon 1,2 / e_z 1,0 m)
  → **NO CUMPLE**, aprovechamiento **3.164**
  (gobierna la estabilidad EC7 / fisuracion).
- **v2 (rediseño)** `PUE-16-v2.ifc`: base ensanchada (puntera 3,4 / talon 3,6 / e_z 1,8 m)
  → **CUMPLE**, aprovechamiento **0.971**.

## Flujo
`PUE-16-vN.ifc` → lector C1 → `run_all_estribo` (EC7 estabilidad + EC2 alzado/puntera/talon)
→ veredicto. El rediseño se materializa **editando la geometria del IFC** y releyendo.

## Archivos
`PUE-16-v1.ifc` (falla) · `PUE-16-v2.ifc` (rediseño) · `PUE-16-v2-resultados.ifc` (write-back)
· `entrada_v1_desde_ifc.json` · `entrada_v2_desde_ifc.json` · `resultado.json`.
