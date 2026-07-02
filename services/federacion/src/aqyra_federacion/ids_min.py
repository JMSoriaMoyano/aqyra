"""Motor de validación IDS mínimo (D7: propio, sobre ifcopenshell).

Cubre exactamente los facets que usa el pack ids/proyecto-piloto/v1 (IDS 1.0):
  - applicability: entity (simpleValue o enumeración) — coincidencia EXACTA de
    clase (sin subtipos), caso-insensible, como el facet entity de IDS.
  - requirements: classification (por system) · property (pset + baseName) ·
    attribute (name + patrón XSD, coincidencia total).

Limitación honesta de v0 (D7): no es un motor IDS completo — si el pack crece más
allá de estos facets, se amplía este módulo o se adopta ifctester (decisión nueva).
R4-GEORREF no está aquí: es regla de módulo (qa.py), no expresable en IDS.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

_NS = {"ids": "http://standards.buildingsmart.org/IDS",
       "xs": "http://www.w3.org/2001/XMLSchema"}

# CamelCase de las clases IFC que puede nombrar un .ids (fallback si el wrapper
# de ifcopenshell no resuelve el nombre); ampliable sin romper nada.
_CAMEL = {
    "IFCCOLUMN": "IfcColumn", "IFCWALL": "IfcWall", "IFCSLAB": "IfcSlab",
    "IFCFOOTING": "IfcFooting", "IFCDOOR": "IfcDoor",
    "IFCTRANSPORTELEMENT": "IfcTransportElement",
    "IFCBUILDINGSTOREY": "IfcBuildingStorey", "IFCPROJECT": "IfcProject",
}


def camel(entity_upper: str) -> str:
    """IFCWALL → IfcWall (vía esquema de ifcopenshell, con fallback estático)."""
    try:
        from ifcopenshell import ifcopenshell_wrapper as w
        for schema in ("IFC4X3_ADD2", "IFC4X3", "IFC4"):
            try:
                return w.schema_by_name(schema).declaration_by_name(entity_upper.lower()).name()
            except Exception:  # noqa: BLE001
                continue
    except Exception:  # noqa: BLE001
        pass
    return _CAMEL.get(entity_upper.upper(), entity_upper)


@dataclass
class Requisito:
    """Un facet de requirements del .ids."""
    tipo: str                      # classification | property | attribute
    params: dict = field(default_factory=dict)


@dataclass
class Spec:
    """Una specification del .ids."""
    id: str
    titulo: str                    # description del .ids (texto libre)
    entidades: list[str]           # clases IFC en MAYÚSCULAS, en orden del .ids
    requisitos: list[Requisito]

    @property
    def aplicabilidad(self) -> str:
        return "|".join(camel(e) for e in self.entidades)


def _texto(nodo, ruta: str) -> str | None:
    hit = nodo.find(ruta, _NS)
    return hit.text if hit is not None else None


def _valores(nodo) -> list[str]:
    """simpleValue o xs:restriction/xs:enumeration de un name/system/value."""
    if nodo is None:
        return []
    sv = nodo.find("ids:simpleValue", _NS)
    if sv is not None:
        return [sv.text]
    return [e.get("value") for e in nodo.findall(".//xs:enumeration", _NS)]


def parse_ids(ids_path: Path) -> list[Spec]:
    """Parsea el .ids (IDS 1.0) a la lista de specs, en orden del fichero."""
    root = ET.parse(str(ids_path)).getroot()
    specs = []
    for sp in root.findall(".//ids:specification", _NS):
        entidades = []
        for ent in sp.findall("ids:applicability/ids:entity", _NS):
            entidades += [v.upper() for v in _valores(ent.find("ids:name", _NS))]
        reqs = []
        requirements = sp.find("ids:requirements", _NS)
        for facet in (requirements if requirements is not None else []):
            tag = facet.tag.split("}")[-1]
            if tag == "classification":
                reqs.append(Requisito("classification", {
                    "system": _valores(facet.find("ids:system", _NS))[0]}))
            elif tag == "property":
                reqs.append(Requisito("property", {
                    "pset": _valores(facet.find("ids:propertySet", _NS))[0],
                    "nombre": _valores(facet.find("ids:baseName", _NS))[0],
                    "dataType": facet.get("dataType")}))
            elif tag == "attribute":
                patron = None
                valor = facet.find("ids:value", _NS)
                if valor is not None:
                    p = valor.find(".//xs:pattern", _NS)
                    patron = p.get("value") if p is not None else None
                reqs.append(Requisito("attribute", {
                    "nombre": _valores(facet.find("ids:name", _NS))[0],
                    "patron": patron}))
            else:
                raise ValueError(f"facet IDS no soportado por el motor mínimo (D7): {tag}")
        specs.append(Spec(id=sp.get("identifier") or sp.get("name"),
                          titulo=sp.get("description") or sp.get("name"),
                          entidades=entidades, requisitos=reqs))
    return specs


# --------------------------------------------------------------------------- #
# Comprobación de facets sobre un modelo abierto con ifcopenshell             #
# --------------------------------------------------------------------------- #
def aplicables(ifc, spec: Spec) -> list:
    """Elementos del modelo que aplican al spec (clase exacta, orden de fichero)."""
    out = []
    for ent in spec.entidades:
        try:
            out += list(ifc.by_type(camel(ent), include_subtypes=False))
        except Exception:  # noqa: BLE001 — clase inexistente en el esquema del fichero
            continue
    return sorted(out, key=lambda e: e.id())


def _sistemas_clasificacion(el) -> set[str]:
    """Sistemas de clasificación del elemento.

    1.3 (hallazgo #9): `ReferencedSource` puede ser una CADENA de
    IfcClassificationReference (patrón Revit/IFC4) — se sigue hasta la
    IfcClassification raíz (tope 8, como el runner). Name=None no entra al set.
    """
    sistemas = set()
    for rel in getattr(el, "HasAssociations", None) or []:
        if not rel.is_a("IfcRelAssociatesClassification"):
            continue
        cur = rel.RelatingClassification
        for _ in range(8):
            if cur is None:
                break
            if cur.is_a("IfcClassification"):
                if getattr(cur, "Name", None):
                    sistemas.add(cur.Name)
                break
            cur = getattr(cur, "ReferencedSource", None)
    return sistemas


def _psets_de(objeto):
    """IfcPropertySet de un objeto (ocurrencia o tipo), tolerante a suciedad."""
    for rel in getattr(objeto, "IsDefinedBy", None) or []:
        if rel.is_a("IfcRelDefinesByProperties"):
            pd = rel.RelatingPropertyDefinition
            if pd is not None and pd.is_a("IfcPropertySet"):
                yield pd
    # tipo con Psets directos (IfcTypeObject.HasPropertySets)
    for pd in getattr(objeto, "HasPropertySets", None) or []:
        if pd is not None and pd.is_a("IfcPropertySet"):
            yield pd


def _tipos_de(el):
    """Tipos del elemento: IsTypedBy (IFC4/4X3) y IsDefinedBy→IfcRelDefinesByType (2X3)."""
    for rel in getattr(el, "IsTypedBy", None) or []:
        if getattr(rel, "RelatingType", None) is not None:
            yield rel.RelatingType
    for rel in getattr(el, "IsDefinedBy", None) or []:
        if rel.is_a("IfcRelDefinesByType") and getattr(rel, "RelatingType", None) is not None:
            yield rel.RelatingType


def _tiene_propiedad(el, pset: str, nombre: str) -> bool:
    """1.3 (hallazgo #10): herencia ocurrencia > TIPO, como manda IDS.

    Los exports de Revit ponen Psets en el IfcTypeObject y no en la ocurrencia:
    mirar solo IsDefinedBy daba FALSOS FAIL sobre IFC conforme.
    """
    objetos = [el, *_tipos_de(el)]
    for objeto in objetos:
        for pd in _psets_de(objeto):
            if pd.Name == pset:
                for p in getattr(pd, "HasProperties", None) or []:
                    if (p.is_a("IfcPropertySingleValue") and p.Name == nombre
                            and p.NominalValue is not None):
                        return True
    return False


def cumple(el, req: Requisito) -> bool:
    """¿El elemento cumple el facet?"""
    if req.tipo == "classification":
        return req.params["system"] in _sistemas_clasificacion(el)
    if req.tipo == "property":
        return _tiene_propiedad(el, req.params["pset"], req.params["nombre"])
    if req.tipo == "attribute":
        valor = getattr(el, req.params["nombre"], None)
        if valor is None:
            return False
        patron = req.params.get("patron")
        return True if patron is None else re.fullmatch(patron, str(valor)) is not None
    raise ValueError(f"facet no soportado: {req.tipo}")


def evaluar_spec(ifc, spec: Spec) -> dict:
    """Evalúa un spec sobre un modelo → {n_comprobados, n_fallos, fallos, corruptos}.

    1.3 (D17): un elemento cuyos atributos revientan al evaluarlo (entidad corrupta)
    se SALTA y se reporta en `corruptos` (ids '#n') — no cuenta en n_comprobados;
    el consumidor (qa.py) lo declara como aviso `entidad-corrupta`.
    """
    els = aplicables(ifc, spec)
    fallos, corruptos = [], []
    for el in els:
        try:
            if not all(cumple(el, r) for r in spec.requisitos):
                fallos.append(el)
        except Exception:  # noqa: BLE001 — atributos rotos: saltar y declarar
            try:
                corruptos.append(f"#{el.id()}")
            except Exception:  # noqa: BLE001
                corruptos.append("#?")
    n = len(els) - len(corruptos)
    return {"n_comprobados": n, "n_fallos": len(fallos), "fallos": fallos,
            "corruptos": corruptos}
