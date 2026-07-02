"""validar(maestro, ids) → informe de QA (pass/fail por requisito, incidencias, S0–S7).

(El módulo se llama qa.py y no validar.py: el guardián anti-espejo del engine filtra por
NOMBRE de fichero y 'validar.py' es uno de los del corte de engines/ifc. No se afloja el
guardián; se evita la colisión.)

Comprueba el conjunto federado contra el pack IDS (motor propio mínimo, D7) MÁS las
reglas de módulo no expresables en IDS (R4-GEORREF: presencia de IfcMapConversion +
IfcProjectedCRS — ficha C4 §3, 'no todo es IDS'). BCF: declarado y NO emitido en v0
(D8 — la emisión de topics BCF 3.0 es la tarea 1.2).

Políticas de v0 (documentadas):
- requisitos ordenados por id (determinista, mezcla ids+módulo);
- resultado por modelo: no-aplica si nada aplica; agregado: fail si falla en algún modelo;
- severidad de incidencias: 'mayor' si origen=modulo, 'menor' si origen=ids;
- incidencias de reglas de módulo a nivel de proyecto → sin GUIDs de elemento;
- estado del maestro = el MENOS maduro de los modelos (min S) — el Maestro no puede
  estar más maduro que su entrada menos madura.
"""
from __future__ import annotations

import json
from pathlib import Path

import ifcopenshell

from . import ids_min

# Reglas de módulo (origen='modulo'): no expresables en IDS puro.
_R4 = {
    "id": "R4-GEORREF",
    "titulo": "Proyecto georreferenciado (IfcMapConversion + IfcProjectedCRS)",
    "aplicabilidad": "IfcProject",
}


def _georref(ifc) -> dict:
    """R4: georreferenciación = presencia de IfcMapConversion + IfcProjectedCRS."""
    n_proj = len(ifc.by_type("IfcProject"))
    ok = bool(ifc.by_type("IfcMapConversion")) and bool(ifc.by_type("IfcProjectedCRS"))
    out = {"n_comprobados": n_proj, "n_fallos": 0 if ok else n_proj}
    if not ok:
        out["detalle"] = "sin IfcMapConversion/IfcProjectedCRS en el IFC"
    return out


def _resultado_modelo(n_comprobados: int, n_fallos: int) -> str:
    if n_comprobados == 0:
        return "no-aplica"
    return "fail" if n_fallos else "pass"


def _agregado(por_modelo: dict) -> str:
    resultados = [v["resultado"] for v in por_modelo.values()]
    if "fail" in resultados:
        return "fail"
    return "pass" if "pass" in resultados else "no-aplica"


def _estado_min(estados: list[str]) -> str:
    return min(estados, key=lambda s: int(s[1:])) if estados else "S0"


def validar(manifiesto: dict, pack_dir: Path, base_dir: Path,
            bcf_version: str = "3.0") -> dict:
    """Valida el Maestro contra el pack IDS + reglas de módulo → informe QA.

    `pack_dir`: carpeta del pack (data/packs/ids/<id>/<version>/ con pack.json).
    `base_dir`: directorio contra el que resuelven los `fichero_origen` del manifiesto.
    """
    pack_dir, base_dir = Path(pack_dir), Path(base_dir)
    pack = json.loads((pack_dir / "pack.json").read_text(encoding="utf-8"))
    specs = ids_min.parse_ids(pack_dir / pack["contenido"]["fichero"])

    modelos = manifiesto["modelos"]
    ifcs = {m["id"]: ifcopenshell.open(str(base_dir / m["fichero_origen"])) for m in modelos}
    orden_modelos = [m["id"] for m in modelos]

    requisitos = []
    fallos_detalle: dict[tuple[str, str], list] = {}   # (req_id, modelo) → elementos

    for spec in specs:
        por_modelo = {}
        for mid in orden_modelos:
            ev = ids_min.evaluar_spec(ifcs[mid], spec)
            r = {"resultado": _resultado_modelo(ev["n_comprobados"], ev["n_fallos"]),
                 "n_comprobados": ev["n_comprobados"], "n_fallos": ev["n_fallos"]}
            if ev["n_fallos"]:
                nombres = [getattr(el, "Name", None) or "(sin nombre)" for el in ev["fallos"]]
                r["detalle"] = (f"{' y '.join(repr(n) for n in nombres)} no conforman "
                                f"el requisito {spec.id}")
                fallos_detalle[(spec.id, mid)] = ev["fallos"]
            por_modelo[mid] = r
        requisitos.append({"id": spec.id, "origen": "ids", "titulo": spec.titulo,
                           "aplicabilidad": spec.aplicabilidad,
                           "resultado": _agregado(por_modelo), "por_modelo": por_modelo})

    # Regla de módulo R4-GEORREF
    por_modelo = {}
    for mid in orden_modelos:
        ev = _georref(ifcs[mid])
        r = {"resultado": _resultado_modelo(ev["n_comprobados"], ev["n_fallos"]),
             "n_comprobados": ev["n_comprobados"], "n_fallos": ev["n_fallos"]}
        if "detalle" in ev:
            r["detalle"] = ev["detalle"]
        por_modelo[mid] = r
    requisitos.append({"id": _R4["id"], "origen": "modulo", "titulo": _R4["titulo"],
                       "aplicabilidad": _R4["aplicabilidad"],
                       "resultado": _agregado(por_modelo), "por_modelo": por_modelo})

    requisitos.sort(key=lambda r: r["id"])

    # Incidencias: por requisito (orden ya determinista) × modelo (orden de manifiesto)
    incidencias = []
    for req in requisitos:
        for mid in orden_modelos:
            pm = req["por_modelo"].get(mid)
            if not pm or pm["resultado"] != "fail":
                continue
            inc = {"id": f"INC-{len(incidencias) + 1:02d}", "requisito": req["id"],
                   "modelo": mid}
            if req["origen"] == "modulo":
                inc["guids"] = []      # regla a nivel de proyecto: sin GUIDs de elemento
                inc["titulo"] = f"{mid} no conforma {req['id']} ({req['titulo']})"
                inc["severidad"] = "mayor"
            else:
                els = fallos_detalle.get((req["id"], mid), [])
                inc["guids"] = [el.GlobalId for el in els]
                nombres = " / ".join(getattr(el, "Name", None) or "?" for el in els)
                inc["titulo"] = f"{req['id']} no conforme en {mid} ({nombres})"
                inc["severidad"] = "menor"
            incidencias.append(inc)

    estados_modelo = {m["id"]: m.get("estado_entrada", "S0") for m in modelos}
    resultados = [r["resultado"] for r in requisitos]

    return {
        "proyecto": manifiesto["proyecto"],
        "ids": {"pack_id": pack["id"], "pack_version": pack["version"],
                "fichero": pack["contenido"]["fichero"],
                "version_ids": pack["contenido"]["version_ids"]},
        "requisitos": requisitos,
        "incidencias": incidencias,
        "estados": {"por_modelo": estados_modelo,
                    "maestro": _estado_min(list(estados_modelo.values()))},
        "veredicto": "no-conforme" if "fail" in resultados else "conforme",
        "bcf": {"estandar": "BCF", "version": bcf_version, "emitido": False},
    }
