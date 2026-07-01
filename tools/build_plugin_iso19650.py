#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_plugin_iso19650.py — empaqueta el .plugin `iso19650-openbim` 0.10.0 desde el monorepo.

PR-E1 (Fase I · hilo 2): retirada del espejo del engine. El compilador narración→IFC es
FUENTE ÚNICA en `engines/ifc`; el plugin NO lleva copia commiteada. Este build la INYECTA:

  skills/narracion-a-ifc/scripts/   ←  engines/ifc/narracion-ifc/*   (8 ficheros de ENGINE)
                                     +  plugins/.../narracion-a-ifc/_aux/*  (auxiliares no-engine)
  scripts/lineal/generate_test_ifc_lineal.py  ←  engines/ifc/scripts/lineal/  (ENGINE)

Antes de zipar, PRUEBA que cada fichero de engine inyectado es byte-a-byte idéntico al
anclaje md5 (LF) de `versions.lock [engines.ifc.md5]`: si el build no deriva del canónico,
falla. Luego zipa a dist/ y pasa la puerta `tools/verificar_empaquetado.py`.

Uso:
    python3 tools/build_plugin_iso19650.py            # build + verificación intrínseca
    python3 tools/build_plugin_iso19650.py --ref <0.9.2.plugin>   # + contraste de tamaños

Exit 0 = APTO (dist/plugins/iso19650-openbim-<v>.plugin listo para firmar/publicar).
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
MEMBER = ROOT / "plugins" / "iso19650-openbim"
ENGINE = ROOT / "engines" / "ifc"
NARRA = ENGINE / "narracion-ifc"
LINEAL = ENGINE / "scripts" / "lineal"
# El staging es EFÍMERO y va fuera del árbol montado (el mount no borra en host).
STAGE = Path(tempfile.mkdtemp(prefix="iso19650-build-"))
DIST = ROOT / "dist" / "plugins"
LOCK = ROOT / "versions.lock"

# Ficheros de ENGINE que se inyectan en skills/narracion-a-ifc/scripts/ (los 8 del corte
# narración→IFC). El fichero lineal se trata aparte por su ruta distinta.
ENGINE_NARRA = [
    "compilar_spec.py", "spec_to_ifc.py", "clasificacion.py", "catalogo_ifc.py",
    "catalogo-ifc4x3.json", "alineaciones_ifc.py", "validar.py", "spec.schema.json",
]
ENGINE_LINEAL = "generate_test_ifc_lineal.py"

# Rutas del miembro que NUNCA se copian al staging: son artefactos generados (gitignored)
# o fuentes auxiliares que se recolocan.
SKIP_REL = {
    "skills/narracion-a-ifc/scripts",                 # se REGENERA desde engine + _aux
    "scripts/lineal/generate_test_ifc_lineal.py",     # se REGENERA desde engine (leftover)
}
SKIP_AUX_DIR = "skills/narracion-a-ifc/_aux"           # su contenido va DENTRO de scripts/


def _md5_lf(p: Path) -> str:
    return hashlib.md5(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _anchors() -> dict[str, str]:
    """md5 anclados en versions.lock [engines.ifc.md5] (clave = basename)."""
    txt = LOCK.read_text(encoding="utf-8")
    out: dict[str, str] = {}
    in_block = False
    for line in txt.splitlines():
        s = line.strip()
        if s.startswith("[engines.ifc.md5]"):
            in_block = True
            continue
        if in_block and s.startswith("["):
            break
        if in_block:
            m = re.match(r'"([^"]+)"\s*=\s*"([0-9a-f]{32})"', s)
            if m:
                out[Path(m.group(1)).name] = m.group(2)
    return out


def _rel(p: Path) -> str:
    return p.relative_to(MEMBER).as_posix()


def _copy_member() -> None:
    """Copia el miembro al staging, saltando artefactos generados y el _aux."""
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    for src in sorted(MEMBER.rglob("*")):
        rel = _rel(src)
        if "__pycache__" in src.parts or rel.endswith(".pyc"):
            continue
        if rel in SKIP_REL or rel.startswith(SKIP_AUX_DIR):
            continue
        dst = STAGE / rel
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def _inject_engine(anchors: dict[str, str]) -> list[str]:
    """Inyecta el compilador desde engines/ifc y prueba identidad vs versions.lock."""
    errores: list[str] = []
    scripts = STAGE / "skills" / "narracion-a-ifc" / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)

    # 8 ficheros de engine
    for name in ENGINE_NARRA:
        src = NARRA / name
        if not src.exists():
            errores.append(f"engine ausente: engines/ifc/narracion-ifc/{name}")
            continue
        shutil.copy2(src, scripts / name)
        got, exp = _md5_lf(src), anchors.get(name)
        if exp and got != exp:
            errores.append(f"{name}: md5 {got[:8]} != anclaje {exp[:8]} (build no deriva del canónico)")

    # auxiliares no-engine (van dentro de scripts/, junto al compilador)
    aux = MEMBER / SKIP_AUX_DIR
    for a in sorted(aux.glob("*.py")):
        shutil.copy2(a, scripts / a.name)

    # fichero lineal de engine
    srcl = LINEAL / ENGINE_LINEAL
    dstl = STAGE / "scripts" / "lineal" / ENGINE_LINEAL
    dstl.parent.mkdir(parents=True, exist_ok=True)
    if not srcl.exists():
        errores.append(f"engine ausente: engines/ifc/scripts/lineal/{ENGINE_LINEAL}")
    else:
        shutil.copy2(srcl, dstl)
        got, exp = _md5_lf(srcl), anchors.get(ENGINE_LINEAL)
        if exp and got != exp:
            errores.append(f"{ENGINE_LINEAL}: md5 {got[:8]} != anclaje {exp[:8]}")
    return errores


def _zip(version: str) -> Path:
    DIST.mkdir(parents=True, exist_ok=True)
    out = DIST / f"iso19650-openbim-{version}.plugin"
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
        default=str(ROOT / "_import" / "aqyra-motor" / "iso19650-openbim-v0.9.2.plugin"),
        help=".plugin previo (0.9.2, frozen) para el contraste anti-truncado",
    )
    # Encogimientos AUDITADOS del salto 0.9.2→0.10.0 (evolución real, no truncado):
    #  - estructural/ifc_to_model_estructural.py y ifc-validate/checks-mep.py: refactor del plugin.
    #  - narracion-a-ifc/scripts/catalogo_ifc.py: es el canónico 0.10.0 de engines/ifc (más compacto).
    ap.add_argument(
        "--allow-shrink",
        default=(
            "scripts/estructural/ifc_to_model_estructural.py,"
            "skills/ifc-validate/references/checks-mep.py,"
            "skills/narracion-a-ifc/scripts/catalogo_ifc.py"
        ),
        help="ficheros cuyo encogimiento vs --ref está auditado",
    )
    args = ap.parse_args()

    pj = json.loads((MEMBER / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    version = pj["version"]
    print(f"== build iso19650-openbim {version} ==")

    anchors = _anchors()
    if not anchors:
        print("ERROR: no pude leer [engines.ifc.md5] de versions.lock", file=sys.stderr)
        return 1

    _copy_member()
    errs = _inject_engine(anchors)
    if errs:
        print("NO APTO — el engine inyectado no deriva del canónico:", file=sys.stderr)
        for e in errs:
            print("  -", e, file=sys.stderr)
        return 1
    print(f"  engine inyectado desde engines/ifc y verificado vs versions.lock (identidad OK)")

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
