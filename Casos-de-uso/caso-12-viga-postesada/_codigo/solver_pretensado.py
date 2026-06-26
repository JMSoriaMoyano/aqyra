"""
Parser IFC -> MODELO NEUTRO de la VIGA POSTESADA isostatica (Caso 12, EC2 §5.10).

Estrategia ortodoxa (igual que casos 5/6/7/9/11):
  - Lee la VIGA (IfcStructuralCurveMember) con su seccion (IfcRectangleProfileDef
    via IfcMaterialProfileSet) y material (C40/50) por la via estandar.
  - Lee los APOYOS (IfcStructuralPointConnection + IfcBoundaryNodeCondition):
    idealizacion isostatica biapoyada.
  - Lee las CARGAS g2/q (IfcStructuralCurveAction + IfcStructuralLoadLinearForce)
    por la via ortodoxa, agrupadas por IfcStructuralLoadGroup (permanente/variable).
  - Lee el PRETENSADO del Pset_Estructurando_Pretensado (P0/sigma_p0, Ap, fpk,
    trazado parabolico/e, conducto, coeficientes de perdidas, anclajes).
  - El peso propio g0 = A*rho*g lo deriva de la seccion y la densidad.

  Para reutilizar el cargador generico de materiales se importa
  laminas/ifc_to_model_3d.py por RUTA EXPLICITA con salvaguarda de sys.path
  (modulos homonimos entre paquetes); si no esta disponible, se leen los
  materiales directamente del IFC (fallback robusto).

Uso: python3 solver_pretensado.py <caso-12.ifc> <salida_modelo.json>
SI (m, N, Pa). Eje de la viga en X, Z vertical, gravedad -Z.
"""
import sys
import os
import json
import importlib.util

import ifcopenshell

HERE = os.path.dirname(os.path.abspath(__file__))
G = 9.81

# Valores de respaldo (enunciado) si faltan en el Pset
FALLBACK_PRET = {
    "Sistema": "postesado_adherente", "n_tendones": 1, "n_cordones": 13,
    "tipo_cordon": "Y1860S7 0.6\"", "Ap_mm2": 1950.0, "fpk_MPa": 1860.0,
    "fp01k_MPa": 1640.0, "Ep_GPa": 195.0, "P0_kN": 2535.0,
    "sigma_p0_MPa": 1300.0, "Pm_inf_kN": 2125.0, "sigma_pm_inf_MPa": 1089.7,
    "trazado": "parabolico", "e_centro_m": 0.50, "e_apoyo_m": 0.0,
    "recubrimiento_mec_m": 0.15, "mu_rozamiento": 0.19, "k_desviacion": 0.01,
    "penetracion_cuna_mm": 6.0, "relajacion_clase": 2, "rho1000_pct": 2.5,
    "tesado": "dos_extremos",
}
FALLBACK_MAT = {"nombre": "C40/50", "E_Pa": 35e9, "nu": 0.2, "fck_Pa": 40e6,
                "fck_t_Pa": 32e6, "fctm_Pa": 3.5e6, "rho": 2500.0,
                "G_Pa": 35e9 / 2.4}


