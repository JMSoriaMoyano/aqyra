"""
Base de datos de perfiles laminados (HEB, IPE) + calculo de propiedades de
seccion a partir de la geometria de un IfcIShapeProfileDef.

Unidades de salida: SI (m, m2, m4, m3).

Las propiedades de catalogo (PROFILE_DB) incluyen el efecto de los acuerdos
(radios de raccord), por lo que son ~4-5 % mayores que el calculo geometrico de
placas rectangulares. Por eso se da PRIORIDAD a la DB y la geometria queda como
respaldo para perfiles no tabulados. (Leccion caso 1; ver INC-06.)
"""
import math
import re

# Catalogo (tablas europeas, unidades SI)
PROFILE_DB = {
    "HEB 200": {
        "A": 78.08e-4, "Iy": 5696e-8, "Iz": 2003e-8,
        "Wely": 569.6e-6, "Wply": 642.5e-6,
        "Welz": 200.3e-6, "Wplz": 305.8e-6,
        "J": 59.28e-8, "Avz": 24.83e-4, "h": 0.200, "clase": 1,
    },
    "IPE 330": {
        "A": 62.61e-4, "Iy": 11770e-8, "Iz": 788.1e-8,
        "Wely": 713.1e-6, "Wply": 804.3e-6,
        "Welz": 98.52e-6, "Wplz": 153.7e-6,
        "J": 28.15e-8, "Avz": 30.81e-4, "h": 0.330, "clase": 1,
    },
    "IPE 300": {
        "A": 53.81e-4, "Iy": 8356e-8, "Iz": 603.8e-8,
        "Wely": 557.1e-6, "Wply": 628.4e-6,
        "Welz": 80.50e-6, "Wplz": 125.2e-6,
        "J": 20.12e-8, "Avz": 25.68e-4, "h": 0.300, "clase": 1,
    },
    "IPE 400": {
        "A": 84.46e-4, "Iy": 23130e-8, "Iz": 1318e-8,
        "Wely": 1156e-6, "Wply": 1307e-6,
        "Welz": 146.4e-6, "Wplz": 229.0e-6,
        "J": 51.08e-8, "Avz": 42.69e-4, "h": 0.400, "clase": 1,
    },
    "IPE 360": {
        "A": 72.73e-4, "Iy": 16270e-8, "Iz": 1043e-8,
        "Wely": 903.6e-6, "Wply": 1019e-6,
        "Welz": 122.8e-6, "Wplz": 191.1e-6,
        "J": 37.32e-8, "Avz": 35.14e-4, "h": 0.360, "clase": 1,
    },
    "HEB 240": {
        "A": 106.0e-4, "Iy": 11260e-8, "Iz": 3923e-8,
        "Wely": 938.3e-6, "Wply": 1053e-6,
        "Welz": 326.9e-6, "Wplz": 498.4e-6,
        "J": 102.7e-8, "Avz": 33.23e-4, "h": 0.240, "clase": 1,
    },
}


def _norm_name(name):
    if not name:
        return None
    s = name.upper().replace("-", " ").replace("_", " ")
    s = " ".join(s.split())
    m = re.match(r"^([A-Z]+)\s*([0-9]+)$", s.replace(" ", ""))
    if m:
        return "%s %s" % (m.group(1), m.group(2))
    # alias Euronorm de exportadores reales: "HE 200 B" / "HE200B" -> "HEB 200"
    m2 = re.match(r"^HE\s*([0-9]+)\s*([ABM])$", s)
    if m2:
        return "HE%s %s" % (m2.group(2), m2.group(1))
    return s


def from_db(name):
    key = _norm_name(name)
    if key in PROFILE_DB:
        d = dict(PROFILE_DB[key])
        d["fuente"] = "catalogo"
        return d
    return None


def from_ishape_geometry(b, h, tw, tf, r=0.0):
    """Propiedades de un perfil en I bisimetrico desde su geometria (placas
    rectangulares; ignora acuerdos -> ligeramente conservador). Metros."""
    hw = h - 2.0 * tf
    A = 2.0 * b * tf + hw * tw
    Iy = (b * h ** 3) / 12.0 - ((b - tw) * hw ** 3) / 12.0
    Iz = (2.0 * tf * b ** 3) / 12.0 + (hw * tw ** 3) / 12.0
    Wely = Iy / (h / 2.0)
    Welz = Iz / (b / 2.0)
    Wply = b * tf * (h - tf) + tw * hw ** 2 / 4.0
    Wplz = (b ** 2 * tf) / 2.0 + (hw * tw ** 2) / 4.0
    J = (2.0 * b * tf ** 3 + (h - tf) * tw ** 3) / 3.0
    Avz = A - 2.0 * b * tf + (tw + 2.0 * r) * tf
    return {
        "A": A, "Iy": Iy, "Iz": Iz, "J": J,
        "Wely": Wely, "Wply": Wply, "Welz": Welz, "Wplz": Wplz,
        "Avz": Avz, "h": h, "clase": _clase_ishape(b, tf, tw, hw),
        "fuente": "geometria",
    }


