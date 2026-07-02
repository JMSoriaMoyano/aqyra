#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_inyectar_nucleo.py — inyección del NÚCLEO transversal en los builds de plugins.

PR-E4 (Fase I · hilo 5): con el TERCER consumidor (obras-lineales) muere la duplicación
(~45 líneas por builder, criterio anclado en NUCLEO_PR-E3_cierre.md). Fuente única del
núcleo: `packages/core/src/aqyra_core/`. Cada builder llama:

    from _inyectar_nucleo import inject_nucleo, core_anchors, md5_lf

    anchors = core_anchors(LOCK)                 # md5 anclados en versions.lock [core]
    errs = inject_nucleo(STAGE, CORE, anchors)   # copia + prueba de identidad md5-LF

El contrato NO cambia respecto a los builders de PR-E2/E3: el plugin no commitea
`scripts/nucleo/`; se genera en el staging desde el canónico, y cada fichero inyectado
debe ser byte a byte (LF) idéntico a su anclaje de `versions.lock [core]` — si el build
no deriva del canónico, la lista de errores devuelta hace fallar el build (NO APTO).
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

# Ficheros de NÚCLEO que se inyectan en scripts/nucleo/. Los scripts de los plugins los
# consumen por sys.path (import ifc_utils / import grafo_red), sin __init__.
NUCLEO_FILES = ["ifc_utils.py", "grafo_red.py"]


def md5_lf(p: Path) -> str:
    """md5 con normalización de fin de línea a LF (identidad estable Windows/Linux)."""
    return hashlib.md5(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def core_anchors(lock: Path) -> dict[str, str]:
    """md5 anclados en versions.lock [core] (ifc_utils_md5 / grafo_red_md5)."""
    txt = lock.read_text(encoding="utf-8")
    out: dict[str, str] = {}
    in_block = False
    for line in txt.splitlines():
        s = line.strip()
        if s.startswith("[core]"):
            in_block = True
            continue
        if in_block and s.startswith("["):
            break
        if in_block:
            m = re.match(r'(\w+)_md5\s*=\s*"([0-9a-f]{32})"', s)
            if m:
                out[m.group(1) + ".py"] = m.group(2)
    return out


def inject_nucleo(stage: Path, core: Path, anchors: dict[str, str]) -> list[str]:
    """Inyecta el núcleo desde packages/core en <stage>/scripts/nucleo/ y prueba identidad.

    Devuelve la lista de errores (vacía = identidad OK). El builder que la reciba no vacía
    debe terminar NO APTO: el build no deriva del canónico.
    """
    import shutil

    errores: list[str] = []
    nucleo = stage / "scripts" / "nucleo"
    nucleo.mkdir(parents=True, exist_ok=True)
    for name in NUCLEO_FILES:
        src = core / name
        if not src.exists():
            errores.append(f"núcleo ausente: packages/core/src/aqyra_core/{name}")
            continue
        shutil.copy2(src, nucleo / name)
        got, exp = md5_lf(src), anchors.get(name)
        if not exp:
            errores.append(f"{name}: sin anclaje md5 en versions.lock [core]")
        elif got != exp:
            errores.append(f"{name}: md5 {got[:8]} != anclaje {exp[:8]} (build no deriva del canónico)")
    return errores
