"""Guardia de conformidad SDD (Llave 1, proceso).

Falla si un PR toca CÓDIGO DE FUNCIONALIDAD o CONTRATOS sin traer su cambio en
`openspec/changes/<x>/`. Convierte la regla de `docs/PROCESO_SDD.md` en una puerta del CI: todo
desarrollo pasa por el flujo SDD (enrich-us -> opsx:propose -> ratificar -> opsx:apply).

Base de comparación: `--base` (por defecto `origin/main`), igual que `tools/affected.py`.
Excepción auditable: si el PR lleva la etiqueta `sin-spec` (variable de entorno PR_LABELS que la
incluye), el guardia AVISA pero no bloquea — la revisión humana de JM decide.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

# Rutas que, si cambian, EXIGEN un cambio en openspec/changes/.
PREFIJOS_FEATURE = (
    "engines/", "services/", "apps/", "packages/core/", "packages/packs/",
    "documentos/", "packages/contracts/",
)
# Rutas exentas (gobierno, infra, docs, herencia, scratch): no disparan por sí solas.
PREFIJOS_EXENTOS = (
    "openspec/", "docs/", "tools/", ".github/", "_operativo/",
    "sdd-aqyra", "versions.lock", "README", "CODEOWNERS",
    "AGENTS.md", "CLAUDE.md", "GEMINI.md", "codex.md",
    "pnpm-lock.yaml", "uv.lock", "justfile", "pyproject.toml", "package.json",
    ".gitattributes", ".gitignore", ".gitmodules",
)


def ficheros_cambiados(base: str) -> list[str]:
    rango = f"{base}...HEAD"
    out = subprocess.check_output(["git", "diff", "--name-only", rango], text=True)
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get("SDD_BASE", "origin/main"))
    args = ap.parse_args()

    try:
        files = ficheros_cambiados(args.base)
    except subprocess.CalledProcessError as e:
        print(f"[conformidad-sdd] no se pudo calcular el diff contra {args.base}: {e}")
        return 0  # no bloquear por un problema de git; el resto del gate sigue

    toca_feature = [f for f in files if f.startswith(PREFIJOS_FEATURE)]
    hay_change = any(f.startswith("openspec/changes/") for f in files)

    if not toca_feature or hay_change:
        print(f"[conformidad-sdd] OK ({len(files)} ficheros; feature={len(toca_feature)}; "
              f"openspec/changes={'si' if hay_change else 'no'})")
        return 0

    etiquetas = (os.environ.get("PR_LABELS", "") or "").lower()
    exento = "sin-spec" in etiquetas

    print("[conformidad-sdd] Se toca CÓDIGO DE FEATURE/CONTRATO sin un cambio en openspec/changes/:")
    for f in toca_feature:
        print("   -", f)
    print("  Todo desarrollo va por el flujo SDD (docs/PROCESO_SDD.md):")
    print("    enrich-us -> opsx:propose (crea openspec/changes/<x>/) -> ratificar decisiones -> opsx:apply")
    if exento:
        print("  [AVISO] etiqueta 'sin-spec' presente: NO se bloquea; revisión humana de JM (Llave 2).")
        return 0
    print("  Si es un hotfix legítimo sin spec, etiqueta el PR 'sin-spec' (excepción auditable).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
