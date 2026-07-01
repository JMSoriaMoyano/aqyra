---
name: cde-audit
description: Audita el estado de la informacion en el Entorno Comun de Datos (CDE), incluido Aqyra, segun el flujo de estados de ISO 19650 (S0-S7 / WIP-Compartido-Publicado-Archivado) y controla hitos de entrega. Usar cuando el usuario pida "auditar el CDE", "estado de entregas", "revisar Aqyra", "control de entregables", "estados S0-S7", "que falta por entregar" o adjunte un export/listado del CDE.
---

# Auditoria del CDE y control de entregas (ISO 19650)

Revisa el estado de la informacion en el CDE (Aqyra u otros) frente al plan de entrega (MIDP/TIDP) y los estados de ISO 19650. Trabaja sobre exportaciones o listados del CDE (CSV/Excel/PDF) ya que no hay conector directo a Aqyra.

## Cuando se activa
"Auditar el CDE", revisar Aqyra, estado de entregas/entregables, "que falta por entregar", control de estados S0-S7, conciliar con el MIDP.

## Flujo
1. Pide al usuario el export del CDE (listado de contenedores de informacion con su estado y revision) y, si existe, el MIDP/TIDP de referencia.
2. Normaliza la nomenclatura de los contenedores de informacion y comprueba que cumple la convencion del proyecto (campos: proyecto, originador, volumen/sistema, nivel, tipo, rol, numero). Consulta `references/estados-cde.md`.
3. Verifica el flujo de estados ISO 19650: WIP (S0) -> Compartido (S1-S4, "shared") -> Publicado (A/An, "published") -> Archivado. Detecta contenedores en estado incoherente o estancados.
4. Concilia con el MIDP/TIDP: marca entregables previstos que faltan, retrasados o sin codigo de aprobacion.
5. Entrega un informe en espanol (Excel o Markdown): resumen por estado, incumplimientos de nomenclatura, entregables faltantes/retrasados y acciones recomendadas.

## Reglas
- No asumir la API de Aqyra; trabajar sobre los datos exportados que aporte el usuario.
- Distinguir claramente codigo de estado (S0-S7) de codigo de revision/aprobacion.
- Trazar cada incidencia al contenedor de informacion concreto y a su responsable.
