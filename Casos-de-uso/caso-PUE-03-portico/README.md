# caso-PUE-03 — Pórtico de paso (barras + resortes Winkler)

Caso e2e del vertical **pórtico (marco)** de la disciplina `puentes` (Ola 7, PT 7.2).
Marco monolítico **L=10 m × H=6 m** (paso inferior), ancho 10 m, HA-30, base sobre
**resortes Winkler**, empuje de tierras **K0 reposo**, 2.º orden aproximado.
**Predimensionado/asistencia; revisar y firmar por ICCP.**

## Flujo
`entrada_caso.json` → `portico` (dintel + pilas + resortes) → permanentes (dintel) +
empuje K0 (pilas) + LM1 (camino del dintel) → `motor-fem` (estático G/E + envolventes
LM1 + modal) → `ec2ec7_portico` (EC2 dintel/pilas + EC7 cimentación) → resultado +
write-back.

## Resultado
- **VEREDICTO: CUMPLE** · aprovechamiento máx **0.644** (gobierna EC7 hundimiento).
- K0 = 0.500 (φ=30°) · δ 2.º orden = 1.005 (despreciable, pila rígida) · f₁ = 4.04 Hz.
- EC7: σ_max = 193 kPa ≤ q_adm = 300 kPa (aprov 0.644); deslizamiento aprov 0.436
  (los empujes de las dos pilas se equilibran por el dintel → reacción de base real).
- Dintel: flexión 0.119, cortante por bielas 0.129. Pila (2.º orden): 0.066.

## Ejecución
```
PYTHONPATH=$PYLIBS:$MOTORFEM/scripts:$MOTORFEM/scripts/elementos:$MCE/scripts/muros-contencion \
python3 puentes/scripts/run_all_portico.py entrada_caso.json resultado_portico.json
```

## Archivos
`entrada_caso.json` · `resultado_portico.json` · `mapping_resultado_portico.json` ·
`memoria-portico-PUE03.md`.
