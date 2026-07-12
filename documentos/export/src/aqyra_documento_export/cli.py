# -*- coding: utf-8 -*-
"""CLI minima del export firmable.

    aqyra-documento-export componer <artefacto.json> <descriptor.json> [--salida DIR]
    aqyra-documento-export firmar   <bundle_dir> [--key KEYID]     # RELEASE-TIME (GPG de JM)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .export import componer_export
from .firma import firmar_detached


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="aqyra-documento-export",
                                 description="Export firmable de artefactos autoritativos de Aqyra")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("componer", help="artefacto + descriptor -> bundle firmable")
    c.add_argument("artefacto", help="JSON del artefacto autoritativo (p.ej. proyeccion)")
    c.add_argument("descriptor", help="JSON del descriptor de export")
    c.add_argument("--salida", default=None, help="carpeta del bundle (por defecto ./export_bundle)")

    f = sub.add_parser("firmar", help="RELEASE-TIME: firma GPG detached del manifiesto (JM)")
    f.add_argument("bundle", help="carpeta del bundle")
    f.add_argument("--key", default=None, help="KEYID GPG de JM")

    args = ap.parse_args(argv)
    if args.cmd == "componer":
        artefacto = json.loads(Path(args.artefacto).read_text(encoding="utf-8"))
        descriptor = json.loads(Path(args.descriptor).read_text(encoding="utf-8"))
        bundle = componer_export(artefacto, descriptor, {"salida": args.salida} if args.salida else None)
        sys.stdout.write(str(bundle) + "\n")
        return 0
    if args.cmd == "firmar":
        asc = firmar_detached(Path(args.bundle), key=args.key)
        sys.stdout.write(str(asc) + "\n")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
