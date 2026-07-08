"""Acceso al IFC(+Qto) para el parser de medición del C5 (módulo 1, D7).

La medición NACE del modelo: este módulo abre el IFC y lee las CANTIDADES de los `Qto_*`
(no adivina geometría, D_modelo), la clase, la clasificación, la ubicación y los HUECOS
(`IfcRelVoidsElement`) de cada elemento medible. El motor (presupuesto.py) presupuesta la vista
neutra que produce `medicion.medir`.

En producción la fuente es el Maestro federado de C4; en el golden, las fixtures congeladas con
`Qto` (md5 propios de C5; los originales anclados quedan intactos).
"""
from __future__ import annotations

# ifcopenshell se importa de forma PEREZOSA (dentro de las funciones del parser): el motor
# (presupuesto.py) presupuesta el modelo neutro SIN necesitar ifcopenshell; sólo `medir`/parser lo
# requiere. Así `presupuestar` funciona en entornos sin la librería (y su test no la exige).

# tipo (unidad) inferido del nombre de la magnitud del Qto — heurística estable para los
# Qto_*BaseQuantities estándar (Area→m2, Volume→m3, Length→ml). El motor toma la unidad del
# CRITERIO (no de aquí); este `tipo` documenta la magnitud en el modelo neutro.
def tipo_de_magnitud(nombre: str) -> str:
    n = nombre.lower()
    if "area" in n:
        return "m2"
    if "volume" in n:
        return "m3"
    if "length" in n or "perimeter" in n or "width" in n or "height" in n:
        return "ml"
    return "ud"


def abrir(path):
    """Abre un IFC."""
    import ifcopenshell
    return ifcopenshell.open(str(path))


def guid_de(entidad):
    """GlobalId de una entidad o None si no es legible."""
    try:
        return entidad.GlobalId
    except Exception:  # noqa: BLE001
        return None


def cantidades_qto(elemento) -> list[dict]:
    """Cantidades del elemento leídas de sus `Qto_*` → [{magnitud, tipo, valor, fuente_qto}].

    La medición nace del modelo (D7): sólo lee los `Qto` (no computa geometría). Ignora claves de
    servicio de get_psets (`id`) y valores no numéricos.
    """
    import ifcopenshell.util.element as _ue
    out: list[dict] = []
    try:
        psets = _ue.get_psets(elemento) or {}
    except Exception:  # noqa: BLE001 — entidad corrupta
        psets = {}
    for pset_name, props in sorted(psets.items()):
        if not str(pset_name).startswith("Qto"):
            continue
        if not isinstance(props, dict):
            continue
        for prop, valor in props.items():
            if prop == "id" or not isinstance(valor, (int, float)) or isinstance(valor, bool):
                continue
            out.append({
                "magnitud": prop,
                "tipo": tipo_de_magnitud(prop),
                "valor": float(valor),
                "fuente_qto": f"{pset_name}.{prop}",
            })
    return out


def huecos_de(elemento) -> list:
    """Huecos (IfcOpeningElement) que perforan el elemento, vía `HasOpenings`
    (IfcRelVoidsElement). Permite tener en cuenta los huecos de forma auditable (D7)."""
    aberturas = []
    for rel in getattr(elemento, "HasOpenings", None) or []:
        op = getattr(rel, "RelatedOpeningElement", None)
        if op is not None:
            aberturas.append(op)
    return aberturas


def clasificacion_de(elemento) -> dict:
    """Doble clasificación {uniclass:{codigo,titulo}, bsdd:{codigo}} desde
    IfcRelAssociatesClassification, si está presente. Cosmética para el motor (mapea por CLASE),
    útil para el modelo neutro y C7."""
    import ifcopenshell.util.element as _ue
    out: dict = {}
    try:
        refs = _ue.get_references(elemento) if hasattr(_ue, "get_references") else []
    except Exception:  # noqa: BLE001
        refs = []
    for ref in refs or []:
        ident = getattr(ref, "Identification", None) or getattr(ref, "ItemReference", None)
        nombre = getattr(ref, "Name", None)
        sistema = getattr(getattr(ref, "ReferencedSource", None), "Name", "") or ""
        entry = {"codigo": ident} if ident else {}
        if nombre:
            entry["titulo"] = nombre
        if "uniclass" in sistema.lower():
            out["uniclass"] = entry
        elif ident:
            out.setdefault("uniclass", entry)
    out.setdefault("bsdd", {"codigo": elemento.is_a()})
    return out


def ubicacion_de(elemento, disciplina: str | None = None) -> dict:
    """Ubicación {planta, disciplina} desde la estructura espacial contenedora (informativa)."""
    import ifcopenshell.util.element as _ue
    planta = None
    try:
        contenedor = _ue.get_container(elemento)
        if contenedor is not None and contenedor.is_a("IfcBuildingStorey"):
            planta = getattr(contenedor, "Name", None)
    except Exception:  # noqa: BLE001
        planta = None
    out: dict = {}
    if planta:
        out["planta"] = planta
    if disciplina:
        out["disciplina"] = disciplina
    return out


