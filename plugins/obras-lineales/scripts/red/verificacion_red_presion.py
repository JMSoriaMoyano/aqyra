# -----------------------------------------------------------------------------
# PROCEDENCIA (PT 6.3, Ola 6): COPIA del arnes de verificacion del solver
#   hidraulico a presion de `instalaciones` (`instalaciones/scripts/red/
#   verificacion_red.py`, PT 4.3/4.4), renombrada a `verificacion_red_presion.py`
#   para el vertical de ABASTECIMIENTO de `obras-lineales`. El cuerpo es IDENTICO;
#   solo se anade este banner. Gemelo a presion de `verificacion_red_lineal.py`
#   (lamina libre, saneamiento).
# -----------------------------------------------------------------------------
"""
ARNES DE VERIFICACION DEL SOLVER HIDRAULICO (analogo al cierre de equilibrio
estructural). Disciplina `instalaciones`, PT 4.3/4.4 (Ola 4).

Sobre el resultado de red/solver_presion.resolver(modelo) comprueba:
  1. BALANCE DE CAUDALES en cada nudo ~= 0 (continuidad): con el caudal CON SIGNO
     por tramo (clave `caudal_signed_l_s`, sentido ni->nj positivo), el caudal neto
     que entra a cada nudo = su demanda (terminal), 0 (union) o -total (fuente).
     Reporta el residuo nodal maximo (%). Vale para ARBOL y para MALLA.
  2. CIERRE DE PERDIDA POR LAZO (solo malla): suma de perdidas de carga con signo
     alrededor de cada lazo ~= 0 (2.a ley de Kirchhoff hidraulica). Se toma del
     bloque `hardy_cross.residuos_lazo_kPa` del solver.
  3. PRESIONES: todo terminal ACTIVO con presion disponible >= presion minima, y
     presion de fuente disponible >= requerida. VELOCIDADES admisibles (<= v_max).
Veredicto CUMPLE solo si no hay errores. Es predimensionado/asistencia; revisar y
firmar por tecnico competente.
"""
import json

TOL_BALANCE_PCT = 0.1    # residuo de continuidad admisible (%)
TOL_LAZO_KPA = 0.01      # residuo de cierre por lazo admisible (kPa)


