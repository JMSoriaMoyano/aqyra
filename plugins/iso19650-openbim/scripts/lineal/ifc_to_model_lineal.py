"""
PARSER LINEAL (fisico -> modelo neutro de ALINEACION). Dominio IFC 4.3
georreferenciado, contrato C1 §4bis. PT 5.1 (Ola 5). Vive en el plugin
iso19650-openbim (capa IFC transversal), junto al parser MEP (scripts/mep).

Lee un IFC 4.3 (IFC4X3) y emite el MODELO NEUTRO LINEAL (JSON serializable),
modelo HERMANO del estructural y del de red: mismas convenciones (bloque
`unidades` SI declarado) y claves NUEVAS, sin redefinir las existentes. El soporte
es una REFERENCIACION LINEAL POR PK (curva parametrica 1D), NO un grafo de red:
por eso este parser NO usa grafo_red (eso es drenaje/hidraulica, Ola 6).

  IfcAlignment
    -> IsNestedBy -> IfcAlignmentHorizontal -> IsNestedBy -> IfcAlignmentSegment
         .DesignParameters = IfcAlignmentHorizontalSegment  (LINE/CIRCULARARC/CLOTHOID)
    -> IsNestedBy -> IfcAlignmentVertical   -> ... IfcAlignmentVerticalSegment
         (CONSTANTGRADIENT/PARABOLICARC/CIRCULARARC)
    -> IsNestedBy -> IfcAlignmentCant       -> ... IfcAlignmentCantSegment
  Georreferencia: IfcMapConversion + IfcProjectedCRS (EPSG, origen E/N, rotacion).

REUTILIZA EL NUCLEO TRANSVERSAL SIN TOCARLO (PT 4.1):
  - ifc_utils.psets / length_scale / pset_value  (Psets y factor de unidades)
La lectura de georreferencia (IfcMapConversion/IfcProjectedCRS) vive AQUI, en el
parser lineal (decision PT 5.1): minima disrupcion; se promovera al nucleo solo
cuando una segunda disciplina georreferenciada lo necesite (re-espejado).

ESTE PARSER NO CALCULA TRAZADO: ni comprueba radios/clotoides frente a 3.1-IC, ni
disena firmes. Eso lo aporta despues la disciplina `obras-lineales` (PT 5.2+).
Deja PREVISTAS las claves `secciones_tipo`, `firme` y `terreno` (None).

Uso:  PYTHONPATH=/tmp/pylibs python3 ifc_to_model_lineal.py eje.ifc [salida.json]

Todo resultado es de predimensionado/asistencia y debe ser revisado y firmado por
tecnico competente (Ingeniero de Caminos). NDP marcados [confirmar AN].
"""
import json
import math
import os
import sys

import ifcopenshell

_HERE = os.path.dirname(os.path.abspath(__file__))
_NUCLEO = os.path.join(_HERE, "..", "nucleo")
if _NUCLEO not in sys.path:
    sys.path.insert(0, _NUCLEO)
import ifc_utils   # noqa: E402  (psets, length_scale, pset_value)

_TIPOS_H = ("LINE", "CIRCULARARC", "CLOTHOID", "BLOSSCURVE", "COSINECURVE",
            "CUBIC", "HELMERTCURVE", "SINECURVE", "VIENNESEBEND")
_TIPOS_V = ("CONSTANTGRADIENT", "PARABOLICARC", "CIRCULARARC", "CLOTHOID")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _radio(v, escala):
    """Radio en metros; 0 (o None) en IFC = recta -> None (radio infinito)."""
    r = _num(v)
    if r is None or abs(r) < 1e-9:
        return None
    return r * escala


def _segmentos_anidados(elemento, clase):
    """IfcAlignmentSegment anidados (IsNestedBy) de una capa, en orden de diseno."""
    out = []
    for rel in getattr(elemento, "IsNestedBy", []) or []:
        if rel.is_a("IfcRelNests"):
            for o in rel.RelatedObjects or []:
                if o.is_a("IfcAlignmentSegment"):
                    out.append(o)
    return out


