# PUE-18 — Tablero mixto acero-hormigón (IFC-driven, FEM-2)

**Ola 7 · PT 7.5.** Vertical avanzado de puentes sobre el peldaño **FEM-2**
(lámina curva MITC4 + rigidizador con offset + pared delgada) del motor `motor-fem`
**v0.3.0 (intacto)**. Calculado **de extremo a extremo arrancando del IFC**.

> Predimensionado/asistencia. **A revisar y firmar por técnico competente (ICCP).**
> Los NDP se marcan `[confirmar AN]`.

## Cadena IFC-driven

```
gen_cases.py mixto  ─►  PUE18_mixto.ifc  (IFC4X3)
        │  Pset_Estructurando_Tipologia {Tipologia: mixto} + claves del vertical
        ▼
ifc_to_model_estructural.parse   ─►  tipología = «mixto»
        ▼
desde_ifc.leer  ─►  entrada_mixto_desde_ifc.json   (adaptador _mixto)
        ▼
run_all_mixto.ejecutar
   1) idealizacion/mixto.py        → malla FEM-2 (lámina curva MITC4 + rigidizador offset)
   2) acciones IAP-11 (permanentes, LM1, FLM3 fatiga)
   3) motor-fem (C5, FEM-2): estático + modal informativo
   4) comprobacion/ec3ec4_mixto.py    → comprobación EC
        ▼
resultado.json  +  mapping_resultado_ifc.json
        ▼
writeback_ifc.aplicar  ─►  PUE18_mixto-resultados.ifc
        Pset_Estructurando_ResultadoPuente (Veredicto_global = CUMPLE)
```

## Resultado

**Veredicto: CUMPLE** · aprovechamiento máximo **0.755** · f₁ = 2.99 Hz.

- **Clase de sección**: 2
- **b_eff losa**: 2.50 m · **M_Rd total**: 43.9 MNm · **PNA**: ala superior
- **Conexión** η = 1.32 · **Fatiga** Δσ_E2 = 38.5 ≤ Δσ_Rd = 66.7 MPa

### Comprobaciones

| Comprobación | Ed | Rd | Aprov. | Cumple |
|---|---|---|---|---|
| Flexion mixta M_pl,Rd (EC4) | 2.53e+07 | 4.39e+07 | 0.578 | ✓ |
| Cortante alma Vpl,Rd (EC3) | 4.25e+05 | 1.73e+07 | 0.025 | ✓ |
| Conexion grado eta (EC4 6.6) | 1.32 | 1 | 0.755 | ✓ |
| Fatiga ala inferior (EC3-1-9) | 38.5 | 66.7 | 0.577 | ✓ |

## Cómo reproducirlo

```bash
export TMPDIR=/tmp HOME=/tmp MOTOR_FEM_SCRIPTS=<motor-fem/scripts> MOTOR_CALCULO_BARRAS=<motor-calculo/scripts/barras>
export PYTHONPATH=/tmp/pylibs:/tmp/ifclib:<motor-fem/scripts>:<motor-calculo/scripts/barras>:<puentes/scripts/lectura>:<iso19650/scripts/estructural>:<iso19650/scripts/lineal>:<iso19650/scripts/nucleo>
python3 <puentes>/scripts/lectura/gen_cases.py mixto entrada_caso.json PUE18_mixto.ifc
python3 <puentes>/scripts/run_all_mixto.py PUE18_mixto.ifc resultado.json
```

## Archivos

- `PUE18_mixto.ifc` — IFC4X3 de entrada (geometría real + Psets).
- `entrada_caso.json` — parámetros del caso (para `gen_cases`).
- `entrada_mixto_desde_ifc.json` → renombrado `entrada_caso_desde_ifc.json` — salida del adaptador `desde_ifc`.
- `resultado.json` — resultado completo del cálculo.
- `mapping_resultado_ifc.json` — Psets de resultado.
- `PUE18_mixto-resultados.ifc` → `caso-PUE-18-resultados.ifc` — IFC con write-back.
- `memoria-PUE18.md` — memoria de cálculo (predimensionado).
