"""
GENERADOR de IFC 4.3 (IFC4X3) de prueba -- EJE DE CARRETERA georreferenciado.
PT 5.1 (Ola 5). Banco de pruebas del parser/validacion de ALINEACION (obra lineal).

  PLANTA:  S1 LINE 100 | S2 CLOTHOID 60 (inf->300) | S3 CIRCULARARC 80 (R300)
           S4 CLOTHOID 60 (300->inf) | S5 LINE 100                TOTAL 400 m
  ALZADO:  V1 CONSTANTGRADIENT 150 (+2%) | V2 PARABOLICARC 100 (+2->-3%, Kv2000)
           V3 CONSTANTGRADIENT 150 (-3%)             cota inicial 100,000
  PERALTE: 0 -> +7% en clotoides (LINEARTRANSITION), 7% en curva (CONSTANTCANT)
  GEORREF: IfcProjectedCRS EPSG:25830 (ETRS89/UTM30N) + IfcMapConversion

NOVEDAD (contrato C1, apertura de familias P1): la construccion del IfcAlignment se
extrae a la funcion REUTILIZABLE `construir_alineacion(model, ctx, ...)`, que ahora
llaman tanto este banco de pruebas (`main`) como el compilador narracion->IFC
(`spec_to_ifc.alineaciones[]`), para NO reimplementar la geometria de alineacion.

Esquema IFC4X3. Unidad SI de longitud EXPLICITA (metro sin prefijo).
Uso:  PYTHONPATH=/tmp/pylibs python3 generate_test_ifc_lineal.py salida.ifc
Predimensionado/asistencia; a revisar y firmar por tecnico competente (ICCP).
"""
import math
import sys

import ifcopenshell
from ifcopenshell.api import run


def _kappa(radio):
    return 0.0 if not radio else 1.0 / float(radio)


def _integrar(x0, y0, az0, radio_ini, radio_fin, longitud, n=400):
    """Integra (x,y,acimut) al final de un segmento de curvatura lineal en s.
    Convencion: radio con SIGNO (+ = giro a izquierda; 0 = recta)."""
    k0, k1 = _kappa(radio_ini), _kappa(radio_fin)
    L = float(longitud)
    if L <= 0:
        return x0, y0, az0
    x, y, az = x0, y0, az0
    ds = L / n
    for i in range(n):
        s = i * ds
        k = k0 + (k1 - k0) * (s / L)
        az_m = az + k * (ds / 2)
        x += math.cos(az_m) * ds
        y += math.sin(az_m) * ds
        az += k * ds + (k1 - k0) / L * ds * (ds / 2)
    return x, y, az


def _nest(model, padre, hijos):
    model.create_entity("IfcRelNests", GlobalId=ifcopenshell.guid.new(),
                        RelatingObject=padre, RelatedObjects=hijos)


def _asegurar_unidad_angulo(model):
    """Asegura que el IfcUnitAssignment tenga unidad de ANGULO PLANO (radian).
    El compilador narracion->IFC solo asigna longitud; el alineamiento la
    necesita (StartDirection en radianes). Idempotente."""
    ua = (model.by_type("IfcUnitAssignment") or [None])[0]
    if ua is None:
        return
    for u in (ua.Units or []):
        if getattr(u, "UnitType", None) == "PLANEANGLEUNIT":
            return
    rad = model.create_entity("IfcSIUnit", UnitType="PLANEANGLEUNIT", Name="RADIAN")
    ua.Units = list(ua.Units or []) + [rad]


def _aplicar_georref(model, ctx, g):
    """IfcProjectedCRS + IfcMapConversion a partir de un dict georref del cebo."""
    crs = model.create_entity(
        "IfcProjectedCRS", Name=g.get("epsg"), Description=g.get("descripcion"),
        GeodeticDatum=g.get("datum_geodesico"), VerticalDatum=g.get("datum_vertical"),
        MapProjection=g.get("map_projection"), MapZone=g.get("map_zone"))
    rot = g.get("rotacion_rad")
    if rot is None and g.get("rotacion_deg") is not None:
        rot = math.radians(float(g["rotacion_deg"]))
    xa, xo = (math.cos(rot), math.sin(rot)) if rot else (1.0, 0.0)
    model.create_entity(
        "IfcMapConversion", SourceCRS=ctx, TargetCRS=crs,
        Eastings=g.get("origen_e"), Northings=g.get("origen_n"),
        OrthogonalHeight=g.get("altura"),
        XAxisAbscissa=float(xa), XAxisOrdinate=float(xo),
        Scale=float(g.get("escala", 1.0)))
    return crs


