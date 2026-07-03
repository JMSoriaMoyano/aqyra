"""verificar(maestro, uso, localizacion, pack) → veredicto de cumplimiento (D7/D8/D9).

Orquesta el engine C3: carga el pack (exigencias + evaluador declarado por exigencia), abre el
Maestro (derivado + procedencia), evalúa cada exigencia con su evaluador determinista, agrega el
resumen por resultado y el veredicto global (regla D4). Determinista y sin `if` por código: la
lista de exigencias y su método vienen del PACK (D8).
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from . import modelo as M
from .evaluadores import EVALUADORES, RESULTADOS

# Claves de localización que el veredicto ECOA (sin metadatos declarativos como `declarado_por`).
_LOC_KEYS = ("pais", "comunidad_autonoma", "provincia", "municipio", "zona_climatica_he")


def cargar_maestro(maestro: dict) -> dict:
    """Abre el IFC derivado (la vista, D7) y reconstruye la procedencia por modelo.

    `maestro` = {"manifiesto": <dict>, "base_dir": <ruta>, "ifc_derivado": <ruta>?}. Si no se pasa
    `ifc_derivado`, se resuelve `manifiesto["ifc_derivado"]["fichero"]` contra `base_dir`.
    """
    base_dir = Path(maestro["base_dir"])
    manifiesto = maestro["manifiesto"]
    derivado_path = maestro.get("ifc_derivado")
    if derivado_path is None:
        derivado_path = base_dir / manifiesto["ifc_derivado"]["fichero"]
    return {
        "derivado": M.abrir(derivado_path),
        "guid2mod": M.guid_a_modelo(manifiesto, base_dir),
        "modelos": [m["id"] for m in manifiesto.get("modelos", [])],
    }


def _cargar_pack(pack) -> tuple[dict, dict]:
    """(`pack.json`, fichero de exigencias) a partir de la ruta al directorio del pack."""
    pack_dir = Path(pack)
    pj = json.loads((pack_dir / "pack.json").read_text(encoding="utf-8"))
    exig = json.loads((pack_dir / pj["contenido"]["fichero"]).read_text(encoding="utf-8"))
    return pj, exig


def _veredicto_global(resultados: list[str]) -> str:
    """Regla agregada D4: no-conforme si hay ≥1 no-cumple; conforme-con-reservas si no hay
    no-cumple pero sí no-verificable; conforme si todas son cumple/no-aplica."""
    if "no-cumple" in resultados:
        return "no-conforme"
    if "no-verificable" in resultados:
        return "conforme-con-reservas"
    return "conforme"


def verificar(maestro: dict, uso: dict, localizacion: dict, pack) -> dict:
    """Emite el veredicto de cumplimiento POR EXIGENCIA sobre el Maestro federado.

    - `maestro`: {manifiesto, base_dir, ifc_derivado?} (+ `proyecto` opcional para el encabezado).
    - `uso` / `localizacion`: DECLARADOS (ADR — nunca inferidos del IFC).
    - `pack`: ruta al directorio del pack normativo (`data/packs/normativa/<id>/<version>`).
    """
    pj, exig = _cargar_pack(pack)
    ctx = cargar_maestro(maestro)
    ctx["uso"] = uso
    ctx["localizacion"] = localizacion

    pack_ref = f"{pj['id']}/{pj['version']}"
    exigencias_out: list[dict] = []
    for e in exig["exigencias"]:
        nombre_ev = e.get("evaluador")
        func = EVALUADORES.get(nombre_ev)
        if func is None:
            raise ValueError(
                f"exigencia {e.get('id')!r}: evaluador {nombre_ev!r} no está registrado "
                f"(evaluadores disponibles: {sorted(EVALUADORES)})")
        frag = func(ctx, e.get("parametros", {}))
        if frag["resultado"] not in RESULTADOS:
            raise ValueError(f"exigencia {e.get('id')!r}: resultado {frag['resultado']!r} "
                             f"fuera de la taxonomía cerrada {RESULTADOS} (D4)")
        item = {
            "id": e["id"],
            "exigencia": e["exigencia"],
            "documento_basico": e["documento_basico"],
            "referencia": {"pack": pack_ref, "apartado": e["apartado"]},
            "resultado": frag["resultado"],
        }
        for k in ("motivo_no_verificable", "evidencia", "por_modelo"):
            if frag.get(k) is not None:
                item[k] = frag[k]
        exigencias_out.append(item)

    resultados = [x["resultado"] for x in exigencias_out]
    cnt = Counter(resultados)
    return {
        "proyecto": maestro.get("proyecto") or maestro["manifiesto"].get("proyecto"),
        "uso": {"principal": uso.get("principal")},
        "localizacion": {k: localizacion[k] for k in _LOC_KEYS if localizacion.get(k) is not None},
        "pack": {"familia": pj.get("familia"), "id": pj["id"], "version": pj["version"],
                 "fichero": pj["contenido"]["fichero"]},
        "exigencias": exigencias_out,
        "resumen": {"total": len(exigencias_out),
                    "por_resultado": {k: cnt.get(k, 0) for k in RESULTADOS}},
        "veredicto": _veredicto_global(resultados),
    }
