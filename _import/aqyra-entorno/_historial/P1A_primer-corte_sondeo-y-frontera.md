# P1·A — Primer corte: sondeo de endpoints + frontera del "proveedor de entorno"

**Fecha:** 2026-06-27 · **Procedencia:** sub-dirección P1 · Aqyra · sondeo en vivo sobre Can Cabassa. **Para visto bueno de JM antes de implementar** (la frontera es nueva; el alcance lo cierra JM).

---

## 1. Sondeo en vivo (qué devuelve cada servicio, comprobado hoy)

### Catastro — WFS Cadastral Parcels (`wfsCP.aspx`)
- **Parcela propia** — `STOREDQUERY_ID=GetParcel&refcat=0419901DF2901H&srsname=EPSG::25831`.
  - GML 3.2, `cp:CadastralParcel`, **CRS EPSG:25831**, orden de coordenadas **E N**.
  - Geometría `MultiSurface → Surface → PolygonPatch → exterior → LinearRing → posList` (lista plana).
  - Atributos: `areaValue` (**11.884 m²**), `nationalCadastralReference`, `referencePoint` (420286.12 4591705.32), `inspireId`.
- **Vecinas** — `STOREDQUERY_ID=GetNeighbourParcel&refcat=…` → devuelve **la parcela + las colindantes** (en Can Cabassa: 3 features; vecinas 0419912DF2901H 770 m² y 0419902DF2901H 759 m²). Limpio, sin bbox.
- *Nota:* el GetFeature **ad-hoc por bbox** dio error de aplicación; el camino bueno son las **stored queries** (`GetParcel`, `GetNeighbourParcel`, `GetParcelsByZoning`).

### Catastro — WFS Buildings (`wfsBU.aspx`)
- Stored queries disponibles (confirmado): `GetBuildingByParcel` (huella), **`GetBuildingPartByParcel`** (partes, **nº de plantas**), `GetOtherBuildingByParcel`, `GetAllConstructionByParcel`. Namespace `bu:Buildings:3.0`.
- El nº de plantas (`numberOfFloorsAboveGround`) vive en la **BuildingPart** → es la base de la altura (decisión 3). *(El render del GML de BU quedó pendiente por un atasco de caché del navegador; la estructura es la estándar INSPIRE-BU; se confirma al implementar con el GML real.)*

### CartoCiudad — geocoder REST
- `…/geocoder/api/geocoder/reverseGeocode?lon=…&lat=…` → **JSON limpio**: `muni` (Sant Cugat del Vallès), `tip_via` (CAMINO), `address` (CAN CABASSA), `portalNumber` (32), `postalCode` (08195), `poblacion` (Mira-Sol) y **`refCatastral`** (cruza con Catastro). Para **viales** se usa el WFS/`find` de CartoCiudad (callejero/carreteras).

### Notas de acceso (decisivas para la arquitectura)
- **`web_fetch` surface el JSON de CartoCiudad pero NO el GML de Catastro** (cuerpo vacío). Desde el navegador, además, hay **CORS**. ⇒ **proxy server-side obligatorio** (patrón del `/__aqyra/llm`), que además **parsea GML→GeoJSON** en el servidor.
- Todo en **ETRS89 / EPSG:25831** → coherente con la georref ya implementada (CRS configurable por proyecto).

---

## 2. Frontera propuesta: "proveedor de entorno" (para tu visto bueno)

**Idea:** una interfaz única `EnvironmentProvider` detrás de la cual viven los proveedores (estatal primero; ICGC como plugin después, decisión 1). El resultado se normaliza a **GeoJSON abierto** (frontera diff-able) y se puede **congelar como snapshot** del proyecto (decisión 4). **No toca el IFC del activo** (decisión 2): alimenta una capa de **contexto visual**.

**Formato abierto en la frontera (GeoJSON normalizado), un Feature por elemento:**

```
FeatureCollection (crs: EPSG:25831)
  Feature {
    properties: {
      kind: "parcel" | "building" | "road",
      sourceId, source: "catastro-cp" | "catastro-bu" | "cartociudad",
      refcat?, areaValue?,            // parcelas
      floorsAbove?, heightEstimate?,  // edificios: plantas × altura_tipo
      roadName?, roadType?            // viales
    },
    geometry: Polygon | MultiPolygon | LineString
  }
```

**Interfaz (borrador, sin implementar):**
- `getParcels(refcat)` → propia + vecinas (Catastro `GetNeighbourParcel`).
- `getBuildings(refcat)` → huellas + plantas (Catastro `GetAllConstructionByParcel` / `GetBuildingPartByParcel`), `heightEstimate = floorsAbove × altura_tipo` (altura_tipo configurable, p. ej. 3,0 m).
- `getRoads(bbox|refPoint)` → viales (CartoCiudad).

**Flujo híbrido (decisión 4):** explorar en vivo (proxy → normaliza) y, al "fijar" el proyecto, **escribir `entorno.snapshot.geojson`** versionado.

**Solo fuentes oficiales (decisión 5):** Catastro + CartoCiudad en este corte; sin OSM/Overture. Atribución visible.

**Dos llaves (frontera nueva):** golden de **parseo** con *fixtures del GML real de Can Cabassa ya capturado hoy* (parcela + vecinas) → asserta nº de features, refcat, área, anillo cerrado, CRS y nº de plantas→altura. La IA prepara; **JM firma**.

---

## 3. Plan de implementación del primer corte (cuando des el OK)

1. **Proxy `/__aqyra/geo`** en el dev server: reenvía a Catastro CP/BU y CartoCiudad, resuelve CORS y **convierte GML→GeoJSON** normalizado.
2. **Módulo `environment/` (TS):** interfaz `EnvironmentProvider` + proveedor estatal (Catastro+CartoCiudad) + normalizador + snapshot.
3. **Golden** con los fixtures reales capturados hoy (parcela 11.884 m² + 2 vecinas).
4. **Capa de contexto visual** en el visor/maqueta: dibuja parcelas (relleno), vecinos (huella extruida por `heightEstimate`) y viales — como contexto, no IFC.
5. **Para-firma** de JM con el bump y el anclado en `versions.lock`.

---

## 4. Lo que confirmo contigo antes de escribir código

- ¿**Altura tipo por planta** por defecto? (propongo **3,0 m**; configurable por proyecto).
- ¿Arranco por **parcela + vecinas** (Catastro) y añado **viales** (CartoCiudad) en el mismo corte, o dejo viales para el segundo paso?
- ¿El snapshot se guarda **dentro de la carpeta del proyecto** del activo (junto al IFC) como `entorno.snapshot.geojson`?
- ¿Confirmas que la huella de vecinos se extruye como **volumen simple** (sin tejados) solo para contexto visual?

*La IA prepara y propone; el alcance y la frontera los cierra JM. No escribo código hasta tu OK.*
