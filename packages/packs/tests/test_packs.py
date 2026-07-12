"""Golden de pack (nivel esqueleto) — valida el manifiesto, ancla la versión y verifica la
identidad del contenido por hash. Sin engine todavía: cuando exista, el hash se sustituye por
el resultado de un proyecto de referencia bajo el pack (misma costura que el runner C1).
"""
import json
from pathlib import Path

import aqyra_packs as packs

REPO = Path(__file__).resolve().parents[3]
PACKS_ROOT = REPO / "data" / "packs"
SCHEMA = PACKS_ROOT / "pack.schema.json"
LOCK = REPO / "versions.lock"


def test_manifiesto_valido():
    m = packs.load_pack(PACKS_ROOT, "codigos", "EC-ES", "2021")
    packs.validate_manifest(m, SCHEMA)  # lanza si no conforma
    assert m["familia"] == "codigos" and m["version"] == "2021"


def test_version_anclada_en_lock():
    m = packs.load_pack(PACKS_ROOT, "codigos", "EC-ES", "2021")
    anclada = packs.version_anclada(LOCK, "codigo")
    assert anclada == m["version"], f"lock={anclada} != pack={m['version']}"


def test_identidad_contenido_golden():
    m = packs.load_pack(PACKS_ROOT, "codigos", "EC-ES", "2021")
    got = packs.content_hash(m)
    exp = json.loads(
        (PACKS_ROOT / "codigos/EC-ES/2021/golden/expected.json").read_text(encoding="utf-8")
    )["content_sha256"]
    assert got == exp, ("el contenido del pack cambió sin actualizar la golden. "
                        "Bump de versión + nuevo hash, nunca editar en silencio.")


# --- pack ids/proyecto-piloto/v1 (adoptado por C4, Fase II·h1) --------------------------

def test_manifiesto_ids_valido():
    m = packs.load_pack(PACKS_ROOT, "ids", "proyecto-piloto", "v1")
    packs.validate_manifest(m, SCHEMA)  # lanza si no conforma
    assert m["familia"] == "ids" and m["version"] == "v1"


def test_version_ids_anclada_en_lock():
    m = packs.load_pack(PACKS_ROOT, "ids", "proyecto-piloto", "v1")
    anclada = packs.version_anclada(LOCK, "ids")
    assert anclada == m["version"], f"lock={anclada} != pack={m['version']}"


def test_identidad_contenido_ids_golden():
    import hashlib
    m = packs.load_pack(PACKS_ROOT, "ids", "proyecto-piloto", "v1")
    got = packs.content_hash(m)
    exp = json.loads(
        (PACKS_ROOT / "ids/proyecto-piloto/v1/golden/expected.json").read_text(encoding="utf-8")
    )["content_sha256"]
    assert got == exp, ("el contenido del pack cambió sin actualizar la golden. "
                        "Bump de versión + nuevo hash, nunca editar en silencio.")
    # el md5 declarado en el manifiesto corresponde al .ids real (el hash ancla el fichero)
    ids_file = PACKS_ROOT / "ids/proyecto-piloto/v1" / m["contenido"]["fichero"]
    md5 = hashlib.md5(ids_file.read_bytes()).hexdigest()
    assert md5 == m["contenido"]["md5_ids"], "requisitos.ids cambió sin actualizar el manifiesto"


# --- pack normativa/CTE/2019 (adoptado por C3, Fase III·h2) ------------------------------

def test_manifiesto_cte_valido():
    m = packs.load_pack(PACKS_ROOT, "normativa", "CTE", "2019")
    packs.validate_manifest(m, SCHEMA)  # lanza si no conforma
    assert m["familia"] == "normativa" and m["version"] == "2019"


def test_version_cte_anclada_en_lock():
    m = packs.load_pack(PACKS_ROOT, "normativa", "CTE", "2019")
    anclada = packs.version_anclada(LOCK, "normativa")
    assert anclada == m["version"], f"lock={anclada} != pack={m['version']}"