# ---- E2.1: cortes (agrupaciones nativas del IFC) — N-06 / C5·D20-D22 -----------------------
# Cada objeto medido gana su atribución a grupos por los cuatro ejes de corte
# (espacial/funcional/uniclass/gubim). Cada eje es una LISTA de pertenencias
# `{grupo, fraccion, fuente}` (D20): sólo la lista con `fraccion` soporta el reparto 50/50 de
# frontera (D21) y la pertenencia múltiple. El reparto se resuelve AQUÍ, al construir el modelo
# neutro (no en la proyección: el corte es consulta). Las funciones puras (`_agregar`,
# `reparto_zonas`, `sistema_fallback`) no requieren ifcopenshell y se testean en aislamiento.

def _agregar(pares: list[tuple]) -> list[dict]:
    """[(grupo, fraccion)] → [{grupo, fraccion, fuente:'ifc'}] agregando por grupo (orden estable)."""
    acc: dict = {}
    orden: list = []
    for g, fr in pares:
        if g not in acc:
            acc[g] = 0.0
            orden.append(g)
        acc[g] += fr
    return [{"grupo": g, "fraccion": round(acc[g], 6), "fuente": "ifc"} for g in orden]


def reparto_zonas(zonas_por_espacio: list[list]) -> list[dict]:
    """Reparto de frontera (N-06 / D21). `zonas_por_espacio`: un item por CADA espacio distinto que
    el elemento delimita, con la lista de nombres de zona de ese espacio. `fraccion = 1/N` por
    espacio, agregada por zona. Un tabique entre dos aulas (2 espacios, 2 zonas) → 0,5/0,5; frontera
    de un único espacio → 1,0; dos espacios de la misma zona → 1,0. Puro (testeable sin IFC).
    Los espacios sin zona no aportan pertenencia (atribución parcial si el modelo está incompleto)."""
    n = len(zonas_por_espacio)
    if n == 0:
        return []
    pares: list[tuple] = []
    for zonas in zonas_por_espacio:
        for z in zonas:
            pares.append((z, 1.0 / n))
    return _agregar(pares)


def sistema_fallback(tipos, atributos: dict, reglas_sistema: list, default: dict | None) -> list[dict]:
    """Fallback funcional del criterio (N-06 / D22), POR JERARQUÍA de tipos IFC: una regla casa si su
    `clase` es la clase del elemento O cualquiera de sus SUPERTIPOS (`tipos` = ascendencia IFC, de
    `tipos_de`). Así ~10 familias por dominio cubren el centenar de clases del estándar (p. ej. una
    sola regla `IfcDistributionElement` cubre toda la MEP; `IfcBuiltElement`/`IfcBuildingElement` es el
    catch-all constructivo). Orden = precedencia (específico→general): gana la primera regla que casa
    por tipo y, si trae `condicion` (p. ej. `is_external`), por atributos; un atributo desconocido
    (None) NO satisface la condicion → la regla condicionada se salta. Si ninguna casa, `default`.
    Puro (testeable pasando la lista de tipos)."""
    tset = set(tipos or [])
    for r in reglas_sistema or []:
        if r.get("clase") not in tset:
            continue
        cond = r.get("condicion") or {}
        if any((atributos or {}).get(k) != v for k, v in cond.items()):
            continue
        return [{"grupo": r["sistema"], "fraccion": 1.0, "fuente": "criterio"}]
    sis = (default or {}).get("sistema", "Sin clasificar")
    return [{"grupo": sis, "fraccion": 1.0, "fuente": "criterio"}]


def tipos_de(elemento) -> list[str]:
    """Ascendencia de tipos IFC del elemento (clase + supertipos, de la hoja a la raíz), para el
    fallback por jerarquía (D22). Lee la declaración del esquema; degrada a `[clase]` si no está
    disponible. No requiere que la clase esté en ninguna lista: se apoya en la herencia del estándar."""
    try:
        decl = elemento.wrapped_data.declaration()
    except Exception:  # noqa: BLE001
        try:
            return [elemento.is_a()]
        except Exception:  # noqa: BLE001
            return []
    nombres: list[str] = []
    visto: set = set()
    cur = decl
    while cur is not None:
        try:
            nombre = cur.name()
        except Exception:  # noqa: BLE001
            break
        if nombre in visto:
            break
        visto.add(nombre)
        nombres.append(nombre)
        try:
            cur = cur.supertype()
        except Exception:  # noqa: BLE001
            cur = None
    if not nombres:
        try:
            return [elemento.is_a()]
        except Exception:  # noqa: BLE001
            return []
    return nombres


def _grupos_de(entidad, tipo_ifc: str) -> list:
    """IfcGroup (IfcSystem/IfcZone) a los que pertenece la entidad, vía `HasAssignments`
    (IfcRelAssignsToGroup). `is_a(tipo_ifc)` cubre los subtipos (IfcDistributionSystem…)."""
    grupos = []
    for rel in getattr(entidad, "HasAssignments", None) or []:
        try:
            if not rel.is_a("IfcRelAssignsToGroup"):
                continue
        except Exception:  # noqa: BLE001
            continue
        g = getattr(rel, "RelatingGroup", None)
        if g is not None and g.is_a(tipo_ifc):
            grupos.append(g)
    return grupos


