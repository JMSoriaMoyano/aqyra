"""
Parser IFC -> MODELO NEUTRO (3 GdL/planta, diafragma rigido) del NUCLEO DE
PANTALLAS ACOPLADAS (caso 15, PT 1.5). Extiende solver_sismo.py (pantalla
aislada) a VARIAS pantallas en planta. Reutiliza laminas/ifc_to_model_3d.py.
EXTIENDE el esquema del modelo neutro con claves NUEVAS (pantallas[], dinteles,
diafragma) SIN alterar las existentes (contrato C1).
Uso: python3 solver_nucleo.py <caso-15.ifc> <salida_modelo.json>
"""
import sys, os, json, importlib.util
import ifcopenshell

HERE = os.path.dirname(os.path.abspath(__file__))
G = 9.81

FALLBACK_EC8 = {"ag_g": 0.20, "TipoSuelo": "C", "TipoEspectro": 1, "S": 1.15,
    "TB_s": 0.20, "TC_s": 0.60, "TD_s": 2.0, "ClaseImportancia": "II",
    "gammaI": 1.0, "q": 3.6, "amortiguamiento": 0.05, "lambda": 0.85}
FALLBACK_NUC = {"Tipologia": "nucleo_U_abierto", "Dintel_b_m": 0.30, "Dintel_h_m": 0.70,
    "Dintel_ln_m": 1.40, "Dinteles_por_planta": 1, "AberturaPuerta_m": 1.40,
    "DireccionAcoplamiento": "Y", "Edificio_Lx_m": 20.0, "Edificio_Ly_m": 14.0,
    "CM_x_m": None, "CM_y_m": None, "ClaseDuctilidad": "DCM"}


