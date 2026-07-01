---
name: loin-matrix
description: Crea la matriz de Nivel de Necesidad de Informacion (LOIN) y la matriz de entregables por elemento, fase e hito segun ISO 19650 e ISO 7817 (LOIN). Usar cuando el usuario pida "matriz LOIN", "nivel de necesidad de informacion", "nivel de detalle/informacion", "matriz de entregables", "LOD/LOI" o definir requisitos de informacion por elemento constructivo.
---

# Matriz de requisitos LOIN

Genera una matriz LOIN como hoja de calculo (skill `xlsx`) que define, por elemento y por hito, la informacion geometrica, alfanumerica y documental requerida.

## Cuando se activa
"Matriz LOIN", "nivel de necesidad de informacion", "LOD/LOI", "matriz de entregables BIM", definir requisitos de informacion por elemento o fase.

## Flujo
1. Confirma el sistema de clasificacion (p. ej. clases IFC, Uniclass, Omniclass o GuBIMClass) y los hitos/fases del proyecto.
2. Construye filas = elementos (por clase IFC o capitulo de clasificacion) y columnas = hitos/fases.
3. Para cada celda define el nivel de necesidad de informacion segun ISO 7817 / ISO 19650: informacion geometrica (detalle, dimensionalidad, ubicacion, apariencia, comportamiento parametrico) e informacion alfanumerica (propiedades requeridas, Psets IFC) y documentacion asociada.
4. Evita la nomenclatura ambigua "LOD 100-500": prioriza describir la informacion necesaria para el proposito de cada hito (enfoque LOIN de ISO 19650). Consulta `references/loin-guia.md`.
5. Entrega como `.xlsx` siguiendo la skill `xlsx`: una pestana de matriz, una de leyenda y una de Property Sets requeridos por elemento.

## Reglas
- El LOIN se define por el PROPOSITO de la informacion en cada hito, no por un numero generico.
- Alinear las propiedades requeridas con Psets IFC estandar cuando existan (Pset_*). Marcar propiedades personalizadas claramente.
- Mantener coherencia con el EIR/BEP (remitir a la skill `bep-eir`).
