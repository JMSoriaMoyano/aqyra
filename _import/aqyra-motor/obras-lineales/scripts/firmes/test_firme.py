"""
MICRO-TEST de la seleccion de firme (6.1-IC). Plugin obras-lineales. PT 5.2.
stdlib pura; sin dependencias. Ejecuta:  python3 test_firme.py
"""
import bases_firme as B
import catalogo_6_1_IC as CAT
import seleccion_firme as S
import verificacion_firme as V

MODELO_BASE = {
    "eje": {"nombre": "TEST"},
    "alineacion": {"peralte": [{"peralte_ini_pct": 0.0, "peralte_fin_pct": 7.0}]},
    "firme": None, "secciones_tipo": None, "terreno": None,
}


def test_categoria_trafico():
    assert B.categoria_trafico_desde_imdp(300) == "T2"
    assert B.categoria_trafico_desde_imdp(1500) == "T1"
    assert B.categoria_trafico_desde_imdp(10) == "T42"
    assert B.categoria_trafico_desde_imdp(5000) == "T00"


def test_categoria_explanada():
    assert B.categoria_explanada_desde_ev2(150) == "E2"
    assert B.categoria_explanada_desde_ev2(350) == "E3"
    assert B.categoria_explanada_desde_ev2(80) == "E1"
    assert B.categoria_explanada_desde_ev2(40) is None


def test_combinacion_no_permitida():
    sec = CAT.seccion("T1", "E1")   # E1 no permitida para T1
    assert "error" in sec


def test_seleccion_rellena_ganchos():
    m2, res = S.seleccionar(MODELO_BASE, imd_total=8000, pct_pesados=12,
                            calzada_unica=True, ev2_mpa=150)
    assert res["veredicto"] == "CUMPLE", res
    assert m2["firme"] is not None
    assert m2["firme"]["categoria_trafico"] in ("T1", "T2")
    assert m2["firme"]["espesor_total_cm"] > 0
    assert m2["secciones_tipo"] is not None
    # no destruye claves existentes
    assert "alineacion" in m2 and m2["terreno"] is None


def test_no_inplace_preserva_original():
    m2, res = S.seleccionar(MODELO_BASE, imdp=300, ev2_mpa=150)
    assert MODELO_BASE["firme"] is None  # original intacto
    assert m2["firme"] is not None


def test_verificacion_cumple():
    m2, res = S.seleccionar(MODELO_BASE, imdp=300, ev2_mpa=150)
    ver = V.verificar(m2, res)
    assert ver["veredicto"] == "CUMPLE", ver["errores"]


def test_verificacion_no_permitida():
    # T1 con explanada insuficiente (E1) -> seleccion falla -> verificacion NO CUMPLE
    m2, res = S.seleccionar(MODELO_BASE, imdp=1500, ev2_mpa=80)  # T1 x E1
    ver = V.verificar(m2, res)
    assert ver["veredicto"] == "NO CUMPLE"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    ok = 0
    for fn in fns:
        try:
            fn(); print("  OK  ", fn.__name__); ok += 1
        except AssertionError as e:
            print("  FAIL", fn.__name__, "->", e)
        except Exception as e:
            print("  ERR ", fn.__name__, "->", type(e).__name__, e)
    print("\n%d/%d tests OK" % (ok, len(fns)))
    raise SystemExit(0 if ok == len(fns) else 1)
