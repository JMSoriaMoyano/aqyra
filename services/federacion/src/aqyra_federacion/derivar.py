"""derivar(manifiesto, base_dir, salida) → IFC federado DERIVADO + manifiesto actualizado.

La decisión que D6 aplazó, resuelta en D26–D30 (Fase II·h6):

- El Maestro autoritativo SIGUE siendo el manifiesto (D1). El .ifc que escribe este
  módulo es un DERIVADO determinista para que el visor tenga algo federado que abrir;
  su identidad se ancla por md5 BYTE A BYTE en la golden (D26).
- Cabecera SPF DETERMINISTA escrita aquí (D26): time_stamp INYECTABLE (patrón
  bcf_generacion/D13; por defecto una constante, nunca now()) y preprocessor/
  originating fijados a 'aqyra-federacion' SIN versión adrede (un bump del service
  sin cambio de comportamiento no puede mover el md5 del contrato; la versión vive
  en procedencia.generado_por del manifiesto).
- La transformación declarada se materializa en un PLACEMENT RAÍZ por modelo (D27):
  la geometría interna NO se toca. Reglas de cuelgue: (a) todo IfcLocalPlacement
  RAÍZ (PlacementRelTo=None) del modelo copiado pasa a colgar del placement raíz de
  su modelo (traslación [dE,dN,dCota] + rotación declarada alrededor de Z); (b) todo
  IfcProduct copiado SIN ObjectPlacement lo recibe directamente (los modelos del
  engine traen Site/Storey sin placement). El derivado declara el CRS destino con
  IfcMapConversion + IfcProjectedCRS (identidad: las coordenadas YA están en el CRS
  destino por los placements raíz) → el derivado CUMPLE R4-GEORREF de serie.
- GUIDs preservados, dedup=nunca (D1/D28): si dos modelos traen el mismo GlobalId el
  derivado conserva AMBOS (la detección/aviso `guid-duplicado` vive en validar()).
- IfcProject ÚNICO (nombre = proyecto del manifiesto, GlobalId determinista uuid5);
  los IfcProject de origen se retiran tras re-colgar sus agregados/declaraciones.
  Unidades y OwnerHistory del proyecto federado: los del PRIMER modelo (v0 no
  convierte unidades — el aviso `unidades-no-metricas` ya lo declara); contextos de
  representación: TODOS los top-level (cada modelo conserva el suyo).
- Esquemas heterogéneos entre modelos → LecturaIfcError (el writer SPF no puede
  mezclar esquemas; diagnóstico accionable, D17).

También vive aquí la CÁMARA determinista del viewpoint BCF (D29): bbox de los
ORÍGENES de los placements ABSOLUTOS de los elementos del topic en el derivado
(cadena de ObjectPlacement resuelta — sin motor de geometría; la cámara por malla
exacta sería decisión nueva). Constantes documentadas: posición = centro +
K_CAMARA·(1,−1,1)·d con d = max(diagonal del bbox, D_MIN); FieldOfView = FOV_DEG;
AspectRatio = ASPECTO; el XML formatea los floats a 6 decimales fijos (bcf.py).

(El módulo se llama derivar.py: sin colisión de NOMBRE con el guardián anti-espejo
del engine — comprobado contra CORTE_ENGINE y NUCLEO antes de crearlo, lección qa.py.)
"""
from __future__ import annotations

import copy as _copy
import hashlib
import math
import uuid
from pathlib import Path

import ifcopenshell
import ifcopenshell.guid

from . import lectura
from .lectura import LecturaIfcError

# Constantes de la cámara (D29 — documentadas, sin números mágicos).
K_CAMARA = 1.0     # posición = centro + K_CAMARA·(1,−1,1)·d (diagonal SE-arriba)
D_MIN = 1.0        # m: un bbox degenerado (punto único) no deja la cámara encima
FOV_DEG = 60.0
ASPECTO = 16.0 / 9.0

# Cabecera SPF determinista (D26).
_TIMESTAMP_DEFECTO = "1970-01-01T00:00:00"
_FIRMA_SPF = "aqyra-federacion"          # SIN versión, adrede (D26)

_NS_DERIVADO = uuid.uuid5(uuid.NAMESPACE_DNS, "aqyra.derivado")


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _guid_det(semilla: str) -> str:
    """GlobalId IFC (22 chars) determinista: uuid5 → compresión base64-IFC."""
    return ifcopenshell.guid.compress(uuid.uuid5(_NS_DERIVADO, semilla).hex)


