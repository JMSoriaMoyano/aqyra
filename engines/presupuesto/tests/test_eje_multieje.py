"""E1.2 (D16-D19) — el engine se generaliza a un eje SIN regresión del coste.

- eje="coste" (default): salida byte-idéntica al C5 previo → no emite `valores` (D16); GOL-PRE-01
  intacta (verificada en test_presupuesto.py).
- eje!="coste": cada partida gana `valores[eje]` etiquetado con unidad + banco (D19, espejo +
  valor etiquetado); precio_unitario/importe reflejan la magnitud del eje (D19).

Contract-first: si algo discrepa, se investiga el ENGINE, jamás el expected.
"""
import copy
import json
from pathlib import Path

from aqyra_presupuesto import presupuestar

REPO = Path(__file__).resolve().parents[3]
GOLDEN = REPO / "packages" / "golden" / "C5" / "GOL-PRE-01"


def _cargar_pack(familia, id_, ver):
    d = REPO / "data" / "packs" / familia / id_ / ver
    man = json.loads((d / "pack.json").read_text(encoding="utf-8"))
    return json.loads((d / man["contenido"]["fichero"]).read_text(encoding="utf-8"))


def _entradas():
    entrada = json.loads((GOLDEN / "entrada.json").read_text(encoding="utf-8"))
    criterio = _cargar_pack("criterio", "AQ", "v1")
    banco = _cargar_pack("banco", "AQ-DEMO", "v1")
    return entrada, criterio, banco


def test_eje_coste_por_defecto_no_emite_valores():
    """El eje coste (default) NO emite `valores`: la salida es la del C5 previo (D16)."""
    entrada, criterio, banco = _entradas()
    pres = presupuestar(entrada["modelo"], criterio, banco, entrada["parametros"])
    assert all("valores" not in p for p in pres["estado_mediciones"])
    assert pres["resumen"]["PEM"] == 7022.53
    assert pres["resumen"]["PEC"] == 10111.74


def test_eje_coste_explicito_igual_al_default():
    """Pedir eje='coste' explícito produce exactamente el mismo objeto que el default."""
    entrada, criterio, banco = _entradas()
    por_defecto = presupuestar(entrada["modelo"], criterio, banco, entrada["parametros"])
    explicito = presupuestar(
        entrada["modelo"], criterio, banco, dict(entrada["parametros"], eje="coste")
    )
    assert explicito == por_defecto


def test_eje_no_coste_rellena_valores_etiquetado():
    """Un eje NO-coste (banco de otro eje) rellena valores[eje] etiquetado (D19)."""
    entrada, criterio, banco = _entradas()
    # banco de juguete de otro eje: reusa códigos/precios de AQ-DEMO como factores kgCO2e
    banco_carbono = copy.deepcopy(banco)
    banco_carbono["banco"] = "generico/v1"
    banco_carbono["ref"] = "banco-carbono/generico/v1"
    banco_carbono["unidad_eje"] = "kgCO2e"
    pres = presupuestar(
        entrada["modelo"], criterio, banco_carbono, dict(entrada["parametros"], eje="carbono")
    )
    modelo = [p for p in pres["estado_mediciones"] if p["origen"] == "modelo"]
    regla = [p for p in pres["estado_mediciones"] if p["origen"] == "regla"]
    assert modelo, "hay partidas origen=modelo"
    for p in modelo:
        v = p["valores"]["carbono"]
        assert v["unidad"] == "kgCO2e"
        assert v["banco"] == "banco-carbono/generico/v1"
        assert v["origen"] == "modelo"
        # D19: espejo — precio_unitario/importe reflejan la magnitud del eje
        assert v["unitario"] == p["precio_unitario"]
        assert v["total"] == p["importe"]
    # partida sin geometría (origen=regla): eje etiquetado, SIN banco
    for p in regla:
        v = p["valores"]["carbono"]
        assert v["unidad"] == "kgCO2e"
        assert v["origen"] == "regla"
        assert "banco" not in v


def test_eje_no_coste_no_altera_el_mapeo_ni_las_cantidades():
    """El mapeo clase→partida y las cantidades no cambian entre ejes: solo el envoltorio de valor."""
    entrada, criterio, banco = _entradas()
    coste = presupuestar(entrada["modelo"], criterio, banco, entrada["parametros"])
    banco_x = copy.deepcopy(banco)
    banco_x["unidad_eje"] = "kgCO2e"
    otro = presupuestar(
        entrada["modelo"], criterio, banco_x, dict(entrada["parametros"], eje="carbono")
    )
    clave = lambda pres: [(p["codigo"], p["cantidad"], p["trazabilidad"]) for p in pres["estado_mediciones"]]
    assert clave(coste) == clave(otro)
