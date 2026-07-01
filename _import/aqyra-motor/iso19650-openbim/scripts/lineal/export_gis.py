"""
EXPORT GIS -- planta de la alineacion a GeoJSON (LineString) en el CRS proyectado.
PT 5.1 (Ola 5). Resuelve el gancho GIS de la decision nº3: GeoJSON + IFC 4.3 como
DOS soportes complementarios (IFC = modelo de ingenieria; GeoJSON = puente a
cartografia/cuencas para la Ola 6, hidrologia). NO implementa hidrologia.

Densifica la planta integrando cada segmento (recta/clotoide/curva) y transforma
las coordenadas LOCALES del eje a coordenadas PROYECTADAS (Eastings/Northings) con
la georreferencia del modelo neutro (IfcMapConversion: origen + rotacion + escala):

    E = E0 + escala*( x*cos(rot) - y*sin(rot) )
    N = N0 + escala*( x*sin(rot) + y*cos(rot) )

Las coordenadas del GeoJSON quedan en el CRS proyectado (no en WGS84): se declara el
EPSG en `crs` (named CRS, uso habitual en GIS) y en las propiedades.

Uso:  python3 export_gis.py modelo_neutro_lineal.json [salida.geojson] [paso_m]
Predimensionado/asistencia; a revisar y firmar por tecnico competente (ICCP).
"""
import json
import math
import sys


def _kappa(radio):
    return 0.0 if not radio else 1.0 / float(radio)


def _muestrear(x0, y0, az0, radio_ini, radio_fin, longitud, paso):
    """Puntos (x,y) LOCALES a lo largo del segmento, cada ~paso m (incluye inicio)."""
    L = float(longitud)
    n = max(1, int(math.ceil(L / paso)))
    k0, k1 = _kappa(radio_ini), _kappa(radio_fin)
    pts = [(x0, y0)]
    x, y, az = x0, y0, az0
    ds = L / n
    for i in range(n):
        s = i * ds
        k = k0 + (k1 - k0) * (s / L) if L > 0 else 0.0
        az_m = az + k * (ds / 2)
        x += math.cos(az_m) * ds
        y += math.sin(az_m) * ds
        az += k * ds + ((k1 - k0) / L * ds * (ds / 2) if L > 0 else 0.0)
        pts.append((x, y))
    return pts


def exportar(modelo, paso=5.0):
    g = modelo.get("georref") or {}
    E0 = g.get("origen_e") or 0.0
    N0 = g.get("origen_n") or 0.0
    rot = g.get("rotacion_rad") or 0.0
    esc = g.get("escala") or 1.0
    cs, sn = math.cos(rot), math.sin(rot)

    def proyectar(x, y):
        E = E0 + esc * (x * cs - y * sn)
        N = N0 + esc * (x * sn + y * cs)
        return [round(E, 4), round(N, 4)]

    planta = (modelo.get("alineacion") or {}).get("planta", [])
    coords = []
    for s in planta:
        if s.get("x_ini") is None:
            continue
        muestras = _muestrear(s["x_ini"], s["y_ini"], s["acimut_ini_rad"],
                              s.get("radio_ini"), s.get("radio_fin"),
                              s["longitud"], paso)
        for j, (x, y) in enumerate(muestras):
            if coords and j == 0:
                continue   # evita duplicar el nudo compartido entre segmentos
            coords.append(proyectar(x, y))

    epsg = g.get("epsg")
    feature = {
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": coords},
        "properties": {
            "eje": (modelo.get("eje") or {}).get("nombre"),
            "pk_inicio": modelo.get("pk_inicio"),
            "pk_fin": modelo.get("pk_fin"),
            "longitud_m": modelo.get("longitud_total"),
            "crs_epsg": epsg,
            "infraestructura": (modelo.get("infraestructura") or {}).get("clase"),
            "nota": "Coordenadas en el CRS proyectado (Eastings, Northings), no WGS84.",
        },
    }
    fc = {
        "type": "FeatureCollection",
        "name": (modelo.get("eje") or {}).get("nombre") or "alineacion",
        "crs": {"type": "name",
                "properties": {"name": "urn:ogc:def:crs:%s" %
                               (epsg.replace("EPSG:", "EPSG::") if epsg else "OGC:CRS84")}},
        "features": [feature],
    }
    return fc


def main(path, out=None, paso=5.0):
    with open(path, encoding="utf-8") as fh:
        modelo = json.load(fh)
    fc = exportar(modelo, paso)
    n = len(fc["features"][0]["geometry"]["coordinates"])
    out = out or (path.rsplit(".", 1)[0] + ".geojson")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(fc, fh, indent=2, ensure_ascii=False)
    print("GeoJSON escrito en %s (%d vertices, CRS %s)"
          % (out, n, fc["features"][0]["properties"]["crs_epsg"]))
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    p = float(sys.argv[3]) if len(sys.argv) > 3 else 5.0
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None, p))
