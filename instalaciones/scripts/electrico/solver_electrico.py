"""
SOLVER DE RED ELECTRICA DE BAJA TENSION (REBT). Disciplina `instalaciones`,
PT 4.5 (Ola 4). Segundo solver SOBRE EL MISMO GRAFO de red (el primero es el
hidraulico Darcy-Weisbach). Las redes BT de interior son RADIALES (arbol): se
reutiliza la PROPAGACION POR ARBOL del solver hidraulico (`red/solver_red.py`,
`_arbol_desde_fuente`), no se duplica el grafo ni hace falta Hardy-Cross.

FRONTERA (contratos C1/C4): el NUCLEO da la TOPOLOGIA (nodos+tramos del modelo
neutro de red, parser MEP de iso19650-openbim, sistema ELECTRICAL) y la DEMANDA la
rellena `electrico/bases_demanda_electrica.py` (potencia/cosphi/fases por terminal,
tension por sistema). Este modulo SOLO CALCULA:
  - reparto de POTENCIAS por continuidad en el arbol (P de un tramo = suma de la
    potencia de calculo del subarbol aguas abajo),
  - INTENSIDAD por tramo: I = P/(U*cosphi) [mono] ; I = P/(sqrt3*U*cosphi) [tri],
  - PROPUESTA DE SECCION (metodo de momentos + intensidad admisible) de un catalogo
    normalizado, respetando la seccion minima normativa del circuito,
  - CAIDA DE TENSION por tramo (metodo de las intensidades, I*R con cosphi):
    dU = 2*L*I*cosphi/(gamma*S) [mono] ; dU = sqrt3*L*I*cosphi/(gamma*S) [tri],
    y su ACUMULADA desde la fuente por la rama,
  - REDIMENSIONADO: si la caida acumulada supera el limite, sube la seccion del
    tramo gobernante de la rama hasta cumplir (o agotar catalogo).

NO lee IFC (eso es C1, en iso19650-openbim). Consume el modelo neutro (JSON) con la
clave `demanda` ya rellena. Es STDLIB PURA.

Hipotesis y NDP (todos [confirmar AN / criterio del despacho]):
  - Conductividad gamma (m/ohm.mm2): Cu 56, Al 35 (a 20 C). A temperatura de
    servicio baja (Cu ~48 a 90 C XLPE, ~44 a 70 C PVC); por defecto 20 C.
  - Intensidad admisible: tabla ITC-BT-19 (Cu) por aislamiento PVC/XLPE y nº de
    conductores cargados (2 = mono, 3 = tri), instalacion de referencia.
  - Caida de tension maxima (ITC-BT-19): 3 % alumbrado / 5 % fuerza (interior).
  - Reactancia despreciada (valido para secciones pequenas; gancho para anadir X).

Todo resultado es de predimensionado/asistencia y debe ser revisado y firmado por
tecnico competente (Ingeniero de Caminos).
"""
import json
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "red"))
import solver_red as _SR   # noqa: E402  (reutiliza _arbol_desde_fuente, _clasificar_tramos)

# --- catalogo de secciones normalizadas (mm2) -------------------------------
SECCIONES = [1.5, 2.5, 4.0, 6.0, 10.0, 16.0, 25.0, 35.0, 50.0, 70.0, 95.0,
             120.0, 150.0, 185.0, 240.0]

# --- conductividad gamma (m/ohm.mm2) a 20 C [confirmar AN] -------------------
GAMMA = {"CU": 56.0, "AL": 35.0}
SQRT3 = math.sqrt(3.0)

