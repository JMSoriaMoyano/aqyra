"""
PARSER MEP (fisico -> modelo neutro de RED). Dominio IFC MEP, contrato C1 §4.
PT 4.2 (Ola 4, hueco H2). Vive en el plugin iso19650-openbim (capa IFC transversal).

Lee un IFC del dominio MEP y emite el MODELO NEUTRO DE RED (JSON serializable),
modelo HERMANO del estructural: mismas convenciones (bloque `unidades` SI declarado,
nomenclatura de nodos del nucleo) y claves NUEVAS, sin redefinir las existentes.

  IfcDistributionSystem (PredefinedType FIRESUPPRESSION/ELECTRICAL/...) -> sistema
  IfcFlowSegment  (tubo/conducto/cable bandeja)  -> segmentos -> tramos (grafo)
  IfcFlowFitting  (codo/te)                        -> nudos de union
  IfcFlowTerminal (BIE/rociador/difusor/luminaria) -> terminales[] + nudo terminal
  IfcFlowController / IfcFlowMovingDevice /         -> fuentes[]  + nudo fuente
    IfcEnergyConversionDevice (bomba/grupo)
  IfcDistributionPort + IfcRelConnectsPorts        -> conectividad (respaldo geometrico)

REUTILIZA EL NUCLEO TRANSVERSAL SIN TOCARLO (PT 4.1):
  - ifc_utils.psets / length_scale / pset_value   (Psets y factor de unidades)
  - grafo_red.construir_grafo(segmentos, tol)      (nodos+tramos: snap + troceo T/X)
  Los IfcFlowSegment aportan los SEGMENTOS; los puertos/extremos, los NUDOS.

ESTE PARSER NO CALCULA: ni hidraulica (Darcy/Manning), ni electrico, ni termico.
Eso lo aporta despues el solver de la disciplina `instalaciones` (no este PT).

Gancho H3 (bases de demanda): cada terminal y el sistema dejan la clave `demanda`
PREVISTA (None) para que mas adelante reciban caudales/potencias/ocupacion. Este
parser NO calcula demandas.

Uso:  python3 ifc_to_model_mep.py red.ifc [salida_modelo_neutro_mep.json]

Todo resultado es de predimensionado/asistencia y debe ser revisado y firmado por
tecnico competente (Ingeniero de Caminos). NDP marcados [confirmar AN].
"""
import json
import math
import os
import sys

import ifcopenshell
import ifcopenshell.util.placement as _place

# --- nucleo transversal (PT 4.1): espejado en scripts/nucleo del plugin ------
_HERE = os.path.dirname(os.path.abspath(__file__))
_NUCLEO = os.path.join(_HERE, "..", "nucleo")
if _NUCLEO not in sys.path:
    sys.path.insert(0, _NUCLEO)
import ifc_utils   # noqa: E402  (psets, length_scale, pset_value, algebra 4x4)
import grafo_red   # noqa: E402  (construir_grafo, filtrar_componentes_desconectadas)

TOL = grafo_red.TOL  # tolerancia de fusion de nudos (m); definida en el nucleo

# Clasificacion funcional de los IfcDistributionElement del modelo neutro.
_CLASES_SEGMENTO = ("IfcFlowSegment",)
_CLASES_TERMINAL = ("IfcFlowTerminal",)
_CLASES_FUENTE = ("IfcFlowMovingDevice", "IfcEnergyConversionDevice")
_CLASES_CONTROL = ("IfcFlowController",)
_CLASES_UNION = ("IfcFlowFitting", "IfcDistributionChamberElement")
# Abastecimiento (PT 6.3): la FUENTE puede ser un DEPOSITO (almacenamiento) ademas
# del grupo de bombeo (IfcFlowMovingDevice, ya en _CLASES_FUENTE). El deposito
# (IfcTank) hereda de IfcFlowStorageDevice -> se reconoce por JERARQUIA is_a()
# (no por string exacto, que para un IfcTank seria "IfcTank").
_CLASES_ALMACEN = ("IfcFlowStorageDevice",)