def test_identidad_contenido_cte_golden():
    import hashlib
    m = packs.load_pack(PACKS_ROOT, "normativa", "CTE", "2019")
    got = packs.content_hash(m)
    exp = json.loads(
        (PACKS_ROOT / "normativa/CTE/2019/golden/expected.json").read_text(encoding="utf-8")
    )["content_sha256"]
    assert got == exp, ("el contenido del pack cambió sin actualizar la golden. "
                        "Bump de versión + nuevo hash, nunca editar en silencio.")
    # el md5 declarado en el manifiesto corresponde al exigencias.json real (el hash ancla el fichero)
    exig_file = PACKS_ROOT / "normativa/CTE/2019" / m["contenido"]["fichero"]
    md5 = hashlib.md5(exig_file.read_bytes()).hexdigest()
    assert md5 == m["contenido"]["md5_exigencias"], "exigencias.json cambió sin actualizar el manifiesto"


# --- pack criterio/AQ/v1 (adoptado por C5, Fase IV·h1) -----------------------------------

def test_manifiesto_criterio_valido():
    m = packs.load_pack(PACKS_ROOT, "criterio", "AQ", "v1")
    packs.validate_manifest(m, SCHEMA)  # lanza si no conforma
    assert m["familia"] == "criterio" and m["version"] == "v1"


def test_version_criterio_anclada_en_lock():
    m = packs.load_pack(PACKS_ROOT, "criterio", "AQ", "v1")
    anclada = packs.version_anclada(LOCK, "criterio")
    assert anclada == m["version"], f"lock={anclada} != pack={m['version']}"


def test_identidad_contenido_criterio_golden():
    import hashlib
    m = packs.load_pack(PACKS_ROOT, "criterio", "AQ", "v1")
    got = packs.content_hash(m)
    exp = json.loads(
        (PACKS_ROOT / "criterio/AQ/v1/golden/expected.json").read_text(encoding="utf-8")
    )["content_sha256"]
    assert got == exp, ("el contenido del pack cambió sin actualizar la golden. "
                        "Bump de versión + nuevo hash, nunca editar en silencio.")
    crit_file = PACKS_ROOT / "criterio/AQ/v1" / m["contenido"]["fichero"]
    md5 = hashlib.md5(crit_file.read_bytes()).hexdigest()
    assert md5 == m["contenido"]["md5_criterio"], "criterio.json cambió sin actualizar el manifiesto"


# --- pack criterio/AQ/v2 (superset E2.1: v1 + reglas_sistema, D22) -----------------------
# v2 NO re-ancla v1 ni la familia en versions.lock (sigue en v1 para GOL-PRE-01); v2 se ancla por
# su propio content_sha256. El mapeo clase→partida de v2 es IDÉNTICO a v1 (mide igual); v2 sólo
# añade la tabla reglas_sistema del fallback funcional. Lo adopta la golden de vista GOL-PRE-03 (E2.2).

def test_manifiesto_criterio_v2_valido():
    m = packs.load_pack(PACKS_ROOT, "criterio", "AQ", "v2")
    packs.validate_manifest(m, SCHEMA)  # lanza si no conforma
    assert m["familia"] == "criterio" and m["version"] == "v2"


def test_identidad_contenido_criterio_v2_golden():
    import hashlib
    m = packs.load_pack(PACKS_ROOT, "criterio", "AQ", "v2")
    got = packs.content_hash(m)
    exp = json.loads(
        (PACKS_ROOT / "criterio/AQ/v2/golden/expected.json").read_text(encoding="utf-8")
    )["content_sha256"]
    assert got == exp, ("el contenido del pack cambió sin actualizar la golden. "
                        "Bump de versión + nuevo hash, nunca editar en silencio.")
    crit_file = PACKS_ROOT / "criterio/AQ/v2" / m["contenido"]["fichero"]
    md5 = hashlib.md5(crit_file.read_bytes()).hexdigest()
    assert md5 == m["contenido"]["md5_criterio"], "criterio.json v2 cambió sin actualizar el manifiesto"


def test_criterio_v2_es_superset_de_v1():
    """v2 = v1 (mapeo IDÉNTICO) + reglas_sistema. v1 queda intacto (D22)."""
    v1 = json.loads((PACKS_ROOT / "criterio/AQ/v1/criterio.json").read_text(encoding="utf-8"))
    v2 = json.loads((PACKS_ROOT / "criterio/AQ/v2/criterio.json").read_text(encoding="utf-8"))
    assert v2["reglas_por_clase"] == v1["reglas_por_clase"], "el mapeo clase→partida NO debe cambiar entre ejes"
    assert v2["reglas_sin_geometria"] == v1["reglas_sin_geometria"]
    assert "reglas_sistema" not in v1 and "reglas_sistema" in v2, "reglas_sistema es la única novedad de v2"