def _load_ifc_to_model_3d():
    path = os.path.abspath(os.path.join(HERE, "..", "laminas", "ifc_to_model_3d.py"))
    sys.path.insert(0, os.path.dirname(path))
    sys.path.insert(0, os.path.join(HERE, "..", "barras"))
    spec = importlib.util.spec_from_file_location("ifc_to_model_3d_nucleo", path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def _psets(element):
    out = {}
    for rel in getattr(element, "IsDefinedBy", []) or []:
        if rel.is_a("IfcRelDefinesByProperties"):
            pdef = rel.RelatingPropertyDefinition
            if pdef.is_a("IfcPropertySet"):
                out[pdef.Name] = {p.Name: getattr(p.NominalValue, "wrappedValue", None)
                    for p in pdef.HasProperties
                    if p.is_a("IfcPropertySingleValue") and p.NominalValue is not None}
    return out


def _node_coords(conn):
    for r in conn.Representation.Representations:
        for item in r.Items:
            if item.is_a("IfcVertexPoint"):
                c = item.VertexGeometry.Coordinates
                return [float(c[0]), float(c[1]), float(c[2])]
    return None


def _read_masses(ifc):
    node_of = {}
    for rel in ifc.by_type("IfcRelConnectsStructuralActivity"):
        act = rel.RelatedStructuralActivity; el = rel.RelatingElement
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
        conn = node_of.get(act.id())
        coords = _node_coords(conn) if conn is not None else None
        if coords is None:
            continue
        masas.append({"accion": act.Name, "nodo": conn.Name, "x": coords[0],
            "y": coords[1], "z": coords[2], "W_N": abs(float(fz)), "m_kg": abs(float(fz)) / G})
    masas.sort(key=lambda d: d["z"])
    return masas


def _global_pset(walls_ifc, name, fallback):
    out = dict(fallback)
    for w in walls_ifc:
        ps = _psets(w).get(name, {})
        if ps:
            for k in out:
                if ps.get(k) is not None:
                    out[k] = ps[k]
            for k, v in ps.items():
                out.setdefault(k, v)
            break
    return out


def parse(ifc_path):
    ifc = ifcopenshell.open(ifc_path)
    base = _load_ifc_to_model_3d()
    neutro = base.parse(ifc_path)
    surfs = neutro["superficies"]
    walls_ifc = ifc.by_type("IfcStructuralSurfaceMember")

    mat_name = surfs[0]["material"] if surfs else "C30/37"
    mp = neutro["materiales"].get(mat_name, {})
    E = float(mp.get("E") or 32.84e9); nu = float(mp.get("nu") or 0.2)
    Gsh = float(mp.get("G") or E / (2.0 * (1.0 + nu)))

    ec8 = _global_pset(walls_ifc, "Pset_Estructurando_Sismo", FALLBACK_EC8)
    nuc = _global_pset(walls_ifc, "Pset_Estructurando_Nucleo", FALLBACK_NUC)

    pset_by_name = {w.Name: _psets(w) for w in walls_ifc}
    pantallas = []
    for s in surfs:
        cs = s["esquinas_coords"]
        xs = [c[0] for c in cs]; ys = [c[1] for c in cs]; zs = [c[2] for c in cs]
        dx = max(xs) - min(xs); dy = max(ys) - min(ys); dz = max(zs) - min(zs)
        if dz < 1e-6:
            continue
        if dx >= dy:
            Lw = dx; resiste = "X"; xc = (min(xs) + max(xs)) / 2.0; yc = ys[0]
        else:
            Lw = dy; resiste = "Y"; yc = (min(ys) + max(ys)) / 2.0; xc = xs[0]
        tw = float(s["espesor"]); Hw = dz
        nm = s["nombre"]
        psp = pset_by_name.get(nm, {}).get("Pset_Estructurando_Pantalla", {})
        rol = psp.get("Rol", "pantalla"); par = psp.get("ParAcoplado", "")
        if psp.get("ResisteDir"):
            resiste = psp["ResisteDir"]
        I = tw * Lw ** 3 / 12.0; A = tw * Lw; A_v = A * 5.0 / 6.0
        pantallas.append({"nombre": nm, "rol": rol, "resiste": resiste,
            "Lw_m": Lw, "tw_m": tw, "H_m": Hw, "xc_m": xc, "yc_m": yc,
            "I_m4": I, "A_m2": A, "A_v_m2": A_v, "par_acoplado": par})

    masas = _read_masses(ifc)
    z_plant = [m["z"] for m in masas]
    z_full = [0.0] + z_plant
    CMx = nuc.get("CM_x_m") or (sum(m["x"] for m in masas) / len(masas) if masas else 0.0)
    CMy = nuc.get("CM_y_m") or (sum(m["y"] for m in masas) / len(masas) if masas else 0.0)
    nuc["CM_x_m"] = CMx; nuc["CM_y_m"] = CMy

    model = {
        "caso": "15-nucleo-sismico-ec8",
        "unidades": {"longitud": "m", "fuerza": "N", "masa": "kg"},
        "material": {"nombre": mat_name, "E_Pa": E, "G_Pa": Gsh, "nu": nu,
            "fck_Pa": mp.get("fck"), "fctm_Pa": mp.get("fctm"), "rho": mp.get("rho")},
        "pantallas": pantallas, "n_pantallas": len(pantallas),
        "diafragma": {"CM_x_m": CMx, "CM_y_m": CMy,
            "Edificio_Lx_m": float(nuc["Edificio_Lx_m"]), "Edificio_Ly_m": float(nuc["Edificio_Ly_m"]),
            "z_nodes_m": z_full, "z_plantas_m": z_plant, "n_plantas": len(z_plant)},
        "masas": {"por_planta_kg": [m["m_kg"] for m in masas],
            "por_planta_W_kN": [m["W_N"] / 1e3 for m in masas], "z_m": z_plant,
            "M_total_kg": sum(m["m_kg"] for m in masas),
            "W_total_kN": sum(m["W_N"] for m in masas) / 1e3, "detalle": masas},
        "dinteles": {"b_m": float(nuc["Dintel_b_m"]), "h_m": float(nuc["Dintel_h_m"]),
            "ln_m": float(nuc["Dintel_ln_m"]), "por_planta": int(nuc.get("Dinteles_por_planta", 1)),
            "abertura_puerta_m": float(nuc["AberturaPuerta_m"]),
            "direccion_acoplamiento": nuc["DireccionAcoplamiento"]},
        "ec8": ec8, "nucleo": nuc,
        "notas": [
            "Diafragma rigido, 3 GdL/planta (ux, uy, theta); cada pantalla aporta su "
            "rigidez de voladizo (flexion + cortante Timoshenko) en su direccion y "
            "posicion en planta (reutiliza ec8.stick_lateral_stiffness).",
            "Seccion abierta en U -> CR != CM -> torsion; + torsion accidental "
            "+-0.05*L (EC8 §4.3.2). Machones de alma ACOPLADOS por dintel.",
            "q=3.6 (muros acoplados) [confirmar AN] NCSE-02 / EC8 NDP Espana."],
    }
    return model


if __name__ == "__main__":
    ifc_path = sys.argv[1] if len(sys.argv) > 1 else "caso-15.ifc"
    out = sys.argv[2] if len(sys.argv) > 2 else "modelo_neutro.json"
    m = parse(ifc_path)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    json.dump(m, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("Modelo neutro (nucleo, 3 GdL/planta) escrito en:", out)
    print("  pantallas=%d plantas=%d M_total=%.1f t W_total=%.0f kN" % (
        m["n_pantallas"], m["diafragma"]["n_plantas"],
        m["masas"]["M_total_kg"] / 1e3, m["masas"]["W_total_kN"]))
    for p in m["pantallas"]:
        print("   %-9s rol=%-9s resiste=%s Lw=%.2f xc=%.2f yc=%.2f I=%.3f" % (
            p["nombre"], p["rol"], p["resiste"], p["Lw_m"], p["xc_m"], p["yc_m"], p["I_m4"]))
    print("  CM=(%.2f,%.2f) edificio %.0fx%.0f" % (m["diafragma"]["CM_x_m"],
        m["diafragma"]["CM_y_m"], m["diafragma"]["Edificio_Lx_m"], m["diafragma"]["Edificio_Ly_m"]))
