#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_plugin_obras_lineales.py — empaqueta el .plugin `obras-lineales` 0.4.0 desde el monorepo.

PR-E4 (Fase I · hilo 5): segundo plugin re-homed que NACE sin espejo. `plugins/obras-lineales`
no lleva copia commiteada del núcleo transversal (`ifc_utils`, `grafo_red`): la fuente única
es `packages/core` y este build la INYECTA vía `tools/_inyectar_nucleo.py` (fuente única de
la inyección desde este PR, tercer consumidor):

  scripts/nucleo/{ifc_utils,grafo_red}.py  ←  packages/core/src/aqyra_core/  (NÚCLEO)

Antes de zipar, PRUEBA que cada fichero inyectado es byte-a-byte idéntico a su anclaje md5
(LF) de `versions.lock [core]`: si el build no deriva del canónico, falla. Luego zipa a
dist/ y pasa la puerta `tools/verificar_empaquetado.py` con el frozen v0.4.0 como --ref.

Diferencia esperada vs el frozen: el nuevo .plugin no lleva `scripts/nucleo/{test_grafo_red.py,
README.md}` (artefactos de desarrollo del núcleo, igual que el piloto e instalaciones). En la
puerta, la ausencia de un .py de la ref es AVISO, no bloqueo: único aviso esperado =
test_grafo_red.py.

Uso:
    python3 tools/build_plugin_obras_lineales.py            # build + verificación intrínseca
    python3 tools/build_plugin_obras_lineales.py --ref <v0.4.0.plugin>   # + contraste de tamaños

Exit 0 = APTO (dist/plugins/obras-lineales-<v>.plugin listo para firmar/publicar).
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from _inyectar_nucleo import core_anchors as _core_anchors_from
from _inyectar_nucleo import inject_nucleo as _inject_nucleo_into

ROOT = Path(__file__).resolve().parents[1]
MEMBER = ROOT / "plugins" / "obras-lineales"
CORE = ROOT / "packages" / "core" / "src" / "aqyra_core"
# El staging es EFÍMERO y va fuera del árbol montado (el mount no borra en host).
STAGE = Path(tempfile.mkdtemp(prefix="obras-lineales-build-"))
DIST = ROOT / "dist" / "plugins"
LOCK = ROOT / "versions.lock"

# Rutas del miembro que NUNCA se copian al staging: carpetas generadas (gitignored).
SKIP_DIRS = (
    "scripts/nucleo",                                 # se REGENERA desde packages/core
)


def _core_anchors() -> dict[str, str]:
    """md5 anclados en versions.lock [core] — consumido de tools/_inyectar_nucleo.py."""
    return _core_anchors_from(LOCK)


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
    """Inyecta el núcleo en el staging — consumido de tools/_inyectar_nucleo.py (PR-E4)."""
    return _inject_nucleo_into(STAGE, CORE, anchors)


def _zip(version: str) -> Path:
    DIST.mkdir(parents=True, exist_ok=True)
    out = DIST / f"obras-lineales-{version}.plugin"
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
        default=str(ROOT / "_import" / "aqyra-motor" / "obras-lineales-v0.4.0.plugin"),
        help=".plugin previo (v0.4.0, frozen) para el contraste anti-truncado",
    )
    ap.add_argument(
        "--allow-shrink",
        default="",
        help="ficheros cuyo encogimiento vs --ref está auditado (ninguno esperado: re-home fiel)",
    )
    args = ap.parse_args()

    pj = json.loads((MEMBER / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    version = pj["version"]
    print(f"== build obras-lineales {version} ==")

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