# --- intensidad admisible (A), conductor de Cu, ITC-BT-19 (Tabla 1) ----------
# por aislamiento y nº de conductores cargados (2=mono, 3=tri). [confirmar AN]
I_ADM = {
    "PVC": {
        2: {1.5: 15, 2.5: 21, 4: 27, 6: 36, 10: 50, 16: 66, 25: 84, 35: 104,
            50: 125, 70: 160, 95: 194, 120: 225, 150: 260, 185: 297, 240: 350},
        3: {1.5: 13, 2.5: 18, 4: 24, 6: 31, 10: 44, 16: 59, 25: 77, 35: 96,
            50: 117, 70: 149, 95: 180, 120: 208, 150: 236, 185: 268, 240: 315},
    },
    "XLPE": {
        2: {1.5: 18, 2.5: 25, 4: 34, 6: 43, 10: 60, 16: 80, 25: 106, 35: 131,
            50: 159, 70: 202, 95: 245, 120: 284, 150: 338, 185: 386, 240: 455},
        3: {1.5: 16, 2.5: 22, 4: 30, 6: 37, 10: 52, 16: 70, 25: 88, 35: 110,
            50: 133, 70: 171, 95: 207, 120: 240, 150: 278, 185: 317, 240: 374},
    },
}

U_MONO = 230.0
U_TRI = 400.0
SIZING_MAX_ITER = 200


def _es_tri(fases):
    return str(fases).lower().startswith("tri")


def _i_admisible(aislamiento, ncond, s_mm2):
    tabla = I_ADM.get(str(aislamiento).upper(), I_ADM["PVC"]).get(ncond, {})
    return float(tabla.get(s_mm2, 0.0))


def _seccion_por_intensidad(aislamiento, ncond, I, s_min=0.0):
    """Menor seccion del catalogo cuya intensidad admisible >= I y >= s_min."""
    for s in SECCIONES:
        if s < s_min:
            continue
        if _i_admisible(aislamiento, ncond, s) >= I:
            return s
    return SECCIONES[-1]


def _siguiente_seccion(s):
    for sx in SECCIONES:
        if sx > s:
            return sx
    return s


def _du_tramo(L, I, cosphi, gamma, S, tri):
    """Caida de tension (V) de un tramo por el metodo de las intensidades."""
    if S <= 0:
        return 0.0
    k = SQRT3 if tri else 2.0
    return k * L * I * cosphi / (gamma * S)


def _demanda_nodo(modelo, activos):
    """Potencia (W), cosphi y fases agregados por nodo desde los terminales
    ACTIVOS. Para varios terminales en un nodo agrega potencia y cosphi ponderado."""
    pot, num, den, tri = {}, {}, {}, {}
    for term in modelo.get("terminales", []):
        if term.get("id") not in activos:
            continue
        nm = term.get("nodo")
        d = term.get("demanda") or {}
        p = float(d.get("potencia_W") or 0.0)
        c = float(d.get("cosphi") or 0.9)
        if nm is None or p <= 0:
            continue
        pot[nm] = pot.get(nm, 0.0) + p
        num[nm] = num.get(nm, 0.0) + p
        den[nm] = den.get(nm, 0.0) + p / c if c > 0 else den.get(nm, 0.0)
        tri[nm] = tri.get(nm, False) or _es_tri(d.get("fases"))
    return pot, num, den, tri


