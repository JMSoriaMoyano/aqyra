# -*- coding: utf-8 -*-
"""CLI mínima del adaptador BC3 (las dos direcciones de la frontera).

    aqyra-bc3 ingerir <muestra.bc3> --banco AQ-BC3-DEMO/v1 [--salida banco.json]
    aqyra-bc3 emitir  <salida-presupuesto.json> [--salida presupuesto.bc3]
                      [--charset utf-8|cp1252] [--fecha AAAAMMDD]

Traducción determinista .bc3 <-> Aqyra (E0.1 ingesta + E0.2 emisión). Git y anclaje
van por el flujo SDD; esto es una utilidad.
"""
from __future__ import annotations

import argparse
import json
import sys

from .bc3 import ingerir_bc3, serializar_banco, emitir_bc3


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="aqyra-bc3", description="Adaptador FIEBDC-3/2024 <-> Aqyra")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ing = sub.add_parser("ingerir", help="FIEBDC-3 (.bc3) -> pack banco (JSON)")
    ing.add_argument("bc3", help="ruta del .bc3 de entrada")
    ing.add_argument("--banco", required=True, help="identidad del pack, p. ej. AQ-BC3-DEMO/v1")
    ing.add_argument("--titulo", default=None, help="título (por defecto, la cabecera del ~V)")
    ing.add_argument("--ci-pct", default="0.03", help="costes indirectos v0 (default 0.03)")
    ing.add_argument("--salida", default=None, help="fichero de salida (por defecto, stdout)")

    emi = sub.add_parser("emitir", help="salida-presupuesto (JSON) -> FIEBDC-3 (.bc3)")
    emi.add_argument("salida_json", help="ruta de la salida-presupuesto (JSON de C5)")
    emi.add_argument("--salida", default=None, help="fichero .bc3 (por defecto, stdout)")
    emi.add_argument("--charset", default="utf-8", help="códec de salida (default utf-8; cp1252=ANSI)")
    emi.add_argument("--fecha", default=None, help="sello de fecha del ~V, AAAAMMDD (default determinista)")

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
    if args.cmd == "emitir":
        with open(args.salida_json, "r", encoding="utf-8") as f:
            salida = json.load(f)
        # la salida-presupuesto puede venir envuelta (p. ej. golden {"presupuesto": {...}})
        if "estado_mediciones" not in salida and isinstance(salida.get("presupuesto"), dict):
            salida = salida["presupuesto"]
        txt = emitir_bc3(salida, fecha=args.fecha, charset=args.charset)
        if args.salida:
            with open(args.salida, "w", encoding=args.charset, newline="") as f:
                f.write(txt)
        else:
            sys.stdout.write(txt)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
