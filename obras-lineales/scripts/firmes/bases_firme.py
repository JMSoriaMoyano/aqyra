"""
BASES DE FIRME -- Norma 6.1-IC (Secciones de firme). Plugin obras-lineales. PT 5.2.

Es el "slot" C4 de la disciplina aplicado a firmes (analogo a las bases de demanda
de instalaciones): fija las dos ENTRADAS que gobiernan la seleccion de seccion del
catalogo 6.1-IC a partir de datos de proyecto:

  1) CATEGORIA DE TRAFICO PESADO (T00..T42) -- de la IMDp (intensidad media diaria
     de vehiculos PESADOS en el carril de proyecto, en el ano de puesta en servicio).
  2) CATEGORIA DE EXPLANADA (E1/E2/E3) -- del modulo de compresibilidad Ev2 (o CBR)
     de la formacion de explanada.

El dato del proyecto (Pset del IFC) prevalece; si falta, lo inyecta el agente.
Predimensionado; revisar/firmar por tecnico competente (ICCP). NDP [confirmar AN].
"""

# --- Categoria de trafico pesado por IMDp (veh. pesados/dia, carril de proyecto)
#     6.1-IC, tabla 1.A. [confirmar AN].
_UMBRALES_TRAFICO = [
    ("T00", 4000, float("inf")),
    ("T0", 2000, 3999),
    ("T1", 800, 1999),
    ("T2", 200, 799),
    ("T31", 100, 199),
    ("T32", 50, 99),
    ("T41", 25, 49),
    ("T42", 0, 24),
]

# --- Categoria de explanada por modulo Ev2 (MPa) -- 6.1-IC, tabla. [confirmar AN].
#     E1: Ev2 >= 60 MPa ; E2: >= 120 MPa ; E3: >= 300 MPa.
_UMBRALES_EXPLANADA = [
    ("E3", 300.0),
    ("E2", 120.0),
    ("E1", 60.0),
]


def categoria_trafico_desde_imdp(imdp):
    """Categoria de trafico pesado (T00..T42) a partir de la IMDp directa."""
    imdp = float(imdp)
    for cat, lo, hi in _UMBRALES_TRAFICO:
        if lo <= imdp <= hi:
            return cat
    return "T42"


def imdp_desde_imd(imd_total, pct_pesados, n_carriles_por_sentido=1,
                   factor_carril=1.0, calzada_unica=False):
    """Estima la IMDp en el carril de proyecto a partir de la IMD total.

    imdp = imd_total * (pct_pesados/100) * reparto_por_sentido * factor_carril
      - calzada_unica=True (carretera convencional de 2 carriles, 1 por sentido):
        el reparto por sentido es 0,5 salvo factor_carril que lo corrija.
      - calzada doble: reparto 0,5 por sentido y el factor_carril concentra los
        pesados en el carril exterior (def. 1,0). [confirmar AN].
    """
    pesados = float(imd_total) * float(pct_pesados) / 100.0
    reparto = 0.5 if (calzada_unica or n_carriles_por_sentido >= 1) else 1.0
    if calzada_unica:
        # en calzada unica los dos sentidos comparten carriles: 50% por sentido
        return pesados * 0.5 * float(factor_carril)
    return pesados * reparto * float(factor_carril)


def categoria_explanada_desde_ev2(ev2_mpa):
    """Categoria de explanada (E1/E2/E3) a partir del modulo Ev2 (MPa)."""
    ev2 = float(ev2_mpa)
    for cat, lim in _UMBRALES_EXPLANADA:
        if ev2 >= lim:
            return cat
    return None  # < 60 MPa: explanada insuficiente, requiere mejora (E1 minimo)


def categoria_explanada_desde_cbr(cbr):
    """Orientacion de categoria de explanada a partir del CBR del suelo (muy
    aproximado; la categoria real depende de la FORMACION de explanada, 6.1-IC
    fig. 1). Solo como respaldo si no hay Ev2. [confirmar AN]."""
    cbr = float(cbr)
    # correlacion orientativa Ev2 ~ 17,6 * CBR^0,64 (NDP) -> categoria
    ev2 = 17.6 * (cbr ** 0.64)
    return categoria_explanada_desde_ev2(ev2), round(ev2, 1)


def bases(imdp=None, imd_total=None, pct_pesados=None, ev2_mpa=None, cbr=None,
          calzada_unica=False, factor_carril=1.0):
    """Resuelve (categoria_trafico, categoria_explanada) desde los datos de proyecto.
    Prioridad: IMDp directa > (IMD + %pesados); Ev2 > CBR."""
    if imdp is None:
        if imd_total is None or pct_pesados is None:
            raise ValueError("Faltan datos de trafico: pasa imdp o (imd_total y pct_pesados).")
        imdp = imdp_desde_imd(imd_total, pct_pesados, calzada_unica=calzada_unica,
                              factor_carril=factor_carril)
    cat_t = categoria_trafico_desde_imdp(imdp)

    ev2_estimado = None
    if ev2_mpa is not None:
        cat_e = categoria_explanada_desde_ev2(ev2_mpa)
    elif cbr is not None:
        cat_e, ev2_estimado = categoria_explanada_desde_cbr(cbr)
    else:
        raise ValueError("Faltan datos de explanada: pasa ev2_mpa o cbr.")

    return {
        "imdp_veh_pesados_dia": round(float(imdp), 1),
        "categoria_trafico": cat_t,
        "ev2_mpa": ev2_mpa if ev2_mpa is not None else ev2_estimado,
        "categoria_explanada": cat_e,
        "fuente_explanada": "Ev2" if ev2_mpa is not None else ("CBR->Ev2(estimado)" if cbr else None),
        "nota": "Predimensionado 6.1-IC; categoria de explanada definitiva segun la "
                "FORMACION (fig.1). NDP [confirmar AN].",
    }


if __name__ == "__main__":
    print(bases(imd_total=8000, pct_pesados=12, calzada_unica=True, ev2_mpa=150))
    print(bases(imdp=300, cbr=8))
