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
