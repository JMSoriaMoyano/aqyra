"""E2.1 (N-06) · Los cortes nacen del IFC — test del parser de cortes.

Dos bloques:
  1. Funciones PURAS (reparto de frontera 50/50 y fallback del criterio): corren SIEMPRE, sin
     ifcopenshell. Fijan la matemática del reparto (D21) y la selección del fallback (D22).
  2. Integración con ifcopenshell (`pytest.importorskip`): construye un modelo mínimo con
     IfcSystem, IfcZone+espacios+IfcRelSpaceBoundary y árbol espacial, corre `medir(...)` con el
     criterio v2 y verifica los cortes completos, el 50/50 en un tabique compartido y el fallback
     por criterio. NOTA: verificar en el conda `mcp-bim` local antes del PR (el sandbox de
     desarrollo no trae ifcopenshell).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aqyra_presupuesto import medir
from aqyra_presupuesto import modelo as M

REPO = Path(__file__).resolve().parents[3]
CRITERIO_V2 = REPO / "data" / "packs" / "criterio" / "AQ" / "v2" / "criterio.json"


def _criterio() -> dict:
    return json.loads(CRITERIO_V2.read_text(encoding="utf-8"))


# ----------------------------------------------------------------------------------------
# 1 · Funciones puras (sin ifcopenshell) — la matemática del reparto y el fallback
# ----------------------------------------------------------------------------------------

def test_reparto_50_50_tabique_compartido():
    """Un tabique que delimita dos espacios de dos zonas → 0,5/0,5 (N-06, D21)."""
    r = M.reparto_zonas([["Aulas"], ["Admin"]])
    assert r == [
        {"grupo": "Aulas", "fraccion": 0.5, "fuente": "ifc"},
        {"grupo": "Admin", "fraccion": 0.5, "fuente": "ifc"},
    ]
    assert abs(sum(p["fraccion"] for p in r) - 1.0) < 1e-9


def test_reparto_100_un_espacio():
    assert M.reparto_zonas([["Aulas"]]) == [{"grupo": "Aulas", "fraccion": 1.0, "fuente": "ifc"}]


def test_reparto_misma_zona_agrega():
    assert M.reparto_zonas([["Z"], ["Z"]]) == [{"grupo": "Z", "fraccion": 1.0, "fuente": "ifc"}]


def test_reparto_sin_espacios():
    assert M.reparto_zonas([]) == []


def test_reparto_espacio_sin_zona_es_parcial():
    """Espacio sin zona → su fracción no se atribuye (atribución parcial si el modelo es incompleto)."""
    assert M.reparto_zonas([["Aulas"], []]) == [{"grupo": "Aulas", "fraccion": 0.5, "fuente": "ifc"}]


def test_fallback_funcional_por_criterio():
    """Sin agrupación nativa, funcional sale del criterio (reglas_sistema) con fuente=criterio (D22).
    El emparejamiento es POR JERARQUÍA: se pasa la ascendencia de tipos IFC (clase + supertipos)."""
    crit = _criterio()
    rs, dflt = crit["reglas_sistema"], crit.get("reglas_sistema_default")

    def fb(tipos, is_ext):
        return M.sistema_fallback(tipos, {"is_external": is_ext}, rs, dflt)

    muro = ["IfcWall", "IfcBuiltElement", "IfcElement"]
    assert fb(muro, True) == [{"grupo": "Envolvente", "fraccion": 1.0, "fuente": "criterio"}]
    assert fb(muro, False) == [{"grupo": "Particiones", "fraccion": 1.0, "fuente": "criterio"}]
    # IsExternal desconocido → la regla condicionada se salta → regla de clase sin condicion
    assert fb(muro, None) == [{"grupo": "Particiones", "fraccion": 1.0, "fuente": "criterio"}]
    assert fb(["IfcSlab", "IfcBuiltElement", "IfcElement"], None) == \
        [{"grupo": "Estructura", "fraccion": 1.0, "fuente": "criterio"}]


def test_fallback_por_supertipo_cubre_clases_no_listadas():
    """Una clase que NO está en la tabla casa por su SUPERTIPO (la clave de la escalabilidad, D22)."""
    crit = _criterio()
    rs, dflt = crit["reglas_sistema"], crit.get("reglas_sistema_default")
    # IfcPipeSegment no está listado, pero desciende de IfcDistributionElement → Instalaciones
    tuberia = ["IfcPipeSegment", "IfcFlowSegment", "IfcDistributionFlowElement",
               "IfcDistributionElement", "IfcElement", "IfcProduct"]
    assert M.sistema_fallback(tuberia, {}, rs, dflt) == \
        [{"grupo": "Instalaciones", "fraccion": 1.0, "fuente": "criterio"}]
    # un elemento construido genérico no listado cae en el catch-all IfcBuiltElement (antes del default)
    generico = ["IfcChimney", "IfcBuiltElement", "IfcElement", "IfcProduct"]
    assert M.sistema_fallback(generico, {}, rs, dflt) == \
        [{"grupo": "Elementos constructivos", "fraccion": 1.0, "fuente": "criterio"}]
    # algo totalmente fuera de las familias → default
    assert M.sistema_fallback(["IfcAnnotation", "IfcProduct"], {}, rs, dflt) == \
        [{"grupo": "Sin clasificar", "fraccion": 1.0, "fuente": "criterio"}]


# ----------------------------------------------------------------------------------------
# 2 · Integración con ifcopenshell — el parser lee las agrupaciones nativas del IFC
#     (verificar en conda `mcp-bim` antes del PR)
# ----------------------------------------------------------------------------------------

def _modelo_cortes(tmp_path: Path) -> Path:
    """Construye un IFC4 mínimo: árbol Edificio-A/Planta-01, dos espacios E-101 (zona Aulas) y
    E-102 (zona Admin), un tabique que los separa (frontera compartida), un tabique interior a
    E-101, una viga en el IfcSystem 'Clima', y un forjado sin agrupación (→ fallback criterio)."""
    ifcopenshell = pytest.importorskip("ifcopenshell")
    import ifcopenshell.guid as guid

    f = ifcopenshell.file(schema="IFC4")

    def E(tipo, nombre=None, **kw):
        return f.create_entity(tipo, guid.new(), None, nombre, **kw) if nombre is not None \
            else f.create_entity(tipo, guid.new(), None)

    proj = E("IfcProject", "Proj")
    site = E("IfcSite", "Site")
    bldg = E("IfcBuilding", "Edificio-A")
    storey = E("IfcBuildingStorey", "Planta-01")
    sp1 = E("IfcSpace", "E-101")
    sp2 = E("IfcSpace", "E-102")

    def agg(padre, hijos):
        f.create_entity("IfcRelAggregates", guid.new(), None,
                        RelatingObject=padre, RelatedObjects=hijos)

    agg(proj, [site]); agg(site, [bldg]); agg(bldg, [storey]); agg(storey, [sp1, sp2])

    w_shared = E("IfcWall", "Tabique-compartido")
    w_int = E("IfcWall", "Tabique-interior")
    viga = E("IfcBeam", "Viga-clima")
    forjado = E("IfcSlab", "Forjado")

    f.create_entity("IfcRelContainedInSpatialStructure", guid.new(), None,
                    RelatingStructure=storey, RelatedElements=[w_shared, w_int, viga, forjado])

    def boundary(space, elem):
        f.create_entity("IfcRelSpaceBoundary", guid.new(), None,
                        RelatingSpace=space, RelatedBuildingElement=elem,
                        PhysicalOrVirtualBoundary="PHYSICAL", InternalOrExternalBoundary="INTERNAL")

    boundary(sp1, w_shared); boundary(sp2, w_shared)   # tabique compartido → 50/50
    boundary(sp1, w_int)                                # tabique interior → 100% Aulas

    zona_aulas = f.create_entity("IfcZone", guid.new(), None, "Aulas")
    zona_admin = f.create_entity("IfcZone", guid.new(), None, "Admin")
    sys_clima = f.create_entity("IfcSystem", guid.new(), None, "Clima")

    def assign(grupo, objetos):
        f.create_entity("IfcRelAssignsToGroup", guid.new(), None,
                        RelatedObjects=objetos, RelatingGroup=grupo)

    assign(zona_aulas, [sp1]); assign(zona_admin, [sp2]); assign(sys_clima, [viga])

    out = tmp_path / "cortes.ifc"
    f.write(str(out))
    return out


def test_parser_cortes_integracion(tmp_path):
    pytest.importorskip("ifcopenshell")
    ifc = _modelo_cortes(tmp_path)
    modelo = medir([{"id": "T", "path": str(ifc)}], _criterio())
    por_nombre = {o.get("nombre"): o for o in modelo["objetos"]}

    # espacial: todos bajo Edificio-A/Planta-01
    assert "Planta-01" in por_nombre["Forjado"]["cortes"]["espacial"][0]["grupo"]

    # funcional por IfcZone con reparto 50/50 (tabique compartido)
    fc = por_nombre["Tabique-compartido"]["cortes"]["funcional"]
    grupos = {p["grupo"]: p["fraccion"] for p in fc}
    assert grupos == {"Aulas": 0.5, "Admin": 0.5}
    assert all(p["fuente"] == "ifc" for p in fc)
    assert abs(sum(p["fraccion"] for p in fc) - 1.0) < 1e-9

    # funcional 100% para el tabique interior (un solo espacio)
    fi = por_nombre["Tabique-interior"]["cortes"]["funcional"]
    assert fi == [{"grupo": "Aulas", "fraccion": 1.0, "fuente": "ifc"}]

    # funcional por IfcSystem (la viga en 'Clima')
    fv = por_nombre["Viga-clima"]["cortes"]["funcional"]
    assert fv == [{"grupo": "Clima", "fraccion": 1.0, "fuente": "ifc"}]

    # fallback del criterio para el forjado (sin sistema ni zona) → Estructura, fuente=criterio
    ff = por_nombre["Forjado"]["cortes"]["funcional"]
    assert ff == [{"grupo": "Estructura", "fraccion": 1.0, "fuente": "criterio"}]
