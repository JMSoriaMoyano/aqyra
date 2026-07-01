# caso-PUE-02 — Losa postesada (lámina DKMQ)

Caso e2e del vertical **losa postesada** de la disciplina `puentes` (Ola 7, PT 7.2).
Tablero losa de **un vano L=14 m**, ancho **B=9 m**, canto **t=0.70 m**, HP-40,
postesado **biaxial** (banda en X + distribuido en Y), 2 carriles LM1 inset (vigas
de borde). **Predimensionado/asistencia; revisar y firmar por ICCP.**

## Flujo
`entrada_caso.json` → `losa_lamina` (malla DKMQ 14×9) → permanentes (g1/g2) +
postesado biaxial (balance de cargas, P∞) → `motor-fem` (estático G1/G2/P +
envolventes LM1 por **objetivo `esfuerzo_lamina`** + modal) → `ec2_losa`
(tensiones vacío/servicio, descompresión, flexión ELU por franja) → resultado +
write-back.

## Resultado
- **VEREDICTO: CUMPLE** · aprovechamiento máx **0.967** (gobierna flexión ELU de
  vano, seguida de tracción en servicio 0.964) · franja crítica `Q_6_4`.
- Postesado: w_p = 20.21 kN/m² ≈ carga a equilibrar 20.17 kN/m² (balance ~100 %).
- M_Ed = 1027 kNm/m · M_Rd = 1062 kNm/m · f₁ = 6.43 Hz.
- Punzonamiento: **N/A** (apoyos lineales en estribos; maquinaria disponible para
  apoyos puntuales).

## Ejecución
```
PYTHONPATH=$PYLIBS:$MOTORFEM/scripts:$MOTORFEM/scripts/elementos:$MCE/scripts/pretensado \
MOTOR_FEM_SCRIPTS=$MOTORFEM/scripts \
python3 puentes/scripts/run_all_losa_postesada.py entrada_caso.json resultado_losa.json
```

## Archivos
`entrada_caso.json` · `resultado_losa.json` · `mapping_resultado_losa.json`
(write-back `Pset_Estructurando_ResultadoPuente`) · `memoria-losa-PUE02.md`.
