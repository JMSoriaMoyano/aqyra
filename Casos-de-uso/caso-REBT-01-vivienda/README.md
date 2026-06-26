# Caso REBT-01 — Instalación eléctrica de vivienda (REBT, electrificación elevada)

Caso de extremo a extremo del **vertical eléctrico** de `instalaciones` (PT 4.5, Ola 4).

**Flujo:** IFC MEP `ELECTRICAL` → parser MEP de `iso19650-openbim` (intacto) → bases de
demanda (ITC-BT-25, vivienda) → solver eléctrico radial → verificación → write-back de
Psets de resultado al IFC → validación (APTO).

**Resultado: CUMPLE.** 8 circuitos (C1–C12), balance de potencias 0,0 %, caída de tensión
máxima 1,098 % (gobernante C8 — Calefacción), todas las intensidades dentro del admisible.
Validación de red **APTO** (continuidad 100 %, 8 elementos enriquecidos).

## Ficheros

- `generate_test_ifc_vivienda.py` — generador del IFC de prueba (fixture; usa ifcopenshell).
- `vivienda_rebt.ifc` — IFC de entrada (sistema ELECTRICAL, 17 elementos).
- `modelo_neutro_mep.json` — modelo neutro de red (salida del parser).
- `demanda.json` — modelo con la demanda eléctrica (slot C4).
- `resultado.json` — salida del solver (I, sección, caída de tensión por tramo).
- `verificacion.json` — arnés (balance / caída de tensión / I admisible).
- `mapping_resultado.json` — mapping de Psets de resultado (write-back).
- `vivienda_rebt_resultado.ifc` — IFC enriquecido con los Psets de resultado.
- `memoria-instalaciones.md` / `.docx` — memoria.

Reproducir (sandbox, `PYTHONPATH=/tmp/pylibs`):

```
python3 generate_test_ifc_vivienda.py vivienda_rebt.ifc
python3 <iso19650>/scripts/mep/ifc_to_model_mep.py vivienda_rebt.ifc modelo_neutro_mep.json
python3 <instalaciones>/scripts/electrico/run_all_electrico.py modelo_neutro_mep.json .
```

Predimensionado/asistencia; revisar y firmar por técnico competente.
