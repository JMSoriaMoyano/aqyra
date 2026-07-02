"""
SOLVER DE MANNING DE RED EN LAMINA LIBRE (flujo por gravedad). Disciplina
`obras-lineales`, PT 6.2 (Ola 6). NACE el solver de Manning SOBRE EL GRAFO DE RED:
es la primera vez que `obras-lineales` cruza la frontera de red (decision nº7
"grafo + N solvers"; el nucleo da TOPOLOGIA, no calcula).

Reutiliza el MOTOR DE RED de la Ola 4 (`instalaciones/red/solver_red.py`): la
construccion del ARBOL por BFS, el reparto de caudales por CONTINUIDAD aguas abajo y
el reparto hiperestatico por HARDY-CROSS en mallas. La fisica cambia: en vez de
Darcy-Weisbach a presion, resuelve el CALADO NORMAL en seccion parcialmente llena por
MANNING (Q = (1/n)*A*R^(2/3)*J^(1/2)), reutilizando la geometria de calado parcial de
`drenaje/odt.py` (geom_circular / geom_marco / calado por biseccion).

INVERSION RESPECTO AL SOLVER A PRESION (saneamiento):
  - El ANCLA del arbol es el VERTIDO (outfall), no una fuente de presion. El BFS
    arranca desde el/los nodo(s) `tipo:"vertido"`; el caudal de un tramo es la
    demanda acumulada del SUBARBOL AGUAS ARRIBA que drena hacia el vertido.
  - El flujo es por GRAVEDAD: la PENDIENTE J de cada tramo la fijan las COTAS DE
    SOLERA de sus nodos (no la presion). J = (solera_aguas_arriba - solera_aguas_
    abajo) / L, en el sentido del flujo. Si J<=0 (contrapendiente o tramo sin
    pendiente) el tramo NO desagua por gravedad -> error.

MALLAS (cableado, decision del ICCP 22/06/2026): el arbol que converge al vertido es
el caso de 0 lazos (sin regresion). Si hay colectores en MALLA (cuerdas/chords entre
pozos) se activa un HARDY-CROSS adaptado a lamina libre: el cierre por lazo es sobre
la PERDIDA DE CARGA POR FRICCION h_f = S_f*L (S_f pendiente motriz de Manning al
calado en circulacion), no sobre presion. Es una aproximacion de predimensionado para
un regimen poco habitual en saneamiento por gravedad [confirmar AN].

COMPRUEBA por tramo: GRADO DE LLENADO (y/H <= fill_max ~0.75), VELOCIDAD en banda de
autolimpieza<->no erosion, PENDIENTE > 0 (y minima por velocidad) y DIAMETRO minimo.
Reporta ademas el regimen (numero de Froude, informativo).

NO lee IFC (eso es C1, vive en iso19650-openbim). Consume el modelo neutro de red
(JSON). Es STDLIB PURA (reutiliza odt.py del propio plugin).

NDP (todos [confirmar AN] -- criterio del despacho / EN 752):
  - n de Manning por material del colector (hormigon 0.013, PVC 0.009, gres 0.013...).
  - fill_max = 0.75 (grado de llenado maximo de proyecto en residuales).
  - velocidad: v_min 0.6 m/s (autolimpieza), v_max 5.0 m/s (no erosion).
  - DN minimo de colector 300 mm; pendiente minima implicada por v_min.

Todo resultado es de predimensionado/asistencia y debe ser revisado y firmado por
tecnico competente (Ingeniero de Caminos).
"""
import json
import math
import os
import sys

# --- reuso interno (mismo plugin): geometria de calado parcial del PT 6.1 -----
_HERE = os.path.dirname(os.path.abspath(__file__))
_DRENAJE = os.path.join(_HERE, "..", "drenaje")
if _DRENAJE not in sys.path:
    sys.path.insert(0, _DRENAJE)
import odt  # noqa: E402  (geom_circular, geom_marco, calado por biseccion)

