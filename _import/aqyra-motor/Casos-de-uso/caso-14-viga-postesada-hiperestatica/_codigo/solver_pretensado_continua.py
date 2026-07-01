"""
Parser ortodoxo de la VIGA POSTESADA CONTINUA (caso 14).

Lee del IFC ortodoxo:
  - seccion: IfcRectangleProfileDef via IfcMaterialProfileSet (b=XDim, h=YDim),
  - material C40/50 de IfcMaterial/IfcMaterialProperties (fck, fctm, E),
  - apoyos: IfcStructuralPointConnection + IfcBoundaryNodeCondition (abscisas),
  - vanos: IfcStructuralCurveMember (2 -> continua de 2 vanos),
  - cargas g2/q: IfcStructuralCurveAction + IfcStructuralLoadGroup,
  - pretensado: Pset_Estructurando_Pretensado del curve member.

Devuelve el modelo neutro (dict) que consume run_all_pretensado_continua.
SI (m, N, Pa).
"""
import ifcopenshell


def _props(element):
    out = {}
    for rel in getattr(element, "IsDefinedBy", []) or []:
        if rel.is_a("IfcRelDefinesByProperties"):
            pset = rel.RelatingPropertyDefinition
            if pset.is_a("IfcPropertySet"):
                d = {}
                for p in pset.HasProperties:
                    if p.is_a("IfcPropertySingleValue") and p.NominalValue is not None:
                        d[p.Name] = p.NominalValue.wrappedValue
                out[pset.Name] = d
    return out


def _material_props(mat):
    d = {}
    for ass in mat.HasProperties or []:
        if ass.is_a("IfcMaterialProperties"):
            for p in ass.Properties:
                if p.is_a("IfcPropertySingleValue") and p.NominalValue is not None:
                    d[p.Name] = p.NominalValue.wrappedValue
    return d


def _section_and_material(ifc, member):
    b = h = None
    matname = None
    mprops = {}
    for rel in ifc.by_type("IfcRelAssociatesMaterial"):
        if member in rel.RelatedObjects:
            rm = rel.RelatingMaterial
            if rm.is_a("IfcMaterialProfileSet"):
                mp = rm.MaterialProfiles[0]
                prof = mp.Profile
                if prof.is_a("IfcRectangleProfileDef"):
                    b = float(prof.XDim); h = float(prof.YDim)
                if mp.Material:
                    matname = mp.Material.Name
                    mprops = _material_props(mp.Material)
    return b, h, matname, mprops


def parse(ifc_path):
    ifc = ifcopenshell.open(ifc_path)
    members = ifc.by_type("IfcStructuralCurveMember")
    # abscisas de cada vano
    spans = []
    for m in members:
        pts = m.Representation.Representations[0].Items[0].Points
        xs = sorted(p.Coordinates[0] for p in pts)
        spans.append((xs[0], xs[-1], m))
    spans.sort()
    n_vanos = len(spans)
    L = spans[0][1] - spans[0][0]

    b, h, matname, mprops = _section_and_material(ifc, spans[0][2])
    A = b * h
    I = b * h ** 3 / 12.0
    cdg = h / 2.0
    W = I / cdg
    fck = float(mprops.get("CompressiveStrength", 40e6))
    fctm = float(mprops.get("TensileStrength", 3.5e6))
    E = float(mprops.get("YoungModulus", 35e9))
    # fck(t) de transferencia ~ 0.8 fck (madurez ~ pocos dias)
    fck_t = 32e6 if abs(fck - 40e6) < 1e6 else 0.8 * fck

    # apoyos
    apoyos = []
    for pc in ifc.by_type("IfcStructuralPointConnection"):
        v = pc.Representation.Representations[0].Items[0].VertexGeometry.Coordinates
        apoyos.append(float(v[0]))
    apoyos.sort()

    # cargas g2 / q por grupo
    g2 = q = 0.0
    grp_of = {}
    for rel in ifc.by_type("IfcRelAssignsToGroup"):
        if rel.RelatingGroup.is_a("IfcStructuralLoadGroup"):
            for o in rel.RelatedObjects:
                grp_of[o.id()] = rel.RelatingGroup
    for act in ifc.by_type("IfcStructuralCurveAction"):
        load = act.AppliedLoad
        wz = abs(float(load.LinearForceZ or 0.0))
        grp = grp_of.get(act.id())
        if grp is None:
            continue
        at = (grp.ActionType or "").upper()
        # tomamos el valor por metro (igual en ambos vanos): no acumular
        if "PERMANENT" in at:
            g2 = max(g2, wz)
        elif "VARIABLE" in at:
            q = max(q, wz)

    # pretensado
    pr = {}
    ps = _props(spans[0][2])
    pr.update(ps.get("Pset_Estructurando_Pretensado", {}))

    model = {
        "caso": "Viga postesada continua hiperestatica (caso 14)",
        "seccion": {"b_m": b, "h_m": h, "A_m2": A, "I_m4": I, "W_m3": W,
                    "cdg_m": cdg, "c_sup_m": cdg, "c_inf_m": cdg},
        "material": {"nombre": matname or "C40/50", "fck_Pa": fck,
                     "fctm_Pa": fctm, "fck_t_Pa": fck_t, "E_Pa": E},
        "geometria": {"L_vano_m": L, "n_vanos": n_vanos, "apoyos_x_m": apoyos,
                      "L_total_m": n_vanos * L},
        "cargas": {"g2_N_m": g2, "q_N_m": q, "psi2": 0.3, "psi0": 0.7, "psi1": 0.5,
                   "g0_N_m": A * 25.0e3},
        "pretensado": pr,
    }
    return model
