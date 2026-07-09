"""E3 (D39-D44) — el eje CARBONO: valores.carbono + etapas A1A3/A4A5 con invariante Σ etapas = total.

Texto puro (usa el modelo neutro inline de GOL-PRE-01 + el pack banco-carbono, sin ifcopenshell):
- eje="coste" (default): salida byte-idéntica (no emite valores); GOL-PRE-01 intacta.
- eje="carbono": cada partida origen=modelo gana valores.carbono con etapas (Σ etapas = total EXACTO);
  la partida origen=regla (S&S) va etiquetada SIN etapas ni banco. La salida conforma el esquema C5.

Contract-first: si algo discrepa, se investiga el ENGINE, jamás el expected/el esquema.
"""
import json
from decimal import Decimal
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
    banco_carbono = _cargar_pack("banco-carbono", "generico", "v1")
    return entrada, criterio, banco_carbono


def test_coste_intacto_sin_valores():
    """El eje coste (default) sigue byte-idéntico: PEM 7022.53 y sin `valores`."""
    entrada, criterio, _ = _entradas()
    banco = _cargar_pack("banco", "AQ-DEMO", "v1")
    pres = presupuestar(entrada["modelo"], criterio, banco, entrada["parametros"])
    assert all("valores" not in p for p in pres["estado_mediciones"])
    assert pres["resumen"]["PEM"] == 7022.53 and pres["resumen"]["PEC"] == 10111.74


def test_carbono_emite_valores_con_etapas_invariante():
    """Cada partida origen=modelo lleva valores.carbono con etapas A1A3/A4A5 y Σ etapas = total EXACTO."""
    entrada, criterio, banco_carbono = _entradas()
    params = dict(entrada["parametros"], eje="carbono", gg_pct=0, bi_pct=0, iva_pct=0, moneda="kgCO2e")
    pres = presupuestar(entrada["modelo"], criterio, banco_carbono, params)
    modelo = [p for p in pres["estado_mediciones"] if p["origen"] == "modelo"]
    regla = [p for p in pres["estado_mediciones"] if p["origen"] == "regla"]
    assert modelo, "hay partidas origen=modelo"
    for p in modelo:
        v = p["valores"]["carbono"]
        assert v["unidad"] == "kgCO2e"
        assert v["banco"] == "banco-carbono/generico/v1"
        assert v["origen"] == "modelo"
        assert v["total"] == p["importe"] and v["unitario"] == p["precio_unitario"]  # espejo D19
        et = v["etapas"]
        assert set(et) == {"A1A3", "A4A5"}
        assert Decimal(str(et["A1A3"])) + Decimal(str(et["A4A5"])) == Decimal(str(v["total"]))  # D18
    for p in regla:  # S&S: etiquetado, SIN etapas ni banco
        v = p["valores"]["carbono"]
        assert v["unidad"] == "kgCO2e" and v["origen"] == "regla"
        assert "banco" not in v and "etapas" not in v


def test_carbono_conforma_esquema_sin_tocarlo():
    """La salida de carbono conforma salida-presupuesto.schema.json (forward-open, esquema intacto)."""
    from jsonschema import Draft202012Validator
    entrada, criterio, banco_carbono = _entradas()
    schema = json.loads((REPO / "packages" / "contracts" / "C5-presupuesto"
                         / "salida-presupuesto.schema.json").read_text(encoding="utf-8"))
    params = dict(entrada["parametros"], eje="carbono", gg_pct=0, bi_pct=0, iva_pct=0, moneda="kgCO2e")
    pres = presupuestar(entrada["modelo"], criterio, banco_carbono, params)
    errs = sorted(Draft202012Validator(schema).iter_errors(pres), key=str)
    assert not errs, f"no conforma: {[e.message for e in errs[:2]]}"


def test_carbono_resumen_totaliza_el_eje():
    """El resumen del run de carbono totaliza el eje (PEM = Σ importes espejados)."""
    entrada, criterio, banco_carbono = _entradas()
    params = dict(entrada["parametros"], eje="carbono", gg_pct=0, bi_pct=0, iva_pct=0, moneda="kgCO2e")
    pres = presupuestar(entrada["modelo"], criterio, banco_carbono, params)
    assert pres["resumen"]["PEM"] == 8032.4
