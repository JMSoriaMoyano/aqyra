"""Write-back de coste al IFC — módulo 6 del C5 (D11–D14, Fase IV·h3): el modelo se vuelve 5D.

`escribir_coste(presupuesto, derivado, salida)` abre el IFC DERIVADO (el Maestro federado que abre el
visor — D13; el engine ABRE el derivado, no federa, D7) y escribe el coste con el **modelo de coste
nativo de IFC** (D12, canónico OpenBIM), no un Pset:

  IfcCostSchedule (BUDGET)
    └ IfcRelNests → IfcCostItem por CAPÍTULO
        └ IfcRelNests → IfcCostItem por PARTIDA
            · CostValues     = [IfcCostValue(AppliedValue = IfcMonetaryMeasure(importe))]
            · CostQuantities = [IfcQuantityArea/Volume/Length/Count(cantidad medida)]
            · IfcRelAssignsToControl → los ELEMENTOS del derivado (GUID ∈ trazabilidad)
    └ IfcRelNests → IfcCostItem RESUMEN (PEM/GG/BI/base/IVA/PEC como IfcCostValue categorizados)
  + IfcMonetaryUnit (EUR) en el UnitAssignment.

Auditable hasta el elemento (la promesa del C5). DETERMINISTA (D14): cabecera SPF con firma fija sin
versión + time_stamp constante (patrón `services/federacion.derivar`, D26) y GUIDs `uuid5` para todo lo
nuevo → escribir dos veces produce BYTES idénticos; su identidad se ancla por determinismo + semántica
en la golden (GOL-PRE-02), sin md5 hardcodeado.
"""
from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

# Cabecera SPF determinista (D26/D14) — firma SIN versión adrede (un bump del engine sin cambio de
# comportamiento no puede mover los bytes del 5D; la versión vive en versions.lock).
_TIMESTAMP_DEFECTO = "1970-01-01T00:00:00"
_FIRMA_SPF = "aqyra-presupuesto"
_NS_5D = uuid.uuid5(uuid.NAMESPACE_DNS, "aqyra.5d")

# Nombre del Pset de coste NO se usa (D12: modelo de coste nativo). Nombres de propiedad estables.
_QTY = {
    "m2": ("IfcQuantityArea", "AreaValue"),
    "m3": ("IfcQuantityVolume", "VolumeValue"),
    "ml": ("IfcQuantityLength", "LengthValue"),
    "ud": ("IfcQuantityCount", "CountValue"),
    "pa": ("IfcQuantityCount", "CountValue"),
}
_RESUMEN_CLAVES = ("PEM", "gg", "bi", "base", "iva", "PEC")


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _guid_det(semilla: str) -> str:
    """GlobalId IFC (22 chars) determinista: uuid5 → compresión base64-IFC (patrón derivar)."""
    import ifcopenshell.guid
    return ifcopenshell.guid.compress(uuid.uuid5(_NS_5D, semilla).hex)


def _monetario(f, importe: float):
    """Valor monetario para un SELECT de medida (IfcAppliedValueSelect): se envuelve el defined
    type IfcMonetaryMeasure para desambiguar el select."""
    return f.create_entity("IfcMonetaryMeasure", round(float(importe), 2))


