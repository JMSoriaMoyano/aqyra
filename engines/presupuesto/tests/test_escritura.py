"""escribir_coste escribe el modelo de coste nativo de IFC y es DETERMINISTA (D14).

Requiere ifcopenshell (como test_medicion). Usa ARQ.ifc como derivado stand-in; el flujo federado
completo lo valida la golden GOL-PRE-02.
"""
import json
from pathlib import Path

import pytest

pytest.importorskip("ifcopenshell")

from aqyra_presupuesto import escribir_coste, presupuestar  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
GOLDEN = REPO / "packages" / "golden" / "C5" / "GOL-PRE-01"


def _presupuesto():
    entrada = json.loads((GOLDEN / "entrada.json").read_text(encoding="utf-8"))
    d = REPO / "data" / "packs"
    crit = json.loads((d / "criterio" / "AQ" / "v1" / "criterio.json").read_text(encoding="utf-8"))
    banco = json.loads((d / "banco" / "AQ-DEMO" / "v1" / "banco.json").read_text(encoding="utf-8"))
    p = presupuestar(entrada["modelo"], crit, banco, entrada["parametros"])
    p["proyecto"] = entrada.get("proyecto")
    return p


def test_determinista_y_cost_schedule(tmp_path):
    import ifcopenshell

    pres = _presupuesto()
    derivado = GOLDEN / "entrada" / "ARQ.ifc"
    r1 = escribir_coste(pres, derivado, tmp_path / "a" / "5d.ifc")
    r2 = escribir_coste(pres, derivado, tmp_path / "b" / "5d.ifc")
    assert r1["md5"] == r2["md5"]  # bytes idénticos (mismo basename, dirs distintas)

    f = ifcopenshell.open(str(tmp_path / "a" / "5d.ifc"))
    assert len(f.by_type("IfcCostSchedule")) == 1
    assert any(getattr(u, "Currency", None) == "EUR" for u in f.by_type("IfcMonetaryUnit"))
    items = {ci.Identification: ci for ci in f.by_type("IfcCostItem")
             if getattr(ci, "Identification", None)}
    fab = items["FAB010"]
    av = fab.CostValues[0].AppliedValue
    assert abs(float(getattr(av, "wrappedValue", av)) - 1065.14) <= 0.01
    # RESUMEN lleva PEM..PEC
    assert "RESUMEN" in items and len(items["RESUMEN"].CostValues) >= 6
