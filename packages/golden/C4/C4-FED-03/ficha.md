# Golden C4-FED-03 — IFC sucio (camino feliz-degradado, tarea 1.3)

> Ancla el ADR de la ficha C4 **"parser sucio = tarea 1.3"** (cerrado en Fase II·h4 con
> D16–D20): un IFC real ("sucio") entra por `federar()`/`validar()` y sale con
> **degradaciones DECLARADAS**, no con un stack trace ni con silencio.

## Entrada (congelada)

- `entrada/SUCIO.ifc` — **sintético ensuciado adrede** (D18): el `ARQ.ifc` congelado de
  C4-FED-01 (md5 `653a359154112146d82ca02de0fde2ee`) procesado por `entrada/ensuciar.py`
  (determinista: GUIDs uuid5 con semilla fija + cabecera SPF normalizada). md5 anclado en
  `expected.json`.
- Suciedades inyectadas (cada una por separado, taxonomía D17):
  - **S1** · `Name=None` en el storey 'Planta 1' → nodo `"(sin nombre)"` + aviso `nombre-vacio`.
  - **S2** · segundo storey 'Planta Baja' → aviso `nombre-duplicado` (unificados en UN nodo).
  - **S3** · segundo `IfcProject` ('FANTASMA', huérfano) → aviso `multi-proyecto`
    (R4-GEORREF pasa a contar 2 proyectos).

## Oráculo (verificado a mano antes de anclar)

- Manifiesto: 5 agregados (Project + Site + Building + 2 Storey), con `"(sin nombre)"`
  visible y 'Planta Baja' con las DOS entidades unificadas por nombre.
- Informe: `avisos_lectura` con exactamente 3 avisos (`multi-proyecto`, `nombre-vacio`,
  `nombre-duplicado`) — la clave existe SOLO aquí (D20: los casos limpios ni se enteran);
  R5-PLANTAS falla en el storey sin nombre (GUID `2VR4ZUrG9A9Bh0O0cEw4bM` — la suciedad
  acaba siendo materia de QA real); R4-GEORREF falla como en el 01 (sin georref).
- Suciedad BLOQUEANTE (fichero ausente / no parsea / md5 ≠ declarado → `LecturaIfcError`
  con diagnóstico): cubierta por pytest (`services/federacion/tests/test_lectura.py`),
  NO por esta golden (D19: el golden ancla el camino feliz-degradado, no los errores).

## Regla de oro

Un fallo NO se arregla aflojando esta golden. Ensuciar más (o menos) el IFC es DISEÑO
del caso (D18) y pasa por re-congelar `SUCIO.ifc` + re-anclar el expected con OK de JM.