def _capas(alineacion):
    """Devuelve (horizontal, vertical, cant) anidadas en el IfcAlignment."""
    h = v = c = None
    for rel in getattr(alineacion, "IsNestedBy", []) or []:
        if rel.is_a("IfcRelNests"):
            for o in rel.RelatedObjects or []:
                if o.is_a("IfcAlignmentHorizontal"):
                    h = o
                elif o.is_a("IfcAlignmentVertical"):
                    v = o
                elif o.is_a("IfcAlignmentCant"):
                    c = o
    return h, v, c


def _planta(horizontal, escala):
    """Lista de segmentos de planta ordenada por PK (abscisa acumulada)."""
    segs = []
    pk = 0.0
    for seg in _segmentos_anidados(horizontal, "h"):
        dp = getattr(seg, "DesignParameters", None)
        if dp is None or not dp.is_a("IfcAlignmentHorizontalSegment"):
            continue
        L = (_num(dp.SegmentLength) or 0.0) * escala
        sp = dp.StartPoint
        x0 = float(sp.Coordinates[0]) * escala if sp else None
        y0 = float(sp.Coordinates[1]) * escala if sp and len(sp.Coordinates) > 1 else None
        ri = _radio(dp.StartRadiusOfCurvature, escala)
        rf = _radio(dp.EndRadiusOfCurvature, escala)
        tipo = str(dp.PredefinedType)
        a_clot = None
        if tipo == "CLOTHOID":
            rfin = ri if ri is not None else rf
            if rfin is not None and L > 0:
                a_clot = round(math.sqrt(abs(rfin) * L), 4)
        segs.append({
            "pk_ini": round(pk, 4), "tipo": tipo, "longitud": round(L, 4),
            "x_ini": round(x0, 4) if x0 is not None else None,
            "y_ini": round(y0, 4) if y0 is not None else None,
            "acimut_ini_rad": round(_num(dp.StartDirection) or 0.0, 8),
            "radio_ini": round(ri, 4) if ri is not None else None,
            "radio_fin": round(rf, 4) if rf is not None else None,
            "A_clotoide": a_clot,
        })
        pk += L
    return segs, round(pk, 4)


def _alzado(vertical, escala):
    segs = []
    if vertical is None:
        return segs
    raw = []
    for seg in _segmentos_anidados(vertical, "v"):
        dp = getattr(seg, "DesignParameters", None)
        if dp is None or not dp.is_a("IfcAlignmentVerticalSegment"):
            continue
        raw.append(dp)
    raw.sort(key=lambda d: _num(d.StartDistAlong) or 0.0)
    for dp in raw:
        Lh = (_num(dp.HorizontalLength) or 0.0) * escala
        kv = _radio(dp.RadiusOfCurvature, escala)
        segs.append({
            "pk_ini": round((_num(dp.StartDistAlong) or 0.0) * escala, 4),
            "tipo": str(dp.PredefinedType),
            "longitud_h": round(Lh, 4),
            "cota_ini": round((_num(dp.StartHeight) or 0.0) * escala, 4),
            "pendiente_ini": round(_num(dp.StartGradient) or 0.0, 6),
            "pendiente_fin": round(_num(dp.EndGradient) or 0.0, 6),
            "kv": round(kv, 4) if kv is not None else None,
        })
    return segs


def _peralte(cant, escala):
    segs = []
    if cant is None:
        return segs
    w = _num(getattr(cant, "RailHeadDistance", None))
    raw = []
    for seg in _segmentos_anidados(cant, "c"):
        dp = getattr(seg, "DesignParameters", None)
        if dp is None or not dp.is_a("IfcAlignmentCantSegment"):
            continue
        raw.append(dp)
    raw.sort(key=lambda d: _num(d.StartDistAlong) or 0.0)
    for dp in raw:
        cr_i = (_num(dp.StartCantRight) or 0.0) * escala
        cr_f = (_num(dp.EndCantRight) or 0.0) * escala
        # peralte en % respecto al semiancho de referencia (si se conoce)
        p_i = round(cr_i / w * 100.0, 4) if w else None
        p_f = round(cr_f / w * 100.0, 4) if w else None
        segs.append({
            "pk_ini": round((_num(dp.StartDistAlong) or 0.0) * escala, 4),
            "tipo": str(dp.PredefinedType),
            "longitud": round((_num(dp.HorizontalLength) or 0.0) * escala, 4),
            "peralte_ini_pct": p_i, "peralte_fin_pct": p_f,
            "cant_ini_m": round(cr_i, 5), "cant_fin_m": round(cr_f, 5),
        })
    return segs


