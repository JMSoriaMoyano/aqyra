# PUE-19 — Tablero oblicuo (esviado) (IFC-driven, FEM-2)

**Ola 7 · PT 7.5.** Vertical avanzado de puentes sobre el peldaño **FEM-2**
(lámina curva MITC4 + rigidizador con offset + pared delgada) del motor `motor-fem`
**v0.3.0 (intacto)**. Calculado **de extremo a extremo arrancando del IFC**.

> Predimensionado/asistencia. **A revisar y firmar por técnico competente (ICCP).**
> Los NDP se marcan `[confirmar AN]`.

## Cadena IFC-driven

```
gen_cases.py oblicuo  ─►  PUE19_oblicuo.ifc  (IFC4X3)
        │  Pset_Estructurando_Tipologia {Tipologia: oblicuo} + claves del vertical
        ▼
ifc_to_model_estructural.parse   ─►  tipología = «oblicuo»
        ▼
desde_ifc.leer  ─►  entrada_oblicuo_desde_ifc.json   (adaptador _oblicuo)
        ▼
run_all_oblicuo.ejecutar
   1) idealizacion/oblicuo.py        → malla FEM-2 (lámina curva MITC4 )
   2) acciones IAP-11 (permanentes, LM1)
   3) motor-fem (C5, FEM-2): estático + modal informativo
   4) comprobacion/ec_oblicuo.py    → comprobación EC
        ▼
resultado.json  +  mapping_resultado_ifc.json
        ▼
writeback_ifc.aplicar  ─►  PUE19_oblicuo-resultados.ifc
        Pset_Estructurando_ResultadoPuente (Veredicto_global = CUMPLE)
```

## Resultado

**Veredicto: CUMPLE** · aprovechamiento máximo **0.949** · f₁ = 5.07 Hz.

- **Esviaje**: 30° · **Concentración esquina obtusa** R_obtusa/R_media = 6.23
- **Reparto transversal** factor = 1.06 · **As_long** = 41.7 cm²/m

### Comprobaciones

| Comprobación | Ed | Rd | Aprov. | Cumple |
|---|---|---|---|---|
| Flexion losa long. M_Rd (EC2) | 1.22e+06 | 1.29e+06 | 0.949 | ✓ |
| Flexion losa transv. M_Rd (EC2) | 2.62e+05 | 4.02e+05 | 0.652 | ✓ |

## Cómo reproducirlo

```bash
export TMPDIR=/tmp HOME=/tmp MOTOR_FEM_SCRIPTS=<motor-fem/scripts> MOTOR_CALCULO_BARRAS=<motor-calculo/scripts/barras>
export PYTHONPATH=/tmp/pylibs:/tmp/ifclib:<motor-fem/scripts>:<motor-calculo/scripts/barras>:<puentes/scripts/lectura>:<iso19650/scripts/estructural>:<iso19650/scripts/lineal>:<iso19650/scripts/nucleo>
python3 <puentes>/scripts/lectura/gen_cases.py oblicuo entrada_caso.json PUE19_oblicuo.ifc
python3 <puentes>/scripts/run_all_oblicuo.py PUE19_oblicuo.ifc resultado.json
```

## Archivos

- `PUE19_oblicuo.ifc` — IFC4X3 de entrada (geometría real + Psets).
- `entrada_caso.json` — parámetros del caso (para `gen_cases`).
- `entrada_oblicuo_desde_ifc.json` → renombrado `entrada_caso_desde_ifc.json` — salida del adaptador `desde_ifc`.
- `resultado.json` — resultado completo del cálculo.
- `mapping_resultado_ifc.json` — Psets de resultado.
- `PUE19_oblicuo-resultados.ifc` → `caso-PUE-19-resultados.ifc` — IFC con write-back.
- `memoria-PUE19.md` — memoria de cálculo (predimensionado).
