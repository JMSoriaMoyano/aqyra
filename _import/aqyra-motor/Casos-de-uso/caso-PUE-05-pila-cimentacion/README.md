# caso-PUE-05 — Pila + aparato de apoyo + cimentación (columna + resortes)

Caso e2e del vertical **pila** de la disciplina `puentes` (Ola 7, PT 7.3). Pila
intermedia **H = 8 m**, sección 1,5 × 1,5 m (HA-30), **aparato de apoyo elastomérico**
en cabeza y **zapata 6 × 6 m** en base sobre resorte Winkler.
**Predimensionado/asistencia; revisar y firmar por ICCP.**

## Flujo
`entrada_caso.json` → `pila` (columna barra 3D) → aparato de apoyo (resorte 6 GdL) +
base sobre resorte Winkler → reacciones del tablero en cabeza (N_G=4200, N_LM1=1500,
frenado=360, viento=120, térmica=150 kN) + peso propio + viento del fuste →
`motor-fem` (estático G/M/F/V/T + modal) → `ec2ec7_pila` (EC2 fuste M-N + 2.º orden +
cortante bielas; **EC7 cimentación enrutada** → zapata) → resultado + write-back.

## Resultado
- **VEREDICTO: CUMPLE** · aprovechamiento máx **0.785** (gobierna EC7 hundimiento).
- Esfuerzos de base (ELU): N = 8291 kN, M = 5918 kN·m, V = 751 kN.
- Fuste: flexo-compresión M-N **0.495**, cortante por bielas **0.109**.
- δ 2.º orden = **1.016** (pila rígida, despreciable) · f₁ = **4.51 Hz**.
- EC7 zapata: σ_max = 432 kPa ≤ q_adm = 550 kPa (aprov **0.785**); e = 0.63 m ≤ B/6.
- Aparato de apoyo elastomérico: Kh = 3.86 MN/m, Kv = 2660 MN/m (resorte de cabeza).

## Decisiones del caso
- **Reacciones del tablero como dato del caso** (también soporta modo *acoplado* a un
  resultado de tablero PT 7.1/7.2 vía `resultado_tablero`+`apoyo_id`).
- **Cimentación enrutada por tipo** = `zapata` (alternativas: `pilotes`, `encepado`).
- **2.º orden por amplificación aproximada**; P-Δ riguroso/pandeo → FEM-3.
- **Sísmica EC8-2 = gancho diferido**.

## Ejecución
```
PYTHONPATH=$PYLIBS:$MOTORFEM/scripts \
python3 puentes/scripts/run_all_pila.py entrada_caso.json resultado_pila.json
```

## Archivos
`entrada_caso.json` · `resultado_pila.json` · `mapping_resultado_pila.json` ·
`memoria-pila-PUE05.md`.
