# Golden C4-FED-04 — Federación mixta (INTEGRACIÓN 1.2×1.3, tarea 1.4)

> El caso que ejercita **todo junto** (D21): federar + validar + emitir sobre una
> federación MIXTA (un modelo sucio + uno limpio). Es exactamente lo que producirá el
> primer proyecto real: informe con `avisos_lectura` **y** emisión de topics BCF.
> Hasta este caso, el 02 emitía con modelos LIMPIOS y el 03 declaraba avisos SIN emitir.

## Entradas (congeladas — RE-USADAS byte a byte, patrón D14: cero ficheros nuevos)

- `entrada/SUCIO.ifc` — el congelado de C4-FED-03 (md5 `1dd956ca02fd085f06a2eaf6dcb10988`),
  con sus 3 suciedades de diseño (D18). Modelo `SUC`, disciplina ARQ, **S1**.
- `entrada/EST.ifc` — el congelado de C4-FED-01 (md5 `b84cb79c4a7cf4b560148340bc8dc305`).
  Modelo `EST`, disciplina EST, **S3**.

## Qué ancla que ningún caso anclaba (D21/D23)

- **Interacción 1.2×1.3**: informe con `avisos_lectura` + `emitido=true` + topics BCF.
- **Procedencia de avisos POR MODELO**: los 3 avisos son de `SUC`; `EST` (limpio) no
  aparece en `avisos_lectura` — la clave declara QUIÉN aporta la suciedad.
- **Estados HETEROGÉNEOS**: `SUC=S1, EST=S3` → `maestro=S1` (min(S), política de v0 de
  qa.py) — primera vez con estados distintos.
- **Transformación NO trivial**: puntos base DISTINTOS y `rotacion_deg` 14.5 / −7.25 —
  las tolerancias del recompute (±1e-6 m, ±1e-9°) tienen por fin valores reales. La
  rotación es METADATO declarado (v0 no rota geometría — el caso no lo finge).

## Oráculo (verificado a mano antes de anclar)

- Manifiesto: 7 agregados — Site/Building unificados por nombre (`SUC`+`EST`); storeys
  por modelo, con el `"(sin nombre)"` de SUC visible. Política `unificada-por-nombre`
  (comparable con 01/03; `mantener-separada` es el caso 05).
- Informe: cada fila `por_modelo` coincide con la fila CONGELADA de su caso de
  procedencia (SUC == 03, EST == 01, mismos ficheros y mismo pack); avisos == 03;
  GUIDs de incidencia == casos de origen.
- Emisión: 4 incidencias → 4 topics (R4-GEORREF ×2 SIN viewpoint — regla de módulo sin
  GUIDs; R5-PLANTAS ×2 CON viewpoint); árbol BCF 3.0 = 7 ficheros anclados por md5
  (D12) con GUIDs `uuid5(NAMESPACE_AQYRA, 'C4-FED-04/INC-xx')` (D13).

## Regla de oro

Un fallo NO se arregla aflojando esta golden. Las entradas son las CONGELADAS de 03 y
01: cambiarlas es cambiar el DISEÑO del caso y pasa por decisión explícita con JM.
