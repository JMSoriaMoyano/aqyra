# GuBIMClass y bsDD

GuBIMClass es un sistema de clasificacion funcional de elementos, desarrollado por el Grup d'Usuaris BIM (Catalunya) y adoptado por buildingSMART Spain; alineado con ISO 19650 e interoperable con IFC.

## Estado en bsDD (verificar periodicamente)
A fecha de esta skill, GuBIMClass NO aparece publicado como diccionario en bsDD: la busqueda de texto en bsDD devuelve 0 resultados para "gubimclass" y no figura en el listado de diccionarios (donde si estan, p. ej., Uniclass, NLSfB, bSItaly, bs-finland). Por tanto, la clasificacion GuBIMClass debe obtenerse de su tabla oficial, no de la API de bsDD.

## Como aportar GuBIMClass
1. El usuario facilita la tabla oficial de GuBIMClass (codigo + denominacion) o un mapeo IfcClass -> codigo GuBIMClass.
2. Se guarda como referencia del proyecto (p. ej. `<obra>/gubimclass-mapping.json` o en la memoria del proyecto) para reutilizar entre hilos.
3. La skill anade GuBIMClass como segunda IfcClassificationReference (sistema "GuBIMClass") junto a Uniclass.

## Si se publica en bsDD
Cuando GuBIMClass este en bsDD, migrar a consultarlo por la API (endpoint Class/Search/v1 con su DictionaryUri) igual que Uniclass, y registrar su URI oficial.
