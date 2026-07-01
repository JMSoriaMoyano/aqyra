# iso19650-openbim

Plugin de Cowork para gestion de informacion BIM segun ISO 19650 y estrategias OpenBIM/IFC, orientado a ingenieria civil y desarrollo inmobiliario.

## Skills incluidas
- **bep-eir** — Redacta y revisa BEP, EIR/AIR/PIR/OIR (salida Word, espanol).
- **loin-matrix** — Genera la matriz de Nivel de Necesidad de Informacion (LOIN) por elemento, fase e hito (salida Excel).
- **ifc-create** — Crea modelos IFC programaticamente con IfcOpenShell (Python).
- **ifc-validate** — Valida modelos IFC (nomenclatura, Psets, clasificacion) con IfcOpenShell y genera informe de incidencias.
- **bsdd-clasificacion** — Enriquece el IFC con bsDD: asigna entidad+URI, propiedades/cantidades por defecto y doble clasificacion Uniclass + GuBIMClass.
- **cde-audit** — Audita el estado de la informacion en el CDE (Aqyra u otros) frente a estados ISO 19650 (S0-S7) y al MIDP/TIDP.

## Requisitos
- Las skills de IFC instalan IfcOpenShell en el entorno: `pip install ifcopenshell --break-system-packages`.
- La auditoria del CDE trabaja sobre exportaciones (CSV/Excel/PDF) del CDE, ya que Aqyra no dispone de conector directo.

## Idioma y norma
Documentos en espanol siguiendo ISO 19650 (internacional).

## Uso
Tras instalar, las skills aparecen en el menu `/`. Ejemplos:
- `/bep-eir` redacta un Plan de Ejecucion BIM.
- `/loin-matrix` construye la matriz LOIN.
- `/ifc-validate` audita un archivo .ifc.
