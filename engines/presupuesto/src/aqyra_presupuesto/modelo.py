"""Acceso al IFC(+Qto) para el parser de medición del C5 (módulo 1, D7).

La medición NACE del modelo: este módulo abre el IFC y lee las CANTIDADES de los `Qto_*`
(no adivina geometría, D_modelo), la clase, la clasificación, la ubicación y los HUECOS
(`IfcRelVoidsElement`) de cada elemento medible. El motor (presupuesto.py) presupuesta la vista
neutra que produce `medicion.medir`.

En producción la fuente es el Maestro federado de C4; en el golden, las fixtures congeladas con
`Qto` (md5 propios de C5; los originales anclados quedan intactos).
"""
from __future__ import annotations

# ifcopenshell se importa de forma PEREZOSA (dentro de las funciones del parser): el motor
# (presupuesto.py) presupuesta el modelo neutro SIN necesitar ifcopenshell; sólo `medir`/parser lo
# requiere. Así `presupuestar` funciona en entornos sin la librería (y su test no la exige).

# tipo (unidad) inferido del nombre de la magnitud del Qto — heurística estable para los
# Qto_*BaseQuantities estándar (Area→m2, Volume→m3, Length→ml). El motor toma la unidad del
# CRITERIO (no de aquí); este `tipo` documenta la magnitud en el modelo neutro.
def tipo_de_magnitud(nombre: str) -> str:
    n = nombre.lower()
    if "area" in n:
        return "m2"
    if "volume" in n:
        return "m3"
    if "length" in n or "perimeter" in n or "width" in n or "height" in n:
        return "ml"
    return "ud"


def abrir(path):
    """Abre un IFC."""
    import ifcopenshell
    return ifcopenshell.open(str(path))


def guid_de(entidad):
    """GlobalId de una entidad o None si no es legible."""
    try:
        return entidad.GlobalId
    except Exception:  # noqa: BLE001
        return None


def cantidades_qto(elemento) -> list[dict]:
    """Cantidades del elemento leídas de sus `Qto_*` → [{magnitud, tipo, valor, fuente_qto}].

    La medición nace del modelo (D7): sólo lee los `Qto` (no computa geometría). Ignora claves de
    servicio de get_psets (`id`) y valores no numéricos.
    """
    import ifcopenshell.util.element as _ue
    out: list[dict] = []
    try:
        psets = _ue.get_psets(elemento) or {}
    except Exception:  # noqa: BLE001 — entidad corrupta
        psets = {}
    for pset_name, props in sorted(psets.items()):
        if not str(pset_name).startswith("Qto"):
            continue
        if not isinstance(props, dict):
            continue
        for prop, valor in props.items():
            if prop == "id" or not isinstance(valor, (int, float)) or isinstance(valor, bool):
                continue
            out.append({
                "magnitud": prop,
                "tipo": tipo_de_magnitud(prop),
                "valor": float(valor),
                "fuente_qto": f"{pset_name}.{prop}",
            })
    return out


def huecos_de(elemento) -> list:
    """Huecos (IfcOpeningElement) que perforan el elemento, vía `HasOpenings`
    (IfcRelVoidsElement). Permite tener en cuenta los huecos de forma auditable (D7)."""
    aberturas = []
    for rel in getattr(elemento, "HasOpenings", None) or []:
        op = getattr(rel, "RelatedOpeningElement", None)
        if op is not None:
            aberturas.append(op)
    return aberturas


def clasificacion_de(elemento) -> dict:
    """Doble clasificación {uniclass:{codigo,titulo}, bsdd:{codigo}} desde
    IfcRelAssociatesClassification, si está presente. Cosmética para el motor (mapea por CLASE),
    útil para el modelo neutro y C7."""
    import ifcopenshell.util.element as _ue
    out: dict = {}
    try:
        refs = _ue.get_references(elemento) if hasattr(_ue, "get_references") else []
    except Exception:  # noqa: BLE001
        refs = []
    for ref in refs or []:
        ident = getattr(ref, "Identification", None) or getattr(ref, "ItemReference", None)
        nombre = getattr(ref, "Name", None)
        sistema = getattr(getattr(ref, "ReferencedSource", None), "Name", "") or ""
        entry = {"codigo": ident} if ident else {}
        if nombre:
            entry["titulo"] = nombre
        if "uniclass" in sistema.lower():
            out["uniclass"] = entry
        elif ident:
            out.setdefault("uniclass", entry)
    out.setdefault("bsdd", {"codigo": elemento.is_a()})
    return out


def ubicacion_de(elemento, disciplina: str | None = None) -> dict:
    """Ubicación {planta, disciplina} desde la estructura espacial contenedora (informativa)."""
    import ifcopenshell.util.element as _ue
    planta = None
    try:
        contenedor = _ue.get_container(elemento)
        if contenedor is not None and contenedor.is_a("IfcBuildingStorey"):
            planta = getattr(contenedor, "Name", None)
    except Exception:  # noqa: BLE001
        planta = None
    out: dict = {}
    if planta:
        out["planta"] = planta
    if disciplina:
        out["disciplina"] = disciplina
    return out
