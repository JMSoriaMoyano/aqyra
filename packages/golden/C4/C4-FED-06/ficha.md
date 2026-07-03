# Golden C4-FED-06 — IFC federado DERIVADO + cámara BCF (v0.x, D26–D30)

> El caso que cierra la decisión que **D6 aplazó**: el Maestro por fin se puede ABRIR.
> Ancla el `.ifc` federado derivado por **md5 byte a byte** (D26) y el árbol BCF donde
> el viewpoint gana **cámara perspectiva determinista** (D29). Hasta este caso, el
> manifiesto era la única salida federada y los topics BCF iban sin ojos.

## Entradas (congeladas — RE-USADAS byte a byte, patrón D14/D21: cero ficheros nuevos)

- `entrada/ARQ.ifc` — el congelado de C4-FED-01 (md5 `653a359154112146d82ca02de0fde2ee`).
  Modelo `ARQ`, rotación **0.0°**, punto base (337000.0, 4610000.0, 700.0), **S2**.
- `entrada/EST.ifc` — el congelado de C4-FED-01 (md5 `b84cb79c4a7cf4b560148340bc8dc305`).
  Modelo `EST`, rotación **30.0°**, punto base (337012.5, 4609987.5, 701.25), **S2** —
  la rotación que el derivado MATERIALIZA (a diferencia del 04, donde era solo metadato).

## Qué ancla que ningún caso anclaba (D26–D30)

- **El derivado por md5 BYTE A BYTE** (`maestro_manifiesto.ifc_derivado.md5`, D26):
  cabecera SPF determinista — `time_stamp` inyectado de `derivado_generacion` (patrón
  bcf_generacion/D13) y `preprocessor/originating` = `aqyra-federacion` SIN versión ni
  string de build del wheel. Doble anclaje: el check dedicado del runner + el diff del
  manifiesto (ifc_derivado entra en el recompute).
- **La materialización D27**: placement RAÍZ por modelo (traslación + rotación 30° de
  EST alrededor de Z; la geometría interna NO se toca), IfcProject ÚNICO, GUIDs
  preservados (6+7 elementos), y el derivado CUMPLE R4-GEORREF de serie
  (IfcMapConversion + IfcProjectedCRS EPSG:25830) — los MODELOS DE ENTRADA siguen sin
  georreferenciar, por eso el informe sigue fallando R4 (la entrada se valida, no el
  derivado).
- **La cámara D29** en el viewpoint del topic con GUIDs (R5-PLANTAS/EST): bbox de los
  ORÍGENES de placement absolutos de los storeys de EST (= punto base de EST, ambos sin
  placement propio → placement raíz), bbox degenerado → d = D_MIN = 1 m, K_CAMARA = 1,
  FOV 60°, aspecto 16/9, floats a 6 decimales fijos. Los R4 (sin GUIDs) siguen SIN
  viewpoint. 02/04 (sin derivado) quedan intactos POR CONSTRUCCIÓN.

## Oráculo (verificado a mano antes de anclar — 2026-07-03)

- **Determinismo**: DOS ejecuciones completas (federar→derivar→validar→emitir) →
  md5 del derivado IDÉNTICO (`dcb1e14460f3556107ce35d6dade16c3`) y árbol BCF idéntico.
- **Cámara cotejada contra el bbox calculado APARTE** (a mano): posición = pb+(1,−1,1) =
  (337013.5, 4609986.5, 702.25); dirección = (−1,1,−1)/√3 = (−0.577350, 0.577350,
  −0.577350); up = Gram-Schmidt(+Z) = (−1,1,2)/√6 = (−0.408248, 0.408248, 0.816497).
- **Procedencia**: cada fila `por_modelo` del informe == fila congelada de C4-FED-01
  (mismas entradas byte a byte, mismo pack); sin `avisos_lectura` (modelos limpios);
  estados S2/S2 → maestro S2.
- **Derivado sano**: abre con ifcopenshell, IFC4X3, 1 IfcProject, 13 elementos (6+7),
  1 IfcMapConversion, 1 IfcProjectedCRS.
- Emisión: 3 incidencias → 3 topics; árbol BCF = 5 ficheros anclados por md5 (D12) con
  GUIDs `uuid5(NAMESPACE_AQYRA, 'C4-FED-06/INC-xx')` (D13).

## Regla de oro

Un fallo NO se arregla aflojando esta golden. El md5 del derivado solo se re-ancla si
cambia el COMPORTAMIENTO documentado del writer (decisión explícita con JM); un bump de
versión del service no puede moverlo (la cabecera no lleva versión, D26). Las entradas
son las CONGELADAS del 01: cambiarlas es cambiar el DISEÑO del caso.
