"""
SELECCION DE FIRME -- 6.1-IC. Plugin obras-lineales. PT 5.2 (Ola 5).

Encadena bases_firme (categoria de trafico + explanada) con el catalogo_6_1_IC
(seccion) y RELLENA los ganchos del MODELO NEUTRO LINEAL que el PT 5.1 dejo
previstos (= None):

  modelo["firme"]         = {categoria_trafico, explanada, codigo_seccion,
                             tipo_firme, paquete[], espesor_total_cm, imdp, ev2}
  modelo["secciones_tipo"] = {plataforma: anchos de calzada/arcenes} (basica)

Solo AÑADE claves; no redefine las existentes (alineacion/georref/...): modelo
hermano retrocompatible (contrato C1 §4bis). El dato del IFC prevalece sobre el
valor por defecto. Predimensionado; revisar/firmar por tecnico competente (ICCP).
"""
import copy

import bases_firme as B
import catalogo_6_1_IC as CAT

# Plataforma tipo por defecto (m) por categoria de trafico -- NDP [confirmar AN].
_PLATAFORMA_DEF = {
    "T00": {"calzada_m": 7.0, "arcen_ext_m": 2.5, "arcen_int_m": 1.0, "n_carriles": 2},
    "T0": {"calzada_m": 7.0, "arcen_ext_m": 2.5, "arcen_int_m": 1.0, "n_carriles": 2},
    "T1": {"calzada_m": 7.0, "arcen_ext_m": 2.5, "arcen_int_m": 1.0, "n_carriles": 2},
    "T2": {"calzada_m": 7.0, "arcen_ext_m": 1.5, "arcen_int_m": 0.5, "n_carriles": 2},
    "T31": {"calzada_m": 7.0, "arcen_ext_m": 1.5, "arcen_int_m": 0.5, "n_carriles": 2},
    "T32": {"calzada_m": 6.0, "arcen_ext_m": 1.0, "arcen_int_m": 0.5, "n_carriles": 2},
    "T41": {"calzada_m": 6.0, "arcen_ext_m": 0.5, "arcen_int_m": 0.0, "n_carriles": 2},
    "T42": {"calzada_m": 5.0, "arcen_ext_m": 0.5, "arcen_int_m": 0.0, "n_carriles": 2},
}


def _peralte_max(modelo):
    """Peralte maximo (%) presente en la alineacion (informativo en la seccion tipo)."""
    peraltes = []
    for s in (modelo.get("alineacion", {}).get("peralte", []) or []):
        for k in ("peralte_ini_pct", "peralte_fin_pct"):
            if s.get(k) is not None:
                peraltes.append(abs(float(s[k])))
    return max(peraltes) if peraltes else None


def seleccionar(modelo, imdp=None, imd_total=None, pct_pesados=None,
                ev2_mpa=None, cbr=None, calzada_unica=False, factor_carril=1.0,
                plataforma=None, in_place=False):
    """Calcula la seccion y rellena los ganchos firme/secciones_tipo del modelo.
    Devuelve (modelo_actualizado, resultado)."""
    m = modelo if in_place else copy.deepcopy(modelo)

    bas = B.bases(imdp=imdp, imd_total=imd_total, pct_pesados=pct_pesados,
                  ev2_mpa=ev2_mpa, cbr=cbr, calzada_unica=calzada_unica,
                  factor_carril=factor_carril)
    cat_t, cat_e = bas["categoria_trafico"], bas["categoria_explanada"]

    sec = CAT.seccion(cat_t, cat_e)
    if "error" in sec:
        resultado = {"veredicto": "NO CUMPLE", "bases": bas, "seccion": sec,
                     "motivo": sec["error"]}
        return m, resultado

    firme = {
        "categoria_trafico": cat_t,
        "explanada": cat_e,
        "codigo_seccion": sec["codigo"],
        "tipo_firme": sec.get("tipo_firme"),
        "paquete": sec["paquete"],
        "espesor_total_cm": sec["espesor_total_cm"],
        "imdp_veh_pesados_dia": bas["imdp_veh_pesados_dia"],
        "ev2_mpa": bas["ev2_mpa"],
        "norma": "6.1-IC",
        "nota": "Predimensionado 6.1-IC (catalogo). NDP [confirmar AN].",
    }
    m["firme"] = firme

    # seccion tipo basica (no redefine nada; solo rellena el gancho previsto)
    plat = plataforma or _PLATAFORMA_DEF.get(cat_t, _PLATAFORMA_DEF["T2"])
    m["secciones_tipo"] = {
        "plataforma": dict(plat),
        "peralte_max_pct": _peralte_max(m),
        "nota": "Seccion tipo basica (anchos por defecto). NDP [confirmar AN].",
    }

    resultado = {"veredicto": "CUMPLE", "bases": bas, "seccion": sec, "firme": firme,
                 "secciones_tipo": m["secciones_tipo"]}
    return m, resultado