G = 9.81

# --- n de Manning por material del colector (s/m^(1/3)) -- NDP [confirmar AN] --
N_MANNING = {
    "hormigon": 0.013,
    "hormigon_in_situ": 0.015,
    "pvc": 0.009,
    "pe": 0.009,
    "polietileno": 0.009,
    "gres": 0.013,
    "fundicion": 0.012,
    "fibrocemento": 0.013,
}
N_DEF = 0.013                 # def.: hormigon
FILL_MAX_DEF = 0.75           # grado de llenado maximo (residuales) [confirmar AN]
V_MIN_DEF = 0.6               # m/s velocidad de autolimpieza [confirmar AN]
V_MAX_DEF = 5.0               # m/s velocidad de no erosion [confirmar AN]
DN_MIN_DEF_MM = 300.0         # diametro minimo de colector [confirmar AN]

# tolerancias de convergencia de Hardy-Cross (lamina libre)
HC_MAX_ITER = 300
HC_TOL_Q = 1.0e-7    # m3/s
HC_TOL_H = 1.0e-5    # m  (residuo de perdida por lazo, en m.c.a.)


# =============================================================================
# Geometria / hidraulica de tramo (Manning, seccion parcialmente llena)
# =============================================================================
def _n_manning(t):
    if t.get("n_manning") is not None:
        return float(t["n_manning"])
    mat = str(t.get("material") or "").strip().lower().replace(" ", "_")
    return N_MANNING.get(mat, N_DEF)


def _es_marco(t):
    return (t.get("seccion") == "marco") or (t.get("B_m") is not None and t.get("dn") is None)


def _geom(t, y):
    """Area mojada, perimetro mojado y ancho superficial al calado y."""
    if _es_marco(t):
        return odt.geom_marco(float(t["B_m"]), float(t["H_m"]), y)
    D = float(t["dn"]) / 1000.0
    return odt.geom_circular(D, y)


def _altura(t):
    """Altura util de la seccion (H del marco o D del tubo), en metros."""
    if _es_marco(t):
        return float(t["H_m"])
    return float(t["dn"]) / 1000.0


def _calado_normal(t, Q, J, n, fill_cap=0.999):
    """Calado normal y (m) que para la pendiente J transporta el caudal Q por
    Manning. Devuelve None si la seccion SE SOBRECARGA (Q > capacidad a tubo
    practicamente lleno)."""
    H = _altura(t)
    if Q <= 0 or J <= 0:
        return 0.0 if Q <= 0 else None

    def q(y):
        A, P, _ = _geom(t, y)
        if A <= 0 or P <= 0:
            return 0.0
        return (1.0 / n) * A * (A / P) ** (2.0 / 3.0) * math.sqrt(max(J, 0.0))

    y_max = fill_cap * H
    if q(y_max) < Q:
        return None                      # sobrecarga (entra en carga)
    lo, hi = 0.0, y_max
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if q(mid) < Q:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-7:
            break
    return 0.5 * (lo + hi)


def hidraulica_tramo(t, Q_abs, J, n):
    """Hidraulica de un tramo a caudal |Q| (m3/s) y pendiente J (m/m) por Manning.
    Devuelve dict con calado y, llenado y/H, velocidad v, pendiente motriz S_f,
    perdida h_f=S_f*L, numero de Froude y bandera de sobrecarga."""
    L = float(t.get("longitud", 0.0) or 0.0)
    H = _altura(t)
    if Q_abs <= 0:
        return {"y_m": 0.0, "llenado": 0.0, "v_m_s": 0.0, "S_f": 0.0,
                "h_f_m": 0.0, "froude": None, "sobrecarga": False, "H_m": H}
    y = _calado_normal(t, Q_abs, J, n)
    sobrecarga = y is None
    if sobrecarga:
        y = 0.999999 * H                 # a tubo lleno (en carga): proxy
    A, P, T = _geom(t, y)
    if A <= 0 or P <= 0:
        return {"y_m": 0.0, "llenado": 0.0, "v_m_s": 0.0, "S_f": 0.0,
                "h_f_m": 0.0, "froude": None, "sobrecarga": sobrecarga, "H_m": H}
    R = A / P
    v = Q_abs / A
    S_f = (n * n * Q_abs * Q_abs) / (A * A * R ** (4.0 / 3.0))   # pendiente motriz
    h_f = S_f * L
    froude = v / math.sqrt(G * A / T) if T > 0 else None
    return {"y_m": y, "llenado": y / H if H > 0 else None, "v_m_s": v,
            "S_f": S_f, "h_f_m": h_f, "froude": froude,
            "sobrecarga": sobrecarga, "H_m": H}


