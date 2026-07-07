"""Write-back de cumplimiento al IFC — 6D (D-6D-1..3, vertical `visor-cumplimiento-6d`).

`escribir_cumplimiento(veredicto, maestro, salida)` abre el IFC **derivado** federado (la vista,
D7 — el engine ABRE el derivado, no federa) y escribe en cada elemento un
**`Pset_Aqyra_Cumplimiento`** con su `Resultado` (D-6D-1), para que el visor lo LEA y pinte (6D).

El veredicto es POR EXIGENCIA con `por_modelo` (sub-modelo federado). El write-back reparte el
resultado de cada sub-modelo a sus elementos (vía la procedencia del manifiesto, `modelo.guid_a_modelo`)
y agrega el **peor caso** cuando varias exigencias tocan un elemento (D-6D-2):
`no-cumple` ≻ `no-verificable` ≻ `cumple`; `no-aplica` es neutro (solo queda `no-aplica` si todas
lo son). Espeja `engines/presupuesto.escribir_coste` (5D, D11–D14): cabecera SPF determinista +
GUIDs `uuid5` → escribir dos veces produce BYTES idénticos; su identidad se ancla por determinismo
+ semántica en la golden 6D (sin md5 hardcodeado, patrón D14 opción b).
"""
from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

from . import modelo as M

# Cabecera SPF determinista (patrón D14/D26) — firma SIN versión adrede.
_TIMESTAMP_DEFECTO = "1970-01-01T00:00:00"
_FIRMA_SPF = "aqyra-cumplimiento"
_NS_6D = uuid.uuid5(uuid.NAMESPACE_DNS, "aqyra.6d")

_PSET = "Pset_Aqyra_Cumplimiento"

# Severidad para el peor caso (D-6D-2): no-cumple > no-verificable > cumple; no-aplica neutro.
_SEVERIDAD = {"no-cumple": 3, "no-verificable": 2, "cumple": 1, "no-aplica": 0}


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _guid_det(semilla: str) -> str:
    """GlobalId IFC (22 chars) determinista: uuid5 → compresión base64-IFC (patrón `escribir_coste`)."""
    import ifcopenshell.guid
    return ifcopenshell.guid.compress(uuid.uuid5(_NS_6D, semilla).hex)


def _pack_ref(veredicto: dict) -> str | None:
    p = veredicto.get("pack") or {}
    if p.get("id") and p.get("version"):
        return f"{p['id']}/{p['version']}"
    return None


def resultado_por_elemento(veredicto: dict, guid2mod: dict) -> dict:
    """PURO (sin IFC): `{guid: {resultado, exigencia, documento_basico, apartado, pack, motivo?}}`.

    Reparte `por_modelo` → elementos y agrega el peor caso por elemento (D-6D-2). La exigencia
    DOMINANTE (la que fija el peor caso) aporta los metadatos del Pset; empate de severidad → la
    PRIMERA exigencia en orden (determinista).
    """
    exigencias = veredicto.get("exigencias", [])
    pack_ref = _pack_ref(veredicto)

    # Elementos agrupados por modelo (todos los del mismo modelo comparten resultado).
    modelo_elems: dict[str, list] = {}
    for g, m in guid2mod.items():
        modelo_elems.setdefault(m, []).append(g)

    salida: dict = {}
    for m, guids in modelo_elems.items():
        best = None  # (severidad, -orden, exigencia, resultado)
        for orden, e in enumerate(exigencias):
            pm = e.get("por_modelo")
            if pm is not None:
                if m not in pm:
                    continue  # exigencia desglosada por modelo, este modelo no rige
                r = pm[m].get("resultado")
            else:
                r = e.get("resultado")  # exigencia global: rige para todos los modelos
            if r is None:
                continue
            cand = (_SEVERIDAD.get(r, 0), -orden, e, r)
            if best is None or cand[:2] > best[:2]:
                best = cand
        if best is None:
            continue
        _, _, e, r = best
        info = {
            "resultado": r,
            "exigencia": e.get("id"),
            "documento_basico": e.get("documento_basico"),
            "apartado": (e.get("referencia") or {}).get("apartado"),
            "pack": (e.get("referencia") or {}).get("pack") or pack_ref,
        }
        if r == "no-verificable" and e.get("motivo_no_verificable"):
            info["motivo"] = e["motivo_no_verificable"]
        for g in guids:
            salida[g] = info
    return salida


