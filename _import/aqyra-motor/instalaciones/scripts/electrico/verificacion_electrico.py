"""
ARNES DE VERIFICACION DEL SOLVER ELECTRICO (analogo al de la red hidraulica y al
cierre de equilibrio estructural). Disciplina `instalaciones`, PT 4.5 (Ola 4).

Sobre el resultado de electrico/solver_electrico.resolver(modelo) comprueba:
  1. BALANCE DE POTENCIAS: la potencia que entra por la(s) cabecera(s) (tramos
     conectados a la fuente) == suma de la potencia de calculo de los terminales
     activos (continuidad de potencia, analogo al balance de caudales). Residuo (%).
  2. CAIDA DE TENSION acumulada <= limite por terminal (3 % alumbrado / 5 % fuerza,
     ITC-BT-19). Se toma de la salida del solver.
  3. INTENSIDAD por tramo <= admisible del conductor (ITC-BT-19, segun aislamiento y
     nº de conductores cargados). Se toma de la salida del solver.
Veredicto CUMPLE solo si no hay errores. Predimensionado/asistencia; revisar y
firmar por tecnico competente.
"""
import json

TOL_BALANCE_PCT = 0.1    # residuo de balance de potencias admisible (%)


def verificar(modelo, resultado):
    errores, avisos, info = [], [], []

    tramos = resultado.get("tramos", {})
    nodos = resultado.get("nodos", {})

    # --- 1) BALANCE DE POTENCIAS ------------------------------------------------
    p_dem = 0.0
    for t in resultado.get("terminales", []):
        if t.get("activo") and t.get("potencia_W"):
            p_dem += float(t["potencia_W"])
    fuentes = [nm for nm, n in nodos.items() if n.get("tipo") == "fuente"]
    p_cab = 0.0
    for tid, to in tramos.items():
        if to.get("potencia_W") is None:
            continue
        if to.get("ni") in fuentes or to.get("nj") in fuentes:
            p_cab += float(to.get("potencia_W") or 0.0)
    base = p_dem if p_dem else 1.0
    res_pct = 100.0 * abs(p_cab - p_dem) / base
    info.append("Balance de potencias: cabecera %.1f W vs demanda %.1f W (residuo %.4f %%)"
                % (p_cab, p_dem, res_pct))
    if res_pct > TOL_BALANCE_PCT:
        errores.append("Balance de potencias NO cierra: residuo %.4f %% (> %.2f %%)."
                       % (res_pct, TOL_BALANCE_PCT))

    # --- 2) CAIDA DE TENSION (del solver) --------------------------------------
    caida_max = 0.0
    for to in resultado.get("terminales", []):
        if to.get("activo") and to.get("caida_acum_pct") is not None:
            caida_max = max(caida_max, to["caida_acum_pct"])
            if to.get("cumple") is False:
                errores.append("Terminal %s: caida acumulada %.2f %% > limite %.2f %%."
                               % (to["id"], to["caida_acum_pct"], to["du_max_pct"]))
    info.append("Caida de tension maxima: %.3f %% (gobernante %s)"
                % (caida_max, resultado.get("terminal_gobernante")))

    # --- 3) INTENSIDAD ADMISIBLE (del solver) ----------------------------------
    i_problemas = 0
    for tid, to in tramos.items():
        if to.get("intensidad_A") is None:
            continue
        i_adm = to.get("I_admisible_A") or 0.0
        if i_adm and to["intensidad_A"] > i_adm:
            i_problemas += 1
            errores.append("Tramo %s: I=%.1f A > admisible %.1f A (S=%s mm2)."
                           % (tid, to["intensidad_A"], i_adm, to.get("seccion_mm2")))
    if not i_problemas:
        info.append("Intensidades dentro del admisible en todos los tramos.")

    # arrastre de errores/avisos del solver
    for e in resultado.get("errores", []):
        if e not in errores:
            errores.append(e)
    for w in resultado.get("avisos", []):
        avisos.append(w)

    veredicto = "CUMPLE" if not errores else "NO CUMPLE"
    return {
        "veredicto": veredicto,
        "balance_potencias_pct": round(res_pct, 6),
        "potencia_cabecera_W": round(p_cab, 2),
        "potencia_demanda_W": round(p_dem, 2),
        "caida_tension_max_pct": round(caida_max, 4),
        "terminal_gobernante": resultado.get("terminal_gobernante"),
        "errores": errores, "avisos": avisos, "info": info,
    }


def main(modelo_path, resultado_path, out=None):
    with open(modelo_path, encoding="utf-8") as fh:
        modelo = json.load(fh)
    with open(resultado_path, encoding="utf-8") as fh:
        resultado = json.load(fh)
    res = verificar(modelo, resultado)
    print("=" * 64)
    print("VERIFICACION DE RED ELECTRICA (REBT)")
    print("=" * 64)
    for i in res["info"]:
        print("  i ", i)
    for w in res["avisos"]:
        print("  ! ", w)
    for e in res["errores"]:
        print("  X ", e)
    print("\nVEREDICTO:", res["veredicto"])
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=2, ensure_ascii=False)
        print("Verificacion escrita en", out)
    return 0 if res["veredicto"] == "CUMPLE" else 1


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None))
