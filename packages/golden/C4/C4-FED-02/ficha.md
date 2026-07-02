# Golden C4-FED-02 (ficha de record) — EMISIÓN BCF 3.0

```
id:           C4-FED-02
contrato:     C4 (federación) · schema 0.1.0 · service services/federacion 0.2.0 (Fase II·h3)
entrada:      LAS MISMAS entradas CONGELADAS que C4-FED-01, byte a byte (D14):
                ARQ.ifc 653a359154112146d82ca02de0fde2ee · EST.ifc b84cb79c4a7cf4b560148340bc8dc305
              + reglas.json idéntico (md5 fc16bee23d074a1f2a3424100e8877f7)
esperado:     expected.json — manifiesto e informe como en el 01 MÁS la emisión (tarea 1.2):
              informe_qa.bcf = {version 3.0, emitido: TRUE, carpeta: 'bcf'}, bcf_topic_guid
              por incidencia (uuid5, D13), bcf_generacion (autor/fecha inyectados) y
              bcf_md5: el ÁRBOL BCF 3.0 anclado por md5 de fichero (D12) —
              bcf.version + 3 topics (markup.bcf; viewpoint.bcfv solo en INC-03, la única
              incidencia con GUIDs de elemento; SIN cámara: no hay IFC derivado, D6).
oráculo:      RECOMPUTE + EMISIÓN con el service real: federar+validar+emitir_bcf sobre las
              entradas congeladas; los md5 del árbol provienen de la emisión real verificada
              (XML bien formado, determinismo doble-run, 2026-07-02).
tolerancia:   conteos y estados EXACTOS; traslación ±1e-6 m, rotación ±1e-9°; el árbol BCF
              se compara BYTE A BYTE (md5 por fichero). Regla de oro en tolerancias.json.
responsable:  JM (firma = Llave 2: tag federacion-v0.2.0, D15)
```

## Cómo la ejercita el runner (Fase II·h3 — D14)

`run_case_c4` descubre el caso por glob y, al ver `informe_qa.bcf.emitido == true` en el
expected, ANTEPONE el paso de emisión al diff del informe: `emitir_bcf(informe_recomputado,
tmp/bcf, caso='C4-FED-02', autor/fecha de bcf_generacion)` → (1) el árbol emitido se compara
contra `bcf_md5` (md5 por fichero, byte a byte) y (2) el informe actualizado (emitido=true,
carpeta, bcf_topic_guid) se compara contra el expected con la política de comparación del 01
(texto libre fuera del diff). Los checks anclados y el recompute del 01 se conservan
ÍNTEGROS: 19 checks. **C4-FED-01 no se toca: queda como record intocado del contract-first.**

## Ficheros

- `entrada/` — MISMAS entradas congeladas que C4-FED-01 (byte a byte, con su procedencia).
- `reglas.json` — idéntico al del 01 (mismo md5: la federación no cambia, cambia la emisión).
- `expected.json` — oráculo del 01 + bcf (emitido) + bcf_topic_guid + bcf_generacion + bcf_md5.
- `tolerancias.json` — tolerancias + la regla de oro (árbol BCF byte a byte).

*Predimensionado/asistencia; a revisar y firmar por técnico competente (Llave 2).*
