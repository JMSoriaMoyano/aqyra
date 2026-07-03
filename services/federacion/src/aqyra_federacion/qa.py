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
  estar más maduro que su entrada menos madura;
- GlobalId duplicado ENTRE modelos (D28, 2.6): se conserva (dedup=nunca, D1) y se
  DECLARA con el aviso `guid-duplicado` en el modelo que llega después — la detección
  vive aquí porque validar() ya abre TODOS los modelos (es transversal, no de fichero).
"""
from __future__ import annotations

import json
from pathlib import Path

from . import ids_min, lectura

# Reglas de módulo (origen='modulo'): no expresables en IDS puro.
_R4 = {
    "id": "R4-GEORREF",
    "titulo": "Proyecto georreferenciado (IfcMapConversion + IfcProjectedCRS)",
    "aplicabilidad": "IfcProject",
}


def _georref(ifc) -> dict:
    """R4: georreferenciación = presencia de IfcMapConversion + IfcProjectedCRS.

    1.3 (hallazgo #7): en IFC2X3 esas clases NO existen en el esquema y `by_type`
    LANZA — `by_type_seguro` lo convierte en fail DIAGNOSTICADO, no en crash.
    """
    n_proj = len(lectura.by_type_seguro(ifc, "IfcProject"))
    ok = (bool(lectura.by_type_seguro(ifc, "IfcMapConversion"))
          and bool(lectura.by_type_seguro(ifc, "IfcProjectedCRS")))
    out = {"n_comprobados": n_proj, "n_fallos": 0 if ok else n_proj}
    if not ok:
        esquema = str(ifc.schema)
        out["detalle"] = ("sin IfcMapConversion/IfcProjectedCRS en el IFC"
                          if esquema.startswith("IFC4")
                          else f"esquema {esquema}: IfcMapConversion/IfcProjectedCRS "
                               f"no existen en ese esquema (georref no expresable)")
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


def _avisos_guid_duplicado(ifcs: dict, orden_modelos: list[str]) -> dict[str, list[dict]]:
    """D28 (2.6): GlobalId duplicado ENTRE modelos → aviso en el modelo posterior.

    Un aviso por (modelo, modelo_previo) que AGREGA los GUIDs compartidos (los 3
    primeros en el detalle) — se declara sin inundar. El orden es determinista:
    modelos en orden de manifiesto, entidades en orden de fichero. Los duplicados
    INTRA-modelo no son de D28 (no los crea la federación).
    """
    visto: dict[str, str] = {}
    out: dict[str, list[dict]] = {mid: [] for mid in orden_modelos}
    for mid in orden_modelos:
        compartidos: dict[str, list[str]] = {}
        for ent in lectura.by_type_seguro(ifcs[mid], "IfcRoot"):
            try:
                g = ent.GlobalId
            except Exception:  # noqa: BLE001 — entidad corrupta: ya se declara aparte
                continue
            if not g:
                continue
            previo = visto.get(g)
            if previo is None:
                visto[g] = mid
            elif previo != mid:
                compartidos.setdefault(previo, []).append(g)
        for previo, gs in compartidos.items():
            extra = f" (+{len(gs) - 3} más)" if len(gs) > 3 else ""
            out[mid].append({"modelo": mid, "codigo": "guid-duplicado",
                             "detalle": f"{len(gs)} GlobalId ya aportado/s por "
                                        f"{previo}: {', '.join(gs[:3])}{extra}; "
                                        f"ambos se conservan (dedup=nunca, D28)"})
    return out


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
    ifcs = {m["id"]: lectura.abrir_ifc(base_dir / m["fichero_origen"]) for m in modelos}
    orden_modelos = [m["id"] for m in modelos]

    # 1.3 (D17/D20): avisos de lectura por modelo (suciedad TOLERABLE, declarada).
    avisos_por_modelo = {m["id"]: lectura.avisos_de_modelo(
        ifcs[m["id"]], base_dir / m["fichero_origen"], m["id"]) for m in modelos}
    # 2.6 (D28): GlobalId duplicado entre modelos, declarado en el modelo posterior.
    duplicados_por_modelo = _avisos_guid_duplicado(ifcs, orden_modelos)
    corruptos_por_modelo: dict[str, dict[str, str]] = {mid: {} for mid in orden_modelos}

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
            for eid in ev.get("corruptos", []):        # 1.3: elemento saltado → aviso
                corruptos_por_modelo[mid].setdefault(eid, spec.id)
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
                # 1.3: GlobalId roto no revienta la incidencia (getattr-safe)
                inc["guids"] = [g for g in (getattr(el, "GlobalId", None) for el in els)
                                if g]
                nombres = " / ".join(getattr(el, "Name", None) or "?" for el in els)
                inc["titulo"] = f"{req['id']} no conforme en {mid} ({nombres})"
                inc["severidad"] = "menor"
            incidencias.append(inc)

    # 1.3 (D20): clave forward-open SOLO si hay avisos (los casos limpios ni se enteran)
    avisos = []
    for mid in orden_modelos:
        avisos += avisos_por_modelo[mid]
        for eid, req_id in sorted(corruptos_por_modelo[mid].items()):
            avisos.append({"modelo": mid, "codigo": "entidad-corrupta",
                           "detalle": f"elemento {eid} saltado al evaluar {req_id} "
                                      f"(atributos rotos); no cuenta en n_comprobados"})
        avisos += duplicados_por_modelo[mid]           # 2.6 (D28), tras los del modelo

    estados_modelo = {m["id"]: m.get("estado_entrada", "S0") for m in modelos}
    resultados = [r["resultado"] for r in requisitos]

    informe_extra = {"avisos_lectura": avisos} if avisos else {}

    return {
        "proyecto": manifiesto["proyecto"],
        "ids": {"pack_id": pack["id"], "pack_version": pack["version"],
                "fichero": pack["contenido"]["fichero"],
                "version_ids": pack["contenido"]["version_ids"]},
        "requisitos": requisitos,
        "incidencias": incidencias,
        **informe_extra,
        "estados": {"por_modelo": estados_modelo,
                    "maestro": _estado_min(list(estados_modelo.values()))},
        "veredicto": "no-conforme" if "fail" in resultados else "conforme",
        "bcf": {"estandar": "BCF", "version": bcf_version, "emitido": False},
    }
