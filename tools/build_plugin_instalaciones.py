#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_plugin_instalaciones.py — empaqueta el .plugin `instalaciones` 0.3.0 desde el monorepo.

PR-E3 (Fase I · hilo 4): primer plugin re-homed que NACE sin espejo. `plugins/instalaciones`
no lleva copia commiteada del núcleo transversal (`ifc_utils`, `grafo_red`): la fuente única
es `packages/core` y este build la INYECTA:

  scripts/nucleo/{ifc_utils,grafo_red}.py  ←  packages/core/src/aqyra_core/  (NÚCLEO)

Antes de zipar, PRUEBA que cada fichero inyectado es byte-a-byte idéntico a su anclaje md5
(LF) de `versions.lock [core]`: si el build no deriva del canónico, falla. Luego zipa a
dist/ y pasa la puerta `tools/verificar_empaquetado.py` con el frozen v0.3.0 como --ref.

Diferencia esperada vs el frozen: el nuevo .plugin no lleva `scripts/nucleo/{test_grafo_red.py,
README.md}` (artefactos de desarrollo del núcleo, igual que el piloto). En la puerta, la
ausencia de un .py de la ref es AVISO, no bloqueo: único aviso esperado = test_grafo_red.py.

NOTA (factorización diferida): la inyección del núcleo está duplicada del builder del piloto
(`build_plugin_iso19650.py`). Con el TERCER consumidor (PR-E4, obras-lineales) se factoriza
a `tools/_inyectar_nucleo.py` — no se abstrae con n=2, y así este PR no toca el builder del
piloto.

Uso:
    python3 tools/build_plugin_instalaciones.py            # build + verificación intrínseca
    python3 tools/build_plugin_instalaciones.py --ref <v0.3.0.plugin>   # + contraste de tamaños

Exit 0 = APTO (dist/plugins/instalaciones-<v>.plugin listo para firmar/publicar).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEMBER = ROOT / "plugins" / "instalaciones"
CORE = ROOT / "packages" / "core" / "src" / "aqyra_core"
# El staging es EFÍMERO y va fuera del árbol montado (el mount no borra en host).
STAGE = Path(tempfile.mkdtemp(prefix="instalaciones-build-"))
DIST = ROOT / "dist" / "plugins"
LOCK = ROOT / "versions.lock"

# Ficheros de NÚCLEO que se inyectan en scripts/nucleo/ desde packages/core.
NUCLEO_FILES = ["ifc_utils.py", "grafo_red.py"]

# Rutas del miembro que NUNCA se copian al staging: carpetas generadas (gitignored).
SKIP_DIRS = (
    "scripts/nucleo",                                 # se REGENERA desde packages/core
)


def _md5_lf(p: Path) -> str:
    return hashlib.md5(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _core_anchors() -> dict[str, str]:
    """md5 anclados en versions.lock [core] (ifc_utils_md5 / grafo_red_md5)."""
    txt = LOCK.read_text(encoding="utf-8")
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


def _rel(p: Path) -> str:
    return p.relative_to(MEMBER).as_posix()


def _copy_member() -> None:
    """Copia el miembro al staging, saltando las carpetas generadas."""
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    for src in sorted(MEMBER.rglob("*")):
        rel = _rel(src)
        if "__pycache__" in src.parts or rel.endswith(".pyc"):
            continue
        if any(rel == d or rel.startswith(d + "/") for d in SKIP_DIRS):
            continue
        dst = STAGE / rel
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def _inject_nucleo(anchors: dict[str, str]) -> list[str]:
    """Inyecta el núcleo desde packages/core y prueba identidad vs versions.lock [core].

    El plugin no commitea scripts/nucleo/; se genera aquí desde el canónico. Los scripts
    del plugin lo consumen por sys.path (import ifc_utils / import grafo_red), sin
    __init__: se inyectan solo los dos módulos.
    """
    errores: list[str] = []
    nucleo = STAGE / "scripts" / "nucleo"
    nucleo.mkdir(parents=True, exist_ok=True)
    for name in NUCLEO_FILES:
        src = CORE / name
        if not src.exists():
            errores.append(f"núcleo ausente: packages/core/src/aqyra_core/{name}")
            continue
        shutil.copy2(src, nucleo / name)
        got, exp = _md5_lf(src), anchors.get(name)
        if not exp:
            errores.append(f"{name}: sin anclaje md5 en versions.lock [core]")
        elif got != exp:
            errores.append(f"{name}: md5 {got[:8]} != anclaje {exp[:8]} (build no deriva del canónico)")
    return errores


def _zip(version: str) -> Path:
    DIST.mkdir(parents=True, exist_ok=True)
    out = DIST / f"instalaciones-{version}.plugin"
    # modo "w" trunca un fichero existente (no requiere borrado — el mount no borra en host).
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(STAGE.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(STAGE).as_posix())
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--ref",
        default=str(ROOT / "_import" / "aqyra-motor" / "instalaciones-v0.3.0.plugin"),
        help=".plugin previo (v0.3.0, frozen) para el contraste anti-truncado",
    )
    ap.add_argument(
        "--allow-shrink",
        default="",
        help="ficheros cuyo encogimiento vs --ref está auditado (ninguno esperado: re-home fiel)",
    )
    args = ap.parse_args()

    pj = json.loads((MEMBER / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    version = pj["version"]
    print(f"== build instalaciones {version} ==")

    core_anchors = _core_anchors()
    if not core_anchors:
        print("ERROR: no pude leer los md5 de [core] de versions.lock", file=sys.stderr)
        return 1

    _copy_member()
    errs = _inject_nucleo(core_anchors)
    if errs:
        print("NO APTO — el núcleo inyectado no deriva del canónico:", file=sys.stderr)
        for e in errs:
            print("  -", e, file=sys.stderr)
        return 1
    print("  núcleo inyectado desde packages/core y verificado vs versions.lock [core] (identidad OK)")

    out = _zip(version)
    print(f"  empaquetado: {out.relative_to(ROOT)}  ({out.stat().st_size} B)")

    # Puerta de empaquetado (truncado, sintaxis, artefactos, semver)
    cmd = [sys.executable, str(ROOT / "tools" / "verificar_empaquetado.py"), str(out)]
    if args.ref:
        cmd += ["--ref", args.ref]
        if args.allow_shrink:
            cmd += ["--allow-shrink", args.allow_shrink]
    print("== verificar_empaquetado ==")
    r = subprocess.run(cmd)
    if r.returncode != 0:
        print("NO APTO — falló la puerta de empaquetado.", file=sys.stderr)
        return r.returncode
    print("APTO — .plugin listo para firmar/publicar (Llave 2: JM).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
