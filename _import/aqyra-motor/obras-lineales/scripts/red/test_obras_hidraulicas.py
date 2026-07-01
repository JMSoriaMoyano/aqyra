"""
MICRO-TEST del solver de Manning de red (lamina libre) y su arnes. Disciplina
`obras-lineales`, PT 6.2 (Ola 6). Sin dependencias externas (stdlib + reuso interno).

Casos:
  POSITIVO  : arbol de colectores que converge al vertido, caudales/pendientes que
              dan velocidad de autolimpieza y llenado admisible -> CUMPLE; balance
              nodal cierra (continuidad hacia el vertido).
  NEGATIVOS : (1) tramo sin pendiente / contrapendiente, (2) velocidad < autolimpieza
              (DN grande, caudal bajo), (3) llenado excesivo / sobrecarga (DN chico,
              caudal alto), (4) DN < minimo.
  MALLA     : red con un lazo (cuerda entre pozos) -> Hardy-Cross lamina libre
              converge y el balance nodal cierra (cableado de mallas).
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "..", "drenaje"))
import solver_lamina_libre as S          # noqa: E402
import verificacion_red_lineal as V      # noqa: E402

OK, KO = 0, 0


def chk(cond, msg):
    global OK, KO
    if cond:
        OK += 1; print("  OK ", msg)
    else:
        KO += 1; print("  XX ", msg)


def _tramo(ni, nj, dn, L, mat="hormigon", elem=None):
    return {"ni": ni, "nj": nj, "dn": dn, "material": mat, "longitud": L,
            "elemento": elem or (ni + nj)}


def _term(tid, nodo, q_ls):
    # caudal directo (l/s) via caudal_min -> demanda controlada para el test
    return {"id": tid, "nodo": nodo, "caudal_min": q_ls, "demanda": {"caudal_l_s": q_ls}}


def _nodo(z, tipo, solera):
    return {"x": 0.0, "y": 0.0, "z": z, "tipo": tipo, "cota_solera": solera}


# --- POSITIVO: arbol P1,P2 -> P3 -> V -----------------------------------------
def caso_positivo():
    # pendiente 1.0 % en todos los tramos (caida de solera 0.5 m en 50 m)
    modelo = {
        "unidades": {"longitud": "m"},
        "sistema": {"tipo": "SEWAGE", "demanda": None},
        "nodos": {
            "P1": _nodo(101.0, "terminal", 100.5),
            "P2": _nodo(101.0, "terminal", 100.5),
            "P3": _nodo(100.5, "union", 100.0),
            "V":  _nodo(100.0, "vertido", 99.5),
        },
        "tramos": {
            "T1": _tramo("P1", "P3", 315, 50.0, elem="COL-1"),
            "T2": _tramo("P2", "P3", 315, 50.0, elem="COL-2"),
            "T3": _tramo("P3", "V", 400, 50.0, elem="COL-3"),
        },
        "terminales": [_term("A1", "P1", 12.0), _term("A2", "P2", 12.0)],
        "fuentes": [{"id": "VERT", "nodo": "V", "tipo": "vertido"}],
    }
    res = S.resolver(modelo)
    ver = V.verificar(modelo, res)
    print("POSITIVO:", res["veredicto"], "| ver:", ver["veredicto"],
          "| res nudo %.4f%%" % ver["residuo_nudo_max_pct"],
          "| v_pico %.2f llenado %.1f%%" % (res["velocidad_pico_m_s"], res["llenado_pico_pct"]))
    chk(res["veredicto"] == "CUMPLE", "positivo: solver CUMPLE")
    chk(ver["veredicto"] == "CUMPLE", "positivo: verificacion CUMPLE")
    chk(ver["residuo_nudo_max_pct"] < 0.1, "positivo: balance nodal cierra (<0.1%)")
    # continuidad: T3 = T1 + T2 = 24 l/s
    chk(abs(res["tramos"]["T3"]["caudal_l_s"] - 24.0) < 1e-6, "positivo: T3 = T1+T2 = 24 l/s")
    chk(res["caudal_total_vertido_l_s"] == 24.0, "positivo: vertido recoge 24 l/s")


# --- NEGATIVO 1: tramo sin pendiente / contrapendiente ------------------------
def caso_sin_pendiente():
    modelo = {
        "unidades": {"longitud": "m"},
        "sistema": {"tipo": "SEWAGE", "demanda": None},
        "nodos": {
            "P1": _nodo(100.0, "terminal", 100.0),   # misma solera aguas arriba
            "V":  _nodo(100.0, "vertido", 100.0),    # ... y aguas abajo -> J=0
        },
        "tramos": {"T1": _tramo("P1", "V", 315, 50.0, elem="COL-1")},
        "terminales": [_term("A1", "P1", 12.0)],
        "fuentes": [{"id": "VERT", "nodo": "V", "tipo": "vertido"}],
    }
    res = S.resolver(modelo)
    ver = V.verificar(modelo, res)
    print("NEG sin pendiente:", res["veredicto"])
    chk(res["veredicto"] == "NO CUMPLE", "neg pendiente: NO CUMPLE")
    chk(any("desagua" in e for e in res["errores"]), "neg pendiente: avisa que no desagua")


# --- NEGATIVO 2: velocidad < autolimpieza (DN grande, caudal bajo) ------------
def caso_velocidad_baja():
    modelo = {
        "unidades": {"longitud": "m"},
        "sistema": {"tipo": "SEWAGE", "demanda": None},
        "nodos": {
            "P1": _nodo(100.2, "terminal", 100.2),
            "V":  _nodo(100.0, "vertido", 100.0),    # J=0.2/50=0.004
        },
        "tramos": {"T1": _tramo("P1", "V", 600, 50.0, elem="COL-1")},
        "terminales": [_term("A1", "P1", 2.0)],      # 2 l/s en DN600 -> muy lento
        "fuentes": [{"id": "VERT", "nodo": "V", "tipo": "vertido"}],
    }
    res = S.resolver(modelo)
    print("NEG velocidad baja: v=%.3f" % res["tramos"]["T1"]["velocidad_m_s"], res["veredicto"])
    chk(res["veredicto"] == "NO CUMPLE", "neg velocidad: NO CUMPLE")
    chk(any("autolimpieza" in e for e in res["errores"]), "neg velocidad: avisa sedimentacion")


# --- NEGATIVO 3: llenado excesivo / sobrecarga (DN chico, caudal alto) --------
def caso_llenado_excesivo():
    modelo = {
        "unidades": {"longitud": "m"},
        "sistema": {"tipo": "SEWAGE", "demanda": None},
        "nodos": {
            "P1": _nodo(100.5, "terminal", 100.5),
            "V":  _nodo(100.0, "vertido", 100.0),    # J=0.5/50=0.01
        },
        "tramos": {"T1": _tramo("P1", "V", 315, 50.0, elem="COL-1")},
        "terminales": [_term("A1", "P1", 150.0)],    # 150 l/s en DN315 -> en carga
        "fuentes": [{"id": "VERT", "nodo": "V", "tipo": "vertido"}],
    }
    res = S.resolver(modelo)
    to = res["tramos"]["T1"]
    print("NEG llenado: llenado=%s%% sobre=%s" % (to.get("llenado_pct"), to.get("sobrecarga")), res["veredicto"])
    chk(res["veredicto"] == "NO CUMPLE", "neg llenado: NO CUMPLE")
    chk(any(("llenado" in e or "CARGA" in e or "carga" in e) for e in res["errores"]),
        "neg llenado: avisa llenado/sobrecarga")


# --- NEGATIVO 4: DN < minimo --------------------------------------------------
def caso_dn_insuficiente():
    modelo = {
        "unidades": {"longitud": "m"},
        "sistema": {"tipo": "SEWAGE", "demanda": None},
        "nodos": {
            "P1": _nodo(100.5, "terminal", 100.5),
            "V":  _nodo(100.0, "vertido", 100.0),
        },
        "tramos": {"T1": _tramo("P1", "V", 200, 50.0, elem="COL-1")},  # DN200 < 300
        "terminales": [_term("A1", "P1", 8.0)],
        "fuentes": [{"id": "VERT", "nodo": "V", "tipo": "vertido"}],
    }
    res = S.resolver(modelo)
    print("NEG DN:", res["veredicto"])
    chk(res["veredicto"] == "NO CUMPLE", "neg DN: NO CUMPLE")
    chk(any("minimo" in e for e in res["errores"]), "neg DN: avisa DN minimo")


# --- MALLA: lazo entre pozos (cuerda) -> Hardy-Cross lamina libre -------------
def caso_malla():
    # 1 LAZO limpio: P1 -> {P2, P3} con cuerda P1-P3; P2 -> P3 -> V.
    # 4 nodos, 4 tramos -> 1 lazo independiente (P1-P2-P3 cerrado por la cuerda).
    modelo = {
        "unidades": {"longitud": "m"},
        "sistema": {"tipo": "SEWAGE", "demanda": None},
        "nodos": {
            "P1": _nodo(102.0, "terminal", 101.5),
            "P2": _nodo(101.5, "union", 101.0),
            "P3": _nodo(101.0, "union", 100.5),
            "V":  _nodo(100.5, "vertido", 100.0),
        },
        "tramos": {
            "T1": _tramo("P1", "P2", 400, 50.0, elem="C1"),
            "T2": _tramo("P2", "P3", 315, 50.0, elem="C2"),
            "Tc": _tramo("P1", "P3", 315, 70.7, elem="Cc"),   # cuerda (lazo)
            "T3": _tramo("P3", "V", 500, 50.0, elem="C3"),
        },
        "terminales": [_term("A1", "P1", 30.0)],
        "fuentes": [{"id": "VERT", "nodo": "V", "tipo": "vertido"}],
    }
    res = S.resolver(modelo)
    ver = V.verificar(modelo, res)
    hc = res.get("hardy_cross")
    print("MALLA: lazos=%d converge=%s res_nudo=%.4f%%"
          % (res["topologia"]["n_lazos"], hc and hc["convergio"], ver["residuo_nudo_max_pct"]))
    chk(res["topologia"]["n_lazos"] == 1, "malla: detecta 1 lazo")
    chk(hc is not None and hc["convergio"], "malla: Hardy-Cross lamina libre converge")
    chk(ver["residuo_nudo_max_pct"] < 0.1, "malla: balance nodal cierra (<0.1%)")


if __name__ == "__main__":
    print("=" * 60)
    print("MICRO-TEST OBRAS HIDRAULICAS DE RED (Manning lamina libre)")
    print("=" * 60)
    caso_positivo()
    caso_sin_pendiente()
    caso_velocidad_baja()
    caso_llenado_excesivo()
    caso_dn_insuficiente()
    caso_malla()
    print("-" * 60)
    print("RESULTADO: %d OK, %d KO" % (OK, KO))
    sys.exit(0 if KO == 0 else 1)
