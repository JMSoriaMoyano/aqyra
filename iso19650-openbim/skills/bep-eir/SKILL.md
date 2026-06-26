---
name: bep-eir
description: Redacta y revisa documentos de requisitos e implantacion de informacion segun ISO 19650 -- BEP (Plan de Ejecucion BIM), EIR/AIR/PIR/OIR (requisitos de intercambio y de informacion). Usar cuando el usuario pida "redactar un BEP", "plan de ejecucion BIM", "EIR", "requisitos de intercambio de informacion", "AIR", "PIR", "OIR", o revisar uno existente para un proyecto inmobiliario o de obra civil.
---

# Redaccion de BEP / EIR (ISO 19650)

Genera o revisa documentos de gestion de la informacion conforme a ISO 19650-1 e ISO 19650-2. Salida final en espanol, como documento Word, usando la skill `docx`.

## Cuando se activa
Peticiones de redactar, plantillar o revisar: BEP (pre y post adjudicacion), EIR, AIR, PIR, OIR, plan de entrega de informacion (MIDP/TIDP).

## Flujo
1. Identifica que documento se pide y la fase (pre-adjudicacion vs post-adjudicacion para el BEP).
2. Recoge los datos del proyecto que falten preguntando de forma concisa: nombre del proyecto, parte designadora (cliente), partes designadas (equipos), hitos clave, usos del modelo (BIM uses) y sistema de clasificacion.
3. Estructura el documento segun la jerarquia de requisitos de ISO 19650: OIR -> AIR -> PIR -> EIR -> BEP. Consulta `references/estructura-iso19650.md` para el contenido minimo de cada apartado.
4. Redacta en espanol, terminologia ISO 19650 internacional. No inventes datos del proyecto: marca con [PENDIENTE] lo que el usuario no haya facilitado.
5. Para el entregable Word, lee y sigue la skill `docx`.

## Reglas
- Mantener trazabilidad entre requisitos: cada requisito del EIR debe responder a un PIR/AIR.
- Incluir siempre: matriz de responsabilidades, estrategia de federacion, niveles de necesidad de informacion (remitir a la skill `loin-matrix`), y protocolo del CDE (remitir a la skill `cde-audit`).
- No confundir BEP pre-adjudicacion (respuesta a la licitacion, capacidad) con post-adjudicacion (plan detallado y acordado).
