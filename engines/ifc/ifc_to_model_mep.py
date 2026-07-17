#!/usr/bin/env python3
"""ifc_to_model_mep.py — parser de disciplina MEP (INSTALACIONES) del engine C1.

Dirección PARSEAR (IFC → modelo neutro), vista MEP navegable v0 del contrato C1
(`instalaciones`, forward-open). Cierra la costura F3.1 del Plan de Cierre: el
Maestro federado pasa a RECONOCER los elementos MEP y a MAPEAR sus sistemas.

Alcance v0 (D-MEP-1..D-MEP-4, ratificadas por JM 2026-07-16):
  - D-MEP-1 · reconoce las 7 clases MEP admitidas como elementos NAVEGABLES, por
    CLASE EXACTA (no by_type: `IfcFireSuppressionTerminal` es subtipo de
    `IfcFlowTerminal` en IFC4 y `by_type` los sumaría dos veces). Forward-open:
    ampliar el catálogo = añadir a CLASES_MEP (lista/pack), no tocar el engine.
  - D-MEP-2 · mapea cada `IfcDistributionSystem` como sistema («Estructura
    funcional» del visor, D-CH-4) por `IfcRelAssignsToGroup` (sistema→elementos)
    + `IfcRelServicesBuildings` (sistema→edificio), con su `PredefinedType`.
  - D-MEP-3 · métrica espacial: `elevationMetric` por planta (edificación),
    tomada del `IfcBuildingStorey` que contiene el elemento (en metros, vía
    `aqyra_core.ifc_utils.length_scale`). `stationMetric`/`IfcAlignment` NO aplica.
  - D-MEP-4 · v0 NO construye el grafo de red por puertos (5.498
    `IfcDistributionPort`): ese es un incremento posterior por
    `aqyra_core.grafo_red` para alimentar el motor de instalaciones.

Reutiliza el NÚCLEO transversal (`aqyra_core.ifc_utils`) SIN tocarlo (identidad
anclada, `test_identidad_nucleo`). No calcula nada: solo lee y estructura.

Todo resultado es de predimensionado/asistencia y debe ser revisado y firmado por
técnico competente.
"""
from __future__ import annotations

# Núcleo transversal compartido (paquete instalado del workspace; no se copia).
from aqyra_core import ifc_utils

# D-MEP-1 · catálogo de clases MEP admitidas en v0 (CLASE EXACTA). Los `*Type`
# son tipos, no elementos. Forward-open: ampliar aquí = pack/lista, no engine.
CLASES_MEP: tuple[str, ...] = (
    "IfcPipeSegment",
    "IfcPipeFitting",
    "IfcValve",
    "IfcCableCarrierSegment",
    "IfcCableCarrierFitting",
    "IfcFireSuppressionTerminal",
    "IfcFlowTerminal",
)


def _cota_por_elemento(ifc, escala: float) -> dict[int, tuple[float | None, str | None]]:
    """Mapa id(elemento) → (elevationMetric en metros, nombre de planta).

    La cota la aporta el `IfcBuildingStorey` que CONTIENE al elemento
    (`IfcRelContainedInSpatialStructure`). Si la contención no es una planta
    (p. ej. un `IfcSpace`), la cota queda a None (honesto: no se inventa)."""
    out: dict[int, tuple[float | None, str | None]] = {}
    for rel in ifc.by_type("IfcRelContainedInSpatialStructure"):
        estructura = rel.RelatingStructure
        if estructura is None or not estructura.is_a("IfcBuildingStorey"):
            continue
        elev = getattr(estructura, "Elevation", None)
        cota = float(elev) * escala if elev is not None else None
        planta = getattr(estructura, "Name", None)
        for obj in rel.RelatedElements or []:
            out[obj.id()] = (cota, planta)
    return out


