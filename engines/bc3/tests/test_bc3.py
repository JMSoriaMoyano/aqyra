# -*- coding: utf-8 -*-
"""Golden del parser BC3 (E0.1) — texto puro, corre en CI y en el sandbox (sin ifcopenshell).

Ancla que el adaptador `aqyra_bc3.ingerir_bc3` REPRODUCE de forma determinista el
`banco.json` anclado a partir de `fuente/muestra.bc3` (D30–D33). Un cambio del parser
o del .bc3 que altere el banco rompe el test — el fallo se corrige en el CÓDIGO, jamás
editando el banco anclado.
"""
import hashlib
import json
from decimal import Decimal
from pathlib import Path

from aqyra_bc3 import ingerir_bc3, serializar_banco

REPO = Path(__file__).resolve().parents[3]
PACK = REPO / "data" / "packs" / "banco" / "AQ-BC3-DEMO" / "v1"
MUESTRA = PACK / "fuente" / "muestra.bc3"
BANCO = PACK / "banco.json"


def _ingerir():
    return ingerir_bc3(MUESTRA, banco="AQ-BC3-DEMO/v1")


def test_reproduce_el_banco_anclado():
    """El .bc3 de muestra -> exactamente el banco.json anclado (byte a byte)."""
    got = serializar_banco(_ingerir())
    exp = BANCO.read_text(encoding="utf-8")
    assert got == exp, "el parser no reproduce el banco.json anclado (drift del adaptador o del .bc3)"


def test_determinismo_2x():
    assert serializar_banco(_ingerir()) == serializar_banco(_ingerir())


def test_md5_banco_casa_con_el_manifiesto():
    got = serializar_banco(_ingerir()).encode("utf-8")
    manif = json.loads((PACK / "pack.json").read_text(encoding="utf-8"))
    assert hashlib.md5(got).hexdigest() == manif["contenido"]["md5_banco"]
    assert hashlib.md5(MUESTRA.read_bytes()).hexdigest() == manif["contenido"]["md5_bc3"]


def test_transcodificacion_ansi_a_utf8():
    """El .bc3 está en ANSI (cp1252); el banco sale en UTF-8 con los acentos intactos."""
    raw = MUESTRA.read_bytes()
    assert b"\xe1" in raw or b"\xf3" in raw, "la muestra debe llevar bytes ANSI (á/ó) para ejercitar la transcodificación"
    banco = _ingerir()
    descrs = [p["descripcion"] for p in banco["partidas"]]
    comps = [c["descripcion"] for p in banco["partidas"] for c in p["componentes"]]
    assert any("Fábrica" in d for d in descrs)          # partida (á)
    assert any("hormigón" in d for d in descrs)          # partida (ó)
    assert any("Hormigón" in c for c in comps)           # componente (ó, mayúscula)


def test_naturaleza_de_componentes():
    """El campo `tipo` del ~C mapea a mano_obra/maquinaria/material (D31)."""
    banco = _ingerir()
    rev = next(p for p in banco["partidas"] if p["codigo"] == "REV010")
    tipos = {c["descripcion"]: c["tipo"] for c in rev["componentes"]}
    assert tipos["Oficial 1ª construcción"] == "mano_obra"
    assert tipos["Mortero de cemento M-5"] == "material"
    assert tipos["Hormigonera"] == "maquinaria"


def test_precio_compuesto_y_ci():
    """precio = Σ subtotales + CI(3%), redondeo HALF_UP; casa con el ~C (D32)."""
    banco = _ingerir()
    fab = next(p for p in banco["partidas"] if p["codigo"] == "FAB010")
    suma = sum(Decimal(str(c["subtotal"])) for c in fab["componentes"])
    assert suma == Decimal("30.50")
    assert fab["costes_indirectos"] == 0.92      # 30.50 * 0.03 -> 0.915 -> 0.92
    assert fab["precio"] == 31.42                 # 30.50 + 0.92
    assert banco["costes_indirectos_pct"] == 0.03


def test_sin_avisos_cuando_el_precio_cuadra():
    """La muestra es consistente: el precio compuesto casa con el ~C -> sin avisos."""
    assert "_avisos_ingesta" not in _ingerir()