# --- pack banco/AQ-DEMO/v1 (adoptado por C5, Fase IV·h1) ---------------------------------

def test_manifiesto_banco_valido():
    m = packs.load_pack(PACKS_ROOT, "banco", "AQ-DEMO", "v1")
    packs.validate_manifest(m, SCHEMA)  # lanza si no conforma
    assert m["familia"] == "banco" and m["version"] == "v1"


def test_version_banco_anclada_en_lock():
    m = packs.load_pack(PACKS_ROOT, "banco", "AQ-DEMO", "v1")
    anclada = packs.version_anclada(LOCK, "banco")
    assert anclada == m["version"], f"lock={anclada} != pack={m['version']}"


def test_identidad_contenido_banco_golden():
    import hashlib
    m = packs.load_pack(PACKS_ROOT, "banco", "AQ-DEMO", "v1")
    got = packs.content_hash(m)
    exp = json.loads(
        (PACKS_ROOT / "banco/AQ-DEMO/v1/golden/expected.json").read_text(encoding="utf-8")
    )["content_sha256"]
    assert got == exp, ("el contenido del pack cambió sin actualizar la golden. "
                        "Bump de versión + nuevo hash, nunca editar en silencio.")
    banco_file = PACKS_ROOT / "banco/AQ-DEMO/v1" / m["contenido"]["fichero"]
    md5 = hashlib.md5(banco_file.read_bytes()).hexdigest()
    assert md5 == m["contenido"]["md5_banco"], "banco.json cambió sin actualizar el manifiesto"


# --- pack banco/AQ-BC3-DEMO/v1 (E0.1: ingerido de un .bc3 FIEBDC-3/2024, engines/bc3) -----
# Banco de muestra PROPIO (D-026) materializado por aqyra_bc3.ingerir_bc3 desde fuente/muestra.bc3.
# NO re-mueve [packs.banco]=AQ-DEMO/v1 (se ancla por su propia clave [packs.banco_bc3]). Golden de
# pack por content_sha256 + md5(banco.json) + md5(muestra.bc3). El golden del PARSER (reproduce el
# banco.json desde el .bc3) vive en engines/bc3/tests/test_bc3.py.

def test_manifiesto_banco_bc3_valido():
    m = packs.load_pack(PACKS_ROOT, "banco", "AQ-BC3-DEMO", "v1")
    packs.validate_manifest(m, SCHEMA)  # lanza si no conforma
    assert m["familia"] == "banco" and m["version"] == "v1"


def test_version_banco_bc3_anclada_en_lock():
    m = packs.load_pack(PACKS_ROOT, "banco", "AQ-BC3-DEMO", "v1")
    anclada = packs.version_anclada(LOCK, "banco_bc3")
    assert anclada == m["version"], f"lock={anclada} != pack={m['version']}"


def test_identidad_contenido_banco_bc3_golden():
    import hashlib
    m = packs.load_pack(PACKS_ROOT, "banco", "AQ-BC3-DEMO", "v1")
    got = packs.content_hash(m)
    exp = json.loads(
        (PACKS_ROOT / "banco/AQ-BC3-DEMO/v1/golden/expected.json").read_text(encoding="utf-8")
    )["content_sha256"]
    assert got == exp, ("el contenido del pack cambió sin actualizar la golden. "
                        "Bump de versión + nuevo hash, nunca editar en silencio.")
    banco_file = PACKS_ROOT / "banco/AQ-BC3-DEMO/v1" / m["contenido"]["fichero"]
    md5 = hashlib.md5(banco_file.read_bytes()).hexdigest()
    assert md5 == m["contenido"]["md5_banco"], "banco.json cambió sin actualizar el manifiesto"
    bc3_file = PACKS_ROOT / "banco/AQ-BC3-DEMO/v1" / m["contenido"]["fuente_bc3"]
    md5_bc3 = hashlib.md5(bc3_file.read_bytes()).hexdigest()
    assert md5_bc3 == m["contenido"]["md5_bc3"], "muestra.bc3 cambió sin actualizar el manifiesto"


