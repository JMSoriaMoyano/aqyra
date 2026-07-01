# caso-LIN-02-trazado — comprobación de trazado 3.1-IC

Caso e2e de la disciplina **`obras-lineales`** (PT 5.2, Ola 5), vertical **trazado**.
Reutiliza el eje del `caso-LIN-01-eje-carretera` (modelo neutro lineal IFC 4.3, por PK)
y lo comprueba frente a la **Norma 3.1-IC** para una **velocidad de proyecto Vp**.

## Cadena de extremo a extremo

```
modelo_neutro_lineal.json (de iso19650-openbim, PT 5.1)
   -> obras-lineales/scripts/trazado/run_all_trazado.py  --vp 60
   -> comprobación planta/alzado/visibilidad/coordinación (3.1-IC)
   -> resultados_trazado.json   (VEREDICTO)
```

```bash
python3 obras-lineales/scripts/trazado/run_all_trazado.py \
        modelo_neutro_lineal.json . --vp 60
```

## Resultado

- **Vp = 60 km/h → CUMPLE** (12 comprobaciones, 0 incumplimientos; ver
  `resultados_trazado.json`). Umbrales 3.1-IC: Rmín 130 m, imáx 6 %, Dp 69,7 m,
  Kv convexo ≥ 1085 m. El eje tiene R = 300 m, clotoides A = 134,2 (∈ [R/3, R] =
  [100, 300]), acuerdo convexo Kv = 2000 m, pendientes ≤ 3 %.
- **Sensibilidad — Vp = 100 km/h → NO CUMPLE** (`resultados_trazado_vp100.json`):
  el radio R = 300 m < Rmín 450 m, las clotoides quedan cortas por confort y el
  acuerdo convexo Kv = 2000 m < Kv mín 7125 m. Demuestra la discriminación de la
  herramienta y que la **Vp es el parámetro de proyecto gobernante**.

## Notas

- La **lectura del IFC y la coherencia geométrica** (continuidad/tangencia/PK/georref)
  ya las hizo `iso19650-openbim` en el PT 5.1 (`caso-LIN-01`); aquí se añade el
  **cumplimiento normativo 3.1-IC** frente a Vp. La herramienta **no rediseña el eje**:
  reporta CUMPLE/NO CUMPLE con propuestas de predimensionado.
- Predimensionado/asistencia; NDP **[confirmar AN]**. Revisar y firmar por técnico
  competente (Ingeniero de Caminos).
