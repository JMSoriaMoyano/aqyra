"""Tests de orquestación de verificar() sobre un Maestro SINTÉTICO en memoria (sin service).

Construye dos IFC fuente + un "derivado" que los funde preservando los GUIDs (como hace C4) y
un pack mínimo que ejercita los cuatro estados, y comprueba: forma del veredicto, atribución
`por_modelo`, resumen == recuento, regla de veredicto agregado (D4) y el error de evaluador
desconocido. La reproducción del checklist REAL de GOL-CTE-01 la cierra el runner (costura).
"""
import json

import ifcopenshell
import ifcopenshell.guid as guid
import pytest

from aqyra_cumplimiento import verificar
from aqyra_cumplimiento.cumplimiento import _veredicto_global


def _add(f, clase, nombre, g, predefined=None):
    kw = {"GlobalId": g, "Name": nombre}
    if predefined is not None:
        kw["PredefinedType"] = predefined
    return f.create_entity(clase, **kw)


def _write(path, elementos):
    f = ifcopenshell.file(schema="IFC4X3")
    for clase, nombre, g, pred in elementos:
        _add(f, clase, nombre, g, pred)
    f.write(str(path))


PACK = {
    "id": "TEST", "familia": "normativa", "version": "1",
    "contenido": {"fichero": "exigencias.json", "exigencias": []},
}
EXIGENCIAS = {
    "exigencias": [
        {"id": "E-ASC", "documento_basico": "DB-SUA", "apartado": "SUA 9",
         "exigencia": "ascensor", "evaluador": "presencia-tipo-ifc",
         "parametros": {"clase": "IfcTransportElement", "predefined_type": "ELEVATOR"}},
        {"id": "E-RF", "documento_basico": "DB-SI", "apartado": "SI6",
         "exigencia": "resistencia al fuego", "evaluador": "presencia-propiedad-pset",
         "parametros": {"clases": ["IfcColumn", "IfcWall"], "propiedad": "FireRating"}},
        {"id": "E-EVAC", "documento_basico": "DB-SI", "apartado": "SI3",
         "exigencia": "evacuación", "evaluador": "requiere-motor",
         "parametros": {"motivo": "requiere motor de evacuación"}},
        {"id": "E-IND", "documento_basico": "RSCIEI", "apartado": "RD 2267/2004",
         "exigencia": "industrial", "evaluador": "aplica-solo-uso",
         "parametros": {"usos": ["Industrial"]}},
    ]
}


def _maestro(tmp_path):
    ga1, gasc, ge1 = guid.new(), guid.new(), guid.new()
    _write(tmp_path / "ARQ.ifc", [("IfcWall", "M1", ga1, None),
                                  ("IfcTransportElement", "Asc", gasc, "ELEVATOR")])
    _write(tmp_path / "EST.ifc", [("IfcColumn", "P1", ge1, None)])
    _write(tmp_path / "fed.ifc", [("IfcWall", "M1", ga1, None),
                                  ("IfcTransportElement", "Asc", gasc, "ELEVATOR"),
                                  ("IfcColumn", "P1", ge1, None)])
    manifiesto = {"proyecto": "T",
                  "modelos": [{"id": "ARQ", "fichero_origen": "ARQ.ifc"},
                              {"id": "EST", "fichero_origen": "EST.ifc"}],
                  "ifc_derivado": {"fichero": "fed.ifc"}}
    return {"manifiesto": manifiesto, "base_dir": tmp_path,
            "ifc_derivado": tmp_path / "fed.ifc", "proyecto": "Proyecto T"}


def _pack(tmp_path):
    d = tmp_path / "pack"
    d.mkdir()
    (d / "pack.json").write_text(json.dumps(PACK), encoding="utf-8")
    (d / "exigencias.json").write_text(json.dumps(EXIGENCIAS), encoding="utf-8")
    return d


def test_veredicto_reproduce_los_cuatro_estados(tmp_path):
    v = verificar(_maestro(tmp_path), {"principal": "Residencial Vivienda"},
                  {"pais": "España", "municipio": "Jaén"}, _pack(tmp_path))
    por = {e["id"]: e["resultado"] for e in v["exigencias"]}
    assert por == {"E-ASC": "cumple", "E-RF": "no-cumple",
                   "E-EVAC": "no-verificable", "E-IND": "no-aplica"}
    assert v["veredicto"] == "no-conforme"       # hay ≥1 no-cumple (D4)
    assert v["resumen"]["total"] == 4
    assert v["resumen"]["por_resultado"] == {"cumple": 1, "no-cumple": 1,
                                             "no-aplica": 1, "no-verificable": 1}


def test_por_modelo_atribuye_desde_la_procedencia(tmp_path):
    v = verificar(_maestro(tmp_path), {"principal": "Residencial Vivienda"},
                  {"pais": "España"}, _pack(tmp_path))
    rf = next(e for e in v["exigencias"] if e["id"] == "E-RF")
    assert rf["por_modelo"]["ARQ"]["n_comprobados"] == 1   # el muro
    assert rf["por_modelo"]["EST"]["n_comprobados"] == 1   # el pilar


def test_encabezado_y_pack_ecoan(tmp_path):
    v = verificar(_maestro(tmp_path), {"principal": "Residencial Vivienda", "extra": "x"},
                  {"pais": "España", "municipio": "Jaén", "declarado_por": "JM"}, _pack(tmp_path))
    assert v["proyecto"] == "Proyecto T"
    assert v["uso"] == {"principal": "Residencial Vivienda"}      # sin claves extra
    assert "declarado_por" not in v["localizacion"]              # sin metadatos declarativos
    assert v["pack"] == {"familia": "normativa", "id": "TEST", "version": "1",
                         "fichero": "exigencias.json"}


def test_evaluador_desconocido_es_error(tmp_path):
    d = _pack(tmp_path)
    mala = {"exigencias": [{"id": "X", "documento_basico": "DB", "apartado": "a",
                            "exigencia": "x", "evaluador": "inexistente", "parametros": {}}]}
    (d / "exigencias.json").write_text(json.dumps(mala), encoding="utf-8")
    with pytest.raises(ValueError, match="no está registrado"):
        verificar(_maestro(tmp_path), {"principal": "R"}, {"pais": "España"}, d)


def test_regla_veredicto_agregado():
    assert _veredicto_global(["cumple", "no-aplica"]) == "conforme"
    assert _veredicto_global(["cumple", "no-verificable"]) == "conforme-con-reservas"
    assert _veredicto_global(["no-cumple", "no-verificable"]) == "no-conforme"