# Psets estandar de los que se leen propiedades de tramo (orden de preferencia).
_PSET_TRAMO = ("Pset_PipeSegmentTypeCommon", "Pset_DuctSegmentTypeCommon",
               "Pset_CableSegmentTypeCommon", "Pset_Estructurando_Red")

# Saneamiento (PT 6.2): sistemas en lamina libre por gravedad. El parser sigue
# siendo AGNOSTICO al sistema (emite el string tal cual); estas constantes solo
# guian el reconocimiento del VERTIDO (outfall) y la lectura de la COTA DE SOLERA.
_SISTEMAS_SANEAMIENTO = ("SEWAGE", "WASTEWATER", "DRAINAGE", "STORMWATER",
                         "SANITARY", "FOULWATER")
_PSET_SOLERA = ("Pset_Estructurando_Red", "Pset_Estructurando_Saneamiento")
_PROP_SOLERA = ("CotaSolera", "Cota_solera", "InvertLevel", "SoleraZ", "Solera")
_PROP_HABEQ = ("HabitantesEq", "Habitantes_eq", "PopulationEquivalent", "HabEq")


# Abastecimiento (PT 6.3): sistemas de agua a presion. El parser sigue siendo
# AGNOSTICO al sistema (emite el string tal cual); estas constantes solo guian el
# reconocimiento de la FUENTE = deposito (ancla de presion por cota) y la lectura de
# su presion/cota. Esquema: IFC4 puede usar DOMESTICCOLDWATER; IFC4X3, WATERSUPPLY.
_SISTEMAS_ABASTECIMIENTO = ("WATERSUPPLY", "DOMESTICCOLDWATER", "POTABLEWATER",
                            "COLDWATER", "DOMESTICWATER", "DRINKINGWATER")
_PROP_PRESION_FUENTE = ("Pressure", "Presion", "SupplyPressure", "PumpPressure",
                        "PresionServicio")
_PROP_COTA_LAMINA = ("WaterLevel", "CotaLamina", "NivelLamina", "TankLevel",
                     "CotaAgua")


def _es_saneamiento(tipo):
    return str(tipo or "").upper() in _SISTEMAS_SANEAMIENTO


def _es_abastecimiento(tipo):
    return str(tipo or "").upper() in _SISTEMAS_ABASTECIMIENTO


def _es_almacen(el):
    """True si el elemento es un DEPOSITO/almacenamiento (IfcTank y demas subtipos
    de IfcFlowStorageDevice). Se comprueba por jerarquia is_a(), no por string
    exacto, porque el is_a() de un IfcTank devuelve 'IfcTank'."""
    try:
        return any(el.is_a(c) for c in _CLASES_ALMACEN)
    except Exception:
        return False


def _es_outfall(el):
    """True si el terminal es el VERTIDO/outfall de la red (ancla del arbol)."""
    pred = str(getattr(el, "PredefinedType", None) or "").upper()
    nm = str(getattr(el, "Name", None) or "").upper()
    return (pred in ("OUTLET", "DRAIN")
            or any(k in nm for k in ("VERTIDO", "OUTFALL", "OUTLET", "EMISARIO")))


def _cota_solera(el):
    """Cota de solera (invert) leida de un Pset del elemento; None si no esta."""
    ps = ifc_utils.psets(el)
    for pset in _PSET_SOLERA:
        props = ps.get(pset) or {}
        for prop in _PROP_SOLERA:
            if props.get(prop) is not None:
                return _num(props[prop])
    return None


def _habeq(el):
    """Habitantes equivalentes del aporte, leidos de un Pset; None si no estan."""
    for prop in _PROP_HABEQ:
        v = _prop_terminal(el, prop)
        if v is not None:
            return _num(v)
    return None



# --- geometria de puertos ----------------------------------------------------
def _origen_mundo(producto, escala):
    """Origen (x,y,z) en METROS del ObjectPlacement de un producto IFC."""
    try:
        M = _place.get_local_placement(producto.ObjectPlacement)
        return [float(M[0][3]) * escala, float(M[1][3]) * escala,
                float(M[2][3]) * escala]
    except Exception:
        return None