def resolver(modelo, aislamiento="PVC", material="Cu", gamma=None, activos=None):
    """Resuelve la red electrica radial. Devuelve dict con tramos (P,I,seccion,dU),
    nodos (caida acumulada), terminales (caida acum vs limite) y el veredicto."""
    nodos = {k: dict(v) for k, v in modelo["nodos"].items()}
    tramos = modelo["tramos"]
    avisos = []
    gamma = float(gamma) if gamma else GAMMA.get(str(material).upper(), GAMMA["CU"])
    aisl = str(aislamiento).upper()

    fuentes = modelo.get("fuentes", [])
    raices = [f.get("nodo") for f in fuentes if f.get("nodo")]
    for nm, n in nodos.items():
        if n.get("tipo") == "fuente" and nm not in raices:
            raices.append(nm)
    if not raices:
        return {"veredicto": "NO CUMPLE",
                "errores": ["La red no tiene fuente (cuadro); no se puede propagar tension."],
                "avisos": avisos}

    sis = modelo.get("sistema", {}) or {}
    sd = sis.get("demanda") or {}
    if activos is None:
        activos = [t.get("id") for t in modelo.get("terminales", []) if t.get("nodo")]
    activos = set(activos)

    padre_tramo, hijos, orden, _m = _SR._arbol_desde_fuente(nodos, tramos, raices)
    _arbol_tids, chords = _SR._clasificar_tramos(nodos, tramos, padre_tramo)
    n_lazos = len(chords)
    if n_lazos:
        avisos.append("La red tiene %d lazo(s): BT de interior se asume RADIAL; se "
                      "resuelve el ARBOL generador (chords ignorados) [confirmar criterio]."
                      % n_lazos)

    # 1) potencia de calculo acumulada por el subarbol aguas abajo (W)
    pot_nodo, num_nodo, den_nodo, tri_nodo = _demanda_nodo(modelo, activos)
    p_sub = {nm: 0.0 for nm in nodos}
    num_sub = {nm: 0.0 for nm in nodos}   # numerador cosphi ponderado (Sigma P)
    den_sub = {nm: 0.0 for nm in nodos}   # denominador (Sigma P/cosphi)
    tri_sub = {nm: False for nm in nodos}
    for nm in reversed(orden):            # de hojas a raiz
        p_sub[nm] += pot_nodo.get(nm, 0.0)
        num_sub[nm] += num_nodo.get(nm, 0.0)
        den_sub[nm] += den_nodo.get(nm, 0.0)
        tri_sub[nm] = tri_sub[nm] or tri_nodo.get(nm, False)
        if nm in padre_tramo:
            _tid, pa = padre_tramo[nm]
            p_sub[pa] += p_sub[nm]
            num_sub[pa] += num_sub[nm]
            den_sub[pa] += den_sub[nm]
            tri_sub[pa] = tri_sub[pa] or tri_sub[nm]

    # 2) por cada tramo del arbol (padre->hijo): P, fases, cosphi, U, I
    tramo_info = {}
    for nm in orden:
        for tid, h in hijos[nm]:
            t = tramos[tid]
            P = p_sub[h]                       # potencia que circula por el tramo (W)
            tri = _es_tri(t.get("fases")) or tri_sub[h]
            cphi = (num_sub[h] / den_sub[h]) if den_sub[h] > 0 else 0.9
            U = U_TRI if tri else U_MONO
            den_i = (SQRT3 * U * cphi) if tri else (U * cphi)
            I = (P / den_i) if den_i > 0 else 0.0
            L = float(t.get("longitud", 0.0) or 0.0)
            # seccion minima normativa heredada de la demanda del terminal del subarbol
            s_min = 0.0
            for term in modelo.get("terminales", []):
                d = term.get("demanda") or {}
                if d.get("seccion_min_mm2") and term.get("nodo") == h:
                    s_min = max(s_min, float(d["seccion_min_mm2"]))
            tramo_info[tid] = {"P": P, "I": I, "cosphi": cphi, "tri": tri, "U": U,
                               "L": L, "s_min": s_min, "h": h, "pa": nm}

    # 3) seccion inicial por intensidad admisible (+ seccion minima)
    seccion = {}
    for tid, ti in tramo_info.items():
        ncond = 3 if ti["tri"] else 2
        seccion[tid] = _seccion_por_intensidad(aisl, ncond, ti["I"], ti["s_min"])

    def _du_acumulada():
        """Caida acumulada (V) por nodo con las secciones actuales."""
        du_t = {}
        for tid, ti in tramo_info.items():
            du_t[tid] = _du_tramo(ti["L"], ti["I"], ti["cosphi"], gamma,
                                  seccion[tid], ti["tri"])
        acum = {r: 0.0 for r in raices}
        for nm in orden:
            if nm not in acum:
                acum[nm] = 0.0
            for tid, h in hijos[nm]:
                acum[h] = acum.get(nm, 0.0) + du_t[tid]
        return du_t, acum

    # 4) redimensionado por caida de tension acumulada (sube seccion del tramo
    #    gobernante de la rama que incumple, hasta cumplir o agotar catalogo)
    def _limite(term):
        d = term.get("demanda") or {}
        return float(d.get("du_max_pct") or 5.0)

    def _u_term(term):
        d = term.get("demanda") or {}
        return float(d.get("tension_V") or U_MONO)

    for _it in range(SIZING_MAX_ITER):
        du_t, acum = _du_acumulada()
        peor = None  # (exceso_pct, terminal)
        for term in modelo.get("terminales", []):
            if term.get("id") not in activos:
                continue
            nm = term.get("nodo")
            if nm is None:
                continue
            pct = 100.0 * acum.get(nm, 0.0) / _u_term(term)
            exceso = pct - _limite(term)
            if exceso > 1e-6 and (peor is None or exceso > peor[0]):
                peor = (exceso, term)
        if peor is None:
            break
        # camino fuente->terminal; sube la seccion del tramo con mayor dU del camino
        nm = peor[1].get("nodo")
        camino = []
        cur, guard = nm, 0
        while cur in padre_tramo and guard < len(nodos) + 1:
            tid, pa = padre_tramo[cur]
            camino.append(tid); cur = pa; guard += 1
        candidatos = [tid for tid in camino if seccion[tid] < SECCIONES[-1]]
        if not candidatos:
            break  # catalogo agotado: lo marcara la verificacion
        tid_max = max(candidatos, key=lambda t: du_t[t])
        seccion[tid_max] = _siguiente_seccion(seccion[tid_max])
    else:
        avisos.append("Redimensionado por caida de tension no convergio en %d iter."
                      % SIZING_MAX_ITER)

    # 5) salida por tramo
    du_t, acum = _du_acumulada()
    tramos_out = {}
    for tid in tramos:
        ti = tramo_info.get(tid)
        if ti is None:   # chord ignorado (red asumida radial)
            tramos_out[tid] = {"potencia_W": None, "intensidad_A": None,
                               "seccion_mm2": None, "I_admisible_A": None,
                               "caida_tension_V": None, "caida_tension_pct": None,
                               "fases": None, "cosphi": None,
                               "longitud_m": float(tramos[tid].get("longitud", 0.0) or 0.0),
                               "material": tramos[tid].get("material"),
                               "ni": tramos[tid].get("ni"), "nj": tramos[tid].get("nj"),
                               "nota": "chord (lazo) ignorado: red radial"}
            continue
        S = seccion[tid]
        ncond = 3 if ti["tri"] else 2
        i_adm = _i_admisible(aisl, ncond, S)
        du_pct_tramo = 100.0 * du_t[tid] / ti["U"]
        tramos_out[tid] = {
            "potencia_W": round(ti["P"], 2),
            "intensidad_A": round(ti["I"], 3),
            "fases": "tri" if ti["tri"] else "mono",
            "cosphi": round(ti["cosphi"], 4),
            "tension_V": ti["U"],
            "seccion_mm2": S,
            "I_admisible_A": i_adm,
            "longitud_m": round(ti["L"], 4),
            "caida_tension_V": round(du_t[tid], 4),
            "caida_tension_pct": round(du_pct_tramo, 4),
            "material": material,
            "ni": tramos[tid].get("ni"), "nj": tramos[tid].get("nj"),
        }

    # 6) nodos con caida acumulada
    for nm in nodos:
        a = acum.get(nm)
        nodos[nm]["caida_acum_V"] = round(a, 4) if a is not None else None

    # 7) terminales: caida acumulada vs limite
    terminales_out = []
    caida_max_pct = 0.0
    gobernante = None
    for term in modelo.get("terminales", []):
        nm = term.get("nodo")
        d = term.get("demanda") or {}
        act = term.get("id") in activos
        U = _u_term(term)
        a = acum.get(nm)
        pct = (100.0 * a / U) if (a is not None and U) else None
        lim = float(d.get("du_max_pct") or 5.0)
        cumple = None
        if act and pct is not None:
            cumple = bool(pct <= lim)
            if pct > caida_max_pct:
                caida_max_pct = pct
                gobernante = term.get("id")
        terminales_out.append({
            "id": term.get("id"), "nodo": nm, "activo": act,
            "potencia_W": d.get("potencia_W"),
            "cosphi": d.get("cosphi"),
            "fases": d.get("fases"),
            "tension_V": U,
            "uso": d.get("uso"),
            "circuito": d.get("circuito"),
            "caida_acum_pct": (round(pct, 4) if pct is not None else None),
            "du_max_pct": lim,
            "margen_pct": (round(lim - pct, 4) if pct is not None else None),
            "cumple": cumple,
        })

    # 8) veredicto
    errores = []
    for tid, to in tramos_out.items():
        if to.get("intensidad_A") is None:
            continue
        if to["I_admisible_A"] and to["intensidad_A"] > to["I_admisible_A"]:
            errores.append("Tramo %s: I=%.1f A > admisible %.1f A (S=%s mm2)."
                           % (tid, to["intensidad_A"], to["I_admisible_A"], to["seccion_mm2"]))
    for to in terminales_out:
        if to["activo"] and to["cumple"] is False:
            errores.append("Terminal %s: caida acumulada %.2f %% > limite %.2f %%."
                           % (to["id"], to["caida_acum_pct"], to["du_max_pct"]))
    veredicto = "CUMPLE" if not errores else "NO CUMPLE"

    p_total = sum(ti["P"] for ti in [tramo_info[t] for t in tramo_info
                  if tramo_info[t]["pa"] in raices]) if tramo_info else 0.0

    return {
        "veredicto": veredicto,
        "metodo": ("Intensidades (I*R con cosphi, mono/tri); seccion propuesta por "
                   "momentos + intensidad admisible (ITC-BT-19) [confirmar AN]"),
        "topologia": {"n_nodos": len(nodos), "n_tramos": len(tramos),
                      "n_lazos": n_lazos, "tipo": "radial"},
        "hipotesis": {"aislamiento": aisl, "material": material, "gamma_m_ohm_mm2": gamma,
                      "U_mono_V": U_MONO, "U_tri_V": U_TRI},
        "activos": sorted(activos),
        "potencia_cabecera_W": round(p_total, 2),
        "caida_max_pct": round(caida_max_pct, 4),
        "terminal_gobernante": gobernante,
        "tramos": tramos_out,
        "nodos": {nm: {"caida_acum_V": nodos[nm].get("caida_acum_V"),
                       "tipo": nodos[nm].get("tipo")} for nm in nodos},
        "terminales": terminales_out,
        "errores": errores, "avisos": avisos,
    }