def construir_alineacion(model, ctx, *, nombre="Eje", planta, alzado=None,
                         peralte=None, ancho_ref=3.5, cota_ini=0.0,
                         x0=0.0, y0=0.0, az0=0.0, georref=None, infra=None,
                         prj=None):
    """Construye un IfcAlignment COMPLETO (planta + alzado + peralte) en `model`.

    MAQUINARIA REUTILIZABLE de la Ola 5: la llaman tanto el banco de pruebas
    (`main`) como el compilador narracion->IFC (`spec_to_ifc.alineaciones[]`).
      planta : [(tipo, L, ri, rf)] LINE/CIRCULARARC/CLOTHOID; radio con signo, 0/None=recta.
      alzado : [(tipo, Lh, gi, gf, R)] CONSTANTGRADIENT/PARABOLICARC/...; R=Kv.
      peralte: [(tipo, s0, Lh, pi_pct, pf_pct)] o None CONSTANTCANT/LINEARTRANSITION.
    Devuelve (alignment, n_planta, n_alzado, n_peralte)."""
    _asegurar_unidad_angulo(model)
    if prj is None:
        prj = model.by_type("IfcProject")[0]

    x, y, az = float(x0), float(y0), float(az0)
    h_raw = []
    for tipo, L, ri, rf in planta:
        h_raw.append((tipo, L, ri or 0.0, rf or 0.0, x, y, az))
        x, y, az = _integrar(x, y, az, ri or 0.0, rf or 0.0, L)
    horizontal = run("root.create_entity", model,
                     ifc_class="IfcAlignmentHorizontal", name="Planta")
    h_segments = []
    for tipo, L, ri, rf, x0s, y0s, az0s in h_raw:
        p = model.create_entity("IfcCartesianPoint",
                                Coordinates=[float(x0s), float(y0s)])
        par = model.create_entity(
            "IfcAlignmentHorizontalSegment", StartPoint=p,
            StartDirection=float(az0s), StartRadiusOfCurvature=float(ri),
            EndRadiusOfCurvature=float(rf), SegmentLength=float(L),
            PredefinedType=tipo)
        seg = run("root.create_entity", model, ifc_class="IfcAlignmentSegment",
                  name="H-%s" % tipo)
        seg.DesignParameters = par
        h_segments.append(seg)
    _nest(model, horizontal, h_segments)
    capas = [horizontal]

    v_segments = []
    if alzado:
        vertical = run("root.create_entity", model,
                       ifc_class="IfcAlignmentVertical", name="Alzado")
        s_along, cota = 0.0, float(cota_ini)
        for tipo, Lh, gi, gf, R in alzado:
            par = model.create_entity(
                "IfcAlignmentVerticalSegment", StartDistAlong=float(s_along),
                HorizontalLength=float(Lh), StartHeight=float(cota),
                StartGradient=float(gi), EndGradient=float(gf),
                RadiusOfCurvature=float(R or 0.0), PredefinedType=tipo)
            seg = run("root.create_entity", model,
                      ifc_class="IfcAlignmentSegment", name="V-%s" % tipo)
            seg.DesignParameters = par
            v_segments.append(seg)
            cota = cota + (gi + gf) / 2.0 * Lh
            s_along += Lh
        _nest(model, vertical, v_segments)
        capas.append(vertical)

    c_segments = []
    if peralte:
        cantw = run("root.create_entity", model, ifc_class="IfcAlignmentCant",
                    name="Peralte")
        cantw.RailHeadDistance = float(ancho_ref)
        for tipo, s0, Lh, pi, pf in peralte:
            ci = pi / 100.0 * float(ancho_ref)
            cf = pf / 100.0 * float(ancho_ref)
            par = model.create_entity(
                "IfcAlignmentCantSegment", StartDistAlong=float(s0),
                HorizontalLength=float(Lh),
                StartCantLeft=float(-ci), EndCantLeft=float(-cf),
                StartCantRight=float(ci), EndCantRight=float(cf),
                PredefinedType=tipo)
            seg = run("root.create_entity", model,
                      ifc_class="IfcAlignmentSegment", name="C-%s" % tipo)
            seg.DesignParameters = par
            c_segments.append(seg)
        _nest(model, cantw, c_segments)
        capas.append(cantw)

    alignment = run("root.create_entity", model, ifc_class="IfcAlignment",
                    name=nombre)
    _nest(model, alignment, capas)
    run("aggregate.assign_object", model, relating_object=prj, products=[alignment])

    if infra:
        fac = run("root.create_entity", model,
                  ifc_class=infra.get("clase", "IfcRoad"),
                  name=infra.get("nombre", "Infraestructura"))
        site = (model.by_type("IfcSite") or [None])[0]
        run("aggregate.assign_object", model,
            relating_object=(site if site is not None else prj), products=[fac])
        model.create_entity("IfcRelReferencedInSpatialStructure",
                            GlobalId=ifcopenshell.guid.new(),
                            RelatedElements=[alignment], RelatingStructure=fac)
    if georref:
        _aplicar_georref(model, ctx, georref)
    return alignment, len(h_segments), len(v_segments), len(c_segments)


