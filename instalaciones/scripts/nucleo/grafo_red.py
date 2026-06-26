"""
NUCLEO TRANSVERSAL - grafo de red nodos+tramos (PT 4.1, Ola 4, hueco H1).

Construye la TOPOLOGIA de una red de elementos lineales (barras estructurales,
tuberias/conductos/cables MEP, colectores) a partir de sus directrices:
  - fusion de nudos proximos por TOLERANCIA (snap), con representante "primero
    anadido" y registro de los huecos/solapes puenteados,
  - TROCEO en cruces T/X: si el extremo de un tramo cae en el interior de otro,
    se trocea el pasante proyectando el punto de corte sobre su directriz,
  - limpieza por COMPONENTES CONEXAS (union-find): descarta los subgrafos sin
    ningun nudo "ancla" (en estructuras = nudo apoyado; en MEP = nudo fuente).

Es AGNOSTICO AL SOLVER: devuelve nodos + tramos + topologia; quien calcula
(FEM estructural, hidraulico Darcy/Manning, electrico, termico) es la disciplina.
Mismo grafo conceptual que el grafo de nudos estructural endurecido en R5
(puente_analitico/puente.py), de donde se extrae sin cambiar el comportamiento.

API estable:
  Primitivas (consumidas por puente.py para retrocompatibilidad byte a byte):
    RegistroNodos(tol)                       -> fusion de nudos por tolerancia
    proyeccion(p, a, b)                       -> proyeccion ortogonal de p sobre a-b
    punto_en_segmento(p, a, b, tol)           -> p cae en el INTERIOR de a-b ?
    bbox_xy(esquinas)                         -> (xmin, xmax, ymin, ymax)
    cortes_por_interseccion(segmentos, tol)   -> puntos de troceo T/X por segmento
    ordenar_segmento(p0, p1, extra)           -> puntos ordenados por parametro t
    filtrar_componentes_desconectadas(nodos, tramos, es_ancla) -> (drop_tramos, drop_nodos)
  Alto nivel (gancho H2: un ifc_to_model_mep.py la alimenta con segmentos de
  IfcDistributionPort/IfcRelConnectsPorts sin tocar el nucleo):
    construir_grafo(segmentos, tol, etiqueta=...) -> {nodos, tramos, metricas}

Todo resultado es de predimensionado/asistencia y debe ser revisado y firmado por
tecnico competente.
"""
import math

TOL = 1e-3  # tolerancia de fusion de nudos por defecto (m)


# --- fusion de nudos --------------------------------------------------------
class RegistroNodos:
    """Registro de nudos con fusion por tolerancia. Conserva el PRIMER punto del
    clenter de cada cluster (representante "primero anadido"), lo que -con el orden
    de proceso de la disciplina- reproduce luces/posiciones exactas (leccion R5)."""
    def __init__(self, tol=TOL):
        self.tol = tol
        self.coords = []   # lista de [x,y,z]
        self.names = []    # nombre asignado (N1, N2, ...)
        self.fused = []    # (nombre_nodo, distancia) por cada fusion de extremos

    def add(self, c):
        for i, q in enumerate(self.coords):
            if (abs(q[0] - c[0]) <= self.tol and abs(q[1] - c[1]) <= self.tol
                    and abs(q[2] - c[2]) <= self.tol):
                d = math.sqrt(sum((q[k] - c[k]) ** 2 for k in range(3)))
                self.fused.append((self.names[i], d))
                return i
        self.coords.append([float(c[0]), float(c[1]), float(c[2])])
        self.names.append("N%d" % len(self.coords))
        return len(self.coords) - 1


# --- geometria del grafo ----------------------------------------------------
def proyeccion(p, a, b):
    """Proyeccion ortogonal de p sobre la recta a-b (para trocear con offset:
    el punto de corte se lleva a la directriz del pasante, que queda recto)."""
    ab = [b[i] - a[i] for i in range(3)]
    L2 = sum(c * c for c in ab) or 1.0
    t = sum((p[i] - a[i]) * ab[i] for i in range(3)) / L2
    return [a[i] + t * ab[i] for i in range(3)]


def punto_en_segmento(p, a, b, tol):
    """True si p cae en el INTERIOR del segmento a-b (para troceo en cruces).
    Margen parametrico RELATIVO a L (no absoluto): evita mezclar distancia y
    fraccion (correccion de R5)."""
    ab = [b[i] - a[i] for i in range(3)]
    ap = [p[i] - a[i] for i in range(3)]
    L2 = sum(c * c for c in ab)
    if L2 < tol * tol:
        return False
    t = sum(ap[i] * ab[i] for i in range(3)) / L2
    marg = tol / math.sqrt(L2)
    if t <= marg or t >= 1.0 - marg:
        return False  # coincide con un extremo, no es interior
    proj = [a[i] + t * ab[i] for i in range(3)]
    d = math.sqrt(sum((p[i] - proj[i]) ** 2 for i in range(3)))
    return d <= tol


def bbox_xy(esquinas):
    """(xmin, xmax, ymin, ymax) de una lista de puntos [x,y,...]."""
    xs = [c[0] for c in esquinas]
    ys = [c[1] for c in esquinas]
    return min(xs), max(xs), min(ys), max(ys)


