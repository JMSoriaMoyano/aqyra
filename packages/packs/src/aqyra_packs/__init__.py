"""aqyra_packs — cargador de packs versionados (`data/packs`).

Un **pack** es una unidad versionada de conocimiento externo (códigos, normativa, banco de
precios, IDS) que un engine consume; **no es código**. Cambiar de mercado/localidad/año =
cambiar de pack, no de engine. Este módulo carga un pack por familia/id/versión, valida su
manifiesto, calcula el hash de su contenido (identidad de la golden de pack) y resuelve la
versión anclada en `versions.lock`. Reproducibilidad (FUNDACION_C6 §3) = engine + pack anclados.

Ruta de un pack: `data/packs/<familia>/<id>/<version>/pack.json`.
"""
import hashlib
import json
from pathlib import Path

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # 3.10
    import tomli as tomllib

__version__ = "0.1.0"

FAMILIAS = {"codigos", "normativa", "banco", "ids"}


def pack_path(root, familia, ident, version) -> Path:
    return Path(root) / familia / ident / str(version) / "pack.json"


def load_pack(root, familia, ident, version) -> dict:
    """Carga el manifiesto de un pack (dict)."""
    return json.loads(pack_path(root, familia, ident, version).read_text(encoding="utf-8"))


def validate_manifest(manifest: dict, schema_path) -> None:
    """Valida el manifiesto contra `pack.schema.json`. Lanza si no conforma."""
    from jsonschema import Draft202012Validator

    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(manifest)


def content_hash(manifest: dict) -> str:
    """SHA-256 del bloque `contenido` (serialización canónica). Identidad de la golden de pack:
    si el contenido cambia sin bump de versión + actualizar la golden, el hash difiere."""
    data = json.dumps(manifest.get("contenido", {}), sort_keys=True,
                      separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def version_anclada(lock_path, clave):
    """Versión del pack anclada en `versions.lock` bajo `[packs.<clave>]` (o None)."""
    with open(lock_path, "rb") as f:
        lock = tomllib.load(f)
    return lock.get("packs", {}).get(clave, {}).get("version")