def main(out):
    model = ifcopenshell.file(schema="IFC4X3")
    run("root.create_entity", model, ifc_class="IfcProject",
        name="Eje de carretera de prueba (PT 5.1)")
    _u = run("unit.add_si_unit", model, unit_type="LENGTHUNIT")
    _ua = run("unit.add_si_unit", model, unit_type="PLANEANGLEUNIT")
    run("unit.assign_unit", model, units=[_u, _ua])
    ctx = run("context.add_context", model, context_type="Model")

    site = run("root.create_entity", model, ifc_class="IfcSite", name="Emplazamiento")
    prj = model.by_type("IfcProject")[0]
    run("aggregate.assign_object", model, relating_object=prj, products=[site])

    INF = 0.0
    planta = [
        ("LINE",        100.0, INF,   INF),
        ("CLOTHOID",     60.0, INF,   300.0),
        ("CIRCULARARC",  80.0, 300.0, 300.0),
        ("CLOTHOID",     60.0, 300.0, INF),
        ("LINE",        100.0, INF,   INF),
    ]
    alzado = [
        ("CONSTANTGRADIENT", 150.0, 0.020, 0.020, 0.0),
        ("PARABOLICARC",     100.0, 0.020, -0.030, 2000.0),
        ("CONSTANTGRADIENT", 150.0, -0.030, -0.030, 0.0),
    ]
    peralte = [
        ("CONSTANTCANT",       0.0, 100.0, 0.0, 0.0),
        ("LINEARTRANSITION", 100.0,  60.0, 0.0, 7.0),
        ("CONSTANTCANT",     160.0,  80.0, 7.0, 7.0),
        ("LINEARTRANSITION", 240.0,  60.0, 7.0, 0.0),
        ("CONSTANTCANT",     300.0, 100.0, 0.0, 0.0),
    ]
    E0, N0, H0 = 337000.0, 4610000.0, 700.0
    georref = {
        "epsg": "EPSG:25830", "descripcion": "ETRS89 / UTM zone 30N",
        "datum_geodesico": "ETRS89", "datum_vertical": "EGM2008",
        "map_projection": "UTM", "map_zone": "30N",
        "origen_e": E0, "origen_n": N0, "altura": H0, "rotacion_rad": 0.0,
        "escala": 1.0,
    }
    _a, nh, nv, nc = construir_alineacion(
        model, ctx, nombre="Eje C-001", planta=planta, alzado=alzado,
        peralte=peralte, ancho_ref=3.5, cota_ini=100.0, georref=georref,
        infra={"clase": "IfcRoad", "nombre": "Carretera C-001"}, prj=prj)

    model.write(out)
    print("IFC 4.3 de prueba escrito en %s (esquema %s)" % (out, model.schema))
    print("  Planta: %d segmentos | Alzado: %d | Peralte: %d" % (nh, nv, nc))
    print("  Georref: %s (E0=%.1f N0=%.1f H0=%.1f)" % (georref["epsg"], E0, N0, H0))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "eje_carretera_prueba.ifc")