def _puertos_de(elemento):
    """Lista de IfcDistributionPort asociados a un elemento (IfcRelNests o
    IfcRelConnectsPortToElement; cubre los dos patrones de exportador)."""
    puertos = []
    for rel in getattr(elemento, "IsNestedBy", []) or []:
        for o in getattr(rel, "RelatedObjects", []) or []:
            if o.is_a("IfcDistributionPort"):
                puertos.append(o)
    for rel in getattr(elemento, "HasPorts", []) or []:   # IfcRelConnectsPortToElement
        po = getattr(rel, "RelatingPort", None)
        if po is not None and po.is_a("IfcDistributionPort"):
            puertos.append(po)
    # respaldo: puertos cuyo placement cuelga del elemento via IfcRelNests inverso
    return puertos


def _coord_puerto(puerto, elemento, escala):
    """Coord en metros de un puerto: su propio placement si lo tiene; si no, el
    del elemento que lo contiene (terminales/fittings puntuales)."""
    c = _origen_mundo(puerto, escala)
    if c is not None and any(abs(v) > 0 for v in c):
        return c
    ce = _origen_mundo(elemento, escala)
    return ce if ce is not None else (c or [0.0, 0.0, 0.0])


# --- union-find de puertos conectados (IfcRelConnectsPorts) -------------------
def _clusters_puertos(ifc):
    """Agrupa los puertos unidos por IfcRelConnectsPorts (representante = primer
    puerto). Devuelve dict {id(puerto): representante_id}."""
    padre = {}

    def find(a):
        padre.setdefault(a, a)
        while padre[a] != a:
            padre[a] = padre[padre[a]]
            a = padre[a]
        return a

    def union(a, b):
        padre[find(a)] = find(b)

    for rel in ifc.by_type("IfcRelConnectsPorts"):
        pa, pb = getattr(rel, "RelatingPort", None), getattr(rel, "RelatedPort", None)
        if pa is not None and pb is not None:
            union(pa.id(), pb.id())   # STEP id estable (NO id() de Python: el wrapper
    return {k: find(k) for k in list(padre)}  # cambia por acceso y colisiona por reuso)


# --- lectura de propiedades ---------------------------------------------------
def _prop_tramo(elemento, nombre, defecto=None):
    """Busca una propiedad en los Psets de tramo estandar del elemento."""
    ps = ifc_utils.psets(elemento)
    for pset in _PSET_TRAMO:
        if pset in ps and nombre in ps[pset] and ps[pset][nombre] is not None:
            return ps[pset][nombre]
    return defecto


def _clase_riesgo_sistema(s):
    """Clase de riesgo PCI (UNE-EN 12845) si el modelador la dejo en un Pset del
    sistema (INC-12); si no, queda None y la inyecta el agente entre parser y
    demanda. El dato del IFC prevalece, como con caudal/presion de terminal."""
    ps = ifc_utils.psets(s)
    for pset in ("Pset_Estructurando_SistemaPCI", "Pset_Estructurando_Red"):
        props = ps.get(pset) or {}
        for prop in ("ClaseRiesgo", "Clase_riesgo", "clase_riesgo", "RiskClass"):
            if props.get(prop):
                return str(props[prop])
    return None


def _tipo_sistema(ifc):
    """(tipo, fluido, nombre, clase_riesgo) del primer IfcDistributionSystem/IfcSystem."""
    for cls in ("IfcDistributionSystem", "IfcDistributionCircuit", "IfcSystem"):
        for s in ifc.by_type(cls):
            tipo = getattr(s, "PredefinedType", None) or "USERDEFINED"
            nombre = getattr(s, "Name", None) or cls
            fluido = ifc_utils.pset_value(ifc, "Pset_DistributionSystemCommon",
                                          "FluidType", None)
            return str(tipo), fluido, nombre, _clase_riesgo_sistema(s)
    return "USERDEFINED", None, None, None


def _dist(a, b):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))


