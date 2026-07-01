"""
VERIFICACION DE DRENAJE -- 5.2-IC (arnes/veredicto). Plugin obras-lineales. PT 6.1.

Recoge las comprobaciones por elemento (cunetas y ODT) y los caudales de calculo
(hidrologia.py) y emite el VEREDICTO global, mas el control del relleno del gancho
`drenaje` del modelo neutro lineal. Analogo a verificacion_firme / verificacion_trazado
(recuento + veredicto + informe). No rehace el calculo: lo agrega y juzga.

Uso:  verificar(modelo_actualizado, resultado) -> dict
"""


def verificar(modelo, resultado):
    errores, info = [], []
    cunetas = resultado.get("cunetas", [])
    odts = resultado.get("odt", [])
    caudales = resultado.get("caudales", [])

    if not caudales:
        errores.append("No se ha calculado ningun caudal de cuenca (hidrologia).")
    if not cunetas and not odts:
        errores.append("No hay ningun elemento de drenaje (cuneta/ODT) que comprobar.")

    n_cuneta_ko = sum(1 for c in cunetas if c.get("veredicto") != "CUMPLE")
    n_odt_ko = sum(1 for o in odts if o.get("veredicto") != "CUMPLE")

    for c in cunetas:
        if c.get("veredicto") != "CUMPLE":
            errores.append("Cuneta %s NO CUMPLE: %s"
                           % (c.get("id"), "; ".join(c.get("errores", []))))
        else:
            info.append("Cuneta %s CUMPLE (Q %.3f / cap. util %.3f m3/s)."
                        % (c.get("id"), c.get("Q_calculo_m3_s", 0.0),
                           c.get("capacidad_util_m3_s", 0.0)))
    for o in odts:
        if o.get("veredicto") != "CUMPLE":
            errores.append("ODT %s NO CUMPLE: %s"
                           % (o.get("id"), "; ".join(o.get("errores", []))))
        else:
            info.append("ODT %s CUMPLE (Q %.3f / cap. %.3f m3/s, control de %s)."
                        % (o.get("id"), o.get("Q_cuenca_m3_s", 0.0),
                           o.get("capacidad_m3_s", 0.0), o.get("control_gobernante")))

    # gancho `drenaje` relleno en el modelo
    dre = modelo.get("drenaje")
    if not dre or not (dre.get("cunetas") or dre.get("odt")):
        errores.append("El gancho 'drenaje' del modelo neutro no se ha rellenado.")
    else:
        info.append("Gancho 'drenaje' relleno: %d cuenca(s), %d cuneta(s), %d ODT."
                    % (len(dre.get("cuencas", [])), len(dre.get("cunetas", [])),
                       len(dre.get("odt", []))))

    veredicto = "CUMPLE" if not errores else "NO CUMPLE"
    return {
        "veredicto": veredicto,
        "n_cunetas": len(cunetas),
        "n_cunetas_no_cumple": n_cuneta_ko,
        "n_odt": len(odts),
        "n_odt_no_cumple": n_odt_ko,
        "errores": errores,
        "info": info,
        "norma": "5.2-IC",
    }


def informe(modelo, resultado, ver):
    out = ["=" * 62, "VERIFICACION DE DRENAJE (5.2-IC)", "=" * 62]
    for q in resultado.get("caudales", []):
        out.append("Cuenca %s: T=%s a, A=%.4f km2, tc=%.3f h, I=%.1f mm/h, C=%.3f "
                    "-> Q=%.3f m3/s"
                    % (q.get("cuenca"), q.get("periodo_retorno_anos"), q.get("area_km2"),
                       q.get("tc_h"), q.get("intensidad_mm_h"), q.get("coef_escorrentia"),
                       q.get("caudal_m3_s")))
    out.append("-" * 62)
    for i in ver.get("info", []):
        out.append("  i  " + i)
    for e in ver.get("errores", []):
        out.append("  X  " + e)
    out.append("-" * 62)
    out.append("Cunetas: %d (%d NO CUMPLE) | ODT: %d (%d NO CUMPLE)"
               % (ver["n_cunetas"], ver["n_cunetas_no_cumple"],
                  ver["n_odt"], ver["n_odt_no_cumple"]))
    out.append("VEREDICTO: %s" % ver["veredicto"])
    return "\n".join(out)
