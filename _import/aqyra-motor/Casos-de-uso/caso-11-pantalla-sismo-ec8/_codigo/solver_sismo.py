"""
Parser IFC -> MODELO NEUTRO (stick) de la PANTALLA DE CORTANTE (Caso 11, EC8).

Estrategia ortodoxa (igual que casos 5/6/7/9):
  - Reutiliza laminas/ifc_to_model_3d.py para el modelo neutro generico de la
    superficie (PANTALLA: nodos, esquinas, espesor, material C30/37, base
    empotrada). Carga ese modulo por RUTA EXPLICITA con salvaguarda de
    sys.path (modulos homonimos entre paquetes).
  - Lee las MASAS sismicas de los IfcStructuralPointAction (aqui via
    IfcStructuralLoadSingleForce.ForceZ negativo -> W_i) mapeadas a su nodo de
    planta (z), y los PARAMETROS EC8 del Pset_Estructurando_Sismo (con respaldo
    a los valores del enunciado si falta alguno).
  - Construye el VOLADIZO EQUIVALENTE (stick de 6 nodos) con la seccion de la
    pared: E (Ecm), I=tw*Lw^3/12, A=tw*Lw, area de cortante A_v y G=Ecm/2.4.

Uso: python3 solver_sismo.py <caso-11.ifc> <salida_modelo.json>
"""
import sys
import os
import json
import importlib.util

import ifcopenshell

HERE = os.path.dirname(os.path.abspath(__file__))
G = 9.81

# Valores de respaldo (enunciado) si faltan en el Pset
FALLBACK_EC8 = {
    "ag_g": 0.20, "TipoSuelo": "C", "TipoEspectro": 1, "S": 1.15,
    "TB_s": 0.20, "TC_s": 0.60, "TD_s": 2.0, "ClaseImportancia": "II",
    "gammaI": 1.0, "q": 3.0, "amortiguamiento": 0.05, "lambda": 0.85,
}
FALLBACK_GEO = {"Lw_m": 4.0, "tw_m": 0.30, "H_m": 15.0, "n_plantas": 5,
                "h_planta_m": 3.0, "ClaseDuctilidad": "DCM"}


