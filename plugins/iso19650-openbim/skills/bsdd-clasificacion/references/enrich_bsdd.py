"""Enriquece un IFC con datos de bsDD: clasificacion doble (Uniclass + GuBIMClass),
URI de entidad bsDD y propiedades por defecto.

Uso: python enrich_bsdd.py modelo.ifc mapping.json salida.ifc

mapping.json (preparado por Claude a partir de consultas a bsDD via web_fetch):
{
  "IfcWall": {
    "bsdd_entity_uri": "https://identifier.buildingsmart.org/uri/buildingsmart/ifc/4.3/class/IfcWall",
    "uniclass": {"identification": "EF_25", "name": "Wall and barrier elements",
                 "uri": "https://identifier.buildingsmart.org/uri/nbs/uniclass2015/1/class/EF_25"},
    "gubim":    {"identification": "E1.10", "name": "Cerramientos verticales",
                 "uri": ""},
    "properties": [
        {"pset": "Pset_WallCommon", "name": "IsExternal", "value": true, "type": "IfcBoolean"}
    ]
  }
}
La clave puede ser "IfcWall" o "IfcWall.PARTITIONING" (clase.PredefinedType).
"""
import sys, json
import ifcopenshell
from ifcopenshell.api import run

def key_for(el):
    pt = getattr(el, "PredefinedType", None)
    base = el.is_a()
    return [f"{base}.{pt}", base] if pt and pt not in ("NOTDEFINED", None) else [base]

def get_classif(model, cache, name):
    if name not in cache:
        cache[name] = run("classification.add_classification", model, classification=name)
    return cache[name]

def main(ifc_in, mapping_path, ifc_out):
    model = ifcopenshell.open(ifc_in)
    mapping = json.load(open(mapping_path, encoding="utf-8"))
    cache = {}
    stats = {"elementos": 0, "uniclass": 0, "gubim": 0, "bsdd_uri": 0, "props": 0}
    for el in model.by_type("IfcObject"):
        if not el.is_a("IfcElement") and not el.is_a("IfcSpace"):
            continue
        spec = None
        for k in key_for(el):
            if k in mapping:
                spec = mapping[k]; break
        if not spec:
            continue
        stats["elementos"] += 1
        # 1) URI de entidad bsDD -> referencia de clasificacion al diccionario IFC de bsDD
        if spec.get("bsdd_entity_uri"):
            c = get_classif(model, cache, "bSDD - IFC")
            ref = run("classification.add_reference", model, products=[el],
                identification=el.is_a(), name=el.is_a(),
                classification=c, is_lightweight=False)
            if ref is not None:
                ref.Location = spec["bsdd_entity_uri"]
            stats["bsdd_uri"] += 1
        # 2) Doble clasificacion
        for sysname, syskey in (("Uniclass 2015", "uniclass"), ("GuBIMClass", "gubim")):
            d = spec.get(syskey)
            if d and d.get("identification"):
                c = get_classif(model, cache, sysname)
                ref = run("classification.add_reference", model, products=[el],
                    identification=d["identification"], name=d.get("name", ""),
                    classification=c, is_lightweight=False)
                if ref is not None and d.get("uri"):
                    ref.Location = d["uri"]
                stats["uniclass" if syskey == "uniclass" else "gubim"] += 1
        # 3) Propiedades por defecto (de bsDD)
        byp = {}
        for p in spec.get("properties", []):
            byp.setdefault(p["pset"], {})[p["name"]] = p["value"]
        for psetname, props in byp.items():
            ps = run("pset.add_pset", model, product=el, name=psetname)
            run("pset.edit_pset", model, pset=ps, properties=props)
            stats["props"] += len(props)  # aplicadas (pueden fusionarse con psets existentes)
    model.write(ifc_out)
    print("Enriquecido ->", ifc_out)
    print("Resumen:", json.dumps(stats, ensure_ascii=False))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
