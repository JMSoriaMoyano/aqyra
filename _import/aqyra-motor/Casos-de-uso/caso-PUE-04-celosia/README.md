# caso-PUE-04 — Celosía de acero (barras articuladas + EC3)

Caso e2e del vertical **celosía** de la disciplina `puentes` (Ola 7, PT 7.2). Celosía
**Pratt L=40 m, canto h=5 m, 8 paneles**, acero S355, tablero inferior, 2 carriles LM1.
**Predimensionado/asistencia; revisar y firmar por ICCP.**

## Flujo
`entrada_caso.json` → `celosia` (cordones + montantes + diagonales articuladas) →
permanente (nudos del cordón inferior) + LM1 (camino del cordón inferior) →
`motor-fem` (estático G + envolventes del axil + modal) → `ec3_celosia` (tracción /
compresión-pandeo curva b / uniones; fatiga = gancho) → resultado + write-back.

## Resultado
- **VEREDICTO: CUMPLE** · aprovechamiento máx **0.985** (gobierna la diagonal de
  apoyo `D_0` en tracción).
- Axiles extremos: tracción cordón inferior centro ≈ +6343 kN; compresión cordón
  superior centro ≈ −6750 kN. f₁ = **2.64 Hz**.
- **Fatiga (EN 1993-1-9): gancho diferido** (LM3 + categorías de detalle +
  Palmgren-Miner) a un PT de fatiga posterior.

## Ejecución
```
PYTHONPATH=$PYLIBS:$MOTORFEM/scripts:$MOTORFEM/scripts/elementos \
python3 puentes/scripts/run_all_celosia.py entrada_caso.json resultado_celosia.json
```

## Archivos
`entrada_caso.json` · `resultado_celosia.json` · `mapping_resultado_celosia.json` ·
`memoria-celosia-PUE04.md`.
