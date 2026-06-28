# P1·A — Estudio de fuentes públicas de geodato para reconstruir el entorno

**Fecha:** 2026-06-27 · **Procedencia:** sub-dirección P1 (Visor/Editor IFC) · Aqyra · IA investiga; **para comentar con JM antes de escribir código**.
**Encargo de JM:** antes de desarrollar herramientas de diseño, reconstruir el entorno del activo —**ubicación, topografía, límites de parcelas, viales y otros edificios (con sus alturas)**— a partir de fuentes públicas georreferenciadas que ofrezcan **servicio online / API** implementable. Este documento inventaría y compara esas fuentes. **No contiene desarrollo.**

---

## 1. Resumen ejecutivo

Hay **mucho más que el Catastro**, y casi todo es gratuito y con licencia abierta. Las fuentes se ordenan en tres niveles que se complementan, no compiten:

- **Estatal (IGN-CNIG + Catastro + CartoCiudad):** cobertura de toda España, oficial, formato abierto OGC. Es el cimiento.
- **Autonómico (ICGC en Cataluña):** la **mejor resolución** para nuestro piloto (Can Cabassa) — LiDAR 8 pts/m², MDS 1 m (25 cm en el área metropolitana de Barcelona), ortofoto 15 cm. Cada CCAA tiene su instituto cartográfico equivalente, así que el patrón generaliza.
- **Europeo/global (Copernicus, GHSL/JRC, EUBUCCO, Overture, OSM):** respaldo y enriquecimiento (sobre todo alturas de edificio), útil donde no llega lo nacional/autonómico o para homogeneizar.

**Distinción clave que pидió JM ("servicio online / API"):** no todas las fuentes son un *servicio en vivo*. Conviene separar:

- **Servicios en vivo (OGC/REST/Overpass)** — se consultan por petición HTTP con un *bounding box* o una dirección, y devuelven justo el trozo que pides. **Esto es lo implementable como API.** (Catastro, IGN, CartoCiudad, ICGC, OSM/Overpass, OpenTopography.)
- **Descargas masivas (ATOM/GeoParquet/CSV)** — ficheros por municipio o por release que bajas y procesas en lote. No son API en vivo; sirven como enriquecimiento offline. (EUBUCCO, Overture, GHS-OBAT, LiDAR bruto.)

**Recomendación de partida (a discutir):** construir el entorno v0 sobre **servicios en vivo estatales + ICGC**, y reservar las descargas masivas (Overture/EUBUCCO) solo si falta el atributo de altura.

---

## 2. Qué capas necesitamos (y a qué tema INSPIRE corresponden)

| Capa del entorno | Tema INSPIRE | Geometría que buscamos |
|---|---|---|
| Ubicación / orientación | (georreferencia) | punto + CRS (ya resuelto con Catastro OVC) |
| Topografía / rasante | Elevation (Anexo II) | MDT (terreno) y MDS (superficie) — raster |
| Límites de parcelas (la nuestra + vecinas) | Cadastral Parcels | polígonos vectoriales |
| Viales | Transport Networks | líneas (eje) y/o polígonos |
| Otros edificios (huella) | Buildings | polígonos vectoriales |
| **Altura de esos edificios** | Buildings / Elevation | nº de plantas (vector) o nDSM = MDS − MDT (raster) |
| Ortofoto (contexto visual) | Orthoimagery | raster |

---

## 3. Inventario de fuentes

### A. Estatales — cobertura toda España

**A1． Dirección General del Catastro** *(ya en uso para la georreferencia)*
- **OVC Coordenadas** (REST/XML): ref. catastral → coordenadas en el EPSG pedido. *Ya implementado en el hilo.*
- **INSPIRE WFS** (GML, vector): tres temas en servicios separados — Cadastral Parcels (`wfsCP.aspx`), Buildings (`wfsBU.aspx`), Addresses (`wfsAD.aspx`). Da **parcela propia y vecinas, huella de edificios y nº de plantas** (en la capa *BuildingPart*, sobre/bajo rasante). **Límite: bbox ≤ 4 km² y ≤ 5.000 elementos por petición.**
- **WMS** de cartografía catastral (raster) y **ATOM** (descarga GML por municipio, refresco ~6 meses).
- Licencia abierta; CRS ETRS89.

