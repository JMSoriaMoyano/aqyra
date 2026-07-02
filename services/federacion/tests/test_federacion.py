"""Tests de unidad del service C4 (v0): conformidad de esquemas de sus salidas,
semántica sobre el caso golden C4-FED-01 (sin duplicar la golden: el recompute
exacto contra expected.json es del runner) y determinismo.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve()
REPO = _HERE.parents[3]                      # aqyra/
SRC = _HERE.parents[1] / "src"
CASO = REPO / "packages" / "golden" / "C4" / "C4-FED-01"
CONTRATOS = REPO / "packages" / "contracts" / "C4-federacion"
PACK = REPO / "data" / "packs" / "ids" / "proyecto-piloto" / "v1"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aqyra_federacion import federar_fichero, validar, __version__  # noqa: E402
from aqyra_federacion import ids_min  # noqa: E402


def _esquema(nombre: str) -> dict:
    return json.loads((CONTRATOS / nombre).read_text(encoding="utf-8"))


def _valida(instancia: dict, esquema: dict) -> None:
    from jsonschema import Draft202012Validator
    errores = list(Draft202012Validator(esquema).iter_errors(instancia))
    assert not errores, f"no conforma: {errores[0].message}"


@pytest.fixture(scope="module")
def manifiesto() -> dict:
    return federar_fichero(CASO / "reglas.json")


@pytest.fixture(scope="module")
def informe(manifiesto) -> dict:
    return validar(manifiesto, PACK, CASO)


# --------------------------- federar() --------------------------------------
def test_manifiesto_conforma_esquema(manifiesto):
    _valida(manifiesto, _esquema("maestro-manifiesto.schema.json"))


def test_manifiesto_semantica(manifiesto):
    por_id = {m["id"]: m for m in manifiesto["modelos"]}
    assert por_id["ARQ"]["n_elementos"] == 6          # incluye IfcOpeningElement
    assert por_id["EST"]["n_elementos"] == 7
    assert por_id["ARQ"]["md5"] == "653a359154112146d82ca02de0fde2ee"
    assert por_id["EST"]["md5"] == "b84cb79c4a7cf4b560148340bc8dc305"
    assert por_id["ARQ"]["transformacion"]["traslacion"] == [337000.0, 4610000.0, 700.0]
    assert manifiesto["guids"]["politica"] == "preservados"
    assert manifiesto["procedencia"]["generado_por"] == f"services/federacion {__version__}"


def test_estructura_espacial_unificada(manifiesto):
    ag = manifiesto["estructura_espacial"]["agregados"]
    por_clave = {(a["nivel"], a["nombre"]): a["aportado_por"] for a in ag}
    assert len(ag) == 7                                # 1 Project + Site + Building + 4 Storey
    assert por_clave[("Project", manifiesto["proyecto"])] == ["ARQ", "EST"]
    assert por_clave[("Site", "Emplazamiento")] == ["ARQ", "EST"]      # unificado por nombre
    assert por_clave[("Building", "Edificio")] == ["ARQ", "EST"]
    assert por_clave[("Storey", "Planta Baja")] == ["ARQ"]             # sin colisión: separado
    assert por_clave[("Storey", "Nivel 00")] == ["EST"]
    assert [a["nivel"] for a in ag] == ["Project", "Site", "Building"] + ["Storey"] * 4


def test_integridad_md5(tmp_path):
    reglas = json.loads((CASO / "reglas.json").read_text(encoding="utf-8"))
    (tmp_path / "entrada").mkdir()
    for m in reglas["modelos"]:
        (tmp_path / m["fichero"]).write_bytes((CASO / m["fichero"]).read_bytes())
    reglas["modelos"][0]["md5"] = "0" * 32             # declarado ≠ real
    from aqyra_federacion import federar
    with pytest.raises(ValueError, match="integridad"):
        federar(reglas, tmp_path)


# --------------------------- ids_min ----------------------------------------
def test_ids_min_parse():
    specs = ids_min.parse_ids(PACK / "requisitos.ids")
    assert [s.id for s in specs] == ["R1-CLASIF", "R2-EXTERIOR", "R3-MATERIAL", "R5-PLANTAS"]
    assert specs[0].aplicabilidad == ("IfcColumn|IfcWall|IfcSlab|IfcFooting|IfcDoor"
                                      "|IfcTransportElement")
    assert [r.tipo for r in specs[0].requisitos] == ["classification", "classification"]
    assert specs[3].requisitos[0].params["patron"] == "Planta .*"


# --------------------------- validar() --------------------------------------
def test_informe_conforma_esquema(informe):
    _valida(informe, _esquema("informe-qa.schema.json"))


def test_informe_semantica(informe):
    por_id = {r["id"]: r for r in informe["requisitos"]}
    assert list(por_id) == ["R1-CLASIF", "R2-EXTERIOR", "R3-MATERIAL",
                            "R4-GEORREF", "R5-PLANTAS"]     # orden por id
    assert por_id["R1-CLASIF"]["resultado"] == "pass"
    assert por_id["R2-EXTERIOR"]["por_modelo"]["EST"]["resultado"] == "no-aplica"
    assert por_id["R3-MATERIAL"]["por_modelo"]["ARQ"]["n_comprobados"] == 4  # sin la puerta
    assert por_id["R4-GEORREF"]["resultado"] == "fail"
    assert por_id["R4-GEORREF"]["origen"] == "modulo"
    assert por_id["R5-PLANTAS"]["por_modelo"]["EST"]["n_fallos"] == 2
    assert informe["veredicto"] == "no-conforme"
    assert informe["estados"]["maestro"] == "S1"
    assert informe["bcf"] == {"estandar": "BCF", "version": "3.0", "emitido": False}


def test_incidencias(informe):
    incs = informe["incidencias"]
    assert [i["id"] for i in incs] == ["INC-01", "INC-02", "INC-03"]
    assert [(i["requisito"], i["modelo"]) for i in incs] == [
        ("R4-GEORREF", "ARQ"), ("R4-GEORREF", "EST"), ("R5-PLANTAS", "EST")]
    assert incs[0]["guids"] == [] and incs[0]["severidad"] == "mayor"
    assert incs[2]["guids"] == ["3OM3R50xH9rQrxdF_D157W", "1_IR0JcG90ghN9CC8WB7E9"]
    assert incs[2]["severidad"] == "menor"


# --------------------------- mantener-separada (D22, 1.4) -------------------
CASO05 = REPO / "packages" / "golden" / "C4" / "C4-FED-05"


def test_mantener_separada_nodos_por_modelo():
    m = federar_fichero(CASO05 / "reglas.json")
    ag = m["estructura_espacial"]["agregados"]
    assert m["estructura_espacial"]["politica"] == "mantenida-separada"
    no_project = [a for a in ag if a["nivel"] != "Project"]
    assert all(len(a["aportado_por"]) == 1 for a in no_project)   # nada se funde
    nombres = [(a["nivel"], a["nombre"], a["aportado_por"][0]) for a in no_project]
    assert ("Site", "Emplazamiento", "ARQ") in nombres            # el mismo nombre,
    assert ("Site", "Emplazamiento", "EST") in nombres            # POR MODELO
    assert ("Building", "Edificio", "ARQ") in nombres
    assert ("Building", "Edificio", "EST") in nombres
    assert len(ag) == 1 + 2 + 2 + 4    # Project único + 2 Site + 2 Building + 4 Storey
    proyecto = [a for a in ag if a["nivel"] == "Project"]
    assert proyecto[0]["aportado_por"] == ["ARQ", "EST"]          # único por definición


def test_politica_desconocida_rechazada(tmp_path):
    reglas = json.loads((CASO / "reglas.json").read_text(encoding="utf-8"))
    (tmp_path / "entrada").mkdir()
    for m in reglas["modelos"]:
        (tmp_path / m["fichero"]).write_bytes((CASO / m["fichero"]).read_bytes())
    reglas["deduplicacion"]["estructura_espacial"] = "fundir-todo"
    from aqyra_federacion import federar
    with pytest.raises(ValueError, match="no soportada"):
        federar(reglas, tmp_path)


def test_estados_heterogeneos_min(tmp_path):
    reglas = json.loads((CASO / "reglas.json").read_text(encoding="utf-8"))
    (tmp_path / "entrada").mkdir()
    for m in reglas["modelos"]:
        (tmp_path / m["fichero"]).write_bytes((CASO / m["fichero"]).read_bytes())
    reglas["modelos"][0]["estado_entrada"] = "S1"
    reglas["modelos"][1]["estado_entrada"] = "S3"
    from aqyra_federacion import federar
    m = federar(reglas, tmp_path)
    inf = validar(m, PACK, tmp_path)
    assert inf["estados"] == {"por_modelo": {"ARQ": "S1", "EST": "S3"},
                              "maestro": "S1"}                    # min(S), política de v0


# --------------------------- determinismo -----------------------------------
def test_determinista():
    a = federar_fichero(CASO / "reglas.json")
    b = federar_fichero(CASO / "reglas.json")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    ia = validar(a, PACK, CASO)
    ib = validar(b, PACK, CASO)
    assert json.dumps(ia, sort_keys=True) == json.dumps(ib, sort_keys=True)
