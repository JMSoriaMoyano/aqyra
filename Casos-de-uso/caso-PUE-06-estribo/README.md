# caso-PUE-06 — Estribo (muro + empuje + cargas de tablero)

Caso e2e del vertical **estribo** de la disciplina `puentes` (Ola 7, PT 7.3). Estribo
cerrado tipo muro ménsula, alzado **Hm = 4,5 m** (HA-30), zapata B = 7,85 m (puntera
3,4 + alzado 0,85 + talón 3,6), empuje de tierras **activo Ka** y reacciones del
tablero en coronación. **Predimensionado/asistencia; revisar y firmar por ICCP.**

## Flujo
`entrada_caso.json` → `estribo` (muro con cargas de tablero: N_G=600, N_LM1=250,
frenado=80 kN en coronación) → empuje activo Ka + sobrecarga + reacciones →
fuste (alzado) por **motor-fem** (ménsula) + `empujes`/`pesos` (reuso muros) →
**`verificacion_muro`** (EC7 vuelco/deslizamiento/hundimiento + EC2 alzado/puntera/
talón) + frenado del tablero en la estabilidad global → resultado + write-back.

## Resultado
- **VEREDICTO: CUMPLE** · aprovechamiento máx **0.971** (gobierna cortante de puntera).
- Empuje **activo Ka = 0.307** (Rankine, φ=32°); altura resistida H = 6.30 m.
- EC7: vuelco **0.20**, deslizamiento **0.35**, hundimiento **0.51** (q_Ed = 330 kPa ≤
  Rd = 650 kPa; e = 0.27 m ≤ B/6, sin despegue).
- EC2: cortante alzado **0.77**, puntera **0.97**, talón **0.36**; alzado armado
  Ø25/225 (trasdós), As = 21.8 cm²/m.

## Decisiones del caso
- **Empuje activo Ka** (estribo abierto/con junta, con movilidad); selector
  `terreno.metodo_empuje` = `reposo` para estribo cerrado/integral (K0 = 1−sin φ).
- **Frenado del tablero** incluido en la estabilidad global (extensión del estribo
  sobre un muro estándar). Reacción **vertical** del tablero vía coronación → `pesos()`.
- **Fuste resuelto con motor-fem** (C5), no PyNite; EC7/EC2 reutilizan `verificacion_muro`.

## Ejecución
```
PYTHONPATH=$PYLIBS:$MOTORFEM/scripts:$MCE/scripts/muros-contencion \
python3 puentes/scripts/run_all_estribo.py entrada_caso.json resultado_estribo.json
```

## Archivos
`entrada_caso.json` · `resultado_estribo.json` · `mapping_resultado_estribo.json` ·
`memoria-estribo-PUE06.md`.