def _georref(ifc, escala):
    """IfcMapConversion + IfcProjectedCRS -> bloque georref del modelo neutro."""
    mc = (ifc.by_type("IfcMapConversion") or [None])[0]
    if mc is None:
        return None
    crs = getattr(mc, "TargetCRS", None)
    xa = _num(getattr(mc, "XAxisAbscissa", None))
    xo = _num(getattr(mc, "XAxisOrdinate", None))
    rot = None
    if xa is not None and xo is not None:
        rot = round(math.atan2(xo, xa), 8)
    return {
        "epsg": getattr(crs, "Name", None) if crs else None,
        "descripcion_crs": getattr(crs, "Description", None) if crs else None,
        "datum_geodesico": getattr(crs, "GeodeticDatum", None) if crs else None,
        "datum_vertical": getattr(crs, "VerticalDatum", None) if crs else None,
        "map_projection": getattr(crs, "MapProjection", None) if crs else None,
        "map_zone": getattr(crs, "MapZone", None) if crs else None,
        "origen_e": _num(mc.Eastings),
        "origen_n": _num(mc.Northings),
        "altura": _num(mc.OrthogonalHeight),
        "rotacion_rad": rot,
        "escala": _num(getattr(mc, "Scale", None)) or 1.0,
    }


def parse(ifc_path, out_path=None):
    ifc = ifcopenshell.open(ifc_path)
    escala = ifc_utils.length_scale(ifc)

    aligns = ifc.by_type("IfcAlignment")
    if not aligns:
        raise SystemExit("El IFC no contiene ningun IfcAlignment (¿es IFC 4.3?).")
    alineacion = aligns[0]   # primer eje; multi-eje -> ampliacion futura
    horizontal, vertical, cant = _capas(alineacion)

    planta, longitud_total = _planta(horizontal, escala) if horizontal else ([], 0.0)
    alzado = _alzado(vertical, escala)
    peralte = _peralte(cant, escala)

    pk_inicio = planta[0]["pk_ini"] if planta else (alzado[0]["pk_ini"] if alzado else 0.0)
    pk_fin = round(pk_inicio + longitud_total, 4)

    facility = (ifc.by_type("IfcRoad") or ifc.by_type("IfcRailway")
                or ifc.by_type("IfcFacility") or [None])[0]

    modelo = {
        "unidades": {"longitud": "m", "angulo": "rad", "pendiente": "m/m"},
        "georref": _georref(ifc, escala),
        "infraestructura": {
            "clase": facility.is_a() if facility else None,
            "nombre": getattr(facility, "Name", None) if facility else None,
        },
        "eje": {"nombre": getattr(alineacion, "Name", None),
                "global_id": getattr(alineacion, "GlobalId", None)},
        "alineacion": {"planta": planta, "alzado": alzado, "peralte": peralte},
        "pk_inicio": pk_inicio, "pk_fin": pk_fin,
        "longitud_total": longitud_total,
        # ganchos a la disciplina obras-lineales (PT 5.2+): NO implementados aqui
        "secciones_tipo": None,
        "firme": None,
        "terreno": None,
        "metricas": {
            "n_planta": len(planta), "n_alzado": len(alzado),
            "n_peralte": len(peralte), "factor_escala_ifc": escala,
            "esquema": ifc.schema,
        },
    }

    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(modelo, fh, indent=2, ensure_ascii=False)
        print("Modelo neutro lineal escrito en %s" % out_path)
    print("Eje '%s' | esquema %s | L=%.3f m (PK %.3f -> %.3f) | planta %d / "
          "alzado %d / peralte %d | georref %s"
          % (modelo["eje"]["nombre"], ifc.schema, longitud_total, pk_inicio,
             pk_fin, len(planta), len(alzado), len(peralte),
             (modelo["georref"] or {}).get("epsg")))
    return modelo


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    parse(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