**A2． IGN — CNIG / IDEE** (Instituto Geográfico Nacional)
- **PNOA ortofoto:** WMS y **WMTS** (`/wmts/pnoa-ma`) — ortofoto de máxima actualidad como contexto visual del terreno.
- **MDT (terreno):** **WCS** de descarga (GeoTIFF/ASCII) a 5/25/200 m, derivado de PNOA-LiDAR; y WMS de visualización. Sirve la **rasante**.
- **MDS LiDAR (superficie):** WMS de modelo digital de superficies — incluye edificios y vegetación; con el MDT permite **nDSM = altura sobre el terreno**.
- **PNOA-LiDAR:** 3ª cobertura (2022-2025), nubes de puntos 5 pts/m² (descarga, no servicio en vivo).
- **API CNIG / API-Features** y nuevo Iberpix. Licencia CC-BY 4.0.

**A3． CartoCiudad** (IGN + Catastro + INE + Correos)
- **Geocoder REST** (JSON/GeoJSON): búsqueda de calle/portal/ref. catastral ↔ coordenadas, y **geocodificación inversa**. Entidades: `callejero`, `portal`, `carreteras`, `Codpost`, `municipio`, `refcatastral`…
- **WFS** (descarga vector) de la **red viaria** y direcciones; **WMS/WMTS** de callejero.
- Actualización trimestral, **CC-BY 4.0**. Es la vía limpia para **viales** a escala nacional.

### B. Autonómicas — máxima resolución (piloto en Cataluña)

**B1． ICGC** (Institut Cartogràfic i Geològic de Catalunya)
- **WMS/WMTS** de base topográfica y **ortofoto** (color/IR/histórica, con fecha y resolución por GetFeatureInfo).
- **Elevaciones (LiDAR):** **MDT 50 cm** (terreno) y **MDS 1 m** en toda Cataluña, **MDS 25 cm en el Área Metropolitana de Barcelona** (¡incluye Sant Cugat!). WMS de elevaciones/orientación/sombras y descarga. → **alturas de edificio reales por nDSM**.
- **3ª cobertura LiDAR** 8 pts/m² (datacloud ICGC).
- **Geocodificador API** (REST) directo y inverso para Cataluña.
- **3D city models** (proyecto ICGC) — contexto urbano 3D.
- Compatible con Leaflet/OpenLayers/Mapbox; licencia abierta.

> **Generalización:** fuera de Cataluña, el equivalente lo da el instituto cartográfico de cada CCAA (Andalucía, Madrid, C. Valenciana, País Vasco…). La arquitectura debe tratar la fuente autonómica como **plugin intercambiable**; donde no haya, se cae al nivel estatal (IGN).

### C. Europeas / globales — respaldo y enriquecimiento

**C1． Copernicus DEM (GLO-30)** — DSM global 30 m. Servicio vía Copernicus Data Space / **OpenTopography REST API** (`/API/globaldem`, COP30). Respaldo de topografía donde no llegue lo nacional. (EU-DEM 1.1 ya no se descarga desde copernicus.eu; queda en OpenTopoData.)

**C2． GHSL / JRC (Comisión Europea)** — **GHS-BUILT-H** (altura de edificio en raster 100 m, 2018) y **GHS-OBAT** (2.3 B de huellas de Overture enriquecidas con **altura, época, uso, compacidad**). Datos abiertos, acceso por descarga / Earth Engine.

**C3． EUBUCCO v0.1** — base abierta de ~202 M de edificios (UE-27 + Suiza) con **altura (73 %)**, año (24 %) y tipo (46 %), armonizando 50 datasets oficiales + OSM. Descarga (no API en vivo).