def _nodo_mas_cercano(nodos, coord, tol):
    """Nombre del nodo del grafo mas cercano a `coord` (<= max(tol, 1e-6))."""
    mejor, dmin = None, None
    for nm, n in nodos.items():
        d = _dist([n["x"], n["y"], n["z"]], coord)
        if dmin is None or d < dmin:
            mejor, dmin = nm, d
    if mejor is not None and dmin <= max(tol, 1e-6) * 10:
        return mejor
    return mejor  # devolver el mas cercano aunque exceda (se reporta en metricas)


# --- parser principal ---------------------------------------------------------
def parse(ifc_path, out_path=None, tol=None):
    ifc = ifcopenshell.open(ifc_path)
    escala = ifc_utils.length_scale(ifc)
    if tol is None:
        # tolerancia de snap parametrizable por Pset (como en el puente estructural)
        tol = ifc_utils.pset_value(ifc, "Pset_Estructurando_Red", "Snap_tol_m", TOL)
        try:
            tol = float(tol)
        except (TypeError, ValueError):
            tol = TOL

    tipo_sis, fluido, nombre_sis, clase_riesgo_sis = _tipo_sistema(ifc)

    # 1) clusters de puertos conectados -> coord representativa por cluster
    rep = _clusters_puertos(ifc)
    coord_rep = {}   # representante_id -> coord (metros)

    # 2) recorrer los elementos de distribucion
    segmentos = []          # para construir_grafo
    seg_meta = []           # metadatos paralelos por segmento
    terminales_raw = []     # (elemento, coord)
    fuentes_raw = []        # (elemento, coord, es_control)
    vertidos_raw = []       # (elemento, coord)  -- outfall de saneamiento (ancla)
    solera_raw = []         # (coord, cota_solera)  -- cotas de solera de nudos
    sin_puerto = []         # avisos

    for el in ifc.by_type("IfcDistributionElement"):
        cls = el.is_a()
        puertos = _puertos_de(el)
        # coord de cada puerto (con escala), reasignada al representante de su cluster
        cps = []
        for po in puertos:
            c = _coord_puerto(po, el, escala)
            r = rep.get(po.id(), po.id())   # STEP id estable (ver _clusters_puertos)
            if r not in coord_rep:
                coord_rep[r] = c
            cps.append(coord_rep[r])

        if cls in _CLASES_SEGMENTO:
            if len(cps) >= 2:
                p0, p1 = cps[0], cps[-1]
            else:
                p0, p1 = _extremos_geom(el, escala)
                if p0 is None:
                    sin_puerto.append(getattr(el, "Name", None) or el.is_a())
                    continue
            payload = {
                "elemento": getattr(el, "Name", None) or cls,
                "clase": cls,
                "dn": _prop_tramo(el, "NominalDiameter", _prop_tramo(el, "DN")),
                "material": _prop_tramo(el, "Material",
                                        _nombre_material(el)),
                "rugosidad": _prop_tramo(el, "Roughness"),
                "sistema": tipo_sis,
            }
            segmentos.append({"p0": p0, "p1": p1, "payload": payload})
            seg_meta.append(payload)
        elif cls in _CLASES_TERMINAL:
            c = cps[0] if cps else _origen_mundo(el, escala)
            cs = _cota_solera(el)
            if cs is not None and c:
                solera_raw.append((c, cs))
            if _es_saneamiento(tipo_sis) and _es_outfall(el):
                vertidos_raw.append((el, c))      # VERTIDO: ancla del arbol
            else:
                terminales_raw.append((el, c))
        elif _es_almacen(el):
            # DEPOSITO (IfcTank/IfcFlowStorageDevice): fuente = ancla de presion por
            # cota (abastecimiento, PT 6.3). Se reconoce por jerarquia is_a().
            c = cps[0] if cps else _origen_mundo(el, escala)
            fuentes_raw.append((el, c, "deposito"))
        elif cls in _CLASES_FUENTE:
            c = cps[0] if cps else _origen_mundo(el, escala)
            fuentes_raw.append((el, c, "equipo"))
        elif cls in _CLASES_CONTROL:
            c = cps[0] if cps else _origen_mundo(el, escala)
            # un controlador en cabecera (sin tramo aguas arriba) actua como fuente
            fuentes_raw.append((el, c, "controlador"))
        elif cls in _CLASES_UNION:
            # IfcFlowFitting / IfcDistributionChamberElement (pozo) -> nudo de union:
            # no crea tramo (lo absorbe el grafo por snap); aporta su COTA DE SOLERA.
            c = cps[0] if cps else _origen_mundo(el, escala)
            cs = _cota_solera(el)
            if cs is not None and c:
                solera_raw.append((c, cs))

    # 3) construir el grafo nodos+tramos con el nucleo (snap + troceo T/X)
    grafo = grafo_red.construir_grafo(segmentos, tol)
    nodos, tramos = grafo["nodos"], grafo["tramos"]

    # 4) clasificar nudos y mapear terminales/fuentes a su nudo
    for nm in nodos:
        nodos[nm]["tipo"] = "union"

    terminales = []
    for el, c in terminales_raw:
        nm = _nodo_mas_cercano(nodos, c, tol) if c else None
        if nm:
            nodos[nm]["tipo"] = "terminal"
        td = {
            "id": getattr(el, "Name", None) or el.is_a(),
            "tipo": str(getattr(el, "PredefinedType", None) or "USERDEFINED"),
            "nodo": nm,
            "caudal_min": (_num(ifc_utils.psets(el).get(
                "Pset_FireSuppressionTerminalTypeCommon", {}).get("FlowRate"))
                or _num(_prop_terminal(el, "FlowRate"))),
            "presion_min": _num(_prop_terminal(el, "PressureDrop")),
            "demanda": None,   # gancho H3: caudal/potencia/ocupacion (no calculado)
        }
        if _es_saneamiento(tipo_sis) or _es_abastecimiento(tipo_sis):
            td["habitantes_eq"] = _habeq(el)   # aporte residual (EN 752) / consumo (EN 805)
        terminales.append(td)

    vertidos = []
    for el, c in vertidos_raw:
        nm = _nodo_mas_cercano(nodos, c, tol) if c else None
        if nm:
            nodos[nm]["tipo"] = "vertido"
        vertidos.append({
            "id": getattr(el, "Name", None) or el.is_a(),
            "nodo": nm,
            "tipo": "vertido",
        })

    fuentes = []
    for el, c, kind in fuentes_raw:
        nm = _nodo_mas_cercano(nodos, c, tol) if c else None
        if nm:
            nodos[nm]["tipo"] = "fuente"
        presion = None
        for prop in _PROP_PRESION_FUENTE:
            presion = _num(_prop_terminal(el, prop))
            if presion is not None:
                break
        f = {
            "id": getattr(el, "Name", None) or el.is_a(),
            "nodo": nm,
            "presion": presion,             # kPa; si None, la inyecta la demanda (C4)
            "caudal": _num(_prop_terminal(el, "FlowRate")),
            "tipo": kind,                   # "deposito" | "equipo" | "controlador"
        }
        if kind == "deposito":
            for prop in _PROP_COTA_LAMINA:
                cota = _num(_prop_terminal(el, prop))
                if cota is not None:
                    f["cota_lamina"] = cota
                    break
        fuentes.append(f)

    # 5) completar tramos con longitud y aplanar payload
    tramos_out = {}
    for tid, t in tramos.items():
        ni, nj = t["ni"], t["nj"]
        L = _dist([nodos[ni]["x"], nodos[ni]["y"], nodos[ni]["z"]],
                  [nodos[nj]["x"], nodos[nj]["y"], nodos[nj]["z"]])
        pl = t.get("payload") or {}
        tramos_out[tid] = {
            "ni": ni, "nj": nj,
            "dn": pl.get("dn"),
            "material": pl.get("material"),
            "rugosidad": pl.get("rugosidad"),
            "longitud": round(L, 4),
            "elemento": pl.get("elemento"),
            "clase": pl.get("clase"),
        }

    # cotas de solera -> nodo mas cercano (gobiernan el flujo por gravedad).
    # Si no hay dato, el solver usa la z del nodo como solera [confirmar AN].
    for coord, cs in solera_raw:
        nm = _nodo_mas_cercano(nodos, coord, tol) if coord else None
        if nm and cs is not None:
            nodos[nm]["cota_solera"] = cs

    # nodos a esquema final (sin claves internas)
    nodos_out = {}
    for nm, n in nodos.items():
        d = {"x": round(n["x"], 4), "y": round(n["y"], 4),
             "z": round(n["z"], 4), "tipo": n.get("tipo", "union")}
        if n.get("cota_solera") is not None:
            d["cota_solera"] = round(float(n["cota_solera"]), 4)
        nodos_out[nm] = d

    modelo = {
        "unidades": {"longitud": "m", "caudal": "l/s", "presion": "kPa",
                     "potencia": "W"},
        "sistema": {"tipo": tipo_sis, "fluido": fluido, "nombre": nombre_sis,
                    "clase_riesgo": clase_riesgo_sis,   # INC-12: dato de proyecto si esta en el IFC
                    "demanda": None},   # gancho H3 a nivel sistema
        "nodos": nodos_out,
        "tramos": tramos_out,
        "terminales": terminales,
        "fuentes": fuentes,
        "vertidos": vertidos,
        "metricas": {
            "nudos_fusionados": grafo["metricas"]["nudos_fusionados"],
            "huecos_puenteados": grafo["metricas"]["huecos_puenteados"],
            "cruces_troceados": grafo["metricas"]["cruces_troceados"],
            "segmentos_sin_puerto": sin_puerto,
            "factor_escala_ifc": escala,
            "tol_snap_m": tol,
        },
    }

    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(modelo, fh, indent=2, ensure_ascii=False)
        print("Modelo neutro de red MEP escrito en %s" % out_path)
    print("Sistema %s | %d nodos | %d tramos | %d terminales | %d fuentes | %d vertidos"
          % (tipo_sis, len(nodos_out), len(tramos_out), len(terminales),
             len(fuentes), len(vertidos)))
    return modelo


