"""
COMPROBACION DE TRAZADO -- Norma 3.1-IC. Plugin obras-lineales. PT 5.2 (Ola 5).

Consume el MODELO NEUTRO LINEAL (alineacion{planta[],alzado[],peralte[]}) emitido
por iso19650-openbim (scripts/lineal/ifc_to_model_lineal.py) y comprueba el
cumplimiento NORMATIVO frente a una VELOCIDAD DE PROYECTO Vp:

  PLANTA   -> radio minimo vs Vp; parametro A y longitud de clotoide (limites 3.1-IC).
  ALZADO   -> Kv minimo de acuerdos convexo/concavo (visibilidad de parada);
              pendiente maxima y minima.
  VISIBIL. -> distancia de parada disponible (informativo).
  COORD.   -> coordinacion planta-alzado (informativo).

NO rediseña el eje: para cada elemento emite CUMPLE/NO CUMPLE + una PROPUESTA de
predimensionado (radio/Kv/A necesarios). El dato del proyecto (Vp del Pset del IFC)
prevalece; si falta, lo inyecta el agente. Predimensionado; revisar/firmar por ICCP.

Uso (programatico):  comprobar(modelo, vp) -> dict
"""
import math

import parametros_3_1_IC as P


def _chk(ok, elemento, magnitud, valor, limite, unidad, propuesta=None):
    """Construye un registro de comprobacion homogeneo."""
    return {
        "elemento": elemento,
        "magnitud": magnitud,
        "valor": round(valor, 4) if isinstance(valor, (int, float)) else valor,
        "limite": round(limite, 4) if isinstance(limite, (int, float)) else limite,
        "unidad": unidad,
        "cumple": bool(ok),
        "propuesta": propuesta,
    }


def comprobar_planta(planta, vp):
    """Radios y clotoides en planta vs Vp."""
    regs = []
    r_min = P.radio_minimo(vp)
    for i, s in enumerate(planta):
        pk = s.get("pk_ini")
        et = "Planta seg %d (PK %.1f, %s)" % (i, pk or 0.0, s.get("tipo"))
        if s.get("tipo") == "CIRCULARARC":
            R = abs(s.get("radio_ini") or s.get("radio_fin") or 0.0)
            ok = R >= r_min - 1e-6
            prop = None if ok else "Aumentar R a >= %.0f m o reducir Vp" % r_min
            regs.append(_chk(ok, et, "radio R", R, r_min, "m", prop))
        if s.get("tipo") == "CLOTHOID" and s.get("A_clotoide"):
            R = abs(s.get("radio_fin") or s.get("radio_ini") or 0.0)
            A = float(s["A_clotoide"])
            a_min, a_max = P.limites_clotoide(R)
            ok = (A >= a_min - 1e-6) and (A <= a_max + 1e-6)
            if A < a_min:
                prop = "A=%.1f < R/3=%.1f: alargar la clotoide (A>=%.0f)" % (A, a_min, a_min)
            elif A > a_max:
                prop = "A=%.1f > R=%.1f: acortar la clotoide (A<=%.0f)" % (A, a_max, a_max)
            else:
                prop = None
            regs.append(_chk(ok, et, "parametro A clotoide", A, "[%.0f, %.0f]" % (a_min, a_max),
                             "m", prop))
            # longitud minima por confort dinamico (jerk) -- informativo
            L = float(s.get("longitud") or 0.0)
            l_min = P.longitud_min_clotoide_jerk(vp, R)
            ok_l = L >= l_min - 1e-6
            prop_l = None if ok_l else "Alargar a L>=%.1f m (variacion de a_centrifuga)" % l_min
            regs.append(_chk(ok_l, et, "longitud clotoide (confort)", L, l_min, "m", prop_l))
    return regs


