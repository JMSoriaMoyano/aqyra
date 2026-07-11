"""Emisor determinista del ÍNDICE DE PROYECCIÓN para la skin del visor (E6.1, D-DV-3).

La skin «Dashboard de valor» (`apps/visor`) es CONSULTA, no cálculo (N-06): NO re-mide, NO
re-valora, NO re-proyecta. Consume un índice de proyección PRECOMPUTADO — la salida de
`proyectar(presupuesto, modelo, eje, corte)` (E2.2, anclada por `GOL-PRE-03`) serializada. Este
emisor es quien lo precomputa: llama al engine `aqyra_presupuesto` por cada `(eje, corte)` de v0 y
vuelca el índice. Vive JUNTO AL ENGINE (repo `tools/`), NO en el visor; corre donde corre el engine
(conda `mcp-bim` de JM / cualquier entorno con `ifcopenshell`), no en el cliente TS.

Determinista: sobre las MISMAS fixtures ancladas (`GOL-PRE-03/entrada/{ARQ,EST}.ifc`, md5
19a272a5…/f1d25192…) + el MISMO criterio (`AQ/v2`) + los MISMOS bancos (coste `AQ-DEMO/v1`,
carbono `generico/v2`), reproduce los totales y grupos de `GOL-PRE-03` (coste, 3 cortes) y añade el
eje carbono (invariante Σ). El md5 LF del índice ancla la fixture del visor.

    python tools/emitir_proyeccion_visor.py            # -> apps/visor/fixtures/proyeccion_valor.json
    python tools/emitir_proyeccion_visor.py --out X.json

Forma del índice (== `GOL-PRE-03.expected.vistas[].{eje,corte,suma,grupos[]}` + `unidad`/
`n_partidas`/`guids` que `proyectar` ya devuelve, más `totales` por eje):

    {"presupuesto": <id>, "presupuesto_md5": {...}, "totales": {eje: {valor, unidad}},
     "vistas": [{"eje","corte","suma","grupos":[{grupo,valor_total,unidad,n_partidas,guids,fuente}]}]}

Regla de oro (D-DV-4): un desajuste entre la fixture y `GOL-PRE-03` se corrige RE-EMITIENDO aquí o
en el engine, NUNCA editando el cliente TS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.abspath(os.path.dirname(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(REPO, "engines", "presupuesto", "src"))

# Cortes de v0 (D-DV-2): espacial + funcional + uniclass (los de GOL-PRE-03). GuBIM = forward.
CORTES_V0 = ("espacial", "funcional", "uniclass")

# Ejes de v0 (D-DV-2): coste (anclado por GOL-PRE-03) + carbono (invariante Σ; su golden = forward).
#   cada eje = (familia_banco, id, version, params extra de presupuestar)
EJES_V0 = (
    ("coste", ("banco", "AQ-DEMO", "v1"), {}),
    ("carbono", ("banco-carbono", "generico", "v2"), {"eje": "carbono"}),
)

# Fixtures de la muestra = la medición anclada por GOL-PRE-03 (D-DV-3: «reproduce GOL-PRE-03»).
FIXTURES_DEFAULT = ("GOL-PRE-03",)
PARAMS_BASE = {"moneda": "EUR", "iva_pct": 0.21, "gg_pct": 0.13, "bi_pct": 0.06}


def _pack(fam: str, pid: str, ver: str) -> dict:
    pdir = os.path.join(REPO, "data", "packs", fam, pid, ver)
    man = json.load(open(os.path.join(pdir, "pack.json"), encoding="utf-8"))
    return json.load(open(os.path.join(pdir, man["contenido"]["fichero"]), encoding="utf-8"))


def _md5_lf(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read().replace(b"\r\n", b"\n")).hexdigest()


def _fuentes(caso: str) -> tuple[list[dict], dict]:
    base = os.path.join(REPO, "packages", "golden", "C5", caso, "entrada")
    fuentes = [
        {"id": "ARQ", "disciplina": "ARQ", "path": os.path.join(base, "ARQ.ifc"), "fichero": "entrada/ARQ.ifc"},
        {"id": "EST", "disciplina": "EST", "path": os.path.join(base, "EST.ifc"), "fichero": "entrada/EST.ifc"},
    ]
    md5 = {f["fichero"]: _md5_lf(f["path"]) for f in fuentes}
    return fuentes, md5


def emitir(caso: str = "GOL-PRE-03") -> dict:
    from aqyra_presupuesto import medir, presupuestar, proyectar, suma_proyeccion

    criterio = _pack("criterio", "AQ", "v2")
    fuentes, md5 = _fuentes(caso)
    modelo = medir(fuentes, criterio)   # una sola medición (N-06): se valora en cada eje, no se re-mide
    modelo["proyecto"] = f"{caso} - índice de proyección para la skin del visor (E6.1)"

    vistas: list[dict] = []
    totales: dict = {}
    for eje, (fam, pid, ver), extra in EJES_V0:
        banco = _pack(fam, pid, ver)
        params = {**PARAMS_BASE, **extra}
        pres = presupuestar(modelo, criterio, banco, params)
        eje_total = None
        for corte in CORTES_V0:
            filas = proyectar(pres, modelo, eje, corte)
            suma = suma_proyeccion(filas)
            eje_total = suma if eje_total is None else eje_total
            vistas.append({
                "eje": eje, "corte": corte, "suma": suma,
                "grupos": [{"grupo": r["grupo"], "valor_total": r["valor_total"], "unidad": r["unidad"],
                            "n_partidas": r["n_partidas"], "guids": r["guids"], "fuente": r["fuente"]}
                           for r in filas],
            })
        unidad = "EUR" if eje == "coste" else (banco.get("unidad_eje") or banco.get("moneda") or "")
        totales[eje] = {"valor": eje_total, "unidad": unidad}

    return {
        "_meta": {
            "descripcion": "Índice de proyección precomputado para la skin del visor (E6.1, D-DV-3). "
                           "Salida de proyectar() serializada; el visor lo LEE (sin cálculo en cliente, N-06).",
            "emisor": "tools/emitir_proyeccion_visor.py",
            "caso": caso, "criterio": "criterio/AQ/v2",
            "bancos": {"coste": "banco/AQ-DEMO/v1", "carbono": "banco-carbono/generico/v2"},
            "ancla": "reproduce GOL-PRE-03 (coste, 3 cortes); carbono por invariante Σ.",
        },
        "presupuesto": caso,
        "presupuesto_md5": md5,
        "totales": totales,
        "vistas": vistas,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Emite el índice de proyección para la skin del visor (E6.1).")
    ap.add_argument("--caso", default="GOL-PRE-03", help="caso golden con entrada/{ARQ,EST}.ifc (medición ancla).")
    ap.add_argument("--out", default=os.path.join(REPO, "apps", "visor", "fixtures", "proyeccion_valor.json"),
                    help="ruta del índice de proyección (fixture del visor).")
    args = ap.parse_args()

    indice = emitir(args.caso)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    # LF + newline final: .gitattributes normaliza apps/visor/** a LF -> el md5 se ancla en LF.
    texto = json.dumps(indice, ensure_ascii=False, indent=2) + "\n"
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(texto)
    print("OK ->", args.out)
    print("md5 LF:", hashlib.md5(texto.encode("utf-8")).hexdigest())
    for v in indice["vistas"]:
        print(f"  [{v['eje']}x{v['corte']}] Σ={v['suma']} : {[g['grupo'] for g in v['grupos']]}")
    print("  totales:", indice["totales"])


if __name__ == "__main__":
    main()
