# Caso PCI-02 — Red mallada de rociadores automáticos (UNE-EN 12845, OH1)

Segundo vertical PCI de la disciplina `instalaciones` (PT 4.4, Ola 4). Ejercita de extremo a
extremo el **motor hidráulico de red con mallas** (solver de Hardy-Cross) y el **write-back de
Psets de resultado** al IFC.

## Flujo (IFC → cálculo → IFC)

1. **IFC MEP** `rociadores-malla.ifc` — red en escalera con 3 lazos y 6 rociadores
   (`iso19650-openbim:scripts/mep/generate_test_ifc_rociadores.py`).
2. **Parser MEP** → `modelo_neutro_mep.json` (`iso19650-openbim:ifc_to_model_mep.py`). Se inyecta
   `sistema.clase_riesgo = "OH1"`.
3. **Bases de demanda** (UNE-EN 12845, OH1) → `demanda.json`
   (`instalaciones:pci/bases_demanda.aplicar_rociadores`): densidad 5,0 mm/min × 72 m² → 6
   rociadores, K=80, p_min 56,25 kPa, Q_diseño 6,0 l/s.
4. **Solver de mallas** (Darcy-Weisbach + Hardy-Cross) → `resultado.json`
   (`instalaciones:red/solver_red.py`): 3 lazos, 9 iteraciones, cierre 5·10⁻⁶ kPa.
5. **Verificación** → `verificacion.json` (`instalaciones:red/verificacion_red.py`): balance nodal
   0,0 %, cierre por lazo ≈ 0, presiones OK → **CUMPLE**.
6. **Write-back** → `mapping_resultado.json` (`instalaciones:red/resultado_ifc.py`) +
   `rociadores-malla-resultado.ifc` (`iso19650-openbim:ifc-create:escribir_psets_resultado.py`):
   `Pset_Estructurando_ResultadoRed` en 22 elementos.
7. **Validación** del IFC enriquecido (`iso19650-openbim:ifc-validate`): continuidad 100 %, APTO.

## Resultado

**CUMPLE.** Grupo 300 kPa disp / 58,9 kPa req (margen 241 kPa); v_pico 1,243 m/s; los 6 rociadores
del área de operación con margen ≈ 241 kPa. Balance de caudales 0,0 %, cierre de lazos ≈ 0.

Predimensionado/asistencia; **revisar y firmar por técnico competente**. NDP `[confirmar AN]`.

## Ficheros

`rociadores-malla.ifc` · `modelo_neutro_mep.json` · `demanda.json` · `resultado.json` ·
`verificacion.json` · `mapping_resultado.json` · `rociadores-malla-resultado.ifc` ·
`memoria-instalaciones.md` (+ `.docx`).