**C4． Overture Maps Foundation** — capa global de **buildings** (con altura) y red de transporte, en **GeoParquet** en S3/Azure; se consulta por bbox con DuckDB/GDAL. Releases mensuales (se conservan ~60 días). Enriquecimiento, no servicio OGC.

**C5． OpenStreetMap — Overpass API** (en vivo, JSON): **edificios** (`building`, con `building:levels` y `height` donde estén mapeados), **viales** (`highway`), mobiliario. Cobertura/calidad variable pero consulta por bbox inmediata y muy flexible. Licencia ODbL (atención a la atribución/share-alike).

---

## 4. Tabla comparada

| Fuente | Dato que aporta | Tipo de servicio | Formato | Cobertura | Licencia | En vivo (API)? | Dificultad |
|---|---|---|---|---|---|---|---|
| Catastro OVC | coords ↔ ref. catastral | REST | XML/JSON | España | Abierta | Sí | Baja *(hecho)* |
| Catastro WFS CP/BU/AD | parcelas, huellas, nº plantas, direcciones | WFS | GML | España | Abierta | Sí (bbox ≤4 km²) | Media |
| IGN PNOA | ortofoto | WMS/WMTS | raster | España | CC-BY 4.0 | Sí | Baja |
| IGN MDT | rasante (terreno) | WCS/WMS | GeoTIFF | España | CC-BY 4.0 | Sí | Media |
| IGN MDS LiDAR | superficie (→ nDSM) | WMS | raster | España | CC-BY 4.0 | Sí | Media-alta |
| CartoCiudad | viales, portales, geocoder | REST + WFS | JSON/GeoJSON/GML | España | CC-BY 4.0 | Sí | Baja-media |
| ICGC WMS/WMTS | base + ortofoto 15 cm | WMS/WMTS | raster | Cataluña | Abierta | Sí | Baja |
| ICGC elevaciones | MDT 50 cm + MDS 1 m/25 cm AMB | WMS/WCS/descarga | raster | Cataluña | Abierta | Sí | Media |
| ICGC geocodificador | direcciones ↔ coords | REST | JSON | Cataluña | Abierta | Sí | Baja |
| Copernicus DEM GLO-30 | superficie 30 m | REST (OpenTopo) | GeoTIFF | Global | Abierta | Sí | Media |
| GHS-BUILT-H / GHS-OBAT | altura de edificio | descarga / GEE | raster / tabla | Global | Abierta | No (lote) | Media |
| EUBUCCO | huella + altura/año/tipo | descarga | CSV/GeoPackage | UE-27+CH | Abierta | No (lote) | Media |
| Overture buildings | huella + altura | cloud GeoParquet | Parquet | Global | Abierta (CDLA) | No (lote, bbox) | Media-alta |
| OSM Overpass | edificios+alturas, viales | Overpass | JSON/XML | Global | ODbL | Sí | Media |

---

## 5. Recomendación por capa (borrador, a cerrar con JM)

- **Topografía / rasante:** ICGC **MDT 50 cm** en el piloto; **IGN MDT (WCS)** como estándar nacional; **Copernicus GLO-30** como respaldo global.
- **Límites de parcela (propia + vecinas):** **Catastro WFS Cadastral Parcels** por bbox. Es la fuente oficial y diff-able.
- **Viales:** **CartoCiudad** (nacional, limpio) y/o **ICGC**; **OSM/Overpass** como complemento (aceras, sentido, anchos).
- **Otros edificios (huella):** **Catastro WFS Buildings** (oficial, nacional). Complemento OSM donde falte.
- **Alturas de edificio (lo más delicado):**
  1. *Primaria, vector, nacional:* **nº de plantas de Catastro** (BuildingPart) → altura estimada = plantas × altura tipo.
  2. *Refinada, medida:* **nDSM = MDS − MDT** del **ICGC** (1 m / 25 cm AMB) o del **IGN** (LiDAR) → altura real del volumen construido.
  3. *Respaldo/atributo:* **GHS-OBAT / EUBUCCO / Overture / OSM** donde no haya lo anterior.
