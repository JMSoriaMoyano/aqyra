"""
ARNES DE VERIFICACION DEL SOLVER DE MANNING DE RED (lamina libre). Disciplina
`obras-lineales`, PT 6.2 (Ola 6). Analogo a `instalaciones/red/verificacion_red.py`
(balance nodal con signo + cierre por lazo), adaptado a SANEAMIENTO por gravedad.

Sobre el resultado de red/solver_lamina_libre.resolver(modelo) comprueba:
  1. BALANCE DE CAUDALES en cada nudo ~= 0 (continuidad), con el caudal CON SIGNO
     por tramo (clave `caudal_signed_l_s`, sentido ni->nj positivo). INVERTIDO
     respecto a la red a presion: el TERMINAL (acometida) INYECTA su caudal y el
     VERTIDO (outfall) RECOGE el total. Reporta el residuo nodal maximo (%). Vale
     para ARBOL y para MALLA.
  2. CIERRE DE PERDIDA POR LAZO (solo malla): suma de perdidas de friccion h_f con
     signo alrededor de cada lazo ~= 0 (del bloque `hardy_cross.residuos_lazo_m`).
  3. COMPROBACIONES POR TRAMO (del solver): grado de llenado <= maximo, velocidad
     en banda autolimpieza<->no erosion, pendiente > 0, DN minimo, sin sobrecarga.
Veredicto CUMPLE solo si no hay errores. Predimensionado/asistencia; revisar y
firmar por tecnico competente (ICCP).
"""
import json

TOL_BALANCE_PCT = 0.1    # residuo de continuidad admisible (%)
TOL_LAZO_M = 0.001       # residuo de cierre por lazo admisible (m)


def verificar(modelo, resultado):
    errores, avisos, info = [], [], []

    tramos = resultado.get("tramos", {})
    nodos = resultado.get("nodos", {})

    # demanda por nodo (terminales activos = acometidas que aportan)
    dem = {}
    for t in resultado.get("terminales", []):
        if t.get("activo") and t.get("caudal_l_s"):
            dem[t.get("nodo")] = dem.get(t.get("nodo"), 0.0) + float(t["caudal_l_s"])
    q_total_dem = sum(dem.values())

    # --- 1) BALANCE DE CAUDALES por nudo con el caudal CON SIGNO (invertido) -----
    tiene_signo = all(("caudal_signed_l_s" in to) for to in tramos.values()) if tramos else False
    vertidos = [nm for nm, n in nodos.items() if n.get("tipo") == "vertido"]
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
        base = q_total_dem if q_total_dem else 1.0
        for nm, n in nodos.items():
            tipo = n.get("tipo")
            if tipo == "vertido":
                objetivo = q_total_dem        # el vertido recoge TODO el caudal
            elif tipo == "terminal":
                objetivo = -dem.get(nm, 0.0)   # la acometida INYECTA su demanda
            else:
                objetivo = 0.0                 # nudo de union/pozo: entra = sale
            residuo = abs(net_in.get(nm, 0.0) - objetivo)
            res_nudo_max = max(res_nudo_max, 100.0 * residuo / base)
        info.append("Residuo maximo de continuidad por nudo: %.4f %% (caudal con "
                    "signo, vertido recoge el total)" % res_nudo_max)
    else:
        avisos.append("Resultado sin caudal con signo: no se puede comprobar el "
                      "balance nodal.")

    if res_nudo_max > TOL_BALANCE_PCT:
        errores.append("Balance de caudales NO cierra: residuo nodal %.4f %% (> %.2f %%)."
                       % (res_nudo_max, TOL_BALANCE_PCT))

    # --- 2) CIERRE DE PERDIDA POR LAZO (malla) ----------------------------------
    lazo_max = 0.0
    hc = resultado.get("hardy_cross")
    if hc:
        residuos = hc.get("residuos_lazo_m") or []
        lazo_max = max((abs(r) for r in residuos), default=0.0)
        info.append("Cierre de perdida por lazo: %d lazo(s), residuo max %.6g m "
                    "(Hardy-Cross lamina libre, %s)"
                    % (hc.get("n_lazos", 0), lazo_max,
                       "converge" if hc.get("convergio") else "NO converge"))
        if lazo_max > TOL_LAZO_M:
            errores.append("Cierre de lazo NO nulo: %.6g m (> %.4g m)." % (lazo_max, TOL_LAZO_M))
        if not hc.get("convergio"):
            errores.append("Hardy-Cross (lamina libre) no convergio.")
    else:
        info.append("Red en arbol (sin lazos): no aplica cierre por lazo.")

    # --- 3) COMPROBACIONES POR TRAMO (del solver) -------------------------------
    n_tramo_ng = 0
    for tid, to in tramos.items():
        for e in to.get("errores_tramo", []) or []:
            errores.append("Tramo %s: %s" % (to.get("elemento", tid), e))
            n_tramo_ng += 1
    if not n_tramo_ng:
        info.append("Todos los tramos: llenado/velocidad/pendiente/DN dentro de limites.")
    info.append("Velocidad pico %s m/s | llenado pico %s %% | caudal vertido %s l/s"
                % (resultado.get("velocidad_pico_m_s"),
                   resultado.get("llenado_pico_pct"),
                   resultado.get("caudal_total_vertido_l_s")))

    # arrastra errores globales del solver no cubiertos por tramo
    for e in resultado.get("errores", []) or []:
        if e not in errores:
            errores.append(e)

    veredicto = "CUMPLE" if not errores else "NO CUMPLE"
    return {
        "veredicto": veredicto,
        "residuo_nudo_max_pct": round(res_nudo_max, 6),
        "cierre_lazo_max_m": round(lazo_max, 8),
        "caudal_total_vertido_l_s": resultado.get("caudal_total_vertido_l_s"),
        "velocidad_pico_m_s": resultado.get("velocidad_pico_m_s"),
        "llenado_pico_pct": resultado.get("llenado_pico_pct"),
        "n_tramos_no_cumple": n_tramo_ng,
        "errores": errores, "avisos": avisos, "info": info,
    }


def main(modelo_path, resultado_path, out=None):
    with open(modelo_path, encoding="utf-8") as fh:
        modelo = json.load(fh)
    with open(resultado_path, encoding="utf-8") as fh:
        resultado = json.load(fh)
    res = verificar(modelo, resultado)
    print("=" * 64)
    print("VERIFICACION DE RED DE SANEAMIENTO (lamina libre)")
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
