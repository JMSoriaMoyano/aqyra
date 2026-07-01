#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clasificacion.py  --  Doble clasificacion determinista (bsDD + Uniclass) para el
compilador narracion->IFC (contrato C1, evolucion de apertura de familias P1).

Una sola via reutilizable: cada elemento AUTORADO recibe
  (a) la referencia de entidad bsDD por URI  (igual que antes, generica para
      CUALQUIER IfcClass: BSDD_BASE + clase), y
  (b) la referencia Uniclass 2015 (tabla EF Elements/functions) por MAPEO
      DETERMINISTA por `ifcClass` (+ PredefinedType cuando refina), tan
      determinista como la URI bsDD: la tabla curada cubre las clases que el
      compilador autora; lo no listado cae a un fallback por GRUPO IFC y, en
      ultimo termino, a un codigo por defecto -> NUNCA queda sin Uniclass.

Esto cierra la capacidad #4 de la RFC "apertura de familias P1" (doble
clasificacion completa) sin volver a tocar el contrato por cada clase nueva:
clases futuras entran con su URI bsDD automatica + su Uniclass por grupo.

Fuente Uniclass 2015 EF v1.x (NBS) -- codigos EF verificados contra la tabla
oficial. El codigo final es responsabilidad del tecnico (Llave 2 / JM); este
modulo fija el MECANISMO determinista, ampliable entre hilos.
"""
from ifcopenshell.api import run

# ---- bsDD (entidad IFC por URI) --------------------------------------------
BSDD_BASE = "https://identifier.buildingsmart.org/uri/buildingsmart/ifc/4.3/class/"


def bsdd_uri(clase):
    return BSDD_BASE + clase


# ---- Uniclass 2015 - tabla EF (Elements/functions) -------------------------
UNICLASS_BASE = "https://identifier.buildingsmart.org/uri/nbs/uniclass2015/1/class/"

# Mapeo determinista por IfcClass -> (codigo EF, titulo). Codigos EF oficiales.
UNICLASS_POR_CLASE = {
    # --- cimentacion (substructure) ---
    "IfcFooting":            ("EF_20_05_30", "Foundations"),
    "IfcPile":               ("EF_20_05_30", "Foundations"),
    "IfcDeepFoundation":     ("EF_20_05_30", "Foundations"),
    "IfcCaissonFoundation":  ("EF_20_05_30", "Foundations"),
    "IfcPileCap":            ("EF_20_05_30", "Foundations"),
    # --- estructura (superstructure / framed) ---
    "IfcColumn":             ("EF_20_10_30", "Framed structures"),
    "IfcBeam":               ("EF_20_10_30", "Framed structures"),
    "IfcMember":             ("EF_20_10_30", "Framed structures"),
    "IfcPlate":              ("EF_20_10_80", "Solid structures"),
    # --- muros y barreras ---
    "IfcWall":               ("EF_25_10", "Walls"),
    "IfcWallStandardCase":   ("EF_25_10", "Walls"),
    "IfcCurtainWall":        ("EF_25_10", "Walls"),
    "IfcRailing":            ("EF_25_55", "Barriers"),
    "IfcDoor":               ("EF_25_30", "Doors and windows"),
    "IfcWindow":             ("EF_25_30", "Doors and windows"),
    # --- cubiertas, forjados y pavimentos ---
    "IfcRoof":               ("EF_30_10", "Roofs"),
    "IfcSlab":               ("EF_30_20", "Floors"),
    "IfcBuildingElementPart":("EF_30_20", "Floors"),
    "IfcCovering":           ("EF_30_25", "Ceilings and soffits"),
    "IfcPavement":           ("EF_30_60", "Pavements"),
    "IfcCourse":             ("EF_30_60", "Pavements"),
    "IfcKerb":               ("EF_30_60", "Pavements"),
    # --- escaleras y rampas ---
    "IfcStair":              ("EF_35_10", "Stairs"),
    "IfcStairFlight":        ("EF_35_10", "Stairs"),
    "IfcRamp":               ("EF_35_20", "Ramps"),
    "IfcRampFlight":         ("EF_35_20", "Ramps"),
    # --- torres, chimeneas, depositos ---
    "IfcChimney":            ("EF_37_17_15", "Chimneys"),
    "IfcTank":               ("EF_37_16_94", "Vessels"),
}

# Refinamiento por PredefinedType (clase.PT -> EF) cuando la clase sola no basta.
UNICLASS_POR_PT = {
    "IfcSlab.ROOF":                 ("EF_30_10", "Roofs"),
    "IfcSlab.BASESLAB":             ("EF_20_05_30", "Foundations"),
    "IfcTransportElement.ELEVATOR": ("EF_80_50", "Lifts"),
    "IfcTransportElement.ESCALATOR":("EF_80_20", "Conveyors"),
    "IfcTransportElement.MOVINGWALKWAY": ("EF_80_20", "Conveyors"),
    "IfcTransportElement.CRANEWAY": ("EF_80_30", "Cranes and hoists"),
    "IfcTransportElement.LIFTINGGEAR":   ("EF_80_30", "Cranes and hoists"),
    "IfcTransportElement.HAULINGGEAR":   ("EF_80_30", "Cranes and hoists"),
}

# Fallback determinista por GRUPO IFC (para CUALQUIER clase no listada arriba).
UNICLASS_POR_GRUPO = {
    "IfcTransportElement":   ("EF_80", "Transport functions"),
    "IfcDistributionElement":("EF_55", "Piped supply functions"),
    "IfcGeotechnicalElement":("EF_15", "Earthworks and remediation"),
    "IfcGeographicElement":  ("EF_45", "Flora and fauna elements"),
    "IfcFurnishingElement":  ("EF_40", "Signage, fittings, furnishings and equipment"),
    "IfcElementComponent":   ("EF_20_10", "Superstructure"),
    "IfcElementAssembly":    ("EF_20_10", "Superstructure"),
    "IfcCivilElement":       ("EF_20", "Structural elements"),
    "IfcBuiltElement":       ("EF_20", "Structural elements"),
}
UNICLASS_DEFAULT = ("EF_20", "Structural elements")


def uniclass_para(clase, predefined=None, grupo=None):
    """(codigo, titulo, uri) Uniclass 2015 EF determinista para `clase`.
    Orden: clase.PredefinedType -> clase -> grupo IFC -> default. Nunca None."""
    if predefined and predefined not in ("NOTDEFINED", "USERDEFINED"):
        ent = UNICLASS_POR_PT.get("%s.%s" % (clase, predefined))
        if ent:
            cod, tit = ent
            return cod, tit, UNICLASS_BASE + cod
    ent = UNICLASS_POR_CLASE.get(clase)
    if ent is None and grupo:
        ent = UNICLASS_POR_GRUPO.get(grupo)
    if ent is None:
        ent = UNICLASS_DEFAULT
    cod, tit = ent
    return cod, tit, UNICLASS_BASE + cod


# ---- aplicacion de la doble clasificacion a un elemento ---------------------
def clasificar_doble(m, el, clase, cache, predefined=None, grupo=None):
    """Adjunta a `el` la referencia bsDD (URI) + la referencia Uniclass 2015
    (IfcClassificationReference), de forma determinista por `clase`.
    `cache` mantiene los IfcClassification compartidos del modelo (idempotente).
    Devuelve (uri_bsdd, codigo_uniclass)."""
    # 1) bsDD - entidad IFC por URI (cualquier clase del catalogo)
    cb = cache.get("__bsdd__")
    if cb is None:
        cb = run("classification.add_classification", m, classification="bSDD - IFC 4.3")
        cache["__bsdd__"] = cb
    uri = bsdd_uri(clase)
    try:
        ref = run("classification.add_reference", m, products=[el],
                  identification=clase, name=clase, classification=cb, is_lightweight=False)
        if ref is not None:
            ref.Location = uri
    except Exception:
        pass
    # 2) Uniclass 2015 EF - mapeo determinista
    cod, tit, u_uri = uniclass_para(clase, predefined=predefined, grupo=grupo)
    cu = cache.get("__uniclass__")
    if cu is None:
        cu = run("classification.add_classification", m, classification="Uniclass 2015")
        cache["__uniclass__"] = cu
    try:
        refu = run("classification.add_reference", m, products=[el],
                   identification=cod, name=tit, classification=cu, is_lightweight=False)
        if refu is not None:
            refu.Location = u_uri
    except Exception:
        pass
    return uri, cod
