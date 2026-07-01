"""
NUCLEO TRANSVERSAL - utilidades de lectura IFC (PT 4.1, Ola 4, hueco H1).

Lo COMUN a todas las disciplinas (estructuras, instalaciones, obras lineales) al
leer un IFC: Property Sets, factor de unidades del IfcUnitAssignment y algebra
homogenea 4x4. Es agnostico al solver y a la disciplina: NO calcula nada.

Origen: estas utilidades estaban DUPLICADAS en el lado de estructuras
(puente_analitico/puente.py -R5-, barras/ifc_to_model.py, laminas/ifc_to_model_3d.py,
y otros parsers). Aqui se centralizan con una API estable; cada parser de disciplina
(p. ej. un futuro ifc_to_model_mep.py por IfcDistributionPort) las reutiliza sin
reimplementarlas y SIN tocar el nucleo (contrato C1).

API estable:
  psets(element)                      -> dict {NombrePset: {Prop: valor}}
  length_scale(ifc)                   -> float (unidad de longitud del IFC -> metros)
  pset_value(ifc, pset, prop, def_)   -> valor de una propiedad (o def_)
  matmul(A, B) / apply(M, p) / to_list4(M) / ident4()   -> algebra 4x4

Todo resultado es de predimensionado/asistencia y debe ser revisado y firmado por
tecnico competente.
"""

# Prefijos del SI para el factor de unidades del IfcUnitAssignment.
_PREFIJO_SI = {None: 1.0, "EXA": 1e18, "PETA": 1e15, "TERA": 1e12, "GIGA": 1e9,
               "MEGA": 1e6, "KILO": 1e3, "HECTO": 1e2, "DECA": 1e1, "DECI": 1e-1,
               "CENTI": 1e-2, "MILLI": 1e-3, "MICRO": 1e-6, "NANO": 1e-9}


def psets(element):
    """Property Sets de un elemento como dict {NombrePset: {Propiedad: valor}}.
    Solo IfcPropertySingleValue con valor no nulo (respaldo generico de cualquier
    parser). Lectura pura, sin interpretar la semantica de las propiedades."""
    out = {}
    for rel in getattr(element, "IsDefinedBy", []) or []:
        if rel.is_a("IfcRelDefinesByProperties"):
            pdef = rel.RelatingPropertyDefinition
            if pdef.is_a("IfcPropertySet"):
                props = {}
                for p in pdef.HasProperties:
                    if p.is_a("IfcPropertySingleValue") and p.NominalValue is not None:
                        props[p.Name] = p.NominalValue.wrappedValue
                out[pdef.Name] = props
    return out


def length_scale(ifc):
    """Factor para pasar la unidad de longitud del IFC a METROS, respetando el
    IfcUnitAssignment del exportador. METRE->1.0; MILLIMETRE->1e-3; unidades de
    conversion (pulgada, pie) -> su factor. Por defecto 1.0 (modelos en metros)."""
    try:
        for ua in ifc.by_type("IfcUnitAssignment"):
            for u in ua.Units:
                if u.is_a("IfcSIUnit") and u.UnitType == "LENGTHUNIT":
                    return _PREFIJO_SI.get(getattr(u, "Prefix", None), 1.0)
                if u.is_a("IfcConversionBasedUnit") and u.UnitType == "LENGTHUNIT":
                    return float(u.ConversionFactor.ValueComponent.wrappedValue)
    except Exception:
        pass
    return 1.0


def pset_value(ifc, pset_name, prop_name, defecto=None):
    """Valor de una propiedad (IfcPropertySingleValue) buscandola por nombre de
    Pset y de propiedad en TODO el modelo; si no existe, devuelve 'defecto'.
    Generaliza el lector puntual de tolerancias/parametros de proyecto (p. ej.
    Pset_Estructurando_Puente.Snap_tol_m); el nombre del Pset es un parametro,
    no queda atado a ninguna disciplina."""
    try:
        for pset in ifc.by_type("IfcPropertySet"):
            if pset.Name == pset_name:
                for p in pset.HasProperties:
                    if p.is_a("IfcPropertySingleValue") and p.Name == prop_name \
                            and p.NominalValue is not None:
                        return p.NominalValue.wrappedValue
    except Exception:
        pass
    return defecto


# --- algebra de matrices homogeneas 4x4 (geometria; sin numpy obligatorio) ----
def matmul(A, B):
    """Producto de dos matrices 4x4."""
    return [[sum(A[i][k] * B[k][j] for k in range(4)) for j in range(4)]
            for i in range(4)]


def apply(M, p):
    """Transforma el punto p=[x,y,z] por la matriz homogenea 4x4 M."""
    x = M[0][0] * p[0] + M[0][1] * p[1] + M[0][2] * p[2] + M[0][3]
    y = M[1][0] * p[0] + M[1][1] * p[1] + M[1][2] * p[2] + M[1][3]
    z = M[2][0] * p[0] + M[2][1] * p[1] + M[2][2] * p[2] + M[2][3]
    return [float(x), float(y), float(z)]


def to_list4(M):
    """Convierte una matriz (numpy o lista) a lista 4x4 de floats."""
    return [[float(M[i][j]) for j in range(4)] for i in range(4)]


def ident4():
    """Matriz identidad 4x4."""
    return [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]
