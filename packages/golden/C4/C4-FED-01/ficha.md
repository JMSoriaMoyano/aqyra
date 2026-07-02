# Golden C4-FED-01 (ficha de record)

```
id:           C4-FED-01
contrato:     C4 (federación) · contract-first, SIN service (schema 0.1.0; el service es la tarea 1.1)
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
oráculo:      MANUAL (modo anclado, D4) — hechos verificados con ifcopenshell 2026-07-02 sobre
              los IFC congelados: doble clasificación 'bSDD - IFC 4.3'+'Uniclass 2015' en los
              elementos objetivo (ARQ 5/5, EST 7/7); Pset_WallCommon.IsExternal en 2/2 muros;
              Pset_Estructurando_Spec.Material en ARQ 4/4 y EST 7/7; IfcMapConversion=0 e
              IfcProjectedCRS=0 en ambos (R4 fail adrede: la federación lo resuelve por punto
              base declarado — ADR); storeys EST 'Nivel 00/01' rompen 'Planta .*' (R5 fail
              adrede; GUIDs de las 2 plantas en INC-03).
tolerancia:   conteos y estados EXACTOS; traslación ±1e-6 m y rotación ±1e-9° (aplican cuando
              el service recompute en 1.1). Regla de oro en tolerancias.json.
responsable:  JM (firma = Llave 2; la Llave 2 de ADOPCIÓN llega con el service en 1.1)
```

## Cómo la ejercita el runner en Fase II·h1 (modo ANCLADO — el service NO existe)

1. `reglas.json`, `expected.maestro_manifiesto` y `expected.informe_qa` **conforman** los tres
   esquemas de `packages/contracts/C4-federacion/`.
2. Los IFC congelados de `entrada/` coinciden con sus **md5** declarados (en `expected.json`,
   en `reglas.json` y en el manifiesto — triple coherencia).
3. **Coherencia interna**: mismos ids de modelo en reglas/manifiesto/informe; el pack IDS de
   las reglas es el del informe y está **anclado** en `versions.lock [packs.ids]`; todo
   requisito con `origen='ids'` existe en el `.ids` del pack (R4-GEORREF es `origen='modulo'`,
   ficha C4 §3: "no todo es IDS"); el veredicto es consistente con los resultados.

**Costura marcada (idéntica a la de C1 en Fase 0):** cuando exista `services/federacion`
(tarea 1.1), el runner antepone el paso *federar+validar* (entradas → manifiesto+informe
recomputados) contra este **MISMO** `expected.json`. El esperado no cambia.

## Ficheros

- `entrada/ARQ.alto.json` + `entrada/EST.alto.json` — procedencia de los IFC (narración).
- `entrada/ARQ.ifc` + `entrada/EST.ifc` — entradas CONGELADAS (la verdad compilada).
- `reglas.json` — entrada de `federar()` (conforma `reglas-federacion.schema.json`).
- `expected.json` — el oráculo (manifiesto + informe; procedencia independiente del runner).
- `tolerancias.json` — tolerancias + la regla de oro.

*Predimensionado/asistencia; a revisar y firmar por técnico competente (Llave 2).*
