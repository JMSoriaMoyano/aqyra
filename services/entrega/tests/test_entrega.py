# -*- coding: utf-8 -*-
"""Tests del operador de entrega C7 (unidad). El paquete = presupuesto + pliego sobre el mismo
`salida-presupuesto` ANCLADO de GOL-PRE-01 (se LEE, no se re-ancla). La conformidad profunda vive en
la golden GOL-EN-01; aqui, cobertura de unidad (roll-up, integridad, determinismo, isCertified).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import aqyra_entrega as E
from aqyra_entrega import manifiesto_entrega as ME
import aqyra_documento_export as adx

_REPO = Path(__file__).resolve().parents[3]
_PRES = _REPO / "packages" / "golden" / "C5" / "GOL-PRE-01" / "expected.json"
_CRIT = _REPO / "data" / "packs" / "criterio" / "AQ" / "v2" / "criterio.json"
_TEXTOS = _REPO / "data" / "packs" / "pliego-textos" / "AQ-DEMO" / "v1" / "textos.json"
SELLO = "2026-07-13"


def _presupuesto() -> dict:
    if not _PRES.exists():
        pytest.skip(f"no esta {_PRES}")
    return json.loads(_PRES.read_text(encoding="utf-8"))["presupuesto"]


def _solicitud() -> dict:
    if not (_CRIT.exists() and _TEXTOS.exists()):
        pytest.skip("faltan packs criterio/AQ/v2 o pliego-textos/AQ-DEMO/v1")
    pres = _presupuesto()
    criterio = json.loads(_CRIT.read_text(encoding="utf-8"))
    textos = json.loads(_TEXTOS.read_text(encoding="utf-8"))
    va = {"contrato_c7": "C7-entrega", "service": "services/entrega", "schema": "manifiesto-entrega"}
    return {
        "proyecto": "GOL-PRE-01",
        "hito": "proyecto-basico",
        "sello_tiempo": SELLO,
        "versiones_ancladas": va,
        "entregables": [
            {"consumidor": "presupuesto-obra", "artefacto_ref": "C5/GOL-PRE-01", "artefacto": pres,
             "descriptor": {"artefacto": {"tipo": "presupuesto-obra", "id": "GOL-PRE-01"},
                            "formatos": ["word", "pdf", "bc3", "xlsx"],
                            "versiones_ancladas": {"contrato_c5": "C5-presupuesto", "criterio": "AQ/v1"}}},
            {"consumidor": "pliego-obra", "artefacto_ref": "C5/GOL-PRE-01", "artefacto": pres,
             "descriptor": {"artefacto": {"tipo": "pliego-obra", "id": "GOL-PRE-01"},
                            "formatos": ["word", "pdf"],
                            "pliego": {"criterio": criterio, "pack_textos": textos},
                            "versiones_ancladas": {"contrato_c5": "C5-presupuesto", "criterio": "AQ/v2"}}},
        ],
    }


def test_paquete_dos_bundles_y_manifiesto(tmp_path):
    paquete = E.componer_entrega(_solicitud(), {"salida": tmp_path / "pkg"})
    assert (paquete / E.NOMBRE_MANIFIESTO_ENTREGA).exists()
    for sub, fmts in (("presupuesto-obra", ["Presupuesto.docx", "Presupuesto-firmable.pdf"]),
                      ("pliego-obra", ["Pliego.docx", "Pliego-firmable.pdf"])):
        assert (paquete / sub / adx.NOMBRE_MANIFIESTO).exists(), sub
        for f in fmts:
            assert (paquete / sub / f).exists(), f"{sub}/{f}"


def test_rollup_integridad(tmp_path):
    sol = _solicitud()
    paquete = E.componer_entrega(sol, {"salida": tmp_path / "pkg"})
    man = json.loads((paquete / E.NOMBRE_MANIFIESTO_ENTREGA).read_text(encoding="utf-8"))
    assert man["esquema"] == "manifiesto-entrega/v0"
    assert len(man["entregables"]) == 2
    ok, det = ME.integridad(man, E.sha_por_bundle(paquete, man))
    assert ok, det
    # el roll-up recomputado casa
    csm = [e["content_sha256_manifiesto"] for e in man["entregables"]]
    assert man["paquete_sha256"] == ME.roll_up(csm)


def test_mismo_maestro(tmp_path):
    # ambos entregables descienden del MISMO salida-presupuesto -> mismo content_sha256 de artefacto
    paquete = E.componer_entrega(_solicitud(), {"salida": tmp_path / "pkg"})
    shas = set()
    for sub in ("presupuesto-obra", "pliego-obra"):
        m = json.loads((paquete / sub / adx.NOMBRE_MANIFIESTO).read_text(encoding="utf-8"))
        shas.add(m["artefacto"]["content_sha256"])
    assert len(shas) == 1, "los dos bundles deben anclar el mismo artefacto (mismo Maestro)"


def test_determinismo(tmp_path):
    sol = _solicitud()
    a = E.componer_entrega(sol, {"salida": tmp_path / "a"})
    b = E.componer_entrega(sol, {"salida": tmp_path / "b"})
    assert (a / E.NOMBRE_MANIFIESTO_ENTREGA).read_bytes() == (b / E.NOMBRE_MANIFIESTO_ENTREGA).read_bytes()


def test_isCertified_sin_firmar(tmp_path):
    paquete = E.componer_entrega(_solicitud(), {"salida": tmp_path / "pkg"})
    for sub in ("presupuesto-obra", "pliego-obra"):
        assert not adx.es_certificado(paquete / sub), f"{sub} sin firmar NO debe ser verified-signed"
    assert not (paquete / (E.NOMBRE_MANIFIESTO_ENTREGA + ".asc")).exists()


def test_artefacto_ref_sin_inline_falla(tmp_path):
    sol = _solicitud()
    del sol["entregables"][0]["artefacto"]  # deja solo artefacto_ref
    with pytest.raises(ValueError):
        E.componer_entrega(sol, {"salida": tmp_path / "pkg"})
