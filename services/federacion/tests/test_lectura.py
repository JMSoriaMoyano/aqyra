"""Tests de la LECTURA ENDURECIDA para IFC sucio (tarea 1.3, D16–D20).

Un test por caso de la taxonomía de D17 — suciedad TOLERABLE (degradación declarada
en `avisos_lectura` / nodos "(sin nombre)") y BLOQUEANTE (LecturaIfcError con
diagnóstico accionable). Los IFC sucios se fabrican aquí con ifcopenshell (sintéticos,
en tmp_path); el camino feliz-degradado congelado es la golden C4-FED-03 (runner).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import ifcopenshell
import ifcopenshell.guid
import pytest

_HERE = Path(__file__).resolve()
REPO = _HERE.parents[3]                      # aqyra/
SRC = _HERE.parents[1] / "src"
CASO_LIMPIO = REPO / "packages" / "golden" / "C4" / "C4-FED-01"
PACK = REPO / "data" / "packs" / "ids" / "proyecto-piloto" / "v1"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aqyra_federacion import LecturaIfcError, federar, federar_fichero, validar  # noqa: E402
from aqyra_federacion import ids_min, lectura  # noqa: E402


# --------------------------- fábrica de IFC sucios ---------------------------
def _g() -> str:
    return ifcopenshell.guid.new()


def _modelo(schema: str = "IFC4X3", *, con_site: bool = True, unidad: str = "METRE",
            prefijo: str | None = None, sin_unidades: bool = False):
    """Modelo mínimo Project(+Units)→[Site]→Building→Storey('Planta Baja')."""
    f = ifcopenshell.file(schema=schema)
    proj = f.create_entity("IfcProject", GlobalId=_g(), Name="P")
    if not sin_unidades:
        u = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name=unidad,
                            Prefix=prefijo)
        proj.UnitsInContext = f.create_entity("IfcUnitAssignment", Units=[u])
    bld = f.create_entity("IfcBuilding", GlobalId=_g(), Name="Edificio")
    st = f.create_entity("IfcBuildingStorey", GlobalId=_g(), Name="Planta Baja")
    if con_site:
        site = f.create_entity("IfcSite", GlobalId=_g(), Name="Emplazamiento")
        f.create_entity("IfcRelAggregates", GlobalId=_g(),
                        RelatingObject=proj, RelatedObjects=[site])
        f.create_entity("IfcRelAggregates", GlobalId=_g(),
                        RelatingObject=site, RelatedObjects=[bld])
    else:
        f.create_entity("IfcRelAggregates", GlobalId=_g(),
                        RelatingObject=proj, RelatedObjects=[bld])
    f.create_entity("IfcRelAggregates", GlobalId=_g(),
                    RelatingObject=bld, RelatedObjects=[st])
    return f


def _reglas(tmp_path: Path, f, mid: str = "SUC") -> dict:
    ruta = tmp_path / f"{mid}.ifc"
    f.write(str(ruta))
    return {"proyecto": "test", "crs_destino": {"epsg": "EPSG:25830"},
            "modelos": [{"id": mid, "disciplina": "ARQ", "fichero": ruta.name,
                         "punto_base": {"e": 0.0, "n": 0.0, "cota": 0.0}}]}


def _avisos(tmp_path: Path, f, mid: str = "SUC") -> tuple[dict, list[dict]]:
    """federar+validar del modelo → (informe, avisos_lectura)."""
    reglas = _reglas(tmp_path, f, mid)
    manifiesto = federar(reglas, tmp_path)
    informe = validar(manifiesto, PACK, tmp_path)
    return informe, informe.get("avisos_lectura", [])


def _codigos(avisos: list[dict]) -> set[str]:
    return {a["codigo"] for a in avisos}


# --------------------------- TOLERABLE: se declara ---------------------------
def test_nombre_vacio_nodo_declarado(tmp_path):
    f = _modelo()
    f.by_type("IfcBuildingStorey")[0].Name = None
    reglas = _reglas(tmp_path, f)
    man = federar(reglas, tmp_path)
    nodos = {(a["nivel"], a["nombre"]) for a in man["estructura_espacial"]["agregados"]}
    assert ("Storey", "(sin nombre)") in nodos          # declarado, no ""
    informe = validar(man, PACK, tmp_path)
    assert "nombre-vacio" in _codigos(informe["avisos_lectura"])


def test_nombre_duplicado_intra_modelo(tmp_path):
    f = _modelo()
    bld = f.by_type("IfcBuilding")[0]
    st2 = f.create_entity("IfcBuildingStorey", GlobalId=_g(), Name="Planta Baja")
    f.create_entity("IfcRelAggregates", GlobalId=_g(),
                    RelatingObject=bld, RelatedObjects=[st2])
    informe, avisos = _avisos(tmp_path, f)
    assert "nombre-duplicado" in _codigos(avisos)
    # los duplicados se unifican en UN nodo (política por-nombre, ahora declarada)
    # y el aviso lleva los #ids de las entidades unificadas
    dup = [a for a in avisos if a["codigo"] == "nombre-duplicado"][0]
    assert "Planta Baja" in dup["detalle"] and "#" in dup["detalle"]


def test_nivel_ausente_sin_site(tmp_path):
    informe, avisos = _avisos(tmp_path, _modelo(con_site=False))
    assert "nivel-ausente" in _codigos(avisos)
    assert any("IfcSite" in a["detalle"] for a in avisos)


def test_multi_proyecto(tmp_path):
    f = _modelo()
    f.create_entity("IfcProject", GlobalId=_g(), Name="FANTASMA")
    informe, avisos = _avisos(tmp_path, f)
    assert "multi-proyecto" in _codigos(avisos)


def test_esquema_2x3_no_revienta_y_r4_diagnostica(tmp_path):
    """Hallazgo #7: IfcMapConversion no existe en IFC2X3 — antes, crash de validar()."""
    informe, avisos = _avisos(tmp_path, _modelo(schema="IFC2X3"))
    assert "esquema-no-4x3" in _codigos(avisos)
    r4 = [r for r in informe["requisitos"] if r["id"] == "R4-GEORREF"][0]
    assert r4["resultado"] == "fail"                    # fail diagnosticado, no excepción
    assert "IFC2X3" in r4["por_modelo"]["SUC"]["detalle"]


