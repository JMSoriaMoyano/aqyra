# Estados del CDE y nomenclatura (ISO 19650-2)

## Estados de aprobacion (suitability)
- S0: WIP (trabajo en curso, uso interno del equipo de tarea).
- S1-S4 (y similares): Compartido (Shared) para coordinacion, revision, informacion o autorizacion.
- A1.. / B1.. : Publicado (Published) - autorizado para uso/construccion.
- Archivado: registro historico de versiones superadas.

> Nota: los conjuntos exactos de codigos pueden variar segun el protocolo del proyecto; confirmar con el BEP.

## Transiciones tipicas
WIP -> Check/Review/Approve dentro del equipo -> Compartido -> Revision por la parte designadora -> Publicado -> (al superarse) Archivado.

## Nomenclatura de contenedores de informacion (convencion habitual)
Campos separados por guion: Proyecto-Originador-Volumen/Sistema-Nivel/Ubicacion-Tipo-Rol-Numero.
Metadatos asociados: Estado (suitability), Revision, Fecha, Descripcion.

## Comprobaciones de auditoria
- Campos de nomenclatura completos y validos.
- Estado coherente con la fase y con el MIDP.
- Contenedores estancados en WIP cerca de un hito.
- Entregables del MIDP/TIDP sin contenedor asociado (faltantes).
- Revisiones sin codigo de aprobacion antes de publicar.
