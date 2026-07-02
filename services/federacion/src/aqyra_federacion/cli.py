"""CLI mínimo del service C4: aqyra-federacion federar|validar."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(prog="aqyra-federacion",
                                 description="Service C4 — federación (v0).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("federar", help="federar(ifcs[], reglas) → manifiesto")
    f.add_argument("--reglas", type=Path, required=True)
    f.add_argument("--base-dir", type=Path, default=None,
                   help="por defecto: la carpeta de reglas.json")
    f.add_argument("-o", "--out", type=Path, default=None, help="por defecto: stdout")

    v = sub.add_parser("validar", help="validar(maestro, ids) → informe QA")
    v.add_argument("--manifiesto", type=Path, required=True)
    v.add_argument("--pack-dir", type=Path, required=True,
                   help="data/packs/ids/<id>/<version>/")
    v.add_argument("--base-dir", type=Path, required=True,
                   help="directorio de los fichero_origen del manifiesto")
    v.add_argument("-o", "--out", type=Path, default=None)

    args = ap.parse_args()
    if args.cmd == "federar":
        from .federar import federar_fichero
        salida = federar_fichero(args.reglas, args.base_dir, fecha=date.today().isoformat())
    else:
        from .qa import validar
        manifiesto = json.loads(args.manifiesto.read_text(encoding="utf-8"))
        salida = validar(manifiesto, args.pack_dir, args.base_dir)

    texto = json.dumps(salida, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.write_text(texto, encoding="utf-8")
    else:
        sys.stdout.write(texto)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
