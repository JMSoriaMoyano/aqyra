# Memoria mínima — Caso LIN-01 (soporte georreferenciado de obra lineal)

> Predimensionado/asistencia. **A revisar y firmar por técnico competente (Ingeniero de Caminos).**
> NDP marcados **[confirmar AN]**. PT 5.1 (Ola 5) · `iso19650-openbim` v0.5.0.

## 1. Objeto y alcance

Apertura de la vía **C1 §4bis (IFC 4.3 Alignment + GIS)**: lectura de un IFC 4.3 de alineación,
emisión del **modelo neutro lineal** y validación de coherencia geométrica y georreferencia. **No
es un cálculo de trazado** (Norma 3.1-IC) ni de firmes (6.1-IC), que corresponden a la disciplina
`obras-lineales` (PT 5.2+). No hay FEM ni grafo de red: la alineación es **referenciación lineal
por PK** (curva paramétrica 1D).

## 2. Soporte y normativa

- Esquema **IFC 4.3 (IFC4X3)**; entidades `IfcAlignment` (planta/alzado/peralte vía
  `IfcAlignmentHorizontal/Vertical/Cant` → `IfcAlignmentSegment.DesignParameters`),
  `IfcRoad`, georreferencia `IfcMapConversion` + `IfcProjectedCRS`.
- Georreferencia: **EPSG:25830** (ETRS89 / UTM huso 30N), datum vertical EGM2008 [confirmar AN].
- Umbrales geométricos de la **Norma 3.1-IC** (trazado): empleados solo como aviso informativo
  (A de clotoide en [R/3, R]); el dimensionado y la velocidad de proyecto Vp los fija la disciplina.

## 3. Datos del eje

Recta (100 m) → clotoide de entrada (60 m, A=134,16) → curva circular (80 m, R=300 m, giro a
izquierda) → clotoide de salida (60 m) → recta (100 m). **L = 400 m (PK 0+000 a 0+400).** Alzado:
rampa +2,0 % (150 m) → acuerdo convexo Kv=2000 (100 m) → pendiente −3,0 % (150 m); cota de salida
98,000 m sobre la cota local 100,000 m de origen. Peralte: bombeo 0 % en rectas, transición a
+7,0 % en las clotoides y 7,0 % constante en la curva.

## 4. Comprobaciones (validación de alineación/georreferencia)

| Comprobación | Criterio | Resultado |
|---|---|---|
| Unidades | SI declaradas (longitud = m) | ✔ |
| PK monótono y contiguo | pk[i+1] = pk[i] + L[i] | ✔ planta/alzado/peralte |
| Continuidad de planta | salto entre segmentos ≤ 0,05 m | ✔ máx 0,0001 m |
| Tangencia de planta | quiebro ≤ 1·10⁻³ rad | ✔ máx 0,0 rad |
| Continuidad de alzado | cota y pendiente encadenan | ✔ |
| Georreferencia | CRS (EPSG) + origen E/N presentes y coherentes | ✔ EPSG:25830 |
| Radios/clotoides (3.1-IC) | A en [R/3, R] (informativo) | ✔ A=134,16 ∈ [100, 300] |

**Veredicto: CUMPLE.**

## 5. Interoperación GIS (decisión nº3)

Soporte dual **GeoJSON + IFC 4.3**: el IFC es el modelo de ingeniería (alineación paramétrica
completa); el **GeoJSON** (`eje-carretera.geojson`, LineString en EPSG:25830) es el puente hacia
cartografía e hidrología de cuencas (Ola 6, drenaje). No se implementa hidrología en este PT.

## 6. Ganchos a la disciplina (PT 5.2+)

El modelo neutro lineal deja previstas (None) las claves `secciones_tipo`, `firme`
(categoría de tráfico/explanada, 6.1-IC) y `terreno`, para que la disciplina `obras-lineales` las
rellene sin redefinir el esquema.

## 7. Conclusión

El eje IFC 4.3 georreferenciado se lee íntegro al modelo neutro lineal y supera la validación de
coherencia geométrica y georreferencia (CUMPLE). Soporte listo para la disciplina de obra lineal.
**A revisar y firmar por técnico competente.**
