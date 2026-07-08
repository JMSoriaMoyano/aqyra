"""Genera las fixtures AUMENTADAS de GOL-PRE-03 (E2.2, D29) y HORNEA el caso (entrada + expected).

Parte de las fixtures de GOL-PRE-01 (IFC con Qto) y les inyecta, de forma DETERMINISTA, las
agrupaciones nativas que la vista necesita — sin tocar los originales anclados (0b998513…/0d7e7f20…):

  ARQ.ifc  ─ IfcSpace E-101/E-102 (agregados a la planta) + IfcZone Aulas/Admin (IfcRelAssignsToGroup)
             + IfcRelSpaceBoundary: M-Fachada delimita E-101(Aulas) y E-102(Admin) → 50/50 (D21);
                                     M-Interior delimita E-101(Aulas) → 1,0.
             La puerta y el solado quedan SIN agrupación → *fallback* funcional del criterio (v2).
  EST.ifc  ─ IfcSystem "Sys-Portico" agrupa los 4 pilares (IfcRelAssignsToGroup) → vista IfcSystem.
             Las zapatas y el forjado quedan SIN agrupación → *fallback*.

Luego MIDE (criterio v2) + PRESUPUESTA + PROYECTA las 5 vistas y escribe entrada.json + expected.json.
Determinismo: GUIDs uuid5 (semilla fija), escritura SPF y normalización a LF → md5 estable.

Correr en el conda `mcp-bim` (ifcopenshell 0.8.x): `python gen_fixtures.py` (ver GEN_gol-pre-03.bat).
El sandbox de desarrollo NO trae ifcopenshell. Un fallo se corrige AQUÍ o en el engine, nunca aflojando
la golden. NOTA 4.3 (ver ficha): la vista `ii-facility` (IfcFacilityPart) exige IFC4X3; este generador
produce IFC4 (las 4 vistas i/iii/iv/v) — el nodo 4.3 es punto a ratificar (candidato D30).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import uuid

import ifcopenshell
import ifcopenshell.guid

HERE = os.path.abspath(os.path.dirname(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SRC01 = os.path.join(REPO, "packages", "golden", "C5", "GOL-PRE-01", "entrada")
DST = os.path.join(HERE, "entrada")
os.makedirs(DST, exist_ok=True)
sys.path.insert(0, os.path.join(REPO, "engines", "presupuesto", "src"))

_NS = uuid.uuid5(uuid.NAMESPACE_URL, "https://aqyra.dev/golden/GOL-PRE-03")


def _guid(nombre: str) -> str:
    """GUID IFC determinista (uuid5 con semilla fija) → base64 comprimido de 22 chars."""
    return ifcopenshell.guid.compress(uuid.uuid5(_NS, nombre).hex)


def _oh(f):
    """Una OwnerHistory existente del fichero (opcional en IFC4; reutilizada para las entidades nuevas)."""
    ohs = f.by_type("IfcOwnerHistory")
    return ohs[0] if ohs else None


def _by_name(f, clase, nombre):
    for e in f.by_type(clase):
        if getattr(e, "Name", None) == nombre:
            return e
    return None


def _storey(f):
    st = f.by_type("IfcBuildingStorey")
    return st[0] if st else None


def aumentar_arq(path_in: str, path_out: str) -> None:
    f = ifcopenshell.open(path_in)
    oh = _oh(f)
    storey = _storey(f)
    m_fachada = _by_name(f, "IfcWall", "M-Fachada-Sur")
    m_interior = _by_name(f, "IfcWall", "M-Interior-01")

    def space(nombre):
        return f.create_entity("IfcSpace", GlobalId=_guid(nombre), OwnerHistory=oh, Name=nombre,
                               CompositionType="ELEMENT")

    e101, e102 = space("E-101"), space("E-102")
    # aggregar los espacios a la planta (árbol espacial → get_aggregate/get_container coherentes)
    if storey is not None:
        f.create_entity("IfcRelAggregates", GlobalId=_guid("agg-espacios"), OwnerHistory=oh,
                        RelatingObject=storey, RelatedObjects=[e101, e102])

    def zona(nombre, espacios):
        z = f.create_entity("IfcZone", GlobalId=_guid("zone-" + nombre), OwnerHistory=oh, Name=nombre)
        f.create_entity("IfcRelAssignsToGroup", GlobalId=_guid("asg-zone-" + nombre), OwnerHistory=oh,
                        RelatedObjects=espacios, RelatingGroup=z)
        return z

    zona("Aulas", [e101])
    zona("Admin", [e102])

    def boundary(space_e, wall, tag):
        f.create_entity("IfcRelSpaceBoundary", GlobalId=_guid("bnd-" + tag), OwnerHistory=oh,
                        RelatingSpace=space_e, RelatedBuildingElement=wall,
                        PhysicalOrVirtualBoundary="PHYSICAL", InternalOrExternalBoundary="INTERNAL")

    if m_fachada is not None:               # tabique de frontera compartido → 2 espacios (2 zonas) → 50/50
        boundary(e101, m_fachada, "fachada-101")
        boundary(e102, m_fachada, "fachada-102")
    if m_interior is not None:              # una sola frontera → 1,0 a Aulas
        boundary(e101, m_interior, "interior-101")

    f.write(path_out)


def aumentar_est(path_in: str, path_out: str) -> None:
    f = ifcopenshell.open(path_in)
    oh = _oh(f)
    pilares = [e for e in f.by_type("IfcColumn")]
    if pilares:
        sistema = f.create_entity("IfcSystem", GlobalId=_guid("sys-portico"), OwnerHistory=oh,
                                  Name="Sys-Portico")
        f.create_entity("IfcRelAssignsToGroup", GlobalId=_guid("asg-sys-portico"), OwnerHistory=oh,
                        RelatedObjects=pilares, RelatingGroup=sistema)
    # zapatas + forjado sin agrupación → *fallback* del criterio (fuente=criterio)
    f.write(path_out)


def _norm_lf_md5(path: str) -> str:
    with open(path, "rb") as fh:
        b = fh.read().replace(b"\r\n", b"\n")
    with open(path, "wb") as fh:
        fh.write(b)
    return hashlib.md5(b).hexdigest()


def hornear() -> None:
    """Mide (criterio v2) + presupuesta + proyecta las 5 vistas y escribe entrada.json + expected.json."""
    from aqyra_presupuesto import medir, presupuestar, proyectar, suma_proyeccion

    arq_out = os.path.join(DST, "ARQ.ifc")
    est_out = os.path.join(DST, "EST.ifc")
    aumentar_arq(os.path.join(SRC01, "ARQ.ifc"), arq_out)
    aumentar_est(os.path.join(SRC01, "EST.ifc"), est_out)
    md5_arq, md5_est = _norm_lf_md5(arq_out), _norm_lf_md5(est_out)
    print("md5 ARQ:", md5_arq, "\nmd5 EST:", md5_est)

    # packs: criterio v2 (fallback), banco v1
    def _pack(fam, ref):
        pdir = os.path.join(REPO, "data", "packs", fam, ref["id"], ref["version"])
        man = json.load(open(os.path.join(pdir, "pack.json"), encoding="utf-8"))
        return json.load(open(os.path.join(pdir, man["contenido"]["fichero"]), encoding="utf-8"))

    crit_ref = {"familia": "criterio", "id": "AQ", "version": "v2"}
    banco_ref = {"familia": "banco", "id": "AQ-DEMO", "version": "v1"}
    params = {"moneda": "EUR", "iva_pct": 0.21, "gg_pct": 0.13, "bi_pct": 0.06}
    criterio, banco = _pack("criterio", crit_ref), _pack("banco", banco_ref)

    fuentes = [{"id": "ARQ", "disciplina": "ARQ", "path": arq_out, "fichero": "entrada/ARQ.ifc"},
               {"id": "EST", "disciplina": "EST", "path": est_out, "fichero": "entrada/EST.ifc"}]
    modelo = medir(fuentes, criterio)
    modelo["proyecto"] = "GOL-PRE-03 - Proyección (vista) sobre la medición del Maestro aumentado"
    pres = presupuestar(modelo, criterio, banco, params)
    pem = pres["resumen"]["PEM"]
    pec = pres["resumen"]["PEC"]
    print("PEM", pem, "PEC", pec)

    # 3 proyecciones DISTINTAS que cubren los 5 aspectos de la acceptance (ver ficha):
    #   i  espacial  → por planta ;  ii uniclass → por clasificación (sustituye a ii-facility 4.3, gancho forward)
    #   funcional → engloba iii IfcSystem (fuente ifc) + iv IfcZone 50/50 (ifc fraccionario) + v fallback (criterio)
    defs = [("i-planta", "coste", "espacial"),
            ("ii-uniclass", "coste", "uniclass"),
            ("iii-v-funcional", "coste", "funcional")]
    vistas = []
    for vid, eje, corte in defs:
        filas = proyectar(pres, modelo, eje, corte)
        vistas.append({"id": vid, "eje": eje, "corte": corte, "suma": suma_proyeccion(filas),
                       "grupos": [{"grupo": r["grupo"], "valor_total": r["valor_total"],
                                   "fuente": r["fuente"]} for r in filas]})
        print(f"[{vid}] {eje}×{corte} Σ={suma_proyeccion(filas)} :", [r["grupo"] for r in filas])

    entrada = {
        "proyecto": modelo["proyecto"],
        "modelo": {"clase": "modelo-neutro-medicion",
                   "fuente_maestro": {"modelos": [
                       {"id": "ARQ", "disciplina": "ARQ", "fichero": "entrada/ARQ.ifc", "md5": md5_arq,
                        "qto_declarados": True},
                       {"id": "EST", "disciplina": "EST", "fichero": "entrada/EST.ifc", "md5": md5_est,
                        "qto_declarados": True}]}},
        "criterio_ref": crit_ref, "banco_ref": banco_ref, "parametros": params,
    }
    expected = {
        "modo": "proyeccion",
        "_nota": "GOL-PRE-03 (E2.2, D24-D29). Ancla la proyección proyectar(eje,corte) por DETERMINISMO "
                 "+ SEMÁNTICA + INVARIANTE (D28). Fixtures aumentadas de GOL-PRE-01 (md5 propios). "
                 "criterio/AQ/v2 anclado por su content_sha256. GOL-PRE-01/02 intactas.",
        "entradas_md5": {"entrada/ARQ.ifc": md5_arq, "entrada/EST.ifc": md5_est},
        "cost": {"PEM": pem, "PEC": pec},
        "vistas": vistas,
    }
    json.dump(entrada, open(os.path.join(HERE, "entrada.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    json.dump(expected, open(os.path.join(HERE, "expected.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("OK entrada.json + expected.json horneados.")


if __name__ == "__main__":
    hornear()