# =============================================================================
# Topologia: arbol desde el vertido + clasificacion arbol/cuerdas + lazos
# (reutiliza la construccion probada del solver a presion de la Ola 4)
# =============================================================================
def _arbol_desde_vertido(nodos, tramos, raices):
    """Orienta la red como ARBOL por BFS desde las raices (nodos VERTIDO/outfall)."""
    ady = {nm: [] for nm in nodos}
    for tid, t in tramos.items():
        ni, nj = t.get("ni"), t.get("nj")
        if ni in ady and nj in ady:
            ady[ni].append((tid, nj))
            ady[nj].append((tid, ni))
    visto = set()
    padre_tramo = {}
    hijos = {nm: [] for nm in nodos}
    orden = []
    usados = set()
    cola = [r for r in raices if r in nodos]
    for r in cola:
        visto.add(r)
    i = 0
    while i < len(cola):
        u = cola[i]; i += 1
        orden.append(u)
        for tid, v in ady[u]:
            if v not in visto:
                visto.add(v)
                padre_tramo[v] = (tid, u)
                hijos[u].append((tid, v))
                usados.add(tid)
                cola.append(v)
    return padre_tramo, hijos, orden


def _clasificar_tramos(nodos, tramos, padre_tramo):
    """Separa los tramos en ARBOL (generador) y CUERDAS (cierran lazo)."""
    arbol = set(tid for (tid, _pa) in padre_tramo.values())
    chords = []
    for tid, t in tramos.items():
        ni, nj = t.get("ni"), t.get("nj")
        if ni in nodos and nj in nodos and ni != nj and tid not in arbol:
            chords.append(tid)
    return arbol, chords


def _ancestros(nm, padre_tramo, nmax):
    chain = [nm]; cur = nm; g = 0
    while cur in padre_tramo and g < nmax:
        _tid, pa = padre_tramo[cur]
        chain.append(pa); cur = pa; g += 1
    return chain


def _ruta_nodos(a, b, padre_tramo, nmax):
    ca = _ancestros(a, padre_tramo, nmax)
    cb = _ancestros(b, padre_tramo, nmax)
    idx_b = {n: i for i, n in enumerate(cb)}
    lca = None; ia = None
    for i, n in enumerate(ca):
        if n in idx_b:
            lca = n; ia = i; break
    if lca is None:
        return None
    subida = ca[:ia + 1]
    bajada = cb[:idx_b[lca]]
    return subida + list(reversed(bajada))


def _edge_between(X, Y, tramos, padre_tramo):
    tid = None
    if X in padre_tramo and padre_tramo[X][1] == Y:
        tid = padre_tramo[X][0]
    elif Y in padre_tramo and padre_tramo[Y][1] == X:
        tid = padre_tramo[Y][0]
    if tid is None:
        return None, 0
    t = tramos[tid]
    orient = 1 if (t.get("ni") == X and t.get("nj") == Y) else -1
    return tid, orient