def _sistemas(ifc) -> tuple[dict[int, str], dict[str, dict]]:
    """Construye (elemento→GUID de sistema) y el catálogo de sistemas.

    - elemento→sistema por `IfcRelAssignsToGroup` cuyo `RelatingGroup` es un
      `IfcDistributionSystem` (D-MEP-2). Un elemento sin grupo queda sin sistema.
    - sistema→edificios por `IfcRelServicesBuildings` (D-MEP-2).
    Determinista: los conjuntos se emiten ordenados aguas arriba."""
    elem_a_sistema: dict[int, str] = {}
    catalogo: dict[str, dict] = {}

    for sis in ifc.by_type("IfcDistributionSystem"):
        catalogo[sis.GlobalId] = {
            "GUID": sis.GlobalId,
            "nombre": getattr(sis, "Name", None),
            "predefinedType": (
                str(sis.PredefinedType) if getattr(sis, "PredefinedType", None) is not None else None
            ),
            "_elementos_ids": set(),
            "edificios": set(),
        }

    for rel in ifc.by_type("IfcRelAssignsToGroup"):
        grp = rel.RelatingGroup
        if grp is None or not grp.is_a("IfcDistributionSystem"):
            continue
        sguid = grp.GlobalId
        for obj in rel.RelatedObjects or []:
            elem_a_sistema.setdefault(obj.id(), sguid)  # primer sistema gana (determinista)
            if sguid in catalogo:
                catalogo[sguid]["_elementos_ids"].add(obj.id())

    for rel in ifc.by_type("IfcRelServicesBuildings"):
        sis = rel.RelatingSystem
        if sis is None or sis.GlobalId not in catalogo:
            continue
        for edif in rel.RelatedBuildings or []:
            nombre = getattr(edif, "Name", None)
            if nombre is not None:
                catalogo[sis.GlobalId]["edificios"].add(nombre)

    return elem_a_sistema, catalogo


def ifc_a_vista_mep(ifc) -> dict:
    """IFC (soporte de intercambio) → vista MEP navegable del modelo neutro C1.

    Devuelve el bloque `instalaciones` = {elementos:[...], sistemas:[...]}.
    Todo orden es determinista (por GUID) para que la golden ancle por conteos
    y asignaciones sin depender del orden de recorrido de ifcopenshell."""
    escala = ifc_utils.length_scale(ifc)
    cotas = _cota_por_elemento(ifc, escala)
    elem_a_sistema, catalogo = _sistemas(ifc)

    # id(elemento) → GUID, para traducir los conjuntos de sistema a GUIDs.
    id_a_guid: dict[int, str] = {}
    elementos: list[dict] = []
    for cls in CLASES_MEP:
        for e in ifc.by_type(cls):
            if e.is_a() != cls:   # CLASE EXACTA: excluye subtipos (IfcFireSuppressionTerminal ⊂ IfcFlowTerminal)
                continue
            cota, planta = cotas.get(e.id(), (None, None))
            id_a_guid[e.id()] = e.GlobalId
            elementos.append({
                "clase": cls,
                "GUID": e.GlobalId,
                "nombre": getattr(e, "Name", None),
                "sistema": elem_a_sistema.get(e.id()),   # GUID del sistema o None
                "elevationMetric": cota,
                "planta": planta,
            })
    elementos.sort(key=lambda d: d["GUID"])

    sistemas: list[dict] = []
    for sguid in sorted(catalogo):
        s = catalogo[sguid]
        guids = sorted(id_a_guid[i] for i in s["_elementos_ids"] if i in id_a_guid)
        sistemas.append({
            "GUID": s["GUID"],
            "nombre": s["nombre"],
            "predefinedType": s["predefinedType"],
            "elementos": guids,
            "edificios": sorted(s["edificios"]),
        })

    return {"elementos": elementos, "sistemas": sistemas}


def parsear(ifc_path) -> dict:
    """Abre un IFC y devuelve el modelo neutro con la vista MEP (`instalaciones`).

    Emite además el bloque `unidades` (requerido por el esquema del modelo neutro)."""
    import ifcopenshell  # perezoso: no se necesita en --schema-only
    ifc = ifcopenshell.open(str(ifc_path))
    return {
        "unidades": {"longitud": "m"},
        "instalaciones": ifc_a_vista_mep(ifc),
    }
