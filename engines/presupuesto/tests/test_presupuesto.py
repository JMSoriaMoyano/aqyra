"""El motor reproduce el oráculo GOL-PRE-01 desde el modelo neutro (sin IFC).

Contract-first: si algo discrepa, se investiga el ENGINE, jamás el expected.
"""
import json
from pathlib import Path

from aqyra_presupuesto import presupuestar

REPO = Path(__file__).resolve().parents[3]
GOLDEN = REPO / "packages" / "golden" / "C5" / "GOL-PRE-01"


def _cargar_pack(familia, id_, ver):
    d = REPO / "data" / "packs" / familia / id_ / ver
    man = json.loads((d / "pack.json").read_text(encoding="utf-8"))
    return json.loads((d / man["contenido"]["fichero"]).read_text(encoding="utf-8"))


def _presupuesto():
    entrada = json.loads((GOLDEN / "entrada.json").read_text(encoding="utf-8"))
    criterio = _cargar_pack("criterio", "AQ", "v1")
    banco = _cargar_pack("banco", "AQ-DEMO", "v1")
    return presupuestar(entrada["modelo"], criterio, banco, entrada["parametros"]), entrada


def test_resumen_pem_pec():
    pres, _ = _presupuesto()
    r = pres["resumen"]
    assert r["PEM"] == 7022.53
    assert r["gg"] == 912.93
    assert r["bi"] == 421.35
    assert r["base"] == 8356.81
    assert r["iva"] == 1754.93
    assert r["PEC"] == 10111.74


def test_partidas_reproducen_el_oraculo():
    pres, _ = _presupuesto()
    exp = json.loads((GOLDEN / "expected.json").read_text(encoding="utf-8"))["presupuesto"]
    got = {p["codigo"]: p for p in pres["estado_mediciones"]}
    want = {p["codigo"]: p for p in exp["estado_mediciones"]}
    assert set(got) == set(want)
    for cod, w in want.items():
        g = got[cod]
        assert g["capitulo"] == w["capitulo"], cod
        assert g["unidad"] == w["unidad"], cod
        assert abs(g["cantidad"] - w["cantidad"]) <= 0.005 * max(1.0, abs(w["cantidad"])), cod
        assert g["precio_unitario"] == w["precio_unitario"], cod
        assert abs(g["importe"] - w["importe"]) <= 0.01, cod
        assert g["origen"] == w["origen"], cod
        assert set(g["trazabilidad"]) == set(w["trazabilidad"]), cod


def test_un_objeto_varias_partidas():
    pres, _ = _presupuesto()
    codigos = {p["codigo"] for p in pres["estado_mediciones"]}
    # cada muro genera fábrica + enfoscado + pintura
    assert {"FAB010", "REV010", "PIN010"} <= codigos
    por = {p["codigo"]: p for p in pres["estado_mediciones"]}
    assert por["FAB010"]["cantidad"] == 33.9   # 15.90 + 18.00 (1 cara)
    assert por["REV010"]["cantidad"] == 67.8   # x2 caras
    assert por["PIN010"]["cantidad"] == 67.8


def test_sys_por_ratio_es_2pct_del_pem_medible():
    pres, _ = _presupuesto()
    por = {p["codigo"]: p for p in pres["estado_mediciones"]}
    sys010 = por["SYS010"]
    assert sys010["origen"] == "regla"
    assert sys010["trazabilidad"] == []
    pem_medible = sum(p["importe"] for p in pres["estado_mediciones"] if p["origen"] == "modelo")
    assert abs(sys010["importe"] - round(0.02 * pem_medible, 2)) <= 0.01


def test_cuadros_coherentes():
    pres, _ = _presupuesto()
    cp1 = {c["codigo"]: c for c in pres["cuadro_precios_1"]}
    cp2 = {c["codigo"]: c for c in pres["cuadro_precios_2"]}
    for cod, c2 in cp2.items():
        suma = sum(x["subtotal"] for x in c2["componentes"]) + c2["costes_indirectos"]
        assert abs(c2["precio_total"] - suma) <= 0.01, cod
        assert abs(c2["precio_total"] - cp1[cod]["precio"]) <= 0.01, cod


def test_num_a_letra():
    from aqyra_presupuesto import num_a_letra
    assert num_a_letra(178.19) == "CIENTO SETENTA Y OCHO CON DIECINUEVE CENTIMOS"
    assert num_a_letra(6.7) == "SEIS CON SETENTA CENTIMOS"
    assert num_a_letra(231.75) == "DOSCIENTOS TREINTA Y UNO CON SETENTA Y CINCO CENTIMOS"


