#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
alineaciones_ifc.py  --  Puente del compilador narracion->IFC al constructor de
ALINEACIONES de la Ola 5 (iso19650-openbim/scripts/lineal/generate_test_ifc_lineal.py).

NO reimplementa la geometria de alineacion: traduce el bloque `alineaciones[]` del
alto.json (recta/clotoide/curva en planta; rasantes/acuerdos en alzado; peralte;
georreferencia) a las estructuras que consume `construir_alineacion(...)`, y delega.

Asi el contrato C1 autora `IfcAlignment` COMPLETO (planta+alzado+seccion+peralte)
reutilizando la maquinaria validada en PT 5.1, legible por `ifc_to_model_lineal.py`.
"""
import math
import os
import sys

_INF = 0.0

# --- mapeos deterministas de tipo (lenguaje del cebo -> PredefinedType IFC4X3) ---
_PLANTA = {
    "recta": "LINE", "line": "LINE", "tangente": "LINE",
    "clotoide": "CLOTHOID", "clothoid": "CLOTHOID", "transicion": "CLOTHOID",
    "espiral": "CLOTHOID",
    "curva": "CIRCULARARC", "arco": "CIRCULARARC", "circular": "CIRCULARARC",
    "circulararc": "CIRCULARARC",
}
_ALZADO = {
    "rampa": "CONSTANTGRADIENT", "rasante": "CONSTANTGRADIENT",
    "pendiente": "CONSTANTGRADIENT", "constantgradient": "CONSTANTGRADIENT",
    "acuerdo": "PARABOLICARC", "parabola": "PARABOLICARC",
    "parabolicarc": "PARABOLICARC", "vertical": "PARABOLICARC",
    "circular": "CIRCULARARC", "clotoide": "CLOTHOID",
}
_PERALTE = {
    "constante": "CONSTANTCANT", "constantcant": "CONSTANTCANT",
    "transicion": "LINEARTRANSITION", "lineartransition": "LINEARTRANSITION",
    "rampa_peralte": "LINEARTRANSITION",
}


def _ruta_lineal():
    """Descubre la carpeta scripts/lineal (dev y plugin instalado) sin hardcodear."""
    here = os.path.dirname(os.path.abspath(__file__))
    cands = [
        os.path.join(here, "..", "iso19650-openbim", "scripts", "lineal"),
        os.path.join(here, "..", "..", "iso19650-openbim", "scripts", "lineal"),
        os.path.join(here, "..", "scripts", "lineal"),
        os.path.join(here, "scripts", "lineal"),
        os.path.join(here, "lineal"),
    ]
    extra = os.environ.get("ESTRUCTURANDO_LINEAL")
    if extra:
        cands.insert(0, extra)
    for c in cands:
        if os.path.isfile(os.path.join(c, "generate_test_ifc_lineal.py")):
            return os.path.abspath(c)
    raise ImportError(
        "No encuentro scripts/lineal/generate_test_ifc_lineal.py (maquinaria de "
        "alineaciones de la Ola 5). Define ESTRUCTURANDO_LINEAL si esta fuera de ruta.")


def _builder():
    ruta = _ruta_lineal()
    if ruta not in sys.path:
        sys.path.insert(0, ruta)
    import generate_test_ifc_lineal as gen
    return gen


def _planta(segs):
    out = []
    for s in segs:
        tipo = _PLANTA.get(str(s.get("tipo", "recta")).lower(), str(s.get("tipo")).upper())
        L = float(s.get("longitud", s.get("L", 0.0)))
        if tipo == "CIRCULARARC":
            R = s.get("radio", s.get("R"))
            ri = rf = (float(R) if R else _INF)
        elif tipo == "CLOTHOID":
            ri = s.get("radio_ini", s.get("ri"))
            rf = s.get("radio_fin", s.get("rf"))
            ri = float(ri) if ri else _INF
            rf = float(rf) if rf else _INF
        else:  # LINE
            ri = rf = _INF
        out.append((tipo, L, ri, rf))
    return out


def _alzado(segs):
    out = []
    for s in segs:
        tipo = _ALZADO.get(str(s.get("tipo", "rampa")).lower(), str(s.get("tipo")).upper())
        Lh = float(s.get("longitud", s.get("longitud_h", s.get("L", 0.0))))
        gi = float(s.get("pendiente_ini", s.get("gi", 0.0)))
        gf = float(s.get("pendiente_fin", s.get("gf", gi)))
        R = s.get("kv", s.get("radio", s.get("R", 0.0))) or 0.0
        out.append((tipo, Lh, gi, gf, float(R)))
    return out


def _peralte(segs, long_total, ancho_ref):
    if not segs:
        return [("CONSTANTCANT", 0.0, float(long_total), 0.0, 0.0)]
    out = []
    s0 = 0.0
    for s in segs:
        pi = float(s.get("peralte_ini_pct", s.get("pi", 0.0)))
        pf = float(s.get("peralte_fin_pct", s.get("pf", pi)))
        tipo = s.get("tipo")
        if tipo is None:
            tipo = "transicion" if abs(pf - pi) > 1e-9 else "constante"
        tipo = _PERALTE.get(str(tipo).lower(),
                            "LINEARTRANSITION" if abs(pf - pi) > 1e-9 else "CONSTANTCANT")
        Lh = float(s.get("longitud", s.get("L", 0.0)))
        s0v = s.get("pk_ini", s.get("s0"))
        s0v = float(s0v) if s0v is not None else s0
        out.append((tipo, s0v, Lh, pi, pf))
        s0 = s0v + Lh
    return out


def autorar_alineacion(model, ctx, spec, prj=None):
    """Autora un IfcAlignment completo desde un dict `alineaciones[]` del alto.json.
    Reutiliza construir_alineacion(...) de la Ola 5. Devuelve la entidad alignment."""
    gen = _builder()
    planta = _planta(spec.get("planta", []))
    alzado = _alzado(spec.get("alzado", [])) if spec.get("alzado") else None
    long_total = sum(p[1] for p in planta)
    ancho_ref = float(spec.get("ancho_ref", spec.get("ancho", 3.5)))
    peralte = _peralte(spec.get("peralte", []), long_total, ancho_ref)

    ini = spec.get("inicio", {})
    az0 = ini.get("acimut_rad")
    if az0 is None:
        az0 = math.radians(float(ini.get("acimut_deg", 0.0)))
    cota_ini = float(ini.get("cota", spec.get("cota_inicial", 0.0)))

    georref = spec.get("georref")
    infra = spec.get("infraestructura") or spec.get("infra")

    alignment, _nh, _nv, _nc = gen.construir_alineacion(
        model, ctx,
        nombre=spec.get("nombre", "Eje"),
        planta=planta, alzado=alzado, peralte=peralte,
        ancho_ref=ancho_ref, cota_ini=cota_ini,
        x0=float(ini.get("x", 0.0)), y0=float(ini.get("y", 0.0)), az0=float(az0),
        georref=georref, infra=infra, prj=prj)
    return alignment