def _construir_lazos(nodos, tramos, padre_tramo, chords):
    nmax = len(nodos) + 1
    lazos = []
    for c in chords:
        t = tramos[c]; a = t.get("ni"); b = t.get("nj")
        ruta = _ruta_nodos(b, a, padre_tramo, nmax)
        if not ruta or ruta[0] != b or ruta[-1] != a:
            continue
        lazo = [(c, 1)]
        ok = True
        for i in range(len(ruta) - 1):
            tid_e, orient = _edge_between(ruta[i], ruta[i + 1], tramos, padre_tramo)
            if tid_e is None:
                ok = False; break
            lazo.append((tid_e, orient))
        if ok:
            lazos.append(lazo)
    return lazos


# =============================================================================
# Demanda / pendientes
# =============================================================================
def _demanda_nodo(modelo, activos):
    """Caudal de saneamiento (m3/s) INYECTADO en cada nodo por los terminales
    (acometidas/sumideros) activos. En saneamiento el terminal es un APORTE."""
    q = {}
    for term in modelo.get("terminales", []):
        if term.get("id") not in activos:
            continue
        nm = term.get("nodo")
        d = term.get("demanda") or {}
        ql = d.get("caudal_l_s")
        if ql is None:
            ql = term.get("caudal_min")
        if nm is not None and ql:
            q[nm] = q.get(nm, 0.0) + float(ql) / 1000.0
    return q


def _solera(nodos, nm):
    """Cota de solera (invert) de un nodo: Pset/clave `cota_solera` si esta; si no,
    la z del nodo [confirmar AN]."""
    n = nodos.get(nm, {}) or {}
    cs = n.get("cota_solera")
    if cs is None:
        cs = n.get("z", 0.0)
    return float(cs)


# =============================================================================
# Hardy-Cross adaptado a lamina libre (cierre por perdida de friccion h_f)
# =============================================================================
def _pendiente_tramo(t, nodos, q_ni_nj):
    """Pendiente J (m/m) en el SENTIDO DEL FLUJO. q_ni_nj es el caudal con signo
    ni->nj; si >0 fluye ni->nj (aguas arriba=ni)."""
    ni, nj = t.get("ni"), t.get("nj")
    L = float(t.get("longitud", 0.0) or 0.0)
    if L <= 0:
        return 0.0
    s_ni, s_nj = _solera(nodos, ni), _solera(nodos, nj)
    up, dn = (s_ni, s_nj) if q_ni_nj >= 0 else (s_nj, s_ni)
    return (up - dn) / L


def _hardy_cross_ll(tramos, nodos, Qsig, lazos):
    """Reparto hiperestatico en MALLA por correccion de Hardy-Cross sobre la
    perdida de friccion de Manning h_f. Adaptacion de predimensionado a lamina
    libre [confirmar AN]."""
    iters = 0
    convergio = False
    for it in range(HC_MAX_ITER):
        dq_max = 0.0; res_max = 0.0
        for lazo in lazos:
            E = 0.0; D = 0.0
            for tid, orient in lazo:
                t = tramos[tid]; q = Qsig[tid]; aq = abs(q)
                n = _n_manning(t)
                J = abs(_pendiente_tramo(t, nodos, q))
                h = hidraulica_tramo(t, aq, J, n)
                hf = h["h_f_m"]
                signo = 1.0 if q >= 0 else -1.0
                E += orient * hf * signo
                if aq > 1e-12:
                    D += 2.0 * hf / aq
            dq = (-E / D) if D > 0 else 0.0
            for tid, orient in lazo:
                Qsig[tid] += orient * dq
            dq_max = max(dq_max, abs(dq))
            res_max = max(res_max, abs(E))
        iters = it + 1
        if dq_max < HC_TOL_Q and res_max < HC_TOL_H:
            convergio = True
            break
    residuos = []
    res_max = 0.0
    for lazo in lazos:
        E = 0.0
        for tid, orient in lazo:
            t = tramos[tid]; q = Qsig[tid]; aq = abs(q)
            n = _n_manning(t); J = abs(_pendiente_tramo(t, nodos, q))
            hf = hidraulica_tramo(t, aq, J, n)["h_f_m"]
            E += orient * hf * (1.0 if q >= 0 else -1.0)
        residuos.append(round(E, 8))
        res_max = max(res_max, abs(E))
    return iters, residuos, res_max, convergio


