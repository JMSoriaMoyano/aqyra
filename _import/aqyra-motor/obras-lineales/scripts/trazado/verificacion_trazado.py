"""
VERIFICACION DE TRAZADO (arnes/veredicto) -- 3.1-IC. Plugin obras-lineales. PT 5.2.

Capa de comprobacion analoga al arnes de equilibrio de estructuras o al balance de
red de instalaciones: toma el resultado de comprobacion_trazado.comprobar() y emite
un RESUMEN verificable (recuento de comprobaciones, las que NO cumplen con su
propuesta) y un veredicto reproducible. No recalcula geometria.

Uso:  resumen(resultado_comprobacion) -> dict ;  informe(resultado) -> str
"""


def resumen(res):
    """Recuento agregado y veredicto a partir del dict de comprobar()."""
    comprob = res.get("comprobaciones", [])
    n = len(comprob)
    n_ok = sum(1 for r in comprob if r["cumple"])
    n_no = n - n_ok
    return {
        "veredicto": "CUMPLE" if n_no == 0 else "NO CUMPLE",
        "n_comprobaciones": n,
        "n_cumple": n_ok,
        "n_no_cumple": n_no,
        "n_avisos": len(res.get("avisos", [])),
    }


def informe(res):
    """Informe de texto del resultado de comprobacion_trazado.comprobar()."""
    s = resumen(res)
    u = res.get("umbrales_3_1_IC", {})
    out = []
    out.append("=" * 68)
    out.append("VERIFICACION DE TRAZADO (3.1-IC) -- eje: %s | Vp=%.0f km/h"
               % (res.get("eje"), res.get("vp_kmh", 0)))
    out.append("=" * 68)
    out.append("Umbrales 3.1-IC: Rmin=%s m | imax=%s%% | Dp=%s m | Kv_conv>=%s | Kv_conc>=%s"
               % (u.get("radio_min_m"), u.get("pendiente_max_pct"),
                  u.get("distancia_parada_m"), u.get("kv_min_convexo_m"),
                  u.get("kv_min_concavo_m")))
    out.append("-" * 68)
    for r in res.get("comprobaciones", []):
        marca = "OK " if r["cumple"] else "X  "
        out.append("  %s %-42s %s=%s (lim %s %s)"
                   % (marca, r["elemento"], r["magnitud"], r["valor"],
                      r["limite"], r["unidad"]))
        if not r["cumple"] and r.get("propuesta"):
            out.append("       -> %s" % r["propuesta"])
    for a in res.get("avisos", []):
        out.append("  !  %s" % a)
    out.append("-" * 68)
    out.append("RESUMEN: %d comprobaciones | %d cumplen | %d no cumplen | %d avisos"
               % (s["n_comprobaciones"], s["n_cumple"], s["n_no_cumple"], s["n_avisos"]))
    out.append("VEREDICTO: %s" % s["veredicto"])
    return "\n".join(out)
