"""El parser (módulo 1) mide desde el IFC(+Qto): la medición NACE del modelo (D7).

Requiere ifcopenshell (como los tests del engine C3). Abre las fixtures congeladas del golden y
comprueba que reproduce las cantidades que el modelo neutro declara + que presupuestar sobre el
modelo MEDIDO reproduce el PEM/PEC del oráculo.
"""
import json
from pathlib import Path

import pytest

pytest.importorskip("ifcopenshell")

from aqyra_presupuesto import medir, presupuestar  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
GOLDEN = REPO / "packages" / "golden" / "C5" / "GOL-PRE-01"


def _fuentes():
    entrada = json.loads((GOLDEN / "entrada.json").read_text(encoding="utf-8"))
    fuentes = []
    for m in entrada["modelo"]["fuente_maestro"]["modelos"]:
        fuentes.append({"id": m["id"], "disciplina": m.get("disciplina"),
                        "path": GOLDEN / m["fichero"], "fichero": m["fichero"]})
    return fuentes, entrada


def test_parser_lee_qto_de_los_muros():
    fuentes, _ = _fuentes()
    modelo = medir(fuentes)
    por_guid = {o["guid"]: o for o in modelo["objetos"]}
    muro = por_guid["0EAm14JNX7Hu9QtYUgOaK4"]  # M-Fachada-Sur (con hueco)
    mags = {c["magnitud"]: c["valor"] for c in muro["cantidades"]}
    assert mags["NetSideArea"] == 15.9
    assert mags["GrossSideArea"] == 18.0
    assert muro.get("_huecos", 0) >= 1  # el hueco de la puerta se detecta (IfcRelVoidsElement)


def test_medicion_nace_del_modelo_reproduce_cantidades():
    fuentes, entrada = _fuentes()
    modelo = medir(fuentes)
    got = {o["guid"]: {c["magnitud"]: c["valor"] for c in o["cantidades"]} for o in modelo["objetos"]}
    for obj in entrada["modelo"]["objetos"]:
        g = obj["guid"]
        assert g in got, g
        for c in obj["cantidades"]:
            mag = c.get("magnitud")
            if mag in ("conteo",):
                continue
            assert mag in got[g], (g, mag)
            assert abs(got[g][mag] - c["valor"]) <= 0.005 * max(1.0, abs(c["valor"])), (g, mag)


def test_presupuesto_desde_el_modelo_medido():
    fuentes, entrada = _fuentes()
    modelo = medir(fuentes)
    d = REPO / "data" / "packs"
    criterio = json.loads((d / "criterio" / "AQ" / "v1" / "criterio.json").read_text(encoding="utf-8"))
    banco = json.loads((d / "banco" / "AQ-DEMO" / "v1" / "banco.json").read_text(encoding="utf-8"))
    pres = presupuestar(modelo, criterio, banco, entrada["parametros"])
    assert pres["resumen"]["PEM"] == 7022.53
    assert pres["resumen"]["PEC"] == 10111.74
