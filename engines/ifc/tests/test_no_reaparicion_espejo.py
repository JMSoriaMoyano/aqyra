"""No-regresión: NI el ESPEJO DEL ENGINE (PR-E1) NI el DEL NÚCLEO (PR-E2) reaparecen.

Con el compilador narración→IFC como FUENTE ÚNICA en `engines/ifc` y el núcleo transversal
como FUENTE ÚNICA en `packages/core`, el plugin re-homed `plugins/iso19650-openbim/` NO
commitea copia de ninguno: las GENERA en build (tools/build_plugin_iso19650.py copia
engines/ifc → skills/narracion-a-ifc/scripts/ y packages/core → scripts/nucleo/). Este
guardián falla si cualquier fichero del corte del engine o del núcleo REAPARECE **trackeado
por git** fuera de su canónico (y de la zona frozen `_import/`). Como las carpetas generadas
están gitignored, su presencia en el índice de git = regresión (alguien re-empotró una copia).

Los plugins aún NO re-homados (`motor-fem`, `obras-lineales`, `instalaciones`, `puentes`)
solo existen como `.plugin` frozen en `_import/` — exentos hasta su re-home (PR-E3…E6),
donde esta misma regla les aplicará al entrar en `plugins/`.

Compañeros en el gate: test_identidad_ifc.py (hash fijo), test_espejo_ifc.py (vs
procedencia) y packages/core/tests/test_identidad_nucleo.py (identidad del canónico).
"""
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

# Ficheros del NÚCLEO transversal (== anclajes de versions.lock [core]). Su hogar único es
# packages/core; cualquier copia trackeada fuera de ahí es el espejo del núcleo reapareciendo.
NUCLEO = {"ifc_utils.py", "grafo_red.py"}

# Rutas exentas: los canónicos y la zona firmada (frozen, no se reescribe).
EXENTO = ("engines/ifc/", "_import/")
EXENTO_NUCLEO = ("packages/core/", "_import/")


def _tracked_files():
    r = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, text=True
    )
    if r.returncode != 0:
        pytest.skip("git no disponible / no es un checkout")
    return [p for p in r.stdout.split("\0") if p]


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


def test_nucleo_no_reaparece_fuera_de_core():
    """PR-E2 (Fase I · hilo 3): el ESPEJO DEL NÚCLEO retirado no puede reaparecer trackeado.

    Sustituye a `test_nucleo_del_plugin_atado_al_canonico` (la copia atada del piloto ya
    no existe: se genera en build). La fuente única es packages/core/src/aqyra_core.
    """
    reapariciones = [
        p for p in _tracked_files()
        if Path(p).name in NUCLEO and not p.startswith(EXENTO_NUCLEO)
    ]
    assert not reapariciones, (
        "El ESPEJO DEL NÚCLEO reapareció (copias trackeadas de ifc_utils/grafo_red fuera "
        "de packages/core): " + ", ".join(sorted(reapariciones))
        + ". La fuente única es packages/core; conéctate a ella (inyección en build, "
        "tools/build_plugin_iso19650.py) en vez de re-empotrar."
    )