def derivar(manifiesto: dict, base_dir: Path, salida: Path,
            fecha: str | None = None) -> dict:
    """Escribe el IFC federado derivado y devuelve el manifiesto ACTUALIZADO (D30).

    `manifiesto`: salida de federar() (NO se muta). `base_dir`: directorio contra
    el que resuelven los `fichero_origen`. `salida`: ruta del .ifc a escribir.
    `fecha`: time_stamp de la cabecera SPF (inyectable — D26; por defecto constante).
    El manifiesto devuelto gana `ifc_derivado = {fichero, md5, determinista: true}`.
    """
    base_dir, salida = Path(base_dir), Path(salida)
    modelos = manifiesto["modelos"]

    # 1 · abrir y verificar integridad (bloqueante, D17 — mismo listón que federar)
    fuentes = []
    for m in modelos:
        ruta = base_dir / m["fichero_origen"]
        if not ruta.is_file():
            raise LecturaIfcError(ruta, f"el fichero del modelo {m['id']!r} no existe "
                                        f"(revisa 'fichero_origen' del manifiesto)")
        md5 = _md5(ruta)
        if m.get("md5") and m["md5"] != md5:
            raise LecturaIfcError(ruta, f"integridad: md5={md5} ≠ declarado {m['md5']} "
                                        f"(el fichero no es el que ancla el manifiesto)",
                                  campo="md5")
        fuentes.append((m, lectura.abrir_ifc(ruta)))

    esquemas = [str(getattr(f, "schema_identifier", None) or f.schema)
                for _, f in fuentes]
    if len(set(esquemas)) > 1:
        det = ", ".join(f"{m['id']}={e}" for (m, _), e in zip(fuentes, esquemas))
        raise LecturaIfcError(salida, f"esquemas heterogéneos entre modelos ({det}): "
                                      f"el derivado SPF no puede mezclarlos (D27)")
    out = ifcopenshell.file(schema=esquemas[0])

    # 2 · copiar cada modelo BAJO su placement raíz (D27)
    proyectos_copiados: list[list] = []
    for m, src in fuentes:
        t = m["transformacion"]
        dx, dy, dz = (float(v) for v in t["traslacion"])
        rot = math.radians(float(t.get("rotacion_deg", 0.0)))
        rp = out.create_entity(
            "IfcLocalPlacement",
            RelativePlacement=out.create_entity(
                "IfcAxis2Placement3D",
                Location=out.create_entity("IfcCartesianPoint",
                                           Coordinates=(dx, dy, dz)),
                Axis=out.create_entity("IfcDirection",
                                       DirectionRatios=(0.0, 0.0, 1.0)),
                RefDirection=out.create_entity(
                    "IfcDirection",
                    DirectionRatios=(math.cos(rot), math.sin(rot), 0.0))))

        for ent in src:                      # copia del grafo (add() cachea: sin duplicar)
            out.add(ent)
        # (a) placements RAÍZ del modelo → cuelgan del placement raíz
        for ent in lectura.by_type_seguro(src, "IfcLocalPlacement"):
            cp = out.add(ent)
            if cp.PlacementRelTo is None and cp != rp:
                cp.PlacementRelTo = rp
        # (b) productos sin placement (Site/Storey del engine) → placement raíz directo
        for ent in lectura.by_type_seguro(src, "IfcProduct"):
            cp = out.add(ent)
            if cp.ObjectPlacement is None:
                cp.ObjectPlacement = rp
        proyectos_copiados.append(
            [out.add(p) for p in
             lectura.by_type_seguro(src, "IfcProject", include_subtypes=False)])

    # 3 · IfcProject ÚNICO del derivado; los de origen se retiran tras re-colgar
    fed = out.create_entity(
        "IfcProject", GlobalId=_guid_det(f"{manifiesto['proyecto']}/IfcProject"),
        Name=manifiesto["proyecto"])
    primero = next((p for copias in proyectos_copiados for p in copias), None)
    if primero is not None:
        fed.OwnerHistory = primero.OwnerHistory
        fed.UnitsInContext = primero.UnitsInContext
    contextos = list(out.by_type("IfcGeometricRepresentationContext",
                                 include_subtypes=False))
    if contextos:
        fed.RepresentationContexts = tuple(contextos)
    for copias in proyectos_copiados:
        for pj in copias:
            for rel in list(getattr(pj, "IsDecomposedBy", None) or []):
                rel.RelatingObject = fed
            for rel in list(getattr(pj, "Declares", None) or []):
                rel.RelatingContext = fed
            out.remove(pj)

    # 4 · georref del CRS destino (D27): identidad — las coordenadas YA están en él
    crs_m = manifiesto.get("crs", {})
    ctx = next((c for c in contextos if getattr(c, "ContextType", None) == "Model"),
               contextos[0] if contextos else None)
    if ctx is not None:
        crs = out.create_entity("IfcProjectedCRS",
                                Name=str(crs_m.get("epsg", "EPSG:?")))
        if crs_m.get("descripcion"):
            crs.Description = crs_m["descripcion"]
        if crs_m.get("datum_vertical"):
            crs.VerticalDatum = crs_m["datum_vertical"]
        out.create_entity("IfcMapConversion", SourceCRS=ctx, TargetCRS=crs,
                          Eastings=0.0, Northings=0.0, OrthogonalHeight=0.0,
                          XAxisAbscissa=1.0, XAxisOrdinate=0.0, Scale=1.0)

    # 5 · cabecera SPF determinista (D26) + escritura
    fn = out.header.file_name
    fn.name = salida.name
    fn.time_stamp = fecha or _TIMESTAMP_DEFECTO
    fn.author = ("",)
    fn.organization = ("",)
    fn.preprocessor_version = _FIRMA_SPF
    fn.originating_system = _FIRMA_SPF
    fn.authorization = ""
    salida.parent.mkdir(parents=True, exist_ok=True)
    out.write(str(salida))

    nuevo = _copy.deepcopy(manifiesto)
    nuevo["ifc_derivado"] = {"fichero": salida.name, "md5": _md5(salida),
                             "determinista": True}
    return nuevo


