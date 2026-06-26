# Memoria de obra lineal — Drenaje (caso LIN-04)

> Predimensionado/asistencia. **Debe ser revisado y firmado por técnico competente
> (Ingeniero de Caminos, Canales y Puertos).** NDP marcados **[confirmar AN]**.

## 1. Datos del proyecto

- Eje: **Eje C-001** (carretera C-001), modelo neutro lineal del caso `caso-LIN-01`
  (IFC 4.3 `IfcAlignment`, georreferenciado **EPSG:25830** ETRS89/UTM 30N).
- Longitud: 400 m (PK 0+000 → 0+400). Calzada única.
- Encargo: **drenaje superficial (cuneta) y transversal (ODT)** según la Norma 5.2-IC.

## 2. Normativa

- **Norma 5.2-IC** «Drenaje superficial» (Orden FOM/298/2016): hidrología (método
  racional), drenaje de plataforma y márgenes (cunetas), obras de drenaje transversal.
- Soporte IFC/coherencia geométrica: `iso19650-openbim` v0.5.0 (modelo neutro lineal,
  validación de continuidad/tangencia/georref, export GIS).

## 3. Materiales / componentes

- Cuneta: sección triangular revestida de **hormigón** (n=0,015), margen derecha.
- ODT: **tubo circular de hormigón** Ø1,80 m (n=0,013).

## 4. Datos de proyecto / acciones (C4 — hidrología)

El **dato del GIS/Pset prevalece**; aquí se inyectan como datos de proyecto y se marcan
**[confirmar AN]** (lluvia de proyecto del mapa «Máximas lluvias diarias en la España
peninsular» y estudio pluviométrico):

| Cuenca | A | L | J | Pd | I1/Id | Po | T |
|---|---|---|---|---|---|---|---|
| C-plataforma | 0,0096 km² | 400 m | 2,0 % | 80 mm | 9,0 | 1,0 mm | 25 a |
| C-vertiente | 0,85 km² | 1,6 km | 3,5 % | 95 mm | 10,0 | 18,0 mm | 100 a |

Método: **racional modificado 5.2-IC** (tc de Témez, curva IDF de la 5.2-IC, coeficiente
de escorrentía por umbral Po, coeficiente de uniformidad Kt). `Q = C·I·A·Kt/3,6`.

## 5. Comprobaciones (5.2-IC)

**Caudales de cálculo:**

- C-plataforma: tc=0,314 h · I=55,0 mm/h · C=0,983 · Kt=1,02 → **Q=0,147 m³/s**.
- C-vertiente: tc=0,811 h · I=44,7 mm/h · C=0,457 · Kt=1,16 → **Q=5,066 m³/s**.

**Cuneta CUN-MD** (triangular 1V:3H, profundidad 0,30 m, hormigón, J=2 %):

- Capacidad útil con resguardo 0,05 m = **0,427 m³/s ≥ Q 0,147 m³/s**.
- Calado normal 0,16 m (resguardo real 0,13 m ≥ 0,05 m); velocidad 1,76 m/s ∈ [0,50; 6,00].
- **Veredicto: CUMPLE.**

**ODT-1** (tubo circular Ø1,80 m, hormigón, J=1,5 %):

- Capacidad de salida (Manning, llenado 0,75) 12,84 m³/s; capacidad de entrada
  (orificio, HW/D=1,2) 7,59 m³/s → **gobierna la entrada: 7,59 m³/s ≥ Q 5,07 m³/s**.
- Dimensión 1,80 m ≥ mínima 1,80 m (conservación/limpieza); velocidad 3,38 m/s ∈ [0,50; 6,00].
- **Veredicto: CUMPLE.**

**Write-back / GIS (no bloqueante):** `Pset_Estructurando_ResultadoLineal` escrito en el
`IfcAlignment` (resumen de drenaje); IFC re-parseado y revalidado **CUMPLE** (continuidad
0,0001 m, georref intacta). Planta exportada a GeoJSON (81 vértices, EPSG:25830).

## 6. Registro fechado

- **2026-06-22** — Encargo: drenaje 5.2-IC sobre el eje C-001. Datos: 2 cuencas (cuneta
  T=25, ODT T=100), 1 cuneta triangular hormigón h=0,30, 1 ODT Ø1,80. Parámetros:
  método racional modificado (Témez/IDF/Po). Resultado: cuneta **CUMPLE** (Q 0,147 / cap.
  0,427), ODT **CUMPLE** (Q 5,07 / cap. 7,59, control de entrada). Gancho `drenaje`
  relleno; write-back + GIS. Decisión: sección de cuneta y ODT predimensionadas válidas;
  pendiente de confirmar lluvia de proyecto y NDP con el AN.

## 7. Conclusiones

El drenaje superficial (cuneta) y transversal (ODT) predimensionados **desaguan los
caudales de cálculo** de sus respectivas cuencas con resguardo y velocidades admisibles.
Predimensionado de asistencia (cálculo local por elemento, sin red); **revisar y firmar
por técnico competente (ICCP)**. NDP **[confirmar AN]**: lluvia de proyecto (Pd, I1/Id),
umbral de escorrentía Po, periodos de retorno, n de Manning, velocidades admisibles y
dimensión mínima de ODT.
