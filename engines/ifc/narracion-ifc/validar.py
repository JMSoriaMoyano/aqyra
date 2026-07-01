#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validar.py  --  Validacion del IFC generado por el compilador narracion->IFC (doble modo).

Reune comprobaciones de INTEGRIDAD estructural del modelo (complementa la skill
`ifc-validate`, cuyos checks de dominio MEP/lineal se encadenan si procede).

Modos:
  (por defecto)   INFORME no bloqueante: imprime incidencias y SIEMPRE exit 0.
  --estricto      PUERTA: exit 1 si hay alguna incidencia ERROR (dura).

Uso:
  python3 validar.py modelo.ifc [--estricto] [--esquema IFC4X3]

Severidades: ERROR (rompe interoperabilidad), AVISO (mejorable), INFO.
"""
import sys
import ifcopenshell
import ifcopenshell.util.element as ue

REQUIRED_PSETS = {  # AVISO si faltan (no bloquean: hay arquetipos placeholder)
    "IfcWall": ["Pset_WallCommon"], "IfcSlab": ["Pset_SlabCommon"],
    "IfcColumn": ["Pset_ColumnCommon"], "IfcBeam": ["Pset_BeamCommon"],
}

def validar(path, esquema_esperado=None):
    m = ifcopenshell.open(path)
    I = []  # (sev, clase, gid, desc)
    def add(sev, cls, gid, desc): I.append((sev, cls, gid, desc))

    # 0) esquema
    add("INFO", "-", "-", f"Esquema IFC detectado: {m.schema}")
    if esquema_esperado and m.schema != esquema_esperado:
        add("ERROR", "-", "-", f"Esquema {m.schema} != esperado {esquema_esperado}")

    # 1) unidades SI (longitud en metros, sin prefijo)
    ok_len = False
    for ua in m.by_type("IfcUnitAssignment"):
        for u in ua.Units or []:
            if u.is_a("IfcSIUnit") and u.UnitType == "LENGTHUNIT":
                ok_len = (u.Name == "METRE" and not u.Prefix)
    if not ok_len:
        add("ERROR", "IfcUnitAssignment", "-", "Sin unidad de longitud SI en metros (LENGTHUNIT=METRE sin prefijo)")

    # 2) contexto geometrico
    if not m.by_type("IfcGeometricRepresentationContext"):
        add("ERROR", "-", "-", "No hay IfcGeometricRepresentationContext (geometria sin contexto)")

    # 3) GlobalId duplicados
    seen = {}
    for r in m.by_type("IfcRoot"):
        g = getattr(r, "GlobalId", None)
        if g: seen.setdefault(g, []).append(r.is_a())
    for g, clases in seen.items():
        if len(clases) > 1:
            add("ERROR", "/".join(clases), g, f"GlobalId duplicado ({len(clases)} entidades)")

    # 4) integridad de huecos (RelVoids) y rellenos (RelFills)
    for rel in m.by_type("IfcRelVoidsElement"):
        if rel.RelatingBuildingElement is None or rel.RelatedOpeningElement is None:
            add("ERROR", "IfcRelVoidsElement", getattr(rel, "GlobalId", "?"), "RelVoids con host u opening nulo")
    for op in m.by_type("IfcOpeningElement"):
        if not getattr(op, "VoidsElements", None):
            add("AVISO", "IfcOpeningElement", op.GlobalId, "Hueco no asociado a ningun elemento (RelVoids ausente)")
    for rel in m.by_type("IfcRelFillsElement"):
        if rel.RelatingOpeningElement is None or rel.RelatedBuildingElement is None:
            add("ERROR", "IfcRelFillsElement", getattr(rel, "GlobalId", "?"), "RelFills con opening o relleno nulo")

    # 5) por elemento: nombre, representacion, Psets, clasificacion bsDD
    n_geo = 0
    for el in m.by_type("IfcElement"):
        cls = el.is_a(); gid = getattr(el, "GlobalId", "?")
        if not getattr(el, "Name", None):
            add("AVISO", cls, gid, "Elemento sin Nombre")
        rep = getattr(el, "Representation", None)
        if rep is not None:
            n_geo += 1
            reps = rep.Representations or []
            if not reps or all(not (r.Items or []) for r in reps):
                add("ERROR", cls, gid, "Representacion presente pero sin Items (geometria vacia)")
        psets = ue.get_psets(el)
        for req in REQUIRED_PSETS.get(cls, []):
            if req not in psets:
                add("AVISO", cls, gid, f"Falta Pset estandar: {req}")
    add("INFO", "-", "-", f"IfcElement: {len(m.by_type('IfcElement'))} | con geometria: {n_geo}")

    return m, I


def informe(m, I):
    orden = {"ERROR": 0, "AVISO": 1, "INFO": 2}
    I = sorted(I, key=lambda x: orden.get(x[0], 9))
    n = {"ERROR": 0, "AVISO": 0, "INFO": 0}
    for sev, *_ in I: n[sev] = n.get(sev, 0) + 1
    print("=" * 64)
    print(f"VALIDACION IFC  ({m.schema})   ERROR={n['ERROR']}  AVISO={n['AVISO']}  INFO={n['INFO']}")
    print("=" * 64)
    for sev, cls, gid, desc in I:
        if sev == "INFO":
            print(f"  [INFO]  {desc}")
        else:
            print(f"  [{sev}] {cls} {gid}: {desc}")
    return n


def main():
    args = sys.argv[1:]
    if not args:
        print("Uso: python3 validar.py modelo.ifc [--estricto] [--esquema IFC4X3]"); sys.exit(2)
    path = args[0]; estricto = "--estricto" in args
    esquema = None
    if "--esquema" in args: esquema = args[args.index("--esquema") + 1]
    m, I = validar(path, esquema_esperado=esquema)
    n = informe(m, I)
    if estricto and n["ERROR"] > 0:
        print(f"\n>>> NO APTO (modo estricto): {n['ERROR']} ERROR <<<"); sys.exit(1)
    print(f"\nVEREDICTO: {'con errores (informativo)' if n['ERROR'] else 'sin errores duros'}"
          + (" — modo informe (no bloqueante)" if not estricto else " — APTO (estricto)"))

if __name__ == "__main__":
    main()
