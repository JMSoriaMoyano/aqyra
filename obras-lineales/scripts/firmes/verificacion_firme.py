"""
VERIFICACION DE FIRME -- 6.1-IC (arnes/veredicto). Plugin obras-lineales. PT 5.2.

Comprueba la coherencia de la seccion seleccionada y el relleno del gancho `firme`
del modelo neutro: combinacion trafico x explanada permitida, espesor de mezcla
bituminosa >= minimo de la categoria, paquete no vacio y gancho escrito. Analogo
al balance de red / arnes de equilibrio. No rehace el dimensionado por fatiga.

Uso:  verificar(modelo_actualizado, resultado_seleccion) -> dict
"""
import catalogo_6_1_IC as CAT


def verificar(modelo, resultado):
    errores, info = [], []
    bas = resultado.get("bases", {})
    cat_t = bas.get("categoria_trafico")
    cat_e = bas.get("categoria_explanada")

    if resultado.get("veredicto") != "CUMPLE":
        errores.append(resultado.get("motivo", "Seleccion sin seccion valida."))
        return {"veredicto": "NO CUMPLE", "errores": errores, "info": info}

    # 1) combinacion permitida
    permitidas = CAT._PERMITIDAS.get(cat_t, [])
    if cat_e not in permitidas:
        errores.append("Combinacion %s x %s no permitida (6.1-IC)." % (cat_t, cat_e))
    else:
        info.append("Combinacion %s x %s permitida; permitidas=%s" % (cat_t, cat_e, permitidas))

    # 2) gancho firme escrito en el modelo
    firme = modelo.get("firme")
    if not firme:
        errores.append("El gancho 'firme' del modelo neutro no se ha rellenado.")
    else:
        info.append("Gancho 'firme' relleno: codigo %s, espesor total %d cm"
                    % (firme.get("codigo_seccion"), firme.get("espesor_total_cm", 0)))

    # 3) espesor de MB >= minimo de la categoria (firme flexible)
    if firme:
        mb = sum(c["espesor_cm"] for c in firme.get("paquete", []) if c.get("material") == "MB")
        mb_min = CAT._MB_POR_TRAFICO.get(cat_t)
        if mb_min is not None:
            if mb + 1e-9 < mb_min:
                errores.append("Espesor MB %d cm < minimo %d cm para %s." % (mb, mb_min, cat_t))
            else:
                info.append("Espesor MB %d cm >= minimo %d cm (%s)." % (mb, mb_min, cat_t))
        # 4) paquete no vacio / espesores positivos
        if not firme.get("paquete") or any(c["espesor_cm"] <= 0 for c in firme["paquete"]):
            errores.append("Paquete de firme vacio o con espesor no positivo.")

    # 5) seccion tipo basica
    if modelo.get("secciones_tipo"):
        info.append("Gancho 'secciones_tipo' relleno (plataforma basica).")

    veredicto = "CUMPLE" if not errores else "NO CUMPLE"
    return {"veredicto": veredicto, "categoria_trafico": cat_t,
            "categoria_explanada": cat_e, "errores": errores, "info": info}


def informe(modelo, resultado, ver):
    out = ["=" * 60, "VERIFICACION DE FIRME (6.1-IC)", "=" * 60]
    bas = resultado.get("bases", {})
    out.append("IMDp=%s veh.pesados/dia -> %s | Ev2=%s MPa -> %s"
               % (bas.get("imdp_veh_pesados_dia"), bas.get("categoria_trafico"),
                  bas.get("ev2_mpa"), bas.get("categoria_explanada")))
    firme = modelo.get("firme")
    if firme:
        capas = " + ".join("%s %dcm" % (c["material"], c["espesor_cm"]) for c in firme["paquete"])
        out.append("Seccion %s (%s): %s | total %d cm"
                   % (firme["codigo_seccion"], firme.get("tipo_firme"), capas,
                      firme["espesor_total_cm"]))
    for i in ver.get("info", []):
        out.append("  i  " + i)
    for e in ver.get("errores", []):
        out.append("  X  " + e)
    out.append("-" * 60)
    out.append("VEREDICTO: %s" % ver["veredicto"])
    return "\n".join(out)
