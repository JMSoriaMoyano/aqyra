"""Comprobaciones base de validacion IFC con IfcOpenShell.
Uso: python checks-ifc.py modelo.ifc
Adaptar REQUIRED_PSETS y reglas al proyecto."""
import sys
import ifcopenshell
import ifcopenshell.util.element as ue

# Psets obligatorios por clase IFC (ajustar al EIR/LOIN del proyecto)
REQUIRED_PSETS = {
    "IfcWall": ["Pset_WallCommon"],
    "IfcSlab": ["Pset_SlabCommon"],
    "IfcColumn": ["Pset_ColumnCommon"],
    "IfcBeam": ["Pset_BeamCommon"],
}

def main(path):
    m = ifcopenshell.open(path)
    print(f"Esquema IFC: {m.schema}")
    issues = []
    # Conteo por clase
    counts = {}
    for el in m.by_type("IfcElement"):
        counts[el.is_a()] = counts.get(el.is_a(), 0) + 1
    print("Conteo por clase:", counts)
    # Reglas
    for el in m.by_type("IfcElement"):
        cls = el.is_a()
        gid = getattr(el, "GlobalId", "?")
        if not getattr(el, "Name", None):
            issues.append((("AVISO"), cls, gid, "Elemento sin Nombre"))
        psets = ue.get_psets(el)
        for req in REQUIRED_PSETS.get(cls, []):
            if req not in psets:
                issues.append(("BLOQUEANTE", cls, gid, f"Falta Pset requerido: {req}"))
    print(f"\nIncidencias: {len(issues)}")
    for sev, cls, gid, desc in issues[:200]:
        print(f"[{sev}] {cls} {gid}: {desc}")

if __name__ == "__main__":
    main(sys.argv[1])