def test_banco_bc3_no_toca_aq_demo():
    # el pack de muestra BC3 es NUEVO; [packs.banco] sigue en AQ-DEMO/v1 (zona anclada intacta)
    assert packs.version_anclada(LOCK, "banco") == "v1"


# --- pack banco-carbono/generico/v1 (E3.2: eje carbono, FAMILIA NUEVA banco-carbono) -----
# Banco de carbono PROPIO/sintetico v0 (D-026): factores kgCO2e por partida con etapas EN 15978
# (A1A3/A4A5). Familia NUEVA banco-carbono (aditiva al enum). NO re-mueve [packs.banco]=AQ-DEMO/v1 ni
# [packs.criterio]=v1 (se ancla por su propia clave [packs.banco_carbono]). Consumidor: GOL-CAR-01 (E3.3).

def test_manifiesto_banco_carbono_valido():
    m = packs.load_pack(PACKS_ROOT, "banco-carbono", "generico", "v1")
    packs.validate_manifest(m, SCHEMA)  # lanza si no conforma (familia banco-carbono en el enum)
    assert m["familia"] == "banco-carbono" and m["version"] == "v1"


def test_version_banco_carbono_anclada_en_lock():
    # E5.2/D46: el pointer de produccion pasa a v2 (banco REAL). v1 (sintetico) coexiste anclado por su
    # propio content_sha256 (test de v1 mas abajo) y consumido explicitamente por GOL-CAR-01.
    m = packs.load_pack(PACKS_ROOT, "banco-carbono", "generico", "v2")
    anclada = packs.version_anclada(LOCK, "banco_carbono")
    assert anclada == m["version"] == "v2", f"lock={anclada} != pack={m['version']}"


def test_identidad_contenido_banco_carbono_golden():
    import hashlib
    m = packs.load_pack(PACKS_ROOT, "banco-carbono", "generico", "v1")
    got = packs.content_hash(m)
    exp = json.loads(
        (PACKS_ROOT / "banco-carbono/generico/v1/golden/expected.json").read_text(encoding="utf-8")
    )["content_sha256"]
    assert got == exp, ("el contenido del pack cambió sin actualizar la golden. "
                        "Bump de versión + nuevo hash, nunca editar en silencio.")
    banco_file = PACKS_ROOT / "banco-carbono/generico/v1" / m["contenido"]["fichero"]
    md5 = hashlib.md5(banco_file.read_bytes()).hexdigest()
    assert md5 == m["contenido"]["md5_banco"], "banco.json (carbono) cambió sin actualizar el manifiesto"


def test_banco_carbono_no_toca_zona_anclada():
    # el pack de carbono es NUEVO; [packs.banco] sigue en AQ-DEMO/v1 y [packs.criterio] en v1 (intacto)
    assert packs.version_anclada(LOCK, "banco") == "v1"
    assert packs.version_anclada(LOCK, "criterio") == "v1"


# --- pack banco-carbono/generico/v2 (E5.2: banco REAL derivado de fuentes ABIERTAS ratificadas) --------
# v2 = ADEME (Licence Ouverte 2.0) + ProBas (dl-de/by-2.0) + UK GHG (OGL v3.0), trazable por partida en
# banco.json>provenance. Es el POINTER de produccion en versions.lock ([packs.banco_carbono]=v2, D46). NO
# re-mueve [packs.banco]=AQ-DEMO/v1 ni [packs.criterio]=v1. Consumidor: GOL-CAR-02 (D48). generico/v1
# (sintetico) queda INTACTO (guarda mas abajo). NO deriva de Okobaudat/INIES/EC3/ICE (via limpia, N-04/D-026).

def test_manifiesto_banco_carbono_v2_valido():
    m = packs.load_pack(PACKS_ROOT, "banco-carbono", "generico", "v2")
    packs.validate_manifest(m, SCHEMA)  # lanza si no conforma (familia banco-carbono en el enum)
    assert m["familia"] == "banco-carbono" and m["version"] == "v2"


