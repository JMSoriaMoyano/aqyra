"""
CATALOGO DE SECCIONES DE FIRME -- Norma 6.1-IC. Plugin obras-lineales. PT 5.2.

CATALOGO LITERAL (no dimensionado parametrico): las secciones del firme son DATOS
de la norma, indexados por (categoria de trafico pesado x categoria de explanada).
Cada seccion es un PAQUETE de capas (de arriba a abajo) con su material y espesor.

Decision (PT 5.2): catalogo, porque es lo que manda la 6.1-IC; el dimensionado por
fatiga no se rehace. Aqui se incluyen las secciones de FIRME FLEXIBLE (mezcla
bituminosa sobre zahorra artificial, codigo terminado en 1) que cubren T1..T42, y
una alternativa SEMIRRIGIDA (suelocemento, codigo terminado en 2) para T00/T0.

Codigo 6.1-IC = [digito trafico][digito explanada][tipo de firme]:
  trafico: 0=T00/T0, 1=T1, 2=T2, 3=T3x, 4=T4x ; explanada: 1=E1,2=E2,3=E3 ;
  tipo: 1=granular(zahorra), 2=suelocemento.

TODOS los espesores son NDP [confirmar AN] con las figuras 2.1/2.2 de la edicion
vigente. Predimensionado; revisar/firmar por tecnico competente (ICCP).
"""


def _sec(codigo, capas):
    total = sum(c["espesor_cm"] for c in capas)
    return {"codigo": codigo, "paquete": capas, "espesor_total_cm": total}


def _mb(esp):
    return {"capa": "Mezcla bituminosa", "material": "MB", "espesor_cm": esp}


def _za(esp):
    return {"capa": "Zahorra artificial", "material": "ZA", "espesor_cm": esp}


def _sc(esp):
    return {"capa": "Suelocemento", "material": "SC", "espesor_cm": esp}


# Espesor de mezcla bituminosa (cm) por categoria de trafico (firme flexible).
# [confirmar AN] (fig. 2.1).
_MB_POR_TRAFICO = {
    "T1": 26, "T2": 18, "T31": 16, "T32": 12, "T41": 8, "T42": 5,
}
# Espesor de zahorra artificial (cm) por categoria de explanada (mas debil -> mas
# espesor). [confirmar AN].
_ZA_POR_EXPLANADA = {"E1": 40, "E2": 30, "E3": 25}

# Matriz de combinaciones PERMITIDAS (6.1-IC): E1 no se admite para trafico alto.
# [confirmar AN].
_PERMITIDAS = {
    "T00": ["E2", "E3"],
    "T0": ["E2", "E3"],
    "T1": ["E2", "E3"],
    "T2": ["E1", "E2", "E3"],
    "T31": ["E1", "E2", "E3"],
    "T32": ["E1", "E2", "E3"],
    "T41": ["E1", "E2", "E3"],
    "T42": ["E1", "E2", "E3"],
}

_DIG_TRAFICO = {"T00": "0", "T0": "0", "T1": "1", "T2": "2",
                "T31": "3", "T32": "3", "T41": "4", "T42": "4"}
_DIG_EXPLANADA = {"E1": "1", "E2": "2", "E3": "3"}

# Secciones semirrigidas explicitas para trafico alto (T00/T0): MB sobre suelocemento.
# [confirmar AN].
_SEMIRRIGIDAS = {
    ("T00", "E2"): _sec("012", [_mb(34), _sc(22)]),
    ("T00", "E3"): _sec("013", [_mb(31), _sc(22)]),
    ("T0", "E2"): _sec("022", [_mb(31), _sc(22)]),
    ("T0", "E3"): _sec("023", [_mb(30), _sc(20)]),
}


def seccion(categoria_trafico, categoria_explanada):
    """Devuelve la seccion de firme del catalogo 6.1-IC para (trafico, explanada),
    o un dict de error si la combinacion no esta permitida/definida."""
    t, e = categoria_trafico, categoria_explanada
    if t not in _PERMITIDAS:
        return {"error": "Categoria de trafico desconocida: %r" % t}
    if e not in _PERMITIDAS[t]:
        return {"error": "Combinacion %s x %s NO permitida por la 6.1-IC "
                         "(mejorar la explanada)." % (t, e),
                "permitidas": _PERMITIDAS[t]}
    # firme flexible (zahorra) si hay MB tabulada para ese trafico
    if t in _MB_POR_TRAFICO:
        codigo = _DIG_TRAFICO[t] + _DIG_EXPLANADA[e] + "1"
        capas = [_mb(_MB_POR_TRAFICO[t]), _za(_ZA_POR_EXPLANADA[e])]
        sec = _sec(codigo, capas)
        sec["tipo_firme"] = "flexible (MB sobre zahorra artificial)"
        return sec
    # trafico alto -> semirrigido
    if (t, e) in _SEMIRRIGIDAS:
        sec = dict(_SEMIRRIGIDAS[(t, e)])
        sec["tipo_firme"] = "semirrigido (MB sobre suelocemento)"
        return sec
    return {"error": "Sin seccion definida en el catalogo para %s x %s." % (t, e)}


def catalogo_completo():
    """Itera todas las secciones definidas (para inspeccion/tests)."""
    out = {}
    for t in _PERMITIDAS:
        for e in _PERMITIDAS[t]:
            out["%s-%s" % (t, e)] = seccion(t, e)
    return out


if __name__ == "__main__":
    for k, v in catalogo_completo().items():
        if "error" in v:
            print("%-8s  %s" % (k, v["error"]))
        else:
            capas = " + ".join("%s %dcm" % (c["material"], c["espesor_cm"]) for c in v["paquete"])
            print("%-8s  %s  [%s]  total %d cm" % (k, v["codigo"], capas, v["espesor_total_cm"]))
