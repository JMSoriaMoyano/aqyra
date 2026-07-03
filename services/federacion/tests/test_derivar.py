"""Tests del IFC federado DERIVADO + cámara BCF (Fase II·h6, D26–D30).

Unidad y semántica: proyecto único, GUIDs preservados (incl. duplicados, D28),
placement raíz por modelo (D27), georref de serie, determinismo del md5 (D26),
cámara determinista (D29) y bloqueantes con diagnóstico. El recompute exacto
contra expected.json (C4-FED-06) es del runner, no de aquí.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import ifcopenshell
import ifcopenshell.guid
import pytest

_HERE = Path(__file__).resolve()
REPO = _HERE.parents[3]                      # aqyra/
SRC = _HERE.parents[1] / "src"
CASO = REPO / "packages" / "golden" / "C4" / "C4-FED-01"
PACK = REPO / "data" / "packs" / "ids" / "proyecto-piloto" / "v1"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aqyra_federacion import (LecturaIfcError, camara_para_guids, derivar,  # noqa: E402
                              emitir_bcf, federar, federar_fichero, validar)
from aqyra_federacion.derivar import ASPECTO, D_MIN, FOV_DEG, K_CAMARA  # noqa: E402


def _md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def _g() -> str:
    return ifcopenshell.guid.new()


def _mini(schema: str = "IFC4X3_ADD2", muro_guid: str | None = None,
          muro_xyz: tuple = (0.0, 0.0, 0.0)):
    """Modelo mínimo Project→Site→Building→Storey + muro con placement raíz."""
    f = ifcopenshell.file(schema=schema)
    proj = f.create_entity("IfcProject", GlobalId=_g(), Name="P")
    u = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
    proj.UnitsInContext = f.create_entity("IfcUnitAssignment", Units=[u])
    ctx = f.create_entity("IfcGeometricRepresentationContext",
                          ContextType="Model", CoordinateSpaceDimension=3,
                          Precision=1e-5)
    proj.RepresentationContexts = (ctx,)
    site = f.create_entity("IfcSite", GlobalId=_g(), Name="Emplazamiento")
    bld = f.create_entity("IfcBuilding", GlobalId=_g(), Name="Edificio")
    st = f.create_entity("IfcBuildingStorey", GlobalId=_g(), Name="Planta Baja")
    f.create_entity("IfcRelAggregates", GlobalId=_g(),
                    RelatingObject=proj, RelatedObjects=[site])
    f.create_entity("IfcRelAggregates", GlobalId=_g(),
                    RelatingObject=site, RelatedObjects=[bld])
    f.create_entity("IfcRelAggregates", GlobalId=_g(),
                    RelatingObject=bld, RelatedObjects=[st])
    pl = f.create_entity("IfcLocalPlacement", RelativePlacement=f.create_entity(
        "IfcAxis2Placement3D", Location=f.create_entity(
            "IfcCartesianPoint", Coordinates=tuple(float(v) for v in muro_xyz))))
    f.create_entity("IfcWall", GlobalId=muro_guid or _g(), Name="M1",
                    ObjectPlacement=pl)
    return f


def _manifiesto(tmp_path: Path, modelos: list[tuple[str, "ifcopenshell.file", dict]]):
    """federar() real sobre modelos escritos en tmp_path → manifiesto válido."""
    ms = []
    for mid, f, pb in modelos:
        ruta = tmp_path / f"{mid}.ifc"
        f.write(str(ruta))
        ms.append({"id": mid, "disciplina": "ARQ", "fichero": ruta.name,
                   "punto_base": pb})
    reglas = {"proyecto": "DERIV-TEST", "crs_destino": {"epsg": "EPSG:25830"},
              "modelos": ms,
              "deduplicacion": {"elementos": "nunca",
                                "estructura_espacial": "unificar-por-nombre"}}
    return federar(reglas, tmp_path)


PB0 = {"e": 100.0, "n": 200.0, "cota": 5.0, "rotacion_deg": 0.0}
PB90 = {"e": 1000.0, "n": 2000.0, "cota": 50.0, "rotacion_deg": 90.0}


# --------------------------- derivar() (D26/D27/D30) --------------------------
def test_derivado_md5_estable_y_proyecto_unico(tmp_path):
    guid_a, guid_b = _g(), _g()
    man = _manifiesto(tmp_path, [("A", _mini(muro_guid=guid_a), PB0),
                                 ("B", _mini(muro_guid=guid_b), PB90)])
    # mismo NOMBRE de fichero (va en la cabecera SPF) en carpetas distintas
    m1 = derivar(man, tmp_path, tmp_path / "r1" / "d.ifc", fecha="2026-07-03T00:00:00")
    m2 = derivar(man, tmp_path, tmp_path / "r2" / "d.ifc", fecha="2026-07-03T00:00:00")
    assert m1["ifc_derivado"]["md5"] == m2["ifc_derivado"]["md5"]      # D26
    assert m1["ifc_derivado"]["determinista"] is True
    assert m1["ifc_derivado"]["fichero"] == "d.ifc"
    assert "ifc_derivado" not in man                                   # no muta
    d = ifcopenshell.open(str(tmp_path / "r1" / "d.ifc"))
    proys = d.by_type("IfcProject")
    assert len(proys) == 1 and proys[0].Name == "DERIV-TEST"           # único
    assert {w.GlobalId for w in d.by_type("IfcWall")} == {guid_a, guid_b}  # preservados
    # la estructura espacial de ambos modelos cuelga del proyecto federado
    hijos = [c for r in d.by_type("IfcRelAggregates") if r.RelatingObject == proys[0]
             for c in r.RelatedObjects]
    assert len([h for h in hijos if h.is_a("IfcSite")]) == 2


def test_cabecera_spf_determinista(tmp_path):
    man = _manifiesto(tmp_path, [("A", _mini(), PB0)])
    derivar(man, tmp_path, tmp_path / "d.ifc", fecha="2026-07-03T00:00:00")
    cab = (tmp_path / "d.ifc").read_text(encoding="utf-8")[:400]
    assert "FILE_NAME('d.ifc','2026-07-03T00:00:00'" in cab            # inyectada
    assert "aqyra-federacion" in cab                                   # sin versión
    assert "IfcOpenShell" not in cab                                   # D26: ni build del wheel


def test_placement_raiz_materializa_transformacion(tmp_path):
    guid_b = _g()
    man = _manifiesto(tmp_path, [("A", _mini(), PB0),
                                 ("B", _mini(muro_guid=guid_b,
                                             muro_xyz=(1.0, 0.0, 0.0)), PB90)])
    man2 = derivar(man, tmp_path, tmp_path / "d.ifc")
    d = ifcopenshell.open(str(tmp_path / "d.ifc"))
    from ifcopenshell.util import placement as up
    muro = next(w for w in d.by_type("IfcWall") if w.GlobalId == guid_b)
    m = up.get_local_placement(muro.ObjectPlacement)
    # local (1,0,0) rotado 90° alrededor de Z + trasladado (1000,2000,50) → (1000,2001,50)
    assert abs(m[0][3] - 1000.0) < 1e-9
    assert abs(m[1][3] - 2001.0) < 1e-9
    assert abs(m[2][3] - 50.0) < 1e-9
    assert man2["ifc_derivado"]["md5"] == _md5(tmp_path / "d.ifc")


def test_georref_de_serie_r4(tmp_path):
    """D27: el derivado declara IfcMapConversion+IfcProjectedCRS → cumple R4."""
    man = _manifiesto(tmp_path, [("A", _mini(), PB0)])
    derivar(man, tmp_path, tmp_path / "d.ifc")
    d = ifcopenshell.open(str(tmp_path / "d.ifc"))
    assert len(d.by_type("IfcMapConversion")) == 1
    crs = d.by_type("IfcProjectedCRS")
    assert len(crs) == 1 and crs[0].Name == "EPSG:25830"


def test_guid_duplicado_conservado_y_declarado(tmp_path):
    """D28: mismo GlobalId en dos modelos → AMBOS en el derivado + aviso."""
    compartido = _g()
    man = _manifiesto(tmp_path, [("A", _mini(muro_guid=compartido), PB0),
                                 ("B", _mini(muro_guid=compartido), PB90)])
    derivar(man, tmp_path, tmp_path / "d.ifc")
    d = ifcopenshell.open(str(tmp_path / "d.ifc"))
    assert len([w for w in d.by_type("IfcWall") if w.GlobalId == compartido]) == 2
    informe = validar(man, PACK, tmp_path)
    avisos = [a for a in informe.get("avisos_lectura", [])
              if a["codigo"] == "guid-duplicado"]
    assert len(avisos) == 1 and avisos[0]["modelo"] == "B"             # el posterior
    assert compartido in avisos[0]["detalle"] and "A" in avisos[0]["detalle"]


def test_esquemas_heterogeneos_bloquea(tmp_path):
    man = _manifiesto(tmp_path, [("A", _mini(schema="IFC4"), PB0),
                                 ("B", _mini(schema="IFC4X3_ADD2"), PB90)])
    with pytest.raises(LecturaIfcError, match="heterogéneos"):
        derivar(man, tmp_path, tmp_path / "d.ifc")


def test_md5_alterado_bloquea(tmp_path):
    man = _manifiesto(tmp_path, [("A", _mini(), PB0)])
    man["modelos"][0]["md5"] = "0" * 32
    with pytest.raises(LecturaIfcError, match="integridad"):
        derivar(man, tmp_path, tmp_path / "d.ifc")


# --------------------------- cámara (D29) ------------------------------------
def test_camara_geometria_y_determinismo(tmp_path):
    guid_a, guid_b = _g(), _g()
    man = _manifiesto(tmp_path, [("A", _mini(muro_guid=guid_a), PB0),
                                 ("B", _mini(muro_guid=guid_b), PB90)])
    derivar(man, tmp_path, tmp_path / "d.ifc")
    d = ifcopenshell.open(str(tmp_path / "d.ifc"))
    cam = camara_para_guids(d, [guid_a, guid_b])
    # bbox de orígenes absolutos: (100,200,5) y (1000,2000,50)
    centro = (550.0, 1100.0, 27.5)
    diag = math.dist((100.0, 200.0, 5.0), (1000.0, 2000.0, 50.0))
    dd = max(diag, D_MIN)
    assert cam["posicion"] == pytest.approx(
        (centro[0] + K_CAMARA * dd, centro[1] - K_CAMARA * dd, centro[2] + K_CAMARA * dd))
    n = math.sqrt(sum(v * v for v in cam["direccion"]))
    assert n == pytest.approx(1.0)                                     # unitaria
    assert sum(a * b for a, b in zip(cam["direccion"], cam["arriba"])) == \
        pytest.approx(0.0, abs=1e-12)                                  # up ⊥ dir
    assert cam["arriba"][2] > 0                                        # Z arriba
    assert cam["fov_deg"] == FOV_DEG and cam["aspecto"] == ASPECTO
    assert cam == camara_para_guids(d, [guid_a, guid_b])               # determinista


def test_camara_bbox_degenerado_usa_d_min(tmp_path):
    guid_a = _g()
    man = _manifiesto(tmp_path, [("A", _mini(muro_guid=guid_a), PB0)])
    derivar(man, tmp_path, tmp_path / "d.ifc")
    d = ifcopenshell.open(str(tmp_path / "d.ifc"))
    cam = camara_para_guids(d, [guid_a])
    assert cam["posicion"] == pytest.approx((100.0 + D_MIN, 200.0 - D_MIN, 5.0 + D_MIN))


def test_camara_sin_guids_resolubles(tmp_path):
    man = _manifiesto(tmp_path, [("A", _mini(), PB0)])
    derivar(man, tmp_path, tmp_path / "d.ifc")
    d = ifcopenshell.open(str(tmp_path / "d.ifc"))
    assert camara_para_guids(d, ["0000000000000000000000"]) is None


# --------------------------- emisión con cámara (D29) -------------------------
def test_emitir_con_derivado_pone_camara_y_sin_el_no(tmp_path):
    manifiesto = federar_fichero(CASO / "reglas.json")
    informe = validar(manifiesto, PACK, CASO)
    derivado = tmp_path / "federado.ifc"
    derivar(manifiesto, CASO, derivado)
    gen = dict(caso="TEST6", autor="t", fecha="2026-07-03T00:00:00Z")
    sin = emitir_bcf(informe, tmp_path / "sin", **gen)
    con = emitir_bcf(informe, tmp_path / "con", **gen, derivado=derivado)
    from aqyra_federacion.bcf import guid_topic
    tg = guid_topic("TEST6", "INC-03")                     # única incidencia con GUIDs
    vp_sin = (tmp_path / "sin" / tg / "viewpoint.bcfv")
    vp_con = (tmp_path / "con" / tg / "viewpoint.bcfv")
    r_sin = ET.parse(str(vp_sin)).getroot()
    r_con = ET.parse(str(vp_con)).getroot()
    assert r_sin.find("PerspectiveCamera") is None         # sin derivado: como en v0
    pc = r_con.find("PerspectiveCamera")
    assert pc is not None                                  # con derivado: cámara (D29)
    assert pc.findtext("FieldOfView") == f"{FOV_DEG:.6f}"
    assert pc.findtext("AspectRatio") == f"{ASPECTO:.6f}"
    for eje in ("CameraViewPoint", "CameraDirection", "CameraUpVector"):
        nodo = pc.find(eje)
        assert [c.tag for c in nodo] == ["X", "Y", "Z"]    # orden del visinfo.xsd
        for c in nodo:
            float(c.text)                                  # 6 decimales parseables
            assert len(c.text.split(".")[1]) == 6
    # el markup y el resto del árbol no cambian por la cámara
    assert _md5(tmp_path / "sin" / tg / "markup.bcf") == \
        _md5(tmp_path / "con" / tg / "markup.bcf")
    # determinismo del árbol CON cámara (doble run)
    emitir_bcf(informe, tmp_path / "con2", **gen, derivado=derivado)
    assert _md5(vp_con) == _md5(tmp_path / "con2" / tg / "viewpoint.bcfv")
    assert sin["bcf"]["emitido"] is True and con["bcf"]["emitido"] is True
