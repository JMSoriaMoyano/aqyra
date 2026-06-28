"""
SOLVER HIDRAULICO DE RED A PRESION (Darcy-Weisbach). Disciplina `instalaciones`,
PT 4.3/4.4 (Ola 4). NACE el motor hidraulico de red (capacidad transversal del
ecosistema, reutilizable luego en obras hidraulicas a presion, Ola 6).

FRONTERA (contratos C1/CN-3 del nucleo): el NUCLEO da la TOPOLOGIA (nodos+tramos del
modelo neutro de red emitido por el parser MEP de iso19650-openbim, PT 4.2) y la
demanda la rellena `pci/bases_demanda.py` (hueco H3). Este modulo SOLO CALCULA:
  - reparto de caudales por continuidad en una red en ARBOL (raiz = fuente),
  - reparto HIPERESTATICO en redes MALLADAS (con bucles) por HARDY-CROSS
    (correccion por lazo, PT 4.4): continuidad en nudos + perdida de carga nula
    en cada lazo; el arbol es el caso particular de 0 lazos (sin regresion),
  - perdida de carga por tramo con DARCY-WEISBACH (friccion por Swamee-Jain,
    aprox. explicita de Colebrook-White),
  - propagacion de presiones desde la(s) fuente(s) (con cota geometrica),
  - comprobacion en terminales (caudal y presion dinamica minima).

NO lee IFC (eso es C1, vive en iso19650-openbim). Consume el modelo neutro (JSON).

Hipotesis y NDP (todos [confirmar AN/criterio del despacho]):
  - Fluido: agua a 20 C; densidad rho=998 kg/m3; visc. cinematica nu=1.01e-6 m2/s.
  - Rugosidad absoluta de tramo: clave `rugosidad` del modelo, en MILIMETROS
    (ej. acero galvanizado ~0.045-0.15 mm); si falta, 0.045 mm.
  - Perdidas localizadas (accesorios): mayoracion global k_acc sobre la friccion
    (def. 1.20 = +20 %), a falta de longitudes equivalentes por accesorio.
  - Velocidad maxima admisible: v_max (def. 6.0 m/s).
  - Mallas: reparto hiperestatico por Hardy-Cross (n=2, friccion reevaluada por
    iteracion). Base de lazos = ciclos fundamentales (chords del arbol generador).

Todo resultado es de predimensionado/asistencia y debe ser revisado y firmado por
tecnico competente (Ingeniero de Caminos).
"""
import json
import math

# --- constantes fisicas / criterios por defecto (NDP [confirmar AN]) ---------
RHO = 998.0          # kg/m3 (agua 20 C)
NU = 1.01e-6         # m2/s  (agua 20 C)
G = 9.81             # m/s2
RUG_DEF_MM = 0.045   # mm    (rugosidad absoluta por defecto, acero)
K_ACC_DEF = 1.20     # mayoracion por accesorios (perdidas localizadas)
V_MAX_DEF = 6.0      # m/s   (velocidad maxima admisible)

# tolerancias de convergencia de Hardy-Cross
HC_MAX_ITER = 300
HC_TOL_Q = 1.0e-7    # m3/s (= 1e-4 l/s) correccion de caudal despreciable
HC_TOL_H = 1.0e-4    # kPa  residuo de perdida por lazo despreciable


def factor_friccion(Re, eps_rel):
    """Factor de friccion de Darcy-Weisbach. Laminar f=64/Re (Re<2000); turbulento
    por SWAMEE-JAIN (aprox. explicita de Colebrook-White, valida 4e3<Re<1e8,
    1e-6<eps_rel<1e-2)."""
    if Re <= 0:
        return 0.0
    if Re < 2000.0:
        return 64.0 / Re
    den = math.log10(eps_rel / 3.7 + 5.74 / (Re ** 0.9))
    return 0.25 / (den * den)


