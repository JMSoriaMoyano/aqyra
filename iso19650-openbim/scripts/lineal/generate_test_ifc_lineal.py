"""
GENERADOR de IFC 4.3 (IFC4X3) de prueba -- EJE DE CARRETERA georreferenciado.
PT 5.1 (Ola 5). Banco de pruebas del parser/validacion de ALINEACION (obra lineal).
Analogo a generate_test_ifc_mep.py (dominio MEP) pero en el dominio georreferenciado.

  PLANTA:  S1 LINE 100 | S2 CLOTHOID 60 (inf->300) | S3 CIRCULARARC 80 (R300)
           S4 CLOTHOID 60 (300->inf) | S5 LINE 100                TOTAL 400 m
  ALZADO:  V1 CONSTANTGRADIENT 150 (+2%) | V2 PARABOLICARC 100 (+2->-3%, Kv2000)
           V3 CONSTANTGRADIENT 150 (-3%)             cota inicial 100,000
  PERALTE: 0 -> +7% en clotoides (LINEARTRANSITION), 7% en curva (CONSTANTCANT)
  GEORREF: IfcProjectedCRS EPSG:25830 (ETRS89/UTM30N) + IfcMapConversion
           (E0=337000 N0=4610000 H0=700, sin rotacion, escala 1,0)

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


def main(out):
    model = ifcopenshell.file(schema="IFC4X3")
    run("root.create_entity", model, ifc_class="IfcProject",
        name="Eje de carretera de prueba (PT 5.1)")
    _u = run("unit.add_si_unit", model, unit_type="LENGTHUNIT")
    _ua = run("unit.add_si_unit", model, unit_type="PLANEANGLEUNIT")
    run("unit.assign_unit", model, units=[_u, _ua])
    ctx = run("context.add_context", model, context_type="Model")

    site = run("root.create_entity", model, ifc_class="IfcSite", name="Emplazamiento")
    road = run("root.create_entity", model, ifc_class="IfcRoad", name="Carretera C-001")
    prj = model.by_type("IfcProject")[0]
    run("aggregate.assign_object", model, relating_object=prj, products=[site])
    run("aggregate.assign_object", model, relating_object=site, products=[road])

    crs = model.create_entity(
        "IfcProjectedCRS", Name="EPSG:25830", Description="ETRS89 / UTM zone 30N",
        GeodeticDatum="ETRS89", VerticalDatum="EGM2008",
        MapProjection="UTM", MapZone="30N")
    E0, N0, H0 = 337000.0, 4610000.0, 700.0
    model.create_entity(
        "IfcMapConversion", SourceCRS=ctx, TargetCRS=crs,
        Eastings=E0, Northings=N0, OrthogonalHeight=H0,
        XAxisAbscissa=1.0, XAxisOrdinate=0.0, Scale=1.0)

    INF = 0.0
    planta_def = [
        ("LINE",        100.0, INF,   INF),
        ("CLOTHOID",     60.0, INF,   300.0),
        ("CIRCULARARC",  80.0, 300.0, 300.0),
        ("CLOTHOID",     60.0, 300.0, INF),
        ("LINE",        100.0, INF,   INF),
    ]
    x, y, az = 0.0, 0.0, 0.0
    h_segs = []
    for tipo, L, ri, rf in planta_def:
        h_segs.append((tipo, L, ri, rf, x, y, az))
        x, y, az = _integrar(x, y, az, ri, rf, L)

    horizontal = run("root.create_entity", model,
                     ifc_class="IfcAlignmentHorizontal", name="Planta")
    h_segments = []
    for tipo, L, ri, rf, x0, y0, az0 in h_segs:
        p = model.create_entity("IfcCartesianPoint",
                                Coordinates=[float(x0), float(y0)])
        par = model.create_entity(
            "IfcAlignmentHorizontalSegment",
            StartPoint=p, StartDirection=float(az0),
            StartRadiusOfCurvature=float(ri), EndRadiusOfCurvature=float(rf),
            SegmentLength=float(L), PredefinedType=tipo)
        seg = run("root.create_entity", model, ifc_class="IfcAlignmentSegment",
                  name="H-%s" % tipo)
        seg.DesignParameters = par
        h_segments.append(seg)
    _nest(model, horizontal, h_segments)

    H_INI = 100.0
    vert_def = [
        ("CONSTANTGRADIENT", 150.0, 0.020, 0.020, 0.0),
        ("PARABOLICARC",     100.0, 0.020, -0.030, 2000.0),
        ("CONSTANTGRADIENT", 150.0, -0.030, -0.030, 0.0),
    ]
    vertical = run("root.create_entity", model,
                   ifc_class="IfcAlignmentVertical", name="Alzado")
    s_along, cota = 0.0, H_INI
    v_segments = []
    for tipo, Lh, gi, gf, R in vert_def:
        par = model.create_entity(
            "IfcAlignmentVerticalSegment",
            StartDistAlong=float(s_along), HorizontalLength=float(Lh),
            StartHeight=float(cota), StartGradient=float(gi),
            EndGradient=float(gf), RadiusOfCurvature=float(R),
            PredefinedType=tipo)
        seg = run("root.create_entity", model, ifc_class="IfcAlignmentSegment",
                  name="V-%s" % tipo)
        seg.DesignParameters = par
        v_segments.append(seg)
        cota = cota + (gi + gf) / 2.0 * Lh
        s_along += Lh
    _nest(model, vertical, v_segments)

    W = 3.5
    def cant(pct):
        return pct / 100.0 * W
    cant_def = [
        ("CONSTANTCANT",       0.0, 100.0, 0.0, 0.0),
        ("LINEARTRANSITION", 100.0,  60.0, 0.0, 7.0),
        ("CONSTANTCANT",     160.0,  80.0, 7.0, 7.0),
        ("LINEARTRANSITION", 240.0,  60.0, 7.0, 0.0),
        ("CONSTANTCANT",     300.0, 100.0, 0.0, 0.0),
    ]
    cantw = run("root.create_entity", model, ifc_class="IfcAlignmentCant",
                name="Peralte")
    cantw.RailHeadDistance = W
    c_segments = []
    for tipo, s0, Lh, pi, pf in cant_def:
        par = model.create_entity(
            "IfcAlignmentCantSegment",
            StartDistAlong=float(s0), HorizontalLength=float(Lh),
            StartCantLeft=float(-cant(pi)), EndCantLeft=float(-cant(pf)),
            StartCantRight=float(cant(pi)), EndCantRight=float(cant(pf)),
            PredefinedType=tipo)
        seg = run("root.create_entity", model, ifc_class="IfcAlignmentSegment",
                  name="C-%s" % tipo)
        seg.DesignParameters = par
        c_segments.append(seg)
    _nest(model, cantw, c_segments)

    alignment = run("root.create_entity", model, ifc_class="IfcAlignment",
                    name="Eje C-001")
    _nest(model, alignment, [horizontal, vertical, cantw])
    run("aggregate.assign_object", model, relating_object=prj, products=[alignment])
    model.create_entity("IfcRelReferencedInSpatialStructure",
                        GlobalId=ifcopenshell.guid.new(),
                        RelatedElements=[alignment], RelatingStructure=road)

    model.write(out)
    print("IFC 4.3 de prueba escrito en %s (esquema %s)" % (out, model.schema))
    print("  Planta: %d segmentos | Alzado: %d | Peralte: %d"
          % (len(h_segments), len(v_segments), len(c_segments)))
    print("  Georref: %s (E0=%.1f N0=%.1f H0=%.1f)" % (crs.Name, E0, N0, H0))


def _nest(model, padre, hijos):
    model.create_entity("IfcRelNests", GlobalId=ifcopenshell.guid.new(),
                        RelatingObject=padre, RelatedObjects=hijos)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "eje_carretera_prueba.ifc")