def derivar_fichero(manifiesto_path: Path, base_dir: Path, salida: Path,
                    fecha: str | None = None) -> dict:
    """derivar() desde un manifiesto JSON en disco (conveniencia del CLI)."""
    import json
    manifiesto = json.loads(Path(manifiesto_path).read_text(encoding="utf-8"))
    return derivar(manifiesto, base_dir, salida, fecha=fecha)


# --------------------------------------------------------------------------- #
# Cámara determinista del viewpoint BCF (D29)                                 #
# --------------------------------------------------------------------------- #
def _origen_absoluto(producto) -> tuple[float, float, float] | None:
    """Origen del placement ABSOLUTO del producto (cadena resuelta) o None."""
    pl = getattr(producto, "ObjectPlacement", None)
    if pl is None:
        return None
    from ifcopenshell.util import placement as _up
    m = _up.get_local_placement(pl)
    return (float(m[0][3]), float(m[1][3]), float(m[2][3]))


def camara_para_guids(ifc, guids: list[str]) -> dict | None:
    """Cámara perspectiva determinista para los elementos de `guids` en el DERIVADO.

    bbox de los orígenes de placement absolutos; None si ningún GUID resuelve a un
    producto con placement (el viewpoint queda sin cámara, como en v0 — opt-in D29).
    GUIDs duplicados (D28): TODAS las ocurrencias entran al bbox.
    """
    objetivo = set(guids)
    origenes = []
    for prod in lectura.by_type_seguro(ifc, "IfcProduct"):
        try:
            g = prod.GlobalId
        except Exception:  # noqa: BLE001 — entidad corrupta: fuera del bbox
            continue
        if g in objetivo:
            o = _origen_absoluto(prod)
            if o is not None:
                origenes.append(o)
    if not origenes:
        return None
    mins = tuple(min(o[i] for o in origenes) for i in range(3))
    maxs = tuple(max(o[i] for o in origenes) for i in range(3))
    centro = tuple((mins[i] + maxs[i]) / 2.0 for i in range(3))
    d = max(math.dist(mins, maxs), D_MIN)
    pos = (centro[0] + K_CAMARA * d, centro[1] - K_CAMARA * d, centro[2] + K_CAMARA * d)
    dir_ = tuple(centro[i] - pos[i] for i in range(3))
    n = math.sqrt(sum(v * v for v in dir_))
    dir_ = tuple(v / n for v in dir_)
    # up: Gram-Schmidt de +Z contra la dirección (fallback +Y si degenera)
    up = tuple((0.0, 0.0, 1.0)[i] - dir_[2] * dir_[i] for i in range(3))
    nu = math.sqrt(sum(v * v for v in up))
    up = tuple(v / nu for v in up) if nu > 1e-9 else (0.0, 1.0, 0.0)
    return {"posicion": pos, "direccion": dir_, "arriba": up,
            "fov_deg": FOV_DEG, "aspecto": ASPECTO}
