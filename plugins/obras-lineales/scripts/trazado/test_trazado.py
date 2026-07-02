"""
MICRO-TEST de la comprobacion de trazado (3.1-IC). Plugin obras-lineales. PT 5.2.
stdlib pura; sin dependencias. Ejecuta:  python3 test_trazado.py
"""
import comprobacion_trazado as C
import parametros_3_1_IC as P
import verificacion_trazado as V


def _modelo(planta, alzado):
    return {"eje": {"nombre": "TEST"}, "alineacion": {"planta": planta, "alzado": alzado}}


def test_planta_cumple():
    # R=300 cumple para Vp=60 (Rmin=130); clotoide A in [R/3,R]=[100,300]
    planta = [{"pk_ini": 0, "tipo": "CLOTHOID", "longitud": 70, "radio_fin": 300, "A_clotoide": 145.0},
              {"pk_ini": 70, "tipo": "CIRCULARARC", "longitud": 80, "radio_ini": 300, "radio_fin": 300}]
    res = C.comprobar(_modelo(planta, []), 60)
    assert res["veredicto"] == "CUMPLE", res["no_cumplen"]


def test_planta_radio_insuficiente():
    # R=300 NO cumple para Vp=100 (Rmin=450)
    planta = [{"pk_ini": 0, "tipo": "CIRCULARARC", "longitud": 80, "radio_ini": 300, "radio_fin": 300}]
    res = C.comprobar(_modelo(planta, []), 100)
    assert res["veredicto"] == "NO CUMPLE"
    assert any("radio" in r["magnitud"] for r in res["no_cumplen"])


def test_clotoide_corta():
    # A=50 < R/3=100 -> NO CUMPLE (parametro corto)
    planta = [{"pk_ini": 0, "tipo": "CLOTHOID", "longitud": 30, "radio_fin": 300, "A_clotoide": 50.0}]
    res = C.comprobar(_modelo(planta, []), 60)
    assert any("clotoide" in r["magnitud"] for r in res["no_cumplen"])


def test_pendiente_excesiva():
    alzado = [{"pk_ini": 0, "tipo": "CONSTANTGRADIENT", "longitud_h": 100,
               "pendiente_ini": 0.09, "pendiente_fin": 0.09, "cota_ini": 0}]
    res = C.comprobar(_modelo([], alzado), 80)   # imax(80)=5% -> 9% no cumple
    assert res["veredicto"] == "NO CUMPLE"
    assert any("pendiente" in r["magnitud"] for r in res["no_cumplen"])


def test_acuerdo_convexo_insuficiente():
    # acuerdo convexo Kv=2000 vs Kv_min_convexo(120) (muy grande) -> NO CUMPLE
    alzado = [{"pk_ini": 0, "tipo": "PARABOLICARC", "longitud_h": 100, "kv": 2000,
               "pendiente_ini": 0.02, "pendiente_fin": -0.03, "cota_ini": 0}]
    res = C.comprobar(_modelo([], alzado), 120)
    assert res["veredicto"] == "NO CUMPLE"
    assert any("Kv" in r["magnitud"] for r in res["no_cumplen"])


def test_acuerdo_convexo_cumple_baja_vp():
    # mismo acuerdo Kv=2000 SI cumple a Vp=60 (Kv_min_convexo(60) ~ 1100)
    alzado = [{"pk_ini": 0, "tipo": "PARABOLICARC", "longitud_h": 100, "kv": 2000,
               "pendiente_ini": 0.02, "pendiente_fin": -0.03, "cota_ini": 0}]
    res = C.comprobar(_modelo([], alzado), 60)
    kv_conv = P.kv_min_convexo(60)
    assert kv_conv < 2000, kv_conv
    assert res["veredicto"] == "CUMPLE", res["no_cumplen"]


def test_resumen_coherente():
    planta = [{"pk_ini": 0, "tipo": "CIRCULARARC", "longitud": 80, "radio_ini": 300, "radio_fin": 300}]
    res = C.comprobar(_modelo(planta, []), 60)
    s = V.resumen(res)
    assert s["n_cumple"] + s["n_no_cumple"] == s["n_comprobaciones"]


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    ok = 0
    for fn in fns:
        try:
            fn()
            print("  OK  ", fn.__name__)
            ok += 1
        except AssertionError as e:
            print("  FAIL", fn.__name__, "->", e)
        except Exception as e:
            print("  ERR ", fn.__name__, "->", type(e).__name__, e)
    print("\n%d/%d tests OK" % (ok, len(fns)))
    raise SystemExit(0 if ok == len(fns) else 1)
