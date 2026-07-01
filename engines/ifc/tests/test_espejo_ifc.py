"""Guardián del ESPEJO (no-regresión) — el engine canónico `engines/ifc` mantiene byte a byte
su PROCEDENCIA en `_import/aqyra-motor` (el canónico 0.10.0 importado por subtree, zona firmada
que NO se reescribe).

Contexto (Fase I · hilo 1): el motor estaba DUPLICADO aguas arriba en los plugins. En el
monorepo el engine es único (`engines/ifc`), pero la retirada de las copias aguas arriba se hace
por PR incremental en hilo aparte (ver `engines/ifc/ESPEJO_plan-retirada.md`). Mientras el espejo
viva, este guardián garantiza que el canónico del monorepo y su procedencia NO diverjan sin una
re-ancla consciente: md5 (LF-normalizado) de cada fichero de `engines/ifc` == el de su origen en
`_import/aqyra-motor`.

Complementa a `test_identidad_ifc` (que ancla contra hashes fijos vetados). Juntos: el canónico
queda fijado a la vez a un hash conocido y a su procedencia viva.

Si `_import/` no está disponible (checkout parcial), el test se omite: la retirada del espejo
aguas arriba es precisamente lo que, en su día, hará innecesaria esta comparación.
"""
import hashlib
from pathlib import Path

import pytest

ENGINE = Path(__file__).resolve().parents[1]          # engines/ifc
REPO = ENGINE.parents[1]                               # aqyra
IMPORT = REPO / "_import" / "aqyra-motor"              # procedencia (zona firmada, read-only)

# engines/ifc/<rel>  <->  _import/aqyra-motor/<procedencia>
PROCEDENCIA = {
    "narracion-ifc/compilar_spec.py":             "narracion-ifc/compilar_spec.py",
    "narracion-ifc/spec_to_ifc.py":               "narracion-ifc/spec_to_ifc.py",
    "narracion-ifc/clasificacion.py":             "narracion-ifc/clasificacion.py",
    "narracion-ifc/catalogo_ifc.py":              "narracion-ifc/catalogo_ifc.py",
    "narracion-ifc/catalogo-ifc4x3.json":         "narracion-ifc/catalogo-ifc4x3.json",
    "narracion-ifc/alineaciones_ifc.py":          "narracion-ifc/alineaciones_ifc.py",
    "narracion-ifc/validar.py":                   "narracion-ifc/validar.py",
    "narracion-ifc/spec.schema.json":             "narracion-ifc/spec.schema.json",
    "scripts/lineal/generate_test_ifc_lineal.py": "iso19650-openbim/scripts/lineal/generate_test_ifc_lineal.py",
}


def _md5_lf(path: Path) -> str:
    return hashlib.md5(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


@pytest.mark.parametrize("rel,origen", sorted(PROCEDENCIA.items()))
def test_engine_espeja_su_procedencia(rel, origen):
    src = IMPORT / origen
    if not src.exists():
        pytest.skip(f"procedencia ausente ({origen}); espejo ya retirado o checkout parcial")
    assert _md5_lf(ENGINE / rel) == _md5_lf(src), (
        f"{rel} DIVERGE de su procedencia {origen}. El canónico y su origen deben espejar "
        "byte a byte mientras el espejo viva; re-importa conscientemente o revierte el cambio."
    )
