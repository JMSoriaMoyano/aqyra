#!/usr/bin/env python3
"""Orquestador de "solo lo afectado" (Fase 0).

Calcula qué objetivos del monorepo están afectados por un diff de git y, opcionalmente,
ejecuta su build/test. Sin Nx/Turbo/Bazel: un mapa carpeta->objetivo + git diff.
Cuando el grafo crezca, se sustituye este script por una herramienta dedicada sin tocar
la fachada `just`.

Uso:
    python tools/affected.py --base origin/main            # lista objetivos afectados
    python tools/affected.py --base origin/main --run test  # ejecuta el test de cada uno
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Mapa: prefijo de ruta -> conjunto de objetivos afectados.
# Regla de dependencia (Fase 0): tocar un contrato o el core reejecuta la golden,
# porque la golden es quien los ejercita.
PATH_TARGETS: list[tuple[str, set[str]]] = [
    ("packages/contracts/", {"golden"}),        # cambiar un esquema -> revalidar golden
    ("packages/golden/",    {"golden"}),
    ("packages/core/",      {"core"}),          # core -> sus tests (pytest)
    ("packages/packs/",     {"packs"}),         # loader de packs -> sus tests
    ("data/packs/",         {"packs"}),         # datos de packs -> golden de pack
    ("engines/",            {"ifc", "golden"}), # engine -> su identidad + la golden que lo compila
    ("apps/visor/",         {"visor"}),
    ("versions.lock",       {"golden", "core", "packs", "ifc"}),
    ("justfile",            {"golden", "visor", "core", "packs", "ifc"}),
    ("tools/",              {"golden", "visor", "core", "packs", "ifc"}),
    ("pyproject.toml",      {"golden", "core", "packs", "ifc"}),
]

# Cómo se construye/prueba cada objetivo (Fase 0). La golden es el test real.
RUN_COMMANDS: dict[str, dict[str, list[str]]] = {
    "golden": {
        "build": ["uv", "sync"],
        "test":  ["uv", "run", "--package", "aqyra-golden",
                  "aqyra-golden", "--golden-dir", "packages/golden"],
    },
    "core": {
        "build": ["uv", "sync"],
        "test":  ["uv", "run", "pytest", "packages/core", "-q"],
    },
    "packs": {
        "build": ["uv", "sync"],
        "test":  ["uv", "run", "pytest", "packages/packs", "-q"],
    },
    "ifc": {
        "build": ["uv", "sync"],
        "test":  ["uv", "run", "pytest", "engines/ifc", "-q"],
    },
    "visor": {
        "build": ["pnpm", "--filter", "visor", "build"],
        "test":  ["pnpm", "--filter", "visor", "test"],
    },
}

ALL_TARGETS = {"golden", "core", "packs", "ifc", "visor"}


def changed_files(base: str) -> list[str] | None:
    """Ficheros cambiados frente a `base`. None si no se puede resolver (repo nuevo)."""
    for rev in (f"{base}...HEAD", base, "HEAD~1"):
        try:
            out = subprocess.run(
                ["git", "diff", "--name-only", rev],
                cwd=REPO, capture_output=True, text=True, check=True,
            )
            return [ln.strip() for ln in out.stdout.splitlines() if ln.strip()]
        except subprocess.CalledProcessError:
            continue
    return None


def affected_targets(files: list[str]) -> set[str]:
    targets: set[str] = set()
    for f in files:
        for prefix, ts in PATH_TARGETS:
            if f == prefix or f.startswith(prefix):
                targets |= ts
    return targets


def main() -> int:
    ap = argparse.ArgumentParser(description="Objetivos afectados por el diff.")
    ap.add_argument("--base", default="origin/main", help="rama/commit base de comparación")
    ap.add_argument("--run", choices=["build", "test"], help="ejecuta esta acción por objetivo")
    args = ap.parse_args()

    files = changed_files(args.base)
    if files is None:
        # Repo nuevo o base inalcanzable: en Fase 0, todo es afectado (conservador).
        targets = set(ALL_TARGETS)
        print(f"[affected] base '{args.base}' inalcanzable -> asumo TODO afectado", file=sys.stderr)
    else:
        targets = affected_targets(files)
        print(f"[affected] {len(files)} fichero(s) cambiado(s) vs {args.base}", file=sys.stderr)

    ordered = [t for t in ("core", "packs", "ifc", "golden", "visor") if t in targets]
    if not ordered:
        print("[affected] nada afectado.", file=sys.stderr)
        return 0

    if not args.run:
        for t in ordered:
            print(t)
        return 0

    rc = 0
    for t in ordered:
        cmd = RUN_COMMANDS.get(t, {}).get(args.run)
        if not cmd:
            continue
        print(f"[affected] {args.run} :: {t} -> {' '.join(cmd)}", file=sys.stderr)
        try:
            subprocess.run(cmd, cwd=REPO, check=True)
        except FileNotFoundError:
            # Herramienta ausente (p. ej. pnpm en Fase 0): aviso, no fallo duro.
            print(f"[affected] herramienta ausente para '{t}', se omite.", file=sys.stderr)
        except subprocess.CalledProcessError as e:
            rc = e.returncode or 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
