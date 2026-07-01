"""
Integracion del CASO SISMICO EC8 en el orquestador de edificio (PT 1.5, obj. 2).

Aplica el sismo a un edificio completo reutilizando el modulo sismico/:
  1. DERIVA las masas de planta del modelo (masas sismicas explicitas del IFC
     -IfcStructuralPointAction- o, en su defecto, de las cargas gravitatorias
     G + psi2*Q por planta).
  2. MONTA el modelo lateral (pantallas / nucleo) con diafragma rigido (nucleo.py)
     -reutiliza el ensamblaje 3 GdL/planta-.
  3. DISTRIBUYE el cortante sismico al sistema de estabilizacion (directo +
     torsion + torsion accidental) y verifica DERIVAS globales.
  4. COMBINACION SISMICA EC0 §6.4.3.4:  Ed = E "+" Sum Gk "+" Sum psi2,i*Qki.

Uso: python3 sismico/edificio_sismo.py <carpeta_proyecto> <ifc>
"""
import sys, os, json, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import solver_nucleo, run_all_nucleo
G = 9.81
PSI2 = 0.3   # categoria de uso A/B (residencial/oficinas) [confirmar AN EC0 tabla A1.1]


def _load_generic():
    path = os.path.abspath(os.path.join(HERE, "..", "laminas", "ifc_to_model_3d.py"))
    sys.path.insert(0, os.path.dirname(path)); sys.path.insert(0, os.path.join(HERE, "..", "barras"))
    spec = importlib.util.spec_from_file_location("ifc_to_model_3d_edif", path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def derivar_masas_desde_gravedad(ifc_path, z_plantas, psi2=PSI2):
    """Deriva W_planta = Sum(G) + psi2*Sum(Q) de las cargas de superficie del
    modelo generico, agrupadas por planta (cota z). Best-effort: requiere que el
    IFC tenga cargas de forjado G/Q. Devuelve lista de W (N) por planta."""
    base = _load_generic(); mn = base.parse(ifc_path)
    W = [0.0] * len(z_plantas)
    def idx_planta(zc):
        best = min(range(len(z_plantas)), key=lambda i: abs(z_plantas[i] - zc))
        return best
    for s in mn.get("superficies", []):
        cs = s["esquinas_coords"]; zs = [c[2] for c in cs]
        if (max(zs) - min(zs)) > 1e-6:
            continue  # solo forjados horizontales
        zc = sum(zs) / len(zs)
        xs = [c[0] for c in cs]; ys = [c[1] for c in cs]
        area = (max(xs) - min(xs)) * (max(ys) - min(ys))
        gq = {"G": 0.0, "Q": 0.0}
        for c in s.get("cargas", []):
            caso = (c.get("caso") or "G")[0].upper()
            gq["Q" if caso == "Q" else "G"] += abs(c.get("qz", 0.0))
        W[idx_planta(zc)] += (gq["G"] + psi2 * gq["Q"]) * area
    return W


def run(proj, ifc):
    os.makedirs(proj, exist_ok=True)
    print("=" * 68)
    print("CASO SISMICO EC8 INTEGRADO EN EL EDIFICIO (PT 1.5, objetivo 2)")
    print("=" * 68)
    model = solver_nucleo.parse(ifc)
    n_walls = model["n_pantallas"]
    masas = model["masas"]["por_planta_kg"]
    origen = "IfcStructuralPointAction (masas sismicas explicitas)"
    if not masas or sum(masas) == 0:
        z = model["diafragma"]["z_plantas_m"]
        W = derivar_masas_desde_gravedad(ifc, z)
        model["masas"]["por_planta_kg"] = [w / G for w in W]
        model["masas"]["por_planta_W_kN"] = [w / 1e3 for w in W]
        model["masas"]["W_total_kN"] = sum(W) / 1e3
        model["masas"]["M_total_kg"] = sum(W) / G
        masas = model["masas"]["por_planta_kg"]
        origen = "derivadas de la gravedad G + psi2*Q por planta (psi2=%.1f)" % PSI2
    print("[1] Sistema de estabilizacion: %d pantallas verticales de hormigon" % n_walls)
    print("[2] Masas de planta (%s): W_total=%.0f kN" % (origen, model["masas"]["W_total_kN"]))

    print("[3] Modelo lateral (diafragma rigido) + reparto de cortante + derivas...")
    res = run_all_nucleo.analizar(model, proj, do_plots=False, out_json="verificacion_sismo_edificio.json")

    # Combinacion sismica EC0 §6.4.3.4
    W_t = model["masas"]["W_total_kN"]
    comb = {
        "norma": "EN 1990 §6.4.3.4",
        "expresion": "Ed = E '+' Sum Gk '+' Sum psi2,i*Qki",
        "peso_sismico_W_kN": W_t,
        "psi2_usado": PSI2,
        "accion_sismica_Fb_X_kN": res["fuerzas_laterales_X"]["Fb_kN"],
        "accion_sismica_Fb_Y_kN": res["fuerzas_laterales_Y"]["Fb_kN"],
        "nota": ("Los subsistemas gravitatorios (porticos, forjados, cimentacion) ya "
                 "se verifican para Sum Gk + Sum psi0/psi2*Qk en run_all_edificio; aqui "
                 "se anade la accion sismica E y se verifica el sistema de estabilizacion "
                 "lateral y las derivas globales. gamma_G=gamma_Q=1.0 en sismica."),
    }
    res["combinacion_sismica_EC0"] = comb
    res["origen_masas"] = origen
    json.dump(res, open(os.path.join(proj, "verificacion_sismo_edificio.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    cr = res["criterios_aceptacion"]
    print("[4] Combinacion sismica EC0 §6.4.3.4: W=%.0f kN, Fb_X=%.0f Fb_Y=%.0f kN" % (
        W_t, comb["accion_sismica_Fb_X_kN"], comb["accion_sismica_Fb_Y_kN"]))
    print("    T1x=%.3f T1y=%.3f s | deriva_max=%.3f%% | equilibrio X/Y=%.3f/%.3f%% | VEREDICTO %s (aprov %.2f)" % (
        cr["T1x_s"], cr["T1y_s"], cr["deriva_max_rel_pct"], cr["equilibrio_X_error_pct"],
        cr["equilibrio_Y_error_pct"], res["verificacion"]["veredicto"], cr["aprov_max"]))
    return res


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else "proyecto-edificio-sismo"
    ifc = sys.argv[2] if len(sys.argv) > 2 else os.path.join(proj, "edificio.ifc")
    run(proj, ifc)
