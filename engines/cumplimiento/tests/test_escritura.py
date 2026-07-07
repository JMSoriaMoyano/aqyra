"""escribir_cumplimiento escribe Pset_Aqyra_Cumplimiento (D-6D-1), agrega el peor caso por
elemento (D-6D-2) y es DETERMINISTA. El helper `resultado_por_elemento` es puro (sin IFC)."""
from pathlib import Path

import pytest

from aqyra_cumplimiento.escritura import resultado_por_elemento

# --- Veredicto sintético que ejercita peor caso + neutro + por_modelo + exigencia global ---
VEREDICTO = {
    "pack": {"familia": "normativa", "id": "CTE", "version": "2019"},
    "exigencias": [
        {"id": "E-A", "documento_basico": "DB-SUA",
         "referencia": {"pack": "CTE/2019", "apartado": "SUA9"}, "resultado": "cumple",
         "por_modelo": {"arq": {"resultado": "cumple"}, "est": {"resultado": "no-aplica"}}},
        {"id": "E-B", "documento_basico": "DB-SI",
         "referencia": {"pack": "CTE/2019", "apartado": "SI6"}, "resultado": "no-cumple",
         "por_modelo": {"est": {"resultado": "no-cumple"}}},  # solo est
        {"id": "E-C", "documento_basico": "DB-HE",
         "referencia": {"pack": "CTE/2019", "apartado": "HE1"}, "resultado": "no-verificable",
         "motivo_no_verificable": "motor termico"},  # global (sin por_modelo)
    ],
}


def test_resultado_por_elemento_peor_caso():
    guid2mod = {"g-arq": "arq", "g-est": "est"}
    r = resultado_por_elemento(VEREDICTO, guid2mod)

    # arq: E-A=cumple(1), E-B no lista arq -> skip, E-C=no-verificable(2) global -> gana E-C
    assert r["g-arq"]["resultado"] == "no-verificable"
    assert r["g-arq"]["exigencia"] == "E-C"
    assert r["g-arq"]["motivo"] == "motor termico"

    # est: E-A=no-aplica(0), E-B=no-cumple(3), E-C=no-verificable(2) -> gana E-B (peor caso)
    assert r["g-est"]["resultado"] == "no-cumple"
    assert r["g-est"]["exigencia"] == "E-B"
    assert r["g-est"]["documento_basico"] == "DB-SI"
    assert r["g-est"]["pack"] == "CTE/2019"


def test_no_aplica_solo_si_todas_lo_son():
    ver = {"pack": {"id": "CTE", "version": "2019"},
           "exigencias": [
               {"id": "X", "documento_basico": "RSCIEI", "referencia": {"apartado": "-"},
                "resultado": "no-aplica", "por_modelo": {"arq": {"resultado": "no-aplica"}}}]}
    r = resultado_por_elemento(ver, {"g": "arq"})
    assert r["g"]["resultado"] == "no-aplica"


# --- Integración: requiere ifcopenshell (como test_medicion / test_escritura de presupuesto) ---
pytest.importorskip("ifcopenshell")


def _derivado_min(tmp: Path):
    """IFC derivado mínimo con dos muros (arq, est). Devuelve (ruta, guid2mod)."""
    import ifcopenshell
    import ifcopenshell.guid as guid

    f = ifcopenshell.file(schema="IFC4")
    g_arq, g_est = guid.new(), guid.new()
    f.create_entity("IfcWall", GlobalId=g_arq, Name="muro-arq")
    f.create_entity("IfcWall", GlobalId=g_est, Name="muro-est")
    ruta = tmp / "derivado.ifc"
    f.write(str(ruta))
    return ruta, {g_arq: "arq", g_est: "est"}


def test_determinista_y_pset(tmp_path):
    import ifcopenshell
    import ifcopenshell.util.element as ue
    from aqyra_cumplimiento.escritura import escribir_cumplimiento

    ruta, guid2mod = _derivado_min(tmp_path)
    maestro = {"ifc_derivado": ruta}

    r1 = escribir_cumplimiento(VEREDICTO, maestro, tmp_path / "a" / "6d.ifc", guid2mod=guid2mod)
    r2 = escribir_cumplimiento(VEREDICTO, maestro, tmp_path / "b" / "6d.ifc", guid2mod=guid2mod)
    assert r1["md5"] == r2["md5"]  # bytes identicos (mismo basename, dirs distintas)
    assert r1["n_elementos"] == 2
    assert r1["por_resultado"]["no-cumple"] == 1
    assert r1["por_resultado"]["no-verificable"] == 1

    f = ifcopenshell.open(str(tmp_path / "a" / "6d.ifc"))
    por_nombre = {w.Name: w for w in f.by_type("IfcWall")}
    ps_est = ue.get_psets(por_nombre["muro-est"])["Pset_Aqyra_Cumplimiento"]
    assert ps_est["Resultado"] == "no-cumple"
    assert ps_est["Exigencia"] == "E-B"
    ps_arq = ue.get_psets(por_nombre["muro-arq"])["Pset_Aqyra_Cumplimiento"]
    assert ps_arq["Resultado"] == "no-verificable"
    assert ps_arq["MotivoNoVerificable"] == "motor termico"