def _perdida_tramo(t, Q_abs, k_acc):
    """Perdida de carga de un tramo para un caudal |Q| (m3/s). Devuelve
    (v, Re, f, dp_kPa) con dp ya mayorada por accesorios; (None,...) si sin DN."""
    dn = t.get("dn")
    D = (float(dn) / 1000.0) if dn else None  # mm -> m
    if not D or D <= 0:
        return (None, None, None, None)
    L = float(t.get("longitud", 0.0) or 0.0)
    rug = t.get("rugosidad")
    eps = (float(rug) if rug is not None else RUG_DEF_MM) / 1000.0  # mm -> m
    A = math.pi * D * D / 4.0
    v = Q_abs / A if A > 0 else 0.0
    Re = v * D / NU if v > 0 else 0.0
    f = factor_friccion(Re, eps / D)
    hf = f * (L / D) * v * v / (2.0 * G) if v > 0 else 0.0   # m.c.a.
    dp = RHO * G * hf * k_acc / 1000.0                        # kPa (con accesorios)
    return (v, Re, f, dp)


def _arbol_desde_fuente(nodos, tramos, raices):
    """Orienta la red como ARBOL por BFS desde las raices (nodos fuente). Devuelve:
      padre_tramo[nodo] = (tid, otro_nodo)  -- tramo que conecta el nodo a su padre,
      hijos[nodo] = [(tid, hijo), ...],
      orden = lista de nodos en orden BFS (de la fuente hacia las hojas),
      mallas = nº de tramos que cierran ciclo (no usados en el arbol)."""
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
    mallas = 0
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
            elif tid not in usados and padre_tramo.get(u, (None,))[0] != tid:
                mallas += 1
                usados.add(tid)
    return padre_tramo, hijos, orden, mallas


def _clasificar_tramos(nodos, tramos, padre_tramo):
    """Separa los tramos en ARBOL (los del arbol generador) y CHORDS (los que
    cierran lazo). nº de lazos independientes = len(chords)."""
    arbol = set(tid for (tid, _pa) in padre_tramo.values())
    chords = []
    for tid, t in tramos.items():
        ni, nj = t.get("ni"), t.get("nj")
        if ni in nodos and nj in nodos and ni != nj and tid not in arbol:
            chords.append(tid)
    return arbol, chords


def _ancestros(nm, padre_tramo, nmax):
    """Cadena de nodos desde nm hasta la raiz por padre_tramo."""
    chain = [nm]; cur = nm; g = 0
    while cur in padre_tramo and g < nmax:
        _tid, pa = padre_tramo[cur]
        chain.append(pa); cur = pa; g += 1
    return chain


def _ruta_nodos(a, b, padre_tramo, nmax):
    """Camino de nodos a->b a traves del arbol (a ... LCA ... b)."""
    ca = _ancestros(a, padre_tramo, nmax)
    cb = _ancestros(b, padre_tramo, nmax)
    idx_b = {n: i for i, n in enumerate(cb)}
    lca = None; ia = None
    for i, n in enumerate(ca):
        if n in idx_b:
            lca = n; ia = i; break
    if lca is None:
        return None
    subida = ca[:ia + 1]               # a ... lca
    bajada = cb[:idx_b[lca]]           # b ... (sin lca)
    return subida + list(reversed(bajada))


def _edge_between(X, Y, tramos, padre_tramo):
    """Tramo del arbol que conecta X-Y y su orientacion al recorrerlo X->Y."""
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
    """Base de ciclos fundamentales: por cada chord (a->b nativo), el lazo es el
    chord (a->b) + el camino del arbol (b->a). Cada arista del lazo lleva su
    orientacion (+1 si se recorre en su sentido nativo ni->nj, -1 si al reves)."""
    nmax = len(nodos) + 1
    lazos = []
    for c in chords:
        t = tramos[c]; a = t.get("ni"); b = t.get("nj")
        ruta = _ruta_nodos(b, a, padre_tramo, nmax)   # b ... a por el arbol
        if not ruta or ruta[0] != b or ruta[-1] != a:
            continue
        lazo = [(c, 1)]                                 # chord recorrido a->b => +1
        ok = True
        for i in range(len(ruta) - 1):
            tid_e, orient = _edge_between(ruta[i], ruta[i + 1], tramos, padre_tramo)
            if tid_e is None:
                ok = False; break
            lazo.append((tid_e, orient))
        if ok:
            lazos.append(lazo)
    return lazos


