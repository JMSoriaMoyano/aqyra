# -*- coding: utf-8 -*-
"""CLI minima del operador de entrega C7: compone el paquete desde una solicitud-entrega en JSON.

    aqyra-entrega solicitud.json --salida ./paquete

El operador es DETERMINISTA: la solicitud debe traer los artefactos INLINE ya anclados (la resolucion
de refs es del companero IA, fuera del operador). No certifica (dos llaves).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .entrega import componer_entrega, NOMBRE_MANIFIESTO_ENTREGA


def main() -> int:
    ap = argparse.ArgumentParser(description="Operador C7 · compone un paquete de entrega firmable.")
    ap.add_argument("solicitud", type=Path, help="ruta a la solicitud-entrega (JSON)")
    ap.add_argument("--salida", type=Path, default=Path.cwd() / "paquete_entrega",
                    help="carpeta del paquete de salida")
    args = ap.parse_args()

    solicitud = json.loads(args.solicitud.read_text(encoding="utf-8"))
    paquete = componer_entrega(solicitud, {"salida": args.salida})
    print(f"paquete: {paquete}")
    print(f"manifiesto-entrega: {paquete / NOMBRE_MANIFIESTO_ENTREGA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