def test_unidades_no_metricas(tmp_path):
    informe, avisos = _avisos(tmp_path, _modelo(prefijo="MILLI"))
    assert "unidades-no-metricas" in _codigos(avisos)


def test_sin_unidades(tmp_path):
    informe, avisos = _avisos(tmp_path, _modelo(sin_unidades=True))
    assert "sin-unidades" in _codigos(avisos)


def test_entidad_corrupta_se_salta_y_declara(monkeypatch):
    """D17: elemento cuyos atributos revientan → saltado, con aviso (vía evaluar_spec)."""
    class Rota:
        def id(self):
            return 99
        def __getattr__(self, name):            # cualquier atributo revienta
            raise RuntimeError("atributo roto")

    spec = ids_min.Spec(id="RX", titulo="t", entidades=["IFCWALL"],
                        requisitos=[ids_min.Requisito("attribute", {"nombre": "Name",
                                                                    "patron": None})])
    monkeypatch.setattr(ids_min, "aplicables", lambda ifc, s: [Rota()])
    ev = ids_min.evaluar_spec(None, spec)
    assert ev["corruptos"] == ["#99"]
    assert ev["n_comprobados"] == 0 and ev["n_fallos"] == 0


# ------------------- CORRECCIONES de lectura (D17, matiz) --------------------
def test_pset_via_tipo(tmp_path):
    """Hallazgo #10: Pset en el TIPO (patrón Revit) — antes, falso fail."""
    f = _modelo()
    muro = f.create_entity("IfcWall", GlobalId=_g(), Name="M1")
    val = f.create_entity("IfcBoolean", True)
    prop = f.create_entity("IfcPropertySingleValue", Name="IsExternal", NominalValue=val)
    pset = f.create_entity("IfcPropertySet", GlobalId=_g(), Name="Pset_WallCommon",
                           HasProperties=[prop])
    tipo = f.create_entity("IfcWallType", GlobalId=_g(), Name="MT",
                           HasPropertySets=[pset], PredefinedType="SOLIDWALL")
    f.create_entity("IfcRelDefinesByType", GlobalId=_g(),
                    RelatedObjects=[muro], RelatingType=tipo)
    assert ids_min._tiene_propiedad(muro, "Pset_WallCommon", "IsExternal")


