# Caso REBT-02 — Instalación eléctrica terciaria/industrial (REBT)

Caso de extremo a extremo del **vertical eléctrico** de `instalaciones` (PT 4.5, Ola 4),
con **mezcla mono/trifásica**: línea general trifásica → subcuadro → derivaciones
(luminarias y toma monofásicas, motor trifásico).

**Flujo:** IFC MEP `ELECTRICAL` → parser MEP de `iso19650-openbim` (intacto) → bases de
demanda (receptores, ITC-BT-10/44/47) → solver eléctrico radial → verificación →
write-back → validación (APTO).

**Resultado: CUMPLE.** 5 tramos, balance de potencias 0,0 %, caída de tensión máxima
3,318 % (gobernante TOMA-1, límite 5 % fuerza), intensidades dentro del admisible. La
línea general se resuelve como trifásica (alimenta cargas mono y tri). Validación de red
**APTO** (continuidad 100 %, 9 elementos enriquecidos).

## Ficheros

- `generate_test_ifc_terciario.py` — generador del IFC de prueba (fixture).
- `terciario_rebt.ifc` — IFC de entrada (sistema ELECTRICAL, 11 elementos).
- `modelo_neutro_mep.json`, `demanda.json`, `resultado.json`, `verificacion.json`,
  `mapping_resultado.json` — artefactos del flujo.
- `terciario_rebt_resultado.ifc` — IFC enriquecido con los Psets de resultado.
- `memoria-instalaciones.md` / `.docx` — memoria.

> Nota de geometría: las derivaciones se disponen en direcciones distintas para evitar
> tramos colineales solapados, que el grafo del núcleo trocearía por intersección T/X
> creando lazos espurios (el solver los trataría como radiales igualmente).

Predimensionado/asistencia; revisar y firmar por técnico competente.
