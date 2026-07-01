# Guia LOIN (ISO 19650 / ISO 7817)

## Componentes del nivel de necesidad de informacion
1. Informacion geometrica: detalle, dimensionalidad (2D/3D), ubicacion, apariencia, comportamiento parametrico.
2. Informacion alfanumerica: propiedades/atributos requeridos (idealmente Psets IFC).
3. Documentacion: documentos asociados al elemento (fichas, manuales, certificados).

## Principio clave
Definir SOLO la informacion necesaria para el proposito de cada hito (principio de "necesidad"). Evitar sobre-especificar.

## Mapa orientativo de propositos por hito
- Diseno conceptual: emplazamiento, volumetria, sistemas principales.
- Diseno desarrollado: dimensiones, sistemas definidos, materiales principales.
- Diseno para construccion: geometria de fabricacion/montaje, propiedades tecnicas completas.
- Entrega/As-built: datos de operacion y mantenimiento, propiedades de activo (alineadas con AIR).

## Psets IFC frecuentes
- Pset_WallCommon, Pset_SlabCommon, Pset_BeamCommon, Pset_ColumnCommon, Pset_DoorCommon, Pset_WindowCommon, Pset_SpaceCommon.
- Para activos: propiedades de mantenimiento, fabricante, modelo, vida util esperada.