- **Ortofoto (contexto):** **ICGC 15 cm** en el piloto; **PNOA** nacional.

> Idea de arquitectura (solo para situar la conversación, no es desarrollo): una **capa de "proveedores de entorno" intercambiable** (estatal / autonómico / global) detrás de una interfaz única; cada proveedor declara qué temas sirve y a qué resolución; el resultado entra al modelo en **formato abierto** y, donde proceda, como **entidad IFC real** (terreno → IfcSite/IfcGeographicElement; vecinos → contexto), nunca como mera ayuda visual.

---

## 6. Cuestiones que cierra JM (antes de código)

1. **Alcance geográfico del v0:** ¿solo el piloto (Cataluña, exprimiendo ICGC) o desde el día uno el patrón estatal (IGN+Catastro+CartoCiudad) con ICGC como "plugin" autonómico?
2. **Qué entra al IFC vs qué es contexto visual:** ¿el terreno y los vecinos se autoran como entidades IFC (IfcSite/IfcGeographicElement/…)? ¿con qué LOD? ¿los edificios vecinos como volúmenes simples extruidos por altura?
3. **Fuente de altura preferente:** ¿plantas de Catastro (rápido, vector, nacional) o nDSM LiDAR (preciso, raster, pesado) como primaria? ¿se cruzan?
4. **En vivo vs precargado:** ¿consultamos servicios en cada sesión (API) o ingerimos una vez por proyecto y versionamos el dato (diff-able, reproducible)? — afecta a la "frontera abierta" y a la golden.
5. **Licencias:** CC-BY (IGN/CartoCiudad) y abiertas (Catastro/ICGC) son cómodas; **OSM es ODbL (share-alike)** y **Overture CDLA** — decidir si entran y cómo se atribuye.
6. **Prioridad de capas para el primer corte:** ¿empezamos por parcela+vecinos+viales (vector, "la planta del entorno") o por topografía (rasante)?

## 7. Notas técnicas de implementación (para cuando toque)

- **CORS desde el navegador:** el visor es web; varios WMS/WFS españoles no envían cabeceras CORS → probablemente haga falta un **proxy** server-side (como el `/__aqyra/llm` actual). A verificar por servicio.
- **Límites de petición:** Catastro WFS topa en 4 km²/5.000 elementos → trocear por teselas para entornos grandes.
- **CRS:** todo el bloque nacional/ICGC habla **ETRS89** (UTM 31N = EPSG:25831 en Cataluña) → encaja con la georreferencia ya implementada (CRS configurable por proyecto).
- **Raster vs vector:** para *reconstruir geometría* (parcelas, huellas, viales) queremos **vector (WFS/Overpass)**; el raster (WMS/WCS) es para **rasante** y **textura/contexto**.

---

*La IA investiga y propone; el alcance, las fuentes que entran y qué se autora al IFC los cierra JM. Sin desarrollo hasta esa conversación.*

### Fuentes consultadas
- IGN/CNIG — Centro de Descargas, IDEE, PNOA-LiDAR, API-CNIG/Iberpix, WMS/WCS MDT, WMS MDS LiDAR.
- Dirección General del Catastro — servicios INSPIRE (WMS/WFS/ATOM), doc. WFS Buildings, OVC Coordenadas.
- CartoCiudad — doc. servicios web IDEE, repositorio Geocoder REST (IDEESpain).
- ICGC — Online services/Geoserveis, modelos de elevaciones (MDT/MDS), Territorial LiDAR, 3D city models, geocodificador.
- Copernicus DEM (Data Space) / OpenTopography API / OpenTopoData (EU-DEM).
- JRC — GHS-BUILT-H, GHS-OBAT; EUBUCCO v0.1 (Nature Scientific Data); Overture Maps (docs getting-data/buildings); OpenStreetMap Overpass API (wiki).