def _hardy_cross(tramos, Qsig, lazos, k_acc):
    """Reparto hiperestatico por HARDY-CROSS sobre los caudales con signo Qsig
    (m3/s, sentido nativo ni->nj). Cada lazo recibe correcciones secuenciales
    ΔQ = -ΣhL / Σ(2|hL|/|Q|) hasta cierre. Devuelve (iteraciones, residuos_lazo,
    residuo_max, convergio)."""
    iters = 0
    convergio = False
    for it in range(HC_MAX_ITER):
        dq_max = 0.0; res_max = 0.0
        for lazo in lazos:
            E = 0.0; D = 0.0
            for tid, orient in lazo:
                q = Qsig[tid]; aq = abs(q)
                _v, _Re, _f, dp = _perdida_tramo(tramos[tid], aq, k_acc)
                dp = dp or 0.0
                signo = 1.0 if q >= 0 else -1.0
                E += orient * dp * signo            # perdida con signo en el lazo
                if aq > 1e-12:
                    D += 2.0 * dp / aq              # d(hL)/dQ ~ 2 hL / Q (n=2)
            dq = (-E / D) if D > 0 else 0.0
            for tid, orient in lazo:
                Qsig[tid] += orient * dq
            dq_max = max(dq_max, abs(dq))
            res_max = max(res_max, abs(E))
        iters = it + 1
        if dq_max < HC_TOL_Q and res_max < HC_TOL_H:
            convergio = True
            break
    # residuos finales de cada lazo (Σ perdidas con signo, kPa)
    residuos = []
    res_max = 0.0
    for lazo in lazos:
        E = 0.0
        for tid, orient in lazo:
            q = Qsig[tid]; aq = abs(q)
            _v, _Re, _f, dp = _perdida_tramo(tramos[tid], aq, k_acc)
            dp = dp or 0.0
            E += orient * dp * (1.0 if q >= 0 else -1.0)
        residuos.append(round(E, 6))
        res_max = max(res_max, abs(E))
    return iters, residuos, res_max, convergio


def _demanda_nodo(modelo, activos):
    """Caudal demandado (m3/s) en cada nodo por los terminales ACTIVOS."""
    q = {}
    for term in modelo.get("terminales", []):
        if term.get("id") not in activos:
            continue
        nm = term.get("nodo")
        d = term.get("demanda") or {}
        ql = d.get("caudal_l_s")
        if ql is None:
            ql = term.get("caudal_min")  # respaldo: dato del modelo neutro
        if nm is not None and ql:
            q[nm] = q.get(nm, 0.0) + float(ql) / 1000.0
    return q


def seleccionar_simultaneos(modelo):
    """Selecciona el conjunto de terminales SIMULTANEOS mas desfavorable: los
    n_simultaneas terminales con MAYOR longitud de camino desde la fuente (proxy
    del caso hidraulico mas desfavorable). n_simultaneas viene de sistema.demanda
    (bases_demanda, H3); si falta, todos. En rociadores n = nº del area de
    operacion (densidad x area, UNE-EN 12845)."""
    nodos, tramos = modelo["nodos"], modelo["tramos"]
    fuentes = [f.get("nodo") for f in modelo.get("fuentes", []) if f.get("nodo")]
    for nm, n in nodos.items():
        if n.get("tipo") == "fuente" and nm not in fuentes:
            fuentes.append(nm)
    padre_tramo, _hijos, _orden, _m = _arbol_desde_fuente(nodos, tramos, fuentes)

    def long_camino(nm):
        L, cur, guard = 0.0, nm, 0
        while cur in padre_tramo and guard < len(nodos) + 1:
            tid, pa = padre_tramo[cur]
            L += float(tramos[tid].get("longitud", 0.0) or 0.0)
            cur = pa; guard += 1
        return L

    sis = modelo.get("sistema", {}) or {}
    dem = sis.get("demanda") or {}
    n_sim = dem.get("n_simultaneas")
    terms = [t for t in modelo.get("terminales", []) if t.get("nodo")]
    terms_orden = sorted(terms, key=lambda t: (-long_camino(t["nodo"]), str(t.get("id"))))
    if not n_sim or n_sim >= len(terms_orden):
        sel = terms_orden
    else:
        sel = terms_orden[:int(n_sim)]
    return [t.get("id") for t in sel]