def _resolver_derivado(maestro: dict) -> Path:
    d = maestro.get("ifc_derivado")
    if d is not None:
        return Path(d)
    base_dir = Path(maestro["base_dir"])
    return base_dir / maestro["manifiesto"]["ifc_derivado"]["fichero"]


def _psv(f, name: str, value, *, text: bool = False):
    tipo = "IfcText" if text else "IfcLabel"
    return f.create_entity(
        "IfcPropertySingleValue", Name=name, NominalValue=f.create_entity(tipo, str(value)))


def escribir_cumplimiento(veredicto: dict, maestro: dict, salida, *,
                          guid2mod: dict | None = None, fecha: str | None = None) -> dict:
    """Escribe `Pset_Aqyra_Cumplimiento` sobre el IFC derivado → IFC 6D en `salida`.

    - `veredicto`: salida de `verificar()` (por exigencia + `por_modelo`).
    - `maestro`: {`ifc_derivado`? , `manifiesto`, `base_dir`} — para abrir el derivado y (si no se
      pasa `guid2mod`) reconstruir la procedencia por modelo.
    - `guid2mod`: opcional `{GlobalId → modelo}`; si es None se calcula con `modelo.guid_a_modelo`.

    Devuelve `{fichero, md5, n_elementos, por_resultado}`. Determinista dado el mismo derivado y
    veredicto. No muta el derivado en disco (abre y escribe a `salida`).
    """
    import ifcopenshell

    salida = Path(salida)
    f = ifcopenshell.open(str(_resolver_derivado(maestro)))
    if guid2mod is None:
        guid2mod = M.guid_a_modelo(maestro["manifiesto"], maestro["base_dir"])

    por_elem = resultado_por_elemento(veredicto, guid2mod)

    n = 0
    por_resultado = {k: 0 for k in _SEVERIDAD}
    for el in f.by_type("IfcElement"):
        g = M.guid_de(el)
        info = por_elem.get(g)
        if info is None:
            continue
        props = [_psv(f, "Resultado", info["resultado"])]
        for clave, nombre in (("exigencia", "Exigencia"), ("documento_basico", "DocumentoBasico"),
                              ("apartado", "Apartado"), ("pack", "Pack")):
            if info.get(clave):
                props.append(_psv(f, nombre, info[clave]))
        if info.get("motivo"):
            props.append(_psv(f, "MotivoNoVerificable", info["motivo"], text=True))
        pset = f.create_entity(
            "IfcPropertySet", GlobalId=_guid_det(f"pset/{g}"), Name=_PSET, HasProperties=props)
        f.create_entity(
            "IfcRelDefinesByProperties", GlobalId=_guid_det(f"rel/{g}"),
            RelatedObjects=[el], RelatingPropertyDefinition=pset)
        n += 1
        por_resultado[info["resultado"]] = por_resultado.get(info["resultado"], 0) + 1

    # Cabecera SPF determinista + escritura (patrón `escribir_coste`).
    fn = f.header.file_name
    fn.name = salida.name
    fn.time_stamp = fecha or _TIMESTAMP_DEFECTO
    fn.author = ("",)
    fn.organization = ("",)
    fn.preprocessor_version = _FIRMA_SPF
    fn.originating_system = _FIRMA_SPF
    fn.authorization = ""
    salida.parent.mkdir(parents=True, exist_ok=True)
    f.write(str(salida))

    return {"fichero": salida.name, "md5": _md5(salida),
            "n_elementos": n, "por_resultado": por_resultado}