def main(modelo_path, out=None):
    with open(modelo_path, encoding="utf-8") as fh:
        modelo = json.load(fh)
    res = resolver(modelo)
    print("=" * 64)
    print("SOLVER RED ELECTRICA (REBT) --", modelo.get("sistema", {}).get("tipo"))
    print("=" * 64)
    print(" Metodo:", res["metodo"])
    print(" Topologia:", res["topologia"])
    print(" Hipotesis:", res["hipotesis"])
    print(" P cabecera: %.0f W | caida max: %.3f %% (gobernante %s)"
          % (res["potencia_cabecera_W"], res["caida_max_pct"], res["terminal_gobernante"]))
    for tid, to in res["tramos"].items():
        if to["intensidad_A"] is None:
            continue
        print("  %s: P=%.0f W I=%.2f A S=%s mm2 (I_adm=%.0f) dU=%.3f%% [%s]"
              % (tid, to["potencia_W"], to["intensidad_A"], to["seccion_mm2"],
                 to["I_admisible_A"], to["caida_tension_pct"], to["fases"]))
    for to in res["terminales"]:
        print("  term %s: P=%s W caida_acum=%s%% (lim %s) cumple=%s"
              % (to["id"], to["potencia_W"], to["caida_acum_pct"],
                 to["du_max_pct"], to["cumple"]))
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