def resolver(modelo, k_acc=K_ACC_DEF, v_max=V_MAX_DEF, activos=None):
    """Resuelve la red a presion (arbol o malla). Devuelve dict con tramos
    (Q,v,Re,f,dp), nodos (presion), terminales (presion disponible vs minima),
    el reparto de mallas (Hardy-Cross) y el veredicto."""
    nodos = {k: dict(v) for k, v in modelo["nodos"].items()}
    tramos = modelo["tramos"]
    avisos = []

    fuentes = modelo.get("fuentes", [])
    raices = [f.get("nodo") for f in fuentes if f.get("nodo")]
    for nm, n in nodos.items():
        if n.get("tipo") == "fuente" and nm not in raices:
            raices.append(nm)
    if not raices:
        return {"veredicto": "NO CUMPLE",
                "errores": ["La red no tiene fuente (ancla); no se puede propagar presion."],
                "avisos": avisos}

    if activos is None:
        activos = seleccionar_simultaneos(modelo)
    activos = set(activos)

    padre_tramo, hijos, orden, _mallas_bfs = _arbol_desde_fuente(nodos, tramos, raices)
    _arbol_tids, chords = _clasificar_tramos(nodos, tramos, padre_tramo)
    n_lazos = len(chords)

    # 1) reparto de caudales por continuidad en el ARBOL (semilla): el caudal de
    #    un tramo (nodo->hijo) es la demanda acumulada del subarbol aguas abajo.
    dem_nodo = _demanda_nodo(modelo, activos)
    q_subarbol = {nm: 0.0 for nm in nodos}
    for nm in reversed(orden):           # de hojas a raiz
        q_subarbol[nm] += dem_nodo.get(nm, 0.0)
        if nm in padre_tramo:
            _tid, pa = padre_tramo[nm]
            q_subarbol[pa] += q_subarbol[nm]
    # caudal con signo (sentido nativo ni->nj); chords arrancan en 0
    Qsig = {tid: 0.0 for tid in tramos}
    for nm in orden:
        for tid, h in hijos[nm]:
            q = q_subarbol[h]            # flujo padre(nm) -> hijo(h), m3/s
            t = tramos[tid]
            Qsig[tid] = q if (t.get("ni") == nm and t.get("nj") == h) else -q

    # 1bis) si hay mallas, reparto hiperestatico por Hardy-Cross
    hardy = None
    if n_lazos:
        lazos = _construir_lazos(nodos, tramos, padre_tramo, chords)
        iters, residuos, res_max, convergio = _hardy_cross(tramos, Qsig, lazos, k_acc)
        hardy = {"metodo": "Hardy-Cross (correccion por lazo, n=2) [confirmar criterio]",
                 "n_lazos": n_lazos, "iteraciones": iters,
                 "residuo_lazo_max_kPa": round(res_max, 6),
                 "residuos_lazo_kPa": residuos, "convergio": convergio}
        avisos.append("Red MALLADA: %d lazo(s) resuelto(s) por Hardy-Cross "
                      "(%d iter, residuo max %.5f kPa, %s)."
                      % (n_lazos, iters, res_max,
                         "converge" if convergio else "NO converge"))
        if not convergio:
            avisos.append("Hardy-Cross no alcanzo tolerancia: revisar la red/datos.")
    caudal_tramo = {tid: abs(Qsig[tid]) for tid in tramos}

    # 2) perdida de carga por tramo (Darcy-Weisbach), con el caudal repartido
    tramos_out = {}
    for tid, t in tramos.items():
        Q = caudal_tramo.get(tid, 0.0)           # m3/s
        v, Re, f, dp = _perdida_tramo(t, Q, k_acc)
        qs = round(Qsig[tid] * 1000.0, 4)          # caudal con signo (ni->nj +)
        sentido = "ni->nj" if Qsig[tid] >= 0 else "nj->ni"
        if v is None:
            avisos.append("Tramo %s sin DN: se omite su perdida de carga." % tid)
            tramos_out[tid] = {"caudal_l_s": round(Q * 1000.0, 4),
                               "caudal_signed_l_s": qs, "sentido": sentido,
                               "dn": t.get("dn"),
                               "longitud_m": float(t.get("longitud", 0.0) or 0.0),
                               "velocidad_m_s": None, "Re": None, "f": None,
                               "dp_kPa": None, "ni": t.get("ni"), "nj": t.get("nj")}
            continue
        tramos_out[tid] = {
            "caudal_l_s": round(Q * 1000.0, 4), "caudal_signed_l_s": qs,
            "sentido": sentido, "dn": t.get("dn"),
            "longitud_m": round(float(t.get("longitud", 0.0) or 0.0), 4),
            "velocidad_m_s": round(v, 4), "Re": round(Re, 1), "f": round(f, 5),
            "dp_kPa": round(dp, 4), "ni": t.get("ni"), "nj": t.get("nj"),
        }

    # 3) propagacion de presiones desde la fuente (con cota) por el ARBOL.
    p_fuente = {}
    for f_ in fuentes:
        if f_.get("nodo"):
            p_fuente[f_["nodo"]] = f_.get("presion")  # kPa (puede ser None)
    presion = {}
    for r in raices:
        presion[r] = p_fuente.get(r)
    for nm in orden:
        if nm not in presion:
            presion[nm] = None
        for tid, h in hijos[nm]:
            pp = presion.get(nm)
            if pp is None:
                presion[h] = None
                continue
            dz = nodos[h].get("z", 0.0) - nodos[nm].get("z", 0.0)
            dp_t = tramos_out[tid].get("dp_kPa") or 0.0
            dp_z = RHO * G * dz / 1000.0   # kPa (ganancia/perdida por cota)
            presion[h] = pp - dp_t - dp_z

    for nm in nodos:
        nodos[nm]["presion_kPa"] = (round(presion[nm], 3)
                                    if presion.get(nm) is not None else None)

    # 4) comprobacion en terminales activos + presion requerida en fuente
    terminales_out = []
    p_requerida = None
    for term in modelo.get("terminales", []):
        nm = term.get("nodo")
        d = term.get("demanda") or {}
        p_min = d.get("presion_din_min_kPa")
        if p_min is None:
            p_min = term.get("presion_min")
        act = term.get("id") in activos
        p_disp = presion.get(nm)
        # presion requerida en fuente para este terminal = p_min + perdidas + cota
        # del camino fuente->terminal (solo si esta activo)
        if act and p_min is not None:
            perd, cur, guard = 0.0, nm, 0
            while cur in padre_tramo and guard < len(nodos) + 1:
                tid, pa = padre_tramo[cur]
                perd += tramos_out[tid].get("dp_kPa") or 0.0
                perd += RHO * G * (nodos[cur].get("z", 0.0) - nodos[pa].get("z", 0.0)) / 1000.0
                cur = pa; guard += 1
            req = float(p_min) + perd
            p_requerida = req if p_requerida is None else max(p_requerida, req)
        cumple = None
        if act and p_disp is not None and p_min is not None:
            cumple = bool(p_disp >= p_min)
        terminales_out.append({
            "id": term.get("id"), "nodo": nm, "activo": act,
            "caudal_l_s": (d.get("caudal_l_s") if d.get("caudal_l_s") is not None
                           else term.get("caudal_min")),
            "presion_disponible_kPa": (round(p_disp, 3) if p_disp is not None else None),
            "presion_min_kPa": p_min,
            "margen_kPa": (round(p_disp - p_min, 3)
                           if (p_disp is not None and p_min is not None) else None),
            "cumple": cumple,
        })

    # presion disponible en fuente (la mayor declarada)
    p_disp_fuente = None
    for f_ in fuentes:
        pv = f_.get("presion")
        if pv is not None:
            p_disp_fuente = pv if p_disp_fuente is None else max(p_disp_fuente, pv)

    # 5) veredicto
    errores = []
    v_lista = [to["velocidad_m_s"] for to in tramos_out.values()
               if to.get("velocidad_m_s") is not None]
    v_pico = max(v_lista) if v_lista else 0.0
    if v_pico > v_max:
        errores.append("Velocidad %.2f m/s > v_max %.1f m/s en algun tramo." % (v_pico, v_max))
    for to in terminales_out:
        if to["activo"] and to["cumple"] is False:
            errores.append("Terminal %s: presion %.1f < min %.1f kPa."
                           % (to["id"], to["presion_disponible_kPa"], to["presion_min_kPa"]))
    if (p_requerida is not None and p_disp_fuente is not None
            and p_disp_fuente < p_requerida):
        errores.append("Presion de fuente %.1f kPa < requerida %.1f kPa."
                       % (p_disp_fuente, p_requerida))
    if hardy is not None and not hardy["convergio"]:
        errores.append("Hardy-Cross no convergio (residuo lazo %.4f kPa)."
                       % hardy["residuo_lazo_max_kPa"])
    veredicto = "CUMPLE" if not errores else "NO CUMPLE"

    return {
        "veredicto": veredicto,
        "metodo": "Darcy-Weisbach (friccion Swamee-Jain) [confirmar AN]",
        "topologia": {"n_nodos": len(nodos), "n_tramos": len(tramos),
                      "n_lazos": n_lazos, "tipo": "malla" if n_lazos else "arbol"},
        "hardy_cross": hardy,
        "hipotesis": {"rho_kg_m3": RHO, "nu_m2_s": NU, "k_accesorios": k_acc,
                      "v_max_m_s": v_max, "rugosidad_def_mm": RUG_DEF_MM},
        "simultaneos": sorted(activos),
        "presion_fuente_disponible_kPa": p_disp_fuente,
        "presion_fuente_requerida_kPa": (round(p_requerida, 3)
                                         if p_requerida is not None else None),
        "margen_fuente_kPa": (round(p_disp_fuente - p_requerida, 3)
                              if (p_disp_fuente is not None and p_requerida is not None) else None),
        "velocidad_pico_m_s": round(v_pico, 4),
        "tramos": tramos_out,
        "nodos": {nm: {"presion_kPa": nodos[nm].get("presion_kPa"),
                       "tipo": nodos[nm].get("tipo")} for nm in nodos},
        "terminales": terminales_out,
        "errores": errores, "avisos": avisos,
    }