def verificar(modelo, resultado):
    errores, avisos, info = [], [], []

    tramos = resultado.get("tramos", {})
    nodos = resultado.get("nodos", {})

    # demanda por nodo (terminales activos)
    dem = {}
    for t in resultado.get("terminales", []):
        if t.get("activo") and t.get("caudal_l_s"):
            dem[t.get("nodo")] = dem.get(t.get("nodo"), 0.0) + float(t["caudal_l_s"])
    q_total_dem = sum(dem.values())

    # --- 1) BALANCE DE CAUDALES por nudo con el caudal CON SIGNO -----------------
    # net_in(nm) = Σ [ +q_s si nj==nm ; -q_s si ni==nm ]  (q_s positivo = ni->nj)
    tiene_signo = all(("caudal_signed_l_s" in to) for to in tramos.values()) if tramos else False
    fuentes = [nm for nm, n in nodos.items() if n.get("tipo") == "fuente"]
    res_nudo_max = 0.0
    if tiene_signo:
        net_in = {nm: 0.0 for nm in nodos}
        for tid, to in tramos.items():
            qs = float(to.get("caudal_signed_l_s") or 0.0)
            ni, nj = to.get("ni"), to.get("nj")
            if ni in net_in:
                net_in[ni] -= qs
            if nj in net_in:
                net_in[nj] += qs
        # base de normalizacion: el caudal total de la red
        base = q_total_dem if q_total_dem else 1.0
        for nm, n in nodos.items():
            tipo = n.get("tipo")
            if tipo == "fuente":
                objetivo = -q_total_dem   # la fuente inyecta todo el caudal
            elif tipo == "terminal":
                objetivo = dem.get(nm, 0.0)   # el terminal consume su demanda
            else:
                objetivo = 0.0                # nudo de union: entra = sale
            residuo = abs(net_in.get(nm, 0.0) - objetivo)
            res_nudo_max = max(res_nudo_max, 100.0 * residuo / base)
        info.append("Residuo maximo de continuidad por nudo: %.4f %% (con caudal con signo)"
                    % res_nudo_max)
    else:
        # respaldo (resultados antiguos sin signo): balance global cabecera vs demanda
        q_cabecera = 0.0
        for tid, to in tramos.items():
            if to.get("ni") in fuentes or to.get("nj") in fuentes:
                q_cabecera += float(to.get("caudal_l_s") or 0.0)
        residuo = abs(q_cabecera - q_total_dem)
        res_nudo_max = (100.0 * residuo / q_total_dem) if q_total_dem else 0.0
        info.append("Balance global (sin signo): cabecera %.4f vs demanda %.4f l/s "
                    "(residuo %.4f %%)" % (q_cabecera, q_total_dem, res_nudo_max))

    # balance global de cabecera (informativo, vale en arbol y malla)
    q_cabecera = 0.0
    for tid, to in tramos.items():
        if to.get("ni") in fuentes or to.get("nj") in fuentes:
            q_cabecera += abs(float(to.get("caudal_signed_l_s")
                                    if to.get("caudal_signed_l_s") is not None
                                    else (to.get("caudal_l_s") or 0.0)))
    res_global_pct = (100.0 * abs(q_cabecera - q_total_dem) / q_total_dem) if q_total_dem else 0.0
    info.append("Balance global de caudales: cabecera %.4f l/s vs demanda %.4f l/s "
                "(residuo %.4f %%)" % (q_cabecera, q_total_dem, res_global_pct))
    if res_nudo_max > TOL_BALANCE_PCT:
        errores.append("Balance de caudales NO cierra: residuo nodal %.4f %% (> %.2f %%)."
                       % (res_nudo_max, TOL_BALANCE_PCT))

    # --- 2) CIERRE DE PERDIDA POR LAZO (malla) ----------------------------------
    lazo_max = 0.0
    hc = resultado.get("hardy_cross")
    if hc:
        residuos = hc.get("residuos_lazo_kPa") or []
        lazo_max = max((abs(r) for r in residuos), default=0.0)
        info.append("Cierre de perdida por lazo: %d lazo(s), residuo max %.6f kPa "
                    "(Hardy-Cross, %s)" % (hc.get("n_lazos", 0), lazo_max,
                                           "converge" if hc.get("convergio") else "NO converge"))
        if lazo_max > TOL_LAZO_KPA:
            errores.append("Cierre de lazo NO nulo: %.4f kPa (> %.3f kPa)." % (lazo_max, TOL_LAZO_KPA))
        if not hc.get("convergio"):
            errores.append("Hardy-Cross no convergio.")
    else:
        info.append("Red en arbol (sin lazos): no aplica cierre por lazo.")

    # --- 3) PRESIONES Y VELOCIDADES (del solver) --------------------------------
    if resultado.get("errores"):
        for e in resultado["errores"]:
            errores.append(e)
    else:
        info.append("Presiones y velocidades dentro de limites (segun solver).")
    info.append("Presion fuente: disponible %s / requerida %s kPa (margen %s)"
                % (resultado.get("presion_fuente_disponible_kPa"),
                   resultado.get("presion_fuente_requerida_kPa"),
                   resultado.get("margen_fuente_kPa")))

    veredicto = "CUMPLE" if not errores else "NO CUMPLE"
    return {
        "veredicto": veredicto,
        "balance_global_pct": round(res_global_pct, 6),
        "residuo_nudo_max_pct": round(res_nudo_max, 6),
        "cierre_lazo_max_kPa": round(lazo_max, 6),
        "presion_fuente_requerida_kPa": resultado.get("presion_fuente_requerida_kPa"),
        "presion_fuente_disponible_kPa": resultado.get("presion_fuente_disponible_kPa"),
        "velocidad_pico_m_s": resultado.get("velocidad_pico_m_s"),
        "errores": errores, "avisos": avisos, "info": info,
    }


def main(modelo_path, resultado_path, out=None):
    with open(modelo_path, encoding="utf-8") as fh:
        modelo = json.load(fh)
    with open(resultado_path, encoding="utf-8") as fh:
        resultado = json.load(fh)
    res = verificar(modelo, resultado)
    print("=" * 64)
    print("VERIFICACION DE RED HIDRAULICA A PRESION (ABASTECIMIENTO)")
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
