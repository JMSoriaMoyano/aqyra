# P1·A — Decisiones de JM sobre la reconstrucción del entorno

**Fecha:** 2026-06-27 · **Procedencia:** sub-dirección P1 · Aqyra · cerrado por JM una a una sobre el estudio `P1A_estudio_fuentes-geodatos.md`.

## Decisiones cerradas

1. **Alcance geográfico:** backbone **estatal** (IGN + Catastro + CartoCiudad, toda España) con **ICGC como plugin** autonómico para la alta resolución del piloto. Capa de proveedores intercambiable.
2. **Qué entra al IFC:** **solo el activo** del proyecto. El entorno (terreno, parcela, viales, vecinos) es **contexto visual** en el visor; no se autora al IFC.
3. **Altura de vecinos:** **nº de plantas de Catastro** (BuildingPart) × altura tipo como primaria. nDSM LiDAR queda como refinamiento posterior.
4. **Consumo:** **híbrido** — exploración en vivo + **congelar snapshot versionado y diff-able** al fijar el proyecto.
5. **Licencias:** **solo oficiales CC-BY / abiertas** en v0 (IGN, CartoCiudad, Catastro, ICGC, Copernicus). **Fuera OSM (ODbL) y Overture (CDLA)** para no arrastrar share-alike al entregable. Atribución visible.
6. **Primera capa:** **parcela + vecinos + viales (vector)** — "la planta del entorno".

## Primer corte que se deriva (a confirmar antes de código)

- **Objetivo:** "planta del entorno" como **contexto visual** alrededor del activo ya georreferenciado de Can Cabassa.
- **Datos y servicios (solo oficiales):**
  - Parcela propia + vecinas → **Catastro WFS Cadastral Parcels** (por bbox).
  - Huellas de edificios vecinos → **Catastro WFS Buildings**, extruidas por **nº de plantas**.
  - Viales → **CartoCiudad** (WFS/REST).
- **Frontera abierta:** el resultado se normaliza a **GeoJSON** (formato abierto, diff-able) y se **congela como snapshot versionado** del proyecto; la exploración previa puede ir en vivo.
- **No toca el IFC del activo** (decisión 2): el entorno se dibuja como capa de contexto en el visor.
- **Arquitectura:** interfaz única de "proveedor de entorno"; implementación estatal primero, ICGC como plugin (decisión 1).

## Notas técnicas (heredadas del estudio)

- **CORS:** servicios españoles que no envían cabeceras CORS → **proxy server-side** (patrón del `/__aqyra/llm` actual).
- **Límite Catastro WFS:** bbox ≤ 4 km² y ≤ 5.000 elementos → trocear por teselas.
- **CRS:** ETRS89; en Cataluña UTM 31N = **EPSG:25831** (coherente con la georref ya implementada).
- **Dos llaves:** esta es **frontera nueva** (no C1). Aplica igualmente la disciplina: formato abierto + golden del parseo de cada proveedor + snapshot reproducible; la IA prepara, **JM firma**.

## Pendiente (no v0)

Topografía/rasante (MDT), ortofoto de fondo, nDSM LiDAR, niveles autonómicos fuera de Cataluña, e integración OSM/Overture si en el futuro se acepta su licencia.

*La IA prepara y propone; el alcance lo ha cerrado JM. Confirmar el primer corte antes de escribir código.*