def _load_ifc_to_model_3d():
    """Carga laminas/ifc_to_model_3d.py por ruta explicita (salvaguarda
    contra modulos homonimos)."""
    path = os.path.join(HERE, "..", "laminas", "ifc_to_model_3d.py")
    path = os.path.abspath(path)
    sys.path.insert(0, os.path.dirname(path))
    sys.path.insert(0, os.path.join(HERE, "..", "barras"))
    spec = importlib.util.spec_from_file_location("ifc_to_model_3d_sismo", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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


def _node_coords(conn):
    for r in conn.Representation.Representations:
        for item in r.Items:
            if item.is_a("IfcVertexPoint"):
                c = item.VertexGeometry.Coordinates
                return [float(c[0]), float(c[1]), float(c[2])]
    return None


def _read_masses(ifc):
    """Lee las masas sismicas: IfcStructuralPointAction con
    IfcStructuralLoadSingleForce.ForceZ<0 -> W_i (N), mapeadas a su nodo de
    planta por IfcRelConnectsStructuralActivity."""
    # mapa accion -> nodo destino
    node_of = {}
    for rel in ifc.by_type("IfcRelConnectsStructuralActivity"):
        act = rel.RelatedStructuralActivity
        el = rel.RelatingElement
        if act is not None and el is not None and el.is_a("IfcStructuralPointConnection"):
            node_of[act.id()] = el
    masas = []
    for act in ifc.by_type("IfcStructuralPointAction"):
        load = act.AppliedLoad
        if load is None or not load.is_a("IfcStructuralLoadSingleForce"):
            continue
        fz = getattr(load, "ForceZ", None)
        if fz is None:
            continue
        W = abs(float(fz))            # N (ForceZ negativo -> peso)
        conn = node_of.get(act.id())
        coords = _node_coords(conn) if conn is not None else None
        if coords is None:
            continue
        masas.append({
            "accion": act.Name, "nodo": conn.Name,
            "z": coords[2], "W_N": W, "m_kg": W / G,
        })
    masas.sort(key=lambda d: d["z"])
    return masas


def _read_ec8(ifc, surf_member):
    ps = _psets(surf_member)
    sis = ps.get("Pset_Estructurando_Sismo", {})
    geo = ps.get("Pset_Estructurando_Pantalla", {})
    ec8 = {}
    for k, v in FALLBACK_EC8.items():
        ec8[k] = sis.get(k, v)
    pant = {}
    for k, v in FALLBACK_GEO.items():
        pant[k] = geo.get(k, v)
    return ec8, pant


def parse(ifc_path):
    ifc = ifcopenshell.open(ifc_path)
    # 1) modelo neutro generico de la superficie (reutilizado)
    base = _load_ifc_to_model_3d()
    neutro = base.parse(ifc_path)

    # superficie pantalla
    surf = neutro["superficies"][0] if neutro["superficies"] else None
    mat_name = surf["material"] if surf else "C30/37"
    mp = neutro["materiales"].get(mat_name, {})

    # 2) parametros EC8 + geometria (del Pset de la superficie en el IFC)
    surf_member = ifc.by_type("IfcStructuralSurfaceMember")[0]
    ec8, pant = _read_ec8(ifc, surf_member)

    # 3) masas por planta
    masas = _read_masses(ifc)

    # 4) seccion de la pared (voladizo equivalente)
    Lw = float(pant["Lw_m"]); tw = float(pant["tw_m"]); H = float(pant["H_m"])
    E = float(mp.get("E") or 33e9)
    nu = float(mp.get("nu") or 0.2)
    Gsh = float(mp.get("G") or E / (2.0 * (1.0 + nu)))
    I = tw * Lw ** 3 / 12.0           # m4 (en el plano)
    A = tw * Lw                         # m2
    A_v = A * (5.0 / 6.0)               # area de cortante (alma rectangular)

    # 5) nodos del stick (cota z), incluida la base; masas mapeadas a su z
    z_base = 0.0
    z_plantas = [m["z"] for m in masas]
    nodos = [{"nombre": "PISO_0_base", "z": z_base, "m_kg": 0.0, "apoyo": "empotrado"}]
    for m in masas:
        nodos.append({"nombre": m["nodo"], "z": m["z"], "m_kg": m["m_kg"],
                      "W_kN": m["W_N"] / 1e3})

    model = {
        "caso": "11-pantalla-sismo-ec8",
        "unidades": {"longitud": "m", "fuerza": "N", "masa": "kg"},
        "material": {
            "nombre": mat_name,
            "E_Pa": E, "G_Pa": Gsh, "nu": nu,
            "fck_Pa": mp.get("fck"), "fctm_Pa": mp.get("fctm"),
            "rho": mp.get("rho"),
        },
        "seccion_pared": {
            "Lw_m": Lw, "tw_m": tw, "H_m": H,
            "I_m4": I, "A_m2": A, "A_v_m2": A_v,
            "I_formula": "tw*Lw^3/12", "A_v_formula": "A*5/6",
        },
        "stick": {
            "n_nodos": len(nodos),
            "z_nodes_m": [n["z"] for n in nodos],
            "z_plantas_m": z_plantas,
            "nodos": nodos,
        },
        "masas": {
            "por_planta_kg": [m["m_kg"] for m in masas],
            "por_planta_W_kN": [m["W_N"] / 1e3 for m in masas],
            "z_m": z_plantas,
            "M_total_kg": sum(m["m_kg"] for m in masas),
            "W_total_kN": sum(m["W_N"] for m in masas) / 1e3,
            "detalle": masas,
        },
        "ec8": ec8,
        "pantalla": pant,
        "notas": [
            "Voladizo equivalente (stick) con seccion de pared; flexion "
            "Euler-Bernoulli + flexibilidad de cortante Timoshenko.",
            "Masas concentradas por planta (lumped).",
            "Parametros EC8 leidos de Pset_Estructurando_Sismo (respaldo: "
            "valores del enunciado). [confirmar AN] NCSE-02 / EC8 NDP Espana.",
        ],
    }
    return model


if __name__ == "__main__":
    ifc_path = sys.argv[1] if len(sys.argv) > 1 else "caso-11.ifc"
    out = sys.argv[2] if len(sys.argv) > 2 else "modelo_neutro.json"
    m = parse(ifc_path)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    json.dump(m, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("Modelo neutro (stick) escrito en:", out)
    print("  nodos=%d  masas=%d  M_total=%.1f t  W_total=%.0f kN" % (
        m["stick"]["n_nodos"], len(m["masas"]["por_planta_kg"]),
        m["masas"]["M_total_kg"] / 1e3, m["masas"]["W_total_kN"]))
    print("  Lw=%.2f tw=%.2f H=%.1f  I=%.3f m4  A=%.3f m2  A_v=%.3f m2" % (
        m["seccion_pared"]["Lw_m"], m["seccion_pared"]["tw_m"],
        m["seccion_pared"]["H_m"], m["seccion_pared"]["I_m4"],
        m["seccion_pared"]["A_m2"], m["seccion_pared"]["A_v_m2"]))