def test_clasificacion_encadenada(tmp_path):
    """Hallazgo #9: ReferencedSource en CADENA (IFC4/Revit) — antes, falso fail."""
    f = _modelo()
    muro = f.create_entity("IfcWall", GlobalId=_g(), Name="M1")
    sistema = f.create_entity("IfcClassification", Name="bsDD")
    padre = f.create_entity("IfcClassificationReference", Identification="Pp",
                            ReferencedSource=sistema)
    hoja = f.create_entity("IfcClassificationReference", Identification="Pp_20",
                           ReferencedSource=padre)
    f.create_entity("IfcRelAssociatesClassification", GlobalId=_g(),
                    RelatedObjects=[muro], RelatingClassification=hoja)
    assert "bsDD" in ids_min._sistemas_clasificacion(muro)


# --------------------------- BLOQUEANTE: diagnóstico --------------------------
def test_fichero_inexistente(tmp_path):
    with pytest.raises(LecturaIfcError, match="no existe"):
        lectura.abrir_ifc(tmp_path / "nada.ifc")


def test_fichero_no_parsea(tmp_path):
    basura = tmp_path / "basura.ifc"
    basura.write_text("esto no es un IFC", encoding="utf-8")
    with pytest.raises(LecturaIfcError, match="no puede parsearlo"):
        lectura.abrir_ifc(basura)


def test_federar_fichero_ausente_diagnostica(tmp_path):
    reglas = {"proyecto": "t", "crs_destino": {"epsg": "EPSG:25830"},
              "modelos": [{"id": "X", "disciplina": "ARQ", "fichero": "no-esta.ifc",
                           "punto_base": {"e": 0.0, "n": 0.0, "cota": 0.0}}]}
    with pytest.raises(LecturaIfcError, match="no existe"):
        federar(reglas, tmp_path)


def test_md5_distinto_es_lectura_error(tmp_path):
    """Compatibilidad: sigue siendo ValueError (test_integridad_md5), ahora con clase."""
    f = _modelo()
    reglas = _reglas(tmp_path, f)
    reglas["modelos"][0]["md5"] = "0" * 32
    with pytest.raises(LecturaIfcError, match="integridad"):
        federar(reglas, tmp_path)


# --------------------------- protección de los limpios ------------------------
def test_modelos_limpios_sin_avisos():
    """D20: la clave avisos_lectura NO aparece con modelos limpios (C4-FED-01/02)."""
    manifiesto = federar_fichero(CASO_LIMPIO / "reglas.json")
    informe = validar(manifiesto, PACK, CASO_LIMPIO)
    assert "avisos_lectura" not in informe


def test_modelo_sucio_es_determinista(tmp_path):
    f = _modelo()
    f.by_type("IfcBuildingStorey")[0].Name = None
    f.create_entity("IfcProject", GlobalId=_g(), Name="FANTASMA")
    reglas = _reglas(tmp_path, f)
    a = validar(federar(reglas, tmp_path), PACK, tmp_path)
    b = validar(federar(reglas, tmp_path), PACK, tmp_path)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