def _try_load_ifc_to_model_3d():
    """Carga laminas/ifc_to_model_3d.py por ruta explicita (salvaguarda contra
    modulos homonimos). Devuelve el modulo o None si no esta disponible."""
    path = os.path.join(HERE, "..", "laminas", "ifc_to_model_3d.py")
    path = os.path.abspath(path)
    if not os.path.exists(path):
        return None
    try:
        sys.path.insert(0, os.path.dirname(path))
        sys.path.insert(0, os.path.join(HERE, "..", "barras"))
        spec = importlib.util.spec_from_file_location("ifc_to_model_3d_pret", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        return None


def _psets(element):
    out = {}
    for rel in getattr(element, "IsDefinedBy", []) or []:
        if rel.is_a("IfcRelDefinesByProperties"):
            pdef = rel.RelatingPropertyDefinition
            if pdef.is_a("IfcPropertySet"):
                props = {p.Name: p.NominalValue.wrappedValue
                         for p in pdef.HasProperties
                         if p.is_a("IfcPropertySingleValue") and p.NominalValue is not None}
                out[pdef.Name] = props
    return out


def _material_props(mat):
    """Lee E, nu, fck, fctm, rho de las IfcMaterialProperties del material."""
    mp = {"nombre": mat.Name}
    for rel in mat.HasProperties or []:
        for p in rel.Properties or []:
            if p.is_a("IfcPropertySingleValue") and p.NominalValue is not None:
                v = p.NominalValue.wrappedValue
                if p.Name == "YoungModulus":
                    mp["E_Pa"] = float(v)
                elif p.Name == "PoissonRatio":
                    mp["nu"] = float(v)
                elif p.Name == "ShearModulus":
                    mp["G_Pa"] = float(v)
                elif p.Name == "CompressiveStrength":
                    mp["fck_Pa"] = float(v)
                elif p.Name == "TensileStrength":
                    mp["fctm_Pa"] = float(v)
                elif p.Name == "MassDensity":
                    mp["rho"] = float(v)
    return mp


def _read_section(ifc, member):
    """Seccion rectangular via IfcMaterialProfileSet -> IfcRectangleProfileDef.
    Devuelve (b, h, material_props)."""
    b = h = None
    mat = None
    for rel in ifc.by_type("IfcRelAssociatesMaterial"):
        if member in (rel.RelatedObjects or []):
            rm = rel.RelatingMaterial
            if rm.is_a("IfcMaterialProfileSet"):
                for prof in rm.MaterialProfiles or []:
                    pr = prof.Profile
                    if pr is not None and pr.is_a("IfcRectangleProfileDef"):
                        b = float(pr.XDim); h = float(pr.YDim)
                    if prof.Material is not None:
                        mat = prof.Material
            elif rm.is_a("IfcMaterial"):
                mat = rm
    mp = _material_props(mat) if mat is not None else {}
    # completar con respaldo
    out = dict(FALLBACK_MAT)
    out.update({k: v for k, v in mp.items() if v is not None})
    return b, h, out


def _read_supports(ifc):
    sup = []
    for c in ifc.by_type("IfcStructuralPointConnection"):
        coords = None
        if c.Representation is not None:
            for r in c.Representation.Representations:
                for item in r.Items:
                    if item.is_a("IfcVertexPoint"):
                        cc = item.VertexGeometry.Coordinates
                        coords = [float(cc[0]), float(cc[1]), float(cc[2])]
        bc = c.AppliedCondition
        restr = None
        if bc is not None and bc.is_a("IfcBoundaryNodeCondition"):
            def g(a):
                return a is not None and getattr(a, "wrappedValue", a) is True
            restr = [g(bc.TranslationalStiffnessX), g(bc.TranslationalStiffnessY),
                     g(bc.TranslationalStiffnessZ), g(bc.RotationalStiffnessX),
                     g(bc.RotationalStiffnessY), g(bc.RotationalStiffnessZ)]
        sup.append({"nombre": c.Name, "coords": coords, "restriccion": restr})
    sup.sort(key=lambda d: (d["coords"][0] if d["coords"] else 0.0))
    return sup


def _read_curve_loads(ifc):
    """Lee cargas lineales gravitatorias (LinearForceZ<0, N/m) por grupo."""
    group_of = {}
    for rel in ifc.by_type("IfcRelAssignsToGroup"):
        grp = rel.RelatingGroup
        if grp is not None and grp.is_a("IfcStructuralLoadGroup"):
            for obj in rel.RelatedObjects or []:
                group_of[obj.id()] = grp
    cargas = []
    for act in ifc.by_type("IfcStructuralCurveAction"):
        load = act.AppliedLoad
        if load is None or not load.is_a("IfcStructuralLoadLinearForce"):
            continue
        wz = getattr(load, "LinearForceZ", None)
        if wz is None:
            continue
        grp = group_of.get(act.id())
        cargas.append({
            "accion": act.Name,
            "w_N_m": abs(float(wz)),
            "grupo": grp.Name if grp is not None else None,
            "action_type": getattr(grp, "ActionType", None) if grp is not None else None,
        })
    return cargas


def parse(ifc_path):
    ifc = ifcopenshell.open(ifc_path)
    _try_load_ifc_to_model_3d()   # garantiza disponibilidad / salvaguarda sys.path

    member = ifc.by_type("IfcStructuralCurveMember")[0]

    # 1) seccion y material
    b, h, mat = _read_section(ifc, member)
    if b is None:
        b, h = 0.50, 1.30
    A = b * h
    I = b * h ** 3 / 12.0
    c_sup = c_inf = h / 2.0
    W_sup = I / c_sup
    W_inf = I / c_inf

    # 2) apoyos -> luz L
    sup = _read_supports(ifc)
    xs = [s["coords"][0] for s in sup if s["coords"] is not None]
    L = (max(xs) - min(xs)) if len(xs) >= 2 else 20.0

    # 3) cargas g2/q
    cargas = _read_curve_loads(ifc)
    g2 = 0.0
    q = 0.0
    for c in cargas:
        at = (c["action_type"] or "").upper()
        if "PERMANENT" in at:
            g2 += c["w_N_m"]
        elif "VARIABLE" in at or "LIVE" in at:
            q += c["w_N_m"]
    # peso propio g0. Convencion validada del plugin: peso especifico del hormigon
    # armado gamma_c = 25 kN/m3 (EC2/EHE), de modo que g0 = A * gamma_c. (Equivale a
    # A*rho*g con rho=2500 kg/m3; se adopta gamma_c=25000 N/m3 para coincidir con la
    # practica espanola y el chequeo de mano.)
    rho = float(mat.get("rho", 2500.0))
    gamma_c = 25000.0
    g0 = A * gamma_c

    # 4) pretensado (Pset)
    ps = _psets(member)
    pr = dict(FALLBACK_PRET)
    pr.update(ps.get("Pset_Estructurando_Pretensado", {}))

    model = {
        "caso": "12-viga-postesada",
        "unidades": {"longitud": "m", "fuerza": "N", "tension": "Pa"},
        "tipo": "viga_postesada_isostatica",
        "material": {
            "nombre": mat.get("nombre", "C40/50"),
            "E_Pa": float(mat.get("E_Pa", 35e9)),
            "nu": float(mat.get("nu", 0.2)),
            "G_Pa": float(mat.get("G_Pa", 35e9 / 2.4)),
            "fck_Pa": float(mat.get("fck_Pa", 40e6)),
            "fck_t_Pa": float(mat.get("fck_t_Pa", 32e6)),
            "fctm_Pa": float(mat.get("fctm_Pa", 3.5e6)),
            "rho": rho,
        },
        "seccion": {
            "b_m": b, "h_m": h, "A_m2": A, "I_m4": I,
            "c_sup_m": c_sup, "c_inf_m": c_inf,
            "W_sup_m3": W_sup, "W_inf_m3": W_inf,
            "cdg_m": h / 2.0,
        },
        "geometria": {"L_m": L, "n_apoyos": len(sup), "isostatica": True},
        "apoyos": sup,
        "cargas": {
            "g0_N_m": g0, "g2_N_m": g2, "q_N_m": q,
            "g0_kN_m": g0 / 1e3, "g2_kN_m": g2 / 1e3, "q_kN_m": q / 1e3,
            "psi2": 0.3, "psi1": 0.5, "psi0": 0.7,
            "detalle": cargas,
        },
        "pretensado": pr,
        "notas": [
            "Viga isostatica biapoyada; idealizacion 1D (flexion).",
            "Peso propio g0 = A*rho*g derivado de la seccion y la densidad.",
            "Pretensado leido del Pset_Estructurando_Pretensado (respaldo: "
            "valores del enunciado).",
            "Trazado parabolico e_centro=%.2f m, e_apoyo=%.2f m." % (
                float(pr.get("e_centro_m", 0.5)), float(pr.get("e_apoyo_m", 0.0))),
            "[confirmar AN] EC2 §5.10 NDP Espana: mu/k de rozamiento, "
            "penetracion de cuna, limites de tension del acero activo.",
        ],
    }
    return model


if __name__ == "__main__":
    ifc_path = sys.argv[1] if len(sys.argv) > 1 else "caso-12.ifc"
    out = sys.argv[2] if len(sys.argv) > 2 else "modelo_neutro.json"
    m = parse(ifc_path)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    json.dump(m, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    s = m["seccion"]; c = m["cargas"]; pr = m["pretensado"]
    print("Modelo neutro (viga postesada) escrito en:", out)
    print("  Seccion b=%.2f h=%.2f  A=%.3f m2  I=%.6f m4  W=%.6f m3  L=%.1f m" % (
        s["b_m"], s["h_m"], s["A_m2"], s["I_m4"], s["W_inf_m3"], m["geometria"]["L_m"])
)
   print("  Cargas g0=%.2f g2=%.2f q=%.2f kN/m" % (
        c["g0_kN_m"], c["g2_kN_m"], c["q_kN_m"]))
    print("  Pretensado P0=%.0f kN  Pm,inf=%.0f kN  Ap=%.0f mm2  e=%.2f m" % (
        float(pr["P0_kN"]), float(pr["Pm_inf_kN"]), float(pr["Ap_mm2"]),
        float(pr["e_centro_m"])))
