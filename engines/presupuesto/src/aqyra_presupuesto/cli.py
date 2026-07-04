"""CLI del engine C5: presupuestar un modelo (o unos IFC con Qto) → presupuesto (JSON).

    # desde el modelo neutro de medición ya extraído (entrada del contrato):
    aqyra-presupuesto --modelo entrada.json --criterio data/packs/criterio/AQ/v1 \
        --banco data/packs/banco/AQ-DEMO/v1

    # desde el IFC(+Qto) — el parser (módulo 1) produce el modelo neutro:
    aqyra-presupuesto --ifc ARQ.ifc:ARQ EST.ifc:EST --criterio ... --banco ...

Pensado para inspección manual y para C7 (consumidor). El runner de la golden NO usa el CLI:
importa `medir`/`presupuestar` por path (patrón engines/ifc), como cierra la costura en packages/golden.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .medicion import medir
from .presupuesto import presupuestar


def _cargar_pack(pack_dir: Path) -> dict:
    manifiesto = json.loads((pack_dir / "pack.json").read_text(encoding="utf-8"))
    fichero = manifiesto["contenido"]["fichero"]
    return json.loads((pack_dir / fichero).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Engine C5 — presupuesto trazable desde la medición.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--modelo", type=Path, help="modelo neutro de medición (JSON, entrada del contrato)")
    src.add_argument("--ifc", nargs="+", help="IFC(+Qto) como ruta[:id[:disciplina]] (el parser mide)")
    ap.add_argument("--criterio", type=Path, required=True, help="dir del pack criterio")
    ap.add_argument("--banco", type=Path, required=True, help="dir del pack banco")
    ap.add_argument("--parametros", type=Path, default=None,
                    help="JSON de parámetros económicos (moneda/iva_pct/gg_pct/bi_pct)")
    ap.add_argument("--proyecto", default=None, help="nombre del proyecto para el encabezado")
    args = ap.parse_args(argv)

    if args.modelo is not None:
        entrada = json.loads(args.modelo.read_text(encoding="utf-8"))
        modelo = entrada.get("modelo", entrada)
        parametros = entrada.get("parametros", {})
        proyecto = args.proyecto or entrada.get("proyecto")
    else:
        fuentes = []
        for spec in args.ifc:
            partes = spec.split(":")
            ruta = Path(partes[0])
            fuentes.append({"path": ruta, "id": partes[1] if len(partes) > 1 else ruta.stem,
                            "disciplina": partes[2] if len(partes) > 2 else None,
                            "fichero": ruta.name})
        modelo = medir(fuentes)
        parametros = {}
        proyecto = args.proyecto

    if args.parametros is not None:
        parametros = json.loads(args.parametros.read_text(encoding="utf-8"))
    if proyecto:
        modelo = {**modelo, "proyecto": proyecto}

    criterio = _cargar_pack(args.criterio)
    banco = _cargar_pack(args.banco)
    presupuesto = presupuestar(modelo, criterio, banco, parametros)
    json.dump(presupuesto, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