# =============================================================================
# Resolucion
# =============================================================================
def resolver(modelo, fill_max=FILL_MAX_DEF, v_min=V_MIN_DEF, v_max=V_MAX_DEF,
             dn_min_mm=DN_MIN_DEF_MM, activos=None):
    nodos = {k: dict(v) for k, v in modelo["nodos"].items()}
    tramos = modelo["tramos"]
    avisos = []

    # raices = nodos de VERTIDO (outfall). En fuentes[] el parser emite el vertido.
    raices = [f.get("nodo") for f in modelo.get("fuentes", []) if f.get("nodo")]
    for nm, n in nodos.items():
        if n.get("tipo") == "vertido" and nm not in raices:
            raices.append(nm)
    if not raices:
        return {"veredicto": "NO CUMPLE",
                "errores": ["La red no tiene VERTIDO (outfall/ancla); no se puede "
                            "orientar el flujo por gravedad."],
                "avisos": avisos}

    if activos is None:
        # en saneamiento todas las acometidas aportan a la vez (la punta ya esta
        # en la demanda); no hay seleccion de simultaneos tipo PCI.
        activos = [t.get("id") for t in modelo.get("terminales", []) if t.get("id")]
    activos = set(activos)

    padre_tramo, hijos, orden = _arbol_desde_vertido(nodos, tramos, raices)
    _arbol_tids, chords = _clasificar_tramos(nodos, tramos, padre_tramo)
    n_lazos = len(chords)

    # 1) reparto de caudales por continuidad en el ARBOL: el caudal de un tramo
    #    (nodo -> padre, hacia el vertido) es la demanda acumulada del subarbol
    #    AGUAS ARRIBA. Identico a la continuidad del solver a presion, invertido.
    dem_nodo = _demanda_nodo(modelo, activos)
    q_subarbol = {nm: 0.0 for nm in nodos}
    for nm in reversed(orden):
        q_subarbol[nm] += dem_nodo.get(nm, 0.0)
        if nm in padre_tramo:
            _tid, pa = padre_tramo[nm]
            q_subarbol[pa] += q_subarbol[nm]
    # caudal con signo (sentido nativo ni->nj). El flujo va del hijo (aguas arriba)
    # al padre (aguas abajo, hacia el vertido).
    Qsig = {tid: 0.0 for tid in tramos}
    for nm in orden:
        for tid, h in hijos[nm]:
            q = q_subarbol[h]                  # flujo hijo(h) -> padre(nm), m3/s
            t = tramos[tid]
            # sentido del flujo: h -> nm. Qsig positivo si coincide con ni->nj.
            Qsig[tid] = q if (t.get("ni") == h and t.get("nj") == nm) else -q

    # 1bis) mallas: reparto hiperestatico por Hardy-Cross (lamina libre)
    hardy = None
    if n_lazos:
        lazos = _construir_lazos(nodos, tramos, padre_tramo, chords)
        iters, residuos, res_max, convergio = _hardy_cross_ll(
            tramos, nodos, Qsig, lazos)
        hardy = {"metodo": "Hardy-Cross lamina libre (cierre por h_f de Manning, "
                           "n=2) [confirmar AN]",
                 "n_lazos": n_lazos, "iteraciones": iters,
                 "residuo_lazo_max_m": round(res_max, 8),
                 "residuos_lazo_m": residuos, "convergio": convergio}
        avisos.append("Red MALLADA: %d lazo(s) resuelto(s) por Hardy-Cross lamina "
                      "libre (%d iter, residuo max %.6g m, %s) [aproximacion de "
                      "predimensionado, confirmar AN]."
                      % (n_lazos, iters, res_max,
                         "converge" if convergio else "NO converge"))

    # 2) hidraulica por tramo (Manning) + comprobaciones
    tramos_out = {}
    for tid, t in tramos.items():
        q = Qsig[tid]
        Qabs = abs(q)
        n = _n_manning(t)
        J = _pendiente_tramo(t, nodos, q)
        sentido = "ni->nj" if q >= 0 else "nj->ni"
        dn = t.get("dn")
        rec = {"caudal_l_s": round(Qabs * 1000.0, 4),
               "caudal_signed_l_s": round(q * 1000.0, 4),
               "sentido": sentido, "dn": dn,
               "seccion": "marco" if _es_marco(t) else "circular",
               "longitud_m": round(float(t.get("longitud", 0.0) or 0.0), 4),
               "n_manning": n, "pendiente_J": round(J, 6),
               "ni": t.get("ni"), "nj": t.get("nj")}
        if J <= 0:
            rec.update({"calado_y_m": None, "llenado_pct": None,
                        "velocidad_m_s": None, "froude": None, "regimen": None,
                        "sobrecarga": None})
            rec["errores_tramo"] = ["Pendiente J=%.5f m/m <= 0: el tramo no desagua "
                                    "por gravedad (contrapendiente o sin pendiente)."
                                    % J]
            tramos_out[tid] = rec
            continue
        h = hidraulica_tramo(t, Qabs, J, n)
        llen = h["llenado"]
        froude = h["froude"]
        regimen = None
        if froude is not None:
            regimen = "subcritico" if froude < 1.0 else ("critico" if abs(froude - 1.0) < 1e-3 else "supercritico")
        et = []
        if h["sobrecarga"]:
            et.append("Tramo EN CARGA: el caudal supera la capacidad a seccion "
                      "llena (y/%s>1); aumentar DN o pendiente." % ("H" if _es_marco(t) else "D"))
        elif llen is not None and llen > fill_max + 1e-9:
            et.append("Grado de llenado %.0f%% > maximo %.0f%%: aumentar DN o "
                      "pendiente." % (100 * llen, 100 * fill_max))
        v = h["v_m_s"]
        if Qabs > 0:
            if v + 1e-9 < v_min:
                et.append("Velocidad %.2f m/s < autolimpieza %.2f m/s "
                          "(sedimentacion): aumentar pendiente o reducir DN."
                          % (v, v_min))
            elif v > v_max + 1e-9:
                et.append("Velocidad %.2f m/s > maxima %.2f m/s (erosion): reducir "
                          "pendiente o proteger la solera." % (v, v_max))
        if dn is not None and not _es_marco(t) and float(dn) + 1e-9 < dn_min_mm:
            et.append("DN %s mm < minimo %.0f mm (conservacion/limpieza)."
                      % (dn, dn_min_mm))
        rec.update({"calado_y_m": round(h["y_m"], 4),
                    "llenado_pct": round(100 * llen, 2) if llen is not None else None,
                    "velocidad_m_s": round(v, 4),
                    "froude": round(froude, 4) if froude is not None else None,
                    "regimen": regimen, "sobrecarga": h["sobrecarga"],
                    "errores_tramo": et})
        tramos_out[tid] = rec

    # 3) caudal total vertido (suma de demandas activas)
    q_total = sum(dem_nodo.values())

    # 4) veredicto
    errores = []
    for tid, to in tramos_out.items():
        for e in to.get("errores_tramo", []):
            errores.append("Tramo %s: %s" % (to.get("elemento", tid), e))
    v_lista = [to["velocidad_m_s"] for to in tramos_out.values()
               if to.get("velocidad_m_s") is not None]
    v_pico = max(v_lista) if v_lista else 0.0
    llen_lista = [to["llenado_pct"] for to in tramos_out.values()
                  if to.get("llenado_pct") is not None]
    llen_pico = max(llen_lista) if llen_lista else 0.0
    if hardy is not None and not hardy["convergio"]:
        errores.append("Hardy-Cross (lamina libre) no convergio (residuo lazo "
                       "%.6g m)." % hardy["residuo_lazo_max_m"])
    veredicto = "CUMPLE" if not errores else "NO CUMPLE"

    return {
        "veredicto": veredicto,
        "metodo": "Manning lamina libre (calado normal por seccion parcialmente "
                  "llena) [confirmar AN]",
        "sistema": modelo.get("sistema", {}).get("tipo"),
        "topologia": {"n_nodos": len(nodos), "n_tramos": len(tramos),
                      "n_lazos": n_lazos, "tipo": "malla" if n_lazos else "arbol"},
        "hardy_cross": hardy,
        "hipotesis": {"fill_max": fill_max, "v_min_m_s": v_min, "v_max_m_s": v_max,
                      "dn_min_mm": dn_min_mm, "n_manning_def": N_DEF,
                      "cota_solera": "Pset/IFC si esta; si no, z del nodo [confirmar AN]"},
        "caudal_total_vertido_l_s": round(q_total * 1000.0, 4),
        "velocidad_pico_m_s": round(v_pico, 4),
        "llenado_pico_pct": round(llen_pico, 2),
        "tramos": tramos_out,
        "nodos": {nm: {"tipo": nodos[nm].get("tipo"),
                       "cota_solera_m": round(_solera(nodos, nm), 4)} for nm in nodos},
        "terminales": [{"id": t.get("id"), "nodo": t.get("nodo"),
                        "caudal_l_s": ((t.get("demanda") or {}).get("caudal_l_s")
                                       if (t.get("demanda") or {}).get("caudal_l_s") is not None
                                       else t.get("caudal_min")),
                        "activo": t.get("id") in activos}
                       for t in modelo.get("terminales", [])],
        "vertidos": [r for r in raices],
        "errores": errores, "avisos": avisos,
    }