def escribir_coste(presupuesto: dict, derivado, salida, fecha: str | None = None) -> dict:
    """Escribe el cost schedule del `presupuesto` sobre el IFC `derivado` → IFC 5D en `salida`.

    Devuelve `{fichero, md5, n_cost_items, n_asignaciones}`. Determinista dado el mismo derivado y
    presupuesto (D14). No muta el derivado en disco (abre y escribe a `salida`).
    """
    import ifcopenshell

    derivado, salida = Path(derivado), Path(salida)
    f = ifcopenshell.open(str(derivado))

    res = presupuesto.get("resumen", {})
    moneda = res.get("moneda", "EUR")

    # 1 · moneda en el UnitAssignment (IfcMonetaryUnit)
    munit = f.create_entity("IfcMonetaryUnit", Currency=moneda)
    proyecto = next(iter(f.by_type("IfcProject")), None)
    if proyecto is not None and proyecto.UnitsInContext is not None:
        ua = proyecto.UnitsInContext
        ua.Units = tuple(list(ua.Units or ()) + [munit])

    # 2 · índice GUID → elemento del derivado (para las asignaciones, D12)
    idx: dict[str, object] = {}
    for p in f.by_type("IfcProduct"):
        try:
            idx.setdefault(p.GlobalId, p)
        except Exception:  # noqa: BLE001 — entidad corrupta: sin GUID
            continue

    # 3 · IfcCostSchedule (BUDGET)
    sched = f.create_entity(
        "IfcCostSchedule", GlobalId=_guid_det("schedule"),
        Name=presupuesto.get("proyecto", "Presupuesto"), PredefinedType="BUDGET")

    em = {l["codigo"]: l for l in presupuesto.get("estado_mediciones", [])}
    n_items = 0
    n_asig = 0
    root_items: list = []

    # 4 · un IfcCostItem por CAPÍTULO → por PARTIDA (D12)
    for cap in res.get("capitulos", []):
        cap_item = f.create_entity(
            "IfcCostItem", GlobalId=_guid_det(f"cap/{cap['codigo']}"),
            Name=cap.get("descripcion"), Identification=cap["codigo"])
        n_items += 1
        part_items: list = []
        for cod in cap.get("partidas", []):
            l = em.get(cod)
            if l is None:
                continue
            val = f.create_entity("IfcCostValue", AppliedValue=_monetario(f, l["importe"]))
            costqty = None
            qtyc = _QTY.get(str(l.get("unidad", "")).lower())
            if qtyc:
                ent, attr = qtyc
                v = float(l.get("cantidad", 0))
                v = int(round(v)) if ent == "IfcQuantityCount" else round(v, 4)
                costqty = [f.create_entity(ent, Name=str(l.get("unidad")), **{attr: v})]
            item = f.create_entity(
                "IfcCostItem", GlobalId=_guid_det(f"partida/{cod}"),
                Name=l.get("descripcion"), Identification=cod,
                CostValues=[val], CostQuantities=costqty)
            n_items += 1
            elems = [idx[g] for g in l.get("trazabilidad", []) if g in idx]
            if elems:
                f.create_entity(
                    "IfcRelAssignsToControl", GlobalId=_guid_det(f"assign/{cod}"),
                    RelatingControl=item, RelatedObjects=elems)
                n_asig += 1
            part_items.append(item)
        if part_items:
            f.create_entity(
                "IfcRelNests", GlobalId=_guid_det(f"nest/{cap['codigo']}"),
                RelatingObject=cap_item, RelatedObjects=part_items)
        root_items.append(cap_item)

    # 5 · IfcCostItem RESUMEN (PEM/GG/BI/base/IVA/PEC categorizados)
    res_vals = [f.create_entity("IfcCostValue", Name=k.upper(), Category=k.upper(),
                                AppliedValue=_monetario(f, res[k]))
                for k in _RESUMEN_CLAVES if k in res]
    if res_vals:
        root_items.append(f.create_entity(
            "IfcCostItem", GlobalId=_guid_det("resumen"),
            Name="Resumen PEM..PEC", Identification="RESUMEN", CostValues=res_vals))
        n_items += 1

    # 6 · los root items cuelgan del schedule (IfcRelNests)
    if root_items:
        f.create_entity("IfcRelNests", GlobalId=_guid_det("nest/schedule"),
                        RelatingObject=sched, RelatedObjects=root_items)

    # 7 · cabecera SPF determinista (D14) + escritura
    fn = f.header.file_name
    fn.name = salida.name
    fn.time_stamp = fecha or _TIMESTAMP_DEFECTO
    fn.author = ("",)
    fn.organization = ("",)
    fn.preprocessor_version = _FIRMA_SPF
    fn.originating_system = _FIRMA_SPF
    fn.authorization = ""
    salida.parent.mkdir(parents=True, exist_ok=True)
    f.write(str(salida))

    return {"fichero": salida.name, "md5": _md5(salida),
            "n_cost_items": n_items, "n_asignaciones": n_asig}
