# -*- coding: utf-8 -*-
"""CLI mínima del adaptador BC3.

    aqyra-bc3 ingerir <muestra.bc3> --banco AQ-BC3-DEMO/v1 [--salida banco.json]

Traducción determinista .bc3 -> banco.json (E0.1). La emisión (E0.2) se añade en el
siguiente change del hilo. Git y anclaje van por el flujo SDD; esto es una utilidad.
"""
from __future__ import annotations

import argparse
import sys

from .bc3 import ingerir_bc3, serializar_banco


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="aqyra-bc3", description="Adaptador FIEBDC-3/2024 <-> Aqyra")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ing = sub.add_parser("ingerir", help="FIEBDC-3 (.bc3) -> pack banco (JSON)")
    ing.add_argument("bc3", help="ruta del .bc3 de entrada")
    ing.add_argument("--banco", required=True, help="identidad del pack, p. ej. AQ-BC3-DEMO/v1")
    ing.add_argument("--titulo", default=None, help="título (por defecto, la cabecera del ~V)")
    ing.add_argument("--ci-pct", default="0.03", help="costes indirectos v0 (default 0.03)")
    ing.add_argument("--salida", default=None, help="fichero de salida (por defecto, stdout)")

    args = ap.parse_args(argv)
    if args.cmd == "ingerir":
        banco = ingerir_bc3(args.bc3, banco=args.banco, titulo=args.titulo,
                            costes_indirectos_pct=args.ci_pct)
        txt = serializar_banco(banco)
        if args.salida:
            with open(args.salida, "w", encoding="utf-8") as f:
                f.write(txt)
        else:
            sys.stdout.write(txt)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
