"""No-regresión de IDENTIDAD del engine C1 — el corte mínimo importado a `engines/ifc`
conserva byte a byte el canónico `iso19650-openbim 0.10.0` (aguas arriba, hoy en
`_import/aqyra-motor`).

Réplica del patrón 0.5 (`test_identidad_nucleo`): en `Estructurando` el motor vivía DUPLICADO
en cada plugin; en el monorepo el engine es único (`engines/ifc`) y la garantía de que el IMPORT
no cambió un byte se conserva aquí: md5 (normalizado a LF, EOL-agnóstico) de cada fichero del
corte mínimo == el hash canónico anclado en `versions.lock [engines.ifc.md5]`.

Un fallo aquí = alguien tocó el engine importado sin pasar por su golden de comportamiento
(la golden C1-APERTURA-01 compila con estos ficheros). Se corrige en el código, o se re-ancla
conscientemente el hash tras validar contra la golden — nunca ignorando el test.
"""
import hashlib
from pathlib import Path

# Corte mínimo C1 (compile narración→IFC), LF puro. Anclados en versions.lock [engines.ifc.md5].
CANONICO = {
    "narracion-ifc/compilar_spec.py":                "eff7e9c34ba633480738afd9b8ac3565",
    "narracion-ifc/spec_to_ifc.py":                  "45284c396d37f1ee591abc9e2e7ded4f",
    "narracion-ifc/clasificacion.py":                "a5bc92893ed3db52475b14d481d83d2e",
    "narracion-ifc/catalogo_ifc.py":                 "6aabeac4663da34dd00a95a0f4a7b228",
    "narracion-ifc/catalogo-ifc4x3.json":            "84840734f3ad19120dd67254b2d2c43f",
    "narracion-ifc/alineaciones_ifc.py":             "da20508e06cd54435e0691fa32508311",
    "narracion-ifc/validar.py":                      "c45940bfd69ffd9e2dd663319254aef4",
    "narracion-ifc/spec.schema.json":                "a1db77f5771de282719429fa4aad2596",
    "scripts/lineal/generate_test_ifc_lineal.py":    "344f975b6e25a95dcce819c11f7089ad",
}

ENGINE = Path(__file__).resolve().parents[1]  # engines/ifc


def _md5_lf(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n")  # EOL-agnóstico entre plataformas
    return hashlib.md5(data).hexdigest()


def test_engine_ifc_identico_al_canonico():
    for rel, expected in CANONICO.items():
        got = _md5_lf(ENGINE / rel)
        assert got == expected, (
            f"{rel} DIVERGE del canónico 0.10.0: {got[:8]} != {expected[:8]}. "
            "El engine importado se conserva byte a byte; corrige el código o re-ancla "
            "conscientemente el hash tras validar contra la golden C1-APERTURA-01."
        )
