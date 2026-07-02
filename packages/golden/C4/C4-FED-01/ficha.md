# Golden C4-FED-01 (ficha de record)

```
id:           C4-FED-01
contrato:     C4 (federación) · schema 0.1.0 · service services/federacion 0.1.0 (Fase II·h2)
entrada:      entrada/ARQ.ifc + entrada/EST.ifc — dos disciplinas del MISMO edificio piloto,
              compiladas con engines/ifc (narración→IFC, iso19650-openbim 0.10.0) desde
              entrada/*.alto.json y CONGELADAS byte a byte (md5 en expected.json y reglas.json):
                ARQ 653a359154112146d82ca02de0fde2ee (2 muros+puerta · losa · ascensor · Planta Baja/1)
                EST b84cb79c4a7cf4b560148340bc8dc305 (4 pilares · forjado · 2 zapatas · Nivel 00/01)
              + reglas.json (EPSG:25830, punto base DECLARADO común, dedup elementos=nunca,
                estructura espacial=unificar-por-nombre, pack ids/proyecto-piloto/v1)
esperado:     expected.json — maestro_manifiesto (D1: manifiesto = fuente de verdad; Site
              'Emplazamiento' y Building 'Edificio' unificados por nombre, 4 storeys con
              procedencia, GUIDs preservados) + informe_qa (R1/R2/R3 pass · R4-GEORREF fail
              en AMBOS (origen=modulo) · R5-PLANTAS fail en EST — 3 incidencias, estados S1,
              veredicto no-conforme, BCF 3.0 declarado y no emitido)
oráculo:      MANUAL (2.1, D4) + RECOMPUTE con el service (2.2, D10: el service lo reprodujo
              con 0 diffs) — hechos verificados con ifcopenshell 2026-07-02 sobre
              los IFC congelados: doble clasificación 'bSDD - IFC 4.3'+'Uniclass 2015' en los
              elementos objetivo (ARQ 5/5, EST 7/7); Pset_WallCommon.IsExternal en 2/2 muros;
              Pset_Estructurando_Spec.Material en ARQ 4/4 y EST 7/7; IfcMapConversion=0 e
              IfcProjectedCRS=0 en ambos (R4 fail adrede: la federación lo resuelve por punto
              base declarado — ADR); storeys EST 'Nivel 00/01' rompen 'Planta .*' (R5 fail
              adrede; GUIDs de las 2 plantas en INC-03).
tolerancia:   conteos y estados EXACTOS; traslación ±1e-6 m y rotación ±1e-9° (ACTIVAS desde
              2.2: el runner recomputa con el service). Regla de oro en tolerancias.json.
responsable:  JM (firma = Llave 2; release/firma del service: decidir en el cierre de 2.2 o en 1.2)
```

## Cómo la ejercita el runner (Fase II·h2 — costura CERRADA)

**0 · RECOMPUTE (antepuesto en Fase II·h2, D10):** el runner ejecuta el service real —
`federar(entradas, reglas)` + `validar(maestro, ids)` con `services/federacion` (import de
path, mismo patrón que `engines/ifc`) — y compara manifiesto e informe recomputados contra
este **MISMO** `expected.json` con `tolerancias.json`. El oráculo manual del 2.1 quedó
VERIFICADO por el recompute (0 diffs) — no hubo que tocar el expected.

*Política de comparación:* la semántica del contrato (ids, resultados, conteos, GUIDs,
severidades, estados, veredicto, md5, transformaciones) se compara EXACTA (números con las
tolerancias); los campos de TEXTO LIBRE (`titulo`, `detalle`), las claves `_*` (comentario)
y el literal de `procedencia.generado_por`/`fecha` (metadato de generación: el expected lo
escribió el oráculo manual, el recompute lo firma el service — `reglas_md5` sí se compara
exacto) quedan fuera del diff. Su presencia/tipo la exige el esquema.

**Checks anclados del 2.1 (se conservan ÍNTEGROS):**

1. `reglas.json`, `expected.maestro_manifiesto` y `expected.informe_qa` **conforman** los tres
   esquemas de `packages/contracts/C4-federacion/`.
2. Los IFC congelados de `entrada/` coinciden con sus **md5** declarados (en `expected.json`,
   en `reglas.json` y en el manifiesto — triple coherencia).
3. **Coherencia interna**: mismos ids de modelo en reglas/manifiesto/informe; el pack IDS de
   las reglas es el del informe y está **anclado** en `versions.lock [packs.ids]`; todo
   requisito con `origen='ids'` existe en el `.ids` del pack (R4-GEORREF es `origen='modulo'`,
   ficha C4 §3: "no todo es IDS"); el veredicto es consistente con los resultados.

**Costura CERRADA (Fase II·h2, hilo 2.2):** `services/federacion` 0.1.0 existe y el runner
antepone *federar+validar* contra este MISMO `expected.json` (paso 0 de arriba). El esperado
NO cambió — misma costura que C1 en Fase 0 → Fase I.

## Ficheros

- `entrada/ARQ.alto.json` + `entrada/EST.alto.json` — procedencia de los IFC (narración).
- `entrada/ARQ.ifc` + `entrada/EST.ifc` — entradas CONGELADAS (la verdad compilada).
- `reglas.json` — entrada de `federar()` (conforma `reglas-federacion.schema.json`).
- `expected.json` — el oráculo (manifiesto + informe; procedencia independiente del runner).
- `tolerancias.json` — tolerancias + la regla de oro.

*Predimensionado/asistencia; a revisar y firmar por técnico competente (Llave 2).*
