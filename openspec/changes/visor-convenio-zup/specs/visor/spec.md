# Delta de spec · Capacidad `visor` — Convenio Z-up

> Primera especificación formal de la capacidad `visor`: se AÑADEN los requisitos que codifican
> el convenio de ejes Z-up. (No hay baseline previa en `openspec/specs/visor/`.)

## ADDED Requirements

### Requirement: Convenio de ejes Z-up del visor
El visor SHALL representar la geometría, la cámara y las métricas en un sistema de coordenadas
con **Z vertical** (Z-up), coherente con el World Coordinate System del IFC y con los motores
del ecosistema, deshaciendo la conversión a Y-up que aplica web-ifc.

#### Scenario: La geometría se ingiere en Z-up
- **GIVEN** un IFC cuyo WCS es `IFCDIRECTION((0.,0.,1.))`
- **WHEN** el visor añade el modelo a la escena
- **THEN** las mallas quedan orientadas con Z vertical (rotación +90° sobre X respecto a la
  salida Y-up de web-ifc)
- **AND** un elemento cuya cota IFC es mayor aparece más arriba en el eje Z de la escena.

#### Scenario: La cámara usa Z como vertical
- **GIVEN** la escena del visor en Z-up
- **WHEN** se inicializa la cámara y los controles de órbita
- **THEN** `camera.up` es `(0,0,1)` y el encuadre inicial (`fitToModels`) orienta el modelo con
  Z hacia arriba.

### Requirement: Cota de elemento sobre el eje Z
El visor SHALL calcular la cota de un elemento y la métrica de elevación a partir del eje **Z**
del AABB en coordenadas de escena.

#### Scenario: elementElevations toma la coordenada Z
- **GIVEN** un elemento cargado en la escena Z-up
- **WHEN** se solicita `elementElevations`
- **THEN** el rango de cota se obtiene de `box.min.z`/`box.max.z`
- **AND** `elevationMetric` refleja esa cota real del modelo.

### Requirement: Cámara BCF sin transformación de marco
Dado que el viewpoint BCF ya está en el marco IFC Z-up y el visor también, `bcfCameraToViewer`
SHALL devolver la posición, dirección y «arriba» de la cámara **sin permutación de ejes**
(identidad), preservando la superficie pública de `@aqyra/visor`.

#### Scenario: El mapeo de cámara es la identidad
- **GIVEN** una `PerspectiveCamera` BCF con `viewPoint=(10,20,30)` y `up=(−0.408,0.408,0.816)`
- **WHEN** se aplica `bcfCameraToViewer`
- **THEN** `position` es `(10,20,30)` y `up` es `(−0.408,0.408,0.816)` (sin cambiar de eje).

#### Scenario: La cámara BCF del golden sigue anclada en IFC Z-up
- **GIVEN** el árbol BCF del derivado congelado (golden `C4-FED-06`, D29)
- **WHEN** se parsea el viewpoint con `parseViewpoint`
- **THEN** la cámara cruda coincide con el golden en marco IFC Z-up **sin re-baseline ni
  re-firma** (el golden no cambia; el cambio queda dentro de la Llave 1).

### Requirement: Indicadores de orientación en Z-up
El gizmo de ejes y los comentarios de convenio del visor SHALL mostrar **Z como eje vertical**.

#### Scenario: El gizmo marca Z vertical
- **GIVEN** el visor en Z-up
- **WHEN** se muestra el gizmo de ejes
- **THEN** el eje Z aparece vertical (no el Y).