def test_identidad_contenido_banco_carbono_v2_golden():
    import hashlib
    m = packs.load_pack(PACKS_ROOT, "banco-carbono", "generico", "v2")
    got = packs.content_hash(m)
    exp = json.loads(
        (PACKS_ROOT / "banco-carbono/generico/v2/golden/expected.json").read_text(encoding="utf-8")
    )["content_sha256"]
    assert got == exp, ("el contenido del pack v2 cambio sin actualizar la golden. "
                        "Bump de version + nuevo hash, nunca editar en silencio.")
    banco_file = PACKS_ROOT / "banco-carbono/generico/v2" / m["contenido"]["fichero"]
    md5 = hashlib.md5(banco_file.read_bytes()).hexdigest()
    assert md5 == m["contenido"]["md5_banco"], "banco.json (carbono v2) cambio sin actualizar el manifiesto"


def test_banco_carbono_v1_intacto():
    # E5.2 solo ANADE v2; el v1 sintetico (que ancla GOL-CAR-01) queda INTACTO por hash.
    import hashlib
    m1 = packs.load_pack(PACKS_ROOT, "banco-carbono", "generico", "v1")
    assert packs.content_hash(m1) == "44d0cd3fd38986806710d5b0b085a240c31a0454684005e3954cf2d462878496"
    banco1 = PACKS_ROOT / "banco-carbono/generico/v1" / m1["contenido"]["fichero"]
    assert hashlib.md5(banco1.read_bytes()).hexdigest() == "47fb478796e3571f6dccf3426999de11"


# --- pack pliego-textos/AQ-DEMO/v1 (E4.1/E5.3: textos de prescripcion, FAMILIA NUEVA pliego-textos) ----
# Textos de prescripcion por partida/tipo de unidad. Familia NUEVA pliego-textos (aditiva al enum). Semilla
# PROPIA (Aqyra, demo); el texto normativo REAL (PG-3/CTE) entra por la via limpia (N-04). NO re-mueve ningun
# pack anclado (se ancla por su clave [packs.pliego_textos]). Consumidor: documentos/pliego + GOL-PLI-01.
def test_manifiesto_pliego_textos_valido():
    m = packs.load_pack(PACKS_ROOT, "pliego-textos", "AQ-DEMO", "v1")
    packs.validate_manifest(m, SCHEMA)  # lanza si no conforma (familia pliego-textos en el enum)
    assert m["familia"] == "pliego-textos" and m["version"] == "v1"


def test_version_pliego_textos_anclada_en_lock():
    m = packs.load_pack(PACKS_ROOT, "pliego-textos", "AQ-DEMO", "v1")
    anclada = packs.version_anclada(LOCK, "pliego_textos")
    assert anclada == m["version"]


def test_identidad_contenido_pliego_textos_golden():
    import hashlib
    m = packs.load_pack(PACKS_ROOT, "pliego-textos", "AQ-DEMO", "v1")
    got = packs.content_hash(m)
    exp = json.loads(
        (PACKS_ROOT / "pliego-textos/AQ-DEMO/v1/golden/expected.json").read_text(encoding="utf-8")
    )["content_sha256"]
    assert got == exp, ("el contenido del pack pliego-textos cambio sin actualizar la golden. "
                        "Bump de version + nuevo hash, nunca editar en silencio.")
    textos_file = PACKS_ROOT / "pliego-textos/AQ-DEMO/v1" / m["contenido"]["fichero"]
    md5 = hashlib.md5(textos_file.read_bytes()).hexdigest()
    assert md5 == m["contenido"]["md5_textos"], "textos.json cambio sin actualizar el manifiesto"


# --- pack banco/BCCA/v1 (Ola 4·E5.1: banco de coste REAL derivado de la BCCA, CC-BY 3.0) ---------------
# 7 partidas del criterio con precio + descomposicion REALES de la unidad de obra BCCA equivalente
# (Junta de Andalucia, edicion BCCA2023_V02 / FIEBDC-3/2020) + provenance por partida. El NUCLEO
# presupuestable se materializa por aqyra_bc3.ingerir_bc3 del .bc3 semilla (golden del PARSER en
# engines/bc3/tests/test_bc3.py, Opcion B/D52). NO mueve [packs.banco]=AQ-DEMO/v1 ni [packs.banco_bc3].
# Golden de pack por content_sha256 + md5(banco.json) + md5(.bc3 semilla). D49-D52.

