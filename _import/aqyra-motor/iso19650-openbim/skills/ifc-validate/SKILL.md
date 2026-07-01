---
name: ifc-validate
description: Valida modelos IFC (OpenBIM) frente a requisitos de nomenclatura, clasificacion, Property Sets y reglas de calidad, usando IfcOpenShell en Python. Usar cuando el usuario pida "validar IFC", "comprobar un modelo IFC", "revisar Psets/propiedades", "auditar nomenclatura del modelo", "control de calidad IFC" o adjunte un archivo .ifc para revisar.
---

# Validacion de modelos IFC con IfcOpenShell

Comprueba un archivo IFC contra los requisitos del proyecto y produce un informe de incidencias. Ejecuta el codigo Python con la herramienta Bash.

## Cuando se activa
"Validar/auditar IFC", revisar Psets, clasificacion o nomenclatura, control de calidad de un .ifc, o cuando se adjunte un archivo .ifc para revisar.

## Preparacion del entorno
Instala IfcOpenShell antes de usarlo:
```
pip install ifcopenshell --break-system-packages
```

## Flujo
1. Localiza el archivo .ifc (en uploads o en la carpeta del usuario). Confirma la ruta.
2. Pregunta o deduce los criterios de validacion: esquema esperado (IFC2X3 / IFC4 / IFC4X3), Psets/propiedades obligatorias por clase, sistema de clasificacion y convencion de nomenclatura.
3. Carga el modelo con IfcOpenShell y ejecuta las comprobaciones. Usa `references/checks-ifc.py` como base de las comprobaciones (esquema, conteo por clase, Psets faltantes, propiedades vacias, clasificacion ausente, elementos sin nombre).
4. Genera un informe de incidencias en espanol agrupado por severidad (Bloqueante / Aviso / Informativo), con clase IFC, GlobalId y descripcion. Entregalo como Excel (skill `xlsx`) o Markdown segun pida el usuario.
5. Ofrece abrir el modelo en el visor por defecto del usuario (plugin `visor-ifc`, skill `visor-ifc`) para inspeccionar visualmente las incidencias.
5. No modifiques el modelo en la validacion; solo informa.

## Dominio MEP (instalaciones) -- validacion de RED

Para modelos del dominio **MEP** (redes de distribucion: PCI, fontaneria, clima, electricas), usa
`references/checks-mep.py` ademas de `checks-ifc.py`. Anade, sobre las comprobaciones base:

- **Inventario y sistema**: clases `IfcFlowSegment/Fitting/Terminal/Controller/MovingDevice` y que esten
  agrupadas en un `IfcDistributionSystem`/`IfcSystem` con `PredefinedType`.
- **Puertos**: cada `IfcFlowSegment` con >= 2 `IfcDistributionPort` (extremos); Psets estandar `Pset_*`.
- **Continuidad de red** (lo nuevo de C1 dominio MEP): parsea el IFC a **modelo neutro de red**
  (`scripts/mep/ifc_to_model_mep.py`) y ejecuta la **validacion de red**
  (`scripts/mep/validacion_red.py`): grafo conexo desde la fuente, **terminales conectados**, **sin
  componentes huerfanas** (`grafo_red.filtrar_componentes_desconectadas`, `es_ancla`=fuente), unidades SI.
  Reutiliza el **nucleo transversal** (`scripts/nucleo`). **No calcula hidraulica** (eso es del solver
  de `instalaciones`).
- **Escritura de resultados**: cuando exista solver de red, los Psets de resultado (DN dimensionado,
  caudal, presion, caida) se escriben de vuelta con la skill `ifc-create`.

## Reglas
- Reporta siempre el esquema IFC detectado y si coincide con el esperado.
- Identifica elementos por GlobalId para trazabilidad.
- Alinea las comprobaciones con el LOIN del proyecto (remitir a `loin-matrix`).
- En MEP, distingue **bloqueante** (red no conexa, terminal aislado, segmento sin 2 puertos, unidad no SI)
  de **aviso** (sin IfcSystem, elemento sin nombre).

## Dominio obra lineal (IFC 4.3) -- validacion de ALINEACION

Para modelos de **obra lineal** georreferenciados (carreteras/ferrocarril en IFC 4.3 / IFC4X3),
usa `references/checks-lineal.py` ademas de `checks-ifc.py`. Anade, sobre las comprobaciones base:

- **Esquema**: la alineacion (`IfcAlignment`) es propia de IFC 4.3; avisa si el esquema no es IFC4X3.
- **Inventario de alineacion**: `IfcAlignment` + capas `IfcAlignmentHorizontal/Vertical/Cant` y sus
  `IfcAlignmentSegment` (con `DesignParameters`); infraestructura `IfcRoad/IfcRailway/IfcFacility`.
- **Georreferencia** (bloqueante): presencia de `IfcMapConversion` + `IfcProjectedCRS` (CRS/EPSG, origen E/N).
- **Continuidad / tangencia** (lo nuevo de C1 §4bis): parsea el IFC a **modelo neutro lineal**
  (`scripts/lineal/ifc_to_model_lineal.py`) y ejecuta la **validacion de alineacion**
  (`scripts/lineal/validacion_alineacion.py`): PK monotono y contiguo, encadenado sin saltos ni
  quiebros de tangencia en planta, continuidad de cotas/pendientes en alzado, unidades SI. Reutiliza
  el **nucleo transversal** (`scripts/nucleo`). **No calcula trazado** (3.1-IC) ni firmes (6.1-IC):
  eso es de la disciplina `obras-lineales`.

> Frontera: la alineacion es referenciacion lineal por **PK** (curva 1D), **no** un grafo de red
> (no usa `grafo_red`). Bloqueante = sin IfcAlignment, sin georreferencia, salto/quiebro de
> continuidad, PK no contiguo, unidad no SI; aviso = parametros de clotoide/radio fuera de 3.1-IC.