def cortes_por_interseccion(segmentos, tol):
    """segmentos: lista de (p0, p1). Devuelve una lista PARALELA: por cada
    segmento, la lista de puntos de corte (proyeccion sobre su directriz de los
    extremos de OTROS segmentos que caen en su interior). Replica el troceo T/X."""
    extremos = []
    for p0, p1 in segmentos:
        extremos.append(p0)
        extremos.append(p1)
    cortes = [[] for _ in segmentos]
    for i, (p0, p1) in enumerate(segmentos):
        for pe in extremos:
            if punto_en_segmento(pe, p0, p1, tol):
                cortes[i].append(proyeccion(pe, p0, p1))
    return cortes


def ordenar_segmento(p0, p1, extra):
    """Devuelve los puntos [p0, p1] + extra ORDENADOS por su parametro t sobre la
    directriz p0->p1 y deduplicados (|dt| < 1e-6). Cada par consecutivo del
    resultado define un sub-tramo recto."""
    ab = [p1[i] - p0[i] for i in range(3)]
    L2 = sum(c * c for c in ab) or 1.0
    pts = [p0, p1] + list(extra)
    uniq = []
    for p in pts:
        t = sum((p[i] - p0[i]) * ab[i] for i in range(3)) / L2
        if not any(abs(t - tt) < 1e-6 for tt, _ in uniq):
            uniq.append((t, p))
    uniq.sort(key=lambda x: x[0])
    return [u[1] for u in uniq]


# --- limpieza por componentes conexas (union-find) --------------------------
def filtrar_componentes_desconectadas(nodos, tramos, es_ancla):
    """Identifica los tramos de componentes NO conectadas a ningun nudo "ancla".
    GENERICO via el predicado es_ancla(nombre_nodo, dict_nodo) -> bool
    (estructuras: nudo apoyado; MEP: nudo fuente/acometida).

    nodos:  dict {nombre: {...}}
    tramos: dict {id: {"ni":.., "nj":.., ...}}
    Devuelve (drop_tramos, drop_nodos): ids de tramos a descartar y nombres de
    nudos que quedan huerfanos. NO muta las estructuras: el caller aplica la
    limpieza (y la de su propio payload: cargas, terminales, ...)."""
    padre = {nm: nm for nm in nodos}

    def find(a):
        while padre[a] != a:
            padre[a] = padre[padre[a]]
            a = padre[a]
        return a

    def union(a, b):
        padre[find(a)] = find(b)

    for t in tramos.values():
        if t["ni"] in padre and t["nj"] in padre:
            union(t["ni"], t["nj"])
    anclados = set(find(nm) for nm, n in nodos.items() if es_ancla(nm, n))
    drop_tramos = [tid for tid, t in tramos.items()
                   if find(t["ni"]) not in anclados]
    nodos_usados = set()
    for tid, t in tramos.items():
        if tid not in drop_tramos:
            nodos_usados.add(t["ni"])
            nodos_usados.add(t["nj"])
    drop_nodos = [nm for nm in nodos if nm not in nodos_usados]
    return drop_tramos, drop_nodos


# --- API de alto nivel (gancho H2 / MEP) ------------------------------------
def construir_grafo(segmentos, tol=TOL, etiqueta=None):
    """Construye el grafo nodos+tramos a partir de una lista de segmentos
    GENERICOS, lista para cualquier disciplina (estructuras via puente.py; MEP
    via un futuro ifc_to_model_mep.py por puertos/intersecciones).

    segmentos: lista de dicts {"p0": [x,y,z], "p1": [x,y,z], "payload": {...}?}.
    etiqueta(i) -> nombre del tramo i (por defecto "T1", "T2", ...).
    Devuelve:
      {"nodos":  {"N1": {"x","y","z"}, ...},
       "tramos": {"T1": {"ni","nj","payload"}, ...},
       "metricas": {"nudos_fusionados", "huecos_puenteados", "cruces_troceados"}}

    El troceo y la fusion usan las MISMAS primitivas que el grafo estructural, de
    modo que el comportamiento es identico al endurecido en R5."""
    if etiqueta is None:
        etiqueta = lambda i: "T%d" % (i + 1)
    segs = [(s["p0"], s["p1"]) for s in segmentos]
    cortes = cortes_por_interseccion(segs, tol)
    cruces = []
    for i, c in enumerate(cortes):
        for proj in c:
            cruces.append({"segmento": i, "punto": [round(x, 4) for x in proj]})
    nod = RegistroNodos(tol)
    tramos = {}
    cont = 0
    for i, s in enumerate(segmentos):
        p0, p1 = s["p0"], s["p1"]
        pts = ordenar_segmento(p0, p1, cortes[i])
        for k in range(len(pts) - 1):
            ia = nod.add(pts[k])
            ib = nod.add(pts[k + 1])
            tid = etiqueta(cont)
            cont += 1
            tramos[tid] = {"ni": nod.names[ia], "nj": nod.names[ib],
                           "payload": s.get("payload")}
    nodos = {}
    for i, c in enumerate(nod.coords):
        nodos[nod.names[i]] = {"x": c[0], "y": c[1], "z": c[2]}
    metricas = {
        "nudos_fusionados": len(nod.fused),
        "huecos_puenteados": [{"nodo": nm, "salto_m": round(d, 4)}
                              for nm, d in nod.fused if d > TOL],
        "cruces_troceados": cruces,
    }
    return {"nodos": nodos, "tramos": tramos, "metricas": metricas}
