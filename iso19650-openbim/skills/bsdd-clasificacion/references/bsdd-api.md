# bsDD: API REST y como consultarla (via fetch web)

bsDD (buildingSMART Data Dictionary) expone una API REST publica (JSON y RDF) y una API GraphQL. La mayoria de endpoints son publicos (algunos requieren Azure AD B2C). Base: https://api.bsdd.buildingsmart.org

Documentacion: Swagger https://app.swaggerhub.com/apis/buildingSMART/Dictionaries/v1 y GitHub buildingSMART/bSDD.

## URIs
Formato: https://identifier.buildingsmart.org/uri/<organizacion>/<diccionario>/<version>/class/<codigo>
Se puede usar `latest` como version. (En migracion de http:// a https://.)

Diccionarios clave:
- IFC (buildingSMART): https://identifier.buildingsmart.org/uri/buildingsmart/ifc/4.3
- Uniclass 2015 (NBS):  https://identifier.buildingsmart.org/uri/nbs/uniclass2015/1

## Endpoints utiles (consumir con fetch web; URL-encode los parametros)
1. Listar diccionarios:
   GET /api/Dictionary/v1?Offset=0&Limit=1000
2. Buscar clase aplicable a una entidad IFC (p. ej. Uniclass para IfcWall):
   GET /api/Class/Search/v1?SearchText=wall&DictionaryUris=<URI_diccionario_urlencoded>&RelatedIfcEntities=IfcWall&limit=20
   -> devuelve classes[].uri, .referenceCode, .name
3. Detalle de una clase con sus propiedades por defecto:
   GET /api/Class/v1?Uri=<URI_clase_urlencoded>&IncludeClassProperties=true&IncludeClassRelations=true
   -> classProperties[] con name, propertySet (Pset/Qto), dataType, predefinedValue, etc.
4. Texto libre (todas las clases/propiedades): GET /api/TextSearch/v2?SearchText=...&Limit=...

## Ejemplo verificado
GET /api/Class/Search/v1?SearchText=wall&DictionaryUris=https%3A%2F%2Fidentifier.buildingsmart.org%2Furi%2Fnbs%2Funiclass2015%2F1&RelatedIfcEntities=IfcWall
-> { "classes": [ { "referenceCode": "EF_25", "name": "Wall and barrier elements",
     "uri": "https://identifier.buildingsmart.org/uri/nbs/uniclass2015/1/class/EF_25" } ] }

## Nota de entorno
El cliente Python `bsdd` (from bsdd import Client) y las llamadas directas con requests pueden fallar por el proxy del sandbox (403). Usa la herramienta de fetch web para consultar la API; aplica los datos al IFC en local con IfcOpenShell.