def test_manifiesto_banco_bcca_valido():
    m = packs.load_pack(PACKS_ROOT, "banco", "BCCA", "v1")
    packs.validate_manifest(m, SCHEMA)  # lanza si no conforma
    assert m["familia"] == "banco" and m["version"] == "v1" and m["id"] == "BCCA"


def test_version_banco_bcca_anclada_en_lock():
    m = packs.load_pack(PACKS_ROOT, "banco", "BCCA", "v1")
    anclada = packs.version_anclada(LOCK, "banco_bcca")
    assert anclada == m["version"], f"lock={anclada} != pack={m['version']}"


def test_identidad_contenido_banco_bcca_golden():
    import hashlib
    m = packs.load_pack(PACKS_ROOT, "banco", "BCCA", "v1")
    got = packs.content_hash(m)
    exp = json.loads(
        (PACKS_ROOT / "banco/BCCA/v1/golden/expected.json").read_text(encoding="utf-8")
    )["content_sha256"]
    assert got == exp, ("el contenido del pack BCCA cambio sin actualizar la golden. "
                        "Bump de version + nuevo hash, nunca editar en silencio.")
    banco_file = PACKS_ROOT / "banco/BCCA/v1" / m["contenido"]["fichero"]
    assert hashlib.md5(banco_file.read_bytes()).hexdigest() == m["contenido"]["md5_banco"], \
        "banco.json (BCCA) cambio sin actualizar el manifiesto"
    bc3_file = PACKS_ROOT / "banco/BCCA/v1" / m["contenido"]["fuente_bc3"]
    assert hashlib.md5(bc3_file.read_bytes()).hexdigest() == m["contenido"]["md5_bc3"], \
        "el .bc3 semilla BCCA cambio sin actualizar el manifiesto"


def test_banco_bcca_no_toca_packs_anclados():
    # E5.1 solo ANADE banco/BCCA; los packs de coste anclados NO se mueven (zona anclada intacta)
    assert packs.version_anclada(LOCK, "banco") == "v1"          # AQ-DEMO
    assert packs.version_anclada(LOCK, "banco_bc3") == "v1"      # AQ-BC3-DEMO
    import hashlib
    md5 = lambda p: hashlib.md5((PACKS_ROOT / p).read_bytes()).hexdigest()
    assert md5("banco/AQ-DEMO/v1/banco.json") == "d0372b7b3c48a28677c17837c04fde4e"  # Slice A (resumen+texto) + Slice B (D-RB-7: clasificacion_gubim)
    assert md5("banco/AQ-BC3-DEMO/v1/banco.json") == "3d6c79494560ba9547e14a5a72b6d264"


# --- pack banco/BCCA-nativo/v1 (Ola 4b·E5.1b: coste REAL NATIVO, codigos BCCA sin recodificar) --------
# 6 unidades de obra BCCA con su CODIGO NATIVO (D53) + provenance. NUCLEO por aqyra_bc3.ingerir_bc3 del
# .bc3 curado (golden del PARSER en engines/bc3). NUEVA clave [packs.banco_bcca_nativo]: NO mueve
# [packs.banco]/[packs.banco_bc3]/[packs.banco_bcca]=BCCA/v1 (semilla). Golden por content_sha256 + md5s. D53-D55.

def test_manifiesto_banco_bcca_nativo_valido():
    m = packs.load_pack(PACKS_ROOT, "banco", "BCCA-nativo", "v1")
    packs.validate_manifest(m, SCHEMA)
    assert m["familia"] == "banco" and m["version"] == "v1" and m["id"] == "BCCA-nativo"


def test_version_banco_bcca_nativo_anclada_en_lock():
    m = packs.load_pack(PACKS_ROOT, "banco", "BCCA-nativo", "v1")
    anclada = packs.version_anclada(LOCK, "banco_bcca_nativo")
    assert anclada == m["version"], f"lock={anclada} != pack={m['version']}"


