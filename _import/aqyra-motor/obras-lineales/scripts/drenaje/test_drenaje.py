"""
MICRO-TEST del drenaje (5.2-IC): hidrologia + cuneta + ODT + run_all/verificacion.
Plugin obras-lineales. PT 6.1. stdlib pura; sin dependencias. Ejecuta: python3 test_drenaje.py
"""
import cuneta as CU
import hidrologia as H
import odt as OD
import run_all_drenaje as R
import verificacion_drenaje as V

MODELO_BASE = {
    "eje": {"nombre": "TEST", "global_id": "gid"},
    "unidades": {"longitud": "m"},
    "alineacion": {"planta": [], "alzado": [], "peralte": []},
    "secciones_tipo": None, "firme": None, "terreno": None,
}

DATOS = {
    "cuencas": [
        {"id": "C-plat", "area_m2": 9000.0, "longitud_m": 300.0, "pendiente": 0.02,
         "pd_mm": 80.0, "i1_id": 9.0, "po_mm": 1.0, "tipo_elemento": "plataforma"},
        {"id": "C-vert", "area_km2": 0.85, "longitud_km": 1.6, "pendiente": 0.03,
         "pd_mm": 95.0, "i1_id": 10.0, "po_mm": 18.0, "tipo_elemento": "odt"},
    ],
    "cunetas": [
        {"id": "CUN-D", "cuenca": "C-plat", "tipo": "triangular", "b_m": 0.0,
         "z1": 3.0, "z2": 3.0, "profundidad_m": 0.30, "pendiente_long": 0.02,
         "revestimiento": "hormigon"},
    ],
    "odt": [
        {"id": "ODT-1", "cuenca": "C-vert", "tipo": "circular", "D_m": 1.80,
         "pendiente_long": 0.015, "material": "hormigon"},
    ],
}


# --- hidrologia ---------------------------------------------------------------
def test_tc_temez_positivo():
    tc = H.tiempo_concentracion(0.3, 0.02)
    assert 0.1 < tc < 1.0, tc


def test_coef_escorrentia_impermeable_vs_permeable():
    # plataforma (Po bajo) -> C alto; cuenca natural (Po alto) -> C bajo
    c_imp = H.coef_escorrentia(80.0, po_mm=1.0)
    c_per = H.coef_escorrentia(80.0, po_mm=30.0)
    assert c_imp > 0.9 and c_per < c_imp, (c_imp, c_per)


def test_caudal_crece_con_area():
    q1 = H.caudal_cuenca(DATOS["cuencas"][0], periodo_retorno_anos=25)["caudal_m3_s"]
    q2 = H.caudal_cuenca(DATOS["cuencas"][1], periodo_retorno_anos=100)["caudal_m3_s"]
    assert q2 > q1 > 0, (q1, q2)


def test_falta_pd_error():
    try:
        H.caudal_cuenca({"id": "x", "area_m2": 1000, "longitud_m": 100,
                         "pendiente": 0.01})
        assert False, "deberia exigir Pd"
    except ValueError:
        pass


# --- cuneta -------------------------------------------------------------------
def test_cuneta_cumple():
    r = CU.comprobar_cuneta(DATOS["cunetas"][0], 0.1524)
    assert r["veredicto"] == "CUMPLE", r["errores"]
    assert r["calado_normal_m"] < r["seccion"]["profundidad_m"]


def test_cuneta_desborda():
    # caudal enorme para una cuneta pequena -> NO CUMPLE (sin capacidad)
    r = CU.comprobar_cuneta(DATOS["cunetas"][0], 5.0)
    assert r["veredicto"] == "NO CUMPLE", r


def test_cuneta_velocidad_baja():
    # pendiente casi nula -> velocidad por debajo de autolimpieza
    c = dict(DATOS["cunetas"][0]); c["pendiente_long"] = 0.0005
    r = CU.comprobar_cuneta(c, 0.02)
    assert r["veredicto"] == "NO CUMPLE", r


# --- ODT ----------------------------------------------------------------------
def test_odt_cumple():
    r = OD.comprobar_odt(DATOS["odt"][0], 1.2)
    assert r["veredicto"] == "CUMPLE", r["errores"]
    assert r["capacidad_m3_s"] >= r["Q_cuenca_m3_s"]


def test_odt_subdimensionada():
    o = dict(DATOS["odt"][0]); o["D_m"] = 0.40   # < dim minima y poca capacidad
    r = OD.comprobar_odt(o, 3.0)
    assert r["veredicto"] == "NO CUMPLE", r


def test_odt_dim_minima():
    o = dict(DATOS["odt"][0]); o["D_m"] = 1.00   # capacidad sobrada pero < 1.8 m
    r = OD.comprobar_odt(o, 0.3)
    assert r["veredicto"] == "NO CUMPLE"
    assert any("minima" in e for e in r["errores"]), r["errores"]


# --- run_all / verificacion + relleno del gancho ------------------------------
def test_run_all_rellena_gancho_y_cumple():
    m2, res = R.dimensionar(MODELO_BASE, DATOS, tr_cuneta=25, tr_odt=100)
    ver = V.verificar(m2, res)
    assert ver["veredicto"] == "CUMPLE", ver["errores"]
    assert m2["drenaje"] is not None
    assert len(m2["drenaje"]["cunetas"]) == 1 and len(m2["drenaje"]["odt"]) == 1
    # solo AÑADE claves: no destruye las existentes
    assert "alineacion" in m2 and m2["terreno"] is None and m2["firme"] is None


def test_run_all_no_inplace_preserva_original():
    R.dimensionar(MODELO_BASE, DATOS)
    assert "drenaje" not in MODELO_BASE  # original intacto


def test_cuenca_inexistente_error():
    datos = {"cuencas": [], "cunetas": [dict(DATOS["cunetas"][0])], "odt": []}
    try:
        R.dimensionar(MODELO_BASE, datos)
        assert False, "deberia fallar por cuenca inexistente"
    except ValueError:
        pass


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
