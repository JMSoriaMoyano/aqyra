"""CLI del engine C3: verificar un Maestro contra un pack normativo → veredicto (JSON).

    aqyra-cumplimiento --manifiesto M.json --base-dir DIR --pack data/packs/normativa/CTE/2019 \
        --uso "Residencial Vivienda" --pais España [...] [--derivado federado.ifc]

Pensado para inspección manual y para C7 (consumidor). El runner de la golden NO usa el CLI:
importa `verificar` por path (patrón engines/ifc), como cierra la costura en packages/golden.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .cumplimiento import verificar


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Engine C3 — veredicto de cumplimiento por exigencia.")
    ap.add_argument("--manifiesto", type=Path, required=True,
                    help="manifiesto del Maestro (JSON) — fuente de verdad, D1")
    ap.add_argument("--base-dir", type=Path, required=True,
                    help="directorio base para resolver fichero_origen y el derivado")
    ap.add_argument("--pack", type=Path, required=True,
                    help="directorio del pack normativo (data/packs/normativa/<id>/<version>)")
    ap.add_argument("--derivado", type=Path, default=None,
                    help="ruta al IFC derivado (si no, se resuelve del manifiesto)")
    ap.add_argument("--proyecto", default=None, help="nombre del proyecto para el encabezado")
    ap.add_argument("--uso", required=True, help="uso característico DECLARADO")
    ap.add_argument("--pais", default="España")
    ap.add_argument("--comunidad-autonoma", default=None)
    ap.add_argument("--provincia", default=None)
    ap.add_argument("--municipio", default=None)
    ap.add_argument("--zona-climatica-he", default=None)
    args = ap.parse_args(argv)

    manifiesto = json.loads(args.manifiesto.read_text(encoding="utf-8"))
    maestro = {"manifiesto": manifiesto, "base_dir": args.base_dir}
    if args.derivado is not None:
        maestro["ifc_derivado"] = args.derivado
    if args.proyecto:
        maestro["proyecto"] = args.proyecto
    localizacion = {k: v for k, v in (
        ("pais", args.pais), ("comunidad_autonoma", args.comunidad_autonoma),
        ("provincia", args.provincia), ("municipio", args.municipio),
        ("zona_climatica_he", args.zona_climatica_he)) if v is not None}

    veredicto = verificar(maestro, {"principal": args.uso}, localizacion, args.pack)
    json.dump(veredicto, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
