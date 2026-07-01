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