def test_identidad_contenido_banco_bcca_nativo_golden():
    import hashlib
    m = packs.load_pack(PACKS_ROOT, "banco", "BCCA-nativo", "v1")
    got = packs.content_hash(m)
    exp = json.loads((PACKS_ROOT / "banco/BCCA-nativo/v1/golden/expected.json").read_text(encoding="utf-8"))["content_sha256"]
    assert got == exp, "el contenido del pack BCCA-nativo cambio sin actualizar la golden. Bump + nuevo hash."
    banco_file = PACKS_ROOT / "banco/BCCA-nativo/v1" / m["contenido"]["fichero"]
    assert hashlib.md5(banco_file.read_bytes()).hexdigest() == m["contenido"]["md5_banco"]
    bc3_file = PACKS_ROOT / "banco/BCCA-nativo/v1" / m["contenido"]["fuente_bc3"]
    assert hashlib.md5(bc3_file.read_bytes()).hexdigest() == m["contenido"]["md5_bc3"]


def test_banco_bcca_nativo_codigos_son_bcca_nativos():
    banco = json.loads((PACKS_ROOT / "banco/BCCA-nativo/v1/banco.json").read_text(encoding="utf-8"))
    esperados = ["06LPC80000", "10CEE00001", "13IPP90016", "05HRL80010", "05HRP80010", "03HRZ80000"]
    assert [p["codigo"] for p in banco["partidas"]] == esperados
    for p in banco["partidas"]:
        pr = p.get("provenance", {})
        assert pr.get("licencia") == "CC-BY 3.0", f"{p['codigo']}: licencia"
        assert pr.get("codigo_bcca") == p["codigo"], f"{p['codigo']}: el codigo de partida DEBE ser el codigo BCCA nativo"
        assert "Junta de Andalucia" in pr.get("atribucion", ""), f"{p['codigo']}: atribucion"


def test_banco_bcca_nativo_no_toca_semilla_ni_anclados():
    assert packs.version_anclada(LOCK, "banco_bcca") == "v1"   # semilla BCCA (la ancla GOL-PRE-04)
    assert packs.version_anclada(LOCK, "banco") == "v1"        # AQ-DEMO
    assert packs.version_anclada(LOCK, "criterio") == "v1"     # pointer del criterio intacto


# --- pack criterio/AQ/v3 (E5.1b: corte NATIVO clase IFC -> codigo BCCA) --------------------------------
# v3 mapea 4 clases a codigos BCCA nativos + capitulos nativos; misma medicion que v1. [packs.criterio]
# sigue en v1 (GOL-PRE-01..04 intactas); v3 se ancla por su content_sha256. Consumidor: GOL-PRE-05.

def test_manifiesto_criterio_v3_valido():
    m = packs.load_pack(PACKS_ROOT, "criterio", "AQ", "v3")
    packs.validate_manifest(m, SCHEMA)
    assert m["familia"] == "criterio" and m["version"] == "v3"


def test_identidad_contenido_criterio_v3_golden():
    import hashlib
    m = packs.load_pack(PACKS_ROOT, "criterio", "AQ", "v3")
    got = packs.content_hash(m)
    exp = json.loads((PACKS_ROOT / "criterio/AQ/v3/golden/expected.json").read_text(encoding="utf-8"))["content_sha256"]
    assert got == exp, "el contenido del criterio v3 cambio sin actualizar la golden."
    crit_file = PACKS_ROOT / "criterio/AQ/v3" / m["contenido"]["fichero"]
    assert hashlib.md5(crit_file.read_bytes()).hexdigest() == m["contenido"]["md5_criterio"]


def test_criterio_v3_es_nativo_sin_puerta():
    crit = json.loads((PACKS_ROOT / "criterio/AQ/v3/criterio.json").read_text(encoding="utf-8"))
    clases = {r["clase"] for r in crit["reglas_por_clase"]}
    assert clases == {"IfcWall", "IfcSlab", "IfcColumn", "IfcFooting"}, "corte nativo de 4 clases (puerta=forward, D54)"
    codigos = {p["codigo"] for r in crit["reglas_por_clase"] for p in r["partidas"]}
    assert codigos == {"06LPC80000", "10CEE00001", "13IPP90016", "05HRL80010", "05HRP80010", "03HRZ80000"}
    assert "IfcDoor" not in clases
    assert crit.get("capitulos"), "v3 declara `capitulos` nativos (pack-overridable; el catalogo DEFAULT usa alias)"
