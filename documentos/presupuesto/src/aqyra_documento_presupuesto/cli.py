# -*- coding: utf-8 -*-
"""CLI del compositor: presupuesto.json (o expected.json de golden) -> .docx del despacho."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .compositor import componer_documento


def _cargar_presupuesto(p: Path) -> dict:
    """Acepta un salida-presupuesto directo o un expected.json de golden (clave `presupuesto`)."""
    data = json.loads(p.read_text(encoding="utf-8"))
    if "presupuesto" in data and "estado_mediciones" not in data:
        return data["presupuesto"]
    return data


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Compone el Documento de Presupuesto (.docx del despacho) desde el JSON C5.")
    ap.add_argument("entrada", type=Path, help="salida-presupuesto.json o expected.json de golden")
    ap.add_argument("-o", "--salida", type=Path, default=None, help="ruta del .docx de salida")
    ap.add_argument("--fecha", default=None, help="fecha determinista para la carátula")
    ap.add_argument("--autor", default=None, help="autor (técnico competente)")
    args = ap.parse_args(argv)

    presupuesto = _cargar_presupuesto(args.entrada)
    salida = args.salida or (args.entrada.parent / "Documento_Presupuesto.docx")
    ruta = componer_documento(presupuesto, {"salida": salida, "fecha": args.fecha,
                                            "autor": args.autor})
    print(f"Documento de Presupuesto: {ruta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
