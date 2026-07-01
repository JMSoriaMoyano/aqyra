"""No-regresión: el ESPEJO DEL ENGINE no reaparece (PR-E1, Fase I · hilo 2).

Con el compilador narración→IFC como FUENTE ÚNICA en `engines/ifc`, el plugin re-homed
`plugins/iso19650-openbim/` NO commitea su copia: la GENERA en build (tools/
build_plugin_iso19650.py copia engines/ifc → skills/narracion-a-ifc/scripts/). Este guardián
falla si cualquiera de esos ficheros del corte del engine REAPARECE **trackeado por git** fuera
de `engines/ifc` (y de la zona frozen `_import/`). Como la carpeta generada está gitignored, su
presencia en el índice de git = regresión (alguien re-empotró una copia).

Complemento (deuda acotada de PR-E2…E5): mientras el plugin conserve su copia del NÚCLEO
(`scripts/nucleo/`), se ata byte a byte al canónico `packages/core` para que no pueda divergir
antes de su retirada.

Compañeros en el gate: test_identidad_ifc.py (hash fijo) y test_espejo_ifc.py (vs procedencia).
"""
import hashlib
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]

# Ficheros del corte mínimo C1 (== anclajes de versions.lock [engines.ifc.md5]). Su hogar único
# es engines/ifc; cualquier copia trackeada fuera de ahí es el espejo reapareciendo.
CORTE_ENGINE = {
    "compilar_spec.py", "spec_to_ifc.py", "clasificacion.py", "catalogo_ifc.py",
    "catalogo-ifc4x3.json", "alineaciones_ifc.py", "validar.py", "spec.schema.json",
    "generate_test_ifc_lineal.py",
}

# Rutas exentas: el canónico y la zona firmada (frozen, no se reescribe).
EXENTO = ("engines/ifc/", "_import/")


def _tracked_files():
    r = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, text=True
    )
    if r.returncode != 0:
        pytest.skip("git no disponible / no es un checkout")
    return [p for p in r.stdout.split("\0") if p]


def _md5_lf(path: Path) -> str:
    return hashlib.md5(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_engine_no_reaparece_fuera_de_engines_ifc():
    reapariciones = [
        p for p in _tracked_files()
        if Path(p).name in CORTE_ENGINE and not p.startswith(EXENTO)
    ]
    assert not reapariciones, (
        "El ESPEJO DEL ENGINE reapareció (copias trackeadas del corte fuera de engines/ifc): "
        + ", ".join(sorted(reapariciones))
        + ". La fuente única es engines/ifc; conéctate a ella (build) en vez de re-empotrar."
    )


def test_nucleo_del_plugin_atado_al_canonico():
    """Deuda diferida (PR-E2…E5): la copia de núcleo del plugin no puede divergir del canónico."""
    canon = ROOT / "packages" / "core" / "src" / "aqyra_core"
    esperado = {f: _md5_lf(canon / f) for f in ("ifc_utils.py", "grafo_red.py")}
    copias = [
        ROOT / p for p in _tracked_files()
        if p.startswith("plugins/") and Path(p).parent.name == "nucleo"
        and Path(p).name in esperado
    ]
    for c in copias:
        got = _md5_lf(c)
        assert got == esperado[c.name], (
            f"{c.relative_to(ROOT).as_posix()} DIVERGE del canónico packages/core "
            f"({got[:8]} != {esperado[c.name][:8]}). El núcleo se retira en PR-E2…E5; hasta "
            "entonces la copia queda atada byte a byte al canónico."
        )