def _clase_ishape(b, tf, tw, hw, fy=275e6):
    eps = math.sqrt(235e6 / fy)
    c_ala = (b - tw) / 2.0
    rel_ala = c_ala / tf
    if rel_ala <= 9 * eps:
        cl_ala = 1
    elif rel_ala <= 10 * eps:
        cl_ala = 2
    elif rel_ala <= 14 * eps:
        cl_ala = 3
    else:
        cl_ala = 4
    rel_alma = hw / tw
    if rel_alma <= 72 * eps:
        cl_alma = 1
    elif rel_alma <= 83 * eps:
        cl_alma = 2
    elif rel_alma <= 124 * eps:
        cl_alma = 3
    else:
        cl_alma = 4
    return max(cl_ala, cl_alma)


def from_rectangle_geometry(b, h):
    """Propiedades de una seccion rectangular maciza b x h (m). Para pilares de
    hormigon leidos de un IfcRectangleProfileDef. b = ancho (XDim), h = canto (YDim)."""
    A = b * h
    Iy = b * h ** 3 / 12.0
    Iz = h * b ** 3 / 12.0
    Wely = Iy / (h / 2.0)
    Welz = Iz / (b / 2.0)
    Wply = b * h ** 2 / 4.0
    Wplz = h * b ** 2 / 4.0
    # rigidez a torsion de seccion rectangular (Roark/St. Venant)
    a, c = max(b, h) / 2.0, min(b, h) / 2.0
    J = a * c ** 3 * (16.0 / 3.0 - 3.36 * (c / a) * (1 - (c ** 4) / (12 * a ** 4)))
    return {
        "A": A, "Iy": Iy, "Iz": Iz, "J": J,
        "Wely": Wely, "Wply": Wply, "Welz": Welz, "Wplz": Wplz,
        "Avz": 5.0 / 6.0 * A, "h": h, "b": b, "clase": 1,
        "fuente": "geometria_rect",
    }


def from_circle_geometry(D):
    """Propiedades de una seccion circular maciza de diametro D (m). Para pilotes
    de hormigon leidos de un IfcCircleProfileDef.  A=pi*D^2/4, I=pi*D^4/64."""
    A = math.pi * D ** 2 / 4.0
    I = math.pi * D ** 4 / 64.0
    Wel = I / (D / 2.0)
    Wpl = D ** 3 / 6.0            # modulo plastico de un circulo macizo
    J = 2.0 * I                   # St. Venant (seccion circular): J = Ip = 2I
    return {
        "A": A, "Iy": I, "Iz": I, "J": J,
        "Wely": Wel, "Wply": Wpl, "Welz": Wel, "Wplz": Wpl,
        "Avz": 0.9 * A, "h": D, "b": D, "D": D, "clase": 1,
        "fuente": "geometria_circ",
    }


def props_from_profile_def(prof):
    """Desde un IfcIShapeProfileDef -> (nombre, props). Prioridad catalogo,
    respaldo geometria."""
    name = getattr(prof, "ProfileName", None)
    db = from_db(name)
    if db is not None:
        return _norm_name(name), db   # nombre normalizado de catalogo (alias->clave)
    if prof.is_a("IfcIShapeProfileDef"):
        b = float(prof.OverallWidth)
        h = float(prof.OverallDepth)
        tw = float(prof.WebThickness)
        tf = float(prof.FlangeThickness)
        r = float(prof.FilletRadius) if getattr(prof, "FilletRadius", None) else 0.0
        nm = name or "I %.0fx%.0f" % (h * 1000, b * 1000)
        return nm, from_ishape_geometry(b, h, tw, tf, r)
    if prof.is_a("IfcRectangleProfileDef"):
        b = float(prof.XDim)
        h = float(prof.YDim)
        nm = name or "R %.0fx%.0f" % (b * 1000, h * 1000)
        return nm, from_rectangle_geometry(b, h)
    if prof.is_a("IfcCircleProfileDef"):
        D = 2.0 * float(prof.Radius)
        nm = name or "C %.0f" % (D * 1000)
        return nm, from_circle_geometry(D)
    return name, None
