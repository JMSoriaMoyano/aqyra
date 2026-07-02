"""CLI mínimo del service C4: aqyra-federacion federar|validar|emitir-bcf."""
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

    b = sub.add_parser("emitir-bcf",
                       help="emitir_bcf(informe, carpeta) → topics BCF 3.0 (1.2)")
    b.add_argument("--informe", type=Path, required=True,
                   help="informe QA (salida de validar)")
    b.add_argument("--carpeta", type=Path, required=True,
                   help="contenedor BCF a crear (el árbol ES el artefacto — D12)")
    b.add_argument("--caso", default=None,
                   help="semilla de los GUIDs deterministas (D13); por defecto: proyecto")
    b.add_argument("--autor", default=None)
    b.add_argument("--fecha", default=None, help='p. ej. "2026-07-02T00:00:00Z"')
    b.add_argument("--bcfzip", type=Path, default=None,
                   help="además, empaquetar el DERIVADO .bcfzip (sin anclar)")
    b.add_argument("-o", "--out", type=Path, default=None,
                   help="informe actualizado (emitido=true); por defecto stdout")

    args = ap.parse_args()
    if args.cmd == "federar":
        from .federar import federar_fichero
        salida = federar_fichero(args.reglas, args.base_dir, fecha=date.today().isoformat())
    elif args.cmd == "validar":
        from .qa import validar
        manifiesto = json.loads(args.manifiesto.read_text(encoding="utf-8"))
        salida = validar(manifiesto, args.pack_dir, args.base_dir)
    else:
        from .bcf import emitir_bcf, empaquetar_bcfzip
        informe = json.loads(args.informe.read_text(encoding="utf-8"))
        salida = emitir_bcf(informe, args.carpeta, caso=args.caso,
                            autor=args.autor, fecha=args.fecha)
        if args.bcfzip:
            empaquetar_bcfzip(args.carpeta, args.bcfzip)

    texto = json.dumps(salida, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.write_text(texto, encoding="utf-8")
    else:
        sys.stdout.write(texto)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
