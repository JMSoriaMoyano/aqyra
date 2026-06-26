#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""construir_catalogo.py -> vuelca el catálogo completo IFC4X3 a JSON.
Uso: python3 construir_catalogo.py catalogo-ifc4x3.json"""
import sys, json, collections
import catalogo_ifc as C

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "catalogo-ifc4x3.json"
    cat = C.construir_catalogo()
    doc = {
        "_esquema": C.SCHEMA,
        "_bsdd_diccionario": "https://identifier.buildingsmart.org/uri/buildingsmart/ifc/4.3",
        "_total": len(cat),
        "_por_grupo": dict(collections.Counter(v["grupo"] for v in cat.values())),
        "clases": cat,
    }
    json.dump(doc, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"OK  catálogo -> {out}  ({len(cat)} clases)")
    for g, n in sorted(doc["_por_grupo"].items(), key=lambda x: -x[1]):
        print(f"    {g:26} {n}")

if __name__ == "__main__":
    main()
