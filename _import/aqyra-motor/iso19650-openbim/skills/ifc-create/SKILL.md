---
name: ifc-create
description: Crea o genera modelos IFC (OpenBIM) de forma programatica con IfcOpenShell en Python -- estructura espacial, elementos basicos, Property Sets y clasificacion. Usar cuando el usuario pida "crear un IFC", "generar un modelo IFC", "exportar geometria/datos a IFC", "anadir Psets a un IFC" o construir un modelo de prueba/plantilla conforme a OpenBIM.
---

# Creacion de modelos IFC con IfcOpenShell

Genera archivos IFC validos por codigo: jerarquia espacial (Project > Site > Building > Storey), elementos, propiedades y clasificacion. Ejecuta el Python con la herramienta Bash.

## Cuando se activa
"Crear/generar un IFC", exportar datos a IFC, anadir Psets a un modelo, construir un modelo plantilla o de prueba conforme a OpenBIM.

## Preparacion del entorno
```
pip install ifcopenshell --break-system-packages
```

## Flujo
1. Aclara el objetivo: modelo plantilla vacio con estructura espacial, modelo con elementos concretos, o enriquecer un IFC existente con Psets/clasificacion.
2. Define el esquema destino (por defecto IFC4) y el sistema de coordenadas/unidades.
3. Usa `references/crear-ifc.py` como base: crea proyecto, contexto geometrico, unidades, jerarquia espacial y elementos con `ifcopenshell.api`.
4. Asigna Property Sets y clasificacion segun el LOIN del proyecto (remitir a `loin-matrix`).
5. Tras generar, valida el resultado con la skill `ifc-validate` y entrega el `.ifc` al usuario.
6. Ofrece SIEMPRE abrir el modelo en el visor por defecto del usuario (plugin `visor-ifc`, skill `visor-ifc`).

## Reglas
- Usar siempre la API de alto nivel `ifcopenshell.api` (run) en lugar de crear entidades a mano cuando sea posible.
- Asegurar unidades y contexto geometrico antes de crear geometria. Para redes en metros, asignar
  explicitamente `unit.add_si_unit` LENGTHUNIT sin prefijo (`unit.assign_unit` por defecto pone MILIMETROS).
- Generar GlobalId validos (la API los crea automaticamente).
- Validar el modelo creado antes de entregarlo.

## Dominio MEP (instalaciones) -- redes de distribucion

Para crear modelos del dominio **MEP** (PCI, fontaneria, climatizacion, electricas), usa entidades
de distribucion y conectividad por puertos:

- **Sistema**: `IfcDistributionSystem` con `PredefinedType` (IFC4: `FIREPROTECTION`, `WATERSUPPLY`,
  `ELECTRICAL`, `AIRCONDITIONING`...; en IFC4X3 PCI es `FIRESUPPRESSION`). Agrupa los elementos con
  `IfcRelAssignsToGroup`.
- **Elementos**: `IfcFlowSegment` (tubo/conducto/cable bandeja), `IfcFlowFitting` (codo/te),
  `IfcFlowTerminal` (BIE/rociador/difusor/luminaria), `IfcFlowController` (valvula),
  `IfcFlowMovingDevice` (bomba/grupo/ventilador).
- **Conectividad**: cada elemento lleva `IfcDistributionPort` (anidados con `IfcRelNests`) y los
  puertos se unen con `IfcRelConnectsPorts`. Cada `IfcFlowSegment` necesita 2 puertos (sus extremos).
- **Propiedades**: Psets estandar `Pset_PipeSegmentTypeCommon` (DN, rugosidad), `Pset_*TerminalTypeCommon`, etc.

Plantilla de referencia (red PCI completa de prueba): `scripts/mep/generate_test_ifc_mep.py`.
Tras crear la red, **valida** con la skill `ifc-validate` (incluye continuidad de red MEP) y ofrece el visor.

## Write-back de Psets de resultado de red (PT 4.4)

Para cerrar el ciclo **IFC → cálculo → IFC**, esta skill incluye un escritor **genérico**
de Psets de resultado: `references/escribir_psets_resultado.py`. Aporta la **mecánica** IFC
(abrir, localizar el elemento por Name/GlobalId, añadir el Pset con `ifcopenshell.api`,
guardar); la **semántica** (qué Pset y qué propiedades) la fija la disciplina, que pasa un
**mapping JSON** `{ "elementos": { "<Name|GlobalId>": { "<Pset>": { "<Prop>": valor } } } }`.

```
python3 references/escribir_psets_resultado.py entrada.ifc mapping.json salida.ifc
```

Uso típico (instalaciones): el solver de red escribe DN dimensionado, caudal, velocidad,
presión y margen en `Pset_Estructurando_ResultadoRed` por tramo y terminal. Tras escribir,
**valida** con `ifc-validate` (reconoce el Pset de resultado y comprueba la continuidad de red)
y ofrece el visor (`visor-ifc`).

## Dominio obra lineal (IFC 4.3) -- alineacion georreferenciada

Para crear modelos de **obra lineal** (carreteras/ferrocarril) usa el esquema **IFC4X3** y las
entidades de alineacion + georreferencia:

- **Eje**: `IfcAlignment` que anida (`IfcRelNests`) tres capas: `IfcAlignmentHorizontal` (planta),
  `IfcAlignmentVertical` (alzado) y `IfcAlignmentCant` (peralte). Cada capa anida `IfcAlignmentSegment`
  cuyo `DesignParameters` es el segmento parametrico: `IfcAlignmentHorizontalSegment`
  (LINE/CIRCULARARC/CLOTHOID...), `IfcAlignmentVerticalSegment` (CONSTANTGRADIENT/PARABOLICARC/
  CIRCULARARC) e `IfcAlignmentCantSegment` (CONSTANTCANT/LINEARTRANSITION...).
- **Infraestructura**: `IfcRoad`/`IfcRailway` (subtipos de `IfcFacility`); el eje se referencia con
  `IfcRelReferencedInSpatialStructure` y/o se agrega al proyecto.
- **Georreferencia** (imprescindible en obra lineal): `IfcProjectedCRS` (Name=EPSG, MapProjection,
  MapZone, datum) + `IfcMapConversion` (SourceCRS=contexto, TargetCRS=CRS, Eastings/Northings/
  OrthogonalHeight, XAxisAbscissa/Ordinate=rotacion, Scale).
- **Unidades**: declarar `unit.add_si_unit` LENGTHUNIT sin prefijo (metros) y PLANEANGLEUNIT (radianes).

Plantilla de referencia (eje de carretera completo de prueba): `scripts/lineal/generate_test_ifc_lineal.py`.
Tras crear el eje, **valida** con la skill `ifc-validate` (`checks-lineal.py`: alineacion + georref +
continuidad) y ofrece el visor.
