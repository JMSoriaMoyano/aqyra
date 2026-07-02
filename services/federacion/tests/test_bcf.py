"""Tests de la emisión BCF 3.0 (tarea 1.2, D11–D13): estructura del contenedor,
XML bien formado, determinismo doble-run, GUIDs uuid5 estables, viewpoint solo
con GUIDs de elemento y SIN cámara (D6), informe de entrada no mutado.
El recompute exacto contra expected.json (C4-FED-02) es del runner, no de aquí.
"""
from __future__ import annotations

import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve()
REPO = _HERE.parents[3]                      # aqyra/
SRC = _HERE.parents[1] / "src"
CASO = REPO / "packages" / "golden" / "C4" / "C4-FED-01"
PACK = REPO / "data" / "packs" / "ids" / "proyecto-piloto" / "v1"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aqyra_federacion import federar_fichero, validar, emitir_bcf  # noqa: E402
from aqyra_federacion.bcf import guid_topic, guid_viewpoint, empaquetar_bcfzip  # noqa: E402

GEN = {"caso": "TEST", "autor": "services/federacion test", "fecha": "2026-07-02T00:00:00Z"}


@pytest.fixture(scope="module")
def informe() -> dict:
    man = federar_fichero(CASO / "reglas.json")
    return validar(man, PACK, CASO)


@pytest.fixture()
def emitido(informe, tmp_path):
    carpeta = tmp_path / "bcf"
    inf = emitir_bcf(informe, carpeta, caso=GEN["caso"], autor=GEN["autor"],
                     fecha=GEN["fecha"])
    return carpeta, inf


def _arbol(carpeta: Path) -> dict[str, str]:
    return {p.relative_to(carpeta).as_posix(): hashlib.md5(p.read_bytes()).hexdigest()
            for p in sorted(carpeta.rglob("*")) if p.is_file()}


# --------------------------- contenedor (D12) --------------------------------
def test_estructura_contenedor(emitido, informe):
    carpeta, inf = emitido
    assert (carpeta / "bcf.version").exists()
    topics = sorted(d.name for d in carpeta.iterdir() if d.is_dir())
    assert len(topics) == len(informe["incidencias"]) == 3   # un topic por incidencia
    for t in topics:
        assert (carpeta / t / "markup.bcf").exists()
    # viewpoint SOLO donde la incidencia trae GUIDs de elemento (INC-03)
    con_vp = [t for t in topics if (carpeta / t / "viewpoint.bcfv").exists()]
    assert con_vp == [guid_topic(GEN["caso"], "INC-03")]


def test_xml_bien_formado_y_version(emitido):
    carpeta, _ = emitido
    for p in carpeta.rglob("*"):
        if p.is_file():
            ET.parse(str(p))                                  # no levanta
    v = ET.parse(str(carpeta / "bcf.version")).getroot()
    assert v.tag == "Version" and v.get("VersionId") == "3.0"


# --------------------------- markup (BCF 3.0) ---------------------------------
def test_markup_topic(emitido, informe):
    carpeta, _ = emitido
    inc = informe["incidencias"][2]                           # INC-03 (R5, con GUIDs)
    tg = guid_topic(GEN["caso"], "INC-03")
    topic = ET.parse(str(carpeta / tg / "markup.bcf")).getroot().find("Topic")
    assert topic.get("Guid") == tg
    assert topic.get("TopicType") == "Issue" and topic.get("TopicStatus") == "Open"
    assert topic.findtext("Title") == inc["titulo"]
    assert topic.findtext("Priority") == inc["severidad"]     # Priority ← severidad literal
    labels = [l.text for l in topic.find("Labels")]
    assert inc["requisito"] in labels and f"modelo:{inc['modelo']}" in labels
    assert topic.findtext("CreationDate") == GEN["fecha"]
    assert topic.findtext("CreationAuthor") == GEN["autor"]
    vp = topic.find("Viewpoints/ViewPoint")
    assert vp.get("Guid") == guid_viewpoint(GEN["caso"], "INC-03")
    assert vp.findtext("Viewpoint") == "viewpoint.bcfv"


def test_markup_sin_viewpoint_en_reglas_de_proyecto(emitido):
    carpeta, _ = emitido
    tg = guid_topic(GEN["caso"], "INC-01")                    # R4: guids=[]
    topic = ET.parse(str(carpeta / tg / "markup.bcf")).getroot().find("Topic")
    assert topic.find("Viewpoints") is None


# --------------------------- viewpoint (D6: sin cámara) -----------------------
def test_viewpoint_components(emitido, informe):
    carpeta, _ = emitido
    inc = informe["incidencias"][2]
    tg = guid_topic(GEN["caso"], "INC-03")
    root = ET.parse(str(carpeta / tg / "viewpoint.bcfv")).getroot()
    assert root.tag == "VisualizationInfo"
    assert root.get("Guid") == guid_viewpoint(GEN["caso"], "INC-03")
    guids = [c.get("IfcGuid") for c in root.findall("Components/Selection/Component")]
    assert guids == inc["guids"]                              # GUIDs afectados, en orden
    assert root.find("OrthogonalCamera") is None              # SIN cámara en v0 (D6)
    assert root.find("PerspectiveCamera") is None


# --------------------------- determinismo (D13) -------------------------------
def test_determinismo_doble_run(informe, tmp_path):
    a = emitir_bcf(informe, tmp_path / "a", **GEN)
    b = emitir_bcf(informe, tmp_path / "b", **GEN)
    assert _arbol(tmp_path / "a") == _arbol(tmp_path / "b")   # byte a byte (md5)
    assert json.dumps(a, sort_keys=True).replace('"a"', '"x"') == \
           json.dumps(b, sort_keys=True).replace('"b"', '"x"')  # informes iguales salvo carpeta


def test_guids_uuid5_estables():
    # anclados: si esto cambia, cambia el contrato de GUIDs (D13) — decisión con JM
    assert guid_topic("C4-FED-02", "INC-01") == "6dcf89b3-1970-5bf0-aef7-4bb9edc9cd66"
    assert guid_viewpoint("C4-FED-02", "INC-03") == "1e07abfe-6a57-5175-9686-71671e2858d0"
    assert guid_topic("otro-caso", "INC-01") != guid_topic("C4-FED-02", "INC-01")


# --------------------------- informe actualizado (D11) ------------------------
def test_informe_actualizado_y_entrada_intacta(informe, emitido):
    carpeta, inf = emitido
    assert inf["bcf"] == {"estandar": "BCF", "version": "3.0",
                          "emitido": True, "carpeta": "bcf"}
    assert all(i["bcf_topic_guid"] == guid_topic(GEN["caso"], i["id"])
               for i in inf["incidencias"])
    # la entrada NO se muta: emitido=true solo en el informe devuelto
    assert informe["bcf"]["emitido"] is False
    assert all("bcf_topic_guid" not in i for i in informe["incidencias"])


def test_bcfzip_derivado(emitido, tmp_path):
    import zipfile
    carpeta, _ = emitido
    z = empaquetar_bcfzip(carpeta, tmp_path / "caso.bcfzip")
    with zipfile.ZipFile(z) as f:
        assert "bcf.version" in f.namelist()
        assert len(f.namelist()) == len(_arbol(carpeta))