def test_guarda_detecta_precio_incoherente(tmp_path):
    """Si el ~C declara un precio que NO casa con la descomposición, se avisa (no se silencia)."""
    lineas = MUESTRA.read_bytes().decode("cp1252").split("\r\n")
    # falsear el precio declarado de FAB010 (31.42 -> 99.99)
    lineas = [l.replace("|31.42|", "|99.99|") if l.startswith("~C|FAB010|") else l for l in lineas]
    fake = tmp_path / "fake.bc3"
    fake.write_bytes("\r\n".join(lineas).encode("cp1252"))
    banco = ingerir_bc3(fake, banco="X/v1")
    assert "_avisos_ingesta" in banco
    assert any("FAB010" in a for a in banco["_avisos_ingesta"])


# --- banco/BCCA/v1 (Ola 4·E5.1): golden del PARSER por la VIA LIMPIA (Opcion B, D52) -----------------
# El .bc3 semilla (7 unidades BCCA reales recodificadas a los codigos del criterio) reproduce el NUCLEO
# presupuestable (codigo/unidad/componentes/costes_indirectos/precio) del banco.json anclado. La
# descripcion honesta y el bloque `provenance` (codigo BCCA + licencia CC-BY 3.0 + atribucion) son
# metadatos ADITIVOS del pack (el adaptador no los emite): asi el determinismo del PRECIO -que sale del
# .bc3, no se inventa- queda anclado sin tocar engines/bc3 (0.2.0 INTOCABLE). costes_indirectos_pct=0
# (el precio BCCA declarado = suma de la descomposicion).
BCCA = REPO / "data" / "packs" / "banco" / "BCCA" / "v1"
BCCA_BC3 = BCCA / "fuente" / "BCCA.bc3"
BCCA_BANCO = BCCA / "banco.json"
_SUBSET_PRESUP = ("codigo", "unidad", "componentes", "costes_indirectos", "precio")


def _ingerir_bcca():
    return ingerir_bc3(BCCA_BC3, banco="BCCA/v1", costes_indirectos_pct="0")


def _subset_presup(p):
    return {k: p[k] for k in _SUBSET_PRESUP}


def test_bcca_parser_reproduce_nucleo_presupuestable():
    """ingerir_bc3(semilla) reproduce el nucleo presupuestable del banco.json anclado (Opcion B/D52)."""
    got = _ingerir_bcca()
    banco = json.loads(BCCA_BANCO.read_text(encoding="utf-8"))
    assert [_subset_presup(p) for p in got["partidas"]] == [_subset_presup(p) for p in banco["partidas"]], \
        "el parser no reproduce el nucleo presupuestable del banco BCCA (drift del adaptador o del .bc3)"


def test_bcca_determinismo_2x():
    assert serializar_banco(_ingerir_bcca()) == serializar_banco(_ingerir_bcca())


def test_bcca_sin_avisos_de_ingesta():
    got = _ingerir_bcca()
    assert "_avisos_ingesta" not in got, got.get("_avisos_ingesta")


def test_bcca_md5_casa_con_el_manifiesto():
    import hashlib
    manif = json.loads((BCCA / "pack.json").read_text(encoding="utf-8"))
    assert hashlib.md5(BCCA_BANCO.read_bytes()).hexdigest() == manif["contenido"]["md5_banco"]
    assert hashlib.md5(BCCA_BC3.read_bytes()).hexdigest() == manif["contenido"]["md5_bc3"]


def test_bcca_provenance_trazable_por_partida():
    banco = json.loads(BCCA_BANCO.read_text(encoding="utf-8"))
    assert len(banco["partidas"]) == 7
    for p in banco["partidas"]:
        pr = p.get("provenance", {})
        assert pr.get("licencia") == "CC-BY 3.0", f"{p['codigo']}: licencia != CC-BY 3.0"
        assert pr.get("codigo_bcca"), f"{p['codigo']}: sin codigo_bcca de origen"
        assert "Junta de Andalucia" in pr.get("atribucion", ""), f"{p['codigo']}: sin atribucion"
