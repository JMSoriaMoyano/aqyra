# -*- coding: utf-8 -*-
"""CLI del compositor: presupuesto.json (o expected.json de golden) + criterio + pack de textos -> .docx."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .compositor import componer_pliego


def _cargar_presupuesto(p: Path) -> dict:
    """Acepta un salida-presupuesto directo o un expected.json de golden (clave `presupuesto`)."""
    data = json.loads(p.read_text(encoding="utf-8"))
    if "presupuesto" in data and "estado_mediciones" not in data:
        return data["presupuesto"]
    return data


def _cargar_json(p: Path | None) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p else {}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Compone el Pliego de Condiciones Tecnicas (.docx del despacho) desde el JSON C5.")
    ap.add_argument("entrada", type=Path, help="salida-presupuesto.json o expected.json de golden")
    ap.add_argument("-c", "--criterio", type=Path, default=None, help="criterio.json (mapeo partida->sistema)")
    ap.add_argument("-t", "--textos", type=Path, default=None, help="textos.json del pack pliego-textos")
    ap.add_argument("-o", "--salida", type=Path, default=None, help="ruta del .docx de salida")
    ap.add_argument("--fecha", default=None, help="fecha determinista para la caratula")
    ap.add_argument("--autor", default=None, help="autor (tecnico competente)")
    args = ap.parse_args(argv)

    presupuesto = _cargar_presupuesto(args.entrada)
    criterio = _cargar_json(args.criterio)
    pack_textos = _cargar_json(args.textos)
    salida = args.salida or (args.entrada.parent / "Documento_Pliego.docx")
    ruta = componer_pliego(presupuesto, criterio,
                           {"salida": salida, "fecha": args.fecha, "autor": args.autor,
                            "pack_textos": pack_textos})
    print(f"Pliego de Condiciones Tecnicas: {ruta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
