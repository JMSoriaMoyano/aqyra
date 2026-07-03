"""Tests unitarios de la librería FINITA de evaluadores (D8), sobre IFC sintéticos en memoria.

Estos tests NO tocan la golden ni el service: prueban cada primitiva determinista en aislamiento.
La reproducción del checklist COMPLETO de GOL-CTE-01 vive en la costura del runner
(packages/golden/run_golden.run_case_c3) — misma división que en C1/C4.
"""
import ifcopenshell
import ifcopenshell.guid as guid

from aqyra_cumplimiento.evaluadores import (
    EVALUADORES, RESULTADOS,
    presencia_tipo_ifc, presencia_propiedad_pset, aplica_solo_uso, requiere_motor,
)


def _f():
    return ifcopenshell.file(schema="IFC4X3")


def _ctx(f, guid2mod=None, uso=None):
    return {"derivado": f, "guid2mod": guid2mod or {}, "modelos": [],
            "uso": uso or {"principal": "Residencial Vivienda"}, "localizacion": {}}


def _elem(f, clase, nombre, pset=None):
    e = f.create_entity(clase, GlobalId=guid.new(), Name=nombre)
    if pset:
        props = [f.create_entity("IfcPropertySingleValue", Name=k,
                                 NominalValue=f.create_entity("IfcLabel", v))
                 for k, v in pset.items()]
        ps = f.create_entity("IfcPropertySet", GlobalId=guid.new(),
                             Name="Pset_Test", HasProperties=props)
        f.create_entity("IfcRelDefinesByProperties", GlobalId=guid.new(),
                        RelatedObjects=[e], RelatingPropertyDefinition=ps)
    return e


# --- registro -------------------------------------------------------------- #

def test_registro_cubre_los_cuatro_metodos():
    assert set(EVALUADORES) == {"presencia-tipo-ifc", "presencia-propiedad-pset",
                                "aplica-solo-uso", "requiere-motor"}


def test_todos_los_resultados_en_taxonomia_cerrada():
    for r in RESULTADOS:
        assert r in ("cumple", "no-cumple", "no-aplica", "no-verificable")


# --- presencia-tipo-ifc ---------------------------------------------------- #

def test_presencia_tipo_cumple_con_ascensor():
    f = _f()
    f.create_entity("IfcTransportElement", GlobalId=guid.new(),
                    Name="Ascensor-01", PredefinedType="ELEVATOR")
    r = presencia_tipo_ifc(_ctx(f), {"clase": "IfcTransportElement",
                                     "predefined_type": "ELEVATOR"})
    assert r["resultado"] == "cumple"


def test_presencia_tipo_no_cumple_sin_elemento():
    r = presencia_tipo_ifc(_ctx(_f()), {"clase": "IfcTransportElement",
                                        "predefined_type": "ELEVATOR"})
    assert r["resultado"] == "no-cumple"


def test_presencia_tipo_discrimina_predefined_type():
    f = _f()
    f.create_entity("IfcTransportElement", GlobalId=guid.new(),
                    Name="Escalera-mec", PredefinedType="ESCALATOR")
    r = presencia_tipo_ifc(_ctx(f), {"clase": "IfcTransportElement",
                                     "predefined_type": "ELEVATOR"})
    assert r["resultado"] == "no-cumple"


# --- presencia-propiedad-pset ---------------------------------------------- #

def test_propiedad_no_cumple_si_falta_en_alguno():
    f = _f()
    c1 = _elem(f, "IfcColumn", "P1", pset={"FireRating": "R60"})
    c2 = _elem(f, "IfcColumn", "P2")  # sin FireRating
    g2m = {c1.GlobalId: "EST", c2.GlobalId: "EST"}
    r = presencia_propiedad_pset(_ctx(f, g2m),
                                 {"clases": ["IfcColumn"], "propiedad": "FireRating"})
    assert r["resultado"] == "no-cumple"
    assert r["por_modelo"]["EST"]["n_comprobados"] == 2
    assert r["por_modelo"]["EST"]["n_fallos"] == 1


def test_propiedad_cumple_si_todos_declaran():
    f = _f()
    c1 = _elem(f, "IfcColumn", "P1", pset={"FireRating": "R60"})
    s1 = _elem(f, "IfcSlab", "L1", pset={"FireRating": "R90"})
    g2m = {c1.GlobalId: "EST", s1.GlobalId: "ARQ"}
    r = presencia_propiedad_pset(_ctx(f, g2m),
                                 {"clases": ["IfcColumn", "IfcSlab"], "propiedad": "FireRating"})
    assert r["resultado"] == "cumple"
    assert r["por_modelo"]["EST"]["resultado"] == "cumple"
    assert r["por_modelo"]["ARQ"]["resultado"] == "cumple"


def test_propiedad_reparte_por_modelo():
    f = _f()
    w1 = _elem(f, "IfcWall", "M1")
    w2 = _elem(f, "IfcWall", "M2")
    c1 = _elem(f, "IfcColumn", "P1")
    g2m = {w1.GlobalId: "ARQ", w2.GlobalId: "ARQ", c1.GlobalId: "EST"}
    r = presencia_propiedad_pset(_ctx(f, g2m),
                                 {"clases": ["IfcWall", "IfcColumn"], "propiedad": "FireRating"})
    assert r["por_modelo"]["ARQ"]["n_comprobados"] == 2
    assert r["por_modelo"]["EST"]["n_comprobados"] == 1
    assert r["resultado"] == "no-cumple"


# --- aplica-solo-uso ------------------------------------------------------- #

def test_aplica_solo_uso_no_aplica_a_residencial():
    r = aplica_solo_uso(_ctx(_f(), uso={"principal": "Residencial Vivienda"}),
                        {"usos": ["Industrial"]})
    assert r["resultado"] == "no-aplica"


def test_aplica_solo_uso_no_verificable_si_aplica():
    r = aplica_solo_uso(_ctx(_f(), uso={"principal": "Industrial"}),
                        {"usos": ["Industrial"]})
    assert r["resultado"] == "no-verificable"
    assert r.get("motivo_no_verificable")


# --- requiere-motor -------------------------------------------------------- #

def test_requiere_motor_declara_motivo():
    r = requiere_motor(_ctx(_f()), {"motivo": "requiere motor de evacuación"})
    assert r["resultado"] == "no-verificable"
    assert r["motivo_no_verificable"] == "requiere motor de evacuación"