def comprobar_alzado(alzado, vp):
    """Acuerdos verticales (Kv) y pendientes en alzado vs Vp."""
    regs = []
    i_max = P.pendiente_maxima(vp)
    kv_conv = P.kv_min_convexo(vp)
    kv_conc = P.kv_min_concavo(vp)
    for i, s in enumerate(alzado):
        pk = s.get("pk_ini")
        # pendientes (rasantes)
        for clave in ("pendiente_ini", "pendiente_fin"):
            p = abs(float(s.get(clave) or 0.0))
            et = "Alzado seg %d (PK %.1f)" % (i, pk or 0.0)
            ok = p <= i_max + 1e-9
            prop = None if ok else "Reducir pendiente a <= %.1f%% o reducir Vp" % (i_max * 100)
            regs.append(_chk(ok, et, "pendiente %s" % clave.split("_")[1], p, i_max, "m/m", prop))
        # pendiente minima por drenaje (informativo): rasante "horizontal"
        if abs(float(s.get("pendiente_ini") or 0.0)) < P.PENDIENTE_MIN_ABS and \
           abs(float(s.get("pendiente_fin") or 0.0)) < P.PENDIENTE_MIN_ABS and \
           s.get("tipo") == "CONSTANTGRADIENT":
            regs.append(_chk(False, "Alzado seg %d (PK %.1f)" % (i, pk or 0.0),
                             "pendiente minima (drenaje)",
                             abs(float(s.get("pendiente_ini") or 0.0)), P.PENDIENTE_MIN,
                             "m/m", "Garantizar i>=0,5%% para drenaje longitudinal"))
        # acuerdos verticales (parabolicos)
        if s.get("tipo") == "PARABOLICARC" and s.get("kv"):
            kv = abs(float(s["kv"]))
            convexo = float(s.get("pendiente_fin") or 0.0) < float(s.get("pendiente_ini") or 0.0)
            kv_lim = kv_conv if convexo else kv_conc
            tipo_ac = "convexo" if convexo else "concavo"
            ok = kv >= kv_lim - 1e-6
            prop = None if ok else "Aumentar Kv a >= %.0f m (visibilidad de parada)" % kv_lim
            regs.append(_chk(ok, "Alzado seg %d (PK %.1f, acuerdo %s)" % (i, pk or 0.0, tipo_ac),
                             "Kv acuerdo %s" % tipo_ac, kv, kv_lim, "m", prop))
    return regs


def comprobar_coordinacion(planta, alzado):
    """Coordinacion planta-alzado (INFORMATIVO, 3.1-IC cap.7): evitar que el
    vertice de un acuerdo vertical coincida con una transicion de curvatura en
    planta (perdida de guiado optico). Reporta avisos, no bloquea."""
    avisos = []
    trans = [s.get("pk_ini") for s in planta if s.get("tipo") == "CLOTHOID"]
    for s in alzado:
        if s.get("tipo") == "PARABOLICARC":
            pk0 = s.get("pk_ini") or 0.0
            pk1 = pk0 + (s.get("longitud_h") or 0.0)
            for pkt in trans:
                if pkt is not None and pk0 - 20.0 <= pkt <= pk1 + 20.0:
                    avisos.append("[3.1-IC cap.7] Acuerdo vertical PK %.1f-%.1f proximo a "
                                  "transicion en planta PK %.1f (revisar guiado optico)."
                                  % (pk0, pk1, pkt))
    return avisos


def comprobar(modelo, vp):
    """Comprobacion completa del trazado para una Vp. Devuelve dict con veredicto."""
    ali = modelo.get("alineacion", {})
    planta = ali.get("planta", [])
    alzado = ali.get("alzado", [])

    regs = comprobar_planta(planta, vp)
    regs += comprobar_alzado(alzado, vp)
    avisos = comprobar_coordinacion(planta, alzado)

    no_cumplen = [r for r in regs if not r["cumple"]]
    veredicto = "CUMPLE" if not no_cumplen else "NO CUMPLE"

    return {
        "veredicto": veredicto,
        "vp_kmh": float(vp),
        "eje": (modelo.get("eje") or {}).get("nombre"),
        "umbrales_3_1_IC": {
            "radio_min_m": P.radio_minimo(vp),
            "pendiente_max_pct": round(P.pendiente_maxima(vp) * 100, 2),
            "distancia_parada_m": round(P.distancia_parada(vp), 1),
            "kv_min_convexo_m": round(P.kv_min_convexo(vp), 0),
            "kv_min_concavo_m": round(P.kv_min_concavo(vp), 0),
        },
        "comprobaciones": regs,
        "no_cumplen": no_cumplen,
        "avisos": avisos,
        "nota": "Predimensionado/asistencia (3.1-IC). NDP [confirmar AN]. "
                "Revisar y firmar por tecnico competente (ICCP).",
    }
