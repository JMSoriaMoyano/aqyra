---
name: bsdd-clasificacion
description: Enriquece modelos IFC con el buildingSMART Data Dictionary (bsDD) -- asigna a cada objeto su entidad bsDD con URI, aplica las propiedades (Pset_*) y cantidades (Qto_*) por defecto de esa entidad, y anade doble clasificacion Uniclass + GuBIMClass. Usar cuando el usuario pida "bsDD", "clasificar con bsDD", "Uniclass", "GuBIMClass", "doble clasificacion", "asignar URI bsDD", "propiedades por defecto del diccionario", "enriquecer IFC con bsDD".
---

# Enriquecimiento de IFC con bsDD (Uniclass + GuBIMClass)

Asocia a cada objeto del modelo IFC su entidad del bsDD (con URI), sus propiedades y cantidades por defecto, y una doble clasificacion Uniclass + GuBIMClass. Ejecuta el codigo Python con Bash; consulta el bsDD con la herramienta de fetch web.

## Conector a bsDD (importante)
bsDD ofrece una API REST publica (JSON/RDF) y GraphQL. En este entorno, el cliente Python de bsDD puede estar bloqueado por el proxy del sandbox, pero la herramienta de fetch web SI alcanza la API. Por tanto:
- Consulta el bsDD via fetch web a los endpoints REST (ver `references/bsdd-api.md`).
- Aplica los resultados al IFC en local con IfcOpenShell (`references/enrich_bsdd.py`).
Instala IfcOpenShell: `pip install ifcopenshell --break-system-packages`.

## Flujo
1. Carga el IFC e inventaria las clases presentes (IfcClass + PredefinedType) y el esquema (IFC4/IFC4X3).
2. Para cada clase, consulta el bsDD via fetch web (ver `references/bsdd-api.md`):
   a) Entidad bsDD del diccionario IFC -> su URI.
   b) Clase Uniclass aplicable a esa entidad IFC (diccionario nbs/uniclass2015) -> codigo + URI.
   c) Propiedades (Pset_*) y cantidades (Qto_*) por defecto de la clase (classProperties).
3. GuBIMClass: a dia de hoy NO esta publicado en bsDD (ver `references/gubimclass.md`). Obten el codigo desde la tabla oficial de GuBIMClass que aporte el usuario o desde la memoria del proyecto.
4. Construye un `mapping.json` (estructura en `references/enrich_bsdd.py`) con, por clase: uri bsDD, Uniclass, GuBIMClass y propiedades por defecto.
5. Ejecuta `enrich_bsdd.py modelo.ifc mapping.json salida.ifc`. Aplica:
   - Referencia de clasificacion al diccionario IFC de bsDD con la URI (objetivo 1).
   - Propiedades/cantidades por defecto como Pset_*/Qto_* (objetivo 2).
   - Doble clasificacion Uniclass + GuBIMClass como IfcClassificationReference (objetivo 3).
6. Valida el resultado con la skill `ifc-validate`, entrega el IFC y ofrece abrirlo en el visor por defecto del usuario (plugin `visor-ifc`).

## Consistencia entre hilos (mapa del proyecto)
Guarda el `mapping.json` en la carpeta del proyecto (p. ej. `<obra>/bsdd-mapping.json`). En el siguiente hilo, reutilizalo para que la clasificacion sea consistente en toda la obra; anade solo las clases nuevas.

## Reglas
- Prioriza SIEMPRE las propiedades/cantidades que la entidad bsDD ya trae por defecto antes de crear propiedades a medida.
- Conserva las URIs https://identifier.buildingsmart.org/... y la version del diccionario usada.
- No inventes codigos de clasificacion: si no hay match claro, marca la clase como [PENDIENTE] y pregunta.
- Verifica que GuBIMClass sigue (o no) sin estar en bsDD; si se publica, migra a consultarlo por API.