def test_descripciones_ricas_del_banco_viajan_a_la_partida():
    """Slice A (D-RB-1): el banco gana `resumen` (corto) + `texto` (ampliado). El engine mapea
    descripcion=resumen (fallback a la descripcion previa) y ARRASTRA `texto` a estado_mediciones
    (aditivo). Coste intacto (PEM/PEC en el test de arriba); S&S (origen=regla) no tiene banco."""
    pres, _ = _presupuesto()
    banco = _cargar_pack("banco", "AQ-DEMO", "v1")
    bd = {p["codigo"]: p for p in banco["partidas"]}
    for p in pres["estado_mediciones"]:
        if p["origen"] == "modelo":
            b = bd[p["codigo"]]
            assert p["descripcion"] == b["resumen"], p["codigo"]      # descripcion de tabla = resumen (corto)
            assert p.get("texto") == b["texto"], p["codigo"]          # texto ampliado arrastrado literal
            assert len(p["texto"]) > len(p["descripcion"]), p["codigo"]
    sys010 = next(p for p in pres["estado_mediciones"] if p["codigo"] == "SYS010")
    assert "texto" not in sys010                                       # origen=regla: sin banco, sin texto


def test_descripcion_fallback_sin_resumen():
    """Compatibilidad: un banco v0 SIN `resumen` sigue usando su `descripcion` (no rompe)."""
    from aqyra_presupuesto import presupuestar
    entrada = json.loads((GOLDEN / "entrada.json").read_text(encoding="utf-8"))
    criterio = _cargar_pack("criterio", "AQ", "v1")
    banco = _cargar_pack("banco", "AQ-DEMO", "v1")
    for p in banco["partidas"]:
        p.pop("resumen", None)
        p.pop("texto", None)
    pres = presupuestar(entrada["modelo"], criterio, banco, entrada["parametros"])
    bd = {p["codigo"]: p for p in banco["partidas"]}
    for p in pres["estado_mediciones"]:
        if p["origen"] == "modelo":
            assert p["descripcion"] == bd[p["codigo"]]["descripcion"], p["codigo"]
            assert "texto" not in p, p["codigo"]


# ------------------------------------------------------------------ Slice B (D-RB-5..8): estructura_capitulos
def _presupuesto_con(estructura):
    entrada = json.loads((GOLDEN / "entrada.json").read_text(encoding="utf-8"))
    criterio = _cargar_pack("criterio", "AQ", "v1")
    banco = _cargar_pack("banco", "AQ-DEMO", "v1")
    par = dict(entrada["parametros"])
    if estructura:
        par["estructura_capitulos"] = estructura
    return presupuestar(entrada["modelo"], criterio, banco, par)


def test_estructura_capitulos_default_es_catalogo():
    """Sin estructura_capitulos (o 'catalogo'): WBS del engine (C01..C06) — GOL-PRE-01 byte-idéntico."""
    caps = [c["codigo"] for c in _presupuesto_con(None)["resumen"]["capitulos"]]
    assert caps == ["C01", "C02", "C03", "C04", "C05", "C06"]
    assert [c["codigo"] for c in _presupuesto_con("catalogo")["resumen"]["capitulos"]] == caps


def test_estructura_capitulos_uniclass():
    """'uniclass' agrupa por grupo EF de 2.º nivel (D-RB-5/6); coste intacto; S&S -> SIN."""
    pres = _presupuesto_con("uniclass")
    caps = {c["codigo"]: c for c in pres["resumen"]["capitulos"]}
    assert set(caps) == {"EF_20", "EF_25", "EF_30", "SIN"}
    assert set(caps["EF_20"]["partidas"]) == {"EHS010", "CSZ010"}
    assert set(caps["EF_25"]["partidas"]) == {"FAB010", "REV010", "PIN010", "PPM010"}
    assert set(caps["EF_30"]["partidas"]) == {"EHL010"}
    assert caps["SIN"]["partidas"] == ["SYS010"]
    assert pres["resumen"]["PEM"] == 7022.53 and pres["resumen"]["PEC"] == 10111.74
    assert round(sum(c["importe"] for c in caps.values()), 2) == 7022.53


def test_estructura_capitulos_gubim():
    """'gubim' agrupa por 1.er segmento del código GuBIM (D-RB-7); coste intacto."""
    pres = _presupuesto_con("gubim")
    caps = {c["codigo"]: c for c in pres["resumen"]["capitulos"]}
    assert set(caps) == {"10", "20", "30", "40", "50", "SIN"}
    assert pres["resumen"]["PEM"] == 7022.53 and pres["resumen"]["PEC"] == 10111.74
    assert round(sum(c["importe"] for c in caps.values()), 2) == 7022.53


def test_estructura_capitulos_no_mueve_el_coste():
    """Reagrupar NO cambia importes de partida ni PEM/PEC (solo el capítulo asignado)."""
    cat = _presupuesto_con("catalogo")
    uni = _presupuesto_con("uniclass")
    imp = lambda s: {p["codigo"]: p["importe"] for p in s["estado_mediciones"]}
    assert imp(cat) == imp(uni)
    assert cat["resumen"]["PEM"] == uni["resumen"]["PEM"] == 7022.53