def main(modelo_path, out=None):
    with open(modelo_path, encoding="utf-8") as fh:
        modelo = json.load(fh)
    res = resolver(modelo)
    print("=" * 64)
    print("SOLVER HIDRAULICO DE RED --", modelo.get("sistema", {}).get("tipo"))
    print("=" * 64)
    print(" Metodo:", res["metodo"])
    print(" Topologia:", res["topologia"])
    if res.get("hardy_cross"):
        hc = res["hardy_cross"]
        print(" Hardy-Cross: %d lazo(s), %d iter, residuo max %.5f kPa, %s"
              % (hc["n_lazos"], hc["iteraciones"], hc["residuo_lazo_max_kPa"],
                 "converge" if hc["convergio"] else "NO converge"))
    print(" Simultaneos:", res["simultaneos"])
    print(" Fuente: disponible=%s kPa | requerida=%s kPa | margen=%s kPa"
          % (res["presion_fuente_disponible_kPa"], res["presion_fuente_requerida_kPa"],
             res["margen_fuente_kPa"]))
    print(" Velocidad pico: %.3f m/s" % res["velocidad_pico_m_s"])
    for tid, to in res["tramos"].items():
        print("  %s: Q=%.3f l/s v=%.3f m/s f=%s dp=%.3f kPa"
              % (tid, to["caudal_l_s"], to["velocidad_m_s"] or 0, to["f"], to["dp_kPa"] or 0))
    for to in res["terminales"]:
        print("  term %s: activo=%s p_disp=%s p_min=%s cumple=%s"
              % (to["id"], to["activo"], to["presion_disponible_kPa"],
                 to["presion_min_kPa"], to["cumple"]))
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
    import sys
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