# --- respaldos ----------------------------------------------------------------
def _extremos_geom(el, escala):
    """Respaldo: extremos de un IfcFlowSegment desde su representacion 'Axis'
    (IfcPolyline de 2 puntos), llevados a mundo por su placement."""
    try:
        M = _place.get_local_placement(el.ObjectPlacement)
        for rep in el.Representation.Representations:
            if rep.RepresentationIdentifier in ("Axis", "Body"):
                for it in rep.Items:
                    if it.is_a("IfcPolyline") and len(it.Points) >= 2:
                        def w(pt):
                            c = list(pt.Coordinates) + [0.0, 0.0, 0.0]
                            x = M[0][0] * c[0] + M[0][1] * c[1] + M[0][2] * c[2] + M[0][3]
                            y = M[1][0] * c[0] + M[1][1] * c[1] + M[1][2] * c[2] + M[1][3]
                            z = M[2][0] * c[0] + M[2][1] * c[1] + M[2][2] * c[2] + M[2][3]
                            return [x * escala, y * escala, z * escala]
                        return w(it.Points[0]), w(it.Points[-1])
    except Exception:
        pass
    return None, None


def _nombre_material(el):
    """Nombre del material asociado (IfcRelAssociatesMaterial -> IfcMaterial)."""
    try:
        for rel in getattr(el, "HasAssociations", []) or []:
            if rel.is_a("IfcRelAssociatesMaterial"):
                m = rel.RelatingMaterial
                if m.is_a("IfcMaterial"):
                    return m.Name
    except Exception:
        pass
    return None


def _prop_terminal(el, nombre):
    """Primer valor de propiedad `nombre` en cualquier Pset del elemento."""
    for _pset, props in ifc_utils.psets(el).items():
        if nombre in props and props[nombre] is not None:
            return props[nombre]
    return None


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    out = sys.argv[2] if len(sys.argv) > 2 else None
    parse(sys.argv[1], out)