def _nombre(entidad) -> str:
    return getattr(entidad, "Name", None) or entidad.is_a()


def espacial_de(elemento) -> list[dict]:
    """Corte espacial: ruta del árbol de contención (IfcSpatialStructure; IFC 4.3 incl.
    IfcFacility/IfcFacilityPart). Atribución directa (1 elemento → 1 nodo, fraccion 1.0)."""
    import ifcopenshell.util.element as _ue
    try:
        cont = _ue.get_container(elemento)
    except Exception:  # noqa: BLE001
        cont = None
    nodos: list[str] = []
    cur = cont
    while cur is not None:
        try:
            es_espacial = cur.is_a("IfcSpatialElement") or cur.is_a("IfcSpatialStructureElement")
        except Exception:  # noqa: BLE001
            es_espacial = False
        if not es_espacial:
            break
        nodos.append(_nombre(cur))
        try:
            cur = _ue.get_aggregate(cur)
        except Exception:  # noqa: BLE001
            cur = None
    grupo = "/".join(reversed(nodos))
    return [{"grupo": grupo, "fraccion": 1.0, "fuente": "ifc"}] if grupo else []


def sistemas_de(elemento) -> list[dict]:
    """Corte funcional por IfcSystem (agrupa elementos, típ. MEP). Pertenencia múltiple → 1/N."""
    grupos = _grupos_de(elemento, "IfcSystem")
    n = len(grupos)
    if n == 0:
        return []
    return _agregar([(_nombre(g), 1.0 / n) for g in grupos])


def zonas_de(elemento) -> list[dict]:
    """Corte funcional por IfcZone vía IfcRelSpaceBoundary: espacios que el elemento delimita
    (`ProvidesBoundaries`) → zonas de esos espacios, con reparto de frontera 1/N (D21)."""
    espacios: list = []
    for rel in getattr(elemento, "ProvidesBoundaries", None) or []:
        sp = getattr(rel, "RelatingSpace", None)
        if sp is not None and sp not in espacios:
            espacios.append(sp)
    if not espacios:
        return []
    zonas_por_espacio = [[_nombre(z) for z in _grupos_de(sp, "IfcZone")] for sp in espacios]
    return reparto_zonas(zonas_por_espacio)


def is_external_de(elemento):
    """Pset_*Common.IsExternal (bool) del elemento, o None si no lo declara. Alimenta el fallback."""
    import ifcopenshell.util.element as _ue
    try:
        psets = _ue.get_psets(elemento) or {}
    except Exception:  # noqa: BLE001
        return None
    for props in psets.values():
        if isinstance(props, dict) and "IsExternal" in props:
            v = props["IsExternal"]
            if isinstance(v, bool):
                return v
    return None


def cortes_clasificacion(elemento) -> dict:
    """Cortes por clasificación (Uniclass / GuBIMClass) desde IfcRelAssociatesClassification.
    Atribución directa (etiqueta en el objeto, fraccion 1.0)."""
    import ifcopenshell.util.element as _ue
    out: dict = {}
    try:
        refs = _ue.get_references(elemento) if hasattr(_ue, "get_references") else []
    except Exception:  # noqa: BLE001
        refs = []
    for ref in refs or []:
        ident = getattr(ref, "Identification", None) or getattr(ref, "ItemReference", None)
        if not ident:
            continue
        sistema = (getattr(getattr(ref, "ReferencedSource", None), "Name", "") or "").lower()
        item = {"grupo": ident, "fraccion": 1.0, "fuente": "ifc"}
        eje = "gubim" if "gubim" in sistema else "uniclass"
        out.setdefault(eje, []).append(item)
    return out


def cortes_de(elemento, criterio: dict | None = None) -> dict:
    """Ensambla `cortes{espacial, funcional, uniclass, gubim}` del elemento (N-06). Funcional por
    prioridad IfcSystem > IfcZone > fallback del criterio (`reglas_sistema`, fuente=criterio). Los
    ejes sin agrupación conocida se OMITEN (forward-open: nunca error)."""
    cortes: dict = {}
    esp = espacial_de(elemento)
    if esp:
        cortes["espacial"] = esp
    func = sistemas_de(elemento) or zonas_de(elemento)
    if not func and criterio:
        func = sistema_fallback(
            tipos_de(elemento),
            {"is_external": is_external_de(elemento)},
            criterio.get("reglas_sistema") or [],
            criterio.get("reglas_sistema_default"),
        )
    if func:
        cortes["funcional"] = func
    clasif = cortes_clasificacion(elemento)
    for eje in ("uniclass", "gubim"):
        if clasif.get(eje):
            cortes[eje] = clasif[eje]
    return cortes
