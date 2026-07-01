"""No-regresión de IDENTIDAD del núcleo — el paquete `aqyra_core` conserva byte a byte los
módulos del núcleo canónico de `Nucleo-transversal`.

En `Estructurando` la puerta `verificar_espejo_nucleo.py` comparaba cada espejo de plugin con
el canónico por hash. En el monorepo el espejo desaparece (un solo paquete), pero la garantía
de que la EXTRACCIÓN no cambió un byte se conserva aquí: md5 (normalizado a LF) de cada módulo
== el hash canónico anclado en `versions.lock`.

Un fallo aquí = alguien tocó el núcleo sin pasar por su golden de comportamiento; se corrige
en el código (o se re-ancla conscientemente el hash tras validar), nunca ignorando el test.
"""
import hashlib
from pathlib import Path

# Hashes del núcleo canónico (Nucleo-transversal/nucleo/), LF puro. Anclados en versions.lock.
CANONICO = {
    "ifc_utils.py": "ad06f87d648fc0388b35d10deeb290b7",
    "grafo_red.py": "fe5dfebb4c5adb73f90718d57978e8a4",
}

PKG = Path(__file__).resolve().parents[1] / "src" / "aqyra_core"


def _md5_lf(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n")  # EOL-agnóstico entre plataformas
    return hashlib.md5(data).hexdigest()


def test_nucleo_identico_al_canonico():
    for fname, expected in CANONICO.items():
        got = _md5_lf(PKG / fname)
        assert got == expected, (
            f"{fname} DIVERGE del canónico: {got[:8]} != {expected[:8]}. "
            "El núcleo se conserva byte a byte; corrige el código o re-ancla conscientemente."
        )
