# PUE-20 — Tablero curvo en planta (IFC-driven, FEM-2)

**Ola 7 · PT 7.5.** Vertical avanzado de puentes sobre el peldaño **FEM-2**
(lámina curva MITC4 + rigidizador con offset + pared delgada) del motor `motor-fem`
**v0.3.0 (intacto)**. Calculado **de extremo a extremo arrancando del IFC**.

> Predimensionado/asistencia. **A revisar y firmar por técnico competente (ICCP).**
> Los NDP se marcan `[confirmar AN]`.

## Cadena IFC-driven

```
gen_cases.py curvo  ─►  PUE20_curvo.ifc  (IFC4X3)
        │  Pset_Estructurando_Tipologia {Tipologia: curvo} + claves del vertical
        ▼
ifc_to_model_estructural.parse   ─►  tipología = «curvo»
        ▼
desde_ifc.leer  ─►  entrada_curvo_desde_ifc.json   (adaptador _curvo)
        ▼
run_all_curvo.ejecutar
   1) idealizacion/curvo.py        → malla FEM-2 (lámina curva MITC4 )
   2) acciones IAP-11 (permanentes, LM1)
   3) motor-fem (C5, FEM-2): estático + modal informativo
   4) comprobacion/ec_curvo.py    → comprobación EC
        ▼
resultado.json  +  mapping_resultado_ifc.json
        ▼
writeback_ifc.aplicar  ─►  PUE20_curvo-resultados.ifc
        Pset_Estructurando_ResultadoPuente (Veredicto_global = CUMPLE)
```

## Resultado

**Veredicto: CUMPLE** · aprovechamiento máximo **0.666** · f₁ = 2.70 Hz.

- **Radio** R = 200 m · **T/M** = 0.141 · **T_apoyo** = 8490 kNm (acoplamiento por curvatura)
- **J de Bredt** = 8.8476 m⁴ · τ_total = 4.91 ≤ τ_Rd = 7.38 MPa

### Comprobaciones

| Comprobación | Ed | Rd | Aprov. | Cumple |
|---|---|---|---|---|
| Flexion compresion sup. (EC2) | 1.25e+07 | 2.7e+07 | 0.462 | ✓ |
| Flexion armado fondo As/As_max (EC2) | 654 | 2.07e+03 | 0.316 | ✓ |
| Cortante+Torsion Bredt (EC2 6.3) | 4.91e+06 | 7.38e+06 | 0.666 | ✓ |

## Cómo reproducirlo

```bash
export TMPDIR=/tmp HOME=/tmp MOTOR_FEM_SCRIPTS=<motor-fem/scripts> MOTOR_CALCULO_BARRAS=<motor-calculo/scripts/barras>
export PYTHONPATH=/tmp/pylibs:/tmp/ifclib:<motor-fem/scripts>:<motor-calculo/scripts/barras>:<puentes/scripts/lectura>:<iso19650/scripts/estructural>:<iso19650/scripts/lineal>:<iso19650/scripts/nucleo>
python3 <puentes>/scripts/lectura/gen_cases.py curvo entrada_caso.json PUE20_curvo.ifc
python3 <puentes>/scripts/run_all_curvo.py PUE20_curvo.ifc resultado.json
```

## Archivos

- `PUE20_curvo.ifc` — IFC4X3 de entrada (geometría real + Psets).
- `entrada_caso.json` — parámetros del caso (para `gen_cases`).
- `entrada_curvo_desde_ifc.json` → renombrado `entrada_caso_desde_ifc.json` — salida del adaptador `desde_ifc`.
- `resultado.json` — resultado completo del cálculo.
- `mapping_resultado_ifc.json` — Psets de resultado.
- `PUE20_curvo-resultados.ifc` → `caso-PUE-20-resultados.ifc` — IFC con write-back.
- `memoria-PUE20.md` — memoria de cálculo (predimensionado).