def main(modelo_path, out=None):
    with open(modelo_path, encoding="utf-8") as fh:
        modelo = json.load(fh)
    # propaga `elemento` (Name del tramo) a la salida para trazabilidad/write-back
    res = resolver(modelo)
    for tid, to in res.get("tramos", {}).items():
        to["elemento"] = (modelo.get("tramos", {}).get(tid, {}) or {}).get("elemento", tid)
    print("=" * 66)
    print("SOLVER MANNING DE RED (LAMINA LIBRE) --", res.get("sistema"))
    print("=" * 66)
    print(" Metodo:", res["metodo"])
    print(" Topologia:", res["topologia"])
    if res.get("hardy_cross"):
        hc = res["hardy_cross"]
        print(" Hardy-Cross: %d lazo(s), %d iter, residuo max %.6g m, %s"
              % (hc["n_lazos"], hc["iteraciones"], hc["residuo_lazo_max_m"],
                 "converge" if hc["convergio"] else "NO converge"))
    print(" Caudal total vertido: %.3f l/s" % res["caudal_total_vertido_l_s"])
    print(" Velocidad pico: %.3f m/s | llenado pico: %.1f %%"
          % (res["velocidad_pico_m_s"], res["llenado_pico_pct"]))
    for tid, to in res["tramos"].items():
        print("  %s [%s]: Q=%.2f l/s J=%.4f y=%s m llenado=%s%% v=%s m/s %s"
              % (to.get("elemento", tid), tid, to["caudal_l_s"], to["pendiente_J"],
                 to.get("calado_y_m"), to.get("llenado_pct"),
                 to.get("velocidad_m_s"), to.get("regimen") or ""))
    for w in res["avisos"]:
        print("  ! ", w)
    for e in res["errores"]:
        print("  X ", e)
    print("\nVEREDICTO:", res["veredicto"])
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=2, ensure_ascii=False)
        print("Resultado escrito en", out)
    return 0 if res["veredicto"] == "CUMPLE" else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
